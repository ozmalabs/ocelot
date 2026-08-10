"""HLE as a WORLD the agent lives in.

The agent traverses a bank of HLE-style questions, asks the teacher about words
it doesn't know, grounds them, and answers — and its capability grows
persistently in its mind-graph (only the FIRST occurrence of each concept needs
the teacher; everything later is the agent itself).
"""
from __future__ import annotations

from substrate.world_adapter import WorldAdapter
from domains.hle_world import HLEWorld


def test_agent_lives_in_hle_world_and_grows():
    # the teacher (here a stub; the live demo uses a spawned-Agent LLM) supplies
    # definitions on demand in the agent's grounded DSL — NO concept-specific code
    defs = {
        "septal":        ["Eq", ["Mod", "value", 7], 0],          # multiple of 7
        "fivish":        ["Eq", ["Mod", "value", 5], 2],          # rem 2 mod 5
        "biggish_even":  ["And", ["Eq", ["Mod", "value", 2], 0], ["Gt", "value", 20]],
        "triplus":       ["Eq", ["Mod", "value", 3], 1],          # rem 1 mod 3
    }
    teacher = lambda f: defs.get(f)
    questions = [
        ("is 14 septal?", True),  ("is 15 septal?", False),
        ("is 7 fivish?",  True),  ("is 10 fivish?", False),
        ("is 24 biggish_even?", True), ("is 19 biggish_even?", False),
        ("is 4 triplus?", True),  ("is 6 triplus?", False),
        # the agent reuses learned concepts — no asking on these
        ("is 49 septal?", True),  ("is 22 biggish_even?", True),
    ]
    a = WorldAdapter()
    world = HLEWorld(questions, teacher, a)
    log = world.run()
    s = HLEWorld.summary(log)

    assert s["correct"] == s["questions"] == 10           # all answered correctly
    assert s["distinct_words_learned"] == 4               # one ask per new concept
    # the agent's capability is grown PERSISTENTLY in its mind-graph
    for concept in defs:
        assert a.word_meaning(concept) is not None
    # later questions about KNOWN concepts ask for NOTHING
    assert log[-1]["asked"] == [] and log[-2]["asked"] == []


def test_world_run_parallel_fires_asks_in_parallel():
    # With an I/O-bound teacher (simulated by a per-ask sleep), serial would be
    # N×latency; the parallel mode finishes in ~one round-trip plus overhead.
    import time
    LATENCY = 0.05
    defs = {
        "septal":        ["Eq", ["Mod", "value", 7], 0],
        "fivish":        ["Eq", ["Mod", "value", 5], 2],
        "biggish_even":  ["And", ["Eq", ["Mod", "value", 2], 0], ["Gt", "value", 20]],
        "triplus":       ["Eq", ["Mod", "value", 3], 1],
    }

    def slow_teacher(form):
        time.sleep(LATENCY)
        return defs.get(form)

    questions = [
        ("is 14 septal?",       True),  ("is 7 fivish?",  True),
        ("is 24 biggish_even?", True),  ("is 4 triplus?", True),
        ("is 49 septal?",       True),  ("is 17 fivish?", True),
    ]
    # head-to-head: parallel vs serial on identical work
    a_par = WorldAdapter()
    a_ser = WorldAdapter()
    t0 = time.monotonic()
    log_par = HLEWorld(questions, slow_teacher, a_par).run_parallel()
    t_par = time.monotonic() - t0
    t0 = time.monotonic()
    log_ser = HLEWorld(questions, slow_teacher, a_ser).run()
    t_ser = time.monotonic() - t0

    s_par = HLEWorld.summary(log_par)
    s_ser = HLEWorld.summary(log_ser)
    assert s_par["correct"] == len(questions)
    assert s_ser["correct"] == len(questions)
    # the 4 asks in serial cost ~4·LATENCY; in parallel they overlap. The rest
    # (comprehension, grounding) is the same on both paths.
    saved = t_ser - t_par
    assert saved > 3 * LATENCY * 0.6        # parallel saves most of N·LATENCY


