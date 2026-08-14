# Cloudflare R2 Setup

Everything on the code side is already configured. `USE_CLOUDFLARE_R2=true`
is left on permanently — until real credentials are added below, media
quietly falls back to local disk storage (with a console warning), so
nothing breaks in the meantime. The **only** remaining steps are on the
Cloudflare side, and then pasting five values into two files.

## 1. Create the bucket

Cloudflare dashboard → R2 → Create bucket. Any name works — just make sure
it matches `CLOUDFLARE_R2_BUCKET_NAME` below. The project defaults to
`ecommerce-images`.

## 2. Create an API token scoped to just this bucket

R2 → Manage API tokens → Create token → **Object Read & Write**, scoped to
the one bucket you just created (not account-wide — no reason to grant more
access than the app needs). This gives you:
- an Access Key ID
- a Secret Access Key
- an endpoint URL, in the form `https://<account-id>.r2.cloudflarestorage.com`

## 3. Enable public access, or connect a custom domain

Required, not optional — the app is configured with `querystring_auth: False`
(permanent, non-expiring image URLs, correct for a public storefront), which
only works if the bucket is actually reachable publicly. Either:

- Turn on the bucket's public `r2.dev` URL (quickest — R2 → your bucket →
  Settings → Public access), or
- Connect a real custom domain (better for production) — R2 → your bucket →
  Settings → Custom Domains, e.g. `media.yourstore.com`.

Either way, you end up with a hostname — that's what goes into
`CLOUDFLARE_R2_CUSTOM_DOMAIN` and `NEXT_PUBLIC_MEDIA_HOST` below (no
protocol, no trailing slash — just the hostname).

## 4. Paste the values in

**`backend/.env`** — replace the five placeholder values:
```
CLOUDFLARE_R2_BUCKET_NAME=<your bucket name>
CLOUDFLARE_R2_ENDPOINT_URL=https://<your-account-id>.r2.cloudflarestorage.com
CLOUDFLARE_R2_ACCESS_KEY_ID=<from step 2>
CLOUDFLARE_R2_SECRET_ACCESS_KEY=<from step 2>
CLOUDFLARE_R2_CUSTOM_DOMAIN=<hostname from step 3, no protocol>
```
`CLOUDFLARE_R2_REGION_NAME` (`auto`) and `CLOUDFLARE_R2_LOCATION` (`media`
— the folder prefix inside the bucket) can stay as they are.

**`frontend/.env`** — one value:
```
NEXT_PUBLIC_MEDIA_HOST=<same hostname as CLOUDFLARE_R2_CUSTOM_DOMAIN above>
```
This is required separately from the backend value — Next's `<Image>`
component refuses to load from any hostname it doesn't already know about
(`next.config.ts`), so it needs to be told about R2's host too.

That's it. No other file needs to change — `USE_CLOUDFLARE_R2` is already
`true`, and `project/settings.py` automatically switches from local disk to
R2 the moment it sees all five backend values are real (see
`_r2_credentials_present` in `settings.py` if you want to see exactly what
it checks for).

## 5. Restart and verify

Restart the Django dev server (env vars are only read at process start) and
the Next.js dev server (`rm -rf frontend/.next` first if you're not sure the
cache is fresh — stale caches have bitten this project before). Then:

1. Upload a product or category image through the Django admin.
2. Load the storefront and confirm the image actually renders.

If it doesn't: check the Django server's console output first —
`USE_CLOUDFLARE_R2=true but CLOUDFLARE_R2_* credentials are still
placeholders` means one of the five backend values still literally says
`replace-me`. A 403 on the image itself (not a Django error) almost always
means step 3 (public access / custom domain) isn't actually live yet on the
Cloudflare side.
