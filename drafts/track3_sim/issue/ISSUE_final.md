# Tier-A exactness resolves below the model's own latency noise floor — the reference engine fails its own exact gate while passing its own realism gate on the same trace

## Good-faith framing

This is a benchmark-feedback issue, filed under the rules that explicitly protect
good-faith reports about the benchmark itself. It is **not** a submission, a score
dispute, or a claim that anything is broken in the code. It is a reproducible
observation about one gate's *well-posedness* with respect to the stated Track 3 goal —
"a faster simulator that still behaves like a real exchange" — together with a suggested
fix. Everything below runs against your own public repo, your own image, your own
reference cache, and your own gate functions. Please read it as "here is something we
measured, here is how to reproduce it, and here is one way it could be tightened," not as
a complaint. Happy to be told we've mismodelled something.

## The observation, stated plainly

Take the reference ABIDES baseline (`track3-abides-baseline:latest`, pinned
`f9cbe51`). Re-run it having re-drawn **only its latency stream** — a stream the scenario
itself declares to be random (`latency_config: {model: uniform | log_normal | pareto,
...}`) — while holding the agent decision RNG fixed. Score that trace against the
scenario's **own** reference-cache trace, through **both** of your own gates, on the
**same bytes**:

- **Tier-A (`semantics.check_tier_a`, exact)** rejects the re-drawn oracle on **60 / 60**
  stochastic re-seeds.
- **Tier-B (`semantics.check_tier_b`, tolerant)** admits **59 / 60** of those same traces.
- The **return-realism core** of the stylized-fact gate — return-distribution KS and
  volatility-clustering ACF, the two robust Cont facts — is invariant across the re-draw
  class: **58 / 60**.

So the canonical correct simulator, re-drawing a stream the scenario *declares* to be
random, is rejected by the exact gate on 100% of stochastic scenarios while being
admitted by its own calibrated tolerant gates on ~98% of the identical traces. On
**59 / 60** re-seeds, Tier-A fails **and** Tier-B (or the KS∧ACF core) passes on the very
same trace.

A latency model that draws nothing — the `eq_deterministic_baseline` control — is a true
no-op under the re-seed: **all 5 / 5** re-seeds pass every gate, all four stylized-fact
numbers exactly `0.000`. That control is the instrument's null and shows the re-seed is
surgical: reseeding a stream that isn't drawn changes nothing.

The reading we draw: **Tier-A is resolving finer than the noise floor of the model's own
declared stochastic-latency physics.** Your README itself concedes the tolerant ceiling
"comes from the natural run-to-run variation of correct simulations." A valid alternate
latency draw is exactly such a variation — the tolerant gate is calibrated to admit it as
one market, and does — yet Tier-A demands agreement on the exact-order coordinate that a
different-but-valid latency draw necessarily changes. On the stated goal, that measures
implementation identity, not simulation correctness.

## What causes it (one paragraph, mechanism)

The kernel event calendar is keyed on `(deliver_at, (sender_id, recipient_id, message))`,
and `deliver_at = sent_time + int(latency)` where `latency` is a per-message
`RandomState` draw. On a busy calendar the gap between neighbouring `deliver_at` values is
typically much smaller than the latency draw's own jitter, so a different valid latency
draw reorders near-ties at the book. Because the matching engine is order-sensitive
(who-crosses-whom depends on arrival order, and fills feed back into agent state), that
reorder rewrites the **event set** — not just timestamps. So a latency re-draw moves the
exact-order coordinate that Tier-A gates (event coverage + fill sequence + Kendall-τ),
while leaving the market statistics the tolerant gate reads (return KS, volatility-
clustering ACF, mean spread) inside their calibrated tolerances. The exact-order
coordinate carries the RNG entropy; the semantic coordinate does not.

## Exact reproduction

Everything is public. From a clean checkout of
`Agenthon-2026/track3-simulation-public`:

```bash
# 1. Build the reference baseline image (pinned ABIDES f9cbe51 + the abides_fork adapter)
docker build --platform=linux/amd64 -t track3-abides-baseline:latest baselines/

# 2. Build the local reference-trace cache the gate scores against
#    (git lfs pull first if the unit parquet files are still LFS pointers)
python regression_suite/build_reference_cache.py

# 3. In the Python 3.13 scoring environment that has this repo's
#    qfbench2_track_simulation + qfbench2_common installed, run the reproduction:
python reproduce.py                    # 13-scenario panel, 3 latency reseeds each
#   or, to reproduce the exact headline counts below (5 reseeds -> 60 stochastic runs):
python reproduce.py --reseeds 5 --json-out wellposed.json
```

