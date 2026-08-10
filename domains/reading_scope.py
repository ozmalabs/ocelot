"""reading_scope — SCOPED, RESIDUAL-PRESERVING, BACKTRACKING COLLAPSE.

The reading stack (domains/reading_collapse.py) is GREEDY bottom-up: order-N
descent commits each layer's collapse and hands the WINNER up, discarding the
residual; the only reach-back is reading_review's word-level adjacency repair.
This driver corrects that to a SCOPED collapse — a cache hierarchy over the held
reading_collapse / reading_review faculties (extended, NOT forked):

  · COLLAPSE IS PROVISIONAL. Each layer hands its collapse UP WITH RESIDUAL — a
    ranked lattice of runner-ups (SEGMENTATIONS at order N, from the region /
    split lattice; CONSTRUCTIONS at order 1, from the ShapeDecode plan's ranked
    parts via the `exclude` re-decode). The lower layer PROPOSES; it does not
    decide.
  · COHERENCE is judged at the ASSEMBLED scope (the SENTENCE). The per-clause
    signal is reading_review.combined_incoherence (groundability + selectional
    fit — REUSED as-is); the scope adds a COMPLETENESS term the head-only
    per-clause signal cannot see: a role span that SWALLOWS a predication (an
    interior verb-headed token with material on both sides — the SAME verb-head
    test read_clause itself uses, one grain finer) is a clause the greedy layer
    wrongly folded into an argument. The higher incoherence PULLS the right
    lower option out of the lattice.
  · BACKTRACK. On incoherence, revisit a lower layer's residual — an alternative
    SEGMENTATION (order N) or CONSTRUCTION (order 1) — until the assembly
    coheres. BOUNDED: a beam of `max_revisits` over the scope's lattice; it
    terminates (the lattice is finite: n-1 binary segmentations + the
    construction runner-ups). This is EAGER COMMITMENT THEN REVISION (the
    garden-path result: commit fast, revise on failure), not indefinite hold.
  · COMMIT = SUPPRESS + RETAIN (Sturt 2007 "Return of the Repressed";
    Christianson et al. 2001). At the sentence boundary the coherent collapse
    commits to a stable lossy GIST, and the residual lattice is NOT purged — it
    is DEMOTED into a SALIENCE-ORDERED BOUNDED BUFFER (the retained/suppressed
    tier), at low activation. The active buffer is freed (the tractability — the
    trace is compressed / deprioritised), but the abandoned alternatives remain
    retrievable. The buffer MIRRORS the substrate's own memory management (the
    Rust `memory_bound` / `forget_over_budget` salience-eviction loop,
    domains/graph_virtual_memory.py's resident/paged pattern): SALIENCE (the
    commit's surprise = how much competition the backtrack left) is the ordering
    key for retention, eviction, and reactivation search; when the buffer exceeds
    its bound the lowest-salience + oldest trace is EVICTED (the ring wraps —
    "scope too far back" == "wrapped out"). [Not GVM directly: GVM is a disk-slab
    concept-cluster pager and its global `memory_bound` would evict arbitrary
    nodes; the reading tier mirrors its salience-eviction shape in-memory.]
  · REANALYSIS (a later NON-SEQUITUR — a new sentence that shares no referent
    with a committed gist) REACTIVATES a still-RESIDENT demoted trace FIRST: an
    in-buffer salience re-promote (page-in) + re-collapse from the retained
    alternatives (cheap — no re-derivation, matching the Sturt reanalysis
    speed-up). RE-READ FROM SOURCE is the COLD MISS: the needed trace was EVICTED
    (wrapped out of the ring), so re-fetch from text and regenerate the lattice —
    measurably more expensive. Similar unresolved traces crowd the same salience
    band and evict/blur each other, so "capacity exceeded" is distinctness lost
    under salience-crowding, not slot-count (Lewis & Vasishth 2005/06 similarity-
    based interference — the shape falls out of the salience ring).

DISCIPLINE (CLAUDE.md). This is a mechanical driver, the twin of
reading_review's review driver: the DECISIONS are the collapse (rc.read_clause)
and the coherence oracle (reading_review.combined_incoherence + the held
is_verb_headed POS faculty) — read off, never a hardcoded meaning branch. The
lattice enumeration (split points / construction exclude-runner-ups) is
mechanical, exactly as reading_review enumerates adjacency neighbours. The
single-pass rc.read_clause / read_clause_order_n / rr.review_* are UNCHANGED —
this is additive. NO regex, NO whitespace tokenizer (rc / ct do the recognition
tokenising). Gists + retained traces are graph nodes (adapter-admissible I/O).

LIVE + FLOW-SCOPED + DYNAMIC (Wave: dynamic-thresholds/reopen/reform,
2026-07-11). `_commit`/`enforce_trace_buffer`/`_resident_traces` now take an
optional `unit=` (the Wave 1A flow-identity convention): a RetainedTrace
carries a `flow` stamp so the ring can be bounded PER FLOW on a persistent
substrate. The ring's CAPACITY is no longer only the Python literal default —
`coref_entities.read_into_situation_model` (the live per-sentence spine driver
`reading_drive._shim_spine` calls) now calls `enforce_trace_buffer` after
EVERY commit with a capacity derived from `domains/reading_norms.
effective_trace_capacity` (a held Program evaluated over this flow's own
register + overflow pressure) — "the reopen is the entire point of the
circular buffer and was already in place for extended reading" (the user's
directive) is now true of the LIVE flow, not only `read_paragraph`.
`swallowed_ratio` is factored out of `_assembled_incoherence` for reuse as a
COMPLEXITY measurement the `reform_overcomplex_clause` rule
(seeds/reading_aperture.json) compares against a held threshold.
"""
from __future__ import annotations

