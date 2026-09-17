import { NextRequest, NextResponse } from "next/server";
import { ApiError, backendFetch } from "@/lib/backend";
import { AUTH_COOKIE_NAME, isSecureRequest } from "@/lib/session";

// The backend revokes the old token and issues a new one on success, so the
// cookie has to be rotated here or the very next request would 401 and the
// user would be silently signed out right after changing their password.
export async function POST(request: NextRequest) {
  const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;
  if (!token) {
    return NextResponse.json({ detail: "Sign in required." }, { status: 401 });
  }

  const body = await request.json();

  try {
    const data = await backendFetch<{ token: string }>("/api/account/change-password/", {
      method: "POST",
      token,
      body,
    });

    const response = NextResponse.json({ ok: true });
    response.cookies.set(AUTH_COOKIE_NAME, data.token, {
      httpOnly: true,
      sameSite: "lax",
      secure: isSecureRequest(request),
      path: "/",
      maxAge: 60 * 60 * 24 * 30,
    });
    return response;
  } catch (error) {
    if (error instanceof ApiError) {
      return NextResponse.json(error.body ?? { detail: "Could not change password." }, {
        status: error.status,
      });
    }
    return NextResponse.json({ detail: "Could not change password." }, { status: 500 });
  }
}
