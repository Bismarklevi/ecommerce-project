import { NextRequest, NextResponse } from "next/server";
import { resolveBackendUrl } from "@/lib/backend";
import { AUTH_COOKIE_NAME } from "@/lib/session";

// Streams the backend's JSON export straight through as a download. Not
// backendFetch: that parses the body, and here the body IS the deliverable --
// it should reach the browser byte-for-byte with its attachment header.
export async function GET(request: NextRequest) {
  const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;
  if (!token) {
    return NextResponse.json({ detail: "Sign in required." }, { status: 401 });
  }

  const backendResponse = await fetch(resolveBackendUrl("/api/me/export/"), {
    headers: { Authorization: `Token ${token}` },
    cache: "no-store",
  });

  if (!backendResponse.ok) {
    const data = await backendResponse.json().catch(() => ({ detail: "Export failed." }));
    return NextResponse.json(data, { status: backendResponse.status });
  }

  return new NextResponse(backendResponse.body, {
    status: 200,
    headers: {
      "Content-Type": "application/json",
      "Content-Disposition":
        backendResponse.headers.get("content-disposition") ??
        'attachment; filename="kaira-my-data.json"',
    },
  });
}