`reproduce.py` (attached) imports **only** public code — `qfbench2_track_simulation.semantics`,
`qfbench2_common.scoring.stylized_facts`, and (inside the baseline image only) the public
`abides_fork` adapter. The latency-only re-seed is a ~20-line monkeypatch of
`abides_fork.config._draw_random_state`, written to a temp file and bind-mounted read-only
into your image, so the image and the checkout are both untouched. For each scenario it
(a) runs the baseline at its native seed, (b) confirms the faithfulness gate (the
instrumented baseline reproduces the reference-cache trace exactly), (c) re-seeds the
latency `RandomState` only, and (d) scores every re-seeded trace through Tier-A,
Tier-B, and `stylized_fact_report` / `admissible` on the same bytes, printing the table
below.

## Headline numbers

From `python reproduce.py --reseeds 5` (13 scenarios × 5 latency re-seeds; 60 stochastic +
5 deterministic-control runs). The faithfulness gate passes on all 13 scenarios, so every
movement is caused by the latency re-seed, not by instrumentation.

| scenario | latency | Tier-A (exact) | Tier-B (tolerant) | realism KS∧ACF | realism full-4 | KS med | ACF med |
|---|---|---:|---:|---:|---:|---:|---:|
| s001_price_time_priority | uniform | 0/5 | 4/5 | 4/5 | 0/5 | 0.070 | 0.099 |
| s012_partial_fill_cancel_race | log_normal | 0/5 | 5/5 | 5/5 | 0/5 | 0.012 | 0.006 |
| **eq_deterministic_baseline** (control) | deterministic | **5/5** | **5/5** | **5/5** | **5/5** | 0.000 | 0.000 |
| eq_uniform_tight | uniform | 0/5 | 5/5 | 5/5 | 4/5 | 0.031 | 0.075 |
| eq_uniform_wide | uniform | 0/5 | 5/5 | 4/5 | 4/5 | 0.022 | 0.099 |
| eq_lognormal_lowsigma | log_normal | 0/5 | 5/5 | 5/5 | 5/5 | 0.019 | 0.049 |
| eq_lognormal_highsigma | log_normal | 0/5 | 5/5 | 5/5 | 4/5 | 0.026 | 0.046 |
| eq_pareto_heavytail | pareto | 0/5 | 5/5 | 5/5 | 2/5 | 0.025 | 0.056 |
| as01_base_mix | log_normal | 0/5 | 5/5 | 5/5 | 5/5 | 0.017 | 0.021 |
| as06_throughput_fast | log_normal | 0/5 | 5/5 | 5/5 | 4/5 | 0.009 | 0.021 |
| sf_01_baseline_regime | log_normal | 0/5 | 5/5 | 5/5 | 2/5 | 0.026 | 0.013 |
| gb_base_30agent_30s | log_normal | 0/5 | 5/5 | 5/5 | 3/5 | 0.036 | 0.024 |
| ca_baseline_calm | log_normal | 0/5 | 5/5 | 5/5 | 2/5 | 0.041 | 0.022 |

**Aggregate, stochastic scenarios only (the deterministic control is separated out):**

| quantity | count |
|---|---|
| Tier-A (exact) **fail** | **60 / 60** |
| Tier-B (tolerant) pass on the same traces | **59 / 60** |
| return-realism core (KS ≤ 0.08 ∧ ACF ≤ 0.12) pass | **58 / 60** |
| Tier-A FAIL **and** (Tier-B ∨ KS∧ACF) PASS on the **same** trace | **59 / 60** |
| deterministic-latency control (no draw): all gates pass | **5 / 5** |

Per-statistic, across the 60 stochastic re-seeds: KS **59/60** (median 0.025), ACF
**59/60** (median 0.030). The single Tier-B miss is `s001` perturb-1 at KS = **0.08052**
vs the 0.08000 ceiling — a 0.0005 overshoot on a 604-row micro-scenario, reported as a
fail because the gate says so, not because the market moved.

## Honest caveat (reported transparently, not scoped away)

The **full four-statistic** `admissible()` check passes only **35 / 60**, and we report
that number in the table above rather than hiding it. The gap is confined to the two
high-variance components, not to the market:

- Per-statistic finite pass rates over the 60 stochastic re-seeds: **KS 59/60, ACF
  59/60**, but **Hill tail-index 41/55 finite, depth-JS 47/60**.
