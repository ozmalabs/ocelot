"""domains/lowercase_primer.py -- THE INSTRUCTION SHEET: recognise a letter by its INTENDED
CONSTRUCTION (its ductus), not by matching a stored exemplar.

The creator's reframe (the session that produced this): "we should SURELY be able to get this
build instruction from a literal child's instruction sheet." A letter's identity is not a
feature to reverse-engineer from the ink (closure, terminals, stems -- every such hand-feature
fixes one confusion and breaks another because it lacks alignment). It is an intended
construction that is ALREADY WRITTEN DOWN: the handwriting-primer formation a child is taught
("an a is a round bowl, then a stem down the right that pokes below"). That intended
construction IS the intentionality, in canonical form, and it carries the small deliberate
element (the stem, the descender, the open side of a c) that an exemplar's ink-MASS drowns.

THE BOWL FAMILY (the maximally self-confusable lowercase set, where a/o lives) as primer
constructions -- each is "a bowl (+ an intended stem/tail with a direction and an extent)":

    o : bowl, closed, nothing else
    a : bowl + a short stem down the right (pokes to the baseline)
    d : bowl + a TALL stem up the right (an ascender)
    c : the bowl LEFT OPEN (an arc that never closes)
    e : bowl + a horizontal bar through the middle
    g : bowl + a descender below the line, hooking left
    q : bowl + a straight descender, tail to the right

MEASURED (scripts/jabberwock_lowercase_primer_demo.py, cross-drawer one-shot on the bowl
family): matching queries to these CONSTRUCTIONS instead of to a support drawer's EXEMPLARS
lifts the bowl family 60.9% -> 76.7% and eliminates the mass-drowning confusions the exemplar
path suffers (G/Q 12->0, D/A 12->0, Q/A 9->0). The construction carries the intended
stem/descender the exemplar's shared bowl-mass buries.

VERDICT = render-and-compare against the construction (`read_by_construction`): the query's
whole-figure point set is compared (held `ShapeContextDist + TpsDeformDist`, held `Argmin`) to
each construction's rendered ideal. This is AbS against the INTENDED form -- robust to how the
query was penned (85/133 real bowl-family glyphs are drawn in a SINGLE stroke, so the substrate's
per-stroke STRUCTURAL coverage-decode over `strokeq`+`rel` collapses to 15% on real ink; the
whole-figure render-compare does not need the query to segment like the construction does).

TWO HONEST FRONTIERS, named not hidden:
  1. CLOSURE (the c/o residual). The whole-figure verdict still drowns the open side of a c
     (C->O is the one surviving confusion). No global OR crudely-localised closure feature fixes
     it without regressing another pair (five measured attempts: endpoint-gap, angular-gap,
     bbox-local openness -- each fixes C/O and breaks Q/G or A/D, because it lacks a true
     alignment of the construction's bowl region onto the query). The fix is a construction-LOCAL
     verdict with real per-element alignment (render each intended element at the query's decoded
     pose and judge it in its own place) -- the substrate's `abs_read.abs_rerank` render-compare
     is that path; it is blocked today by the single-stroke segmentation gap above, not by the
     construction idea.
  2. The primer here is the BOWL FAMILY only. It extends letter-by-letter; the non-bowl families
     (the F/L vertical-stem family, etc.) are the same shape of data.

`author_primer` installs each construction into the substrate as a real `ShapeSignature`
(`character_compose.grow_character_quantum`) so the agent HOLDS the instruction sheet as graph
data; the verdict reads the primer's rendered prototypes directly (no persistence side effect),
so it is usable without booting/authoring.
"""
from __future__ import annotations

import numpy as np

from domains import abs_read as ar

_N = 48  # whole-figure resample density for the render-compare


# --------------------------------------------------------------------------------------------- #
#  THE PRIMER -- each letter's intended construction as its ordered strokes (role, polyline).
#  Geometry is in a lowercase writing frame: baseline y=0, x-height ~0.70, ascender ~1.0,
#  descender ~-0.5 (y-up). Sourced from standard handwriting-primer formation, NOT tuned to any
#  eval number. `role` names the intended element (bowl / open_bowl / stem / bar / descender).
# --------------------------------------------------------------------------------------------- #
def _arc(cx, cy, rx, ry, a0, sweep, n=40):
    t = np.radians(np.linspace(a0, a0 - sweep, n))
    return np.c_[cx + rx * np.cos(t), cy + ry * np.sin(t)]


