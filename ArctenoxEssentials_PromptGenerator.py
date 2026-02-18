"""
Arctenox Essentials - Semi-Random Prompt Generator
====================================================

Generates semi-random prompts using Danbooru/e621 tag data and
co-occurrence statistics. Starting from seed tags, it walks the
co-occurrence graph to find related tags, filters by category,
and assembles a coherent prompt.

Strategy:
  1. Start from user-supplied seed tags (or pick random high-count ones)
  2. Use co-occurrence data to find tags that naturally appear together
  3. Sample tags with weighted probability (higher co-occurrence = more likely)
  4. Fill categories: subject, species/character, general descriptors, quality
  5. Output as comma-separated prompt string

Categories (Danbooru):
  0 = general    1 = artist    3 = copyright
  4 = character  5 = species/meta  7 = meta

Author: Arctenox
Version: 1.1.0
License: GPL-3.0
"""

import os
import csv
import random
import threading
from pathlib import Path
from collections import defaultdict

try:
    import folder_paths
    _BASE_PATH = Path(folder_paths.base_path)
except Exception:
    _BASE_PATH = Path(__file__).parent.parent.parent

_THIS_DIR = Path(__file__).parent
_DATA_DIR = _THIS_DIR / "data"

# ─────────────────────────────────────────────────────────────────────────────
#  Shared in-memory tag data (loaded once, reused across runs)
# ─────────────────────────────────────────────────────────────────────────────

class _TagData:
    def __init__(self):
        self.tags: dict          = {}   # name → {name, category, count, source}
        self.cooccurrence: dict  = {}   # name → [(related_name, score), ...]
        self.by_category: dict   = defaultdict(list)  # cat → [name, ...]
        self.loaded = False
        self.lock   = threading.Lock()

_DB = _TagData()

# Tags we never want in prompts
_BLOCKLIST = {
    "commentary", "translated", "check_translation", "hard_translated",
    "poorly_translated", "third-party_edit", "original", "commission",
    "paid_reward", "patreon_reward", "fanbox_reward", "artstation",
    "pixiv", "twitter", "english_text", "japanese_text", "speech_bubble",
    "text_focus", "watermark", "signature", "dated", "artist_name",
    "character_name", "copyright_name", "sample_watermark",
    "low_quality", "lowres", "bad_anatomy", "bad_hands",
    "censored", "bar_censor", "mosaic_censoring",
    "animated", "video", "webm", "gif", "flash",
    "multiple_images", "image_sample", "image_set",
    "meta", "check_character", "check_copyright", "check_artist",
    "revision", "resized", "upscaled", "downscaled", "cropped",
    "photo_inset", "real_life_insert", "screencap",
}

# High-quality general descriptors worth inserting
_QUALITY_TAGS = [
    "masterpiece", "best_quality", "high_quality", "detailed",
    "highly_detailed", "absurdres", "highres", "8k", "4k",
]

_RATING_TAGS = {
    "safe":     {"rating:safe", "rating:general", "general"},
    "nsfw":     {"rating:explicit", "rating:questionable", "explicit", "questionable"},
    "all":      set(),
}


def _parse_filter_tags(raw: str) -> set:
    """
    Parse a multiline / comma-separated string of tags to exclude.
    Normalises to lowercase with spaces replaced by underscores, matching
    how tags are stored internally.  Lines starting with # are ignored.
    """
    result = set()
    for part in raw.replace("\n", ",").split(","):
        tag = part.strip()
        if not tag or tag.startswith("#"):
            continue
        result.add(tag.replace(" ", "_").lower())
    return result


def _load_csv(path: Path, source: str, db: _TagData):
    """Load tag CSV into db.tags and db.by_category."""
    try:
        with path.open(encoding="utf-8", newline="") as f:
            for row in csv.reader(f):
                if not row or len(row) < 2:
                    continue
                name = row[0].strip()
                if not name or name.lower() == "tag":
                    continue
                try:
                    cat = int(row[1])
                except ValueError:
                    cat = 0
                try:
                    count = int(row[2]) if len(row) > 2 else 0
                except ValueError:
                    count = 0
                if name in db.tags:
                    continue  # don't overwrite — danbooru loaded first
                entry = {"name": name, "category": cat, "count": count, "source": source}
                db.tags[name] = entry
                if cat not in (1, 3) and name not in _BLOCKLIST:  # skip artist/copyright
                    db.by_category[cat].append(name)
    except Exception as exc:
        print(f"[Arctenox PromptGen] Error loading {path.name}: {exc}")


