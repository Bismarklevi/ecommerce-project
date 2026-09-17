import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import ProductCard from "@/components/ProductCard";
import { mapProduct, type BackendProduct } from "@/lib/api";
import { backendFetch, unwrapList } from "@/lib/backend";
import { getAuthToken } from "@/lib/session";

export const metadata: Metadata = { title: "Saved items" };
export const dynamic = "force-dynamic";

interface WishlistItem {
  id: number;
  product: number;
  product_detail: BackendProduct;
}

export default async function SavedPage() {
  const token = await getAuthToken();
  if (!token) {
    redirect("/login?next=/saved");
  }

  const items = await backendFetch<WishlistItem[] | { results: WishlistItem[] }>("/api/wishlist/", {
    token,
  })
    .then(unwrapList)
    .catch(() => [] as WishlistItem[]);

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <p className="section-eyebrow mb-3">Account</p>
      <h1 className="section-title mb-3">Saved items</h1>
      <p className="mb-10 max-w-lg text-sm leading-7 text-muted">
        Everything you&apos;ve hearted, in one place. Tap the heart again to take something off the
        list.
      </p>

      {items.length === 0 ? (
        <div className="border border-hairline py-16 text-center">
          <p className="text-xl font-extrabold uppercase">Nothing saved yet</p>
          <p className="mt-3 text-sm text-muted">
            Use the heart on any product to keep it here for later.
          </p>
          <Link href="/shop" className="site-btn focus-ring mt-7">
            Shop the edit
          </Link>
        </div>
      ) : (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {items.map((item) => (
            /* The wishlist row id, not the product id, is what the card needs
               to unsave -- DELETE /api/wishlist/{id} addresses the row. */
            <ProductCard
              key={item.id}
              product={mapProduct(item.product_detail)}
              initialSavedId={item.id}
            />
          ))}
        </div>
      )}
    </div>
  );
}
