"""analogy_search — MECHANICAL host glue for the ANALOGY SEARCH grain.

`SHAPE_AUDIT.md` §2.4, closed here: `domains/analogical_thinking.py`'s
`find_analogies` was a Python triple-nested loop (source concept × target Mts ×
target concept) scoring a set overlap of string tokens at five fixed
abstraction orders — "not one of the five orders consults a concept's edges",
and the whole search / verdict ran in Python. This module makes the search a
first-class graph loop over `seeds/analogy_search.json`, exactly the shape
`domains/meta_shape.py` / `domains/problem_shape.py` already are one grain over.

ARCHITECTURE (CLAUDE.md's rule): every DECISION lives in graph rules or Rust.
This module does exactly three mechanical things:

  1. `concept_signature(sub, concept_node)` — read a Concept's own TYPE, attrs
     AND OUTGOING RELATIONAL EDGES (plus its shape-vocabulary axes) into a
     relation-set signature. Pure destructuring: no conditional over graph
     state, no ranking, no choice. Reading a concept's edges is what makes the
     search work on ARBITRARY SHAPE — a concept with real relational structure
     (causal_influence / has_part / causes / …) is matched on that structure;
     an edge-poor concept falls back to its attrs + vocabulary axes.

  2. `observe(agent, source_mt, target_mts)` — write the target fields'
     concepts as a `ConceptShape` codebook and each source concept as an
     `AnalogyProbe`, then `run_rules()`. The decode / match / systematicity /
     emit decisions are `ap_*` rules; nothing here decides anything.

  3. read-back helpers (`find_analogies` / `think_harder`) that seed probes,
     run the fixpoint, and destructure the `Analogy` nodes the rules emitted.

The systematicity/parallelogram verdict, the shared-structure specificity, and
the cross-field scan are all in the graph / Rust (`ShapeDecode`, `AntiUnify`,
`FixedCount`, `ToJsonString`, `Count`, `Filter`) — ZERO new Rust, the same
choice `problem_shape` made.
"""
from __future__ import annotations

import json
from typing import Any, Optional

import domains.analogical_thinking as at

#: Node/edge vocabulary the `ap_*` rules match on — mirrors
#: `meta_shape.py`'s `OBSERVATION_TYPE`/`OBSERVED_EDGE`.
PROBE_TYPE = "AnalogyProbe"
CODEBOOK_TYPE = "ConceptShape"
OBSERVED_EDGE = "observed_probe"
EMITTED_EDGE = "emitted_analogy"
EPOCH_ATTR = "analogy_codebook_epoch"

#: Field-qualified part-name separator. A `ConceptShape` part is named
#: "field::concept_name" so a source concept can never falsely match a concept
#: in its OWN field (belt-and-braces with `codebook_scope`; see the seed's
#: `ap_decode` comment on the empty-scope hazard).
_SEP = "::"

#: Structural / bookkeeping edges that are NOT part of a concept's relational
#: SHAPE and must be excluded from its signature: the Mt membership edge, the
#: analogy machinery's own edges, and the shape-vocabulary wiring. Everything
#: else outgoing is genuine relational structure and becomes a signature
#: relation — that is the "arbitrary shape" surface.
_NON_SHAPE_EDGES = frozenset({
    "has_concept", "observed_probe", "observed_shape", "observed_problem",
    "emitted_analogy", "minted_shape", "minted_problem_shape", "has_principle",
    "about_a", "about_b", "about_goal", "implements",
})


# --------------------------------------------------------------------------- #
# Signature builder — the QUALIA-SPACE surface.
#
# A concept's signature is its COORDINATES in qualia space: a frozenset of
# `(dimension, predicate, value)` 3-tuples. The dimension tag is what makes
# this a SCHEMA and not a flat bag — two relations align only when they sit on
# the SAME qualia dimension, so "made of a switch" (constitutive) never matches
# "used to switch" (telic) just because both mention switching. The dimensions
# are read from the `QualiaDimension` codebook (seeds/qualia_space.json); when
# that seed is absent the builder degrades to an untyped `relational:` /
# `attr:` tagging so the analogy engine still runs (the qualia schema enriches
# the space, it is not required for it to exist).
#
# ONE SPACE: the lexical axes (FORMAL/CONSTITUTIVE/TELIC/AGENTIVE — what a thing
# is/made-of/for/from) and the dynamical axes (valence/commitment/pull/
# activation — what it is LIKE, read off the CAN fields) are tuples in the SAME
# frozenset. A felt concept and a reasoned-about concept differ only in which
# dimensions they light up.
# --------------------------------------------------------------------------- #
def _sub(substrate):
    return getattr(substrate, "s", substrate)


def _node_name(sub, nid) -> str:
    try:
        return str(sub.node(nid)["attrs"].get("name", "")).lower()
    except Exception:
        return ""


def _round_to_vocab(x, quantum: float, half_width: int):
    """The CAN tests' own quantiser (test_can_identity_feedback.py etc.):
    k = round(x/quantum) clamped to ±half_width, returned as the integer step
    k (a discrete coordinate AntiUnify can intersect), or None when x rounds to
    0 — a zero coordinate is the DEFAULT every concept trivially shares and
    would flood the intersection, so it is omitted (absence, not a shared 0)."""
    try:
        k = round(float(x) / quantum)
    except Exception:
        return None
    k = max(-half_width, min(half_width, k))
    return k if k != 0 else None


#: Default concept-relational edge types to read when the substrate does not
#: expose full edge enumeration (`out_edges`) — the native `_native.Substrate`
#: handle has only `neighbours(node, edge_type)`. Union of the edges that occur
#: in the tree AND every edge type the seeded DimensionEdgeRole map types.
_DEFAULT_REL_EDGES = (
    "causal_influence", "causes", "caused_by", "enables", "excites", "inhibits",
    "has_part", "part_of", "made_of", "constitutes", "contains", "member_of",
    "composed_of", "depends_on", "relates_to", "precedes", "before",
    "coherence_rel", "activates", "suppresses", "regulates", "used_for",
    "serves", "gates", "controls", "produces", "creates", "created_by",
    "derived_from", "grounds", "exhibits",
    # the taxonomy backbone the real corpus actually uses (is-a hypernymy)
    "built_from", "genls", "is_a", "kind_of", "subtype_of", "instance_of",
    "isa",
)

