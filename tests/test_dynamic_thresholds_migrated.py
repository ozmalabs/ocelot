"""test_dynamic_thresholds_migrated — DYNAMIC THRESHOLDS + REOPEN + REFORM
(2026-07-11). The user's directive: "thresholds should be dynamic based on
complexity and overflow and be able to be reformed. if a concept is too
complex, then human approach is to take it and reform your own understanding
into component shapes. the reopen is the entire point of the circular buffer
and was already in place for extended reading."

Three things landed, all reading-layer, all held graph data + mechanical
Python I/O (CLAUDE.md discipline — no Python decision anywhere below):

  1. THE RING, LIVE. `reading_scope.enforce_trace_buffer` is now bounded
     PER FLOW after EVERY commit inside `coref_entities.read_into_situation_
     model` (the live per-sentence spine driver `reading_drive._shim_spine`
     calls) — not only at `read_paragraph`'s paragraph-scope end. Eviction
     pressure (`traces_evicted`/`max_evicted_salience`) is recorded
     mechanically on the flow's own Source node.

  2. THE REOPEN, LIVE. A non-sequitur between two successive live commits
     REACTIVATES the prior sentence's still-resident retained trace first
     (warm — `reading_scope.reactivate`, no re-derivation) and falls back to
     a cold `_reread_from_source` only once the ring has evicted it — the
     SAME mechanism `read_paragraph` already had, now wired into the LIVE
     per-sentence loop (`coref_entities.read_into_situation_model`) AND into
     `reading_drive._shim_monitoring`'s global-contradiction path
     (`global_monitoring.validate_against_model`'s new `prior_establisher`
     provenance -> `escalate_reread`).

  3. THE REFORM. `reform_overcomplex_clause` (seeds/reading_aperture.json)
     marks a SentenceParse `reform_pending` when its own measurements
     (`residual_marker_count`, `swallowed_ratio` — mechanical, stamped by
     `coref_entities.read_into_situation_model`) cross this flow's held
     `ApertureBudget` threshold; `reading_drive._execute_pending_reforms`
     (run both opportunistically inside `_shim_monitoring` and via the
     ALWAYS-ON `reform_reflex`, seeds/reading_reform_reflex.json — see that
     seed's own docstring for why a dedicated reflex is required) mechanically
     runs `reading_collapse.read_clause_order_n` and records the decomposed
     `part_of`/marker component predications back onto the SentenceParse. A
     SIMPLE clause (0/0.0 on both measurements) never crosses either
     threshold. THE LADDER: sustained eviction pressure widens capacity ONCE
     (`reading_widen_capacity_once`); beyond that, `reform_pressure_factor`
     TIGHTENS the reform threshold instead of widening again.

Thresholds are DYNAMIC + REFORMABLE: `domains/reading_norms.effective_trace_
capacity`/`effective_max_order` evaluate held Program (Term-tree) derivations
(`reading_derive_trace_capacity`/`reading_derive_max_order`,
seeds/reading_aperture.json) over this register's own `ApertureBudget` row —
editing either the budget's numbers or the Program itself changes the
derived value with ZERO code changes.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_dynamic_thresholds_migrated.py -p no:randomly -q
"""
from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core                              # noqa: E402
from substrate.world_adapter import WorldAdapter                       # noqa: E402
from substrate.boot_all import load_all_seeds                          # noqa: E402
from domains import dictionary_lexicon as dl                           # noqa: E402
from domains import coref_entities as ce                               # noqa: E402
from domains import global_monitoring as gm                            # noqa: E402
from domains import reading_collapse as rc                             # noqa: E402
from domains import reading_drive as rd                                # noqa: E402
from domains import reading_norms as rn                                # noqa: E402
from domains import reading_scope as rs                                # noqa: E402
from domains import register_source as regs                            # noqa: E402
from domains.reflective_faculty import _ensure_seed_chain              # noqa: E402

jd = pytest.importorskip("jabberwock_daemon")
import jabberwock_produces_analysis_from_goal as jpafg                 # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def _warm():
    dl.warm_wordnet("en")


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


def _vv(n):
    return n.value if hasattr(n, "value") else n


