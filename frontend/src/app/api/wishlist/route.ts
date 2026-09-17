import { NextRequest, NextResponse } from "next/server";
import { ApiError, backendFetch, unwrapList } from "@/lib/backend";
import { AUTH_COOKIE_NAME } from "@/lib/session";

interface WishlistItem {
  id: number;
  product: number;
}

// Same-origin proxy for the wishlist, mirroring the cart routes: the auth
// token lives in an httpOnly cookie, so only server-side code can read it and
// attach it to the Django call.
export async function GET(request: NextRequest) {
  const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;
  if (!token) {
    return NextResponse.json({ detail: "Sign in required." }, { status: 401 });
  }

  try {
    const payload = await backendFetch<WishlistItem[] | { results: WishlistItem[] }>(
      "/api/wishlist/",
      { token },
    );
    return NextResponse.json(unwrapList(payload));
  } catch (error) {
    if (error instanceof ApiError) {
      return NextResponse.json(error.body ?? { detail: "Could not load wishlist." }, {
        status: error.status,
      });
    }
    return NextResponse.json({ detail: "Could not load wishlist." }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;
  if (!token) {
    return NextResponse.json({ detail: "Sign in required." }, { status: 401 });
  }

  const body = await request.json();

  try {
    // The backend's create is idempotent (get_or_create), so re-saving an
    // already-saved product returns the existing row instead of a 400 the
    // client would have to special-case.
    const item = await backendFetch<WishlistItem>("/api/wishlist/", {
      method: "POST",
      token,
      body,
    });
    return NextResponse.json(item, { status: 201 });
  } catch (error) {
    if (error instanceof ApiError) {
      return NextResponse.json(error.body ?? { detail: "Could not save item." }, {
        status: error.status,
      });
    }
    return NextResponse.json({ detail: "Could not save item." }, { status: 500 });
  }
}
