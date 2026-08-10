"""forward_segmentation — the agent DESIGNS FORWARD a word-segmenter from the
transitional-probability STRUCTURE of its own sub-word units. NOT search.

THE PRINCIPLE (do not violate it). This is constructive, not optimisation. The
agent does not sweep thresholds and keep the best-scoring one — that is ML
optimisation, the agent as a tuned knob, FORBIDDEN here. Instead the structure of
the data DETERMINES the segmentation: where transitional probability TROUGHS, a
word boundary is; the high-TP runs between troughs ARE the words. Compression is
the SELECTOR/quality-check run AFTER the agent has built — never the search.

THE SCIENCE the agent reasons from (its own flagged gap). The agent assessed its
speech system and named `statistical_learning` / `distributional_learning_of_
categories` as a gap (domains/speech_science.assess_speech_system). That gap IS
the infant word-segmentation mechanism (Saffran, Aslin & Newport 1996): inside a
word the next sub-unit is highly predictable (high transitional probability,
TP = P(next | cur)); ACROSS a word boundary it is not (TP drops). So the TP
structure of the agent's sub-word units constructively says where the words are.

FORWARD CONSTRUCTION (the build, bottom-up like an infant / like BPE):
  1. Read the agent's ordered sub-word unit sequences (its perception).
  2. Estimate TP = P(next | cur) from the bigram counts (the structure).
  3. Place a boundary where TP TROUGHS — below a level DERIVED FROM the
     distribution itself: the running median of the observed TP values. The
     median is a statistic of the data's own distribution, NOT a free knob that
     gets swept; there is one structure-derived level, computed, never searched.
  4. Merge the high-TP runs between troughs into CHUNKS (proto-words).
  5. Iterate: chunks become the new alphabet; re-estimate TP; chunk again —
     building the lexicon UP from the structure, the constructive bottom-up build.

GRAPH-RESIDENT BOUNDARY RULE (architecture rule). The boundary DECISION is not a
Python `if`. It is a Term the agent owns and evaluates natively (mirroring
domains/recognition_graph): the ordered adjacent unit-pairs of a sequence become
`Transition` nodes carrying a `tp` attr; the boundary set is

    Filter(transitions, t, Lt(Attr(t, "tp"), Lit(level)))

— "the transitions whose TP is below the structure-derived level". The agent runs
its own program over the transition structure to find the troughs. The structure
lives as graph data; the rule is graph data; Python only translates I/O and
computes the distributional statistic that parameterises the rule.

This module is the world-adapter + the agent's constructive segmenter. The
boundary decision runs in the substrate; the chunk-merge is mechanical assembly of
the boundaries the graph rule found. No agent reasoning lives in Python beyond
that translation.

Honest: real continuous-speech TP is noisy. The demo script reports whether
forward construction actually discovers word-like units (fewer, longer, recurring;
compresses better; lands on real word boundaries) or whether the TP structure is
too noisy — with numbers, stated plainly. No tuning to force the result.
"""
from __future__ import annotations

import math
from collections import defaultdict


# ---------------------------------------------------------------------------
# (0) The agent reasons FORWARD from its statistical_learning science to the
# boundary principle — the same move as runtime_design.agent_specify_primitive.
# ---------------------------------------------------------------------------

