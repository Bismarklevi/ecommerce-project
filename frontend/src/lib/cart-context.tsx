"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { Cart } from "./types";

// productId -> wishlist row id, or null once we know it is NOT saved. The null
// matters: a product absent from the map is "unknown", a null is "checked and
// unsaved", and callers with their own initial state fall back only on unknown.
type SavedMap = Record<number, number | null>;

interface CartContextValue {
  cart: Cart | null;
  loading: boolean;
  // undefined = "haven't checked yet", false = "checked, signed out"
  signedIn: boolean | undefined;
  count: number;
  refresh: () => Promise<void>;
  addItem: (
    variantId: number,
    quantity?: number,
  ) => Promise<{ ok: true } | { ok: false; detail: string }>;
  updateQuantity: (itemId: number, quantity: number) => Promise<void>;
  removeItem: (itemId: number) => Promise<void>;
  savedIds: SavedMap;
  setSavedId: (productId: number, wishlistId: number | null) => void;
}

const CartContext = createContext<CartContextValue | null>(null);

export function CartProvider({ children }: { children: React.ReactNode }) {
  const [cart, setCart] = useState<Cart | null>(null);
  const [loading, setLoading] = useState(true);
  const [signedIn, setSignedIn] = useState<boolean | undefined>(undefined);
  const [savedIds, setSavedIds] = useState<SavedMap>({});

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/cart");
      const data = await response.json().catch(() => null);
      // The proxy answers 200 {signed_in:false} for a visitor with no session,
      // so an ordinary page view no longer logs a 401 in the console. A real
      // 401 still means the same thing (a stale token the proxy just cleared).
      if (response.status === 401 || data?.signed_in === false) {
        setSignedIn(false);
        setCart(null);
        setSavedIds({});
        return;
      }
      if (response.ok) {
        setSignedIn(true);
        setCart(data);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refresh();
  }, [refresh]);

  // One wishlist fetch per session, so every ProductCard on every page can
  // render its heart in the right state instead of always starting unsaved.
  useEffect(() => {
    if (signedIn !== true) return;
    let cancelled = false;
    fetch("/api/wishlist")
      .then((r) => (r.ok ? r.json() : []))
      .then((items: { id: number; product: number }[]) => {
        if (cancelled) return;
        const map: SavedMap = {};
        for (const item of items) map[item.product] = item.id;
        setSavedIds(map);
      })
      .catch(() => {
        // Non-fatal: hearts just stay in their fallback state.
      });
    return () => {
      cancelled = true;
    };
  }, [signedIn]);

  const setSavedId = useCallback((productId: number, wishlistId: number | null) => {
    setSavedIds((prev) => ({ ...prev, [productId]: wishlistId }));
  }, []);

  const addItem = useCallback(async (variantId: number, quantity = 1) => {
    const response = await fetch("/api/cart", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ product_variant_id: variantId, quantity }),
    });
    if (response.status === 401) {
      setSignedIn(false);
      return { ok: false as const, detail: "Sign in to add items to your bag." };
    }
    const data = await response.json();
    if (!response.ok) {
      return { ok: false as const, detail: data.detail || "Could not add to bag." };
    }
    setCart(data);
    setSignedIn(true);
    return { ok: true as const };
  }, []);

  const updateQuantity = useCallback(async (itemId: number, quantity: number) => {
    const response = await fetch(`/api/cart/items/${itemId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ quantity }),
    });
    if (response.ok) setCart(await response.json());
  }, []);

  const removeItem = useCallback(async (itemId: number) => {
    const response = await fetch(`/api/cart/items/${itemId}`, { method: "DELETE" });
    if (response.ok) setCart(await response.json());
  }, []);

  const count = cart?.item_count ?? 0;

  return (
    <CartContext.Provider
      value={{
        cart,
        loading,
        signedIn,
        count,
        refresh,
        addItem,
        updateQuantity,
        removeItem,
        savedIds,
        setSavedId,
      }}
    >
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error("useCart must be used within CartProvider");
  return ctx;
}
