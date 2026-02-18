/**
 * Arctenox Essentials — Combined Tag & Wildcard Autocomplete
 * ===========================================================
 * Version: 2.1.0  •  Author: Arctenox  •  License: GPL-3.0
 *
 * Replaces BOTH arctenox_autocomplete.js AND arctenox_wildcard_autocomplete.js
 * Only this one file should be in the web/ folder.
 *
 * Triggers:
 *   typing           → tag autocomplete (danbooru / e621 / all)
 *   <lora:           → LoRA autocomplete
 *   embedding:       → embedding autocomplete
 *   __               → wildcard file picker
 *   {                → inline option picker
 *   <c:              → chant bulk-insert
 *   Ctrl+Space       → show all wildcards manually
 *   Home (configurable) → show all tags for current textarea
 *   F1               → open wiki for selected tag
 *   Alt+Shift+F      → manual prompt format
 */

import { app } from "../../scripts/app.js";

// ─────────────────────────────────────────────────────────────────────────────
//  Settings
// ─────────────────────────────────────────────────────────────────────────────

const S_NS = "ArctenoxEssentials.Autocomplete";
const DEFAULTS = {
    enabled:           true,
    tagSource:         "all",
    maxSuggestions:    50,
    autoComma:         true,
    replaceUnderscore: false,
    enableLorasEmb:    true,
    autoFormat:        true,
    autoFormatTrigger: "auto",
    trailingComma:     false,
    hideAlias:         false,
    enableWildcards:   true,
};

function getSetting(key) {
    try {
        const v = app.ui?.settings?.getSettingValue(`${S_NS}.${key}`);
        return v !== undefined ? v : DEFAULTS[key];
    } catch { return DEFAULTS[key]; }
}

// ─────────────────────────────────────────────────────────────────────────────
//  Category colours / labels
// ─────────────────────────────────────────────────────────────────────────────

const CAT_COLORS = {
    0: "#b5c0d0",
    1: "#f2ac08",
    3: "#d0614f",
    4: "#7bae3e",
    5: "#ee76a4",
    6: "#888888",
    7: "#aaaaaa",
    8: "#228b22",
};

const CAT_LABELS = {
    0: "gen", 1: "artist", 3: "copy", 4: "char", 5: "spec", 6: "inv", 7: "meta", 8: "lore",
};

// Plain text source labels — avoids broken emoji squares in ComfyUI
const SOURCE_LABELS = {
    danbooru:  "DB",
    e621:      "E6",
    lora:      "LR",
    embedding: "EM",
    wildcard:  "WC",
};

// ─────────────────────────────────────────────────────────────────────────────
//  Data caches
// ─────────────────────────────────────────────────────────────────────────────

const _tagCache = new Map();
const _TAG_CACHE_MAX = 500;

async function fetchTags(query, source) {
    if (!query) return [];
    const key = `${source}:${query}`;
    if (_tagCache.has(key)) return _tagCache.get(key);
    try {
        const limit = getSetting("maxSuggestions") || 50;
        const r = await fetch(`/arctenox/ac/tags?q=${encodeURIComponent(query)}&source=${source}&limit=${limit}`);
        if (!r.ok) return [];
        const data = await r.json();
        if (_tagCache.size >= _TAG_CACHE_MAX) _tagCache.delete(_tagCache.keys().next().value);
        _tagCache.set(key, data);
        return data;
    } catch { return []; }
}

let _loras = null, _embeddings = null, _wildcards = null, _wcPromise = null;

async function fetchLoras() {
    if (_loras) return _loras;
    try { _loras = await (await fetch("/arctenox/ac/loras")).json(); } catch { _loras = []; }
    return _loras;
}
async function fetchEmbeddings() {
    if (_embeddings) return _embeddings;
    try { _embeddings = await (await fetch("/arctenox/ac/embeddings")).json(); } catch { _embeddings = []; }
    return _embeddings;
}
async function fetchWildcards() {
    if (_wildcards !== null) return _wildcards;
    if (_wcPromise) return _wcPromise;
    _wcPromise = fetch("/arctenox/wildcards")
        .then(r => r.json())
        .then(d => { _wildcards = d; return d; })
        .catch(() => { _wildcards = {}; return {}; });
    return _wcPromise;
}

