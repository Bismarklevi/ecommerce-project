# Kaira — Ship Checklist

Status as of the production-hardening pass. ✅ done · ⬜ needs owner action
(credentials / hosting / manual verification).

## Engineering

- [x] Version control + CI (backend + frontend gates: check, migrations, tests,
      lint, format, typecheck, build, dependency audit)
- [x] TypeScript strict, ESLint, Prettier enforced
- [x] Backend test suite (89 tests) + frontend unit tests
- [x] Pagination on all list endpoints
- [x] Per-endpoint rate limiting (auth + checkout)
- [x] Production security headers + secure cookies + SECRET_KEY boot guard
- [x] Structured logging; optional Sentry (set `SENTRY_DSN`)
- [ ] One end-to-end smoke test wired into CI (Playwright scaffold to add)

## Security

- [x] Per-record authorization (no IDOR) on cart/order/payment/address
- [x] Payments verified server-side via HMAC webhook; no client-trusted success
- [x] Secrets in env only; `.env` gitignored; `.env.example` documented
- [x] `manage.py check --deploy` clean (with a real SECRET_KEY)
- [ ] Run `/security-review` once more against the final deploy config

## Legal & data

- [x] Privacy policy + Terms pages (Ghana Act 843 aware)
- [x] Data export + account erasure (self-service)
- [ ] Have counsel review the policy/terms; update contact emails from the
      `kaira.example.com` placeholders

## Pre-launch (owner)

- [ ] Real `SECRET_KEY`, live Paystack keys, SMTP `EMAIL_*`, `FRONTEND_URL`
- [ ] Hosting chosen + deployed (frontend + backend + managed Postgres)
- [ ] Paystack webhook pointed at `/api/payments/webhook/` and test-fired
- [ ] `NEXT_PUBLIC_SITE_URL` set (canonical/robots/sitemap)
- [ ] Lighthouse ≥ 90 on home + shop + product (run against the deployed URL)
- [ ] Nightly DB backups verified by a **test restore**; R2 versioning on
- [ ] Uptime monitor + Sentry alerts + billing alerts on every cloud service

## Verified working (commerce flow)

- [x] register → add to cart → update qty → checkout → order in account
- [x] stock reservation prevents overselling; released on failure/cancel
- [x] dark mode, WCAG-audited contrast, responsive/mobile-first
