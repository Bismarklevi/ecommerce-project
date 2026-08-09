# Kaira — Runbook

Operational guide for running, deploying, and recovering the store.

## Architecture

- **backend/** — Django 6 + DRF API (default DB: PostgreSQL). Serves `/api/*`,
  the Unfold admin at `/admin/`, and OpenAPI docs at `/api/docs/`.
- **frontend/** — Next.js 16 storefront. Talks to Django server-side and proxies
  browser calls same-origin through `/api/catalog`, `/api/auth/*`, etc.
- **Paystack** — payments. **Cloudflare R2** (optional) — media. **Sentry**
  (optional) — error tracking.

## Run locally

```bash
# Backend (terminal 1)
cd backend
python -m venv .venv && ./.venv/Scripts/activate   # (Windows) or source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill in values; SQLite works for a quick start
python manage.py migrate
python manage.py runserver

# Frontend (terminal 2)
cd frontend
npm install
cp .env.example .env
npm run dev
```

Both servers must run together. Tests: `python manage.py test` (backend),
`npm test` / `npm run build` (frontend). To run backend tests without Postgres,
override `DATABASE_ENGINE=django.db.backends.sqlite3 DATABASE_NAME=test.sqlite3`.

## Deploy checklist (every release)

1. CI green on the commit (see `.github/workflows/ci.yml`).
2. Production env set: real `SECRET_KEY` (app refuses to boot on the default),
   `DEBUG=False`, `ALLOWED_HOSTS`, DB creds, `PAYSTACK_SECRET_KEY`/`PUBLIC_KEY`
   (live), SMTP `EMAIL_*`, `FRONTEND_URL`, `SENTRY_DSN`. Frontend:
   `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_SITE_URL`.
3. `python manage.py migrate` (expand→migrate→contract for schema changes).
4. `python manage.py collectstatic`.
5. Point the **Paystack webhook** at `https://<api-host>/api/payments/webhook/`.
6. Smoke test: register → add to cart → checkout → confirm webhook marks paid.

## Common incidents

| Symptom | Likely cause | Fix |
|---|---|---|
| Storefront: "Couldn't load products" | Django down or `NEXT_PUBLIC_API_BASE_URL` wrong | Check backend health; verify env; catalogue proxy is `/api/catalog`. |
| Orders paid on Paystack but stuck "pending" | Webhook not reaching Django or signature mismatch | Verify webhook URL + that `PAYSTACK_SECRET_KEY` matches the dashboard; check logs for "invalid signature". Re-send the event from Paystack. |
| App won't boot: RuntimeError on SECRET_KEY | `DEBUG=False` with the default dev key | Set a real `SECRET_KEY`. |
| Images 403 in browser | R2 enabled without a public custom domain | Set `CLOUDFLARE_R2_CUSTOM_DOMAIN` (ADR-0002). |
| Login appears to succeed then user is logged out | Cookie `Secure` flag over plain HTTP | Ensure TLS / correct `X-Forwarded-Proto` from the proxy. |

## Degradation fallbacks

- **Paystack down**: checkout initialisation returns 502 and the order stays
  `pending` (nothing is marked paid) — safe to retry later; no stock is lost
  because reservation happens at order creation, not payment.
- **R2 down**: switch `USE_CLOUDFLARE_R2=false` to fall back to local disk for new
  uploads (existing R2 URLs still resolve).
- **Email down**: password-reset/order emails fail silently by design (logged);
  the rest of the store keeps working.

## Backups & recovery

- Nightly automated Postgres backups; **test a restore quarterly** (a backup you
  haven't restored is a hope, not a backup).
- R2 media is the object store of record; enable bucket versioning.
- Rotate `SECRET_KEY`, Paystack keys, and DB creds on the maintenance cadence.