def agent_specify_segmenter(substrate) -> dict:
    """The agent reasons from its OWN flagged science gap (statistical_learning)
    to the constructive boundary principle, and specifies the segmenter. Records a
    graph-resident `SegmenterSpec`. Returns the spec.

    This is reasoning FROM science to a constructive design, not a parameter
    search: the spec names WHAT determines a boundary (a TP trough below the
    distribution's own running median), not a knob to tune.
    """
    # Does the agent hold the statistical_learning science it needs?
    grounded = False
    mt = next((n for n in substrate.nodes("Microtheory")
               if substrate.node(n)["attrs"].get("name") == "speech_science"),
              None)
    if mt is not None:
        for c in substrate.neighbours(mt, "has_concept"):
            nm = substrate.node(c)["attrs"].get("name", "")
            if nm in ("statistical_learning",
                      "distributional_learning_of_categories"):
                grounded = True
                break
    spec = {
        "name": "TpTroughSegmenter",
        "principle": "transitional_probability_trough",
        "boundary_rule": (
            "place a boundary at adjacent unit-pair (cur, nxt) iff "
            "TP(nxt|cur) < running_median(TP) — a TROUGH below the level the "
            "TP distribution itself sets"),
        "level_source": "running_median_of_observed_TP",
        "level_is_searched": False,
        "why": (
            "inside a word the next sub-unit is predictable (high TP); across a "
            "word boundary it is not (TP drops). So the TP structure of my "
            "sub-word units CONSTRUCTIVELY says where the words are. The "
            "threshold is not a free knob — it is the median of my own TP "
            "distribution, a statistic OF the structure."),
        "construction": (
            "merge high-TP runs between troughs into chunks (proto-words); "
            "iterate — chunks become the new alphabet, re-estimate TP, chunk "
            "again — building the lexicon UP from the structure (bottom-up, "
            "like an infant / like BPE)"),
        "grounded_in_science": bool(grounded),
        "is_forward_construction": True,
        "is_search": False,
    }
    try:
        substrate.add_node("SegmenterSpec",
                           {**{k: v for k, v in spec.items()
                               if isinstance(v, (str, bool, int, float))},
                            "origin": "agent_forward_segmentation"})
    except Exception:
        pass
    return spec


# ---------------------------------------------------------------------------
# (1) The structure: TP = P(next | cur) from the bigram counts.
# ---------------------------------------------------------------------------

def estimate_tp(sequences) -> dict:
    """TP[(cur, nxt)] = count(cur, nxt) / count(cur, *). The transitional-
    probability structure of the unit stream — the thing the boundaries are read
    off. Pure statistics over the agent's perceived sequences."""
    pair = defaultdict(int)
    cur_total = defaultdict(int)
    for seq in sequences:
        for a, b in zip(seq, seq[1:]):
            pair[(a, b)] += 1
            cur_total[a] += 1
    tp = {}
    for (a, b), c in pair.items():
        tp[(a, b)] = c / cur_total[a]
    return tp


def estimate_bidirectional_tp(sequences) -> dict:
    """BOND[(cur, nxt)] = min(P(nxt|cur), P(cur|nxt)) — the SYMMETRIC transitional bond.
    Within a word the pair is predictable BOTH ways (high min); across a boundary it is
    loose in at least one direction (low min). The dual-direction reading of the SAME TP
    structure — still a statistic OF the data, not a swept knob — that suppresses the
    false IN-WORD cuts the forward-only TP makes when units are SHARED across words.
    Validated +0.06..+0.11 token-F1 over forward-only on the Saffran paradigm
    (scripts/segmentation_saffran.py); ties the clean (distinct-unit) case at 1.0."""
    pair = defaultdict(int)
    cur_total = defaultdict(int)
    nxt_total = defaultdict(int)
    for seq in sequences:
        for a, b in zip(seq, seq[1:]):
            pair[(a, b)] += 1
            cur_total[a] += 1
            nxt_total[b] += 1
    bond = {}
    for (a, b), c in pair.items():
        fwd = c / cur_total[a]            # P(nxt | cur)
        bwd = c / nxt_total[b]            # P(cur | nxt)
        bond[(a, b)] = min(fwd, bwd)
    return bond


def _median(values) -> float:
    """The structure-derived boundary level: the median of the observed TP
    distribution. A statistic OF the data, not a swept knob."""
    vs = sorted(values)
    n = len(vs)
    if n == 0:
        return 0.0
    m = n // 2
    return vs[m] if n % 2 else 0.5 * (vs[m - 1] + vs[m])


# ---------------------------------------------------------------------------
# (2) The boundary DECISION as a graph-resident Term the agent OWNS.
# The TP structure of one sequence becomes Transition nodes; the boundary set
# is a Filter Term the agent evaluates natively. Mirrors recognition_graph.
# ---------------------------------------------------------------------------

def _V(n): return {"type": "Var", "name": n}
def _Lit(v): return {"type": "Lit", "value": v}
def _Attr(node, k): return {"type": "Attr", "node": node, "key": k}
def _Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def _And(items): return {"type": "And", "items": list(items)}
def _NodesWhere(t, k, v): return {"type": "NodesWhere", "node_type": t,
                                  "attr_key": k, "value": v}
def _Filter(src, var, pred): return {"type": "Filter", "source": src,
                                     "var_name": var, "predicate": pred}