def _line(p0, p1, n=20):
    return np.linspace(np.asarray(p0, float), np.asarray(p1, float), n)


def _bowl(cx=0.30):
    return _arc(cx, 0.35, 0.28, 0.35, 80, 350)   # a near-closed loop


PRIMER: dict[str, list[tuple[str, np.ndarray]]] = {
    "o": [("bowl", _bowl(0.35))],
    "a": [("bowl", _bowl(0.30)), ("stem", _line((0.58, 0.70), (0.58, -0.02)))],
    "d": [("bowl", _bowl(0.30)), ("stem", _line((0.58, 1.00), (0.58, 0.00)))],
    "c": [("open_bowl", _arc(0.36, 0.35, 0.30, 0.35, 60, 300))],
    "e": [("bowl", _bowl(0.33)), ("bar", _line((0.06, 0.36), (0.60, 0.36)))],
    "g": [("bowl", _bowl(0.30)),
          ("descender", np.vstack([_line((0.58, 0.70), (0.58, -0.42)),
                                    _line((0.58, -0.42), (0.30, -0.50))]))],
    "q": [("bowl", _bowl(0.30)),
          ("descender", np.vstack([_line((0.58, 0.70), (0.58, -0.50)),
                                    _line((0.58, -0.50), (0.76, -0.40))]))],
}


# --------------------------------------------------------------------------------------------- #
#  Render a construction to its whole-figure prototype point set (the ideal glyph), in the SAME
#  centre + abs-max frame the query is put in -- so the held ShapeContext/TPS verdict compares
#  like with like.
# --------------------------------------------------------------------------------------------- #
def _resample(pts, n=_N):
    P = np.asarray(pts, float)
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    if d[-1] < 1e-9:
        return None
    u = np.linspace(0, d[-1], n)
    return np.c_[np.interp(u, d, P[:, 0]), np.interp(u, d, P[:, 1])]


def _frame(R):
    R = R - R.mean(0)
    return R / (np.abs(R).max() + 1e-9)


def whole_figure(strokes):
    """The concatenated, arc-length-resampled, centre+abs-max-normalised whole-figure point set
    for a list of stroke polylines -- the same frame for a query and a rendered construction."""
    R = _resample(np.vstack([np.asarray(s, float) for s in strokes]))
    return _frame(R) if R is not None else None


def prototype(letter: str):
    """The rendered ideal point set for a primer letter's intended construction."""
    return whole_figure([pts for _role, pts in PRIMER[letter]])


_PROTOTYPES = {c: prototype(c) for c in PRIMER}


# --------------------------------------------------------------------------------------------- #
#  THE VERDICT -- render-and-compare against the construction (held Terms).
# --------------------------------------------------------------------------------------------- #
def _sctps_term(a_pts, b_pts) -> dict:
    return {"type": "Plus", "items": [
        {"type": "ShapeContextDist", "a": {"type": "Lit", "value": a_pts},
         "b": {"type": "Lit", "value": b_pts}},
        {"type": "TpsDeformDist", "a": {"type": "Lit", "value": a_pts},
         "b": {"type": "Lit", "value": b_pts}}]}


def _closes(letter: str) -> bool:
    """Whether the construction's bowl is INTENDED to close (a closed loop) -- false only for the
    open_bowl role (c). This is a property of the intent, not the execution."""
    return not any(role == "open_bowl" for role, _ in PRIMER[letter])


def bowl_closure(strokes) -> float:
    """The bowl's endpoint gap relative to its extent -- the CLOSURE INTENT that survives the
    mouse: an o closes (its stroke returns to its start, gap ~0.07), a c does not (it starts
    top-but-over and ends at the opposite terminal, gap ~0.63). The bowl is taken as the longest
    stroke. This is the motor-intent trace the whole-figure shape verdict drowns."""
    s = np.asarray(max(strokes, key=lambda a: len(a)), float)[:, :2]
    return float(np.linalg.norm(s[0] - s[-1]) / (np.linalg.norm(s.max(0) - s.min(0)) + 1e-9))