#: Cache of the qualia-space codebook read (pure read over unchanging seed
#: data; CLAUDE.md permits caching, the substrate stays source of truth).
_QUALIA_SCHEMA_CACHE: dict = {}


def _qualia_schema(substrate) -> dict:
    """Read the qualia-space codebook off the graph:
      {"edge_role": {edge_type -> dimension},
       "field_axes": [(dimension, attr, quantum, half_width, overlay)],
       "have": bool}
    `have` is False when seeds/qualia_space.json is not installed — the builder
    then falls back to untyped tagging. Mechanical read, no decision."""
    sub = _sub(substrate)
    try:
        dims = list(sub.nodes("QualiaDimension"))
        roles = list(sub.nodes("DimensionEdgeRole"))
    except Exception:
        return {"edge_role": {}, "field_axes": [], "have": False}
    key = (id(sub), len(dims), len(roles))
    cached = _QUALIA_SCHEMA_CACHE.get(key)
    if cached is not None:
        return cached
    edge_role: dict = {}
    for n in roles:
        a = sub.node(n)["attrs"]
        et, dim = a.get("edge_type"), a.get("dimension")
        if et and dim:
            edge_role[str(et)] = str(dim)
    field_axes = []
    for n in dims:
        a = sub.node(n)["attrs"]
        src = str(a.get("source") or "")
        if not src.startswith("field:"):
            continue
        field_axes.append((str(a.get("name")), src.split(":", 1)[1],
                           float(a.get("quantum") or 1.0),
                           int(a.get("half_width") or 1),
                           bool(a.get("overlay"))))
    out = {"edge_role": edge_role, "field_axes": field_axes,
           "have": bool(dims)}
    _QUALIA_SCHEMA_CACHE[key] = out
    return out


def _edge_dimension(schema: dict, edge_type: str) -> str:
    """The qualia dimension a given outgoing edge evidences, from the seeded
    DimensionEdgeRole map. An edge with no seeded role stays on an untyped
    `relational:<edge_type>` axis — still matched, honestly untyped (a
    candidate for later minting into a real qualia role)."""
    return schema["edge_role"].get(edge_type, "relational:%s" % edge_type)


def _outgoing_relations(substrate, concept_node, schema, edge_types=None) -> list:
    """Outgoing relational edges as `(dimension, edge_type, target_type)`
    3-tuples — the concept's relational qualia coordinates. The dimension is
    the edge's seeded lexical role (CONSTITUTIVE/TELIC/AGENTIVE) or an untyped
    `relational:` axis.

    STRUCTURE-MAPPING: the value is the target's TYPE, not its name, so an
    analogy aligns `gates(X)` in one field with `gates(Y)` in another on the
    predicate + dimension regardless of the concrete filler.

    `out_edges(nid)` (TypedGraph) enumerates ALL edge types; else
    `neighbours(nid, et)` over `edge_types` (the native-handle path).
    """
    sub = _sub(substrate)
    out: list = []

    def _tgt_type(tgt) -> str:
        try:
            return str(sub.node(tgt).get("type", "")).lower() or "·"
        except Exception:
            return "·"

    oe = getattr(sub, "out_edges", None)
    if oe is not None:
        try:
            for e in oe(concept_node):
                et = getattr(e.key, "edge_type", None)
                tgt = getattr(e.key, "tgt", None)
                if et is None or tgt is None or et in _NON_SHAPE_EDGES:
                    continue
                out.append((_edge_dimension(schema, str(et).lower()),
                            str(et).lower(), _tgt_type(tgt)))
            return out
        except Exception:
            out = []
    for et in (edge_types or _DEFAULT_REL_EDGES):
        if et in _NON_SHAPE_EDGES:
            continue
        try:
            for tgt in sub.neighbours(concept_node, et):
                out.append((_edge_dimension(schema, str(et).lower()),
                            str(et).lower(), _tgt_type(tgt)))
        except Exception:
            continue
    return out


def _dynamical_relations(substrate, concept_node, schema, overlay: bool) -> list:
    """The concept's CAN-field coordinates as `(dimension, "field", k)`
    3-tuples — the proto-phenomenal "what it is like" axes.

    CRYSTALLISED axes (identity_field → commitment, committed state → valence)
    are ALWAYS included: the concept's STANDING felt shape. LIVE overlay axes
    (external_field → pull, state → activation) are included ONLY when
    `overlay=True` — the "how the agent feels RIGHT NOW" reading. A field that
    rounds to 0 contributes NO tuple (a zero coordinate is the default every
    concept shares; see `_round_to_vocab`), so a never-relaxed concept stays
    dark on the dynamical axes rather than all trivially matching at valence 0.

    This is `h_eff = external + identity` (can_ops.rs) read as coordinates: the
    crystallised term is in the standing signature, the live term is the
    overlay, and their gap is 'I'm not sure how I feel'.
    """
    sub = _sub(substrate)
    try:
        attrs = sub.node(concept_node)["attrs"]
    except Exception:
        return []
    if not schema.get("field_axes"):
        return []
    out: list = []
    for dim, attr_name, quantum, half_width, is_overlay in schema["field_axes"]:
        if is_overlay and not overlay:
            continue
        raw = attrs.get(attr_name)
        if raw is None:
            continue
        k = _round_to_vocab(raw, quantum, half_width)
        if k is None:
            continue
        out.append((dim, "field", k))
    return out


def _vocabulary_relations(substrate, concept_node) -> list:
    """The concept's shape-vocabulary axes as `(dimension, name, slots)`
    3-tuples — the keyword-evidenced role/principle/shape axes, on their own
    `vocab:role|principle|shape` dimensions (not folded into the lexical qualia
    roles: a keyword hit is weaker evidence than a typed edge and is honestly
    labelled). The BOOTSTRAP that keeps the edge-poor booted corpus matchable.
    """
    try:
        reading = at._concept_reading(_sub(substrate), concept_node)
    except Exception:
        return []
    rels: list = []
    for axis in ("role", "principle", "shape"):
        for name, slots in (reading.get(axis) or {}).items():
            rels.append(("vocab:%s" % axis, str(name).lower(),
                         "|".join(sorted(slots)) if slots else "·"))
    return rels


