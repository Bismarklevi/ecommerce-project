import { Suspense, cache } from "react";
import Image from "next/image";
import Link from "next/link";
import { getCategories, getProducts } from "@/lib/api";
import { PLACEHOLDER_IMAGE } from "@/lib/constants";
import type { Category, Product } from "@/lib/types";
import EditCarousel from "@/components/EditCarousel";
import HeroHeadline from "@/components/HeroHeadline";
import { ProductCardSkeleton, Skeleton, SkeletonScreen } from "@/components/Skeleton";
import TestimonialCarousel, { type Testimonial } from "@/components/TestimonialCarousel";
import LookAccordion, { type Look } from "@/components/LookAccordion";

export const dynamic = "force-dynamic";

// Three cards, fixed rather than one per category: the layout is built around
// a wide lead image and two narrower ones, so the count is part of the design.
// Tints are fixed hexes -- a decorative set of their own, not palette roles.
const LOOKS: Look[] = [
  {
    label: "Evening",
    image: "/images/look-evening.jpeg",
    href: "/shop?category=dresses",
    tint: "#e7eff5",
  },
  {
    label: "Knitwear",
    image: "/images/look-knit.jpeg",
    href: "/shop?category=knitwear",
    tint: "#f1ebf7",
  },
  {
    label: "Everyday",
    image: "/images/chunky-cable-knit-cardigan.jpg",
    href: "/shop?category=knitwear",
    tint: "#fbeadf",
  },
  {
    label: "Occasion",
    image: "/images/satin-slip-dress.jpg",
    href: "/shop?category=dresses",
    tint: "#e9f2ec",
  },
  {
    label: "Workwear",
    image: "/images/oversized-tailored-blazer.jpg",
    href: "/shop?category=tailoring",
    tint: "#f7efdc",
  },
  {
    label: "Denim",
    image: "/images/high-rise-straight-jeans.jpg",
    href: "/shop?category=denim",
    tint: "#eae7f2",
  },
  {
    label: "Summer",
    image: "/images/floral-wrap-midi-dress.jpg",
    href: "/shop?category=dresses",
    tint: "#fdf0e8",
  },
];

const fallbackCategories: Category[] = [
  { id: 1, slug: "dresses", name: "Dresses", image: "/images/cream-tiered-dress.jpg" },
  { id: 2, slug: "knitwear", name: "Knitwear", image: "/images/chunky-cable-knit-cardigan.jpg" },
];

const fallbackProducts: Product[] = [
  {
    id: 1,
    slug: "cream-tiered-dress",
    name: "Cream Tiered Dress",
    description: "A soft tiered silhouette from the Kaira edit.",
    price: "280.00",
    compare_at_price: null,
    category: fallbackCategories[0],
    images: [{ id: 1, image: "/images/cream-tiered-dress.jpg", alt: "Cream Tiered Dress" }],
    sizes: ["S", "M", "L"],
    variants: [],
    fabric: "",
    in_stock: true,
    look_number: "001",
    is_new: true,
    average_rating: null,
    review_count: 0,
  },
  {
    id: 2,
    slug: "chunky-cable-knit-cardigan",
    name: "Chunky Cable Knit Cardigan",
    description: "A textured layer with a relaxed everyday fit.",
    price: "240.00",
    compare_at_price: null,
    category: fallbackCategories[1],
    images: [
      { id: 2, image: "/images/chunky-cable-knit-cardigan.jpg", alt: "Chunky Cable Knit Cardigan" },
    ],
    sizes: ["S", "M", "L"],
    variants: [],
    fabric: "",
    in_stock: true,
    look_number: "002",
    is_new: true,
    average_rating: null,
    review_count: 0,
  },
  {
    id: 3,
    slug: "oversized-tailored-blazer",
    name: "Oversized Tailored Blazer",
    description: "Clean tailoring for a sharper daily uniform.",
    price: "360.00",
    compare_at_price: null,
    category: {
      id: 3,
      slug: "tailoring",
      name: "Tailoring",
      image: "/images/oversized-tailored-blazer.jpg",
    },
    images: [
      { id: 3, image: "/images/oversized-tailored-blazer.jpg", alt: "Oversized Tailored Blazer" },
    ],
    sizes: ["S", "M", "L"],
    variants: [],
    fabric: "",
    in_stock: true,
    look_number: "003",
    is_new: true,
    average_rating: null,
    review_count: 0,
  },
  {
    id: 4,
    slug: "high-rise-straight-jeans",
    name: "High Rise Straight Jeans",
    description: "A straight-leg staple cut for repeat wear.",
    price: "220.00",
    compare_at_price: null,
    category: {
      id: 4,
      slug: "denim",
      name: "Denim",
      image: "/images/high-rise-straight-jeans.jpg",
    },
    images: [
      { id: 4, image: "/images/high-rise-straight-jeans.jpg", alt: "High Rise Straight Jeans" },
    ],
    sizes: ["26", "28", "30"],
    variants: [],
    fabric: "",
    in_stock: true,
    look_number: "004",
    is_new: true,
    average_rating: null,
    review_count: 0,
  },
];

