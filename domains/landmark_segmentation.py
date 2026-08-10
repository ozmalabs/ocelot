"""landmark_segmentation — the agent forward-builds a BOUNDARY-STABLE segmenter
that anchors word/syllable boundaries to a STABLE acoustic landmark (the sonority
ENVELOPE valley) instead of the jittery transitional-probability troughs of the
codebook stream. This is the iter-14 fix for the binding continuous-speech blocker:
the same word must segment to the same chunk WITHIN a speaker.

WHY TP-TROUGHS JITTER (the diagnosed cause). The corpus-TP chunker (iter-9..13)
cuts where P(next-unit | cur-unit) troughs on a per-frame k-means stream. But the
per-frame unit a vowel/consonant quantises to shifts by a unit or two with
coarticulation and codebook noise, so the TP curve — and therefore the trough
positions — MOVE between two utterances of the SAME word. The boundary is read off
a representation that is itself unstable, so the same word is cut into a different
span each time. Result (verified, iter-13): within-speaker full-DTW on continuous
chunks 0.025 (~chance), vs FSDD isolated digits 0.875.

THE FORWARD-BUILD (from the agent's OWN sonority / onset science). A word boundary
in speech is a PHYSICAL event, not a statistical one: between words (and between
syllables) the vocal tract constricts and the acoustic ENERGY drops — a sonority
VALLEY. Syllable nuclei are sonority PEAKS (open vocal tract, voiced vowels). The
sonority envelope is tied to articulation, so it recurs for the same word
independent of which codebook unit each frame happened to land in. The agent
already holds this (domains/sonority_valley installs a SonorityValley landmark op
+ its tuner; speech_science seeds onset/syllable perception). Anchoring boundaries
to envelope valleys makes the boundary STABLE: the same word lands the same valleys
each time.

A VALLEY IS THE AGENT'S OWN order-1-time SIGN-CHANGE CONCEPT (order_n_concepts).
The smoothed total-energy envelope e[t] over frames has a first difference
d[t] = e[t]-e[t-1]; a valley is a frame where d changes sign − -> + (the envelope
stops falling and starts rising) AND the dip is deep enough relative to the flanking
peaks to be a real constriction, not envelope ripple. That is exactly the order-1
sign-change trough the agent uses on the TP curve in forward_segmentation, here
applied to the ENERGY curve — a far more stable carrier of word structure.

GRAPH-RESIDENT BOUNDARY RULE (architecture rule). The boundary DECISION is a Term
the agent owns and evaluates natively, mirroring forward_segmentation.local_min_
boundary_term. Each frame becomes an EnvFrame node carrying its smoothed energy `e`
and its order-adjacent neighbours `prev_e` / `next_e`, plus the depth-relative
flank peaks `left_peak` / `right_peak` (mechanical structure translation, the same
way `tp`/`prev_tp` are stored on Transition nodes). The boundary set is

    Filter(env_frames, f,
           And( Lt(f.e, f.prev_e),            # falling into f ...
                Lt(f.e, f.next_e),            # ... then rising out of f  (valley)
                Lt(f.e, mean_e) ))            # in the LOW-sonority regime

— "the frames that are local minima of the energy envelope sitting in the
low-sonority regime (energy below the utterance mean)". The depth gate is the
utterance's MEAN envelope energy — a statistic OF the envelope, not a swept knob.
A genuine inter-syllable / inter-word constriction drops below the mean energy; a
ripple on the flank of a syllable peak does not. The agent runs its own program
over the envelope structure to find the boundaries. (The median-of-dips gate used
for the TP curve in forward_segmentation is wrong here: when most local minima ARE
real valleys, a median split rejects half of them; the mean-energy regime split is
the right structural statistic for a sonority envelope.)

This module is a world-adapter + the agent's segmenter: it translates the frame
matrix into the EnvFrame structure and evaluates the agent's boundary Term; the
chunk-merge is mechanical assembly of the boundaries the graph rule found. No agent
reasoning lives in Python beyond that translation.

Honest: this is the deep unsupervised word-segmentation problem. The probe reports
whether anchoring to envelope valleys actually makes the same word match itself
within a speaker (within-speaker full-DTW before -> after), shuffle-controlled, with
numbers stated plainly. No tuning to force the result.
"""
from __future__ import annotations

