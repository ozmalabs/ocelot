"""
SPIKE / PROOF-OF-CONCEPT ONLY -- NOT PRODUCTION CODE.

Part of CAN_CONCEPT_REIMPLEMENTATION_SPIKE.md (design spike, 2026-08-13).
Pure Python, standalone, no Rust, no PyO3, no seeds, no substrate import.
Does not touch runners/dsl/src/can_ops.rs or any production path. It
exists ONLY to numerically check ONE falsifiable sub-claim registered in
that document: that a DISCRETE, ASYNCHRONOUS (Hopfield-style) threshold
update on the SAME frustrated networks the CAN research already measured
does not exhibit the persistent 2-cycle oscillation that the CURRENT
CONTINUOUS, SYNCHRONOUS (Jacobi) mean-field update
(can_ops.rs::mt_mean_field_marginal) measurably does
(CAN_BELIEF_QUANTIZATION_RESULTS.md Sec 3.1).

This script reproduces the CONTINUOUS solver's math independently (not by
calling the Rust engine) so the "before" comparison is an honest, from-
first-principles replication, not an assumed-true citation. It does NOT
edit, call, or depend on can_ops.rs in any way.

Run: python3 can_concept_poc_discrete_async.py
"""

import random

N = 8
BETA = 2.0
MAX_ITER_CONTINUOUS = 402
MAX_SWEEPS_DISCRETE = 200
N_DRAWS = 30


def round_to_vocab(x, granularity, half_width):
    k = round(x / granularity)
    k = max(-half_width, min(half_width, k))
    return k * granularity


def build_draw(seed, coarse):
    """N=8 complete graph. J ~ Uniform(-1,1) per pair (shared draw between
    coarse/fine at a given seed, exactly as CAN_BELIEF_QUANTIZATION_RESULTS.md
    Sec 2.2 does -- apples to apples, only encoding resolution differs).
    h ~ Uniform(-1,1) fixed nonzero field per node (the PREREG's own
    documented fix for the h=0 degenerate all-zero fixed point)."""
    pair_rng = random.Random(seed * 31 + N)
    field_rng = random.Random(seed * 53 + N)
    J = {}
    for i in range(N):
        for j in range(i + 1, N):
            raw = pair_rng.uniform(-1, 1)
            if coarse:
                v = round_to_vocab(raw, 1.0, 1)       # {-1,0,+1}
            else:
                v = round_to_vocab(raw, 0.25, 4)       # 9-level
            J[(i, j)] = v
            J[(j, i)] = v
    h = {i: field_rng.uniform(-1, 1) for i in range(N)}
    return J, h


def local_field(J, h, state, i):
    return h[i] + sum(J[(i, j)] * state[j] for j in range(N) if j != i)


# ---------------------------------------------------------------------------
# (A) Continuous, SYNCHRONOUS (Jacobi) mean field -- independent replication
# of can_ops.rs::mt_mean_field_marginal's exact update rule, for the
# "before" baseline. Confirms the known oscillation on THIS script's own
# draws before testing whether the discrete/async candidate avoids it.
# ---------------------------------------------------------------------------
def continuous_sync_run(J, h, max_iter):
    state = {i: 0.0 for i in range(N)}
    for _ in range(max_iter):
        new_state = {}
        for i in range(N):
            local = local_field(J, h, state, i)
            new_state[i] = __import__("math").tanh(BETA * local)
        state = new_state
    return state


def continuous_oscillates(J, h):
    s400 = continuous_sync_run(J, h, 400)
    s401 = continuous_sync_run(J, h, 401)
    s402 = continuous_sync_run(J, h, 402)
    gap_opposite = sum((s400[i] - s401[i]) ** 2 for i in range(N)) ** 0.5
    gap_same = sum((s400[i] - s402[i]) ** 2 for i in range(N)) ** 0.5
    return gap_opposite > 0.1 and gap_same < 0.01, gap_opposite, gap_same


