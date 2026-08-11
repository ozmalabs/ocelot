"""test_prog_read_selfimprove_migrated — ARC6 A25 gates: the `prog_read`
sibling of `tests/test_prog_synthesis_selfimprove_migrated.py`'s headline
scene (PROGRAM_SYNTHESIS_ARC6_PREREG.md Amendment A25;
PROGRAM_SYNTHESIS_ARC6_PROGREAD_SELFIMPROVE.md).

Background (the investigation this amendment closed a residual from,
docs/research/program_synthesis/PROGRAM_SYNTHESIS_SELF_IMPROVEMENT_WIRING_
INVESTIGATION.md §2, §4): `code_write` StandingConcerns are routed by
`_concern_tick` (scripts/jabberwock_daemon.py) DIRECTLY into
`domains.code_write_growth.work_on_code_write_gap`, never the generic
`induce_concern`/`ground_concern` capability-axis composer. `prog_read`
concerns, the sibling gap kind `seeds/prog_read_gap.json`'s
`note_prog_read_gap` mints for a blocked source read (Lambda, varargs,
...), had NEVER been exercised through `promote_self_concern` by any test
before this amendment — the investigation predicted (reasoned, not
measured) it would fall through to the generic `comprehend_first` default
and produce something "structurally mismatched."

AR25a measured this LIVE, for real, before any fix: the generic composer
does not merely do nothing — it MINTS an inert, misleadingly-named rule
(`comprehend_describe_directive_<tag>`, matched on a literal Mention text
`'describe'` about a `Scene` node — vision-domain vocabulary, structurally
unrelated to program reading) and reports `{"grounded": True, ...}` with
NO record of the mismatch anywhere (`_concern_tick` discards
`ground_concern`'s return value for every kind but `code_write`). This is
WORSE than the investigation's own "plausible... degrades gracefully"
possibility — it is a confirmed, actively wrong outcome, not a graceful
null.

AR25b/AR25c: the population of `prog_read` blockers (grep-verified: zero
`Lambda`/`Yield`/`Match`/... hits anywhere in `runners/dsl/src/*.rs`)
genuinely needs new Rust engine Term/IR-variant coverage to CLOSE for
real — NO-GO on that half, named precisely per blocker
(`domains/prog_read_growth._BLOCKER_RUST_NEED`). But the WIRING itself —
stop the wrong generic composer, route to a dedicated pipeline, record an
honest per-blocker reason — is closeable at the seed/adapter grain,
mirroring `code_write`'s own dedicated-routing shape exactly: GO on that
half. These tests demonstrate the fix live: a `prog_read` StandingConcern
now routes to `_process_prog_read_standing`
(`domains.prog_read_growth.work_on_prog_read_gap`), mints NO
Experiment/CapabilityAxis/Observation, and the concern's own
`experiments_exhausted`/`exhausted_note` (via the new
`note_prog_read_composition_exhausted` seed rule,
`seeds/prog_read_gap.json` v1.1.0) names the specific missing Rust
primitive — never a flat "unsupported".

Run (worktree engine discipline — the P1 note):
    pytest tests/test_prog_read_selfimprove_migrated.py --confcutdir=. -q
"""
from __future__ import annotations

import os
import sys
import tempfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs as srs  # noqa: E402


def _prog_eval_live() -> bool:
    s = srs.Substrate()
    try:
        s._inner.evaluate({"type": "ProgEval",
                           "prog": {"type": "ProgSeq", "stmts": []},
                           "env": None, "oracles": None, "fuel": 10,
                           "field": ""}, {})
        return True
    except ValueError as e:
        if "UnknownTermType" in str(e):
            return False
        raise


if not _prog_eval_live():
    pytest.skip(
        "ProgEval Term not present in the installed substrate_rs binary — "
        "rebuild runners/dsl. Honest skip, not a fake pass.",
        allow_module_level=True)

jd = pytest.importorskip("jabberwock_daemon")

from substrate.boot_all import load_all_seeds       # noqa: E402
from substrate.world_adapter import WorldAdapter     # noqa: E402
import domains.file_ingest as fi                     # noqa: E402
import domains.prog_read_growth as prg               # noqa: E402


@pytest.fixture(autouse=True)
def _no_real_seed_writes(monkeypatch):
    monkeypatch.setenv("OZMA_SEED_PERSIST_DISABLED", "1")


PY_TWO_FUNCTIONS = """
def add_one(x):
    return x + 1

def uses_lambda(v):
    f = lambda y: y + 1
    return f(v)
"""


def _ingest_source_text(agent, text: str, filename: str) -> dict:
    suffix = os.path.splitext(filename)[1]
    with tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False,
                                     encoding="utf-8") as f:
        f.write(text)
        path = f.name
    try:
        return fi.ingest_file(agent, path, filename=filename)
    finally:
        os.unlink(path)


def _boot_with_blocked_lambda_gap():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    _ingest_source_text(agent, PY_TWO_FUNCTIONS, "two_fns.py")
    agent.comprehend()
    concerns = [c for c in jd.list_self_concerns(agent) if c.get("kind") == "prog_read"]
    assert len(concerns) == 1
    assert concerns[0]["content"] == "python read blocked: Lambda"
    return agent, concerns[0]