// ─────────────────────────────────────────────────────────────────────────────
//  Utilities
// ─────────────────────────────────────────────────────────────────────────────

function fmtCount(n) {
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
    if (n >= 1_000)     return `${(n / 1_000).toFixed(1)}k`;
    return n > 0 ? String(n) : "";
}

function escRx(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }

function getEnteredTags(text) {
    const tags = new Set();
    for (const part of text.split(/[,\n]/)) {
        const t = part.trim().replace(/\s+/g, "_").toLowerCase();
        if (t) tags.add(t);
    }
    return tags;
}

function getWordAtCursor(ta) {
    const pos  = ta.selectionStart;
    const text = ta.value;
    let start = pos;
    while (start > 0 && text[start - 1] !== "," && text[start - 1] !== "\n") start--;
    while (start < pos && text[start] === " ") start++;
    return { word: text.slice(start, pos), start, end: pos };
}

function processTagForInsert(tag) {
    return getSetting("replaceUnderscore") ? tag.replace(/_/g, " ") : tag;
}

function openWiki(item) {
    if (!item?.name) return;
    const name = item.name.replace(/ /g, "_");
    const url = item.source === "e621"
        ? `https://e621.net/wiki_pages/${encodeURIComponent(name)}`
        : `https://danbooru.donmai.us/wiki_pages/${encodeURIComponent(name)}`;
    window.open(url, "_blank");
}

// ─────────────────────────────────────────────────────────────────────────────
//  Styles
// ─────────────────────────────────────────────────────────────────────────────

(function injectStyles() {
    if (document.getElementById("arctenox-ac-styles")) return;
    const s = document.createElement("style");
    s.id = "arctenox-ac-styles";
    s.textContent = `
        #arctenox-ac-dropdown {
            font-family: "Inter", "Segoe UI", system-ui, sans-serif;
            font-size: 13px;
            box-sizing: border-box;
        }
        #arctenox-ac-dropdown * {
            box-sizing: border-box;
        }
        .arc-panel-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 5px 12px;
            background: rgba(0,0,0,0.45);
            border-bottom: 1px solid rgba(255,255,255,0.09);
            font-size: 11px;
            font-weight: 600;
            color: #aab;
            flex-shrink: 0;
            user-select: none;
            gap: 8px;
            letter-spacing: 0.03em;
        }
        .arc-panel-header-hint {
            font-size: 10px;
            font-weight: 400;
            opacity: 0.4;
            white-space: nowrap;
        }
        .arc-scrollable {
            overflow-y: auto;
        }
        .arc-scrollable::-webkit-scrollbar { width: 4px; }
        .arc-scrollable::-webkit-scrollbar-track { background: transparent; }
        .arc-scrollable::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 4px; }

        .arc-item {
            display: grid;
            grid-template-columns: 14px 1fr auto 58px 28px;
            align-items: center;
            padding: 4px 10px 4px 8px;
            cursor: pointer;
            min-height: 26px;
            transition: background 0.05s;
            border-bottom: 1px solid rgba(255,255,255,0.03);
        }
        .arc-item:hover { background: rgba(255,255,255,0.07); }
        .arc-item.arc-selected { background: rgba(80,100,220,0.22); }
        .arc-item.arc-entered { opacity: 0.3; }
        .arc-dot {
            width: 7px; height: 7px;
            border-radius: 50%;
            justify-self: center;
        }
        .arc-name {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            padding: 0 6px 0 4px;
            font-size: 13px;
        }
        .arc-alias {
            font-size: 11px;
            color: #667;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .arc-src-badge {
            font-size: 9px;
            font-weight: 700;
            padding: 1px 4px;
            border-radius: 3px;
            white-space: nowrap;
            letter-spacing: 0.04em;
            align-self: center;
        }
        .arc-src-db {
            background: rgba(140,70,220,0.22);
            color: #c49af5;
        }
        .arc-src-e6 {
            background: rgba(220,120,30,0.22);
            color: #f5a352;
        }
        .arc-src-other {
            background: rgba(255,255,255,0.07);
            color: #778;
        }
        .arc-pct {
            font-size: 11px;
            color: #8899bb;
            text-align: right;
            white-space: nowrap;
            padding-right: 6px;
            font-variant-numeric: tabular-nums;
        }
        .arc-cat {
            font-size: 10px;
            font-weight: 600;
            text-align: center;
            opacity: 0.72;
            letter-spacing: 0.02em;
            white-space: nowrap;
        }
        .arc-wiki {
            display: none;
            font-size: 10px;
            cursor: pointer;
            padding: 1px 4px;
            border-radius: 3px;
            color: #99b;
            background: rgba(255,255,255,0.06);
            white-space: nowrap;
            grid-column: 2;
            justify-self: end;
            margin-right: 4px;
        }
        .arc-item:hover .arc-wiki { display: inline; }
        .arc-wiki:hover { background: rgba(255,255,255,0.12); }
        .arc-close-btn {
            background: none;
            border: none;
            color: #778;
            cursor: pointer;
            font-size: 12px;
            line-height: 1;
            padding: 2px 4px;
            border-radius: 3px;
            margin-left: auto;
            flex-shrink: 0;
            transition: color 0.1s, background 0.1s;
        }
        .arc-close-btn:hover { color: #dde; background: rgba(255,255,255,0.1); }
        .arc-empty {
            padding: 10px 12px;
            color: #446;
            font-style: italic;
            font-size: 12px;
        }
    `;
    document.head.appendChild(s);
})();

