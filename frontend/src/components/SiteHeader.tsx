"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useCart } from "@/lib/cart-context";
import ThemeToggle from "./ThemeToggle";

const NAV_LINKS = [
  { href: "/", label: "Home" },
  { href: "/shop", label: "Shop" },
  { href: "/shop?category=dresses", label: "Dresses" },
  { href: "/shop?category=knitwear", label: "Knitwear" },
  { href: "/shop?category=tailoring", label: "Tailoring" },
];

export default function SiteHeader() {
  const { count, signedIn, refresh } = useCart();
  const router = useRouter();
  const [menuOpen, setMenuOpen] = useState(false);

  async function handleSignOut() {
    await fetch("/api/auth/logout", { method: "POST" });
    await refresh();
    router.push("/");
    router.refresh();
  }

  const accountAction = signedIn ? (
    <button
      onClick={handleSignOut}
      className="focus-ring text-left transition-colors hover:text-wine"
    >
      Sign out
    </button>
  ) : (
    <Link href="/login" className="focus-ring transition-colors hover:text-wine">
      Sign in
    </Link>
  );

  return (
    <header className="z-50 border-hairline bg-bone lg:fixed lg:inset-y-0 lg:left-0 lg:w-64 lg:border-r">
      <div className="flex h-16 items-center justify-between border-b border-hairline px-4 sm:px-6 lg:h-full lg:flex-col lg:items-stretch lg:justify-start lg:border-b-0 lg:px-8 lg:py-10">
        <div className="flex items-center justify-between lg:block">
          <Link
            href="/"
            className="focus-ring inline-block text-3xl font-extrabold tracking-[0.08em] text-ink"
          >
            KAIRA
          </Link>
          <button
            className="focus-ring -mr-2 p-2 lg:hidden"
            aria-label="Toggle menu"
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((v) => !v)}
          >
            <span className="block h-px w-6 bg-ink" />
            <span className="mt-1.5 block h-px w-6 bg-ink" />
            <span className="mt-1.5 block h-px w-6 bg-ink" />
          </button>
        </div>

        <nav className="mt-14 hidden flex-col gap-6 text-sm font-bold uppercase tracking-[0.12em] lg:flex">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.label}
              href={link.href}
              className="focus-ring transition-colors hover:text-wine"
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="mt-auto hidden space-y-5 text-sm font-semibold uppercase tracking-[0.1em] lg:block">
          <div className="flex items-center justify-between border-b border-hairline pb-4">
            <span className="text-xs tracking-[0.14em] text-muted">Theme</span>
            <ThemeToggle />
          </div>
          <Link
            href="/cart"
            className="focus-ring flex items-center justify-between transition-colors hover:text-wine"
          >
            <span>Cart</span>
            <span className="inline-flex h-7 min-w-7 items-center justify-center bg-sage px-2 text-xs text-on-accent">
              {count}
            </span>
          </Link>
          <Link href="/account" className="focus-ring block transition-colors hover:text-wine">
            Account
          </Link>
          {accountAction}
        </div>
      </div>

      {menuOpen && (
        <div className="border-b border-hairline bg-bone px-4 py-5 shadow-sm sm:px-6 lg:hidden">
          <nav className="flex flex-col gap-4 text-sm font-bold uppercase tracking-[0.12em]">
            {NAV_LINKS.map((link) => (
              <Link
                key={link.label}
                href={link.href}
                className="focus-ring"
                onClick={() => setMenuOpen(false)}
              >
                {link.label}
              </Link>
            ))}
          </nav>
          <div className="mt-5 flex items-center justify-between border-t border-hairline pt-5">
            <span className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">
              Theme
            </span>
            <ThemeToggle />
          </div>
          <div className="mt-5 flex items-center justify-between border-t border-hairline pt-5 text-sm font-semibold uppercase tracking-[0.1em]">
            <Link href="/cart" className="focus-ring" onClick={() => setMenuOpen(false)}>
              Cart ({count})
            </Link>
            {signedIn ? (
              <button
                onClick={() => {
                  setMenuOpen(false);
                  handleSignOut();
                }}
                className="focus-ring"
              >
                Sign out
              </button>
            ) : (
              <Link href="/login" className="focus-ring" onClick={() => setMenuOpen(false)}>
                Sign in
              </Link>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
