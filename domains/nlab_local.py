"""LOCAL nLab reference — the RESEARCH-MATH wiki the agent READS the research-tier
DEFINITIONS + CONTEXT from (classifying space, spectral sequences incl.
Adams/Atiyah-Hirzebruch, cobordism, spin). The fourth corpus in the agent's
reading STACK, between Stacks (rigorous research defs+proofs) and Wikipedia (the
broad fallback), above NaturalProofs (foundational defs+proofs) and OEIS
(number-theory values).

The downloaded nLab dump (data/nlab/*.jsonl — ncatlab.org, 19,097 pages) gives,
per entry:
  · `title`   — the math TERM the page defines ('classifying space', 'cobordism',
                'spectral sequence', 'spin group').
  · `url`     — the ncatlab source URL (the WHERE for provenance).
  · `content` — the page in INSTIKI markup: `+-- {...}` toc/context blocks,
                `### headers`, `[[wikilinks]]` / `[[link|surface]]`, `**bold**`,
                `$...$` / `$$...$$` LaTeX math, `## Idea` lead.

What nLab ADDS to the stack (the named research-tier gap the LOWER corpora
LACKED): the RESEARCH-MATH DEFINITIONS — classifying space, spectral sequence
(Adams / Atiyah-Hirzebruch), cobordism, spin group — that NaturalProofs (ProofWiki-
heavy) and Wikipedia (broad) do not state at the research tier. The page's lead
'## Idea' section is the readable definition the agent's grammar comprehends.

The LaTeX MATH is no longer STRIPPED (lossy) — it is RENDERED via the agent's
LaTeX-notation grammar (domains/latex_notation.render — graph data), so the
SYMBOL-CARRIED subject SURVIVES into comprehension (a definition stated with inline
symbols keeps them — vs the old strip that deleted them). LaTeX IS LEARNABLE — the
loader reads it, does not delete it.

HONEST (the named residual): nLab is DENSE categorical research prose in instiki
markup; the math-CORE LaTeX is now READ, but the LONG TAIL (every macro/package)
and multi-line display blocks / diagrams remain the named residual. The agent's
genus-differentia / order-N COMPREHENSION still grounds this dense prose only
PARTIALLY — but the symbol-drop that DEGRADED the subject is fixed.

World-adapter only: jsonl -> {title, url, content}; the lead-extraction strips
the markup minimally to readable prose. The agent's OWN construction grammar
comprehends the prose; this module only supplies the text to read.

  present()           -> True if the corpus is on disk.
  lookup(title)       -> {title, url, content} or None (exact / normalised).
  definition(name)    -> the page's '## Idea' lead, markup-plainified to readable
                         prose (concept -> its research-tier definition, the
                         reference-reader hook), or None.
  search(substr)      -> [title,...] coarse title-contains search.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

_ROOT = Path(__file__).resolve().parent.parent
_DUMP = _ROOT / "data" / "nlab"

# title -> {title, url, content}   (first-seen wins).
_entries: Optional[dict[str, dict]] = None
# normalised-title -> the canonical title (case/space-insensitive lookup).
_norm_index: Optional[dict[str, str]] = None


def _files() -> list[Path]:
    return sorted(_DUMP.glob("**/*.jsonl"))


def _norm(title: str) -> str:
    """Normalise a title for matching: lowercase, underscores->spaces, collapse
    whitespace, strip. nLab titles ARE the math terms, space-separated
    ('classifying space', 'spectral sequence')."""
    t = (title or "").replace("_", " ").strip().lower()
    return re.sub(r"\s+", " ", t)


def _load() -> dict[str, dict]:
    """Load title -> {title, url, content} from the jsonl shard(s) (once)."""
    global _entries, _norm_index
    if _entries is not None:
        return _entries
    out: dict[str, dict] = {}
    norm: dict[str, str] = {}
    for p in _files():
        with p.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                title = d.get("title", "")
                if not title or title in out:
                    continue
                out[title] = {"title": title, "url": d.get("url", ""),
                              "content": d.get("content", "")}
                norm.setdefault(_norm(title), title)
    _entries = out
    _norm_index = norm
    return _entries


def present() -> bool:
    return bool(_files())


def _resolve(title: str) -> Optional[str]:
    """Resolve a (loosely-cased) title to its canonical key, or None."""
    ents = _load()
    if title in ents:
        return title
    if _norm_index is None:
        return None
    return _norm_index.get(_norm(title))


def lookup(title: str) -> Optional[dict[str, Any]]:
    """The full entry for a title (exact, then normalised): {title, url,
    content(the raw instiki markup)}. None on a miss."""
    if not title:
        return None
    key = _resolve(title)
    if key is None:
        return None
    e = _load()[key]
    return {"title": e["title"], "url": e["url"], "content": e["content"]}


def _plainify_instiki(markup: str) -> str:
    """Turn nLab INSTIKI markup into the readable text the construction grammar
    reads — a MINIMAL translation (a world-adapter surface op, NOT a meaning
    decision). The LaTeX MATH is no longer STRIPPED (lossy): it is RENDERED via the
    agent's LaTeX-notation grammar (domains/latex_notation.render — graph data), so
    the SYMBOL-CARRIED subject SURVIVES into comprehension (a definition stated with
    inline symbols keeps them — vs the old strip that deleted them). LaTeX IS
    LEARNABLE — the loader reads it, does not delete it.

    a `[[link|surface]]` -> surface, a bare `[[link]]` -> link, `**bold**`/`_em_`
    -> the bare term, `### headers` -> dropped, `+-- {...}` / `=--` context blocks
    -> dropped, newlines -> spaces."""
    from domains import latex_notation as _lx
    t = markup or ""
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    # NOTE: the LaTeX MATH is PRESERVED (rendered) at the END of this function —
    # after the instiki markup is plainified — so render sees clean `$...$`
    # fragments. The old drop-to-nothing strip is gone (the named LOSS is fixed).
    # [[link|surface]] -> surface ; [[!include ...]] -> dropped ; [[link]] -> link
    t = re.sub(r"\[\[!?include[^\]]*\]\]", " ", t)
    t = re.sub(r"\[\[[^\]|]*\|([^\]]+)\]\]", r"\1", t)
    t = re.sub(r"\[\[([^\]|]+)\]\]", r"\1", t)
    # markdown links [surface](target) -> surface
    t = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", t)
    t = t.replace("**", "").replace("__", "")
    t = re.sub(r"(?<!\w)_([^_\n]+)_(?!\w)", r"\1", t)  # _emphasis_ -> emphasis
    t = re.sub(r"&lbrack;|&rbrack;", " ", t)
    t = re.sub(r"&[a-z]+;", " ", t)                     # stray html entities
    # render the LaTeX MATH AFTER the markup is plainified (so render sees clean
    # `$...$` fragments, not interleaved instiki) — the symbol-carried subject
    # survives. Idempotent on text with no remaining math.
    t = _lx.render(t)
    t = re.sub(r"[ \t]+", " ", t)
    return t.strip()


def _idea_section(content: str) -> Optional[str]:
    """Extract the page's lead — the `## Idea` section (nLab's convention for the
    informal definition), else the first prose section after the toc/context
    blocks. Returns the raw markup of that section (plainified by the caller),
    or None when no prose lead is present."""
    c = (content or "").replace("\r\n", "\n").replace("\r", "\n")
    # prefer the '## Idea' / '# Idea' section.
    m = re.search(r"^#{1,3}\s*Idea\b", c, flags=re.MULTILINE)
    if m:
        start = m.end()
        nxt = re.search(r"^#{1,3}\s+\S", c[start:], flags=re.MULTILINE)
        body = c[start: start + nxt.start()] if nxt else c[start:]
        body = re.sub(r"^\s*\{#[^}]*\}\s*$", " ", body, flags=re.MULTILINE)
        if body.strip():
            return body
    # else the first body paragraph after the +-- context / #Contents blocks.
    # drop the leading '+-- {...} ... =--' context machinery and the toc.
    c2 = re.sub(r"\+--.*?=--", " ", c, flags=re.DOTALL)
    c2 = re.sub(r"^#Contents#.*?\{:toc\}", " ", c2, flags=re.DOTALL)
    c2 = re.sub(r"^#{1,6}.*$", " ", c2, flags=re.MULTILINE)  # drop headers
    c2 = re.sub(r"^\s*\{#[^}]*\}\s*$", " ", c2, flags=re.MULTILINE)
    para = c2.strip()
    return para or None


def _lead_sentence(name: str, prose: str) -> Optional[str]:
    """Take the SENTENCE that defines the term (mentions the term head + has a
    copula) from the plainified Idea prose, so the agent's genus-differentia
    grammar extracts the genus nLab named. Falls back to the first copula
    sentence, then the first sentence. None when no readable prose."""
    if not prose:
        return None
    nm = _norm(name)
    head = nm.split()[-1] if nm else ""
    full = nm  # the full term phrase ('classifying space')
    sentences = [s.strip() for s in re.split(r"(?<=[.])\s+|\n+", prose)
                 if s.strip()]
    if not sentences:
        return None
    # a copula nLab uses for an informal definition: 'is a/an/the', 'refers to',
    # 'is defined as', 'is the notion of', 'denotes'.
    copula = re.compile(r"\bis\s+(?:a|an|the)\b|\brefers?\s+to\b|"
                        r"\bis\s+defined\b|\bdenotes?\b|\bis\s+the\s+notion\b")
    # prefer the FIRST sentence naming the full term AND carrying a copula
    # (the lead definitional sentence — 'A classifying space ... refers to ...').
    for sent in sentences:
        sl = sent.lower()
        if full and full in sl and copula.search(sl):
            return sent
    for sent in sentences:
        sl = sent.lower()
        if head and head in sl and copula.search(sl):
            return sent
    for sent in sentences:
        if copula.search(sent.lower()):
            return sent
    return sentences[0]


def definition(name: str) -> Optional[dict[str, Any]]:
    """The DEFINITION entry for a concept NAME (the reference-reader hook): the
    page's '## Idea' lead, plainified to a readable definitional sentence the
    agent reads. Returns {title, url, text(the lead sentence), lead(the full
    plainified Idea prose)} or None when the corpus holds no page for the name OR
    the lead has no readable prose (the dense-math honest miss). The MEANING is
    the agent's grammar's; this only supplies the text."""
    if not name:
        return None
    entry = lookup(name)
    if entry is None:
        return None
    idea = _idea_section(entry["content"])
    if idea is None:
        return None
    prose = _plainify_instiki(idea)
    if not prose or len(prose) < 20:
        return None
    sent = _lead_sentence(name, prose)
    if not sent:
        return None
    return {"title": entry["title"], "url": entry["url"], "text": sent,
            "lead": prose[:1200]}


def search(substr: str, limit: int = 10) -> list[str]:
    """Coarse title search — titles that CONTAIN `substr` (normalised)."""
    q = _norm(substr)
    if not q:
        return []
    out: list[str] = []
    for key, e in _load().items():
        if q in _norm(key):
            out.append(e["title"])
            if len(out) >= limit:
                break
    return out


__all__ = ["present", "lookup", "definition", "search"]
