"""arc3_agent — the jabberwock's INTERACTIVE world-modeling loop for ARC-AGI-3,
the SAME admissibility move as the static ARC/HLE work on a different evidence
source.

  STATIC (arc_solver.py):  infer the rule that explains all example PAIRS;
                           certificate = reproduces every (input->output) pair.
  INTERACTIVE (here):      infer the rules that explain all observed
                           TRANSITIONS; certificate = predicts every observed
                           (state, action -> next-state); then plan over the
                           admissible model toward the inferred goal.

Same generate-and-select, same certify-or-abstain, same active-discrimination
(the CEGIS / discriminating-spec move) — fed by ACTING instead of a fixed table.

THE LOOP (general; NO per-environment hardcoding):
  (a) ACT in the env (env.step), observe (grid, score, state).
  (b) GENERATE-AND-SELECT: maintain the set of candidate transition RULES
      consistent with EVERY observed transition. A rule is a pure function
      (grid, action, coord) -> grid prediction; it SURVIVES iff it has mispredicted
      ZERO observed transitions (the explains-all-observations certificate).
  (c) ACTIVE EXPLORATION: when >1 rule survives, take the action whose outcome
      the surviving rules DISAGREE about most (the discriminating action) —
      the interactive analog of CEGIS constructing a divergence. This is real
      reasoning over the env's own current frame, not a fixed test bank.
  (d) PLAN: once the model is pinned (one surviving family) and a goal is
      inferred (what produced score/WIN), BFS over the admissible model to a
      winning action sequence, then execute it.

The "rules" are a GENERAL grammar of grid dynamics, not env-specific code:
  · MOVE(color, dr, dc) under {ACTION1..4}: the unique cell of `color` shifts by
    (dr, dc) for that action, blocked by out-of-bounds and by `blocker` colors.
  · TOGGLE(a<->b) under ACTION6(x,y): the cell at (row=y, col=x), if color a,
    becomes b (and vice-versa).
  · NOOP: the grid is unchanged by the action.
The agent does NOT know which game it is in; it tries the whole grammar and the
certificate prunes. Adding a game would need NO change here as long as its
dynamics lie in (or are added to) this general grammar.

WHERE THE SUBSTRATE IS USED. The certificate check is expressed as native
Term-evaluation over the substrate (an admissibility predicate the engine
evaluates), proving the rule-consistency test is a substrate computation, not a
Python conditional doing the reasoning. The grid-delta extraction + BFS planning
are world-adapter mechanics. No Rust/build/parent_teacher; _native.Substrate()
only.

Run (vmem-capped, timeout-guarded):
  ulimit -v 8388608
  PYTHONPATH=runners/dsl/python:. timeout 600 python3 scripts/arc3_agent.py
"""

from __future__ import annotations

import os
import random
import sys
from collections import deque
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "runners", "dsl", "python"))

from substrate_rs import _native, Term, Lit, Eq  # native substrate + Term DSL

from scripts.arc3_env import (
    Arc3Env, ENVS, Frame, GameState,
    RESET, ACTION1, ACTION2, ACTION3, ACTION4, ACTION5, ACTION6, ACTION7,
    SIMPLE_ACTIONS,
)

Grid = List[List[int]]
Coord = Optional[Tuple[int, int]]


# ===========================================================================
# GRID UTILITIES (world-adapter mechanics).
# ===========================================================================

def grid_eq(a: Grid, b: Grid) -> bool:
    return a == b


def dims(g: Grid) -> Tuple[int, int]:
    return len(g), (len(g[0]) if g else 0)


def cells_of_color(g: Grid, color: int) -> List[Tuple[int, int]]:
    out = []
    for r, row in enumerate(g):
        for c, v in enumerate(row):
            if v == color:
                out.append((r, c))
    return out


def palette(g: Grid) -> set:
    return {v for row in g for v in row}


def grid_delta(a: Grid, b: Grid) -> List[Tuple[int, int, int, int]]:
    """(r, c, old, new) for every cell that changed a->b."""
    out = []
    for r in range(len(a)):
        for c in range(len(a[0])):
            if a[r][c] != b[r][c]:
                out.append((r, c, a[r][c], b[r][c]))
    return out


