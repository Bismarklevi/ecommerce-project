import { Skeleton, SkeletonScreen } from "@/components/Skeleton";

export default function AccountLoading() {
  return (
    <SkeletonScreen className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
      <Skeleton className="h-3 w-20" />
      <Skeleton className="mb-4 mt-3 h-9 w-72" />
      <Skeleton className="mb-10 h-3 w-40" />

      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-28 w-full" />
        ))}
      </div>
    </SkeletonScreen>
  );
}
