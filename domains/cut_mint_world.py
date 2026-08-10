"""CUT-MINT POLICY — the world adapter.

`VISION_CUT_MINT_POLICY_PREREG.md`. A world adapter and nothing else. It
translates frames into `VidFrame` / `FrameStep` nodes, draws one `at_step` edge
from each Observation to the steps incident on the frame the runner just
presented, calls `run_rules()`, and reads attributes back.

**Everything that DECIDES is graph data:**

- whether a step is a discontinuity — `seeds/vision_cut_abstention.json`,
  LOADED UNEDITED (`ca_step_mag` -> `ca_otsu` -> `ca_mark_cut`), whose
  threshold falls out of the sequence's own distribution and contains no
  numeric literal (protocol section 13, gated in that rung);
- whether an observation is novel enough to mint — `is_decide` / `is_mint` of
  `seeds/vision_identity_seam.json`, byte-unchanged;
- **whether to DECLINE that mint — `cm_abstain_mint` of
  `seeds/vision_cut_mint_policy.json`**, this rung's one rule.

WHY THIS CLASS EXISTS AT ALL, RATHER THAN A SUBCLASS HOOK. `run_rules`
iterates the rule vector in INSTALL ORDER and restarts at index 0 whenever a
rule progresses, so a rule that must pre-empt `is_mint` has to be installed
BEFORE it. `SeamWorld.__init__` installs the seam last, so the load sequence
has to be rebuilt here rather than appended to. That duplication is the
liability this file carries, and it is gated two ways:
`test_the_policy_rule_precedes_is_mint` asserts the installed order, and
`test_disarmed_growth_is_identical_to_the_incumbent` asserts that with the
policy DISARMED this world grows the incumbent `AccumWorld`'s codebook exactly
-- same K, same mints, same frames and regions. The second gate is what makes
the duplicated boot trustworthy, and it is the protocol section 9 check.

Nothing between ingest and read-back inspects graph state to take a branch.
"""
from __future__ import annotations

import numpy as np

from domains.video_accumulation_world import AccumWorld  # noqa: F401


def _split_at_mint(seam):
    """Split the SEAM's OWN manifest at `is_mint`, so the policy rule can be
    installed BETWEEN `is_decide` and `is_mint`.

    **This re-authors nothing.** Both halves carry the seam file's rule bodies
    verbatim; only the INSTALL POSITION of `is_mint` moves, and
    `test_the_split_seam_is_the_seam_verbatim` asserts the union of the two
    halves is the file's rule list, name-for-name and body-for-body.

    WHY IT IS NECESSARY, measured rather than assumed. `Substrate::run_rules`
    schedules **every dirty rule in one pass, in index order, with no break on
    progress** — so `is_decide` (writing `status = "is_novel"`) and `is_mint`
    (reading it) fire in the SAME pass. A rule at ANY index below `is_decide`
    sees the pre-decision state and cannot interpose; a rule above `is_mint`
    arrives after the codebook already grew. The only position that works is
    between them, and install order is the only lever on index.
    """
    rules = list(seam["rules"])
    names = [r["name"] for r in rules]
    assert names.count("is_mint") == 1, names
    i = names.index("is_mint")
    pre = {**seam, "rules": rules[:i] + rules[i + 1:]}
    mint = {**seam, "nodes": [], "edges": [], "productions": [],
            "rules": [rules[i]]}
    return pre, mint


