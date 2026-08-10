"""PER-AREA ASYNC SETTLEMENT — the gate (block 186000).

Prereg: `SETTLEMENT_PER_AREA_PREREG.md`. Results: `SETTLEMENT_PER_AREA_RESULTS.md`.

A cortex tick is a SETTLEMENT EVENT that CARRIES a residual. `run_rules_settle`
is that mechanism, built ALONGSIDE the committed global `run_rules` fixpoint and
DEFAULT OFF — nothing in the committed tree calls it.

What this file pins:
  * DEFAULT-OFF: `run_rules` is untouched and still reaches a TRUE fixed point;
    settlement runs only when a caller asks for it by name.
  * THE REDUCTION: settlement with an UNBOUNDED budget reproduces the global
    fixpoint's final graph state EXACTLY. This is the correctness bridge that
    makes the mechanism a GENERALISATION rather than a different system.
  * RESIDUAL IS CARRIED: under a FINITE budget an area settles part of its work
    and carries the rest; more rounds converge to the SAME endpoint.
  * THE FALSIFIER: DROPPING the residual instead of carrying it DIVERGES. (If
    it did not, the residual accounting would not be real. Mirrors the block
    185000 negative: shedding a residual by freezing its reference FABRICATES
    surprise.)
  * COST ∝ SURPRISE AT THE AREA GRAIN: an area with no dirty input does NO work,
    measured at the MECHANISM grain (rule attempts), never as wall-clock — an
    async schedule must not be gated on a timing threshold.
  * NO new Term enum variant.

Every assertion is an invariant of the MECHANISM, so it holds in this worktree
and on `main` alike. No global-barrier snapshot is taken: the ledger is read
per-area, per-round, from the engine's own report.
"""
from __future__ import annotations

import json
import os

import pytest

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_ROUNDS = 200_000

#: WHICH SETTLEMENT SCHEDULE THE REDUCTION IS PINNED AGAINST — the measured
#: scope, not a preference. `snapshot_round=True` is the BARRIER form: every
#: area reads its dirty set once at round start, so a round attempts exactly
#: the rule multiset one committed global pass would, permuted into area-major
#: order. `snapshot_round=False` is the fully ASYNC form (each area reads on
#: its own clock); it is the DEFAULT of the entrypoint and is exercised
#: separately below, where the scope of its agreement is asserted honestly.
SCHEDULE_SNAPSHOT = True


# ------------------------------------------------------------------ helpers ---
def _canon(obj):
    """Float-EXACT canonical text for a whole-graph dump (`repr` on floats, so
    identity is claimed at full precision and never at `str()`)."""
    if isinstance(obj, float):
        return "f" + repr(obj)
    if isinstance(obj, bool):
        return "b" + repr(obj)
    if isinstance(obj, int):
        return "i" + repr(obj)
    if isinstance(obj, (list, tuple)):
        return "[" + ",".join(_canon(x) for x in obj) + "]"
    if isinstance(obj, dict):
        return "{" + ",".join(
            repr(k) + ":" + _canon(obj[k]) for k in sorted(obj, key=repr)) + "}"
    return repr(obj)


#: The ONLY attributes excluded from a byte-identity dump, NAMED (never a
#: pattern, never a tolerance). Both are WALL-CLOCK instrumentation the runtime
#: writes into the graph, so they differ between two runs of the SAME binary on
#: the SAME input. `test_the_only_nondeterminism_is_the_named_wall_clock` proves
#: the exclusion is exactly right and not a convenient blanket.
NONDETERMINISTIC_ATTRS = {("AreaLoad", "service_wall_micros"),
                          ("TaskResult", "wall_micros")}


def _dump(inner, strip=True):
    d = inner.graph_to_dict()
    if strip:
        for node in d.get("nodes", []):
            for type_, key in NONDETERMINISTIC_ATTRS:
                if node.get("type") == type_:
                    node["attrs"].pop(key, None)
    return _canon(d)


def _sched_agent(*extra):
    agent = WorldAdapter(seeds=())
    for name in ("cognitive_areas", "cognitive_scheduler") + tuple(extra):
        path = os.path.join(ROOT, "seeds", name + ".json")
        with open(path) as fh:
            agent.inner.load_seed_manifest(json.load(fh), agent.agent)
    return agent