# ---------------------------------------------------------------------------
# (B) Discrete, ASYNCHRONOUS (Hopfield-style) threshold update -- the
# candidate "native" reframing. Two variants tested, registered in advance
# as having DIFFERENT theoretical footing:
#   TWO-STATE (sign, no zero): the classical Hopfield case -- Lyapunov
#     monotone-energy-decrease proof applies cleanly (search-confirmed
#     this session, converging across multiple independent sources).
#   THREE-STATE (round(tanh(.)) to nearest of {-1,0,+1}): the CAN model's
#     OWN native vocabulary (seed description: "sigma in {-1,0,+1} (or
#     continuous)") -- but the deadzone case (committed -> neutral when the
#     field is weak) can, on inspection, produce sigma_new*local < sigma_
#     old*local, which breaks the standard proof's strict step. Registered
#     as UNVERIFIED by the theory and checked empirically here rather than
#     assumed.
# Update order is deterministic round-robin (0..N-1), not randomized --
# matching CAN_SYNCHRONOUS_UPDATE_FIX_PREREG.md's own finding that this
# Rust engine has no RNG crate dependency anywhere, so a candidate
# mechanism that needs no new RNG source is preferred and tested first.
# ---------------------------------------------------------------------------
def discrete_async_run(J, h, max_sweeps, three_state):
    state = {i: 0.0 for i in range(N)}
    seen = {}
    history = []
    for sweep in range(max_sweeps):
        changed = False
        for i in range(N):
            local = local_field(J, h, state, i)
            raw = __import__("math").tanh(BETA * local)
            if three_state:
                if raw > 0.5:
                    new_v = 1.0
                elif raw < -0.5:
                    new_v = -1.0
                else:
                    new_v = 0.0
            else:
                new_v = 1.0 if local >= 0 else -1.0
            if new_v != state[i]:
                changed = True
            state[i] = new_v
        snapshot = tuple(state[i] for i in range(N))
        history.append(snapshot)
        if not changed:
            return {"converged": True, "cycled": False, "sweeps": sweep + 1, "state": dict(state)}
        if snapshot in seen:
            return {"converged": False, "cycled": True, "sweeps": sweep + 1, "state": dict(state)}
        seen[snapshot] = sweep
    return {"converged": False, "cycled": False, "sweeps": max_sweeps, "state": dict(state)}


def frustration(J, state):
    total = 0.0
    for i in range(N):
        for j in range(i + 1, N):
            w = J[(i, j)]
            actual = -w * state[i] * state[j]
            ideal = -abs(w)
            total += actual - ideal
    return total


def main():
    print(f"N={N} complete graph, beta={BETA}, {N_DRAWS} draws x {{coarse,fine}}")
    print()
    rows = []
    for coarse in (True, False):
        cont_osc = 0
        disc2_nonconv = 0
        disc3_nonconv = 0
        disc2_frustr = []
        disc3_frustr = []
        for seed in range(N_DRAWS):
            J, h = build_draw(1000 + seed, coarse)
            osc, gap_opp, gap_same = continuous_oscillates(J, h)
            if osc:
                cont_osc += 1
            r2 = discrete_async_run(J, h, MAX_SWEEPS_DISCRETE, three_state=False)
            r3 = discrete_async_run(J, h, MAX_SWEEPS_DISCRETE, three_state=True)
            if not r2["converged"]:
                disc2_nonconv += 1
            if not r3["converged"]:
                disc3_nonconv += 1
            disc2_frustr.append(frustration(J, r2["state"]))
            disc3_frustr.append(frustration(J, r3["state"]))
        label = "coarse" if coarse else "fine"
        mean2 = sum(disc2_frustr) / len(disc2_frustr)
        mean3 = sum(disc3_frustr) / len(disc3_frustr)
        rows.append((label, cont_osc, disc2_nonconv, disc3_nonconv, mean2, mean3))
        print(f"{label:8s}  continuous_sync_osc={cont_osc}/{N_DRAWS}  "
              f"discrete_async_2state_nonconv={disc2_nonconv}/{N_DRAWS}  "
              f"discrete_async_3state_nonconv={disc3_nonconv}/{N_DRAWS}  "
              f"mean_frustr_2state={mean2:.3f}  mean_frustr_3state={mean3:.3f}")

    print()
    print("Registered predictions, checked against the numbers above:")
    print("1. continuous_sync_osc > 0 for at least one condition "
          "(replicates the already-measured pathology on THIS script's own draws).")
    print("2. discrete_async_2state_nonconv == 0 in BOTH conditions "
          "(the classical Hopfield Lyapunov guarantee, applied cleanly).")
    print("3. discrete_async_3state_nonconv: predicted small but UNVERIFIED by "
          "theory in advance -- reported honestly whichever way it comes out.")
    print("4. Bonus / secondary: does the 3-state (neutral-option) variant show "
          "LOWER frustration at convergence than the 2-state (no-neutral) variant "
          "-- the discrete-native analogue of the V=2-vs-V>=3 cliff measured in "
          "CAN_CROSSOVER_POINT_RESULTS.md Sec 3?")


if __name__ == "__main__":
    main()
