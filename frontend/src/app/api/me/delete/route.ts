import { NextRequest, NextResponse } from "next/server";
import { ApiError, backendFetch } from "@/lib/backend";
import { AUTH_COOKIE_NAME } from "@/lib/session";

// Requires the account password in the body -- the backend insists on it so a
// stolen token alone can't destroy an account. On success the user no longer
// exists in any usable form, so the cookie is cleared here rather than leaving
// a dead token for the client to trip over.
export async function POST(request: NextRequest) {
  const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;
  if (!token) {
    return NextResponse.json({ detail: "Sign in required." }, { status: 401 });
  }

  const body = await request.json();

  try {
    await backendFetch("/api/me/delete/", { method: "POST", token, body });
    const response = NextResponse.json({ ok: true });
    response.cookies.delete(AUTH_COOKIE_NAME);
    return response;
  } catch (error) {
    if (error instanceof ApiError) {
      return NextResponse.json(error.body ?? { detail: "Could not delete account." }, {
        status: error.status,
      });
    }
    return NextResponse.json({ detail: "Could not delete account." }, { status: 500 });
  }
}