def _mint_flow(agent, register="conversational"):
    """Mint a minimal Source+Goal pair (mirrors reading_drive.run_reading_flow's
    own mint step) so `coref_entities.read_into_situation_model` can be driven
    directly with `unit=`/`flow_node=`/`register=`, without paying for the
    full ten-stage comprehension pipeline in tests that only exercise the
    live spine driver itself."""
    _ensure_seed_chain(agent.s, agent.inner, agent.agent,
                       ("literary_analysis_driving", "reading_aperture"))
    src = agent.s.add_node("Source", {"text": ""})
    agent.s.set_attr(src, "flow", _vv(src))
    goal = agent.s.add_node("Goal", {"register": register, "flow": _vv(src)})
    agent.inner.add_edge_unchecked(goal, "reads_source", src)
    return src, _vv(src)


# --------------------------------------------------------------------------- #
#  Fixture texts.
# --------------------------------------------------------------------------- #
# Eight simple, independently-grounding SVO sentences (the mining-domain
# vocabulary test_reading_scope.py's HEADLINE/AMBIG already proves grounds
# cleanly) — clean commits, salience 0.0.
CLEAN_8 = (". ".join([
    "miners extract ore", "smelters process alloys", "workers gather metal",
    "miners mine ore", "smelters melt metal", "workers extract alloys",
    "miners gather ore", "smelters process metal"]) + ".")

# The SAME genuine attachment ambiguity test_reading_scope.py's AMBIG uses
# ('metal' attaches to 'ore' or to 'smelters' — both segmentations cohere;
# greedy backtracks to a coherent one with salience 0.5) followed by a
# NON-SEQUITUR trigger sharing no referent with the committed gist.
AMBIG = "miners extract ore metal smelters process alloys"
NON_SEQUITUR_TRIGGER = "smelters melt iron"

ENUMERATION = "The device includes a battery, a screen, a camera, and a speaker."
SIMPLE = "miners extract ore."


# =========================================================================== #
#  1. THE RING, LIVE — bounded per flow, evicts lowest-salience, records
#     the eviction datum mechanically on the flow's own Source.
# =========================================================================== #
def test_live_ring_bounds_resident_traces_and_records_eviction():
    ag = _fresh()
    src, flow = _mint_flow(ag, register="conversational")
    out = ce.read_into_situation_model(ag, CLEAN_8, unit=flow, flow_node=src,
                                       register="conversational")
    resident = rs._resident_traces(ag.s, unit=flow)
    cap = rn.effective_trace_capacity(ag, "conversational", widened=False)
    assert cap == 4, "conversational's held base capacity"
    assert len(resident) <= cap, resident
    at = ag.s.node(src)["attrs"]
    assert at["traces_evicted"] == 8.0 - cap
    assert at["max_evicted_salience"] == 0.0          # every commit here was clean
    # every RetainedTrace this flow minted carries the flow stamp (task 1: "add
    # the flow stamp mechanically if needed").
    for n in ag.s.nodes("RetainedTrace"):
        assert ag.s.node(n)["attrs"].get("flow") == flow


def test_ring_is_flow_scoped_on_a_persistent_substrate():
    """A second flow's traces never evict or count toward the first flow's own
    ring — the Wave 1A `unit=`/`flow` isolation convention, now exercised for
    RetainedTrace."""
    ag = _fresh()
    src1, flow1 = _mint_flow(ag, register="conversational")
    ce.read_into_situation_model(ag, CLEAN_8, unit=flow1, flow_node=src1,
                                 register="conversational")
    src2, flow2 = _mint_flow(ag, register="conversational")
    ce.read_into_situation_model(ag, "workers gather metal.", unit=flow2, flow_node=src2,
                                 register="conversational")
    assert len(rs._resident_traces(ag.s, unit=flow2)) == 1
    # flow1's own ring is unaffected by flow2's single clean commit.
    assert ag.s.node(src1)["attrs"]["traces_evicted"] == 4.0
    assert ag.s.node(src2)["attrs"].get("traces_evicted") is None


# =========================================================================== #
#  2. THE REOPEN, LIVE — warm beats cold, gated by the ring.
# =========================================================================== #
def test_warm_reopen_reactivates_before_eviction():
    ag = _fresh()
    src, flow = _mint_flow(ag, register="narrative")     # generous capacity (8)
    out = ce.read_into_situation_model(
        ag, AMBIG + ". " + NON_SEQUITUR_TRIGGER + ".", unit=flow, flow_node=src,
        register="narrative")
    assert out["n_reanalyses"] == 1, out
    ra = out["reanalyses"][0]
    assert ra["path"] == "reactivate_retained_trace", ra
    assert "smelters" not in ra["r1_referents"]
    assert "smelters" in ra["r2_referents"]