import json
from typing import Any, Optional

from domains import comprehend_text as ct
from domains import instruction_reading as ir
from domains import reading_collapse as rc
from domains import reading_review as rr
from domains import reflective_faculty as rf


# --------------------------------------------------------------------------- #
#  resolution (mechanical adapter I/O).
# --------------------------------------------------------------------------- #
def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    return sub, native


def _decode_calls(agent) -> int:
    """A cheap decode-cost counter (the tractability metric — reactivation must be
    cheaper than a cold re-read). Kept on the driver, mechanical."""
    return int(getattr(agent, "_scope_decode_calls", 0) or 0)


def _bump(agent, n: int = 1) -> None:
    agent._scope_decode_calls = _decode_calls(agent) + n


# --------------------------------------------------------------------------- #
#  ASSEMBLED-SCOPE COHERENCE — reading_review per clause + a scope completeness
#  term (a SWALLOWED predication the head-only per-clause signal cannot see).
# --------------------------------------------------------------------------- #
def _swallows_predication(span: str) -> bool:
    """Does argument `span` (underscore-joined recognised words) SWALLOW a
    predication — i.e. contain an interior verb-headed token with content on BOTH
    sides? That is a clause the greedy layer folded into an argument. The test is
    read_clause's OWN verb-head test (ir.is_verb_headed with non-empty left/right),
    applied one grain finer inside the argument. Held POS faculty, no regex."""
    toks = [t for t in str(span).split("_") if t]
    for i in range(len(toks)):
        if ir.is_verb_headed(toks[i]) and toks[:i] and toks[i + 1:]:
            return True
    return False


def _clause_read(agent, words: list) -> dict:
    _bump(agent)
    return rc.read_clause(agent, list(words), write=False)


