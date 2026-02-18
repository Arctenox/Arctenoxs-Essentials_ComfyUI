"""
Arctenox Essentials - Wildcard API Server
==========================================

Registers ComfyUI API endpoints that serve:

  GET /arctenox/wildcards
      Returns: JSON map of { "filename_stem": ["option1", "option2", ...] }

  GET /arctenox/e621_tags?q=<query>&limit=<n>
      Returns: JSON array of e621 tag objects:
          [{ "name": "...", "post_count": 12345, "category": 0 }, ...]
      Proxies the public e621 tags autocomplete API so the browser doesn't
      need to deal with CORS.  Results are cached server-side for 30 minutes.

Author: Arctenox
Version: 1.1.0
License: GPL-3.0
"""

import os
import json
import time
import asyncio
from pathlib import Path
from aiohttp import web, ClientSession, ClientTimeout
import folder_paths

_THIS_DIR = Path(__file__).parent
_WILDCARD_DIRS = [
    _THIS_DIR / "wildcards",
    Path(folder_paths.base_path) / "wildcards",
]

# ─────────────────────────────────────────────────────────────────────────────
#  Wildcard loader  (unchanged from v1.0.0)
# ─────────────────────────────────────────────────────────────────────────────

def _load_all_wildcards() -> dict:
    """
    Scan all wildcard directories and return a dict of:
        { "stem": ["option1", "option2", ...] }
    Files in subdirectories become "subdir/stem" keys.
    Duplicate stems are merged (local pack dir wins on collision).
    """
    result: dict = {}

    for base_dir in reversed(_WILDCARD_DIRS):   # reversed so local dir overwrites global
        if not base_dir.is_dir():
            continue
        for txt_file in sorted(base_dir.rglob("*.txt")):
            try:
                lines   = txt_file.read_text(encoding="utf-8").splitlines()
                options = [l.strip() for l in lines if l.strip() and not l.startswith("#")]
                if not options:
                    continue
                rel = txt_file.relative_to(base_dir).with_suffix("")
                key = rel.as_posix()
                result[key] = options
            except Exception as exc:
                print(f"[Arctenox Wildcard API] Could not read {txt_file}: {exc}")

    return result


# ─────────────────────────────────────────────────────────────────────────────
#  e621 tag proxy + cache
# ─────────────────────────────────────────────────────────────────────────────

_E621_CACHE: dict[str, tuple[float, list]] = {}   # query → (timestamp, results)
_E621_CACHE_TTL  = 1800   # seconds (30 min)
_E621_MAX_CACHED = 500
_E621_BASE_URL   = "https://e621.net/tags/autocomplete.json"
_E621_USER_AGENT = "ArctenoxEssentials/1.1 (ComfyUI wildcard plugin; contact: plugin@arctenox.local)"

# Shared aiohttp session (created lazily)
_http_session: ClientSession | None = None


def _get_session() -> ClientSession:
    global _http_session
    if _http_session is None or _http_session.closed:
        _http_session = ClientSession(
            headers={"User-Agent": _E621_USER_AGENT},
            timeout=ClientTimeout(total=8),
        )
    return _http_session


async def _fetch_e621_tags(query: str, limit: int = 20) -> list:
    """
    Fetch tag autocomplete results from e621 with a short-term in-memory cache.
    Returns a list of dicts: [{ name, post_count, category }, ...]
    """
    cache_key = f"{query}:{limit}"
    now = time.monotonic()

    # Check cache
    if cache_key in _E621_CACHE:
        ts, data = _E621_CACHE[cache_key]
        if now - ts < _E621_CACHE_TTL:
            return data

    try:
        session = _get_session()
        params  = {"search[name_matches]": f"{query}*", "limit": str(min(limit, 20))}
        async with session.get(_E621_BASE_URL, params=params) as resp:
            if resp.status != 200:
                return []
            raw  = await resp.json(content_type=None)
            tags = []
            for t in (raw if isinstance(raw, list) else []):
                tags.append({
                    "name":       t.get("name", ""),
                    "post_count": t.get("post_count", 0),
                    "category":   t.get("category", 0),
                })
    except asyncio.TimeoutError:
        print(f"[Arctenox e621 API] Timeout fetching tags for '{query}'")
        return []
    except Exception as exc:
        print(f"[Arctenox e621 API] Error fetching tags for '{query}': {exc}")
        return []

    # Evict oldest entries if over limit
    if len(_E621_CACHE) >= _E621_MAX_CACHED:
        oldest_key = min(_E621_CACHE, key=lambda k: _E621_CACHE[k][0])
        del _E621_CACHE[oldest_key]

    _E621_CACHE[cache_key] = (now, tags)
    return tags


# ─────────────────────────────────────────────────────────────────────────────
#  Route registration
# ─────────────────────────────────────────────────────────────────────────────

def register_routes(app: web.Application) -> None:
    """Register wildcard and e621 API routes on the ComfyUI aiohttp app."""

    # ── GET /arctenox/wildcards ───────────────────────────────────────────────
    async def get_wildcards(request: web.Request) -> web.Response:
        data = _load_all_wildcards()
        return web.Response(
            text=json.dumps(data),
            content_type="application/json",
        )

    # ── GET /arctenox/e621_tags?q=<query>&limit=<n> ───────────────────────────
    async def get_e621_tags(request: web.Request) -> web.Response:
        query = request.rel_url.query.get("q", "").strip().lower()
        limit = int(request.rel_url.query.get("limit", "20"))

        if not query or len(query) < 2:
            return web.Response(text="[]", content_type="application/json")

        tags = await _fetch_e621_tags(query, limit=limit)
        return web.Response(
            text=json.dumps(tags),
            content_type="application/json",
        )

    app.router.add_get("/arctenox/wildcards",   get_wildcards)
    app.router.add_get("/arctenox/e621_tags",   get_e621_tags)

    print("[Arctenox Essentials] Wildcard API endpoint registered: GET /arctenox/wildcards")
    print("[Arctenox Essentials] e621 tag proxy registered:        GET /arctenox/e621_tags?q=<query>")
