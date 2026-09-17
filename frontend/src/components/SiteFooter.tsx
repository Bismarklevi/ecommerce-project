import Link from "next/link";

export default function SiteFooter() {
  return (
    <footer className="border-t border-hairline text-ink">
      <div className="mx-auto grid max-w-7xl grid-cols-2 gap-10 px-4 py-16 sm:px-6 md:grid-cols-4 lg:px-8">
        <div className="col-span-2 md:col-span-1">
          <p className="mb-4 text-2xl font-extrabold tracking-[0.08em]">KAIRA</p>
          <p className="max-w-xs text-sm leading-relaxed text-muted">
            Considered clothing, cut to be worn. A small edit refreshed by season rather than by
            trend.
          </p>
        </div>

        <div>
          <p className="mb-5 text-xs font-bold uppercase tracking-[0.16em] text-ink">
            Useful links
          </p>
          <ul className="space-y-3 text-sm text-muted">
            <li>
              <Link href="/shop" className="focus-ring hover:text-wine">
                Shop
              </Link>
            </li>
            <li>
              <Link href="/account" className="focus-ring hover:text-wine">
                Account
              </Link>
            </li>
            <li>
              <Link href="/saved" className="focus-ring hover:text-wine">
                Saved items
              </Link>
            </li>
            <li>
              <Link href="/cart" className="focus-ring hover:text-wine">
                Cart
              </Link>
            </li>
            <li>
              <Link href="/login" className="focus-ring hover:text-wine">
                Sign in
              </Link>
            </li>
          </ul>
        </div>

        <div>
          <p className="mb-5 text-xs font-bold uppercase tracking-[0.16em] text-ink">Sitemap</p>
          <ul className="space-y-3 text-sm text-muted">
            <li>
              <Link href="/shop?category=dresses" className="focus-ring hover:text-wine">
                Dresses
              </Link>
            </li>
            <li>
              <Link href="/shop?category=knitwear" className="focus-ring hover:text-wine">
                Knitwear
              </Link>
            </li>
            <li>
              <Link href="/shop?category=tailoring" className="focus-ring hover:text-wine">
                Tailoring
              </Link>
            </li>
            <li>
              <Link href="/shop?category=denim" className="focus-ring hover:text-wine">
                Denim
              </Link>
            </li>
          </ul>
        </div>

        <div>
          <p className="mb-5 text-xs font-bold uppercase tracking-[0.16em] text-ink">
            Shipping & returns
          </p>
          <ul className="space-y-3 text-sm text-muted">
            <li>
              <Link href="/shop" className="focus-ring hover:text-wine">
                New arrivals
              </Link>
            </li>
            <li>
              <Link href="/checkout" className="focus-ring hover:text-wine">
                Checkout
              </Link>
            </li>
            <li>
              <Link href="/account" className="focus-ring hover:text-wine">
                Track orders
              </Link>
            </li>
          </ul>
        </div>
      </div>
      <div className="flex flex-col items-center justify-center gap-2 border-t border-hairline py-6 text-center text-xs text-muted sm:flex-row sm:gap-4">
        <span>Copyright © {new Date().getFullYear()} Kaira. All rights reserved.</span>
        <span className="flex gap-4">
          <Link href="/privacy" className="focus-ring hover:text-wine">
            Privacy
          </Link>
          <Link href="/terms" className="focus-ring hover:text-wine">
            Terms
          </Link>
        </span>
      </div>
    </footer>
  );
}