def _load_cooccurrence(path: Path, db: _TagData):
    """Load co-occurrence CSV into db.cooccurrence."""
    raw: dict = defaultdict(dict)
    try:
        with path.open(encoding="utf-8", newline="") as f:
            for row in csv.reader(f):
                if not row or len(row) < 3:
                    continue
                try:
                    a, b, cnt = row[0].strip(), row[1].strip(), int(row[2])
                except (ValueError, IndexError):
                    continue
                if not a or not b or a == b:
                    continue
                raw[a][b] = raw[a].get(b, 0) + cnt
                raw[b][a] = raw[b].get(a, 0) + cnt
    except Exception as exc:
        print(f"[Arctenox PromptGen] Error loading cooccurrence: {exc}")
        return
    for tag, related in raw.items():
        db.cooccurrence[tag] = sorted(related.items(), key=lambda x: -x[1])


def _ensure_loaded():
    """Load CSVs once. Thread-safe."""
    if _DB.loaded:
        return
    with _DB.lock:
        if _DB.loaded:
            return

        for source, prefix in [("danbooru", "danbooru"), ("e621", "e621")]:
            tag_path  = _DATA_DIR / f"{prefix}_tags.csv"
            cooc_path = _DATA_DIR / f"{prefix}_tags_cooccurrence.csv"
            if tag_path.exists():
                _load_csv(tag_path, source, _DB)
                print(f"[Arctenox PromptGen] Loaded {source} tags: {sum(1 for v in _DB.tags.values() if v['source']==source):,}")
            else:
                print(f"[Arctenox PromptGen] Warning: {tag_path.name} not found — run autocomplete first to download it")

            if cooc_path.exists():
                _load_cooccurrence(cooc_path, _DB)
                print(f"[Arctenox PromptGen] Loaded {source} co-occurrence: {len(_DB.cooccurrence):,} entries")

        _DB.loaded = True


# ─────────────────────────────────────────────────────────────────────────────
#  Prompt generation logic
# ─────────────────────────────────────────────────────────────────────────────

def _weighted_sample(candidates: list, rng: random.Random, k: int) -> list:
    """
    Sample k unique tags from candidates weighted by score.
    candidates = [(tag_name, weight), ...]
    """
    if not candidates:
        return []
    tags, weights = zip(*candidates)
    total = sum(weights)
    if total == 0:
        return list(rng.sample(list(tags), min(k, len(tags))))

    chosen = []
    remaining = list(zip(tags, weights))
    for _ in range(min(k, len(remaining))):
        norm_weights = [w / sum(w2 for _, w2 in remaining) for _, w in remaining]
        r = rng.random()
        cumulative = 0.0
        idx = 0
        for i, w in enumerate(norm_weights):
            cumulative += w
            if r <= cumulative:
                idx = i
                break
        chosen.append(remaining[idx][0])
        remaining.pop(idx)

    return chosen


def _expand_from_seeds(
    seeds: list,
    rng: random.Random,
    target_count: int,
    source_filter: str,
    rating: str,
    min_count: int,
    user_filter: set,        # ← new: tags explicitly blocked by the user
) -> list:
    """
    Walk the co-occurrence graph from seed tags to gather related tags.
    Returns a list of tag names (deduplicated, filtered).
    """
    result_set: set = set()
    candidate_pool: dict = {}  # tag → accumulated score

    # Determine which sources to allow
    allowed_sources = {"danbooru", "e621"} if source_filter == "all" else {source_filter}

    # Blocklist additions based on rating
    rating_block: set = set()
    if rating == "safe":
        rating_block = _RATING_TAGS["nsfw"]
    elif rating == "nsfw":
        rating_block = _RATING_TAGS["safe"]

    def _is_valid(tag_name: str) -> bool:
        if tag_name in _BLOCKLIST or tag_name in rating_block:
            return False
        # ── user filter ──────────────────────────────────────────────
        if tag_name in user_filter:
            return False
        entry = _DB.tags.get(tag_name)
        if not entry:
            return False
        if entry["source"] not in allowed_sources:
            return False
        if entry["count"] < min_count:
            return False
        if entry["category"] in (1, 3):  # skip artist/copyright
            return False
        return True

    # Add seed tags first if valid
    for seed in seeds:
        seed_norm = seed.strip().replace(" ", "_").lower()
        if seed_norm in _DB.tags and _is_valid(seed_norm):
            result_set.add(seed_norm)

    # Gather candidates from co-occurrence of seeds + already-chosen tags
    frontier = list(result_set) if result_set else seeds[:3]

    for _ in range(6):  # expand up to 6 hops
        if len(result_set) >= target_count:
            break
        new_frontier = []
        for tag in frontier:
            related = _DB.cooccurrence.get(tag, [])
            for rel_name, score in related[:80]:  # top-80 co-occurring per tag
                if rel_name not in result_set and _is_valid(rel_name):
                    candidate_pool[rel_name] = candidate_pool.get(rel_name, 0) + score
                    new_frontier.append(rel_name)

        if not candidate_pool:
            break

        # Sample from pool weighted by score
        pool_list = [(t, s) for t, s in candidate_pool.items() if t not in result_set]
        pool_list.sort(key=lambda x: -x[1])

        # Take top candidates with some randomness — top-N * variability
        variability_pool = pool_list[:max(30, target_count * 4)]
        picks = _weighted_sample(variability_pool, rng, min(8, target_count - len(result_set)))
        for p in picks:
            result_set.add(p)
        new_frontier = picks
        frontier = new_frontier

    # If still under target, pad with random high-count general tags
    if len(result_set) < target_count:
        general_tags = _DB.by_category.get(0, [])
        top_general = sorted(
            [t for t in general_tags if _is_valid(t) and t not in result_set],
            key=lambda t: _DB.tags[t]["count"], reverse=True
        )[:500]
        if top_general:
            pad_count = target_count - len(result_set)
            picks = rng.sample(top_general[:min(200, len(top_general))], min(pad_count, len(top_general[:200])))
            result_set.update(picks)

    return list(result_set)