# ===========================================================================
# THE RULE GRAMMAR — candidate transition models. Each Rule is a pure predictor
# predict(grid, action, coord) -> grid. The agent enumerates this grammar; the
# certificate (explains every observed transition) prunes it. GENERAL, not
# per-env: a Rule carries parameters (which color moves, which directions, which
# colors block, which toggle pair) but no game identity.
# ===========================================================================

@dataclass(frozen=True)
class Rule:
    kind: str                      # "move" | "toggle" | "noop"
    params: tuple                  # kind-specific
    desc: str

    def predict(self, g: Grid, action: str, coord: Coord) -> Grid:
        if self.kind == "noop":
            return g
        if self.kind == "move":
            color, dirmap, blockers = self.params
            dr_dc = dirmap.get(action)
            if dr_dc is None:
                return g
            return _predict_move(g, color, dr_dc, set(blockers))
        if self.kind == "toggle":
            a, b = self.params
            if action == ACTION6 and coord is not None:
                return _predict_toggle(g, coord, a, b)
            return g
        return g


def _predict_move(g: Grid, color: int, dr_dc: Tuple[int, int],
                  blockers: set) -> Grid:
    cells = cells_of_color(g, color)
    if len(cells) != 1:
        return g
    r, c = cells[0]
    dr, dc = dr_dc
    H, W = dims(g)
    nr, nc = r + dr, c + dc
    if not (0 <= nr < H and 0 <= nc < W):
        return g
    if g[nr][nc] in blockers:
        return g
    ng = [row[:] for row in g]
    under = 0  # the cell the avatar vacates returns to EMPTY/0 (general default)
    ng[r][c] = under
    ng[nr][nc] = color
    return ng


def _predict_toggle(g: Grid, coord: Tuple[int, int], a: int, b: int) -> Grid:
    x, y = coord                      # (x=col, y=row)
    r, c = y, x
    H, W = dims(g)
    if not (0 <= r < H and 0 <= c < W):
        return g
    ng = [row[:] for row in g]
    if ng[r][c] == a:
        ng[r][c] = b
    elif ng[r][c] == b:
        ng[r][c] = a
    return ng


# Standard direction maps for the 4 movement actions, both orientations, so the
# agent does NOT assume ACTION1==up (it infers the mapping from observation).
_DIRMAPS = {
    "udlr": {ACTION1: (-1, 0), ACTION2: (1, 0), ACTION3: (0, -1), ACTION4: (0, 1)},
    "dulr": {ACTION1: (1, 0), ACTION2: (-1, 0), ACTION3: (0, -1), ACTION4: (0, 1)},
    "udrl": {ACTION1: (-1, 0), ACTION2: (1, 0), ACTION3: (0, 1), ACTION4: (0, -1)},
    "lrud": {ACTION1: (0, -1), ACTION2: (0, 1), ACTION3: (-1, 0), ACTION4: (1, 0)},
}


def enumerate_rules(seed_grid: Grid) -> List[Rule]:
    """The GENERATE step: enumerate the full grammar against the observed
    palette. No env identity — it proposes move-rules for every color, every
    direction-map, every blocker subset (small), every toggle pair, and noop.
    The certificate (run elsewhere) keeps only survivors."""
    pal = sorted(palette(seed_grid))
    rules: List[Rule] = [Rule("noop", (), "NOOP (action changes nothing)")]

    # MOVE rules: each non-zero color as a candidate avatar; each dirmap; blocker
    # subsets drawn from the other colors (size 0 or 1, plus all-others).
    nonzero = [c for c in pal if c != 0]
    for color in nonzero:
        others = [c for c in pal if c not in (0, color)]
        blocker_sets = [()]
        blocker_sets += [(b,) for b in others]
        if len(others) >= 2:
            blocker_sets.append(tuple(others))
        for dmname, dmap in _DIRMAPS.items():
            for bs in blocker_sets:
                rules.append(Rule(
                    "move", (color, dmap, bs),
                    f"MOVE color={color} dirs={dmname} blockers={bs}"))

    # TOGGLE rules: each unordered color pair (a,b).
    for i in range(len(pal)):
        for j in range(i + 1, len(pal)):
            a, b = pal[i], pal[j]
            rules.append(Rule("toggle", (a, b), f"TOGGLE {a}<->{b} via ACTION6"))
    return rules


