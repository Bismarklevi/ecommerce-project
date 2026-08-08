import type { NextRequest } from "next/server";

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000").replace(
  /\/$/,
  "",
);

export function resolveBackendUrl(path: string): string {
  if (path.startsWith("http")) return path;
  return `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

// Propagate the real caller's IP to Django so its per-endpoint rate-limiter and
// logs see the shopper rather than this Next.js server (which every proxied
// request would otherwise share). Only forwards headers a fronting proxy
// (Vercel / nginx / Cloudflare) is trusted to have set.
export function forwardedClientHeaders(request: NextRequest): Record<string, string> {
  const headers: Record<string, string> = {};
  const xff = request.headers.get("x-forwarded-for");
  if (xff) headers["X-Forwarded-For"] = xff;
  const realIp = request.headers.get("x-real-ip");
  if (realIp) headers["X-Real-IP"] = realIp;
  return headers;
}

// DRF list endpoints return a {count, next, previous, results} envelope now
// that pagination is enabled. Server-side callers use this to get back a plain
// array regardless of whether a given endpoint is paginated (mirrors the
// client-side unwrapList in lib/api.ts).
export function unwrapList<T>(payload: T[] | { results: T[] }): T[] {
  return Array.isArray(payload) ? payload : (payload?.results ?? []);
}

export class ApiError extends Error {
  status: number;
  body: unknown;
  constructor(status: number, body: unknown) {
    super(`Backend request failed with ${status}`);
    this.status = status;
    this.body = body;
  }
}

// Server-only fetch helper: attaches the bearer token when present, throws
// ApiError (status + parsed body) on a non-2xx response so callers can
// decide how to surface it instead of every call site re-parsing errors.
export async function backendFetch<T>(
  path: string,
  options: { method?: string; body?: unknown; token?: string } = {},
): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (options.token) headers.Authorization = `Token ${options.token}`;

  const response = await fetch(resolveBackendUrl(path), {
    method: options.method || "GET",
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    cache: "no-store",
  });

  const isJson = response.headers.get("content-type")?.includes("application/json");
  const data = isJson ? await response.json().catch(() => null) : null;

  if (!response.ok) {
    throw new ApiError(response.status, data);
  }
  return data as T;
}
