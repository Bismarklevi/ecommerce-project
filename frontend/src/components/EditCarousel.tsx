"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { Product } from "@/lib/types";
import ProductCard from "./ProductCard";

function Arrow({ direction }: { direction: "prev" | "next" }) {
  return (
    <svg
      aria-hidden="true"
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={direction === "prev" ? "rotate-180" : undefined}
    >
      <path d="M5 12h14M13 6l6 6-6 6" />
    </svg>
  );
}

export default function EditCarousel({ products }: { products: Product[] }) {
  const trackRef = useRef<HTMLDivElement>(null);
  const [atStart, setAtStart] = useState(true);
  const [atEnd, setAtEnd] = useState(false);

  // Drive the arrows from the track's real scroll position rather than an
  // index we maintain ourselves -- the track is also swipeable and keyboard
  // scrollable, so any index we tracked separately would drift out of sync.
  const syncEdges = useCallback(() => {
    const el = trackRef.current;
    if (!el) return;
    const max = el.scrollWidth - el.clientWidth;
    setAtStart(el.scrollLeft <= 1);
    setAtEnd(el.scrollLeft >= max - 1);
  }, []);

  useEffect(() => {
    const el = trackRef.current;
    if (!el) return;
    syncEdges();
    el.addEventListener("scroll", syncEdges, { passive: true });
    window.addEventListener("resize", syncEdges);
    return () => {
      el.removeEventListener("scroll", syncEdges);
      window.removeEventListener("resize", syncEdges);
    };
  }, [syncEdges]);

  const scrollByPage = useCallback((dir: 1 | -1) => {
    const el = trackRef.current;
    if (!el) return;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    el.scrollBy({ left: dir * el.clientWidth * 0.85, behavior: reduced ? "auto" : "smooth" });
  }, []);

  if (products.length === 0) {
    return (
      <div className="surface-card border border-hairline py-12 text-center text-sm text-muted">
        New pieces are coming soon.
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex justify-end gap-3">
        <button
          type="button"
          onClick={() => scrollByPage(-1)}
          disabled={atStart}
          aria-label="Previous products"
          className="btn-hard-icon focus-ring"
        >
          <Arrow direction="prev" />
        </button>
        <button
          type="button"
          onClick={() => scrollByPage(1)}
          disabled={atEnd}
          aria-label="Next products"
          className="btn-hard-icon focus-ring"
        >
          <Arrow direction="next" />
        </button>
      </div>

      {/* A plain scroll container, so it still swipes on touch and scrolls with
          the keyboard if the arrows' JS never loads. */}
      <div
        ref={trackRef}
        className="no-scrollbar flex snap-x snap-mandatory gap-8 overflow-x-auto pb-3"
      >
        {products.map((product) => (
          <div key={product.id} className="edit-slide w-[84%] shrink-0 snap-start sm:w-[48%]">
            <ProductCard product={product} />
          </div>
        ))}
      </div>
    </div>
  );
}