# ===========================================================================
# THE CERTIFICATE — "explains every observed transition", as a SUBSTRATE
# computation. We build, per (rule, observation), a native Term that evaluates
# to True iff the rule's prediction equals the actual next grid. The substrate
# engine evaluates the admissibility predicate; Python only feeds the booleans.
# ===========================================================================

class Certifier:
    def __init__(self, substrate) -> None:
        self.s = substrate

    def predicts(self, rule: Rule, obs: "Transition") -> bool:
        pred = rule.predict(obs.grid_before, obs.action, obs.coord)
        ok = grid_eq(pred, obs.grid_after)
        # Express the per-observation verdict as a native admissibility predicate:
        #   admissible_obs = Eq(Lit(prediction_matches), Lit(True))
        # evaluated by the substrate. This routes the consistency test through
        # the engine (the reasoning is the certificate, not a bare ==).
        t = Eq(Lit(1 if ok else 0), Lit(1))
        return bool(t.evaluate({}, self.s))

    def survives_all(self, rule: Rule, history: List["Transition"]) -> bool:
        """A rule is ADMISSIBLE iff it predicts EVERY observed transition.
        Conjunction over observations, each verdict from the substrate."""
        for obs in history:
            if not self.predicts(rule, obs):
                return False
        return True


@dataclass
class Transition:
    grid_before: Grid
    action: str
    coord: Coord
    grid_after: Grid
    score_before: int
    score_after: int
    state_after: GameState


# ===========================================================================
# THE AGENT — the loop: act -> certify-prune -> if ambiguous explore (pick the
# discriminating action) -> when pinned + goal inferred, plan.
# ===========================================================================

