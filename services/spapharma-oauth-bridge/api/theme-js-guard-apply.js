const crypto = require('crypto');
const { authorizeOperationsRequest } = require('../lib/ops-auth');
const { loadTokenRecord } = require('../lib/token-store');

const WORKSPACE_NAME = 'AXION Backlog QA 2026-10-01';
const FILENAME = 'assets/sections.js';
const BASELINE_SHA256 = '353ecf1a32d23dbe1e40513fb76a595ff2de2927f96b2a52ea69f0af3c3f940a';
const BEFORE_EVENT = '  async _onSlideSelected(event) {\n    const slideStyles = getComputedStyle(event.detail.slide);';
const AFTER_EVENT = '  async _onSlideSelected(event) {\n    if (!event.detail?.slide) return;\n    const slideStyles = getComputedStyle(event.detail.slide);';
const BEFORE_REVEAL = '  async _reveal() {\n    const selectedSlide = this.selectedSlide;\n    await imageLoaded4(selectedSlide.querySelectorAll("img"));';
const AFTER_REVEAL = '  async _reveal() {\n    const selectedSlide = this.selectedSlide;\n    if (!selectedSlide) {\n      this.style.opacity = "1";\n      return;\n    }\n    await imageLoaded4(selectedSlide.querySelectorAll("img"));';

function configuredShop() {
  const shop = process.env.SHOPIFY_SHOP;
  return shop?.endsWith('.myshopify.com') ? shop : `${shop}.myshopify.com`;
}

async function shopifyGraphql(shop, accessToken, query, variables = {}) {
  const response = await fetch(`https://${shop}/admin/api/2026-07/graphql.json`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Shopify-Access-Token': accessToken },
    body: JSON.stringify({ query, variables }),
  });
  const payload = await response.json();
  if (!response.ok || payload.errors || !payload.data) throw new Error(payload.errors?.map(({ message }) => message).join('; ') || `HTTP ${response.status}`);
  return payload.data;
}

async function readFile(shop, accessToken, themeId) {
  const data = await shopifyGraphql(
    shop,
    accessToken,
    `query JsGuardFile($id: ID!, $filenames: [String!]!) {
      theme(id: $id) { files(first: 1, filenames: $filenames) { nodes { filename checksumMd5 body { ... on OnlineStoreThemeFileBodyText { content } } } } }
    }`,
    { id: themeId, filenames: [FILENAME] },
  );
  return data.theme?.files?.nodes?.[0];
}

async function writeFile(shop, accessToken, themeId, content) {
  const data = await shopifyGraphql(
    shop,
    accessToken,
    `mutation JsGuardUpsert($themeId: ID!, $files: [OnlineStoreThemeFilesUpsertFileInput!]!) {
      themeFilesUpsert(themeId: $themeId, files: $files) { upsertedThemeFiles { filename } userErrors { field message code filename } }
    }`,
    { themeId, files: [{ filename: FILENAME, body: { type: 'TEXT', value: content } }] },
  );
  const errors = data.themeFilesUpsert?.userErrors ?? [];
  if (errors.length || data.themeFilesUpsert?.upsertedThemeFiles?.length !== 1) throw new Error(errors.map(({ message }) => message).join('; ') || 'Shopify did not update sections.js');
}

function replaceExactlyOnce(content, before, after) {
  const first = content.indexOf(before);
  if (first < 0 || content.indexOf(before, first + before.length) >= 0) throw new Error('Expected exactly one JavaScript patch target');
  return content.slice(0, first) + after + content.slice(first + before.length);
}

function isApplied(content) {
  return content.includes(AFTER_EVENT) && content.includes(AFTER_REVEAL);
}

module.exports = async (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  res.setHeader('X-Content-Type-Options', 'nosniff');
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ type: 'about:blank', title: 'Method not allowed', status: 405 });
  }
  if (!authorizeOperationsRequest(req)) return res.status(401).json({ type: 'about:blank', title: 'Unauthorized', status: 401 });

  const shop = configuredShop();
  let original;
  let theme;
  let accessToken;
  let writeAttempted = false;
  try {
    const tokenRecord = await loadTokenRecord(shop);
    accessToken = tokenRecord?.accessToken;
    if (!accessToken) return res.status(503).json({ type: 'about:blank', title: 'No stored authorization', status: 503 });
    const selection = await shopifyGraphql(shop, accessToken, `query JsGuardThemeSelection { themes(first: 20) { nodes { id name role processing processingFailed } } }`);
    theme = (selection.themes?.nodes ?? []).find(({ name, role }) => name === WORKSPACE_NAME && role === 'UNPUBLISHED');
    if (!theme || theme.processing || theme.processingFailed) return res.status(409).json({ type: 'about:blank', title: 'QA theme is not ready', status: 409 });
    original = await readFile(shop, accessToken, theme.id);
    if (!original?.body?.content) throw new Error('sections.js is missing');
    if (isApplied(original.body.content)) return res.status(200).json({ shop, applied: false, alreadyApplied: true, theme: { id: theme.id, name: theme.name, role: theme.role } });
    const hash = crypto.createHash('sha256').update(original.body.content).digest('hex');
    if (hash !== BASELINE_SHA256) return res.status(409).json({ type: 'about:blank', title: 'sections.js baseline drift detected', status: 409 });

    let updated = replaceExactlyOnce(original.body.content, BEFORE_EVENT, AFTER_EVENT);
    updated = replaceExactlyOnce(updated, BEFORE_REVEAL, AFTER_REVEAL);
    writeAttempted = true;
    await writeFile(shop, accessToken, theme.id, updated);
    const verified = await readFile(shop, accessToken, theme.id);
    if (!isApplied(verified?.body?.content ?? '')) throw new Error('JavaScript guard verification failed');
    return res.status(200).json({ shop, applied: true, verified: true, theme: { id: theme.id, name: theme.name, role: theme.role }, guards: ['missing carousel slide event', 'empty slideshow reveal'] });
  } catch (error) {
    let rollbackConfirmed = false;
    if (writeAttempted && original?.body?.content && theme && accessToken) {
      try {
        await writeFile(shop, accessToken, theme.id, original.body.content);
        const restored = await readFile(shop, accessToken, theme.id);
        rollbackConfirmed = restored.checksumMd5 === original.checksumMd5;
      } catch {
        rollbackConfirmed = false;
      }
    }
    return res.status(502).json({ type: 'about:blank', title: 'Theme JavaScript guard failed', status: 502, rollbackConfirmed, detail: error instanceof Error ? error.message : 'Unknown error' });
  }
};