def _scenario(agent, n_areas=3, n_tasks=3):
    """The committed scheduler scenario shape (areas with tasks, a residual, a
    projection, an area load) — the same one `test_seizure_dynamics_migrated`
    drives. Real rules, real material."""
    made = []
    for a in range(n_areas):
        area = agent.s.add_node("CognitiveArea", {
            "name": f"test{a}", "status": "active", "input_epoch": 2,
            "logical_tick": 0, "desired_workers": 1, "effort": 0.0,
            "last_residual_epoch": -1})
        dst = agent.s.add_node("CognitiveArea", {
            "name": f"dst{a}", "status": "active", "input_epoch": 1,
            "logical_tick": 0, "desired_workers": 1, "effort": 0.0,
            "last_residual_epoch": -1})
        agent.inner.add_edge_unchecked(area, "projects_to", dst)
        res = agent.s.add_node("Residual", {"epoch": 5 + a})
        agent.inner.add_edge_unchecked(area, "has_residual", res)
        load = agent.s.add_node("AreaLoad", {
            "queued": 3, "failed": 0, "fold_conflicts": 0, "capacity_workers": 2})
        agent.inner.add_edge_unchecked(area, "has_area_load", load)
        for i in range(n_tasks):
            t = agent.s.add_node("CognitiveTask", {
                "status": "pending", "kind": "abs_diff_energy",
                "payload": [float(i), float(i + 1)], "input_epoch": 2,
                "salience": 0.9 - 0.1 * i, "logical_time": i,
                "area": f"test{a}", "order": 2, "effort": 1})
            agent.inner.add_edge_unchecked(area, "has_task", t)
        made.append(area)
    return made


#: Two more COMMITTED seeds whose rules live in OTHER areas (`executive`,
#: `spatial`) and which have no material here, so those areas are permanently
#: QUIET. Loading them turns the scheduler scenario into a genuine MULTI-AREA
#: workload without inventing a taxonomy.
QUIET_AREA_SEEDS = ("information_commitment", "spatial_belief_core")


def _drive_scheduler(driver, n_calls=4, extra=()):
    """One protocol, one substitutable engine call. Returns (dump, reports)."""
    agent = _sched_agent(*extra)
    _scenario(agent)
    reports = []
    for _ in range(n_calls):
        agent.inner.run_cognitive_tasks(1)
        r = driver(agent.inner)
        if isinstance(r, dict):
            reports.append(r)
    return _dump(agent.inner), reports


def _global(inner):
    return inner.run_rules()


def _settle(budget, drop=False, snapshot=SCHEDULE_SNAPSHOT):
    return lambda inner: inner.run_rules_settle(
        budget, MAX_ROUNDS, drop, snapshot)


def _synth(n_areas, dirty_areas, chain=5):
    """N independent areas, each a rule CHAIN over its own edge types, so an
    area's work AND its quietness are both real. `"area"` is the ordinary
    manifest key every seed already uses.

    The agent is returned SETTLED and then perturbed in exactly `dirty_areas`
    areas. Settling first is load-bearing: a freshly installed rule is dirty by
    construction (the engine must try it once), so measuring straight after
    `add_rule` would measure 'try every area once' and say nothing at all about
    surprise. Same discipline as block 185000's adapt-then-perturb."""
    agent = WorldAdapter(seeds=())
    inner = agent.inner
    for a in range(n_areas):
        for k in range(chain):
            inner.add_rule({
                "name": f"pas_a{a}_r{k}",
                "area": f"pas{a}",
                "order": 1,
                "match": [["src", f"pe_a{a}_{k}", "tgt"]],
                "effects": [["add_edge", "src", f"pe_a{a}_{k + 1}", "tgt", {}],
                            ["set_attr_if_different", "tgt", f"pv{k}", float(k)]],
            })
    inner.run_rules_settle(0, MAX_ROUNDS, False, SCHEDULE_SNAPSHOT)   # SETTLE
    for a in range(dirty_areas):                                      # PERTURB
        s = agent.s.add_node(f"PasSrc{a}", {"i": float(a)})
        t = agent.s.add_node(f"PasTgt{a}", {"i": float(a)})
        inner.add_edge_unchecked(s, f"pe_a{a}_0", t)
    return agent


def _attempts(report):
    return sum(row["attempted"] for rd in report["rounds"] for row in rd["rows"])


