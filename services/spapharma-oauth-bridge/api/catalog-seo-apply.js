const { authorizeOperationsRequest } = require('../lib/ops-auth');
const { loadTokenRecord } = require('../lib/token-store');

const SEO_UPDATES = [
  ['gid://shopify/Product/7726451785764', 'creme-firmador-com-colageno-spa-pharma-50ml', 'Creme Firmador com Colágeno 50ml | Spa Pharma', 'Conheça o Creme Firmador com Colágeno 50ml da Spa Pharma. Consulte informações, preço e disponibilidade na loja oficial.'],
  ['gid://shopify/Product/7726452080676', 'espuma-de-limpeza-com-vitamina-c-spa-pharma-220ml', 'Espuma de Limpeza com Vitamina C 220ml | Spa Pharma', 'Conheça a Espuma de Limpeza com Vitamina C 220ml da Spa Pharma. Consulte informações, preço e disponibilidade na loja oficial.'],
  ['gid://shopify/Product/7726458929188', 'kit-4-produtos-limpeza-antioxidante-tratamento-anti-idade-dia-e-noite', 'Kit BOOST Firmeza com Q10 e Colágeno | Spa Pharma', 'Conheça o Kit BOOST Firmeza com sérum de Coenzima Q10, creme firmador com colágeno e escovinha. Consulte preço e disponibilidade.'],
  ['gid://shopify/Product/11147846942756', 'kit-boost-vitamina-c-espuma-de-limpeza-com-vitamina-c-serum-com-vitamina-c-brinde-escova-facial', 'Kit BOOST Vitamina C com Escova Facial | Spa Pharma', 'Conheça o Kit BOOST Vitamina C com espuma de limpeza, sérum de vitamina C e escova facial. Consulte preço e disponibilidade.'],
  ['gid://shopify/Product/11061732048932', 'kit-efeito-microagulhamento-peeling-biologico-mineral-serum-revitalizador-pdrn-com-exossomas', 'Kit Mineral Peel e Sérum PDRN com Exossomas | Spa Pharma', 'Conheça o kit com Mineral Peel e Sérum Revitalizador com PDRN de arroz e exossomas. Veja informações, preço e disponibilidade.'],
  ['gid://shopify/Product/8272114253860', 'kit-tratamento-anti-idade-serum-coenzima-q10-e-creme-firmador-colageno', 'Kit Skincare Anti-idade com Q10 e Oliva | Spa Pharma', 'Conheça o kit com sérum de Coenzima Q10, creme anti-idade de oliva e escovinha. Consulte informações, preço e disponibilidade.'],
  ['gid://shopify/Product/7726453686308', 'kit-2-produtos-tratamento-anti-idade-hidratacao', 'Kit Skincare Firmador com Aparelho LED | Spa Pharma', 'Conheça o kit com espuma de limpeza, sérum Q10, creme anti-idade de oliva e aparelho LED. Consulte preço e disponibilidade.'],
  ['gid://shopify/Product/8272147251236', 'kit-tratamento-serum-multivitaminas-c-e-e-e-creme-anti-idade-de-oliva-dia-e-noite', 'Kit Skincare Preventivo C e E | Spa Pharma', 'Conheça o kit com sérum multivitaminas C e E, creme firmador com colágeno e escovinha. Consulte preço e disponibilidade.'],
  ['gid://shopify/Product/7726458798116', 'kit-3-produtos-limpeza-tratamento-e-prevencao-de-rugas-dia-e-noite', 'Kit Skincare Completo com Aparelho LED | Spa Pharma', 'Conheça o kit com espuma de limpeza, sérum multivitaminas, creme de colágeno e aparelho LED. Consulte preço e disponibilidade.'],
  ['gid://shopify/Product/11061650030628', 'mineral-peel-peeling-fisico-biologico-mineral-argila-verde-albumina-sponge-spicule-100mg', 'Mineral Peel Peeling Biológico Mineral 100mg | Spa Pharma', 'Conheça o Mineral Peel em pó com argila verde, albumina e Sponge Spicules. Consulte modo de uso, preço e disponibilidade.'],
  ['gid://shopify/Product/7726451687460', 'poderoso-creme-antirrugas-oliva-com-acido-hialuronico-spa-pharma-50ml', 'Creme Antirrugas Oliva e Ácido Hialurônico 50ml | Spa Pharma', 'Conheça o Creme Antirrugas de Oliva com Ácido Hialurônico 50ml da Spa Pharma. Consulte informações, preço e disponibilidade.'],
  ['gid://shopify/Product/7726452539428', 'serum-anti-idade-firmador-com-q10-e-acido-hialuronico-50ml', 'Sérum Firmador Q10 e Ácido Hialurônico 50ml | Spa Pharma', 'Conheça o Sérum Firmador com Coenzima Q10 e Ácido Hialurônico 50ml. Consulte informações, preço e disponibilidade.'],
  ['gid://shopify/Product/7726452211748', 'serum-de-vitamina-c-spa-pharma-30ml', 'Sérum de Vitamina C 30ml | Spa Pharma', 'Conheça o Sérum de Vitamina C 30ml da Spa Pharma. Consulte informações do produto, preço e disponibilidade na loja oficial.'],
  ['gid://shopify/Product/7726451327012', 'serum-intensivo-multivitaminas-50ml', 'Sérum Multivitaminas C e E 50ml | Spa Pharma', 'Conheça o Sérum Intensivo Multivitaminas C e E 50ml da Spa Pharma. Consulte informações, preço e disponibilidade.'],
  ['gid://shopify/Product/11061588525092', 'serum-revitalizador-com-pdrn-e-exossomas-30ml', 'Sérum PDRN com Exossomas 30ml | Spa Pharma', 'Conheça o Sérum Revitalizador com PDRN de arroz e exossomas 30ml. Consulte informações, preço e disponibilidade.'],
].map(([id, handle, title, description]) => ({ id, handle, title, description }));

