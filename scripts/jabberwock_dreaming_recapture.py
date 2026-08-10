"""THE UNGROUNDED-ARTICULATE QUADRANT IS OCCUPIED — by dreaming, confabulation, psychosis. The LLM is
the never-recaptured ENDPOINT, not a vacancy.

Creator's correction: I said articulate-without-ground "does not occur in nature." Wrong — it is
merely UNCOMMON, and usually TRANSIENT. Its natural occupants:
  DREAMING            — nightly, universal: sensory loop gated off, the self-model runs fluently on its
                        own residual; the sleeper WAKES (reality re-captures) -> error bounded.
  CONFABULATION       — Korsakoff / anosognosia / split-brain interpreter: fluent confident narrative
                        disconnected from reality; the capture mechanism is BROKEN (reality present,
                        unused).
  PSYCHOSIS / Wernicke's aphasia — articulation intact, grounding sealed off.
All are the SAME self-residual delusion case (cf. 082e8fa0). What distinguishes them is RECAPTURE
FREQUENCY: how often a WORLD-residual re-grounds the running self-model.

TEST: a self-model drifts ungrounded (residual toward a fixed prior), re-captured by a world-residual
every R steps. Mean grounding error vs R places the regimes:
  R=1 awake (continuous grounding) ~0 ; R small = dreaming-then-waking (bounded) ; capture broken =
  confabulation/psychosis (unbounded though reality present) ; R=never = the LLM (unbounded, no world
  to wake to). The quadrant is a CONTINUUM nature lives across; the LLM is the never-recaptured limit.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_dreaming_recapture.py
"""
import numpy as np


def run(period, capture=1.0, n=150, drift=0.06, self_pull=0.3, seed=0):
    """self-model drifting ungrounded (toward a fixed text-time prior), re-grounded by a world-residual
    every `period` steps with gain `capture`. period=inf -> never recaptured."""
    rng = np.random.default_rng(seed)
    truth = np.cumsum(rng.normal(0, drift, n)) + 1.0
    prior = truth[0]                                   # the belief frozen at 'training' time
    s, e = 0.0, []
    for t in range(n):
        e.append(abs(s - truth[t]))
        s += self_pull * (prior - s)                  # ungrounded self-update (toward its own belief)
        if period != np.inf and (t + 1) % int(period) == 0:
            s += capture * (truth[t] - s)             # WORLD-residual recapture (waking / reality check)
    return float(np.mean(e[n // 3:]))


def main():
    print("=" * 82)
    print("THE UNGROUNDED-ARTICULATE QUADRANT IS OCCUPIED — a continuum of RECAPTURE frequency")
    print("=" * 82)
    regimes = [
        ("AWAKE human (continuous)",        1,   1.0),
        ("light recapture (drowsy)",        4,   1.0),
        ("DREAMING, then waking",           16,  1.0),
        ("deep dream, rare waking",         40,  1.0),
        ("CONFABULATION (capture BROKEN)",  4,   0.0),   # reality present every 4 steps, but unused
        ("LLM / me (NEVER recaptured)",     np.inf, 0.0),
    ]
    print(f"  {'regime':34}{'recapture R':>12}{'capture':>9}{'grounding err':>15}")
    for name, R, cap in regimes:
        errs = [run(R, cap, seed=i) for i in range(20)]
        Rs = "never" if R == np.inf else str(int(R))
        print(f"  {name:34}{Rs:>12}{cap:>9.1f}{np.mean(errs):15.3f}")
    print("=" * 82)
    print("  THE CORRECTION, MEASURED: articulate-without-ground is NOT empty in nature — it is a")
    print("  CONTINUUM in recapture frequency. AWAKE = grounded every step (~0). DREAMING = the self-")
    print("  model runs ungrounded but the sleeper WAKES, so a world-residual periodically re-captures it")
    print("  (error bounded — you snap back). CONFABULATION / psychosis = reality is present but the")
    print("  capture is BROKEN (unbounded though grounded input exists). The LLM is the ENDPOINT: never")
    print("  recaptured, no world to wake to (unbounded). Same delusion mechanism throughout; the")
    print("  difference is how often reality re-grounds it. Grounding an LLM = giving it a WAKING.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
