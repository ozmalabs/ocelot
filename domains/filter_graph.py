"""filter_graph — the speech FRONT END as a GRAPH OF CONNECTABLE FILTERS.

THE ARCHITECTURE (the user's correction): the front end is NOT a fixed pipeline.
It is the substrate applied to PERCEPTION — a typed graph whose NODES are filters
({input_type -> output_type, op}) and whose EDGES are admissible connections.  Gamma
governs which output type may connect to which input (type-compatibility); the AGENT
composes + wires the graph (and may route per input, weight a fan-in, or add a
feedback / collapse edge).  The agent already composes Term-trees (graphs of ops) for
all its cognition; this applies that same native capability to its OWN front end,
the one place it had run a fixed pipeline.

A FilterNode is exactly the substrate idea, one level up: instead of an op over
attribute values it is an op over whole REPRESENTATIONS (signal -> trajectory ->
stabilized trajectory -> relational shape).  Weighting (fan-in) and chaining (path)
are both special cases of the graph (a chain is a path; a weighting is a fan-in node).

TYPES (the Gamma alphabet at the front-end level):
  SIGNAL          : 1-D waveform (np.float32, the clip)
  BAND_TRAJ       : frames x bands gammatone band-energy trajectory
  POLE_TRAJ       : frames x 6 raw LPC pole/formant trajectory (jittery)
  POLE_TRAJ_STABLE: frames x 6 STABILIZED pole/formant trajectory (de-jittered)
  REL_SHAPE       : frames x D whole-unit relational shape (DtwTo-ready readout)

Gamma admits an edge u -> v iff u.output_type == v.input_type.  A DANGLING node is
one whose input_type has no incoming producer in the wired graph: that is exactly
what REL-FILTER was (a RELATIONAL_RANK reading POLE_TRAJ with NO stabilizer between
the jittery poles and the relational ranking).

THE NODES (all from OWNED ops — primitives at the I/O boundary, relational/recognition
composition native):
  SIGNAL            source node (the clip)
  GAMMATONE         SIGNAL -> BAND_TRAJ   (band_trajectory_matrix, owned gammatone)
  LPC_POLES         SIGNAL -> POLE_TRAJ   (lpc_formants_bw per frame; filter_relational
                                           .formant_trajectory)
  DEJITTER          POLE_TRAJ -> POLE_TRAJ_STABLE   (THE NEW NODE, below)
  RELATIONAL_RANK   BAND_TRAJ|POLE_TRAJ|POLE_TRAJ_STABLE -> REL_SHAPE
                      (domains.relational_shape.relational_shape — ordinal rank +
                       whole-unit self-similarity, native eval; dimension-agnostic so
                       it consumes bands OR poles)
  DTW_READOUT       REL_SHAPE | BAND_TRAJ -> the native DtwTo nearest-exemplar score

The agent WIRES different graphs by connecting nodes:
  BAND PATH       SIGNAL -> GAMMATONE -> RELATIONAL_RANK -> DTW_READOUT     (REL-BAND)
  FILTER DANGLING SIGNAL -> LPC_POLES -> RELATIONAL_RANK -> DTW_READOUT     (REL-FILTER, B)
  FILTER WIRED    SIGNAL -> LPC_POLES -> DEJITTER -> RELATIONAL_RANK -> DTW_READOUT (C)
The only difference between B and C is the WIRED de-jitter EDGE — demonstrating the
graph composes, not a hardcoded route.

DISCIPLINE: filters = owned ops at the I/O boundary or native Terms; the relational
composition is reused verbatim from domains/relational_shape (native eval); the
de-jitter is built from OWNED pieces (in-order formant assignment + temporal median +
order_n velocity / continuity from domains/order_n_concepts).  Recognition stays the
native DtwTo Term.  No .fit / net / sweep.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

import numpy as np

import substrate_rs._native as N
from substrate_rs import Substrate
from domains.relational_shape import relational_shape
from domains.filter_relational import (formant_trajectory,
                                       cepstral_formant_trajectory,
                                       LPC_ORDER, LPC_FRAME,
                                       LPC_HOP, LPC_PE, N_FORMANT, F_LO, F_HI,
                                       BW_MAX, RMS_GATE_FRAC)
from domains.order_n_concepts import total_variation_term
from substrate_rs import Attr, Var


# ---------------------------------------------------------------------------
# Gamma type alphabet for the front-end graph.
# ---------------------------------------------------------------------------
SIGNAL = "SIGNAL"
BAND_TRAJ = "BAND_TRAJ"
POLE_TRAJ = "POLE_TRAJ"
POLE_TRAJ_STABLE = "POLE_TRAJ_STABLE"
REL_SHAPE = "REL_SHAPE"


@dataclass
class FilterNode:
    """A front-end filter: an op carrying a typed input -> output contract.

    The op maps a representation to a representation (or None on failure, which
    flows through the graph as a dropped clip — the same convention the probes use).
    A SOURCE node (input_type is None) emits the clip itself."""
    name: str
    input_type: Optional[str]
    output_type: str
    op: Callable[[np.ndarray], Optional[np.ndarray]]


@dataclass
class FilterGraph:
    """A wired graph of FilterNodes.  The agent ADDS nodes and CONNECTS them; Gamma
    (type-compatibility) admits or rejects each edge.  Evaluation flows a clip through
    the wired path to a final REL_SHAPE / BAND_TRAJ the native DtwTo recognises."""
    nodes: Dict[str, FilterNode] = field(default_factory=dict)
    # edge: producer_name -> consumer_name (admissible iff types match)
    edges: List[tuple] = field(default_factory=list)

    # -- composition (the agent's wiring) -----------------------------------
    def add(self, node: FilterNode) -> "FilterGraph":
        self.nodes[node.name] = node
        return self

    def connect(self, producer: str, consumer: str) -> "FilterGraph":
        """Wire producer.output -> consumer.input.  GAMMA CHECK: the edge is
        admissible only if the producer's output type equals the consumer's input
        type.  Refuses an inadmissible wire (e.g. POLE_TRAJ into a BAND_TRAJ input)."""
        u, v = self.nodes[producer], self.nodes[consumer]
        if u.output_type != v.input_type:
            raise TypeError(
                f"Gamma rejects edge {producer}({u.output_type}) -> "
                f"{consumer}({v.input_type}): type mismatch")
        self.edges.append((producer, consumer))
        return self

    # -- structure queries ---------------------------------------------------
    def _producers_of(self, name: str) -> List[str]:
        return [u for (u, v) in self.edges if v == name]

    def dangling(self) -> List[str]:
        """Nodes whose input_type has no incoming producer = unfed inputs.  REL-FILTER
        dangling = a RELATIONAL_RANK fed POLE_TRAJ with NO producer of the stabilized
        type it actually needs (it was reading raw jittery poles directly)."""
        out = []
        for name, nd in self.nodes.items():
            if nd.input_type is None:
                continue
            if not self._producers_of(name):
                out.append(name)
        return out

    def _topo_path_to(self, sink: str) -> List[str]:
        """Linear order of nodes feeding `sink` (the graphs here are paths/fan-ins to
        one readout; a simple DFS over producer edges suffices)."""
        order: List[str] = []
        seen = set()

        def visit(n: str):
            if n in seen:
                return
            seen.add(n)
            for p in self._producers_of(n):
                visit(p)
            order.append(n)

        visit(sink)
        return order

    # -- evaluation (flow a clip through the wired graph) -------------------
    def evaluate(self, sink: str, signal: np.ndarray, fs: int) -> Optional[np.ndarray]:
        """Flow `signal` through the wired graph to `sink`, returning the sink's
        output representation (a frames x D trajectory the DtwTo readout matches over),
        or None if any node drops the clip.  A SOURCE node emits the signal; every
        other node applies its op to its (single) producer's output."""
        cache: Dict[str, Optional[np.ndarray]] = {}
        for name in self._topo_path_to(sink):
            nd = self.nodes[name]
            if nd.input_type is None:               # SOURCE
                cache[name] = nd.op(signal, fs) if _takes_fs(nd.op) else signal
                continue
            prods = self._producers_of(name)
            if not prods:                            # dangling -> no input
                cache[name] = None
                continue
            x = cache.get(prods[0])
            if x is None:
                cache[name] = None
                continue
            cache[name] = nd.op(x, fs) if _takes_fs(nd.op) else nd.op(x)
        return cache.get(sink)

    def describe(self, sink: str) -> str:
        order = self._topo_path_to(sink)
        return " -> ".join(f"{n}[{self.nodes[n].output_type}]" for n in order)


