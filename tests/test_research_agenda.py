"""test_research_agenda — SELF-IMPROVEMENT #5: THE RESEARCH-AGENDA DRIVER.

The driver CHAINS the four held self-improvement faculties into one autonomous
CYCLE the agent runs on ITSELF:

  PERCEIVE (#1) -> PRIORITIZE -> per gap [ ROUTE (graph dispatch by kind) ->
  FILL (#3 knowledge / #4 capability) -> VERIFY (#2) -> accept/open ] -> LOOP
  -> STOP (queue drained).

Gates, discriminative, donkey=0:

  END-TO-END CYCLE (headline) — a battery of gaps (knowledge-kind + capability-kind
    + a fake), each ROUTED to the right filler, VERIFIED, the real fills ACCEPTED
    (closed) and the fake REJECTED (left open), driven until the queue drains.

  ROUTE-BY-KIND (discriminative) — a knowledge gap -> acquisition, a capability gap
    -> substrate_extension, decided by the gap kind via the GRAPH dispatch
    (route_pick Program over GapRouteCue), not a Python branch. Same driver,
    different filler by kind.

  VERIFY-GATES-THE-CYCLE — a fake/incomplete fill is REJECTED by #2 and its gap
    stays OPEN (not falsely closed).

  CLEAN STOP — the loop terminates (queue drained); no infinite loop.

  GRAPH-NATIVE audit — the route-by-kind is the seeded Program; the driver calls
    the held faculties + reads their verdicts back; no new kind->filler decision in
    Python (source + spy audit).

  NO REGRESSION — the four faculties + the composer route are unbroken.
"""
from __future__ import annotations

import inspect
import os
import sys
import tempfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import concept_graph as cg
from domains import research_agenda as ra
from domains import reflective_faculty as rf


# A real reference document — the extractor reads it, never invents (donkey=0).
CRYPTO_DOC = (
    "In cryptography, the main primitives are: cipher, key, plaintext, ciphertext, hash function, "
    "digital signature, key exchange, and message authentication code. Other concepts include: nonce, "
    "salt, initialization vector, and block cipher. A cipher transforms plaintext into ciphertext.")


def _fresh():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    cg._CACHE.clear()
    return a


def _knowledge_gap(a, *, topic="cryptography", source=CRYPTO_DOC, faculty="cryptography_knowledge"):
    """A KNOWLEDGE gap: names a thin/ungrounded knowledge DOMAIN (concept_graph's
    is_knowledge_gap true) with a fed reference source to read."""
    at = {"faculty": faculty, "topic": topic,
          "observation": [["capability_gap", "self", topic]], "status": "perceived"}
    if source is not None:
        at["source_text"] = source
    return a.s.add_node("CapabilityGap", at)


def _capability_gap(a, faculty="input_handling"):
    """A CAPABILITY gap: a behavioral faculty need solvable by a COMPOSITION of held
    primitives (classify -> route -> finalize). No knowledge domain."""
    return a.s.add_node("CapabilityGap", {
        "faculty": faculty,
        "observation": [["classify the item", "self", "input"],
                        ["route to a handler", "input", "handler"],
                        ["mark handled", "handler", "done"]],
        "status": "perceived"})


def _tmp():
    return tempfile.mkdtemp(prefix="ra_seed_")


