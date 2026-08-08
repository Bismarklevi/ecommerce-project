import Image from "next/image";
import Link from "next/link";
import { Product } from "@/lib/types";
import { formatPrice } from "@/lib/currency";
import { PLACEHOLDER_IMAGE } from "@/lib/constants";

export default function ProductCard({ product }: { product: Product }) {
  const onSale = product.compare_at_price !== null;
  const primaryImage = product.images[0];

  return (
    <Link href={`/product/${product.slug}`} className="group block focus-ring">
      <div className="relative aspect-[3/4] overflow-hidden bg-bone-2">
        <Image
          src={primaryImage?.image || PLACEHOLDER_IMAGE}
          alt={primaryImage?.alt || product.name}
          fill
          sizes="(min-width: 1280px) 20vw, (min-width: 768px) 33vw, 50vw"
          className="object-cover transition-transform duration-700 ease-out group-hover:scale-[1.04]"
        />

        {(product.is_new || onSale) && (
          <span className="absolute left-4 top-4 bg-sage px-3 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-on-accent">
            {product.is_new ? "New" : "Sale"}
          </span>
        )}

        <div className="absolute inset-x-0 bottom-0 translate-y-full bg-ink px-4 py-4 text-center text-[11px] font-bold uppercase tracking-[0.18em] text-bone transition-transform duration-300 group-hover:translate-y-0">
          View product
        </div>
      </div>

      <div className="pt-5 text-center">
        <p className="mb-2 text-[11px] font-bold uppercase tracking-[0.16em] text-muted">
          {product.category.name}
        </p>
        <h3 className="text-base font-bold leading-snug text-ink transition-colors group-hover:text-wine">
          {product.name}
        </h3>
        <div className="mt-3 flex items-center justify-center gap-2 text-sm font-bold text-wine">
          <span>{formatPrice(product.price)}</span>
          {onSale && (
            <span className="text-xs text-muted line-through">
              {formatPrice(product.compare_at_price!)}
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}