class _Pred:
    """Tiny Term wrapper so substrate.evaluate (which unwraps `._json`) accepts a
    raw JSON Term dict — same shim recognition_graph uses."""
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def boundary_term(seq_tag: str, level: float) -> dict:
    """The graph-resident boundary RULE: the set of this sequence's Transition
    nodes whose TP is below the structure-derived `level` (a TP trough).

        Filter(NodesWhere(Transition, seq, <tag>), t, Lt(Attr(t, tp), level))

    The agent runs THIS over the transition structure to find the troughs. `level`
    is the running median of the TP distribution — derived, not searched."""
    return _Filter(
        _NodesWhere("Transition", "seq", _Lit(seq_tag)),
        "t",
        _Lt(_Attr(_V("t"), "tp"), _Lit(float(level))))


def local_min_boundary_term(seq_tag: str) -> dict:
    """The graph-resident LOCAL-MINIMUM boundary RULE — the agent's forward-built
    fix for the median rule's ~8x over-segmentation.

        Filter(transitions, t, And(Lt(t.tp, t.prev_tp), Lt(t.tp, t.next_tp)))

    THE SCIENCE (the SAME statistical_learning gap, read more faithfully). Saffran,
    Aslin & Newport: a word boundary is where predictability DROPS — a local DIP in
    TP, not merely any below-average transition. The median rule cuts at every
    below-median transition (= ~half of ALL transitions, hence ~8 cuts per word on a
    per-frame stream). A genuine TROUGH is a LOCAL MINIMUM: TP lower than BOTH its
    neighbours. This is exactly the agent's own order-1 sign-change concept (a dip is
    where the first difference changes sign), the order_n_concepts mechanism applied
    to the TP curve. Far fewer boundaries -> word-scale chunks.

    The DECISION is graph-resident (a Term evaluated natively); `prev_tp`/`next_tp`
    are mechanical structure translation (stored on each Transition the same way `tp`
    is). Sequence-end transitions get a sentinel-high prev/next so they never fire."""
    t = _V("t")
    return _Filter(
        _NodesWhere("Transition", "seq", _Lit(seq_tag)),
        "t",
        _And([_Lt(_Attr(t, "tp"), _Attr(t, "prev_tp")),
              _Lt(_Attr(t, "tp"), _Attr(t, "next_tp"))]))


def local_min_below_median_boundary_term(seq_tag: str, level: float) -> dict:
    """The graph-resident PROMINENT-TROUGH boundary RULE — the AND of the agent's
    two existing structure-derived boundary terms, no new knob:

        Filter(transitions, t,
               And(Lt(t.tp, t.prev_tp), Lt(t.tp, t.next_tp),    # local_min: a dip
                   Lt(t.tp, level)))                            # median: globally low

    THE SCIENCE (both halves of the agent's own statement). A word boundary is where
    predictability DROPS — "a local DIP in TP" (local_min) AND below "the level the
    TP distribution itself sets" (the running median). local_min ALONE cuts at every
    micro-dip, which on a FINE grid (100 fps -> many shallow within-word wiggles)
    over-segments to syllable/sub-word scale; the median condition keeps only the
    PROMINENT dips (those also below the distribution's own median), pulling the cut
    rate to word scale. This composes the agent's two designed terms — it adds no
    swept parameter; `level` is the same running-median statistic OF the structure."""
    t = _V("t")
    return _Filter(
        _NodesWhere("Transition", "seq", _Lit(seq_tag)),
        "t",
        _And([_Lt(_Attr(t, "tp"), _Attr(t, "prev_tp")),
              _Lt(_Attr(t, "tp"), _Attr(t, "next_tp")),
              _Lt(_Attr(t, "tp"), _Lit(float(level)))]))


