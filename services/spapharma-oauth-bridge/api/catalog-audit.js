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
        query: `query CatalogAudit {
          products(first: 100, sortKey: TITLE) {
            nodes { id title handle status productType vendor updatedAt seo { title description } }
          }
          collections(first: 100, sortKey: TITLE) {
            nodes { id title handle updatedAt productsCount { count } seo { title description } }
          }
          pages(first: 100, sortKey: TITLE) {
            nodes { id title handle isPublished updatedAt }
          }
          blogs(first: 50) {
            nodes { id title handle updatedAt }
          }
          menus(first: 100) {
            nodes { id title handle }
          }
          themes(first: 20) {
            nodes { id name role updatedAt processing processingFailed }
          }
        }`,
      }),
    });

    const payload = await apiResponse.json();
    if (!apiResponse.ok || payload.errors || !payload.data) {
      return res.status(502).json({
        type: 'about:blank',
        title: 'Shopify catalog audit failed',
        status: 502,
        errors: payload.errors?.map(({ message }) => message) ?? [],
      });
    }

    return res.status(200).json({ shop, audit: payload.data });
  } catch {
    return res.status(502).json({ type: 'about:blank', title: 'Catalog audit failed', status: 502 });
  }
};