#: CAN MECHANISM BOOKKEEPING attrs that must NOT become `attr:*` coordinates.
#:
#: When a Concept is driven through the native CAN field (the discrete-async
#: update + `can_decay_identity`'s decay/identity rules), those rules WRITE
#: per-Concept counters onto it — an identity-evidence LEDGER and per-rule
#: TICK/EPOCH gates. These are the field's own bookkeeping, NOT qualia content:
#: they are identical (or near-identical) across every concept that has been
#: relaxed the same number of ticks, so the `attr:<key>` catch-all folds them
#: in as NON-DISCRIMINATIVE coordinates that two relaxed concepts spuriously
#: share (identical ledger values => noise that leaks into find_analogies'
#: aligned_dimensions). The felt content the CAN field produces already has a
#: home: `state`/`external_field`/`identity_field` are the DYNAMICAL axes
#: (`_dynamical_relations`, quantised), so excluding the raw counters loses no
#: signal.
#:
#: DERIVED HONESTLY from the seed rule effects (which attrs those rules
#: `set_attr`), not guessed:
#:   * seeds/can_native_reimplementation.json — the Mt epoch `can_tick`; the
#:     Coactivation ledger `noted_tick`/`evidence_confirm`/`evidence_disconfirm`/
#:     `evidence_tick` (on Coactivation NODES, but a Concept can carry the
#:     `evidence_*` family if seeded), and the shape-loop `*_epoch` idiom.
#:   * seeds/can_decay_identity.json — the per-Concept identity ledger
#:     `identity_evidence_confirm`/`identity_evidence_disconfirm`, and the
#:     per-rule tick gates `identity_evidence_tick`, `identity_decay_tick`,
#:     `external_field_decay_tick`, `identity_field_tick`, plus the
#:     event-nudge markers `pending_identity_nudge_target_sigma`/`_recurrence`/
#:     `_epoch` and `identity_nudge_applied_epoch`.
#:
#: The rule is PRINCIPLED (mechanical, over-match-proof), not a frozen list:
#:   (a) any attr ending in `_tick` or `_epoch` — every CAN rule's epoch/gate
#:       counter matches this suffix idiom and nothing a concept carries as
#:       genuine content does;
#:   (b) the evidence-ledger family: `evidence_confirm`/`evidence_disconfirm`
#:       and any `identity_evidence_*` / `evidence_*` counter;
#:   (c) an explicit small set for the few names that fit neither pattern (the
#:       `pending_identity_nudge_target_sigma`/`_recurrence` markers — the
#:       matching `_epoch` sibling is already caught by (a)).
#: `category`/`state`/`external_field`/`identity_field` are handled ABOVE this
#: gate (formal / dynamical axes), so they never reach it. Genuine content —
#: name/definition/why/roles/etc. — matches none of these and is KEPT.
_CAN_BOOKKEEPING_ATTRS = frozenset({
    # identity + causal evidence LEDGERS (counts, not content)
    "identity_evidence_confirm", "identity_evidence_disconfirm",
    "evidence_confirm", "evidence_disconfirm",
    # event-nudge markers whose names carry no `_tick`/`_epoch`/`evidence` cue
    "pending_identity_nudge_target_sigma", "pending_identity_nudge_recurrence",
})


def _is_can_bookkeeping_attr(kl: str) -> bool:
    """True when `kl` (a lowercased attr key) is a native CAN mechanism counter
    — an epoch/tick gate, an evidence-ledger count, or a named nudge marker —
    rather than qualia CONTENT. See `_CAN_BOOKKEEPING_ATTRS` for the honest
    derivation from the seed rule effects and the over-match-proof rationale."""
    if kl.endswith("_tick") or kl.endswith("_epoch"):
        return True  # every CAN rule's epoch/gate counter; no content uses it
    if kl in _CAN_BOOKKEEPING_ATTRS:
        return True
    # the evidence-ledger family (identity_evidence_*, evidence_*) — Laplace-
    # smoothed counters the log-odds render reads, never content.
    if kl.startswith("identity_evidence_") or kl.startswith("evidence_"):
        return True
    return False


def concept_signature(substrate, concept_node, edge_types=None,
                      *, overlay: bool = False) -> frozenset:
    """A Concept → its COORDINATES in qualia space: a frozenset of
    `(dimension, predicate, value)` 3-tuples.

    Mechanical extraction only. The dimensions:

      * `lexical:formal`         ← the concept's type + `category` (what KIND)
      * `lexical:{constitutive,   ← outgoing edges, by their seeded
         telic,agentive}` /          DimensionEdgeRole role; unmapped edges land
         `relational:<edge>`         on an untyped `relational:` axis
      * `dynamical:{valence,      ← the CAN fields, quantised; crystallised,
         commitment}`               always present
      * `dynamical:{pull,         ← the CAN fields, LIVE; only when overlay=True
         activation}`               (the "how I feel right now" reading)
      * `vocab:{role,principle,   ← shape-vocabulary keyword hits (bootstrap)
         shape}`
      * `attr:<key>`              ← remaining plain attributes (name/definition…)
                                    MINUS the dynamical field SOURCES (the raw
                                    CAN fields + mirrored trait fields, read as
                                    dynamical axes) and native CAN mechanism
                                    bookkeeping (identity/evidence ledgers +
                                    tick/epoch gates), both excluded as
                                    non-discriminative noise (see
                                    `_is_can_bookkeeping_attr`).

    A frozenset because STRUCTURAL INTERSECTION is the match: AntiUnify's
    "all sets → the intersection" branch aligns two coordinate sets, and the
    3-tuple's leading dimension tag makes that intersection PER-DIMENSION —
    same telic shape aligns with same telic shape, never with a constitutive
    one.

    `overlay=False` (default) = the CRYSTALLISED / standing signature (stable
    shape). `overlay=True` = the standing signature PLUS the live field reading
    (perturbed shape — how the agent feels about it right now). Both are one
    space; see `_dynamical_relations`.
    """
    sub = _sub(substrate)
    try:
        node = sub.node(concept_node)
        typ = str(node.get("type", "Concept")).lower()
        attrs = node["attrs"]
    except Exception:
        return frozenset()
    schema = _qualia_schema(substrate)
    # The attrs that are SOURCES for a dynamical field axis — the three raw CAN
    # fields AND every MIRRORED trait field (disposition_field/_external,
    # abstraction_field/_external, …). They are read as the quantised dynamical
    # axes, so they must NOT ALSO surface as raw attr:* coordinates (that would
    # be a non-discriminative duplicate of the felt content — the same leak the
    # cross-family gate forbids for state/external_field/identity_field). Read
    # off the field: axes' own `source`, so a trait added to the codebook is
    # excluded automatically (no hand-kept list). Falls back to the three raw
    # fields when the qualia seed is absent.
    _field_source_attrs = {a for (_d, a, _q, _hw, _o) in schema["field_axes"]}
    _field_source_attrs |= {"state", "external_field", "identity_field"}

    rels: list = [("lexical:formal", "is_a", typ)]
    for k, v in (attrs or {}).items():
        if v is None:
            continue
        kl = str(k).lower()
        if kl == "category":
            rels.append(("lexical:formal", "category", str(v).lower()))
        elif kl in _field_source_attrs:
            continue  # a dynamical field axis SOURCE (raw CAN field or mirrored
                      # trait field) — read as a quantised dynamical axis, never
                      # a raw attr:* duplicate
        elif _is_can_bookkeeping_attr(kl):
            continue  # native CAN mechanism counter (ledger/tick/epoch), not
                      # content — would leak as non-discriminative attr:* noise
        else:
            rels.append(("attr:%s" % kl, kl, str(v).lower()))
    rels.extend(_outgoing_relations(substrate, concept_node, schema, edge_types))
    rels.extend(_dynamical_relations(substrate, concept_node, schema, overlay))
    rels.extend(_vocabulary_relations(substrate, concept_node))
    return frozenset(rels)


