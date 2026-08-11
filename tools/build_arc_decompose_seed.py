#!/usr/bin/env python3
"""EMIT `seeds/arc_decompose.json` — MG4: ORDER-N DECOMPOSITION.

`tools/*` are one-off AUTHORING scripts that EMIT seed manifests (CLAUDE.md:
"deletable; not agent runtime").  Nothing here runs at agent time and nothing
here decides anything about a live graph: it assembles JSON.

Prereg: `PROGRAM_SYNTHESIS_ARC6_PREREG.md` amendment **A16** (`MG4a`-`MG4d`),
registered before this build.  Design: `PROGRAM_SYNTHESIS_ARC6_MAGNITUDE.md`
§6 ("MG4 — THE DESIGN. NOT BUILT.").

WHAT THIS SEED IS, AND WHY IT IS A SEPARATE FILE FROM `arc_magnitude`.
`mg_rung` (`seeds/arc_magnitude.json`) already computes `decompose_required`
and names the measured ladder (`decompose_ladder_key`) a split would use —
that is MG3, already shipped, already gated 43/43.  This seed adds the
missing consumer: `mg_decompose` mints one child `ArcGoal` per un-materialised,
IN-HORIZON tier of the ladder, and `mg_decompose_retire` moves the parent to a
terminal state once its currently-affordable tiers are fully materialised.
Kept out of `arc_magnitude.json` itself (MG5's own precedent: "this rung adds
a second seed rather than editing the first") so MG1-3/5's existing 43 gates
load a graph that has not changed under them, and out of `arc_executor`'s
dependency tree entirely — decomposition is graph arithmetic over
`ArcGoal`/`ArcTier`, needs no `ExecClass`/dispatch of its own, and stays
addable/removable independent of the executor line.

THREE DECISIONS BEYOND MAGNITUDE.md §6.1's LITERAL PSEUDOCODE (registered in
A16; decision 2 was CORRECTED DURING BUILD — see the note below, and A16's
own correction — rather than shipped as originally registered):

  (1) THE PARENT'S POOL-EXIT IS THE EXISTING `headroom_n > 0` CLAUSE, NOT A
      NEW STATUS DISJUNCT ON `POOL()`.  §6.2(2) declined the interim
      "decomposed status in the pool filter" workaround because it required
      editing `seeds/arc_goals.json`.  It still would, if the exclusion were
      written as a literal third status check there.  This seed does not
      touch `arc_goals.json`: `mg_decompose_retire` stamps the parent's
      `headroom_n` to `0.0`, which `POOL()`'s OWN, PRE-EXISTING
      `Gt(headroom_n, 0.0)` clause already excludes — the SAME narrow
      pool-exit technique A13 §7.1 / A15 §4.2 validated for constructing
      scenes, now used as the production mechanism.  `status: "decomposed"`
      is still written, exactly parallel to `ax_retired_epoch`'s `"retired"`,
      but as a DESCRIPTIVE terminal token — legible to a human or a later
      rung — never the exclusion mechanism itself.  Because `POOL()` is
      SHARED between `ag_select` (order-1) and `mg_select` (order-N,
      machine-lifted from the same `Filter`), one stamp excludes the parent
      from BOTH collapses at once.
  (2) `mg_decompose` MINTS EVERY UN-MATERIALISED TIER, UNCONDITIONALLY —
      NOT ONLY IN-HORIZON ONES.  A FIRST DRAFT of this rule gated each
      child's mint on `in_horizon == 1.0` (mirroring `_order_n_sum`'s own
      truncation), reasoning that this would make the registered arithmetic
      identity hold "by construction".  MEASURED TO BE WRONG BEFORE
      SHIPPING, and corrected: `decompose_required == 1.0` requires
      `magnitude_ratio_first_tier > 1`, i.e. `cost_first > horizon_net`
      where `cost_first` IS the cheapest tier's own `cum_cost_units` (the
      `MINOVER` over the SAME field `in_horizon` compares against). Because
      tier cost is cumulative and therefore monotonic, `cost_first >
      horizon_net` implies `cum_cost_units(t) > horizon_net` — i.e.
      `NOT in_horizon(t)` — for EVERY tier `t` on the ladder, not just the
      cheapest.  So `decompose_required == 1.0` and `EXISTS t, in_horizon(t)`
      are MUTUALLY EXCLUSIVE for any ladder, always — an in-horizon gate on
      the mint would make `mg_decompose` permanently unreachable under its
      own natural trigger: RESIDENT AND STRUCTURALLY DEAD, exactly the
      failure mode `PROGRAM_SYNTHESIS_ARC6_MAGNITUDE.md` §1 (JOB 0) found
      for `qd_decompose` and named as WORSE than merely unreached. It would
      also have contradicted §6.3's own stated purpose: children are meant
      to be INDEPENDENTLY re-priced against the SAME horizon so a cheap tier
      (e.g. B0 at 8 units) can become individually actionable even when the
      full ladder (28 units) was not — which requires minting the whole
      ladder, not only the pre-filtered affordable slice. So: NO in-horizon
      gate here. Each child gets `magnitude_rung`'d on its own by the
      EXISTING, UNCHANGED `mg_rung` (it matches every `ArcGoal`), via its own
      `cost_bits`.
  (3) THE PARENT RETIRES ONLY ONCE **EVERY** TIER HAS BEEN MATERIALISED AS A
      CHILD (not only the in-horizon ones — decision 2's correction applies
      here too) **AND AT LEAST ONE CHILD EXISTS** — never on the
      `decompose_required` flag alone. The "at least one child" guard
      remains a defensive no-op today (a real ladder always has tiers, so
      the two conditions coincide), kept because it costs nothing and
      documents the invariant explicitly.

**THE HONEST CONSEQUENCE OF DECISION 2's CORRECTION, NAMED RATHER THAN
BURIED.** The registered arithmetic identity
(`Sum(children.headroom_n * children.tier_survival) ==
parent.orderN_headroom_n`) compares two quantities that are EQUAL only when
horizon truncation does not zero the parent's own reading — i.e. on a scene
where `decompose_required` is TRUE (so decomposition fires) but the horizon
is not the thing making it true (a direct, narrow attribute poke of
`decompose_required`, the SAME technique A13/A14/A15 validated, with NO
horizon held so every tier reads `in_horizon`). Under the NATURAL trigger
(a genuinely tight horizon, e.g. the existing pinned horizon=5 scene), the
parent's own `orderN_headroom_n` is horizon-truncated to `0` (nothing fits,
by the same mathematical fact above) WHILE the children — correctly, per
decision 2 — sum to the ladder's full, untruncated projected value (13.637
on the shipped ladder). `results/…` is not the place this is hidden: the
gate (`test_mg4a_…`) checks BOTH scenes and reports both numbers, and the
constructed (no-horizon, poked) scene is the one the identity is REGISTERED
against, matching MG4a's own bar text ("on a constructed decomposition
scene"). See `PROGRAM_SYNTHESIS_ARC6_MG4_DECOMPOSE.md` for the full
measurement and the recommended re-statement of the bar for whoever revisits
it.

WHAT IS NOT BUILT, NAMED RATHER THAN SILENTLY DROPPED (A16):
  - fold-up is not twinned — nothing resolves a decomposition child's
    status, so a twinned `qd_compound_resolve`/`_wall` rule would be dead
    code with nothing to trigger it (the same shape JOB 0 found for
    `qd_decompose` itself).  The child shape (`parent_agid`, `tier_order`)
    is legible to a future fold-up rule; this rung does not write one.
  - no `ExecClass` for a decomposition-tier goal — there is no runner that
    could execute "supply a structural primitive"; that remains genuine
    outside work, same as it was for the undecomposed parent.

Run:  python tools/build_arc_decompose_seed.py         (writes the seed)
      python tools/build_arc_decompose_seed.py --check (fails if out of date)
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from build_arc_magnitude_seed import (  # noqa: E402
    A, AND, EQ, EXISTS, FILT, L, MEASURE_EPOCH, NEIGH, NOT, NUM, ONE_OF,
    SCAT, STR, T, TIMES, V, _is_decomposition_child, _tiers_of,
)

OUT = os.path.join(ROOT, "seeds", "arc_decompose.json")


# --------------------------------------------------------------------------- #
#  Tier/child bookkeeping — every un-materialised tier (decision 2, corrected:
#  NOT filtered to in-horizon ones — see the module docstring).
# --------------------------------------------------------------------------- #
def _children_of(gvar="g"):
    return NEIGH(V(gvar), "has_subgoal")


def _child_at_tier(gvar, tvar):
    """A child already minted for this exact (goal, tier order) pair."""
    return EXISTS(_children_of(gvar), "chx",
                  EQ(A(V("chx"), "tier_order"), A(V(tvar), "order")))


def _undecomposed_tiers(gvar="g", tvar="tud"):
    """Every tier of this goal's own ladder that has no child yet — ALL
    tiers, unconditionally (decision 2, corrected). Named `_undecomposed_tiers`
    rather than `..._in_horizon_tiers`: the horizon plays no role in WHICH
    tiers get minted, only (via the existing, unchanged mg_rung) in how each
    resulting child is individually priced afterwards."""
    return FILT(_tiers_of(gvar, tvar), tvar, NOT(_child_at_tier(gvar, tvar)))


# --------------------------------------------------------------------------- #
#  RULES
# --------------------------------------------------------------------------- #
def _r_decompose():
    return {
        "name": "mg_decompose",
        "comment": (
            "MG4/A16. THE SPLIT. MAGNITUDE.md 6.1's rule, built: mints ONE "
            "child ArcGoal per un-materialised tier of the parent's own "
            "measured ladder -- EVERY tier, not only in-horizon ones "
            "(decision 2, CORRECTED during build -- see this file's module "
            "docstring: gating on in_horizon would make this rule "
            "permanently unreachable under its own decompose_required "
            "trigger, and would contradict 6.3's own point that children "
            "get individually re-priced). One child per fixpoint pass (the "
            "pcon_mint / ag_mint_blocker Argmin-ONE_OF serializer: effects "
            "apply against PRE-EFFECT reads, so minting every un-"
            "materialised tier of one goal in a single pass would let two "
            "tiers both mint before either's dedup saw the other). "
            "THE CHILD DOES NOT CARRY proposed_seam (6.2(1)): it carries "
            "parent_ladder_key instead, so _has_ladder(child) is FALSE and "
            "this rule cannot re-fire on its own output -- no rule ordering "
            "on this engine, so the guard chain IS the confinement. "
            "headroom_n is the tier's RAW increment_n and tier_survival is "
            "carried alongside it (not multiplied in here) so the registered "
            "arithmetic identity (MG4a) can read both factors independently "
            "off the child, exactly as MAGNITUDE.md 6.1 lists them. "
            "cost_bits mirrors magnitude_cost_units (a decision beyond "
            "6.1's literal attr list): without it, mg_rung's OWN cost "
            "fallback for a ladder-less goal (_cost_total's ITE) reads 0 for "
            "a childless-ladder goal and would misprice every child as "
            "trivially 'absorb' regardless of its own tier's real cost -- "
            "WITH it, mg_rung (unchanged, matches every ArcGoal) prices each "
            "child on its OWN cost against the SAME horizon, which is "
            "exactly the independent-re-pricing 6.3 describes. "
            "sig_seam/sig_lever/sig_target are inherited from the parent "
            "verbatim, per 6.1."),
        "batch": True,
        "match": [["agenda", "has_arc_goal", "g"], ["lad", "has_tier", "t"]],
        "where": AND(
            EQ(A(V("g"), "decompose_required"), L(1.0)),
            EQ(A(V("t"), "ladder_key"), A(V("g"), "proposed_seam")),
            NOT(_child_at_tier("g", "t")),
            # one mint per pass, PER GOAL — the pcon_mint serializer.
            EQ(V("t"), ONE_OF(_undecomposed_tiers("g", "tsel"), "tsel")),
        ),
        "effects": [
            ["add_node", "child", "ArcGoal", {
                "agid": T(SCAT(A(V("g"), "agid"), L(".tier"),
                               STR(A(V("t"), "order")))),
                "parent_agid": T(A(V("g"), "agid")),
                "parent_ladder_key": T(A(V("g"), "proposed_seam")),
                "tier_order": T(A(V("t"), "order")),
                "headroom_n": T(A(V("t"), "increment_n")),
                "tier_survival": T(A(V("t"), "survival")),
                "magnitude_cost_units": T(A(V("t"), "cum_cost_units")),
                "cost_bits": T(A(V("t"), "cum_cost_units")),
                "sig_seam": T(A(V("g"), "sig_seam")),
                "sig_lever": T(A(V("g"), "sig_lever")),
                "sig_target": T(A(V("g"), "sig_target")),
                "reach_class_factor": 1.0,
                "novelty_bits": 0.0,
                "status": "minted",
                "kind": "decomposition_tier",
                "source_kind": "decomposition_tier",
                "_the_decision_lives_here": (
                    "which tiers become goals is mg_rung's decompose_required "
                    "(seeds/arc_magnitude.json) alone; the adapter never "
                    "chooses a tier."),
            }],
            ["add_edge", "g", "has_subgoal", "child"],
            ["add_edge", "agenda", "has_arc_goal", "child"],
        ],
    }


def _r_decompose_retire():
    return {
        "name": "mg_decompose_retire",
        "comment": (
            "MG4/A16, decision 3. THE PARENT LEAVES THE POOL -- decision 1 "
            "(module docstring): stamps headroom_n=0.0, which POOL()'s OWN "
            "pre-existing Gt(headroom_n, 0.0) clause already excludes, "
            "removing the parent from BOTH ag_select's and mg_select's pool "
            "with ZERO edits to seeds/arc_goals.json. status='decomposed' is "
            "DESCRIPTIVE, exactly parallel to ax_retired_epoch's 'retired', "
            "never itself the exclusion mechanism. "
            "FIRES ONLY ONCE DECOMPOSITION IS ACTUALLY COMPLETE: "
            "decompose_required==1.0 AND at least one child already exists "
            "AND no undecomposed tier remains (decision 2, corrected: ALL "
            "tiers, not only in-horizon ones)."),
        "batch": True,
        "match": [["agenda", "has_arc_goal", "g"]],
        "where": AND(
            EQ(A(V("g"), "decompose_required"), L(1.0)),
            NOT(EQ(A(V("g"), "status"), L("decomposed"))),
            EXISTS(_children_of("g"), "chr", L(True)),
            NOT(EXISTS(_undecomposed_tiers("g", "tud2"), "tud2", L(True))),
        ),
        "effects": [
            ["set_attr", "g", "status", "decomposed"],
            ["set_attr", "g", "decomposed_epoch", T(MEASURE_EPOCH())],
            ["set_attr", "g", "decomposed_because",
             "all_tiers_of_the_measured_ladder_materialized_as_children"],
            ["set_attr", "g", "headroom_n", 0.0],
            ["set_attr", "g", "orderN_headroom_n", 0.0],
        ],
    }


def _r_child_order_n():
    return {
        "name": "mg_child_order_n",
        "comment": (
            "MG4/A16. A decomposition child's OWN order-N headroom is its "
            "tier's discounted value -- headroom_n * tier_survival, the SAME "
            "product the registered arithmetic identity (MG4a) sums. This "
            "is what mg_goal_order_n_default's new parent_agid exclusion "
            "(seeds/arc_magnitude.json v1.1.0) makes room for: without both "
            "halves, the generic order-N fallback would silently overwrite "
            "this back to the undiscounted headroom_n every fixpoint pass -- "
            "precisely the order-1-credit inflation trap MAGNITUDE.md 6.2(4) "
            "names as 'the single most likely way for this to go wrong'."),
        "batch": True,
        "match": [["agenda", "has_arc_goal", "g"]],
        "where": _is_decomposition_child(),
        "effects": [
            ["set_attr", "g", "orderN_headroom_n",
             T(TIMES(NUM(A(V("g"), "headroom_n"), 0.0),
                     NUM(A(V("g"), "tier_survival"), 0.0)))],
            ["set_attr", "g", "order_n_basis",
             "decomposition_child_tier_survival"],
            ["set_attr", "g", "order_n_orders_counted", 1.0],
        ],
    }


def _rules():
    return [_r_decompose(), _r_decompose_retire(), _r_child_order_n()]


def _productions():
    return [
        {"provenance": "seed:arc_decompose:has_subgoal-0",
         "src": {"type": "ArcGoal", "var": "s"}, "edge_type": "has_subgoal",
         "tgt": {"type": "ArcGoal", "var": "t"}},
    ]


def build():
    return {
        "_GENERATED_BY": "tools/build_arc_decompose_seed.py",
        "_REGENERATION_IS_GATED_BYTE_IDENTICAL": (
            "tests/test_arc_decompose_migrated.py::"
            "test_mg4d_the_seed_regenerates_byte_identically re-runs this "
            "builder and diffs. The Term idioms (_tiers_of, _has_ladder, "
            "_is_decomposition_child, MEASURE_EPOCH, NUM, ...) are IMPORTED "
            "from tools/build_arc_magnitude_seed.py, so if that builder's "
            "idioms change this seed goes out of date LOUDLY."),
        "self_load_only": True,
        "_SELF_LOAD_ONLY_RATIONALE": (
            "substrate/boot_all.py::_read_seeds GLOBS seeds/*.json and "
            "installs every match at boot, so a file here is live in EVERY "
            "agent in the tree the moment it lands. seeds/arc_goals.json and "
            "seeds/arc_magnitude.json both ship self_load_only for that "
            "reason and this seed DEPENDS ON THE LATTER, so shipping this "
            "one globbed would activate a chain whose base is deliberately "
            "gated. Activation is one key and the paired sweep A5 requires."),
        "id": "arc_decompose",
        "version": "1.0.0",
        "depends_on": ["goal_residuals", "arc_goals", "arc_magnitude"],
        "_NO_DEPENDENCY_ON_arc_executor": (
            "A16's own design investigation: decomposition needs no "
            "ExecClass, no dispatch, no re-arm -- it is graph arithmetic "
            "over ArcGoal/ArcTier. Depending on arc_magnitude (and, through "
            "it, arc_goals) is sufficient. This keeps MG4 addable/removable "
            "independent of the executor line and out of the re-arm/"
            "dispatch scope A13-A16 all exclude."),
        "description": (
            "MG4 -- ORDER-N DECOMPOSITION (A16). mg_rung "
            "(seeds/arc_magnitude.json) computes decompose_required and "
            "names the measured ladder a split would use; nothing consumed "
            "it. This seed is the consumer: mg_decompose mints one child "
            "ArcGoal per un-materialised tier of the ladder -- EVERY tier, "
            "not only the ones affordable under the CURRENT horizon (a "
            "first draft gated on in_horizon and was corrected before "
            "shipping: decompose_required==1.0 and in_horizon(any tier) are "
            "mutually exclusive by construction on this ladder's monotonic "
            "cost, which would have made the gated rule permanently dead "
            "under its own trigger -- see this builder's docstring) -- each "
            "child carrying its tier's raw increment_n as headroom_n and the "
            "tier's own survival factor alongside it, then individually "
            "re-priced by the UNCHANGED mg_rung against the same horizon "
            "(6.3's own point: a cheap tier can become actionable even when "
            "the whole ladder was not). mg_decompose_retire moves the parent "
            "to a DESCRIPTIVE terminal status ('decomposed') and, "
            "load-bearingly, zeroes its headroom_n -- which is what actually "
            "excludes it from ag_select's AND mg_select's pool, via "
            "POOL()'s own pre-existing Gt(headroom_n, 0.0) clause, with ZERO "
            "edits to seeds/arc_goals.json. Retirement fires only once EVERY "
            "tier has been materialised as a child and at least one child "
            "exists, never on the flag alone. "
            "mg_child_order_n gives each child its own discounted order-N "
            "headroom (headroom_n * tier_survival), which "
            "seeds/arc_magnitude.json v1.1.0's ONE additive guard on "
            "mg_goal_order_n_default protects from being silently "
            "overwritten -- otherwise the SAME inflation trap decision 2 "
            "guards against on the mint side would re-appear on the pricing "
            "side every fixpoint pass. FOLD-UP IS NOT TWINNED and NO "
            "ExecClass IS ADDED -- named out of scope in A16, not silently "
            "dropped. THE HONEST CONSEQUENCE OF DECISION 2's CORRECTION: "
            "the registered arithmetic identity "
            "(Sum(children.headroom_n*tier_survival)==parent.orderN_"
            "headroom_n) holds on a CONSTRUCTED scene (decompose_required "
            "forced with no horizon truncating the parent's own reading) "
            "but NOT on the natural push_back trigger, where the parent's "
            "own orderN_headroom_n is horizon-truncated to 0 while the "
            "children correctly sum to the ladder's full projected value -- "
            "measured and reported, not hidden, in "
            "PROGRAM_SYNTHESIS_ARC6_MG4_DECOMPOSE.md."),
        "microtheory": {
            "name": "arc_goal_decomposition",
            "description": (
                "A huge goal is not one atomic unit with one discounted "
                "headroom -- it is a measured tier ladder, already graph "
                "data, already keyed by a measured population join. "
                "Decomposition is the projection of that existing object "
                "into goals, each re-priced INDEPENDENTLY against the same "
                "horizon the parent could not fit — so a cheap tier can "
                "become individually actionable even when the whole ladder "
                "was not."),
        },
        "nodes": [],
        "edges": [],
        "productions": _productions(),
        "rules": _rules(),
    }


def main(argv):
    text = json.dumps(build(), indent=2, sort_keys=False) + "\n"
    if "--check" in argv:
        cur = open(OUT).read() if os.path.exists(OUT) else ""
        if cur != text:
            print("seeds/arc_decompose.json is OUT OF DATE", file=sys.stderr)
            return 1
        print("seeds/arc_decompose.json is up to date")
        return 0
    with open(OUT, "w") as fh:
        fh.write(text)
    print("wrote", OUT, "(%d bytes)" % len(text))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