def swallowed_ratio(preds: list) -> float:
    """The COMPLEXITY measurement `_assembled_incoherence` folds into its
    scope-completeness term, factored out for reuse (Wave: dynamic-thresholds/
    reform): the fraction of grounded argument roles that SWALLOW a predication
    (an interior verb-headed token with content on both sides — a clause the
    greedy layer folded into an argument). Pure measurement, no decision — a
    reform RULE (seeds/reading_aperture.json) compares this against a held,
    revisable threshold."""
    roles = 0
    swallowed = 0
    for p in preds or []:
        for arg in p[1:]:
            roles += 1
            if _swallows_predication(arg):
                swallowed += 1
    return (swallowed / roles) if roles else 0.0


def _assembled_incoherence(agent, reads: list) -> float:
    """The scope's incoherence in [0, 1]. max of: (a) each clause's
    reading_review.combined_incoherence (groundability AND selectional fit,
    REUSED); (b) the fraction of grounded argument roles that SWALLOW a
    predication (the scope-completeness term). A segmentation that leaves a clause
    folded into an argument reads incoherently AT THE SCOPE even when every
    per-clause head is groundable — the documented head-only limit of the
    per-clause signal, lifted to the assembled scope."""
    if not reads:
        return 1.0
    per_clause = max(rr.combined_incoherence(agent, r) for r in reads)
    preds = [p for r in reads for p in (r.get("predications") or [])]
    complete = swallowed_ratio(preds)
    # a segmentation that grounded NOTHING (all thin) is maximally incoherent so a
    # real reading always beats it.
    if not any(r.get("predications") for r in reads):
        return 1.0
    return max(per_clause, complete)


# --------------------------------------------------------------------------- #
#  ORDER-N SEGMENTATION LATTICE — the residual-preserving alternatives. The whole
#  sentence is the greedy (commit-lower) segmentation; the binary splits at each
#  interior boundary are the ranked runner-ups. Mechanical enumeration (the twin
#  of reading_review's adjacency-neighbour enumeration); the coherence oracle
#  ranks them, the driver never hand-picks a boundary.
# --------------------------------------------------------------------------- #
def _segmentations(words: list) -> list:
    """Candidate segmentations of one sentence scope: the WHOLE (greedy) first,
    then every binary split. Each is a list of clause word-lists. Finite (n
    candidates) => the backtrack terminates."""
    words = [w for w in words if str(w).strip()]
    segs = [[list(words)]]
    for k in range(1, len(words)):
        left, right = words[:k], words[k:]
        if left and right:
            segs.append([list(left), list(right)])
    return segs


def _score_segmentation(agent, seg: list) -> dict:
    reads = [_clause_read(agent, cl) for cl in seg if cl]
    preds = [p for r in reads for p in (r.get("predications") or [])]
    return {"segmentation": [list(c) for c in seg], "reads": reads,
            "predications": preds, "incoherence": _assembled_incoherence(agent, reads)}


# --------------------------------------------------------------------------- #
#  ORDER-1 CONSTRUCTION LATTICE — the ShapeDecode plan's ranked runner-ups for a
#  clause skeleton, surfaced via the `exclude` re-decode (the residual the greedy
#  _winner discards). Available as a lower re-decode for a single clause whose
#  construction choice is what is incoherent (as opposed to its segmentation).
# --------------------------------------------------------------------------- #
def construction_lattice(agent, skeleton: list, *, depth: int = 5) -> list:
    """The ranked alternative CONSTRUCTIONS for one clause skeleton — the order-1
    residual. Re-decodes with each accepted winner EXCLUDED so the ShapeDecode
    Term surfaces the next-best part; the ranking is the decode's own, never
    re-ranked here. This is the order-1 twin of `_segmentations`."""
    sub, _ = _resolve(agent)
    lattice: list = []
    excl: list = []
    for _ in range(depth):
        res = rf.compose_design_for_goal(sub, skeleton, exclude=excl or None)
        name, fit = rc._winner(res)
        if name is None or fit <= 0:
            break
        lattice.append({"construction": name, "shape_fit": fit})
        excl.append(name)
    return lattice


