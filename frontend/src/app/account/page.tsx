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

interface UserProfile {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  phone_number: string;
  date_joined: string;
}

export default async function AccountPage() {
  const token = await getAuthToken();
  if (!token) {
    redirect("/login?next=/account");
  }

  const [profile, orders] = await Promise.all([
    backendFetch<UserProfile>("/api/me/", { token }).catch(() => null),
    backendFetch<Order[] | { results: Order[] }>("/api/orders/", { token })
      .then(unwrapList)
      .catch(() => [] as Order[]),
  ]);

  const displayName =
    profile && (profile.first_name || profile.last_name)
      ? `${profile.first_name} ${profile.last_name}`.trim()
      : profile?.username;

  return (
    <div className="mx-auto max-w-5xl px-4 py-12 sm:px-6 lg:px-8">
      <p className="section-eyebrow mb-3">Account</p>
      <h1 className="section-title mb-10">Your account</h1>

      {profile && (
        <div className="mb-12 border border-hairline p-6 sm:p-8">
          <p className="mb-6 text-xs font-bold uppercase tracking-[0.18em] text-muted">Profile</p>
          <div className="grid gap-6 sm:grid-cols-2">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.12em] text-muted">Name</p>
              <p className="mt-1 text-lg font-bold">{displayName || "-"}</p>
            </div>
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.12em] text-muted">Username</p>
              <p className="mt-1 text-lg font-bold">{profile.username}</p>
            </div>
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.12em] text-muted">Email</p>
              <p className="mt-1 text-lg font-bold">{profile.email}</p>
            </div>
            {profile.phone_number && (
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.12em] text-muted">Phone</p>
                <p className="mt-1 text-lg font-bold">{profile.phone_number}</p>
              </div>
            )}
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.12em] text-muted">Member since</p>
              <p className="mt-1 text-lg font-bold">
                {new Date(profile.date_joined).toLocaleDateString()}
              </p>
            </div>
          </div>
        </div>
      )}

      <p className="mb-6 text-xs font-bold uppercase tracking-[0.18em] text-muted">
        Orders &amp; purchases
      </p>

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
