import { NextRequest, NextResponse } from "next/server";
import { ApiError, backendFetch } from "@/lib/backend";
import { AUTH_COOKIE_NAME } from "@/lib/session";
import type { Cart } from "@/lib/types";

export async function GET(request: NextRequest) {
  const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;
  // Not a 401: CartProvider probes this on every page load, and a signed-out
  // visitor is the normal case, not a failure. A 401 here put a red console
  // line on every page for everyone who wasn't logged in.
  if (!token) {
    return NextResponse.json({ signed_in: false });
  }

  try {
    const cart = await backendFetch<Cart>("/api/cart/mine/", { token });
    return NextResponse.json(cart);
  } catch (error) {
    // A token the backend no longer honours (revoked, expired) is a dead
    // cookie; clear it so the client stops presenting it on every request.
    if (error instanceof ApiError && error.status === 401) {
      const response = NextResponse.json({ signed_in: false });
      response.cookies.delete(AUTH_COOKIE_NAME);
      return response;
    }
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