# --------------------------------------------------------------------------- #
# Ingest — write the codebook + probes, hand off to the rules.
# --------------------------------------------------------------------------- #
def _agent_node(agent):
    for name in ("agent", "agent_node", "_agent"):
        n = getattr(agent, name, None)
        if n is not None:
            return n
    # Fallback: the raw substrate was passed (tests / reframing_proposer pass a
    # bare Substrate). Find the single Agent hub by scan — the same body
    # analogical_thinking._agent_node_id uses.
    sub = _sub(agent)
    try:
        nodes = sub.nodes("Agent")
        return nodes[0] if nodes else None
    except Exception:
        return None


def _find_mt(sub, name: str):
    for mt in sub.nodes("Microtheory"):
        if str(sub.node(mt)["attrs"].get("name", "")) == name:
            return mt
    return None


def _concepts(sub, mt_node) -> list:
    return list(sub.neighbours(mt_node, "has_concept"))


def _part_name(field: str, concept_name: str) -> str:
    return "%s%s%s" % (field, _SEP, concept_name)


def _strip_field(part_name: str) -> tuple[str, str]:
    """"field::concept" → (field, concept). A part name with no separator is
    returned as ("", name) — defensive, should not happen for our own parts."""
    s = str(part_name or "")
    if _SEP in s:
        f, _, c = s.partition(_SEP)
        return f, c
    return "", s


def _installed_seed_ids(sub) -> set:
    """Seed ids already installed, read from BOTH provenance markers in use
    (the `Seed{id}` node this shim mints and the `SeedSummary{seed_id}` node a
    full boot mints) — the exact idempotency read
    `reflective_faculty._installed_seed_ids` uses, so a `load_all_seeds` boot
    that already installed these seeds is not re-installed (which would double
    every `ap_*` rule)."""
    have = set()
    for typ, key in (("Seed", "id"), ("SeedSummary", "seed_id")):
        try:
            for n in sub.nodes(typ):
                sid = sub.node(n)["attrs"].get(key)
                if sid:
                    have.add(sid)
        except Exception:
            continue
    return have


#: The seed chain this faculty needs, in dependency order (analogy_search
#: depends_on shape_vocabulary). Mirrors reflective_faculty's own seed chains.
_SEED_CHAIN = ("shape_vocabulary", "qualia_space", "analogy_search")


def _ensure_seed(agent) -> None:
    """Idempotently load `shape_vocabulary` + `analogy_search` onto the
    substrate, guarded per-seed by a `Seed`/`SeedSummary` marker — the same
    mechanical seed I/O `reflective_faculty._ensure_seed_chain` /
    `_ensure_shape_decode_loop` do. No decision; a held seed is left alone."""
    sub = _sub(agent)
    if sub is None:
        return
    native = getattr(sub, "_inner", sub)
    if not hasattr(native, "load_seed_manifest"):
        return
    ag = _agent_node(agent)
    if ag is None:
        return
    try:
        from substrate.seed_loader import manifest_for
    except Exception:
        return
    have = _installed_seed_ids(sub)
    for sid in _SEED_CHAIN:
        if sid in have:
            continue
        try:
            native.load_seed_manifest(manifest_for(sid), ag)
            sub.add_node("Seed", {"id": sid, "version": "1.0.0"})
            have.add(sid)
        except Exception:
            continue


