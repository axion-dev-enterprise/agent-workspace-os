const { authorizeOperationsRequest } = require('../lib/ops-auth');
const { loadTokenRecord } = require('../lib/token-store');

const WORKSPACE_NAME = 'AXION Backlog QA 2026-10-01';
const FILES = ['templates/index.json', 'sections/footer-group.json'];
const BASELINE_CHECKSUMS = {
  'templates/index.json': 'a39b170f99c6a0fff98137c369594d7b',
  'sections/footer-group.json': 'ea4e6ba5ec027fba49bb71db8cf3a548',
};

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

function replaceExactlyOnce(content, before, after, filename) {
  const first = content.indexOf(before);
  if (first < 0 || content.indexOf(before, first + before.length) >= 0) {
    throw new Error(`Expected exactly one target string in ${filename}`);
  }
  return content.slice(0, first) + after + content.slice(first + before.length);
}

async function readFiles(shop, accessToken, themeId) {
  const data = await shopifyGraphql(
    shop,
    accessToken,
    `query QuickWinFiles($id: ID!, $filenames: [String!]!) {
      theme(id: $id) {
        files(first: 2, filenames: $filenames) {
          nodes {
            filename checksumMd5
            body { ... on OnlineStoreThemeFileBodyText { content } }
          }
        }
      }
    }`,
    { id: themeId, filenames: FILES },
  );
  return new Map((data.theme?.files?.nodes ?? []).map((node) => [node.filename, node]));
}

async function writeFiles(shop, accessToken, themeId, contents) {
  return shopifyGraphql(
    shop,
    accessToken,
    `mutation ApplyQuickWins($themeId: ID!, $files: [OnlineStoreThemeFilesUpsertFileInput!]!) {
      themeFilesUpsert(themeId: $themeId, files: $files) {
        upsertedThemeFiles { filename }
        userErrors { field message code filename }
      }
    }`,
    {
      themeId,
      files: FILES.map((filename) => ({ filename, body: { type: 'TEXT', value: contents.get(filename) } })),
    },
  );
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

  let originals;
  let theme;
  let accessToken;
  const shop = configuredShop();
  try {
    const tokenRecord = await loadTokenRecord(shop);
    accessToken = tokenRecord?.accessToken;
    if (!accessToken) {
      return res.status(503).json({ type: 'about:blank', title: 'No stored authorization', status: 503 });
    }
    const selection = await shopifyGraphql(
      shop,
      accessToken,
      `query QuickWinThemeSelection { themes(first: 20) { nodes { id name role processing processingFailed } } }`,
    );
    theme = (selection.themes?.nodes ?? []).find(({ name, role }) => name === WORKSPACE_NAME && role === 'UNPUBLISHED');
    if (!theme || theme.processing || theme.processingFailed) {
      return res.status(409).json({ type: 'about:blank', title: 'QA theme is not ready', status: 409 });
    }

    originals = await readFiles(shop, accessToken, theme.id);
    if (originals.size !== FILES.length) throw new Error('One or more baseline files are missing');
    const alreadyApplied = originals.get('templates/index.json').body.content.includes('"link_text": "Ver todos"')
      && originals.get('sections/footer-group.json').body.content.includes('Pagamento protegido pela Shopify');
    if (alreadyApplied) {
      return res.status(200).json({ shop, applied: false, alreadyApplied: true, theme: { id: theme.id, name: theme.name, role: theme.role } });
    }
    for (const filename of FILES) {
      if (originals.get(filename).checksumMd5 !== BASELINE_CHECKSUMS[filename]) {
        return res.status(409).json({ type: 'about:blank', title: `Baseline drift detected in ${filename}`, status: 409 });
      }
    }

    const updated = new Map();
    updated.set(
      'templates/index.json',
      replaceExactlyOnce(originals.get('templates/index.json').body.content, '"link_text": "View all"', '"link_text": "Ver todos"', 'templates/index.json'),
    );
    updated.set(
      'sections/footer-group.json',
      replaceExactlyOnce(
        originals.get('sections/footer-group.json').body.content,
        '<p>Informe seus clientes sobre seus métodos de pagamento.</p>',
        '<p>Pagamento protegido pela Shopify. As opções disponíveis são exibidas no checkout.</p>',
        'sections/footer-group.json',
      ),
    );

    const result = await writeFiles(shop, accessToken, theme.id, updated);
    const errors = result.themeFilesUpsert?.userErrors ?? [];
    if (errors.length || result.themeFilesUpsert?.upsertedThemeFiles?.length !== FILES.length) {
      throw new Error(errors.map(({ message }) => message).join('; ') || 'Shopify did not update both files');
    }
    const verified = await readFiles(shop, accessToken, theme.id);
    const verifiedContent = verified.get('templates/index.json').body.content.includes('"link_text": "Ver todos"')
      && verified.get('sections/footer-group.json').body.content.includes('Pagamento protegido pela Shopify');
    if (!verifiedContent) throw new Error('Quick-win verification failed after update');

    return res.status(200).json({
      shop,
      applied: true,
      verified: true,
      theme: { id: theme.id, name: theme.name, role: theme.role },
      files: FILES,
    });
  } catch (error) {
    let rollbackConfirmed = false;
    if (originals?.size === FILES.length && theme && accessToken) {
      try {
        const rollback = new Map(FILES.map((filename) => [filename, originals.get(filename).body.content]));
        await writeFiles(shop, accessToken, theme.id, rollback);
        const verified = await readFiles(shop, accessToken, theme.id);
        rollbackConfirmed = FILES.every((filename) => verified.get(filename).checksumMd5 === originals.get(filename).checksumMd5);
      } catch {
        rollbackConfirmed = false;
      }
    }
    return res.status(502).json({
      type: 'about:blank',
      title: 'Theme quick wins failed',
      status: 502,
      rollbackConfirmed,
      detail: error instanceof Error ? error.message : 'Unknown error',
    });
  }
};
