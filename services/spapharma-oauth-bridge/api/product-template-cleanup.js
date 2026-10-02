const { authorizeOperationsRequest } = require('../lib/ops-auth');
const { loadTokenRecord } = require('../lib/token-store');
const crypto = require('crypto');

const WORKSPACE_NAME = 'AXION Backlog QA 2026-10-01';
const FILENAME = 'templates/product.json';
const BASELINE_CHECKSUM = 'bf40c7047563175531c473a00c32bd4a';
const BASELINE_STRUCTURAL_SHA256 = '99c372aadeed9771a1cb683dfb91586989066becdb673086122f9177b00bfd45';
const REMOVE_BLOCKS = [
  'judge_me_reviews_preview_badge_Q49kYe',
  'judge_me_reviews_review_snippet_widget_y8YAM7',
  'judge_me_reviews_preview_badge_nkdYRj',
];
const REMOVE_SECTIONS = ['1785962822fb989731'];

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
  if (!response.ok || payload.errors || !payload.data) {
    throw new Error(payload.errors?.map(({ message }) => message).join('; ') || `HTTP ${response.status}`);
  }
  return payload.data;
}

async function readFile(shop, accessToken, themeId) {
  const data = await shopifyGraphql(
    shop,
    accessToken,
    `query ProductTemplate($id: ID!, $filenames: [String!]!) {
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
    `mutation ProductTemplateCleanup($themeId: ID!, $files: [OnlineStoreThemeFilesUpsertFileInput!]!) {
      themeFilesUpsert(themeId: $themeId, files: $files) { upsertedThemeFiles { filename } userErrors { field message code filename } }
    }`,
    { themeId, files: [{ filename: FILENAME, body: { type: 'TEXT', value: content } }] },
  );
  const errors = data.themeFilesUpsert?.userErrors ?? [];
  if (errors.length || data.themeFilesUpsert?.upsertedThemeFiles?.length !== 1) {
    throw new Error(errors.map(({ message }) => message).join('; ') || 'Shopify did not update the product template');
  }
}

function validateApplied(template) {
  const main = template.sections?.main;
  return main
    && REMOVE_BLOCKS.every((id) => !main.blocks?.[id] && !main.block_order?.includes(id))
    && REMOVE_SECTIONS.every((id) => !template.sections?.[id] && !template.order?.includes(id))
    && Boolean(main.blocks?.judge_me_reviews_preview_badge_J4FGfE)
    && Boolean(template.sections?.['17859559252a5da3db']?.blocks?.judge_me_reviews_review_widget_Dj6WQD);
}

function parseThemeJson(content) {
  const objectStart = content.indexOf('{');
  if (objectStart < 0) throw new Error('Product template JSON object is missing');
  return { header: content.slice(0, objectStart), value: JSON.parse(content.slice(objectStart)) };
}

module.exports = async (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  res.setHeader('X-Content-Type-Options', 'nosniff');
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ type: 'about:blank', title: 'Method not allowed', status: 405 });
  }
  if (!authorizeOperationsRequest(req)) {
    return res.status(401).json({ type: 'about:blank', title: 'Unauthorized', status: 401 });
  }

  const shop = configuredShop();
  let original;
  let theme;
  let accessToken;
  let writeAttempted = false;
  try {
    const tokenRecord = await loadTokenRecord(shop);
    accessToken = tokenRecord?.accessToken;
    if (!accessToken) return res.status(503).json({ type: 'about:blank', title: 'No stored authorization', status: 503 });
    const selection = await shopifyGraphql(shop, accessToken, `query CleanupThemeSelection { themes(first: 20) { nodes { id name role processing processingFailed } } }`);
    theme = (selection.themes?.nodes ?? []).find(({ name, role }) => name === WORKSPACE_NAME && role === 'UNPUBLISHED');
    if (!theme || theme.processing || theme.processingFailed) {
      return res.status(409).json({ type: 'about:blank', title: 'QA theme is not ready', status: 409 });
    }
    original = await readFile(shop, accessToken, theme.id);
    if (!original?.body?.content) throw new Error('Product template is missing');
    const parsedDocument = parseThemeJson(original.body.content);
    const parsed = parsedDocument.value;
    if (validateApplied(parsed)) {
      return res.status(200).json({ shop, applied: false, alreadyApplied: true, theme: { id: theme.id, name: theme.name, role: theme.role } });
    }
    const structuralHash = crypto.createHash('sha256').update(JSON.stringify(parsed)).digest('hex');
    if (original.checksumMd5 !== BASELINE_CHECKSUM && structuralHash !== BASELINE_STRUCTURAL_SHA256) {
      return res.status(409).json({ type: 'about:blank', title: 'Product template baseline drift detected', status: 409 });
    }
    for (const id of REMOVE_BLOCKS) {
      if (!parsed.sections?.main?.blocks?.[id] || !parsed.sections.main.block_order?.includes(id)) {
        throw new Error(`Expected duplicate review block is missing: ${id}`);
      }
      delete parsed.sections.main.blocks[id];
      parsed.sections.main.block_order = parsed.sections.main.block_order.filter((blockId) => blockId !== id);
    }
    for (const id of REMOVE_SECTIONS) {
      if (!parsed.sections?.[id] || !parsed.order?.includes(id)) throw new Error(`Expected empty section is missing: ${id}`);
      delete parsed.sections[id];
      parsed.order = parsed.order.filter((sectionId) => sectionId !== id);
    }
    writeAttempted = true;
    await writeFile(shop, accessToken, theme.id, `${parsedDocument.header}${JSON.stringify(parsed, null, 2)}`);
    const verified = parseThemeJson((await readFile(shop, accessToken, theme.id)).body.content).value;
    if (!validateApplied(verified)) throw new Error('Product template verification failed');
    return res.status(200).json({
      shop,
      applied: true,
      verified: true,
      theme: { id: theme.id, name: theme.name, role: theme.role },
      preserved: ['judge_me_reviews_preview_badge_J4FGfE', 'judge_me_reviews_review_widget_Dj6WQD', 'upsell_com_ex_reconvert_product_upsell_6zyGCY'],
      removed: [...REMOVE_BLOCKS, ...REMOVE_SECTIONS],
    });
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
    return res.status(502).json({
      type: 'about:blank',
      title: 'Product template cleanup failed',
      status: 502,
      rollbackConfirmed,
      detail: error instanceof Error ? error.message : 'Unknown error',
    });
  }
};
