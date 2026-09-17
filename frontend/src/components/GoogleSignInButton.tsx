"use client";

import Script from "next/script";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { useCart } from "@/lib/cart-context";

// The slice of Google Identity Services we use. Typed here rather than pulling
// in @types/google.accounts for three calls.
interface GoogleIdentity {
  accounts: {
    id: {
      initialize(config: {
        client_id: string;
        callback: (response: { credential: string }) => void;
        ux_mode?: "popup" | "redirect";
      }): void;
      renderButton(parent: HTMLElement, options: Record<string, unknown>): void;
    };
  };
}

declare global {
  interface Window {
    google?: GoogleIdentity;
  }
}

const CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;

/**
 * "Continue with Google" for the sign-in page. Renders nothing at all until
 * NEXT_PUBLIC_GOOGLE_CLIENT_ID is set, so the feature is a config switch, not
 * a code change -- and a half-configured deployment shows no broken button.
 *
 * Google's own script draws the button (it's the only way to get the real
 * one-tap/credential flow); we receive a signed ID token and hand it to our
 * backend, which is what actually verifies it. The token never becomes a
 * session on its own.
 */
export default function GoogleSignInButton({
  mode,
  redirectTo,
  onError,
}: {
  mode: "login" | "register";
  redirectTo: string;
  onError: (message: string) => void;
}) {
  const router = useRouter();
  const { refresh } = useCart();
  const slot = useRef<HTMLDivElement>(null);
  const [ready, setReady] = useState(false);
  const [busy, setBusy] = useState(false);

  const handleCredential = useCallback(
    async ({ credential }: { credential: string }) => {
      setBusy(true);
      try {
        const response = await fetch("/api/auth/google", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ credential }),
        });
        if (!response.ok) {
          const data = await response.json().catch(() => ({}));
          onError(
            (data && typeof data === "object" && "detail" in data && String(data.detail)) ||
              "Google sign-in failed. Please try again.",
          );
          return;
        }
        await refresh();
        router.push(redirectTo);
        router.refresh();
      } catch {
        onError("Could not reach the server. Please try again.");
      } finally {
        setBusy(false);
      }
    },
    [onError, redirectTo, refresh, router],
  );

  // Draw (or redraw) the button whenever the script is ready or the mode
  // flips -- Google's button text is baked in at render time, so switching
  // between "Sign in with" and "Sign up with" needs a fresh render.
  useEffect(() => {
    if (!ready || !CLIENT_ID || !slot.current || !window.google) return;
    slot.current.innerHTML = "";
    window.google.accounts.id.initialize({
      client_id: CLIENT_ID,
      callback: handleCredential,
      ux_mode: "popup",
    });
    window.google.accounts.id.renderButton(slot.current, {
      theme: "outline",
      size: "large",
      shape: "pill",
      width: 320,
      text: mode === "register" ? "signup_with" : "signin_with",
    });
  }, [ready, mode, handleCredential]);

  if (!CLIENT_ID) return null;

  return (
    <>
      <Script
        src="https://accounts.google.com/gsi/client"
        strategy="afterInteractive"
        onLoad={() => setReady(true)}
        onError={() => onError("Google sign-in could not be loaded.")}
      />
      <div className="my-6 flex items-center gap-4 text-xs font-bold uppercase tracking-[0.15em] text-muted">
        <span className="h-px flex-1 bg-hairline" />
        or
        <span className="h-px flex-1 bg-hairline" />
      </div>
      <div className={`flex justify-center ${busy ? "pointer-events-none opacity-60" : ""}`}>
        {/* Google renders into this node; a fixed min-height stops the form
            jumping while the script loads. */}
        <div ref={slot} className="min-h-11" aria-busy={busy} />
      </div>
    </>
  );
}
