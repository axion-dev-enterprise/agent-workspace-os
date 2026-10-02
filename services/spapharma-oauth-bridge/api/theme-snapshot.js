const { authorizeOperationsRequest } = require('../lib/ops-auth');
const { loadTokenRecord } = require('../lib/token-store');

function configuredShop() {
  const shop = process.env.SHOPIFY_SHOP;
  return shop?.endsWith('.myshopify.com') ? shop : `${shop}.myshopify.com`;
}

async function shopifyGraphql(shop, accessToken, query, variables = {}) {
  const response = await fetch(`https://${shop}/admin/api/2026-07/graphql.json`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Shopify-Access-Token': accessToken,
    },
    body: JSON.stringify({ query, variables }),
  });
  const payload = await response.json();
  if (!response.ok || payload.errors || !payload.data) {
    throw new Error(payload.errors?.map(({ message }) => message).join('; ') || `HTTP ${response.status}`);
  }
  return payload.data;
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

  const after = req.body?.after ?? null;
  const target = req.body?.target ?? 'main';
  if (after !== null && (typeof after !== 'string' || after.length > 512)) {
    return res.status(400).json({ type: 'about:blank', title: 'Invalid cursor', status: 400 });
  }
  if (!['main', 'workspace'].includes(target)) {
    return res.status(400).json({ type: 'about:blank', title: 'Invalid target', status: 400 });
  }

  try {
    const shop = configuredShop();
    const tokenRecord = await loadTokenRecord(shop);
    if (!tokenRecord?.accessToken) {
      return res.status(503).json({ type: 'about:blank', title: 'No stored authorization', status: 503 });
    }
    const selection = await shopifyGraphql(
      shop,
      tokenRecord.accessToken,
      `query ThemeSnapshotSelection { themes(first: 20) { nodes { id name role updatedAt } } }`,
    );
    const themes = selection.themes?.nodes ?? [];
    const selected = target === 'main'
      ? themes.find(({ role }) => role === 'MAIN')
      : themes.find(({ role, name }) => role === 'UNPUBLISHED' && name === 'AXION Backlog QA 2026-10-01')
        ?? themes.find(({ role, name }) => role === 'UNPUBLISHED' && /c[oó]pia/i.test(name))
        ?? themes.find(({ role }) => role === 'UNPUBLISHED');
    if (!selected) {
      return res.status(404).json({ type: 'about:blank', title: 'Main theme not found', status: 404 });
    }
    const snapshot = await shopifyGraphql(
      shop,
      tokenRecord.accessToken,
      `query ThemeSnapshotFiles($id: ID!, $after: String) {
        theme(id: $id) {
          id name role updatedAt
          files(first: 50, after: $after) {
            nodes {
              filename contentType size checksumMd5 createdAt updatedAt
              body {
                ... on OnlineStoreThemeFileBodyText { content }
                ... on OnlineStoreThemeFileBodyBase64 { contentBase64 }
                ... on OnlineStoreThemeFileBodyUrl { url }
              }
            }
            pageInfo { hasNextPage endCursor }
            userErrors { code filename }
          }
        }
      }`,
      { id: selected.id, after },
    );
    const theme = snapshot.theme;
    return res.status(200).json({ shop, theme });
  } catch (error) {
    return res.status(502).json({
      type: 'about:blank',
      title: 'Theme snapshot failed',
      status: 502,
      detail: error instanceof Error ? error.message : 'Unknown error',
    });
  }
};
