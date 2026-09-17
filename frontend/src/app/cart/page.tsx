"use client";

import Image from "next/image";
import Link from "next/link";
import { useCart } from "@/lib/cart-context";
import { formatPrice } from "@/lib/currency";
import { PLACEHOLDER_IMAGE, normalizeImageUrl } from "@/lib/constants";
import { Skeleton, SkeletonScreen } from "@/components/Skeleton";

const FREE_SHIPPING_THRESHOLD = 500;

export default function CartPage() {
  const { cart, loading, signedIn, updateQuantity, removeItem } = useCart();

  if (loading) {
    return (
      <SkeletonScreen className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
        <Skeleton className="h-3 w-20" />
        <Skeleton className="mb-8 mt-3 h-9 w-48" />
        <div className="space-y-6">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-28 w-full" />
          ))}
        </div>
        <Skeleton className="mt-10 h-40 w-full" />
      </SkeletonScreen>
    );
  }

  if (signedIn === false) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 text-center sm:px-6 lg:px-8">
        <p className="section-eyebrow mb-3">Your bag</p>
        <h1 className="section-title">Sign in to see your bag</h1>
        <p className="mx-auto mt-5 max-w-md text-sm leading-7 text-muted">
          Your bag is tied to your account, so it is there whenever you come back.
        </p>
        <Link href="/login?next=/cart" className="site-btn focus-ring mt-8">
          Sign in
        </Link>
      </div>
    );
  }

  const items = cart?.items ?? [];
  const subtotal = Number(cart?.subtotal ?? 0);

  if (items.length === 0) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 text-center sm:px-6 lg:px-8">
        <p className="section-eyebrow mb-3">Your bag</p>
        <h1 className="section-title">Your cart is empty</h1>
        <p className="mx-auto mt-5 max-w-md text-sm leading-7 text-muted">
          Nothing added yet - browse the current edit and find something worth carrying home.
        </p>
        <Link href="/shop" className="site-btn focus-ring mt-8">
          Shop with us
        </Link>
      </div>
    );
  }

  const remaining = Math.max(0, FREE_SHIPPING_THRESHOLD - subtotal);

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
      <p className="section-eyebrow mb-3">
        {items.length} item{items.length === 1 ? "" : "s"}
      </p>
      <h1 className="section-title mb-8">Shopping cart</h1>

      {remaining > 0 ? (
        <div className="mb-8 border border-hairline px-5 py-4 text-sm text-muted">
          Add <span className="font-bold text-ink">{formatPrice(remaining)}</span> more for free
          shipping.
        </div>
      ) : (
        <div className="mb-8 border border-sage bg-sage/20 px-5 py-4 text-sm text-muted">
          You have unlocked free shipping.
        </div>
      )}

      <div className="grid gap-10 lg:grid-cols-[1fr_22rem]">
        <ul className="divide-y divide-hairline border-y border-hairline">
          {items.map((item) => (
            <li key={item.id} className="flex gap-5 py-6">
              <Link
                href={`/product/${item.product_slug}`}
                className="focus-ring relative aspect-[3/4] w-24 shrink-0 bg-bone-2 sm:w-32"
              >
                <Image
                  src={normalizeImageUrl(item.product_image) || PLACEHOLDER_IMAGE}
                  alt={item.product_name}
                  fill
                  sizes="140px"
                  className="object-cover"
                />
              </Link>

              <div className="flex flex-1 flex-col">
                <div className="flex justify-between gap-4">
                  <div>
                    <Link
                      href={`/product/${item.product_slug}`}
                      className="focus-ring text-lg font-extrabold uppercase leading-snug hover:text-wine"
                    >
                      {item.product_name}
                    </Link>
                    <p className="mt-2 text-xs font-bold uppercase tracking-[0.14em] text-muted">
                      Size {item.product_variant.size}
                    </p>
                  </div>
                  <p className="whitespace-nowrap text-sm font-bold">
                    {formatPrice(item.line_total)}
                  </p>
                </div>

                <div className="mt-auto flex items-center justify-between pt-5">
                  <div className="flex items-center border border-hairline">
                    <button
                      onClick={() => updateQuantity(item.id, item.quantity - 1)}
                      disabled={item.quantity <= 1}
                      className="focus-ring flex h-9 w-9 items-center justify-center hover:bg-bone-2 disabled:opacity-30"
                      aria-label="Decrease quantity"
                    >
                      -
                    </button>
                    <span className="w-9 text-center text-sm font-bold" aria-live="polite">
                      {item.quantity}
                    </span>
                    <button
                      onClick={() => updateQuantity(item.id, item.quantity + 1)}
                      className="focus-ring flex h-9 w-9 items-center justify-center hover:bg-bone-2"
                      aria-label="Increase quantity"
                    >
                      +
                    </button>
                  </div>
                  <button
                    onClick={() => removeItem(item.id)}
                    className="focus-ring text-xs font-bold uppercase tracking-[0.14em] text-muted underline underline-offset-4 hover:text-wine"
                  >
                    Remove
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>

        <aside>
          <div className="sticky top-8 border border-hairline p-6">
            <h2 className="mb-6 text-xl font-extrabold uppercase">Order summary</h2>
            <dl className="space-y-4 text-sm">
              <div className="flex justify-between">
                <dt className="text-muted">Subtotal</dt>
                <dd className="font-bold">{formatPrice(subtotal)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted">Shipping</dt>
                <dd className="font-bold">{remaining > 0 ? "Calculated at checkout" : "Free"}</dd>
              </div>
            </dl>
            <div className="mt-6 flex justify-between border-t border-hairline pt-6 text-lg font-extrabold uppercase">
              <span>Total</span>
              <span>{formatPrice(subtotal)}</span>
            </div>
            <Link href="/checkout" className="site-btn focus-ring mt-6 w-full">
              Checkout
            </Link>
          </div>
        </aside>
      </div>
    </div>
  );
}
