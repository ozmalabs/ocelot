"""THE JABBERWOCK RESEARCHES WHAT IT NEEDS — it names its OWN gap, emits its OWN
arXiv query from that gap, fetches over its web effector, and judges the hits with
its OWN selector. Per user: "simply ask the agent."

NO assistant-chosen topics. The agent ranks its held gaps (order_n_postulates ->
gap_prioritiser, its graph-resident compression Term); the QUERY is the winning
gap's own ``capability_keys`` (the agent's terms of art, verbatim); RELEVANCE is the
agent's own name-key COVERAGE selector over each abstract (the same selector
gap_prioritiser uses over the codebase). This shell does I/O (arxiv_search) and
prints; every DECISION — which gap, which query, which hit lands — is the agent's.

Donkey-clean: papers are read as STRUCTURE to construct from, never "train a model";
GET-only via the web-world's arxiv_search (best-effort, never blocks); no verbatim
abstract is emitted, only the agent's coverage verdict + the un-held terms it would
acquire-by-reading. HONEST residual (per cmsg c82551fa/764a5141): deep body-to-claims
comprehension grounds to TOPIC, not always to PRIMITIVE — reported, not hidden.

Run:  python -m scripts.jabberwock_researches_its_need
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


def _held_concept_names(sub) -> set[str]:
    """The agent's held vocabulary — Concept node names, lower-cased. Used so the
    agent can flag which terms in a hit are un-held (acquire-by-reading targets)."""
    names: set[str] = set()
    try:
        for nid in sub.nodes_of_type("Concept"):
            nm = sub.node(nid)["attrs"].get("name")
            if nm:
                names.add(str(nm).lower())
    except Exception:  # noqa: BLE001
        pass
    return names


_WORD = re.compile(r"[a-zA-Z][a-zA-Z\-]{3,}")
_STOP = {"this", "that", "with", "from", "which", "these", "those", "their",
         "paper", "study", "model", "models", "using", "based", "show", "results",
         "method", "approach", "propose", "present", "between", "while", "also",
         "such", "have", "than", "into", "over", "more", "most", "both", "where"}


def main() -> int:
    print("=" * 78)
    print("THE JABBERWOCK RESEARCHES WHAT IT NEEDS — its gap, its query, its read")
    print("=" * 78)

    sub = _build_mind()
    held = _held_concept_names(sub)

    # (1) THE AGENT NAMES ITS GAP — synthesize over every held postulate, then rank
    # by the graph-resident compression Term (payoff = held postulates unified).
    shape_lib, mode = onp._resolve_shapes(sub, None)
    onp.synthesize_over_all(sub, record=True, shapes="harvested", prune=False)
    breadth = gp.shape_firing_breadth(sub, shape_lib)
    rows = gp.rank_gaps(sub, shape_breadth=breadth)
    print(f"\n[1] AGENT'S GAP RANKING (shape-lib mode='{mode}', {len(rows)} axes; "
          f"payoff = held postulates UNIFIED):")
    for r in rows[:8]:
        print(f"      payoff={r['payoff']:>3} order={r['min_order']} "
              f"score={r['score']:>9}  {r['capability_keys'][:4]}")
    if not rows:
        print("    (the agent named no gap — nothing to research)")
        return 0

    # (2) THE AGENT'S QUERY — the winning gap's OWN capability_keys, verbatim.
    # Research the top THREE distinct gaps so the self-direction is visible.
    print("\n[2] THE AGENT TAKES ITS TOP GAPS TO arXiv (query = the gap's own "
          "capability_keys — the agent's terms, not the assistant's):")
    any_reached = False
    for r in rows[:3]:
        keys = [str(k) for k in r["capability_keys"] if str(k)]
        query = " ".join(keys[:5])
        print("\n" + "-" * 74)
        print(f"  GAP (payoff={r['payoff']}): {keys[:4]}")
        print(f"  AGENT'S arXiv QUERY: {query!r}")
        hits = ww.arxiv_search(query, limit=3)
        reach = ww.arxiv_reachable()
        any_reached = any_reached or bool(reach)
        if not hits:
            print(f"    -> arxiv_reachable={reach}  HITS=0  "
                  f"({'unreachable — honest null, network boundary' if reach is False else 'no match for the agent gap terms'})")
            continue
        print(f"    -> arxiv_reachable={reach}  HITS={len(hits)}")
        for h in hits:
            title = re.sub(r"\s+", " ", h.get("title", "")).strip()
            abstract = (h.get("abstract") or "").lower()
            # (3) THE AGENT'S SELECTOR — name-key COVERAGE: which of THIS gap's terms
            # does the abstract carry? (the agent's own compression-coverage read).
            cover = sorted({k.lower() for k in keys
                            if k.lower() in (title.lower() + " " + abstract)})
            # un-held content terms in the abstract = the agent's acquire-by-reading
            # targets (terms it does NOT already ground out).
            terms = [w.lower() for w in _WORD.findall(abstract)]
            unheld = sorted({w for w in terms
                             if w not in held and w not in _STOP})[:8]
            verdict = ("ON-GAP" if cover else "off-gap (the agent's terms don't "
                       "cover it)")
            print(f"      • {title[:96]}")
            print(f"        {h.get('url','')}")
            print(f"        AGENT VERDICT: {verdict}; gap-terms covered={cover}")
            if cover:
                print(f"        acquire-by-reading (un-held terms it would ground): "
                      f"{unheld}")

    # (4) HONEST CLOSE.
    print("\n" + "=" * 78)
    if not any_reached:
        print("ARXIV UNREACHABLE this run (network boundary) — honest null. The "
              "agent named its gaps + emitted its own queries; the fetch is the "
              "external grant. Re-run when the network is open.")
    else:
        print("The agent named its OWN gaps, emitted its OWN queries (its "
              "capability_keys), fetched, and judged each hit with its OWN coverage "
              "selector. RESIDUAL (honest): coverage flags topical relevance; deep "
              "body-to-claims grounding (to PRIMITIVE, donkey-clean structure to "
              "CONSTRUCT) is the next step, not done here. No verbatim abstract emitted.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
