"""LEARNING FROM REPLAYS. An all-or-nothing game gives the agent no foothold by
its own trial-and-error (it never sees a win, so it never gets the win-rule —
chicken-and-egg). But the jabberwock can WATCH (StoryBots, its visual cortex): if
it watches a REPLAY where the game is WON, the win is DEMONSTRATED in front of it
(the score rises), so its ordinary implied-rule induction learns the win-rule from
the demonstration — then it plays with what it learned.

This shell only: (1) RECORDS a winning playthrough (a replay) of a game, (2) has a
fresh agent WATCH it through its normal observe/record loop (no choosing — it just
perceives the demonstrated frames + actions + the win), (3) lets the agent PLAY and
measures whether watching gave it the win-rule. No agent logic here; the learning
is the agent's own induction over what it watched.
"""
from __future__ import annotations

import argparse
import os
import random
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
for p in (str(_ROOT), str(_HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault("ARC3_THIN", "1")
os.environ.setdefault("ARC3_FULL", "1")

from arc3_env import Frame, GameState, ACTION6   # noqa: E402
from domains.curious_agent import CuriousAgent, canonical_action_kind  # noqa: E402
from domains.arc3_thin import arc3_thin_handle, _build_thin, SELF_ID  # noqa: E402
from domains.arc3_full_seed import install_full_seed_set  # noqa: E402


def record_collect_replay(env):
    """Record a WINNING playthrough of CollectEnv as a replay: the demonstrator
    clicks each target in turn (it knows the solution — a replay is a recording of
    a successful play, the thing the agent watches). Returns [(grid, action, score)]."""
    handle = arc3_thin_handle(env, CuriousAgent())   # only for reset/apply plumbing
    sub, ctx = handle["reset"]()
    replay = [(env._render(), None, ctx["score"])]
    targets = list(env._targets)
    for (r, c) in targets:
        sub, ctx = handle["apply_action"](sub, ctx, (f"c6@CellC4@{c}@{r}",))
        replay.append((env._render(), (f"c6@CellC4@{c}@{r}",), ctx["score"]))
        if ctx["won"]:
            break
    return replay


def watch_recording_jsonl(agent, lines, game_label="recording"):
    """Watch a REAL ARC-AGI-3 recording (the site/swarm format). Each JSONL line is
    {"timestamp":…, "data":{"game_id","frame":[64×64 grid],"state","score",
    "action_input":{"id":<0-7>,…},"guid",…}}. The agent observes the recorded
    FRAMES through its own perceive/learn loop, with the recorded action + the
    DEMONSTRATED score — so a scoring run teaches it the win-rule. The same watch
    consumes its OWN recorded play, a swarm's, or a downloaded winning replay."""
    import json
    _AID = {1: "a1", 2: "a2", 3: "a3", 4: "a4", 5: "a5"}   # ACTION ids → kinds
    steps, prev = [], None
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        d = json.loads(ln).get("data", {})
        grid = d.get("frame")
        grid = grid[0] if grid and isinstance(grid[0][0], list) else grid  # frame[0]
        if not grid:
            continue
        ai = (d.get("action_input") or {}).get("id")
        if ai in _AID:
            act = (_AID[ai],)
        elif ai == 6:
            ip = (d.get("action_input") or {}).get("data", {})
            x, y = ip.get("x", 0), ip.get("y", 0)
            v = grid[y][x] if 0 <= y < len(grid) and 0 <= x < len(grid[0]) else 0
            act = (f"c6@CellC{v}@{x}@{y}",)
        else:
            act = None
        # The progress signal. Many games report `score`; LEVEL games (e.g. ls20)
        # report null score and instead carry `levels_completed` (the count of
        # levels cleared) — the same monotone progress the agent learns from. A
        # mechanical field-translation, no decision.
        sc = d.get("score")
        if sc is None:
            lc = d.get("levels_completed")
            sc = len(lc) if isinstance(lc, (list, dict)) else (lc or 0)
        steps.append((grid, act, int(sc or 0)))
    return watch(agent, steps, game_label)


def watch(agent, replay, game_label="replay"):
    """The agent WATCHES the replay through its OWN perceive/learn loop: build each
    demonstrated frame, observe it (vision + symbolic + change-history + the
    demonstrated score), and record the demonstrated action's outcome — so the
    win-rule induction fires on the DEMONSTRATED win. No action choosing; it watches."""
    agent.set_compute_limit(50.0 * (len(replay) + 50))
    prev = None
    prev_score = None
    handle = arc3_thin_handle(type("E", (), {"game_id": game_label})(), agent)  # for interpret_acts_on
    for (grid, action, score) in replay:
        # A demonstrated WIN is a score/level RISE on this step (the action that
        # just cleared a level), not merely score>=1 — a cumulative level-count
        # would otherwise flag every post-level-1 frame as a win.
        won = (prev_score is not None and score > prev_score) and action is not None
        prev_score = score
        fr = Frame(game_id=game_label, guid="g",
                   state=GameState.WIN if won else GameState.NOT_FINISHED,
                   score=int(score), frame=[grid])
        sub, occ, present, ctype = _build_thin(fr, prev, game_label)
        # The win-rule the agent learns by watching is SYMBOLIC (cell-type
        # transition ⟹ reward — "what it is", location-irrelevant). The visual
        # cortex runs on its own thread and is only needed for FORM/shape
        # perception; over a long replay it can back up. WATCH_VISION=0 skips it
        # so a fresh agent can watch a full winning replay quickly and robustly.
        if os.environ.get("WATCH_VISION", "1") == "0":
            sub.vision_screen = None
            sub.vision_frame = None
        ctx = {"frame": fr, "score": int(score), "won": won, "over": False,
               "occupied": occ, "present_types": present,
               "cell_type_at": ctype, "tick": 0}
        agent.observe(sub)
        if action is not None:
            ck = canonical_action_kind(action)
            touched = handle["interpret_acts_on"](sub, ctx, action)
            for t in touched:
                agent._register_relation(t, "acts_on")
            agent._record_activity("act", touched)
            agent.record_action_outcome(
                ck, agent.last_world_novelty, 0.0, agent.boredom_count(sub),
                0, terminal_delta=(1.0 if won else 0.0),
                frontier_after=agent.last_freshening_count)
        prev = grid
        agent.insight(layer=2)


def play(agent, EnvCls, n=120):
    """Play a fresh game and report the first win and total wins."""
    env = EnvCls()
    handle = arc3_thin_handle(env, agent)
    sub, ctx = handle["reset"]()
    agent.observe(sub)
    wins, first = 0, None
    for i in range(n):
        acts = handle["legal_actions"](sub, ctx)
        if not acts:
            break
        a = agent.choose_action(sub, ctx, acts, handle)
        ck = canonical_action_kind(a)
        touched = handle["interpret_acts_on"](sub, ctx, a)
        for t in touched:
            agent._register_relation(t, "acts_on")
        agent._record_activity("act", touched)
        qb = agent.quality_of_position(sub)
        sub, ctx = handle["apply_action"](sub, ctx, a)
        agent.observe(sub)
        agent.record_action_outcome(
            ck, agent.last_world_novelty, max(0.0, qb - agent.quality_of_position(sub)),
            agent.boredom_count(sub), ctx.get("tick", 0),
            terminal_delta=(1.0 if ctx["won"] else 0.0),
            frontier_after=agent.last_freshening_count)
        if ctx["won"]:
            wins += 1
            if first is None:
                first = i + 1
            sub, ctx = handle["reset"]()
            agent.observe(sub)
        if (i + 1) % 8 == 0:
            agent.insight(layer=2)
    return wins, first


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--actions", type=int, default=120)
    args = ap.parse_args(argv)
    from arc3_env import CollectAllEnv as CollectEnv   # ALL-OR-NOTHING: no foothold
    random.seed(0)

    print("=== LEARNING A GAME BY WATCHING A REPLAY (all-or-nothing) ===")
    # (A) BASELINE — a cold agent that has NEVER seen a win plays from scratch.
    cold = CuriousAgent(); cold.my_world_id = SELF_ID; install_full_seed_set(cold)
    cold.set_compute_limit(50.0 * (args.actions + 50))
    w0, f0 = play(cold, CollectEnv, args.actions)
    print(f"  COLD (no replay): first win @ {f0}, wins={w0}, "
          f"held win-rule={cold._held_winrule()}")

    # (B) WATCHER — a fresh agent WATCHES a winning replay, then plays.
    print("  recording a winning replay (a demonstrator solving the game)...")
    replay = record_collect_replay(CollectEnv())
    print(f"  replay length: {len(replay)} frames (ends in a WIN: "
          f"{replay[-1][2] >= 1})")
    watcher = CuriousAgent(); watcher.my_world_id = SELF_ID
    install_full_seed_set(watcher)
    watch(watcher, replay, "collect")
    print(f"  AFTER WATCHING: held win-rule = {watcher._held_winrule()}")
    random.seed(0)
    w1, f1 = play(watcher, CollectEnv, args.actions)
    print(f"  WATCHER (learned from replay): first win @ {f1}, wins={w1}, "
          f"held win-rule={watcher._held_winrule()}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