// cache() dedupes across the two Suspense boundaries below -- both sections
// need the same catalogue, and the API helpers fetch with cache: "no-store",
// so without this the page would hit the backend twice per request.
const getHomeCatalog = cache(async function getHomeCatalog(): Promise<{
  allProducts: Product[];
  categories: Category[];
}> {
  try {
    const [allProducts, categories] = await Promise.all([
      getProducts({ sort: "new" }),
      getCategories(),
    ]);
    return { allProducts, categories };
  } catch (error) {
    console.error(error);
    return { allProducts: fallbackProducts, categories: fallbackCategories };
  }
});

// Synchronous on purpose: nothing in the page shell waits on the backend, so
// the hero, the copy sections and the newsletter render and stream straight
// away. Only the two sections that actually need catalogue data suspend, and
// only those show placeholders.
export default function Home() {
  return (
    <div>
      {/* ---------------------------------------------------------------- hero */}
      <section className="px-4 pb-10 pt-3 sm:px-6 lg:px-8 lg:pb-14 lg:pt-5">
        <div className="mx-auto max-w-5xl px-2 text-center">
          <HeroHeadline
            className="display-title"
            text="Your shopping destination for considered fashion"
            blockWord="considered"
          />
        </div>

        {/* No max-width cap: the band runs the full bleed of the page, held off
            the edges only by the section's small gutter. */}
        <div className="relative mt-8 overflow-hidden rounded-3xl">
          <Image
            src="/images/first.png"
            alt="A woman in a lilac floral midi dress beside a man in a white linen shirt, against a peach and blue gradient backdrop"
            width={1536}
            height={1024}
            priority
            sizes="100vw"
            /* The source is a full-length studio shot; the reference hero is a
               wide, short band. Cropping to 2:1 means losing the bottom of the
               frame, so the object-position is biased upward (and slightly
               right, where the models stand) to keep faces and torsos in
               frame and drop the feet rather than the heads. */
            className="aspect-[4/3] w-full object-cover object-[58%_18%] sm:aspect-[16/9] lg:aspect-[21/9]"
          />

          {/* Circular sticker on the empty ground at the top left, tilted and
              carrying the same hard offset shadow as the buttons below it. It
              is a real link, not decoration -- "shop the edit" is an
              instruction, so it should do what it says. */}
          <Link
            href="/shop"
            style={{ "--rise-delay": "620ms" } as React.CSSProperties}
            className="hero-fade focus-ring absolute left-5 top-5 flex h-20 w-20 -rotate-12 flex-col items-center justify-center rounded-full bg-[var(--wine)] text-center text-[0.6rem] font-semibold uppercase leading-tight tracking-[0.12em] text-[#fefaf1] shadow-[4px_4px_0_0_var(--ink)] transition-transform hover:-rotate-6 sm:left-8 sm:top-8 sm:h-24 sm:w-24 sm:text-[0.68rem]"
          >
            <span>Shop the</span>
            <span>Dress edit</span>
          </Link>

          {/* Overlaid on the artwork, so these two pills are pinned to fixed
              colours: they have to hold against the photograph's own gradient,
              which owes nothing to the palette. */}
          <div
            style={{ "--rise-delay": "720ms" } as React.CSSProperties}
            className="hero-rise absolute bottom-5 left-5 flex flex-wrap gap-3 sm:bottom-8 sm:left-8"
          >
            <Link
              href="/shop"
              className="focus-ring inline-flex items-center rounded-full bg-[#221018] px-6 py-3.5 text-xs font-semibold uppercase tracking-[0.14em] text-[#fefaf1] shadow-[5px_5px_0_0_var(--wine)] transition-all hover:translate-x-[2px] hover:translate-y-[2px] hover:bg-[#3e012f] hover:shadow-[3px_3px_0_0_var(--wine)]"
            >
              Shop this edit
            </Link>
            <Link
              href="/shop?sort=featured"
              className="focus-ring inline-flex items-center rounded-full bg-white px-6 py-3.5 text-xs font-semibold uppercase tracking-[0.14em] text-[#221018] shadow-[5px_5px_0_0_var(--wine)] transition-all hover:translate-x-[2px] hover:translate-y-[2px] hover:bg-[#f2ece4] hover:shadow-[3px_3px_0_0_var(--wine)]"
            >
              Top collections
            </Link>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------- new in */}
      <section className="px-4 py-16 sm:px-6 lg:px-8 lg:py-20">
        <div className="mx-auto max-w-7xl">
          <div
            data-reveal-children
            className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between"
          >
            <div className="md:max-w-md">
              <h2 className="section-title">Our products</h2>
            </div>
            <div className="flex flex-col gap-5 md:items-end">
              <Link href="/shop" className="btn-hard focus-ring shrink-0">
                View all products
                <span aria-hidden="true" className="btn-hard__badge">
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M7 7l10 10M17 17V9M17 17H9" />
                  </svg>
                </span>
              </Link>
            </div>
          </div>

          <Suspense fallback={<EditFallback />}>
            <EditContent />
          </Suspense>
        </div>
      </section>

      {/* --------------------------------------------------------------- why */}
      <section className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8 lg:py-20">
        <div className="text-center">
          <h2 className="section-title">
            <span className="display-outline">Why</span> Kaira?
          </h2>
          <Swash />
        </div>
        <div data-reveal-children className="mt-10 grid gap-10 md:grid-cols-3">
          {[
            [
              "The best pieces in one place",
              "A tight edit rather than an endless catalogue. Everything here earned its spot.",
            ],
            [
              "Every item is chosen",
              "We handle the looking, the fabric checks and the fit notes, so you don't have to.",
            ],
            [
              "Made to outlast the season",
              "Quality over quantity. Buy well once instead of replacing something twice.",
            ],
          ].map(([title, body], index) => (
            <article key={title}>
              <StepMark index={index} />
              <h3 className="mt-6 text-2xl leading-tight text-ink">{title}</h3>
              <p className="mt-4 text-sm leading-7 text-muted">{body}</p>
            </article>
          ))}
        </div>
      </section>

      {/* ------------------------------------------------------- real people */}
      <section className="py-14 lg:py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          {/* Heading left, supporting copy and the CTA right -- they sit
              together on desktop and stack on mobile. */}
          <div
            data-reveal-children
            className="grid gap-6 md:grid-cols-[1fr_auto] md:items-start md:gap-12"
          >
            <h2 className="section-title max-w-xl">Real clothes on real people</h2>

            <div className="max-w-sm">
              <p className="text-sm leading-7 text-muted">
                Three ways to wear the edit, from a slip dress that carries an evening to the
                tailoring that gets you through the week.
              </p>
              <Link href="/shop" className="btn-hard focus-ring mt-5">
                Browse all products
                <span aria-hidden="true" className="btn-hard__badge">
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M7 7l10 10M17 17V9M17 17H9" />
                  </svg>
                </span>
              </Link>
            </div>
          </div>
        </div>

        <div data-reveal className="mx-auto mt-10 max-w-7xl px-4 sm:px-6 lg:px-8">
          <LookAccordion looks={LOOKS} />
        </div>
      </section>

      <Suspense fallback={<CategoryBandFallback />}>
        <CategoryBand />
      </Suspense>

      {/* ------------------------------------------------------ testimonials */}
      <section className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8 lg:py-16">
        <div className="text-center">
          <h2 className="section-title">
            <span className="display-outline">What</span> are people saying?
          </h2>
          <Swash />
          <p className="mx-auto mt-5 max-w-lg text-sm leading-7 text-muted">
            Some nice words from nice people who shop the Kaira edit.
          </p>
        </div>

        <div className="mt-10">
          <TestimonialCarousel items={TESTIMONIALS} />
        </div>
      </section>
      {/* ---------------------------------------------------------- promo band */}
      <section className="px-4 py-6 sm:px-6 lg:px-8">
        <div className="relative mx-auto max-w-7xl overflow-hidden rounded-3xl">
          <Image
            src="/images/second.png"
            alt=""
            width={1830}
            height={850}
            sizes="(min-width: 1280px) 1280px, 100vw"
            /* The models stand hard right and the left third is empty gradient,
               which is where the copy goes -- so the crop holds the right edge
               and lets the empty side be the first thing lost as it narrows. */
            className="aspect-[5/4] w-full object-cover object-[78%_50%] sm:aspect-[16/9] lg:aspect-[21/9]"
          />

          {/* Below sm the frame is too tight for the figures to clear the text,
              so a scrim carries the copy instead of bare photograph. */}
          <div className="absolute inset-0 bg-gradient-to-r from-white/85 via-white/55 to-transparent sm:from-transparent sm:via-transparent" />

          <div
            data-reveal-children
            className="absolute inset-y-0 left-0 flex max-w-[34rem] flex-col justify-end gap-5 p-6 sm:p-10 lg:p-14"
          >
            <h2 className="font-display text-2xl leading-tight text-[#221018] sm:text-3xl lg:text-4xl">
              Grab exciting deals and special promos today
            </h2>

            <form className="flex w-full max-w-sm items-center gap-2">
              <label className="sr-only" htmlFor="promo-email">
                Email address
              </label>
              <input
                id="promo-email"
                type="email"
                placeholder="Enter email address"
                className="field-input h-12 rounded-full"
              />
              <button
                type="submit"
                aria-label="Sign up for deals"
                className="focus-ring flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-[#221018] text-white shadow-[4px_4px_0_0_var(--wine)] transition-all hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0_0_var(--wine)]"
              >
                <svg
                  aria-hidden="true"
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M7 17 17 7M17 7H9M17 7v8" />
                </svg>
              </button>
            </form>
          </div>
        </div>
      </section>
    </div>
  );
}