def observe(agent, source_mt_name: str, target_mt_names: list,
            *, run: bool = True, edge_types=None, overlay: bool = False) -> dict:
    """Write the analogy-search inputs and let the rules decide.

    For each TARGET field, every concept becomes a `ConceptShape` codebook part
    named "field::concept_name". For each SOURCE concept, one `AnalogyProbe` is
    written, scoped (`scope` attr → `codebook_scope`) to exactly the target
    fields' part names, so a source only ever decodes against OTHER fields.
    Then `run_rules()` ticks the decode→match→systematicity→emit fixpoint.

    Returns `{"probes": [...], "codebook": [...], "source_nodes": {...},
    "target_nodes": {...}}` — the node bookkeeping `find_analogies` needs to
    read back verdicts and write the `implements` edges. Mechanical ingest
    only; degrades to an empty result (no raise) when the substrate is not
    live.
    """
    sub = _sub(agent)
    out = {"probes": [], "codebook": [], "source_nodes": {}, "target_nodes": {}}
    if sub is None or not hasattr(sub, "add_node"):
        return out
    _ensure_seed(agent)  # idempotent: install shape_vocabulary + analogy_search

    source_mt = _find_mt(sub, source_mt_name)
    if source_mt is None:
        return out
    targets = [(nm, _find_mt(sub, nm)) for nm in target_mt_names]
    targets = [(nm, mt) for nm, mt in targets if mt is not None]
    if not targets:
        return out

    ag = _agent_node(agent)
    try:
        if ag is not None and sub.node(ag)["attrs"].get(EPOCH_ATTR) is None:
            sub.set_attr(ag, EPOCH_ATTR, 0)

        # ---- the target-field codebook -----------------------------------
        scope_names: list = []
        for field, mt in targets:
            for c in _concepts(sub, mt):
                cname = _node_name(sub, c) or ("c%s" % c)
                pname = _part_name(field, cname)
                cid = sub.add_node(CODEBOOK_TYPE, {
                    "name": pname,
                    "signature": concept_signature(sub, c, edge_types,
                                                    overlay=overlay),
                    "field": field,
                })
                out["codebook"].append(cid)
                out["target_nodes"][pname] = c
                scope_names.append(pname)

        if not scope_names:
            return out  # never write an empty scope (unrestricted-decode hazard)

        # ---- one probe per source concept --------------------------------
        # When a target field == the source field (self-analogy, as
        # reframing_proposer does), a source concept must be able to match its
        # same-field SIBLINGS but never ITSELF. So each probe's scope is the
        # target part set MINUS the probe's own "source_field::name" part (if
        # present). Cross-field probes are unaffected (their own part name
        # never appears among the target parts).
        target_field_label = ",".join(nm for nm, _ in targets)
        for c in _concepts(sub, source_mt):
            cname = _node_name(sub, c) or ("c%s" % c)
            out["source_nodes"][cname] = c
            own_part = _part_name(source_mt_name, cname)
            probe_scope = [p for p in scope_names if p != own_part]
            if not probe_scope:
                # Only its own field's only concept was in scope — nothing to
                # compare against. Skip (never write an empty scope).
                continue
            pid = sub.add_node(PROBE_TYPE, {
                "signature": concept_signature(sub, c, edge_types,
                                               overlay=overlay),
                "source_concept": cname,
                "source_field": source_mt_name,
                "target_field": target_field_label,
                "scope": probe_scope,
                "status": "pending",
            })
            if ag is not None:
                sub.add_edge(ag, OBSERVED_EDGE, pid)
            out["probes"].append(pid)

        if run:
            native = getattr(sub, "_inner", sub)
            native.run_rules()
    except Exception:
        return out
    return out


# --------------------------------------------------------------------------- #
# Read-back — destructure the emitted Analogy nodes into verdicts.
# --------------------------------------------------------------------------- #
def _emitted_analogies(sub, book: dict) -> list:
    """The `Analogy` nodes the `ap_emit` rule wrote for THIS observe() call,
    found via each probe's `emitted_analogy` edge (so we read back only our own
    run's verdicts, not stale Analogy nodes from a prior call)."""
    out = []
    for pid in book.get("probes", []):
        for an in sub.neighbours(pid, EMITTED_EDGE):
            out.append((pid, an))
    return out


#: Coordinates present in (nearly) every concept, carrying NO cross-concept
#: analogical signal — the floor must not be met by these alone. The universal
#: `(lexical:formal, is_a, concept)` type coordinate every same-typed Concept
#: trivially shares, and any vacuously-empty value. MetaShapeMint's "a
#: predicate present in EVERY observation carries zero discriminative
#: information" discipline (shape_decode.rs), applied to the analogy floor.
_NON_DISCRIMINATIVE_PREDS = ("is_a",)


def _discriminative_struct(transform_key: str) -> int:
    """How many shared coordinates in the lgg (transform_key JSON) are
    DISCRIMINATIVE — not the universal `is_a` type coordinate, not an empty
    value. A pair whose only shared coordinate is `(lexical:formal, is_a,
    concept)` (which every same-typed concept trivially shares) is NOT an
    analogy. Handles both 3-tuples (dimension, predicate, value) — the
    qualia-space signature — and legacy 2-tuples (predicate, value)."""
    try:
        rels = json.loads(transform_key or "[]")
    except Exception:
        return 0
    n = 0
    for r in rels:
        if not isinstance(r, (list, tuple)):
            continue
        if len(r) == 3:
            _dim, pred, val = str(r[0]), str(r[1]), str(r[2])
        elif len(r) == 2:
            pred, val = str(r[0]), str(r[1])
        else:
            continue
        if pred in _NON_DISCRIMINATIVE_PREDS:
            continue
        if val == "" or val == "·":
            continue
        n += 1
    return n


def _dimensions_in_transform(transform_key: str) -> set:
    """The set of qualia DIMENSIONS the shared shape spans — the dimension tag
    (element 0) of each shared 3-tuple. Lets a caller see WHICH axes two
    concepts are analogous ON (a same-telic match vs a same-dynamical-valence
    match), which is the whole point of the dimensional schema."""
    try:
        rels = json.loads(transform_key or "[]")
    except Exception:
        return set()
    dims = set()
    for r in rels:
        if isinstance(r, (list, tuple)) and len(r) == 3 and str(r[2]) not in ("", "·"):
            dims.add(str(r[0]))
    return dims


