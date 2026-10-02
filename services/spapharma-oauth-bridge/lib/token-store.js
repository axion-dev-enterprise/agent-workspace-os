const { get, put } = require('@vercel/blob');

function tokenPathFor(shop) {
  return `shopify-oauth/${encodeURIComponent(shop)}.json`;
}

async function saveTokenRecord(record) {
  return put(tokenPathFor(record.shop), JSON.stringify(record), {
    access: 'private',
    addRandomSuffix: false,
    allowOverwrite: true,
    contentType: 'application/json',
  });
}

async function loadTokenRecord(shop) {
  const result = await get(tokenPathFor(shop), { access: 'private' });
  if (!result) return null;
  return JSON.parse(await new Response(result.stream).text());
}

module.exports = { loadTokenRecord, saveTokenRecord };
