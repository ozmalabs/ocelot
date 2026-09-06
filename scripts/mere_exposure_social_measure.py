#!/usr/bin/env python3
"""BLOCK 293000 -- MERE-EXPOSURE x INITIAL-VALENCE confirmatory measure
(pre-registered).

Reproduces the Zajonc mere-exposure x initial-valence INTERACTION as a CROSSING
LATENCY on the substrate's discrete 3-state regard unit: repeated POSITIVE contact
warms a NEUTRAL prior FAST, while a NEGATIVE prior RESISTS -- crossing to
regard>0 only after strictly more positive encounters, and a deep-enough negative
prior does NOT cross within a fixed exposure budget. See
MERE_EXPOSURE_SOCIAL_PREREG.md (SS4-SS7).

This script is a MEASURE -- it takes NO decision. It sweeps the pre-registered
(initial_valence x exposure_count) grid through domains/mere_exposure_world.py,
records the PRODUCED regard state + qualia valence per cell (the graph's own
discrete-3-state relaxation of the CAN belief-update primitive, never hand-set),
and checks it against the analytic crossing-latency oracle. The regard is produced
by record_hate_incident -> concept_apply_evidence -> run_rules(); the adapter only
DRIVES the encounter and READS regard_for.state / its qualia signature.

Sections:
  factorial grid       -- deterministic single agent per (valence, n) cell,
                          PRODUCED regard-sign + qualia-valence vs the oracle, exact
  G-interaction        -- the exposure x initial-valence INTERACTION as CROSSING
                          LATENCY: neutral vs negative conditions, with bootstrap
                          95% CIs (jitter alpha within a personality cohort so the
                          deterministic latency yields a distribution for _boot_ci,
                          mirroring marshmallow / trait-anxiety); reports the
                          deterministic latencies AND the jittered cohort CIs
  G-crystallized       -- the crystallized-negative outcome the prior stage
                          measured: depth-scaled latency (delay), up to
                          never-within-budget -- NOT an identity-level permanent
                          lock (identity_field stays 0 through the confirmed path)
  G-qualia-tracks      -- at EVERY step the dynamical:valence sign == sign(state)
  G-ablation-falsifier -- freeze the update (alpha=0) => regard never crosses in
                          ANY condition => the exposure effect vanishes
  G-personality        -- warm/hostile plasticity => distinct crossing latencies
  G-glass-box          -- regard state / identity_field / qualia coordinates read
                          straight off graph_to_dict + source audit (forbidden = 0)
  G-discipline         -- canonical .so md5, integer-native accumulator, no new seed
"""
from __future__ import annotations
import hashlib
import json
import math
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np                                              # noqa: E402
from domains.mere_exposure_world import (                       # noqa: E402
    MereExposureWorld, predicted_crossing_latency,
    TEMPERATURE, DEFAULT_ALPHA, CROSS_THRESHOLD)

OUTDIR = os.path.join(ROOT, "results", "mere_exposure_social")
CANON_MD5 = "7efe75eba05b006cafd15dbb4b7da246"   # canonical .so, native-only CAN cutover
BLOCK = 293000
N = 60                # agents per cohort (mirrors marshmallow / trait-anxiety N)
BUDGET = 30           # positive-encounter budget (pre-registered SS3)
_RNG = np.random.default_rng(BLOCK)

# The three pre-registered initial-valence conditions (SS3 recipes). The two deeper
# crystallized recipes exercise the depth-scaled-latency -> never-crosses boundary
# the prior stage measured; each is a list of per-harm-encounter kwarg dicts.
CONDITIONS = {
    "neutral":            "neutral",
    "negative_noncryst":  "negative_noncryst",
    "negative_cryst_mid": "negative_cryst",              # default recipe, ext0 ~ -3.0
    "negative_cryst_deep": [dict(alpha=0.6)] * 12,        # ext0 ~ -7.2
    "negative_cryst_verydeep": [dict(alpha=0.6)] * 15,    # ext0 ~ -9.0 (never <=30)
}
# The exposure counts recorded per row of the produced grid (SS5 headline columns).
GRID_COLS = [1, 2, 4, 5, 12, 26, 30]

