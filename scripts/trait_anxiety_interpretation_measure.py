#!/usr/bin/env python3
"""BLOCK 292000 -- TRAIT-ANXIETY NEGATIVE INTERPRETATION BIAS confirmatory measure
(pre-registered).

Reproduces MacLeod & Mathews' TRAIT x AMBIGUITY INTERACTION: high trait-anxious
(high-skepticism) agents interpret AMBIGUOUS threat stimuli as anxiety-provoking
more than low-anxious agents, while SAFE and THREAT stimuli are interpreted
identically by every temperament (personality-invariant endpoints). See
TRAIT_ANXIETY_INTERPRETATION_PREREG.md (§4-§7).

This script is a MEASURE -- it takes NO decision. It sweeps the pre-registered
SKEPTICISM x AMBIGUITY grid through domains/trait_anxiety_world.py, records the
PRODUCED anxiety-label rate per cell (the graph's ms.emotion == anxiety code 3),
and checks it against the analytic oracle. The emotion is produced by the REAL
emx_anxiety region predicate + mod_securing formula; the adapter only sets the
stimulus (exploration_urge), seeds the skepticism trait, syncs skepticism_bias,
run_rules, and reads ms.emotion/ms.securing.

Sections:
  factorial grid       -- deterministic single agent per cell, PRODUCED vs ORACLE
  G-interaction        -- high-skep minus low-skep anxiety RATE, per band, with CIs
                          (jittered cohort so the deterministic mapping yields a
                          rate in (0,1) for _boot_ci, mirroring marshmallow)
  G-dissociation       -- SAFE all-0, THREAT all-1 across the skep sweep (invariant)
  G-ablation-falsifier -- skepticism_bias forced to 0 => ambiguous interaction ~0
  G-glass-box          -- skep_level/exploration_urge/skepticism_bias/securing/
                          emotion read straight off graph_to_dict + source audit
  G-discipline         -- canonical .so md5, integer-native, no new seed
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np                                              # noqa: E402
import domains.disposition as disp                              # noqa: E402
import domains.trait_modulator_bridge as tmb                    # noqa: E402
from domains.trait_anxiety_world import (                       # noqa: E402
    TraitAnxietyWorld, AMBIGUITY_BANDS, SKEPTICISM_LEVELS,
    ANXIETY_CODE, COMPETENCE, K, SECURING_HI,
    securing as oracle_securing, anxiety_fires as oracle_anxiety,
    skepticism_bias as oracle_bias, _DRIVE_OVER, _MS_OVER)

OUTDIR = os.path.join(ROOT, "results", "trait_anxiety_interpretation")
CANON_MD5 = "a32ed336662eaa9eb6df27b7112541ac"   # canonical .so, native-only CAN cutover
BLOCK = 292000
N = 60                # agents per cohort (mirrors marshmallow N)
JITTER = 10           # exploration_urge jitter half-width for the CI cohort
_RNG = np.random.default_rng(BLOCK)

# The skepticism cohorts for the interaction contrast: LOW trait-anxiety vs HIGH.
LOW_SKEP = (-4, -2)
HIGH_SKEP = (2, 4)


def _boot_ci(xs, reps=2000, seed=BLOCK):
    xs = np.asarray(xs, float)
    if len(xs) == 0:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    means = xs[rng.integers(0, len(xs), size=(reps, len(xs)))].mean(axis=1)
    return (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))


# --------------------------------------------------------------------------- #
# The jitter window per band. The mapping is FULLY DETERMINISTIC (integer
# arithmetic, no mechanism noise), so -- exactly as marshmallow jitters a
# temperament/prior family per cohort to feed _boot_ci -- we jitter the STIMULUS
# ambiguity (exploration_urge) WITHIN each band to obtain a rate in (0,1). The
# jitter is bounded by the band's own pre-registered margin to the securing_hi
# boundary so it NEVER manufactures a cross that the band's construction forbids:
#   * SAFE ceiling sits AT 50 at skep=+4 (margin 0 above) -> jitter DOWNWARD only
#     (eu in [center-JITTER, center]); the band stays sub-boundary by design.
#   * THREAT floor sits AT 60 at skep=-4 (margin 10 above) -> jitter UPWARD only;
#     the band stays over-boundary by design.
#   * AMBIGUOUS straddles the boundary (skep=0 lands EXACTLY on 50) -> jitter
#     SYMMETRIC so the cohort straddles the crossing and the rate reflects how
#     far the skepticism offset has moved the baseline across 50. This is the
#     ONLY band where jitter produces an intermediate rate -- which is precisely
#     where the human interaction lives.
# --------------------------------------------------------------------------- #
def _jitter_offsets(band):
    if band == "safe":
        return np.arange(-JITTER, 1)          # downward only (stay sub-boundary)
    if band == "threat":
        return np.arange(0, JITTER + 1)       # upward only (stay over-boundary)
    return np.arange(-JITTER, JITTER + 1)     # ambiguous: symmetric straddle


def _cohort_rate(world, band, eu, skep_levels):
    """PRODUCED anxiety rate over a jittered-exploration_urge cohort at the given
    skepticism levels -- the graph's own ms.emotion==anxiety, N samples."""
    offs = _jitter_offsets(band)
    hits = []
    for _ in range(N):
        d = int(_RNG.choice(offs))
        lvl = int(_RNG.choice(list(skep_levels)))
        c = world.classify(eu + d, lvl)
        hits.append(1.0 if c["anxiety"] else 0.0)
    return hits


