import { NextRequest, NextResponse } from "next/server";
import { ApiError, backendFetch } from "@/lib/backend";
import { AUTH_COOKIE_NAME } from "@/lib/session";
import type { Order } from "@/lib/types";

export async function GET(request: NextRequest) {
  const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;
  if (!token) {
    return NextResponse.json({ detail: "Sign in required." }, { status: 401 });
  }

  try {
    const orders = await backendFetch<Order[]>("/api/orders/", { token });
    return NextResponse.json(orders);
  } catch (error) {
    if (error instanceof ApiError) {
      return NextResponse.json(error.body ?? { detail: "Could not load orders." }, { status: error.status });
    }
    return NextResponse.json({ detail: "Could not load orders." }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;
  if (!token) {
    return NextResponse.json({ detail: "Sign in required." }, { status: 401 });
  }

  const body = await request.json();

  try {
    const order = await backendFetch<Order>("/api/orders/", { method: "POST", token, body });
    return NextResponse.json(order, { status: 201 });
  } catch (error) {
    if (error instanceof ApiError) {
      return NextResponse.json(error.body ?? { detail: "Could not place order." }, { status: error.status });
    }
    return NextResponse.json({ detail: "Could not place order." }, { status: 500 });
  }
}