def _carried(report):
    return sum(row["carried"] for rd in report["rounds"] for row in rd["rows"])


# ---------------------------------------------------------------- DEFAULT OFF --
def test_settlement_is_a_separate_entrypoint_and_run_rules_is_untouched():
    """`run_rules` still reaches a TRUE fixed point, and settlement is reachable
    only by explicit call. A caller that never names it gets the committed loop.
    """
    agent = _sched_agent()
    _scenario(agent)
    agent.inner.run_cognitive_tasks(1)
    assert agent.inner.run_rules() > 0          # it did real work
    assert agent.inner.run_rules() == 0         # ...to a true fixed point
    # And the fixed point of the global loop is ALSO a fixed point of
    # settlement: settling a settled account moves nothing.
    rep = agent.inner.run_rules_settle(0, MAX_ROUNDS, False, SCHEDULE_SNAPSHOT)
    assert rep["steps"] == 0
    assert rep["rounds"][-1]["residual"] == 0


def test_the_only_nondeterminism_is_the_named_wall_clock():
    """The byte-identity claims below exclude exactly TWO attributes. This pins
    that the exclusion is honest: run the SAME committed loop on the SAME input
    twice and the graphs differ ONLY in those two wall-clock counters — node
    ids, the edge set and every other attribute reproduce exactly. Without this
    the exclusion would be a blanket that could hide a real divergence."""
    a, _ = _drive_scheduler(_global)
    b, _ = _drive_scheduler(_global)
    assert a == b                                     # stripped: identical
    ra, _ = _drive_scheduler_raw()
    rb, _ = _drive_scheduler_raw()
    if ra != rb:                                      # unstripped may differ...
        for node_a, node_b in zip(ra["nodes"], rb["nodes"]):
            assert node_a["id"] == node_b["id"]
            assert node_a["type"] == node_b["type"]
            for key in set(node_a["attrs"]) | set(node_b["attrs"]):
                if node_a["attrs"].get(key) != node_b["attrs"].get(key):
                    assert (node_a["type"], key) in NONDETERMINISTIC_ATTRS, (
                        f"unexpected non-determinism at "
                        f"{node_a['type']}.{key} — the exclusion set is wrong")
        assert ra["edges"] == rb["edges"]
        assert ra["next_id"] == rb["next_id"]


def _drive_scheduler_raw(n_calls=4):
    agent = _sched_agent()
    _scenario(agent)
    for _ in range(n_calls):
        agent.inner.run_cognitive_tasks(1)
        agent.inner.run_rules()
    return agent.inner.graph_to_dict(), None


def test_no_new_term_enum_variant():
    """The mechanism is a graph op + PyO3 entrypoint, never a new Term."""
    with open(os.path.join(ROOT, "runners", "dsl", "src", "term.rs")) as fh:
        term_src = fh.read()
    assert "Settle" not in term_src, (
        "term.rs declares a Settle Term variant — settlement must be a graph op "
        "plus a PyO3 entrypoint, never a new Term")


# ------------------------------------------------------------- THE REDUCTION --
def test_unbounded_settlement_reproduces_the_global_fixpoint_exactly():
    """THE CORRECTNESS BRIDGE. Per-area settlement with an UNBOUNDED budget must
    land on the global fixpoint's final state, byte-for-byte. If it did not, the
    mechanism would be a different system, not a generalisation."""
    base, _ = _drive_scheduler(_global, extra=QUIET_AREA_SEEDS)
    got, reports = _drive_scheduler(_settle(0), extra=QUIET_AREA_SEEDS)
    assert got == base
    # NON-VACUITY: it really ran the settlement path, over a REAL partition.
    assert sum(r["steps"] for r in reports) > 0
    assert max(r["n_rounds"] for r in reports) >= 2
    assert any(len(r["areas"]) >= 2 for r in reports), (
        "the workload must expose more than one area for this to mean anything")
    # ...and the partition is the committed seeds' OWN area labels.
    assert {"scheduler", "executive", "spatial"} <= set(reports[-1]["areas"])


