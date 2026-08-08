import { cookies } from "next/headers";
import type { NextRequest } from "next/server";

export const AUTH_COOKIE_NAME = "kaira_token";

export async function getAuthToken(): Promise<string | undefined> {
  const store = await cookies();
  return store.get(AUTH_COOKIE_NAME)?.value;
}

// `next start` always sets NODE_ENV=production, whether or not the request
// actually arrived over HTTPS -- trusting NODE_ENV for the cookie's Secure
// flag means the browser (or any HTTP client) silently drops the cookie on
// any plain-HTTP deployment, and the user appears logged out on every
// request after a login that looked successful. Check the real protocol
// instead: the connection itself, or (behind a reverse proxy that
// terminates TLS, e.g. most PaaS deployments) the standard forwarded-proto
// header it sets.
export function isSecureRequest(request: NextRequest): boolean {
  return request.nextUrl.protocol === "https:" || request.headers.get("x-forwarded-proto") === "https";
}