def _install_transitions(substrate, seq, tp, seq_tag: str) -> list:
    """Translate one unit sequence into graph Transition nodes carrying the TP
    structure (mechanical I/O->graph). Each Transition is the adjacent pair at
    position i; `pos` preserves order, `tp` is its transitional probability.
    Returns the ordered Transition NodeIDs."""
    try:
        substrate.add_production({
            "src": {"type": "Transition", "var": "a"},
            "edge_type": "in_seq",
            "tgt": {"type": "UnitSeq", "var": "b"},
            "provenance": "forward_segmentation:transition"})
    except Exception:
        pass
    pairs = list(zip(seq, seq[1:]))
    tps = [float(tp.get((a, b), 0.0)) for (a, b) in pairs]
    # prev_tp / next_tp let the local-minimum boundary Term compare a transition to
    # its order-adjacent neighbours natively (scalar attrs, the same mechanical
    # structure translation as `tp`). Sequence ends get a sentinel HIGH value so an
    # endpoint never reads as a local minimum (a boundary at the very edge is moot).
    SENTINEL = 1e9
    nodes = []
    for i, (a, b) in enumerate(pairs):
        t = substrate.add_node("Transition", {
            "seq": seq_tag, "pos": i,
            "cur": _keystr(a), "nxt": _keystr(b),
            "tp": tps[i],
            "prev_tp": tps[i - 1] if i > 0 else SENTINEL,
            "next_tp": tps[i + 1] if i + 1 < len(tps) else SENTINEL,
            "origin": "forward_segmentation"})
        nodes.append(t)
    return nodes


def _keystr(k):
    """Stable string form of a unit key (ints stay ints-as-str; tuples join)."""
    if isinstance(k, tuple):
        return "+".join(str(x) for x in k)
    return str(k)


def find_boundaries_via_graph(substrate, seq, tp, level, seq_tag: str,
                              boundary_mode: str = "median") -> set:
    """The agent finds this sequence's word boundaries by EVALUATING its own
    boundary Term over the transition structure — natively, in the substrate. NOT
    a Python loop of comparisons: the decision is graph-resident. Returns the set
    of boundary positions (a boundary AFTER position i means cut between unit i and
    unit i+1).

    boundary_mode selects WHICH graph-resident boundary Term the agent evaluates:
      • "median"    — cut at every below-running-median transition (original; cuts
                      ~half of all transitions -> ~8x over-segmentation per word).
      • "local_min" — cut only at LOCAL MINIMA of TP (a genuine trough: TP below
                      BOTH neighbours). The agent's order-1 sign-change concept on
                      the TP curve. On a FINE grid (100 fps) this still cuts at every
                      micro-dip -> syllable-scale over-segmentation.
      • "prominent"  — cut at local minima that are ALSO below the running median
                      (the AND of the agent's local_min and median terms). Keeps only
                      PROMINENT troughs -> word-scale on the fine grid. Grid-robust.
    """
    _install_transitions(substrate, seq, tp, seq_tag)
    sub = substrate
    if boundary_mode == "local_min":
        term = local_min_boundary_term(seq_tag)
    elif boundary_mode == "prominent":
        term = local_min_below_median_boundary_term(seq_tag, level)
    else:
        term = boundary_term(seq_tag, level)
    try:
        trough_nodes = sub.evaluate(_Pred(term), None)
    except Exception:
        # If native eval is unavailable, the structure is still in the graph;
        # surface the failure rather than silently falling back to Python logic.
        raise
    cuts = set()
    for t in trough_nodes:
        cuts.add(int(sub.node(t)["attrs"].get("pos", -1)))
    cuts.discard(-1)
    return cuts


# ---------------------------------------------------------------------------
# (3) Merge high-TP runs between troughs into chunks (mechanical assembly of the
# boundaries the graph rule found). Then iterate (BPE-like) over chunks.
# ---------------------------------------------------------------------------

def chunk_sequence(seq, cuts) -> list:
    """Assemble chunks from boundary positions. A cut at position i ends a chunk
    after unit i. Each chunk is a tuple of the units it spans. Mechanical."""
    chunks = []
    cur = []
    for i, u in enumerate(seq):
        cur.append(u)
        if i in cuts:            # boundary AFTER unit i
            chunks.append(tuple(cur))
            cur = []
    if cur:
        chunks.append(tuple(cur))
    return chunks


_MODE_CODE = {"median": 0, "local_min": 1, "prominent": 2}


