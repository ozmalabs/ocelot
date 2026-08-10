"""SCOPED, RESIDUAL-PRESERVING, BACKTRACKING COLLAPSE (domains/reading_scope.py).

The reading stack (reading_collapse) is GREEDY bottom-up: each order-N layer
commits its winner and discards the residual; the only reach-back is
reading_review's word-level adjacency repair. reading_scope corrects that to a
SCOPED collapse over the HELD reading_collapse / reading_review faculties
(extended by a new driver, NOT forked): a sentence-scope residual-preserving
lattice, an assembled-coherence score, a bounded backtrack-to-a-LOWER-re-decode,
a commit that SUPPRESSES + RETAINS the residual in a salience-ordered bounded
buffer (Sturt 2007 / Christianson 2001 — not a hard flush), reanalysis that
REACTIVATES the retained trace before a cold RE-READ FROM SOURCE, and a held-open
anti-polygraph.

Discriminative gates (donkey = 0, no LLM):

  * BACKTRACK-TO-A-LOWER-RE-DECODE (headline) — a sentence whose GREEDY collapse
    is incoherent (a clause SWALLOWED into an argument) but a BACKTRACK to a lower
    SEGMENTATION re-decode coheres. The fix is a LOWER re-decode, NOT a word swap
    (same words, different segmentation).
  * COMMIT = SUPPRESS + RETAIN — the committed gist holds the lossy summary and NO
    lattice (active buffer freed); the residual is DEMOTED to a suppressed, still-
    resident RetainedTrace (retained, not purged).
  * SENTENCE-SCOPE + STAGGERED COMMIT — the hard commit is at the sentence
    boundary; an unambiguous clause is stable across the lattice, the ambiguous
    boundary resolves only at the scope backtrack.
  * RE-READ ON NON-SEQUITUR — A commits R1; B shares no referent; REACTIVATE the
    retained trace -> R2 coheres with B (verbatim R1 -> R2).
  * COLD MISS -> RE-READ FROM SOURCE — an EVICTED trace forces the cold re-read
    (measurably more decode-expensive than reactivation).
  * HOLD-OPEN — no segmentation coheres -> HELD OPEN (flagged), not force-collapsed.
  * TERMINATION + BOUND — the backtrack is bounded (max_revisits) and terminates
    on the hardest case.
  * SALIENCE-EVICTION BUFFER — the bounded buffer evicts lowest-salience + oldest
    (mirrors the Rust memory forget_over_budget loop).
  * SOURCE AUDIT — no `import re`; lattice = ShapeDecode plan parts / segmentation;
    coherence = reading_review; single-pass rc/rr UNCHANGED (additive).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_reading_scope.py -p no:randomly -q
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core            # noqa: E402
from domains import dictionary_lexicon as dl          # noqa: E402
from domains import reading_collapse as rc            # noqa: E402
from domains import reading_review as rr              # noqa: E402
from domains import reading_scope as rs               # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


@pytest.fixture(scope="module", autouse=True)
def _warm():
    dl.warm_wordnet("en")


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


# A sentence whose GREEDY whole-scope collapse folds a whole clause ('smelt metal')
# into the object argument of the first verb; the LOWER segmentation splits it into
# two coherent transitive clauses. Same words, different segmentation.
HEADLINE = "miners extract ore furnaces smelt metal"


# --------------------------------------------------------------------------- #
#  HEADLINE — backtrack to a LOWER re-decode (segmentation), not a word swap.
# --------------------------------------------------------------------------- #
def test_backtrack_to_lower_redecode():
    ag = _fresh()
    r = rs.read_scope(ag, HEADLINE)
    assert r["committed"] is True and r["backtracked"] is True, r

    # GREEDY (commit-lower) is INCOHERENT — one clause, a clause swallowed into arg.
    greedy = r["ladder"][0]
    assert greedy["layer"] == "greedy_whole"
    assert greedy["predications"] == [["extract", "miners", "ore_furnaces_smelt_metal"]]
    assert greedy["incoherence"] > 0.0                                   # incoherent

    # BACKTRACK pulled a LOWER SEGMENTATION from the preserved residual -> COHERENT.
    step = r["ladder"][-1]
    assert step["layer"] == "backtrack_segmentation", r["ladder"]
    assert step["incoherence"] == 0.0
    assert r["predications"] == [["extract", "miners", "ore"], ["smelt", "furnaces", "metal"]]

    # the fix is a LOWER re-decode (2 clauses vs 1), NOT a word swap: the word
    # multiset is identical across greedy and the coherent reading.
    def _words(preds):
        # the FULL surface multiset — predicate AND args (a swallowed verb moves
        # from an argument into the predicate slot under a lower segmentation, so a
        # word-swap check must count both).
        out = []
        for p in preds:
            for tok in p:
                out.extend(tok.split("_"))
        return sorted(out)
    assert _words(greedy["predications"]) == _words(r["predications"])   # no word changed
    assert len(r["segmentation"]) == 2 and len(greedy["segmentation"]) == 1


# --------------------------------------------------------------------------- #
#  COMMIT = SUPPRESS + RETAIN (not a hard flush) — Sturt/Christianson.
# --------------------------------------------------------------------------- #
def test_commit_flush_suppress_retain():
    ag = _fresh()
    r = rs.read_scope(ag, HEADLINE)
    sub = ag.s
    gist = sub.node(r["gist_node"])["attrs"]

    # the GIST is the stable LOSSY summary — NO lattice / alternatives on it
    # (active buffer freed).
    assert gist["summary"] == "extract(miners, ore); smelt(furnaces, metal)"
    assert "alternatives" not in gist and "lattice" not in gist and "residual" not in gist

    # the residual is RETAINED, not purged: a SUPPRESSED, still-RESIDENT trace holds
    # the demoted alternatives (retrievable).
    tr = sub.node(r["trace_node"])["attrs"]
    assert tr["suppressed"] == 1.0 and tr["resident"] == 1.0 and tr["evicted"] == 0.0
    assert tr["activation"] < 0.5                                        # demoted / low
    assert r["n_retained_alternatives"] >= 1
    import json
    assert len(json.loads(tr["alternatives"])) == r["n_retained_alternatives"]


# --------------------------------------------------------------------------- #
#  SENTENCE-SCOPE + STAGGERED COMMIT — hard commit at the boundary.
# --------------------------------------------------------------------------- #
def test_sentence_scope_staggered_commit():
    ag = _fresh()
    sub = ag.s
    before = len(sub.nodes("ScopeGist"))
    r = rs.read_scope(ag, HEADLINE)
    after = len(sub.nodes("ScopeGist"))
    # exactly ONE hard commit, at the sentence boundary (one ScopeGist written).
    assert after - before == 1

    # STAGGERED: the unambiguous constituent (extract(miners, ore)) is stable — it is
    # already present in the greedy provisional reading; the ambiguous boundary
    # (smelt(furnaces, metal)) appears ONLY after the scope-level backtrack resolves.
    greedy_preds = r["ladder"][0]["predications"]
    committed = r["predications"]
    assert ["extract", "miners", "ore"] in committed                    # unambiguous, committed
    # the ambiguous clause is NOT in the greedy reading (it was swallowed) — it only
    # commits when the sentence scope resolves the boundary.
    assert ["smelt", "furnaces", "metal"] in committed
    assert ["smelt", "furnaces", "metal"] not in greedy_preds


# --------------------------------------------------------------------------- #
#  RE-READ ON NON-SEQUITUR — reactivate the retained trace -> R2 coheres with B.
# --------------------------------------------------------------------------- #
# A has a genuine ATTACHMENT ambiguity: 'metal' attaches to 'ore' (@4) or to
# 'smelters' (@3); both segmentations are fully coherent. Greedy backtracks to the
# first coherent one (R1: metal_smelters); B ('smelters melt iron') shares no
# referent with R1's committed gist -> reactivate -> R2 (clean 'smelters') coheres.
AMBIG = "miners extract ore metal smelters process alloys"


def test_reread_on_non_sequitur_reactivates_trace():
    ag = _fresh()
    out = rs.read_paragraph(ag, AMBIG + ". smelters melt iron.", trace_capacity=8)
    assert out["n_reanalyses"] == 1, out
    ra = out["reanalyses"][0]
    assert ra["path"] == "reactivate_retained_trace", ra
    # R1 (committed) had the blurred 'metal_smelters' attachment; B did not cohere.
    assert ra["r1"] == [["extract", "miners", "ore"], ["process", "metal_smelters", "alloys"]]
    assert "smelters" not in ra["r1_referents"]
    # R2 (reactivated from the RETAINED trace) has the clean 'smelters' that coheres
    # with B — a re-collapse of A, NOT of B.
    assert ra["r2"] == [["extract", "miners", "ore_metal"], ["process", "smelters", "alloys"]]
    assert "smelters" in ra["r2_referents"]


def test_cold_miss_reread_from_source_when_evicted():
    ag = _fresh()
    recA = rs.read_scope(ag, AMBIG)
    # EVICT A's trace (the ring wrapped it out — 'scope too far back').
    rs.enforce_trace_buffer(ag, 0)
    assert len(rs._resident_traces(ag.s)) == 0

    b = rs.read_scope(ag, "smelters melt iron")
    trigger = {"sentence": "smelters melt iron", "predications": b["predications"]}
    res = rs._reanalyse(ag, recA, trigger, 8)
    # the retained path is a COLD MISS (trace evicted) -> RE-READ FROM SOURCE.
    assert res["path"] == "reread_from_source", res
    assert res["reactivate_decode_cost"] == 0                # immediate miss, no re-derivation
    assert res["reread_decode_cost"] > res["reactivate_decode_cost"]     # source is costlier
    assert res["r2"] == [["extract", "miners", "ore_metal"], ["process", "smelters", "alloys"]]


# --------------------------------------------------------------------------- #
#  HOLD-OPEN — no residual alternative coheres -> flagged, not force-collapsed.
# --------------------------------------------------------------------------- #
def test_hold_open_when_nothing_coheres():
    ag = _fresh()
    r = rs.read_scope(ag, "glorp flonk zibble wug")
    assert r["committed"] is False and r["held_open"] is True, r
    assert r["best_incoherence"] >= 0.9                       # nothing grounded coherently
    # HELD OPEN is flagged on the ScopeGist, not a forced commit.
    g = ag.s.node(r["gist_node"])["attrs"]
    assert g["held_open"] == 1.0


# --------------------------------------------------------------------------- #
#  TERMINATION + BOUND — the backtrack is bounded and terminates.
# --------------------------------------------------------------------------- #
def test_backtrack_terminates_and_is_bounded():
    ag = _fresh()
    c0 = rs._decode_calls(ag)
    r = rs.read_scope(ag, HEADLINE, max_revisits=8)
    spent = rs._decode_calls(ag) - c0
    assert r["committed"] is True
    assert r["max_revisits"] == 8 and r["n_revisits"] <= 8   # bounded revisits
    # the lattice is finite (whole + n-1 binary splits) so the decode cost is O(n),
    # not exponential — it terminates well within a generous ceiling.
    assert spent < 60, spent


# --------------------------------------------------------------------------- #
#  SALIENCE-EVICTION BUFFER — mirrors forget_over_budget (lowest salience first).
# --------------------------------------------------------------------------- #
def test_salience_ordered_eviction():
    ag = _fresh()
    # a clean greedy commit (salience 0 — low) and an ambiguous one that backtracked
    # (salience > 0 — high). Bound to capacity 1: the LOW-salience trace evicts first.
    clean = rs.read_scope(ag, "smelters melt iron")          # greedy coheres -> salience 0
    hard = rs.read_scope(ag, HEADLINE)                       # backtracked -> salience > 0
    assert clean["salience"] == 0.0 and hard["salience"] > 0.0
    rs.enforce_trace_buffer(ag, 1)
    # the high-salience (surprising) trace is retained; the low-salience one evicted.
    assert rs._trace_resident(ag.s, hard["trace_node"]) is True
    assert rs._trace_resident(ag.s, clean["trace_node"]) is False


# --------------------------------------------------------------------------- #
#  SOURCE AUDIT + NO REGRESSION (additive over unchanged rc / rr).
# --------------------------------------------------------------------------- #
def test_source_audit_no_regex():
    path = os.path.join(ROOT, "domains", "reading_scope.py")
    with open(path) as f:
        src = f.read()
    # no standalone regex import (line-exact, so 'import reading_collapse' is fine).
    lines = {ln.strip() for ln in src.splitlines()}
    assert not any(ln == "import re" or ln.startswith(("import re ", "import re,", "import regex"))
                   for ln in lines)
    assert "re.compile" not in src and "re.match" not in src and "re.search" not in src
    # the coherence oracle is reading_review (reused), the lattice the ShapeDecode
    # plan / segmentation — assert the driver imports and calls them, not a parser.
    assert "from domains import reading_review" in src
    assert "from domains import reading_collapse" in src


def test_single_pass_faculties_unchanged():
    # the scoped collapse is a NEW driver OVER rc/rr; the single-pass read_clause is
    # byte-identical (additive). Read the headline's first clause directly.
    ag = _fresh()
    r = rc.read_clause(ag, "miners extract ore", write=False)
    assert r["predications"] == [["extract", "miners", "ore"]]
    # reading_review still reviews a clause independently (unchanged surface).
    rev = rr.review_clause(ag, "miners extract ore")
    assert rev["repaired"] is False               # coherent — not touched by the review
