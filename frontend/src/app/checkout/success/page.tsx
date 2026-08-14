"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { formatPrice } from "@/lib/currency";
import type { Order } from "@/lib/types";

function StatusBanner({ paymentStatus }: { paymentStatus: string }) {
  if (paymentStatus === "paid") {
    return (
      <div className="border border-sage bg-sage/20 p-6">
        <p className="mb-1 text-xl font-extrabold uppercase">Payment received - thank you</p>
        <p className="text-sm text-muted">We are preparing your order for delivery.</p>
      </div>
    );
  }
  if (paymentStatus === "failed") {
    return (
      <div className="border border-wine bg-wine/10 p-6">
        <p className="mb-1 text-xl font-extrabold uppercase">Payment did not go through</p>
        <p className="text-sm text-muted">
          No money left your account. You can try again from your bag.
        </p>
      </div>
    );
  }
  return (
    <div className="border border-hairline bg-bone-2 p-6">
      <p className="mb-1 text-xl font-extrabold uppercase">Confirming your payment...</p>
      <p className="text-sm text-muted">
        This usually takes just a few seconds -- this page will update automatically.
      </p>
    </div>
  );
}

// Paystack's webhook can (and does) arrive a few seconds after the browser
// is redirected back here -- a single fetch on page load can easily land in
// that gap and show "still confirming" even though payment already went
// through. Poll a bounded number of times with backoff instead of relying
// on the customer to manually refresh.
const POLL_INTERVALS_MS = [1500, 2000, 2500, 3000, 4000, 5000, 6000]; // ~24s total

function CheckoutSuccessContent() {
  const searchParams = useSearchParams();
  const orderId = searchParams.get("order_id");
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(Boolean(orderId));
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    if (!orderId) {
      return;
    }
    let cancelled = false;
    let attempt = 0;

    async function poll() {
      if (attempt === 0) {
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setLoading(true);
        setNotFound(false);
      }
      try {
        const response = await fetch(`/api/orders/${orderId}`);
        if (!response.ok) throw new Error("not ok");
        const data: Order = await response.json();
        if (cancelled) return;
        setOrder(data);
        setLoading(false);

        // Still waiting on the webhook and haven't exhausted the poll
        // schedule yet -- try again rather than leaving the customer
        // staring at "Confirming your payment..." with no next step.
        if (data.payment_status === "pending" && attempt < POLL_INTERVALS_MS.length) {
          const delay = POLL_INTERVALS_MS[attempt];
          attempt += 1;
          setTimeout(poll, delay);
        }
      } catch {
        if (!cancelled) {
          setNotFound(true);
          setLoading(false);
        }
      }
    }

    poll();
    return () => {
      cancelled = true;
    };
  }, [orderId]);

  if (!orderId) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-24 text-center sm:px-6 lg:px-8">
        <h1 className="section-title mb-6">We could not find that order</h1>
        <Link href="/account" className="site-btn focus-ring">
          View your orders
        </Link>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-24 text-center text-muted sm:px-6 lg:px-8">
        Loading...
      </div>
    );
  }

  if (notFound || !order) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-24 text-center sm:px-6 lg:px-8">
        <h1 className="section-title mb-6">We could not find that order</h1>
        <Link href="/account" className="site-btn focus-ring">
          View your orders
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
      <p className="section-eyebrow mb-3">Order #{order.id}</p>
      <h1 className="section-title mb-8">Order confirmation</h1>

      <StatusBanner paymentStatus={order.payment_status} />

      <div className="mt-8 border-t border-hairline pt-8">
        <ul className="mb-6 space-y-4 text-sm">
          {order.items.map((item) => (
            <li key={item.id} className="flex justify-between gap-3">
              <span className="text-muted">
                {item.product_name}{" "}
                <span className="text-muted">
                  ({item.size}) x {item.quantity}
                </span>
              </span>
              <span className="whitespace-nowrap font-bold">{formatPrice(item.line_total)}</span>
            </li>
          ))}
        </ul>
        <div className="flex justify-between border-t border-hairline pt-4 text-lg font-extrabold uppercase">
          <span>Total</span>
          <span>{formatPrice(order.total_amount)}</span>
        </div>
      </div>

      <Link href="/shop" className="site-btn focus-ring mt-10">
        Continue shopping
      </Link>
    </div>
  );
}

export default function CheckoutSuccessPage() {
  return (
    <Suspense
      fallback={
        <div className="mx-auto max-w-2xl px-4 py-24 text-center text-muted sm:px-6 lg:px-8">
          Loading...
        </div>
      }
    >
      <CheckoutSuccessContent />
    </Suspense>
  );
}
