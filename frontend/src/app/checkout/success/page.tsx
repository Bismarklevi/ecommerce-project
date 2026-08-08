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
        This usually takes a few seconds. Refresh in a moment if this does not update.
      </p>
    </div>
  );
}

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
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true);
    setNotFound(false);
    fetch(`/api/orders/${orderId}`)
      .then((response) => (response.ok ? response.json() : Promise.reject()))
      .then((data) => setOrder(data))
      .catch(() => setNotFound(true))
      .finally(() => setLoading(false));
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
