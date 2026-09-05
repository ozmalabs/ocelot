#!/usr/bin/env python3
"""Qualia FELT demo — the dynamical axes lighting up by RUNNING THE DYNAMICS.

Run: python3 scripts/qualia_felt_demo.py

Companion to scripts/qualia_vibe_probe.py. The vibe probe found ZERO dynamical
coordinates across ~543 domain concepts — because those concepts have never
been through the CAN (continuous attractor network) field, so their
state/external_field/identity_field are all 0/absent and every dynamical axis
is DARK (`_round_to_vocab` returns None on 0). This script closes that gap the
only honest way: it RELAXES a small, realistic attitude/affect network through
the REAL native CAN field, and shows the felt coordinates
(`dynamical:valence` / `dynamical:commitment`) APPEAR in the crystallised
signatures — produced by the dynamics, never hand-set.

THE THEORY it demonstrates: felt states are a REGION of the ONE qualia space,
reached by running the real dynamics, differing in DEGREE not KIND from the
functional (lexical) coordinates. A felt concept and a reasoned-about concept
are tuples in the same frozenset; the felt ones simply light up the dynamical
family of axes.

What it prints:
  (1) BEFORE — every concept dark on the dynamical axes (never relaxed).
  (2) The native relaxation: evidence -> committed `state` (valence) ->
      sustained sigma crystallising into `identity_field` (commitment), driven
      by the CAN's OWN rules (can_native_update_3state +
      can_native_identity_field_feedback), NOT by us writing the fields.
  (3) AFTER — the same concepts now LIT on dynamical:valence/commitment.
  (4) FELT-SHAPE CLUSTERING — concepts that settled to the same felt sign
      cluster on the dynamical axes (pairwise shared-dynamical-coordinate
      counts + analogy_search.find_analogies aligning them ON dynamical axes).
  (5) THE UNSETTLED POINT — "I'm not sure how I feel": a concept torn between
      equally committed positive and negative basins (balanced, cancelling
      couplings + sub-threshold own evidence) sits in the 3-state deadzone, so
      its identity_field never accrues (dark on commitment) — yet a live
      observation still registers as pull in its overlay. The gap between the
      live overlay and the empty crystallised reading IS the uncertainty.

CONSTRAINTS honoured: NATIVE CAN path only (discrete_mode='3state', the native
update + identity-feedback rules); no mt_relax_to_marginal / mt_mean_field_
marginal (removed). identity_field is PRODUCED by the relaxation from evidence —
never asserted. Reuses can_self_worth_bridge.ensure_can_seed,
self_improvement_loop.relax (scoped_settle), analogy_search.crystallize /
concept_signature / find_analogies.
"""
from __future__ import annotations

import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent
                       / "runners" / "dsl" / "python"))

import json

from substrate_rs import _native

import domains.analogical_thinking as at
import domains.analogy_search as asr
from domains.can_self_worth_bridge import ensure_can_seed
from domains.self_improvement_loop import relax  # native scoped_settle path

ROOT = Path(__file__).resolve().parent.parent
SEEDS = ROOT / "seeds"

# The identity-evidence ledger attrs the native identity-feedback rule
# (can_native_identity_field_feedback) reads/writes — pre-initialised exactly
# as tests/test_can_identity_feedback.py::_feedback_concept_setup does. These
# are BOOKKEEPING for the rule's own log-odds render, not the felt coordinate
# itself; identity_field (the coordinate) starts at 0.0 and is PRODUCED.
_LEDGER = {
    "identity_evidence_confirm": 0,
    "identity_evidence_disconfirm": 0,
    "identity_evidence_tick": -1,
    "identity_decay_tick": -1,
    "identity_field_tick": -1,
}


