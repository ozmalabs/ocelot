"""format_channel — FORMAT AS A GENERIC SIGNAL CHANNEL, decoded by COLLAPSE.

The LAYOUT of a text is a signal channel PARALLEL to its content. It carries
nothing about the story, but something TRUE about the FILE: a hard-wrap at ~80
columns says 'this file is laid out for a terminal' (its display MEDIUM); a
regular line-break-plus-rhyme says 'this is verse' (PROSODY, format-AS-content);
leading whitespace says 'this is nested' (STRUCTURE / code); a plain paragraphed
block says 'this is a letter/note' (REGISTER). Formatting is ONE GENERIC function
at every order-N scale, and PROSODY (the meter faculty) is just the one member of
it the reader already had -- which is why the reader MISTOOK a hard-wrapped Grimm
tale for verse: it had prosody and nothing else to read the layout as.

This faculty is the prosodic/ink/construction twin: a ShapeDecode over a held
FORMAT-FUNCTION codebook (seeds/format_channel.json). The pipeline mirrors
metrical_reading exactly:

  TEXT ─perceive→ LAYOUT FEATURES ─quantize→ FUNCTIONAL TOKEN VECTOR
       ─ShapeDecode(compose_design_for_goal = Rust ShapeDecode Term)→ FORMAT
       (no seeded signature covers it ─mint→ install → re-decode)

The three functional features are COLUMN-AGNOSTIC (no magic width number):

  * wrap_pressure — are the line breaks FORCED by a width limit? At each break,
    would the first word of the next line have fit on the current line WITHOUT
    exceeding the text's OWN widest line (its implicit column)? A hard wrap fills
    each line to the column and breaks because the next word won't fit (high
    pressure); verse breaks VOLUNTARILY, short of the width (low pressure). The
    text is its own ruler — no hardcoded 80.
  * local_rhyme — do the line endings track a REGULAR couplet/alternating scheme
    (each ending rhymes with the previous or previous-but-one, by the meter
    faculty's SPECTRAL rime distance)? Verse: high. Prose whose wrapped endings
    happen to collide: ~chance, low, and NOT locally regular.
  * indent — do lines carry leading whitespace (nesting)?

WHICH format function fits is the ShapeDecode verdict, position-aligned over the
token vector, NOT a Python `if`. is_prosody / reflow ride the winning signature:
PROSODY keeps its line breaks (content); MEDIUM/REGISTER newlines are SOFT (the
reflow the AGENT does, driven by its own verdict — the world adapter never
unwraps); STRUCTURE keeps indentation (content).

donkey=0 (no LLM). No `import re` — features are a character scan. Graph-native:
the classification is a ShapeDecode collapse over graph-resident signatures; the
Python here PERCEIVES the layout (mechanical I/O) and APPLIES the transform the
graph verdict dictates (like coref_entities' verse pincer applies the perceptual
read) — it never DECIDES the format in Python.
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

from domains import reflective_faculty as rf

_SEED = os.path.join(os.path.dirname(__file__), "..", "seeds", "format_channel.json")

# Quantization boundaries — perceptual thresholds (the format twin of
# metrical_reading's _BEAT_MIN / _RHYME_THRESHOLD). Fixed perceptual grain; the
# DECISION they feed is the ShapeDecode collapse, not these numbers.
_WRAP_FORCED = 0.50        # >= this fraction of breaks width-forced -> a hard wrap
_RHYME_REG = 0.33          # >= this fraction of lines in a local rhyme -> a scheme
_INDENT_YES = 0.50         # >= this fraction of lines indented -> nesting


# --------------------------------------------------------------------------- #
#  RESOLVE + CODEBOOK (mechanical seed I/O, no decision) — metrical idiom.
# --------------------------------------------------------------------------- #
def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    ag_node = None
    for n in sub.nodes("Agent"):
        if not sub.node(n)["attrs"].get("is_class"):
            ag_node = n
            break
    return sub, native, ag_node


def ensure_format_codebook(agent) -> None:
    """Idempotently install the format-function codebook (`ShapeSignatureFormat`
    nodes) and register one `ShapeSignature{kind:'format_sig'}` decode-part per
    function (so the Rust ShapeDecode has candidate parts). Guarded by a
    graph-resident `Seed{id:'format_channel'}` — the same idiom
    `metrical_reading.ensure_meter_codebook` uses. Mechanical seed I/O."""
    sub, _native, ag_node = _resolve(agent)
    seeded = any(sub.node(n)["attrs"].get("id") == "format_channel"
                 for n in sub.nodes("Seed"))
    if not seeded:
        with open(_SEED) as f:
            manifest = json.load(f)
        for nd in manifest.get("nodes", []):
            sub.add_node(nd["type"], dict(nd.get("attrs", {})))
        sub.add_node("Seed", {"id": "format_channel",
                              "version": manifest.get("version", "1.0.0")})
        if ag_node is not None and sub.node(ag_node)["attrs"].get("codebook_epoch") is None:
            sub.set_attr(ag_node, "codebook_epoch", 0.0)
    # Register the decode-parts (idempotent, keyed by name). The part carries the
    # verdict attrs so the winner reads back format / is_prosody / reflow directly.
    have = set()
    for nd in sub.nodes("ShapeSignature"):
        at = sub.node(nd)["attrs"]
        if at.get("kind") == "format_sig":
            have.add(at.get("name"))
    for nd in sub.nodes("ShapeSignatureFormat"):
        at = sub.node(nd)["attrs"]
        nm = at.get("name")
        if not nm or nm in have:
            continue
        sub.add_node("ShapeSignature", {
            "name": nm, "kind": "format_sig", "signature": at.get("signature"),
            "format": at.get("format", nm),
            "is_prosody": float(at.get("is_prosody", 0.0) or 0.0),
            "reflow": float(at.get("reflow", 0.0) or 0.0),
        })


# --------------------------------------------------------------------------- #
#  PERCEIVE — LAYOUT FEATURES. Mechanical character scan (NO regex, NO graph).
# --------------------------------------------------------------------------- #
def _nonblank(text: str) -> list[str]:
    return [ln.rstrip() for ln in str(text).split("\n") if ln.strip()]


def _first_word_len(line: str) -> int:
    toks = line.split()
    return len(toks[0]) if toks else 0


def _wrap_pressure(lines: list[str]) -> float:
    """Fraction of line-breaks that are WIDTH-FORCED: the first word of the next
    line would NOT have fit on the current line without exceeding the text's own
    widest line (its implicit display column). Column-agnostic — the text is its
    own ruler. A hard wrap fills each line to the column (high); verse breaks
    short (low)."""
    if len(lines) < 2:
        return 0.0
    col = max(len(ln) for ln in lines)
    forced = breaks = 0
    for i in range(len(lines) - 1):
        fw = _first_word_len(lines[i + 1])
        if fw == 0:
            continue
        breaks += 1
        if len(lines[i]) + 1 + fw > col:
            forced += 1
    return forced / breaks if breaks else 0.0


def _local_rhyme(lines: list[str]) -> float:
    """Fraction of lines whose ending rhymes (SPECTRAL rime distance, the meter
    faculty) with the previous or previous-but-one line — a regular couplet /
    alternating scheme. Verse scores high; wrapped prose whose endings collide
    by chance is not LOCALLY regular, so it scores low."""
    try:
        from domains import metrical_reading as mr
    except Exception:
        return 0.0

    def ok(a: str, b: str) -> bool:
        try:
            wa, wb = mr._last_word(a), mr._last_word(b)
            if not wa or not wb:
                return False
            d = mr.rime_distance(wa, wb)
            return d is not None and d < mr._RHYME_THRESHOLD
        except Exception:
            return False

    n = len(lines)
    if n < 2:
        return 0.0
    hits = 0
    for i in range(n):
        if (i >= 1 and ok(lines[i], lines[i - 1])) or (i >= 2 and ok(lines[i], lines[i - 2])):
            hits += 1
    return hits / n


def _indent_frac(text: str) -> float:
    """Fraction of non-blank lines that START with leading whitespace (nesting).
    Scans the RAW lines (not rstripped) so leading space survives."""
    raw = [ln for ln in str(text).split("\n") if ln.strip()]
    if not raw:
        return 0.0
    return sum(1 for ln in raw if ln[:1] in (" ", "\t")) / len(raw)


def layout_features(text: str) -> dict[str, Any]:
    """Perceive `text` into its FUNCTIONAL layout features + reporting stats.
    Mechanical — no graph, no regex."""
    lines = _nonblank(text)
    lens = [len(ln) for ln in lines] or [0]
    return {
        "wrap_pressure": round(_wrap_pressure(lines), 3),
        "local_rhyme": round(_local_rhyme(lines), 3),
        "indent": round(_indent_frac(text), 3),
        "n_lines": len(lines),
        "mean_len": round(sum(lens) / len(lens), 1),
        "max_len": max(lens),
    }


def _quantize(feat: dict[str, Any]) -> list[str]:
    """The observed FUNCTIONAL TOKEN VECTOR — position-aligned with every
    ShapeSignatureFormat signature: [wrap, rhyme, indent]."""
    return [
        "wrap_forced" if feat["wrap_pressure"] >= _WRAP_FORCED else "wrap_free",
        "rhyme_reg" if feat["local_rhyme"] >= _RHYME_REG else "rhyme_none",
        "indent_yes" if feat["indent"] >= _INDENT_YES else "indent_no",
    ]


# --------------------------------------------------------------------------- #
#  MEDIUM META-KNOWLEDGE — the held display-geometry prior grounds the read.
# --------------------------------------------------------------------------- #
def _display_media(agent) -> list[dict[str, Any]]:
    """The DisplayMedium prior the agent HOLDS (seeds/format_channel.json): the
    canonical 80x24 terminal + its foveation-bounded width band. Mechanical read."""
    sub, _n, _a = _resolve(agent)
    out = []
    for n in sub.nodes("DisplayMedium"):
        at = sub.node(n)["attrs"]
        out.append({"name": at.get("name"),
                    "columns": float(at.get("columns", 80.0) or 80.0),
                    "columns_min": float(at.get("columns_min", 64.0) or 64.0),
                    "columns_max": float(at.get("columns_max", 100.0) or 100.0)})
    return out


def _grounding(agent, feat: dict[str, Any]) -> dict[str, Any]:
    """WHY a wrap is formatting: does the observed wrap-column (the text's widest
    line) fall in a HELD display medium's foveation-bounded band? A ~72-80 char
    column matching the 80x24 terminal is confident MEDIUM (the file was laid out
    for that display) and LICENSES reconstruction. Returns {matches_medium, medium,
    columns}. This is the meta-knowledge the reader uses to know a 76-char line is
    almost certainly wrapped by formatting — and to say why."""
    col = feat.get("max_len", 0)
    for m in _display_media(agent):
        if m["columns_min"] <= col <= m["columns_max"]:
            return {"matches_medium": True, "medium": m["name"], "columns": col,
                    "why": f"wrap-column {col} sits in {m['name']}'s foveation band "
                           f"[{int(m['columns_min'])},{int(m['columns_max'])}] "
                           f"(canonical {int(m['columns'])}-col terminal) -> formatting"}
    return {"matches_medium": False, "medium": None, "columns": col,
            "why": "no held display medium's width band contains this wrap-column"}


# --------------------------------------------------------------------------- #
#  RECONSTRUCT — INVERT the medium's transform (a faithful decode of content).
#  Understanding the medium (how it wraps + encodes) lets the reader recover the
#  pre-formatted content: rejoin wrapped lines, invert line-end HYPHENATION (a
#  word transposed across a line ending), normalize the medium's smart-punctuation
#  encoding. Mechanical character scan (NO regex) — the DECISION that it is a
#  wrapped medium is the graph verdict + the held-medium match; this only applies
#  the inverse the verdict dictates.
# --------------------------------------------------------------------------- #
_SMART_PUNCT = {"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
                "\u2013": "-", "\u2014": "-", "\u2026": "...", "\u00a0": " "}


def _normalize_encoding(text: str) -> str:
    """Normalize the medium's ENCODING artefacts (smart/curly quotes, en/em dashes,
    ellipsis, nbsp) to their plain-content form. This is the file's TYPESETTING
    shape, not the prose: a curly apostrophe in 'All-gone' is the same word as a
    straight one, and mis-reading it fragments the token."""
    return "".join(_SMART_PUNCT.get(ch, ch) for ch in str(text))


def _dehyphenate_wrap(text: str) -> str:
    """INVERT line-end hyphenation: a word split 'trans-\\nposed' by the wrap is
    rejoined to 'transposed' (the transposition the medium introduced). Only a
    SINGLE trailing hyphen followed by a newline is treated as a wrap break; a
    double '--' (an em-dash rendered ascii) is left intact. Character scan."""
    lines = str(text).split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        cur = lines[i]
        r = cur.rstrip()
        if (i + 1 < len(lines) and r.endswith("-") and not r.endswith("--")
                and len(r) >= 2 and r[-2].isalpha()):
            nxt = lines[i + 1].lstrip()
            # glue the split word: drop the hyphen, take the next line's first token
            j = 0
            while j < len(nxt) and not nxt[j].isspace():
                j += 1
            out.append(r[:-1] + nxt[:j])
            rest = nxt[j:].lstrip()
            lines[i + 1] = rest
            i += 1
            if not rest:
                i += 1
            continue
        out.append(cur)
        i += 1
    return "\n".join(out)


# --------------------------------------------------------------------------- #
#  CROSS-LINE CHANNEL — signal read DOWN the page, invisible to newline-stripping.
# --------------------------------------------------------------------------- #
def _cross_line_reading(text: str) -> dict[str, Any]:
    """Read the ACROSS-LINE / down-the-page channel: the initial letters of the
    lines, read vertically, may spell an embedded word (an acrostic) — signal a
    process that strips newlines is blind to. Returns {initials, acrostic} where
    `acrostic` is a held-lexicon word the initials spell (>= 3 letters), else None.
    Mechanical perception; the word-check is the held phonology/lexicon."""
    lines = _nonblank(text)
    initials = "".join((ln.lstrip()[:1] for ln in lines if ln.lstrip())).lower()
    acrostic = None
    letters = "".join(c for c in initials if c.isalpha())
    if len(letters) >= 3:
        try:
            from nltk.corpus import wordnet as wn
            if wn.synsets(letters):
                acrostic = letters
        except Exception:
            acrostic = None
    return {"initials": initials, "acrostic": acrostic}


# --------------------------------------------------------------------------- #
#  DECODE + WINNER read-off — the collapse decides the format (metrical idiom).
# --------------------------------------------------------------------------- #
def _goal(tokens: list[str]) -> list:
    return [[t] for t in tokens]


def _decode(agent, tokens: list[str]) -> dict:
    sub, _native, _ag = _resolve(agent)
    res = rf.compose_design_for_goal(sub, _goal(tokens))
    if not isinstance(res, dict):
        return {"plan": [], "residual": list(_goal(tokens)), "ordered_parts": []}
    return res


def _winner(res: dict) -> tuple[Optional[str], int]:
    """The format the decode chose = the plan part with the greatest `shape_fit`
    (the signature that position-aligns to the most feature tokens). Read off
    ShapeDecode's own ranking, never re-ranked here."""
    plan = res.get("plan") or []
    best_name, best_fit = None, -1
    for p in plan:
        try:
            fit = int(p.get("shape_fit", 0))
        except (TypeError, ValueError):
            fit = 0
        if fit > best_fit:
            best_fit, best_name = fit, p.get("part")
    return best_name, best_fit


