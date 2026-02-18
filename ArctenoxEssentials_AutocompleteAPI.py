"""
Arctenox Essentials - Autocomplete API
========================================

Backend for the full Autocomplete system. Provides:

  GET /arctenox/ac/tags?q=<query>&source=<danbooru|e621|all>&limit=<n>
      Tag autocomplete from local CSV, sorted by post count, aliases included.

  GET /arctenox/ac/related?tag=<tag>&source=<danbooru|e621|all>&limit=<n>
      Co-occurrence related tags for the given tag.

  GET /arctenox/ac/loras
      List of available LoRA files (name, path).

  GET /arctenox/ac/embeddings
      List of available embedding/textual-inversion files.

  GET /arctenox/ac/csv_status
      Reports which CSV files are loaded and tag counts.

  POST /arctenox/ac/reload_csv
      Force-reload all CSV files from disk.

CSV data format (compatible with DominikDoom/a1111-sd-webui-tagcomplete):
    tag, category, count, alias
    e.g.:  1girl,4,9999999,

Column indices:
    0 = tag name
    1 = category  (0=general, 1=artist, 3=copyright, 4=character, 5=species/meta)
    2 = post count
    3 = alias (comma-separated, optional)

CSV files are expected in: <this_dir>/data/
  - danbooru_tags.csv               (base Danbooru tags)
  - danbooru_tags_cooccurrence.csv  (co-occurrence pairs)
  - e621_tags.csv                   (optional e621 tags)
  - e621_tags_cooccurrence.csv      (optional)
  - danbooru_tags*.csv              (any extra user CSVs)
  - e621_tags*.csv                  (any extra user e621 CSVs)

If base CSVs are missing they are auto-downloaded:
  - danbooru CSVs from HuggingFace (newtextdoc1111/danbooru-tag-csv)
  - e621_tags.csv from GitHub (DominikDoom/a1111-sd-webui-tagcomplete)
  - No e621 cooccurrence file is available for auto-download.

Author: Arctenox
Version: 1.1.0
License: GPL-3.0
"""

import os
import csv
import json
import asyncio
import threading
from pathlib import Path
from collections import defaultdict
from aiohttp import web, ClientSession, ClientTimeout

try:
    import folder_paths
    _BASE_PATH = Path(folder_paths.base_path)
except Exception:
    _BASE_PATH = Path(__file__).parent.parent.parent

_THIS_DIR  = Path(__file__).parent
_DATA_DIR  = _THIS_DIR / "data"
_META_FILE = _THIS_DIR / "csv_meta.json"

_HF_BASE   = "https://huggingface.co/datasets/newtextdoc1111/danbooru-tag-csv/resolve/main"
_GH_E621   = "https://raw.githubusercontent.com/DominikDoom/a1111-sd-webui-tagcomplete/main/tags"
_HF_FILES = {
    "danbooru_tags.csv":              f"{_HF_BASE}/danbooru_tags.csv",
    "danbooru_tags_cooccurrence.csv": f"{_HF_BASE}/danbooru_tags_cooccurrence.csv",
    "e621_tags.csv":                  f"{_GH_E621}/e621.csv",
}

# ─────────────────────────────────────────────────────────────────────────────
#  Data structures
# ─────────────────────────────────────────────────────────────────────────────

class TagDB:
    """In-memory tag database for one source (danbooru or e621)."""
    __slots__ = ("tags", "alias_map", "cooccurrence", "source", "loaded")

    def __init__(self, source: str):
        self.source      = source
        self.loaded      = False
        self.tags: dict[str, dict]         = {}
        self.alias_map: dict[str, str]     = {}
        self.cooccurrence: dict[str, list] = {}


_DBS: dict[str, TagDB] = {
    "danbooru": TagDB("danbooru"),
    "e621":     TagDB("e621"),
}

# Use a threading lock for sync CSV loading + an async lock for the load gate
_LOAD_LOCK   = asyncio.Lock()
_THREAD_LOCK = threading.Lock()
_csv_loaded  = False

# ─────────────────────────────────────────────────────────────────────────────
#  CSV downloader
# ─────────────────────────────────────────────────────────────────────────────

async def _download_csv(url: str, dest: Path) -> bool:
    """Download a file from url to dest. Returns True on success."""
    try:
        timeout = ClientTimeout(total=180)
        async with ClientSession(timeout=timeout) as session:
            async with session.get(url) as r:
                if r.status != 200:
                    print(f"[Arctenox AC] Download failed ({r.status}): {url}")
                    return False
                dest.parent.mkdir(parents=True, exist_ok=True)
                content = await r.read()
                dest.write_bytes(content)
                print(f"[Arctenox AC] Downloaded {dest.name} ({len(content) // 1024} KB)")
                return True
    except Exception as exc:
        print(f"[Arctenox AC] Download error for {url}: {exc}")
        return False