// Placeholder copy until there are real reviews to pull from -- swap the array
// for whatever the backend ends up serving. The initials in each avatar are
// derived from the name, so no portrait assets are needed.
const TESTIMONIALS: Testimonial[] = [
  {
    quote:
      "Love Kaira. I am very much of the 'buy less but buy better' persuasion but never really knew where to look. The edit does the deciding for me.",
    name: "Ama Boateng",
    handle: "@amaboateng",
  },
  {
    quote:
      "The fit notes are the thing. I have ordered three times now and not sent a single piece back, which has never happened to me shopping online.",
    name: "Josh Lartey",
    handle: "@joshlartey",
  },
  {
    quote:
      "Bought a coat here two winters ago and it still looks new. That is the whole pitch really, and it turned out to be true.",
    name: "Nadia Mensah",
    handle: "@nadiamensah",
  },
];

// Hand-drawn underline swash sitting beneath a section heading -- the reference
// design's one piece of non-photographic decoration. Purely ornamental, so it's
// hidden from assistive tech.
function Swash() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 220 12"
      className="mx-auto mt-3 h-3 w-52 text-wine"
      fill="none"
    >
      <path
        d="M2 8.5C40 3.2 92 2 138 4.2c28 1.3 54 3.4 80 5.3-30-6-58-8.9-88-9.3"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  );
}