# --------------------------------------------------------------------------- #
#  GIST + RETAINED TRACE — commit = SUPPRESS + RETAIN (not purge).
# --------------------------------------------------------------------------- #
def _referents(preds: list) -> set:
    out: set = set()
    for p in preds or []:
        for arg in p[1:]:
            out.add(str(arg))
    return out


def _summary(preds: list) -> str:
    """The stable LOSSY gist string — the committed predications, joined. No
    lattice, no residual (the flush semantics: the gist is lossy)."""
    return "; ".join("%s(%s)" % (p[0], ", ".join(p[1:])) for p in preds or [])


def _next_age(agent) -> int:
    agent._scope_trace_age = int(getattr(agent, "_scope_trace_age", 0)) + 1
    return agent._scope_trace_age


def _commit(agent, sentence: str, winner: dict, residual: list, *, salience: float,
           unit=None) -> dict:
    """COMMIT the coherent collapse to a GIST and DEMOTE the residual lattice into
    the salience-ordered retained buffer (Sturt/Christianson: suppress + retain,
    NOT delete). Writes a ScopeGist node (the stable lossy summary — no lattice)
    and a RetainedTrace node (the demoted alternatives, suppressed=1, low
    activation, resident=1, carrying its `salience` retention key + monotone
    `age`). The active buffer is freed (the residual leaves the open scope) but the
    trace stays retrievable until the bound evicts it. Mechanical graph I/O.

    `unit` (Wave: dynamic-thresholds, the Wave-1A `unit=`/`flow` convention):
    when given, stamped as `flow` on both nodes so the ring buffer (`enforce_
    trace_buffer`) can be bounded PER FLOW on a persistent substrate — a second
    flow's traces never evict or count toward this flow's own ring. `None` (every
    caller before this wave) is the byte-identical unscoped ring."""
    sub, _ = _resolve(agent)
    preds = winner["predications"]
    gist_attrs = {"sentence": sentence, "summary": _summary(preds),
                  "predications": json.dumps(preds),
                  "segmentation": json.dumps(winner["segmentation"]),
                  "incoherence": float(winner["incoherence"]),
                  "held_open": 0.0}
    trace_attrs = {"sentence": sentence, "suppressed": 1.0, "activation": 0.1,
                   "resident": 1.0, "evicted": 0.0, "salience": float(salience),
                   "age": float(_next_age(agent)),
                   "alternatives": json.dumps([
                       {"segmentation": a["segmentation"], "incoherence": float(a["incoherence"]),
                        "predications": a["predications"]}
                       for a in residual])}
    if unit is not None:
        gist_attrs["flow"] = unit
        trace_attrs["flow"] = unit
    gist_node = sub.add_node("ScopeGist", gist_attrs)
    trace_attrs["gist"] = gist_node.value if hasattr(gist_node, "value") else gist_node
    # DEMOTE, do not discard: the abandoned alternatives become a suppressed trace
    # in the salience-ordered bounded buffer.
    trace_node = sub.add_node("RetainedTrace", trace_attrs)
    return {"sentence": sentence, "committed": True, "held_open": False,
            "gist_node": gist_node, "trace_node": trace_node,
            "gist": _summary(preds), "predications": preds, "salience": float(salience),
            "segmentation": winner["segmentation"], "referents": sorted(_referents(preds)),
            "incoherence": float(winner["incoherence"]),
            "n_retained_alternatives": len(residual)}


# --------------------------------------------------------------------------- #
#  SALIENCE-ORDERED BOUNDED BUFFER — mirrors the Rust memory `forget_over_budget`
#  eviction loop (rank victims ascending by keep-value, evict, repeat until under
#  bound). Here keep-value = SALIENCE (the commit's surprise), tie-broken by AGE.
# --------------------------------------------------------------------------- #
def _resident_traces(sub, unit=None) -> list:
    out: list = []
    for nd in sub.nodes("RetainedTrace"):
        at = sub.node(nd)["attrs"]
        if unit is not None and at.get("flow") != unit:
            continue
        if float(at.get("evicted", 0.0)) < 1.0 and float(at.get("resident", 0.0)) >= 1.0:
            out.append((nd, float(at.get("salience", 0.0)), float(at.get("age", 0.0))))
    return out