# --------------------------------------------------------------------------- #
# Boot
# --------------------------------------------------------------------------- #
def _boot():
    """Substrate + qualia machinery seeds + native CAN seeds."""
    for cache in (at._CONCEPT_READING_CACHE, at._VOCAB_KEYS_CACHE,
                  at._METASHAPE_COUNT_CACHE, asr._QUALIA_SCHEMA_CACHE):
        cache.clear()
    s = _native.Substrate()
    ag = s.add_node("Agent", {})
    # qualia machinery (defines the QualiaDimension codebook + edge roles)
    for name in ("shape_vocabulary", "qualia_space", "analogy_search"):
        path = SEEDS / f"{name}.json"
        if path.exists():
            s.load_seed_manifest(json.load(open(path)), ag)
    # native CAN field rules (discrete update + decay + identity feedback)
    ensure_can_seed(s)
    # open productions so our affect network's edges are admitted
    _open_productions(s)
    return s, ag


def _open_productions(s):
    node_types = ("Agent", "Concept", "Microtheory")
    edge_types = ("has_concept", "causal_influence")
    for a in node_types:
        for b in node_types:
            for et in edge_types:
                s.add_production({
                    "src": {"type": a, "var": "x"},
                    "edge_type": et,
                    "tgt": {"type": b, "var": "y"},
                    "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "felt_demo:open",
                })


# --------------------------------------------------------------------------- #
# Build a SMALL realistic attitude/affect network (the CAN's real use case).
# --------------------------------------------------------------------------- #
def _concept(s, mt, name, external_field, category):
    """A CAN Concept: state/identity_field start at ZERO (nothing felt yet),
    external_field is the standing EVIDENCE pulling on it. The felt coordinates
    will be PRODUCED from this evidence by the relaxation — not written here."""
    attrs = {
        "name": name, "category": category,
        "state": 0.0, "external_field": float(external_field),
        "identity_field": 0.0,
    }
    attrs.update(_LEDGER)
    c = s.add_node("Concept", attrs)
    s.add_edge_unchecked(mt, "has_concept", c)
    return c


def _couple(s, a, b, weight):
    """A symmetric attitude coupling (both directions, the convention every
    native CAN builder in this codebase uses — worlds/bigville_can_beliefs.py,
    tests/test_can_native_reimplementation.py::_build_draw)."""
    s.add_edge(a, "causal_influence", b, {"weight": float(weight)})
    s.add_edge(b, "causal_influence", a, {"weight": float(weight)})


def _build_affect_mt(s):
    """A resident's small standing attitude network:

      POSITIVE cluster (things going well, mutually reinforcing):
        good_news --+-- feeling_safe --+-- trust_neighbour
      NEGATIVE cluster (a grievance, mutually reinforcing):
        the_slight --+-- resentment
      and one CONFLICTED concept (the unsettled point):
        the_offer  — pulled BOTH ways, evidence flip-flops, never commits.

    Couplings are POSITIVE within a cluster (agree) so the discrete-async
    update settles each cluster to a single committed sign — the real
    Hopfield-basin behaviour, from evidence, not asserted."""
    mt = s.add_node("Microtheory", {
        "name": "resident_attitudes", "category": "affect",
        "temperature": 1.0, "discrete_mode": "3state", "can_tick": 0,
        "update_policy": "adaptive",   # allow_h_drift -> identity may crystallise
    })

    # POSITIVE basin — strong positive evidence, positive mutual coupling.
    good_news = _concept(s, mt, "good_news", +5.0, "event")
    feeling_safe = _concept(s, mt, "feeling_safe", +4.0, "affect")
    trust_neighbour = _concept(s, mt, "trust_neighbour", +3.0, "belief")
    _couple(s, good_news, feeling_safe, +1.0)
    _couple(s, feeling_safe, trust_neighbour, +1.0)

    # NEGATIVE basin — strong negative evidence, positive mutual coupling
    # (they agree WITH EACH OTHER on a negative reading).
    the_slight = _concept(s, mt, "the_slight", -5.0, "event")
    resentment = _concept(s, mt, "resentment", -4.0, "affect")
    _couple(s, the_slight, resentment, +1.0)

    # THE UNSETTLED POINT — a genuinely TORN concept. Weak own evidence (below
    # the 3-state deadzone threshold atanh(0.5)≈0.549 at temperature 1.0), and
    # EQUAL-strength couplings to the (equally committed) positive and negative
    # basins that exactly CANCEL. So the local field stays inside the deadzone,
    # the discrete update leaves it at state=0, sigma is never ±1, and the
    # identity rule never accrues a commitment — it stays DARK on valence AND
    # commitment while still being pulled on (nonzero external_field → overlay
    # pull). This is 'I'm not sure how I feel', PRODUCED by balanced dynamics.
    the_offer = _concept(s, mt, "the_offer", +0.5, "proposal")
    _couple(s, the_offer, trust_neighbour, +0.5)   # pull toward the good basin (state +1)
    _couple(s, the_offer, resentment, +0.5)        # equal pull toward the bad basin (state -1)
    # → coupling contribution 0.5·(+1) + 0.5·(-1) = 0: the two basins cancel.

    concepts = {
        "good_news": good_news, "feeling_safe": feeling_safe,
        "trust_neighbour": trust_neighbour,
        "the_slight": the_slight, "resentment": resentment,
        "the_offer": the_offer,
    }
    return mt, concepts


