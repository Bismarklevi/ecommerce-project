import {
  ProductGridSkeleton,
  Skeleton,
  SkeletonScreen,
  TextLinesSkeleton,
} from "@/components/Skeleton";

export default function ProductLoading() {
  return (
    <SkeletonScreen>
      <div className="mx-auto max-w-7xl px-4 pt-6 sm:px-6 lg:px-8">
        <Skeleton className="h-3 w-56" />
      </div>

      <div className="mx-auto grid max-w-7xl gap-10 px-4 py-8 sm:px-6 md:grid-cols-2 lg:gap-16 lg:px-8">
        <div className="space-y-4">
          <Skeleton className="aspect-[3/4] w-full" />
          <div className="grid grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="aspect-square" />
            ))}
          </div>
        </div>

        <div>
          <Skeleton className="h-3 w-24" />
          <Skeleton className="mt-4 h-9 w-4/5" />
          <Skeleton className="mt-5 h-6 w-28" />
          <div className="mt-8">
            <TextLinesSkeleton lines={4} />
          </div>
          <div className="mt-8 flex gap-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-11 w-12" />
            ))}
          </div>
          <Skeleton className="mt-8 h-14 w-full rounded-full" />
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <Skeleton className="mb-8 h-8 w-64" />
        <ProductGridSkeleton count={3} />
      </div>
    </SkeletonScreen>
  );
}
