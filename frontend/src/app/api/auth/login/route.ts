import { NextRequest, NextResponse } from "next/server";
import { resolveBackendUrl, forwardedClientHeaders } from "@/lib/backend";
import { AUTH_COOKIE_NAME, isSecureRequest } from "@/lib/session";

export async function POST(request: NextRequest) {
  const body = await request.json();

  const backendResponse = await fetch(resolveBackendUrl("/api/auth/login/"), {
    method: "POST",
    headers: { "Content-Type": "application/json", ...forwardedClientHeaders(request) },
    body: JSON.stringify(body),
    cache: "no-store",
  });

  const data = await backendResponse.json();
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