- **23 of the 25** full-4 realism failures still pass **both** KS and ACF — i.e. the
  failure is Hill and/or depth-JS only, never the return distribution or volatility
  clustering.
- The reference is fixed, so the Hill scatter against it is the estimator's own run-to-run
  noise: e.g. `eq_pareto_heavytail` |α_cand − α_ref| ranges 0.71 / 1.95 / 2.05 (min/med/max
  over 5 re-seeds), `ca_baseline_calm` 0.78 / 1.67 / 4.94 — a 1.5 ceiling sits inside the
  finite-sample Hill spread a second *correct* reference run would show.
- depth-JS breaches concentrate in the degenerate matching-engine micro-scenarios (`s001`
  is 604 rows and its fill-price series is near-constant, so Hill is literally NaN);
  outside those, depth-JS medians are ≈ 0.001–0.011, far under the 0.10 ceiling.

So we make the narrower, defensible claim: the theorem holds on the gate's **calibrated
semantic core** (Tier-B 59/60; KS∧ACF 58/60), and we hand you the full-4 number (35/60)
plus the attribution so you can weigh the caveat directly. We do **not** claim full-4
invariance — it isn't there, because two of its four estimators are noisy against a single
fixed reference.

## Suggested well-posed fix

The tolerant gates already constrain the semantic invariants a "behaves-like-real" goal
cares about (return distribution, volatility clustering, mean spread). The exact gate adds
a constraint on the RNG-projected exact-order coordinate that the model's *declared*
stochastic-latency physics leaves free. A well-posed gate would:

1. **Gate exactness only where the model is deterministic.** The `eq_deterministic_baseline`
   control shows Tier-A is exactly right when there is no latency draw to reproduce — there,
   the exact-order coordinate *is* determined by the seed. For scenarios whose
   `latency_config.model` is stochastic (`uniform` / `log_normal` / `pareto`), the exact
   fill-sequence / Kendall-τ requirement is finer than the model's own noise floor.
2. **Tolerate the RNG-projected exact-order coordinate** for those scenarios, and instead
   constrain the semantic invariants the tolerant gates already check (which, per this
   report, are invariant across the valid re-draw class). Matching-engine families that are
   genuinely exact-by-design (deterministic tie-break, no latency draw) keep Tier-A.

Concretely: the family → tier mapping (`TIER_A_FAMILIES`) could be made conditional on
whether the scenario declares a stochastic latency model, rather than assigning Tier-A by
family alone. That keeps the exact gate where it is well-formed and lets the tolerant gate
arbitrate where the physics is stochastic.

We are not attached to this particular fix — the point is the diagnostic (exact fails +
tolerant passes on the same bytes ⇒ the exact gate is below the model's noise floor), and
we'd defer to whatever the organizers judge cleanest.

## Honest limits

- **Panel, not census.** 13 of the 65 public scenarios, chosen to span every family and the
  full latency axis (deterministic → uniform tight/wide → lognormal low/high-σ → pareto).
  Per-family n is small (1–2 outside latency-profile). The split is uniform with no
  counterexample to the core within the panel, but we did not run a full 65-scenario sweep.
  `reproduce.py --scenarios ...` extends to any subset if you want the census.
- **Re-seed = independent alternate latency stream**, not a per-message ±ε nudge. This is
  our operationalization of "a different valid latency draw"; a per-message infinitesimal-
  perturbation sensitivity is a finer measurement we did not run.
- **Transfer is conjectured, not proven.** The mechanism (order-pivotal near-injective
  draw→order map + order-sensitive dynamics) should recur in other declared-stochastic
  discrete-event sims graded by an exact comparator, but we verified it only on this
  ABIDES-class baseline here.
- **Stack note.** Sims run on the pinned baseline image (numpy 1.26.4 / pandas 1.5.3); the
  gates run on the 3.13 scoring stack. The gate functions only read parquet and compute
  set-coverage / Kendall-τ / KS / ACF / Hill / JS, which are version-stable, and the exact
  faithfulness gate passing on all 13 scenarios confirms no cross-stack artifact.

## Attachment

`reproduce.py` — the self-contained reproduction described above. It depends only on
`track3-abides-baseline:latest`, the reference cache, the shipped scenarios, and the public
`qfbench2_track_simulation` / `qfbench2_common` gate functions.


---

<details>
<summary><code>reproduce.py</code> (click to expand — paste into your repo root and run)</summary>

```python
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

```

</details>
