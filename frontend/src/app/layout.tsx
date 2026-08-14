import type { Metadata } from "next";
import { Raleway } from "next/font/google";
import Script from "next/script";
import "./globals.css";
import { CartProvider } from "@/lib/cart-context";
import SiteHeader from "@/components/SiteHeader";
import SiteFooter from "@/components/SiteFooter";

// Previously the design just *referenced* "Raleway" as a bare font-family
// name (a CSS variable fallback list with no actual loading mechanism --
// no next/font, no <link>), so every visitor's browser silently fell back
// to a system font instead. This actually loads it.
const raleway = Raleway({
  variable: "--font-plaza",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
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
const themeInitScript = `
(function () {
  try {
    var stored = localStorage.getItem("kaira-theme");
    var theme = stored || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    if (theme === "dark") document.documentElement.classList.add("dark");
  } catch (e) {}
})();
`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={raleway.variable} suppressHydrationWarning>
      <head>
        <Script id="theme-init" strategy="beforeInteractive">
          {themeInitScript}
        </Script>
      </head>
      <body className="antialiased">
        <CartProvider>
          <a
            href="#main"
            className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-[100] focus:bg-ink focus:text-bone focus:px-4 focus:py-2 focus:text-sm"
          >
            Skip to content
          </a>
          <SiteHeader />
          <main id="main" className="lg:pl-64">
            {children}
          </main>
          <SiteFooter />
        </CartProvider>
      </body>
    </html>
  );
}