def _takes_fs(op) -> bool:
    """True if the op's signature takes (x, fs).  Source / band / pole ops need fs;
    relational / dejitter ops operate on a ready trajectory."""
    return getattr(op, "_needs_fs", False)


def needs_fs(fn):
    fn._needs_fs = True
    return fn


# ===========================================================================
# THE OWNED-OP FILTER NODES.
# ===========================================================================

# --- SIGNAL (source) -------------------------------------------------------
@needs_fs
def _signal_op(x, fs):
    return np.asarray(x, dtype=np.float32)


# --- GAMMATONE : SIGNAL -> BAND_TRAJ ---------------------------------------
@needs_fs
def _gammatone_op(x, fs):
    from scripts.invariant_units_accept import band_trajectory_matrix
    M = band_trajectory_matrix(x, fs)
    return M if M is not None and len(M) >= 2 else None


# --- LPC_POLES : SIGNAL -> POLE_TRAJ (raw, jittery) ------------------------
@needs_fs
def _lpc_poles_op(x, fs):
    """Raw LPC pole/formant trajectory (frames x 6 = F1/F2/F3 + bw1/bw2/bw3).  This
    is filter_relational.formant_trajectory verbatim — the EXCITATION-FREE filter, but
    JITTERY frame-to-frame off the blurry cochlea.  Owned-op I/O boundary."""
    return formant_trajectory(x, fs)


