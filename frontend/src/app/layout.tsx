import type { Metadata } from "next";
import { Google_Sans, Lilita_One } from "next/font/google";
import "./globals.css";
import { CartProvider } from "@/lib/cart-context";
import SiteHeader from "@/components/SiteHeader";
import SiteFooter from "@/components/SiteFooter";
import ScrollReveal from "@/components/ScrollReveal";

// Two families, strictly divided (see globals.css): a heavy display face for
// every heading, Google Sans for body copy and UI. Lilita One ships a single
// weight (400) -- headings must not ask for 500/600, there is nothing to
// synthesise from, and the browser would fake-bold the glyphs.
const lilitaOne = Lilita_One({
  variable: "--font-display-face",
  subsets: ["latin"],
  weight: ["400"],
  display: "swap",
});

// Body text. Loaded through next/font rather than the <link> tags from
// fonts.googleapis.com: next/font self-hosts the files from this origin, so
// there is no render-blocking stylesheet request, no preconnect needed, and no
// layout shift when the face arrives.
const googleSans = Google_Sans({
  variable: "--font-body",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  style: ["normal", "italic"],
  display: "swap",
  // Next ships no fallback metrics for this family ("Failed to find font
  // override values" at build time), so it cannot auto-generate a
  // size-adjusted fallback face. Naming the chain explicitly at least keeps
  // the pre-swap render on a close neighbour instead of Times.
  fallback: ["Roboto", "Helvetica Neue", "Arial", "sans-serif"],
});

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";
const siteDescription =
  "Kaira is a small edit of considered clothing: tailoring, knitwear, and dresses built to be worn, not just bought.";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "Kaira — Considered Clothing",
    // Child pages set just their own title; this appends the brand.
    template: "%s | Kaira",
  },
  description: siteDescription,
  applicationName: "Kaira",
  openGraph: {
    title: "Kaira — Considered Clothing",
    description: siteDescription,
    siteName: "Kaira",
    type: "website",
    locale: "en_GH",
  },
  twitter: {
    card: "summary_large_image",
    title: "Kaira — Considered Clothing",
    description: siteDescription,
  },
};

// Applies the saved/preferred color scheme before first paint, so there's
// no flash of the wrong theme. Runs as an inline script (not a React
// effect) specifically because effects run after paint -- too late to
// prevent the flash this exists to avoid.
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${lilitaOne.variable} ${googleSans.variable}`}>
      <body className="antialiased">
        <CartProvider>
          <a
            href="#main"
            className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-[100] focus:rounded-lg focus:bg-ink focus:px-4 focus:py-2 focus:text-sm focus:text-bone"
          >
            Skip to content
          </a>
          <SiteHeader />
          <ScrollReveal />
          <main id="main">{children}</main>
          <SiteFooter />
        </CartProvider>
      </body>
    </html>
  );
}