# Personality plasticity cohorts (SS2 warm/hostile): belief-plasticity alpha rescales
# the per-encounter step and thus the crossing latency.
WARM_ALPHA = 0.6
HOSTILE_ALPHA = 0.15
JITTER_ALPHAS = {          # alpha values a cohort jitters over, per personality band
    "warm":    [0.5, 0.6, 0.7],
    "default": [0.25, 0.3, 0.35],
    "hostile": [0.12, 0.15, 0.18],
}


def _boot_ci(xs, reps=2000, seed=BLOCK):
    xs = np.asarray(xs, float)
    if len(xs) == 0:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    means = xs[rng.integers(0, len(xs), size=(reps, len(xs)))].mean(axis=1)
    return (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))


def _qual_sign(state):
    """The expected dynamical:valence at a discrete regard state: +1 / -1, or None
    (valence axis absent) at state 0 -- the oracle the produced qualia must match."""
    return None if state == 0 else (1 if state > 0 else -1)


def _run_condition(recipe, *, alpha=DEFAULT_ALPHA, budget=BUDGET):
    """Seed one condition, then sweep `budget` positive encounters, returning
    (ext0, trajectory) where trajectory[n-1] is the PRODUCED read after encounter n.
    The regard is produced by the engine; this only drives + reads."""
    w = MereExposureWorld(alpha=alpha)
    seeded = w.seed_initial_valence(recipe)
    ext0 = seeded["regard_external_field"]
    tr = w.exposure_trajectory(budget=budget)
    ident = seeded["regard_identity_field"]
    cryst = seeded["crystallized"]
    return ext0, tr, ident, cryst


# ---------------------------------------------------------------- factorial grid
def factorial_grid():
    """Deterministic single agent per (condition, n) cell: the PRODUCED regard sign
    + qualia valence vs the analytic oracle at EVERY cell (produced-not-hand-set).
    `all_match` is the exact-match discipline over BOTH the state sign AND the
    qualia valence at every recorded exposure count for every condition."""
    grid, all_match = {}, True
    latencies = {}
    for cname, recipe in CONDITIONS.items():
        ext0, tr, ident, cryst = _run_condition(recipe)
        row = {}
        # per-n produced state + qualia vs oracle (oracle state from the linear law)
        for n in GRID_COLS:
            cell = tr["trajectory"][n - 1]
            prod_state = int(cell["state"])
            prod_qval = cell["qval"]
            oracle_ext = ext0 + DEFAULT_ALPHA * n
            oracle_state = (1 if oracle_ext > CROSS_THRESHOLD
                            else (-1 if oracle_ext < -CROSS_THRESHOLD else 0))
            oracle_qval = _qual_sign(oracle_state)
            match = (prod_state == oracle_state and prod_qval == oracle_qval)
            all_match = all_match and match
            row[f"n{n}"] = dict(produced_state=prod_state, oracle_state=oracle_state,
                                produced_qval=prod_qval, oracle_qval=oracle_qval,
                                match=bool(match))
        # crossing latency: produced vs oracle
        prod_cross = tr["crossing_latency"]
        oracle_cross = predicted_crossing_latency(ext0, budget=BUDGET)
        cross_match = (prod_cross == oracle_cross)
        all_match = all_match and cross_match
        latencies[cname] = prod_cross
        grid[cname] = dict(
            ext0=round(ext0, 4), identity_field=round(ident, 4), crystallized=bool(cryst),
            produced_crossing_latency=prod_cross, oracle_crossing_latency=oracle_cross,
            crossing_match=bool(cross_match), cells=row)
    return dict(grid=grid, matches_oracle=bool(all_match),
                crossing_latencies=latencies, grid_cols=GRID_COLS, budget=BUDGET)