async def _ensure_base_csvs():
    """Download base CSVs if missing (Danbooru from HuggingFace, e621 from GitHub)."""
    meta = {}
    if _META_FILE.exists():
        try:
            meta = json.loads(_META_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass

    if meta.get("check_updates_on_startup") is False:
        return

    tasks = []
    for filename, url in _HF_FILES.items():
        dest = _DATA_DIR / filename
        if not dest.exists():
            print(f"[Arctenox AC] Missing {filename}, downloading from HuggingFace…")
            tasks.append(_download_csv(url, dest))

    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for i, res in enumerate(results):
            if isinstance(res, Exception):
                print(f"[Arctenox AC] Download task {i} raised: {res}")


# ─────────────────────────────────────────────────────────────────────────────
#  CSV loaders  (run in thread pool to avoid blocking the event loop)
# ─────────────────────────────────────────────────────────────────────────────

def _load_tag_csv(path: Path, db: TagDB):
    """Parse a tag CSV into db.tags and db.alias_map."""
    try:
        with path.open(encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or len(row) < 2:
                    continue
                name = row[0].strip()
                if not name or name.lower() == "tag":   # skip header row
                    continue

                # Chant rows: name wrapped in quotes containing multiple tags
                is_chant = name.startswith('"') and name.endswith('"')
                if is_chant:
                    name = name[1:-1]

                try:
                    category = int(row[1]) if len(row) > 1 else 0
                except ValueError:
                    category = 0
                try:
                    count = int(row[2]) if len(row) > 2 else 0
                except ValueError:
                    count = 0

                aliases_raw = row[3].strip() if len(row) > 3 else ""
                aliases     = [a.strip() for a in aliases_raw.split(",") if a.strip()] if aliases_raw else []

                entry = {
                    "name":     name,
                    "category": category,
                    "count":    count,
                    "aliases":  aliases,
                    "chant":    is_chant,
                    "source":   db.source,
                }

                # Don't overwrite higher-count entries
                existing = db.tags.get(name)
                if existing is None or count > existing["count"]:
                    db.tags[name] = entry

                for alias in aliases:
                    al = alias.lower()
                    if al not in db.alias_map:
                        db.alias_map[al] = name

    except Exception as exc:
        print(f"[Arctenox AC] Error loading tag CSV {path}: {exc}")


def _load_cooccurrence_csv(path: Path, db: TagDB):
    """Parse co-occurrence CSV: tag_a, tag_b, count"""
    raw: dict[str, dict[str, int]] = defaultdict(dict)
    try:
        with path.open(encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or len(row) < 3:
                    continue
                try:
                    tag_a = row[0].strip()
                    tag_b = row[1].strip()
                    cnt   = int(row[2])
                except (ValueError, IndexError):
                    continue
                if not tag_a or not tag_b or tag_a == tag_b:
                    continue
                raw[tag_a][tag_b] = raw[tag_a].get(tag_b, 0) + cnt
                raw[tag_b][tag_a] = raw[tag_b].get(tag_a, 0) + cnt
    except Exception as exc:
        print(f"[Arctenox AC] Error loading cooccurrence CSV {path}: {exc}")
        return

    for tag, related in raw.items():
        db.cooccurrence[tag] = sorted(related.items(), key=lambda x: -x[1])


def _glob_csvs(source: str, suffix: str = "") -> list[Path]:
    """
    Glob CSV files in data dir for a given source.
    suffix=""              → tag CSVs  (danbooru_tags*.csv)
    suffix="_cooccurrence" → co-occurrence CSVs
    """
    if not _DATA_DIR.is_dir():
        return []
    pattern = f"{source}_tags{suffix}*.csv"
    return sorted(_DATA_DIR.glob(pattern))


def _load_db(db: TagDB):
    """Load all CSVs for a TagDB from disk (synchronous, runs in thread)."""
    with _THREAD_LOCK:
        db.tags.clear()
        db.alias_map.clear()
        db.cooccurrence.clear()
        db.loaded = False

    source     = db.source
    tag_files  = _glob_csvs(source)
    cooc_files = _glob_csvs(source, "_cooccurrence")

    if not tag_files:
        print(f"[Arctenox AC] No tag CSV found for source '{source}' in {_DATA_DIR}")
        return

    # User override files first, then base
    base_tag  = _DATA_DIR / f"{source}_tags.csv"
    user_tags = [f for f in tag_files if f != base_tag]
    for f in user_tags:
        _load_tag_csv(f, db)
    if base_tag.exists():
        _load_tag_csv(base_tag, db)

    base_cooc  = _DATA_DIR / f"{source}_tags_cooccurrence.csv"
    user_coocs = [f for f in cooc_files if f != base_cooc]
    for f in user_coocs:
        _load_cooccurrence_csv(f, db)
    if base_cooc.exists():
        _load_cooccurrence_csv(base_cooc, db)

    db.loaded = True
    print(f"[Arctenox AC] {source}: {len(db.tags):,} tags, "
          f"{len(db.cooccurrence):,} co-occurrence entries loaded")


async def _load_all(force: bool = False):
    """Ensure all databases are loaded. Downloads missing CSVs first."""
    global _csv_loaded
    async with _LOAD_LOCK:
        if _csv_loaded and not force:
            return
        await _ensure_base_csvs()
        loop = asyncio.get_event_loop()
        # Run blocking CSV I/O in a thread pool so the event loop stays responsive
        await asyncio.gather(
            loop.run_in_executor(None, _load_db, _DBS["danbooru"]),
            loop.run_in_executor(None, _load_db, _DBS["e621"]),
        )
        _csv_loaded = True


# ─────────────────────────────────────────────────────────────────────────────
#  Tag search
# ─────────────────────────────────────────────────────────────────────────────

def _search_tags(query: str, source: str, limit: int) -> list[dict]:
    """
    Search tags across the requested source(s).
    Priority: prefix match > alias prefix match > substring match.
    Returns list of tag dicts sorted by post count descending.
    """
    q = query.lower().strip()
    if not q:
        return []

    sources = ["danbooru", "e621"] if source == "all" else [source]
    seen:    set[str]   = set()
    prefix:  list[dict] = []
    alias:   list[dict] = []
    substr:  list[dict] = []

    for src in sources:
        db = _DBS.get(src)
        if not db or not db.loaded:
            continue

        for name, entry in db.tags.items():
            nl = name.lower()
            if nl.startswith(q):
                if name not in seen:
                    seen.add(name)
                    prefix.append(entry)
            elif q in nl:
                if name not in seen:
                    seen.add(name)
                    substr.append(entry)

        for alias_lower, canonical in db.alias_map.items():
            if alias_lower.startswith(q) and canonical not in seen:
                entry = db.tags.get(canonical)
                if entry:
                    seen.add(canonical)
                    # Surface which alias matched so the JS can display it
                    alias.append({**entry, "_matchedAlias": alias_lower})

    # Sort each tier by count, then combine
    prefix.sort(key=lambda e: e.get("count", 0), reverse=True)
    alias.sort( key=lambda e: e.get("count", 0), reverse=True)
    substr.sort(key=lambda e: e.get("count", 0), reverse=True)

    combined = prefix + alias + substr
    return combined[:limit]


def _get_related(tag: str, source: str, limit: int) -> list[dict]:
    """Return related tags for a given tag via co-occurrence."""
    sources = ["danbooru", "e621"] if source == "all" else [source]
    results = []
    seen: set[str] = set()

    for src in sources:
        db = _DBS.get(src)
        if not db or not db.loaded:
            continue
        related = db.cooccurrence.get(tag, [])
        for rel_name, score in related:
            if rel_name in seen:
                continue
            seen.add(rel_name)
            entry = db.tags.get(rel_name, {"name": rel_name, "category": 0, "count": 0, "source": src})
            results.append({**entry, "score": score, "source": src})

    results.sort(key=lambda e: e.get("score", 0), reverse=True)
    return results[:limit]


# ─────────────────────────────────────────────────────────────────────────────
#  LoRA / Embedding listing
# ─────────────────────────────────────────────────────────────────────────────

_LORA_EXTENSIONS      = {".safetensors", ".ckpt", ".pt", ".bin"}
_EMBEDDING_EXTENSIONS = {".safetensors", ".pt", ".bin", ".pth"}


def _list_loras() -> list[dict]:
    try:
        lora_dirs = folder_paths.get_folder_paths("loras")
    except Exception:
        return []
    items = []
    seen: set[str] = set()
    for base in lora_dirs:
        base = Path(base)
        if not base.is_dir():
            continue
        for f in sorted(base.rglob("*")):
            if f.suffix.lower() not in _LORA_EXTENSIONS:
                continue
            rel = f.relative_to(base)
            stem = rel.stem
            if stem in seen:
                continue
            seen.add(stem)
            items.append({
                "name":   stem,
                "path":   rel.as_posix(),
                "source": "lora",
            })
    return items


def _list_embeddings() -> list[dict]:
    try:
        emb_dirs = folder_paths.get_folder_paths("embeddings")
    except Exception:
        return []
    items = []
    seen: set[str] = set()
    for base in emb_dirs:
        base = Path(base)
        if not base.is_dir():
            continue
        for f in sorted(base.rglob("*")):
            if f.suffix.lower() not in _EMBEDDING_EXTENSIONS:
                continue
            rel = f.relative_to(base)
            stem = rel.stem
            if stem in seen:
                continue
            seen.add(stem)
            items.append({
                "name":   stem,
                "path":   rel.as_posix(),
                "source": "embedding",
            })
    return items


# ─────────────────────────────────────────────────────────────────────────────
#  CSV status
# ─────────────────────────────────────────────────────────────────────────────

def _csv_status() -> dict:
    status = {}
    for src in ("danbooru", "e621"):
        base   = (_DATA_DIR / f"{src}_tags.csv").exists()
        extras = [f.name for f in _glob_csvs(src) if f.name != f"{src}_tags.csv"]
        status[src] = {
            "base":      base,
            "extra":     ", ".join(extras) if extras else "none",
            "loaded":    _DBS[src].loaded,
            "tag_count": len(_DBS[src].tags),
            "cooc_count": len(_DBS[src].cooccurrence),
        }
    return status


# ─────────────────────────────────────────────────────────────────────────────
#  Route registration
# ─────────────────────────────────────────────────────────────────────────────

def register_routes(app: web.Application) -> None:

    # ── GET /arctenox/ac/tags ─────────────────────────────────────────────────
    async def get_tags(request: web.Request) -> web.Response:
        await _load_all()
        q      = request.rel_url.query.get("q", "").strip()
        source = request.rel_url.query.get("source", "danbooru").strip().lower()
        if source not in ("danbooru", "e621", "all"):
            source = "danbooru"
        try:
            limit = min(int(request.rel_url.query.get("limit", "50")), 200)
        except ValueError:
            limit = 50

        if not q:
            return web.Response(text="[]", content_type="application/json")

        tags = _search_tags(q, source, limit)
        return web.Response(
            text=json.dumps(tags, ensure_ascii=False),
            content_type="application/json",
        )

    # ── GET /arctenox/ac/related ──────────────────────────────────────────────
    async def get_related(request: web.Request) -> web.Response:
        await _load_all()
        tag    = request.rel_url.query.get("tag", "").strip()
        source = request.rel_url.query.get("source", "danbooru").strip().lower()
        if source not in ("danbooru", "e621", "all"):
            source = "danbooru"
        try:
            limit = min(int(request.rel_url.query.get("limit", "30")), 100)
        except ValueError:
            limit = 30

        if not tag:
            return web.Response(text="[]", content_type="application/json")

        related = _get_related(tag, source, limit)
        return web.Response(
            text=json.dumps(related, ensure_ascii=False),
            content_type="application/json",
        )

    # ── GET /arctenox/ac/loras ────────────────────────────────────────────────
    async def get_loras(request: web.Request) -> web.Response:
        loop  = asyncio.get_event_loop()
        items = await loop.run_in_executor(None, _list_loras)
        return web.Response(
            text=json.dumps(items),
            content_type="application/json",
        )

    # ── GET /arctenox/ac/embeddings ───────────────────────────────────────────
    async def get_embeddings(request: web.Request) -> web.Response:
        loop  = asyncio.get_event_loop()
        items = await loop.run_in_executor(None, _list_embeddings)
        return web.Response(
            text=json.dumps(items),
            content_type="application/json",
        )

    # ── GET /arctenox/ac/csv_status ───────────────────────────────────────────
    async def get_csv_status(request: web.Request) -> web.Response:
        return web.Response(
            text=json.dumps(_csv_status()),
            content_type="application/json",
        )

    # ── POST /arctenox/ac/reload_csv ──────────────────────────────────────────
    async def reload_csv(request: web.Request) -> web.Response:
        global _csv_loaded
        _csv_loaded = False
        for db in _DBS.values():
            db.loaded = False
        await _load_all(force=True)
        return web.Response(
            text=json.dumps({"ok": True, "status": _csv_status()}),
            content_type="application/json",
        )

    app.router.add_get( "/arctenox/ac/tags",        get_tags)
    app.router.add_get( "/arctenox/ac/related",     get_related)
    app.router.add_get( "/arctenox/ac/loras",       get_loras)
    app.router.add_get( "/arctenox/ac/embeddings",  get_embeddings)
    app.router.add_get( "/arctenox/ac/csv_status",  get_csv_status)
    app.router.add_post("/arctenox/ac/reload_csv",  reload_csv)

    print("[Arctenox Essentials] Autocomplete API registered on /arctenox/ac/*")

    # Kick off background CSV load so first request is fast
    async def _bg_load(_app):
        await _load_all()

    app.on_startup.append(_bg_load)
