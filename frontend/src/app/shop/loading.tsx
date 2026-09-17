import { ProductGridSkeleton, Skeleton, SkeletonScreen } from "@/components/Skeleton";

// Doubles as the route's loading.tsx and as the Suspense fallback in page.tsx,
// so the wait for useSearchParams and the wait for the products look the same.
export default function ShopLoading() {
  return (
    <SkeletonScreen>
      <section className="border-b border-hairline px-4 py-10 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <Skeleton className="h-3 w-32" />
          <Skeleton className="mt-3 h-10 w-40" />
          <Skeleton className="mt-5 h-3 w-full max-w-2xl" />
        </div>
      </section>

      <div className="mx-auto grid max-w-7xl gap-10 px-4 py-10 sm:px-6 lg:grid-cols-[15rem_1fr] lg:px-8">
        <aside>
          <Skeleton className="h-3 w-24" />
          <div className="mt-5 flex flex-wrap gap-2 lg:flex-col lg:items-start">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-4 w-28" />
            ))}
          </div>
          <Skeleton className="mt-8 h-3 w-20" />
          <Skeleton className="mt-3 h-12 w-full" />
        </aside>

        <section>
          <div className="mb-8 flex items-center justify-between border-b border-hairline pb-5">
            <Skeleton className="h-3 w-24" />
            <Skeleton className="hidden h-3 w-64 md:block" />
          </div>
          <ProductGridSkeleton />
        </section>
      </div>
    </SkeletonScreen>
  );
}