# --------------------------------------------------------------------------- #
# Drive the native relaxation.
# --------------------------------------------------------------------------- #
def _dims(sig):
    return {d for d, _, _ in sig}


def _dynamical_coords(sig):
    return {t for t in sig if t[0].startswith("dynamical:")}


def _fmt_dyn(sub, c):
    """Compact felt reading of a concept for the trace."""
    a = sub.node(c)["attrs"]
    return (f"state={a.get('state', 0.0):+.1f} "
            f"external_field={a.get('external_field', 0.0):+.2f} "
            f"identity_field={a.get('identity_field', 0.0):+.2f}")


def _relax_and_crystallise(s, mt, concepts, *, settled_concept="the_offer",
                           ticks=12):
    """Run the NATIVE dynamics:

      1. relax() (self_improvement_loop -> scoped_settle) settles `state` from
         the external_field EVIDENCE — the committed sign IS the discrete-async
         fixpoint, produced not asserted.
      2. Then drive `ticks` strictly-later can_tick epochs, running the fixpoint
         each tick so can_native_identity_field_feedback accrues a sustained
         same-sign sigma into identity_field for the committed concepts. The
         UNSETTLED concept sits balanced in the 3-state deadzone (its opposing
         couplings cancel and its own evidence is sub-threshold), so its sigma
         stays 0, no identity accrues, and it stays dark on commitment.

    We NEVER write `state` or `identity_field` on any concept during the drive.
    The committed sign is the discrete-async fixpoint of the standing evidence;
    identity_field is produced by the native identity-feedback rule from that
    self-produced sigma. Nothing here is asserted — that is the whole point.
    """
    the_offer = concepts[settled_concept]

    print("  ── initial relaxation (evidence → committed state) ──")
    steps = relax(s, mt)  # native scoped_settle
    print(f"     relax() settled in {steps} progressing steps")
    for name, c in concepts.items():
        print(f"       {name:16s} {_fmt_dyn(s, c)}")

    print(f"\n  ── {ticks} identity ticks (sustained sigma → identity_field) ──")
    for i in range(ticks):
        tick = i + 1
        s.set_attr(mt, "can_tick", tick)
        # The committed concepts sustain their sign; the_offer stays balanced in
        # the deadzone (state 0) with no injection from us — so its identity
        # never accrues. We write NOTHING onto any concept's state or
        # identity_field: the discrete update re-settles state from the standing
        # evidence, and can_native_identity_field_feedback accrues identity from
        # the sustained sigma, both in crystallize's run_rules fixpoint.
        asr.crystallize(_Agent(s))
        if tick in (1, ticks):
            print(f"     tick {tick:2d}: "
                  f"good_news.identity_field="
                  f"{s.node(concepts['good_news'])['attrs']['identity_field']:+.2f}  "
                  f"resentment.identity_field="
                  f"{s.node(concepts['resentment'])['attrs']['identity_field']:+.2f}  "
                  f"the_offer.identity_field="
                  f"{s.node(the_offer)['attrs']['identity_field']:+.2f}")


