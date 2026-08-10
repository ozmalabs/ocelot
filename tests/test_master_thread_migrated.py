"""The master thread, migrated — run in the WorldAdapter (no CuriousAgent).
Covers tests/test_master_thread.

The master thread is ``init``-shaped: it does almost no cognition itself. Its
job is to MANAGE the other processes (reflexes, threads) — all real thinking
happens INSIDE them. Under the burn discipline that maps cleanly onto the
adapter:

  • THE CLOCK is mechanical bookkeeping — ``master_tick`` advances it and
    surfaces it as the agent's ``tick`` attr so stimulus Terms can read it.
  • A REFLEX is a graph-resident Reflex node carrying a stimulus TERM the
    SUBSTRATE evaluates over the agent node; the firing DECISION is the Term,
    not a Python if/else. Its response is a registered callable (the I/O
    boundary — a side effect that genuinely lives outside the graph).
  • A THREAD is a first-class Thread node (task / priority / state) with an
    external ``step`` callable. The master picks the highest-priority active
    one by a DSL Argmax (the substrate decides), runs it once, and — init
    reaping zombies — CAPTURES any thread whose step raised so the loop
    survives.

So: advance the clock -> the substrate evaluates each reflex stimulus + the
thread-priority argmax -> the adapter runs the chosen side effects and records
the outcome. No agent decision lives in Python.
"""
from __future__ import annotations

from substrate.dsl import Attr, Gt, Lit, Var
from substrate.jsonio import term_to_json
from substrate.world_adapter import WorldAdapter


def _tick_gt_zero():
    """The stimulus Term `agent.tick > 0` — a graph Term the substrate runs."""
    return term_to_json(Gt(Attr(Var("agent"), "tick"), Lit(0)))


def test_master_tick_advances_clock_and_dispatches():
    a = WorldAdapter()
    record = []
    a.register_reflex_response(
        "note", lambda ad: record.append(("reflex", ad.activity_tick)))
    a.install_reflex("tick_witness", _tick_gt_zero(), response="note")

    def step(ad):
        record.append(("thread", ad.activity_tick))
        return "done"

    thread_id = a.fork_thread("witness", priority=1.0, step=step)

    before = a.activity_tick
    dispatch = a.master_tick()

    # the master advanced the clock by exactly one
    assert a.activity_tick == before + 1
    # the master fired reflexes (the stimulus Term tripped in the substrate)
    assert "tick_witness" in dispatch["reflexes_fired"]
    # the master ran the highest-priority active thread (Argmax in the substrate)
    assert dispatch["thread_ran"] == thread_id
    # both ran exactly once — the dispatch record reflects it
    assert ("reflex", before + 1) in record
    assert ("thread", before + 1) in record


def test_master_tick_does_not_deliberate_or_act_in_a_world():
    # the master itself doesn't observe, decide, plan, or score actions —
    # those are jobs for threads/reflexes. master_tick on a fresh adapter with
    # nothing installed should NOT produce world-action side effects.
    a = WorldAdapter()
    a.master_tick()
    a.master_tick()
    a.master_tick()
    # the activity clock advanced; nothing else happened that would require
    # cognition
    assert a.activity_tick == 3
    # the master doesn't fork its own threads — concerns are spawned by
    # whoever drives the adapter
    assert a.threads() == []


def test_init_captures_misbehaving_thread_and_keeps_running():
    # a thread whose step raises shouldn't crash master_tick — the master reaps
    # it (marks it errored, records the failure) and the loop survives
    a = WorldAdapter()

    def crash(_):
        raise RuntimeError("boom from inside the thread")

    bad = a.fork_thread("bad", priority=2.0, step=crash)
    good_calls = []

    def good(_):
        good_calls.append(True)
        return "done"

    ok = a.fork_thread("ok", priority=1.0, step=good)

    out = a.master_tick()
    # the misbehaving thread was captured and recorded
    assert out["thread_captured"] == bad
    assert a.s.node(bad)["attrs"]["state"] == "errored"
    assert "RuntimeError" in a.s.node(bad)["attrs"]["last_error"]
    assert a.s.node(bad)["attrs"]["error_count"] == 1
    # the master loop survives — next tick picks the still-good thread
    out2 = a.master_tick()
    assert out2["thread_ran"] == ok
    assert good_calls == [True]


