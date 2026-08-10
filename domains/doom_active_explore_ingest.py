"""doom_active_explore_ingest — MECHANICAL adapter for LP-curiosity + commit-net
frontier prioritisation (block 205000). NO decision here (CLAUDE.md): every function
either (a) creates the graph-resident curiosity state, (b) reads a SENSOR value off the
belief (info-gain = how much unknown borders a frontier), or (c) moves a RULE-computed
value (an AttentionItem's interest, computed by the 202000 lp_* rules) to where the
selection RULE reads it, matched by pose key. WHICH frontier is chosen is the
`ae_frontier_goal` RULE; WHEN to re-decide is the commit-net (`cn_*`, `ae_commit_*`).

Persistent curiosity state lives in the GRAPH (pose-keyed AttentionItem nodes), never in
Python (CLAUDE.md: no Python agent state). The adapter only find-or-creates by key and
sets the sensor obs.
"""
from __future__ import annotations

import json
import os

_LP_SEED = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "seeds", "learning_progress_curiosity.json")

# 202000 curiosity params (reused verbatim from learning_progress_measure.py) + the
# commit-net Deliberation defaults.
# mode=1 (surprise-gated freshness): for GEOMETRIC frontier info-gain there is no noisy-TV to
# trap on (info-gain is a real quantity, not a noisy sensor), so surprise-mode IS the correct
# Next-Best-View curiosity signal -- a frontier with sustained unknown-adjacency (high info-gain
# residual against the slow-blending held estimate) keeps its interest FRESH; an exhausted
# frontier (info-gain -> 0) stops boosting and decays. blend_div slows the held estimate so a
# still-productive frontier keeps a positive residual. NOT tuned to a coverage score.
PARAMS = dict(
    enabled=1.0, mode=1.0,
    hl_min=1.0, hl_scale=4.0, interest_c0=1024.0, attend_thresh=256.0,
    progress_floor=10.0, surprise_floor=4.0,
    fast_div=3.0, slow_div=20.0, blend_div=8.0,
)
ITEM_INIT = dict(
    held=0.0, obs=0.0, input_epoch=0.0, epoch=-1.0, residual=0.0,
    fast_res=0.0, slow_res=0.0, learning_progress=0.0, smoothed_progress=0.0,
    interest_half_life=1.0, last_boost_epoch=0.0, interest=1024.0, attended=0.0,
)


def install_curiosity(wa, game, *, commit=True, v_max=1024, commit_cost=50):
    """Create the graph-resident CuriosityHub{params, deliberation} for this game.
    Mechanical construction of the opt-in state (the lp_* / cn_* rules are inert without
    an enabled HeldCuriosityParams)."""
    S, I = wa.s, wa.inner
    # learning_progress_curiosity is self_load_only (skipped by load_all_seeds); load its
    # lp_* / cn_* rules explicitly so the interest law + commit-net are live.
    I.load_seed_manifest(json.load(open(_LP_SEED)), None)
    hub = S.add_node("CuriosityHub", {"kind": "doom_explore"})
    I.add_edge_unchecked(game, "has_curiosity_hub", hub)
    cp = S.add_node("HeldCuriosityParams", dict(PARAMS))
    I.add_edge_unchecked(hub, "has_curiosity_params", cp)
    d = S.add_node("Deliberation", {
        "step": 0.0, "seen_step": -1.0, "v_max": float(v_max), "value": 0.0,
        "marginal_value": 0.0, "committed": 0.0, "commit_step": -1.0,
        "commit_enabled": 1.0 if commit else 0.0, "commit_cost": float(commit_cost)})
    I.add_edge_unchecked(hub, "has_deliberation", d)
    return hub


def _hub(wa, game):
    I = wa.inner
    for h in I.neighbours(game, "has_curiosity_hub"):
        return h
    return None


def _known(wa, game):
    """Set of known (reconstructed) belief cell poses — mechanical read."""
    S, I = wa.s, wa.inner
    known = set()
    for c in I.neighbours(game, "has_cell"):
        p = S.node(c)["attrs"]["pose"]
        known.add((int(p[0]), int(p[1])))
    return known


def _info_gain(F_attrs, known):
    """SENSOR read: how many unknown (absent) cells 4-border this frontier box. High =
    much still to learn through this frontier; 0 = exhausted. Pure geometry over the
    belief; no decision."""
    lo = F_attrs["lo"]; hi = F_attrs["hi"]
    lox, loy = int(lo[0]), int(lo[1]); hix, hiy = int(hi[0]), int(hi[1])
    gain = 0
    for x in range(lox, hix + 1):
        for y in range(loy, hiy + 1):
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = (x + dx, y + dy)
                if nb not in known:
                    gain += 1
    return gain