def test_the_reduction_holds_on_the_real_vision_retina():
    """The vision path — the real 2-D retina on the GRAPH (`retina_accel=False`),
    carrying the carve / motion / salience settle ops that block 185000 named as
    the next bottleneck. Two REAL areas from committed seeds: `scheduler` and
    `retina`."""
    dumps = []
    areas_seen = None
    for driver in (_global, _settle(0)):
        out, seen = _vision_run(driver)
        dumps.append(out)
        if seen is not None:
            areas_seen = seen
    assert dumps[0] == dumps[1]
    assert areas_seen is not None and {"retina", "scheduler"} <= set(areas_seen)


def _vision_run(driver, n_az=8, n_el=6, hold=3, motion=2):
    from domains.photon_eye import GraphEye
    from domains import doom_photon_world as dpw
    import numpy as np

    rng = np.random.default_rng(186000)
    eye = GraphEye(
        n_az=n_az, n_el=n_el, adapt_rate=0.4,
        context={"retina_2d": True, "synchronous": True, "worker_capacity": 1,
                 "onset_threshold_db": 6.0, "onset_refractory_epochs": 0.0,
                 "visual_carve": True, "carve_min_coherence": 0.5,
                 "carve_min_events": 2.5, "visual_motion": True,
                 "visual_salience": True, "retina_accel": False}).build()
    inner = eye.substrate._inner
    base = rng.uniform(20.0, 200.0, size=(n_el, n_az))
    areas = None

    def step(grid):
        nonlocal areas
        eye.submit_photons_2d(
            dpw.packets_from_counts(dpw.photon_counts(grid, None), None))
        inner.run_cognitive_tasks(1)
        r = driver(inner)
        if isinstance(r, dict):
            areas = r["areas"]
        eye.prune_settled_tasks()

    for _ in range(hold):
        step(base)
    for nid in list(eye.substrate.nodes("RetinalOnsetEvent")):
        eye.substrate.remove_node(nid)
    since = eye._epoch + 1
    for m in range(motion):
        g = base.copy()
        g[:, (m + 1) % n_az] = 240.0          # a moving bright column
        step(g)
    eye.settle_carve_2d(since_epoch=since)
    eye.settle_motion_2d(since_epoch=since)
    eye.settle_salience_2d(since_epoch=since)
    inner.run_cognitive_tasks(1)
    r = driver(inner)
    if isinstance(r, dict):
        areas = r["areas"]
    out = _dump(inner)
    eye.stop()
    return out, areas


# ------------------------------------------------- RESIDUAL IS CARRIED --------
@pytest.mark.parametrize("budget", [1, 2, 4, 8])
def test_a_finite_budget_still_reaches_the_same_endpoint(budget):
    """You settle for this time; the rest is CARRIED, never lost. More rounds
    converge on the SAME final state the unbounded / global run reaches."""
    base, _ = _drive_scheduler(_global)
    got, reports = _drive_scheduler(_settle(budget))
    assert got == base, f"budget {budget} lost work instead of carrying it"
    # The account CLOSES at the end: terminal residual is exactly 0.
    assert reports[-1]["rounds"][-1]["residual"] == 0


@pytest.mark.parametrize("budget", [1, 2])
def test_a_tight_budget_genuinely_defers_work(budget):
    """NON-VACUITY for the test above: at a budget that actually BITES, work is
    measurably carried and the run needs strictly MORE rounds than the
    unbounded one. (At a loose budget nothing is deferred and carried is 0 —
    correct, and the reason this assertion is scoped to the tight budgets.)"""
    _, reports = _drive_scheduler(_settle(budget))
    _, unbounded = _drive_scheduler(_settle(0))
    assert sum(_carried(r) for r in reports) > 0
    assert (sum(r["n_rounds"] for r in reports)
            > sum(r["n_rounds"] for r in unbounded))


