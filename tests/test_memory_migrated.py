"""bigville cognitive C3 (block 326000): episodic memory with appraisal, decay,
reconsolidation (Tulving + OCC + ACT-R). Gates mirror BIGVILLE_MEMORY_PREREG.md.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_memory_world import BigvilleMemoryWorld   # noqa: E402


# ------------------------------------------------------ G-forgetting-curve (headline)
def test_activation_decays_and_recall_reboosts():
    w = BigvilleMemoryWorld(retention=0.6)
    i = w.present_event("Ada", topic="work", valence=1.0) if w.add_agent("Ada", cares_about="work") or True else 0
    a0 = w.activation("Ada", i)
    acts = [a0]
    for _ in range(4):
        w.pass_time()
        acts.append(w.activation("Ada", i))
    assert all(acts[k + 1] < acts[k] for k in range(len(acts) - 1)), f"activation must decay monotonically: {acts}"
    faded = w.activation("Ada", i)
    w.recall("Ada", i, context_target=1.0)
    assert w.activation("Ada", i) > faded, "recall reboosts activation (ACT-R rise)"


# ------------------------------------------------------ G-mood-from-active-traces (headline)
def test_mood_tracks_the_salient_trace_not_the_last_event():
    w = BigvilleMemoryWorld(retention=0.6)
    w.add_agent("Ada", cares_about="work", mood_thr=0.25)
    i0 = w.present_event("Ada", topic="work", valence=1.0)
    assert w.mood("Ada") == 1.0, "a fresh strong trace sets mood"
    for _ in range(4):
        w.pass_time()
    assert w.mood("Ada") == 0.0, "once the trace fades below threshold, mood returns to neutral"
    # a newer salient trace takes over mood
    w.present_event("Ada", topic="work", valence=-1.0)
    assert w.mood("Ada") == -1.0, "the new salient memory dominates mood"


# ------------------------------------------------------ G-appraisal-is-goal-relative (OCC)
def test_the_same_event_is_appraised_by_concern():
    w = BigvilleMemoryWorld()
    w.add_agent("Worker", cares_about="work")
    w.add_agent("Idler", cares_about="play")
    w.present_event("Worker", topic="work", valence=-1.0)
    w.present_event("Idler", topic="work", valence=-1.0)
    assert abs(w.appraisal("Worker", 0)) > abs(w.appraisal("Idler", 0)), \
        "the same event bites harder for whoever cares about its topic"
    assert w.appraisal("Worker", 0) == -1.0 and w.appraisal("Idler", 0) == -0.3


# ------------------------------------------------------ G-reconsolidation-changes-the-trace
def test_recall_reconsolidates_the_appraisal():
    w = BigvilleMemoryWorld()
    w.add_agent("Ada", cares_about="work")
    i = w.present_event("Ada", topic="work", valence=1.0)
    before = w.appraisal("Ada", i)
    w.recall("Ada", i, context_target=-1.0)          # recall it in a bad light
    after = w.appraisal("Ada", i)
    assert after < before, f"a memory recalled in a new context is re-encoded: {before} -> {after}"


# ------------------------------------------------------ G-no-decay-collapses-it (falsifier)
def test_without_decay_ancient_traces_dominate_forever():
    w = BigvilleMemoryWorld(retention=1.0)   # no forgetting
    w.add_agent("Ada", cares_about="work")
    i = w.present_event("Ada", topic="work", valence=1.0)
    for _ in range(6):
        w.pass_time()
    assert w.activation("Ada", i) == 1.0, "no decay -> the trace never fades"
    assert w.mood("Ada") == 1.0, "and the ancient memory dominates mood forever"


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_decides_memory():
    src = open(os.path.join(_ROOT, "worlds", "bigville_memory_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_memory.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"mem_appraise", "mem_decay", "mem_recall", "mem_mood"} <= names, names
    assert "Argmax" in json.dumps(seed), "mood must be an Argmax collapse over traces in the seed"