# coarse spatial bin for the learning-progress region key. Learning progress is a property
# of a REGION, not an ephemeral frontier quantum whose lo-corner churns every epoch: keying by
# a coarse bin gives each region a PERSISTENT AttentionItem (LP history survives re-quantizing)
# AND bounds the item population (pruned to live frontier bins each epoch).
BIN = 4


def _bin(pose_xy):
    return "%d_%d" % (int(pose_xy[0]) // BIN, int(pose_xy[1]) // BIN)


def maintain_frontier_interest(wa, game, epoch):
    """Mechanical, once per epoch AFTER accumulate: aggregate each REGION's frontiers into a
    coarse-bin-keyed AttentionItem, set obs = the region's total info-gain sensor + input_epoch,
    move the item's rule-computed interest onto every frontier in that bin as `f_interest` (so
    ae_frontier_goal can Argmax over it), and PRUNE items whose bin is no longer a live frontier
    (bounds the population). No decision -- interest is the lp_* rules; selection is
    ae_frontier_goal."""
    S, I = wa.s, wa.inner
    hub = _hub(wa, game)
    if hub is None:
        return 0
    items = {}
    for it in I.neighbours(hub, "has_attention_item"):
        k = S.node(it)["attrs"].get("fkey")
        if k is not None:
            items[k] = it
    known = _known(wa, game)
    # gather live frontiers per bin
    bin_gain = {}
    bin_fronts = {}
    for F in S.nodes("SpaceQuantum"):
        if game not in list(I.neighbours(F, "in_space")):
            continue
        a = S.node(F)["attrs"]
        if a.get("kind") != "frontier":
            continue
        key = _bin(a["lo"])
        bin_gain[key] = bin_gain.get(key, 0) + _info_gain(a, known)
        bin_fronts.setdefault(key, []).append(F)
    # update / create an item per live bin; move interest to its frontiers
    for key, gain in bin_gain.items():
        it = items.get(key)
        if it is None:
            it = S.add_node("AttentionItem", dict(ITEM_INIT, fkey=key))
            I.add_edge_unchecked(hub, "has_attention_item", it)
            items[key] = it
        I.set_attr(it, "obs", float(gain))
        I.set_attr(it, "input_epoch", float(epoch))
        interest = float(S.node(it)["attrs"].get("interest", 1024.0))
        for F in bin_fronts[key]:
            I.set_attr(F, "f_interest", interest)
    # prune items whose bin is no longer a live frontier (bounds the population)
    for key, it in items.items():
        if key not in bin_gain:
            I.remove_node(it)
    return len(bin_gain)


def retire_while_deliberating(wa, game):
    """G3 commit-net gate (host I/O reacting to a GRAPH flag, separate pass -- not a decision,
    and split from the flood to avoid a mint/retire oscillation inside one run_rules fixpoint):
    while the commit-net has NOT yet committed (Deliberation.committed==0), retire the exploration
    goal so ae_frontier_goal re-selects this tick. The 202000 cn_commit RULE decides WHEN
    committed flips to 1 (marginal value < commit_cost); once it does, this retire stops and the
    goal is HELD (dwell). The commit ablation is the graph flag commit_enabled: with it 0,
    cn_commit never fires -> committed stays 0 -> perpetual re-selection (thrash). Thus the cn_*
    net's `committed` output is LOAD-BEARING here. Returns #retired."""
    S, I = wa.s, wa.inner
    hub = _hub(wa, game)
    if hub is None:
        return 0
    d = next(iter(I.neighbours(hub, "has_deliberation")), None)
    if d is None or float(S.node(d)["attrs"].get("committed", 0.0)) != 0.0:
        return 0
    n = 0
    for g in list(I.neighbours(game, "committed_goal")):
        if float(S.node(g)["attrs"].get("exploration", 0.0)) == 1.0:
            I.remove_node(g)
            n += 1
    return n


def bump_deliberation(wa, game):
    """Mechanical: increment the commit-net Deliberation step each tick a frontier goal is
    being pursued (the diminishing-returns clock). The cn_* rules DECIDE commit vs
    deliberate; this only advances the clock the rule reads."""
    S, I = wa.s, wa.inner
    hub = _hub(wa, game)
    if hub is None:
        return
    for d in I.neighbours(hub, "has_deliberation"):
        step = float(S.node(d)["attrs"].get("step", 0.0))
        I.set_attr(d, "step", step + 1.0)