# --------------------------------------------------------------------------- #
# PERSONALITY-VECTOR CONSUMERS (layer 2) — abstraction -> analogy order floor,
# skepticism -> analogy acceptance floor.
#
# WHAT THIS IS
# ------------
# The agent's cognitive PERSONALITY (domains/disposition.TRAIT_REGISTRY) is a
# vector of independent CAN-relaxable traits. Layer 1 built the vector; the
# `openness` trait already drives the mint gate (relation_grounding.MintPolicy
# reads disposition_level). This block wires the two remaining traits to the two
# REAL knobs the analogy search already exposes — NOT invented knobs:
#
#   · ABSTRACTION -> the MINIMUM ORDER FLOOR on returned analogies. Each emitted
#     analogy already carries a DERIVED order (`_order_from_transform`: surface
#     role/lexical/dynamical = 2, shared abstract PRINCIPLE = 3, shared
#     META-SHAPE = 4). An abstract temperament "reaches for higher-order matches
#     first" by FILTERING OUT the surface (order-2) matches and keeping only the
#     principle/meta-shape ones; a concrete temperament keeps everything
#     (surface included). This is a monotone floor over an EXISTING quantity, not
#     a new dial. (The legacy `order_n` PARAMETER was already inert — the search
#     matches on structure in one decode — so this floor is the honest place the
#     "how abstract a match do I reach for" knob actually lives.)
#   · SKEPTICISM -> the `min_score` acceptance floor: how much shared
#     DISCRIMINATIVE structure (`_discriminative_struct`) an analogy must have to
#     be returned. A skeptical temperament demands MORE shared structure (higher
#     min_score => fewer, better-supported matches); a credulous one accepts the
#     default floor of 1 (first sight of any discriminative overlap).
#
# THE MAPPINGS — trait_level (integer step in [-4,+4]) -> knob. HONEST + MONOTONE.
#   abstraction_level -> min_order floor:
#       level <= 0 : 2   (today's floor — keep every emitted match, surface incl.)
#       level 1..2 : 3   (drop pure-surface; keep principle + meta-shape matches)
#       level >= 3 : 4   (only the deepest shared META-SHAPE matches survive)
#   skepticism_level  -> min_score floor:
#       level <= 0 : 1   (today's default — accept any discriminative overlap)
#       level 1..2 : 2   (demand two shared discriminative coordinates)
#       level >= 3 : 3   (demand three — a strongly-supported correspondence)
#
# THE SAFE-DEFAULT INVARIANT (decision-equivalence, proven in tests): a
# SEEDED-neutral (level 0) trait maps to EXACTLY today's default (min_order=2 is
# the minimum `_order_from_transform` ever returns, so it filters nothing;
# min_score=1 is today's default). An agent with NO trait vector at all reads the
# defaults directly (the derivation is skipped entirely — the trait read is
# ensure=False, so a bare call NEVER mints a trait Mt). So a default agent
# behaves EXACTLY like today.
#
# OVERRIDE PRECEDENCE (mirrors MintPolicy's explicit-pin-wins): an EXPLICIT
# caller argument (order_n/min_score passed to find_analogies, start_n to
# think_harder) ALWAYS wins over the trait-derived default. The trait only
# supplies the DEFAULT for a knob the caller left unset (the `None` sentinel).
# --------------------------------------------------------------------------- #

#: The neutral defaults — these reproduce TODAY's behaviour exactly. min_order=2
#: is the minimum `_order_from_transform` ever emits (so it filters nothing);
#: min_score=1 is find_analogies' historical default. start_n=1 is think_harder's.
_DEFAULT_MIN_ORDER = 2
_DEFAULT_MIN_SCORE = 1


def _abstraction_min_order(agent) -> Optional[int]:
    """Derive the analogy ORDER FLOOR from the agent's standing `abstraction`
    trait, or None when this graph carries NO abstraction trait (then the caller
    keeps the default floor of 2 == today). A pure, MONOTONE read of the
    produced, quantised trait level — no decision here beyond the documented
    mapping; the level itself was produced by CAN relaxation.

    Reads with `ensure=False` so a bare call NEVER mints a trait Mt (the
    off-by-default discipline): a graph with no personality vector adds nothing
    and behaves like today. Only derives when the abstraction Concept ACTUALLY
    EXISTS on this graph.

    Mapping (see the block comment):  level<=0 -> 2, 1..2 -> 3, >=3 -> 4."""
    level = _trait_level_if_present(agent, "abstraction")
    if level is None:
        return None
    if level >= 3:
        return 4
    if level >= 1:
        return 3
    return _DEFAULT_MIN_ORDER


def _skepticism_min_score(agent) -> Optional[int]:
    """Derive the analogy ACCEPTANCE FLOOR (min_score) from the agent's standing
    `skepticism` trait, or None when this graph carries NO skepticism trait (then
    the caller keeps the default floor of 1 == today). Pure, MONOTONE read of the
    produced, quantised level; `ensure=False` (never mints). Only derives when the
    skepticism Concept ACTUALLY EXISTS.

    Mapping (see the block comment):  level<=0 -> 1, 1..2 -> 2, >=3 -> 3."""
    level = _trait_level_if_present(agent, "skepticism")
    if level is None:
        return None
    if level >= 3:
        return 3
    if level >= 1:
        return 2
    return _DEFAULT_MIN_SCORE


def _trait_level_if_present(agent, trait_name: str) -> Optional[int]:
    """The agent's quantised standing level for `trait_name`, or None when the
    graph carries no such trait Concept (so the caller falls back to today's
    default). NON-MINTING (`ensure=False`): a bare read never mints a trait Mt.

    Lazily imports domains.disposition INSIDE the call — disposition imports THIS
    module at load, so a module-level import here would be circular (the same
    lazy-import discipline relation_grounding._disposition_derived_gate uses)."""
    try:
        import domains.disposition as _disp
    except Exception:
        return None
    sub = _sub(agent)
    if sub is None:
        return None
    # only derive when the trait Concept ACTUALLY EXISTS on this graph — never
    # mint one from an analogy pass. No trait Mt / no trait Concept -> None -> today.
    try:
        spec = _disp.trait_spec(trait_name)
        ag = _disp._agent_node(agent)
        mt = _disp._find_disposition_mt(sub, ag)
        if mt is None or _disp._trait_concept(sub, mt, spec.concept_name) is None:
            return None
        return int(_disp.trait_level(agent, trait_name, ensure=False))
    except Exception:
        return None


def _order_from_transform(transform_key: str) -> int:
    """The abstraction ORDER of a match, DERIVED from which qualia dimensions
    the shared shape spans (never asserted). A shared META-SHAPE (`vocab:shape`)
    is the deepest (4); a shared abstract PRINCIPLE (`vocab:principle`) is 3; a
    shared functional ROLE (`vocab:role`) or a shared LEXICAL qualia role
    (telic/agentive/constitutive) or DYNAMICAL felt axis is 2 — a genuine
    structural/qualia correspondence above surface. Read from the dimensions
    the anti-unify actually fixed, mirroring the old five-order dial's meaning
    without its string-token basis."""
    dims = _dimensions_in_transform(transform_key)
    tk = transform_key or ""
    if any(d.startswith("vocab:shape") for d in dims) or "vocab:shape" in tk:
        return 4
    if any(d.startswith("vocab:principle") for d in dims):
        return 3
    return 2


