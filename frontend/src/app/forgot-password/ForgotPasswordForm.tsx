"use client";

import { useState } from "react";
import Link from "next/link";

export default function ForgotPasswordForm() {
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setLoading(true);

    const email = new FormData(event.currentTarget).get("email");

    try {
      const response = await fetch("/api/auth/password-reset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        setError(
          typeof data === "object" && data
            ? Object.values(data).flat().join(" ")
            : "Something went wrong.",
        );
        setLoading(false);
        return;
      }

      // The backend deliberately answers the same for known and unknown
      // emails, and so does this screen: the copy below never confirms whether
      // an account exists.
      setSent(true);
    } catch {
      setError("Could not reach the server. Please try again.");
      setLoading(false);
    }
  }

  if (sent) {
    return (
      <div>
        <p className="text-lg font-bold">Check your email</p>
        <p className="mt-3 text-sm leading-7 text-muted">
          If that address has an account, a reset link is on its way. It can take a minute to arrive
          -- check your spam folder if it doesn&apos;t show up.
        </p>
        <p className="mt-6 text-sm text-muted">
          <Link
            href="/login"
            className="focus-ring font-bold uppercase tracking-[0.12em] underline underline-offset-4 hover:text-wine"
          >
            Back to sign in
          </Link>
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-5">
      <div>
        <label
          htmlFor="email"
          className="mb-2 block text-xs font-bold uppercase tracking-[0.15em] text-muted"
        >
          Email
        </label>
        <input
          id="email"
          name="email"
          type="email"
          required
          autoComplete="email"
          className="field-input"
        />
      </div>

      {error && (
        <p className="border border-wine bg-wine/10 px-4 py-3 text-sm text-wine">{error}</p>
      )}

      <button
        type="submit"
        disabled={loading}
        className="site-btn focus-ring disabled:pointer-events-none disabled:opacity-40"
      >
        {loading ? "Sending..." : "Send reset link"}
      </button>

      <p className="text-sm text-muted">
        <Link
          href="/login"
          className="focus-ring font-bold uppercase tracking-[0.12em] underline underline-offset-4 hover:text-wine"
        >
          Back to sign in
        </Link>
      </p>
    </form>
  );
}