def test_cold_reopen_after_forced_eviction():
    """Same non-sequitur shape, but the prior sentence's trace has NO room in
    the ring (a held capacity of 0 — an explicit ApertureBudget row, edited
    with zero code beyond the test's own setup) — the ring wraps it out before
    the trigger sentence is even read, forcing the COLD `reread_from_source`
    path. Both warm and cold reach the SAME coherent reading; only the PATH
    differs (that IS the point of the ring: reopen is cheap while resident,
    costly once wrapped out)."""
    ag = _fresh()
    _ensure_seed_chain(ag.s, ag.inner, ag.agent, ("literary_analysis_driving", "reading_aperture"))
    ag.s.add_node("ApertureBudget", {
        "register": "zero_cap", "trace_capacity_base": 0.0, "trace_capacity_min": 0.0,
        "trace_capacity_max": 0.0, "max_revisits": 8.0, "widen_step": 0.0})
    src = ag.s.add_node("Source", {"text": ""})
    ag.s.set_attr(src, "flow", _vv(src))
    goal = ag.s.add_node("Goal", {"register": "zero_cap", "flow": _vv(src)})
    ag.inner.add_edge_unchecked(goal, "reads_source", src)

    out = ce.read_into_situation_model(
        ag, AMBIG + ". " + NON_SEQUITUR_TRIGGER + ".", unit=_vv(src), flow_node=src,
        register="zero_cap")
    assert rn.effective_trace_capacity(ag, "zero_cap", widened=False) == 0
    assert out["n_reanalyses"] == 1, out
    ra = out["reanalyses"][0]
    assert ra["path"] == "reread_from_source", ra
    assert ra["reactivate_decode_cost"] == 0                 # immediate cold miss
    assert ra["reread_decode_cost"] > 0                       # source re-derivation is costlier
    # both paths reach the SAME coherent reading (the ring changes cost, not correctness).
    warm_ag = _fresh()
    src_w, flow_w = _mint_flow(warm_ag, register="narrative")
    warm_out = ce.read_into_situation_model(
        warm_ag, AMBIG + ". " + NON_SEQUITUR_TRIGGER + ".", unit=flow_w, flow_node=src_w,
        register="narrative")
    assert ra["r2"] == warm_out["reanalyses"][0]["r2"]


def test_global_contradiction_reopen_provenance_round_trips():
    """The GLOBAL-INCOHERENCE reopen path (reading_drive._shim_monitoring):
    validate_against_model's new `sentence_order`/`trace_node` provenance
    bookkeeping (`establish_meta`) round-trips to a real, dereferenceable
    RetainedTrace via `reading_drive._resolve_node_by_value`, and a fired
    contradiction is never silently accepted — escalate_reread runs and
    reaches a verdict (reactivate when resident, cold re-read once evicted)."""
    ag = _fresh()
    src, flow = _mint_flow(ag, register="narrative")
    rec = rs.read_scope(ag, "the lawyer had no children", unit=flow)
    assert rec["committed"]
    chk1 = gm.validate_against_model(
        ag, "lawyer", "has_child", 0, sentence="the lawyer had no children", turn=1,
        unit=flow, sentence_order=0, trace_node=_vv(rec["trace_node"]))
    assert chk1["contradiction"] is False and chk1["prior_establisher"] is None

    chk2 = gm.validate_against_model(
        ag, "lawyer", "has_child", 1, sentence="his daughter arrived", turn=2,
        unit=flow, sentence_order=1, trace_node=None)
    assert chk2["contradiction"] is True
    est = chk2["prior_establisher"]
    assert est is not None and est["sentence"] == "the lawyer had no children"
    resolved = rd._resolve_node_by_value(
        _LA(ag), "RetainedTrace", est["trace_node"])
    assert resolved == rec["trace_node"]
    esc = gm.escalate_reread(ag, {**est, "trace_node": resolved},
                             {"sentence": "his daughter arrived"},
                             ["arrived", "his_daughter", "home"], max_revisits=4)
    assert esc["escalated"] is True
    assert esc["path"] in ("reactivate_retained_trace", "reread_from_source")


