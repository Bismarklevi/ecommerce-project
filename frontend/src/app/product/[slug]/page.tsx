import { notFound } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { getProductBySlug, getRelatedProducts } from "@/lib/api";
import { formatPrice } from "@/lib/currency";
import { PLACEHOLDER_IMAGE } from "@/lib/constants";
import ProductCard from "@/components/ProductCard";
import AddToCartForm from "./AddToCartForm";

export const dynamic = "force-dynamic";

export default async function ProductPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const product = await getProductBySlug(slug);

  if (!product) notFound();

  const related = await getRelatedProducts(product, 4);
  const onSale = product.compare_at_price !== null;

  return (
    <div>
      <div className="mx-auto max-w-7xl px-4 pt-6 sm:px-6 lg:px-8">
        <nav className="text-right text-xs uppercase tracking-[0.12em] text-muted sm:text-left">
          <Link href="/shop" className="focus-ring hover:text-wine">
            Shop
          </Link>
          <span className="mx-2">/</span>
          <Link
            href={`/shop?category=${product.category.slug}`}
            className="focus-ring hover:text-wine"
          >
            {product.category.name}
          </Link>
          <span className="mx-2">/</span>
          <span className="text-ink">{product.name}</span>
        </nav>
      </div>

      <div className="mx-auto grid max-w-7xl gap-10 px-4 py-8 sm:px-6 md:grid-cols-2 lg:gap-16 lg:px-8">
        <div className="space-y-4">
          <div className="relative aspect-[3/4] bg-bone-2">
            <Image
              src={product.images[0]?.image || PLACEHOLDER_IMAGE}
              alt={product.images[0]?.alt || product.name}
              fill
              priority
              sizes="(min-width: 1024px) 42vw, 100vw"
              className="object-cover"
            />
            <span className="absolute right-4 top-4 bg-ink px-3 py-2 text-xs font-bold uppercase tracking-[0.14em] text-bone">
              No. {product.look_number}
            </span>
          </div>
          {product.images.length > 1 && (
            <div className="grid grid-cols-4 gap-4">
              {product.images.slice(1).map((img) => (
                <div key={img.id} className="relative aspect-[3/4] bg-bone-2">
                  <Image src={img.image} alt={img.alt} fill sizes="20vw" className="object-cover" />
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="md:pt-8">
          <p className="section-eyebrow mb-3">{product.category.name}</p>
          <h1 className="text-4xl font-extrabold uppercase leading-tight sm:text-5xl">
            {product.name}
          </h1>

          <div className="mt-6 flex items-baseline gap-3 text-xl font-bold">
            {onSale && (
              <span className="text-base text-muted line-through">
                {formatPrice(product.compare_at_price!)}
              </span>
            )}
            <span className={onSale ? "text-wine" : "text-ink"}>{formatPrice(product.price)}</span>
          </div>

          <p className="mt-7 max-w-lg text-sm leading-7 text-muted">{product.description}</p>

          <div className="mt-8 border-y border-hairline py-8">
            <AddToCartForm product={product} />
          </div>

          <dl className="mt-8 grid grid-cols-2 gap-y-4 text-sm">
            {product.fabric && (
              <>
                <dt className="font-bold uppercase tracking-[0.12em] text-muted">Fabric</dt>
                <dd>{product.fabric}</dd>
              </>
            )}
            <dt className="font-bold uppercase tracking-[0.12em] text-muted">Availability</dt>
            <dd>{product.in_stock ? "In stock" : "Sold out"}</dd>
            <dt className="font-bold uppercase tracking-[0.12em] text-muted">Look number</dt>
            <dd>No. {product.look_number}</dd>
          </dl>
        </div>
      </div>

      {related.length > 0 && (
        <section className="mx-auto max-w-7xl border-t border-hairline px-4 py-16 sm:px-6 lg:px-8">
          <div className="mb-10 text-center">
            <h2 className="section-title">You may also like</h2>
          </div>
          <div className="grid grid-cols-2 gap-x-5 gap-y-12 lg:grid-cols-4">
            {related.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
