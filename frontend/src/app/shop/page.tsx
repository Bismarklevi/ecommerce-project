import { Suspense } from "react";
import ShopClient from "./ShopClient";

export const metadata = {
  title: "Shop - Kaira",
};

export default function ShopPage() {
  return (
    <Suspense fallback={null}>
      <ShopClient />
    </Suspense>
  );
}