def _sort_tags(tags: list) -> list:
    """
    Sort tags into a natural prompt order:
    character/species → subject matter → general → quality
    """
    CAT_ORDER = {4: 0, 5: 1, 0: 2, 7: 3, 6: 4}

    def sort_key(tag):
        entry = _DB.tags.get(tag, {})
        cat   = entry.get("category", 0)
        count = entry.get("count", 0)
        order = CAT_ORDER.get(cat, 5)
        return (order, -count)

    return sorted(tags, key=sort_key)


def generate_prompt(
    seed_tags:       str,
    source:          str,
    tag_count:       int,
    variability:     float,
    rating:          str,
    min_post_count:  int,
    add_quality:     bool,
    quality_count:   int,
    prepend:         str,
    append:          str,
    seed:            int,
    filter_tags:     str = "",   # ← new parameter
) -> tuple:
    """
    Main generation function. Returns (prompt, debug_info).
    """
    _ensure_loaded()

    if not _DB.tags:
        return ("", "Error: No tag data loaded. Make sure danbooru_tags.csv exists in the data/ folder.")

    rng = random.Random() if seed == -1 else random.Random(seed)

    # Parse user filter
    user_filter = _parse_filter_tags(filter_tags)

    # Parse seed tags
    seeds = [t.strip().replace(" ", "_").lower()
             for t in seed_tags.replace("\n", ",").split(",")
             if t.strip()]

    # If no seeds given, pick a random high-count character or species tag
    if not seeds:
        pool = _DB.by_category.get(4, []) + _DB.by_category.get(5, [])
        pool = [t for t in pool if _DB.tags[t]["count"] >= min_post_count and t not in user_filter]
        if pool:
            pool_sorted = sorted(pool, key=lambda t: _DB.tags[t]["count"], reverse=True)
            seeds = [rng.choice(pool_sorted[:200])]

    # Adjust target count for variability
    effective_target = tag_count + int(tag_count * variability * 0.5)

    generated = _expand_from_seeds(
        seeds         = seeds,
        rng           = rng,
        target_count  = effective_target,
        source_filter = source,
        rating        = rating,
        min_count     = min_post_count,
        user_filter   = user_filter,
    )

    # Trim back to target count
    if len(generated) > tag_count:
        seed_set = set(seeds) & set(generated)
        others   = [t for t in generated if t not in seed_set]
        others   = sorted(others, key=lambda t: _DB.tags[t].get("count", 0), reverse=True)
        generated = list(seed_set) + others[:tag_count - len(seed_set)]

    # Sort into natural order
    generated = _sort_tags(generated)

    # Build quality prefix
    quality_prefix = []
    if add_quality:
        picks = rng.sample(_QUALITY_TAGS, min(quality_count, len(_QUALITY_TAGS)))
        quality_prefix = picks

    # Assemble final prompt
    parts = []
    if prepend.strip():
        parts.append(prepend.strip())
    if quality_prefix:
        parts.extend(quality_prefix)
    parts.extend(generated)
    if append.strip():
        parts.append(append.strip())

    prompt = ", ".join(parts).replace("_", " ")

    # Debug info
    sources_used = set(_DB.tags.get(t, {}).get("source", "?") for t in generated)
    filter_summary = f"\nFiltered out: {len(user_filter)} user tag(s)" if user_filter else ""
    debug = (
        f"Seeds: {', '.join(seeds) or 'none (random)'}\n"
        f"Generated: {len(generated)} tags from {', '.join(sorted(sources_used))}\n"
        f"Total output tags: {len(parts)}"
        f"{filter_summary}"
    )

    return (prompt, debug)


