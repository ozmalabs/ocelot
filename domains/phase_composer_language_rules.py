"""Phase-composer rules for context-weighted lexical inference.

Per CLAUDE.md: the agent is Rust, Python is a world adapter. The
language-world refactor moved the "what concept does this unknown
word denote?" decision OUT of Python and into graph-resident Rules
that fire on UnknownToken nodes via a has_unknown trigger edge from
the phase_composer_language_trigger Microtheory — the same pattern
phase_composer_rules.py (commit aef7486) established for Term-tree
composition.

WHAT THE WORLD ADAPTER PUTS IN THE GRAPH

For each held-out content word the substrate has no lexicon entry
for, the LanguageWorld creates:

    UnknownToken {
        word: str,              surface form (lowercased for latin)
        slot: str,              "agent" | "patient" | "location" | "event"
                                — mechanical positional hint from the
                                grammar; the world-adapter side is
                                purely surface morphology, no graph
                                reasoning. The rules consume this as
                                their slot guess.
        language: str,          "en" | "es" | "zh" | "ja"
        position: int,          0-based token index in the sentence
        sentence_id: str        opaque id grouping tokens of one sentence
    }

each wired via [trigger_mt, has_unknown, unknown_token] so the rules
match it.

WHAT THE RULES DO

Each rule fires once per UnknownToken whose slot matches the rule's
slot. It walks every Concept node carrying the matching `category`
attr (animate/person/object/event — seeded in conceptual_categories.json
as graph data, replacing the Python ANIMATE_CONCEPTS / OBJECT_CONCEPTS
/ EVENT_CONCEPTS lists). For each such Concept it computes a weight
= 1 + count of prior SemanticFrame nodes whose slot was already filled
by that concept name. Argmax over those weights selects the winning
concept; a LexEntry node is added carrying it.

Per-slot rule = per-slot category selection:

   slot       category(ies) consulted     bonus reasoning
   ---------  --------------------------  -------------------------
   agent      animal ∪ person             selectional restriction:
                                            an agent doer is animate
   patient    object                      selectional restriction:
                                            the affected thing is
                                            inanimate
   location   object                      stays of inanimate locale
   event      event                       events fill the predicate
                                            slot, never noun-like

Each rule's effect chain is:
  1) add_node LexEntry { concept: <argmax term>, surface, language,
                          status: "tentative", source: "context_inferred",
                          weight }
  2) add_edge unknown has_lex new_lex_entry  — marks the unknown as
                                                 resolved so the
                                                 where-clause stops
                                                 firing it.

The where-clause guards against re-fire:
  And([
    Eq(Attr(unknown, "slot"), Lit(<this rule's slot>)),
    Not(Exists(Neighbours(unknown, "has_lex"), "_", Lit(True))),
  ])

ARGMAX-OVER-EMITTED-CANDIDATES — WHAT'S MISSING

The original spec proposed five rules: one to emit a CandidateMeaning
node per (unknown, frame) pair, three to up-weight per
animate/inanimate/event, and a final pick_best_candidate Argmax.
That five-rule pipeline does NOT cleanly express in the present rule
engine because:

  (1) The matcher fires the same (unknown, frame) binding once per
      tick — but AddNode always counts as progress, so a CandidateMeaning
      rule re-emits its candidate every tick without a dedup guard.
      We'd need either a "no-progress-when-equivalent-node-exists"
      check (the engine doesn't have it for AddNode), OR a wherein-
      clause that searches for an already-existing CandidateMeaning
      with the same (target_unknown, candidate_concept) pair —
      doable, but pushes the rule into a paragraph-long where-clause
      Term-tree for each of the three boosting rules.

  (2) The SetAttr boost rules (upweight_candidate_with_animate_for_agent
      etc.) need to *re-fire* on a CandidateMeaning EACH tick at most
      once. That works (SetAttr to the same value isn't progress), but
      multiple slot-category boosts compose only if the where-clause
      reads the candidate's current weight + adds a delta. The
      "delta-applied" guard then also belongs in the where, or the
      boost re-applies every tick.

  (3) Argmax over an emitted-CandidateMeaning set is expressible
      (Argmax+NodesWhere+Attr — already done below in the SINGLE-rule
      form), so step 5 alone is fine. It's the staging through 3+
      intermediate-node rules that incurs the dedup tax.

The single-rule-per-slot form collapses the pipeline: no intermediate
nodes, no boost rules, no dedup tax. The CandidateMeaning + boost +
pick-best decomposition is the "good factoring" the original spec
wanted but ALSO requires an `add_node_if_not_present` semantic
(or equivalently "AddNode is only progress when no Node with these
attrs exists") — that's the missing primitive. With it the 5-rule
form is exactly as clean as the spec's prose; without it the 1-rule
form is what fits the engine cleanly.

CONCEPTUAL CATEGORY ATTRS

The category seed is `domain_data/conceptual_categories.json` — tiny, only
the concepts the held-out demo touches. Real coverage of "what is
animate / what is an object" should be self-derived (the LLM teacher
emits a `category` per grounded concept, or the substrate derives
it from a hypernym/is_a edge chain).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Term-JSON helpers — same shape as phase_composer_rules.py.
# ---------------------------------------------------------------------------


def _lit(value: Any) -> dict:
    return {"type": "Lit", "value": value}


def _var(name: str) -> dict:
    return {"type": "Var", "name": name}


def _attr(node_term: dict, key: str) -> dict:
    return {"type": "Attr", "node": node_term, "key": key}


def _computed(term: dict) -> dict:
    return {"__term__": term}


def _and(items: list) -> dict:
    return {"type": "And", "items": items}


def _or(items: list) -> dict:
    return {"type": "Or", "items": items}


def _not(arg: dict) -> dict:
    return {"type": "Not", "arg": arg}


def _eq(a: dict, b: dict) -> dict:
    return {"type": "Eq", "a": a, "b": b}


def _plus(items: list) -> dict:
    return {"type": "Plus", "items": items}


def _count(source: dict) -> dict:
    return {"type": "Count", "source": source}


def _argmax(source: dict, var_name: str, value: dict,
            default: dict | None = None) -> dict:
    out = {"type": "Argmax", "source": source, "var_name": var_name,
           "value": value}
    if default is not None:
        out["default"] = default
    return out


def _exists(source: dict, var_name: str, predicate: dict) -> dict:
    return {"type": "Exists", "source": source, "var_name": var_name,
            "predicate": predicate}


def _neighbours(node: dict, edge_type: str | None = None) -> dict:
    out = {"type": "Neighbours", "node": node}
    if edge_type is not None:
        out["edge_type"] = edge_type
    return out


def _nodes_where(node_type: str, attr_key: str, value: dict) -> dict:
    return {"type": "NodesWhere", "node_type": node_type,
            "attr_key": attr_key, "value": value}


def _union(a: dict, b: dict) -> dict:
    return {"type": "Union", "a": a, "b": b}


def _pick(source: dict) -> dict:
    """First element of `source`, or None when empty."""
    return {"type": "Pick", "source": source}


def _if(cond: dict, then: dict, other: dict) -> dict:
    return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}


def _in(member: dict, container: dict) -> dict:
    return {"type": "In", "member": member, "container": container}


# ---------------------------------------------------------------------------
# Microtheory + production setup.
# ---------------------------------------------------------------------------


def _find_or_create_mt(substrate, name: str):
    for n in substrate.nodes("Microtheory"):
        if substrate.node(n)["attrs"].get("name") == name:
            return n
    return substrate.add_node("Microtheory", {
        "name": name,
        "description": ("trigger Mt for phase_composer_language rules — "
                        "wires UnknownToken via has_unknown."),
    })


def _open_productions(substrate) -> None:
    """Open the productions the rules' match + effect edges need so the
    Rust grammar admits them. Idempotent (re-add swallowed)."""
    prods = [
        # trigger -has_unknown→ unknown
        ("Microtheory", "has_unknown", "UnknownToken"),
        # unknown -has_lex→ lex_entry (effect edge, marks resolution)
        ("UnknownToken", "has_lex", "LexEntry"),
        # lex_entry -entry_concept→ the newly-grounded Concept
        ("LexEntry", "entry_concept", "Concept"),
    ]
    for src_type, et, tgt_type in prods:
        try:
            substrate.add_production({
                "src": {"type": src_type, "var": "a"},
                "edge_type": et,
                "tgt": {"type": tgt_type, "var": "b"},
                "where": None,
                "weight": {"type": "Lit", "value": 1.0},
                "provenance": "phase_composer_language_rules",
            })
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Seed loader — small static category data.
# ---------------------------------------------------------------------------


def _load_category_seed(substrate) -> int:
    """Load domain_data/conceptual_categories.json into `substrate`. Idempotent
    against existing Concept nodes with the same name (we set `category`
    via SetAttr if the Concept already exists, else add it)."""
    seed_path = (Path(__file__).resolve().parent.parent
                 / "domain_data" / "conceptual_categories.json")
    if not seed_path.exists():
        return 0
    with seed_path.open() as f:
        manifest = json.load(f)

    # Build a name -> existing-NodeID index so we can reuse / merge.
    existing: dict[str, Any] = {}
    for cid in substrate.nodes("Concept"):
        attrs = substrate.node(cid)["attrs"]
        n = attrs.get("name")
        if isinstance(n, str):
            existing[n] = cid

    # Index existing RolePrior nodes by slot so they're not re-added.
    existing_priors: set[Any] = set()
    for rid in substrate.nodes("RolePrior"):
        slot = substrate.node(rid)["attrs"].get("slot")
        if isinstance(slot, str):
            existing_priors.add(slot)

    loaded = 0
    for entry in manifest.get("nodes", []):
        node_type = entry.get("type")
        attrs = dict(entry.get("attrs", {}))
        if node_type == "Concept":
            name = attrs.get("name")
            if not isinstance(name, str):
                continue
            category = attrs.get("category")
            if name in existing:
                # Stamp category onto the existing Concept if it lacks one.
                nid = existing[name]
                current = substrate.node(nid)["attrs"].get("category")
                if current != category and isinstance(category, str):
                    try:
                        substrate.set_attr(nid, "category", category)
                        loaded += 1
                    except Exception:
                        pass
            else:
                substrate.add_node("Concept", attrs)
                loaded += 1
        elif node_type == "RolePrior":
            # Generic slot -> category prior, graph-resident. Idempotent
            # against an already-loaded prior for the same slot.
            slot = attrs.get("slot")
            if not isinstance(slot, str) or slot in existing_priors:
                continue
            substrate.add_node("RolePrior", attrs)
            existing_priors.add(slot)
            loaded += 1
        else:
            # Skip comment / unknown entries silently.
            continue
    return loaded


# ---------------------------------------------------------------------------
# Category-inference Term-tree builder — TYPED new-concept grounding.
# ---------------------------------------------------------------------------
#
# The previous form did Argmax over EXISTING category-matching Concepts
# weighted by SemanticFrame recurrence — i.e. it SUBSTITUTED the nearest
# known concept (dog → cat). We replace that with TYPING: infer the
# CATEGORY an unknown word should have from context, then GROUND A NEW
# concept named by the token's `lemma` carrying that category. "John said
# hello" types `john` as a person NAME even though no `john`-the-agent was
# ever substituted; "the dog chased the ball" grounds `dog`{animal},
# `chase`{event}, `ball`{object} as genuinely-new concepts.
#
# All of this is graph data read by the rule:
#   * RolePrior nodes (domain_data/conceptual_categories.json) carry the generic
#     slot→category prior + the proper-noun category. NodesWhere reads them.
#   * SelectionalRestriction nodes (materialised by the rule below from
#     grounded SemanticFrames) carry per-predicate slot→category. When the
#     held-out predicate is KNOWN the rule prefers its restriction; when the
#     predicate is unknown (the John/dog demos) it falls back to RolePrior.
#   * Orthographic cues (is_capitalized / has_determiner) are token attrs
#     the world adapter computed mechanically at the I/O boundary; the rule
#     reads them to refine common-vs-proper.


def _role_prior_node(slot: str) -> dict:
    """Pick the RolePrior node for `slot` (a graph node carrying
    `category` + `proper_category`)."""
    return _pick(_nodes_where("RolePrior", "slot", _lit(slot)))


def _selectional_category_term(slot: str) -> dict:
    """Category from the SELECTIONAL RESTRICTION of this sentence's
    predicate, if the predicate is known; else None.

    The world adapter stamps the UnknownToken with `predicate` = the
    resolved event concept of the sentence (a mechanical surface fact —
    the concept the parse already resolved for the verb). We read the
    SelectionalRestriction node for (predicate, slot) and return its
    `category`. SelectionalRestriction nodes are materialised by
    install's restriction-mining rule from grounded SemanticFrames, so
    this is pure graph data.

    Pick over the NodesWhere(SelectionalRestriction, predicate, P) set,
    then a second filter on slot via In-membership is awkward in one
    NodesWhere (two attr keys). We encode the (predicate, slot) pair as
    a single `key` attr = "<predicate>|<slot>" on the restriction node
    so a single NodesWhere selects it."""
    key = _string_concat([
        _attr(_var("unknown"), "predicate"),
        _lit("|"),
        _lit(slot),
    ])
    restr = _pick(_nodes_where_dyn("SelectionalRestriction", "key", key))
    return _attr(restr, "category")


def _base_category_term(slot: str) -> dict:
    """Category before orthographic refinement: selectional restriction
    of the (known) predicate if present, else the generic RolePrior
    category for the slot."""
    prior = _role_prior_node(slot)
    prior_cat = _attr(prior, "category")
    sel_cat = _selectional_category_term(slot)
    # Coalesce: prefer the selectional category when it resolved to a
    # non-None value (predicate known + restriction mined); else the
    # generic prior. IfThenElse on the truthiness of sel_cat.
    return _if(sel_cat, sel_cat, prior_cat)


def _category_term(slot: str) -> dict:
    """Full category inference for an UnknownToken in `slot`.

    proper-noun refinement: a capitalized token with NO determiner is a
    NAME → use the RolePrior's `proper_category` (e.g. agent → person).
    Otherwise use the base category (selectional restriction or generic
    prior)."""
    prior = _role_prior_node(slot)
    proper_cat = _attr(prior, "proper_category")
    is_proper = _and([
        _eq(_attr(_var("unknown"), "is_capitalized"), _lit(True)),
        _eq(_attr(_var("unknown"), "has_determiner"), _lit(False)),
    ])
    return _if(is_proper, proper_cat, _base_category_term(slot))


def _proper_flag_term() -> dict:
    """True iff the token is a proper noun (capitalized, no determiner)."""
    return _if(
        _and([
            _eq(_attr(_var("unknown"), "is_capitalized"), _lit(True)),
            _eq(_attr(_var("unknown"), "has_determiner"), _lit(False)),
        ]),
        _lit(True),
        _lit(False),
    )


def _string_concat(parts: list) -> dict:
    return {"type": "StringConcat", "parts": parts}


def _nodes_where_dyn(node_type: str, attr_key: str, value_term: dict) -> dict:
    """NodesWhere with a COMPUTED value term (vs a literal). The
    JSON schema for NodesWhere takes `value` as a child term, so a
    computed value is just another term subtree."""
    return {"type": "NodesWhere", "node_type": node_type,
            "attr_key": attr_key, "value": value_term}


# ---------------------------------------------------------------------------
# Selectional-restriction mining rule — materialise SelectionalRestriction
# nodes from grounded SemanticFrames.
# ---------------------------------------------------------------------------


def _install_selectional_restriction_rules(substrate) -> list:
    """For each grounded SemanticFrame with a known event + an agent or
    patient filler, materialise a SelectionalRestriction node
    {predicate, slot, category, key="<predicate>|<slot>"} carrying the
    CATEGORY of the filler concept. AddNodeIfAbsent dedups on the full
    attr set so the rule is idempotent across ticks.

    The filler's category is read from the matching Concept node. We
    match: frame -frame_event-> evt_concept (gives predicate name), and
    frame -frame_role[role=slot]-> filler_concept (gives category). The
    role lives on the EDGE attr; matching on edge attrs needs a where
    over the edge. To keep this in the engine's vocabulary we instead
    mine from the frame's flat `agent`/`patient` attrs (the world
    adapter copies meaning keys onto the SemanticFrame node) joined to
    the Concept index by name.

    Two rules: one for agent, one for patient. Each:
      match SemanticFrame
      where  the frame has a non-None event AND a non-None <slot> AND a
             Concept named <slot-filler> with a category exists
      effect add_node_if_absent SelectionalRestriction {predicate=event,
             slot, category=<filler concept's category>,
             key="<event>|<slot>"}
    """
    installed: list = []
    for slot in ("agent", "patient"):
        # filler concept node = Pick(NodesWhere(Concept, name, frame.<slot>))
        filler = _pick(_nodes_where_dyn(
            "Concept", "name", _attr(_var("frame"), slot)))
        category_term = _attr(filler, "category")
        key_term = _string_concat([
            _attr(_var("frame"), "event"), _lit("|"), _lit(slot)])

        where = _and([
            # frame carries an event predicate
            _not(_eq(_attr(_var("frame"), "event"), _lit(None))),
            # frame carries a filler for this slot
            _not(_eq(_attr(_var("frame"), slot), _lit(None))),
            # the filler concept exists AND has a category we can copy
            _not(_eq(category_term, _lit(None))),
        ])

        rule = {
            "name": f"mine_selectional_{slot}",
            "match": [["frame", "of_language", "lang"]],
            "where": where,
            "effects": [
                ["add_node_if_absent", "restr", "SelectionalRestriction", {
                    "predicate": _computed(_attr(_var("frame"), "event")),
                    "slot":      slot,
                    "category":  _computed(category_term),
                    "key":       _computed(key_term),
                }],
            ],
        }
        try:
            installed.append(substrate.add_rule(rule))
        except Exception as e:  # noqa: BLE001
            print(f"  WARNING: rule install failed: {rule['name']}: {e}")
    return installed


# ---------------------------------------------------------------------------
# Rule installer.
# ---------------------------------------------------------------------------


_SLOTS = ("agent", "patient", "location", "event")


def install_phase_composer_language_rules(substrate) -> list:
    """Install the TYPED new-concept grounding rules — one per slot.

    Each rule fires on an UnknownToken whose `slot` matches; it
      1. infers the token's CATEGORY (selectional restriction of a known
         predicate → else generic RolePrior → refined by orthographic
         proper-noun cue), all read from graph data;
      2. GROUNDS A NEW Concept named by the token's `lemma` carrying that
         category (+ proper flag), idempotently via add_node_if_absent;
      3. emits a LexEntry mapping surface→that NEW concept and wires
         entry_concept to the Concept node;
      4. wires has_lex from the unknown to the LexEntry so the where
         stops it re-firing.

    No substitution: the grounded concept is the WORD ITSELF, typed.
    """
    _open_productions(substrate)
    _load_category_seed(substrate)
    _find_or_create_mt(substrate, "phase_composer_language_trigger")
    installed = _install_selectional_restriction_rules(substrate)

    lemma = _computed(_attr(_var("unknown"), "lemma"))
    for slot in _SLOTS:
        category_term = _computed(_category_term(slot))
        proper_term = _computed(_proper_flag_term())

        # Guard: the unknown's slot is this rule's slot, AND it has no
        # has_lex neighbour yet, AND it carries a lemma to name the
        # new concept (defensive — the adapter always sets it).
        where = _and([
            _eq(_attr(_var("unknown"), "slot"), _lit(slot)),
            _not(_exists(
                _neighbours(_var("unknown"), "has_lex"),
                "_lex",
                _lit(True),
            )),
            _not(_eq(_attr(_var("unknown"), "lemma"), _lit(None))),
        ])

        rule = {
            "name": f"type_unknown_{slot}",
            "match": [["trig", "has_unknown", "unknown"]],
            "where": where,
            "effects": [
                # 1+2. Ground a NEW concept named by the lemma, typed.
                ["add_node_if_absent", "new_concept", "Concept", {
                    "name":     lemma,
                    "category": category_term,
                    "proper":   proper_term,
                    "source":   "context_typed",
                }],
                # 3. LexEntry surface→the new concept (concept = lemma).
                ["add_node", "new_lex", "LexEntry", {
                    "language": _computed(_attr(_var("unknown"), "language")),
                    "surface":  _computed(_attr(_var("unknown"), "word")),
                    "concept":  lemma,
                    "category": category_term,
                    "proper":   proper_term,
                    "status":   "tentative",
                    "source":   "context_typed",
                    "weight":   1.0,
                    "slot":     slot,
                }],
                ["add_edge", "new_lex", "entry_concept", "new_concept", {}],
                # 4. Mark the unknown resolved.
                ["add_edge", "unknown", "has_lex", "new_lex", {}],
            ],
        }
        try:
            installed.append(substrate.add_rule(rule))
        except Exception as e:  # noqa: BLE001
            print(f"  WARNING: rule install failed: {rule['name']}: {e}")
    return installed


def wire_unknown(substrate, unknown_nid) -> bool:
    """Wire an UnknownToken to phase_composer_language_trigger via
    has_unknown. Idempotent."""
    trigger = _find_or_create_mt(substrate, "phase_composer_language_trigger")
    existing = substrate.in_neighbours(unknown_nid, "has_unknown")
    if trigger in existing:
        return False
    try:
        substrate.add_edge(trigger, "has_unknown", unknown_nid, {})
        return True
    except Exception:
        return False
