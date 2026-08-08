import { NextRequest, NextResponse } from "next/server";
import { ApiError, backendFetch } from "@/lib/backend";
import { AUTH_COOKIE_NAME } from "@/lib/session";
import type { Cart } from "@/lib/types";

export async function GET(request: NextRequest) {
  const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;
  if (!token) {
    return NextResponse.json({ detail: "Sign in required." }, { status: 401 });
  }

  try {
    const cart = await backendFetch<Cart>("/api/cart/mine/", { token });
    return NextResponse.json(cart);
  } catch (error) {
    if (error instanceof ApiError) {
      return NextResponse.json(error.body ?? { detail: "Could not load cart." }, {
        status: error.status,
      });
    }
    return NextResponse.json({ detail: "Could not load cart." }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;
  if (!token) {
    return NextResponse.json({ detail: "Sign in required." }, { status: 401 });
  }

  const body = await request.json();

  try {
    const cart = await backendFetch<Cart>("/api/cart/add-item/", { method: "POST", token, body });
    return NextResponse.json(cart);
  } catch (error) {
    if (error instanceof ApiError) {
      return NextResponse.json(error.body ?? { detail: "Could not update cart." }, {
        status: error.status,
      });
    }
    return NextResponse.json({ detail: "Could not update cart." }, { status: 500 });
  }
}