def test_captured_thread_is_not_picked_again():
    a = WorldAdapter()

    def crash(_):
        raise ValueError("oops")

    a.fork_thread("bad", priority=5.0, step=crash)
    a.master_tick()
    # the misbehaving thread, even at the highest priority, is no longer
    # ``active`` after capture — master_tick won't pick it on subsequent ticks
    out = a.master_tick()
    assert out["thread_ran"] is None
    assert out["thread_captured"] is None       # nothing to capture this time
    # the errored thread is still introspectable by state
    assert len(a.threads("errored")) == 1


def test_master_tick_keeps_running_when_no_threads_are_active():
    a = WorldAdapter()
    out = a.master_tick()
    assert out["thread_ran"] is None
    # but the clock still advanced; reflexes still got a chance (none installed)
    assert a.activity_tick == 1
    assert isinstance(out["reflexes_fired"], list)


# --- extra coverage: the substrate is the decision-maker -------------------

def test_reflex_stimulus_is_a_substrate_term_not_python():
    """The reflex does NOT fire while its stimulus Term is false in the
    substrate, and DOES the moment it's true — the gating is the Term, run in
    Rust, never a Python branch in the adapter."""
    a = WorldAdapter()
    fires = []
    a.register_reflex_response("rec", lambda ad: fires.append(ad.activity_tick))
    # stimulus: agent.tick > 2  (false on ticks 1,2; true from tick 3)
    a.install_reflex("after_two",
                     term_to_json(Gt(Attr(Var("agent"), "tick"), Lit(2))),
                     response="rec")
    for _ in range(4):
        a.master_tick()
    assert fires == [3, 4]   # only once the substrate-evaluated stimulus tripped


def test_reflex_refractory_debounces_firing():
    """A refractory window suppresses re-firing for N ticks — bookkeeping read
    off the Reflex node, the stimulus still a substrate Term."""
    a = WorldAdapter()
    fires = []
    a.register_reflex_response("rec", lambda ad: fires.append(ad.activity_tick))
    a.install_reflex("debounced", _tick_gt_zero(), response="rec",
                     refractory_ticks=2)
    for _ in range(5):
        a.master_tick()
    # ticks 1..5, refractory 2 -> fires at 1, 3, 5
    assert fires == [1, 3, 5]
    rid = a.reflex("debounced")
    assert a.s.node(rid)["attrs"]["fire_count"] == 3


def test_highest_priority_thread_runs_first_each_tick():
    """When several threads are active, the master runs the highest-priority
    one — the pick is a DSL Argmax over the candidates' priority."""
    a = WorldAdapter()
    order = []
    a.fork_thread("low", priority=1.0, step=lambda _: order.append("low"))
    a.fork_thread("high", priority=3.0, step=lambda _: order.append("high"))
    a.fork_thread("mid", priority=2.0, step=lambda _: order.append("mid"))
    # none return "done", so all stay active; each tick takes the current max
    for _ in range(3):
        a.master_tick()
    assert order == ["high", "high", "high"]


def test_completed_thread_drops_out_and_next_priority_takes_over():
    """A thread that returns "done" completes; the next-highest active thread
    is picked on the following tick."""
    a = WorldAdapter()
    runs = []

    def once(name):
        def step(_):
            runs.append(name)
            return "done"
        return step

    a.fork_thread("a", priority=2.0, step=once("a"))
    b = a.fork_thread("b", priority=1.0, step=once("b"))
    a.master_tick()                 # runs a (priority 2), a completes
    out = a.master_tick()           # a is done -> runs b
    assert runs == ["a", "b"]
    assert out["thread_ran"] == b
    assert a.threads() == []        # both done
    assert len(a.threads("done")) == 2


def test_install_reflex_replaces_in_place():
    """Re-installing a reflex by name replaces its stimulus + response without
    duplicating the Reflex node — one node, rewired."""
    a = WorldAdapter()
    hits = {"x": 0, "y": 0}
    a.register_reflex_response("x", lambda _: hits.__setitem__("x", hits["x"] + 1))
    a.register_reflex_response("y", lambda _: hits.__setitem__("y", hits["y"] + 1))
    first = a.install_reflex("r", _tick_gt_zero(), response="x")
    second = a.install_reflex("r", _tick_gt_zero(), response="y")
    assert first == second          # same node, replaced in place
    assert len(a.reflexes()) == 1
    a.master_tick()
    assert hits == {"x": 0, "y": 1}   # only the replacement response fired
