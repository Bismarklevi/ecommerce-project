"use client";

import { usePathname } from "next/navigation";
import { useEffect } from "react";

/** Gap between siblings in a [data-reveal-children] group. */
const STAGGER_MS = 80;

/** Beyond this many siblings the stagger stops growing, so a long grid's last
 *  item doesn't arrive a second and a half after its first. */
const MAX_STAGGER_STEPS = 6;

/**
 * The sections to animate are the children of <main> -- except most pages wrap
 * everything in a single <div>, and some wrap that again. Taking <main>'s
 * children literally would match one full-page wrapper, which is on screen at
 * load and so reveals instantly, animating nothing. Descend through any
 * single-child chain first to find the level where the sections actually are.
 */
function findSectionParent(main: HTMLElement): HTMLElement {
  let node = main;
  while (node.childElementCount === 1) {
    const only = node.firstElementChild;
    if (!(only instanceof HTMLElement)) break;
    node = only;
  }
  return node;
}

/**
 * Fades sections up as they scroll into view.
 *
 * Three ways in:
 *   - every section (the children of <main>), automatically;
 *   - `data-reveal` on anything else that should arrive on its own;
 *   - `data-reveal-children` on a container, which reveals each child in turn
 *     with a stagger, so a grid deals itself out rather than landing flat.
 * `data-no-reveal` opts an element out.
 *
 * Progressive enhancement, deliberately: the CSS only hides anything once this
 * component has added `reveal-ready` to <html>. If the bundle fails or JS is
 * off, nothing is ever hidden and the page reads exactly as it does now --
 * the failure mode of the naive version (hide in CSS, reveal in JS) is a blank
 * page, which is not a trade worth making for a fade.
 */
export default function ScrollReveal() {
  // Re-run per navigation: App Router keeps this mounted across routes, so
  // without this the next page's sections never get observed.
  const pathname = usePathname();

  useEffect(() => {
    const root = document.documentElement;

    // Honour the OS setting. Checked here rather than only in CSS so we skip
    // the observer work entirely instead of animating into a no-op.
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    if (!("IntersectionObserver" in window)) return;

    const main = document.querySelector("main");
    if (!main) return;

    root.classList.add("reveal-ready");

    const registered = new Set<HTMLElement>();

    /**
     * Hand the element back to its own stylesheet once it has arrived.
     *
     * This matters more than it looks: `.reveal` sets a transition (and, for a
     * staggered child, a transition-delay) that outranks Tailwind's own
     * `transition-*` classes. Leaving it in place would make a hover on, say, a
     * category pill wait out its reveal delay before moving. The resting state
     * is opacity 1 / no transform either way, so dropping the classes changes
     * nothing visually.
     */
    function settle(el: HTMLElement) {
      let done = false;
      const finish = () => {
        if (done) return;
        done = true;
        window.clearTimeout(timer);
        el.classList.remove("reveal", "is-revealed");
        el.style.removeProperty("--reveal-delay");
      };
      // transitionend fires per property and can be missed entirely if the
      // element is scrolled out mid-transition, so a timeout backs it up.
      const delay = Number.parseInt(el.style.getPropertyValue("--reveal-delay"), 10) || 0;
      const timer = window.setTimeout(finish, delay + 900);
      el.addEventListener("transitionend", finish, { once: true });
    }

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (!entry.isIntersecting) continue;
          if (!(entry.target instanceof HTMLElement)) continue;
          entry.target.classList.add("is-revealed");
          settle(entry.target);
          // One-way: a section that has arrived stays arrived. Re-hiding on
          // scroll-up reads as a glitch rather than an effect.
          observer.unobserve(entry.target);
        }
      },
      // Fire a little before the element's top edge clears the fold, so the
      // motion finishes about when it is properly in view.
      { rootMargin: "0px 0px -12% 0px", threshold: 0.05 },
    );

    function register(el: HTMLElement, delayMs = 0) {
      if (registered.has(el) || el.hasAttribute("data-no-reveal")) return;
      registered.add(el);
      el.classList.add("reveal");
      if (delayMs) el.style.setProperty("--reveal-delay", `${delayMs}ms`);

      // Anything already on screen at load (the hero, chiefly) is revealed
      // immediately -- it should not fade in under a viewport it already fills.
      if (el.getBoundingClientRect().top < window.innerHeight) {
        el.classList.add("is-revealed");
        settle(el);
        return;
      }
      observer.observe(el);
    }

    function scan() {
      if (!main) return;

      for (const child of findSectionParent(main).children) {
        if (child instanceof HTMLElement) register(child);
      }
      for (const el of main.querySelectorAll<HTMLElement>("[data-reveal]")) {
        register(el);
      }
      for (const group of main.querySelectorAll<HTMLElement>("[data-reveal-children]")) {
        let step = 0;
        for (const child of group.children) {
          if (!(child instanceof HTMLElement)) continue;
          register(child, Math.min(step, MAX_STAGGER_STEPS) * STAGGER_MS);
          step += 1;
        }
      }
    }

    scan();

    // Sections behind a <Suspense> boundary (the homepage's product carousel
    // and category band) land in the DOM after this effect has run, so a
    // one-shot scan would miss them entirely and leave them unanimated.
    // Re-scanning on mutation catches them whenever they stream in. Only
    // childList is observed, so the classes and custom properties set above
    // don't feed back into this.
    let queued = 0;
    const mutations = new MutationObserver(() => {
      if (queued) return;
      queued = requestAnimationFrame(() => {
        queued = 0;
        scan();
      });
    });
    mutations.observe(main, { childList: true, subtree: true });

    return () => {
      if (queued) cancelAnimationFrame(queued);
      mutations.disconnect();
      observer.disconnect();
      root.classList.remove("reveal-ready");
      for (const el of registered) {
        el.classList.remove("reveal", "is-revealed");
        el.style.removeProperty("--reveal-delay");
      }
    };
  }, [pathname]);

  return null;
}
