# Kaira — Product Requirements

_Reverse-engineered from the implemented system to serve as the reference going
forward. Kaira is a small-batch fashion storefront for the Ghanaian market._

## Goal

Let a shopper browse a curated clothing catalogue, add items to a cart, and pay
in Ghana Cedis via Paystack (cards + Mobile Money), while giving the shop owner
an admin dashboard to manage catalogue, orders, inventory, and fulfilment.

## Users

- **Shopper** — browses, registers, buys, tracks orders, manages their own data.
- **Staff / owner** — manages catalogue, inventory, orders, returns, and content
  through the Django (Unfold) admin; sees sales analytics on the dashboard.

## Screens (frontend routes)

| Route | Purpose |
|---|---|
| `/` | Home: featured products, category entry points |
| `/shop` | Catalogue with category filter + sort |
| `/product/[slug]` | Product detail, size selection, add to cart |
| `/cart` | Cart review, quantity edits |
| `/checkout` → `/checkout/success` | Address, order creation, Paystack redirect, confirmation |
| `/login` | Register / sign in |
| `/account` | Order history; data export + account deletion |
| `/privacy`, `/terms` | Legal |

## Data model (core)

- **User** (custom) — email-unique, phone, default shipping address.
- **Category / Product / ProductVariant / ProductImage / Review** — catalogue.
  Stock lives on the variant.
- **Cart / CartItem** — one cart per user.
- **Order / OrderItem** — created from the cart; line items freeze name/price at
  purchase time. Governed by a status **state machine** (see ADR-0003 context in
  `app/models.py`): pending → paid → processing → shipped → delivered → completed,
  with cancelled/returned branches.
- **Payment** — one per order; Paystack reference + status; source of truth is the
  webhook, never the browser.
- **Address, WishlistItem, Coupon/CouponRedemption, ShippingZone, ReturnRequest,
  Banner/ContentBlock, Notification** — supporting domains.

## Key rules / edge cases (all enforced in code + tests)

- **No overselling**: stock is reserved with a `select_for_update` row lock at
  order creation; released on payment failure / cancellation / return.
- **Payment truth**: an order is only marked paid by the HMAC-verified Paystack
  webhook. Client "success" is never trusted. Webhook handling is idempotent and
  tolerant of out-of-order / duplicate delivery.
- **Authorization**: every cart/order/payment/address query is scoped to the
  requesting user — no cross-account access.
- **Rate limiting**: login / register / password-reset / checkout are throttled.
- **Data rights**: shoppers can export or erase their data (GDPR / Act 843);
  erasure anonymises retained order records rather than deleting them.

## Out of scope (today)

- Guest checkout (every order requires an account).
- Multi-currency (GHS only).
- A double-entry accounting ledger (Paystack + Payment records are the current
  reconciliation model — revisit if disputes/accounting volume grows).
- Discount/compare-at pricing on the storefront.