def _part_verdict(sub, part_name: str) -> dict[str, Any]:
    """(format, is_prosody, reflow) for a winning format_sig part — mechanical read."""
    for nd in sub.nodes("ShapeSignature"):
        at = sub.node(nd)["attrs"]
        if at.get("name") == part_name and at.get("kind") == "format_sig":
            return {"format": at.get("format", part_name),
                    "is_prosody": bool(float(at.get("is_prosody", 0.0) or 0.0)),
                    "reflow": bool(float(at.get("reflow", 0.0) or 0.0))}
    return {"format": "register", "is_prosody": False, "reflow": True}


# --------------------------------------------------------------------------- #
#  DECODE FORMAT — the whole loop: perceive -> quantize -> collapse -> record.
# --------------------------------------------------------------------------- #
def decode_format(agent, text: str, *, record: bool = True) -> dict[str, Any]:
    """Decode the FORMAT FUNCTION of `text` by collapse. Returns {format,
    is_prosody, reflow, tokens, fit, features}. WHICH function is the ShapeDecode
    verdict. Optionally RECORDS a `Format` node (the format signal, held in the
    graph parallel to the content) — mechanical adapter I/O."""
    ensure_format_codebook(agent)
    sub, _native, _ag = _resolve(agent)
    feat = layout_features(text)
    tokens = _quantize(feat)
    res = _decode(agent, tokens)
    name, fit = _winner(res)
    verdict = _part_verdict(sub, name) if name else {
        "format": "register", "is_prosody": False, "reflow": True}
    grounding = _grounding(agent, feat)         # WHY (held-medium match)
    cross = _cross_line_reading(text)           # the down-page channel
    out = {"format": verdict["format"], "is_prosody": verdict["is_prosody"],
           "reflow": verdict["reflow"], "tokens": tokens, "fit": fit,
           "features": feat, "winner": name, "grounding": grounding,
           "cross_line": cross}
    if record:
        # Hold the format signal PARALLEL to content — including the 2D shape
        # (line grid) and the down-page channel, so nothing read across lines is
        # lost to a newline-strip.
        sub.add_node("Format", {
            "format": out["format"], "is_prosody": 1.0 if out["is_prosody"] else 0.0,
            "reflow": 1.0 if out["reflow"] else 0.0,
            "wrap_pressure": feat["wrap_pressure"], "local_rhyme": feat["local_rhyme"],
            "indent": feat["indent"], "tokens": json.dumps(tokens),
            "n_lines": float(feat["n_lines"]), "max_len": float(feat["max_len"]),
            "matches_medium": 1.0 if grounding["matches_medium"] else 0.0,
            "medium": grounding.get("medium") or "",
            "why": grounding.get("why", ""),
            "cross_line_initials": cross.get("initials", ""),
            "acrostic": cross.get("acrostic") or "",
            "note": "the file's FORMAT signal (function + medium grounding + 2D shape "
                    "+ down-page channel), decoded parallel to its content",
        })
    return out