# ---------------------------------------------------------------- factorial grid
def factorial_grid():
    """Deterministic single agent per (band, skep) cell: PRODUCED label + securing
    vs the analytic oracle. all_match is the produced-not-hand-set discipline."""
    w = TraitAnxietyWorld()
    grid, all_match, all_securing_match = {}, True, True
    for band, eu in AMBIGUITY_BANDS.items():
        row = {}
        for lvl in SKEPTICISM_LEVELS:
            c = w.classify(eu, lvl)
            osec = oracle_securing(eu, lvl)
            oanx = bool(oracle_anxiety(eu, lvl))
            lbl_ok = (c["anxiety"] == oanx)
            sec_ok = (c["securing"] == osec)
            all_match = all_match and lbl_ok
            all_securing_match = all_securing_match and sec_ok
            row[f"skep{lvl:+d}"] = dict(
                produced_securing=c["securing"], oracle_securing=osec,
                produced_anxiety=bool(c["anxiety"]), oracle_anxiety=oanx,
                emotion_name=c["emotion_name"], match=bool(lbl_ok and sec_ok))
        grid[band] = row
    w.close() if hasattr(w, "close") else None
    return dict(grid=grid, labels_match_oracle=bool(all_match),
                securing_matches_oracle=bool(all_securing_match),
                bands=AMBIGUITY_BANDS, skepticism_levels=list(SKEPTICISM_LEVELS),
                anxiety_code=ANXIETY_CODE)


# ------------------------------------------------- G-interaction (per-band effect)
def g_interaction():
    """The TRAIT x AMBIGUITY interaction, measured SEPARATELY in each band as the
    PERSONALITY EFFECT = high-skepticism anxiety rate minus low-skepticism rate,
    with bootstrap 95% CIs. The human signature: the effect is present ONLY in the
    AMBIGUOUS band; SAFE and THREAT show ~0 effect (invariant endpoints)."""
    w = TraitAnxietyWorld()
    out = {}
    for band, eu in AMBIGUITY_BANDS.items():
        low = _cohort_rate(w, band, eu, LOW_SKEP)
        high = _cohort_rate(w, band, eu, HIGH_SKEP)
        ci_low, ci_high = _boot_ci(low), _boot_ci(high)
        low_m, high_m = float(np.mean(low)), float(np.mean(high))
        effect = high_m - low_m
        # high CI-separated ABOVE low (the interaction present in this band)
        separated = ci_high[0] > ci_low[1]
        out[band] = dict(
            exploration_urge=eu,
            low_skep_levels=list(LOW_SKEP), high_skep_levels=list(HIGH_SKEP),
            low_skep_rate=round(low_m, 4), low_skep_ci=[round(x, 4) for x in ci_low],
            high_skep_rate=round(high_m, 4), high_skep_ci=[round(x, 4) for x in ci_high],
            personality_effect=round(effect, 4),
            high_ci_separated_above_low=bool(separated))
    w.close() if hasattr(w, "close") else None
    # the interaction VERDICT: separated in ambiguous, NOT separated in safe/threat
    amb = out["ambiguous"]
    safe = out["safe"]
    threat = out["threat"]
    interaction_shape = (amb["high_ci_separated_above_low"]
                         and not safe["high_ci_separated_above_low"]
                         and not threat["high_ci_separated_above_low"])
    return dict(per_band=out,
                ambiguous_personality_effect=amb["personality_effect"],
                safe_personality_effect=safe["personality_effect"],
                threat_personality_effect=threat["personality_effect"],
                verdict_interaction_shape=bool(interaction_shape),
                note="personality bends ONLY the ambiguous interpretation; "
                     "safe/threat effects ~0 -> INTERACTION not a main effect")


