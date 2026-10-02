const crypto = require('crypto');
const { authorizeOperationsRequest } = require('../lib/ops-auth');
const { loadTokenRecord } = require('../lib/token-store');

const WORKSPACE_NAME = 'AXION Backlog QA 2026-10-01';
const EXISTING_FILES = ['templates/index.json', 'layout/theme.liquid'];
const FAVICON_FILE = 'assets/favicon.svg';
const INDEX_BASELINE_STRUCTURAL_SHA256 = '4adb84ac8c90c5667d37d381f8372b26265349b24e27478edf1be1aba23abd9f';
const THEME_BASELINE_SHA256 = '198204a9a703ac1e75988d5791baa9f3413b57e44222bb48382e93ff78d4dbff';
const FALLBACK_DESCRIPTION = 'Produtos Spa Pharma para cuidados faciais, limpeza, hidratação, firmeza e rotina de skincare. Consulte informações, preços e disponibilidade.';
const FAVICON_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#ffffff"/><circle cx="32" cy="32" r="27" fill="none" stroke="#0f3b57" stroke-width="4"/><text x="32" y="39" text-anchor="middle" font-family="Arial,sans-serif" font-size="22" font-weight="700" fill="#0f3b57">SP</text></svg>';

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

async function readFiles(shop, accessToken, themeId) {
  const filenames = [...EXISTING_FILES, FAVICON_FILE];
  const data = await shopifyGraphql(
    shop,
    accessToken,
    `query QualityFiles($id: ID!, $filenames: [String!]!) {
      theme(id: $id) { files(first: 3, filenames: $filenames) { nodes { filename checksumMd5 body { ... on OnlineStoreThemeFileBodyText { content } } } } }
    }`,
    { id: themeId, filenames },
  );
  return new Map((data.theme?.files?.nodes ?? []).map((node) => [node.filename, node]));
}

async function writeFiles(shop, accessToken, themeId, contents) {
  const data = await shopifyGraphql(
    shop,
    accessToken,
    `mutation QualityFilesUpsert($themeId: ID!, $files: [OnlineStoreThemeFilesUpsertFileInput!]!) {
      themeFilesUpsert(themeId: $themeId, files: $files) { upsertedThemeFiles { filename } userErrors { field message code filename } }
    }`,
    { themeId, files: [...contents].map(([filename, value]) => ({ filename, body: { type: 'TEXT', value } })) },
  );
  const errors = data.themeFilesUpsert?.userErrors ?? [];
  if (errors.length || data.themeFilesUpsert?.upsertedThemeFiles?.length !== contents.size) {
    throw new Error(errors.map(({ message }) => message).join('; ') || 'Shopify did not update all quality files');
  }
}

async function deleteFile(shop, accessToken, themeId, filename) {
  const data = await shopifyGraphql(
    shop,
    accessToken,
    `mutation QualityFileDelete($themeId: ID!, $files: [String!]!) {
      themeFilesDelete(themeId: $themeId, files: $files) { deletedThemeFiles { filename } userErrors { field message code filename } }
    }`,
    { themeId, files: [filename] },
  );
  const errors = data.themeFilesDelete?.userErrors ?? [];
  if (errors.length) throw new Error(errors.map(({ message }) => message).join('; '));
}

function parseThemeJson(content) {
  const start = content.indexOf('{');
  if (start < 0) throw new Error('Theme JSON object is missing');
  return { header: content.slice(0, start), value: JSON.parse(content.slice(start)) };
}

function replaceExactlyOnce(content, before, after, filename) {
  const first = content.indexOf(before);
  if (first < 0 || content.indexOf(before, first + before.length) >= 0) throw new Error(`Expected exactly one target in ${filename}`);
  return content.slice(0, first) + after + content.slice(first + before.length);
}

function validateIndexBaseline(index) {
  const copy = structuredClone(index);
  if (copy.sections?.featured_collection_b3tLwB?.settings?.link_text === 'Ver todos') {
    copy.sections.featured_collection_b3tLwB.settings.link_text = 'View all';
  }
  const hash = crypto.createHash('sha256').update(JSON.stringify(copy)).digest('hex');
  return hash === INDEX_BASELINE_STRUCTURAL_SHA256;
}

