import LoginForm from "./LoginForm";

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string }>;
}) {
  const { next } = await searchParams;

  return (
    <div className="mx-auto grid max-w-6xl gap-10 px-4 py-16 sm:px-6 lg:grid-cols-[0.85fr_1.15fr] lg:px-8 lg:py-24">
      <section className="bg-bone-2 p-8 sm:p-10">
        <p className="section-eyebrow mb-3">Account</p>
        <h1 className="section-title">Sign in</h1>
        <p className="mt-5 text-sm leading-7 text-muted">
          Sign in to keep your bag, checkout details, and order history connected to your Kaira account.
        </p>
      </section>
      <section className="border border-hairline p-6 sm:p-8">
        <LoginForm redirectTo={next || "/account"} />
      </section>
    </div>
  );
}