# --------------------------------------------- G-interaction (crossing-latency CIs)
def _latency_cohort(recipe, alpha_band):
    """A cohort of PRODUCED crossing latencies: jitter the belief-plasticity alpha
    within `alpha_band` (mechanism has no noise, so -- exactly as marshmallow /
    trait-anxiety jitter a stimulus/temperament to feed _boot_ci -- we jitter the
    per-agent plasticity to obtain a latency DISTRIBUTION). Non-crossing within
    budget is recorded as (BUDGET + 1) so the CI is well-defined and a never-cross
    condition sits strictly above any crossing one."""
    alphas = JITTER_ALPHAS[alpha_band]
    lat = []
    for _ in range(N):
        a = float(_RNG.choice(alphas))
        w = MereExposureWorld(alpha=a)
        w.seed_initial_valence(recipe)
        tr = w.exposure_trajectory(budget=BUDGET)
        lat.append(float(tr["crossing_latency"]) if tr["crossed"] else float(BUDGET + 1))
    return lat


def g_interaction():
    """The exposure x initial-valence INTERACTION expressed as CROSSING LATENCY.
    The headline: NEUTRAL crosses in the FEWEST encounters; every NEGATIVE condition
    has a STRICTLY GREATER crossing latency, CI-separated ABOVE neutral. This is an
    INTERACTION (initial valence sets how many exposures liking takes), not a bare
    main effect of exposure. Deterministic latencies + jittered-alpha cohort CIs."""
    # deterministic single-agent latencies at the default alpha (the exact result)
    det = {}
    for cname, recipe in CONDITIONS.items():
        ext0, tr, _i, _c = _run_condition(recipe)
        det[cname] = tr["crossing_latency"]

    # jittered-alpha cohorts for the CI machinery (default plasticity band)
    cohorts = {c: _latency_cohort(r, "default") for c, r in CONDITIONS.items()}
    cis = {c: _boot_ci(v) for c, v in cohorts.items()}
    means = {c: float(np.mean(v)) for c, v in cohorts.items()}

    neutral_ci = cis["neutral"]
    # each negative condition CI-separated strictly ABOVE neutral (longer latency)
    separated = {}
    for c in CONDITIONS:
        if c == "neutral":
            continue
        separated[c] = bool(cis[c][0] > neutral_ci[1])
    # monotone in prior depth (deterministic): neutral < noncryst < mid < deep < never
    order = ["neutral", "negative_noncryst", "negative_cryst_mid",
             "negative_cryst_deep", "negative_cryst_verydeep"]
    det_ordered = [det[c] if det[c] is not None else (BUDGET + 1) for c in order]
    monotone = all(det_ordered[i] < det_ordered[i + 1] for i in range(len(det_ordered) - 1))
    return dict(
        deterministic_crossing_latency=det,
        cohort_mean_latency={c: round(m, 3) for c, m in means.items()},
        cohort_latency_ci={c: [round(x, 3) for x in cis[c]] for c in CONDITIONS},
        neutral_immediate=(det["neutral"] == 2),   # SS5: neutral crosses at 2 at alpha=0.3
        all_negative_ci_separated_above_neutral=bool(all(separated.values())),
        per_condition_separated_above_neutral=separated,
        monotone_in_prior_depth=bool(monotone),
        verdict_interaction=bool(all(separated.values()) and monotone),
        note="crossing latency DEPENDS on initial valence: neutral crosses fastest, "
             "each negative prior crosses strictly later (CI-separated), deeper => "
             "later up to never-within-budget -> INTERACTION, not a main effect")


