"""test_reform_reingest_migrated — BLIND-SPOT CLOSURE R8 (reform components
reach the situation model, 2026-07-12).

Today (commit 401ea41a5d, dynamic-thresholds/reform wave) the reform
executor (`domains/reading_drive.py::_execute_pending_reforms`) runs
`reading_collapse.read_clause_order_n` on an over-complex SentenceParse and
records the decomposed `part_of`/marker component predications as
`reform_predications`/`reform_members` ON THE PARSE NODE — but those
components never reached the SmEntity/SmEvent situation model itself
(deliberately deferred at that wave to avoid double-ingest against the
once-per-sentence `kin_monitored` monitoring guard).

THE CLOSURE (seeds/reading_reform_ingest.json::ingest_reform_components +
`reading_drive._execute_pending_reform_ingests`): a graph RULE decides a
completed reform's components belong in the model (mirroring the reform_
pending/reform_done two-stage handoff one level up); the mechanical executor
mints real `part_of` SmEntity/edge structure (via the EXISTING
`inference_generation._mint_part_of` idiom, stamped `from_reform=1`) or hands
non-part_of component predications to `situation_model_reader.
ingest_predication` (structure only — deliberately NOT resolve_and_ingest,
whose coref bookkeeping would double-count a sentence's already-counted
mentions and distort the salience Argmax; see the executor's docstring). The
once-per-sentence kinship guard (`kin_monitored`) is UNTOUCHED — it reads
`resolved_predications` only, never `reform_predications`.
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
from domains import reading_drive as rd                                # noqa: E402
from domains import register_source as regs                            # noqa: E402

jd = pytest.importorskip("jabberwock_daemon")

ENUMERATION = "The device includes a battery, a screen, a camera, and a speaker."
SIMPLE = "miners extract ore."
PARTS = ("battery", "screen", "camera", "speaker")


@pytest.fixture(scope="module", autouse=True)
def _warm():
    dl.warm_wordnet("en")


def _vv(n):
    return n.value if hasattr(n, "value") else n


def _fresh_la():
    s, _node = boot_core()
    return rd._LAAdapter(s)


def _part_of_pairs(ag):
    """[(part_name, whole_name), ...] read straight off the graph's own
    part_of EDGES (not the SentenceParse's reform_predications JSON) --
    the actual proof the components reached the SITUATION MODEL."""
    out = []
    for n in ag.s.nodes("SmEntity"):
        at = ag.s.node(n)["attrs"]
        name = at.get("name")
        if not name:
            continue
        for whole in ag.s.neighbours(n, "part_of"):
            wat = ag.s.node(whole)["attrs"]
            out.append((name, wat.get("name")))
    return out


def _has_rule(ag, name):
    return any(r.get("name") == name for r in ag.inner.export_rules())


def _the_flow(ag):
    """`rd.run_reading_flow` wraps its OWN fresh `_LAAdapter` around `ag.s`
    internally (never mutates the caller's `ag.flow`), so the flow identity
    must be read back off the minted SentenceParse rows themselves — the
    same re-derivation every graph re-reader in reading_drive.py performs.
    A fresh single-read substrate mints exactly one flow."""
    flows = {ag.s.node(n)["attrs"].get("flow") for n in ag.s.nodes("SentenceParse")}
    flows.discard(None)
    assert len(flows) == 1, flows
    return next(iter(flows))


# --------------------------------------------------------------------------- #
#  THE CLOSURE: reform components mint REAL SmEntity + part_of graph edges.
# --------------------------------------------------------------------------- #
def test_reform_components_mint_real_part_of_edges():
    ag = _fresh_la()
    rd.run_reading_flow(ag, SIMPLE + " " + ENUMERATION, report="comprehend",
                        stages=None, max_sentences=40, window=2, register="narrative")
    assert _has_rule(ag, "ingest_reform_components")

    pairs = _part_of_pairs(ag)
    assert sorted(pairs) == sorted([(p, "device") for p in PARTS]), pairs

    # the components are stamped `from_reform=1` (provenance) and unit-scoped
    # to THIS flow, exactly like every other SmEntity the live spine mints.
    flow = _the_flow(ag)
    for n in ag.s.nodes("SmEntity"):
        at = ag.s.node(n)["attrs"]
        if at.get("name") in PARTS:
            assert at.get("from_reform") == 1.0, at
            assert at.get("unit") == flow, at


def test_reform_ingest_executes_exactly_once():
    ag = _fresh_la()
    rd.run_reading_flow(ag, SIMPLE + " " + ENUMERATION, report="comprehend",
                        stages=None, max_sentences=40, window=2, register="narrative")
    before = sorted(_part_of_pairs(ag))
    # re-running the executor is a no-op (the reform_ingested guard) — no
    # duplicate edges, no duplicate SmEntity nodes.
    rd._execute_pending_reform_ingests(ag)
    rd._execute_pending_reform_ingests(ag)
    after = sorted(_part_of_pairs(ag))
    assert after == before
    n_battery = sum(1 for n in ag.s.nodes("SmEntity")
                    if ag.s.node(n)["attrs"].get("name") == "battery")
    assert n_battery == 1, "must never duplicate-mint the same reform component"


def test_kin_monitored_guard_is_untouched_by_reform_reingest():
    """The once-per-sentence KINSHIP guard (`_shim_monitoring`'s own
    `kin_monitored` loop) reads `resolved_predications` ONLY -- re-ingesting a
    reform's components (which touches `reform_predications`, a DIFFERENT
    attr, and mints NEW SmEntity/part_of structure) must never re-trigger or
    duplicate that scan. Every SentenceParse this flow minted is `kin_
    monitored` exactly once, and its own `resolved_predications` attr is
    byte-unchanged by the reform re-ingest."""
    ag = _fresh_la()
    rd.run_reading_flow(ag, SIMPLE + " " + ENUMERATION, report="comprehend",
                        stages=None, max_sentences=40, window=2, register="narrative")
    flow = _the_flow(ag)
    rows = [ag.s.node(n)["attrs"] for n in ag.s.nodes("SentenceParse")
           if ag.s.node(n)["attrs"].get("flow") == flow]
    assert rows, "the flow must have minted its own SentenceParse rows"
    resolved_before = {at.get("order"): at.get("resolved_predications") for at in rows}
    for at in rows:
        assert at.get("kin_monitored") == 1, at

    rd._execute_pending_reform_ingests(ag)   # idempotent no-op, re-asserted

    rows2 = [ag.s.node(n)["attrs"] for n in ag.s.nodes("SentenceParse")
            if ag.s.node(n)["attrs"].get("flow") == flow]
    for at in rows2:
        assert at.get("kin_monitored") == 1, "must still be exactly-once"
        assert at.get("resolved_predications") == resolved_before[at.get("order")], (
            "reform re-ingest must never touch resolved_predications")


# --------------------------------------------------------------------------- #
#  DOCUMENT QA reaches the reform's components through the SmEntity graph.
# --------------------------------------------------------------------------- #
def test_document_qa_mentions_reform_components():
    a = WorldAdapter(seeds=(), shadow_read=True, deep_ingest=True)
    load_all_seeds(a)
    route = regs.route_reading(a, ENUMERATION, hint="narrative", max_sentences=40)
    flow = route["flow"]
    assert flow is not None

    pairs = []
    for n in a.s.nodes("SmEntity"):
        at = a.s.node(n)["attrs"]
        if at.get("unit") != flow:
            continue
        for whole in a.s.neighbours(n, "part_of"):
            pairs.append((at.get("name"), a.s.node(whole)["attrs"].get("name")))
    assert sorted(pairs) == sorted([(p, "device") for p in PARTS]), pairs

    a._mint_document_held_answers("device_doc", flow)
    reply = a.converse("What do you know about the device?", speech_act="question")
    assert isinstance(reply, str) and reply.strip()
    lowered = reply.lower()
    assert any(part in lowered for part in PARTS), reply


# --------------------------------------------------------------------------- #
#  CLOSURE PROOF (agent-in-control): ablating the rule reverts to the OLD
#  (pre-closure) behaviour -- the reform still fires and records its
#  predications on the parse node, but NOTHING is re-ingested into the
#  situation model, proving the "components belong in the model" decision
#  genuinely lives in the ablated rule, not in Python.
# --------------------------------------------------------------------------- #
def test_ablating_the_rule_reverts_to_no_reingest():
    ag = _fresh_la()
    # force the seed to install, then remove the rule BEFORE reading, so the
    # reform still fires (reform_overcomplex_clause is untouched) but its
    # components are never re-ingested.
    rd._register_cortices(ag)
    idx = None
    for i, r in enumerate(ag.inner.export_rules()):
        if isinstance(r, dict) and r.get("active", True) and \
                r.get("name") == "ingest_reform_components":
            idx = i
            break
    assert idx is not None, "the re-ingest decision must be a live, named, removable rule"
    assert ag.inner.remove_rule(idx) is True

    rd.run_reading_flow(ag, SIMPLE + " " + ENUMERATION, report="comprehend",
                        stages=None, max_sentences=40, window=2, register="narrative")
    flow = _the_flow(ag)

    # the reform ITSELF (an unrelated, unablated rule) still fires and still
    # records its component predications on the parse node.
    reformed = [n for n in ag.s.nodes("SentenceParse")
               if ag.s.node(n)["attrs"].get("flow") == flow
               and ag.s.node(n)["attrs"].get("reform_done") == 1.0]
    assert reformed, "reform_overcomplex_clause must be unaffected by ablating the re-ingest rule"
    preds = json.loads(ag.s.node(reformed[0])["attrs"]["reform_predications"])
    assert any(p[0] == "part_of" for p in preds), preds

    # but NOTHING was re-ingested: NO part_of edges exist anywhere (the base
    # order-1 read's own single captured enumeration member, "battery" --
    # `part_of(battery, device)`, unrelated to this closure -- touches a
    # coref-bookkeeping SmEntity for "battery"/"device" via `_touch_entity`
    # but mints no EDGE, since `part_of` is not a change-of-state/property/
    # eventive verb `situation_model_reader.ingest_predication` would ever
    # act on; only the reform's order-N descent recovers "screen"/"camera"/
    # "speaker" at all, and NONE of the four gets a part_of EDGE without the
    # ablated rule). reform_ingest_pending is also never set.
    assert _part_of_pairs(ag) == []
    names = {ag.s.node(n)["attrs"].get("name") for n in ag.s.nodes("SmEntity")}
    assert not ({"screen", "camera", "speaker"} & names), names
    for n in ag.s.nodes("SentenceParse"):
        assert ag.s.node(n)["attrs"].get("reform_ingest_pending") is None


# --------------------------------------------------------------------------- #
#  Seed structure + canon round-trip + refreshability.
# --------------------------------------------------------------------------- #
def test_seed_structure_and_canon_round_trip():
    d = json.load(open(os.path.join(ROOT, "seeds", "reading_reform_ingest.json")))
    assert d["depends_on"] == ["reading_cortices"]
    names = {r["name"] for r in d["rules"]}
    assert names == {"ingest_reform_components"}
    assert len(d["reflexes"]) == 1
    assert d["reflexes"][0]["response"] == "reform_ingest_advance"
    assert d["id"] in jd._REFRESHABLE_SEEDS
    for r in d["rules"]:
        body = jd._canon_rule_body(r)
        assert body, "must round-trip through the Rust rule serializer cleanly"


def test_boot_installs_reform_ingest_idempotently():
    ag1 = _fresh_la()
    rd._register_cortices(ag1)
    n1 = len(list(ag1.s.nodes("Reflex"))) if hasattr(ag1.s, "nodes") else 0
    r1 = len(ag1.inner.export_rules())
    rd._register_cortices(ag1)
    n2 = len(list(ag1.s.nodes("Reflex"))) if hasattr(ag1.s, "nodes") else 0
    r2 = len(ag1.inner.export_rules())
    assert n2 == n1
    assert r2 == r1


if __name__ == "__main__":
    a = WorldAdapter(seeds=(), shadow_read=True, deep_ingest=True)
    load_all_seeds(a)
    route = regs.route_reading(a, ENUMERATION, hint="narrative", max_sentences=40)
    flow = route["flow"]
    print("flow:", flow)
    for n in a.s.nodes("SmEntity"):
        at = a.s.node(n)["attrs"]
        if at.get("unit") == flow:
            print(" ", at.get("name"), "part_of ->",
                 [a.s.node(w)["attrs"].get("name") for w in a.s.neighbours(n, "part_of")])
    a._mint_document_held_answers("device_doc", flow)
    print("reply:", a.converse("What do you know about the device?", speech_act="question"))