# --- CEPSTRAL_POLES : SIGNAL -> POLE_TRAJ (BETTER, source-robust estimator) -
@needs_fs
def _cepstral_poles_op(x, fs):
    """The BETTER formant estimator: per-frame [F1,F2,F3,bw1,bw2,bw3] read off the
    LIFTERED CEPSTRAL ENVELOPE (homomorphic deconvolution — source comb/noise removed
    before peak-picking), via the authored native cepstral_formants op.  Same
    POLE_TRAJ output type as LPC_POLES, so it drops into the SAME downstream
    DEJITTER -> RELATIONAL_RANK path.  Owned-op I/O boundary."""
    return cepstral_formant_trajectory(x, fs)


# ===========================================================================
# THE DEJITTER NODE : POLE_TRAJ -> POLE_TRAJ_STABLE.
#
# Formant TRACKING / continuity stabilization of the jittery pole trajectory,
# composed from OWNED pieces:
#
#  (1) IN-ORDER FORMANT ASSIGNMENT.  lpc_formants_bw already returns poles ASCENDING
#      by frequency, so F1<F2<F3 by construction — the cheapest resolution of
#      crossings.  We additionally GAP-FILL: a frame missing a pole in a slot (the
#      ascending list was short and got zero-padded in formant_trajectory) is a hole;
#      a 0.0 in a formant slot is replaced by carrying the last valid value forward
#      (continuity), so a dropped pole does not read as a plunge to 0 Hz.
#
#  (2) OCTAVE-JUMP / OUTLIER REJECTION via a TEMPORAL MEDIAN over a small sliding
#      window per formant slot.  The median is the owned robust statistic for spurious
#      frame-to-frame jumps (an octave doubling/halving in one frame is an outlier the
#      median rejects while a real transition, sustained over several frames, passes).
#      Median over a window is an I/O-boundary owned op (np.median at the boundary,
#      exactly as the band path uses np.mean/np.std for z-scaling).
#
#  (3) ORDER-N VELOCITY / CONTINUITY PENALTY (native).  The agent's order_n_concepts
#      total_variation_term over TIME (order 1) is the smoothness criterion: it is
#      composed as a native Term and EVALUATED on the trajectory to MEASURE residual
#      jitter (total order-1 variation) before vs after stabilization — the
#      de-jitter's own self-test that it reduced the velocity it was built to reduce.
#      The stabilization itself (median + carry) is what drives that variation down;
#      the order_n term is the native yardstick that confirms it (the agent measuring
#      its own filter).
#
# This is the incoming STABILIZER edge REL-FILTER lacked.  Owned ops at the boundary;
# the continuity yardstick native.
# ===========================================================================

DEJITTER_MEDIAN_WIN = 5         # temporal median window (frames); odd, ~50 ms @ 10 ms hop


def _carry_forward_fill(col: np.ndarray) -> np.ndarray:
    """Replace 0.0 holes (a dropped/zero-padded pole) by carrying the last valid
    value forward, then back-fill the leading holes.  Continuity gap-fill — owned
    boundary op, no decision over graph state."""
    col = col.copy()
    last = None
    for i in range(len(col)):
        if col[i] > 0.0:
            last = col[i]
        elif last is not None:
            col[i] = last
    # back-fill leading holes with the first valid value
    first_valid = next((v for v in col if v > 0.0), 0.0)
    for i in range(len(col)):
        if col[i] <= 0.0:
            col[i] = first_valid
        else:
            break
    return col


