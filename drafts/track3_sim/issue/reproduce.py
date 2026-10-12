#!/usr/bin/env python3
"""Reproduce the Track 3 Tier-A well-posedness observation, using ONLY public code.

WHAT THIS SHOWS
---------------
The reference ABIDES engine, re-run with a *different valid draw of its own declared
latency stream* (agent decision RNG held fixed), scored against its OWN reference-cache
trace, through the organizers' OWN gates on the SAME bytes:

  * Tier-A  (semantics.check_tier_a, exact)      -> FAILS on every stochastic scenario
  * Tier-B  (semantics.check_tier_b, tolerant)   -> PASSES ~all the same traces
  * realism (stylized_facts, tolerant)           -> return-distribution KS and
                                                    volatility-clustering ACF invariant

A latency model that draws nothing (the deterministic-latency control) is a true no-op:
the reseed changes nothing and every gate passes. That control is the instrument's null
and shows the reseed is surgical.

The conclusion drawn in ISSUE.md: Tier-A resolves below the model's own declared
stochastic-latency noise floor, so on the stated goal ("a faster simulator that still
behaves like a real exchange") it is measuring implementation identity rather than
simulation behaviour.

WHAT IT DEPENDS ON (all public, all in YOUR repo)
-------------------------------------------------
  * track3-abides-baseline:latest        (docker build baselines/, pinned ABIDES f9cbe51)
  * regression_suite/reference_traces/   (python regression_suite/build_reference_cache.py)
  * regression_suite/scenarios/*.json    (shipped)
  * qfbench2_track_simulation.semantics  (this repo)
  * qfbench2_common.scoring.stylized_facts (the toolkit this repo already depends on)

It imports NOTHING private. The only ABIDES-side code it runs is a ~20-line latency-only
reseed that monkeypatches abides_fork.config._draw_random_state (public repo code); the
patch is written to a temp file and bind-mounted read-only into the baseline image, so the
image and repo checkout are both untouched.

HOW TO RUN
----------
From your repo checkout root, in the Python 3.13 toolkit environment that has
qfbench2_track_simulation + qfbench2_common installed (the scoring env):

    python reproduce.py                       # full 13-scenario panel, 3 reseeds each
    python reproduce.py --reseeds 5           # more reseeds per scenario
    python reproduce.py --scenarios s001_price_time_priority eq_deterministic_baseline
    python reproduce.py --image track3-abides-baseline:latest --repo .

Runtime is dominated by the container sims (a few seconds each for the small scenarios;
s012 is large). The default panel + 3 reseeds is ~50 short container runs.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import tempfile

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------- #
# Organizer gate parameters (the real ones, read straight from the toolkit).
# --------------------------------------------------------------------------- #
# CEILINGS is the admissible() ceiling set the stylized-fact gate uses; the KS and
# spread ceilings are Tier-B's. They are stated here only so the printed table shows
# them next to the measured numbers -- the gate functions apply their own defaults.
CEILINGS = {"ks": 0.08, "acf_abs_l2": 0.12, "hill_abs": 1.5, "depth_js": 0.10}
TIER_B_KS = 0.08
TIER_B_SPREAD_BPS = 10.0

# Default panel: spans every scenario family + the full latency axis (deterministic ->
# uniform tight/wide -> lognormal low/high sigma -> pareto), plus matching-engine,
# agent-mix, stylized-facts and throughput-scale scenarios. Not a census (13 of 65); it
# is the panel behind the numbers in ISSUE.md. The deterministic control MUST be present
# -- it is the instrument's null.
DEFAULT_PANEL = [
    "s001_price_time_priority",       # matching-engine
    "s012_partial_fill_cancel_race",  # matching-engine (large)
    "eq_deterministic_baseline",      # latency-profile -- the no-draw CONTROL
    "eq_uniform_tight",               # latency-profile
    "eq_uniform_wide",                # latency-profile
    "eq_lognormal_lowsigma",          # latency-profile
    "eq_lognormal_highsigma",         # latency-profile
    "eq_pareto_heavytail",            # latency-profile
    "as01_base_mix",                  # agent-mix
    "as06_throughput_fast",           # agent-mix
    "sf_01_baseline_regime",          # stylized-facts
    "gb_base_30agent_30s",            # throughput-scale
    "ca_baseline_calm",               # stylized-facts (calm)
]

# --------------------------------------------------------------------------- #
# The in-container payload. Imports ONLY abides_fork (public repo code, already on
# PYTHONPATH=/opt inside the baseline image) + numpy. It reproduces exactly what the
# shipped `simulate` verb does, except that -- for mode=lat_reseed -- it re-seeds the
# ONE RandomState the latency model owns, and nothing else.
#
# WHY THIS IS A LATENCY-ONLY PERTURBATION. build_config() calls np.random.seed(seed)
# once, then _draw_random_state() mints each component's RandomState in a fixed order:
#     oracle -> exchange(id 0) -> agents(id 1..N) -> latency_model -> kernel
# We wrap _draw_random_state to tag every minted state with its ordinal, let build_config
# run untouched (so the agent/oracle/kernel streams are byte-identical to the reference
# run), then AFTER build we .seed() only the latency model's state in place. The latency
# model holds a live reference to that object, so re-seeding it re-draws the latency
# stream and leaves every other stream exactly as the reference run drew it.
# --------------------------------------------------------------------------- #
_PAYLOAD = r'''
import json, os, pathlib
import numpy as np
from abides_core import abides
from abides_fork import config as cfg
from abides_fork.simulate import reset_abides_counters
from abides_fork.trace import extract_trace

scenario = json.loads(pathlib.Path(os.environ["RS_SCENARIO"]).read_text())
out_dir  = pathlib.Path(os.environ["RS_OUT"]); out_dir.mkdir(parents=True, exist_ok=True)
mode     = os.environ.get("RS_MODE", "baseline")     # baseline | lat_reseed
perturb  = int(os.environ.get("RS_PERTURB", "0"))

# Tag every minted RandomState with its mint ordinal so we can find the latency one.
minted = []
orig_draw = cfg._draw_random_state
def tagged():
    rs = orig_draw(); minted.append(rs); return rs
cfg._draw_random_state = tagged

reset_abides_counters()
config = cfg.build_config(scenario)
cfg._draw_random_state = orig_draw

# Mint order: 0=oracle, 1=exchange, 2..=agents, latency (iff latency_config), kernel(last).
n = len(minted)
has_latency = bool(scenario.get("latency_config"))
latency_idx = (n - 2) if has_latency else None

def reseed_only_latency(salt):
    if latency_idx is None:
        return False
    base = int(scenario.get("seed", 0)) & 0xFFFFFFFF
    new_seed = (base * 2654435761 + salt * 40503 + 0x9E3779B1) % (2**32)
    minted[latency_idx].seed(int(new_seed))   # in-place: the model holds this object
    return True

reseeded = False
if mode == "lat_reseed":
    reseeded = reseed_only_latency(perturb)

# A "deterministic" latency model returns a constant and performs NO RandomState draw,
# so re-seeding it is a true no-op regardless of has_latency_config. That is the control.
model = (scenario.get("latency_config") or {}).get("model", "deterministic")
draws_latency = model in ("uniform", "log_normal", "pareto")

end_state = abides.run(config)
trace = extract_trace(end_state)
trace.to_parquet(out_dir / "trace.parquet", compression="snappy", index=False)
(out_dir / "meta.json").write_text(json.dumps({
    "mode": mode, "perturb": perturb, "has_latency_config": has_latency,
    "latency_reseeded": reseeded, "draws_latency": draws_latency,
    "latency_model": model, "n_rows": int(len(trace)),
}))
print(json.dumps({"ok": True, "mode": mode, "perturb": perturb,
                  "latency_reseeded": reseeded, "draws_latency": draws_latency,
                  "n_rows": int(len(trace))}))
'''


def run_in_container(image, payload_path, scenario_path, out_dir, mode, perturb):
    """Run the payload inside the baseline image, network disabled, image untouched."""
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "docker", "run", "--rm", "--network", "none",
        "-v", f"{payload_path}:/payload.py:ro",
        "-v", f"{scenario_path}:/input/scenario.json:ro",
        "-v", f"{out_dir}:/out",
        "-e", "RS_SCENARIO=/input/scenario.json",
        "-e", "RS_OUT=/out",
        "-e", f"RS_MODE={mode}",
        "-e", f"RS_PERTURB={perturb}",
        "--entrypoint", "python", image, "/payload.py",
    ]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    meta_path = out_dir / "meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    return p.returncode, meta, p.stderr[-1200:]


def score(cand: pd.DataFrame, ref: pd.DataFrame, semantics, sf) -> dict:
    """Score one candidate trace against the reference through BOTH public gates."""
    out: dict = {}
    okA, brA = semantics.check_tier_a(cand, ref)
    out["tier_a_pass"] = bool(okA)
    out["tier_a_breaches"] = brA

    try:
        okB, brB = semantics.check_tier_b(
            cand, ref, ks_ceiling=TIER_B_KS, spread_bps_tolerance=TIER_B_SPREAD_BPS
        )
        out["tier_b_pass"] = bool(okB)
        out["tier_b_breaches"] = brB
    except Exception as exc:  # organizer-side fault surfaces, does not crash the panel
        out["tier_b_pass"] = None
        out["tier_b_breaches"] = [f"{type(exc).__name__}: {exc}"]

    # realism: the four stylized-fact numbers vs their ceilings, computed with the
    # scorer's own extraction (mid_price_series / depth_histogram).
    try:
        cm = semantics.mid_price_series(cand).to_numpy(dtype=float)
        rm = semantics.mid_price_series(ref).to_numpy(dtype=float)
        cd = semantics.depth_histogram(cand)
        rd = semantics.depth_histogram(ref)
        if cm.size >= 2 and rm.size >= 2 and np.all(cm > 0) and np.all(rm > 0):
            # The Hill estimator can hit log(0) -> NaN on a near-constant (degenerate)
            # micro-scenario fill series; that is expected and is exactly the estimator
            # noise reported as the honest caveat. Silence only the numpy noise, not the
            # result -- a NaN Hill still shows up in the report and drives a full-4 breach.
            with np.errstate(divide="ignore", invalid="ignore"):
                rep = sf.stylized_fact_report(cm, rm, cand_depth_hist=cd, ref_depth_hist=rd)
                okR, brR = sf.admissible(rep, CEILINGS)
            out["realism_report"] = {k: float(v) for k, v in rep.items()}
            out["realism_admissible"] = bool(okR)
            out["realism_breaches"] = brR
        else:
            out["realism_report"] = None
            out["realism_admissible"] = None
            out["realism_breaches"] = ["insufficient/non-positive mid-price series"]
    except Exception as exc:
        out["realism_report"] = None
        out["realism_admissible"] = None
        out["realism_breaches"] = [f"{type(exc).__name__}: {exc}"]
    return out


def _core_ok(rep: dict | None) -> bool | None:
    """Return-realism core: KS and volatility-clustering ACF both within ceiling.

    This is the part of the realism gate whose tolerance the organizers calibrated on
    'the natural run-to-run variation of correct simulations' -- the semantic core, as
    opposed to the two high-variance estimators (Hill tail index, depth Jensen-Shannon).
    """
    if not rep:
        return None
    return rep["ks"] <= CEILINGS["ks"] and rep["acf_abs_l2"] <= CEILINGS["acf_abs_l2"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=".", help="path to the track3 repo checkout root (default: .)")
    ap.add_argument("--image", default="track3-abides-baseline:latest", help="baseline docker image")
    ap.add_argument("--reseeds", type=int, default=3, help="latency reseeds per scenario (>=1; default 3)")
    ap.add_argument("--scenarios", nargs="*", default=None, help="scenario stems (default: the panel)")
    ap.add_argument("--json-out", default=None, help="optional path to dump the full per-reseed record")
    args = ap.parse_args()

    repo = pathlib.Path(args.repo).resolve()
    scen_dir = repo / "regression_suite" / "scenarios"
    ref_dir = repo / "regression_suite" / "reference_traces"

    # Public gates -- imported from the repo + the toolkit it depends on.
    sys.path.insert(0, str(repo))
    try:
        from qfbench2_track_simulation import semantics
        from qfbench2_common.scoring import stylized_facts as sf
    except Exception as exc:
        print(f"ERROR: could not import the public gates: {exc}\n"
              f"  Run this in the Python 3.13 scoring environment that has\n"
              f"  qfbench2_track_simulation (this repo) and qfbench2_common installed.", file=sys.stderr)
        return 2

    if not ref_dir.exists():
        print(f"ERROR: reference cache {ref_dir} not found.\n"
              f"  Build it first:  python regression_suite/build_reference_cache.py", file=sys.stderr)
        return 2

    panel = args.scenarios or DEFAULT_PANEL
    perturbs = list(range(1, max(1, args.reseeds) + 1))

    # Write the in-container payload once, to a temp file bind-mounted read-only.
    tmp = tempfile.NamedTemporaryFile("w", suffix=".py", delete=False)
    tmp.write(_PAYLOAD)
    tmp.flush()
    payload_path = pathlib.Path(tmp.name)

    results = {"ceilings": CEILINGS, "tier_b_ks": TIER_B_KS, "tier_b_spread_bps": TIER_B_SPREAD_BPS,
               "tier_a_tol_ns": semantics.DEFAULT_TIMESTAMP_TOLERANCE_NS,
               "tier_a_kendall_floor": semantics.DEFAULT_KENDALL_TAU_FLOOR,
               "reseeds": len(perturbs), "panel": []}

    with tempfile.TemporaryDirectory(prefix="t3_wellposed_") as work_s:
        work = pathlib.Path(work_s)
        for stem in panel:
            scen = scen_dir / f"{stem}.json"
            if not scen.exists():
                print(f"  SKIP {stem}: scenario file not found", file=sys.stderr)
                continue
            sid = json.loads(scen.read_text()).get("scenario_id")
            ref_path = ref_dir / str(sid) / "trace.parquet"
            if not ref_path.exists():
                print(f"  SKIP {stem}: reference trace {ref_path} not found", file=sys.stderr)
                continue
            ref = pd.read_parquet(ref_path)
            entry = {"scenario": stem, "scenario_id": sid, "n_ref_rows": int(len(ref))}
            print(f"\n=== {stem}  (ref rows {len(ref)}) ===", flush=True)

            # 1. baseline (native seed) + faithfulness gate: instrumented run == reference (EXACT).
            rc, meta, err = run_in_container(args.image, payload_path, scen, work / stem / "baseline",
                                             "baseline", 0)
            if rc != 0:
                entry["error"] = f"baseline run failed: {err}"
                results["panel"].append(entry)
                print(f"  baseline FAILED: {err}", flush=True)
                continue
            base = pd.read_parquet(work / stem / "baseline" / "trace.parquet")
            okF, brF = semantics.check_tier_a(base, ref)
            entry["faithfulness_pass"] = bool(okF)
            entry["latency_model"] = meta.get("latency_model")
            print(f"  faithfulness (baseline == reference, exact): {okF}", flush=True)

            # 2. latency-only reseeds, scored through BOTH gates on the same bytes.
            entry["reseeds"] = []
            for pv in perturbs:
                rc, meta, err = run_in_container(args.image, payload_path, scen, work / stem / f"lat_p{pv}",
                                                 "lat_reseed", pv)
                if rc != 0:
                    entry["reseeds"].append({"perturb": pv, "error": err})
                    continue
                cand = pd.read_parquet(work / stem / f"lat_p{pv}" / "trace.parquet")
                sc = score(cand, ref, semantics, sf)
                sc["perturb"] = pv
                sc["latency_reseeded"] = bool(meta.get("latency_reseeded"))
                sc["draws_latency"] = bool(meta.get("draws_latency"))
                entry["reseeds"].append(sc)
            results["panel"].append(entry)

    payload_path.unlink(missing_ok=True)

    print_report(results)
    if args.json_out:
        pathlib.Path(args.json_out).write_text(json.dumps(results, indent=2))
        print(f"\nWrote full record to {args.json_out}")
    return 0


def print_report(results: dict) -> None:
    ce = results["ceilings"]
    print("\n" + "=" * 100)
    print("TRACK 3 TIER-A WELL-POSEDNESS -- reference engine scored against its OWN reference,")
    print("through the organizers' OWN gates, on the SAME bytes, under a latency-only reseed.")
    print("=" * 100)
    print(f"gate params: Tier-A timestamp tol {results['tier_a_tol_ns']} ns, Kendall-tau floor "
          f"{results['tier_a_kendall_floor']}; Tier-B KS<={results['tier_b_ks']}, spread<="
          f"{results['tier_b_spread_bps']} bps; realism ceilings KS<={ce['ks']} ACF<="
          f"{ce['acf_abs_l2']} Hill<={ce['hill_abs']} depthJS<={ce['depth_js']}")
    print()

    hdr = (f"{'scenario':<30}{'latency':<14}{'faith':<7}{'TierA':<8}{'TierB':<8}"
           f"{'realism4':<10}{'KS&ACF':<8}{'KS(med)':<9}{'ACF(med)':<9}")
    print(hdr)
    print("-" * len(hdr))

    # accumulators, splitting stochastic scenarios from the no-draw control(s)
    agg = {"stoch": {"A": [0, 0], "B": [0, 0], "R4": [0, 0], "core": [0, 0]},
           "ctrl":  {"A": [0, 0], "B": [0, 0], "R4": [0, 0], "core": [0, 0]}}
    single_joint = []  # scenarios where TierA fails and (TierB or KS&ACF) passes on the same trace

    for e in results["panel"]:
        if "reseeds" not in e:
            print(f"{e['scenario']:<30}{'?':<14}ERROR {e.get('error','')[:40]}")
            continue
        rs = [x for x in e["reseeds"] if "error" not in x]
        n = len(rs)
        model = e.get("latency_model") or "?"
        # is this a real draw, or the no-draw control? A deterministic latency model
        # performs no RandomState draw, so a reseed cannot change its trace -- that is
        # the instrument's null. Bucket it separately from the stochastic scenarios.
        drew = any(x.get("draws_latency") for x in rs)
        bucket = "stoch" if drew else "ctrl"

        nA = sum(1 for x in rs if x["tier_a_pass"])
        nB = sum(1 for x in rs if x["tier_b_pass"])
        nR4 = sum(1 for x in rs if x["realism_admissible"])
        ncore = sum(1 for x in rs if _core_ok(x.get("realism_report")))
        ks_med = np.median([x["realism_report"]["ks"] for x in rs if x.get("realism_report")]) if any(x.get("realism_report") for x in rs) else float("nan")
        acf_med = np.median([x["realism_report"]["acf_abs_l2"] for x in rs if x.get("realism_report")]) if any(x.get("realism_report") for x in rs) else float("nan")

        agg[bucket]["A"][0] += nA; agg[bucket]["A"][1] += n
        agg[bucket]["B"][0] += nB; agg[bucket]["B"][1] += n
        agg[bucket]["R4"][0] += nR4; agg[bucket]["R4"][1] += n
        agg[bucket]["core"][0] += ncore; agg[bucket]["core"][1] += n

        if drew:
            single_joint.extend(
                (not x["tier_a_pass"]) and (bool(x["tier_b_pass"]) or bool(_core_ok(x.get("realism_report"))))
                for x in rs
            )

        faith = "PASS" if e.get("faithfulness_pass") else "FAIL"
        tag = "" if drew else "  (control)"
        print(f"{e['scenario']:<30}{model:<14}{faith:<7}"
              f"{f'{nA}/{n}':<8}{f'{nB}/{n}':<8}{f'{nR4}/{n}':<10}{f'{ncore}/{n}':<8}"
              f"{ks_med:<9.4f}{acf_med:<9.4f}{tag}")

    print("-" * len(hdr))
    s, c = agg["stoch"], agg["ctrl"]
    print("\nSTOCHASTIC scenarios (latency stream actually re-drawn):")
    print(f"  Tier-A (exact)          pass {s['A'][0]}/{s['A'][1]}   <- the exact gate rejects the oracle")
    print(f"  Tier-B (tolerant)       pass {s['B'][0]}/{s['B'][1]}   <- the same traces admitted")
    print(f"  realism KS&ACF core     pass {s['core'][0]}/{s['core'][1]}   <- return + volatility-clustering invariant")
    print(f"  realism full-4          pass {s['R4'][0]}/{s['R4'][1]}   <- includes Hill + depth-JS (estimator-noisy)")
    joint = sum(1 for x in single_joint if x)
    print(f"  Tier-A FAIL AND (Tier-B OR KS&ACF) PASS on the SAME trace: {joint}/{len(single_joint)}")
    if c["A"][1]:
        print("\nDETERMINISTIC-LATENCY CONTROL (no draw -> reseed is a no-op):")
        print(f"  Tier-A pass {c['A'][0]}/{c['A'][1]} | Tier-B pass {c['B'][0]}/{c['B'][1]} | "
              f"realism full-4 pass {c['R4'][0]}/{c['R4'][1]}   <- all-pass expected (instrument null)")

    print("\nHEADLINE:")
    print(f"  The reference engine FAILS its own exact gate (Tier-A {s['A'][0]}/{s['A'][1]} pass)")
    print(f"  while PASSING its own tolerant gate (Tier-B {s['B'][0]}/{s['B'][1]}, KS&ACF {s['core'][0]}/{s['core'][1]})")
    print(f"  on the identical bytes -- and the no-draw control passes everything.")
    print("=" * 100)


if __name__ == "__main__":
    raise SystemExit(main())
