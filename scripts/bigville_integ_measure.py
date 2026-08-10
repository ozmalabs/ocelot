"""bigville_integ_measure -- the R10 MACRO REGIME CLASSIFIER (block 258000).

Reads the per-tick MACRO series (activity + cost) produced by the assembled town
and classifies it against the FIVE fake/broken signatures vs PUNCTUATED EQUILIBRIUM,
per BIGVILLE_MOVEMENT_ECONOMY_SPEC.md §0 (the punctuated-equilibrium capstone) + §3
R10. The criteria are PRE-REGISTERED (BIGVILLE_INTEG_PREREG.md); this module only
computes the metrics and applies them. The verdict is whatever the REAL data says --
a dead fixpoint / smooth / noise / EXPLODED result is a FINDING, reported honestly,
never tuned away.

The seven regimes:
  EXPLODED            -- a runaway (units error / coefficient runaway): a BUG,
                         categorically distinct from an endogenous catastrophe.
  FROZEN              -- a diorama: essentially no activity ever (max ~ 0 from t0).
  DEAD_FIXPOINT       -- ran, then ground to a halt and STAYED halted (dead tail).
  SMOOTH              -- gradual/linear change, low volatility, no sharp transitions.
  WHITE_NOISE         -- no equilibria: low autocorrelation, no dwell structure,
                         light-tailed bursts.
  CLEAN_PERIODIC      -- too regular to be adaptive: a dominant periodic component.
  PUNCTUATED_EQUILIBRIUM -- STABILITY -> RAPID CHANGE -> STABILITY: long dwells +
                         heavy-tailed cascades + cost spikes AT the transitions.
"""
from __future__ import annotations

import json
import math
import sys

# ---- pre-registered thresholds (see BIGVILLE_INTEG_PREREG.md) -----------------
FROZEN_TOTAL_ACT = 3          # sum(activity) <= this => nothing ever happened
DEAD_TAIL_FRAC = 0.33         # last third of ticks...
DEAD_TAIL_EPS = 0            # ...with activity <= this everywhere => dead fixpoint
EXPLODE_FACTOR = 20.0         # last-decile mean > this * first-decile mean & rising
LOW_DWELL_QUANTILE = 0.50     # activity <= this quantile counts as a "stable" tick
BURST_QUANTILE = 0.90         # activity >= this quantile counts as a "burst"
HEAVY_TAIL_RATIO = 5.0        # max burst / median-nonzero >= this => heavy-tailed
PERIODIC_ACF = 0.60           # a dominant autocorr peak (lag>1) >= this => periodic
NOISE_ACF = 0.20             # |lag-1 acf| < this AND no dwell => white noise
SMOOTH_CV = 0.35             # coeff of variation of activity < this => smooth
STABLE_FRACTION_MIN = 0.55    # >= this fraction of ticks stable => real dwell


def _mean(x):
    return sum(x) / len(x) if x else 0.0


def _std(x):
    if len(x) < 2:
        return 0.0
    m = _mean(x)
    return math.sqrt(sum((v - m) ** 2 for v in x) / len(x))


def _quantile(x, q):
    if not x:
        return 0.0
    s = sorted(x)
    i = min(len(s) - 1, int(q * (len(s) - 1)))
    return s[i]


def _acf(x, lag):
    n = len(x)
    if n <= lag + 1:
        return 0.0
    m = _mean(x)
    denom = sum((v - m) ** 2 for v in x)
    if denom == 0:
        return 0.0
    num = sum((x[i] - m) * (x[i + lag] - m) for i in range(n - lag))
    return num / denom


def _runs_of_stable(x, thr):
    """Lengths of maximal runs of consecutive stable (<=thr) ticks -- the DWELL-TIME
    distribution."""
    runs, cur = [], 0
    for v in x:
        if v <= thr:
            cur += 1
        else:
            if cur:
                runs.append(cur)
            cur = 0
    if cur:
        runs.append(cur)
    return runs


def _cascades(x, thr):
    """Sizes (summed activity) of maximal runs of consecutive BURST (>thr) ticks --
    the CASCADE/AVALANCHE-SIZE distribution."""
    sizes, cur = [], 0
    for v in x:
        if v > thr:
            cur += v
        else:
            if cur:
                sizes.append(cur)
            cur = 0
    if cur:
        sizes.append(cur)
    return sizes


