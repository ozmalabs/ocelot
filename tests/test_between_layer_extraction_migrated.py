"""Between-layer extraction — tests.

See docs/research/psychology_affect/BETWEEN_LAYER_EXTRACTION_PREREG.md and
scripts/between_layer_extraction_measure.py.

The substrate test suite runs WITHOUT torch — so the torch-dependent tests
skip gracefully, and the KEY invariant (importing the module does not require
torch — lazy import) is asserted unconditionally. The pure-python ranking
logic is tested on synthetic arrays. When run with the external venv python
(torch present), the real-model tests also execute.
"""

import os
import sys

import pytest

sys.path.insert(0, "runners/dsl/python")
sys.path.insert(0, ".")

# CRITICAL: this import must succeed WITHOUT torch installed (lazy import).
from domains import between_layer_extraction as ble  # noqa: E402

MODEL = "/applications/data/model_graph_work/Qwen3-1.7B"
_HAVE = ble.have_torch() and os.path.isdir(MODEL)
_need = pytest.mark.skipif(not _HAVE, reason="torch/Qwen3-1.7B absent")


# ---- lazy-import invariant + pure-python logic (unconditional) ---------

def test_module_imports_without_torch():
    """Importing the module must not require torch — the substrate import
    surface is unchanged when torch is absent. (This test file already
    imported it at module load; reaching here proves it.)"""
    assert hasattr(ble, "forward_trace")
    assert hasattr(ble, "logit_lens")
    assert callable(ble.have_torch)


def test_rank_in_pure_python():
    # scores: index 2 is the max -> rank 0; index 0 is min -> rank last
    scores = [0.1, 0.5, 0.9, 0.3]
    assert ble._rank_in(scores, 2) == 0
    assert ble._rank_in(scores, 1) == 1
    assert ble._rank_in(scores, 0) == 3


def test_rank_in_matches_argsort():
    import random
    rng = random.Random(0)
    scores = [rng.random() for _ in range(50)]
    tgt = 17
    # rank == number of scores strictly greater than scores[tgt]
    expected = sum(1 for s in scores if s > scores[tgt])
    assert ble._rank_in(scores, tgt) == expected


# ---- real-model tests (skip without the venv torch + model) ------------

@_need
def test_forward_trace_deltas_grow_with_depth():
    tm = ble.load_traced(MODEL)
    tr = ble.forward_trace(tm, "The capital of France is")
    d = tr["deltas"]
    assert len(d) == tm.n_layers
    assert d[-1] > d[0]          # model commits its work late


@_need
def test_logit_lens_resolves_answer_late():
    tm = ble.load_traced(MODEL)
    tr = ble.forward_trace(tm, "The capital of France is")
    aid = tm.tok(" Paris", add_special_tokens=False)["input_ids"][0]
    ranks = ble.answer_rank_by_layer(tm, tr["hidden"], aid)
    assert ranks[-1] == 0                      # answer is top at the final layer
    assert ranks[0] > 100                       # and NOT near the top early
    # resolution depth is in the late band
    res = next((L for L, r in enumerate(ranks) if r == 0), None)
    assert res is not None and res > tm.n_layers // 2


# ---- default == today ---------------------------------------------------

def test_default_equals_today_so_unchanged():
    import hashlib
    so = "runners/dsl/python/substrate_rs/_native.abi3.so"
    if not os.path.exists(so):
        return
    md5 = hashlib.md5(open(so, "rb").read()).hexdigest()
    assert md5 == "7efe75eba05b006cafd15dbb4b7da246", md5
