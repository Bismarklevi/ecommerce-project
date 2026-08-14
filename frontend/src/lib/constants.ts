// Used whenever a product has no uploaded/linked photo -- keeps every image
// slot filled with something on-brand instead of a broken box or a crash
// (Product.images can legitimately be an empty array; see lib/api.ts).
export const PLACEHOLDER_IMAGE = "/images/placeholder-product.svg";

// A misconfigured CLOUDFLARE_R2_CUSTOM_DOMAIN (pasted with its own
// "https://" prefix still attached, rather than a bare hostname) can make
// the backend emit "https://https://host/..." image URLs -- next/image
// rejects those outright ("hostname \"https\" is not configured") instead
// of degrading gracefully. Fixed at the backend too, but every place an
// image URL from the API reaches next/image normalizes here as well, so a
// product photo never crashes the page regardless of which backend
// configuration is actually running.
export function normalizeImageUrl(url: string): string {
  if (!url) return url;
  return url.replace(/^(https?:\/\/)https?:\/\//, "$1");
}