def test_residual_is_positive_while_input_flows_and_zero_only_when_it_stops():
    """'You never get to 0 unless you stop operating.' One settlement round per
    world tick under a finite budget: while material keeps arriving the account
    never closes; when it stops, it drains."""
    agent = _sched_agent()
    areas = _scenario(agent, n_areas=2, n_tasks=2)
    inner = agent.inner
    flowing = []
    for ep in range(3, 23):
        for a in areas:
            t = agent.s.add_node("CognitiveTask", {
                "status": "pending", "kind": "abs_diff_energy",
                "payload": [1.0, 2.0], "input_epoch": ep, "salience": 0.5,
                "logical_time": ep, "area": "test", "order": 2, "effort": 1})
            inner.add_edge_unchecked(a, "has_task", t)
        r = inner.run_rules_settle(2, 1, False, SCHEDULE_SNAPSHOT)      # EXACTLY ONE round
        flowing.append(r["rounds"][-1]["residual"] if r["rounds"] else 0)
    assert sum(1 for x in flowing if x > 0) >= 0.95 * len(flowing), flowing
    quiet = []
    for _ in range(200):                              # the input STOPS
        r = inner.run_rules_settle(2, 1, False, SCHEDULE_SNAPSHOT)
        quiet.append(r["rounds"][-1]["residual"] if r["rounds"] else 0)
        if quiet[-1] == 0:
            break
    assert quiet[-1] == 0, "a closed account never settled"
    assert len(quiet) <= 50


# --------------------------------------------------------- THE FALSIFIER ------
def test_dropping_the_residual_diverges_from_carrying_it():
    """If SHEDDING the unreached work gave the same answer as CARRYING it, the
    residual accounting would not be real. It must diverge."""
    base, _ = _drive_scheduler(_global)
    diverged = []
    for budget in (1, 2, 4):
        carried, _ = _drive_scheduler(_settle(budget))
        dropped, _ = _drive_scheduler(_settle(budget, drop=True))
        assert carried == base                       # carrying is exact
        if dropped != carried:
            diverged.append(budget)
    assert diverged, (
        "DROP == CARRY at every budget — the residual accounting is not real")


# --------------------------------------- COST ∝ SURPRISE AT THE AREA GRAIN ----
def test_a_quiet_area_does_no_work():
    """An area with no dirty input is skipped entirely: it never appears in a
    round's ledger, so it performs zero rule attempts."""
    agent = _synth(n_areas=8, dirty_areas=1)
    rep = agent.inner.run_rules_settle(0, MAX_ROUNDS, False, SCHEDULE_SNAPSHOT)
    assert len(rep["areas"]) >= 8
    worked = {row["area"] for rd in rep["rounds"] for row in rd["rows"]}
    assert worked == {"pas0"}, worked
    for rd in rep["rounds"]:
        assert rd["dirty_areas"] <= 1


def test_cost_tracks_dirty_areas_not_total_areas():
    """At a FIXED total area count, the work done tracks the DIRTY count. Read
    at the MECHANISM grain (rule attempts) — an async schedule must never be
    gated on wall-clock."""
    n = 16
    attempts = {}
    for d in (1, 2, 4, 8, 16):
        rep = _synth(n_areas=n, dirty_areas=d).inner.run_rules_settle(
            0, MAX_ROUNDS, False, SCHEDULE_SNAPSHOT)
        attempts[d] = _attempts(rep)
    assert attempts[1] > 0
    for a, b in zip((1, 2, 4, 8), (2, 4, 8, 16)):
        assert attempts[a] < attempts[b], attempts
    assert attempts[1] / attempts[16] <= 0.30, attempts


def test_the_fully_async_schedule_also_reaches_a_settled_account():
    """The DEFAULT schedule reads each area's dirty set on the AREA'S OWN clock
    — no barrier anywhere. It is not asserted byte-identical to the committed
    fixpoint (that is the barrier form's job and the measured scope); what IS
    asserted is that it terminates on a genuinely CLOSED account: residual 0,
    and no dirty rule left standing."""
    agent = _sched_agent()
    _scenario(agent)
    agent.inner.run_cognitive_tasks(1)
    rep = agent.inner.run_rules_settle(0, MAX_ROUNDS, False, False)
    assert rep["steps"] > 0
    assert rep["rounds"][-1]["residual"] == 0
    assert not rep["hit_max_rounds"]
    # ...and it is a real fixed point: the committed loop finds nothing to do.
    assert agent.inner.run_rules() == 0


def test_the_area_partition_is_the_seeds_own_metadata_not_an_invention():
    """The partition settlement uses is the `"area"` key the committed seeds
    already carry — this rung made inert scheduling metadata EXECUTABLE, it did
    not invent a taxonomy."""
    agent = _sched_agent()
    areas = dict(agent.inner.rule_areas())
    assert areas["ct_ready_when_dependencies_settle"] == "scheduler"
    assert areas["ct_broadcast_residual_once_per_destination_epoch"] == "scheduler"