# ===========================================================================
# END-TO-END CYCLE — the headline: the agent runs the session's meta-process
# on ITSELF, on a small scale.
# ===========================================================================
def test_end_to_end_cycle_headline():
    a = _fresh()
    _knowledge_gap(a)                                    # knowledge -> acquire -> close
    _capability_gap(a)                                   # capability -> compose -> close
    _knowledge_gap(a, topic="zzq_no_such_domain_qzz",    # fake: no source -> reject -> open
                   source=None, faculty="zzq_knowledge")
    out = ra.run_cycle(a, seeds_dir=_tmp())

    # every perceived gap was processed exactly once, the queue drained, no loop.
    assert out["perceived"] == 3
    assert out["iterations"] == 3
    assert out["drained"] is True

    by_fac = {r["faculty"]: r for r in out["processed"]}
    # the KNOWLEDGE fill routed to acquisition, verified, CLOSED.
    kg = by_fac["cryptography_knowledge"]
    assert kg["kind"] == "knowledge" and kg["filler"] == "acquisition"
    assert kg["accepted"] is True and kg["status"] == "closed"
    # the CAPABILITY fill routed to substrate_extension, verified, CLOSED.
    cgp = by_fac["input_handling"]
    assert cgp["kind"] == "capability" and cgp["filler"] == "substrate_extension"
    assert cgp["accepted"] is True and cgp["status"] == "closed"
    # the FAKE knowledge gap (no source) was REJECTED by #2 -> stays OPEN.
    fk = by_fac["zzq_knowledge"]
    assert fk["kind"] == "knowledge" and fk["filler"] == "acquisition"
    assert fk["accepted"] is False and fk["status"] == "open"

    # the final resting state: exactly the real fills closed, the fake left open.
    assert len(out["closed"]) == 2 and len(out["open"]) == 1


# ===========================================================================
# ROUTE-BY-KIND — same driver, different filler by kind, via the GRAPH dispatch.
# ===========================================================================
def test_route_by_kind_is_graph_dispatch():
    a = _fresh()
    # the route decision is the seeded route_pick Program, evaluated in Rust.
    assert ra.route(a, "knowledge") == "acquisition"
    assert ra.route(a, "capability") == "substrate_extension"
    # an unknown kind matches no GapRouteCue -> no filler (honest None, not a default).
    assert ra.route(a, "not_a_kind") is None


def test_route_uses_seeded_program_not_python(monkeypatch):
    # SPY: prove route() dispatches through the graph-resident route_pick Program
    # (rf._load_program over the seed), not a Python kind->filler branch.
    a = _fresh()
    ra._ensure_dispatch_seed(a)
    seen = {}
    real = rf._load_program

    def spy(sub, name):
        if name == "route_pick":
            seen["called"] = True
        return real(sub, name)

    monkeypatch.setattr(rf, "_load_program", spy)
    assert ra.route(a, "knowledge") == "acquisition"
    assert seen.get("called") is True


def test_kind_read_off_held_faculty_signals():
    a = _fresh()
    # KNOWLEDGE iff the gap names a domain that is_knowledge_gap (concept_graph's
    # own coverage read) — a thin/ungrounded dimension.
    kg = _knowledge_gap(a)
    cgp = _capability_gap(a)
    assert ra.classify_kind(a, kg) == "knowledge"
    assert ra.classify_kind(a, cgp) == "capability"
    # the kind is written onto the gap node as an attr (the token the dispatch reads).
    assert a.s.node(kg)["attrs"]["kind"] == "knowledge"
    assert a.s.node(cgp)["attrs"]["kind"] == "capability"


def test_same_driver_routes_both_kinds():
    # DISCRIMINATIVE: the SAME process_gap routes a knowledge gap to acquisition and
    # a capability gap to substrate_extension — the ONLY difference is the gap kind.
    a = _fresh()
    kg = _knowledge_gap(a)
    cgp = _capability_gap(a)
    rk = ra.process_gap(a, kg, seeds_dir=_tmp())
    rc = ra.process_gap(a, cgp, seeds_dir=_tmp())
    assert rk["filler"] == "acquisition" and rc["filler"] == "substrate_extension"
    assert rk["filler"] != rc["filler"]                  # separated cleanly by kind


