"""Graph-resident word-sense / translation SELECTION — the decision as a Rule.

Per CLAUDE.md: a decision over graph state is a Rule, not Python. The
word-sense / translation pick used to live in ``dictionary_lexicon`` as
Python arithmetic + argmax (``score_sense`` combined the features into a
``total``; ``pick_sense`` / ``pick_best_concept`` argmaxed over candidates).
That combine+select IS the decision. This module moves it into:

  * a SCORE Term-tree (``score_term``) that reads a SenseCandidate node's
    mechanically-measured feature attrs + the slot's RolePrior expected
    categories (graph data) and computes the combined score, and
  * a ``select_sense`` Rule that, per SenseSelection node, Argmaxes the score
    over its ``has_candidate`` SenseCandidate neighbours and writes the
    winner's ``english_word`` / ``sense`` back onto the selection node.

The exact same shape as the existing typing rules in
``phase_composer_language_rules.py`` (Argmax + NodesWhere/Neighbours + Attr +
IfThenElse). NO Python ``if/else`` / score arithmetic / argmax decides the
winner — the rule does.

THE CLEAN SPLIT (mirrors the typing-rules move, commit ea508e33)

  Boundary (Python, allowed): external I/O + mechanical MEASUREMENT only.
    Fetching candidate senses/translations from WordNet/Wiktionary is I/O.
    Computing a candidate's FEATURES — its substrate category (lexname→map),
    its Lesk overlap COUNT (|gloss-words ∩ context-words|), its sense rank,
    its SemCor freq — is mechanical measurement. Grounding those as node
    attrs is allowed (same as grounding `category` in the typing work).

  Rule (graph-resident, THE DECISION): combine the features into a score
    and Argmax to select the winner.

SCRATCH SUBSTRATE. The selection runs on a small dedicated substrate (one
SenseSelection + its SenseCandidate fan-out, ticked once) so it neither
perturbs nor is perturbed by the world graph mid-ingest. The decision still
lives in a real installed Rule that fires on ``tick()`` — the substrate it
runs on is an implementation detail of the boundary, not the locus of the
decision.

SCORE WEIGHTS (graph data on the rule's score Term, the SAME constants the
old Python used so the pick is byte-identical):
  * category fit   : +100 when the candidate's category ∈ the slot's expected
                     categories (RolePrior.expected_categories, graph data).
  * Lesk overlap   : +5 per overlapping content word (the measured count).
  * rank prior     : +1/(1+rank) — earlier sense slightly preferred; the whole
                     range (≤1) is < one Lesk hit, so it only breaks ties.
  * freq nudge     : +0.001 per SemCor count — the finest tiebreak, scaled so
                     it never reorders by itself.
The Argmax tiebreak is "first encountered"; the boundary grounds candidates in
(candidate-order, sense-rank) order, so an uninformative context reproduces
WordNet's sense-1 / Wiktionary-salience ordering exactly as the old stable key
``(-total, cand_index, rank)`` did.
"""
from __future__ import annotations

from typing import Any, Optional


# ---------------------------------------------------------------------------
# Term-JSON helpers — same shape as phase_composer_language_rules.py.
# ---------------------------------------------------------------------------


def _lit(v: Any) -> dict:
    return {"type": "Lit", "value": v}


def _var(n: str) -> dict:
    return {"type": "Var", "name": n}


def _attr(node: dict, key: str) -> dict:
    return {"type": "Attr", "node": node, "key": key}


def _computed(term: dict) -> dict:
    return {"__term__": term}


def _plus(items: list) -> dict:
    return {"type": "Plus", "items": items}


def _times(items: list) -> dict:
    return {"type": "Times", "items": items}


def _div(a: dict, b: dict) -> dict:
    return {"type": "Div", "a": a, "b": b}


def _eq(a: dict, b: dict) -> dict:
    return {"type": "Eq", "a": a, "b": b}


def _and(items: list) -> dict:
    return {"type": "And", "items": items}


def _in(member: dict, container: dict) -> dict:
    return {"type": "In", "member": member, "container": container}


def _if(cond: dict, then: dict, other: dict) -> dict:
    return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}


def _pick(source: dict) -> dict:
    return {"type": "Pick", "source": source}


def _nodes_where_dyn(node_type: str, attr_key: str, value_term: dict) -> dict:
    return {"type": "NodesWhere", "node_type": node_type,
            "attr_key": attr_key, "value": value_term}


def _neighbours(node: dict, edge_type: str) -> dict:
    return {"type": "Neighbours", "node": node, "edge_type": edge_type}


def _argmax(source: dict, var_name: str, value: dict) -> dict:
    return {"type": "Argmax", "source": source, "var_name": var_name,
            "value": value}


def _exists(source: dict, var_name: str, predicate: dict) -> dict:
    return {"type": "Exists", "source": source, "var_name": var_name,
            "predicate": predicate}


# ---------------------------------------------------------------------------
# Score weights — graph-resident constants in the score Term. Identical to the
# old dictionary_lexicon._W_* so the rule reproduces the Python pick.
# ---------------------------------------------------------------------------

