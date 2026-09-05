#!/usr/bin/env python3
"""Granularity probe for the DYNAMICAL qualia axes (honest gap #4).

Run: python3 scripts/qualia_commitment_granularity_probe.py [--domain philosophy]

QUESTION (honest gap #4): dynamical:valence quantises `state` with
quantum=1.0/half_width=1 → only {−1,0,+1}. Is finer felt-gradient better carried
by dynamical:commitment (identity_field, quantum=0.25/half_width=4, "9 levels")
than by valence?

WHAT THE UNDERLYING DYNAMICS ACTUALLY PRODUCE (read from the seed rules):

  · state (valence): committed by can_native_update_3state via an IfThenElse
    threshold to sigma ∈ {−1, 0, +1} EXACTLY (seeds/can_native_reimplementation
    .json, "3state" guard). There is NO intermediate state value on the native
    3-state path. So valence is GENUINELY ternary — it is not a coarsening of a
    finer signal, it IS the signal. Widening half_width would quantise nothing
    (state can never be ±2).

  · identity_field (commitment): written by can_native_identity_field_feedback
    (seeds/can_decay_identity.json) as a FIXED ±1 integer step per tick toward
    the sign of the evidence log-odds (a magnitude-scaled step was investigated
    and REJECTED on Lyapunov-stability grounds — see that rule's own `why`). So
    identity_field only ever takes INTEGER values 0, ±1, ±2, ±3, … under
    sustained same-sign evidence.

THE QUANTISER MISMATCH this probe measures empirically:
  commitment quantum = 0.25, so _round_to_vocab(identity_field) = round(if/0.25),
  clamped to ±4. But identity_field steps by whole integers (=4 quantum-steps
  each), so the very FIRST tick (identity_field=±1) already rounds to ±4 and
  clamps. The intermediate coordinates ±1,±2,±3 are UNREACHABLE — every
  committed concept saturates to ±4 immediately. The documented "9 levels"
  collapse, in practice, to {−4, 0, +4}: commitment is effectively as ternary as
  valence, NOT a finer intensity gradient.

This probe RUNS the native dynamics on a real domain and prints the actual
distribution of raw identity_field magnitudes AND the quantised commitment
coordinates, so the finding is measured, not asserted. It also measures whether
quantum=1.0 (matching the integer step size) would expose the real integer
gradient the dynamics DO produce — a faithful change, because it quantises a
value the underlying state genuinely takes, not noise.

CONSTRAINTS: native CAN 3-state path only; felt coords produced by relaxation,
never hand-written; reuses the sweep's _prepare_can_mt / _relax_and_crystallise
and analogy_search.concept_signature. Does NOT touch CAN backend internals.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent
                       / "runners" / "dsl" / "python"))

from substrate_rs import _native

import domains.analogical_thinking as at
import domains.analogy_search as asr
from domains.can_self_worth_bridge import ensure_can_seed

import qualia_vibe_probe as vibe
import qualia_felt_sweep as sweep

ROOT = Path(__file__).resolve().parent.parent
SEEDS = ROOT / "seeds"


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
    ensure_can_seed(s)
    sweep._open_productions(s)
    return s, ag


def main():
    ap = argparse.ArgumentParser(description="commitment granularity probe")
    ap.add_argument("--domain", default="philosophy")
    ap.add_argument("--ticks", type=int, default=16)
    ap.add_argument("--evidence-scale", type=float, default=1.0)
    ap.add_argument("--coupling", type=float, default=0.2)
    args = ap.parse_args()

    print("booting substrate + qualia seeds + native CAN seeds…")
    s, _ag = _boot()
    mt = vibe._materialise_domain(s, args.domain)
    if mt is None:
        print(f"  '{args.domain}' is not a materialisable domain seed.")
        return
    concepts = list(s.neighbours(mt, "has_concept"))
    print(f"materialised '{args.domain}' — {len(concepts)} concepts")

    concepts, by_category, evidence, n_edges = sweep._prepare_can_mt(
        s, mt, evidence_scale=args.evidence_scale, coupling=args.coupling)
    sweep._relax_and_crystallise(s, mt, concepts, ticks=args.ticks)

    # (A) RAW identity_field magnitude distribution — what the dynamics produce.
    raw = Counter()
    raw_vals = []
    for c in concepts:
        v = float(s.node(c)["attrs"].get("identity_field", 0.0))
        raw[abs(round(v))] += 1
        if v != 0.0:
            raw_vals.append(v)
    print("\n─── (A) RAW identity_field |magnitude| distribution "
          "(the value the dynamics actually produce) ───")
    for mag in sorted(raw):
        bar = "█" * raw[mag]
        print(f"  |identity_field| = {mag:3d}   {raw[mag]:3d}  {bar}")
    if raw_vals:
        print(f"  committed concepts: {len(raw_vals)}; "
              f"min|if|={min(abs(v) for v in raw_vals):.0f}, "
              f"max|if|={max(abs(v) for v in raw_vals):.0f}  "
              f"→ every committed concept has |identity_field| ≥ 1 (integer steps)")

    # (B) commitment coordinate under the CURRENT quantum (0.25 / hw 4).
    def _commit_k(v, quantum, hw):
        return asr._round_to_vocab(v, quantum, hw)

    print("\n─── (B) dynamical:commitment coordinate under CURRENT quantum "
          "(0.25 / half_width 4) ───")
    cur = Counter()
    for c in concepts:
        v = s.node(c)["attrs"].get("identity_field", 0.0)
        cur[_commit_k(v, 0.25, 4)] += 1
    for k in sorted(cur, key=lambda x: (x is None, x)):
        label = "dark (0)" if k is None else f"k={k:+d}"
        print(f"  {label:12s} {cur[k]:3d}")
    reachable = sorted(k for k in cur if k is not None)
    print(f"  → distinct NONZERO commitment levels actually reached: {reachable}")
    if reachable and set(map(abs, reachable)) <= {4}:
        print("  → CONFIRMED: only the SATURATED ±4 level is reached. The "
              "intermediate levels ±1,±2,±3 the '9 levels' gloss implies are "
              "UNREACHABLE, because identity_field steps by whole integers "
              "(=4 quantum-steps) — commitment is effectively ternary {−4,0,+4}.")

    # (C) what a quantum MATCHING the integer step (1.0) would expose — a
    # FAITHFUL finer gradient, because it quantises the real integer value the
    # dynamics produce, not noise.
    print("\n─── (C) HYPOTHETICAL quantum=1.0 / half_width=4 (matches the ±1 "
          "integer step the dynamics actually take) ───")
    alt = Counter()
    for c in concepts:
        v = s.node(c)["attrs"].get("identity_field", 0.0)
        alt[_commit_k(v, 1.0, 4)] += 1
    for k in sorted(alt, key=lambda x: (x is None, x)):
        label = "dark (0)" if k is None else f"k={k:+d}"
        bar = "█" * alt[k]
        print(f"  {label:12s} {alt[k]:3d}  {bar}")
    alt_reach = sorted(k for k in alt if k is not None)
    print(f"  → distinct NONZERO levels under quantum=1.0: {alt_reach}")
    print("  NOTE: this only spreads concepts across levels if they are driven "
          "for DIFFERENT numbers of sustained ticks / with decay; under a single "
          "uniform {ticks}-tick drive every committed concept reaches the same "
          "high magnitude and still clamps at the top. The gradient is REAL only "
          "when the evidence histories differ — which is the honest condition "
          "for exposing it.".format(ticks=args.ticks))

    print("\ndone.")


if __name__ == "__main__":
    main()