class _Agent:
    """Minimal agent wrapper crystallize()/observe() accept (they read `.s` /
    `.agent`), matching the pattern tests/test_qualia_space_migrated.py uses."""
    def __init__(self, sub):
        self.s = sub
        try:
            self.agent = sub.nodes("Agent")[0]
        except Exception:
            self.agent = None


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #
def _print_signatures(s, concepts, *, title):
    print(f"\n─── {title} ───")
    for name, c in concepts.items():
        sig = asr.concept_signature(s, c)
        dyn = sorted(_dynamical_coords(sig))
        lit = ", ".join(f"{d.split(':')[1]}={v}" for d, _, v in dyn) or "· (dark)"
        print(f"  {name:16s} dynamical: {lit}")


def _felt_cluster_report(s, concepts):
    """Show that concepts which settled to the same felt sign CLUSTER on the
    dynamical axes: (a) group by their dynamical:valence coordinate, and
    (b) pairwise shared-dynamical-coordinate counts (the felt-shape distance)."""
    print("\n─── felt-shape clustering (dynamical axes only) ───")
    sigs = {n: asr.concept_signature(s, c) for n, c in concepts.items()}

    # (a) cluster by committed valence sign
    by_valence = defaultdict(list)
    for n, sig in sigs.items():
        val = next((v for d, _, v in sig if d == "dynamical:valence"), None)
        by_valence[val].append(n)
    print("  clusters by dynamical:valence coordinate:")
    for val in sorted(by_valence, key=lambda x: (x is None, x)):
        label = "DARK / unsettled" if val is None else f"valence={val:+d}"
        print(f"    {label:20s} {sorted(by_valence[val])}")

    # (b) pairwise shared DYNAMICAL coordinate counts
    print("\n  pairwise shared-dynamical-coordinate counts (felt similarity):")
    names = list(concepts)
    for a, b in combinations(names, 2):
        shared = _dynamical_coords(sigs[a]) & _dynamical_coords(sigs[b])
        if shared:
            dims = ", ".join(sorted(d.split(":")[1] for d, _, _ in shared))
            print(f"    {a:16s} ~ {b:16s} {len(shared)} shared  [{dims}]")


def _analogy_report(s):
    """Reuse analogy_search.find_analogies to show two co-settled concepts now
    MATCH on a dynamical axis — the felt coordinate is a first-class analogy
    basis, in the SAME space as lexical structure. We split the settled
    concepts into two single-concept microtheories and ask the graph analogy
    loop whether they align; then read the aligned_dimensions back.

    NO 'clean view' scaffolding: concept_signature now excludes the native CAN
    bookkeeping counters (identity/evidence ledgers + tick/epoch gates) at the
    source, so the REAL relaxed concepts carry no non-discriminative attr:*
    noise. We just re-file two real relaxed concepts under two fresh
    single-concept Mts (a `has_concept` edge to the very same node) and run the
    analogy loop directly on them."""
    print("\n─── analogy_search: do co-settled concepts align ON dynamical axes? ───")
    src_mt = s.add_node("Microtheory", {"name": "src_field", "category": "affect"})
    tgt_mt = s.add_node("Microtheory", {"name": "tgt_field", "category": "affect"})

    # find the two positive-basin concepts by reading current state
    positives = [c for c in s.nodes("Concept")
                 if s.node(c)["attrs"].get("state", 0.0) > 0
                 and s.node(c)["attrs"].get("identity_field", 0.0) > 0]
    if len(positives) < 2:
        print("  (fewer than two positively-crystallised concepts to align)")
        return
    # Re-file the REAL relaxed concepts (not clones) under two separate fields.
    s.add_edge_unchecked(src_mt, "has_concept", positives[0])
    s.add_edge_unchecked(tgt_mt, "has_concept", positives[1])

    results = asr.find_analogies(s, "src_field", ["tgt_field"], min_score=1)
    if not results:
        print("  (no analogy emitted — reporting honestly)")
        return
    for r in results:
        dims = r.get("aligned_dimensions") or []
        dyn = [d for d in dims if d.startswith("dynamical:")]
        noise = [d for d in dims if d.startswith("attr:")]
        print(f"  {r['source_concept']} ~ {r['target_concept']}  "
              f"aligned_dimensions={dims}")
        if noise:
            print(f"    !! unexpected bookkeeping noise in aligned_dimensions: {noise}")
        if dyn:
            print(f"    → they are analogous ON the felt axes {dyn} — "
                  f"a shared FELT SHAPE, in the one qualia space.")