_W_CATEGORY = 100.0
_W_LESK = 5.0
_W_RANK = 1.0
_W_FREQ = 0.001


# ---------------------------------------------------------------------------
# The SCORE Term-tree — reads a SenseCandidate's measured feature attrs +
# the slot's RolePrior expected categories. THE COMBINE (was score_sense's
# arithmetic).
# ---------------------------------------------------------------------------


def _expected_categories_term(sel: dict) -> dict:
    """The expected-category SET for this selection's slot, read from the
    RolePrior graph node (RolePrior.expected_categories). Pick the RolePrior
    whose `slot` equals the SenseSelection's `slot`, then read its
    `expected_categories` list attr."""
    rp = _pick(_nodes_where_dyn("RolePrior", "slot", _attr(sel, "slot")))
    return _attr(rp, "expected_categories")


def score_term(cand_var: str = "cand", sel_var: str = "sel") -> dict:
    """The combined score for a SenseCandidate bound to `cand_var`, given the
    SenseSelection bound to `sel_var`. Reads only graph node attrs:

        100 * [category ∈ slot.expected_categories]
      +   5 * lesk_overlap
      +   1 * 1/(1 + rank)
      + 0.001 * freq
    """
    cand = _var(cand_var)
    sel = _var(sel_var)
    cat_hit = _if(
        _in(_attr(cand, "category"), _expected_categories_term(sel)),
        _lit(1.0), _lit(0.0))
    rank_prior = _div(_lit(1.0),
                      _plus([_lit(1.0), _attr(cand, "rank")]))
    return _plus([
        _times([_lit(_W_CATEGORY), cat_hit]),
        _times([_lit(_W_LESK), _attr(cand, "lesk_overlap")]),
        _times([_lit(_W_RANK), rank_prior]),
        _times([_lit(_W_FREQ), _attr(cand, "freq")]),
    ])


def _winner_argmax(field: str, sel_var: str = "sel") -> dict:
    """Argmax over the selection's has_candidate SenseCandidates of the score
    Term, returning the winner's `field` attr. THE SELECT."""
    am = _argmax(_neighbours(_var(sel_var), "has_candidate"),
                 "cand", score_term("cand", sel_var))
    return _attr(am, field)


# ---------------------------------------------------------------------------
# Productions + rule install.
# ---------------------------------------------------------------------------


def _open_productions(substrate) -> None:
    prods = [
        ("Microtheory", "has_selection", "SenseSelection"),
        ("SenseSelection", "has_candidate", "SenseCandidate"),
    ]
    for src_t, et, tgt_t in prods:
        try:
            substrate.add_production({
                "src": {"type": src_t, "var": "a"},
                "edge_type": et,
                "tgt": {"type": tgt_t, "var": "b"},
                "where": None,
                "weight": {"type": "Lit", "value": 1.0},
                "provenance": "sense_selection_rules",
            })
        except Exception:
            pass


_TRIGGER_MT = "sense_selection_trigger"


def install_sense_selection_rules(substrate) -> list:
    """Install the graph-resident SELECTION rule. Fires once per
    SenseSelection that (a) is not yet resolved and (b) has at least one
    candidate; Argmaxes the score Term over its candidates and writes the
    winner back. Idempotent (the where-guard stops re-fire; AddRule of the
    same name is swallowed by the engine / our try)."""
    _open_productions(substrate)
    for n in substrate.nodes("Microtheory"):
        if substrate.node(n)["attrs"].get("name") == _TRIGGER_MT:
            break
    else:
        substrate.add_node("Microtheory", {
            "name": _TRIGGER_MT,
            "description": "trigger Mt for sense_selection rules.",
        })

    sel = _var("sel")
    where = _and([
        _eq(_attr(sel, "resolved"), _lit(None)),
        _exists(_neighbours(sel, "has_candidate"), "_c", _lit(True)),
    ])
    rule = {
        "name": "select_sense",
        "match": [["trig", "has_selection", "sel"]],
        "where": where,
        "effects": [
            ["set_attr", "sel", "winner_concept",
             _computed(_winner_argmax("english_word"))],
            ["set_attr", "sel", "winner_sense",
             _computed(_winner_argmax("sense"))],
            ["set_attr", "sel", "winner_rank",
             _computed(_winner_argmax("rank"))],
            # Mark resolved so the where stops re-firing.
            ["set_attr", "sel", "resolved", _computed(_lit(True))],
        ],
    }
    installed: list = []
    try:
        installed.append(substrate.add_rule(rule))
    except Exception as e:  # noqa: BLE001
        print(f"  WARNING: rule install failed: select_sense: {e}")
    return installed


# ---------------------------------------------------------------------------
# Boundary helper — ground candidate FEATURES + run the SELECTION rule.
#
# This is world-adapter mechanics: it grounds the mechanically-measured
# features as SenseCandidate nodes, ticks (the rule decides), and reads the
# winner back. No Python decision — the combine + argmax are the rule's.
# ---------------------------------------------------------------------------