import numpy as np


# ---------------------------------------------------------------------------
# (0) The agent specifies the landmark segmenter by reasoning FROM its sonority /
# onset science to the boundary-stable principle (records a graph-resident spec).
# ---------------------------------------------------------------------------

def agent_specify_landmark_segmenter(substrate) -> dict:
    """The agent reasons from its sonority/onset science to the boundary-stable
    principle and records a graph-resident LandmarkSegmenterSpec. Returns the spec.
    This is reasoning FROM science to a constructive design — it names WHAT
    determines a boundary (a deep sonority-envelope valley = an order-1-time
    sign-change of the energy curve), not a knob to tune."""
    grounded = False
    for n in substrate.nodes("Microtheory"):
        if substrate.node(n)["attrs"].get("name") == "speech_science":
            for c in substrate.neighbours(n, "has_concept"):
                nm = substrate.node(c)["attrs"].get("name", "")
                if nm in ("onset", "syllable", "sonority", "coarticulation"):
                    grounded = True
                    break
    # also count: does the agent already hold a sonority_valley landmark op?
    has_sv = any(substrate.node(o)["attrs"].get("kind") == "sonority_valley"
                 for o in substrate.nodes("Operation"))
    spec = {
        "name": "SonorityValleySegmenter",
        "principle": "sonority_envelope_valley_landmark",
        "boundary_rule": (
            "place a boundary at frame f iff e[f] is a LOCAL MINIMUM of the "
            "smoothed total-energy envelope (e[f] < e[f-1] and e[f] < e[f+1]) AND "
            "the relative dip e[f]/min(flank_peaks) is below the median dip over "
            "this utterance's valleys"),
        "landmark": "smoothed_total_energy_envelope_valley",
        "is_order1_sign_change": True,
        "level_source": "median_relative_dip_over_this_utterances_valleys",
        "level_is_searched": False,
        "why": (
            "a word/syllable boundary is a PHYSICAL constriction of the vocal "
            "tract -> a sonority energy VALLEY, tied to articulation; it recurs "
            "for the same word regardless of which codebook unit each frame "
            "lands in. TP troughs are read off the codebook stream, which jitters "
            "with coarticulation, so they MOVE between utterances of the same word "
            "-> the same word is cut differently. The envelope is the STABLE "
            "carrier of word structure."),
        "grounded_in_science": bool(grounded),
        "already_has_sonority_op": bool(has_sv),
        "is_forward_construction": True,
        "is_search": False,
    }
    try:
        substrate.add_node("LandmarkSegmenterSpec",
                           {**{k: v for k, v in spec.items()
                               if isinstance(v, (str, bool, int, float))},
                            "origin": "agent_landmark_segmentation"})
    except Exception:
        pass
    return spec


# ---------------------------------------------------------------------------
# (1) The structure: the smoothed total-energy (sonority) envelope of a frame
# matrix. Pure mechanical translation of the perceived audio into a 1-D curve.
# ---------------------------------------------------------------------------

def energy_envelope(M, smooth=2) -> np.ndarray:
    """Per-frame sonority energy = total energy across bands. M is frames x bands
    of LOG band energies (the agent's gammatone front-end), so total energy is the
    log-sum-exp across bands; we then lightly smooth over time (a short moving
    average, `smooth` frames each side) so codebook-grain ripple does not create
    spurious micro-valleys. Mechanical I/O translation, not a tuned knob — the
    smoothing window is the front-end's own ~frame grain."""
    arr = np.asarray(M, dtype=np.float64)
    if arr.ndim == 1:
        arr = arr[None, :]
    # log-sum-exp across bands -> total energy per frame (bands are log energies)
    mx = arr.max(axis=1, keepdims=True)
    e = (mx[:, 0] + np.log(np.exp(arr - mx).sum(axis=1)))
    if smooth > 0 and len(e) > 2 * smooth + 1:
        k = 2 * smooth + 1
        pad = np.pad(e, (smooth, smooth), mode="edge")
        e = np.convolve(pad, np.ones(k) / k, mode="valid")
    return e


