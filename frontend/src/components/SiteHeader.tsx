"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useCart } from "@/lib/cart-context";

const NAV_LINKS = [
  { href: "/shop?sort=new", label: "New in" },
  { href: "/shop", label: "Collections" },
  { href: "/shop?sort=featured", label: "Featured" },
  { href: "/saved", label: "Saved" },
  { href: "/account", label: "Account" },
];

function SearchIcon() {
  return (
    <svg
      aria-hidden="true"
      width="15"
      height="15"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
    >
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.5-3.5" />
    </svg>
  );
}

function BagIcon() {
  return (
    <svg
      aria-hidden="true"
      width="17"
      height="17"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M6 7h12l1 13H5L6 7Z" />
      <path d="M9 7V5.5a3 3 0 0 1 6 0V7" />
    </svg>
  );
}

export default function SiteHeader() {
  const { count, signedIn, refresh } = useCart();
  const router = useRouter();
  const [menuOpen, setMenuOpen] = useState(false);
  const [searchValue, setSearchValue] = useState("");
  const [scrolled, setScrolled] = useState(false);

  // The glass only switches on once there is page behind the bar to refract.
  // Read on mount as well as on scroll: a reload partway down the page, or a
  // deep link to an anchor, starts already scrolled.
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  function handleSearchSubmit(event: React.FormEvent) {
    event.preventDefault();
    const query = searchValue.trim();
    setMenuOpen(false);
    router.push(query ? `/shop?search=${encodeURIComponent(query)}` : "/shop");
  }

  async function handleSignOut() {
    await fetch("/api/auth/logout", { method: "POST" });
    await refresh();
    router.push("/");
    router.refresh();
  }

  return (
    <header
      className={`sticky top-0 z-50 transition-[background-color,box-shadow,border-color] duration-300 ${
        scrolled ? "glass-header" : "glass-header-top"
      }`}
    >
      <div className="mx-auto flex h-16 max-w-7xl items-center gap-8 px-4 sm:px-6 lg:px-8">
        {/* Logo and nav sit together as one left-hand group, rather than the
            links being centred -- that grouping is what makes the bar read as
            compact and editorial instead of as a wide split menu. */}
        <Link href="/" className="focus-ring font-display text-xl tracking-tight text-ink">
          Kaira
        </Link>

        <nav className="hidden items-center gap-7 text-sm lg:flex">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.label}
              href={link.href}
              className={`focus-ring transition-colors hover:text-ink ${scrolled ? "text-ink" : "text-muted"}`}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-2 sm:gap-3">
          <form onSubmit={handleSearchSubmit} className="relative hidden md:block">
            <label htmlFor="site-search" className="sr-only">
              Search products
            </label>
            <input
              id="site-search"
              type="search"
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              placeholder="Search"
              className="h-10 w-52 rounded-full border border-hairline bg-bone-2/50 pl-4 pr-10 text-sm text-ink placeholder:text-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-wine"
            />
            <button
              type="submit"
              aria-label="Search"
              className="focus-ring absolute right-1 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full text-muted transition-colors hover:text-ink"
            >
              <SearchIcon />
            </button>
          </form>

          {signedIn ? (
            <button
              onClick={handleSignOut}
              className={`focus-ring hidden text-sm transition-colors hover:text-ink lg:block ${scrolled ? "text-ink" : "text-muted"}`}
            >
              Sign out
            </button>
          ) : (
            <Link
              href="/login"
              className={`focus-ring hidden text-sm transition-colors hover:text-ink lg:block ${scrolled ? "text-ink" : "text-muted"}`}
            >
              Sign in
            </Link>
          )}

          {/* Solid dark disc, the bar's one piece of heavy weight. The count
              rides as a corner badge so the control stays a circle at any
              basket size, and the label carries the number for screen readers
              since the badge alone would read as a bare digit. */}
          <Link
            href="/cart"
            aria-label={`Cart, ${count} item${count === 1 ? "" : "s"}`}
            className="focus-ring relative flex h-10 w-10 items-center justify-center rounded-full bg-ink text-bone shadow-[3px_3px_0_0_var(--wine)] transition-all hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[2px_2px_0_0_var(--wine)] active:translate-x-[3px] active:translate-y-[3px] active:shadow-[0_0_0_0_var(--wine)]"
          >
            <BagIcon />
            {count > 0 && (
              <span
                aria-hidden="true"
                className="absolute -right-0.5 -top-0.5 flex h-5 min-w-5 items-center justify-center rounded-full bg-sage px-1 text-[10px] font-semibold text-on-accent"
              >
                {count}
              </span>
            )}
          </Link>

          <button
            className="focus-ring -mr-2 p-2 lg:hidden"
            aria-label="Toggle menu"
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((v) => !v)}
          >
            <span className="block h-0.5 w-5 rounded bg-ink" />
            <span className="mt-1.5 block h-0.5 w-5 rounded bg-ink" />
            <span className="mt-1.5 block h-0.5 w-5 rounded bg-ink" />
          </button>
        </div>
      </div>

      {menuOpen && (
        <div className="border-t border-hairline bg-bone px-4 py-5 sm:px-6 lg:hidden">
          <form onSubmit={handleSearchSubmit} className="relative mb-5">
            <label htmlFor="site-search-mobile" className="sr-only">
              Search products
            </label>
            <input
              id="site-search-mobile"
              type="search"
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              placeholder="Search"
              className="h-11 w-full rounded-full border border-hairline bg-bone-2/50 pl-4 pr-11 text-sm text-ink placeholder:text-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-wine"
            />
            <button
              type="submit"
              aria-label="Search"
              className="focus-ring absolute right-1.5 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full text-muted"
            >
              <SearchIcon />
            </button>
          </form>
          <nav className="flex flex-col gap-4 text-sm">
            {NAV_LINKS.map((link) => (
              <Link
                key={link.label}
                href={link.href}
                className="focus-ring text-ink"
                onClick={() => setMenuOpen(false)}
              >
                {link.label}
              </Link>
            ))}
          </nav>
          <div className="mt-5 border-t border-hairline pt-5 text-sm">
            {signedIn ? (
              <button
                onClick={() => {
                  setMenuOpen(false);
                  handleSignOut();
                }}
                className="focus-ring text-ink"
              >
                Sign out
              </button>
            ) : (
              <Link
                href="/login"
                className="focus-ring text-ink"
                onClick={() => setMenuOpen(false)}
              >
                Sign in
              </Link>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
