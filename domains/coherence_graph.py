"""coherence_graph — the agent ASSEMBLES its own graph-native COHERENCE function.

A comprehended frame COHERES iff it forms a GROUNDED + CONNECTED structure in the
agent's OWN concept graph. The agent composes that judgement as a Term-tree over
the DSL graph primitives (NodesWhere / Exists / InNeighbours / Intersect / Count /
Sum / Div / IfThenElse / Gt) and the ENGINE computes the number — NO Python
arithmetic decides the score, exactly like domains/order_n_concepts.py (the
Term-tree IS the agent's program; substrate.evaluate runs it in Rust).

THE AGENT'S UNDERSTANDING (-> the tree it composes)
---------------------------------------------------
A frame is a set of CONTENT fillers (the values of event/agent/patient/... that
aren't WH placeholders or bare numbers). For each filler:

  · GROUNDED — the agent HOLDS the concept: ``Exists(NodesWhere(Concept,
    name == filler))`` is true (a concept node by that name exists, e.g. it was
    seeded / lexicalised / asserted). A research term ("bordism", "spin",
    "classifying-space", "g2") is NOT a held concept -> ungrounded.

  · CONNECTED — the filler LINKS to the rest of the frame: it shares a graph
    in-neighbour with another grounded filler (the same KnownFact / Frame /
    LexEntry — a co-occurrence in a KNOWN relational structure), i.e.
    ``Count(Intersect(InNeighbours(this), InNeighbours(other))) > 0``. A bag of
    unrelated tokens has no shared structure -> disconnected. (A lone grounded
    filler has nothing to connect to and is coherent by grounding alone.)

  coherence = Σ (grounded AND connected, per filler) / (total content fillers)
            ∈ [0, 1]

evaluated as ONE Term-tree on the substrate. A CONSTRUCTION match (an
instantiated known structure — e.g. the seeded ``relation`` "X is the N of Y")
short-circuits to 1.0: matching a known construction IS coherence-by-structure.

  "what is the capital of France?"  -> capital & france grounded + share the
      KnownFact -> connected -> HIGH (and the relation construction matches -> 1.0)
  "the 12th Spin bordism of the classifying space of G2" -> bordism/spin/... not
      held -> ungrounded -> LOW (the agent KNOWS it doesn't understand here)

THE TERM-TREE is stored once as a graph-resident Concept (feature_kind=
"coherence", composed_by="agent") — the agent's general coherence SCHEMA — and
``coherence(substrate, frame)`` INSTANTIATES it with the frame's fillers (baking
each filler into a Lit, exactly as compose_order_n_features bakes its
sample_attrs) and evaluates it natively.

HONEST DSL-EXPRESSIVENESS NOTE
------------------------------
Every piece of the score is a native Term: NodesWhere/Exists ground a filler,
InNeighbours/Intersect/Count test connectivity, IfThenElse gates grounded-AND-
connected to 1/0, Sum aggregates, Div normalises. The ONLY Python is
world-adapter glue: reading the frame's filler strings and baking them into Lit
leaves of the tree (mechanical translation, the same kind order_n_concepts does
with sample_attrs) and choosing WHICH fillers are content vs WH/number (an
I/O-boundary read of the frame, no arithmetic). The number itself is the engine's.

See domains/order_n_concepts.py (the compose+store+evaluate-natively pattern),
domains/dynamic_depth.py (the relevance threshold the abstain reads), CLAUDE.md.
"""
from __future__ import annotations

from typing import Any, Optional

try:
    from domains import interrogative_reference as _ireg
    _WH = set(_ireg.ALL_PLACEHOLDERS)
except Exception:  # pragma: no cover
    _WH = {"?WHO", "?WHAT", "?WHERE", "?WHEN", "?WHY", "?HOW"}

# The content roles a frame fills (mirrors conversation_world._FACT_SLOTS, minus
# tense/speech_act which are not content). The coherence judgement reads exactly
# the slots the QA match reads.
CONTENT_SLOTS = ("event", "agent", "patient", "location", "recipient",
                 "instrument", "source", "beneficiary", "topic",
                 "time", "cause", "manner", "standard")


# ---------------------------------------------------------------------------
# The DSL term builders — pure JSON Term-tree construction (no evaluation here).
# These ARE the agent's composition; the engine evaluates the result.
# ---------------------------------------------------------------------------

def _lit(v):
    return {"type": "Lit", "value": v}


def _concept_nodes(filler: str):
    """NodesWhere(Concept, name == filler) — the held-concept lookup."""
    return {"type": "NodesWhere", "node_type": "Concept",
            "attr_key": "name", "value": _lit(filler)}


def _grounded(filler: str):
    """Exists a Concept node named `filler` -> the agent HOLDS this content."""
    return {"type": "Exists", "source": _concept_nodes(filler),
            "var_name": "_n", "predicate": _lit(True)}


def _pick_concept(filler: str):
    """One held Concept node for `filler` (for its graph neighbourhood)."""
    return {"type": "Pick", "source": _concept_nodes(filler)}


def _shared_in_neighbours_count(a: str, b: str):
    """Count of graph in-neighbours SHARED by the two filler-concepts — the
    KnownFact / Frame / LexEntry they CO-OCCUR in. > 0 ⇒ they instantiate a
    known relational structure together (CONNECTED)."""
    return {"type": "Count", "source": {"type": "Intersect",
            "a": {"type": "InNeighbours", "node": _pick_concept(a)},
            "b": {"type": "InNeighbours", "node": _pick_concept(b)}}}