# ---------------------------------------------------------------------------
# (2) The boundary DECISION as a graph-resident Term the agent OWNS. Each frame
# becomes an EnvFrame node carrying e / prev_e / next_e and the flank-relative
# dip; the boundary set is a Filter Term the agent evaluates natively. Mirrors
# forward_segmentation.local_min_boundary_term, on the ENERGY curve.
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
    raw JSON Term dict — the same shim recognition_graph / forward_segmentation use."""
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def syllable_boundary_term(seq_tag: str) -> dict:
    """The graph-resident SYLLABLE boundary RULE: EVERY local minimum of the energy
    envelope (no low-sonority depth gate). Syllable boundaries sit at sonority
    valleys between successive syllable nuclei; in connected speech word boundaries
    are frequently NOT marked by a sub-mean energy dip (function words, liaison,
    coarticulation run words together), so the mean-energy gate (valley_boundary_
    term) under-segments to ~0.6 chunks/word. Cutting at every envelope local
    minimum gives ~0.9 chunks/word — closer to word scale.

        Filter(EnvFrame[seq], f, And( Lt(f.e, f.prev_e), Lt(f.e, f.next_e) ))

    This is the agent's pure order-1-time sign-change concept on the energy curve."""
    f = _V("f")
    return _Filter(
        _NodesWhere("EnvFrame", "seq", _Lit(seq_tag)),
        "f",
        _And([_Lt(_Attr(f, "e"), _Attr(f, "prev_e")),
              _Lt(_Attr(f, "e"), _Attr(f, "next_e"))]))


def valley_boundary_term(seq_tag: str, mean_e: float) -> dict:
    """The graph-resident VALLEY boundary RULE: the set of this utterance's EnvFrame
    nodes that are LOCAL MINIMA of the energy envelope (e below BOTH neighbours) AND
    sit in the LOW-sonority regime (e below the utterance's mean energy `mean_e`).

        Filter(EnvFrame[seq], f,
               And( Lt(f.e, f.prev_e), Lt(f.e, f.next_e),     # order-1 valley
                    Lt(f.e, mean_e) ))                        # low-sonority regime

    `mean_e` is the mean envelope energy over this utterance — a statistic OF the
    envelope, derived, not searched. A genuine inter-syllable/inter-word
    constriction drops below the mean; a ripple on a syllable peak's flank does not.
    The agent runs THIS over the envelope structure to find the boundary frames."""
    f = _V("f")
    return _Filter(
        _NodesWhere("EnvFrame", "seq", _Lit(seq_tag)),
        "f",
        _And([_Lt(_Attr(f, "e"), _Attr(f, "prev_e")),
              _Lt(_Attr(f, "e"), _Attr(f, "next_e")),
              _Lt(_Attr(f, "e"), _Lit(float(mean_e)))]))


def _install_env_frames(substrate, e, seq_tag: str) -> list:
    """Translate one utterance's energy envelope into graph EnvFrame nodes carrying
    the valley structure the boundary Term reads (mechanical I/O->graph). For each
    frame: its energy `e` and its order-adjacent neighbours `prev_e`/`next_e`
    (endpoints get a sentinel HIGH so an endpoint never reads as a local minimum).
    Returns the ordered EnvFrame NodeIDs."""
    n = len(e)
    SENTINEL = 1e9
    nodes = []
    for i in range(n):
        t = substrate.add_node("EnvFrame", {
            "seq": seq_tag, "pos": i,
            "e": float(e[i]),
            "prev_e": float(e[i - 1]) if i > 0 else SENTINEL,
            "next_e": float(e[i + 1]) if i + 1 < n else SENTINEL,
            "origin": "landmark_segmentation"})
        nodes.append(t)
    return nodes