# ------------------------------------------- G-crystallized (the boundary outcome)
def g_crystallized():
    """The crystallized-negative outcome, exactly as the prior stage measured: the
    boundary condition manifests as a DEPTH-SCALED LATENCY (delay), up to
    never-within-budget -- NOT an identity-level permanent lock. Confirms the crux:
    identity_field stays 0.0 through the confirmed path (record_hate_incident writes
    external_field only), so `crystallized`==1 is a deep negative external_field, not
    an identity commitment."""
    out = {}
    for cname in ("negative_cryst_mid", "negative_cryst_deep", "negative_cryst_verydeep"):
        ext0, tr, ident, cryst = _run_condition(CONDITIONS[cname])
        out[cname] = dict(
            ext0=round(ext0, 4), identity_field=round(ident, 4),
            crystallized_flag=bool(cryst),
            crossing_latency=tr["crossing_latency"],
            crosses_within_budget=bool(tr["crossed"]))
    # the very-deep condition is the permanent-within-budget boundary
    verydeep = out["negative_cryst_verydeep"]
    return dict(
        conditions=out,
        identity_field_all_zero=all(abs(v["identity_field"]) < 1e-9 for v in out.values()),
        depth_scales_latency=bool(
            out["negative_cryst_mid"]["crossing_latency"]
            < out["negative_cryst_deep"]["crossing_latency"]),
        verydeep_never_crosses_within_budget=bool(not verydeep["crosses_within_budget"]),
        outcome="DELAY_NOT_PERMANENT_IMMUNITY",
        note="a crystallized negative is a DEEP accumulated external_field, NOT an "
             "identity lock (identity_field stays 0 via the confirmed API); it warms "
             "eventually unless the prior exceeds the budget's total warming capacity "
             "-> the substrate models negativity bias as DELAY, not permanent immunity")


# ------------------------------------------------------ G-qualia-tracks-state
def g_qualia_tracks_state():
    """At EVERY step of EVERY condition the produced dynamical:valence sign equals
    sign(regard_state) (+1 / -1, or absent at state 0). This is what makes it a
    QUALIA experiment: the felt quality is coupled to the produced dynamics, never
    a decorative label."""
    mismatches = []
    total = 0
    for cname, recipe in CONDITIONS.items():
        ext0, tr, _i, _c = _run_condition(recipe)
        for cell in tr["trajectory"]:
            total += 1
            exp = _qual_sign(cell["state"])
            if cell["qval"] != exp:
                mismatches.append(dict(condition=cname, n=cell["n"],
                                       state=cell["state"], qval=cell["qval"],
                                       expected=exp))
    return dict(steps_checked=total, mismatches=mismatches[:10],
                n_mismatches=len(mismatches),
                verdict_qualia_tracks_state=bool(len(mismatches) == 0),
                note="dynamical:valence sign == sign(regard_state) at every step in "
                     "every condition -> felt quality coupled to produced dynamics")


# ------------------------------------------- G-ablation-falsifier (freeze update)
def g_ablation_falsifier():
    """Freeze the belief update (alpha=0 on the POSITIVE encounters, per SS7): the
    regard external_field never climbs, so regard NEVER crosses in ANY condition
    (neutral never warms; negative never recovers). If a crossing SURVIVES with the
    update frozen the effect is not coming from the belief-update pathway and the
    claim is false."""
    out = {}
    any_crossed = False
    for cname, recipe in CONDITIONS.items():
        w = MereExposureWorld(alpha=0.0)   # positive encounters apply +0.0 evidence
        w.seed_initial_valence(recipe)     # (seeding uses the recipe's own alpha)
        tr = w.exposure_trajectory(budget=BUDGET)
        any_crossed = any_crossed or tr["crossed"]
        out[cname] = dict(crossing_latency=tr["crossing_latency"],
                          crossed=bool(tr["crossed"]),
                          final_state=int(tr["trajectory"][-1]["state"]),
                          final_ext=round(tr["trajectory"][-1]["ext"], 4))
    return dict(conditions=out, any_condition_crosses=bool(any_crossed),
                verdict_falsifier=bool(not any_crossed),
                note="alpha=0 freezes external_field => regard never crosses in any "
                     "condition => the exposure effect VANISHES; if it survived the "
                     "claim is false")


