import { Category, Product, ProductVariant } from "./types";
import { normalizeImageUrl } from "./constants";

// ---------------------------------------------------------------------------
// Real Django backend integration. Every function below fetches from the
// REST API (see backend/project/urls.py -- DRF router + drf-spectacular
// schema at /api/schema/). The shapes the backend actually returns
// (base_price, variants, images[], primary_image_url, is_featured -- see
// products/serializers.py) don't exactly match this frontend's Product type
// (a flat sizes[] array, a single price, a look_number for the swing-tag
// motif), so mapProduct()/mapCategory() below are the one seam that
// reconciles the two. Components never see a raw backend shape.
// ---------------------------------------------------------------------------

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000").replace(
  /\/$/,
  "",
);

function resolveUrl(path: string): string {
  if (path.startsWith("http")) return path;

  // In the browser, NEXT_PUBLIC_API_BASE_URL is whatever host the site was
  // *built* with in mind -- for local dev that's 127.0.0.1:8000, which is
  // the visitor's OWN machine, not the server's. That only ever worked for
  // a developer testing on the exact same machine as the backend; anyone
  // else (a different device, a real deployment) gets a hard "failed to
  // fetch" -- which is exactly the reported "products returning errors" bug.
  // Server Components don't have this problem (this same function, called
  // during SSR, has no `window` and fetches Django directly, server-to-
  // server) -- so only browser-side calls get redirected through the
  // same-origin proxy, which the browser can always reach.
  if (typeof window !== "undefined") {
    const proxied = `/api/catalog${path.startsWith("/") ? path : `/${path}`}`;
    // Next's catch-all route match normalizes away a trailing slash right
    // before the query string (redirects .../products/?x to .../products?x)
    // -- stripping it here avoids that extra redirect hop on every request.
    return proxied.replace(/\/(\?|$)/, "$1");
  }
  return `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

async function fetchJSON<T>(path: string): Promise<T> {
  const url = resolveUrl(path);
  let response: Response;

  try {
    response = await fetch(url, { cache: "no-store" });
  } catch (cause) {
    throw new Error(
      `Network request to ${url} failed: ${cause instanceof Error ? cause.message : String(cause)}`,
    );
  }

  if (!response.ok) {
    const text = await response.text().catch(() => "");
    let details = text;
    try {
      const json = JSON.parse(text);
      details = typeof json === "string" ? json : JSON.stringify(json);
    } catch {
      // Leave details as plain text if it is not valid JSON.
    }

    throw new Error(
      `Request to ${url} failed with ${response.status} ${response.statusText}${
        details ? `: ${details}` : ""
      }`,
    );
  }

  return response.json();
}

// DRF list endpoints in this project return a bare array (no pagination
// configured) -- see products/views.py -- but this guards against that
// changing later without every call site needing to know.
function unwrapList<T>(payload: T[] | { results: T[] }): T[] {
  return Array.isArray(payload) ? payload : payload.results;
}

interface BackendCategory {
  id: number;
  slug: string;
  name: string;
  image: string;
}

interface BackendProductImage {
  id: number;
  image: string;
  alt_text: string;
}

interface BackendProductVariant {
  id: number;
  size: string;
  stock_quantity: number;
}

interface BackendProduct {
  id: number;
  slug: string;
  name: string;
  short_description: string;
  description: string;
  base_price: string;
  category: BackendCategory;
  images: BackendProductImage[];
  variants: BackendProductVariant[];
  primary_image_url: string;
  is_featured: boolean;
}

function mapCategory(raw: BackendCategory): Category {
  return { id: raw.id, slug: raw.slug, name: raw.name, image: normalizeImageUrl(raw.image || "") };
}

function mapProduct(raw: BackendProduct): Product {
  const images =
    raw.images.length > 0
      ? raw.images.map((img) => ({
          id: img.id,
          image: normalizeImageUrl(img.image),
          alt: img.alt_text || raw.name,
        }))
      : raw.primary_image_url
        ? [{ id: 0, image: normalizeImageUrl(raw.primary_image_url), alt: raw.name }]
        : [];

  // One variant per size in this catalog (color is always "Default" -- see
  // seed_kaira_catalog.py) -- dedupe just in case that ever changes, keeping
  // the first (lowest-stock-risk-free) variant id for that size.
  const seenSizes = new Set<string>();
  const variants: ProductVariant[] = [];
  for (const v of raw.variants) {
    if (seenSizes.has(v.size)) continue;
    seenSizes.add(v.size);
    variants.push({ id: v.id, size: v.size, inStock: v.stock_quantity > 0 });
  }

  return {
    id: raw.id,
    slug: raw.slug,
    name: raw.name,
    description: raw.description || raw.short_description,
    price: raw.base_price,
    compare_at_price: null, // no discount-pricing concept in the backend yet
    category: mapCategory(raw.category),
    images,
    sizes: variants.map((v) => v.size),
    variants,
    fabric: "", // not modeled on the backend -- product detail page hides this row when empty
    in_stock: raw.variants.some((v) => v.stock_quantity > 0),
    look_number: String(raw.id).padStart(3, "0"),
    is_new: raw.is_featured,
  };
}

export async function getProducts(params?: {
  category?: string;
  sort?: "featured" | "price-asc" | "price-desc" | "new";
  search?: string;
}): Promise<Product[]> {
  const query = new URLSearchParams();
  if (params?.category && params.category !== "all") {
    query.set("category", params.category);
  }
  if (params?.search) {
    query.set("search", params.search);
  }
  switch (params?.sort) {
    case "price-asc":
      query.set("ordering", "base_price");
      break;
    case "price-desc":
      query.set("ordering", "-base_price");
      break;
    case "new":
      query.set("ordering", "-created_at");
      break;
    default:
      break;
  }

  const qs = query.toString();
  const payload = await fetchJSON<BackendProduct[] | { results: BackendProduct[] }>(
    `/api/products/${qs ? `?${qs}` : ""}`,
  );
  return unwrapList(payload).map(mapProduct);
}

export async function getProductBySlug(slug: string): Promise<Product | undefined> {
  try {
    const raw = await fetchJSON<BackendProduct>(`/api/products/${encodeURIComponent(slug)}/`);
    return mapProduct(raw);
  } catch {
    return undefined;
  }
}

export async function getRelatedProducts(product: Product, limit = 4): Promise<Product[]> {
  const payload = await fetchJSON<BackendProduct[] | { results: BackendProduct[] }>(
    `/api/products/?category=${encodeURIComponent(product.category.slug)}`,
  );
  return unwrapList(payload)
    .filter((p) => p.id !== product.id)
    .slice(0, limit)
    .map(mapProduct);
}

export async function getCategories(): Promise<Category[]> {
  const payload = await fetchJSON<BackendCategory[] | { results: BackendCategory[] }>(
    "/api/categories/",
  );
  return unwrapList(payload).map(mapCategory);
}

export async function getFeaturedProducts(limit = 4): Promise<Product[]> {
  const payload = await fetchJSON<BackendProduct[] | { results: BackendProduct[] }>(
    "/api/products/?is_featured=true",
  );
  return unwrapList(payload).slice(0, limit).map(mapProduct);
}