# ─────────────────────────────────────────────────────────────────────────────
#  ComfyUI Node
# ─────────────────────────────────────────────────────────────────────────────

class PromptGenerator:
    """
    Semi-random prompt generator using Danbooru/e621 tag co-occurrence data.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "seed_tags": ("STRING", {
                    "multiline": True,
                    "default":   "",
                    "tooltip":   (
                        "Comma-separated or one-per-line starting tags. The generator "
                        "will find tags that naturally co-occur with these. "
                        "Leave blank for a fully random starting point."
                    ),
                }),
                "filter_tags": ("STRING", {
                    "multiline": True,
                    "default":   "",
                    "tooltip":   (
                        "Tags to EXCLUDE from generated output.\n"
                        "Enter one per line or comma-separate them.\n"
                        "Spaces and underscores are treated the same.\n"
                        "Lines starting with # are treated as comments and ignored.\n\n"
                        "Example:\n"
                        "  male_focus\n"
                        "  solo\n"
                        "  monochrome"
                    ),
                }),
                "tag_count": ("INT", {
                    "default": 20, "min": 1, "max": 80, "step": 1,
                    "tooltip": "How many tags to generate (excluding prepend/append/quality).",
                }),
                "source": (["danbooru", "e621", "all"], {
                    "default": "all",
                    "tooltip": "Which tag database to pull from.",
                }),
                "rating": (["safe", "nsfw", "all"], {
                    "default": "safe",
                    "tooltip": (
                        "safe  = exclude explicit/questionable tags\n"
                        "nsfw  = exclude safe-only tags\n"
                        "all   = no rating filter"
                    ),
                }),
                "variability": ("FLOAT", {
                    "default": 0.5, "min": 0.0, "max": 1.0, "step": 0.05,
                    "tooltip": (
                        "0.0 = always pick the most co-occurring (predictable)\n"
                        "1.0 = heavily randomised selection (surprising)"
                    ),
                }),
                "min_post_count": ("INT", {
                    "default": 500, "min": 0, "max": 100000, "step": 100,
                    "tooltip": "Ignore tags with fewer posts than this. Higher = more common tags only.",
                }),
                "add_quality_tags": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Prepend quality tags like 'masterpiece, best_quality'.",
                }),
                "quality_tag_count": ("INT", {
                    "default": 3, "min": 1, "max": 8, "step": 1,
                }),
                "seed": ("INT", {
                    "default": 0, "min": -1, "max": 0xffffffffffffffff,
                    "tooltip": "-1 = random every run. 0+ = reproducible.",
                }),
            },
            "optional": {
                "prepend_text": ("STRING", {
                    "multiline": False,
                    "default":   "",
                    "tooltip":   "Text placed at the very start of the prompt (before quality tags).",
                }),
                "append_text": ("STRING", {
                    "multiline": False,
                    "default":   "",
                    "tooltip":   "Text placed at the very end of the prompt.",
                }),
            },
        }

    RETURN_TYPES  = ("STRING", "STRING")
    RETURN_NAMES  = ("prompt",  "debug_info")
    FUNCTION      = "generate"
    CATEGORY      = "Arctenox Essentials/Prompting"

    DESCRIPTION = (
        "Generates semi-random prompts by walking the tag co-occurrence graph. "
        "Give it seed tags and it finds naturally related ones. "
        "Use filter_tags to exclude anything you don't want in the output. "
        "Connect the prompt output directly to a CLIP Text Encode node."
    )

    @classmethod
    def IS_CHANGED(cls, seed, filter_tags="", **kwargs):
        if seed == -1:
            return float("NaN")
        # Include filter in cache key so changing it forces a re-run
        return hash((seed, filter_tags))

    def generate(
        self,
        seed_tags:         str,
        filter_tags:       str,
        tag_count:         int,
        source:            str,
        rating:            str,
        variability:       float,
        min_post_count:    int,
        add_quality_tags:  bool,
        quality_tag_count: int,
        seed:              int,
        prepend_text:      str = "",
        append_text:       str = "",
    ):
        prompt, debug = generate_prompt(
            seed_tags      = seed_tags,
            source         = source,
            tag_count      = tag_count,
            variability    = variability,
            rating         = rating,
            min_post_count = min_post_count,
            add_quality    = add_quality_tags,
            quality_count  = quality_tag_count,
            prepend        = prepend_text,
            append         = append_text,
            seed           = seed,
            filter_tags    = filter_tags,
        )
        return (prompt, debug)


# ─────────────────────────────────────────────────────────────────────────────
#  Registration
# ─────────────────────────────────────────────────────────────────────────────

NODE_CLASS_MAPPINGS = {
    "ArctenoxPromptGenerator": PromptGenerator,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ArctenoxPromptGenerator": "Prompt Generator (Arctenox's Essentials)",
}
