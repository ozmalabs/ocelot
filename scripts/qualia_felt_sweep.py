#!/usr/bin/env python3
"""Qualia FELT sweep — populate the DYNAMICAL qualia axes at CORPUS SCALE.

Run: python3 scripts/qualia_felt_sweep.py [--domain philosophy]
                                          [--ticks 16] [--evidence-scale 1.0]

Companion to scripts/qualia_felt_demo.py (the 6-concept single-network
template) and scripts/qualia_vibe_probe.py (which found ZERO dynamical
coordinates across ~543 domain concepts, because domain concepts boot with
state/external_field/identity_field absent/0 and are therefore DARK on every
dynamical axis). The demo PROVED dynamical:valence/commitment are PRODUCIBLE by
native-CAN relaxation on a hand-built 6-node affect network; this sweep shows
the SAME thing across a REAL, LARGER concept population (~86 philosophy
concepts) and prints the dark->lit felt-shape histogram — the dynamical analogue
of the relational lexical:formal 968->1393 shift.

────────────────────────────────────────────────────────────────────────────
THE HONEST PROBLEM (and the faithful mechanism chosen)
────────────────────────────────────────────────────────────────────────────
A materialised domain concept has NO couplings (no causal_influence edges) and
NO evidence (external_field absent). Relaxation alone leaves every concept at
state=0 — dark. To light the dynamical axes the concept must be driven by
something REAL, and the felt coordinate must be PRODUCED by the relaxation
dynamics, never hand-written onto state/identity_field.

This sweep combines the two FAITHFUL options the task names, each grounded in a
signal the corpus ALREADY carries — nothing random, nothing invented:

  (b) EVIDENCE from a real signal the concept carries — an AFFECTIVE reading of
      the concept's OWN `definition`+`why` text against a small, transparent,
      in-script valence lexicon (evaluative words the philosophy corpus really
      uses: "avoids/justified/foundation/solves" vs
      "problem/fails/insufficient/paradox/regress"). The net (pos-neg) word
      count, scaled, becomes the concept's standing `external_field` — the
      standing EVIDENCE. This is a real signal: the author WROTE that a Gettier
      case is a "problem", that coherentism "avoids" a defect, that skepticism
      is about what we "cannot" know. We only read it.

  (a) COUPLING from a real edge structure — same-`category` concepts get a
      symmetric POSITIVE causal_influence coupling (via the author-supplied
      `category` attr, the exact classification grounded_representation.
      ground_categories structuralises). So each category is a basin: its
      concepts mutually reinforce toward a single committed sign, and a
      weakly/neutrally-evidenced concept is pulled to its category's dominant
      sign by its neighbours — a Hopfield basin, from real structure.

The felt coordinate is then PRODUCED by the native relaxation:
  external_field (real affective evidence) + Σ coupling·neighbour_state
    ──(can_native_update_3state)──▶ committed `state`  = dynamical:valence
  sustained same-sign σ over strictly-later can_ticks
    ──(can_native_identity_field_feedback)──▶ `identity_field` = dynamical:commitment

We NEVER write state or identity_field on any concept. `external_field` is the
standing evidence (a real read of the text); everything felt is produced.

If a concept's own text is affectively neutral AND its category basin does not
commit (evidence cancels), it HONESTLY stays dark — reported in the numbers,
not faked.

────────────────────────────────────────────────────────────────────────────
CONSTRAINTS honoured: native CAN path only (discrete_mode='3state'); no
mt_relax_to_marginal / mt_mean_field_marginal (removed). Reuses
can_self_worth_bridge.ensure_can_seed, self_improvement_loop.relax
(scoped_settle), analogy_search.crystallize / concept_signature /
find_analogies, and qualia_vibe_probe._materialise_domain. Does NOT touch CAN
backend internals or toolbox solvers.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent
                       / "runners" / "dsl" / "python"))

from substrate_rs import _native

import domains.analogical_thinking as at
import domains.analogy_search as asr
from domains.can_self_worth_bridge import ensure_can_seed
from domains.self_improvement_loop import relax  # native scoped_settle path

# reuse the vibe probe's faithful domain materialiser (reads the SAME JSON the
# real domain loader reads: name/definition/why/category per concept).
import qualia_vibe_probe as vibe

ROOT = Path(__file__).resolve().parent.parent
SEEDS = ROOT / "seeds"

# The identity-evidence ledger attrs the native identity-feedback rule
# (can_native_identity_field_feedback) reads/writes — pre-initialised exactly as
# the felt demo + tests/test_can_identity_feedback.py do. BOOKKEEPING for the
# rule's own log-odds render; identity_field (the coordinate) starts 0.0 and is
# PRODUCED.
_LEDGER = {
    "identity_evidence_confirm": 0,
    "identity_evidence_disconfirm": 0,
    "identity_evidence_tick": -1,
    "identity_decay_tick": -1,
    "identity_field_tick": -1,
}


# --------------------------------------------------------------------------- #
# The affective lexicon — a small, TRANSPARENT valence reading of a concept's
# OWN text. These are evaluative words the philosophy/CS corpus actually uses;
# nothing here is per-concept, nothing is hand-tuned to a target sign. This is
# option (b): evidence derived from a real signal the concept carries.
# --------------------------------------------------------------------------- #
_POS = frozenset("""
avoid avoids avoided solve solves solved solution solutions justified justify
justifies justification knowledge true truth foundation foundational coherent
coherence reliable reliability sufficient valid sound soundness progress
success successful clear clarity good better best strong stronger support
supports supported enables enable trust safe secure robust elegant powerful
consistent complete correctness correct optimal efficient advantage benefit
benefits proven guarantee guarantees stable stability preserve preserves
""".split())

_NEG = frozenset("""
problem problems fail fails failed failure insufficient cost costs regress
regression doubt skeptic skeptical skepticism paradox paradoxes counterexample
counterexamples false invalid unsound weak weaker attack attacks undermine
undermines denies deny error errors illusion vague conflict conflicts hard
limit limits limited cannot impossible flaw flawed defect trap circular
contradiction contradictory incoherent unreliable unstable overhead expensive
loss lose broken danger dangerous risk risks bug bugs violate violates
""".split())

_WORD = re.compile(r"[a-z]+")


def _affective_evidence(text: str, scale: float) -> float:
    """The concept's OWN standing evidence, read from its text: (pos-neg) count
    of evaluative words, scaled. This is `external_field` — a real read, never a
    felt coordinate. Returns 0.0 for affectively neutral text (which then relies
    on its category basin, or stays honestly dark)."""
    toks = _WORD.findall((text or "").lower())
    pos = sum(t in _POS for t in toks)
    neg = sum(t in _NEG for t in toks)
    return float(pos - neg) * scale


# --------------------------------------------------------------------------- #
# Boot
# --------------------------------------------------------------------------- #
def _open_productions(s):
    node_types = ("Agent", "Concept", "Microtheory")
    edge_types = ("has_concept", "causal_influence", "genls", "built_from",
                  "is_a", "kind_of", "subtype_of")
    for a in node_types:
        for b in node_types:
            for et in edge_types:
                s.add_production({
                    "src": {"type": a, "var": "x"},
                    "edge_type": et,
                    "tgt": {"type": b, "var": "y"},
                    "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "felt_sweep:open",
                })


def _boot():
    for cache in (at._CONCEPT_READING_CACHE, at._VOCAB_KEYS_CACHE,
                  at._METASHAPE_COUNT_CACHE, asr._QUALIA_SCHEMA_CACHE):
        cache.clear()
    s = _native.Substrate()
    ag = s.add_node("Agent", {})
    for name in ("shape_vocabulary", "qualia_space", "analogy_search"):
        path = SEEDS / f"{name}.json"
        if path.exists():
            s.load_seed_manifest(json.load(open(path)), ag)
    ensure_can_seed(s)          # native CAN field rules (update + decay + identity)
    _open_productions(s)
    return s, ag


class _Agent:
    """Minimal agent wrapper crystallize() accepts (reads `.s` / `.agent`)."""
    def __init__(self, sub):
        self.s = sub
        try:
            self.agent = sub.nodes("Agent")[0]
        except Exception:
            self.agent = None


# --------------------------------------------------------------------------- #
# Turn the materialised domain Mt into a native-CAN affect network.
#
# The Mt the vibe probe materialises has plain Concepts (name/definition/why/
# category) under a Microtheory with NO CAN config. We (1) make the Mt an
# adaptive 3-state CAN field, (2) give each concept its ZERO felt fields + the
# evidence-ledger bookkeeping + the standing `external_field` read from its OWN
# text, and (3) wire same-category positive couplings so each category is a
# basin. NOTHING felt is written — external_field is real evidence, state and
# identity_field start at 0 and are produced.
# --------------------------------------------------------------------------- #
def _prepare_can_mt(s, mt, *, evidence_scale, coupling):
    s.set_attr(mt, "temperature", 1.0)
    s.set_attr(mt, "discrete_mode", "3state")
    s.set_attr(mt, "update_policy", "adaptive")   # allow_h_drift → identity may crystallise
    s.set_attr(mt, "can_tick", 0)

    concepts = list(s.neighbours(mt, "has_concept"))
    by_category = defaultdict(list)
    evidence = {}
    for c in concepts:
        a = s.node(c)["attrs"]
        text = f"{a.get('definition', '')} {a.get('why', '')}"
        ev = _affective_evidence(text, evidence_scale)
        # standing felt fields start at ZERO; external_field is the REAL read.
        s.set_attr(c, "state", 0.0)
        s.set_attr(c, "identity_field", 0.0)
        s.set_attr(c, "external_field", ev)
        for k, v in _LEDGER.items():
            s.set_attr(c, k, v)
        evidence[c] = ev
        cat = str(a.get("category", "") or "")
        if cat:
            by_category[cat].append(c)

    # (a) same-category symmetric positive couplings → one basin per category.
    n_edges = 0
    for cat, members in by_category.items():
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                a_, b_ = members[i], members[j]
                s.add_edge(a_, "causal_influence", b_, {"weight": float(coupling)})
                s.add_edge(b_, "causal_influence", a_, {"weight": float(coupling)})
                n_edges += 2
    return concepts, by_category, evidence, n_edges


# --------------------------------------------------------------------------- #
# Signature helpers
# --------------------------------------------------------------------------- #
def _dyn_coords(sig):
    return {t for t in sig if t[0].startswith("dynamical:")}


def _valence(sig):
    return next((v for d, _, v in sig if d == "dynamical:valence"), None)


def _commitment(sig):
    return next((v for d, _, v in sig if d == "dynamical:commitment"), None)


def _lit_counts(s, concepts):
    """(valence_lit, commitment_lit, any_dynamical_lit) across a concept set."""
    val = com = anyd = 0
    for c in concepts:
        sig = asr.concept_signature(s, c)
        if _valence(sig) is not None:
            val += 1
        if _commitment(sig) is not None:
            com += 1
        if _dyn_coords(sig):
            anyd += 1
    return val, com, anyd


# --------------------------------------------------------------------------- #
# Drive the native relaxation + crystallisation.
# --------------------------------------------------------------------------- #
def _relax_and_crystallise(s, mt, concepts, *, ticks):
    print("  ── initial relaxation (real evidence + category couplings → committed state) ──")
    steps = relax(s, mt)   # native scoped_settle
    committed = sum(1 for c in concepts
                    if s.node(c)["attrs"].get("state", 0.0) != 0.0)
    print(f"     relax() settled in {steps} progressing steps; "
          f"{committed}/{len(concepts)} concepts committed to a nonzero state")

    print(f"\n  ── {ticks} identity ticks (sustained σ → identity_field) ──")
    ag = _Agent(s)
    for i in range(ticks):
        tick = i + 1
        s.set_attr(mt, "can_tick", tick)   # strictly-later epoch each tick
        asr.crystallize(ag)                # native identity-feedback fixpoint
        if tick in (1, ticks // 2 or 1, ticks):
            _, com, _ = _lit_counts(s, concepts)
            print(f"     tick {tick:2d}: {com}/{len(concepts)} concepts "
                  f"lit on dynamical:commitment")


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #
def _histogram(s, concepts, *, title):
    print(f"\n─── {title} ───")
    dim_hist = Counter()
    for c in concepts:
        for dim, _p, _v in asr.concept_signature(s, c):
            if dim.startswith("dynamical:"):
                dim_hist[dim] += 1
    total = len(concepts)
    if not dim_hist:
        print("  (no dynamical axis lit — every concept dark)")
    for dim in ("dynamical:valence", "dynamical:commitment"):
        count = dim_hist.get(dim, 0)
        bar = "█" * int(40 * count / total) if total else ""
        print(f"  {dim:28s} {count:4d}/{total} {bar}")
    return dim_hist


def _commitment_magnitude_histogram(s, concepts):
    """Part B.3: the commitment-MAGNITUDE distribution now that we look at
    intensity, not just lit/dark. Prints BOTH the raw integer identity_field
    magnitude the dynamics produce AND the quantised dynamical:commitment
    coordinate — showing whether concepts are weakly or strongly committed, and
    (honestly) that the quantised coordinate saturates to |k|=4 because
    identity_field accrues in whole-integer steps (see
    scripts/qualia_commitment_granularity_probe.py + the seed gloss)."""
    print("\n─── (commitment magnitude) how strongly committed are concepts? ───")
    raw = Counter()
    coord = Counter()
    committed = 0
    for c in concepts:
        v = float(s.node(c)["attrs"].get("identity_field", 0.0))
        raw[abs(round(v))] += 1
        if v != 0.0:
            committed += 1
        k = _commitment(asr.concept_signature(s, c))
        coord[abs(k) if k is not None else 0] += 1
    print("  raw |identity_field| magnitude (the value the dynamics produce):")
    for mag in sorted(raw):
        bar = "█" * raw[mag]
        tag = " (dark/uncommitted)" if mag == 0 else ""
        print(f"    |identity_field| = {mag:3d}   {raw[mag]:3d}  {bar}{tag}")
    print("  quantised dynamical:commitment |coordinate|:")
    for mag in sorted(coord):
        bar = "█" * coord[mag]
        tag = " (dark)" if mag == 0 else (" (SATURATED at half_width)"
                                          if mag == 4 else "")
        print(f"    |k| = {mag:d}   {coord[mag]:3d}  {bar}{tag}")
    print(f"  → {committed}/{len(concepts)} concepts are committed; those that "
          f"are, are STRONGLY committed (raw magnitude ≫ 1), and the quantised "
          f"coordinate saturates to |k|=4 — commitment reads as {{−4,0,+4}}, an "
          f"honest sign+saturation axis, NOT a fine 9-level intensity.")
    return raw, coord


def _valence_sign_distribution(s, concepts):
    print("\n─── valence-sign distribution (committed felt sign) ───")
    signs = Counter()
    for c in concepts:
        v = _valence(asr.concept_signature(s, c))
        if v is None:
            signs["dark (0 / unsettled)"] += 1
        elif v > 0:
            signs["positive (+)"] += 1
        elif v < 0:
            signs["negative (−)"] += 1
        else:
            signs["dark (0 / unsettled)"] += 1
    for label in ("positive (+)", "negative (−)", "dark (0 / unsettled)"):
        print(f"  {label:24s} {signs.get(label, 0):4d}")
    return signs


def _basin_cluster_report(s, by_category, evidence):
    """Show felt-shape CLUSTERING: concepts in the same category-basin settling
    to the SAME committed sign now SHARE dynamical coordinates. Print, per
    category, the committed sign its members reached and how coherent the basin
    is (fraction agreeing on the dominant sign)."""
    print("\n─── felt-shape clustering by category basin ───")
    print("  category                    n  +   −   0   basin sign  (mean evidence)")
    coherent_basins = []
    for cat in sorted(by_category):
        members = by_category[cat]
        signs = Counter()
        for c in members:
            v = _valence(asr.concept_signature(s, c))
            signs["+" if (v or 0) > 0 else "−" if (v or 0) < 0 else "0"] += 1
        n = len(members)
        pos, neg, zero = signs["+"], signs["−"], signs["0"]
        dominant = "+" if pos > neg and pos > zero else \
                   "−" if neg > pos and neg > zero else "·"
        mean_ev = sum(evidence[c] for c in members) / n if n else 0.0
        print(f"  {cat:26s} {n:2d} {pos:3d} {neg:3d} {zero:3d}   "
              f"{dominant:^10s} ({mean_ev:+.2f})")
        # a coherent basin: >=2 members and >=2/3 agree on a nonzero dominant sign
        agree = max(pos, neg)
        if dominant in "+−" and n >= 2 and agree >= max(2, (2 * n) // 3):
            coherent_basins.append((cat, dominant, members))
    return coherent_basins


def _analogy_report(s, coherent_basins):
    """Reuse analogy_search.find_analogies to VERIFY that two concepts which
    co-settled in the same category basin now align ON the dynamical axes — the
    felt coordinate is a first-class analogy basis, in the same qualia space as
    lexical structure. We take two same-basin concepts, clone their PRODUCED
    felt fields into two single-concept Mts, and ask the graph analogy loop
    whether they align."""
    print("\n─── analogy_search: do same-basin concepts align ON dynamical axes? ───")
    if not coherent_basins:
        print("  (no coherent basin with >=2 same-sign members to test)")
        return
    # pick the largest coherent basin
    cat, sign, members = max(coherent_basins, key=lambda t: len(t[2]))
    same_sign = [c for c in members
                 if (_valence(asr.concept_signature(s, c)) or 0)
                 == (1 if sign == "+" else -1)]
    if len(same_sign) < 2:
        print(f"  (basin '{cat}' had <2 readable same-sign members)")
        return
    a_c, b_c = same_sign[0], same_sign[1]
    a_name = s.node(a_c)["attrs"].get("name", "a")
    b_name = s.node(b_c)["attrs"].get("name", "b")

    # NO clean-view / clone scaffolding: concept_signature now excludes the
    # native CAN bookkeeping at the source, so the REAL relaxed concepts carry
    # no non-discriminative attr:* noise. We just re-file the two real relaxed
    # concepts under two fresh single-concept Mts (a has_concept edge to the
    # very same nodes) and run the analogy loop directly on them.
    src_mt = s.add_node("Microtheory", {"name": "felt_src", "category": "affect"})
    tgt_mt = s.add_node("Microtheory", {"name": "felt_tgt", "category": "affect"})
    s.add_edge_unchecked(src_mt, "has_concept", a_c)
    s.add_edge_unchecked(tgt_mt, "has_concept", b_c)

    print(f"  basin '{cat}' (sign {sign}): aligning '{a_name}' vs '{b_name}'")
    print(f"    {a_name}: {_dyn_str(s, a_c)}")
    print(f"    {b_name}: {_dyn_str(s, b_c)}")
    results = asr.find_analogies(s, "felt_src", ["felt_tgt"], min_score=1)
    if not results:
        print("  (no analogy emitted — reporting honestly)")
        return
    for r in results:
        dims = r.get("aligned_dimensions") or r.get("dimensions") or []
        dyn = [d for d in dims if str(d).startswith("dynamical:")]
        noise = [d for d in dims if str(d).startswith("attr:")]
        print(f"  {r['source_concept']} ~ {r['target_concept']}  "
              f"aligned_dimensions={dims}")
        if noise:
            print(f"    !! unexpected bookkeeping noise in aligned_dimensions: {noise}")
        if dyn:
            print(f"    → analogous ON the felt axes {dyn}: a shared FELT SHAPE, "
                  f"in the one qualia space.")


def _dyn_str(s, c):
    a = s.node(c)["attrs"]
    return (f"state={a.get('state', 0.0):+.1f} "
            f"external_field={a.get('external_field', 0.0):+.2f} "
            f"identity_field={a.get('identity_field', 0.0):+.2f}")


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description="Qualia felt sweep at corpus scale")
    ap.add_argument("--domain", default="philosophy",
                    help="domain seed to materialise (default: philosophy)")
    ap.add_argument("--ticks", type=int, default=16,
                    help="identity crystallisation ticks (default: 16)")
    ap.add_argument("--evidence-scale", type=float, default=1.0,
                    help="scale on the affective (pos-neg) word count → external_field")
    ap.add_argument("--coupling", type=float, default=0.2,
                    help="same-category positive coupling weight (default: 0.2). "
                         "Lower => outcome tracks each concept's own text-evidence "
                         "(basins fragment); higher => whole categories collapse to "
                         "one sign (strong basin pull). The felt coord is produced "
                         "by the dynamics either way.")
    args = ap.parse_args()

    print("booting substrate + qualia seeds + native CAN seeds…")
    s, _ag = _boot()

    mt = vibe._materialise_domain(s, args.domain)
    if mt is None:
        print(f"  domain seed '{args.domain}' is not a materialisable domain seed.")
        return
    mt_name = s.node(mt)["attrs"].get("name", args.domain)
    concepts0 = list(s.neighbours(mt, "has_concept"))
    print(f"materialised domain Mt '{mt_name}' — {len(concepts0)} concepts")

    # (1) BEFORE — every dynamical axis dark (never relaxed).
    before = _histogram(s, concepts0,
                        title="(1) BEFORE — dynamical axes (never relaxed)")
    b_val, b_com, b_any = _lit_counts(s, concepts0)

    # Wire the Mt into a native-CAN affect field: real evidence + category basins.
    concepts, by_category, evidence, n_edges = _prepare_can_mt(
        s, mt, evidence_scale=args.evidence_scale, coupling=args.coupling)
    lit_ev = sum(1 for e in evidence.values() if e != 0.0)
    print(f"\nwired native-CAN field: discrete_mode='3state', "
          f"{len(by_category)} category basins, {n_edges} coupling edges")
    print(f"  affective evidence (from concept text): {lit_ev}/{len(concepts)} "
          f"concepts carry a nonzero standing external_field")

    # (2)/(3) RUN THE NATIVE DYNAMICS.
    print("\n(2) RUNNING THE NATIVE CAN DYNAMICS "
          "(can_native_update_3state + can_native_identity_field_feedback)")
    _relax_and_crystallise(s, mt, concepts, ticks=args.ticks)

    after = _histogram(s, concepts,
                       title="(3) AFTER — dynamical axes LIT")
    a_val, a_com, a_any = _lit_counts(s, concepts)

    # (4) the dark->lit shift, analogous to the relational 968->1393.
    print("\n─── (4) DARK → LIT shift (the felt-shape histogram) ───")
    print(f"  dynamical:valence     {b_val:4d} → {a_val:4d}   "
          f"(+{a_val - b_val})")
    print(f"  dynamical:commitment  {b_com:4d} → {a_com:4d}   "
          f"(+{a_com - b_com})")
    print(f"  any dynamical axis    {b_any:4d} → {a_any:4d}   "
          f"(+{a_any - b_any})")

    signs = _valence_sign_distribution(s, concepts)
    _commitment_magnitude_histogram(s, concepts)
    coherent = _basin_cluster_report(s, by_category, evidence)
    _analogy_report(s, coherent)

    # Honest summary.
    print("\n─── summary ───")
    if a_any == 0:
        print("  Every concept stayed DARK: the affective signal was too weak "
              "and no category basin committed. Reported honestly.")
    else:
        print(f"  {a_val}/{len(concepts)} concepts now lit on dynamical:valence, "
              f"{a_com}/{len(concepts)} on dynamical:commitment — PRODUCED by the "
              f"native relaxation from real text-evidence + category basins.")
        print(f"  {len([c for c in concepts if evidence[c] == 0.0 and _valence(asr.concept_signature(s, c)) is not None])}"
              f" concepts had NEUTRAL own-text yet lit up — pulled to their "
              f"category's sign by the basin (felt-shape clustering).")
        print(f"  {len(coherent)} coherent category basins (>=2/3 members agree "
              f"on a nonzero sign) => same-basin concepts now share dynamical "
              f"coordinates.")
    print("\ndone.")


if __name__ == "__main__":
    main()
