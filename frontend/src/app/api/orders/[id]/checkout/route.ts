import { NextRequest, NextResponse } from "next/server";
import { ApiError, backendFetch } from "@/lib/backend";
import { AUTH_COOKIE_NAME } from "@/lib/session";

interface CheckoutInitResponse {
  authorization_url: string;
  access_code: string;
  reference: string;
  order_id: number;
}

export async function POST(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;
  if (!token) {
    return NextResponse.json({ detail: "Sign in required." }, { status: 401 });
  }

  try {
    const result = await backendFetch<CheckoutInitResponse>(`/api/orders/${id}/checkout/`, {
      method: "POST",
      token,
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
