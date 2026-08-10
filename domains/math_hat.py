"""math_hat — the MATH sense behind the Hat interface, mirroring domains/audio_hat.

The universal cortex (domains/cortex_loop.CortexLoop) is ONE front-end-agnostic
analysis-by-synthesis loop: coarse-match -> adapt-style -> order-N iterate ->
readout argmin_content[ min_style compare(H, synth(C, S)) ]. It contains ZERO
sense-specifics; everything a sense needs lives behind the Hat interface
(domains/hat.Hat). The audio sense (domains/audio_hat.AudioHat) is one such hat.

This hat points the SAME loop at the math DESCRIPTION->OBJECT gap. The gap (the
derivation engine stalls at "comprehend: prose -> object" — a prose description has
no chain complex to derive over) is an analysis-by-synthesis problem: INVERT the
forward model (object -> its properties). Synthesize candidate OBJECTS, derive each
one's properties, keep the one whose properties match the description.

  · encode(description) -> the description's stated PROPERTIES (the agent's HELD
                           comprehension: construction_grammar.apply_constructions
                           matches prose clauses -> a property frame -> a numeric
                           property VECTOR). The front end: prose -> properties.
  · synth(object, style) -> the object's DERIVED properties (the agent's HELD
                           homology FORWARD MODEL: the candidate object is a
                           simplicial complex; betti_number — acquired-by-reading,
                           grounded over the held boundary operator ∂ — derives its
                           Betti vector; dimension/connectivity fall out). This is
                           the forward model the loop inverts. NO domain gap: the
                           candidate's properties are DERIVED, never approximated.
  · compare(a, b)        -> the agent's OWNED graph metric Magnitude(VecSub(a, b))
                           over the property vectors (the SAME owned L2 the toy hat
                           uses, evaluated natively in Rust — no net, no fit).
  · library()            -> the known spaces (the compute_homology seed: S^1 / S^2 /
                           disk / point / two-points / torus — each with its chain
                           complex), the candidates the readout argmin ranges over.

STYLE / PRESENTATION-INVARIANCE. In audio, style = the voice (a nuisance transform
the loop factors out by min_S). The math analog of the nuisance is the description's
PRESENTATION / phrasing — but a candidate object's properties are PRESENTATION-FREE
by construction (the same complex derives the same Betti vector no matter how the
description was phrased). So the math style is DEGENERATE: a single neutral
presentation, no style axes. The loop runs UNCHANGED — min_S over the one neutral
style — and grounds to the object regardless of the description's surface form. That
IS the math echo of speaker-invariant-by-construction: the grounding is
presentation-invariant because the forward model derives properties from the OBJECT.

HONEST SCOPE (the same frontier the derivation engine names). The loop grounds
description->object for any object whose chain complex is in the library and whose
properties the held forward model derives. The real HLE case ("moduli space of
nondegenerate unit-area lattices -> H_1") STALLS: the forward model / library LACKS
the identification "moduli space of lattices -> the modular orbifold / S^3 minus the
trefoil" — the loop cannot synthesize a candidate it does not hold. That is the
forward-model KNOWLEDGE gap = the same ground+acquire frontier (acquire-by-reading
the identification puts the object in the library, then the loop grounds it). The
loop's STRUCTURE is right; the held breadth is the climb. See [[ozma_order_n_analysis
_by_synthesis]] / [[ozma_synthesizes_own_gaps]] / [[ozma_agent_writes_its_own_code]].

DONKEY BOUNDARY: the CortexLoop owns coarse-match / adapt / order-N / argmin (no
net). This hat owns the sense: encode = the held construction-grammar comprehension,
synth = the held betti_number forward model, compare = the owned L2 graph op,
library = the held known spaces. Composed from HELD pieces; no hand-coded math, no
new operator, no Rust.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

from substrate_rs import _native
from domains.hat import Hat
from domains import construction_grammar as CG
from domains import grounded_representation as gr
from domains import reason
from domains import compute_grounding as cg
from scripts.dtw_trajectory_loso import _Pred, _V, _Attr

# the owned compare: L2 over the property vector = Magnitude(VecSub(a, b)) — the SAME
# owned graph op the toy hat uses, evaluated natively (no net, no fit).
_PROP_ATTR = "math_props"


def _vecsub(a, b):
    return {"type": "VecSub", "a": a, "b": b}


def _magnitude(a):
    return {"type": "Magnitude", "arg": a}


# ---------------------------------------------------------------------------
# The Betti FORMULA, acquired BY READING (compute_homology's discipline): b_n =
# (#n-simplices − rank ∂_n) − rank ∂_{n+1}. The hat grounds it ONCE over the held
# boundary operator ∂ + matrix rank, then `synth` derives any candidate's Betti
# vector through it. This is the agent's HELD forward model, not hand-coded.
# ---------------------------------------------------------------------------
_BETTI_DEF = ("betti_number(complex, k) = "
              "cardinality(simplices_of_dim(complex, k)) "
              "- matrix_rank(boundary_matrix(complex, k)) "
              "- matrix_rank(boundary_matrix(complex, k + 1))")


# ---------------------------------------------------------------------------
# THE KNOWN SPACES (the library content) — the SAME small set compute_homology
# builds, each as its simplicial complex (a flat list of ordered vertex lists).
# The hat is NEVER told their homology; `synth` DERIVES it through the forward model.
# ---------------------------------------------------------------------------
def _known_spaces() -> Dict[str, List[List[int]]]:
    s1 = [[0], [1], [2], [0, 1], [1, 2], [0, 2]]              # triangle boundary
    disk = s1 + [[0, 1, 2]]                                   # filled triangle
    s2 = [[0], [1], [2], [3],                                 # tetra boundary
          [0, 1], [0, 2], [0, 3], [1, 2], [1, 3], [2, 3],
          [0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]]
    point = [[0]]
    two_points = [[0], [1]]

    def torus():
        def orbit(b):
            return [sorted([(v + s) % 7 for v in b]) for s in range(7)]
        tris = orbit([0, 1, 3]) + orbit([0, 2, 3])
        cx = set()
        for t in tris:
            t = sorted(t)
            cx.add(tuple(t))
            for i in range(3):
                for j in range(i + 1, 3):
                    cx.add((t[i], t[j]))
            for v in t:
                cx.add((v,))
        return [list(s) for s in cx]

    return {
        "S^1": s1,
        "S^2": s2,
        "disk": disk,
        "point": point,
        "two_points": two_points,
        "torus": torus(),
    }


# ---------------------------------------------------------------------------
# THE PROPERTY VECTOR — the common feature space encode() and synth() both produce.
# A fixed schema of homological predicates, so the owned L2 compare is meaningful:
#   [ b0, b1, b2, dimension, connected ]
# Both the description's STATED properties (encode) and a candidate's DERIVED
# properties (synth) are laid into this schema; unstated description slots are NaN-
# masked so they do not penalise (the compare ignores unconstrained axes).
# ---------------------------------------------------------------------------
_SCHEMA = ["b0", "b1", "b2", "dimension", "connected"]


def _props_to_vec(props: Dict[str, Any], *, mask_unstated: bool) -> List[float]:
    """Lay a property dict into the fixed schema vector. For the DESCRIPTION
    (mask_unstated=True) an unstated slot is left at the candidate's own value by
    the masking in compare; here we mark it with a sentinel the compare neutralises."""
    out = []
    for k in _SCHEMA:
        if k in props and props[k] is not None:
            out.append(float(props[k]))
        else:
            out.append(float("nan") if mask_unstated else 0.0)
    return out


# ---------------------------------------------------------------------------
# PROPERTY-EXTRACTION CONSTRUCTIONS (graph DATA — the agent's comprehension). Each
# is a slot pattern over a prose CLAUSE -> a property frame, matched by the HELD
# construction_grammar.apply_constructions (the same matcher the conversation grammar
# uses). NOT per-description code: clause patterns the agent reads, like the math-
# prose constructions. encode() scans the description's clauses through these.
# ---------------------------------------------------------------------------
def _property_constructions() -> List[dict]:
    C = []

    def add(pattern, meaning):
        C.append({"language": "en", "pattern": pattern, "meaning": meaning})

    # "first Betti number (is) N" / "first homology ... rank N"
    add(["first", "betti", "number", "is", "{n}"], {"property": "betti", "dim": 1, "value": "{n}"})
    add(["first", "betti", "number", "{n}"], {"property": "betti", "dim": 1, "value": "{n}"})
    add(["zeroth", "betti", "number", "is", "{n}"], {"property": "betti", "dim": 0, "value": "{n}"})
    add(["zeroth", "betti", "number", "{n}"], {"property": "betti", "dim": 0, "value": "{n}"})
    add(["second", "betti", "number", "is", "{n}"], {"property": "betti", "dim": 2, "value": "{n}"})
    add(["second", "betti", "number", "{n}"], {"property": "betti", "dim": 2, "value": "{n}"})
    # dimension
    add(["{d}", "dimensional"], {"property": "dimension", "value": "{d}"})
    add(["dimension", "is", "{d}"], {"property": "dimension", "value": "{d}"})
    add(["dimension", "{d}"], {"property": "dimension", "value": "{d}"})
    # connectivity
    add(["connected"], {"property": "connected", "value": 1})
    add(["path", "connected"], {"property": "connected", "value": 1})
    add(["disconnected"], {"property": "connected", "value": 0})
    # a surface = 2-dimensional (a held synonym; the comprehension, graph data)
    add(["surface"], {"property": "dimension", "value": 2})
    add(["closed", "surface"], {"property": "dimension", "value": 2})
    # contractible / trivial higher homology -> b1=b2=0 (a held synonym)
    add(["contractible"], {"property": "contractible", "value": 1})
    add(["all", "higher", "homology", "vanishes"], {"property": "contractible", "value": 1})
    add(["all", "higher", "homology", "is", "zero"], {"property": "contractible", "value": 1})
    return C


class MathHat(Hat):
    """The math sense as a Hat. content = a known-space name; style = a degenerate
    neutral presentation (presentation factored out at encode); the forward model is
    the held homology computation. Mirrors AudioHat's structure exactly."""

    name = "math"

    def __init__(self, substrate, spaces: Dict[str, List[List[int]]] = None):
        # `substrate` is the wrapper Substrate the owned compare metric evaluates on
        # (same as the toy/audio hats). The homology forward model grounds on its OWN
        # _native substrate (the compute_homology path), kept separate.
        self.s = substrate
        self.spaces = dict(spaces) if spaces else _known_spaces()
        self._constructions = _property_constructions()
        # the owned L2 compare term over the property vectors (Magnitude(VecSub)).
        self._resid_term = _Pred(_magnitude(_vecsub(
            _Attr(_V("q"), _PROP_ATTR), _Attr(_V("c"), _PROP_ATTR))))
        self.qn = substrate.add_node("MathHatQ", {"origin": "mathhat_q"})
        self.cn = substrate.add_node("MathHatCand", {"origin": "mathhat_c"})
        # ground the held Betti forward model ONCE (acquire-by-reading), on a private
        # _native substrate — exactly the compute_homology grounding.
        self._fwd_s = _native.Substrate()
        gr.open_grounding_productions(self._fwd_s)
        self._caps = dict(reason.CAPABILITIES)
        cg.ground_computation(self._fwd_s, "betti_number", _BETTI_DEF,
                              capabilities=self._caps)
        self._prop_cache: Dict[str, Dict[str, Any]] = {}
        self._library: List[Tuple[str, Dict[str, Any], Any]] = []
        self._build_library()

    # ---- the HELD homology FORWARD MODEL: object (complex) -> derived properties ----
    def _derive_props(self, name: str) -> Dict[str, Any]:
        cached = self._prop_cache.get(name)
        if cached is not None:
            return cached
        cx = self.spaces[name]
        top = max(len(s) - 1 for s in cx)
        betti = []
        for k in range(top + 1):
            b = reason.solve({"betti_number": {"complex": cx, "k": k}}, {},
                             capabilities=self._caps)
            betti.append(int(b))
        props = {
            "b0": betti[0] if len(betti) > 0 else 0,
            "b1": betti[1] if len(betti) > 1 else 0,
            "b2": betti[2] if len(betti) > 2 else 0,
            # dimension = the top simplex dimension that carries homology / the
            # complex's top dimension (the held structural read of the object).
            "dimension": top,
            # connected iff b0 == 1 (the held homological reading of connectivity).
            "connected": 1 if (betti and betti[0] == 1) else 0,
        }
        self._prop_cache[name] = props
        return props

    # ---- the HELD comprehension: description prose -> stated properties ----
    def _comprehend(self, description: str) -> Dict[str, Any]:
        """Scan the description's CLAUSES through the held construction-grammar
        matcher, accumulating a property frame. The agent's comprehension (graph-data
        patterns), NOT per-description math parsing."""
        text = (description or "").lower()
        for ch in ",.;:!?$\\{}()":
            text = text.replace(ch, " ")
        text = text.replace("-", " ")
        toks = text.split()
        props: Dict[str, Any] = {}
        n = len(toks)
        # slide a window over the token stream; the held matcher fires on any clause
        # whose pattern fully matches (window lengths 1..5 cover the patterns).
        for i in range(n):
            for L in range(5, 0, -1):
                if i + L > n:
                    continue
                frame = CG.apply_constructions(" ".join(toks[i:i + L]),
                                               self._constructions)
                if not frame:
                    continue
                self._absorb(frame, props)
        return props

    @staticmethod
    def _absorb(frame: Any, props: Dict[str, Any]) -> None:
        frames = frame if isinstance(frame, list) else [frame]
        for f in frames:
            if not isinstance(f, dict):
                continue
            p = f.get("property")
            if p == "betti":
                try:
                    props[f"b{int(f['dim'])}"] = int(f["value"])
                except Exception:
                    pass
            elif p == "dimension":
                try:
                    props["dimension"] = int(f["value"])
                except Exception:
                    pass
            elif p == "connected":
                props["connected"] = int(f["value"])
            elif p == "contractible":
                # contractible = b1 = b2 = 0 and connected (b0 = 1).
                props.setdefault("b1", 0)
                props.setdefault("b2", 0)
                props.setdefault("b0", 1)
                props.setdefault("connected", 1)

    # ---- the three core Hat methods ----
    def encode(self, raw: str) -> Any:
        """description prose -> the stated-property VECTOR (unstated slots NaN-masked
        so the compare ignores unconstrained axes)."""
        props = self._comprehend(raw)
        return _props_to_vec(props, mask_unstated=True)

    def synth(self, content: str, style: Dict[str, Any]) -> Any:
        """candidate OBJECT -> its DERIVED-property vector (the held forward model).
        Style is the degenerate neutral presentation — it does not change the object's
        derived properties (presentation-invariance by construction)."""
        if content not in self.spaces:
            return None
        props = self._derive_props(content)
        return _props_to_vec(props, mask_unstated=False)

    def compare(self, a: Any, b: Any) -> float:
        """owned L2 over the property vectors, with the description's UNSTATED axes
        (NaN in `a`) neutralised so they do not penalise. Evaluated natively in Rust
        on the stated axes via the owned Magnitude(VecSub) term."""
        if a is None or b is None:
            return float("inf")
        # mask: keep only the axes the description STATED (non-NaN in a). For those,
        # build the two sub-vectors and run the owned graph metric.
        qa, qb = [], []
        for x, y in zip(a, b):
            if x != x:        # NaN -> unstated -> ignored
                continue
            qa.append(float(x))
            qb.append(float(y))
        if not qa:
            return float("inf")
        self.s.set_attr(self.qn, _PROP_ATTR, qa)
        self.s.set_attr(self.cn, _PROP_ATTR, qb)
        d = self.s.evaluate(self._resid_term, {"q": self.qn, "c": self.cn})
        return float(d) if d is not None else float("inf")

    # ---- search scaffolding ----
    def contents(self):
        return list(self.spaces.keys())

    def style_init(self) -> Dict[str, Any]:
        # the degenerate neutral presentation (no style axes — presentation factored
        # out at encode; the math analog of speaker-invariant-by-construction).
        return {"presentation": "neutral"}

    def n_stages(self) -> int:
        return 1

    def style_neighbours(self, style: Dict[str, Any], stage: int) -> Iterable[Dict[str, Any]]:
        # no nuisance axes to adapt: the object's properties are presentation-free.
        return []

    def library(self):
        return self._library

    def close(self):
        self.s.remove_node(self.qn)
        self.s.remove_node(self.cn)

    # ---- the library (the known spaces, each with its DERIVED-property vector) ----
    def _build_library(self):
        neutral = self.style_init()
        for name in self.spaces:
            vec = self.synth(name, neutral)
            if vec is not None:
                self._library.append((name, dict(neutral), vec))