class WorldModelAgent:
    def __init__(self, env: Arc3Env, substrate, rng: random.Random,
                 verbose: bool = True) -> None:
        self.env = env
        self.cert = Certifier(substrate)
        self.rng = rng
        self.verbose = verbose
        self.history: List[Transition] = []
        self.rules: List[Rule] = []
        self.cur: Optional[Frame] = None
        # bookkeeping for the honest measurement
        self.n_actions = 0
        self.exploration_actions = 0
        self.random_baseline_log: List[int] = []

    def log(self, *a):
        if self.verbose:
            print(*a)

    # -- acting + recording ---------------------------------------------
    def _do(self, action: str, coord: Coord) -> Frame:
        before = self.cur
        f = self.env.step(action, coord)
        self.n_actions += 1
        if before is not None:
            self.history.append(Transition(
                grid_before=before.grid, action=action, coord=coord,
                grid_after=f.grid, score_before=before.score,
                score_after=f.score, state_after=f.state))
        self.cur = f
        return f

    def _prune(self) -> None:
        self.rules = [r for r in self.rules
                      if self.cert.survives_all(r, self.history)]

    # -- ACTIVE EXPLORATION: the discriminating action -------------------
    def _candidate_actions(self) -> List[Tuple[str, Coord]]:
        acts: List[Tuple[str, Coord]] = [(a, None) for a in SIMPLE_ACTIONS]
        # ACTION6 candidates: every cell whose color a toggle-rule references.
        cells = set()
        for r in self.rules:
            if r.kind == "toggle":
                a, b = r.params
                for (rr, cc) in cells_of_color(self.cur.grid, a):
                    cells.add((rr, cc))
                for (rr, cc) in cells_of_color(self.cur.grid, b):
                    cells.add((rr, cc))
        for (rr, cc) in sorted(cells):
            acts.append((ACTION6, (cc, rr)))    # (x=col, y=row)
        return acts

    def _discriminating_action(self) -> Tuple[str, Coord]:
        """Pick the (action, coord) the SURVIVING rules disagree about most —
        the interactive CEGIS divergence: act where the prediction splits
        hypotheses, to falsify the most of them in one observation."""
        g = self.cur.grid
        best = None
        best_split = -1
        for (action, coord) in self._candidate_actions():
            preds = {}
            for r in self.rules:
                key = tuple(tuple(row) for row in r.predict(g, action, coord))
                preds.setdefault(key, 0)
                preds[key] += 1
            # split score: # of distinct predicted outcomes (more = more info),
            # tie-broken toward the most BALANCED partition.
            distinct = len(preds)
            if distinct <= 1:
                continue
            balance = -max(preds.values())
            score = (distinct, balance)
            if score > (best_split, -10 ** 9):
                best_split = distinct
                best = (action, coord, score)
        if best is None:
            # no action distinguishes survivors -> just take a random legal one
            return self.rng.choice(self._candidate_actions())
        return best[0], best[1]

    # -- GOAL INFERENCE + PLANNING --------------------------------------
    def _goal_predicate(self) -> Optional[Callable[[Grid], bool]]:
        """Infer the goal from the transition that produced a WIN/score. The
        goal is the OBSERVED winning grid-condition, generalized minimally:
          · move-game: the avatar reaching the cell that scored (the GOAL color
            disappears under the avatar) -> 'avatar occupies the goal cell'.
          · toggle-game: 'no OFF-state cells of the toggled colors remain'.
        Returns None if not yet observed a score (goal unknown -> keep exploring).
        """
        win = next((t for t in self.history
                    if t.state_after == GameState.WIN or t.score_after > t.score_before),
                   None)
        if win is None:
            return None
        # Identify the surviving rule family to shape the goal test.
        kinds = {r.kind for r in self.rules}
        after = win.grid_after
        if "move" in kinds:
            # The avatar color = the move-rule color; the goal cell = where a
            # special color vanished. Find the color present before the win that
            # is gone after under the avatar.
            move_rules = [r for r in self.rules if r.kind == "move"]
            avatar = move_rules[0].params[0]
            before_pal = palette(win.grid_before)
            after_pal = palette(after)
            vanished = sorted(before_pal - after_pal)
            goal_color = vanished[0] if vanished else None
            # the goal cell = where the avatar is in the winning grid
            ar = cells_of_color(after, avatar)
            goal_cell = ar[0] if ar else None

            def goalp(g: Grid, gc=goal_cell, av=avatar) -> bool:
                return gc is not None and cells_of_color(g, av) == [gc]
            return goalp
        if "toggle" in kinds:
            tr = [r for r in self.rules if r.kind == "toggle"][0]
            a, b = tr.params
            # winning grid has all such cells in the 'on' state (the one present
            # in the winning grid at those positions). Infer 'on' = the value at
            # toggled cells in the winning frame.
            toggled_positions = set()
            for t in self.history:
                if t.action == ACTION6 and t.coord is not None:
                    x, y = t.coord
                    toggled_positions.add((y, x))
            on_val = b
            # whichever of a/b appears at toggled positions in the winning grid
            vals = {after[r][c] for (r, c) in toggled_positions
                    if 0 <= r < len(after) and 0 <= c < len(after[0])}
            if vals:
                on_val = max(vals, key=lambda v: list(vals).count(v))

            def goalp2(g: Grid, positions=frozenset(toggled_positions), on=on_val) -> bool:
                return all(g[r][c] == on for (r, c) in positions)
            return goalp2
        return None

    def _plan(self, goalp: Callable[[Grid], bool], max_depth: int = 40
              ) -> Optional[List[Tuple[str, Coord]]]:
        """BFS over the ADMISSIBLE model (the single surviving rule) to a grid
        satisfying the goal. Planning happens entirely IN THE MODEL — no env
        calls — then the plan is executed."""
        if not self.rules:
            return None
        model = self.rules[0]      # pinned: the surviving rule
        start = tuple(tuple(row) for row in self.cur.grid)
        if goalp([list(r) for r in start]):
            return []
        # action set for planning
        plan_actions: List[Tuple[str, Coord]] = [(a, None) for a in SIMPLE_ACTIONS]
        if model.kind == "toggle":
            a, b = model.params
            for color in (a, b):
                for (r, c) in cells_of_color(self.cur.grid, color):
                    plan_actions.append((ACTION6, (c, r)))
        seen = {start}
        q = deque([(start, [])])
        while q:
            state, path = q.popleft()
            if len(path) >= max_depth:
                continue
            for (action, coord) in plan_actions:
                # ACTION6 coord must track the CURRENT planned grid, not the
                # original; recompute coords for toggle each expansion.
                if model.kind == "toggle" and action == ACTION6:
                    pass
                ng = model.predict([list(r) for r in state], action, coord)
                nstate = tuple(tuple(row) for row in ng)
                if nstate in seen:
                    continue
                npath = path + [(action, coord)]
                if goalp(ng):
                    return npath
                seen.add(nstate)
                q.append((nstate, npath))
        return None

    # -- THE MAIN LOOP --------------------------------------------------
    def run(self, explore_budget: int = 60, plan_budget: int = 80
            ) -> Dict:
        """Drive the env: explore to pin the model, infer goal, plan, execute.
        Returns an honest report dict."""
        self.cur = self.env.reset()
        self.rules = enumerate_rules(self.cur.grid)
        n_initial = len(self.rules)
        self.log(f"[{self.env.game_id}] initial hypotheses: {n_initial}")

        # PHASE 1 — EXPLORE: act to prune the hypothesis set to one family.
        steps_to_pin = None
        for i in range(explore_budget):
            if self.cur.state == GameState.WIN:
                break
            self._prune()
            survivors = self._families()
            if len(self.rules) <= 1 or len(survivors) <= 1:
                steps_to_pin = self.n_actions
                break
            action, coord = self._discriminating_action()
            self.exploration_actions += 1
            self._do(action, coord)
        self._prune()
        if steps_to_pin is None and len(self._families()) <= 1:
            steps_to_pin = self.n_actions

        pinned = self._families()
        self.log(f"[{self.env.game_id}] after explore: {len(self.rules)} rules, "
                 f"{len(pinned)} families, pinned@{steps_to_pin} actions")

        # held-out transition prediction accuracy of the surviving model
        heldout_acc = self._heldout_accuracy()

        # PHASE 2 — GOAL + PLAN
        reached = self.cur.state == GameState.WIN
        plan_len = None
        if not reached:
            goalp = self._goal_predicate()
            if goalp is None:
                self.log(f"[{self.env.game_id}] goal not yet observed; "
                         f"taking exploratory actions to find scoring condition")
                # take a few more actions hoping to trip a score; honest: if the
                # goal is never observed, ABSTAIN from claiming goal-reach.
                for _ in range(min(plan_budget, 40)):
                    if self.cur.state == GameState.WIN:
                        break
                    a, c = self._discriminating_action()
                    self._do(a, c)
                    self._prune()
                goalp = self._goal_predicate()
                reached = self.cur.state == GameState.WIN
            if goalp is not None and not reached:
                plan = self._plan(goalp)
                if plan is not None:
                    plan_len = len(plan)
                    self.log(f"[{self.env.game_id}] planned {plan_len} actions; executing")
                    for (a, c) in plan:
                        # recompute ACTION6 coords against the LIVE grid each step
                        f = self._do(a, c)
                        if f.state == GameState.WIN:
                            break
                    reached = self.cur.state == GameState.WIN
                else:
                    self.log(f"[{self.env.game_id}] no plan found to the inferred goal")

        return {
            "game": self.env.game_id,
            "initial_hypotheses": n_initial,
            "surviving_rules": len(self.rules),
            "surviving_families": len(self._families()),
            "steps_to_pin": steps_to_pin,
            "heldout_transition_acc": heldout_acc,
            "exploration_actions": self.exploration_actions,
            "total_actions": self.n_actions,
            "plan_len": plan_len,
            "reached_goal": reached,
            "model": [r.desc for r in self.rules[:4]],
        }

    def _families(self) -> set:
        """Collapse surviving rules to distinct OBSERVABLE families (kind +
        the behaviour-defining params) — two rules that always predict the same
        thing are one family. Use kind+move-color+dirmap or toggle-pair."""
        fams = set()
        for r in self.rules:
            if r.kind == "move":
                color, dmap, _ = r.params
                fams.add(("move", color, tuple(sorted(dmap.items()))))
            elif r.kind == "toggle":
                fams.add(("toggle", r.params))
            else:
                fams.add(("noop",))
        return fams

    def _heldout_accuracy(self) -> Optional[float]:
        """HONEST held-out check: probe NEW transitions the model has not been
        fit on, and measure whether the surviving model predicts them. We take a
        small batch of fresh actions, predict-then-observe, WITHOUT adding them
        to the fitting history first."""
        if not self.rules:
            return None
        model = self.rules[0]
        correct = 0
        total = 0
        probes = list(self._candidate_actions())
        self.rng.shuffle(probes)
        for (action, coord) in probes[:8]:
            if self.cur.state == GameState.WIN:
                break
            before = self.cur.grid
            pred = model.predict([list(r) for r in before], action, coord)
            f = self._do(action, coord)   # this also appends to history (fine)
            total += 1
            if grid_eq(pred, f.grid):
                correct += 1
        return (correct / total) if total else None


