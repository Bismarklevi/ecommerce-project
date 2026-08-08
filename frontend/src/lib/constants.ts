// Used whenever a product has no uploaded/linked photo -- keeps every image
// slot filled with something on-brand instead of a broken box or a crash
// (Product.images can legitimately be an empty array; see lib/api.ts).
export const PLACEHOLDER_IMAGE = "/images/placeholder-product.svg";