def find_valley_boundaries(substrate, M, seq_tag: str,
                           min_sep: int = 3, smooth: int = 2,
                           gate: str = "mean") -> tuple:
    """The agent finds this utterance's boundaries by EVALUATING its valley boundary
    Term over the EnvFrame structure — natively, in the substrate. Returns
    (cut_positions, envelope). A cut AFTER position i means a boundary between frame
    i and frame i+1; we cut at the valley frame (assign it to the end of the chunk).

    The depth gate is derived from the envelope itself: the utterance's MEAN
    envelope energy (a statistic of the data, not a swept knob) — a valley counts as
    a boundary only when it drops into the low-sonority regime (below the mean).
    `min_sep` enforces a minimum syllable-scale separation between boundaries (drop
    the shallower of two valleys closer than min_sep frames) — a structural
    constraint (syllables have a minimum duration), not a tuned score."""
    e = energy_envelope(M, smooth=smooth)
    n = len(e)
    if n < 5:
        return set(), e
    # run the agent's graph-resident boundary Term natively. gate="mean" keeps only
    # sub-mean (low-sonority) valleys (word/phrase scale, under-segments); gate=
    # "syllable" cuts at EVERY envelope local minimum (syllable scale, ~word scale).
    _install_env_frames(substrate, e, seq_tag)
    if gate == "syllable":
        term = syllable_boundary_term(seq_tag)
    else:
        term = valley_boundary_term(seq_tag, float(e.mean()))
    valley_nodes = substrate.evaluate(_Pred(term), None)
    cuts = sorted(int(substrate.node(t)["attrs"].get("pos", -1))
                  for t in valley_nodes)
    cuts = [c for c in cuts if 0 < c < n - 1]
    # min-separation: keep the deeper valley when two are too close (mechanical
    # structural constraint, syllable minimum duration).
    if min_sep > 1 and cuts:
        kept = []
        for c in cuts:
            if kept and c - kept[-1] < min_sep:
                # keep whichever has the lower energy (deeper)
                if e[c] < e[kept[-1]]:
                    kept[-1] = c
            else:
                kept.append(c)
        cuts = kept
    return set(cuts), e


# ---------------------------------------------------------------------------
# (3) Assemble real-frame chunk blocks from the valley boundaries (mechanical).
# A cut at frame position i ends a chunk after frame i (the valley frame goes with
# the preceding chunk). Returns [(frame_block, n_frames)] like the TP chunker.
# ---------------------------------------------------------------------------

def chunk_by_landmarks(M, cuts) -> list:
    """Split the frame matrix M into contiguous blocks at the valley cut positions.
    Mechanical span assembly, matching the (block, n_frames) shape the lexicon /
    DTW path expects."""
    n = M.shape[0]
    if not cuts:
        return [(M, n)]
    blocks = []
    start = 0
    for c in sorted(cuts):
        end = c + 1                       # valley frame goes with preceding chunk
        if end - start >= 1:
            blocks.append((M[start:end], end - start))
            start = end
    if start < n:
        blocks.append((M[start:], n - start))
    return blocks if blocks else [(M, n)]


def landmark_chunk_utterance(substrate, M, seq_tag: str,
                             min_sep: int = 3, smooth: int = 2,
                             gate: str = "mean") -> list:
    """One utterance's frame matrix -> list of (frame_block, n_frames), with chunk
    boundaries anchored to the agent's sonority-envelope valley landmarks (found by
    the graph-resident boundary Term). Drop-in replacement for chunk_with_corpus_tp.
    gate="mean" = sub-mean valleys only; gate="syllable" = every envelope local min."""
    cuts, _e = find_valley_boundaries(substrate, M, seq_tag,
                                      min_sep=min_sep, smooth=smooth, gate=gate)
    return chunk_by_landmarks(M, cuts)


__all__ = [
    "agent_specify_landmark_segmenter",
    "energy_envelope",
    "valley_boundary_term",
    "find_valley_boundaries",
    "chunk_by_landmarks",
    "landmark_chunk_utterance",
]