def read_by_construction(native, query_strokes, *, candidates=None,
                         intent: bool = True, closure_thr: float = 0.30) -> dict:
    """Classify a query glyph by its INTENDED CONSTRUCTION: the held `ShapeContextDist +
    TpsDeformDist` distance from the query's whole figure to each construction's rendered ideal,
    the winner chosen by a held `Argmin` (`abs_read._argmin_pairs_term`) -- no Python min.

    INTENT ADJUDICATION (`intent=True`): the whole-figure shape verdict drowns closure (an open
    c bends shut and reads o). When the shape top-2 STRADDLE an open-bowl construction (c) and a
    closed one, the tie is broken not by shape but by the query's own CLOSURE INTENT
    (`bowl_closure` vs `closure_thr`) -- the motor trace that survives the mouse. This is applied
    LOCALLY, only on the open-vs-closed contention, so it never touches the closed-bowl pairs
    (a/d/g/q) a global closure feature would wreck. Measured: bowl family 76.7% -> 89.5%, c->o
    17 -> 0, no regressions.

    Returns `{winner, scores, adjudicated}` where scores is `[(distance, letter), ...]`.
    `candidates`: restrict to a subset of primer letters (default: the whole primer)."""
    letters = list(candidates) if candidates else list(PRIMER)
    q = whole_figure(query_strokes)
    if q is None:
        return {"winner": None, "scores": [], "note": "degenerate query"}
    ql = q.tolist()
    pairs = []
    for i, c in enumerate(letters):
        proto = _PROTOTYPES[c]
        if proto is None:
            continue
        dist = float(native.evaluate(_sctps_term(ql, proto.tolist()), {}) or 0.0)
        pairs.append((dist, i))
    if not pairs:
        return {"winner": None, "scores": []}
    w = native.evaluate(ar._argmin_pairs_term(pairs), {})
    wi = int(w[1]) if w is not None else pairs[0][1]
    scores = sorted((d, letters[i]) for d, i in pairs)
    winner = letters[wi]

    adjudicated = None
    if intent and len(scores) >= 2:
        top2 = [c for _d, c in scores[:2]]
        opens = [c for c in top2 if not _closes(c)]
        closeds = [c for c in top2 if _closes(c)]
        if opens and closeds:  # the top-2 straddle open vs closed -> the closure INTENT decides
            winner = opens[0] if bowl_closure(query_strokes) > closure_thr else closeds[0]
            adjudicated = "closure_intent"
    return {"winner": winner, "scores": scores, "adjudicated": adjudicated}


# --------------------------------------------------------------------------------------------- #
#  AUTHORING -- install the primer into the substrate as real ShapeSignatures (the agent HOLDS
#  the instruction sheet as graph data). Legal seed-builder work (persists via teach()); the
#  rendered prototype travels along as a meta attr so a construction-render verdict can read it
#  straight off the held node.
# --------------------------------------------------------------------------------------------- #
def author_primer(agent, *, letters=None) -> dict:
    """Install each primer construction into the substrate: mint its stroke quanta, compose the
    character `ShapeSignature` (`strokeq`+`rel`+`cpose`), and grow it into the character codebook
    with its rendered whole-figure prototype attached. Returns the per-letter install records."""
    from domains import stroke_codebook as sc
    from domains import character_compose as cc
    native = getattr(agent, "_inner", getattr(agent, "inner", agent))
    out = {}
    for c in (letters or list(PRIMER)):
        strokes = PRIMER[c]
        named = []
        for role, pts in strokes:
            qn = f"prim_{c}_{role}"   # unique per (letter, role): a's stem != d's stem
            sc.grow_stroke_quantum(agent, np.asarray(pts).tolist(), qn)
            named.append((np.asarray(pts).tolist(), qn))
        sig = cc.compose_character_signature(native, named)["signature"]
        proto = _PROTOTYPES[c]
        rec = cc.grow_character_quantum(agent, f"lc_{c}", sig,
                                        primer_letter=c,
                                        prototype=(proto.tolist() if proto is not None else None))
        out[c] = {"signature": sig, "record": rec}
    return out
