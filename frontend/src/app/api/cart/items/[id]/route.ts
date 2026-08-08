import { NextRequest, NextResponse } from "next/server";
import { ApiError, backendFetch } from "@/lib/backend";
import { AUTH_COOKIE_NAME } from "@/lib/session";
import type { Cart } from "@/lib/types";

export async function PATCH(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;
  if (!token) {
    return NextResponse.json({ detail: "Sign in required." }, { status: 401 });
  }

  const body = await request.json();

  try {
    // The backend's PATCH on a cart item returns the updated *cart*, not
    // just the item (see CartItemViewSet._cart_response) -- one round trip
    // instead of a patch response the client would have to re-fetch anyway.
    const cart = await backendFetch<Cart>(`/api/cart/items/${id}/`, { method: "PATCH", token, body });
    return NextResponse.json(cart);
  } catch (error) {
    if (error instanceof ApiError) {
      return NextResponse.json(error.body ?? { detail: "Could not update item." }, { status: error.status });
    }
    return NextResponse.json({ detail: "Could not update item." }, { status: 500 });
  }
}

export async function DELETE(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;
  if (!token) {
    return NextResponse.json({ detail: "Sign in required." }, { status: 401 });
  }

  try {
    const cart = await backendFetch<Cart>(`/api/cart/items/${id}/remove/`, { method: "DELETE", token });
    return NextResponse.json(cart);
  } catch (error) {
    if (error instanceof ApiError) {
      return NextResponse.json(error.body ?? { detail: "Could not remove item." }, { status: error.status });
    }
    return NextResponse.json({ detail: "Could not remove item." }, { status: 500 });
  }
}