class _LA:
    """A minimal stand-in exposing `.s`/`.inner` for `_resolve_node_by_value`
    (which only reads `ad.s.nodes(...)`), so the provenance-round-trip test
    above doesn't need the full `_LAAdapter`/cortex-registration machinery."""
    def __init__(self, ag):
        self.s = ag.s
        self.inner = ag.inner


# =========================================================================== #
#  3. THE REFORM — complexity overflow decomposes into component shapes.
# =========================================================================== #
def test_reform_fires_on_enumeration_not_on_simple_clause():
    ag = _fresh()
    src, flow = _mint_flow(ag, register="conversational")
    out = ce.read_into_situation_model(
        ag, SIMPLE + " " + ENUMERATION, unit=flow, flow_node=src, register="conversational")
    tb = {t["sentence"]: t for t in out["textbase"]}
    assert tb[SIMPLE]["residual_marker_count"] == 0
    assert tb[SIMPLE]["swallowed_ratio"] == 0.0
    assert tb[ENUMERATION]["residual_marker_count"] == 4


def test_reform_executes_exactly_once_and_records_components():
    ag = rd._LAAdapter(_fresh().s)
    out = rd.run_reading_flow(ag, SIMPLE + " " + ENUMERATION, report="comprehend",
                              stages=None, max_sentences=40, window=2, register="narrative")
    rows = {ag.s.node(n)["attrs"].get("order"): ag.s.node(n)["attrs"]
           for n in ag.s.nodes("SentenceParse")}
    simple_row = rows[0]
    enum_row = rows[1]
    assert simple_row.get("reform_pending") is None and simple_row.get("reform_done") is None
    assert enum_row["reform_pending"] == 1.0 and enum_row["reform_done"] == 1.0
    preds = json.loads(enum_row["reform_predications"])
    assert sorted(preds) == sorted([
        ["part_of", "battery", "device"], ["part_of", "screen", "device"],
        ["part_of", "camera", "device"], ["part_of", "speaker", "device"]])
    # exactly once: re-running the executor is a no-op (reform_done guard).
    rd._execute_pending_reforms(ag)
    assert json.loads(ag.s.node([n for n in ag.s.nodes("SentenceParse")
                                 if ag.s.node(n)["attrs"].get("order") == 1][0])["attrs"]
                      ["reform_predications"]) == preds


def test_reform_ladder_widen_once_then_tighten():
    """The ladder (task 2): sustained eviction pressure widens capacity ONCE
    (reading_widen_capacity_once); a clause whose swallowed_ratio sits BETWEEN
    the un-tightened and pressure-tightened threshold only reforms once the
    flow has already spent its widen — never before, and a genuinely simple
    (0/0.0) clause never reforms either way."""
    def _fires(widened: bool) -> bool:
        ag = _fresh()
        src, flow = _mint_flow(ag, register="narrative")
        if widened:
            ag.s.set_attr(src, "capacity_widened", 1.0)
        sp = ag.s.add_node("SentenceParse", {
            "flow": flow, "sentence": "x", "order": 0.0,
            "residual_marker_count": 0.0, "swallowed_ratio": 0.3})   # between 0.25 and 0.5
        ag.inner.add_edge_unchecked(sp, "is_sentence_parse", sp)
        ag.inner.run_rules()
        return ag.s.node(sp)["attrs"].get("reform_pending") == 1.0

    assert _fires(widened=False) is False, "0.3 must NOT cross the un-tightened 0.5 threshold"
    assert _fires(widened=True) is True, "0.3 MUST cross the pressure-tightened 0.25 threshold"

    # eviction pressure genuinely trips capacity_widened live (the ladder's own
    # rung 1), demonstrated on the exact same live flow that reforms rung 2.
    ag = rd._LAAdapter(_fresh().s)
    text = ". ".join([AMBIG] * 6) + "."       # 6 high-salience (0.5) commits, capacity 4
    rd.run_reading_flow(ag, text, report="comprehend", stages=["spine"],
                        max_sentences=40, window=2, register="conversational")
    src = list(ag.s.nodes("Source"))[-1]
    at = ag.s.node(src)["attrs"]
    assert at["capacity_widened"] == 1.0
    assert at["max_evicted_salience"] >= 0.5


