import { NextRequest, NextResponse } from "next/server";
import { resolveBackendUrl, forwardedClientHeaders } from "@/lib/backend";

// Public: no token. The backend answers identically whether or not the email
// exists (anti-enumeration), and this proxy passes that answer through
// unchanged so the frontend can't accidentally leak the difference either.
export async function POST(request: NextRequest) {
  const body = await request.json();

  const backendResponse = await fetch(resolveBackendUrl("/api/auth/password-reset/"), {
    method: "POST",
    headers: { "Content-Type": "application/json", ...forwardedClientHeaders(request) },
    body: JSON.stringify(body),
    cache: "no-store",
  });

  const data = await backendResponse.json().catch(() => ({ detail: "Request failed." }));
  return NextResponse.json(data, { status: backendResponse.status });
}
