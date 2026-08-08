import { NextRequest, NextResponse } from "next/server";
import { ApiError, backendFetch } from "@/lib/backend";
import { AUTH_COOKIE_NAME } from "@/lib/session";
import type { Order } from "@/lib/types";

export async function GET(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;
  if (!token) {
    return NextResponse.json({ detail: "Sign in required." }, { status: 401 });
  }

  try {
    const order = await backendFetch<Order>(`/api/orders/${id}/`, { token });
    return NextResponse.json(order);
  } catch (error) {
    if (error instanceof ApiError) {
      return NextResponse.json(error.body ?? { detail: "Could not load order." }, { status: error.status });
    }
    return NextResponse.json({ detail: "Could not load order." }, { status: 500 });
  }
}
