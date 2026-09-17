import { NextRequest, NextResponse } from "next/server";
import { ApiError, backendFetch } from "@/lib/backend";
import { AUTH_COOKIE_NAME } from "@/lib/session";

interface CheckoutInitResponse {
  authorization_url: string;
  access_code: string;
  reference: string;
  order_id: number;
  amount: string;
  discount_amount: string;
}

export async function POST(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;
  if (!token) {
    return NextResponse.json({ detail: "Sign in required." }, { status: 401 });
  }

  // Optional {coupon_code}; the backend applies it atomically with payment
  // initiation, so a code is only ever consumed by an order that reached Paystack.
  const body = await request.json().catch(() => undefined);

  try {
    const result = await backendFetch<CheckoutInitResponse>(`/api/orders/${id}/checkout/`, {
      method: "POST",
      token,
      body,
    });
    return NextResponse.json(result);
  } catch (error) {
    if (error instanceof ApiError) {
      return NextResponse.json(error.body ?? { detail: "Could not start checkout." }, {
        status: error.status,
      });
    }
    return NextResponse.json({ detail: "Could not start checkout." }, { status: 500 });
  }
}