def classify_regime(macro, *, exploded=None):
    """Return (verdict, evidence). macro is a list of {tick,activity,cost}.
    `exploded` is the harness's own runaway flag (None or a dict)."""
    A = [int(m["activity"]) for m in macro]
    C = [int(m["cost"]) for m in macro]
    T = len(A)
    ev = {"ticks": T}
    if T == 0:
        return "NO_DATA", ev

    # ---- EXPLODED (a BUG, distinct from an endogenous catastrophe) ------------
    dec = max(1, T // 10)
    first_dec = _mean(C[:dec]) + _mean(A[:dec])
    last_dec = _mean(C[-dec:]) + _mean(A[-dec:])
    rising = _mean((A + C)[-dec:]) > _mean((A + C)[-2 * dec:-dec]) if T >= 2 * dec else False
    ev["cost_first_decile"] = round(_mean(C[:dec]), 2)
    ev["cost_last_decile"] = round(_mean(C[-dec:]), 2)
    ev["first_decile_load"] = round(first_dec, 2)
    ev["last_decile_load"] = round(last_dec, 2)
    if exploded is not None:
        ev["harness_flag"] = exploded
        return "EXPLODED", ev
    if first_dec > 0 and last_dec > EXPLODE_FACTOR * first_dec and rising:
        ev["reason"] = "load grew %.1fx over the run and is still rising" % (
            last_dec / max(1e-9, first_dec))
        return "EXPLODED", ev

    # ---- summary stats --------------------------------------------------------
    tot_act = sum(A)
    max_act = max(A)
    nz = [a for a in A if a > 0]
    med_nz = _quantile(nz, 0.5) if nz else 0.0
    low_thr = _quantile(A, LOW_DWELL_QUANTILE)
    burst_thr = _quantile(A, BURST_QUANTILE)
    stable_ticks = sum(1 for a in A if a <= low_thr)
    stable_fraction = stable_ticks / T
    dwell = _runs_of_stable(A, max(low_thr, 0))
    cascades = _cascades(A, burst_thr)
    acf1 = _acf(A, 1)
    peak_acf, peak_lag = 0.0, 0
    for lag in range(2, max(3, T // 3)):
        v = _acf(A, lag)
        if v > peak_acf:
            peak_acf, peak_lag = v, lag
    cv_act = (_std(A) / _mean(A)) if _mean(A) > 0 else 0.0
    heavy_ratio = (max_act / med_nz) if med_nz > 0 else (float("inf") if max_act > 0 else 0.0)

    # cost-spike / activity-transition coincidence (triangulation)
    dA = [abs(A[i] - A[i - 1]) for i in range(1, T)]
    cost_spike_thr = _quantile(C, 0.90)
    trans_thr = _quantile(dA, 0.90) if dA else 0
    spike_ticks = set(i for i in range(1, T) if C[i] >= cost_spike_thr and cost_spike_thr > 0)
    trans_ticks = set(i for i in range(1, T) if dA[i - 1] >= trans_thr and trans_thr > 0)
    coincide = (len(spike_ticks & trans_ticks) / max(1, len(trans_ticks))) if trans_ticks else 0.0

    ev.update({
        "activity_total": tot_act, "activity_max": max_act,
        "activity_median_nonzero": med_nz, "activity_mean": round(_mean(A), 3),
        "cost_mean": round(_mean(C), 2), "cost_max": max(C), "cost_min": min(C),
        "stable_fraction": round(stable_fraction, 3),
        "dwell_runs": len(dwell), "dwell_max": (max(dwell) if dwell else 0),
        "dwell_mean": round(_mean(dwell), 2) if dwell else 0.0,
        "cascade_count": len(cascades), "cascade_max": (max(cascades) if cascades else 0),
        "cascade_sizes_sorted": sorted(cascades, reverse=True)[:10],
        "heavy_tail_ratio": (round(heavy_ratio, 2) if heavy_ratio != float("inf") else "inf"),
        "acf_lag1": round(acf1, 3), "acf_peak": round(peak_acf, 3), "acf_peak_lag": peak_lag,
        "cv_activity": round(cv_act, 3),
        "cost_transition_coincidence": round(coincide, 3),
    })

    # ---- FROZEN: nothing ever happened ---------------------------------------
    if tot_act <= FROZEN_TOTAL_ACT:
        ev["reason"] = "sum(activity)=%d <= %d: a diorama" % (tot_act, FROZEN_TOTAL_ACT)
        return "FROZEN", ev

    # ---- DEAD_FIXPOINT: ran then halted and stayed halted ---------------------
    tail_n = max(1, int(DEAD_TAIL_FRAC * T))
    head_act = sum(A[:T - tail_n])
    tail_act = sum(A[T - tail_n:])
    ev["head_activity"] = head_act
    ev["tail_activity"] = tail_act
    if head_act > FROZEN_TOTAL_ACT and tail_act <= DEAD_TAIL_EPS:
        ev["reason"] = ("activity in the first %d ticks=%d then ZERO for the last %d"
                        % (T - tail_n, head_act, tail_n))
        return "DEAD_FIXPOINT", ev

    # ---- CLEAN_PERIODIC: a dominant regular period ----------------------------
    if peak_acf >= PERIODIC_ACF and acf1 < peak_acf:
        ev["reason"] = "dominant autocorr peak %.2f at lag %d" % (peak_acf, peak_lag)
        return "CLEAN_PERIODIC", ev

    # ---- PUNCTUATED_EQUILIBRIUM: long dwells + heavy tail + cost coincidence ---
    heavy = (heavy_ratio == float("inf")) or (heavy_ratio >= HEAVY_TAIL_RATIO)
    long_dwell = stable_fraction >= STABLE_FRACTION_MIN and (dwell and max(dwell) >= 3)
    if long_dwell and heavy and len(cascades) >= 1:
        ev["reason"] = ("stable_fraction=%.2f (max dwell %d) + heavy-tailed cascades "
                        "(max %d vs median-nonzero %.0f) + cost/transition coincidence %.2f"
                        % (stable_fraction, max(dwell), (max(cascades) if cascades else 0),
                           med_nz, coincide))
        return "PUNCTUATED_EQUILIBRIUM", ev

    # ---- WHITE_NOISE: no autocorrelation, no dwell, light tail ----------------
    if abs(acf1) < NOISE_ACF and not long_dwell and not heavy:
        ev["reason"] = ("acf_lag1=%.2f, stable_fraction=%.2f, heavy_ratio=%s: "
                        "structureless" % (acf1, stable_fraction, ev["heavy_tail_ratio"]))
        return "WHITE_NOISE", ev

    # ---- SMOOTH: gradual, low volatility, no sharp transitions ----------------
    if cv_act < SMOOTH_CV:
        ev["reason"] = "coeff of variation %.2f < %.2f: gradual/linear" % (cv_act, SMOOTH_CV)
        return "SMOOTH", ev

    # ---- residual: structured but not cleanly one of the above ----------------
    # report the closest by the dominant evidence (honest ambiguity).
    if long_dwell and heavy:
        ev["reason"] = "punctuated-like but weak cost coincidence (%.2f)" % coincide
        return "PUNCTUATED_EQUILIBRIUM", ev
    if long_dwell:
        ev["reason"] = ("long dwells (stable_fraction=%.2f) but light-tailed bursts "
                        "(heavy_ratio=%s): intermittent, not full SOC"
                        % (stable_fraction, ev["heavy_tail_ratio"]))
        return "PUNCTUATED_WEAK", ev
    ev["reason"] = ("no clean signature: acf1=%.2f cv=%.2f stable=%.2f heavy=%s"
                    % (acf1, cv_act, stable_fraction, ev["heavy_tail_ratio"]))
    return "UNRESOLVED", ev


def main(argv):
    path = argv[1] if len(argv) > 1 else "results/bigville_integ/macro.json"
    with open(path) as f:
        data = json.load(f)
    macro = data.get("macro", data) if isinstance(data, dict) else data
    exploded = data.get("exploded") if isinstance(data, dict) else None
    verdict, ev = classify_regime(macro, exploded=exploded)
    print("MACRO REGIME VERDICT:", verdict)
    print("EVIDENCE:")
    for k, v in ev.items():
        print("  %-28s %s" % (k, v))
    return verdict


if __name__ == "__main__":
    main(sys.argv)