const COLLECTION_SEO_UPDATES = [
  ['gid://shopify/Collection/471896260644', 'black', 'Seleção BLACK | Spa Pharma', 'Conheça a seleção BLACK da Spa Pharma com produtos para cuidados faciais. Consulte itens, preços e disponibilidade na loja oficial.'],
  ['gid://shopify/Collection/459925979172', 'kit', 'Kits de Tratamento Facial | Spa Pharma', 'Encontre kits de tratamento facial Spa Pharma para limpeza, hidratação, firmeza e cuidados anti-idade. Consulte preços e disponibilidade.'],
  ['gid://shopify/Collection/459924996132', 'mais-vendidos', 'Produtos Mais Vendidos | Spa Pharma', 'Conheça os produtos mais vendidos da Spa Pharma para sua rotina de skincare. Consulte informações, preços e disponibilidade.'],
  ['gid://shopify/Collection/459616682020', 'frontpage', 'Destaques de Skincare | Spa Pharma', 'Veja os destaques de skincare da Spa Pharma para cuidados diários com a pele. Consulte informações, preços e disponibilidade.'],
].map(([id, handle, title, description]) => ({ id, handle, title, description }));

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

async function readProduct(shop, accessToken, id) {
  const data = await shopifyGraphql(
    shop,
    accessToken,
    `query SeoProduct($id: ID!) { product(id: $id) { id handle status seo { title description } } }`,
    { id },
  );
  return data.product;
}

async function updateProduct(shop, accessToken, id, seo) {
  const data = await shopifyGraphql(
    shop,
    accessToken,
    `mutation SeoProductUpdate($product: ProductUpdateInput!) {
      productUpdate(product: $product) { product { id handle seo { title description } } userErrors { field message } }
    }`,
    { product: { id, seo } },
  );
  const errors = data.productUpdate?.userErrors ?? [];
  if (errors.length || !data.productUpdate?.product) {
    throw new Error(errors.map(({ message }) => message).join('; ') || `Product update failed for ${id}`);
  }
  return data.productUpdate.product;
}

async function readCollection(shop, accessToken, id) {
  const data = await shopifyGraphql(
    shop,
    accessToken,
    `query SeoCollection($id: ID!) { collection(id: $id) { id handle seo { title description } } }`,
    { id },
  );
  return data.collection;
}