def _native_segment(sequences, boundary_mode: str, bidirectional: bool):
    """Fast path: the agent's segmenter COMPILED to a native primitive
    (substrate_rs._native.segment_units) — the same statistical-learning TP-bond
    structure, the same boundary rule, run in Rust. Returns the chunked sequences
    (list per seq of unit-tuples), or None when the primitive is unavailable or the
    alphabet is not integer-coded (later BPE passes chunk over chunk-symbols, not
    ints — those stay on the graph-resident Term path). The boundary DECISION is
    still the agent's: this primitive computes exactly what the boundary Terms
    define (gated bit-for-bit in scripts/segmenter_native_gate.py)."""
    int_seqs = []
    for seq in sequences:
        s = []
        for u in seq:
            if isinstance(u, bool) or not isinstance(u, int):
                return None
            s.append(int(u))
        int_seqs.append(s)
    try:
        from substrate_rs import _native
        lens = _native.segment_units(int_seqs, bool(bidirectional),
                                     _MODE_CODE.get(boundary_mode, 0))
    except Exception:
        return None
    chunked = []
    for seq, ls in zip(sequences, lens):
        chunks, pos = [], 0
        for ln in ls:
            chunks.append(tuple(seq[pos:pos + ln])); pos += ln
        chunked.append(chunks)
    return chunked


def segment_pass(substrate, sequences, pass_id: int = 0,
                 boundary_mode: str = "median", bidirectional: bool = True) -> dict:
    """One forward pass: estimate TP over the current alphabet, derive the level
    (running median of TP), find troughs via the graph boundary Term, merge runs
    into chunks. Returns the chunked sequences (each a list of chunk-tuples) + the
    level used + the trough boundary positions. boundary_mode picks the boundary
    Term (see find_boundaries_via_graph).

    `bidirectional` (default True): the transition `tp` is the SYMMETRIC bond
    min(P(nxt|cur), P(cur|nxt)) — the validated upgrade over forward-only TP. The
    boundary Terms are unchanged; only the structure they read is the richer bond.
    """
    tp = (estimate_bidirectional_tp(sequences) if bidirectional
          else estimate_tp(sequences))
    level = _median(tp.values())          # the distribution sets its own level

    # Fast path: the agent's segmenter compiled to a native primitive (same TP-bond
    # structure, same boundary rule, in Rust). The graph-resident Term path below is
    # the definition + the fallback when the primitive is absent / units are non-int.
    nat = _native_segment(sequences, boundary_mode, bidirectional)
    if nat is not None:
        return {"chunked": nat, "level": level, "tp": tp,
                "boundary_counts": [max(len(ch) - 1, 0) for ch in nat]}

    chunked = []
    boundary_counts = []
    for j, seq in enumerate(sequences):
        if len(seq) < 2:
            chunked.append([tuple(seq)] if seq else [])
            boundary_counts.append(0)
            continue
        tag = f"p{pass_id}_s{j}"
        cuts = find_boundaries_via_graph(substrate, seq, tp, level, tag,
                                         boundary_mode=boundary_mode)
        chunked.append(chunk_sequence(seq, cuts))
        boundary_counts.append(len(cuts))
    return {"chunked": chunked, "level": level, "tp": tp,
            "boundary_counts": boundary_counts}