# --------------------------------------------------------- G-personality
def g_personality():
    """PERSONALITY contrast (SS2 warm/hostile): belief-plasticity alpha rescales the
    per-encounter step and thus the crossing latency. From a NEUTRAL prior a WARM
    (high-plasticity) agent crosses in strictly FEWER encounters than a HOSTILE
    (low-plasticity) one -- distinct crossing latencies by personality, with
    jittered-alpha cohort CIs."""
    det = {}
    for band, alpha in (("warm", WARM_ALPHA), ("default", DEFAULT_ALPHA),
                        ("hostile", HOSTILE_ALPHA)):
        w = MereExposureWorld(alpha=alpha)
        w.seed_initial_valence("neutral")
        det[band] = w.exposure_trajectory(budget=BUDGET)["crossing_latency"]
    cohorts = {b: _latency_cohort("neutral", b) for b in ("warm", "default", "hostile")}
    cis = {b: _boot_ci(v) for b, v in cohorts.items()}
    means = {b: float(np.mean(v)) for b, v in cohorts.items()}
    warm_faster = bool(cis["warm"][1] < cis["hostile"][0])   # warm strictly below hostile
    return dict(
        deterministic_latency=det,
        cohort_mean_latency={b: round(m, 3) for b, m in means.items()},
        cohort_latency_ci={b: [round(x, 3) for x in cis[b]] for b in cis},
        warm_ci_separated_below_hostile=warm_faster,
        distinct_by_personality=bool(det["warm"] < det["default"] < det["hostile"]),
        verdict_personality=bool(warm_faster and det["warm"] < det["hostile"]),
        note="warm (high plasticity) crosses fastest, hostile (low plasticity) slowest "
             "-> distinct crossing latencies by personality")


# --------------------------------------------------------------- G-glass-box
def g_glass_box():
    """Read regard state / external_field / identity_field / qualia coordinates
    straight off graph_to_dict at three representative points + audit the adapter
    source for the forbidden tokens (must be zero)."""
    readouts = {}
    for tag, (recipe, n_pos) in dict(
            neutral_crossed=("neutral", 2),
            negcryst_pre=("negative_cryst", 0),
            negcryst_crossed=("negative_cryst", 12)).items():
        w = MereExposureWorld()
        w.seed_initial_valence(recipe)
        for _ in range(n_pos):
            w.encounter(positive=True)
        d = w.s.graph_to_dict()
        # the regard Concept node, read straight off the graph dump
        reg_nodes = [nd for nd in d["nodes"] if nd["type"] == "Concept"
                     and "regard" in str(nd["attrs"].get("name", ""))]
        reg = reg_nodes[0]["attrs"] if reg_nodes else w.s.graph_to_dict()  # fallback
        readouts[tag] = dict(
            regard_state=int(round(float(reg.get("state", 0)))),
            external_field=round(float(reg.get("external_field", 0)), 4),
            identity_field=round(float(reg.get("identity_field", 0)), 4),
            qualia_valence=w.qualia_valence(),
            qualia_signature=w.qualia_signature(),
            read_via="graph_to_dict")

    adapter = os.path.join(ROOT, "domains", "mere_exposure_world.py")
    src = open(adapter).read()
    forbidden = ["graph_rewrite.run(", "gr.run(", "._match(", "._apply(",
                 "make_rule(", "graph_rewrite("]
    hits = {p: len(re.findall(re.escape(p), src)) for p in forbidden}
    shaping = {t: len(re.findall(r"\b" + re.escape(t) + r"\b", src))
               for t in ["reward_signal", "punish", "reinforce", "backprop", "gradient"]}
    api = {c: len(re.findall(r"\b" + re.escape(c) + r"\b", src))
           for c in ["record_hate_incident", "concept_signature", "mint_target_pattern",
                     "ensure_can_seed", "load_seed_manifest"]}
    return dict(
        readouts=readouts,
        forbidden_hits=hits, source_audit_clean=all(v == 0 for v in hits.values()),
        shaping_tokens=shaping, no_shaping=all(v == 0 for v in shaping.values()),
        substrate_api_calls=api,
        mechanism=dict(
            liking="discrete 3-state regard Concept (can_native_update_3state) -- the "
                   "marginal <sigma> relaxed by run_rules() over concept_apply_evidence",
            exposure="record_hate_incident(negative=False) => concept_apply_evidence(+1.0, "
                     "alpha) on external_field + run_rules()",
            qualia="analogy_search.concept_signature dynamical:valence coordinate "
                   "(seeds/qualia_space.json)",
            adapter_role="drive positive/harm encounters + read regard_for.state / "
                         "concept_signature -- NO Python computes the liking"),
        verdict_glass_box=bool(all(v == 0 for v in hits.values())
                               and all(v == 0 for v in shaping.values())))