def find_analogies(substrate, source_mt_name: str,
                   target_mt_names: list, order_n: Optional[int] = None,
                   min_score: Optional[int] = None, edge_types=None,
                   *, overlay: bool = False) -> list:
    """The analogy search, now a thin wrapper over the graph loop.

    Seeds probes over `seeds/analogy_search.json`, ticks the fixpoint, and
    destructures the emitted `Analogy` nodes into the verdict dicts callers
    expect. Also writes an `implements` edge between the two REAL `Concept`
    nodes for each emitted analogy (the shim holds the node ids; the rule layer
    never touches `Concept`s).

    PERSONALITY-VECTOR KNOBS (layer 2) — `order_n` and `min_score` are BOTH
    None-sentinel defaults so the agent's cognitive personality can supply them
    when the caller does not (see the block comment above `_order_from_transform`):

      · `order_n` — the legacy source-compatibility param (the search matches on
        STRUCTURE in one decode, so `order_n` never dialled the search itself).
        It now ALSO serves as the caller's EXPLICIT PIN over the abstraction-
        derived order FLOOR: when the caller passes an explicit `order_n`, the
        trait-derived floor is NOT applied (the caller's intent wins, and a
        pinned legacy `order_n` filters nothing — today's behaviour). When
        `order_n` is None (unpinned) AND the agent carries a standing
        `abstraction` trait, the floor `_abstraction_min_order` derives is
        applied: an abstract temperament keeps only higher-order (principle /
        meta-shape) matches, "reaching for higher-order matches first".
      · `min_score` — the acceptance floor on shared DISCRIMINATIVE structure.
        When None (unpinned) AND the agent carries a standing `skepticism` trait,
        `_skepticism_min_score` derives it (skeptical => higher floor => fewer,
        better-supported matches). An explicit `min_score` ALWAYS wins.

    NEUTRAL/ABSENT trait == today EXACTLY (decision-equivalence): min_order
    resolves to 2 (the minimum order ever emitted — filters nothing) and
    min_score to 1 (today's default). The trait reads are NON-MINTING.

    Returns a list of `{source_concept, target_concept, source_mt, target_mt,
    struct_shared, corroboration, feature_count, features_total, order_n,
    rationale, source_node, target_node}`, ranked by `RANK_KEY`.
    """
    sub = _sub(substrate)
    if sub is None or not hasattr(sub, "add_node"):
        return []

    # ---- resolve the personality-vector knobs (explicit caller arg wins) ----
    # min_score: explicit pin > skepticism-derived default > today's default (1).
    if min_score is None:
        derived = _skepticism_min_score(substrate)
        eff_min_score = _DEFAULT_MIN_SCORE if derived is None else derived
    else:
        eff_min_score = int(min_score)
    # min_order FLOOR on the emitted analogies' DERIVED order. Only the UNPINNED
    # (order_n is None) path consults the abstraction trait; an explicit legacy
    # `order_n` pins the floor OFF (filters nothing — today's inert behaviour),
    # so callers passing order_n=4 keep every match exactly as before.
    if order_n is None:
        derived_order = _abstraction_min_order(substrate)
        eff_min_order = _DEFAULT_MIN_ORDER if derived_order is None else derived_order
    else:
        eff_min_order = _DEFAULT_MIN_ORDER  # explicit legacy order_n => no floor

    book = observe(substrate, source_mt_name, target_mt_names, run=True,
                   edge_types=edge_types, overlay=overlay)

    results = []
    for _pid, an in _emitted_analogies(sub, book):
        a = sub.node(an)["attrs"]
        struct = int(a.get("struct_shared") or 0)
        corr = int(a.get("corroboration") or 0)
        tkey = str(a.get("transform_key") or "")
        # The analogy FLOOR is applied to DISCRIMINATIVE shared structure — a
        # pair whose ONLY shared relation is the universal `is_a:concept` (or a
        # vacuously-shared empty value) is a non-answer, not an analogy. This is
        # MetaShapeMint's "a predicate present in every observation carries zero
        # discriminative information" discipline, applied to the analogy floor.
        # The floor is `eff_min_score` — skepticism raises it (a skeptical
        # temperament demands more shared structure).
        disc = _discriminative_struct(tkey)
        if disc < eff_min_score:
            continue
        # The ABSTRACTION ORDER FLOOR — a skeptic of the SURFACE. An abstract
        # temperament reaches for higher-order matches first by dropping the
        # pure-surface (order-2) ones; neutral/concrete keeps them (floor 2,
        # the minimum order emitted, filters nothing = today).
        this_order = _order_from_transform(tkey)
        if this_order < eff_min_order:
            continue
        _tf, tconcept = _strip_field(a.get("target_concept"))
        sconcept = str(a.get("source_concept") or "")
        src_node = book["source_nodes"].get(sconcept)
        tgt_node = book["target_nodes"].get(str(a.get("target_concept") or ""))
        # `implements` asserts STRUCTURAL correspondence — written only here,
        # only for an emitted (aligned/corroborated) analogy (contrast
        # SHAPE_AUDIT.md §2.4's hand-set order_n>=2 ordinal).
        if src_node is not None and tgt_node is not None:
            try:
                sub.add_edge(src_node, "implements", tgt_node, {})
            except Exception:
                pass
        results.append({
            "source_concept": sconcept,
            "target_concept": tconcept,
            "source_mt": str(a.get("source_mt") or source_mt_name),
            "target_mt": str(a.get("target_mt") or ""),
            "struct_shared": struct,
            "name_shared": struct,  # kept for RANK_KEY compatibility
            "corroboration": corr,
            "covered_count": int(a.get("covered_count") or 0),
            # RELATIVE placement, DERIVED from the shared shape: the deepest
            # vocabulary axis the anti-unify fixed sets the order (shape:->4,
            # principle:->3, role:->2), read from transform_key, not asserted.
            "order_n": this_order,
            "feature_count": struct,
            "features_total": struct + corr,
            "transform_key": tkey,
            # WHICH qualia dimensions the two concepts are analogous ON — the
            # point of the dimensional schema. A match may be a shared TELIC
            # shape, a shared AGENTIVE (causal) shape, a shared DYNAMICAL felt
            # valence, or several at once; the caller can see the basis.
            "aligned_dimensions": sorted(_dimensions_in_transform(tkey)),
            "source_node": src_node,
            "target_node": tgt_node,
            "rationale": (
                "aligned on qualia dimension(s) %s%s (graph analogy_search)"
                % (", ".join(sorted(_dimensions_in_transform(tkey))) or
                   "structural",
                   "; corroborated by %d pair(s) realising the same transform"
                   % corr if corr else "")),
        })
    results.sort(key=at.RANK_KEY)
    return results


