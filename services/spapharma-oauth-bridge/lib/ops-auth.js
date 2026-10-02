const crypto = require('crypto');

function safeEqual(left, right) {
  const leftBuffer = Buffer.from(left ?? '', 'utf8');
  const rightBuffer = Buffer.from(right ?? '', 'utf8');
  if (leftBuffer.length !== rightBuffer.length) return false;
  return crypto.timingSafeEqual(leftBuffer, rightBuffer);
}

function authorizeOperationsRequest(req) {
  const configuredKey = process.env.SPAPHARMA_OPS_KEY;
  const authorization = req.headers.authorization ?? '';
  const suppliedKey = authorization.startsWith('Bearer ') ? authorization.slice(7) : '';
  return Boolean(configuredKey && safeEqual(suppliedKey, configuredKey));
}

module.exports = { authorizeOperationsRequest };
