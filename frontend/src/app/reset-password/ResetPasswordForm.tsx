"use client";

import { useState } from "react";
import Link from "next/link";

export default function ResetPasswordForm({ uid, token }: { uid: string; token: string }) {
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const formData = new FormData(event.currentTarget);
    const newPassword = formData.get("new_password");
    if (newPassword !== formData.get("new_password_confirm")) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch("/api/auth/password-reset/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ uid, token, new_password: newPassword }),
      });
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        setError(
          typeof data === "object" && data
            ? Object.values(data).flat().join(" ")
            : "Something went wrong.",
        );
        setLoading(false);
        return;
      }
      setDone(true);
    } catch {
      setError("Could not reach the server. Please try again.");
      setLoading(false);
    }
  }

  if (done) {
    return (
      <div>
        <p className="text-lg font-bold">Password updated</p>
        <p className="mt-3 text-sm leading-7 text-muted">
          Your new password is saved. Sign in with it to pick up where you left off.
        </p>
        <Link href="/login" className="site-btn focus-ring mt-6">
          Sign in
        </Link>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-5">
      <div>
        <label
          htmlFor="new_password"
          className="mb-2 block text-xs font-bold uppercase tracking-[0.15em] text-muted"
        >
          New password
        </label>
        <input
          id="new_password"
          name="new_password"
          type="password"
          required
          autoComplete="new-password"
          className="field-input"
        />
      </div>
      <div>
        <label
          htmlFor="new_password_confirm"
          className="mb-2 block text-xs font-bold uppercase tracking-[0.15em] text-muted"
        >
          Confirm new password
        </label>
        <input
          id="new_password_confirm"
          name="new_password_confirm"
          type="password"
          required
          autoComplete="new-password"
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
        {loading ? "Saving..." : "Save new password"}
      </button>
    </form>
  );
}
