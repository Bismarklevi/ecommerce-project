import Image from "next/image";
import Link from "next/link";
import { getCategories, getFeaturedProducts, getProducts } from "@/lib/api";
import { PLACEHOLDER_IMAGE } from "@/lib/constants";
import { formatPrice } from "@/lib/currency";
import type { Category, Product } from "@/lib/types";
import ProductCard from "@/components/ProductCard";

export const dynamic = "force-dynamic";

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
  },
];

async function getHomeCatalog(): Promise<{
  featuredRaw: Product[];
  allProducts: Product[];
  categories: Category[];
}> {
  try {
    const [featuredRaw, allProducts, categories] = await Promise.all([
      getFeaturedProducts(8),
      getProducts({ sort: "new" }),
      getCategories(),
    ]);
    return { featuredRaw, allProducts, categories };
  } catch (error) {
    console.error(error);
    return {
      featuredRaw: fallbackProducts,
      allProducts: fallbackProducts,
      categories: fallbackCategories,
    };
  }
}

export default async function Home() {
  const { featuredRaw, allProducts, categories } = await getHomeCatalog();

  const featured = featuredRaw.length > 0 ? featuredRaw : allProducts.slice(0, 8);
  const heroProduct = featured[0] ?? allProducts[0];
  const recommended = featured.slice(0, 5);
  const arrivals = allProducts.slice(0, 8);
  const promoCategories = categories.slice(0, 2);

  return (
    <div>
      <section className="relative min-h-[calc(100vh-4rem)] overflow-hidden bg-[#171717] text-bone lg:min-h-screen">
        <div className="mx-auto grid max-w-7xl items-center gap-10 px-4 py-12 sm:px-6 lg:grid-cols-[0.82fr_1.18fr] lg:px-8 lg:py-0">
          <div className="relative z-10 max-w-xl py-10 lg:py-24">
            <p className="mb-5 text-sm font-bold uppercase tracking-[0.18em] text-wine">
              from {heroProduct ? formatPrice(heroProduct.price) : "the new edit"}
            </p>
            <h1 className="text-5xl font-extrabold uppercase leading-[0.95] text-bone sm:text-7xl lg:text-8xl">
              2026
              <span className="block text-wine">summer collection</span>
            </h1>
            <p className="mt-7 max-w-md text-sm leading-7 text-bone/70">
              {heroProduct
                ? `${heroProduct.name} leads the current Kaira edit, with the rest of the collection ready to browse.`
                : "The current Kaira edit is ready to browse."}
            </p>
            <Link href="/shop" className="site-btn focus-ring mt-9">
              Shop now
            </Link>
          </div>

          <div className="relative min-h-[26rem] lg:min-h-screen">
            <Image
              src={heroProduct?.images[0]?.image || PLACEHOLDER_IMAGE}
              alt={heroProduct?.images[0]?.alt || heroProduct?.name || "Kaira collection"}
              fill
              priority
              sizes="(min-width: 1024px) 65vw, 100vw"
              className="object-cover object-center"
            />
            <div className="absolute inset-0 bg-gradient-to-r from-[#171717] via-[#171717]/25 to-transparent lg:from-[#171717]/80" />
          </div>
        </div>
      </section>

      {recommended.length > 0 && (
        <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
          <div className="mb-10 text-center">
            <h2 className="section-title">Premium products</h2>
            <p className="mt-3 text-sm font-semibold text-muted">We recommend</p>
          </div>
          <div className="grid grid-cols-2 gap-x-5 gap-y-12 md:grid-cols-3 xl:grid-cols-5">
            {recommended.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        </section>
      )}

      {promoCategories.length > 0 && (
        <section className="grid md:grid-cols-2">
          {promoCategories.map((category) => (
            <Link
              key={category.id}
              href={`/shop?category=${category.slug}`}
              className="group relative min-h-[22rem] overflow-hidden bg-bone-2 focus-ring"
            >
              <Image
                src={category.image || PLACEHOLDER_IMAGE}
                alt={category.name}
                fill
                sizes="(min-width: 768px) 50vw, 100vw"
                className="object-cover transition-transform duration-700 group-hover:scale-[1.04]"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/65 via-black/10 to-transparent" />
              <div className="absolute bottom-8 left-8 right-8 text-bone">
                <p className="mb-3 text-xs font-bold uppercase tracking-[0.2em] text-bone/75">
                  See more
                </p>
                <h3 className="text-4xl font-extrabold uppercase leading-none">{category.name}</h3>
              </div>
            </Link>
          ))}
        </section>
      )}

      <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="mb-10 flex flex-col gap-5 border-b border-hairline pb-6 md:flex-row md:items-end md:justify-between">
          <div>
            <h2 className="section-title">New arrivals</h2>
            <div className="mt-5 flex flex-wrap gap-5 text-sm font-bold uppercase tracking-[0.12em]">
              <Link href="/shop?sort=new" className="focus-ring text-wine">
                New arrivals
              </Link>
              <Link href="/shop?sort=featured" className="focus-ring hover:text-wine">
                Recommended
              </Link>
              <Link href="/shop?sort=price-desc" className="focus-ring hover:text-wine">
                Best sellers
              </Link>
            </div>
          </div>
          <Link href="/shop" className="site-btn-outline focus-ring">
            See more
          </Link>
        </div>

        {arrivals.length > 0 ? (
          <div className="grid grid-cols-2 gap-x-5 gap-y-12 lg:grid-cols-4">
            {arrivals.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        ) : (
          <div className="border border-hairline py-16 text-center text-sm text-muted">
            New products are coming soon.
          </div>
        )}
      </section>

      <section className="bg-bone-2 px-4 py-16 sm:px-6 lg:px-8">
        <div className="mx-auto grid max-w-7xl gap-8 md:grid-cols-3">
          {[
            [
              "10 tips to dress like a queen",
              "Dresses, tailoring, and small details that keep the edit polished.",
            ],
            [
              "Fashion outlet products",
              "A closer look at the pieces customers return to each season.",
            ],
            [
              "The little black dress just for you",
              "Simple lines, exact fits, and outfits that work after sunset.",
            ],
          ].map(([title, body]) => (
            <article key={title} className="border-t border-ink/20 pt-6">
              <p className="mb-4 text-xs font-bold uppercase tracking-[0.16em] text-wine">
                From the blog
              </p>
              <h3 className="text-xl font-extrabold uppercase leading-tight">{title}</h3>
              <p className="mt-4 text-sm leading-6 text-muted">{body}</p>
              <Link
                href="/shop"
                className="focus-ring mt-6 inline-block text-xs font-bold uppercase tracking-[0.16em] hover:text-wine"
              >
                Read more
              </Link>
            </article>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="grid gap-8 border-y border-hairline py-12 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
          <div>
            <p className="section-eyebrow mb-3">Get 20% off</p>
            <h2 className="section-title max-w-2xl">Join our list for early access</h2>
          </div>
          <form className="grid gap-3 sm:grid-cols-[1fr_auto]">
            <label className="sr-only" htmlFor="newsletter-email">
              Email address
            </label>
            <input
              id="newsletter-email"
              type="email"
              placeholder="Enter your email address"
              className="field-input"
            />
            <button type="submit" className="site-btn focus-ring">
              Subscribe
            </button>
          </form>
        </div>
      </section>
    </div>
  );
}