# ------------------------------------------------- G-dissociation (invariance)
def g_dissociation():
    """The endpoint DISSOCIATION (deterministic, exact): SAFE band all-0 and
    THREAT band all-1 across the ENTIRE skepticism sweep -- personality-INVARIANT
    endpoints, the proof it is an interaction and not a main effect."""
    w = TraitAnxietyWorld()
    safe = {lvl: bool(w.classify(AMBIGUITY_BANDS["safe"], lvl)["anxiety"])
            for lvl in SKEPTICISM_LEVELS}
    threat = {lvl: bool(w.classify(AMBIGUITY_BANDS["threat"], lvl)["anxiety"])
              for lvl in SKEPTICISM_LEVELS}
    ambiguous = {lvl: bool(w.classify(AMBIGUITY_BANDS["ambiguous"], lvl)["anxiety"])
                 for lvl in SKEPTICISM_LEVELS}
    w.close() if hasattr(w, "close") else None
    safe_all_none = not any(safe.values())
    threat_all_anx = all(threat.values())
    amb_flips = (len(set(ambiguous.values())) == 2)   # the band that MOVES
    return dict(
        safe_labels={f"skep{k:+d}": v for k, v in safe.items()},
        threat_labels={f"skep{k:+d}": v for k, v in threat.items()},
        ambiguous_labels={f"skep{k:+d}": v for k, v in ambiguous.items()},
        safe_all_none=bool(safe_all_none),
        threat_all_anxiety=bool(threat_all_anx),
        ambiguous_flips_with_trait=bool(amb_flips),
        verdict_dissociation=bool(safe_all_none and threat_all_anx and amb_flips))


# ------------------------------------------- G-ablation-falsifier (bias forced 0)
def _classify_bias_ablated(w, eu, skep_level):
    """Re-run a cell with skepticism_bias FORCED to 0 after sync (the §7
    falsifier). Everything else identical -- so securing = exploration_urge + K,
    independent of the trait; the ambiguous band should stop flipping."""
    native = w._native()
    w._set(w.drive, "exploration_urge", eu)
    for k, v in _DRIVE_OVER.items():
        w._set(w.drive, k, v)
    w._set(w.drive, "exploration_urge", eu)
    w._set(w.ms, "competence", COMPETENCE)
    w._set(w.ms, "competence_epoch", _MS_OVER["epoch"])
    w._set(w.ms, "emotion_epoch", -1.0)
    disp.set_trait_seed(w, "skepticism", float(skep_level))
    tmb.sync_traits_to_modulator(w, run=False)
    w._set(w.ms, "skepticism_bias", 0.0)                 # <-- THE ABLATION
    native.run_rules()
    a = w._attrs(w.ms)
    return dict(securing=int(a.get("securing") or 0),
                anxiety=(int(a.get("emotion") or 0) == ANXIETY_CODE))