// ─────────────────────────────────────────────────────────────────────────────
//  Autocomplete Dropdown
// ─────────────────────────────────────────────────────────────────────────────

class AcDropdown {
    constructor() {
        this._el           = null;
        this._headerLabel  = null;
        this._scrollable   = null;
        this._textarea     = null;
        this._items        = [];
        this._selected     = 0;
        this._mode         = null;
        this._wordStart    = 0;
        this._wordEnd      = 0;
        this._debounce     = null;
        this._dragging     = false;
        this._dragged      = false;  // true once user has manually moved it
        this._dragOffX     = 0;
        this._dragOffY     = 0;
        this._onKey        = this._handleKey.bind(this);
        this._onInput      = this._handleInput.bind(this);
        this._onBlur       = this._handleBlur.bind(this);
        this._build();
    }

    _build() {
        const el = document.createElement("div");
        el.id = "arctenox-ac-dropdown";
        Object.assign(el.style, {
            position:      "fixed",
            zIndex:        "99999",
            background:    "var(--comfy-menu-bg, #1c1c26)",
            border:        "1px solid rgba(255,255,255,0.1)",
            borderRadius:  "8px",
            boxShadow:     "0 8px 30px rgba(0,0,0,0.75)",
            minWidth:      "380px",
            maxWidth:      "560px",
            display:       "none",
            overflow:      "hidden",
            flexDirection: "column",
            userSelect:    "none",
        });

        const hdr = document.createElement("div");
        hdr.className = "arc-panel-header";
        hdr.style.cursor = "grab";

        const lbl = document.createElement("span");
        lbl.textContent = "Autocomplete";
        const hint = document.createElement("span");
        hint.className = "arc-panel-header-hint";
        hint.textContent = "↑↓  Enter/Tab insert  F1 wiki";

        // X close button
        const closeBtn = document.createElement("button");
        closeBtn.textContent = "✕";
        closeBtn.className = "arc-close-btn";
        closeBtn.addEventListener("mousedown", e => { e.preventDefault(); e.stopPropagation(); this.hide(); });

        hdr.appendChild(lbl);
        hdr.appendChild(hint);
        hdr.appendChild(closeBtn);
        this._headerLabel = lbl;

        // Drag logic
        hdr.addEventListener("mousedown", e => {
            if (e.target === closeBtn) return;
            e.preventDefault();
            this._dragging = true;
            this._dragged  = true;
            hdr.style.cursor = "grabbing";
            const rect = el.getBoundingClientRect();
            this._dragOffX = e.clientX - rect.left;
            this._dragOffY = e.clientY - rect.top;
        });
        document.addEventListener("mousemove", e => {
            if (!this._dragging) return;
            let left = e.clientX - this._dragOffX;
            let top  = e.clientY - this._dragOffY;
            left = Math.max(0, Math.min(window.innerWidth  - el.offsetWidth,  left));
            top  = Math.max(0, Math.min(window.innerHeight - el.offsetHeight, top));
            el.style.left = left + "px";
            el.style.top  = top  + "px";
        });
        document.addEventListener("mouseup", () => {
            if (this._dragging) { this._dragging = false; hdr.style.cursor = "grab"; }
        });

        const scrollable = document.createElement("div");
        scrollable.className = "arc-scrollable";
        scrollable.style.maxHeight = "360px";
        this._scrollable = scrollable;

        el.appendChild(hdr);
        el.appendChild(scrollable);
        document.body.appendChild(el);
        this._el = el;
    }