def forward_segment(substrate, sequences, n_passes: int = 2,
                    boundary_mode: str = "median", bidirectional: bool = True) -> dict:
    """The full constructive build: iterate segment_pass, each pass treating the
    previous pass's chunks as the new alphabet (bottom-up, BPE-like). Returns the
    final chunked sequences + per-pass stats.

    Each pass: re-estimate TP over the new (chunk) alphabet -> derive the median
    level -> graph boundary rule finds troughs -> merge runs. The lexicon grows UP
    from the structure across passes. boundary_mode ("median"|"local_min") picks
    which graph-resident boundary Term each pass evaluates (see
    find_boundaries_via_graph): local_min cuts only at genuine TP troughs and is the
    agent's forward-built fix for median's ~8x over-segmentation.
    """
    # Pass 0 runs on the raw sub-word units; subsequent passes flatten the
    # previous pass's chunks into a sequence of chunk-symbols and chunk THOSE.
    passes = []
    cur_seqs = sequences
    final_chunked = None
    prev_chunked = None
    for p in range(n_passes):
        # STRUCTURAL STOPPING CONDITION (not a tuned knob): a pass can only read
        # troughs if the TP distribution is NON-DEGENERATE. When almost every
        # transition occurs once (the chunk alphabet has gone sparse), TP -> 1.0
        # for nearly all pairs and the median collapses to the max — there is no
        # trough structure left to read. The structure ITSELF says "stop"; we
        # keep the previous pass's chunks rather than cut everywhere. We detect
        # this from the TP distribution before committing the pass.
        tp_now = (estimate_bidirectional_tp(cur_seqs) if bidirectional
                  else estimate_tp(cur_seqs))
        if p > 0 and tp_now:
            mx = max(tp_now.values())
            med_now = _median(tp_now.values())
            # degenerate: the median is already at the ceiling -> no troughs.
            if med_now >= mx - 1e-9:
                passes.append({
                    "pass": p, "level": med_now,
                    "n_sequences": len(cur_seqs),
                    "total_boundaries": 0,
                    "alphabet_size": len({u for s in cur_seqs for u in s}),
                    "stopped": "degenerate_TP_no_trough_structure",
                })
                final_chunked = prev_chunked
                break
        res = segment_pass(substrate, cur_seqs, pass_id=p,
                           boundary_mode=boundary_mode, bidirectional=bidirectional)
        prev_chunked = final_chunked
        final_chunked = res["chunked"]
        passes.append({
            "pass": p,
            "level": res["level"],
            "n_sequences": len(cur_seqs),
            "total_boundaries": sum(res["boundary_counts"]),
            "alphabet_size": len({u for s in cur_seqs for u in s}),
        })
        # Next pass's alphabet = this pass's chunk-symbols (each chunk-tuple is one
        # symbol). The next-level sequence is the list of those chunk-symbols.
        cur_seqs = [[c for c in chunks] for chunks in final_chunked]
        # Stop early if no more merging happens (chunks == alphabet already).
        if res["boundary_counts"] and \
                all(bc == 0 for bc in res["boundary_counts"]):
            break
    return {"chunked": final_chunked, "passes": passes}


# ---------------------------------------------------------------------------
# (4) The honest SELECTOR — compression — computed AFTER the agent built.
# Never used to search; only to check whether the construction discovered
# word-like (more compressible) units.
# ---------------------------------------------------------------------------

def description_length_bits(sequences) -> dict:
    """Two-part MDL description length (bits) of a token stream:
      model  = bits to name the lexicon (|lex| * log2|lex|, the codebook), and
      data   = sum over tokens of -log2 P(token)  (the unigram code length).
    Lower total = the stream is more compressible = the units are more word-like
    (fewer, recurring symbols carry the stream). This is the SELECTOR, computed
    once AFTER construction — not a knob the build optimised against."""
    counts = defaultdict(int)
    total = 0
    for seq in sequences:
        for tok in seq:
            counts[_keystr(tok)] += 1
            total += 1
    if total == 0:
        return {"bits_total": 0.0, "bits_per_token": 0.0,
                "n_tokens": 0, "lexicon": 0}
    lex = len(counts)
    data_bits = 0.0
    for c in counts.values():
        p = c / total
        data_bits += c * (-math.log2(p))
    model_bits = lex * math.log2(max(lex, 2))
    bits_total = data_bits + model_bits
    return {"bits_total": bits_total,
            "bits_per_token": bits_total / total,
            "data_bits_per_token": data_bits / total,
            "n_tokens": total, "lexicon": lex}


def chunk_stats(chunked) -> dict:
    """Word-likeness of the constructed chunks: count, mean length, recurrence."""
    all_chunks = [c for seq in chunked for c in seq]
    n = len(all_chunks)
    if n == 0:
        return {"n_chunks": 0, "mean_len": 0.0, "distinct": 0,
                "recurrence": 0.0}
    keys = [_keystr(c) for c in all_chunks]
    seen = set()
    repeat = 0
    for k in keys:
        if k in seen:
            repeat += 1
        else:
            seen.add(k)
    mean_len = sum(len(c) for c in all_chunks) / n
    return {"n_chunks": n, "mean_len": mean_len,
            "distinct": len(seen), "recurrence": repeat / n}


__all__ = [
    "agent_specify_segmenter",
    "estimate_tp",
    "estimate_bidirectional_tp",
    "boundary_term",
    "local_min_boundary_term",
    "local_min_below_median_boundary_term",
    "find_boundaries_via_graph",
    "chunk_sequence",
    "segment_pass",
    "forward_segment",
    "description_length_bits",
    "chunk_stats",
]