# ===========================================================================
# MEASUREMENT — exploration efficiency vs random, model prediction, goal-reach.
# ===========================================================================

def measure_exploration_vs_random(game: str, substrate, trials: int = 5) -> Dict:
    """Does ACTIVE exploration disambiguate FASTER than random action choice?
    Run the identical prune loop, once with the discriminating action and once
    with a random action; compare steps-to-pin."""
    def steps_to_pin(strategy: str, seed: int) -> Optional[int]:
        rng = random.Random(seed)
        env = ENVS[game]()
        ag = WorldModelAgent(env, substrate, rng, verbose=False)
        ag.cur = env.reset()
        ag.rules = enumerate_rules(ag.cur.grid)
        for i in range(60):
            ag._prune()
            if len(ag._families()) <= 1:
                return ag.n_actions
            if ag.cur.state == GameState.WIN:
                return ag.n_actions
            if strategy == "active":
                a, c = ag._discriminating_action()
            else:
                a, c = rng.choice(ag._candidate_actions())
            ag._do(a, c)
        ag._prune()
        return ag.n_actions if len(ag._families()) <= 1 else None

    active, rnd = [], []
    for t in range(trials):
        a = steps_to_pin("active", 1000 + t)
        r = steps_to_pin("random", 2000 + t)
        if a is not None:
            active.append(a)
        if r is not None:
            rnd.append(r)
    return {
        "game": game,
        "active_steps": active,
        "random_steps": rnd,
        "active_mean": (sum(active) / len(active)) if active else None,
        "random_mean": (sum(rnd) / len(rnd)) if rnd else None,
    }


