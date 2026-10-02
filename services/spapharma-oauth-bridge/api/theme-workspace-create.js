const { authorizeOperationsRequest } = require('../lib/ops-auth');
const { loadTokenRecord } = require('../lib/token-store');

const WORKSPACE_NAME = 'AXION Backlog QA 2026-10-01';

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

  try {
    const shop = configuredShop();
    const tokenRecord = await loadTokenRecord(shop);
    if (!tokenRecord?.accessToken) {
      return res.status(503).json({ type: 'about:blank', title: 'No stored authorization', status: 503 });
    }
    const selection = await shopifyGraphql(
      shop,
      tokenRecord.accessToken,
      `query ThemeWorkspaceSelection { themes(first: 20) { nodes { id name role processing processingFailed } } }`,
    );
    const themes = selection.themes?.nodes ?? [];
    const existing = themes.find(({ name }) => name === WORKSPACE_NAME);
    if (existing) {
      return res.status(200).json({ shop, created: false, theme: existing });
    }
    const main = themes.find(({ role }) => role === 'MAIN');
    if (!main) {
      return res.status(404).json({ type: 'about:blank', title: 'Main theme not found', status: 404 });
    }
    const result = await shopifyGraphql(
      shop,
      tokenRecord.accessToken,
      `mutation CreateThemeWorkspace($id: ID!, $name: String) {
        themeDuplicate(id: $id, name: $name) {
          newTheme { id name role processing processingFailed }
          userErrors { field message }
        }
      }`,
      { id: main.id, name: WORKSPACE_NAME },
    );
    const errors = result.themeDuplicate?.userErrors ?? [];
    if (errors.length || !result.themeDuplicate?.newTheme) {
      throw new Error(errors.map(({ message }) => message).join('; ') || 'Shopify did not duplicate the theme');
    }
    return res.status(201).json({ shop, created: true, sourceThemeId: main.id, theme: result.themeDuplicate.newTheme });
  } catch (error) {
    return res.status(502).json({
      type: 'about:blank',
      title: 'Theme workspace creation failed',
      status: 502,
      detail: error instanceof Error ? error.message : 'Unknown error',
    });
  }
};
