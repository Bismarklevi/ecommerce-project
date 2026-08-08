"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { Cart } from "./types";

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
}

const CartContext = createContext<CartContextValue | null>(null);

export function CartProvider({ children }: { children: React.ReactNode }) {
  const [cart, setCart] = useState<Cart | null>(null);
  const [loading, setLoading] = useState(true);
  const [signedIn, setSignedIn] = useState<boolean | undefined>(undefined);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/cart");
      if (response.status === 401) {
        setSignedIn(false);
        setCart(null);
        return;
      }
      if (response.ok) {
        setSignedIn(true);
        setCart(await response.json());
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refresh();
  }, [refresh]);

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
      value={{ cart, loading, signedIn, count, refresh, addItem, updateQuantity, removeItem }}
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