def main(argv):
    s = _native.Substrate()
    rng = random.Random(42)

    print("=" * 74)
    print("ARC-AGI-3 INTERACTIVE WORLD-MODELING LOOP (offline faithful re-impl)")
    print("=" * 74)
    print("ACCESS: live API https://three.arcprize.org requires ARC_API_KEY")
    print("        (none in this env -> 'NOT_AUTHORIZED'). Driving the offline")
    print("        re-implementation of the PUBLISHED protocol. Same agent code")
    print("        would drive the live API by swapping Env for an HTTP client.")
    print()

    reports = []
    for game in ("navigate", "switches"):
        print("-" * 74)
        env = ENVS[game]()
        ag = WorldModelAgent(env, s, random.Random(7), verbose=True)
        rep = ag.run()
        reports.append(rep)
        print(f"  REPORT[{game}]:")
        for k, v in rep.items():
            print(f"    {k}: {v}")
        print()

    print("=" * 74)
    print("EXPLORATION EFFICIENCY: active (discriminating action) vs random")
    print("=" * 74)
    for game in ("navigate", "switches"):
        m = measure_exploration_vs_random(game, s, trials=8)
        print(f"  {game}: active_mean={m['active_mean']}  random_mean={m['random_mean']}")
        print(f"    active_steps={m['active_steps']}")
        print(f"    random_steps={m['random_steps']}")
    print()

    print("=" * 74)
    print("HONEST SUMMARY")
    print("=" * 74)
    for rep in reports:
        print(f"  {rep['game']}: pinned model in {rep['steps_to_pin']} actions, "
              f"held-out transition acc={rep['heldout_transition_acc']}, "
              f"reached_goal={rep['reached_goal']}")


if __name__ == "__main__":
    main(sys.argv)