# RolePrior expected-category sets are GRAPH DATA — the single source of
# truth is seeds/conceptual_categories.json (each RolePrior carries
# `expected_categories`). The scratch substrate the boundary ticks on loads
# those RolePrior nodes from the seed so the rule reads the same graph data
# the world substrate's typing rules read. No Python copy of the sets.


def _load_role_priors_from_seed(substrate) -> int:
    """Ground the seed's RolePrior nodes (slot + expected_categories) onto
    `substrate` so the selection rule can read them. Reads the same JSON the
    world substrate seeds from; idempotent against an existing prior."""
    import json
    from pathlib import Path
    seed_path = (Path(__file__).resolve().parent.parent
                 / "seeds" / "conceptual_categories.json")
    existing = {substrate.node(r)["attrs"].get("slot")
                for r in substrate.nodes("RolePrior")}
    loaded = 0
    try:
        with seed_path.open() as f:
            manifest = json.load(f)
    except Exception:
        return 0
    for entry in manifest.get("nodes", []):
        if entry.get("type") != "RolePrior":
            continue
        attrs = dict(entry.get("attrs", {}))
        slot = attrs.get("slot")
        if not isinstance(slot, str) or slot in existing:
            continue
        substrate.add_node("RolePrior", attrs)
        existing.add(slot)
        loaded += 1
    return loaded


class _ScratchSelector:
    """A reusable scratch substrate carrying the select_sense rule + the
    RolePrior expected-category nodes. One per process (lazy)."""

    def __init__(self):
        from substrate_rs import _native
        self.s = _native.Substrate()
        install_sense_selection_rules(self.s)
        # Ground the slot→expected-categories priors as graph data.
        self._trigger = None
        for n in self.s.nodes("Microtheory"):
            if self.s.node(n)["attrs"].get("name") == _TRIGGER_MT:
                self._trigger = n
                break
        _load_role_priors_from_seed(self.s)

    def select(self, candidates: list[dict], slot: str) -> Optional[dict]:
        """`candidates` is a list of feature dicts in (cand_order, rank)
        order, each carrying english_word / category / lesk_overlap / rank /
        freq / sense. Grounds them, ticks, returns the winner's feature dict
        (the one whose english_word the rule selected) or None when empty."""
        if not candidates:
            return None
        sel = self.s.add_node("SenseSelection", {"slot": slot})
        by_word_rank: dict[tuple, dict] = {}
        for c in candidates:
            cn = self.s.add_node("SenseCandidate", {
                "english_word": c["english_word"],
                "category": c.get("category") or "?",
                "lesk_overlap": float(c.get("lesk_overlap", 0)),
                "rank": float(c.get("rank", 0)),
                "freq": float(c.get("freq", 0.0)),
                "sense": c.get("sense") or "",
            })
            self.s.add_edge(sel, "has_candidate", cn, {})
            by_word_rank[(c["english_word"], c.get("sense"))] = c
        self.s.add_edge(self._trigger, "has_selection", sel, {})
        try:
            self.s.tick()
        except Exception:
            return None
        attrs = self.s.node(sel)["attrs"]
        win_word = attrs.get("winner_concept")
        win_sense = attrs.get("winner_sense")
        if win_word is None:
            return None
        # Return the original feature dict for the winner (keyed by
        # english_word+sense so callers recover the synset object).
        return by_word_rank.get((win_word, win_sense))


_SELECTOR: Optional[_ScratchSelector] = None


def selector() -> _ScratchSelector:
    global _SELECTOR
    if _SELECTOR is None:
        _SELECTOR = _ScratchSelector()
    return _SELECTOR


def select_winner(candidates: list[dict], slot: str) -> Optional[dict]:
    """Run the graph-resident SELECTION rule over `candidates` (feature dicts)
    and return the winner's feature dict. The combine + argmax are the rule's
    decision; this function only grounds features + reads the result back."""
    return selector().select(candidates, slot)


def score_one(features: dict, slot: str) -> float:
    """Evaluate the graph SCORE Term for ONE candidate's measured features —
    for DIAGNOSTIC display only (the test's score table). The number comes
    from the same graph Term-tree the rule argmaxes, so it is NOT a duplicated
    Python formula: it is the rule's own scoring, evaluated on one node."""
    sel_obj = selector()
    s = sel_obj.s
    sel = s.add_node("SenseSelection", {"slot": slot})
    cn = s.add_node("SenseCandidate", {
        "english_word": features.get("english_word", "?"),
        "category": features.get("category") or "?",
        "lesk_overlap": float(features.get("lesk_overlap", 0)),
        "rank": float(features.get("rank", 0)),
        "freq": float(features.get("freq", 0.0)),
        "sense": features.get("sense") or "",
    })
    s.add_edge(sel, "has_candidate", cn, {})
    val = s.evaluate(score_term("cand", "sel"), {"cand": cn, "sel": sel})
    try:
        return float(val)
    except Exception:
        return 0.0


__all__ = [
    "install_sense_selection_rules",
    "score_term",
    "select_winner",
    "score_one",
    "selector",
]
