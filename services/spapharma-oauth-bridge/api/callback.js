const crypto = require('crypto');
const { saveTokenRecord } = require('./token-store');

function readCookie(header, name) {
  return (header || '').split(';').map((part) => part.trim()).find((part) => part.startsWith(`${name}=`))?.slice(name.length + 1);
}

function validHmac(query, secret) {
  const received = query.hmac;
  if (!received || !secret) return false;
  const message = Object.keys(query).filter((key) => key !== 'hmac' && key !== 'signature').sort().map((key) => `${key}=${Array.isArray(query[key]) ? query[key].join(',') : query[key]}`).join('&');
  const expected = crypto.createHmac('sha256', secret).update(message).digest('hex');
  return received.length === expected.length && crypto.timingSafeEqual(Buffer.from(received), Buffer.from(expected));
}

module.exports = async (req, res) => {
  const { code, shop: requestedShop, state } = req.query;
  const expectedState = readCookie(req.headers.cookie, 'shopify_oauth_state');
  if (!code || !requestedShop || !state || state !== expectedState || !validHmac(req.query, process.env.SHOPIFY_CLIENT_SECRET)) {
    return res.status(400).json({ type: 'about:blank', title: 'Invalid OAuth callback', status: 400 });
  }

  const shop = requestedShop.endsWith('.myshopify.com') ? requestedShop : `${requestedShop}.myshopify.com`;
  const configuredShop = process.env.SHOPIFY_SHOP?.endsWith('.myshopify.com')
    ? process.env.SHOPIFY_SHOP
    : `${process.env.SHOPIFY_SHOP}.myshopify.com`;
  if (shop !== configuredShop) {
    return res.status(400).json({ type: 'about:blank', title: 'Unexpected Shopify store', status: 400 });
  }

  try {
    const tokenResponse = await fetch(`https://${shop}/admin/oauth/access_token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ client_id: process.env.SHOPIFY_CLIENT_ID, client_secret: process.env.SHOPIFY_CLIENT_SECRET, code }),
    });
    if (!tokenResponse.ok) return res.status(502).json({ type: 'about:blank', title: 'Token exchange failed', status: 502 });
    const tokenPayload = await tokenResponse.json();
    if (typeof tokenPayload.access_token !== 'string' || tokenPayload.access_token.length === 0) {
      return res.status(502).json({ type: 'about:blank', title: 'Token exchange returned no access token', status: 502 });
    }

    const apiResponse = await fetch(`https://${shop}/admin/api/2026-07/graphql.json`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Shopify-Access-Token': tokenPayload.access_token },
      body: JSON.stringify({ query: '{ shop { name myshopifyDomain } }' }),
    });
    if (!apiResponse.ok) return res.status(502).json({ type: 'about:blank', title: 'Shop verification failed', status: 502 });
    const payload = await apiResponse.json();
    if (!payload.data?.shop?.myshopifyDomain) {
      return res.status(502).json({ type: 'about:blank', title: 'Shop verification returned no store identity', status: 502 });
    }

    const storedAt = new Date().toISOString();
    const expiresAt = Number.isFinite(tokenPayload.expires_in)
      ? new Date(Date.now() + (tokenPayload.expires_in * 1000)).toISOString()
      : null;
    await saveTokenRecord({
      version: 1,
      shop,
      accessToken: tokenPayload.access_token,
      refreshToken: typeof tokenPayload.refresh_token === 'string' ? tokenPayload.refresh_token : null,
      scopes: typeof tokenPayload.scope === 'string' ? tokenPayload.scope : null,
      expiresAt,
      storedAt,
    });

    return res.status(200).json({
      verified: true,
      tokenStored: true,
      tokenExpiresAt: expiresAt,
      shop: payload.data.shop,
    });
  } catch {
    return res.status(502).json({ type: 'about:blank', title: 'Authorization storage failed', status: 502 });
  }
};