    attach(ta) {
        if (this._textarea === ta) return;
        this.detach();
        this._textarea = ta;
        ta.addEventListener("keydown", this._onKey);
        ta.addEventListener("input",   this._onInput);
        ta.addEventListener("blur",    this._onBlur);
    }

    detach() {
        if (!this._textarea) return;
        this._textarea.removeEventListener("keydown", this._onKey);
        this._textarea.removeEventListener("input",   this._onInput);
        this._textarea.removeEventListener("blur",    this._onBlur);
        this._textarea = null;
        // Don't hide — panel stays until X is clicked
    }

    show(items, mode, wordStart, wordEnd, label) {
        this._mode      = mode;
        this._wordStart = wordStart;
        this._wordEnd   = wordEnd;
        this._items     = items;
        this._selected  = 0;
        if (label) this._headerLabel.textContent = label;
        this._render();
        if (!items.length) { this.hide(); return; }
        this._el.style.display = "flex";
        if (!this._dragged) this._position();
    }

    hide() {
        this._el.style.display = "none";
        this._items   = [];
        this._mode    = null;
        this._dragged = false;
        clearTimeout(this._debounce);
    }

    isVisible() { return this._el.style.display !== "none"; }

    _render() {
        this._scrollable.innerHTML = "";
        const entered   = this._textarea ? getEnteredTags(this._textarea.value) : new Set();
        const hideAlias = getSetting("hideAlias");
        const srcSet    = new Set(this._items.map(i => i.source || "tag"));

        this._items.forEach((item, idx) => {
            const src       = item.source || "tag";
            const isSel     = idx === this._selected;
            const isEntered = item.name && entered.has(item.name.toLowerCase());
            const color     = CAT_COLORS[item.category ?? 0] ?? CAT_COLORS[0];
            const catLabel  = CAT_LABELS[item.category ?? 0] ?? "";

            const row = document.createElement("div");
            row.className = "arc-item" +
                (isSel     ? " arc-selected" : "") +
                (isEntered ? " arc-entered"  : "");

            // Col 1: colour dot
            const dot = document.createElement("span");
            dot.className = "arc-dot";
            dot.style.background = color;
            row.appendChild(dot);

            // Col 2: tag name (+ optional alias overlay on hover via wiki slot)
            const nameWrap = document.createElement("span");
            nameWrap.style.cssText = "display:contents";

            const name = document.createElement("span");
            name.className = "arc-name";
            name.textContent = item.displayName ?? item.name ?? item.label ?? "";
            name.style.color = isSel ? "#fff" : color;
            row.appendChild(name);

            // Wiki link — hidden, appears on hover inside col 2
            if (src === "danbooru" || src === "e621") {
                const wiki = document.createElement("span");
                wiki.className = "arc-wiki";
                wiki.textContent = "wiki";
                wiki.title = "Open wiki (F1)";
                wiki.addEventListener("mousedown", e => {
                    e.preventDefault();
                    e.stopPropagation();
                    openWiki(item);
                });
                row.appendChild(wiki);
            }

            // Col 3: source badge with per-source colour
            const srcBadge = document.createElement("span");
            srcBadge.className = "arc-src-badge";
            if (src === "danbooru")       { srcBadge.textContent = "DB"; srcBadge.classList.add("arc-src-db"); }
            else if (src === "e621")      { srcBadge.textContent = "E6"; srcBadge.classList.add("arc-src-e6"); }
            else if (src === "lora")      { srcBadge.textContent = "LR"; srcBadge.classList.add("arc-src-other"); }
            else if (src === "embedding") { srcBadge.textContent = "EM"; srcBadge.classList.add("arc-src-other"); }
            else if (src === "wildcard")  { srcBadge.textContent = "WC"; srcBadge.classList.add("arc-src-other"); }
            else                          { srcBadge.classList.add("arc-src-other"); }
            row.appendChild(srcBadge);

            // Col 4: image count
            const pct = document.createElement("span");
            pct.className = "arc-pct";
            if (item.count > 0) pct.textContent = fmtCount(item.count);
            row.appendChild(pct);

            // Col 4: category label
            const cat = document.createElement("span");
            cat.className = "arc-cat";
            cat.textContent = catLabel || (src !== "danbooru" && src !== "e621" ? src.slice(0,2).toUpperCase() : "");
            cat.style.color = color;
            row.appendChild(cat);

            const ci = idx;
            row.addEventListener("mousedown", e => {
                e.preventDefault();
                this._selected = ci;
                this._commit();
            });
            row.addEventListener("mouseenter", () => {
                this._selected = ci;
                this._render();
            });

            this._scrollable.appendChild(row);
        });
    }

