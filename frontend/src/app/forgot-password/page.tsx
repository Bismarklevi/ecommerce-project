import type { Metadata } from "next";
import ForgotPasswordForm from "./ForgotPasswordForm";

export const metadata: Metadata = { title: "Forgot password" };

export default function ForgotPasswordPage() {
  return (
    <div className="mx-auto grid max-w-6xl gap-10 px-4 py-16 sm:px-6 lg:grid-cols-[0.85fr_1.15fr] lg:px-8 lg:py-24">
      <section className="rounded-2xl border border-hairline p-8 sm:p-10">
        <p className="section-eyebrow mb-3">Account</p>
        <h1 className="section-title">Forgot your password?</h1>
        <p className="mt-5 text-sm leading-7 text-muted">
          Enter the email on your account and we&apos;ll send a link to set a new one. The link
          works once and expires soon after.
        </p>
      </section>
      <section className="border border-hairline p-6 sm:p-8">
        <ForgotPasswordForm />
      </section>
    </div>
  );
}