def _temporal_median(col: np.ndarray, win: int) -> np.ndarray:
    """Sliding temporal median per formant slot — rejects octave-jump outliers while
    preserving sustained transitions.  Owned robust statistic at the boundary."""
    n = len(col)
    if n < 2:
        return col
    half = win // 2
    out = np.empty_like(col)
    for i in range(n):
        lo, hi = max(0, i - half), min(n, i + half + 1)
        out[i] = float(np.median(col[lo:hi]))
    return out


def dejitter_trajectory(M: np.ndarray) -> Optional[np.ndarray]:
    """POLE_TRAJ (frames x 6, jittery) -> POLE_TRAJ_STABLE (frames x 6, stabilized).

    Per formant/bw slot: carry-forward gap-fill (continuity, kill 0-Hz plunges) then a
    sliding TEMPORAL MEDIAN (octave-jump rejection).  In-order assignment is already
    guaranteed by lpc_formants_bw's ascending return.  Owned boundary ops only."""
    if M is None or len(M) < 2:
        return None
    M = np.asarray(M, dtype=np.float32)
    out = np.empty_like(M)
    for c in range(M.shape[1]):
        col = _carry_forward_fill(M[:, c])
        out[:, c] = _temporal_median(col, DEJITTER_MEDIAN_WIN)
    return out.astype(np.float32)


def _dejitter_op(M):
    return dejitter_trajectory(M)


# --- native order-1 (velocity) continuity yardstick ------------------------
def _velocity_term(n_dims: int, win: int = 3):
    """A native order_n total-variation Term over TIME: total order-1 variation of a
    short window of frames laid out as attrs f0..f{win-1} of one node, summed over the
    formant dims.  The agent's order_n_concepts.total_variation_term (order 1) is the
    native smoothness measure.  Used to MEASURE residual jitter, not to gate."""
    # Per dim d, samples are attrs d_t0..d_t{win-1}; total order-1 variation.
    terms = []
    for d in range(n_dims):
        samples = [Attr(Var("s"), f"d{d}_t{t}") for t in range(win)]
        tv = total_variation_term(samples, 1)
        if tv is not None:
            terms.append(tv)
    if not terms:
        return None
    from substrate_rs import Plus
    return Plus(items=tuple(terms))


def measure_jitter(M: np.ndarray, win: int = 3) -> float:
    """Native order-1 total-variation (mean per overlapping window) over the
    trajectory — the agent's own continuity yardstick, evaluated via substrate.evaluate
    (NO python arithmetic in the measure).  Lower = smoother (less jitter)."""
    M = np.asarray(M, dtype=np.float64)
    n_frames, n_dims = M.shape
    if n_frames < win:
        return float("nan")
    s = Substrate()
    term = _velocity_term(n_dims, win=win)
    if term is None:
        return float("nan")
    from domains.order_n_concepts import _Pred
    pred = _Pred(term.to_dict())
    total, cnt = 0.0, 0
    for t0 in range(n_frames - win + 1):
        attrs = {}
        for d in range(n_dims):
            for t in range(win):
                attrs[f"d{d}_t{t}"] = float(M[t0 + t, d])
        nid = s.add_node("Win", attrs)
        total += float(s.evaluate(pred, {"s": nid}))
        cnt += 1
    return total / max(cnt, 1)


# --- RELATIONAL_RANK : (BAND_TRAJ|POLE_TRAJ|POLE_TRAJ_STABLE) -> REL_SHAPE --
def _relational_op(M):
    """The agent's whole-unit relational shape (ordinal rank + self-similarity),
    native eval, dimension-agnostic — reused VERBATIM from domains/relational_shape.
    Consumes bands OR (stabilized) poles identically."""
    if M is None or len(M) < 2:
        return None
    return relational_shape(M, n_anchors=6)


# ===========================================================================
# THE THREE GRAPHS THE AGENT WIRES.
# ===========================================================================
def _base_nodes() -> Dict[str, FilterNode]:
    return {
        "SIGNAL": FilterNode("SIGNAL", None, SIGNAL, _signal_op),
        "GAMMATONE": FilterNode("GAMMATONE", SIGNAL, BAND_TRAJ, _gammatone_op),
        "LPC_POLES": FilterNode("LPC_POLES", SIGNAL, POLE_TRAJ, _lpc_poles_op),
        "CEPSTRAL_POLES": FilterNode("CEPSTRAL_POLES", SIGNAL, POLE_TRAJ,
                                     _cepstral_poles_op),
        "DEJITTER": FilterNode("DEJITTER", POLE_TRAJ, POLE_TRAJ_STABLE, _dejitter_op),
    }