async function updateCollection(shop, accessToken, id, seo) {
  const data = await shopifyGraphql(
    shop,
    accessToken,
    `mutation SeoCollectionUpdate($input: CollectionInput!) {
      collectionUpdate(input: $input) { collection { id handle seo { title description } } userErrors { field message } }
    }`,
    { input: { id, seo } },
  );
  const errors = data.collectionUpdate?.userErrors ?? [];
  if (errors.length || !data.collectionUpdate?.collection) {
    throw new Error(errors.map(({ message }) => message).join('; ') || `Collection update failed for ${id}`);
  }
  return data.collectionUpdate.collection;
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
  if ([...SEO_UPDATES, ...COLLECTION_SEO_UPDATES].some(({ title, description }) => title.length > 70 || description.length > 160)) {
    return res.status(500).json({ type: 'about:blank', title: 'SEO matrix exceeds length limits', status: 500 });
  }

  const shop = configuredShop();
  const originals = new Map();
  const changed = [];
  const collectionOriginals = new Map();
  const changedCollections = [];
  let accessToken;
  try {
    const tokenRecord = await loadTokenRecord(shop);
    accessToken = tokenRecord?.accessToken;
    if (!accessToken) {
      return res.status(503).json({ type: 'about:blank', title: 'No stored authorization', status: 503 });
    }
    for (const update of SEO_UPDATES) {
      const current = await readProduct(shop, accessToken, update.id);
      if (!current || current.handle !== update.handle || current.status !== 'ACTIVE') {
        return res.status(409).json({ type: 'about:blank', title: `Catalog drift detected for ${update.handle}`, status: 409 });
      }
      originals.set(update.id, current.seo);
      const isApplied = current.seo?.title === update.title && current.seo?.description === update.description;
      const isBaseline = current.seo?.title == null && current.seo?.description == null;
      if (!isApplied && !isBaseline) {
        return res.status(409).json({ type: 'about:blank', title: `SEO drift detected for ${update.handle}`, status: 409 });
      }
    }

    for (const update of COLLECTION_SEO_UPDATES) {
      const current = await readCollection(shop, accessToken, update.id);
      if (!current || current.handle !== update.handle) {
        return res.status(409).json({ type: 'about:blank', title: `Collection drift detected for ${update.handle}`, status: 409 });
      }
      collectionOriginals.set(update.id, current.seo);
      const isApplied = current.seo?.title === update.title && current.seo?.description === update.description;
      const isBaseline = current.seo?.title == null && current.seo?.description == null;
      if (!isApplied && !isBaseline) {
        return res.status(409).json({ type: 'about:blank', title: `Collection SEO drift detected for ${update.handle}`, status: 409 });
      }
    }

    for (const update of SEO_UPDATES) {
      const current = originals.get(update.id);
      if (current?.title === update.title && current?.description === update.description) continue;
      const product = await updateProduct(shop, accessToken, update.id, { title: update.title, description: update.description });
      changed.push(update.id);
      if (product.seo?.title !== update.title || product.seo?.description !== update.description) {
        throw new Error(`SEO verification failed for ${update.handle}`);
      }
    }
    for (const update of COLLECTION_SEO_UPDATES) {
      const current = collectionOriginals.get(update.id);
      if (current?.title === update.title && current?.description === update.description) continue;
      const collection = await updateCollection(shop, accessToken, update.id, { title: update.title, description: update.description });
      changedCollections.push(update.id);
      if (collection.seo?.title !== update.title || collection.seo?.description !== update.description) {
        throw new Error(`Collection SEO verification failed for ${update.handle}`);
      }
    }
    return res.status(200).json({
      shop,
      products: { applied: changed.length, verified: SEO_UPDATES.length },
      collections: { applied: changedCollections.length, verified: COLLECTION_SEO_UPDATES.length },
      rollbackAvailable: true,
    });
  } catch (error) {
    let rollbackConfirmed = true;
    for (const id of changedCollections.reverse()) {
      try {
        const original = collectionOriginals.get(id) ?? { title: null, description: null };
        const restored = await updateCollection(shop, accessToken, id, original);
        rollbackConfirmed = rollbackConfirmed
          && restored.seo?.title === original.title
          && restored.seo?.description === original.description;
      } catch {
        rollbackConfirmed = false;
      }
    }
    for (const id of changed.reverse()) {
      try {
        const original = originals.get(id) ?? { title: null, description: null };
        const restored = await updateProduct(shop, accessToken, id, original);
        rollbackConfirmed = rollbackConfirmed
          && restored.seo?.title === original.title
          && restored.seo?.description === original.description;
      } catch {
        rollbackConfirmed = false;
      }
    }
    return res.status(502).json({
      type: 'about:blank',
      title: 'Catalog SEO update failed',
      status: 502,
      changedBeforeFailure: changed.length,
      rollbackConfirmed,
      detail: error instanceof Error ? error.message : 'Unknown error',
    });
  }
};
