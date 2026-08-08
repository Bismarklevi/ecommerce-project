"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCart } from "@/lib/cart-context";

export default function LoginForm({ redirectTo }: { redirectTo: string }) {
  const router = useRouter();
  const { refresh } = useCart();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setLoading(true);

    const formData = new FormData(event.currentTarget);
    const endpoint = mode === "login" ? "/api/auth/login" : "/api/auth/register";
    const payload =
      mode === "login"
        ? { username: formData.get("username"), password: formData.get("password") }
        : {
            username: formData.get("username"),
            email: formData.get("email"),
            password: formData.get("password"),
            password_confirm: formData.get("password_confirm"),
          };

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json();

      if (!response.ok) {
        const message =
          typeof data === "object" ? Object.values(data).flat().join(" ") : "Something went wrong.";
        setError(message || "Invalid details - please try again.");
        setLoading(false);
        return;
      }

      await refresh();
      router.push(redirectTo);
      router.refresh();
    } catch {
      setError("Could not reach the server. Please try again.");
      setLoading(false);
    }
  }

  return (
    <div>
      <div className="mb-8 flex border border-hairline text-sm font-bold uppercase tracking-[0.12em]">
        <button
          type="button"
          onClick={() => {
            setMode("login");
            setError(null);
          }}
          className={`focus-ring min-h-12 flex-1 transition-colors ${
            mode === "login" ? "bg-ink text-bone" : "bg-bone text-ink hover:bg-bone-2"
          }`}
        >
          Sign in
        </button>
        <button
          type="button"
          onClick={() => {
            setMode("register");
            setError(null);
          }}
          className={`focus-ring min-h-12 flex-1 border-l border-hairline transition-colors ${
            mode === "register" ? "bg-ink text-bone" : "bg-bone text-ink hover:bg-bone-2"
          }`}
        >
          Register
        </button>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        <div>
          <label htmlFor="username" className="mb-2 block text-xs font-bold uppercase tracking-[0.15em] text-muted">
            Username
          </label>
          <input id="username" name="username" type="text" required className="field-input" />
        </div>

        {mode === "register" && (
          <div>
            <label htmlFor="email" className="mb-2 block text-xs font-bold uppercase tracking-[0.15em] text-muted">
              Email
            </label>
            <input id="email" name="email" type="email" required className="field-input" />
          </div>
        )}

        <div>
          <label htmlFor="password" className="mb-2 block text-xs font-bold uppercase tracking-[0.15em] text-muted">
            Password
          </label>
          <input id="password" name="password" type="password" required className="field-input" />
        </div>

        {mode === "register" && (
          <div>
            <label
              htmlFor="password_confirm"
              className="mb-2 block text-xs font-bold uppercase tracking-[0.15em] text-muted"
            >
              Confirm password
            </label>
            <input id="password_confirm" name="password_confirm" type="password" required className="field-input" />
          </div>
        )}

        {error && <p className="border border-wine bg-wine/10 px-4 py-3 text-sm text-wine">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="site-btn focus-ring disabled:pointer-events-none disabled:opacity-40"
        >
          {loading ? "Please wait..." : mode === "login" ? "Sign in" : "Create account"}
        </button>
      </form>

      <p className="mt-6 text-sm text-muted">
        <Link href="/shop" className="focus-ring font-bold uppercase tracking-[0.12em] underline underline-offset-4 hover:text-wine">
          Continue browsing
        </Link>
      </p>
    </div>
  );
}
