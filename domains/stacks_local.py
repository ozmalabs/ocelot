"""LOCAL Stacks Project reference — the RIGOROUS research-tier DEFINITIONS +
DERIVATIONS the agent READS the algebraic-geometry definitions and PROOFS from.
The third corpus in the agent's reading STACK (consulted before nLab and
Wikipedia, after NaturalProofs): the rigorous research-tier material — 1,721
definitions + 12,586 lemmas + 13,180 proofs.

The Stacks Project repo (data/stacks/repo/*.tex — 119 LaTeX chapters) tags its
mathematics in LaTeX environments with a `\\label`:

  \\begin{definition}\\label{<chap>-definition-NAME} ... \\end{definition}
  \\begin{lemma}\\label{<chap>-lemma-NAME} ... \\end{lemma}
  \\begin{proof} ... \\end{proof}

A single pass over the 119 .tex builds the index: every definition keyed by the
human part of its label ('torsor' <- 'definition-torsor'), and every lemma paired
with its FOLLOWING proof (the derivation material — the 13k proofs).

What Stacks ADDS to the stack (the named research-tier gap): the RIGOROUS
research DEFINITIONS + the 13,180 PROOFS — the derivation material at the research
tier that NaturalProofs (foundational) and Wikipedia (broad) lack. e.g.
'cohomology' definitions + a lemma stating a torsor/H^1 bijection WITH its proof.

The LaTeX MATH is no longer STRIPPED (lossy) — it is RENDERED via the agent's
LaTeX-notation grammar (domains/latex_notation.render — graph data), so the
SYMBOL-CARRIED subject SURVIVES into comprehension. e.g. '$M$ is finite if $M$ is
finite as an $R$-module' -> 'M is finite if M is finite as an R-module' (the
$M$/$R$ survive — vs the old strip 'finite if is finite as an -module', the
subject dropped). LaTeX IS LEARNABLE — the loader reads it, does not delete it.

HONEST (the named residual): the math-CORE LaTeX (super/subscript, the named
operators, blackboard/Greek, set-builder) is now READ; the LONG TAIL — every
macro/package/\\newcommand, and multi-line DISPLAY blocks / commutative diagrams
(enumerate/align/xymatrix) — remains the named residual (dropped). The un-held
operations (kernel/image) are the acquirable residual already named. The agent's
genus-differentia / order-N COMPREHENSION still grounds dense research prose only
PARTIALLY — but the symbol-drop that DEGRADED the subject is fixed.

World-adapter only: .tex -> {name, label, chapter, text(definition prose)} +
{name, label, chapter, statement(lemma), proof}. The agent's OWN construction
grammar comprehends the prose; this module only supplies the text to read.

  present()           -> True if the repo is on disk.
  lookup(name)        -> the DEFINITION entry {name, label, chapter, text} or None.
  definition(concept) -> the definition prose for a concept (reader hook), or None.
  proof_for(name)     -> a {name, label, chapter, statement, proof} lemma+proof or
                         None (the derivation material).
  search(substr)      -> [(name, kind)] coarse name-contains search (kind=
                         'definition'|'lemma').
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

_ROOT = Path(__file__).resolve().parent.parent
_REPO = _ROOT / "data" / "stacks" / "repo"

# name -> {name, label, chapter, text}   (DEFINITION entries; first-seen wins).
_defs: Optional[dict[str, dict]] = None
# name -> {name, label, chapter, statement, proof}  (LEMMA+PROOF pairs).
_lemmas: Optional[dict[str, dict]] = None


def _files() -> list[Path]:
    return sorted(_REPO.glob("*.tex"))


def _norm(name: str) -> str:
    """Normalise a name for matching: lowercase, hyphens/underscores->spaces,
    collapse whitespace, strip. Stacks labels are hyphenated ('definition-
    torsor' -> name 'torsor', 'lemma-torsors-h1' -> 'torsors h1')."""
    t = (name or "").replace("-", " ").replace("_", " ").strip().lower()
    return re.sub(r"\s+", " ", t)


def _label_name(label: str, kind: str) -> str:
    """The human NAME from a `\\label{<chap>-<kind>-NAME}` — strip the chapter
    prefix (everything up to and including the kind token) leaving the NAME
    ('phantom-cohomology-definition-torsor' -> 'torsor'). Falls back to the raw
    label tail when the kind token is absent."""
    lab = (label or "").strip()
    marker = f"-{kind}-"
    i = lab.find(marker)
    if i >= 0:
        return lab[i + len(marker):]
    # kind at the very start ('definition-torsor').
    pre = f"{kind}-"
    if lab.startswith(pre):
        return lab[len(pre):]
    return lab


def _plainify_latex(tex: str) -> str:
    """Turn a Stacks LaTeX environment body into the readable text the construction
    grammar reads — a MINIMAL translation (a world-adapter surface op, NOT a meaning
    decision). The LaTeX MATH is no longer STRIPPED (lossy): it is RENDERED via the
    agent's LaTeX-notation grammar (domains/latex_notation.render — graph data), so
    the SYMBOL-CARRIED subject SURVIVES into comprehension. e.g. '$M$ is finite if
    $M$ is finite as an $R$-module' -> 'M is finite if M is finite as an R-module'
    (the $M$/$R$ survive — vs the old strip 'finite if is finite as an -module',
    the subject dropped). The LaTeX IS LEARNABLE — don't strip it, READ it.

    `{\\it term}`/`{\\bf t}`/`\\emph{t}`/`\\textit{t}` -> the bare term;
    `\\label{...}`/`\\ref{...}`/`\\cite{...}` -> dropped; comments -> dropped;
    `enumerate`/`xymatrix`/`align` DISPLAY environments -> dropped (the named
    residual — multi-line formula blocks / diagrams; the inline + simple display
    math is now PRESERVED via render)."""
    from domains import latex_notation as _lx
    t = tex or ""
    t = re.sub(r"(?<!\\)%.*", " ", t)                       # comments
    t = re.sub(r"\\label\{[^}]*\}", " ", t)
    # nested DISPLAY environments (enumerate/align/xymatrix/...) remain dropped —
    # multi-line formula blocks / commutative diagrams are the named LaTeX residual
    # (the long tail). The INLINE + simple display math is PRESERVED below.
    t = re.sub(r"\\begin\{(enumerate|itemize|align\*?|"
               r"xymatrix|matrix|array|gather\*?)\}.*?\\end\{\1\}", " ", t,
               flags=re.DOTALL)
    # \ref/\eqref/\cite{...} -> dropped ; \input{...} -> dropped (provenance refs,
    # not meaning) BEFORE the math render so they do not leak into rendered prose.
    t = re.sub(r"\\(?:ref|eqref|cite|input|index)\{[^}]*\}", " ", t)
    # emphasis/font wrappers -> bare term (text-mode; the math-mode \mathit etc.
    # are handled inside render).
    t = re.sub(r"\{\\(?:it|bf|em|sl|tt)\s+([^{}]*)\}", r"\1", t)
    t = re.sub(r"\\(?:emph|textit|textbf|text)\{([^{}]*)\}", r"\1", t)
    # PRESERVE the LaTeX MATH: render $...$ / $$...$$ / \[..\] (the agent READS the
    # notation rather than dropping it — the symbol-carried subject survives).
    t = _lx.render(t)
    # remaining bare text-mode control sequences (\medskip, \noindent, ...) ->
    # dropped (render handled the math; these are layout).
    t = re.sub(r"\\[a-zA-Z]+\*?", " ", t)
    t = t.replace("{", " ").replace("}", " ")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n\s*\n+", " ", t)
    return t.strip()


_ENV_RE = re.compile(
    r"\\begin\{(definition|lemma|proposition|theorem)\}(.*?)\\end\{\1\}",
    re.DOTALL)
_PROOF_RE = re.compile(r"\\begin\{proof\}(.*?)\\end\{proof\}", re.DOTALL)
_LABEL_RE = re.compile(r"\\label\{([^}]*)\}")


def _load() -> tuple[dict[str, dict], dict[str, dict]]:
    """One pass over the 119 .tex: build the DEFINITION index (name -> prose) and
    the LEMMA+PROOF index (name -> statement + following proof)."""
    global _defs, _lemmas
    if _defs is not None and _lemmas is not None:
        return _defs, _lemmas
    defs: dict[str, dict] = {}
    lemmas: dict[str, dict] = {}
    for p in _files():
        chapter = p.stem
        try:
            src = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for m in _ENV_RE.finditer(src):
            kind = m.group(1)
            body = m.group(2)
            lab_m = _LABEL_RE.search(body)
            label = lab_m.group(1) if lab_m else ""
            if kind == "definition":
                name = _label_name(label, "definition") if label else ""
                if not name:
                    continue
                key = _norm(name)
                if key in defs:
                    continue
                text = _plainify_latex(body)
                if text:
                    defs[key] = {"name": name, "label": label,
                                 "chapter": chapter, "text": text}
            else:
                # lemma/proposition/theorem: pair with the FOLLOWING proof env.
                name = _label_name(label, kind) if label else ""
                if not name:
                    continue
                key = _norm(name)
                if key in lemmas:
                    continue
                # find the next \begin{proof} after this environment's end.
                pm = _PROOF_RE.search(src, m.end())
                if pm is None:
                    continue
                # the proof must immediately follow (allow only whitespace/blank
                # lines between) — else it belongs to a later statement.
                between = src[m.end():pm.start()].strip()
                if between:
                    continue
                statement = _plainify_latex(body)
                proof = _plainify_latex(pm.group(1))
                if statement and proof:
                    lemmas[key] = {"name": name, "label": label,
                                   "chapter": chapter, "statement": statement,
                                   "proof": proof}
    _defs, _lemmas = defs, lemmas
    return _defs, _lemmas


def present() -> bool:
    return bool(_files())


def _resolve_def(name: str) -> Optional[str]:
    """Resolve a concept name to a DEFINITION key (exact normalised, then a
    name whose words END with the query — 'cohomology' -> 'group-cohomology' /
    a '...-cohomology' label — and finally any name CONTAINING the query)."""
    defs, _ = _load()
    q = _norm(name)
    if not q:
        return None
    if q in defs:
        return q
    # prefer a name whose LAST word(s) match the query (the head sense), shortest.
    cands = [k for k in defs if k == q or k.endswith(" " + q) or k.startswith(q + " ")]
    if not cands:
        cands = [k for k in defs if q in k]
    if not cands:
        return None
    cands.sort(key=len)
    return cands[0]


def lookup(name: str) -> Optional[dict[str, Any]]:
    """The DEFINITION entry for a name (exact / head / contains): {name, label,
    chapter, text(the definition prose)}. None on a miss."""
    key = _resolve_def(name)
    if key is None:
        return None
    e = _load()[0][key]
    return dict(e)


def definition(concept: str) -> Optional[dict[str, Any]]:
    """The DEFINITION prose for a concept NAME (the reference-reader hook) —
    {name, label, chapter, text, lead(the first defining sentence)} or None when
    the corpus holds no definition (honest miss). The lead is the sentence that
    defines the term (the term + a copula), for the genus-differentia grammar."""
    e = lookup(concept)
    if e is None:
        return None
    prose = e["text"]
    nm = _norm(concept)
    head = nm.split()[-1] if nm else ""
    sentences = [s.strip() for s in re.split(r"(?<=[.])\s+", prose) if s.strip()]
    lead = None
    for sent in sentences:
        sl = sent.lower()
        if head and head in sl and re.search(r"\bis\s+(?:a|an|the)\b", sl):
            lead = sent
            break
    if lead is None:
        for sent in sentences:
            if re.search(r"\bis\s+(?:a|an|the)\b", sent.lower()):
                lead = sent
                break
    if lead is None and sentences:
        lead = sentences[0]
    return {"name": e["name"], "label": e["label"], "chapter": e["chapter"],
            "text": prose, "lead": lead}


def proof_for(name: str) -> Optional[dict[str, Any]]:
    """A LEMMA+PROOF pair for `name` (the derivation material): {name, label,
    chapter, statement, proof} — exact normalised key, else the first lemma whose
    name CONTAINS the query. None on a miss."""
    _, lemmas = _load()
    q = _norm(name)
    if not q:
        return None
    if q in lemmas:
        return dict(lemmas[q])
    for key, e in lemmas.items():
        if q in key:
            return dict(e)
    return None


def search(substr: str, limit: int = 10) -> list[tuple[str, str]]:
    """Coarse name search across DEFINITIONS + LEMMAS — [(name, kind)] for names
    that CONTAIN `substr` (normalised); kind is 'definition' | 'lemma'."""
    q = _norm(substr)
    if not q:
        return []
    defs, lemmas = _load()
    out: list[tuple[str, str]] = []
    for key, e in defs.items():
        if q in key:
            out.append((e["name"], "definition"))
            if len(out) >= limit:
                return out
    for key, e in lemmas.items():
        if q in key:
            out.append((e["name"], "lemma"))
            if len(out) >= limit:
                return out
    return out


__all__ = ["present", "lookup", "definition", "proof_for", "search"]
