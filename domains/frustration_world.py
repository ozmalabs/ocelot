"""FrustrationWorld — a MECHANICAL cycling-scenario adapter (block 226000).

ARCHITECTURE RULE COMPLIANCE (see experiments/gamma-substrate/CLAUDE.md): this
file is a WORLD ADAPTER. It ingests the scenario mechanics and emits the graph's
decision around `run_rules()`. It contains NO agent decision:

  * whether a repeat is FUTILE is the graph rule `fr_mark_futile` (recurrence via
    an Exists match over the step history AND no-gain over the three raw
    observables); this adapter only ADDS the immutable Step with its RAW
    per-step observables (sig, d_hyp, d_state, s_drop) that the SCENARIO
    (world physics) produced.
  * the FRUSTRATION magnitude is the graph rule `fr_accumulate` (a leaky scale2
    Sum over futile steps); this adapter only advances `now_epoch` and READS
    `frustration`.
  * the STOP is the graph rule `fr_break` (frustration >= threshold ->
    break_now=1); this adapter only READS `break_now` and, when regulation is ON,
    ends the loop. There is NO `if repeated: stop` in Python.

The SCENARIO is the world: a task that, when the agent repeats one
(state,action), returns an observation. The FUTILE task returns NO gain on the
repeat; the PRODUCTIVE task returns a gain. The agent's naive loop policy (keep
doing the same action — the "just cycling" the owner saw) is the harness policy;
the frustration regulation is the CAPABILITY that breaks it.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from domains.photon_eye import GraphEye                 # noqa: E402
from substrate.seed_loader import manifest_for          # noqa: E402

# ---- FROZEN scenario constants (pre-registered, LS20_FRUSTRATION_PREREG §4) ----
FRUST_UNIT = 8
HALF_LIFE = 4
FRUSTRATION_THRESH = 20
CAP = 40                # episode cap: the un-regulated agent never self-stops


class FrustrationWorld:
    """One EmotionHub agent facing a repetitive task. All decisions (futile? how
    much frustration? stop?) run in ONE run_rules() fixpoint per step."""

    def __init__(self, *, enabled=True, frust_unit=FRUST_UNIT, half_life=HALF_LIFE,
                 frustration_thresh=FRUSTRATION_THRESH):
        self.eye = GraphEye(n_az=4, n_el=4, adapt_rate=0.15,
                            context={"retina_2d": True, "synchronous": True,
                                     "worker_capacity": 1}).build()
        self.s = self.eye.substrate
        self.inner = self.s._inner
        self.inner.load_seed_manifest(manifest_for("ls20_frustration"), self.eye._agent)

        self.hub = self.s.add_node("EmotionHub", {})
        self.fp = self.s.add_node("HeldFrustrationParams", {
            "enabled": 1.0 if enabled else 0.0,
            "frust_unit": float(frust_unit), "half_life": float(half_life),
            "frustration_thresh": float(frustration_thresh)})
        self.inner.add_edge_unchecked(self.hub, "has_frustration_params", self.fp)
        self.m = self.s.add_node("FrustrationModulator", {
            "now_epoch": 0.0, "frustration": 0.0, "break_now": 0.0,
            "hit_frustration": 0.0, "action_tendency": "", "emotion_code": 0.0})
        self.inner.add_edge_unchecked(self.hub, "has_frustration", self.m)
        self.epoch = 0

    # ---- ingest: add the immutable Step the SCENARIO produced (mechanical) ----
    def observe(self, sig, d_hyp=0, d_state=0, s_drop=0):
        """Add one Step carrying the RAW per-step observables the world yielded,
        advance now_epoch, run the rules, and read the graph's decision back.
        Returns (frustration, break_now)."""
        st = self.s.add_node("Step", {
            "sig": str(sig), "epoch": float(self.epoch), "d_hyp": float(d_hyp),
            "d_state": float(d_state), "s_drop": float(s_drop), "futile": 0.0})
        self.inner.add_edge_unchecked(self.m, "has_step", st)
        self.inner.set_attr(self.m, "now_epoch", float(self.epoch))
        self.inner.run_rules()
        self.epoch += 1
        a = self.s.node(self.m)["attrs"]
        return float(a.get("frustration") or 0.0), float(a.get("break_now") or 0.0)

    def narrate(self):
        """Emit the graph's frustration narration (208000 template lexicon keyed
        by emotion_code). Mechanical read + format; None if not broken."""
        a = self.s.node(self.m)["attrs"]
        if float(a.get("break_now") or 0.0) != 1.0:
            return None
        code = float(a.get("emotion_code") or 0.0)
        for n in self.s.nodes("FrustrationNarration"):
            na = self.s.node(n)["attrs"]
            if float(na.get("code") or 0.0) == code:
                return na.get("template")
        return None


# ==========================================================================
# THE SCENARIO (the world) — a productive prefix then a repeated (state,action).
# ==========================================================================
def _scenario(arm, rng):
    """Return a per-step generator of (sig, d_hyp, d_state, s_drop) for `arm`.

    Both arms repeat the SAME looped (state,action) sig; the ONLY difference is
    whether the repeats keep YIELDING understanding. The productive prefix (novel
    sigs, each a genuine gain) never recurs, so it is never futile in either arm.
    """
    prefix = int(rng.integers(1, 5))            # 1..4 genuine exploration steps
    steps = []
    for i in range(prefix):
        steps.append((f"P{i}", 1, 0, 0))        # novel sig, a real gain (minted)
    loop_sig = "LOOP|A1"
    for _ in range(CAP):                        # then the same (state,action)
        if arm == "futile":
            steps.append((loop_sig, 0, 0, 0))   # recurs, NO gain
        else:                                    # productive: recurs WITH a gain
            which = int(rng.integers(0, 3))     # jitter which gain signal fires
            steps.append((loop_sig,
                          1 if which == 0 else 0,
                          1 if which == 1 else 0,
                          1 if which == 2 else 0))
    return prefix, steps


def run_episode(arm, seed, *, enabled=True, measure_horizon=None):
    """Run one cycling episode.

    measure_horizon=None (episode mode): step until break_now fires (regulation
    ON) or the cap (OFF/never-breaks). Returns break_step / n_steps / narration.

    measure_horizon=H (trajectory mode): NEVER stop; record the frustration value
    at each of the first H LOOPED repeats (past the prefix) for the headline
    CI comparison. break is still recorded but does not end the run.
    """
    import numpy as np
    rng = np.random.default_rng(seed)
    prefix, steps = _scenario(arm, rng)
    w = FrustrationWorld(enabled=enabled)
    traj = []; loop_traj = []; break_step = None; narration = None
    for i, (sig, dh, ds, sd) in enumerate(steps):
        frust, brk = w.observe(sig, dh, ds, sd)
        traj.append(frust)
        if i >= prefix:
            loop_traj.append(frust)
        if brk == 1.0 and break_step is None:
            break_step = i
            narration = w.narrate()
        if measure_horizon is None:
            if enabled and brk == 1.0:
                break                            # regulation ON -> STOP the loop
        else:
            if len(loop_traj) >= measure_horizon:
                break
    return {
        "arm": arm, "seed": int(seed), "enabled": bool(enabled),
        "prefix": prefix, "break_step": break_step,
        "n_steps": len(traj), "frustration_traj": traj,
        "loop_traj": loop_traj, "narration": narration,
        "steps_to_break": (break_step if break_step is not None else CAP),
    }