// Line-art numerals standing in for the reference design's drawn hands: one,
// two, three fingers. Same role -- a warm, non-corporate step marker.
function StepMark({ index }: { index: number }) {
  return (
    <span
      aria-hidden="true"
      className="flex h-12 w-12 items-center justify-center rounded-full border-2 border-wine text-lg font-semibold text-wine shadow-[4px_4px_0_0_var(--ink)]"
    >
      {index + 1}
    </span>
  );
}

/**
 * The category chips and the product carousel -- the only parts of the "Our
 * products" section that depend on the backend. Everything around them (the
 * heading, the "View all products" button) is static, so it stays in the page
 * shell and is never replaced by a placeholder.
 */
async function EditContent() {
  const { allProducts, categories } = await getHomeCatalog();
  const featured = allProducts.slice(0, 9);

  return (
    <>
      {/* Filter chips built from the real categories, so each one lands on a
              populated shop view rather than an empty filtered state. */}
      <div data-reveal-children className="mt-9 flex flex-wrap gap-2.5">
        <Link
          href="/shop?sort=new"
          className="focus-ring rounded-full border border-hairline bg-bone px-4 py-2 text-xs font-medium text-ink transition-colors hover:border-ink"
        >
          New
        </Link>
        {categories.map((category) => (
          <Link
            key={category.id}
            href={`/shop?category=${category.slug}`}
            className="focus-ring rounded-full border border-hairline bg-bone px-4 py-2 text-xs font-medium text-ink transition-colors hover:border-ink"
          >
            {category.name}
          </Link>
        ))}
        <Link
          href="/shop?sort=featured"
          className="focus-ring rounded-full border border-hairline bg-bone px-4 py-2 text-xs font-medium text-ink transition-colors hover:border-ink"
        >
          Top selection
        </Link>
      </div>

      <div className="mt-12">
        <EditCarousel products={featured} />
      </div>
    </>
  );
}

