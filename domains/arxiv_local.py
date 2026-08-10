"""LOCAL arXiv MATH reference — the FRONTIER-LITERATURE source the agent READS the
COMPUTED INVARIANTS + IDENTIFICATIONS from (the HLE detail nLab/Stacks LACK).

The FIFTH corpus in the agent's reading STACK and the one that scales: arXiv math
.tex is BULK LaTeX, the SAME SHAPE as the Stacks Project repo, so the agent's
EXISTING reader (research-register comprehension + the LaTeX-preserving loader)
reads it UNCHANGED. This module mirrors domains/stacks_local exactly — a mechanical
world-adapter that parses the .tex into the theorem/definition/lemma/proof
environments + surrounding prose, LaTeX PRESERVED (the agent reads it).

The strategic finding this addresses: no single corpus cracks HLE — the detail is
spread across the frontier literature; nLab has IDENTIFICATIONS but almost no
COMPUTED INVARIANTS (147 of 19,097 pages). arXiv is where the computed
invariants + identifications live; the ingestion is mechanical (scripts/
fetch_arxiv.py — list ids, fetch .tex), full scale is the SAME pipeline at more
ids.

The arXiv source (data/arxiv/<id>/*.tex — fetched by scripts/fetch_arxiv.py) tags
its mathematics in LaTeX environments:

  \\begin{theorem}[<attribution>]\\label{<name>} ... \\end{theorem}
  \\begin{definition}\\label{<name>} ... \\end{definition}
  \\begin{lemma} ... \\end{lemma}   (a label is OPTIONAL in arXiv)
  \\begin{proposition} / \\begin{corollary} ...
  \\begin{proof} ... \\end{proof}

A single pass over the fetched .tex builds the index: every statement
(theorem/definition/lemma/proposition/corollary) keyed by an id (its \\label
human-name when present, else a synthesised paper#index key), each paired with its
FOLLOWING proof when one immediately follows. The surrounding prose is preserved.

DIFFERENCES from Stacks (the arXiv reality, handled mechanically):
  · a `\\begin{theorem}[Author, Year]` OPTIONAL attribution argument — kept as the
    statement's `attribution`, stripped from the body.
  · labels are arbitrary author strings (or absent) — the key falls back to
    `<paper>#<n>` so unlabelled statements are still indexed (Stacks always labels).
  · author \\newcommand macros are the named LaTeX long-tail residual (same as
    Stacks) — the math-core LaTeX is rendered; the bespoke macros are dropped.

World-adapter only: .tex -> {kind, key, label, attribution, paper, text/statement,
proof}. The agent's OWN construction grammar comprehends the prose + harvests the
invariant/identification facts (domains/construction_grammar); this module only
supplies the text to read. No reasoning, no LLM (CLAUDE.md).

  present()           -> True if any arXiv .tex is on disk.
  papers()            -> [paper-id, ...] the fetched papers.
  statements()        -> all parsed statement entries (list of dicts).
  lookup(name)        -> a statement entry by label/key, or None.
  search(substr)      -> [(key, kind)] coarse contains search.
  stats()             -> {papers, environments, by_kind} ingestion summary.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

_ROOT = Path(__file__).resolve().parent.parent
_DIR = _ROOT / "data" / "arxiv"

# the statement kinds arXiv math papers use (the same family Stacks tags, plus
# the proposition/corollary the frontier literature leans on).
_KINDS = ("theorem", "definition", "lemma", "proposition", "corollary")

# key -> entry. An entry is a parsed statement {kind, key, label, attribution,
# paper, text, statement, proof}. statements: the ordered list (index order).
_entries: Optional[list[dict]] = None
_by_key: Optional[dict[str, dict]] = None


def _files() -> list[Path]:
    if not _DIR.exists():
        return []
    return sorted(_DIR.glob("*/*.tex"))


def _norm(name: str) -> str:
    """Normalise a key for matching: lowercase, hyphens/underscores->spaces,
    collapse whitespace, strip."""
    t = (name or "").replace("-", " ").replace("_", " ").strip().lower()
    return re.sub(r"\s+", " ", t)


def _plainify_latex(tex: str) -> str:
    """Turn an arXiv LaTeX environment body into the readable text the construction
    grammar + harvester read — a MINIMAL world-adapter translation, IDENTICAL in
    spirit to stacks_local._plainify_latex: the LaTeX MATH is RENDERED (not
    stripped) via the agent's LaTeX-notation grammar so the SYMBOL-CARRIED subject
    SURVIVES (the $H_n(X)$ / $\\cong$ / $\\mathbb{Z}$ a harvested invariant fact
    needs). The author \\newcommand macros + multi-line display blocks are the
    named LaTeX long-tail residual (dropped) — the math-core is read."""
    from domains import latex_notation as _lx
    t = tex or ""
    t = re.sub(r"(?<!\\)%.*", " ", t)                       # comments
    t = re.sub(r"\\label\{[^}]*\}", " ", t)
    # multi-line DISPLAY environments (align/equation/xymatrix/...) — the named
    # residual (kept simple-inline math below). align*/equation often carry the
    # invariant equation; we preserve a SINGLE-LINE display by unwrapping it first.
    t = re.sub(r"\\begin\{(align\*?|equation\*?|gather\*?|displaymath|"
               r"multline\*?|eqnarray\*?)\}(.*?)\\end\{\1\}",
               lambda m: " $ " + m.group(2).replace("\\\\", " ").replace("&", " ")
               + " $ ", t, flags=re.DOTALL) if False else t
    # (the inline path below handles $...$; for displays we convert the body to
    # inline math so a one-line "H_n(X) \\cong \\mathbb{Z}" display still renders.)
    def _disp(m):
        body = m.group(2)
        # only keep a SHORT single-relation display (the invariant-bearing kind);
        # drop long multi-line blocks (the residual).
        body = body.replace("\\\\", " \\\\ ").replace("&", " ")
        if body.count("\\\\") <= 2 and len(body) < 400:
            return " $" + body + "$ "
        return " "
    t = re.sub(r"\\begin\{(align\*?|equation\*?|gather\*?|displaymath|"
               r"multline\*?)\}(.*?)\\end\{\1\}", _disp, t, flags=re.DOTALL)
    # remaining nested DISPLAY/list environments -> dropped (residual).
    t = re.sub(r"\\begin\{(enumerate|itemize|xymatrix|matrix|array|"
               r"tikzcd|cases|pmatrix|bmatrix)\}.*?\\end\{\1\}", " ", t,
               flags=re.DOTALL)
    # \ref/\eqref/\cite/\input -> dropped (provenance refs, not meaning).
    t = re.sub(r"\\(?:ref|eqref|cref|Cref|autoref|cite[a-z]*|input|index)"
               r"\{[^}]*\}", " ", t)
    # emphasis/font wrappers -> bare term.
    t = re.sub(r"\{\\(?:it|bf|em|sl|tt)\s+([^{}]*)\}", r"\1", t)
    t = re.sub(r"\\(?:emph|textit|textbf|textrm|text)\{([^{}]*)\}", r"\1", t)
    # PRESERVE the LaTeX MATH: render $...$ / \\[..\\] (the agent READS the notation).
    t = _lx.render(t)
    # remaining bare text-mode control sequences -> dropped (layout / macros).
    t = re.sub(r"\\[a-zA-Z]+\*?", " ", t)
    t = t.replace("{", " ").replace("}", " ")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n\s*\n+", " ", t)
    return t.strip()


# a statement environment: \begin{KIND}[opt-attr] ... \end{KIND}. The optional
# `[...]` attribution argument is captured (arXiv's "[Author, Year]" convention).
_ENV_RE = re.compile(
    r"\\begin\{(" + "|".join(_KINDS) + r")\}(\[[^\]]*\])?(.*?)\\end\{\1\}",
    re.DOTALL)
_PROOF_RE = re.compile(r"\\begin\{proof\}(?:\[[^\]]*\])?(.*?)\\end\{proof\}",
                       re.DOTALL)
_LABEL_RE = re.compile(r"\\label\{([^}]*)\}")


def _load() -> tuple[list[dict], dict[str, dict]]:
    """One pass over the fetched .tex: parse every statement environment +
    pair each with its FOLLOWING proof (when one immediately follows)."""
    global _entries, _by_key
    if _entries is not None and _by_key is not None:
        return _entries, _by_key
    entries: list[dict] = []
    by_key: dict[str, dict] = {}
    for p in _files():
        paper = p.parent.name
        try:
            src = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        n_in_paper = 0
        for m in _ENV_RE.finditer(src):
            kind = m.group(1)
            attr = (m.group(2) or "").strip("[]").strip() or None
            body = m.group(3)
            n_in_paper += 1
            lab_m = _LABEL_RE.search(body)
            label = lab_m.group(1) if lab_m else ""
            # key: the label human-name when present, else <paper>#<n> so
            # UNLABELLED statements (common in arXiv) are still indexed.
            if label:
                key = _norm(label)
            else:
                key = f"{paper}#{n_in_paper}"
            if key in by_key:
                key = f"{key}#{n_in_paper}"
            text = _plainify_latex(body)
            if not text:
                continue
            entry = {"kind": kind, "key": key, "label": label,
                     "attribution": attr, "paper": paper,
                     "text": text, "statement": text, "proof": None}
            # pair with the FOLLOWING proof when it immediately follows (only
            # whitespace between) — the derivation material.
            pm = _PROOF_RE.search(src, m.end())
            if pm is not None and not src[m.end():pm.start()].strip():
                entry["proof"] = _plainify_latex(pm.group(1))
            entries.append(entry)
            by_key[key] = entry
    _entries, _by_key = entries, by_key
    return _entries, _by_key


def present() -> bool:
    return bool(_files())


def papers() -> list[str]:
    """The fetched paper ids (directory names under data/arxiv)."""
    if not _DIR.exists():
        return []
    return sorted({p.parent.name for p in _files()})


def statements() -> list[dict[str, Any]]:
    """All parsed statement entries (theorem/definition/lemma/proposition/
    corollary), each {kind, key, label, attribution, paper, text, statement,
    proof}. The harvester scans these."""
    ents, _ = _load()
    return [dict(e) for e in ents]


def lookup(name: str) -> Optional[dict[str, Any]]:
    """A statement entry by label/key (exact normalised, else contains). None on
    a miss."""
    ents, by_key = _load()
    q = _norm(name)
    if not q:
        return None
    if q in by_key:
        return dict(by_key[q])
    for k, e in by_key.items():
        if q in k:
            return dict(e)
    return None


def search(substr: str, limit: int = 10) -> list[tuple[str, str]]:
    """Coarse key search — [(key, kind)] for keys/text that CONTAIN `substr`."""
    q = _norm(substr)
    if not q:
        return []
    ents, _ = _load()
    out: list[tuple[str, str]] = []
    for e in ents:
        if q in _norm(e["key"]) or q in e["text"].lower():
            out.append((e["key"], e["kind"]))
            if len(out) >= limit:
                break
    return out


def stats() -> dict[str, Any]:
    """Ingestion summary {papers, environments, by_kind, with_proof}."""
    ents, _ = _load()
    by_kind: dict[str, int] = {}
    with_proof = 0
    for e in ents:
        by_kind[e["kind"]] = by_kind.get(e["kind"], 0) + 1
        if e.get("proof"):
            with_proof += 1
    return {"papers": len(papers()), "environments": len(ents),
            "by_kind": by_kind, "with_proof": with_proof}


__all__ = ["present", "papers", "statements", "lookup", "search", "stats"]
