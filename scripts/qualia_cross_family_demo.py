#!/usr/bin/env python3
"""Qualia CROSS-FAMILY demo — a genuine analogy on TWO axes at once.

Run: python3 scripts/qualia_cross_family_demo.py

THE PAYOFF OF THE ONE-SPACE THESIS (qualia gap 3). Companion to
scripts/qualia_felt_demo.py (which showed the dynamical axes light up under real
relaxation) and the gap-1 relational extractor (domains/relation_grounding.py,
which derives typed telic/constitutive/agentive edges between HELD concepts from
their own prose). This script joins the two: it demonstrates a match where two
concepts from UNRELATED fields align on BOTH

    a RELATIONAL / lexical axis   (lexical:telic  — both REGULATE something), and
    a DYNAMICAL / felt axis        (dynamical:valence — both feel NEGATIVE)

AT ONCE. 'debt functions like a toxin AND feels like a toxin' — findable only
because the lexical (what-it-is) coordinates and the phenomenal (what-it-is-like)
coordinates are ONE space, matched in the same frozenset intersection.

HONESTY / DISCIPLINE (the whole point — a real demonstration, not a rigged one):

  * The RELATIONAL edge is DERIVED, not asserted. We write real prose into each
    concept's `definition` ("... regulates the ledger", "... regulates the cell")
    and run domains.relation_grounding.ground_relations, the SAME gap-1
    machinery. The extractor finds the 'regulates' cue, resolves the object to a
    HELD Concept (ledger / cell — both materialised first), and only THEN emits
    the typed `regulates` edge (lexical:telic). An object that does not ground to
    a held concept is DROPPED — the anti-hallucination gate. No fabricated target.

  * The DYNAMICAL coordinate is PRODUCED by the real native CAN relaxation, never
    hand-written. Each field's concepts get negative external_field EVIDENCE and
    a positive within-field coupling; relax() (native scoped_settle) settles
    `state` to the committed negative sign, and crystallize() ticks the native
    identity-feedback rule so the sustained sign accrues into identity_field. We
    write NOTHING onto state/identity_field. `dynamical:valence` is read off the
    settled `state`.

  * The match itself is emitted by analogy_search.find_analogies over the two
    fields' Microtheories — the graph fixpoint, not a Python comparison. We only
    read back `aligned_dimensions`.

  * CONTRAST: we also show a pair that aligns on only ONE family (functional-only
    or felt-only) to prove the cross-family match adds real information over
    either axis alone.

CONSTRAINTS honoured: NATIVE CAN path only (discrete_mode='3state', adaptive
policy); state/identity_field PRODUCED by relaxation + crystallize ticks, never
asserted; relational targets are HELD Concepts grounded by ground_relations;
reuses ground_relations / self_improvement_loop.relax /
analogy_search.crystallize/concept_signature/find_analogies / _materialise_domain
patterns.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent
                       / "runners" / "dsl" / "python"))

import json

from substrate_rs import _native

import domains.analogical_thinking as at
import domains.analogy_search as asr
import domains.relation_grounding as rg
from domains.can_self_worth_bridge import ensure_can_seed
from domains.self_improvement_loop import relax  # native scoped_settle path

ROOT = Path(__file__).resolve().parent.parent
SEEDS = ROOT / "seeds"

# Identity-evidence ledger attrs the native identity-feedback rule
# (can_native_identity_field_feedback) reads/writes — pre-initialised exactly as
# tests/test_can_identity_feedback.py / scripts/qualia_felt_demo.py do. These are
# BOOKKEEPING for the rule's log-odds render; identity_field (the coordinate)
# starts at 0.0 and is PRODUCED.
_LEDGER = {
    "identity_evidence_confirm": 0,
    "identity_evidence_disconfirm": 0,
    "identity_evidence_tick": -1,
    "identity_decay_tick": -1,
    "identity_field_tick": -1,
}


class _Agent:
    """Minimal agent wrapper crystallize() accepts (reads `.s` / `.agent`),
    matching tests/test_qualia_space_migrated.py + scripts/qualia_felt_demo.py."""

    def __init__(self, sub):
        self.s = sub
        try:
            self.agent = sub.nodes("Agent")[0]
        except Exception:
            self.agent = None


# --------------------------------------------------------------------------- #
# Boot — substrate + qualia machinery seeds + native CAN seeds.
# --------------------------------------------------------------------------- #
def _boot():
    for cache in (at._CONCEPT_READING_CACHE, at._VOCAB_KEYS_CACHE,
                  at._METASHAPE_COUNT_CACHE, asr._QUALIA_SCHEMA_CACHE):
        cache.clear()
    s = _native.Substrate()
    ag = s.add_node("Agent", {})
    # qualia machinery: the QualiaDimension codebook + DimensionEdgeRole map +
    # the analogy_search ap_* rules.
    for name in ("shape_vocabulary", "qualia_space", "analogy_search"):
        path = SEEDS / f"{name}.json"
        if path.exists():
            s.load_seed_manifest(json.load(open(path)), ag)
    # native CAN field rules (discrete update + decay + identity feedback).
    ensure_can_seed(s)
    _open_productions(s)
    return s, ag


def _open_productions(s):
    """Admit the edges we write: has_concept + the within-field CAN coupling
    (causal_influence), plus EVERY relation edge ground_relations may emit
    (used_for/regulates/causes/…) + genls, so the derived telic edge is
    admitted."""
    node_types = ("Agent", "Concept", "Microtheory")
    edge_types = (("has_concept", "causal_influence")
                  + rg.RELATION_EDGE_TYPES + ("genls",))
    for a in node_types:
        for b in node_types:
            for et in edge_types:
                s.add_production({
                    "src": {"type": a, "var": "x"},
                    "edge_type": et,
                    "tgt": {"type": b, "var": "y"},
                    "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "cross_family_demo:open",
                })


# --------------------------------------------------------------------------- #
# Build the two fields. Concepts carry PROSE (definition) — the relational edge
# is DERIVED from it by ground_relations, not asserted. state/identity_field
# start at ZERO; the felt coordinate is PRODUCED by relaxation.
# --------------------------------------------------------------------------- #
def _concept(s, mt, name, *, definition, category, external_field=0.0):
    attrs = {
        "name": name, "category": category, "definition": definition,
        "state": 0.0, "external_field": float(external_field),
        "identity_field": 0.0,
    }
    attrs.update(_LEDGER)
    c = s.add_node("Concept", attrs)
    s.add_edge_unchecked(mt, "has_concept", c)
    return c


def _couple(s, a, b, weight):
    """Symmetric CAN coupling (causal_influence, the edge the native builder
    uses — worlds/bigville_can_beliefs.py / test_can_native_reimplementation)."""
    s.add_edge(a, "causal_influence", b, {"weight": float(weight)})
    s.add_edge(b, "causal_influence", a, {"weight": float(weight)})


def _make_field(s, field_name, category, spec):
    """Materialise a field as a 3-state CAN Microtheory of held Concepts.

    `spec` maps concept-name -> {definition, category, external_field}. Returns
    (mt_node, {name: node}). The Mt is adaptive + 3-state so relax() commits a
    sign and the identity rule may crystallise it."""
    mt = s.add_node("Microtheory", {
        "name": field_name, "category": category,
        "temperature": 1.0, "discrete_mode": "3state", "can_tick": 0,
        "update_policy": "adaptive",
    })
    nodes = {}
    for name, c in spec.items():
        nodes[name] = _concept(
            s, mt, name,
            definition=c["definition"], category=c["category"],
            external_field=c.get("external_field", 0.0),
        )
    return mt, nodes


# --------------------------------------------------------------------------- #
# Native relaxation — PRODUCE the felt coordinates.
# --------------------------------------------------------------------------- #
def _relax_and_crystallise(s, mt, *, ticks=16):
    """relax() (native scoped_settle) commits `state` from the standing
    external_field evidence; then `ticks` strictly-later can_tick epochs run the
    fixpoint so can_native_identity_field_feedback accrues the sustained sign
    into identity_field. We write NOTHING onto state/identity_field."""
    steps = relax(s, mt)
    for i in range(ticks):
        s.set_attr(mt, "can_tick", i + 1)
        asr.crystallize(_Agent(s))
    return steps


# --------------------------------------------------------------------------- #
# Reporting helpers
# --------------------------------------------------------------------------- #
def _valence(s, c):
    """The concept's committed valence sign as the demo reads it (the SAME
    quantum=1.0 the dynamical:valence axis uses): -1 / 0 / +1."""
    st = s.node(c)["attrs"].get("state", 0.0)
    if st > 0.5:
        return +1
    if st < -0.5:
        return -1
    return 0


def _fmt_dyn(s, c):
    a = s.node(c)["attrs"]
    return (f"state={a.get('state', 0.0):+.1f} "
            f"external_field={a.get('external_field', 0.0):+.2f} "
            f"identity_field={a.get('identity_field', 0.0):+.2f}")


def _telic_targets(s, c):
    """The held concepts this concept has an outgoing `regulates` (telic) edge
    to, by name — read straight off the graph (what ground_relations emitted)."""
    out = []
    try:
        for t in s.neighbours(c, "regulates"):
            out.append(s.node(t)["attrs"].get("name", "·"))
    except Exception:
        pass
    return out


# --------------------------------------------------------------------------- #
# Run the analogy directly on the REAL relaxed fields.
#
# Historically this demo built FRESH 'clean view' Concepts that copied only
# category + produced-felt fields + the derived telic edge, because the native
# identity-rule BOOKKEEPING attrs (_LEDGER: identity_evidence_tick, …) leaked
# into concept_signature as non-discriminative `attr:*` coordinates and polluted
# aligned_dimensions. That scaffolding is GONE: concept_signature now excludes
# the CAN mechanism counters (identity/evidence ledgers + tick/epoch gates) at
# the source (see domains/analogy_search._is_can_bookkeeping_attr), so the REAL
# relaxed concepts already carry clean signatures. find_analogies runs directly
# on the real 'econ' / 'bio' Microtheories.
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
def main():
    print("booting substrate + qualia seeds + native CAN seeds…")
    s, _ag = _boot()

    # ── (A) Build two UNRELATED fields. All concepts hold real prose; the
    #        relational targets (ledger, cell) are HELD Concepts. debt & toxin
    #        get NEGATIVE evidence; each field also holds a POSITIVE-valence
    #        regulator (audit / enzyme) for the single-family contrast. ────────
    econ, e = _make_field(s, "econ", "economics", {
        "ledger": dict(category="record",
                       definition="A ledger is a record of accounts."),
        "debt":   dict(category="burden", external_field=-5.0,
                       definition=("Debt is a burden that regulates the ledger "
                                   "and drains the borrower.")),
        "audit":  dict(category="control", external_field=+5.0,
                       definition=("An audit is a control that regulates the "
                                   "ledger and reassures owners.")),
    })
    bio, b = _make_field(s, "bio", "biology", {
        "cell":   dict(category="unit",
                       definition="A cell is the basic unit of an organism."),
        "toxin":  dict(category="burden", external_field=-5.0,
                       definition=("A toxin is a burden that regulates the cell "
                                   "and poisons the tissue.")),
        "enzyme": dict(category="control", external_field=+5.0,
                       definition=("An enzyme is a control that regulates the "
                                   "cell and speeds reactions.")),
    })
    # Within-field POSITIVE couplings pin each concept to its own evidence sign
    # (a real Hopfield basin), keeping debt/toxin negative and audit/enzyme
    # positive after relaxation. Cross those to their in-field target so the
    # committed sign is genuinely settled, not marginal.
    _couple(s, e["debt"], e["ledger"], +0.4)
    _couple(s, e["audit"], e["ledger"], +0.4)
    _couple(s, b["toxin"], b["cell"], +0.4)
    _couple(s, b["enzyme"], b["cell"], +0.4)
    print("built fields 'econ' {ledger, debt, audit} and "
          "'bio' {cell, toxin, enzyme} — discrete_mode='3state', adaptive")

    # ── (B) DERIVE the relational edges from prose (gap-1 machinery). ─────────
    print("\n─── (B) ground_relations: DERIVE telic edges from prose "
          "(anti-hallucination gate) ───")
    rep_e = rg.ground_relations(s, "econ")
    rep_b = rg.ground_relations(s, "bio")
    for field, rep in (("econ", rep_e), ("bio", rep_b)):
        print(f"  {field:5s}: edges_added={rep['edges_added']} "
              f"telic={rep['telic']} constitutive={rep['constitutive']} "
              f"agentive={rep['agentive']} formal={rep['formal']}  "
              f"emitted={rep['emitted']}")
    print("  → the 'regulates' cue grounded to the HELD targets ledger / cell "
          "(telic). Prose objects that do not name a held concept were dropped.")
    print(f"     debt   regulates -> {_telic_targets(s, e['debt'])}")
    print(f"     toxin  regulates -> {_telic_targets(s, b['toxin'])}")

    # ── (C) PRODUCE the felt coordinates by native relaxation. ───────────────
    print("\n─── (C) native relaxation → committed state → crystallised "
          "identity_field (PRODUCED, never asserted) ───")
    steps_e = _relax_and_crystallise(s, econ)
    steps_b = _relax_and_crystallise(s, bio)
    print(f"  relax() settled econ in {steps_e} steps, bio in {steps_b} steps")
    for fld, nodes in (("econ", e), ("bio", b)):
        for name, c in nodes.items():
            print(f"     {fld}:{name:8s} {_fmt_dyn(s, c)}  "
                  f"valence={_valence(s, c):+d}")

    # ── (D) THE CROSS-FAMILY MATCH — find_analogies over the two fields. ─────
    #        Run directly on the REAL relaxed 'econ' / 'bio' Microtheories: the
    #        felt fields were PRODUCED by relaxation, the telic edge DERIVED by
    #        ground_relations, and concept_signature now excludes the CAN
    #        bookkeeping counters at the source — so no 'clean view' is needed.
    print("\n─── (D) find_analogies(econ, [bio]) — the cross-family match ───")
    results = at.find_analogies(s, "econ", ["bio"], order_n=4,
                                min_score=1)
    if not results:
        print("  (no analogy emitted — reporting honestly)")
        return 1

    def _pair(sc, tc):
        for r in results:
            if r["source_concept"] == sc and r["target_concept"] == tc:
                return r
        return None

    cross = _pair("debt", "toxin")
    print("  all emitted analogies:")
    for r in results:
        print(f"    {r['source_concept']:8s} ~ {r['target_concept']:8s}  "
              f"aligned_dimensions={r['aligned_dimensions']}")

    if cross is None:
        print("\n  ✗ debt~toxin NOT emitted — cross-family match not found; "
              "see honest report below.")
        _honest_note(s, e, b)
        return 1

    dims = set(cross["aligned_dimensions"])
    lex = {d for d in dims if d.startswith("lexical:")
           and d.split(":", 1)[1] in ("telic", "constitutive", "agentive")}
    dyn = {d for d in dims if d.startswith("dynamical:")}
    print(f"\n  ★ CROSS-FAMILY analogy: debt ~ toxin")
    print(f"      aligned_dimensions = {sorted(dims)}")
    print(f"      relational (lexical) axis : {sorted(lex) or '—'}")
    print(f"      dynamical  (felt)    axis : {sorted(dyn) or '—'}")
    if lex and dyn:
        print("\n  NARRATION:")
        print("      debt~toxin: both REGULATE (telic) and both feel NEGATIVE "
              "(valence)")
        print("      — 'debt functions like a toxin AND feels like a toxin',")
        print("        found because lexical and phenomenal are ONE space.")
    else:
        print("\n  ✗ the match does NOT span both families "
              "(missing lexical or dynamical axis) — honest report below.")
        _honest_note(s, e, b)
        return 1

    # ── (E) CONTRAST — single-family matches, to prove the cross-family one
    #        adds information. We build two DEDICATED single-axis probes against
    #        the biology field's toxin, each isolating ONE family:
    #          * FELT-ONLY:      a concept that settled NEGATIVE (native
    #            relaxation) but carries NO telic edge → shares dynamical:valence
    #            with toxin, but NOT lexical:telic.
    #          * FUNCTIONAL-ONLY: a concept that REGULATES a held target but was
    #            never relaxed (valence dark) → shares lexical:telic with toxin,
    #            but NOT dynamical:valence.
    #        Kept in their own fields so they do not compete with debt~toxin. ──
    print("\n─── (E) CONTRAST: single-family matches (only ONE axis) ───")
    _contrast(s)

    print("\n─── summary ───")
    print("  The cross-family match aligns on BOTH a relational axis (lexical:"
          "telic, derived from prose by ground_relations) AND a dynamical axis "
          "(dynamical:valence, produced by native relaxation). The single-family "
          "contrasts align on only one. Two axes at once is the payoff of the "
          "one-space thesis.")
    return 0


def _contrast(s):
    """Build two single-family probes against biology's `toxin` (in field `bio`).

    FELT-ONLY (`grief`): a CAN concept given negative evidence and relaxed, so
    it settles NEGATIVE — but with NO telic edge. Aligns with toxin on
    dynamical:valence, NOT on lexical:telic.

    FUNCTIONAL-ONLY (`valve`): a concept whose prose says it 'regulates the
    conduit' (a held target), grounded by ground_relations to a telic edge — but
    NEVER relaxed, so its dynamical axes are DARK. Aligns with toxin on
    lexical:telic, NOT on dynamical:valence.

    Both probes run DIRECTLY on their own real fields against the real `bio`
    field — no 'clean views', since concept_signature now strips the CAN
    bookkeeping counters at the source.
    """
    # ---- FELT-ONLY: relax a negative concept with no relation ----
    felt_mt = s.add_node("Microtheory", {
        "name": "mood", "category": "affect",
        "temperature": 1.0, "discrete_mode": "3state", "can_tick": 0,
        "update_policy": "adaptive"})
    _concept(s, felt_mt, "grief", category="burden",
             definition="Grief is a heavy sorrow.", external_field=-5.0)
    _relax_and_crystallise(s, felt_mt)
    felt_res = at.find_analogies(s, "mood", ["bio"], order_n=4, min_score=1)
    _report_single_family("FELT-ONLY", felt_res, "grief", "toxin",
                           expect_dyn=True, expect_telic=False,
                           note="settled NEGATIVE (relaxation) but NO telic edge")

    # ---- FUNCTIONAL-ONLY: telic edge (from prose), never relaxed ----
    func_mt = s.add_node("Microtheory", {"name": "plumbing", "category": "eng"})
    _funcconcept(s, func_mt, "conduit", "A conduit is a channel for flow.")
    _funcconcept(s, func_mt, "valve", "A valve regulates the conduit.")
    rg.ground_relations(s, "plumbing")
    # valve now carries a derived telic `regulates` edge; state/identity_field
    # are absent (never relaxed) → dynamical axes DARK.
    func_res = at.find_analogies(s, "plumbing", ["bio"], order_n=4, min_score=1)
    _report_single_family("FUNCTIONAL-ONLY", func_res, "valve", "toxin",
                           expect_dyn=False, expect_telic=True,
                           note="REGULATES a held target (telic) but never "
                                "relaxed → valence DARK")

    print("  → each contrast shares function OR feeling, not BOTH — so "
          "debt~toxin's two-axis alignment is strictly more than either alone.")


def _funcconcept(s, mt, name, definition):
    """A plain (non-CAN) held concept carrying prose — no felt fields, no
    ledger. Used for the functional-only contrast (never relaxed)."""
    c = s.add_node("Concept", {"name": name, "category": "device",
                               "definition": definition})
    s.add_edge_unchecked(mt, "has_concept", c)
    return c


def _report_single_family(label, results, sc, tc, *, expect_dyn, expect_telic,
                           note):
    r = None
    for cand in results:
        if cand["source_concept"] == sc and cand["target_concept"] == tc:
            r = cand
            break
    if r is None:
        print(f"  {label}: {sc} ~ {tc} not emitted "
              f"(no shared discriminative structure) — {note}")
        return
    dims = set(r["aligned_dimensions"])
    has_dyn = any(d.startswith("dynamical:") for d in dims)
    has_telic = "lexical:telic" in dims
    print(f"  {label}: {sc} ~ {tc}  aligned_dimensions={sorted(dims)}")
    print(f"         → {note}")
    print(f"           dynamical axis present? {has_dyn}   "
          f"lexical:telic present? {has_telic}")
    ok = (has_dyn == expect_dyn) and (has_telic == expect_telic)
    print(f"           single-family as expected? {ok} "
          f"(aligns on {'feeling' if expect_dyn else 'function'} only)")


def _honest_note(s, e, b):
    print("\n  ── honest diagnostics ──")
    print(f"     debt  regulates -> {_telic_targets(s, e['debt'])}, "
          f"valence={_valence(s, e['debt']):+d}")
    print(f"     toxin regulates -> {_telic_targets(s, b['toxin'])}, "
          f"valence={_valence(s, b['toxin']):+d}")
    print("     For a cross-family match both must (a) carry a telic edge to a "
          "held target (so the lexical:telic tuple matches on target TYPE) and "
          "(b) settle to the SAME valence sign. If either is missing, the "
          "aligned_dimensions cannot span both families.")


if __name__ == "__main__":
    raise SystemExit(main())