# ===========================================================================
# VERIFY-GATES-THE-CYCLE — a fill that fails #2 leaves its gap OPEN.
# ===========================================================================
def test_verify_gates_fake_knowledge_fill_stays_open():
    a = _fresh()
    # a knowledge gap with NO readable source: acquisition cannot fill it (honest
    # null), so #2's control (region must be edge-bearing) fails -> REJECTED -> open.
    fk = _knowledge_gap(a, topic="zzq_no_such_domain_qzz", source=None, faculty="zzq_knowledge")
    rec = ra.process_gap(a, fk, seeds_dir=_tmp())
    assert rec["accepted"] is False
    assert rec["status"] == "open"
    assert a.s.node(fk)["attrs"]["status"] == "open"     # the gap is NOT falsely closed


def test_verify_gates_incomplete_capability_fill_stays_open():
    a = _fresh()
    # a capability gap that grounds to only classify+route (NO finalize): a real
    # 2-rule composition that does NOT set handled -> #2's positive case fails -> open.
    partial = a.s.add_node("CapabilityGap", {
        "faculty": "partial_pipe",
        "observation": [["classify the item", "self", "input"],
                        ["route to a handler", "input", "handler"]],
        "status": "perceived"})
    rec = ra.process_gap(a, partial, seeds_dir=_tmp())
    assert rec["kind"] == "capability" and rec["filler"] == "substrate_extension"
    assert rec["accepted"] is False and rec["status"] == "open"


def test_verify_accepts_real_knowledge_fill():
    a = _fresh()
    kg = _knowledge_gap(a)
    rec = ra.process_gap(a, kg, seeds_dir=_tmp())
    assert rec["accepted"] is True and rec["status"] == "closed"
    # the region really became edge-bearing (the coverage read, #3's own signal).
    from domains import gap_driven_acquisition as gda
    assert gda.coverage(a, "cryptography")["bag"] >= 8


# ===========================================================================
# CLEAN STOP — the loop terminates at a resting point.
# ===========================================================================
def test_clean_stop_drains_the_queue():
    a = _fresh()
    _knowledge_gap(a)
    _capability_gap(a)
    out = ra.run_cycle(a, seeds_dir=_tmp())
    assert out["drained"] is True
    # no perceived gap remains — every gap reached a terminal status.
    remaining = [n for n in a.s.nodes("CapabilityGap")
                 if a.s.node(n)["attrs"].get("status", "perceived") == "perceived"]
    assert remaining == []


def test_clean_stop_on_empty_queue():
    # no gaps at all -> the loop stops immediately (a clean resting point, not a hang).
    a = _fresh()
    out = ra.run_cycle(a, seeds_dir=_tmp())
    assert out["perceived"] == 0 and out["iterations"] == 0 and out["drained"] is True


def test_re_running_a_drained_cycle_is_stable():
    # after a cycle drains, re-running finds no perceived gap -> 0 iterations (the
    # closed/open statuses persist; the loop cannot re-grind).
    a = _fresh()
    _knowledge_gap(a)
    _capability_gap(a)
    ra.run_cycle(a, seeds_dir=_tmp())
    again = ra.run_cycle(a, seeds_dir=_tmp())
    assert again["iterations"] == 0 and again["drained"] is True


# ===========================================================================
# PRIORITIZE — the queue is ordered by a residual salience read off graph state.
# ===========================================================================
def test_prioritize_orders_by_salience():
    a = _fresh()
    kg = _knowledge_gap(a)
    cgp = _capability_gap(a)
    ordered = ra.prioritize(a, [kg, cgp])
    # both carry a written salience attr (the shortfall-residual shape, Rust-evaluated).
    assert "salience" in a.s.node(kg)["attrs"]
    assert "salience" in a.s.node(cgp)["attrs"]
    # a capability behavioral failure (maximally ungrounded) is at least as salient
    # as a thin-but-slightly-grounded knowledge dimension.
    assert a.s.node(cgp)["attrs"]["salience"] >= a.s.node(kg)["attrs"]["salience"]
    assert ordered[0] in (kg, cgp)


