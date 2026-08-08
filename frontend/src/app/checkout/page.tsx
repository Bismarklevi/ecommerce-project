"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCart } from "@/lib/cart-context";
import { formatPrice } from "@/lib/currency";

export default function CheckoutPage() {
  const router = useRouter();
  const { cart, loading, signedIn } = useCart();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (signedIn === false) router.replace("/login?next=/checkout");
  }, [signedIn, router]);

  if (loading || signedIn === undefined) {
    return <div className="mx-auto max-w-3xl px-4 py-24 text-center text-muted sm:px-6 lg:px-8">Loading...</div>;
  }

  const items = cart?.items ?? [];
  if (items.length === 0) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-24 text-center sm:px-6 lg:px-8">
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
        setError(typeof order === "object" ? Object.values(order).flat().join(" ") : "Could not place order.");
        setSubmitting(false);
        return;
      }

      const checkoutResponse = await fetch(`/api/orders/${order.id}/checkout`, { method: "POST" });
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

  return (
    <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
      <p className="section-eyebrow mb-3">Checkout</p>
      <h1 className="section-title mb-8">Delivery details</h1>

      <div className="grid gap-10 lg:grid-cols-[1fr_22rem]">
        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          <div>
            <label htmlFor="name" className="mb-2 block text-xs font-bold uppercase tracking-[0.15em] text-muted">
              Full name
            </label>
            <input id="name" name="name" required className="field-input" />
          </div>
          <div>
            <label htmlFor="email" className="mb-2 block text-xs font-bold uppercase tracking-[0.15em] text-muted">
              Email
            </label>
            <input id="email" name="email" type="email" required className="field-input" />
          </div>
          <div>
            <label htmlFor="phone" className="mb-2 block text-xs font-bold uppercase tracking-[0.15em] text-muted">
              Phone
            </label>
            <input id="phone" name="phone" required className="field-input" />
          </div>
          <div>
            <label htmlFor="address" className="mb-2 block text-xs font-bold uppercase tracking-[0.15em] text-muted">
              Delivery address
            </label>
            <textarea id="address" name="address" required rows={4} className="field-input" />
          </div>

          {error && <p className="border border-wine bg-wine/10 px-4 py-3 text-sm text-wine">{error}</p>}

          <button
            type="submit"
            disabled={submitting}
            className="site-btn focus-ring disabled:pointer-events-none disabled:opacity-40"
          >
            {submitting ? "Redirecting to payment..." : "Continue to payment"}
          </button>
          <p className="text-xs text-muted">You will be redirected to Paystack to complete payment securely.</p>
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
                  <span className="whitespace-nowrap font-bold">{formatPrice(item.line_total)}</span>
                </li>
              ))}
            </ul>
            <div className="flex justify-between border-t border-hairline pt-6 text-lg font-extrabold uppercase">
              <span>Total</span>
              <span>{formatPrice(subtotal)}</span>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
