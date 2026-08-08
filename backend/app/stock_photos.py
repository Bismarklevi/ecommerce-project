"""Fetches real stock photography from Unsplash and Pexels for seeding the catalog.

Both services offer a generous free tier and a straightforward "search photos"
endpoint that returns a direct, hotlink-safe image URL plus everything needed
for attribution. This module wraps both behind one function
(`fetch_stock_photo`) so seed commands don't care which provider answered.

Getting API keys (both free, a couple of minutes each):
  Unsplash: https://unsplash.com/developers -> "New Application" -> copy the
            "Access Key" -> set UNSPLASH_ACCESS_KEY in backend/.env
  Pexels:   https://www.pexels.com/api/     -> sign up -> copy your API key
            -> set PEXELS_API_KEY in backend/.env

Whichever key is present is tried first (Unsplash, then Pexels as a
fallback). If neither key is configured, or the request fails for any
reason (offline dev environment, rate limit, etc.), `fetch_stock_photo`
returns None and callers should skip the image rather than crash the seed.

Downloaded bytes flow straight into Django's `ImageField.save()`, which
means they land wherever `DEFAULT_FILE_STORAGE`/`STORAGES["default"]` points
-- the local `media/` folder in development, or the Cloudflare R2 bucket
whenever `USE_CLOUDFLARE_R2=true`. This module has no idea which one is
active, on purpose.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 15


@dataclass(frozen=True)
class StockPhoto:
    content: bytes
    filename: str
    credit: str
    source_url: str


def _unsplash_search(query: str) -> StockPhoto | None:
    access_key = getattr(settings, "UNSPLASH_ACCESS_KEY", "") or ""
    if not access_key:
        return None

    try:
        response = requests.get(
            "https://api.unsplash.com/search/photos",
            params={"query": query, "per_page": 1, "orientation": "portrait"},
            headers={"Authorization": f"Client-ID {access_key}"},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        results = response.json().get("results") or []
        if not results:
            return None
        photo = results[0]
        image_url = photo["urls"]["regular"]
        photographer = photo["user"]["name"]
        photographer_link = photo["user"]["links"]["html"]

        image_response = requests.get(image_url, timeout=REQUEST_TIMEOUT)
        image_response.raise_for_status()

        return StockPhoto(
            content=image_response.content,
            filename=f"{photo['id']}.jpg",
            credit=f"Photo by {photographer} on Unsplash",
            source_url=photographer_link,
        )
    except (requests.RequestException, KeyError, ValueError) as exc:
        logger.warning("Unsplash lookup for %r failed: %s", query, exc)
        return None


def _pexels_search(query: str) -> StockPhoto | None:
    api_key = getattr(settings, "PEXELS_API_KEY", "") or ""
    if not api_key:
        return None

    try:
        response = requests.get(
            "https://api.pexels.com/v1/search",
            params={"query": query, "per_page": 1, "orientation": "portrait"},
            headers={"Authorization": api_key},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        photos = response.json().get("photos") or []
        if not photos:
            return None
        photo = photos[0]
        image_url = photo["src"]["large2x"]
        photographer = photo["photographer"]
        photographer_link = photo["photographer_url"]

        image_response = requests.get(image_url, timeout=REQUEST_TIMEOUT)
        image_response.raise_for_status()

        return StockPhoto(
            content=image_response.content,
            filename=f"pexels-{photo['id']}.jpg",
            credit=f"Photo by {photographer} on Pexels",
            source_url=photographer_link,
        )
    except (requests.RequestException, KeyError, ValueError) as exc:
        logger.warning("Pexels lookup for %r failed: %s", query, exc)
        return None


def fetch_stock_photo(query: str) -> StockPhoto | None:
    """Try Unsplash first, then Pexels. Returns None (never raises) if both
    are unconfigured or unreachable, so a seed command can decide to skip
    that one image instead of failing the whole run."""
    return _unsplash_search(query) or _pexels_search(query)
