# SpaPharma OAuth bridge

OAuth bridge for the SPA Pharma Shopify app. It exchanges the one-time OAuth code, verifies the store identity with the Admin GraphQL API, then writes the token record to the project's private Vercel Blob store. The token, refresh token, storage URL, and client secret are never returned by the HTTP endpoints or written to application logs.

Required Vercel environment variables: `SHOPIFY_SHOP`, `SHOPIFY_CLIENT_ID`, `SHOPIFY_CLIENT_SECRET`, `SHOPIFY_SCOPES`, and the automatically connected `BLOB_READ_WRITE_TOKEN`. The production callback must be registered in the Shopify app version before using `/api/auth`.

The record is private storage: it can only be read server-side with Vercel Blob authentication. `lib/token-store.js` is deliberately an internal module; no endpoint exposes the token. Mutation routes require separate bearer authentication and implement fixed operation policies.

`GET /api/capabilities` is a read-only diagnostic route. It returns only the scopes Shopify actually granted to this installation and their descriptions; it never returns a token, customer data, order data, or Blob metadata.

`GET /api/catalog-audit` is a read-only, non-PII inventory route for products, collections, pages, blogs, menus, and themes. It never returns tokens, customers, orders, or payment data.

`POST /api/write-probe` is an authenticated, fixed-purpose capability check. It requires `Authorization: Bearer <SPAPHARMA_OPS_KEY>`, creates a uniquely named technical metafield on a draft product, deletes it immediately, and verifies cleanup. It does not accept arbitrary GraphQL or user-supplied resource IDs.

`POST /api/theme-snapshot` is an authenticated, read-only export in pages of 50 files. It accepts only an optional pagination cursor and a fixed target enum: `main` selects the live theme; `workspace` selects the unpublished working copy.

`POST /api/theme-quality-apply` applies checksum/structure-guarded accessibility, metadata and performance fixes only to the unpublished QA theme. It restores the original files and removes the created favicon if verification fails. The earlier `write_themes` probe completed successfully and was retired after proving create/delete cleanup.

`POST /api/theme-js-guard-apply` adds two narrow guards to the audited Impact `sections.js` in the QA theme, preventing empty and single-slide carousels from throwing during initialization. It rejects any baseline drift and restores the original asset if verification fails. The earlier `write_products` probe completed successfully and was retired after proving metafield create/delete cleanup.

`POST /api/theme-workspace-create` idempotently duplicates the current main theme as the unpublished `AXION Backlog QA 2026-10-01` workspace. It never publishes or deletes a theme.

`POST /api/theme-quick-wins-apply` applies two checksum-guarded content fixes to that unpublished workspace: translates `View all` and replaces the payment placeholder. It verifies both files and rolls back to the captured originals on failure.

`POST /api/catalog-seo-apply` applies a fixed, length-validated SEO title and description matrix to 15 active products and four collections whose SEO fields were empty in the baseline. It verifies identity, status and current values before each mutation and rolls back prior changes if any item fails.

`POST /api/product-template-cleanup` removes three duplicate Judge.me blocks and one empty app section from the unpublished QA product template. It preserves the primary Judge.me badge, the full review widget, ReConvert, cart controls and buy buttons; structural drift aborts the operation.
