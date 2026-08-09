# ADR-0002: Cloudflare R2 for media storage

**Status:** Accepted

## Context

Product and category images must survive deploys and be served from many
regions. Local disk on an ephemeral app host loses uploads on redeploy and
doesn't scale. Egress fees on S3-class stores can be significant for an
image-heavy catalogue.

## Decision

Store uploaded media in **Cloudflare R2** (S3-compatible, zero egress fees) via
`django-storages` + boto3, toggled by `USE_CLOUDFLARE_R2`. Local disk remains the
default for development so no cloud account is needed to run the project.

## Consequences

- Production must set the R2 bucket/keys **and** a public custom domain
  (`CLOUDFLARE_R2_CUSTOM_DOMAIN`); without the public domain, saved URLs point at
  the private S3 API endpoint and 403 in the browser.
- Media URLs differ between environments; the frontend reads the host from
  `NEXT_PUBLIC_MEDIA_HOST` where needed.
- Storage backend is selected in `settings.py` via `STORAGES`, so switching to
  another S3-compatible provider is a config change, not a code change.
