import { Suspense } from "react";
import ShopClient from "./ShopClient";
import ShopLoading from "./loading";

export const metadata = {
  title: "Shop - Kaira",
};

export default function ShopPage() {
  return (
    <Suspense fallback={<ShopLoading />}>
      <ShopClient />
    </Suspense>
  );
}
