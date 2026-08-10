"""VIDEO ACCUMULATION — the world adapter.

`VISION_VIDEO_ACCUMULATION_PREREG.md`. A world adapter and nothing else. It
reuses `identity_seam_world.SeamWorld` (arm B, the NCC seam) verbatim for
growth, and adds exactly two mechanical facilities the measurement needs:

1. `install_codebook(entries)` -- write `ShapeSignature` nodes with
   `seam_grown = 1.0` directly. This is INPUT CONSTRUCTION, the same class of
   work as the seam rung's declared "codebook insertion order": it builds the
   held codebook an evaluation is run against. It takes no branch on graph
   state.

2. `freeze()` / `refreeze()` -- hold the codebook FIXED across an evaluation
   pass, so that observation #400 is scored against the same codebook as
   observation #1. `refreeze()` demotes every `seam_grown` signature whose name
   is not in the recorded frozen set (an unconditional write over a set
   difference of node ids, not a decision), and re-arms the measured noise
   floor by resetting the G2c probes' `calib_epoch`. `assert_frozen()` gates it:
   K and the floor must be identical at the start and the end of every pass.

Everything that DECIDES -- which held identity an observation is, whether it is
novel enough to mint -- remains `seeds/vision_identity_seam.json`. Nothing here
compares graph state.
"""
from __future__ import annotations

import numpy as np

from domains.identity_seam_world import (  # noqa: F401  (re-exported)
    GRID, K_LEVELS, REGION, SeamWorld, encode, grey_regions_of, mean_abs_diff,
    otsu, quantize, regions_of, shuffle_arrangement,
)


class AccumWorld(SeamWorld):
    """A `SeamWorld` that can be handed a codebook and frozen against growth."""

    def __init__(self, arm: str = "ncc"):
        super().__init__(arm)
        self._frozen = None

    # --------------------------------------------------------- construction
    def install_codebook(self, entries):
        """`entries` = [(name, qtile, gtile)]. Mechanical node writes."""
        for name, qt, gt in entries:
            e = encode(qt, gt)
            self.s.add_node("ShapeSignature", {
                "name": name, "faculty": name,
                "signature": e["signature"], "dim_types": e["dim_types"],
                "nvals": e["nvals"], "kind": "faculty", "seam_grown": 1.0,
            })
        # A codebook change is an epoch bump; the floor re-arms off it.
        self.s.set_attr(self.ag, "codebook_epoch",
                        float(self.s.node(self.ag)["attrs"]
                              .get("codebook_epoch") or 0.0) + 1.0)
        self.run()
        return self.codebook_size()

    # ------------------------------------------------------------- freezing
    def _held_names(self):
        out = set()
        for sid in self.s.nodes("ShapeSignature"):
            at = self.s.node(sid)["attrs"]
            if at.get("seam_grown") == 1.0:
                out.add(sid)
        return out

    def freeze(self):
        """Record the codebook the evaluation pass runs against."""
        self._frozen = self._held_names()
        self._frozen_floor = self._floor_now()
        return len(self._frozen)

    def _floor_now(self):
        vals = []
        for nid in self.s.nodes("Observation"):
            at = self.s.node(nid)["attrs"]
            if at.get("probe_kind") == "G2c" and at.get("is_max") is not None:
                vals.append(float(at["is_max"]))
        return max(vals) if vals else None

    def refreeze(self):
        """Demote anything minted since `freeze()` and re-arm the floor."""
        assert self._frozen is not None, "freeze() first"
        grew = False
        for sid in self.s.nodes("ShapeSignature"):
            at = self.s.node(sid)["attrs"]
            if at.get("seam_grown") == 1.0 and sid not in self._frozen:
                self.s.set_attr(sid, "seam_grown", 0.0)
                grew = True
        if grew:
            for nid in self.s.nodes("Observation"):
                if self.s.node(nid)["attrs"].get("probe_kind") == "G2c":
                    self.s.set_attr(nid, "calib_epoch", -1.0)
            self.run()
        return grew

    def assert_frozen(self):
        """The freeze gate. K and the measured floor must not have moved."""
        k = self.codebook_size()
        assert k == len(self._frozen), f"codebook moved: {len(self._frozen)}->{k}"
        f = self._floor_now()
        assert (f is None) == (self._frozen_floor is None)
        if f is not None:
            assert abs(f - self._frozen_floor) < 1e-12, \
                f"floor moved: {self._frozen_floor} -> {f}"
        return k, f

    # ------------------------------------------------------------ readback
    def read_full(self):
        node, tag = self._obs[-1]
        at = self.s.node(node)["attrs"]
        return {"tag": tag, "status": at.get("status"),
                "identity": at.get("identified_as"),
                "is_max": at.get("is_max"), "is_floor": at.get("is_floor")}


def block_split(n_frames, block=10, holdout_every=3, holdout_offset=1, guard=1):
    """The pre-registered TRAIN / HELD-OUT split.

    Contiguous blocks, so a held-out frame is never the temporal neighbour of a
    training frame it could be recognised through; `guard` training frames are
    dropped either side of every held-out block.
    """
    n_blocks = n_frames // block
    hold_blocks = [b for b in range(n_blocks)
                   if b % holdout_every == holdout_offset]
    held = []
    for b in hold_blocks:
        held.extend(range(b * block, (b + 1) * block))
    heldset = set(held)
    banned = set()
    for f in held:
        for g in range(1, guard + 1):
            banned.add(f - g)
            banned.add(f + g)
    train = [f for f in range(n_blocks * block)
             if f not in heldset and f not in banned]
    return train, held


def cut_flags(frames):
    """Otsu on the corpus's own per-step motion. No free parameter.
    Verbatim from `identity_seam_measure.cut_flags`."""
    steps = [float(np.mean(np.abs(np.asarray(frames[t + 1], float)
                                  - np.asarray(frames[t], float))))
             for t in range(len(frames) - 1)]
    thr = otsu(steps)
    return steps, thr, [s > thr for s in steps]


def dist_to_cut(frame, cuts):
    """Frames from `frame` to the nearest marked step. Reported as a
    continuous quantity so nothing depends on a chosen window."""
    idx = [t for t, c in enumerate(cuts) if c]
    if not idx:
        return None
    return min(abs(frame - t) for t in idx)
