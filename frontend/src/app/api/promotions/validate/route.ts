import { NextRequest, NextResponse } from "next/server";
import { ApiError, backendFetch } from "@/lib/backend";
import { AUTH_COOKIE_NAME } from "@/lib/session";

// Preview only: the backend computes the discount without redeeming the code.
// Redemption happens inside the checkout call, so an applied-then-abandoned
// code never burns a usage slot.
export async function POST(request: NextRequest) {
  const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;
  const body = await request.json();
  try {
    const result = await backendFetch<{ code: string; discount_amount: string }>(
      "/api/promotions/validate/",
      { method: "POST", token, body },
    );
    return NextResponse.json(result);
  } catch (error) {
    if (error instanceof ApiError) {
      return NextResponse.json(error.body ?? { detail: "Invalid code." }, { status: error.status });
    }
    return NextResponse.json({ detail: "Could not check that code." }, { status: 500 });
  }
}