def build_band_graph() -> FilterGraph:
    """(A/B) BAND PATH: SIGNAL -> GAMMATONE -> RELATIONAL_RANK -> REL_SHAPE."""
    g = FilterGraph()
    for nd in _base_nodes().values():
        g.add(nd)
    g.add(FilterNode("RELATIONAL_RANK", BAND_TRAJ, REL_SHAPE, _relational_op))
    g.connect("SIGNAL", "GAMMATONE")
    g.connect("GAMMATONE", "RELATIONAL_RANK")
    return g


def build_filter_dangling_graph() -> FilterGraph:
    """(B) FILTER DANGLING: SIGNAL -> LPC_POLES -> RELATIONAL_RANK(POLE_TRAJ).

    The RELATIONAL_RANK input is POLE_TRAJ — it reads RAW jittery poles with NO
    stabilizer.  This is the 31.3% broken baseline.  Note the node is NOT dangling in
    the graph-topology sense (LPC_POLES feeds it) — it is dangling in the sense the
    user means: no STABILIZER edge between the jittery producer and the relational
    consumer.  Built explicitly so C differs from it by exactly the DEJITTER edge."""
    g = FilterGraph()
    for nd in _base_nodes().values():
        g.add(nd)
    g.add(FilterNode("RELATIONAL_RANK", POLE_TRAJ, REL_SHAPE, _relational_op))
    g.connect("SIGNAL", "LPC_POLES")
    g.connect("LPC_POLES", "RELATIONAL_RANK")
    return g


def build_filter_wired_graph() -> FilterGraph:
    """(C) FILTER WIRED: SIGNAL -> LPC_POLES -> DEJITTER -> RELATIONAL_RANK.

    The de-jitter EDGE is wired in: the RELATIONAL_RANK now reads POLE_TRAJ_STABLE.
    Differs from (B) by exactly the inserted DEJITTER node — the wiring is the fix."""
    g = FilterGraph()
    for nd in _base_nodes().values():
        g.add(nd)
    g.add(FilterNode("RELATIONAL_RANK", POLE_TRAJ_STABLE, REL_SHAPE, _relational_op))
    g.connect("SIGNAL", "LPC_POLES")
    g.connect("LPC_POLES", "DEJITTER")
    g.connect("DEJITTER", "RELATIONAL_RANK")
    return g


def build_cepstral_filter_graph(dejitter: bool = True) -> FilterGraph:
    """(C) BETTER-FILTER: SIGNAL -> CEPSTRAL_POLES [-> DEJITTER] -> RELATIONAL_RANK.

    The LPC_POLES estimator is REPLACED by CEPSTRAL_POLES (the liftered cepstral-
    envelope formant node, source-removed).  Same downstream relational path; if
    `dejitter`, the stabilizer edge is wired in exactly as the LPC-wired graph (C)
    does, so the only change from the old (C) is the ESTIMATOR node."""
    g = FilterGraph()
    for nd in _base_nodes().values():
        g.add(nd)
    if dejitter:
        g.add(FilterNode("RELATIONAL_RANK", POLE_TRAJ_STABLE, REL_SHAPE, _relational_op))
        g.connect("SIGNAL", "CEPSTRAL_POLES")
        g.connect("CEPSTRAL_POLES", "DEJITTER")
        g.connect("DEJITTER", "RELATIONAL_RANK")
    else:
        g.add(FilterNode("RELATIONAL_RANK", POLE_TRAJ, REL_SHAPE, _relational_op))
        g.connect("SIGNAL", "CEPSTRAL_POLES")
        g.connect("CEPSTRAL_POLES", "RELATIONAL_RANK")
    return g


# Convenience reps for the probe (flow a clip through each wired graph) -------
def rep_band(x, fs):
    return build_band_graph().evaluate("RELATIONAL_RANK", x, fs)


def rep_filter_dangling(x, fs):
    return build_filter_dangling_graph().evaluate("RELATIONAL_RANK", x, fs)


def rep_filter_wired(x, fs):
    return build_filter_wired_graph().evaluate("RELATIONAL_RANK", x, fs)


def rep_cepstral_filter(x, fs, dejitter: bool = True):
    return build_cepstral_filter_graph(dejitter=dejitter).evaluate(
        "RELATIONAL_RANK", x, fs)


__all__ = [
    "FilterNode", "FilterGraph", "SIGNAL", "BAND_TRAJ", "POLE_TRAJ",
    "POLE_TRAJ_STABLE", "REL_SHAPE", "dejitter_trajectory", "measure_jitter",
    "build_band_graph", "build_filter_dangling_graph", "build_filter_wired_graph",
    "build_cepstral_filter_graph",
    "rep_band", "rep_filter_dangling", "rep_filter_wired", "rep_cepstral_filter",
]