def think_harder(substrate, source_mt_name: str,
                 target_mt_names: list, start_n: Optional[int] = None,
                 max_n: int = 4, want_at_least: int = 5) -> dict:
    """The n-abstractable entry point, preserved. The search is now structural
    (one graph fixpoint), so "thinking harder" is a single call whose verdicts
    are already ranked by depth (structural alignment) and corroboration.

    PERSONALITY-VECTOR KNOB (layer 2): `start_n` is the reported STARTING order
    floor. It is now a None-sentinel so the agent's `abstraction` trait can
    supply it — an abstract temperament starts higher up the order ladder
    ("reach for higher-order matches first"), so the underlying `find_analogies`
    applies the abstraction-derived order floor AND the reported `start_n` /
    `order_used` fallback reflect that floor. A concrete/neutral/absent trait
    keeps `start_n=1` — today's value EXACTLY (decision-equivalence). An EXPLICIT
    `start_n` passed by the caller ALWAYS wins (same precedence as find_analogies'
    explicit `order_n`), and pins the floor OFF in the delegated search too.

    Returns the same `{order_used, analogies, satisfied, n_found, n_emitted,
    start_n, rationale}` shape the old faculty did.
    """
    # EXPLICIT start_n pins the floor OFF (caller intent wins); an UNPINNED
    # start_n lets the abstraction trait drive both the search floor and the
    # reported starting order. Neutral/absent trait -> start_n == 1 (== today).
    if start_n is None:
        derived_floor = _abstraction_min_order(substrate)
        eff_start_n = 1 if derived_floor is None else int(derived_floor)
        # unpinned -> the delegated search consults the traits itself (order_n
        # None, min_score None): abstraction floor + skepticism min_score apply.
        analogies = find_analogies(substrate, source_mt_name, target_mt_names)
    else:
        eff_start_n = int(start_n)
        # explicit start_n pins the abstraction floor OFF in the search too, so
        # a caller that names a start_n keeps every emitted match (today's inert
        # legacy behaviour); skepticism's min_score still applies (unpinned).
        analogies = find_analogies(substrate, source_mt_name, target_mt_names,
                                   order_n=eff_start_n)
    satisfied = len(analogies) >= want_at_least
    return {
        "order_used": max((a["order_n"] for a in analogies), default=eff_start_n),
        "analogies": analogies,
        "satisfied": satisfied,
        "n_found": len(analogies),
        "n_emitted": len(analogies),
        "start_n": eff_start_n,
        "rationale": (
            "Found %d graph-emitted analogies (structural alignment + "
            "systematicity); %s." % (
                len(analogies),
                "satisfied" if satisfied else
                "fewer than %d — domains genuinely disjoint or edge-poor"
                % want_at_least)),
    }


# --------------------------------------------------------------------------- #
# CRYSTALLISATION — experience becoming character.
#
# This is the operator that moves a recurring LIVE-overlay perturbation into the
# CRYSTALLISED signature: a felt state (`state`/`external_field`) that keeps
# recurring in the same direction settles into `identity_field` — which
# `concept_signature` reads as the crystallised `dynamical:commitment` /
# `dynamical:valence` axes. The gap between a concept's overlay signature and
# its crystallised signature is "I'm not sure how I feel about this"; running
# this closes that gap when the feeling is sustained, and lets it decay back
# toward zero when the feeling flip-flops (no commitment to either basin).
#
# IT IS NOT REINVENTED HERE. The dynamics already exist as a tick-driven graph
# rule — `can_native_identity_field_feedback` (seeds/can_decay_identity.json):
# `identity_field` steps toward the sign of the accumulated evidence each tick,
# gated by the Mt's `allow_h_drift` policy, decaying toward zero under a
# flip-flopping reading (can_ops.rs::update_identity_dynamics: "sustained σ →
# identity grows... flipping σ → identity decays toward zero"). This hook only
# ensures that seed is installed and ticks the fixpoint, exactly as `observe`
# ensures the analogy seed. The overlay reading and the crystallised axis are
# the SAME CAN field at two timescales; this is the bridge between them.
# --------------------------------------------------------------------------- #
def crystallize(agent, *, run: bool = True) -> bool:
    """Tick the CAN identity dynamics so sustained felt state settles into the
    crystallised qualia axes (`identity_field` → `dynamical:commitment`).
    Idempotently installs the CAN base seed + `can_decay_identity` (via the
    established `can_self_worth_bridge.ensure_can_seed` + `engine_rules_only`
    entry points — NOT a bespoke loader). Returns True if the dynamics were
    ticked, False on a non-live substrate (honest no-op, no raise).

    Mechanical: the DECISION (how much identity moves, in which direction,
    whether the Mt's policy allows it) lives entirely in the existing
    `can_native_identity_field_feedback` graph rule; this only loads the seed
    and calls `run_rules`."""
    sub = _sub(agent)
    if sub is None or not hasattr(sub, "add_node"):
        return False
    native = getattr(sub, "_inner", sub)
    if not hasattr(native, "run_rules"):
        return False
    try:
        import json as _json
        from substrate.seed_loader import engine_rules_only, manifest_for
        from domains.can_self_worth_bridge import ensure_can_seed
        ensure_can_seed(native)
        if not _has_seed_sentinel(sub, "can_decay_identity"):
            native.load_seed_manifest(
                engine_rules_only(manifest_for("can_decay_identity")))
            sub.add_node("Seed", {"id": "can_decay_identity", "version": "1.0.0"})
    except Exception:
        return False
    if run:
        try:
            native.run_rules()
        except Exception:
            return False
    return True


def _has_seed_sentinel(sub, seed_id: str) -> bool:
    try:
        for n in sub.nodes("Seed"):
            if sub.node(n)["attrs"].get("id") == seed_id:
                return True
    except Exception:
        pass
    return False


__all__ = [
    "PROBE_TYPE", "CODEBOOK_TYPE", "OBSERVED_EDGE", "EMITTED_EDGE",
    "EPOCH_ATTR", "concept_signature", "observe",
    "find_analogies", "think_harder", "crystallize",
]
