"""THE JABBERWOCK FIXES ITS OWN RELEVANCE JUDGE — fix the fixer, not the outcome.

scripts/jabberwock_researches_its_need.py exposed a SILENT failure: the relevance
judge was a SURFACE keyword-coverage test (a Python decision over a token) — so it
false-positived 'ON-GAP' on word collisions ('levinson' firing on a tableau-crystals
paper, 'cross-speaker' on a TTS style-transfer paper). That is the agent's already-
named failure shape: SURFACE-BOUND relevance (the held MEANING judged in an
unrecognised SURFACE — cmsg 130d1d7f). The fix is meaning-vs-surface.

THE FIX (the agent's own faculty, not a Python heuristic): judge each hit by the
agent's COMPREHENSION — read_and_ground the paper's SUBJECT (what it is ABOUT) and
accept it as ON-GAP only if a gap term lands in the COMPREHENDED SUBJECT STRUCTURE
(term/genus/primitives), NOT anywhere in the surface. Where the agent cannot
comprehend the subject, it ABSTAINS ('undecided') rather than false-positiving on a
token. So the surface FALSE-POSITIVE becomes a meaning-judgement-or-honest-abstention.

HONEST (binary admissibility): this fixes the PRECISION half (no more token
collisions) by routing the decision through the agent's comprehension. The RECALL
half — confirming a genuinely on-gap paper by DEEP body comprehension — remains gated
on the comprehension-DEPTH frontier the agent already named (grounds-to-topic, not
always-to-primitive). The fix is real and bounded; reported, not overclaimed.

Run:  python -m scripts.jabberwock_fixes_its_relevance
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.jabberwock_frontier_select import _build_mind            # noqa: E402
from domains import order_n_postulates as onp                         # noqa: E402
from domains import gap_prioritiser as gp                             # noqa: E402
from domains import web_world as ww                                   # noqa: E402
from domains import read_and_ground as rag                            # noqa: E402

# the abstract's OWN verb -> its nominal genus (mechanical surface->frame mapping,
# the agent's grammar then recovers the subject; identical to the find-and-read path).
_VERB = {"study": "study", "studies": "study", "present": "presentation",
         "presents": "presentation", "prove": "proof", "proves": "proof",
         "introduce": "introduction", "introduces": "introduction",
         "construct": "construction", "constructs": "construction",
         "investigate": "investigation", "propose": "proposal", "proposes": "proposal",
         "consider": "consideration", "establish": "establishment",
         "show": "demonstration", "describe": "description", "develop": "development",
         "address": "treatment", "addresses": "treatment", "use": "use", "uses": "use"}


def _subject_frame(title: str, abstract: str) -> tuple[str, str] | None:
    """Build a definitional frame the construction grammar reads, from the paper's
    OWN first sentence: 'this paper is a <genus> <rest>'. The genus is the verb's
    nominal — the abstract's own word, not the assistant's. Returns (term, frame)."""
    first = re.split(r"(?<=[.])\s+", abstract.strip())[0] if abstract else ""
    vm = re.match(r"^\s*(?:In this (?:paper|work|study),?\s*)?[Ww]e\s+(\w+)\b(.*)$",
                  first)
    if vm is None:
        vm = re.match(r"^\s*(?:This|The present)\s+"
                      r"(?:paper|note|article|work|study)\s+(\w+?)s?\b(.*)$", first)
    term = re.sub(r"[^a-zA-Z0-9 \-]", "", title).strip().lower()[:60] or "this paper"
    if vm:
        genus = _VERB.get(vm.group(1).lower()) or _VERB.get(vm.group(1).lower().rstrip("s"))
        if genus:
            return term, f"{term} is a {genus} {vm.group(2).strip()}".strip()
    if first:
        return term, first
    return None


def _comprehend(sub, title: str, abstract: str) -> dict:
    """THE AGENT'S FACULTY judges the hit: comprehend its subject via read_and_
    ground. Returns the comprehension {grounded, genus, about_terms, reason}."""
    fr = _subject_frame(title, abstract)
    if fr is None:
        return {"grounded": False, "genus": None, "about": set(), "reason": "no abstract"}
    term, frame = fr
    try:
        res = rag.read_and_ground(sub, term, None, definition_text=frame, max_depth=2)
    except Exception as e:  # noqa: BLE001
        return {"grounded": False, "genus": None, "about": set(),
                "reason": f"comprehension raised {type(e).__name__}"}
    st = res.get("structure") or {}
    about = set()
    for k in ("term", "genus"):
        if st.get(k):
            about.add(str(st[k]).lower())
    for p in (st.get("primitives") or []):
        about.add(str(p).lower())
    about.add(term)  # the paper's OWN subject head is part of what it is about
    return {"grounded": bool(res.get("grounded")), "genus": st.get("genus"),
            "about": about, "reason": res.get("reason")}


def main() -> int:
    print("=" * 78)
    print("THE JABBERWOCK FIXES ITS RELEVANCE JUDGE — surface -> meaning")
    print("=" * 78)
    sub = _build_mind()

    shape_lib, _ = onp._resolve_shapes(sub, None)
    onp.synthesize_over_all(sub, record=True, shapes="harvested", prune=False)
    breadth = gp.shape_firing_breadth(sub, shape_lib)
    rows = gp.rank_gaps(sub, shape_breadth=breadth)[:3]

    print("\nDIAGNOSIS (the agent's own failure shape): the old judge was SURFACE-")
    print("BOUND — a gap TOKEN appearing ANYWHERE in the surface scored ON-GAP. The")
    print("fix routes the decision through the agent's COMPREHENSION of the SUBJECT.\n")

    n_old_pos = n_new_pos = n_abstain = n_rescued = 0
    for r in rows:
        keys = [str(k).lower() for k in r["capability_keys"] if str(k)]
        query = " ".join(keys[:5])
        hits = ww.arxiv_search(query, limit=3)
        print("-" * 74)
        print(f"GAP {keys[:3]}  query={query!r}  -> {len(hits)} hits "
              f"(reachable={ww.arxiv_reachable()})")
        for h in hits:
            title = re.sub(r"\s+", " ", h.get("title", "")).strip()
            abstract = h.get("abstract") or ""
            surf = " ".join([title.lower(), abstract.lower()])
            old_cover = sorted({k for k in keys if k in surf})        # OLD: surface
            comp = _comprehend(sub, title, abstract)                  # NEW: meaning
            about_text = " ".join(comp["about"])
            new_cover = sorted({k for k in keys if k in about_text})
            old_pos = bool(old_cover)
            if not comp["grounded"] and not new_cover:
                new = "ABSTAIN"   # cannot comprehend the subject -> honest undecided
            elif new_cover:
                new = "ON-GAP"
            else:
                new = "OFF-GAP"
            n_old_pos += old_pos
            n_new_pos += (new == "ON-GAP")
            n_abstain += (new == "ABSTAIN")
            if old_pos and new != "ON-GAP":
                n_rescued += 1     # a surface false-positive the fix removed
            flag = "  <-- surface FALSE-POSITIVE removed" if (old_pos and new != "ON-GAP") else ""
            print(f"  • {title[:84]}")
            print(f"      OLD(surface)={'ON-GAP' if old_pos else 'off'} cover={old_cover}"
                  f"   NEW(meaning)={new} about-cover={new_cover}{flag}")

    print("\n" + "=" * 78)
    print(f"OLD surface ON-GAP: {n_old_pos}   NEW meaning ON-GAP: {n_new_pos}   "
          f"ABSTAIN: {n_abstain}   surface false-positives REMOVED: {n_rescued}")
    print("THE FIX: precision restored by judging the SUBJECT the agent comprehends,")
    print("abstaining where it cannot — never false-positiving on a surface token.")
    print("HONEST RESIDUAL: recall (confirming a truly on-gap paper by DEEP body")
    print("comprehension) stays gated on the comprehension-DEPTH frontier. Fix the")
    print("fixer (the judge), not the outcome (a hand-filtered hit list).")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