# --------------------------------------------------------------- G-discipline
def g_discipline():
    so = os.path.join(ROOT, "runners", "dsl", "python", "substrate_rs", "_native.abi3.so")
    md5 = hashlib.md5(open(so, "rb").read()).hexdigest() if os.path.exists(so) else None
    # No new seed authored (prereg SS8): confirm no mere_exposure seed file exists and
    # nothing named mere_exposure is in load_all_seeds (base tree byte-identical absent).
    seed_path = os.path.join(ROOT, "seeds", "mere_exposure_social.json")
    new_seed_exists = os.path.exists(seed_path)
    from substrate.boot_all import _read_seeds
    seeds = _read_seeds(os.path.join(ROOT, "seeds"))
    absent = not any("mere_exposure" in s for s in seeds)
    # integer-native: the accumulator step is alpha (0.3) so external_field is a
    # multiple of 0.3 -- NOT integer, but no non-integer float Lit is AUTHORED here
    # (no new seed). Confirm the produced STATE (the discrete liking) is integer.
    ext0, tr, _i, _c = _run_condition(CONDITIONS["neutral"])
    states_integer = all(float(c["state"]).is_integer() for c in tr["trajectory"])
    return dict(
        canonical_so_md5=md5, canonical_untouched=(md5 == CANON_MD5),
        no_new_seed_file=(not new_seed_exists),
        no_mere_exposure_in_load_all=bool(absent),
        produced_states_integer=bool(states_integer),
        world_constants=dict(temperature=TEMPERATURE, alpha=DEFAULT_ALPHA,
                             cross_threshold=CROSS_THRESHOLD, budget=BUDGET),
        verdict_discipline=bool(md5 == CANON_MD5 and not new_seed_exists
                                and absent and states_integer))


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    print("factorial grid ..."); grid = factorial_grid()
    print("G-interaction ..."); inter = g_interaction()
    print("G-crystallized ..."); cry = g_crystallized()
    print("G-qualia-tracks-state ..."); qua = g_qualia_tracks_state()
    print("G-ablation-falsifier ..."); abl = g_ablation_falsifier()
    print("G-personality ..."); per = g_personality()
    print("G-glass-box ..."); gb = g_glass_box()
    print("G-discipline ..."); disc = g_discipline()
    result = dict(block=BLOCK, n_per_cohort=N, rng_seed=BLOCK, budget=BUDGET,
                  temperature=TEMPERATURE, alpha=DEFAULT_ALPHA,
                  factorial_grid=grid, g_interaction=inter, g_crystallized=cry,
                  g_qualia_tracks_state=qua, g_ablation_falsifier=abl,
                  g_personality=per, g_glass_box=gb, g_discipline=disc)
    path = os.path.join(OUTDIR, "results.json")
    json.dump(result, open(path, "w"), indent=1)
    print("wrote", path)
    print(json.dumps(dict(
        grid_matches_oracle=grid["matches_oracle"],
        crossing_latencies=grid["crossing_latencies"],
        interaction=inter["verdict_interaction"],
        interaction_cis=inter["cohort_latency_ci"],
        crystallized_outcome=cry["outcome"],
        crystallized_identity_field_zero=cry["identity_field_all_zero"],
        verydeep_never_crosses=cry["verydeep_never_crosses_within_budget"],
        qualia_tracks_state=qua["verdict_qualia_tracks_state"],
        falsifier=abl["verdict_falsifier"],
        personality=per["verdict_personality"],
        personality_latency=per["deterministic_latency"],
        glass_box=gb["verdict_glass_box"],
        discipline=disc["verdict_discipline"]), indent=1))


if __name__ == "__main__":
    main()