def g_ablation_falsifier():
    """With skepticism_bias forced to 0, the ambiguous-band personality effect
    must VANISH (all cells collapse to the no-bias securing = eu + K = 50, none)
    and the high-minus-low rate goes to ~0. If it SURVIVES, the effect is not
    coming from the trait->set-point pathway and the claim is false."""
    w = TraitAnxietyWorld()
    eu = AMBIGUITY_BANDS["ambiguous"]
    cells = {lvl: _classify_bias_ablated(w, eu, lvl) for lvl in SKEPTICISM_LEVELS}
    # jittered cohort rates under ablation (same offsets, straddling)
    offs = _jitter_offsets("ambiguous")

    def rate(skep_levels):
        hits = []
        for _ in range(N):
            d = int(_RNG.choice(offs)); lvl = int(_RNG.choice(list(skep_levels)))
            hits.append(1.0 if _classify_bias_ablated(w, eu + d, lvl)["anxiety"] else 0.0)
        return hits
    low = rate(LOW_SKEP); high = rate(HIGH_SKEP)
    ci_low, ci_high = _boot_ci(low), _boot_ci(high)
    w.close() if hasattr(w, "close") else None
    effect = float(np.mean(high) - np.mean(low))
    # baseline no-bias securing for the ambiguous band
    no_bias_securing = eu + K
    all_collapse = all(c["securing"] == no_bias_securing and not c["anxiety"]
                       for c in cells.values())
    separated = ci_high[0] > ci_low[1]
    return dict(
        ambiguous_cells={f"skep{k:+d}": dict(securing=v["securing"],
                                             anxiety=v["anxiety"])
                         for k, v in cells.items()},
        no_bias_securing=no_bias_securing,
        all_cells_collapse_to_no_bias=bool(all_collapse),
        low_skep_rate=round(float(np.mean(low)), 4), low_skep_ci=[round(x, 4) for x in ci_low],
        high_skep_rate=round(float(np.mean(high)), 4), high_skep_ci=[round(x, 4) for x in ci_high],
        ablated_personality_effect=round(effect, 4),
        interaction_survives=bool(separated),
        verdict_falsifier=bool(all_collapse and not separated),
        note="skepticism_bias=0 => securing independent of trait => ambiguous "
             "interaction VANISHES; if it survives the claim is false")


# --------------------------------------------------------------- G-glass-box
def g_glass_box():
    """Read skep_level / exploration_urge / skepticism_bias / securing / emotion
    straight off graph_to_dict at three representative cells + audit the adapter
    source for the forbidden tokens (must be zero)."""
    w = TraitAnxietyWorld()
    readouts = {}
    for tag, (eu, lvl) in dict(
            ambiguous_low=(AMBIGUITY_BANDS["ambiguous"], -4),
            ambiguous_high=(AMBIGUITY_BANDS["ambiguous"], 4),
            threat_low=(AMBIGUITY_BANDS["threat"], -4)).items():
        w.classify(eu, lvl)
        d = w.s.graph_to_dict()
        ms = [n for n in d["nodes"] if n["type"] == "ModulatorState"][0]["attrs"]
        drive = [n for n in d["nodes"] if n["type"] == "Drive"][0]["attrs"]
        readouts[tag] = dict(
            exploration_urge=int(drive.get("exploration_urge") or 0),
            skepticism_bias=int(ms.get("skepticism_bias") or 0),
            securing=int(ms.get("securing") or 0),
            emotion=int(ms.get("emotion") or 0),
            skep_level=lvl, read_via="graph_to_dict")
    w.close() if hasattr(w, "close") else None

    adapter = os.path.join(ROOT, "domains", "trait_anxiety_world.py")
    src = open(adapter).read()
    forbidden = ["graph_rewrite.run(", "gr.run(", "._match(", "._apply(",
                 "make_rule(", "graph_rewrite("]
    hits = {p: len(re.findall(re.escape(p), src)) for p in forbidden}
    shaping = {t: len(re.findall(r"\b" + re.escape(t) + r"\b", src))
               for t in ["reward_signal", "punish", "reinforce", "backprop", "gradient"]}
    api = {c: len(re.findall(r"\b" + re.escape(c) + r"\b", src))
           for c in ["set_attr", "run_rules", "set_trait_seed",
                     "sync_traits_to_modulator", "ensure_modulator_state"]}
    return dict(
        readouts=readouts,
        forbidden_hits=hits, source_audit_clean=all(v == 0 for v in hits.values()),
        shaping_tokens=shaping, no_shaping=all(v == 0 for v in shaping.values()),
        substrate_api_calls=api,
        mechanism=dict(
            emotion="graph region predicate emx_anxiety (build_modulator_seeds order 10) "
                    "sets ms.hit_anxiety; emx_readoff (order 13) writes ms.emotion",
            securing="graph formula mod_securing (order 6) over exploration_urge + K + skepticism_bias",
            bias="trait_modulator_bridge.sync_traits_to_modulator writes ms.skepticism_bias "
                 "from the crystallised skepticism level (STEP=15)",
            adapter_role="set exploration_urge (stimulus ambiguity) + skepticism seed, "
                         "sync bias, run_rules, READ ms.emotion/ms.securing"),
        verdict_glass_box=bool(all(v == 0 for v in hits.values())
                               and all(v == 0 for v in shaping.values())))


