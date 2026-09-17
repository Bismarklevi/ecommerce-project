import { NextRequest, NextResponse } from "next/server";
import { resolveBackendUrl, forwardedClientHeaders } from "@/lib/backend";
import { AUTH_COOKIE_NAME, isSecureRequest } from "@/lib/session";

// Same shape as the login/register proxies: the backend verifies the Google
// credential and answers with the user plus a token, and the token goes into
// the httpOnly cookie here so the browser never holds it.
export async function POST(request: NextRequest) {
  const body = await request.json();

  const backendResponse = await fetch(resolveBackendUrl("/api/auth/google/"), {
    method: "POST",
    headers: { "Content-Type": "application/json", ...forwardedClientHeaders(request) },
    body: JSON.stringify(body),
    cache: "no-store",
  });

  const data = await backendResponse.json().catch(() => ({ detail: "Google sign-in failed." }));
  if (!backendResponse.ok) {
    return NextResponse.json(data, { status: backendResponse.status });
  }

  const response = NextResponse.json(data, { status: backendResponse.status });
  response.cookies.set(AUTH_COOKIE_NAME, data.token, {
    httpOnly: true,
    sameSite: "lax",
    secure: isSecureRequest(request),
    path: "/",
    maxAge: 60 * 60 * 24 * 30,
  });
  return response;
}
