import { redirect } from "next/navigation";
import Link from "next/link";
import { backendFetch, unwrapList } from "@/lib/backend";
import { formatPrice } from "@/lib/currency";
import { getAuthToken } from "@/lib/session";
import type { Order } from "@/lib/types";

export const dynamic = "force-dynamic";

const STATUS_LABELS: Record<string, string> = {
  pending: "Pending payment",
  paid: "Paid",
  processing: "Processing",
  shipped: "Shipped",
  delivered: "Delivered",
  completed: "Completed",
  cancelled: "Cancelled",
  returned: "Returned",
};

export default async function AccountPage() {
  const token = await getAuthToken();
  if (!token) {
    redirect("/login?next=/account");
  }

  const orders = await backendFetch<Order[] | { results: Order[] }>("/api/orders/", { token })
    .then(unwrapList)
    .catch(() => [] as Order[]);

  return (
    <div className="mx-auto max-w-5xl px-4 py-12 sm:px-6 lg:px-8">
      <p className="section-eyebrow mb-3">Account</p>
      <h1 className="section-title mb-10">Your orders</h1>

      {orders.length === 0 ? (
        <div className="border border-hairline py-16 text-center">
          <p className="text-xl font-extrabold uppercase">No orders yet</p>
          <p className="mt-3 text-sm text-muted">Once you place an order, it will show up here.</p>
          <Link href="/shop" className="site-btn focus-ring mt-7">
            Shop the edit
          </Link>
        </div>
      ) : (
        <ul className="divide-y divide-hairline border-y border-hairline">
          {orders.map((order) => (
            <li key={order.id} className="flex flex-wrap items-center justify-between gap-4 py-6">
              <div>
                <p className="text-lg font-extrabold uppercase">Order #{order.id}</p>
                <p className="mt-2 text-xs font-bold uppercase tracking-[0.12em] text-muted">
                  {new Date(order.created_at).toLocaleDateString()} / {order.item_count} item
                  {order.item_count === 1 ? "" : "s"} /{" "}
                  {STATUS_LABELS[order.status] || order.status}
                </p>
              </div>
              <span className="text-sm font-bold">{formatPrice(order.total_amount)}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
