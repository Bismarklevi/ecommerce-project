"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export interface Testimonial {
  quote: string;
  name: string;
  handle: string;
}

const ROTATE_MS = 7000;

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

function QuoteMark({ className }: { className?: string }) {
  return (
    <svg aria-hidden="true" width="34" height="26" viewBox="0 0 34 26" className={className}>
      <path
        fill="currentColor"
        d="M0 26V14.3C0 6.6 4.4 1.2 12.6 0l1.5 3.9C9.4 5.4 7 8.2 7 11.4h5.8V26H0Zm19.9 0V14.3C19.9 6.6 24.3 1.2 32.5 0L34 3.9c-4.7 1.5-7.1 4.3-7.1 7.5h5.8V26H19.9Z"
      />
    </svg>
  );
}

export default function TestimonialCarousel({ items }: { items: Testimonial[] }) {
  const [index, setIndex] = useState(0);
  // Auto-rotation stops for good once someone uses the controls: a card that
  // moves itself while you are reading it is the whole complaint about
  // carousels, and having taken over, the reader keeps control.
  const [taken, setTaken] = useState(false);
  const [paused, setPaused] = useState(false);

  const count = items.length;
  const go = useCallback(
    (delta: number) => {
      setTaken(true);
      setIndex((i) => (i + delta + count) % count);
    },
    [count],
  );

  const reduced = useRef(false);
  useEffect(() => {
    reduced.current = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }, []);

  useEffect(() => {
    if (taken || paused || count < 2 || reduced.current) return;
    const id = window.setInterval(() => setIndex((i) => (i + 1) % count), ROTATE_MS);
    return () => window.clearInterval(id);
  }, [taken, paused, count]);

  if (!count) return null;
  const current = items[index];

  return (
    <div
      className="mx-auto max-w-3xl"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      // Pausing on focus-within matters more than the hover case: a keyboard
      // user tabbing to the handle link must not have it swapped mid-reach.
      onFocus={() => setPaused(true)}
      onBlur={() => setPaused(false)}
    >
      <figure className="surface-card relative border border-hairline px-7 pb-8 pt-12 text-center sm:px-12">
        <QuoteMark className="absolute left-6 top-6 text-wine/25" />

        {/* Only the contents swap, so the card itself never remounts and the
            shadow/border stay put. aria-live announces each new quote to a
            screen reader without moving focus. */}
        <div aria-live="polite" aria-atomic="true">
          <span
            aria-hidden="true"
            className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-sage text-base text-on-accent"
          >
            {current.name
              .split(" ")
              .map((part) => part[0])
              .join("")}
          </span>

          {/* A fixed floor under the quote: without it the card jumps height
              between a short testimonial and a long one on every rotation. */}
          <blockquote className="mx-auto mt-6 min-h-[7.5rem] max-w-xl text-base leading-8 text-ink sm:min-h-[6rem]">
            {current.quote}
          </blockquote>

          <figcaption className="mt-6 text-xs text-muted">
            <span className="block text-ink">{current.name}</span>
            <span className="mt-1 block">{current.handle}</span>
          </figcaption>
        </div>
      </figure>

      {count > 1 && (
        <div className="mt-6 flex items-center justify-center gap-4">
          <button
            type="button"
            onClick={() => go(-1)}
            aria-label="Previous testimonial"
            className="btn-hard-icon focus-ring"
          >
            <Arrow direction="prev" />
          </button>

          <div className="flex gap-2">
            {items.map((item, i) => (
              <button
                key={item.handle}
                type="button"
                onClick={() => {
                  setTaken(true);
                  setIndex(i);
                }}
                aria-label={`Testimonial ${i + 1} of ${count}`}
                aria-current={i === index}
                className={`focus-ring h-2.5 rounded-full transition-all ${
                  i === index ? "w-6 bg-ink" : "w-2.5 bg-ink/25 hover:bg-ink/50"
                }`}
              />
            ))}
          </div>

          <button
            type="button"
            onClick={() => go(1)}
            aria-label="Next testimonial"
            className="btn-hard-icon focus-ring"
          >
            <Arrow direction="next" />
          </button>
        </div>
      )}
    </div>
  );
}
