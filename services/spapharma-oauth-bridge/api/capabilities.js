const { loadTokenRecord } = require('./token-store');

function configuredShop() {
  const shop = process.env.SHOPIFY_SHOP;
  return shop?.endsWith('.myshopify.com') ? shop : `${shop}.myshopify.com`;
}

module.exports = async (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  res.setHeader('X-Content-Type-Options', 'nosniff');
  if (req.method !== 'GET') {
    return res.status(405).json({ type: 'about:blank', title: 'Method not allowed', status: 405 });
  }

  try {
    const shop = configuredShop();
    const tokenRecord = await loadTokenRecord(shop);
    if (!tokenRecord?.accessToken) {
      return res.status(503).json({ type: 'about:blank', title: 'No stored authorization', status: 503 });
    }

    const apiResponse = await fetch(`https://${shop}/admin/api/2026-07/graphql.json`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Shopify-Access-Token': tokenRecord.accessToken,
      },
      body: JSON.stringify({
        query: '{ currentAppInstallation { accessScopes { handle description } } }',
      }),
    });
    if (!apiResponse.ok) {
      return res.status(502).json({ type: 'about:blank', title: 'Shopify capability query failed', status: 502 });
    }

    const payload = await apiResponse.json();
    const accessScopes = payload.data?.currentAppInstallation?.accessScopes;
    if (!Array.isArray(accessScopes)) {
      return res.status(502).json({ type: 'about:blank', title: 'Shopify returned no granted scopes', status: 502 });
    }
    return res.status(200).json({ shop, accessScopes: accessScopes.sort((a, b) => a.handle.localeCompare(b.handle)) });
  } catch {
    return res.status(502).json({ type: 'about:blank', title: 'Capability query failed', status: 502 });
  }
};
