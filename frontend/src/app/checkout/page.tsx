"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCart } from "@/lib/cart-context";
import { Skeleton, SkeletonScreen } from "@/components/Skeleton";
import { formatPrice } from "@/lib/currency";

export default function CheckoutPage() {
  const router = useRouter();
  const { cart, loading, signedIn } = useCart();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [promoInput, setPromoInput] = useState("");
  const [promo, setPromo] = useState<{ code: string; discount: number } | null>(null);
  const [promoError, setPromoError] = useState<string | null>(null);
  const [promoBusy, setPromoBusy] = useState(false);

  useEffect(() => {
    if (signedIn === false) router.replace("/login?next=/checkout");
  }, [signedIn, router]);

  if (loading || signedIn === undefined) {
    return (
      <SkeletonScreen className="mx-auto max-w-3xl px-4 py-10 sm:px-6 lg:px-8">
        <Skeleton className="mb-8 h-9 w-56" />
        <div className="space-y-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
        <Skeleton className="mt-8 h-40 w-full" />
        <Skeleton className="mt-8 h-14 w-full rounded-full" />
      </SkeletonScreen>
    );
  }

  const items = cart?.items ?? [];
  if (items.length === 0) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 text-center sm:px-6 lg:px-8">
        <h1 className="section-title mb-6">Your bag is empty</h1>
        <Link href="/shop" className="site-btn focus-ring">
          Shop the edit
        </Link>
      </div>
    );
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    const formData = new FormData(event.currentTarget);
    const orderPayload = {
      items: items.map((item) => ({
        product_variant_id: item.product_variant.id,
        quantity: item.quantity,
      })),
      shipping_name: formData.get("name"),
      shipping_email: formData.get("email"),
      shipping_phone: formData.get("phone"),
      shipping_address: formData.get("address"),
    };

    try {
      const orderResponse = await fetch("/api/orders", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(orderPayload),
      });
      const order = await orderResponse.json();
      if (!orderResponse.ok) {
        setError(
          typeof order === "object"
            ? Object.values(order).flat().join(" ")
            : "Could not place order.",
        );
        setSubmitting(false);
        return;
      }

      const checkoutResponse = await fetch(`/api/orders/${order.id}/checkout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(promo ? { coupon_code: promo.code } : {}),
      });
      const checkout = await checkoutResponse.json();
      if (!checkoutResponse.ok) {
        setError(checkout.detail || "Could not start payment. Your order was saved as pending.");
        setSubmitting(false);
        return;
      }

      window.location.href = checkout.authorization_url;
    } catch {
      setError("Could not reach the server. Please try again.");
      setSubmitting(false);
    }
  }

  const subtotal = Number(cart?.subtotal ?? 0);
  const total = Math.max(0, subtotal - (promo?.discount ?? 0));

  async function applyPromo() {
    const code = promoInput.trim();
    if (!code) return;
    setPromoBusy(true);
    setPromoError(null);
    try {
      const response = await fetch("/api/promotions/validate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code, order_subtotal: subtotal.toFixed(2) }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        setPromo(null);
        setPromoError(
          typeof data === "object" && data
            ? Object.values(data).flat().join(" ")
            : "That code didn't work.",
        );
        return;
      }
      setPromo({ code: data.code, discount: Number(data.discount_amount) });
    } catch {
      setPromoError("Could not check that code. Please try again.");
    } finally {
      setPromoBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
      <p className="section-eyebrow mb-3">Checkout</p>
      <h1 className="section-title mb-8">Delivery details</h1>

      <div className="grid gap-10 lg:grid-cols-[1fr_22rem]">
        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          <div>
            <label
              htmlFor="name"
              className="mb-2 block text-xs font-bold uppercase tracking-[0.15em] text-muted"
            >
              Full name
            </label>
            <input id="name" name="name" required className="field-input" />
          </div>
          <div>
            <label
              htmlFor="email"
              className="mb-2 block text-xs font-bold uppercase tracking-[0.15em] text-muted"
            >
              Email
            </label>
            <input id="email" name="email" type="email" required className="field-input" />
          </div>
          <div>
            <label
              htmlFor="phone"
              className="mb-2 block text-xs font-bold uppercase tracking-[0.15em] text-muted"
            >
              Phone
            </label>
            <input id="phone" name="phone" required className="field-input" />
          </div>
          <div>
            <label
              htmlFor="address"
              className="mb-2 block text-xs font-bold uppercase tracking-[0.15em] text-muted"
            >
              Delivery address
            </label>
            <textarea id="address" name="address" required rows={4} className="field-input" />
          </div>

          {error && (
            <p className="border border-wine bg-wine/10 px-4 py-3 text-sm text-wine">{error}</p>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="site-btn focus-ring disabled:pointer-events-none disabled:opacity-40"
          >
            {submitting ? "Redirecting to payment..." : "Continue to payment"}
          </button>
          <p className="text-xs text-muted">
            You will be redirected to Paystack to complete payment securely.
          </p>
        </form>

        <aside>
          <div className="sticky top-8 border border-hairline p-6">
            <h2 className="mb-6 text-xl font-extrabold uppercase">Order summary</h2>
            <ul className="mb-6 space-y-4 text-sm">
              {items.map((item) => (
                <li key={item.id} className="flex justify-between gap-3">
                  <span className="text-muted">
                    {item.product_name} <span className="text-muted">x {item.quantity}</span>
                  </span>
                  <span className="whitespace-nowrap font-bold">
                    {formatPrice(item.line_total)}
                  </span>
                </li>
              ))}
            </ul>
            {/* Promo code. Applying only previews the discount; the code is
                redeemed by the checkout call itself, so nothing is consumed if
                the shopper stops here. */}
            <div className="mb-6 border-t border-hairline pt-6">
              <label
                htmlFor="promo"
                className="mb-2 block text-xs font-bold uppercase tracking-[0.15em] text-muted"
              >
                Promo code
              </label>
              <div className="flex gap-2">
                <input
                  id="promo"
                  value={promoInput}
                  onChange={(e) => setPromoInput(e.target.value)}
                  disabled={Boolean(promo)}
                  className="field-input min-w-0 flex-1 uppercase disabled:opacity-60"
                />
                {promo ? (
                  <button
                    type="button"
                    onClick={() => {
                      setPromo(null);
                      setPromoInput("");
                    }}
                    className="site-btn-outline focus-ring shrink-0"
                  >
                    Remove
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={applyPromo}
                    disabled={promoBusy || !promoInput.trim()}
                    className="site-btn focus-ring shrink-0 disabled:pointer-events-none disabled:opacity-40"
                  >
                    {promoBusy ? "..." : "Apply"}
                  </button>
                )}
              </div>
              {promoError && <p className="mt-2 text-xs text-wine">{promoError}</p>}
            </div>

            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-muted">Subtotal</dt>
                <dd>{formatPrice(subtotal)}</dd>
              </div>
              {promo && (
                <div className="flex justify-between text-wine">
                  <dt>Promo {promo.code}</dt>
                  <dd>-{formatPrice(promo.discount)}</dd>
                </div>
              )}
            </dl>
            <div className="mt-4 flex justify-between border-t border-hairline pt-6 text-lg font-extrabold uppercase">
              <span>Total</span>
              <span>{formatPrice(total)}</span>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
