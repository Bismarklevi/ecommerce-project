import type { Metadata } from "next";
import Link from "next/link";
import ResetPasswordForm from "./ResetPasswordForm";

export const metadata: Metadata = { title: "Reset password" };

// The path and query names are dictated by the backend: PasswordResetRequestView
// emails `${FRONTEND_URL}/reset-password?uid=...&token=...`. Renaming either
// side without the other breaks every link already sitting in an inbox.
export default async function ResetPasswordPage({
  searchParams,
}: {
  searchParams: Promise<{ uid?: string; token?: string }>;
}) {
  const { uid, token } = await searchParams;
  const linkIsComplete = Boolean(uid && token);

  return (
    <div className="mx-auto grid max-w-6xl gap-10 px-4 py-16 sm:px-6 lg:grid-cols-[0.85fr_1.15fr] lg:px-8 lg:py-24">
      <section className="rounded-2xl border border-hairline p-8 sm:p-10">
        <p className="section-eyebrow mb-3">Account</p>
        <h1 className="section-title">Set a new password</h1>
        <p className="mt-5 text-sm leading-7 text-muted">
          Choose a new password for your account. Once it&apos;s saved you&apos;ll be signed out
          everywhere and can sign in again with the new one.
        </p>
      </section>
      <section className="border border-hairline p-6 sm:p-8">
        {linkIsComplete ? (
          <ResetPasswordForm uid={uid!} token={token!} />
        ) : (
          <div>
            <p className="text-lg font-bold">This link is incomplete</p>
            <p className="mt-3 text-sm leading-7 text-muted">
              The reset link is missing part of its address. Open it from the email again, or
              request a fresh one.
            </p>
            <Link href="/forgot-password" className="site-btn focus-ring mt-6">
              Request a new link
            </Link>
          </div>
        )}
      </section>
    </div>
  );
}