    _moveSel(d) {
        this._selected = Math.max(0, Math.min(this._items.length - 1, this._selected + d));
        this._render();
        this._scrollable.querySelectorAll(".arc-item")[this._selected]?.scrollIntoView({ block: "nearest" });
    }

    _commit() {
        if (!this._textarea || !this._items.length) { this.hide(); return; }
        const item = this._items[this._selected];
        if (!item) { this.hide(); return; }

        const ta     = this._textarea;
        const before = ta.value.slice(0, this._wordStart);
        const after  = ta.value.slice(this._wordEnd);
        let ins = "";

        if (this._mode === "tag") {
            const entered = getEnteredTags(ta.value);
            const tagLow  = (item.name || "").toLowerCase();
            if (entered.has(tagLow)) {
                const rx = new RegExp(`(?:^|,|\\n)\\s*${escRx(item.name)}`, "i");
                const m  = ta.value.match(rx);
                if (m) {
                    const off = ta.value.indexOf(m[0]) + m[0].length - item.name.length;
                    ta.setSelectionRange(off, off + item.name.length);
                }
                this.hide();
                return;
            }
            ins = processTagForInsert(item.name ?? "");
            if (getSetting("autoComma")) {
                const tb = before.trimEnd();
                if (tb.length > 0 && !tb.endsWith(",")) ins = ", " + ins;
                const ta2 = after.trimStart();
                if (ta2.length > 0 && !ta2.startsWith(",") && !ta2.startsWith("\n")) ins += ", ";
            }
        } else if (this._mode === "lora")      { ins = `<lora:${item.name}:1>`; }
        else if (this._mode === "embedding")   { ins = `embedding:${item.name}`; }
        else if (this._mode === "wildcard")    { ins = `__${item.name}__`; }
        else if (this._mode === "inline")      { ins = item.insertText ?? item.name ?? ""; }

        ta.value = before + ins + after;
        const np = before.length + ins.length;
        ta.setSelectionRange(np, np);
        ta.dispatchEvent(new Event("input",  { bubbles: true }));
        ta.dispatchEvent(new Event("change", { bubbles: true }));
        this.hide();
    }