def enforce_trace_buffer(agent, capacity: int, *, unit=None) -> list:
    """Bound the retained buffer to `capacity` resident traces. While over bound,
    EVICT the lowest-salience + oldest resident trace (mark evicted=1, resident=0 —
    the ring wraps it out; it is now a cold miss). Mirrors the Rust memory
    `forget_over_budget` ascending-keep-value eviction loop. Returns the evicted
    trace nodes (for inspection).

    `unit` (Wave: dynamic-thresholds): when given, the ring is bounded to THIS
    flow's own resident traces only (a persistent substrate's other flows are
    untouched) — the same `unit=`/`flow` convention every other flow-scoped
    reader/writer in this codebase uses. `None` is the byte-identical unscoped
    ring `read_paragraph` already exercises."""
    sub, _ = _resolve(agent)
    evicted: list = []
    while True:
        res = _resident_traces(sub, unit=unit)
        if len(res) <= capacity:
            break
        res.sort(key=lambda t: (t[1], t[2]))          # salience asc, then age asc (oldest)
        victim = res[0][0]
        try:
            sub.set_attr(victim, "evicted", 1.0)
            sub.set_attr(victim, "resident", 0.0)
        except Exception:
            break
        evicted.append(victim)
    return evicted


def _trace_resident(sub, trace_node) -> bool:
    try:
        at = sub.node(trace_node)["attrs"]
        return float(at.get("evicted", 0.0)) < 1.0 and float(at.get("resident", 0.0)) >= 1.0
    except Exception:
        return False


# --------------------------------------------------------------------------- #
#  CLAUSE-DECOMPOSITION COMMIT — the order-N clause descent's reading committed as
#  a normal sentence scope (a gist + a retained trace), so the downstream drivers
#  (situation_model_reader / coref_entities read rec["predications"]; read_paragraph
#  reanalyses off rec["trace_node"]/rec["referents"]) see the SAME shape a greedy/
#  backtrack commit produces. Mechanical — the DECISION (which clauses, which
#  predication) is rc.decompose_sentence's collapse; this only records it.
# --------------------------------------------------------------------------- #
def _commit_decomposition(agent, text: str, decomp: dict, *, unit=None) -> dict:
    winner = {"predications": decomp["predications"],
              "segmentation": decomp.get("read_clauses") or decomp["clauses"],
              "incoherence": 0.0}
    out = _commit(agent, text, winner, [], salience=0.0, unit=unit)
    out["ladder"] = [{"layer": "clause_decomposition",
                      "segmentation": winner["segmentation"],
                      "incoherence": 0.0, "predications": winner["predications"]}]
    out["greedy_incoherence"] = 0.0
    out["backtracked"] = False
    out["n_revisits"] = 0
    out["source"] = "clause_decomposition"
    out["n_boundaries"] = decomp.get("n_boundaries")
    return out


