"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";
import { Product } from "@/lib/types";
import { formatPrice } from "@/lib/currency";
import { PLACEHOLDER_IMAGE } from "@/lib/constants";
import { useCart } from "@/lib/cart-context";

function HeartIcon({ filled }: { filled: boolean }) {
  return (
    <svg
      aria-hidden="true"
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill={filled ? "#e0244a" : "none"}
      stroke={filled ? "#e0244a" : "currentColor"}
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M12 20.5s-7.5-4.6-7.5-9.6A4.4 4.4 0 0 1 12 8.1a4.4 4.4 0 0 1 7.5 2.8c0 5-7.5 9.6-7.5 9.6Z" />
    </svg>
  );
}

function CartIcon() {
  return (
    <svg
      aria-hidden="true"
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M3 4h2l2.2 10.4a2 2 0 0 0 2 1.6h7.4a2 2 0 0 0 2-1.55L20.5 8H6" />
      <circle cx="10" cy="20" r="1.2" />
      <circle cx="17.5" cy="20" r="1.2" />
    </svg>
  );
}

// initialSavedId: the wishlist row id when the caller already knows the
// product is saved (the /saved page does), so the heart renders filled and
// the first tap removes rather than re-adds.
export default function ProductCard({
  product,
  initialSavedId = null,
}: {
  product: Product;
  initialSavedId?: number | null;
}) {
  const { signedIn, addItem, savedIds, setSavedId } = useCart();
  const router = useRouter();
  const primaryImage = product.images[0];
  const onSale = product.compare_at_price !== null;

  // The reference strip is colour swatches; this catalogue varies by size, so
  // the same slot carries sizes -- and because a size is selected here, the
  // Add to cart button can do the real thing instead of punting to the PDP.
  const firstAvailable = product.variants.find((v) => v.inStock) ?? product.variants[0];
  const [selectedId, setSelectedId] = useState<number | undefined>(firstAvailable?.id);
  const selected = product.variants.find((v) => v.id === selectedId);

  // Shared map first (kept current across every card on the page), then the
  // caller's own knowledge, then "not saved". `in` rather than `??`: a null in
  // the map means "checked and unsaved" and must win over initialSavedId.
  const savedId = product.id in savedIds ? savedIds[product.id] : initialSavedId;
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<"idle" | "adding" | "added">("idle");
  const [addError, setAddError] = useState<string | null>(null);

  const toggleSaved = useCallback(async () => {
    if (busy) return;
    setBusy(true);
    try {
      if (savedId === null) {
        const res = await fetch("/api/wishlist", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ product: product.id }),
        });
        if (res.ok) setSavedId(product.id, (await res.json()).id);
      } else {
        const res = await fetch(`/api/wishlist/${savedId}`, { method: "DELETE" });
        if (res.ok) setSavedId(product.id, null);
      }
    } finally {
      setBusy(false);
    }
  }, [busy, savedId, product.id, setSavedId]);

  const handleAdd = useCallback(async () => {
    if (!selected || status === "adding") return;
    setStatus("adding");
    setAddError(null);
    const result = await addItem(selected.id, 1);
    if (result.ok) {
      setStatus("added");
      setTimeout(() => setStatus("idle"), 1600);
      return;
    }
    setStatus("idle");
    // The cart API answers 401 for a signed-out shopper; send them to sign in
    // rather than failing silently under the cursor. Any other rejection --
    // chiefly the stock check, which this button no longer pre-empts -- belongs
    // under the card, not at the login page.
    if (signedIn === false) {
      router.push("/login");
      return;
    }
    setAddError(result.detail);
  }, [addItem, router, selected, signedIn, status]);

  const saved = savedId !== null;

  return (
    /* Not one wrapping <Link>: the card owns buttons, and interactive elements
       cannot be nested inside an anchor. */
    <article className="flex h-full flex-col rounded-2xl bg-bone p-3 ring-1 ring-hairline transition-shadow hover:shadow-[0_16px_38px_-26px_rgba(62,1,47,0.5)]">
      <Link href={`/product/${product.slug}`} className="focus-ring group block">
        <div className="relative aspect-square overflow-hidden rounded-xl bg-bone-2/60">
          <Image
            src={primaryImage?.image || PLACEHOLDER_IMAGE}
            alt={primaryImage?.alt || product.name}
            fill
            sizes="(min-width: 1280px) 25vw, (min-width: 768px) 33vw, 50vw"
            className="object-cover transition-transform duration-700 ease-out group-hover:scale-[1.03]"
          />
          {product.is_new && (
            <span className="absolute left-3 top-3 rounded-full bg-bone px-3 py-1.5 text-[11px] font-semibold text-ink shadow-[3px_3px_0_0_var(--ink)]">
              New in
            </span>
          )}
        </div>
      </Link>

      {/* Size chips: one outlined as selected, out-of-stock ones disabled. */}
      {product.variants.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5" role="group" aria-label="Choose a size">
          {product.variants.slice(0, 5).map((variant) => {
            const active = variant.id === selectedId;
            return (
              <button
                key={variant.id}
                type="button"
                disabled={!variant.inStock}
                aria-pressed={active}
                onClick={() => setSelectedId(variant.id)}
                className={`focus-ring h-8 min-w-8 rounded-lg border px-2 text-xs font-medium transition-colors ${
                  active
                    ? "border-wine bg-wine/10 text-wine"
                    : "border-hairline text-ink hover:border-ink"
                } disabled:cursor-not-allowed disabled:opacity-35 disabled:line-through`}
              >
                {variant.size}
              </button>
            );
          })}
        </div>
      )}

      <p className="mt-3 text-[11px] font-medium uppercase tracking-[0.14em] text-muted">
        {product.category.name}
      </p>

      <Link href={`/product/${product.slug}`} className="focus-ring mt-1 block">
        <h3 className="font-display text-base leading-snug text-ink">{product.name}</h3>
      </Link>

      <div className="mt-2 flex items-baseline gap-2">
        <span className="text-base font-semibold text-ink">{formatPrice(product.price)}</span>
        {onSale && (
          <span className="text-xs text-muted line-through">
            {formatPrice(product.compare_at_price!)}
          </span>
        )}
      </div>

      <div className="mt-auto flex items-center gap-2 pb-1 pr-1 pt-3">
        <button
          type="button"
          onClick={handleAdd}
          disabled={status === "adding"}
          className="focus-ring inline-flex min-w-0 flex-1 items-center justify-center gap-2 rounded-xl bg-wine px-3 py-3 text-xs font-semibold uppercase tracking-[0.1em] text-[#fefaf1] shadow-[4px_4px_0_0_var(--ink)] transition-all hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0_0_var(--ink)] active:translate-x-[4px] active:translate-y-[4px] active:shadow-[0_0_0_0_var(--ink)] disabled:translate-x-0 disabled:translate-y-0 disabled:cursor-not-allowed disabled:opacity-40 disabled:shadow-none"
        >
          <CartIcon />
          <span className="truncate">{status === "added" ? "Added" : "Add to cart"}</span>
        </button>

        {signedIn === false ? (
          <Link
            href="/login"
            aria-label={`Sign in to save ${product.name}`}
            className="focus-ring flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-hairline bg-bone text-muted shadow-[4px_4px_0_0_var(--wine)] transition-all hover:translate-x-[2px] hover:translate-y-[2px] hover:border-ink hover:text-ink hover:shadow-[2px_2px_0_0_var(--wine)] active:translate-x-[4px] active:translate-y-[4px] active:shadow-[0_0_0_0_var(--wine)]"
          >
            <HeartIcon filled={false} />
          </Link>
        ) : (
          <button
            type="button"
            onClick={toggleSaved}
            disabled={busy}
            aria-pressed={saved}
            aria-label={saved ? `Remove ${product.name} from saved` : `Save ${product.name}`}
            className="focus-ring flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-hairline bg-bone text-muted shadow-[4px_4px_0_0_var(--wine)] transition-all hover:translate-x-[2px] hover:translate-y-[2px] hover:border-ink hover:text-ink hover:shadow-[2px_2px_0_0_var(--wine)] active:translate-x-[4px] active:translate-y-[4px] active:shadow-[0_0_0_0_var(--wine)] disabled:translate-x-0 disabled:translate-y-0 disabled:opacity-50 disabled:shadow-none"
          >
            <HeartIcon filled={saved} />
          </button>
        )}
      </div>

      {addError && (
        <p role="status" className="mt-2 text-xs leading-5 text-wine">
          {addError}
        </p>
      )}
    </article>
  );
}
