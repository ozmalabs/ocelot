"""LOCAL NaturalProofs reference — a real maths source the agent READS the
FOUNDATIONAL DEFINITIONS and the genuinely-new PROOFS from. The third corpus in
the agent's reading STACK, alongside wiki_local (broad + research-tier prose) and
oeis_local (number-theory sequences + ground-truth values).

The downloaded NaturalProofs corpus (data/naturalproofs/{train,valid,test}/
*.jsonl — ProofWiki + Stacks + textbooks, 14,698 entries) gives, per entry:
  · `title`   — the theorem / definition name ('Definition:Kernel of Group
                Homomorphism', 'Kernel of Group Homomorphism is Subgroup').
  · `text`    — the STATEMENT / DEFINITION in prose (the thing being asserted).
  · `target`  — the PROOF (the derivation material — empty for a bare definition).
  · `ctxs`    — the referenced statements/definitions ([{title, text}, ...]).

What NaturalProofs ADDS to the stack (the two things the agent needs to keep
climbing):
  · the LOWER-TOWER OPERATIONS *with proofs* — kernel, image, quotient, rank,
    boundary (the operations the agent HAS), now sourced WITH the derivation.
  · the genuinely-new PROOFS (the `target` field) — not just definitions.

HONEST (the named gap): NaturalProofs is ProofWiki-heavy and does NOT cover the
research-topology tier — homology / cohomology / spectral sequence / classifying
space / cobordism / spin are 0 (or incidental) here. Those DEFINITIONS are in
Wikipedia (wiki_local); the research-tier PROOFS / derivations are the named
residual -> nLab / Stacks / arXiv, NOT connected.

World-adapter only: jsonl -> {title, text(statement/definition), proof(`target`),
refs(`ctxs` titles)}. Crucially the corpus's DEFINITIONS live both as the rare
top-level 'Definition:' entry AND (richly — 4,775 of them) inside the `ctxs` of
the theorems that cite them; this loader indexes BOTH so a definition lookup
resolves. The agent's OWN construction grammar comprehends the prose; this module
only supplies the text to read.

  present()           -> True if the corpus is on disk.
  lookup(title)       -> {title, text, proof, refs} or None (exact / normalised).
  definition(name)    -> the 'Definition:<name>' entry's text+refs (concept ->
                         its definition, the reference-reader hook), or None.
  search(substr)      -> [(title, has_proof)] coarse title-contains search.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

_ROOT = Path(__file__).resolve().parent.parent
_DUMP = _ROOT / "data" / "naturalproofs"

# title -> {title, text, proof, refs:[title,...]}   (the canonical, first-seen)
_entries: Optional[dict[str, dict]] = None
# normalised-title -> the canonical title (for case/space-insensitive lookup).
_norm_index: Optional[dict[str, str]] = None


def _files() -> list[Path]:
    return sorted(_DUMP.glob("**/*.jsonl"))


def _norm(title: str) -> str:
    """Normalise a title for matching: lowercase, underscores->spaces, collapse
    whitespace, strip. ProofWiki titles are space-separated, e.g.
    'Definition:Kernel of Group Homomorphism'."""
    t = (title or "").replace("_", " ").strip().lower()
    return re.sub(r"\s+", " ", t)


def _add(out: dict[str, dict], norm: dict[str, str], title: str, text: str,
         proof: str, refs: list[str]) -> None:
    """Index one (title, text, proof, refs). First occurrence wins (a definition
    cited in many ctxs is identical); a later occurrence carrying a PROOF upgrades
    a previously proof-less entry (the top-level theorem over a bare ctx mention)."""
    if not title:
        return
    cur = out.get(title)
    if cur is None:
        out[title] = {"title": title, "text": text or "", "proof": proof or "",
                      "refs": refs or []}
        norm.setdefault(_norm(title), title)
        return
    # upgrade: fill a missing proof / a missing text from a richer later sighting.
    if proof and not cur["proof"]:
        cur["proof"] = proof
    if text and not cur["text"]:
        cur["text"] = text
    if refs and not cur["refs"]:
        cur["refs"] = refs


def _load() -> dict[str, dict]:
    """Load title -> {title, text, proof, refs} from the jsonl shards (once).
    Indexes BOTH the top-level theorem/definition entries (which carry the PROOF
    in `target`) AND every `ctxs` referenced statement/definition (which carry the
    foundational DEFINITIONS' text)."""
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
                refs = [c.get("title", "") for c in (d.get("ctxs") or [])
                        if c.get("title")]
                _add(out, norm, d.get("title", ""), d.get("text", ""),
                     d.get("target", ""), refs)
                # the cited statements/definitions — the foundational DEFINITION
                # text lives here (a definition is rarely a top-level entry).
                for c in (d.get("ctxs") or []):
                    _add(out, norm, c.get("title", ""), c.get("text", ""),
                         "", [])
    _entries = out
    _norm_index = norm
    return _entries


def present() -> bool:
    return bool(_files())


def _resolve(title: str) -> Optional[str]:
    """Resolve a (possibly loosely-cased) title to its canonical key, or None."""
    ents = _load()
    if title in ents:
        return title
    if _norm_index is None:
        return None
    return _norm_index.get(_norm(title))


def lookup(title: str) -> Optional[dict[str, Any]]:
    """The full entry for a title (exact, then normalised): {title, text(the
    statement/definition), proof(the `target` derivation — '' for a bare
    definition), refs(the cited titles)}. None on a miss."""
    if not title:
        return None
    key = _resolve(title)
    if key is None:
        return None
    e = _load()[key]
    return {"title": e["title"], "text": e["text"], "proof": e["proof"],
            "refs": list(e["refs"])}


# Differentia qualifiers we strip when a concept name has no bare definition of
# its own ('Definition:Kernel' is absent, but 'Definition:Kernel of Linear
# Transformation' exists). A surface->title retry on data availability, NOT a
# meaning decision (the agent's grammar decides meaning; this only finds the page).
def _definition_candidates(name: str) -> list[str]:
    n = (name or "").replace("_", " ").strip()
    if not n:
        return []
    # the title-case form ProofWiki uses ('kernel' -> 'Kernel').
    tc = " ".join(w[:1].upper() + w[1:] if w else w for w in n.split())
    return [f"Definition:{tc}", f"Definition:{n}"]


def _is_substantive(text: str) -> bool:
    """A ProofWiki page is SUBSTANTIVE prose (a real definition) rather than a
    transclusion / redirect stub. A stub is mostly '{{:Definition:...}}'
    transclusions and '=== ... ===' section headers with no copula sentence — it
    points at sub-pages instead of stating the definition. A surface shape test
    (no meaning decision): substantive iff there is prose left after stripping the
    transclusions and headers."""
    t = (text or "")
    t = re.sub(r"\{\{[^}]*\}\}", " ", t)        # drop {{:...}} transclusions
    t = re.sub(r"={2,}[^=]*={2,}", " ", t)       # drop === headers ===
    t = re.sub(r"\s+", " ", t).strip()
    return len(t) >= 40


def definition(name: str) -> Optional[dict[str, Any]]:
    """The DEFINITION entry for a concept NAME (the reference-reader hook): the
    text of 'Definition:<Name>' (the foundational definition the agent reads),
    plus its cited refs. Resolves exact 'Definition:<Name>' first, then — when no
    bare page exists — the FIRST 'Definition:<Name> ...' qualified entry (e.g.
    'kernel' -> 'Definition:Kernel of Group Homomorphism'). None when the corpus
    holds no definition for the name (honest miss).

    Returns {title, text, proof, refs} (proof is normally '' for a definition;
    some ProofWiki definition pages carry an equivalence proof in `target`)."""
    if not name:
        return None
    # exact bare 'Definition:<Name>' (title-case + raw).
    for cand in _definition_candidates(name):
        hit = lookup(cand)
        if hit and hit["text"]:
            return hit
    # qualified fallback: a 'Definition:<Name> ...' / '<Name>/...' entry (the bare
    # page is a transclusion stub with no prose of its own). Rank the candidates:
    # prefer SUBSTANTIVE prose (a ProofWiki transclusion page is just '{{:...}}' /
    # '=== ... ===' with no real definition) and then the SHORTEST title (the most
    # general sense). A data-availability retry, not a meaning decision.
    ents = _load()
    nl = _norm(name)
    prefix_a = f"definition:{nl} "
    prefix_b = f"definition:{nl}/"
    best: Optional[dict] = None
    best_key: Optional[tuple] = None
    for key, e in ents.items():
        k = _norm(key)
        if not ((k.startswith(prefix_a) or k.startswith(prefix_b)) and e["text"]):
            continue
        # a transclusion/redirect stub (no genuine prose) is the worst candidate.
        substantive = _is_substantive(e["text"])
        rank_key = (0 if substantive else 1, len(e["title"]))
        if best_key is None or rank_key < best_key:
            best_key = rank_key
            best = e
    if best is not None:
        return {"title": best["title"], "text": best["text"],
                "proof": best["proof"], "refs": list(best["refs"])}
    return None


def proof_for(title: str) -> Optional[dict[str, Any]]:
    """The first THEOREM whose title contains `title` AND carries a proof — the
    derivation material. {title, text, proof, refs} or None. (A convenience over
    `search` for showing 'a proof read from the corpus'.)"""
    nl = _norm(title)
    for key, e in _load().items():
        if nl in _norm(key) and e["proof"]:
            return {"title": e["title"], "text": e["text"],
                    "proof": e["proof"], "refs": list(e["refs"])}
    return None


def search(substr: str, limit: int = 10) -> list[tuple[str, bool]]:
    """Coarse title search — entries whose title CONTAINS `substr` (normalised).
    Returns [(title, has_proof)] (best-effort first-seen order)."""
    q = _norm(substr)
    if not q:
        return []
    out: list[tuple[str, bool]] = []
    for key, e in _load().items():
        if q in _norm(key):
            out.append((e["title"], bool(e["proof"])))
            if len(out) >= limit:
                break
    return out


__all__ = ["present", "lookup", "definition", "proof_for", "search"]
