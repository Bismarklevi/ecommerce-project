# ADR-0001: Paystack for payments

**Status:** Accepted

## Context

The store sells to customers in Ghana, where card penetration is low and Mobile
Money (MTN MoMo, Vodafone/Telecel Cash, AirtelTigo) dominates. We need one
processor that covers both, settles in GHS, and is trusted locally.

## Decision

Use **Paystack** as the sole payment processor, via its Initialize/Verify API
plus webhooks. Card and Mobile Money both go through the same Charge flow.

## Consequences

- Amounts are handled in **pesewas** (the minor unit); passing cedis directly is
  a 100× overcharge bug, so conversion is centralised in `app/paystack.py`.
- The **webhook is the single source of truth** for payment success — it is
  HMAC-SHA512 verified and the only path that marks an order paid. The browser
  callback is UX only.
- Refunds go through Paystack's refund API and are reconciled locally.
- Vendor lock-in to Paystack's API shape is contained behind `app/paystack.py`;
  swapping processors would touch only that module and the service layer.