# --------------------------------------------------------------------------- #
#  READ ONE SENTENCE SCOPE — provisional greedy collapse + bounded backtrack.
# --------------------------------------------------------------------------- #
def read_scope(agent, sentence, *, max_revisits: int = 8, cohere_threshold: float = 1e-9,
               _words: Optional[list] = None, unit=None) -> dict:
    """Read ONE sentence scope by a PROVISIONAL greedy collapse + a BOUNDED
    backtrack over the residual-preserving segmentation lattice. Eager commit then
    revise: the whole-sentence (greedy) segmentation is tried first; if it does not
    cohere at the assembled scope, the ranked residual (the runner-up
    segmentations) is walked — bounded by `max_revisits` — until the assembly
    coheres. Commit = suppress+retain (a gist + a demoted retained trace). If the
    residual exhausts with nothing coherent the scope is HELD OPEN (flagged), not
    force-collapsed. Returns the commit record + the ladder + the greedy baseline."""
    rr.ensure_review_seed(agent)
    if _words is not None:
        words = list(_words)
    elif isinstance(sentence, (list, tuple)):
        words = list(sentence)
    else:
        words = ct._recognise_words(agent, str(sentence))
    text = sentence if isinstance(sentence, str) else " ".join(str(w) for w in words)

    # CLAUSE DECOMPOSITION (order-N descent into CLAUSES) — a multi-clause sentence
    # whose subordinate/coordinate/participial structure the greedy whole-sentence
    # collapse would GLOM into one blob argument is first decomposed at RECOGNISED
    # clause boundaries (CLAUSE_LINK / IF / CAUSE_SUB / REL markers, comma regions,
    # AND/OR between two verb-headed clauses) and each clause read into its own clean
    # verb-headed predication (rc.decompose_sentence). Fires ONLY when a real clause
    # boundary is recognised AND >=1 clause grounds — a single-clause SVO sentence
    # (no boundary marker) has multi_clause False and falls straight through to the
    # greedy/binary segmentation lattice below, unchanged (so every short-SVO gate
    # and the reading_scope backtrack tests are untouched).
    decomp = rc.decompose_sentence(agent, text)
    if decomp.get("multi_clause"):
        return _commit_decomposition(agent, text, decomp, unit=unit)

    cands = _segmentations(words)
    if not cands:
        return {"sentence": text, "committed": False, "held_open": True,
                "note": "empty scope — nothing to read"}

    # order 0: the GREEDY (whole-sentence) collapse — the provisional commit.
    greedy = _score_segmentation(agent, cands[0])
    # the residual lattice: the runner-up segmentations, RANKED by the coherence
    # oracle (the review decides the order, not the driver).
    residual = [_score_segmentation(agent, seg) for seg in cands[1:]]
    residual.sort(key=lambda d: (d["incoherence"], len(d["segmentation"])))

    ladder = [{"layer": "greedy_whole", "segmentation": greedy["segmentation"],
               "incoherence": greedy["incoherence"],
               "predications": greedy["predications"]}]

    winner = None
    if greedy["incoherence"] <= cohere_threshold:
        winner = greedy
    else:
        # BACKTRACK: pull the first residual alternative that coheres. Bounded.
        for i, alt in enumerate(residual[:max_revisits]):
            ladder.append({"layer": "backtrack_segmentation", "revisit": i + 1,
                           "segmentation": alt["segmentation"],
                           "incoherence": alt["incoherence"],
                           "predications": alt["predications"]})
            if alt["incoherence"] <= cohere_threshold:
                winner = alt
                break

    if winner is None:
        # HELD OPEN — eager revision exhausted the bounded lattice with nothing
        # coherent. Flag, do not force. (Best-so-far recorded for inspection.)
        best = min([greedy] + residual, key=lambda d: d["incoherence"])
        sub, _ = _resolve(agent)
        node = sub.add_node("ScopeGist", {
            "sentence": text, "held_open": 1.0, "summary": "(held open)",
            "best_incoherence": float(best["incoherence"]),
            "predications": json.dumps(best["predications"]),
            "segmentation": json.dumps(best["segmentation"])})
        return {"sentence": text, "committed": False, "held_open": True,
                "gist_node": node, "ladder": ladder,
                "greedy_incoherence": greedy["incoherence"],
                "best_incoherence": best["incoherence"],
                "n_revisits": min(len(residual), max_revisits),
                "note": ("residual exhausted within the %d-revisit bound with nothing "
                         "coherent — HELD OPEN, not force-collapsed" % max_revisits)}

    # the residual demoted at commit = every scored alternative EXCEPT the winner.
    demoted = [a for a in ([greedy] + residual) if a is not winner]
    # SALIENCE = the commit's SURPRISE (residual currency): how much the greedy
    # provisional collapse failed = how much live competition the backtrack left.
    # A clean greedy commit (0) is low-salience (evicted first); an ambiguous one
    # that needed revision is high-salience (retained longer).
    salience = float(greedy["incoherence"])
    out = _commit(agent, text, winner, demoted, salience=salience, unit=unit)
    out["ladder"] = ladder
    out["greedy_incoherence"] = greedy["incoherence"]
    out["backtracked"] = winner is not greedy
    out["n_revisits"] = (len(ladder) - 1) if winner is not greedy else 0
    out["max_revisits"] = max_revisits
    return out