def test_world_run_cooperative_defers_unknowns_keeps_answering():
    # the agent fires an ask for the first unknown, defers that question, and
    # keeps moving — answering subsequent questions whose unknowns have already
    # landed. Slow asks don't stall the main line.
    import time
    LATENCY = 0.05
    defs = {"septal": ["Eq", ["Mod", "value", 7], 0],
            "fivish": ["Eq", ["Mod", "value", 5], 2]}

    def slow_teacher(form):
        time.sleep(LATENCY)
        return defs.get(form)

    # Q1 introduces 'septal' (deferred — slow ask in flight)
    # Q2 introduces 'fivish' (deferred — slow ask in flight)
    # Q3 reuses 'septal' — but Q1 hasn't returned yet
    questions = [
        ("is 14 septal?", True),   ("is 7 fivish?",  True),
        ("is 49 septal?", True),   ("is 17 fivish?", True),
    ]
    a = WorldAdapter()
    world = HLEWorld(questions, slow_teacher, a)
    log = world.run_cooperative()

    s = HLEWorld.summary(log)
    assert s["correct"] == s["questions"] == len(questions)
    # both new concepts fired asks; the agent didn't re-ask the duplicates
    assert sum(1 for e in log if e["deferred"]) == len(questions)   # all needed an ask


def test_cortex_scoped_hle_world_does_not_leak_vocabulary():
    # Two worlds, two cortexes — words taught in one cortex stay in that cortex
    a = WorldAdapter()
    math = a.create_cortex("math")
    other = a.create_cortex("other")
    teach_math = lambda f: {"primal": ["Eq", ["Mod", "value", 2], 0]}.get(f)
    teach_other = lambda f: {"funky": ["Gt", "value", 5]}.get(f)
    HLEWorld([("is 4 primal?", True), ("is 7 primal?", False)],
             teach_math, a).run_cooperative(cortex=math)
    HLEWorld([("is 10 funky?", True), ("is 3 funky?", False)],
             teach_other, a).run_cooperative(cortex=other)
    # each cortex holds only its own vocabulary
    assert a.word_meaning("primal", cortex=math) is not None
    assert a.word_meaning("primal", cortex=other) is None
    assert a.word_meaning("funky", cortex=other) is not None
    assert a.word_meaning("funky", cortex=math) is None
    # the default lexicon was never touched
    assert a.word_meaning("primal") is None
    assert a.word_meaning("funky") is None


def test_router_picks_the_cortex_whose_vocabulary_matches():
    # the entity picks WHICH cortex a question belongs in by lexical overlap
    a = WorldAdapter()
    math = a.create_cortex("math")
    bio = a.create_cortex("biology")
    a.ground_from_spec("septal", ["Eq", ["Mod", "value", 7], 0], cortex=math)
    a.ground_from_spec("cellish", ["Eq", ["Mod", "value", 3], 0], cortex=bio)
    assert a.route_question("is 14 septal?") == math
    assert a.route_question("is 9 cellish?") == bio
    # no overlap → falls back to default
    assert a.route_question("is 5 mysterious?") is None
    assert a.route_question("is 5 mysterious?", default=math) == math


def test_multi_cortex_world_grows_cortices_in_parallel_by_domain():
    a = WorldAdapter()
    math = a.create_cortex("math")
    bio = a.create_cortex("biology")
    # seed each with one domain-specific term so the router has signal
    a.ground_from_spec("septal", ["Eq", ["Mod", "value", 7], 0], cortex=math)
    a.ground_from_spec("cellish", ["Eq", ["Mod", "value", 3], 0], cortex=bio)
    teacher = lambda f: {"fivish":  ["Eq", ["Mod", "value", 5], 2],   # math-ish
                         "organic": ["Gt", "value", 5]}.get(f)        # bio-ish
    qs = [
        ("is 14 septal?",  True),   # math (known)
        ("is 9 cellish?",  True),   # bio (known)
        ("is 49 septal?",  True),   # math (known, reused)
        ("is 12 cellish?", True),   # bio (known, reused)
    ]
    log = HLEWorld(qs, teacher, a).run_multi_cortex()
    assert all(e["correct"] for e in log)
    # each question landed in the right cortex
    by_q = {e["question"]: e["cortex"] for e in log}
    assert by_q["is 14 septal?"]  == math
    assert by_q["is 49 septal?"]  == math
    assert by_q["is 9 cellish?"]  == bio
    assert by_q["is 12 cellish?"] == bio
    # isolation: each cortex holds only its own vocabulary
    assert a.word_meaning("septal",  cortex=math) is not None
    assert a.word_meaning("septal",  cortex=bio)  is None
    assert a.word_meaning("cellish", cortex=bio)  is not None
    assert a.word_meaning("cellish", cortex=math) is None
    # the default lexicon (used by the speech faculty) is untouched
    assert a.word_meaning("septal")  is None
    assert a.word_meaning("cellish") is None


