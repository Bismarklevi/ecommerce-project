import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Terms of Service",
  description: "The terms that govern your use of the Kaira store.",
};

export default function TermsPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6 lg:px-8">
      <p className="section-eyebrow mb-3">Legal</p>
      <h1 className="section-title mb-2">Terms of Service</h1>
      <p className="mb-10 text-sm text-muted">Last updated: 8 August 2026</p>

      <div className="space-y-8 text-sm leading-relaxed">
        <section>
          <p>
            These terms govern your use of the Kaira online store. By creating an account or placing
            an order, you agree to them.
          </p>
        </section>

        <section>
          <h2 className="mb-2 text-lg">Your account</h2>
          <p>
            You are responsible for keeping your login details secure and for activity under your
            account. Let us know promptly if you believe your account has been accessed without your
            permission.
          </p>
        </section>

        <section>
          <h2 className="mb-2 text-lg">Orders and pricing</h2>
          <p>
            All prices are shown in Ghana Cedis (GHS) and include applicable charges shown at
            checkout. An order is an offer to buy; we confirm it once payment succeeds. If an item
            is mispriced or out of stock after you order, we will contact you and offer a correction
            or a full refund.
          </p>
        </section>

        <section>
          <h2 className="mb-2 text-lg">Payment</h2>
          <p>
            Payments are handled by Paystack (cards and Mobile Money). Your order is processed once
            Paystack confirms a successful payment to us directly &mdash; we never treat a payment
            as complete based on the browser alone.
          </p>
        </section>

        <section>
          <h2 className="mb-2 text-lg">Shipping and returns</h2>
          <p>
            Delivery times and costs depend on your shipping zone and are shown at checkout. If
            something isn&rsquo;t right, you may request a return or exchange from your{" "}
            <Link href="/account" className="underline">
              account
            </Link>{" "}
            in line with our returns process.
          </p>
        </section>

        <section>
          <h2 className="mb-2 text-lg">Acceptable use</h2>
          <p>
            Don&rsquo;t misuse the store: no attempting to disrupt the service, access other
            customers&rsquo; data, or use it for unlawful purposes.
          </p>
        </section>

        <section>
          <h2 className="mb-2 text-lg">Intellectual property</h2>
          <p>
            The Kaira name, content, and product imagery are our property or used with permission,
            and may not be reused without consent.
          </p>
        </section>

        <section>
          <h2 className="mb-2 text-lg">Liability</h2>
          <p>
            We provide the store with reasonable care but make no guarantee that it will always be
            uninterrupted or error-free. To the extent permitted by law, our liability is limited to
            the value of the order in question.
          </p>
        </section>

        <section>
          <h2 className="mb-2 text-lg">Governing law</h2>
          <p>These terms are governed by the laws of the Republic of Ghana.</p>
        </section>

        <section>
          <h2 className="mb-2 text-lg">Contact</h2>
          <p>
            Questions about these terms? Email{" "}
            <a href="mailto:hello@kaira.example.com" className="underline">
              hello@kaira.example.com
            </a>
            .
          </p>
        </section>
      </div>
    </div>
  );
}
