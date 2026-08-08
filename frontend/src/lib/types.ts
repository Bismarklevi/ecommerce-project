// Shapes mirror the Django REST routes seen in urls.py:
// /api/products/, /api/categories/, /api/cart/, /api/orders/.

export interface Category {
  id: number;
  slug: string;
  name: string;
  image: string;
}

export interface ProductImage {
  id: number;
  image: string;
  alt: string;
}

export interface ProductVariant {
  id: number;
  size: string;
  inStock: boolean;
}

export interface Product {
  id: number;
  slug: string;
  name: string;
  description: string;
  price: string;
  compare_at_price: string | null;
  category: Category;
  images: ProductImage[];
  sizes: string[];
  variants: ProductVariant[];
  fabric: string;
  in_stock: boolean;
  look_number: string;
  is_new: boolean;
}

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
}

export interface CartLineItem {
  id: number;
  product_variant: {
    id: number;
    size: string;
    color: string;
    product: number;
  };
  quantity: number;
  unit_price: string;
  line_total: string;
  product_name: string;
  product_slug: string;
  product_image: string;
}

export interface Cart {
  id: number;
  items: CartLineItem[];
  item_count: number;
  subtotal: string;
}

export interface OrderItem {
  id: number;
  product_name: string;
  size: string;
  color: string;
  quantity: number;
  unit_price: string;
  line_total: string;
}

export interface Order {
  id: number;
  status: string;
  payment_status: string;
  total_amount: string;
  shipping_name: string;
  shipping_email: string;
  shipping_phone: string;
  shipping_address: string;
  shipping_cost: string;
  tracking_number: string;
  items: OrderItem[];
  item_count: number;
  created_at: string;
}