function EditFallback() {
  return (
    <SkeletonScreen>
      <div className="mt-9 flex flex-wrap gap-2.5">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-9 w-24 rounded-full" />
        ))}
      </div>
      <div className="mt-12 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <ProductCardSkeleton key={i} />
        ))}
      </div>
    </SkeletonScreen>
  );
}

/** The dark "Shop by category" band. Drops out entirely with no categories. */
async function CategoryBand() {
  const { allProducts, categories } = await getHomeCatalog();

  // Counts shown on the category pills are of the *loaded edit*, not the whole
  // catalogue -- getProducts() returns one paginated page. Good enough as a
  // browsing signal; if these ever need to be authoritative, the backend has to
  // annotate categories with a product count.
  const countsBySlug = allProducts.reduce<Record<string, number>>((acc, product) => {
    const slug = product.category?.slug;
    if (slug) acc[slug] = (acc[slug] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <>
      {/* ------------------------------------------------- shop by category */}
      {categories.length > 0 && (
        <section className="bg-ink px-4 py-14 sm:px-6 lg:px-8 lg:py-20">
          <div className="mx-auto max-w-5xl text-center text-bone">
            <h2 className="section-title section-title--invert">
              Shop <span className="display-outline">by</span> category
            </h2>
            <p className="mt-5 text-sm text-bone/70">Looking for something specific?</p>

            <div data-reveal-children className="mt-10 flex flex-wrap justify-center gap-3">
              {categories.map((category) => (
                <Link
                  key={category.id}
                  href={`/shop?category=${category.slug}`}
                  className="focus-ring group flex items-center gap-3 overflow-hidden rounded-xl bg-bone pr-4 text-ink shadow-[4px_4px_0_0_var(--bone-2)] transition-all hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0_0_var(--bone-2)] active:translate-x-[4px] active:translate-y-[4px] active:shadow-[0_0_0_0_var(--bone-2)]"
                >
                  <span className="relative h-14 w-14 shrink-0 bg-bone-2">
                    <Image
                      src={category.image || PLACEHOLDER_IMAGE}
                      alt=""
                      fill
                      sizes="56px"
                      className="object-cover"
                    />
                  </span>
                  <span className="py-3 text-sm font-medium">{category.name}</span>
                  {countsBySlug[category.slug] ? (
                    <span className="count-chip">{countsBySlug[category.slug]}</span>
                  ) : null}
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}
    </>
  );
}

// The band's heading is fixed copy, so it renders for real while only the
// pills -- which are category data -- stand in as placeholders.
function CategoryBandFallback() {
  return (
    <section className="bg-ink px-4 py-14 sm:px-6 lg:px-8 lg:py-20">
      <div className="mx-auto max-w-5xl text-center text-bone">
        <h2 className="section-title section-title--invert">
          Shop <span className="display-outline">by</span> category
        </h2>
        <p className="mt-5 text-sm text-bone/70">Looking for something specific?</p>
        <SkeletonScreen className="mt-10">
          <div className="flex flex-wrap justify-center gap-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-20 w-44 rounded-xl" />
            ))}
          </div>
        </SkeletonScreen>
      </div>
    </section>
  );
}
