import { NextRequest, NextResponse } from "next/server";
import { resolveBackendUrl } from "@/lib/backend";

// Generic read-only proxy for public catalog endpoints (products/categories).
// Client Components (like the shop page's filter/sort UI) need this rather
// than calling the Django host directly: NEXT_PUBLIC_API_BASE_URL gets baked
// into the browser bundle at build time, so a direct browser fetch only ever
// works when the visitor's own machine happens to be running the backend
// (e.g. a developer testing locally) -- it fails for any real deployment or
// different device. Routing through this same-origin proxy means the browser
// always hits a host it can actually reach; the real Django fetch then
// happens server-side, the same reliable way Server Components already do it.
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> },
) {
  const { path } = await params;
  const search = request.nextUrl.search;
  const backendPath = `/${path.join("/")}/${search}`;

  try {
    const backendResponse = await fetch(resolveBackendUrl(backendPath), { cache: "no-store" });
    const data = await backendResponse.json().catch(() => null);
    return NextResponse.json(data, { status: backendResponse.status });
  } catch (cause) {
    return NextResponse.json(
      {
        detail: `Could not reach the backend: ${cause instanceof Error ? cause.message : String(cause)}`,
      },
      { status: 502 },
    );
  }
}