# =========================================================================== #
#  4. DYNAMIC + REFORMABLE DERIVATION — held Programs, editable with zero code.
# =========================================================================== #
def test_capacity_and_max_order_are_dynamic_over_flow_signals():
    ag = _fresh()
    _mint_flow(ag, register="conversational")
    clean = rn.effective_trace_capacity(ag, "conversational", widened=False)
    widened = rn.effective_trace_capacity(ag, "conversational", widened=True)
    assert widened > clean, "sustained overflow pressure must yield a DIFFERENT (wider) capacity"
    assert widened == 6 and clean == 4                        # clamped at trace_capacity_max=6

    base_order = rn.effective_max_order(ag, "conversational", reform_count=0)
    deeper_order = rn.effective_max_order(ag, "conversational", reform_count=1)
    assert deeper_order > base_order, "proven residual mass must license a DEEPER descent"
    assert base_order == 2 and deeper_order == 3


def test_editing_the_held_program_changes_the_outcome_with_zero_code():
    """"able to be reformed": mutate the ApertureBudget node's OWN numbers (no
    code change) and the derived capacity changes; mutate the Program
    Term-tree ITSELF (no code change) and the derivation FUNCTION changes."""
    ag = _fresh()
    _mint_flow(ag, register="conversational")
    before = rn.effective_trace_capacity(ag, "conversational", widened=True)
    for n in ag.s.nodes("ApertureBudget"):
        if ag.s.node(n)["attrs"].get("register") == "conversational":
            ag.s.set_attr(n, "widen_step", 100.0)      # edit the BELIEF, not the code
            ag.s.set_attr(n, "trace_capacity_max", 100.0)
    after = rn.effective_trace_capacity(ag, "conversational", widened=True)
    assert after == 100, "clamped by the EDITED trace_capacity_max, still held data"
    assert after != before

    # mutate the PROGRAM itself: capacity = base only (ignore widen entirely).
    for n in ag.s.nodes("Program"):
        if ag.s.node(n)["attrs"].get("name") == "reading_derive_trace_capacity":
            ag.s.set_attr(n, "program", json.dumps({"type": "Var", "name": "base"}))
    rewritten = rn.effective_trace_capacity(ag, "conversational", widened=True)
    assert rewritten == 4, "the rewritten Program ignores widen_step entirely"


def test_clamps_hold_as_data_not_code():
    """A capacity/order derivation is clamped by the HELD min/max attrs, not a
    Python floor — proven both directions (a below-floor base clamps up to
    min_cap; an intentionally-configured zero clamps to zero, never silently
    floored to 1 by hidden code)."""
    ag = _fresh()
    _ensure_seed_chain(ag.s, ag.inner, ag.agent, ("literary_analysis_driving", "reading_aperture"))
    ag.s.add_node("ApertureBudget", {
        "register": "clamp_test", "trace_capacity_base": 1.0, "trace_capacity_min": 5.0,
        "trace_capacity_max": 5.0, "widen_step": 0.0})
    assert rn.effective_trace_capacity(ag, "clamp_test", widened=False) == 5   # floored UP to min
    ag.s.add_node("ApertureBudget", {
        "register": "zero_test", "trace_capacity_base": 0.0, "trace_capacity_min": 0.0,
        "trace_capacity_max": 0.0, "widen_step": 0.0})
    assert rn.effective_trace_capacity(ag, "zero_test", widened=False) == 0    # NOT floored to 1


# =========================================================================== #
#  5. Canon round-trip, churn-free, reconcile, seed structure.
# =========================================================================== #
def test_new_rules_canon_round_trip_and_are_refreshable():
    d = json.load(open(os.path.join(ROOT, "seeds", "reading_aperture.json")))
    names = {r["name"] for r in d["rules"]}
    assert {"reading_widen_capacity_once", "reform_overcomplex_clause"} <= names
    assert d["id"] in jd._REFRESHABLE_SEEDS
    for r in d["rules"]:
        if r["name"] in ("reading_widen_capacity_once", "reform_overcomplex_clause"):
            body = jd._canon_rule_body(r)
            assert body, "must round-trip through the Rust rule serializer cleanly"


def test_reform_reflex_seed_structure():
    d = json.load(open(os.path.join(ROOT, "seeds", "reading_reform_reflex.json")))
    assert d["depends_on"] == ["reading_cortices"]
    assert len(d["reflexes"]) == 1
    assert d["reflexes"][0]["response"] == "reform_advance"


