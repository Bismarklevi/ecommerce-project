import { NextRequest, NextResponse } from "next/server";
import { resolveBackendUrl } from "@/lib/backend";
import { AUTH_COOKIE_NAME } from "@/lib/session";

export async function POST(request: NextRequest) {
  const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;

  if (token) {
    await fetch(resolveBackendUrl("/api/auth/logout/"), {
      method: "POST",
      headers: { Authorization: `Token ${token}` },
      cache: "no-store",
    }).catch(() => {
      // Best-effort revoke -- the cookie clears below regardless, so a
      // network hiccup here shouldn't strand the user "logged in" client-side.
    });
  }

  const response = NextResponse.json({ ok: true });
  response.cookies.delete(AUTH_COOKIE_NAME);
  return response;
}
