import { NextRequest, NextResponse } from "next/server";
import { resolveBackendUrl, forwardedClientHeaders } from "@/lib/backend";

// Public: the uid + token from the emailed link are the credential here. The
// backend voids any existing auth token on success, so there is no cookie to
// set -- the user signs in fresh with the new password.
export async function POST(request: NextRequest) {
  const body = await request.json();

  const backendResponse = await fetch(resolveBackendUrl("/api/auth/password-reset/confirm/"), {
    method: "POST",
    headers: { "Content-Type": "application/json", ...forwardedClientHeaders(request) },
    body: JSON.stringify(body),
    cache: "no-store",
  });

  const data = await backendResponse.json().catch(() => ({ detail: "Request failed." }));
  return NextResponse.json(data, { status: backendResponse.status });
}