# ===========================================================================
# GRAPH-NATIVE audit — the route-by-kind is graph data; the driver chains held
# faculties; no new kind->filler decision in Python.
# ===========================================================================
def test_route_by_kind_is_graph_data():
    a = _fresh()
    ra._ensure_dispatch_seed(a)
    # the dispatch is GapRouteCue nodes + a route_pick Program, all in the graph.
    cues = {a.s.node(n)["attrs"]["kind"]: a.s.node(n)["attrs"]["filler"]
            for n in a.s.nodes("GapRouteCue")}
    assert cues.get("knowledge") == "acquisition"
    assert cues.get("capability") == "substrate_extension"
    assert rf._load_program(a.s, "route_pick") is not None


def test_source_audit_no_python_route_decision():
    src = inspect.getsource(ra)
    # the route goes through the seeded Program + the held faculties.
    for reused in ("route_pick", "GapRouteCue", "_load_program",
                   "gap_driven_acquisition", "substrate_extension", "self_verification"):
        assert reused in src, reused
    # NO Python literal that maps a kind to a filler name (that decision is the graph
    # Program). The route() function — the decision path — must contain NO filler-name
    # literal; the filler names it yields come from the route_pick Program in the graph.
    route_src = src[src.index("def route("):src.index("def _fill_acquisition")]
    assert '"acquisition"' not in route_src and "'acquisition'" not in route_src
    assert '"substrate_extension"' not in route_src and "'substrate_extension'" not in route_src
    assert "route_pick" in route_src and "evaluate" in route_src   # the graph Program drives it
    # the filler NAMES appear ONLY as _FILLER_REGISTRY keys (a name->callable marshal
    # lookup, the twin of rf._COMPOSER_REGISTRY) — never returned from a kind test.
    assert '"acquisition": _fill_acquisition' in src
    assert '"substrate_extension": _fill_extension' in src
    # no LLM / no training in the driver.
    for banned in (".fit(", ".backward(", "import torch", "openai", "anthropic", "gemini"):
        assert banned not in src, banned


def test_driver_calls_held_faculties(monkeypatch):
    # SPY: the fills are the HELD faculties (#3 acquire_for_gap, #4 extend_for_gap),
    # not a bespoke path in the driver.
    from domains import gap_driven_acquisition as gda
    from domains import substrate_extension as se
    a = _fresh()
    seen = {"acquire": False, "extend": False}
    r_acq, r_ext = gda.acquire_for_gap, se.extend_for_gap

    def spy_acq(agent, domain, **kw):
        seen["acquire"] = True
        return r_acq(agent, domain, **kw)

    def spy_ext(agent, gap, **kw):
        seen["extend"] = True
        return r_ext(agent, gap, **kw)

    monkeypatch.setattr(gda, "acquire_for_gap", spy_acq)
    monkeypatch.setattr(se, "extend_for_gap", spy_ext)
    ra.process_gap(a, _knowledge_gap(a), seeds_dir=_tmp())
    ra.process_gap(a, _capability_gap(a), seeds_dir=_tmp())
    assert seen["acquire"] is True and seen["extend"] is True


# ===========================================================================
# NO REGRESSION — the composer route + the four faculties are unbroken.
# ===========================================================================
def test_composer_dispatch_unbroken():
    a = _fresh()
    sub, native, ag = rf._resolve_agent(a)
    # the existing composer_pick dispatch still resolves (our seed is additive).
    assert rf._pick_composer(sub, native, ag, ["control"]) == "control"
    assert rf._pick_composer(sub, native, ag, ["comprehend"]) == "comprehension"


def test_no_pollution_of_repo_seeds():
    # the driver persists acquired knowledge to the CALLER's seeds_dir; a temp dir
    # here leaves the repo seeds/ untouched (no cryptography_microtheory.json globbed).
    a = _fresh()
    tmp = _tmp()
    ra.run_cycle(a, seeds_dir=tmp)
    assert not os.path.exists(os.path.join(ROOT, "seeds", "cryptography_microtheory.json"))
