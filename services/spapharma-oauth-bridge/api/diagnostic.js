const { loadTokenRecord } = require('../lib/token-store');

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
        query: `query BaselineDiagnostic {
          shop { myshopifyDomain primaryDomain { url } }
          productsCount { count precision }
          collectionsCount { count precision }
          pagesCount { count precision }
          blogsCount { count precision }
          themes(first: 20) { nodes { role processing processingFailed updatedAt } }
        }`,
      }),
    });
    if (!apiResponse.ok) {
      return res.status(502).json({ type: 'about:blank', title: 'Shopify diagnostic query failed', status: 502 });
    }

    const payload = await apiResponse.json();
    if (!payload.data) {
      return res.status(502).json({ type: 'about:blank', title: 'Shopify returned no diagnostic data', status: 502 });
    }
    return res.status(200).json({ diagnostic: payload.data });
  } catch {
    return res.status(502).json({ type: 'about:blank', title: 'Diagnostic query failed', status: 502 });
  }
};
