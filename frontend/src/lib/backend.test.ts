import { describe, expect, it } from "vitest";
import type { NextRequest } from "next/server";

import { resolveBackendUrl, forwardedClientHeaders } from "./backend";
import { isSecureRequest } from "./session";

function fakeRequest(headers: Record<string, string> = {}, protocol = "http:"): NextRequest {
  return {
    headers: new Headers(headers),
    nextUrl: { protocol },
  } as unknown as NextRequest;
}

describe("resolveBackendUrl", () => {
  it("joins a leading-slash path onto the base url", () => {
    expect(resolveBackendUrl("/api/auth/login/")).toBe("http://127.0.0.1:8000/api/auth/login/");
  });

  it("adds the missing separator slash for a bare path", () => {
    expect(resolveBackendUrl("api/products")).toBe("http://127.0.0.1:8000/api/products");
  });

  it("passes an absolute url straight through", () => {
    expect(resolveBackendUrl("https://example.com/x")).toBe("https://example.com/x");
  });
});

describe("forwardedClientHeaders", () => {
  it("propagates X-Forwarded-For and X-Real-IP when present", () => {
    const headers = forwardedClientHeaders(
      fakeRequest({ "x-forwarded-for": "203.0.113.7, 10.0.0.1", "x-real-ip": "203.0.113.7" }),
    );
    expect(headers["X-Forwarded-For"]).toBe("203.0.113.7, 10.0.0.1");
    expect(headers["X-Real-IP"]).toBe("203.0.113.7");
  });

  it("forwards nothing when the proxy set no client-ip headers", () => {
    expect(forwardedClientHeaders(fakeRequest())).toEqual({});
  });
});

describe("isSecureRequest", () => {
  it("is true over direct https", () => {
    expect(isSecureRequest(fakeRequest({}, "https:"))).toBe(true);
  });

  it("is true behind a TLS-terminating proxy (x-forwarded-proto)", () => {
    expect(isSecureRequest(fakeRequest({ "x-forwarded-proto": "https" }, "http:"))).toBe(true);
  });

  it("is false over plain http with no forwarded-proto", () => {
    expect(isSecureRequest(fakeRequest({}, "http:"))).toBe(false);
  });
});
