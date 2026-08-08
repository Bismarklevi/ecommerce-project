# Kaira — Next.js Storefront

A Next.js 16 (App Router) storefront styled as an editorial womenswear
boutique, built to replace the frontend of an existing Django REST project.

Currently running on **mock data** (`src/lib/mock-data.ts`) so the UI can be
reviewed and iterated on without the backend running. Swapping in the real
API is intentionally a small, contained change — see below.

## Getting started

```bash
npm install
npm run dev
```

Open http://localhost:3000. Google Fonts (Fraunces, Inter, JetBrains Mono)
are fetched at build time, so you'll need normal internet access the first
time you run `npm run dev` / `npm run build`.

## Project structure

```
src/
  app/
    page.tsx              Home (hero, category rail, featured products)
    shop/                 Shop grid with category filter + sort
    product/[slug]/       Product detail + add-to-cart
    cart/                 Cart page (localStorage-backed for now)
  components/
    SiteHeader.tsx         Nav + live cart count
    SiteFooter.tsx
    ProductCard.tsx         Product card w/ garment-tag signature element
  lib/
    types.ts                Types shaped to match the Django DRF response shapes
    mock-data.ts             Placeholder catalog (14 products from your photos)
    api.ts                   Swap this file to wire up the real API
    cart-context.tsx         Client cart state (localStorage) — swap for /api/cart/
public/images/                Product photography from store-images.zip
```

## Wiring up the real Django API

Everything reads through `src/lib/api.ts`. Each function currently returns
mock data; replace the body with a `fetch()` call against your DRF routes and
nothing else in the app needs to change, since components only depend on the
types in `src/lib/types.ts`.

Based on the `urls.py` you shared:

| `api.ts` function | Django route |
|---|---|
| `getProducts()` | `GET /api/products/` |
| `getProductBySlug()` | `GET /api/products/{slug}/` |
| `getCategories()` | `GET /api/categories/` |

Suggested steps:

1. Add `NEXT_PUBLIC_API_BASE_URL` to `.env.local`.
2. In `api.ts`, replace each function body with a `fetch()` call against
   `${BASE_URL}/api/...`, and confirm the JSON shape matches
   `src/lib/types.ts` (adjust the types if your serializers differ — e.g. if
   `price` isn't a string, or images come back as a single field rather than
   an array).
3. For the cart, decide whether to keep the current localStorage cart (guest
   cart, no login required) or switch `cart-context.tsx` to call
   `/api/cart/` and `/api/cart/items/` directly. Given your backend already
   has auth (`/api/auth/login/`, `/api/me/`), you'll likely want carts tied to
   a logged-in user plus a guest fallback.
4. Checkout currently ends at a static summary. Your backend already has
   `CheckoutView` at `/api/orders/{id}/checkout/` and a Paystack webhook —
   the next step would be creating an order from the cart, then redirecting
   to Paystack.

## Not yet built

- Auth (login/register) pages
- Checkout flow (payment)
- Wishlist, addresses, order history
- Search

These map to routes your Django API already exposes
(`/api/auth/*`, `/api/wishlist/`, `/api/addresses/`, `/api/orders/`).
