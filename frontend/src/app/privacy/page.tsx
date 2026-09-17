import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Privacy Policy",
  description: "How Kaira collects, uses, and protects your personal data.",
};

export default function PrivacyPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6 lg:px-8">
      <p className="section-eyebrow mb-3">Legal</p>
      <h1 className="section-title mb-2">Privacy Policy</h1>
      <p className="mb-10 text-sm text-muted">Last updated: 8 August 2026</p>

      <div className="space-y-8 text-sm leading-relaxed">
        <section>
          <p>
            This policy explains what personal data Kaira collects when you use our store, why we
            collect it, and the choices you have. We handle personal data in line with Ghana&rsquo;s
            Data Protection Act, 2012 (Act 843).
          </p>
        </section>

        <section>
          <h2 className="mb-2 text-lg">What we collect</h2>
          <ul className="list-disc space-y-1 pl-5">
            <li>
              Account details: name, email address, and password (stored only as a secure hash).
            </li>
            <li>
              Order details: items purchased, delivery name, phone number, and shipping address.
            </li>
            <li>Optional saved addresses, wishlist items, and product reviews you create.</li>
            <li>
              A single preference cookie for your light/dark theme. We do not use advertising or
              third-party tracking cookies.
            </li>
          </ul>
        </section>

        <section>
          <h2 className="mb-2 text-lg">How we use it</h2>
          <p>
            We use your data to create and secure your account, process and deliver your orders,
            provide customer support, and send transactional email (order updates and password
            resets). We do not sell your personal data.
          </p>
        </section>

        <section>
          <h2 className="mb-2 text-lg">Payments</h2>
          <p>
            Payments are processed by Paystack. Your card or Mobile Money details are entered on
            Paystack&rsquo;s secure systems and are never seen or stored by Kaira. We retain only a
            payment reference and status to reconcile your order.
          </p>
        </section>

        <section>
          <h2 className="mb-2 text-lg">Sharing</h2>
          <p>
            We share data only with the providers needed to run the store: our payment processor
            (Paystack), our hosting provider, and our email provider. Each processes data on our
            behalf under their own security obligations.
          </p>
        </section>

        <section>
          <h2 className="mb-2 text-lg">Retention</h2>
          <p>
            We keep your account data for as long as your account is active. Completed order and
            payment records are retained afterwards where required for tax and accounting
            obligations, but stripped of information that identifies you.
          </p>
        </section>

        <section>
          <h2 className="mb-2 text-lg">Your rights</h2>
          <p>
            You can access or erase your data at any time. From your{" "}
            <Link href="/account" className="underline">
              account
            </Link>{" "}
            you can download a copy of everything we hold about you, or request deletion of your
            account. Deletion removes your personal data and locks the account; retained order
            records are anonymised. You may also contact us using the details below.
          </p>
        </section>

        <section>
          <h2 className="mb-2 text-lg">Security</h2>
          <p>
            We protect your data with encryption in transit (HTTPS), hashed passwords, rate-limited
            authentication, and access controls that ensure you can only ever see your own data.
          </p>
        </section>

        <section>
          <h2 className="mb-2 text-lg">Contact</h2>
          <p>
            Questions about this policy or your data? Email{" "}
            <a href="mailto:privacy@kaira.example.com" className="underline">
              privacy@kaira.example.com
            </a>
            .
          </p>
        </section>
      </div>
    </div>
  );
}
