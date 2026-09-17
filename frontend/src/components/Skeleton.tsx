// Shared loading placeholders. Every screen that waits on the backend draws
// from these, so a slow response looks the same everywhere instead of each
// route inventing its own spinner or "Loading..." line.
//
// The shapes deliberately trace the layout they stand in for -- same grid, same
// aspect ratios, same rough text widths -- so the page doesn't jump when the
// real content lands.

/** One shimmering block. `className` carries the size. */
export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded bg-bone-2 ${className}`} />;
}

/**
 * Wrapper for a full-screen loading state.
 *
 * The placeholder boxes themselves are meaningless to a screen reader, so the
 * region is labelled once and the shapes inside are left as decoration. The
 * polite live region means the announcement doesn't interrupt whatever the
 * user is doing.
 */
export function SkeletonScreen({
  className = "",
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <div role="status" aria-live="polite" aria-busy="true" className={className}>
      <span className="sr-only">Loading</span>
      <div aria-hidden="true">{children}</div>
    </div>
  );
}

/** Stand-in for a single ProductCard: image, size chips, category, name, price. */
export function ProductCardSkeleton() {
  return (
    <div>
      <Skeleton className="aspect-[3/4] w-full" />
      <div className="mt-4 flex gap-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-8 w-10" />
        ))}
      </div>
      <Skeleton className="mt-4 h-3 w-20" />
      <Skeleton className="mt-3 h-4 w-3/4" />
      <Skeleton className="mt-3 h-4 w-24" />
    </div>
  );
}

/** A grid of product placeholders on the same breakpoints as the real grids. */
export function ProductGridSkeleton({ count = 9 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 gap-x-5 gap-y-12 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: count }).map((_, i) => (
        <ProductCardSkeleton key={i} />
      ))}
    </div>
  );
}

/** A run of text lines, the last one short so it reads as a paragraph. */
export function TextLinesSkeleton({ lines = 3 }: { lines?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} className={`h-3 ${i === lines - 1 ? "w-1/2" : "w-full"}`} />
      ))}
    </div>
  );
}
