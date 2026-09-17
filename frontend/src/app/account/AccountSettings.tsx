"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useCart } from "@/lib/cart-context";

function errorText(data: unknown, fallback: string): string {
  if (data && typeof data === "object") {
    const joined = Object.values(data as Record<string, unknown>)
      .flat()
      .join(" ");
    if (joined) return joined;
  }
  return fallback;
}

function Field({ id, label, autoComplete }: { id: string; label: string; autoComplete: string }) {
  return (
    <div>
      <label
        htmlFor={id}
        className="mb-2 block text-xs font-bold uppercase tracking-[0.15em] text-muted"
      >
        {label}
      </label>
      <input
        id={id}
        name={id}
        type="password"
        required
        autoComplete={autoComplete}
        className="field-input"
      />
    </div>
  );
}

// The three account-level rights the backend already serves (change password,
// data export, erasure) and the privacy page promises. Each is its own form so
// a failure in one leaves the others untouched.
export default function AccountSettings() {
  const router = useRouter();
  const { refresh } = useCart();

  const [pwState, setPwState] = useState<{ error?: string; done?: boolean; busy?: boolean }>({});
  const [delState, setDelState] = useState<{ error?: string; busy?: boolean; armed?: boolean }>({});

  async function changePassword(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    if (formData.get("new_password") !== formData.get("new_password_confirm")) {
      setPwState({ error: "New passwords do not match." });
      return;
    }
    setPwState({ busy: true });
    try {
      const response = await fetch("/api/account/change-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          current_password: formData.get("current_password"),
          new_password: formData.get("new_password"),
        }),
      });
      if (!response.ok) {
        const data = await response.json().catch(() => null);
        setPwState({ error: errorText(data, "Could not change password.") });
        return;
      }
      form.reset();
      setPwState({ done: true });
    } catch {
      setPwState({ error: "Could not reach the server. Please try again." });
    }
  }

  async function deleteAccount(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const password = new FormData(event.currentTarget).get("delete_password");
    setDelState({ busy: true, armed: true });
    try {
      const response = await fetch("/api/me/delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      });
      if (!response.ok) {
        const data = await response.json().catch(() => null);
        setDelState({ armed: true, error: errorText(data, "Could not delete account.") });
        return;
      }
      // The cookie is already gone; drop the client-side session too so the
      // header stops showing a signed-in state on the page we land on.
      await refresh();
      router.push("/");
      router.refresh();
    } catch {
      setDelState({ armed: true, error: "Could not reach the server. Please try again." });
    }
  }

  return (
    <div className="space-y-12">
      <section className="border border-hairline p-6 sm:p-8">
        <p className="mb-6 text-xs font-bold uppercase tracking-[0.18em] text-muted">
          Change password
        </p>
        <form onSubmit={changePassword} className="flex max-w-md flex-col gap-5">
          <Field id="current_password" label="Current password" autoComplete="current-password" />
          <Field id="new_password" label="New password" autoComplete="new-password" />
          <Field
            id="new_password_confirm"
            label="Confirm new password"
            autoComplete="new-password"
          />
          {pwState.error && (
            <p className="border border-wine bg-wine/10 px-4 py-3 text-sm text-wine">
              {pwState.error}
            </p>
          )}
          {pwState.done && (
            <p role="status" className="text-sm text-wine">
              Password updated. You stay signed in here; other devices will need to sign in again.
            </p>
          )}
          <button
            type="submit"
            disabled={pwState.busy}
            className="site-btn focus-ring self-start disabled:pointer-events-none disabled:opacity-40"
          >
            {pwState.busy ? "Saving..." : "Update password"}
          </button>
        </form>
      </section>

      <section className="border border-hairline p-6 sm:p-8">
        <p className="mb-3 text-xs font-bold uppercase tracking-[0.18em] text-muted">Your data</p>
        <p className="max-w-lg text-sm leading-7 text-muted">
          Download a copy of everything we hold about you -- profile, addresses, orders and saved
          items -- as a JSON file.
        </p>
        {/* A plain link, not fetch(): the route answers with a
            Content-Disposition attachment, and letting the browser handle it
            natively gets the download prompt for free. */}
        <a href="/api/me/export" download className="site-btn-outline focus-ring mt-6">
          Download my data
        </a>
      </section>

      <section className="border border-wine/40 p-6 sm:p-8">
        <p className="mb-3 text-xs font-bold uppercase tracking-[0.18em] text-wine">
          Delete account
        </p>
        <p className="max-w-lg text-sm leading-7 text-muted">
          This removes your profile, addresses and saved items permanently. Order records are kept
          in anonymised form, as the law requires, but they will no longer be linked to you. It
          cannot be undone.
        </p>

        {!delState.armed ? (
          <button
            type="button"
            onClick={() => setDelState({ armed: true })}
            className="site-btn-outline focus-ring mt-6"
          >
            Delete my account
          </button>
        ) : (
          <form onSubmit={deleteAccount} className="mt-6 flex max-w-md flex-col gap-5">
            {/* The password is the confirmation: the backend refuses without it,
                and typing it is a deliberate act in a way a second click isn't. */}
            <Field
              id="delete_password"
              label="Enter your password to confirm"
              autoComplete="current-password"
            />
            {delState.error && (
              <p className="border border-wine bg-wine/10 px-4 py-3 text-sm text-wine">
                {delState.error}
              </p>
            )}
            <div className="flex flex-wrap gap-3">
              <button
                type="submit"
                disabled={delState.busy}
                className="site-btn focus-ring disabled:pointer-events-none disabled:opacity-40"
              >
                {delState.busy ? "Deleting..." : "Permanently delete"}
              </button>
              <button
                type="button"
                onClick={() => setDelState({})}
                className="site-btn-outline focus-ring"
              >
                Cancel
              </button>
            </div>
          </form>
        )}
      </section>
    </div>
  );
}