def _connected(filler: str, others: list[str]):
    """The filler is CONNECTED iff it shares an in-neighbour with ANY other
    content filler (Σ shared-in-neighbour counts over the others) > 0. With NO
    other filler, a grounded filler is coherent by grounding alone (Lit True)."""
    if not others:
        return _lit(True)
    total = {"type": "Plus",
             "items": [_shared_in_neighbours_count(filler, o) for o in others]}
    return {"type": "Gt", "a": total, "b": _lit(0)}


def _filler_coherent(filler: str, others: list[str]):
    """1 if the filler is GROUNDED AND CONNECTED, else 0 — gated natively by
    IfThenElse over the grounded ∧ connected predicate."""
    cond = {"type": "And",
            "items": [_grounded(filler), _connected(filler, others)]}
    return {"type": "IfThenElse", "cond": cond, "then": _lit(1.0),
            "other": _lit(0.0)}


def coherence_term(fillers: list[str]):
    """Compose the FULL coherence Term-tree for a frame's content fillers:

        coherence = ( Σ_f  [grounded(f) ∧ connected(f, others)] )  /  |fillers|

    a single Term the engine evaluates to a float in [0,1]. Empty content -> 0.0
    (nothing to ground -> the agent has comprehended nothing). One native tree;
    no Python sums the per-filler verdicts — Plus/Div do."""
    if not fillers:
        return _lit(0.0)
    per = []
    for i, f in enumerate(fillers):
        others = [g for j, g in enumerate(fillers) if j != i]
        per.append(_filler_coherent(f, others))
    numer = per[0] if len(per) == 1 else {"type": "Plus", "items": per}
    return {"type": "Div", "a": numer, "b": _lit(float(len(fillers)))}


# ---------------------------------------------------------------------------
# Store the agent's coherence SCHEMA as a graph-resident composed-by:agent
# Concept (the order_n_concepts.compose_* idiom), once.
# ---------------------------------------------------------------------------

SCHEMA_NAME = "coherence_grounded_connected"


def compose_coherence_concept(substrate) -> Optional[Any]:
    """Mint (idempotently) the graph-resident Concept that records the agent's
    coherence schema: feature_kind="coherence", composed_by="agent", carrying a
    canonical 2-filler example Term-tree (over Lit placeholders) so the schema is
    inspectable as graph DATA — like a compose_order_n_features Concept. The
    per-frame instantiation happens in coherence(); this node is the agent's
    stored understanding. Returns the concept id (or None)."""
    for c in substrate.nodes("Concept"):
        a = substrate.node(c)["attrs"]
        if a.get("name") == SCHEMA_NAME and a.get("feature_kind") == "coherence":
            return c
    example = coherence_term(["_filler_a", "_filler_b"])
    try:
        return substrate.add_node("Concept", {
            "name": SCHEMA_NAME, "feature_kind": "coherence",
            "composed_by": "agent", "origin": "comprehension",
            "definition": ("a frame coheres iff each content filler is GROUNDED "
                           "(a held Concept) AND CONNECTED (shares a graph "
                           "in-neighbour with another filler); "
                           "coherence = grounded-and-connected / total"),
            "predicate": example})
    except Exception:
        return None


# ---------------------------------------------------------------------------
# The public entry: evaluate the composed tree on a frame, natively.
# ---------------------------------------------------------------------------

def content_fillers(frame: dict[str, Any]) -> list[str]:
    """The frame's CONTENT fillers: distinct string slot values that are not a
    WH placeholder and not a bare number. An I/O-boundary read of the frame (no
    arithmetic) — these become the Lit leaves of the composed tree."""
    out: list[str] = []
    seen: set = set()
    for slot in CONTENT_SLOTS:
        v = frame.get(slot)
        if not isinstance(v, str):
            continue
        v = v.strip()
        if not v or v in _WH:
            continue
        # a bare number (or numeric token) is a VALUE, not a held concept to
        # ground — skip it (it neither grounds nor disqualifies the frame).
        if v.replace(".", "", 1).replace("-", "", 1).isdigit():
            continue
        low = v.lower()
        if low in seen:
            continue
        seen.add(low)
        out.append(low)
    return out


def coherence(substrate, frame: dict[str, Any],
              construction_matched: bool = False) -> float:
    """The agent's coherence VALUE for a comprehended frame, in [0,1], COMPUTED
    BY THE ENGINE: compose the coherence Term-tree for the frame's content
    fillers and evaluate it via substrate.evaluate (NOT a Python sum). A
    construction match short-circuits to 1.0 — an instantiated known structure
    is coherent by construction. Empty content -> 0.0 (nothing comprehended).

    The Python here only reads the frame's filler strings and bakes them into
    the tree's Lit leaves (mechanical, order_n_concepts-style); the float is the
    substrate's."""
    if construction_matched:
        return 1.0
    fillers = content_fillers(frame)
    if not fillers:
        return 0.0
    term = coherence_term(fillers)
    try:
        v = substrate.evaluate(term, {})
    except Exception:
        return 0.0
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


__all__ = ["CONTENT_SLOTS", "SCHEMA_NAME", "coherence_term", "content_fillers",
           "compose_coherence_concept", "coherence"]