# --------------------------------------------------------------------------- #
#  CROSS-SENTENCE COHERENCE + REANALYSIS — reactivate the retained trace FIRST,
#  re-read from source only as the cold-miss fallback.
# --------------------------------------------------------------------------- #
def _coheres_across(referents_a: set, referents_b: set) -> bool:
    """Two committed gists cohere across the paragraph iff they SHARE a referent
    (a discourse link). No shared referent => a NON-SEQUITUR — the trigger for
    reanalysis of the earlier commit."""
    return bool(set(referents_a) & set(referents_b))


def reactivate(agent, trace_node, referents_b: set) -> Optional[dict]:
    """REACTIVATE a retained suppressed trace (the Sturt reanalysis path): boost
    the demoted alternatives and pick the one whose reading SHARES A REFERENT with
    the non-sequitur sentence B — re-collapsing from the RETAINED lattice, NOT
    re-deriving from source. Cheap: it reads the few retained alternatives, not
    the full split lattice. Returns the reactivated reading or None (trace EVICTED
    — wrapped out of the ring, a cold miss — or holds no alternative coherent with
    B)."""
    sub, _ = _resolve(agent)
    if not _trace_resident(sub, trace_node):
        return None                                    # wrapped out of the ring — cold miss
    try:
        alts = json.loads(sub.node(trace_node)["attrs"].get("alternatives") or "[]")
    except Exception:
        alts = []
    # boost: the trace is re-activated (mechanical set_attr — the suppression lifts).
    try:
        sub.set_attr(trace_node, "activation", 1.0)
        sub.set_attr(trace_node, "suppressed", 0.0)
    except Exception:
        pass
    for a in alts:
        # re-collapse this retained segmentation (cheap: known segmentation).
        reads = [_clause_read(agent, cl) for cl in a["segmentation"] if cl]
        preds = [p for r in reads for p in (r.get("predications") or [])]
        if _assembled_incoherence(agent, reads) > 1e-9:
            continue
        if _coheres_across(_referents(preds), referents_b):
            return {"segmentation": a["segmentation"], "predications": preds,
                    "referents": sorted(_referents(preds)), "source": "retained_trace"}
    return None


def read_paragraph(agent, text: str, *, max_sentences: int = 40,
                   max_revisits: int = 8, trace_capacity: int = 8) -> dict:
    """A PARAGRAPH scope over sentence scopes: commit each sentence provisionally,
    hold the committed gists for cross-sentence coherence, and on a NON-SEQUITUR
    (a sentence sharing no referent with the prior commit) REANALYSE the prior
    sentence — REACTIVATE its retained suppressed trace FIRST (cheap), falling back
    to a cold RE-READ FROM SOURCE when the trace was EVICTED from the bounded
    buffer (`trace_capacity`) or holds nothing coherent with B. Returns the
    committed gists, the reanalysis events + which path resolved each + its decode
    cost (reactivation is markedly cheaper than the cold re-read)."""
    rr.ensure_review_seed(agent)
    sentences = rc._split_sentences(text)
    commits: list = []
    reanalyses: list = []
    prior: Optional[dict] = None
    for s in sentences[:max_sentences]:
        if not s.strip():
            continue
        rec = read_scope(agent, s, max_revisits=max_revisits)
        commits.append(rec)
        if prior is not None and rec.get("committed") and prior.get("committed"):
            if not _coheres_across(prior["referents"], _referents(rec["predications"])):
                reanalyses.append(_reanalyse(agent, prior, rec, max_revisits))
        if rec.get("committed"):
            prior = rec
        # bound the retained buffer: the ring wraps, evicting lowest-salience+oldest.
        enforce_trace_buffer(agent, trace_capacity)
    return {"sentences": sentences, "commits": commits, "reanalyses": reanalyses,
            "n_reanalyses": len(reanalyses),
            "resident_traces": len(_resident_traces(_resolve(agent)[0]))}