# --------------------------------------------------------------- G-discipline
def g_discipline():
    so = os.path.join(ROOT, "runners", "dsl", "python", "substrate_rs", "_native.abi3.so")
    md5 = hashlib.md5(open(so, "rb").read()).hexdigest() if os.path.exists(so) else None
    # No new seed authored (prereg §8). Confirm no trait_anxiety seed file exists
    # and (belt-and-braces) that nothing named trait_anxiety is in load_all_seeds.
    seed_path = os.path.join(ROOT, "seeds", "trait_anxiety_interpretation.json")
    new_seed_exists = os.path.exists(seed_path)
    from substrate.boot_all import _read_seeds
    seeds = _read_seeds(os.path.join(ROOT, "seeds"))
    absent = not any("trait_anxiety" in s for s in seeds)
    # integer-native: PRODUCED securing values are all integers (checked in grid);
    # here confirm the analytic oracle over the whole grid is integer-valued.
    non_integer = [oracle_securing(eu, lvl)
                   for _b, eu in AMBIGUITY_BANDS.items() for lvl in SKEPTICISM_LEVELS
                   if not float(oracle_securing(eu, lvl)).is_integer()]
    return dict(
        canonical_so_md5=md5, canonical_untouched=(md5 == CANON_MD5),
        no_new_seed_file=(not new_seed_exists),
        no_trait_anxiety_in_load_all=bool(absent),
        integer_native=(len(non_integer) == 0), non_integer_securing=non_integer[:10],
        world_constants=dict(competence=COMPETENCE, K=K, securing_hi=SECURING_HI,
                             skepticism_step=15,
                             bands=AMBIGUITY_BANDS, skep_levels=list(SKEPTICISM_LEVELS)),
        oracle_bias_scale={f"skep{lvl:+d}": oracle_bias(lvl) for lvl in SKEPTICISM_LEVELS},
        verdict_discipline=bool(md5 == CANON_MD5 and not new_seed_exists
                                and absent and len(non_integer) == 0))


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    print("factorial grid ..."); grid = factorial_grid()
    print("G-interaction ..."); inter = g_interaction()
    print("G-dissociation ..."); diss = g_dissociation()
    print("G-ablation-falsifier ..."); abl = g_ablation_falsifier()
    print("G-glass-box ..."); gb = g_glass_box()
    print("G-discipline ..."); disc = g_discipline()
    result = dict(block=BLOCK, n_per_cohort=N, rng_seed=BLOCK, jitter_half_width=JITTER,
                  low_skep=list(LOW_SKEP), high_skep=list(HIGH_SKEP),
                  factorial_grid=grid, g_interaction=inter, g_dissociation=diss,
                  g_ablation_falsifier=abl, g_glass_box=gb, g_discipline=disc)
    path = os.path.join(OUTDIR, "results.json")
    json.dump(result, open(path, "w"), indent=1)
    print("wrote", path)
    print(json.dumps(dict(
        grid_labels_match_oracle=grid["labels_match_oracle"],
        grid_securing_matches_oracle=grid["securing_matches_oracle"],
        interaction_shape=inter["verdict_interaction_shape"],
        ambiguous_effect=inter["ambiguous_personality_effect"],
        safe_effect=inter["safe_personality_effect"],
        threat_effect=inter["threat_personality_effect"],
        ambiguous_low_ci=inter["per_band"]["ambiguous"]["low_skep_ci"],
        ambiguous_high_ci=inter["per_band"]["ambiguous"]["high_skep_ci"],
        dissociation=diss["verdict_dissociation"],
        falsifier=abl["verdict_falsifier"],
        ablated_effect=abl["ablated_personality_effect"],
        glass_box=gb["verdict_glass_box"],
        discipline=disc["verdict_discipline"]), indent=1))


if __name__ == "__main__":
    main()
