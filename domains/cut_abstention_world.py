"""GRAPH-RESIDENT ABSTENTION ON A DISCONTINUED PRIOR — the world adapter.

`VISION_CUT_ABSTENTION_PREREG.md`. A world adapter and nothing else, in exactly
the sense `verdict_comparator_world.VerdictWorld` is one: it turns pixels into
node attributes, draws the edges that say which frames a probe's interval is
made of, calls `run_rules()`, and reads attributes back. **It makes no
comparison over graph state, computes no motion, derives no threshold and takes
no branch on any of them.**

WHAT LIVES WHERE, stated plainly because this rung's whole claim is about it
--------------------------------------------------------------------------
  ADAPTER (here)   one `VidFrame` node per decoded frame carrying `vals` (flat
                   row-major grey), `rows` and `cols` (its transpose); one
                   `FrameStep` per consecutive pair with `from_frame` /
                   `to_frame` edges; one `spans` edge from a probe's `ObsGroup`
                   to each `FrameStep` of the interval THE RUNNER ALREADY
                   CONSTRUCTED when it built that probe. Mechanical
                   translation, no conditionals over graph state.

  GRAPH (seed)     the motion of each step (`ca_step_mag` / `ca_step_res`), the
                   THRESHOLD (`ca_otsu`, Argmax of Otsu's between-class
                   variance over the held steps — a value the data supplied),
                   the marking (`ca_mark_cut`) and THE DECISION TO DECLINE
                   (`ca_abstain`), which also mints the `Refusal` node that
                   makes the abstention visible afterwards.

WHY `spans` IS NOT A DECISION. A probe is constructed as "region r of frame t,
presented against frame t+delta". The interval `[t, t+delta)` is therefore part
of the probe's own construction, known to the runner before any graph state
exists — the same class of mechanical labelling as `present()`'s existing
`kind` argument, which copies the probe's provenance tag straight in. The
adapter draws the edges and stops; it never asks whether a step in that interval
is a cut, and it never reads `is_cut`.

Only probes that HAVE such an interval get `spans` edges: A1 (identity at
t+delta) and A3 (the arrangement-destroyed floor at t+delta). A2 is a randomly
chosen distant frame and G1/G2c/G2t are presented at d=0, so no interval exists
for them to span — a structural fact about the probe set, not a choice about
which probes deserve protection. The refusal floor's calibration probes (G2c)
are therefore untouched by this rung, and the verdict seed's own `vd_refuse`
runs exactly as it did.
"""
from __future__ import annotations

import numpy as np

from domains.verdict_comparator_world import VerdictWorld

#: The three armings. `""` is the shipped, inert configuration — the seed is
#: LOADED but no rule of it can fire, so the baseline carries the identical
#: graph construction and differs from the armed runs in one attribute.
ARMINGS = ("", "mag", "xcorr")


