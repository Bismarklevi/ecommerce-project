"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";

export interface Look {
  label: string;
  image: string;
  href: string;
  tint: string;
}

const ROTATE_MS = 4000;

/**
 * An accordion carousel: the panels share one row, and the active one grows
 * while the others shrink. Nothing slides -- the movement is the widths
 * themselves changing, so the images stay put and only their frames resize.
 */
export default function LookAccordion({ looks }: { looks: Look[] }) {
  const [active, setActive] = useState(0);
  // Hovering or focusing only PAUSES the cycle -- it used to stop it for good,
  // which meant one pass of the cursor over the section killed the animation
  // for the rest of the visit. It resumes as soon as the pointer leaves.
  const [paused, setPaused] = useState(false);
  const reduced = useRef(false);
  const trackRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    reduced.current = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }, []);

  // Keep the active panel in view. scrollLeft on the track itself rather than
  // scrollIntoView, which would also scroll every ancestor -- including the
  // page -- and yank the section around as the carousel advances.
  useEffect(() => {
    const track = trackRef.current;
    if (!track) return;
    // Do NOT measure the active panel's position here. At this moment the
    // widths have not transitioned yet: the previous panel is still wide, and
    // over the next 700ms it shrinks and drags everything after it left by one
    // collapsed width -- so a target read from the current layout lands one
    // panel short, and a fourth card leaks in at the edge.
    // Compute from the settled layout instead: every panel before the active
    // one ends up collapsed, so its final left edge is index * (width + gap).
    const panels = Array.from(track.querySelectorAll<HTMLElement>(".look-panel"));
    if (!panels.length) return;
    // The collapsed rest width is the smallest on the row: the shrinking one is
    // still on its way down to it, and the growing one is above it.
    const collapsed = Math.min(...panels.map((el) => el.getBoundingClientRect().width));
    const gap = parseFloat(getComputedStyle(track).columnGap) || 0;
    track.scrollTo({
      left: active * (collapsed + gap),
      behavior: reduced.current ? "auto" : "smooth",
    });
  }, [active]);

  useEffect(() => {
    if (paused || reduced.current || looks.length < 2) return;
    const id = window.setInterval(() => setActive((i) => (i + 1) % looks.length), ROTATE_MS);
    return () => window.clearInterval(id);
  }, [paused, looks.length]);

  return (
    // The track is wider than the viewport on purpose: panels keep fixed widths
    // instead of sharing the row, so the ones past the right edge simply are not
    // seen until the carousel travels to them. Native scroll, so it still swipes
    // on touch and drags with a trackpad.
    <div
      ref={trackRef}
      // No horizontal padding here on purpose: padding on a scroll container is
      // not a mask, so the next panel renders straight into it and a fourth card
      // leaks past the right edge. The gutter lives on the wrapper instead, and
      // the track clips at its own content box.
      className="no-scrollbar flex gap-4 overflow-x-auto scroll-smooth pb-2"
    >
      {looks.map((look, index) => {
        const isActive = index === active;
        return (
          <Link
            key={look.label}
            href={look.href}
            onMouseEnter={() => {
              setPaused(true);
              setActive(index);
            }}
            onMouseLeave={() => setPaused(false)}
            onFocus={() => {
              setPaused(true);
              setActive(index);
            }}
            onBlur={() => setPaused(false)}
            aria-current={isActive}
            data-panel={index}
            className={`focus-ring group relative h-[22rem] shrink-0 overflow-hidden rounded-3xl border-2 border-ink transition-[width] duration-700 ease-[cubic-bezier(0.16,1,0.3,1)] sm:h-[28rem] ${
              // Sized so exactly three panels fill the track and the fourth is
              // fully past the edge. With a 16px gap and the wide panel at twice
              // the others: 4w + 2*16px = 100%, so w = 25% - 8px.
              // The underscores are load-bearing: Tailwind emits arbitrary
              // values verbatim, and CSS calc() is invalid without whitespace
              // around the operator -- "calc(25%-8px)" is dropped outright.
              isActive ? "look-panel look-panel--active" : "look-panel"
            }`}
            style={{ background: look.tint }}
          >
            <Image
              src={look.image}
              alt=""
              fill
              sizes="(min-width: 640px) 50vw, 70vw"
              className="object-cover transition-transform duration-700 ease-out group-hover:scale-[1.04]"
            />

            {/* With seven panels a collapsed one is far too narrow for a pill,
                so the label fades out with the width. Opacity keeps it in the
                accessibility tree, so the link is still named when collapsed --
                the image itself is decorative and carries no alt. */}
            <span
              className={`absolute bottom-5 left-5 z-[1] whitespace-nowrap rounded-full bg-[#221018] px-4 py-2 text-xs font-semibold text-[#fefaf1] transition-opacity duration-500 ${
                isActive ? "opacity-100" : "opacity-100 sm:opacity-0"
              }`}
            >
              {look.label}
            </span>
          </Link>
        );
      })}
    </div>
  );
}