def _reanalyse(agent, prior: dict, trigger: dict, max_revisits: int) -> dict:
    """Reanalyse `prior` given the non-sequitur `trigger`: REACTIVATE first, cold
    RE-READ FROM SOURCE as the fallback. Reports which path resolved it + the
    decode cost of each, so the retained-trace speed-up is measurable."""
    b_refs = _referents(trigger["predications"])
    # 1) REACTIVATE the retained suppressed trace (cheap — no re-derivation).
    c0 = _decode_calls(agent)
    reac = reactivate(agent, prior["trace_node"], b_refs)
    reactivate_cost = _decode_calls(agent) - c0
    if reac is not None:
        return {"prior_sentence": prior["sentence"], "trigger_sentence": trigger["sentence"],
                "non_sequitur": True, "path": "reactivate_retained_trace",
                "r1": prior["predications"], "r1_referents": prior["referents"],
                "r2": reac["predications"], "r2_referents": reac["referents"],
                "trigger_referents": sorted(b_refs),
                "reactivate_decode_cost": reactivate_cost,
                "note": ("NON-SEQUITUR: B shares no referent with the committed gist "
                         "-> REACTIVATED the retained suppressed trace (Sturt path) -> "
                         "re-collapsed to a reading that shares %s with B"
                         % sorted(set(reac["referents"]) & b_refs))}
    # 2) COLD FALLBACK — re-read the prior sentence FROM SOURCE (regenerate the whole
    #    lattice). Only when the retained trace holds nothing coherent with B.
    c0 = _decode_calls(agent)
    words = ct._recognise_words(agent, prior["sentence"])
    reread = _reread_from_source(agent, prior["sentence"], words, b_refs, max_revisits)
    reread_cost = _decode_calls(agent) - c0
    return {"prior_sentence": prior["sentence"], "trigger_sentence": trigger["sentence"],
            "non_sequitur": True, "path": "reread_from_source",
            "r1": prior["predications"], "r2": reread,
            "reactivate_decode_cost": reactivate_cost, "reread_decode_cost": reread_cost,
            "note": ("retained trace held nothing coherent with B -> COLD RE-READ FROM "
                     "SOURCE (deep fallback) regenerated the full lattice")}


def _reread_from_source(agent, sentence: str, words: list, referents_b: set,
                        max_revisits: int) -> Optional[list]:
    """The cold-miss path: regenerate the full segmentation lattice from source and
    re-collapse to a reading coherent with B. This is the DEEP FALLBACK (the
    retained trace was unavailable); it re-derives everything, so it is measurably
    more expensive than reactivation."""
    for seg in _segmentations(words):
        sc = _score_segmentation(agent, seg)
        if sc["incoherence"] <= 1e-9 and _coheres_across(_referents(sc["predications"]), referents_b):
            return sc["predications"]
    return None


__all__ = [
    "read_scope", "read_paragraph", "reactivate", "enforce_trace_buffer",
    "construction_lattice", "_segmentations", "_assembled_incoherence",
    "_swallows_predication", "_coheres_across", "_resident_traces",
    "swallowed_ratio", "_reanalyse", "_referents",
]
