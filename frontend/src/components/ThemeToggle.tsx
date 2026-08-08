"use client";

import { useCallback, useSyncExternalStore } from "react";

// Reflect the <html class="dark"> flag the no-flash theme script sets before
// React hydrates. useSyncExternalStore is the idiomatic way to read
// browser-only state without a set-state-in-effect: the server snapshot is
// null (theme unknown until the client), so the first paint renders a neutral
// placeholder that matches the server HTML -- no hydration mismatch -- and the
// MutationObserver keeps the icon correct if the class changes anywhere.
function subscribe(callback: () => void) {
  const observer = new MutationObserver(callback);
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
  return () => observer.disconnect();
}

function getSnapshot(): boolean {
  return document.documentElement.classList.contains("dark");
}

function getServerSnapshot(): boolean | null {
  return null;
}

export default function ThemeToggle() {
  const isDark = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  const toggle = useCallback(() => {
    const next = !document.documentElement.classList.contains("dark");
    document.documentElement.classList.toggle("dark", next);
    try {
      localStorage.setItem("kaira-theme", next ? "dark" : "light");
    } catch {
      // Private browsing / storage disabled -- theme just won't persist.
    }
    // No setState: the MutationObserver above observes the class change and
    // useSyncExternalStore re-renders this component.
  }, []);

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      className="focus-ring flex h-9 w-9 items-center justify-center text-ink transition-colors hover:text-wine"
    >
      {isDark === null ? (
        <span className="block h-[18px] w-[18px]" />
      ) : isDark ? (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="4.5" />
          <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
        </svg>
      ) : (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z" />
        </svg>
      )}
    </button>
  );
}
