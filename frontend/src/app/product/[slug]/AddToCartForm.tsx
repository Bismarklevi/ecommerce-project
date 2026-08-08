"use client";

import { useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useCart } from "@/lib/cart-context";
import { Product } from "@/lib/types";

export default function AddToCartForm({ product }: { product: Product }) {
  const { addItem } = useCart();
  const router = useRouter();
  const pathname = usePathname();
  const [size, setSize] = useState<string | null>(
    product.sizes.length === 1 ? product.sizes[0] : null,
  );
  const [error, setError] = useState<string | null>(null);
  const [added, setAdded] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const selectedVariant = product.variants.find((v) => v.size === size);

  async function handleAdd() {
    if (!size) {
      setError("select a size");
      return;
    }
    if (!selectedVariant) {
      setError("that size is not available");
      return;
    }
    if (!selectedVariant.inStock) {
      setError("that size is sold out");
      return;
    }

    setSubmitting(true);
    setError(null);
    const result = await addItem(selectedVariant.id, 1);
    setSubmitting(false);

    if (!result.ok) {
      if (result.detail.toLowerCase().includes("sign in")) {
        router.push(`/login?next=${encodeURIComponent(pathname)}`);
        return;
      }
      setError(result.detail);
      return;
    }

    setAdded(true);
    setTimeout(() => setAdded(false), 2000);
  }

  return (
    <div>
      {product.sizes.length > 1 && (
        <fieldset className="mb-6">
          <legend className="mb-3 text-xs font-bold uppercase tracking-[0.15em] text-muted">
            Size {error && <span className="text-wine normal-case">- {error}</span>}
          </legend>
          <div className="flex flex-wrap gap-2">
            {product.variants.map((v) => (
              <button
                key={v.id}
                type="button"
                onClick={() => {
                  setSize(v.size);
                  setError(null);
                }}
                disabled={!v.inStock}
                aria-pressed={size === v.size}
                className={`focus-ring min-h-11 min-w-12 border px-3 text-sm font-bold transition-colors ${
                  size === v.size
                    ? "border-ink bg-ink text-bone"
                    : "border-hairline bg-bone text-ink hover:border-ink"
                } ${!v.inStock ? "pointer-events-none opacity-30 line-through" : ""}`}
              >
                {v.size}
              </button>
            ))}
          </div>
        </fieldset>
      )}

      <div className="flex flex-col gap-3 sm:flex-row">
        <button
          type="button"
          onClick={handleAdd}
          disabled={!product.in_stock || submitting}
          className="site-btn focus-ring flex-1 disabled:pointer-events-none disabled:opacity-40"
        >
          {!product.in_stock
            ? "Sold out"
            : submitting
              ? "Adding..."
              : added
                ? "Added to cart"
                : "Add to cart"}
        </button>
        {added && (
          <button
            type="button"
            onClick={() => router.push("/cart")}
            className="site-btn-outline focus-ring"
          >
            View cart
          </button>
        )}
      </div>
    </div>
  );
}