class CutMintWorld(AccumWorld):
    """An `AccumWorld` whose minting can be declined by the graph at a cut.

    `policy=False` is the DISARMED configuration: `CutParams.armed` is the
    empty string (matching no statistic) and `CutMintParams.armed` is 0.0, so
    every cut rule and the policy rule are inert and growth is the incumbent's.
    """

    def __init__(self, *, policy: bool = False, arm: str = "ncc"):
        from substrate.boot_core import boot_core
        from substrate.seed_loader import manifest_for
        from domains import reflective_faculty as rf

        assert arm == "ncc", "the stock loop cannot refuse; out of scope here"
        self.arm = arm
        self.policy = bool(policy)
        self.s, self.ag = boot_core()
        self.native = rf._native_eval2(self.s)
        rf._ensure_shape_decode_loop(self.s, self.native, self.ag)
        self.native.load_seed_manifest(manifest_for("vision_sdloop"), self.ag)
        # ---- ORDER IS THE MECHANISM (see the module docstring) ------------
        self.native.load_seed_manifest(
            manifest_for("vision_cut_abstention"), self.ag)
        seam = manifest_for("vision_identity_seam")
        seam_pre, seam_mint = _split_at_mint(seam)
        self.native.load_seed_manifest(seam_pre, self.ag)
        self.native.load_seed_manifest(
            manifest_for("vision_cut_mint_policy"), self.ag)
        self.native.load_seed_manifest(seam_mint, self.ag)
        # ---- arming: blind writes of DECLARED measurement flags ------------
        # No read of graph state, no branch on one. `policy` is the runner's
        # own configuration, indexed arithmetically so no comparison appears.
        for p in self.s.nodes("IdentitySeamParams"):
            self.s.set_attr(p, "seam", 1.0)
        # The `has_cut_params` edge is the anchor `ca_otsu` matches on: the
        # seed loader installs the node, the adapter attaches it -- exactly as
        # `cut_abstention_world` does, and for the same reason.
        for p in self.s.nodes("CutParams"):
            self.s.set_attr(p, "armed", ("", "mag")[int(self.policy)])
            self.s.add_edge(self.ag, "has_cut_params", p)
        for p in self.s.nodes("CutMintParams"):
            self.s.set_attr(p, "armed", float(self.policy))
            self.s.add_edge(self.ag, "has_cut_mint_params", p)
        self._obs = []
        self._frozen = None
        self._steps = {}

    # ------------------------------------------------------------- ingest
    def hold_sequence(self, frames):
        """Write the frame sequence and its steps. PURE TRANSLATION.

        Verbatim from `cut_abstention_world.hold_sequence`: the pixel values go
        in as the decoder produced them, and the only derived quantities are
        `rows` / `cols`, the same numbers transposed. **No difference, no
        magnitude and no threshold is computed here** -- `ca_step_mag` computes
        the motion, `ca_otsu` derives the threshold and `ca_mark_cut` marks the
        steps, all inside the graph.
        """
        fnodes = []
        for t, f in enumerate(frames):
            a = np.asarray(f, float)
            fnodes.append(self.s.add_node("VidFrame", {
                "t": t,
                "vals": [float(x) for x in a.ravel()],
                "rows": [[float(x) for x in row] for row in a],
                "cols": [[float(x) for x in row] for row in a.T]}))
        for t in range(len(fnodes) - 1):
            st = self.s.add_node("FrameStep", {"t": t,
                                               "status": "ca_step_pending",
                                               "mag": 0.0, "is_cut": 0})
            self.s.add_edge(self.ag, "has_step", st)
            self.s.add_edge(st, "from_frame", fnodes[t])
            self.s.add_edge(st, "to_frame", fnodes[t + 1])
            self._steps[t] = st
        self.run()
        return len(self._steps)

    def present_at(self, qtile, gtile, *, tag, frame):
        """Present one region AND declare which frame the runner took it from.

        The incident steps of frame `t` are `t-1` (the step INTO it) and `t`
        (the step OUT of it). That interval is not inferred from graph state:
        the runner knows which frame it just handed over, exactly as
        `cut_abstention_world.present` is TOLD its probe's span. The `is not
        None` guards are PRESENCE guards at the sequence ends -- frame 0 has no
        step into it -- and are not decisions over a verdict.
        """
        node = self.present(qtile, gtile, tag=tag)
        for s in (frame - 1, frame):
            st = self._steps.get(s)
            if st is not None:
                self.s.add_edge(node, "at_step", st)
        return node

    # ----------------------------------------------------------- read-back
    def marked_steps(self):
        """The steps the GRAPH marked. A mechanical query of `is_cut`."""
        out = []
        for t, st in sorted(self._steps.items()):
            if self.s.node(st)["attrs"].get("is_cut") == 1:
                out.append(int(t))
        return out

    def step_mags(self):
        """Every step's motion, as the graph computed it."""
        return {int(t): self.s.node(st)["attrs"].get("mag")
                for t, st in sorted(self._steps.items())}

    def cut_threshold(self):
        """The threshold the graph derived. Read, never written by this file."""
        for p in self.s.nodes("CutParams"):
            return self.s.node(p)["attrs"].get("cut_threshold")
        return None

    def abstentions(self):
        """The `MintAbstention` trace, so a reader can see WHY, not just THAT."""
        out = []
        for nid in self.s.nodes("MintAbstention"):
            at = self.s.node(nid)["attrs"]
            out.append({"obs_key": at.get("obs_key"), "reason": at.get("reason")})
        return out