def _unsettled_report(s, mt, concepts):
    print("\n─── the unsettled point — \"I'm not sure how I feel\" ───")
    c = concepts["the_offer"]
    # The crystallised reading FIRST: after all the ticks, the offer never
    # committed — dark on valence AND commitment. This is the standing shape.
    cryst = asr.concept_signature(s, c)
    print(f"  crystallised: {_fmt_dyn(s, c)}")
    print(f"    crystallised dynamical dims: "
          f"{sorted(d for d in _dims(cryst) if d.startswith('dynamical:'))}")
    if "dynamical:commitment" not in _dims(cryst):
        print("    → NO crystallised commitment: balanced opposing pulls kept it "
              "in the deadzone; sigma stayed 0, so no identity ever accrued.")

    # Now a LIVE observation arrives: the offer is put in front of the agent
    # RIGHT NOW — a small, sub-threshold external pull. It is genuine live
    # evidence (external_field), NOT a faked identity_field, and it is
    # sub-threshold so the discrete update still won't commit it. We read the
    # OVERLAY (live) here; the standing signature is unchanged.
    s.set_attr(c, "external_field", +0.5)
    over = asr.concept_signature(s, c, overlay=True)
    print(f"\n  a live observation arrives (external_field=+0.5, sub-threshold):")
    print(f"    overlay dynamical dims: "
          f"{sorted(d for d in _dims(over) if d.startswith('dynamical:'))}")
    gap = _dims(over) - _dims(cryst)
    print(f"    gap (overlay − crystallised): {sorted(gap)}")
    if any(d == "dynamical:pull" for d in gap):
        print("    → it is being FELT right now (live pull in the overlay) yet has "
              "NO settled commitment. That GAP is 'I'm not sure how I feel.'")


# --------------------------------------------------------------------------- #
def main():
    print("booting substrate + qualia seeds + native CAN seeds…")
    s, _ag = _boot()
    mt, concepts = _build_affect_mt(s)
    print(f"built '{s.node(mt)['attrs']['name']}' — {len(concepts)} concepts, "
          f"discrete_mode='3state', update_policy='adaptive'")

    # (1) BEFORE — every dynamical axis dark (never relaxed)
    _print_signatures(s, concepts, title="(1) BEFORE relaxation — dynamical axes")
    any_lit = any(_dynamical_coords(asr.concept_signature(s, c))
                  for c in concepts.values())
    print(f"  → any dynamical coordinate lit before relaxation? {any_lit}")

    # (2)/(3) RUN THE DYNAMICS
    print("\n(2) RUNNING THE NATIVE CAN DYNAMICS "
          "(can_native_update_3state + can_native_identity_field_feedback)")
    _relax_and_crystallise(s, mt, concepts)

    _print_signatures(s, concepts, title="(3) AFTER relaxation — dynamical axes LIT")

    # (4) FELT-SHAPE CLUSTERING
    _felt_cluster_report(s, concepts)
    _analogy_report(s)

    # (5) THE UNSETTLED POINT
    _unsettled_report(s, mt, concepts)

    print("\ndone.")


if __name__ == "__main__":
    main()
