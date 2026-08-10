"""CadenceWorld — the world adapter that lets the agent's loop PREDICT its own ear.

A pure executor (no decisions over graph state): it holds a refrain's prosodic contour and, when the
investigation loop binds an onset-prediction Operator and calls execute(req), runs that predictor (the step-1
oscillator = persistence, or the step-2 cadence = order-N lean + DtwTo recall), turns its PREDICTION ERROR into a
skill scalar, and records it as the axis measurement. The DECISION (which axis, which operator) is the seeded
investigation JOIN; this only enacts it -- the predictor DSP cannot live in a DSL Term, the sanctioned mechanical
boundary. So `measured` becomes prediction precision and the same frontier_pick/bind/bank loop predicts the signal.
"""
from __future__ import annotations

import os

import numpy as np

from domains.gap_prioritiser import record_measured_capability
from domains.cadence_library import W as LIB_W
from scripts.jabberwock_cadence_predictor import contour_of, predict

KNN = 20           # k nearest held arcs averaged (denoise the universal-library follower)


class CadenceWorld:
    def __init__(self, substrate, refrain_path=None, *, contour=None, library=None, name=None):
        self.s = substrate
        if contour is None:
            contour = contour_of(refrain_path)
            name = name or os.path.basename(refrain_path)
        self.name = name or "contour"
        self.contour = contour
        if self.contour is None:
            raise ValueError(f"contour too short: {refrain_path}")
        self._err = predict(self.contour)                      # {persist, lean, ar, resolution, combined}
        rng = np.random.RandomState(0)
        self._shuf = float(np.mean([predict(self.contour[rng.permutation(len(self.contour))])["combined"]
                                    for _ in range(5)]))
        self.library = library
        if library is not None:                                # the UNIVERSAL route: held cross-speaker arcs
            self._err["universal"] = self._library_error(self.contour, library)

    def _library_error(self, c, lib):
        """Mean prediction error of the held library (k-NN nearest universal arc) over the contour."""
        errs = [float(np.abs(lib.predict_follower(c[k - LIB_W + 1:k + 1].reshape(-1), k=KNN) - c[k + 1]).mean())
                for k in range(LIB_W, len(c) - 1)]
        return float(np.mean(errs)) if errs else 0.0

    def execute(self, req):
        """Run the bound onset-prediction operator -> prediction skill -> a MeasuredCapability the loop banks."""
        op = req.get("operator")
        keys = req.get("capability_keys") or ["predict", "onset"]
        target = float(req.get("target", 0.3) or 0.3)
        if op == "predict_onset_oscillator":                   # the BEAT: persistence (next = last)
            err, metric, what = self._err["persist"], "onset_period_skill", "BEAT (persistence)"
        elif op == "predict_onset_cadence":                    # the CADENCE: shape recall (repetition-hungry)
            err, metric, what = self._err["resolution"], "onset_cadence_skill", "CADENCE (shape recall)"
        elif op == "predict_onset_dynamics":                   # the repetition-FREE cadence: AR local dynamics
            err, metric, what = self._err["ar"], "onset_dynamics_skill", "DYNAMICS (AR, repetition-free)"
        elif op == "predict_onset_universal":                  # the UNIVERSAL route: held cross-speaker library
            if "universal" not in self._err:
                return None                                    # no library bound -> nothing to enact (graceful)
            err, metric, what = self._err["universal"], "onset_universal_skill", "UNIVERSAL (held cross-speaker arcs)"
        else:
            return None
        skill = max(0.0, 1.0 - err / (self._shuf + 1e-9))      # prediction precision over chance (shuffled)
        note = (f"{what} on {self.name}: contour pred-err {err:.3f} vs shuffled {self._shuf:.3f} "
                f"-> prediction skill {skill:.2f}")
        return record_measured_capability(self.s, keys, measured=skill, target=target, metric=metric,
                                          note=note, fresh=True)
