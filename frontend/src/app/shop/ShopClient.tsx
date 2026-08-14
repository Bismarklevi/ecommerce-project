"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { getCategories, getProducts } from "@/lib/api";
import { Category, Product } from "@/lib/types";
import ProductCard from "@/components/ProductCard";

type SortValue = "featured" | "price-asc" | "price-desc" | "new";

export default function ShopClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const activeCategory = searchParams.get("category") ?? "all";
  const activeSort = (searchParams.get("sort") as SortValue) ?? "featured";
  const activeSearch = searchParams.get("search") ?? "";

  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true);
    setError(null);
    Promise.all([getProducts({ category: activeCategory, sort: activeSort, search: activeSearch || undefined }), getCategories()])
      .then(([p, c]) => {
        if (cancelled) return;
        setProducts(p);
        setCategories(c);
        setLoading(false);
      })
      .catch((err) => {
        if (cancelled) return;
        console.error(err);
        setError(
          "Couldn't load products right now. If you're running this locally, make sure the Django backend is started (python manage.py runserver).",
        );
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [activeCategory, activeSort, activeSearch]);

  function setParam(key: string, value: string) {
    const params = new URLSearchParams(searchParams.toString());
    if (value === "all" || value === "featured" || value === "") {
      params.delete(key);
    } else {
      params.set(key, value);
    }
    router.push(`/shop${params.toString() ? `?${params}` : ""}`, { scroll: false });
  }

  return (
    <div>
      <section className="border-b border-hairline bg-bone-2 px-4 py-14 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <p className="section-eyebrow mb-3">Full collection</p>
          <h1 className="section-title">Shop</h1>
          <p className="mt-5 max-w-2xl text-sm leading-7 text-muted">
            Discover the latest styles, timeless classics, and premium essentials in the Kaira
            catalog.
          </p>
          {activeSearch && (
            <p className="mt-4 text-sm text-muted">
              Showing results for <span className="font-bold text-ink">&ldquo;{activeSearch}&rdquo;</span>
              {" - "}
              <button
                type="button"
                onClick={() => setParam("search", "")}
                className="focus-ring underline underline-offset-4 hover:text-wine"
              >
                clear search
              </button>
            </p>
          )}
        </div>
      </section>

      <div className="mx-auto grid max-w-7xl gap-10 px-4 py-12 sm:px-6 lg:grid-cols-[15rem_1fr] lg:px-8">
        <aside className="lg:sticky lg:top-8 lg:self-start">
          <div className="border-b border-hairline pb-6 lg:border-b-0 lg:border-r lg:pr-8">
            <p className="mb-5 text-xs font-bold uppercase tracking-[0.18em] text-ink">
              Categories
            </p>
            <div className="flex flex-wrap gap-2 lg:flex-col lg:items-start">
              <button
                type="button"
                onClick={() => setParam("category", "all")}
                className={`focus-ring text-sm font-bold uppercase tracking-[0.12em] transition-colors ${
                  activeCategory === "all" ? "text-wine" : "text-ink hover:text-wine"
                }`}
              >
                All
              </button>
              {categories.map((c) => (
                <button
                  key={c.id}
                  type="button"
                  onClick={() => setParam("category", c.slug)}
                  className={`focus-ring text-sm font-bold uppercase tracking-[0.12em] transition-colors ${
                    activeCategory === c.slug ? "text-wine" : "text-ink hover:text-wine"
                  }`}
                >
                  {c.name}
                </button>
              ))}
            </div>

            <div className="mt-8">
              <label
                htmlFor="sort"
                className="mb-3 block text-xs font-bold uppercase tracking-[0.18em] text-ink"
              >
                Sort by
              </label>
              <select
                id="sort"
                value={activeSort}
                onChange={(e) => setParam("sort", e.target.value)}
                className="field-input focus-ring"
              >
                <option value="featured">Featured</option>
                <option value="new">Newest</option>
                <option value="price-asc">Price: Low to High</option>
                <option value="price-desc">Price: High to Low</option>
              </select>
            </div>
          </div>
        </aside>

        <section>
          <div className="mb-8 flex items-center justify-between border-b border-hairline pb-5">
            <p className="text-sm text-muted">
              {loading
                ? "Loading products"
                : `${products.length} product${products.length === 1 ? "" : "s"}`}
            </p>
            <div className="hidden gap-5 text-sm font-bold uppercase tracking-[0.12em] md:flex">
              <button
                onClick={() => setParam("sort", "new")}
                className="focus-ring hover:text-wine"
              >
                New arrivals
              </button>
              <button
                onClick={() => setParam("sort", "featured")}
                className="focus-ring hover:text-wine"
              >
                Recommended
              </button>
              <button
                onClick={() => setParam("sort", "price-desc")}
                className="focus-ring hover:text-wine"
              >
                Best sellers
              </button>
            </div>
          </div>

          {error ? (
            <div className="border border-wine/40 bg-wine/5 py-16 text-center px-6">
              <p className="text-xl font-extrabold uppercase text-wine">
                Couldn&apos;t load products
              </p>
              <p className="mt-3 text-sm text-muted">{error}</p>
            </div>
          ) : loading ? (
            <div className="grid grid-cols-2 gap-x-5 gap-y-12 lg:grid-cols-3 xl:grid-cols-4">
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="animate-pulse">
                  <div className="aspect-[3/4] bg-bone-2" />
                  <div className="mx-auto mt-5 h-4 w-3/4 bg-bone-2" />
                  <div className="mx-auto mt-3 h-3 w-1/2 bg-bone-2" />
                </div>
              ))}
            </div>
          ) : products.length === 0 ? (
            <div className="border border-hairline py-24 text-center">
              <p className="text-xl font-extrabold uppercase">
                {activeSearch ? `Nothing matched "${activeSearch}"` : "Nothing here yet"}
              </p>
              <p className="mt-3 text-sm text-muted">
                {activeSearch
                  ? "Try a shorter search, or browse by category instead."
                  : "Try a different category."}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-x-5 gap-y-12 lg:grid-cols-3 xl:grid-cols-4">
              {products.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
