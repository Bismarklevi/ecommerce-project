# ADR-0003: Auth via DRF token stored in an httpOnly cookie

**Status:** Accepted

## Context

The Next.js frontend and Django API are separate origins. We need browser
sessions that are (a) not stealable by client-side JavaScript (XSS), and (b)
usable from both server components and client components.

## Decision

Authenticate the API with **DRF TokenAuthentication**, but never expose the token
to browser JavaScript. The Next.js auth route handlers store it in an **httpOnly,
SameSite=Lax** cookie and attach it as an `Authorization: Token …` header only
from server-side code (route handlers / server components). Django's
SessionAuthentication stays enabled for the admin and browsable API.

## Consequences

- No token sits in `localStorage` or is reachable by a script, so an XSS payload
  can't exfiltrate the credential.
- Client components never call Django directly; they go through same-origin
  Next.js proxy routes, which also means Django sees the proxy's IP (auth
  throttles are therefore keyed on the account identifier, and the proxy forwards
  `X-Forwarded-For`).
- Logout and password-change **revoke the token server-side**, so a leaked cookie
  can't be replayed after sign-out.
- The cookie's `Secure` flag is set from the real request protocol, so login
  works on plain-HTTP local dev and is secure in production.
