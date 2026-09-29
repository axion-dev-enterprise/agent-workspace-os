# SpaPharma OAuth bridge

OAuth bridge for the SPA Pharma Shopify app. It exchanges the one-time OAuth code, verifies the store identity with the Admin GraphQL API, then writes the token record to the project's private Vercel Blob store. The token, refresh token, storage URL, and client secret are never returned by the HTTP endpoints or written to application logs.

Required Vercel environment variables: `SHOPIFY_SHOP`, `SHOPIFY_CLIENT_ID`, `SHOPIFY_CLIENT_SECRET`, `SHOPIFY_SCOPES`, and the automatically connected `BLOB_READ_WRITE_TOKEN`. The production callback must be registered in the Shopify app version before using `/api/auth`.

The record is private storage: it can only be read server-side with Vercel Blob authentication. `api/token-store.js` is deliberately an internal module; no endpoint exposes the token. A future operations endpoint must implement separate authentication and a constrained operation policy before it can invoke Admin API mutations.

`GET /api/capabilities` is a read-only diagnostic route. It returns only the scopes Shopify actually granted to this installation and their descriptions; it never returns a token, customer data, order data, or Blob metadata.

`GET /api/catalog-audit` is a read-only, non-PII inventory route for products, collections, pages, blogs, menus, and themes. It never returns tokens, customers, orders, or payment data.