def test_unknown_word_falls_back_to_default_cortex():
    # for a question whose predicate no cortex knows, the agent routes it to the
    # default cortex and learns there — so the default grows for unclassified
    # questions while specialised cortices keep their isolation
    a = WorldAdapter()
    math = a.create_cortex("math")
    bio = a.create_cortex("biology")
    a.ground_from_spec("septal", ["Eq", ["Mod", "value", 7], 0], cortex=math)
    teacher = lambda f: {"fivish": ["Eq", ["Mod", "value", 5], 2]}.get(f)
    log = HLEWorld([("is 7 fivish?", True)], teacher, a).run_multi_cortex(
        default_cortex=math)
    assert log[0]["correct"] is True
    assert log[0]["cortex"] == math                  # routed to the default
    assert a.word_meaning("fivish", cortex=math) is not None    # learned in math
    assert a.word_meaning("fivish", cortex=bio)  is None        # bio is clean


def test_word_meaning_spans_multiple_cortices():
    # word_meaning accepts a LIST of cortexes; first match across the spanned
    # lexicons wins. This is cross-domain LOOKUP.
    a = WorldAdapter()
    math = a.create_cortex("math")
    bio = a.create_cortex("biology")
    a.ground_from_spec("septal", ["Eq", ["Mod", "value", 7], 0], cortex=math)
    a.ground_from_spec("cellish", ["Eq", ["Mod", "value", 3], 0], cortex=bio)
    # span both cortexes for a single lookup
    assert a.word_meaning("septal",  cortex=[math, bio]) is not None
    assert a.word_meaning("cellish", cortex=[math, bio]) is not None
    # the default lexicon still doesn't see them
    assert a.word_meaning("septal")  is None
    assert a.word_meaning("cellish") is None


def test_cross_domain_world_uses_n_lexicons_simultaneously():
    # one bank, mixed math + biology questions; the agent comprehends each one
    # against BOTH cortexes simultaneously and answers correctly.
    a = WorldAdapter()
    math = a.create_cortex("math")
    bio = a.create_cortex("biology")
    a.ground_from_spec("septal", ["Eq", ["Mod", "value", 7], 0], cortex=math)
    a.ground_from_spec("cellish", ["Eq", ["Mod", "value", 3], 0], cortex=bio)
    questions = [
        ("is 14 septal?",  True),    # math
        ("is 9 cellish?",  True),    # bio
        ("is 49 septal?",  True),    # math
        ("is 12 cellish?", True),    # bio
        ("is 7 septal?",   True),    # math
    ]
    teacher = lambda f: None         # nothing to teach; both predicates known
    log = HLEWorld(questions, teacher, a).run_cross_domain(cortexes=[math, bio])
    assert all(e["correct"] for e in log)
    # the cortices stayed ISOLATED — answers came from the right one
    assert a.word_meaning("septal",  cortex=math) is not None
    assert a.word_meaning("septal",  cortex=bio)  is None
    assert a.word_meaning("cellish", cortex=bio)  is not None
    assert a.word_meaning("cellish", cortex=math) is None


def test_cross_domain_learning_routes_unknowns_into_best_cortex():
    # for a NEW word, the agent learns it in the cortex that best matches the
    # question's context — without merging vocabularies
    a = WorldAdapter()
    math = a.create_cortex("math")
    bio = a.create_cortex("biology")
    a.ground_from_spec("septal", ["Eq", ["Mod", "value", 7], 0], cortex=math)
    a.ground_from_spec("cellish", ["Eq", ["Mod", "value", 3], 0], cortex=bio)
    # 'fivish' is unknown to both cortexes; the question's other vocabulary
    # (none) means routing falls back to the default → learning_cortex=math
    teacher = lambda f: {"fivish": ["Eq", ["Mod", "value", 5], 2]}.get(f)
    log = HLEWorld([("is 7 fivish?", True)], teacher, a).run_cross_domain(
        cortexes=[math, bio], learning_cortex=math)
    assert log[0]["correct"] is True
    # the new word landed in math (not bio, not default)
    assert a.word_meaning("fivish", cortex=math) is not None
    assert a.word_meaning("fivish", cortex=bio)  is None
    assert a.word_meaning("fivish") is None


def test_unknown_question_returns_none_when_no_teacher_available():
    a = WorldAdapter()
    world = HLEWorld([("is 14 septal?", True)], teacher=lambda f: None, agent=a)
    log = world.run()
    assert log[0]["answer"] is None                       # the agent honestly missed