def is_prosody(agent, text: str) -> bool:
    """Does `text`'s layout decode as PROSODY (line breaks = content, keep for
    meter)? The graph-native replacement for coref_entities._text_is_verse: verse
    is now ONE format the decoder recognizes, not the default reading of any
    multi-line block."""
    return bool(decode_format(agent, text, record=False)["is_prosody"])


# --------------------------------------------------------------------------- #
#  REFLOW — apply the transform the VERDICT dictates (not a Python decision).
# --------------------------------------------------------------------------- #
def _reflow_soft(text: str) -> str:
    """Reflow SOFT (medium/register) newlines into flowing prose: join runs of
    non-blank lines with a space, keep blank-line paragraph breaks. Mechanical
    string transform — the DECISION to do it is the graph verdict's."""
    paras: list[str] = []
    cur: list[str] = []
    for ln in str(text).split("\n"):
        if ln.strip():
            cur.append(ln.strip())
        else:
            if cur:
                paras.append(" ".join(cur))
                cur = []
    if cur:
        paras.append(" ".join(cur))
    return "\n\n".join(paras)


def reflow(agent, text: str) -> dict[str, Any]:
    """Perceive the format, then hand comprehension a FAITHFULLY RECONSTRUCTED
    content — the inverse of the medium's transform, licensed by the agent's own
    verdict + its held medium knowledge:

      * ENCODING is always normalized (smart punctuation -> plain content — a
        curly apostrophe is not part of the word);
      * for a WRAPPED MEDIUM (the verdict is `medium` AND the wrap-column matches a
        held display medium), line-end HYPHENATION is inverted (a word transposed
        across a line ending is rejoined) and the soft display newlines are
        reflowed into flowing prose;
      * a REGISTER block reflows its soft newlines (no wrap-hyphenation to invert);
      * PROSODY / STRUCTURE keep their line breaks — the newlines are CONTENT.

    A CROSS-LINE signal (an acrostic read down the page) is detected FIRST and, if
    present, the layout is NOT reflowed (the newlines are load-bearing) — the
    down-page channel is never silently stripped. The corpus loader never does any
    of this: the reconstruction is the agent's own read of the format.
    Returns {text, format, is_prosody, reflowed, features, cross_line, grounding}."""
    v = decode_format(agent, text)
    cross = v["cross_line"]
    normalized = _normalize_encoding(text)
    if cross.get("acrostic"):
        # signal runs DOWN the page -> the newlines carry meaning, keep them.
        return {"text": normalized, "format": v["format"], "is_prosody": v["is_prosody"],
                "reflowed": False, "features": v["features"], "tokens": v["tokens"],
                "cross_line": cross, "grounding": v["grounding"],
                "note": "down-page signal held; layout preserved"}
    do = v["reflow"]
    if do and v["format"] == "medium" and v["grounding"].get("matches_medium"):
        normalized = _dehyphenate_wrap(normalized)     # invert the wrap transposition
    text_out = _reflow_soft(normalized) if do else normalized
    return {"text": text_out, "format": v["format"], "is_prosody": v["is_prosody"],
            "reflowed": bool(do), "features": v["features"], "tokens": v["tokens"],
            "cross_line": cross, "grounding": v["grounding"]}


__all__ = ["ensure_format_codebook", "layout_features", "decode_format",
           "is_prosody", "reflow"]