    _handleKey(e) {
        if (e.code === "Space" && e.ctrlKey && !e.shiftKey) {
            if (!this.isVisible()) { e.preventDefault(); this._triggerWildcardManual(); }
            return;
        }
        if (!this.isVisible()) return;
        if (e.key === "ArrowDown") { e.preventDefault(); this._moveSel(1);  return; }
        if (e.key === "ArrowUp")   { e.preventDefault(); this._moveSel(-1); return; }
        if (e.key === "Enter")     { e.preventDefault(); this._commit();    return; }
        if (e.key === "Tab")       { e.preventDefault(); this._commit();    return; }
        if (e.key === "Escape")    { e.preventDefault(); this.hide();       return; }
        if (e.key === "F1")        { e.preventDefault(); openWiki(this._items[this._selected]); }
    }

    async _handleInput() {
        if (!getSetting("enabled")) return;
        const ta   = this._textarea;
        const pos  = ta.selectionStart;
        const text = ta.value.slice(0, pos);

        // 1. Wildcard __ trigger
        if (getSetting("enableWildcards")) {
            const wm = text.match(/__([a-zA-Z0-9_/.-]*)$/);
            if (wm) {
                const query = wm[1];
                const start = pos - wm[0].length;
                const data  = await fetchWildcards();
                const keys  = Object.keys(data);
                const items = keys
                    .filter(k => k.toLowerCase().startsWith(query.toLowerCase()))
                    .map(k => ({
                        name:        k,
                        displayName: `__${k}__`,
                        source:      "wildcard",
                        count:       data[k]?.length ?? 0,
                        category:    5,
                    }));
                if (items.length) { this.show(items, "wildcard", start, pos, `Wildcards (${keys.length})`); return; }
                this.hide(); return;
            }

            // 2. Inline { trigger
            const im = text.match(/\{([^{}]*)$/);
            if (im) {
                const query = im[1];
                const start = pos - im[0].length;
                const data  = await fetchWildcards();
                const items = [];
                for (const [stem, opts] of Object.entries(data)) {
                    const matching = query ? opts.filter(o => o.toLowerCase().includes(query.toLowerCase())) : opts;
                    if (matching.length) {
                        items.push({ name: stem, displayName: `{${stem}}`, insertText: `{${opts.slice(0,8).join("|")}}`, source: "wildcard", count: opts.length, category: 5 });
                        matching.slice(0, 4).forEach(o => items.push({ name: o, displayName: o, insertText: `{${o}}`, source: "wildcard", count: 0, category: 0 }));
                    }
                }
                if (items.length) { this.show(items, "inline", start, pos, "Inline Options"); return; }
            }
        }

        // 3. LoRA trigger
        if (getSetting("enableLorasEmb")) {
            const lm = text.match(/<lora:([^>]*)$/);
            if (lm) {
                const query = lm[1].toLowerCase();
                const start = pos - lm[0].length;
                const loras = await fetchLoras();
                const items = loras.filter(l => l.name.toLowerCase().includes(query))
                    .map(l => ({ ...l, displayName: l.name, source: "lora", category: 7, count: 0 }));
                if (items.length) { this.show(items, "lora", start, pos, "LoRA"); return; }
                this.hide(); return;
            }

            // 4. Embedding trigger
            const em = text.match(/embedding:([^\s,]*)$/);
            if (em) {
                const query = em[1].toLowerCase();
                const start = pos - em[0].length;
                const embs  = await fetchEmbeddings();
                const items = embs.filter(e => e.name.toLowerCase().includes(query))
                    .map(e => ({ ...e, displayName: e.name, source: "embedding", category: 7, count: 0 }));
                if (items.length) { this.show(items, "embedding", start, pos, "Embeddings"); return; }
                this.hide(); return;
            }
        }

        // 5. Chant trigger
        const cm = text.match(/<c:([^>]*)$/);
        if (cm) {
            const query = cm[1].toLowerCase();
            const start = pos - cm[0].length;
            const src   = getSetting("tagSource");
            const tags  = await fetchTags(query || " ", src);
            const chants = tags.filter(t => t.chant);
            if (chants.length) { this.show(chants, "tag", start, pos, "Chants"); return; }
            this.hide(); return;
        }

        // 6. Normal tag autocomplete
        const { word, start: ws, end: we } = getWordAtCursor(ta);
        const q = word.trim();
        clearTimeout(this._debounce);
        if (q.length < 1) { this.hide(); return; }

        this._debounce = setTimeout(async () => {
            const source = getSetting("tagSource");
            const tags   = await fetchTags(q, source);
            if (!tags.length) { this.hide(); return; }
            if (ta.selectionStart !== we) return;
            const lbl = source === "all" ? "All Tags" : source.charAt(0).toUpperCase() + source.slice(1) + " Tags";
            this.show(tags, "tag", ws, we, lbl);
        }, 120);
    }

    _handleBlur(e) {
        // Panel stays open until X is clicked — only auto-format on blur
        if (getSetting("autoFormat") && getSetting("autoFormatTrigger") === "auto" && this._textarea) {
            _autoFormat(this._textarea);
        }
    }

    async _triggerWildcardManual() {
        if (!this._textarea) return;
        const pos  = this._textarea.selectionStart;
        const data = await fetchWildcards();
        const items = Object.keys(data).map(k => ({
            name:        k,
            displayName: `__${k}__`,
            source:      "wildcard",
            count:       data[k]?.length ?? 0,
            category:    5,
        }));
        if (!items.length) return;
        this.show(items, "wildcard", pos, pos, `All Wildcards (${items.length})`);
    }

    async _triggerShowAll() {
        if (!this._textarea) return;
        const ta     = this._textarea;
        const source = getSetting("tagSource");
        // Collect all unique tags already in the textarea
        const lines  = ta.value.split(/[\n,]/).map(t => t.trim()).filter(Boolean);
        const unique = [...new Set(lines.map(t => t.replace(/\s+/g, "_").toLowerCase()))];
        if (!unique.length) return;
        // Fetch suggestions for each tag and merge, deduplicated
        const seen = new Set();
        const all  = [];
        await Promise.all(unique.map(async q => {
            const tags = await fetchTags(q, source);
            for (const t of tags) {
                if (!seen.has(t.name)) { seen.add(t.name); all.push(t); }
            }
        }));
        if (!all.length) return;
        all.sort((a, b) => (b.count || 0) - (a.count || 0));
        const pos = ta.selectionStart;
        const lbl = source === "all" ? "All Tags" : source.charAt(0).toUpperCase() + source.slice(1) + " Tags";
        this.show(all, "tag", pos, pos, lbl);
    }

    _position() {
        const ta = this._textarea;
        if (!ta) return;
        const rect  = ta.getBoundingClientRect();
        const text  = ta.value.slice(0, ta.selectionStart);
        const lineH = parseInt(getComputedStyle(ta).lineHeight) || 18;
        const lines = text.split("\n");
        const caretY = rect.top + (lines.length - 1) * lineH + lineH;
        const caretX = rect.left + 12;
        const ddW = 560, ddH = 400;
        let top  = caretY + 4;
        let left = caretX;
        if (top  + ddH > window.innerHeight) top  = caretY - ddH - 4;
        if (left + ddW > window.innerWidth)  left = window.innerWidth - ddW - 8;
        if (left < 4) left = 4;
        if (top  < 4) top  = 4;
        this._el.style.top  = `${top}px`;
        this._el.style.left = `${left}px`;
    }
}


function _autoFormat(ta) {
    if (!ta || !getSetting("autoFormat")) return;
    const original = ta.value;
    const result = original.split("\n").map(line => {
        const parts = line.split(",").map(p => p.trim()).filter(Boolean);
        if (!parts.length) return line;
        return getSetting("trailingComma") ? parts.join(", ") + "," : parts.join(", ");
    }).join("\n");
    if (result !== original) {
        const sel = ta.selectionStart;
        ta.value = result;
        ta.setSelectionRange(Math.min(sel, result.length), Math.min(sel, result.length));
        ta.dispatchEvent(new Event("input",  { bubbles: true }));
        ta.dispatchEvent(new Event("change", { bubbles: true }));
    }
}

document.addEventListener("keydown", e => {
    if (e.altKey && e.shiftKey && e.key === "F" && document.activeElement?.tagName === "TEXTAREA") {
        e.preventDefault();
        _autoFormat(document.activeElement);
    }
});

// ─────────────────────────────────────────────────────────────────────────────
//  Attach / scan
// ─────────────────────────────────────────────────────────────────────────────

const dropdown     = new AcDropdown();

function attachToTextarea(ta) {
    if (!ta || ta.tagName !== "TEXTAREA") return;
    if (ta.getAttribute("data-arctenox-ac")) return;
    ta.setAttribute("data-arctenox-ac", "1");

    ta.addEventListener("focus", () => dropdown.attach(ta));

    if (document.activeElement === ta) dropdown.attach(ta);
}

function scanAndAttach() {
    document.querySelectorAll("textarea").forEach(attachToTextarea);
}

new MutationObserver(mutations => {
    for (const mut of mutations) {
        for (const node of mut.addedNodes) {
            if (node.nodeType !== 1) continue;
            if (node.tagName === "TEXTAREA") attachToTextarea(node);
            else node.querySelectorAll?.("textarea").forEach(attachToTextarea);
        }
    }
}).observe(document.body, { childList: true, subtree: true });

// ─────────────────────────────────────────────────────────────────────────────
//  Settings registration
// ─────────────────────────────────────────────────────────────────────────────

function registerSettings() {
    try {
        const add = (id, name, type, def, extra = {}) =>
            app.ui.settings.addSetting({ id: `${S_NS}.${id}`, name: `Arctenox: ${name}`, type, defaultValue: def, ...extra });

        add("enabled",           "Enable Autocomplete",            "boolean", true);
        add("tagSource",         "Tag Source",                     "combo",   "all",      { options: ["danbooru", "e621", "all"] });
        add("maxSuggestions",    "Max Suggestions",                "slider",  50,         { attrs: { min: 10, max: 200, step: 10 } });
        add("autoComma",         "Auto-insert Comma After Tag",    "boolean", true);
        add("replaceUnderscore", "Replace _ with Space on Insert", "boolean", false);
        add("enableLorasEmb",    "LoRA & Embedding Autocomplete",  "boolean", true);
        add("enableWildcards",   "Wildcard Autocomplete",          "boolean", true);
        add("autoFormat",        "Auto-format Prompt on Blur",     "boolean", true);
        add("autoFormatTrigger", "Auto-format Trigger",            "combo",   "auto",     { options: ["auto", "manual"] });
        add("trailingComma",     "Trailing Comma in Formatter",    "boolean", false);
        add("hideAlias",         "Hide Alias in Suggestions",      "boolean", false);
    } catch (err) {
        console.warn("[Arctenox AC] Could not register settings:", err);
    }
}

// ─────────────────────────────────────────────────────────────────────────────
//  ComfyUI Extension
// ─────────────────────────────────────────────────────────────────────────────

app.registerExtension({
    name: "ArctenoxEssentials.Autocomplete",

    commands: [
        {
            id:      "ArctenoxEssentials.ShowAllTags",
            label:   "Arctenox: Show All Tags",
            function: () => {
                const ta = document.activeElement;
                if (ta?.tagName === "TEXTAREA") dropdown._triggerShowAll();
            },
        },
    ],

    keybindings: [
        {
            combo:     { key: "Home" },
            commandId: "ArctenoxEssentials.ShowAllTags",
        },
    ],

    async setup() {
        registerSettings();
        await new Promise(r => setTimeout(r, 500));
        scanAndAttach();
    },

    async nodeCreated(node) {
        await new Promise(r => setTimeout(r, 30));
        for (const w of (node.widgets || [])) {
            if (w.inputEl?.tagName === "TEXTAREA") attachToTextarea(w.inputEl);
        }
    },
});

// Pre-warm caches
(async () => {
    await new Promise(r => setTimeout(r, 1200));
    const src = getSetting("tagSource");
    fetchTags("1girl", src);
    fetchWildcards();
    if (getSetting("enableLorasEmb")) { fetchLoras(); fetchEmbeddings(); }
})();
