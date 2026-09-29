const crypto = require('crypto');

function readCookie(header, name) {
  return (header || '').split(';').map((part) => part.trim()).find((part) => part.startsWith(`${name}=`))?.slice(name.length + 1);
}

module.exports = (req, res) => {
  const configuredShop = process.env.SHOPIFY_SHOP;
  const clientId = process.env.SHOPIFY_CLIENT_ID;
  const scopes = process.env.SHOPIFY_SCOPES;
  if (!configuredShop || !clientId || !scopes) {
    return res.status(503).json({ type: 'about:blank', title: 'OAuth bridge is not configured', status: 503 });
  }

  const shop = configuredShop.endsWith('.myshopify.com') ? configuredShop : `${configuredShop}.myshopify.com`;
  const state = crypto.randomBytes(32).toString('hex');
  const redirectUri = `https://${req.headers.host}/api/callback`;
  const query = new URLSearchParams({ client_id: clientId, scope: scopes, redirect_uri: redirectUri, state });
  res.setHeader('Set-Cookie', `shopify_oauth_state=${state}; Path=/api; HttpOnly; Secure; SameSite=Lax; Max-Age=600`);
  return res.redirect(302, `https://${shop}/admin/oauth/authorize?${query.toString()}`);
};