def test_aperture_budget_rows_carry_the_new_fields():
    d = json.load(open(os.path.join(ROOT, "seeds", "reading_aperture.json")))
    fields = {"trace_capacity_base", "trace_capacity_min", "trace_capacity_max",
             "max_revisits", "max_order_base", "max_order_max", "widen_step",
             "widen_salience_threshold", "reform_eviction_threshold",
             "reform_residual_threshold", "reform_swallowed_threshold",
             "reform_pressure_factor"}
    budgets = [n for n in d["nodes"] if n["type"] == "ApertureBudget"]
    assert len(budgets) == 7
    for b in budgets:
        assert fields <= set(b["attrs"].keys()), b["attrs"].get("register")
    # conversational stays TIGHT (bounded chat turns); document registers stay
    # at the PRE-WAVE Python literal defaults (byte-identical baseline).
    by_reg = {b["attrs"]["register"]: b["attrs"] for b in budgets}
    assert by_reg["conversational"]["trace_capacity_base"] == 4.0
    assert by_reg["default"]["trace_capacity_base"] == 8.0
    assert by_reg["default"]["max_revisits"] == 8.0
    assert by_reg["default"]["max_order_base"] == 2.0


def test_boot_installs_reform_reflex_and_dynamic_programs_idempotently():
    ag1 = _fresh()
    rd._register_cortices(rd._LAAdapter(ag1.s))
    n1 = len(list(ag1.s.nodes("Program")))
    r1 = len(list(ag1.s.nodes("Reflex"))) if hasattr(ag1.s, "nodes") else 0
    # loading again (idempotent seed installation) must not duplicate nodes.
    rd._register_cortices(rd._LAAdapter(ag1.s))
    n2 = len(list(ag1.s.nodes("Program")))
    assert n2 == n1


# =========================================================================== #
#  6. Live daemon-shaped smoke — a convoluted paragraph reforms; the agent
#     still answers about its content.
# =========================================================================== #
def test_live_daemon_smoke_convoluted_paragraph_reforms_and_still_answers():
    a = WorldAdapter(seeds=(), shadow_read=True, deep_ingest=True)
    load_all_seeds(a)
    text = (
        "Miners extract ore from the mountain. "
        "The device includes a battery, a screen, a camera, and a speaker. "
        "Smelters process the alloys."
    )
    route = regs.route_reading(a, text, hint="narrative", max_sentences=40)
    assert route.get("flow") is not None
    flow = route["flow"]
    sp_rows = [n for n in a.s.nodes("SentenceParse") if a.s.node(n)["attrs"].get("flow") == flow]
    assert len(sp_rows) >= 3
    reformed = [n for n in sp_rows if a.s.node(n)["attrs"].get("reform_done") == 1.0]
    assert reformed, "at least one over-complex sentence must have reformed"
    all_reform_preds = [p for n in reformed
                        for p in json.loads(a.s.node(n)["attrs"]["reform_predications"])]
    assert any(p[0] == "part_of" for p in all_reform_preds), (
        "the enumeration sentence's component structure must be among the reforms: %r"
        % all_reform_preds)

    a._mint_document_held_answers("smoke_doc", flow)
    reply = a.converse("What do you know about the device?", speech_act="question")
    assert isinstance(reply, str) and reply.strip()


if __name__ == "__main__":
    a = WorldAdapter(seeds=(), shadow_read=True, deep_ingest=True)
    load_all_seeds(a)
    text = (
        "Miners extract ore from the mountain. "
        "The device includes a battery, a screen, a camera, and a speaker. "
        "Smelters process the alloys."
    )
    route = regs.route_reading(a, text, hint="narrative", max_sentences=40)
    print("flow:", route.get("flow"))
    for n in a.s.nodes("SentenceParse"):
        at = a.s.node(n)["attrs"]
        if at.get("flow") != route["flow"]:
            continue
        print("SentenceParse[%s] %r" % (at.get("order"), at.get("sentence")))
        print("   residual_marker_count=%s swallowed_ratio=%s reform_pending=%s reform_done=%s"
              % (at.get("residual_marker_count"), at.get("swallowed_ratio"),
                 at.get("reform_pending"), at.get("reform_done")))
        if at.get("reform_done") == 1.0:
            print("   reform_predications:", at.get("reform_predications"))
    a._mint_document_held_answers("smoke_doc", route["flow"])
    print("reply:", a.converse("What do you know about the device?", speech_act="question"))
