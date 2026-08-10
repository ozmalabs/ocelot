"""Meta-cognitive structure, migrated — run on the seed-booted WorldAdapter
(no CuriousAgent). Covers tests/test_meta_cognitive.

The entity manages its own COGNITIVE STRUCTURE — it instates specialised
CORTICES for new domains (each with its own isolated sub-lexicon) and forks
concurrent THREADS for parallel concerns. Both are graph-resident nodes the
adapter creates / lists / transitions: Cortex + Lexicon + Sign nodes wired by
`lexicon` / `entry` / `denotes` edges, and Thread nodes wired by `has_thread`
/ `child_thread` / `in_cortex` edges. Every method here is mechanical I/O +
bookkeeping over those nodes — the same structure the old CuriousAgent kept on
its mind_graph, here on the Rust substrate. No agent decision lives in Python.

  • A CORTEX is a Cortex node owning its own Lexicon (via a `lexicon` edge); a
    taught word is a Sign in that lexicon (an `entry`), denoting a Term
    subgraph. The DEFAULT lexicon (used by the speech faculty) is the one with
    NO owning cortex — cortices live ALONGSIDE it.
  • Word routing isolates vocabularies: looking a word up is SCOPED to a
    lexicon, so `primal` grounded in the math cortex is invisible to the
    default lexicon and vice-versa.
  • A THREAD is a first-class Thread node (task / priority / state); it can be
    rooted in a cortex (`in_cortex`), forked from a parent (`child_thread`), or
    advanced one cooperative step at a time by priority Argmax (`tick_threads`).
  • A genuinely PARALLEL OS-level thread runs its worker off the main thread
    and delivers its result back into the Thread node on join.
"""
from __future__ import annotations

from substrate.world_adapter import WorldAdapter


def test_entity_creates_specialised_cortices():
    a = WorldAdapter()
    math = a.create_cortex("math", "groups, linear algebra, number theory")
    poetry = a.create_cortex("poetry", "rhythm, meter, image")
    # both are first-class graph nodes the entity can list
    assert set(a.cortexes()) == {math, poetry}
    # each cortex owns its own (initially empty) lexicon, isolated
    assert a.cortex_lexicon(math) is not None
    assert a.cortex_lexicon(poetry) is not None
    assert a.cortex_lexicon(math) != a.cortex_lexicon(poetry)
    # the autopoietic loop's default lexicon (used by the speech faculty) is
    # NOT a cortex lexicon — cortices live alongside, they don't replace it
    a._ensure_lexicon()
    default = a._ensure_lexicon()
    assert default != a.cortex_lexicon(math)
    assert default != a.cortex_lexicon(poetry)


def test_entity_forks_and_manages_threads():
    a = WorldAdapter()
    math = a.create_cortex("math")
    # two concurrent concerns the entity pursues
    t_q = a.fork_thread("answer the current HLE question", priority=1.0)
    t_inv = a.fork_thread("investigate Grigorchuk subgroups",
                          priority=0.8, cortex=math)
    assert set(a.threads()) == {t_q, t_inv}
    # the investigation runs in the math cortex
    assert a.thread_cortex(t_inv) == math
    assert a.thread_cortex(t_q) is None
    # threads close when their concern resolves
    a.complete_thread(t_q)
    assert a.threads("active") == [t_inv]
    assert a.threads("done") == [t_q]


def test_threads_can_fork_children():
    # a thread can fork a SUB-thread (an entity can recursively subdivide a
    # concern into parallel sub-concerns)
    a = WorldAdapter()
    parent = a.fork_thread("read paper on growth groups")
    child = a.fork_thread("look up 'self-similar' first", parent=parent)
    # parent -> child edge captured in the graph
    assert child in a.child_threads(parent)


# --- Extension 1: cortex routing ---------------------------------------------

def test_cortex_routing_isolates_vocabularies():
    a = WorldAdapter()
    math = a.create_cortex("math")
    # ground 'primal' in the math cortex only
    a.ground_from_spec("primal", ["Eq", ["Mod", "value", 2], 0], cortex=math)
    assert a.word_meaning("primal", cortex=math) is not None
    assert a.word_meaning("primal") is None                  # not in default
    # default learning is unaffected
    a.ground_from_spec("trip", ["Eq", ["Mod", "value", 3], 0])
    assert a.word_meaning("trip") is not None
    assert a.word_meaning("trip", cortex=math) is None       # isolated the other way


# --- Extension 2: thread argmax (cooperative interleaving) ------------------

def test_tick_threads_interleaves_by_priority():
    a = WorldAdapter()
    counts = {"hi": 0, "lo": 0}

    def hi_step(_):
        counts["hi"] += 1
        return "done" if counts["hi"] >= 3 else None

    def lo_step(_):
        counts["lo"] += 1
        return "done" if counts["lo"] >= 3 else None

    a.fork_thread("hi", priority=2.0, step=hi_step)
    a.fork_thread("lo", priority=0.5, step=lo_step)
    # the higher-priority thread runs first; after it completes the other takes over
    for _ in range(6):
        a.tick_threads()
    assert counts == {"hi": 3, "lo": 3}
    assert a.threads("active") == []
    assert len(a.threads("done")) == 2


# --- Extension 3: genuinely parallel OS-level threads -----------------------

def test_spawn_python_thread_runs_in_parallel():
    import time
    a = WorldAdapter()

    def work(label):
        time.sleep(0.05)              # I/O-style wait — GIL releases
        return f"done:{label}"

    t0 = time.monotonic()
    threads = [a.spawn_python_thread(work, args=(c,)) for c in ("a", "b", "c")]
    results = [a.join_thread(t) for t in threads]
    elapsed = time.monotonic() - t0
    # all three completed, with results delivered to their Thread nodes
    assert results == ["done:a", "done:b", "done:c"]
    for t in threads:
        assert a.s.node(t)["attrs"].get("state") == "done"
    # genuinely parallel: well under the sum (0.15s) — would be >=0.15s if serial
    assert elapsed < 0.12