class CutAbstentionWorld(VerdictWorld):
    """`VerdictWorld` plus the frame sequence the abstention rule reasons over.

    Everything `VerdictWorld` does is unchanged and is reached by `super()`;
    this class adds ingest and read-back only."""

    def __init__(self, verdict, armed, *, manifest=None):
        from substrate.seed_loader import manifest_for

        if armed not in ARMINGS:
            raise ValueError(armed)
        super().__init__(verdict, manifest=manifest)
        self.armed = armed
        self.native.load_seed_manifest(
            manifest_for("vision_cut_abstention"), self.ag)
        # Section 9: the seed ships armed="" (inert). Arming it is a blind
        # write of a declared measurement flag -- no read, no branch. The
        # `has_cut_params` edge is the anchor the threshold rule matches on;
        # the seed loader installs the node, the adapter attaches it, exactly
        # as `VerdictWorld` attaches its own params.
        for p in self.s.nodes("CutParams"):
            self.s.set_attr(p, "armed", armed)
            self.s.add_edge(self.ag, "has_cut_params", p)
        self._steps: list = []

    # --- ingest ------------------------------------------------------------ #
    def hold_sequence(self, frames):
        """Write the frame sequence and its steps. PURE TRANSLATION: the
        pixel values go in as they came out of the decoder, and the only
        derived quantities written are `rows`/`cols`, which are the SAME
        numbers in a different shape (`XCorrPeak` sweeps lags over the outer
        index, so the transpose is how the column axis is offered to it).
        No difference, no magnitude, no threshold is computed here."""
        fnodes = []
        for t, f in enumerate(frames):
            a = np.asarray(f, float)
            fnodes.append(self.s.add_node("VidFrame", {
                "t": t,
                "vals": [float(x) for x in a.ravel()],
                "rows": [[float(x) for x in row] for row in a],
                "cols": [[float(x) for x in row] for row in a.T]}))
        for t in range(len(fnodes) - 1):
            st = self.s.add_node("FrameStep", {"t": t, "status": "ca_step_pending",
                                               "mag": 0.0, "is_cut": 0})
            self.s.add_edge(self.ag, "has_step", st)
            self.s.add_edge(st, "from_frame", fnodes[t])
            self.s.add_edge(st, "to_frame", fnodes[t + 1])
            self._steps.append(st)
        return self._steps

    def present(self, orbit, *, truth, tag, kind, span=()):
        """As `VerdictWorld.present`, plus the probe's own interval as edges.

        `span` is the half-open range of step indices the runner used to build
        this probe. It is passed in, not inferred — the adapter does not decide
        which steps a probe is made of, it is TOLD by the construction."""
        grp = super().present(orbit, truth=truth, tag=tag, kind=kind)
        self.s.set_attr(grp, "ca_status", "ca_pending")
        for t in span:
            if 0 <= t < len(self._steps):
                self.s.add_edge(grp, "spans", self._steps[t])
        return grp

    # --- read-back --------------------------------------------------------- #
    def read(self):
        """`VerdictWorld.read` plus the abstention's TRACE. Mechanical."""
        rows = super().read()
        for row, (grp, _truth, _tag, _kind, _encs) in zip(rows, self._groups):
            at = self.s.node(grp)["attrs"]
            row["abstain_reason"] = at.get("abstain_reason")
            row["ca_status"] = at.get("ca_status")
            row["n_refusal_nodes"] = len(
                [n for n in self.s.nodes("Refusal")])
            row["spans_marked"] = sum(
                1 for st in self.s.neighbours(grp, "spans")
                if int(self.s.node(st)["attrs"].get("is_cut", 0)) == 1)
        return rows

    def step_readout(self):
        """The graph's own motion + threshold + marks, read straight out. The
        runner checks `mag` against an independently computed reference; the
        threshold is reported, never supplied."""
        cp = list(self.s.nodes("CutParams"))
        thr = (float(self.s.node(cp[0])["attrs"].get("cut_threshold", 0.0))
               if cp else None)
        steps = []
        for st in self._steps:
            a = self.s.node(st)["attrs"]
            steps.append({"t": int(a.get("t", -1)),
                          "mag": float(a.get("mag", 0.0)),
                          "is_cut": int(a.get("is_cut", 0)),
                          "status": a.get("status")})
        return {"cut_threshold": thr, "steps": steps,
                "n_cut": sum(s["is_cut"] for s in steps)}

    def marker_inventory(self):
        """THE OBSERVABILITY READING, taken with the redundancy rung's OWN
        scanner logic, unchanged. `VISION_REDUNDANCY_RESULTS.md` ARM 4 found
        this inventory EMPTY in all 26 probe runs including baseline; the
        question here is whether this rung's graph makes it non-empty under
        the SAME regex, not under a friendlier one written for the occasion."""
        import collections
        import importlib.util as iu
        import os

        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        src = os.path.join(root, "scripts", "redundancy_observability.py")
        # Read the constants out of the module TEXT rather than importing it
        # (importing runs its measurement preamble). The regex and key sets
        # are the committed ones, verbatim.
        ns: dict = {}
        with open(src) as fh:
            text = fh.read()
        import re as _re
        for name in ("MARKER_TYPES", "DOC_KEYS", "MARKER_RE"):
            m = _re.search(rf"^{name} = (.+?)^\w", text, _re.S | _re.M)
            if m:
                exec(f"import re\n{name} = {m.group(1).strip()}", ns)
        marker_types = ns["MARKER_TYPES"]
        doc_keys = ns["DOC_KEYS"]
        marker_re = ns["MARKER_RE"]

        markers: collections.Counter = collections.Counter()
        for nid in self.s.nodes():
            n = self.s.node(nid)
            t = n.get("type")
            if t in marker_types or marker_re.search(t or ""):
                markers["type:" + t] += 1
            for k, v in (n.get("attrs") or {}).items():
                if k in doc_keys:
                    continue
                if marker_re.search(k):
                    markers["attr:" + k] += 1
                if isinstance(v, str) and " " not in v.strip() and marker_re.search(v):
                    markers[f"val:{k}={v.strip()}"] += 1
        return dict(markers)