function validateApplied(files) {
  const index = parseThemeJson(files.get('templates/index.json').body.content).value;
  const theme = files.get('layout/theme.liquid').body.content;
  return index.sections?.slideshow?.settings?.autoplay === false
    && index.sections?.slideshow_waXeAK?.settings?.autoplay === true
    && index.sections?.video_938iEc?.settings?.autoplay === false
    && index.sections?.video_RVLKEU?.settings?.autoplay === false
    && theme.includes('width=device-width, initial-scale=1.0, height=device-height"')
    && theme.includes(FALLBACK_DESCRIPTION)
    && theme.includes(`{{ '${FAVICON_FILE.split('/')[1]}' | asset_url }}`)
    && files.get(FAVICON_FILE)?.body?.content === FAVICON_SVG;
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
  let originals;
  let theme;
  let accessToken;
  let writeAttempted = false;
  try {
    const tokenRecord = await loadTokenRecord(shop);
    accessToken = tokenRecord?.accessToken;
    if (!accessToken) return res.status(503).json({ type: 'about:blank', title: 'No stored authorization', status: 503 });
    const selection = await shopifyGraphql(shop, accessToken, `query QualityThemeSelection { themes(first: 20) { nodes { id name role processing processingFailed } } }`);
    theme = (selection.themes?.nodes ?? []).find(({ name, role }) => name === WORKSPACE_NAME && role === 'UNPUBLISHED');
    if (!theme || theme.processing || theme.processingFailed) return res.status(409).json({ type: 'about:blank', title: 'QA theme is not ready', status: 409 });

    originals = await readFiles(shop, accessToken, theme.id);
    if (!EXISTING_FILES.every((name) => originals.get(name)?.body?.content)) throw new Error('One or more quality baseline files are missing');
    if (validateApplied(originals)) return res.status(200).json({ shop, applied: false, alreadyApplied: true, theme: { id: theme.id, name: theme.name, role: theme.role } });

    const indexDocument = parseThemeJson(originals.get('templates/index.json').body.content);
    if (!validateIndexBaseline(indexDocument.value)) return res.status(409).json({ type: 'about:blank', title: 'Home template structural drift detected', status: 409 });
    const layoutHash = crypto.createHash('sha256').update(originals.get('layout/theme.liquid').body.content).digest('hex');
    if (layoutHash !== THEME_BASELINE_SHA256) return res.status(409).json({ type: 'about:blank', title: 'Theme layout baseline drift detected', status: 409 });
    if (originals.has(FAVICON_FILE)) return res.status(409).json({ type: 'about:blank', title: 'Favicon asset already exists outside this operation', status: 409 });

    const index = indexDocument.value;
    if (Object.keys(index.sections?.slideshow?.blocks ?? {}).length !== 1 || Object.keys(index.sections?.slideshow_waXeAK?.blocks ?? {}).length < 2) {
      throw new Error('Slideshow structure does not match the audited baseline');
    }
    index.sections.slideshow.settings.autoplay = false;
    index.sections.video_938iEc.settings.autoplay = false;
    index.sections.video_RVLKEU.settings.autoplay = false;

    let themeLayout = originals.get('layout/theme.liquid').body.content;
    themeLayout = replaceExactlyOnce(
      themeLayout,
      '<meta name="viewport" content="width=device-width, initial-scale=1.0, height=device-height, minimum-scale=1.0, maximum-scale=1.0">',
      '<meta name="viewport" content="width=device-width, initial-scale=1.0, height=device-height">',
      'layout/theme.liquid',
    );
    themeLayout = replaceExactlyOnce(
      themeLayout,
      `{%- if page_description -%}\n      <meta name="description" content="{{ page_description | escape }}">\n    {%- endif -%}`,
      `{%- assign effective_description = page_description | default: '${FALLBACK_DESCRIPTION}' -%}\n    <meta name="description" content="{{ effective_description | escape }}">`,
      'layout/theme.liquid',
    );
    themeLayout = replaceExactlyOnce(
      themeLayout,
      `{%- if settings.favicon -%}\n      <link rel="shortcut icon" href="{{ settings.favicon | image_url: width: 96 }}">\n      <link rel="apple-touch-icon" href="{{ settings.favicon | image_url: width: 180 }}">\n    {%- endif -%}`,
      `{%- if settings.favicon -%}\n      <link rel="shortcut icon" href="{{ settings.favicon | image_url: width: 96 }}">\n      <link rel="apple-touch-icon" href="{{ settings.favicon | image_url: width: 180 }}">\n    {%- else -%}\n      <link rel="icon" href="{{ 'favicon.svg' | asset_url }}" type="image/svg+xml">\n    {%- endif -%}`,
      'layout/theme.liquid',
    );

    const updated = new Map([
      ['templates/index.json', `${indexDocument.header}${JSON.stringify(index, null, 2)}`],
      ['layout/theme.liquid', themeLayout],
      [FAVICON_FILE, FAVICON_SVG],
    ]);
    writeAttempted = true;
    await writeFiles(shop, accessToken, theme.id, updated);
    const verified = await readFiles(shop, accessToken, theme.id);
    if (!validateApplied(verified)) throw new Error('Quality verification failed after update');
    return res.status(200).json({
      shop,
      applied: true,
      verified: true,
      theme: { id: theme.id, name: theme.name, role: theme.role },
      changes: ['single-slide autoplay disabled', 'two autoplay videos disabled', 'viewport zoom restored', 'fallback meta description added', 'fallback favicon added'],
    });
  } catch (error) {
    let rollbackConfirmed = false;
    if (writeAttempted && originals && theme && accessToken) {
      try {
        const rollback = new Map(EXISTING_FILES.map((name) => [name, originals.get(name).body.content]));
        await writeFiles(shop, accessToken, theme.id, rollback);
        if (!originals.has(FAVICON_FILE)) await deleteFile(shop, accessToken, theme.id, FAVICON_FILE);
        const restored = await readFiles(shop, accessToken, theme.id);
        rollbackConfirmed = EXISTING_FILES.every((name) => restored.get(name)?.checksumMd5 === originals.get(name).checksumMd5)
          && !restored.has(FAVICON_FILE);
      } catch {
        rollbackConfirmed = false;
      }
    }
    return res.status(502).json({ type: 'about:blank', title: 'Theme quality update failed', status: 502, rollbackConfirmed, detail: error instanceof Error ? error.message : 'Unknown error' });
  }
};
