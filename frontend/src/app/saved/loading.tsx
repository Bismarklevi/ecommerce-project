import { ProductGridSkeleton, Skeleton, SkeletonScreen } from "@/components/Skeleton";

export default function SavedLoading() {
  return (
    <SkeletonScreen className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <Skeleton className="h-3 w-24" />
      <Skeleton className="mt-3 h-9 w-64" />
      <Skeleton className="mb-10 mt-5 h-3 w-full max-w-lg" />
      <ProductGridSkeleton count={6} />
    </SkeletonScreen>
  );
}