# =========================================================================== #
#  (1) AR25a/AR25c HEADLINE — promote routes to the DEDICATED pipeline, not
#      the generic composer; the outcome is recorded honestly, per-blocker.
# =========================================================================== #
def test_prog_read_gap_promotes_and_routes_to_dedicated_pipeline():
    agent, concern = _boot_with_blocked_lambda_gap()

    res = jd.promote_self_concern(agent, str(concern["id"]))
    assert res["ok"], res
    assert res["kind"] == "prog_read"
    # the routing fix: prog_read gets its OWN pipeline tag, not comprehend_first.
    assert res["pipeline"] == "prog_read"

    standing = [n for n in agent.s.nodes("StandingConcern")
               if agent.s.node(n)["attrs"].get("kind") == "prog_read"]
    assert len(standing) == 1
    sat_before = agent.s.node(standing[0])["attrs"]
    assert sat_before["status"] == "pending"
    assert "prog_read_compose_ok" not in sat_before

    jd._concern_tick(agent)

    sat = agent.s.node(standing[0])["attrs"]
    assert sat["status"] == "processed"
    # the mechanical outcome datum _process_prog_read_standing records —
    # honestly exhausted (no seed-level close for Lambda exists today).
    assert sat.get("prog_read_compose_ok") == 0.0
    reason = sat.get("prog_read_compose_reason", "")
    assert "Lambda" in reason
    assert "closure" in reason.lower()
    assert "Rust-engine-level" in reason

    # the seeded note_prog_read_composition_exhausted rule reads the fact
    # and marks the StandingConcern exhausted — the human-readable trail
    # reflective_faculty._run_self_improvement_status already surfaces for
    # every other kind.
    agent.s._inner.run_rules(400000)
    sat2 = agent.s.node(standing[0])["attrs"]
    assert sat2.get("experiments_exhausted") is True
    assert "Lambda" in sat2.get("exhausted_note", "")


# =========================================================================== #
#  (2) THE MEASURED BUG THE FIX CLOSES — no Experiment/CapabilityAxis/
#      Observation gets minted for a promoted prog_read concern any more
#      (before the fix, AR25a measured a live CapabilityAxis + a permanently
#      installed, never-firing Rule minted for exactly this scene).
# =========================================================================== #
def test_no_capability_axis_or_experiment_minted_for_prog_read_standing():
    agent, concern = _boot_with_blocked_lambda_gap()
    res = jd.promote_self_concern(agent, str(concern["id"]))
    assert res["ok"], res
    tag = f"promoted_self_concern_{concern['id']}"

    axes_before = set(agent.s.nodes("CapabilityAxis"))
    obs_before = set(agent.s.nodes("Observation"))

    jd._concern_tick(agent)

    assert agent.s.nodes("Experiment") == []
    new_axes = set(agent.s.nodes("CapabilityAxis")) - axes_before
    new_obs = set(agent.s.nodes("Observation")) - obs_before
    # NOTHING new minted with this concern's own tag as capability_keys/key —
    # the generic induce_concern/ground_concern path is never invoked for
    # prog_read any more.
    for n in new_axes:
        assert list(agent.s.node(n)["attrs"].get("capability_keys") or []) != [tag]
    for n in new_obs:
        assert list(agent.s.node(n)["attrs"].get("key") or []) != [tag]


# =========================================================================== #
#  (3) work_on_prog_read_gap — the per-blocker Rust-primitive naming, unit
#      grain, including the classified prefixes (RecvMethod:/OpExt:/...) and
#      a multi-blocker request.
# =========================================================================== #
def test_work_on_prog_read_gap_names_the_rust_primitive_per_blocker():
    out = prg.work_on_prog_read_gap(None, "python read blocked: KwargsCall,Lambda")
    assert out["ok"] is False
    assert out["frame"] == "python"
    assert out["blockers"] == ["KwargsCall", "Lambda"]
    assert "closure" in out["needs"]["Lambda"].lower()
    assert "keyword-argument" in out["needs"]["KwargsCall"].lower()
    assert "KwargsCall" in out["reason"] and "Lambda" in out["reason"]
    assert "Rust-engine-level" in out["reason"]


def test_work_on_prog_read_gap_classifies_recvmethod_and_opext_prefixes():
    out = prg.work_on_prog_read_gap(None, "python read blocked: RecvMethod:append")
    assert out["ok"] is False
    assert "write-back" in out["needs"]["RecvMethod:append"].lower()

    out2 = prg.work_on_prog_read_gap(None, "lua read blocked: OpExt:LShift")
    assert out2["ok"] is False
    assert "operator" in out2["needs"]["OpExt:LShift"].lower()


def test_work_on_prog_read_gap_generic_fallback_for_unnamed_blocker():
    out = prg.work_on_prog_read_gap(None, "python read blocked: SomeBrandNewBlocker")
    assert out["ok"] is False
    assert "no known engine correspondence" in out["needs"]["SomeBrandNewBlocker"]


def test_work_on_prog_read_gap_no_blocker_named():
    out = prg.work_on_prog_read_gap(None, "not a recognised content string")
    assert out["ok"] is False
    assert out["blockers"] == []


# =========================================================================== #
#  (4) pending_prog_read_gaps — the pending_code_write_gaps precedent,
#      kind-swapped.
# =========================================================================== #
def test_pending_prog_read_gaps_reader():
    agent, concern = _boot_with_blocked_lambda_gap()
    gaps = prg.pending_prog_read_gaps(agent)
    assert len(gaps) == 1
    assert gaps[0]["content"] == "python read blocked: Lambda"
    assert gaps[0]["kind"] == "prog_read"
