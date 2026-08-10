"""P0 GATE — the code-synthesis baseline is a LIST, and it stays live.

    A BASELINE MUST BE A LIST OF IDENTITIES, NEVER A COUNT OR A CHARACTERISATION.
    A COUNT CAN BE HELD; A LIST HAS TO BE READ.  (the 2026-07-21 retraction rule)

`results/code_synthesis_baseline.json` freezes PROGRAM_SYNTHESIS_PLAN.md's P0
starting point: the enumerated Term-emittable function list (file + qualname,
never "27"), the per-function construction labels over the full `domains/`
scan, the frozen 26-item NL write battery with per-item outcome, and the
2-file deterministic fixture-corpus scan. The follow-on phases (P1–P6) are
measured as DIFFS AGAINST THESE LISTS — an identity moving between lists is
readable; a count absorbing a change is not.

Following the `test_failure_baseline_migrated.py` precedent:

  * every total must be DERIVED from its list (an authored count is the exact
    regression this gate exists to reject);
  * the checker is ONE function, POSITIVE-CONTROLLED (protocol 12.3 — a gate
    you have only ever seen pass is not a gate you have tested): the BITES
    tests mutate a copy and require rejection;
  * a SMALL deterministic subset is re-verified LIVE — the 3 held-starter
    battery items and the isolated fixture corpus (chosen precisely so a
    concurrent edit elsewhere in domains/ cannot flake this gate) — so the
    artifact cannot silently rot against the code paths it froze.

The full `domains/` re-scan (~50s) is the builder's job
(`scripts/code_synthesis_baseline_build.py`), not this always-on gate's.

Run: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 \
     OZMA_SEED_PERSIST_DISABLED=1 python3 -m pytest \
     tests/test_code_synthesis_baseline_migrated.py -p no:randomly -q
"""
from __future__ import annotations

import copy
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
          os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

srs = pytest.importorskip("substrate_rs")

LIST_PATH = os.path.join(ROOT, "results", "code_synthesis_baseline.json")
FIXTURE_ROOT = "tests/fixtures/code_curriculum/measurement_corpus"

REQUIRED_TOP_KEYS = {"head", "measured_at", "engine", "condition", "scan",
                     "term_emittable", "write_battery", "fixture_scan"}
REQUIRED_FUNCTION_KEYS = {"file", "qualname", "construction", "emittable",
                          "predict_correct"}
REQUIRED_BATTERY_KEYS = {"request", "ok", "construction", "reason"}


@pytest.fixture(autouse=True)
def _no_real_seed_writes(monkeypatch):
    monkeypatch.setenv("OZMA_SEED_PERSIST_DISABLED", "1")


def _load():
    if not os.path.exists(LIST_PATH):
        pytest.skip("code_synthesis_baseline.json absent — run "
                    "scripts/code_synthesis_baseline_build.py")
    with open(LIST_PATH) as f:
        return json.load(f)


# --------------------------------------------------------------------------- #
#  THE CHECKER — one function, so the positive controls exercise the REAL code
# --------------------------------------------------------------------------- #
def check_is_a_list_not_a_count(data) -> list:
    """Return a list of violations. EMPTY means the artifact is list-shaped."""
    bad: list = []
    missing_top = REQUIRED_TOP_KEYS - set(data)
    if missing_top:
        return ["missing top-level keys %s" % sorted(missing_top)]
    for k in ("head", "measured_at"):
        if not data.get(k):
            bad.append("missing `%s` — a number without its commit and moment "
                       "is a rumour" % k)
    if not (data.get("engine") or {}).get("substrate_rs"):
        bad.append("missing `engine.substrate_rs` — a number without its "
                   "engine is a rumour")
    if not (data.get("condition") or {}).get("scan_scope"):
        bad.append("missing `condition.scan_scope` — eval-subset coverage is "
                   "part of every claim")

    scan = data["scan"]
    fns = scan.get("functions")
    if not isinstance(fns, list) or not fns:
        return bad + ["`scan.functions` is not a non-empty list — the scan is "
                      "a count, not a baseline"]
    # THE CENTRAL CHECK: every total is DERIVED, never authored.
    if scan.get("n_functions") != len(fns):
        bad.append("`scan.n_functions` (%s) != len(scan.functions) (%d) — a "
                   "count was AUTHORED instead of derived" %
                   (scan.get("n_functions"), len(fns)))
    n_emittable_in_scan = 0
    for i, f in enumerate(fns):
        missing = REQUIRED_FUNCTION_KEYS - set(f)
        if missing:
            bad.append("scan.functions[%d] missing %s" % (i, sorted(missing)))
            continue
        if f["emittable"]:
            n_emittable_in_scan += 1
    counts = scan.get("counts") or {}
    if counts.get("parseable") != len(fns):
        bad.append("`scan.counts.parseable` (%s) != len(scan.functions) (%d) — "
                   "an authored count" % (counts.get("parseable"), len(fns)))

    te = data["term_emittable"]
    entries = te.get("entries")
    if not isinstance(entries, list):
        return bad + ["`term_emittable.entries` is not a list"]
    if te.get("total") != len(entries):
        bad.append("`term_emittable.total` (%s) != len(entries) (%d) — a count "
                   "was AUTHORED instead of derived" %
                   (te.get("total"), len(entries)))
    if counts.get("term_emittable") != len(entries):
        bad.append("`scan.counts.term_emittable` (%s) != len(term_emittable."
                   "entries) (%d) — the headline count drifted from its list" %
                   (counts.get("term_emittable"), len(entries)))
    if len(entries) != n_emittable_in_scan:
        bad.append("term_emittable.entries (%d) disagrees with the scan's own "
                   "emittable rows (%d) — the two lists desynchronised" %
                   (len(entries), n_emittable_in_scan))
    scan_ids = {(f["file"], f["qualname"]) for f in fns}
    for e in entries:
        if not e.get("file") or not e.get("qualname"):
            bad.append("term_emittable entry %r lacks file+qualname — an "
                       "identity, not a label, is what a list is made of" % (e,))
        elif (e["file"], e["qualname"]) not in scan_ids:
            bad.append("term_emittable entry %s::%s is not in the scan list" %
                       (e["file"], e["qualname"]))

    wb = data["write_battery"]
    items = wb.get("items")
    if not isinstance(items, list) or not items:
        return bad + ["`write_battery.items` is not a non-empty list"]
    if wb.get("n") != len(items):
        bad.append("`write_battery.n` (%s) != len(items) (%d) — AUTHORED" %
                   (wb.get("n"), len(items)))
    if wb.get("n_ok") != sum(1 for i in items if i.get("ok")):
        bad.append("`write_battery.n_ok` (%s) != derived ok count (%d) — a "
                   "count was AUTHORED instead of derived" %
                   (wb.get("n_ok"), sum(1 for i in items if i.get("ok"))))
    for i, it in enumerate(items):
        missing = REQUIRED_BATTERY_KEYS - set(it)
        if missing:
            bad.append("write_battery.items[%d] missing %s" % (i, sorted(missing)))
            continue
        if not it["ok"] and not it.get("reason"):
            bad.append("battery item %r failed with NO reason string — an "
                       "undiagnosed entry is exactly what a count hides" %
                       it["request"])

    fx = data["fixture_scan"]
    ffns = fx.get("functions")
    if not isinstance(ffns, list) or not ffns:
        bad.append("`fixture_scan.functions` is not a non-empty list")
    elif fx.get("n_functions") != len(ffns):
        bad.append("`fixture_scan.n_functions` (%s) != len (%d) — AUTHORED" %
                   (fx.get("n_functions"), len(ffns)))
    return bad


# --------------------------------------------------------------------------- #
#  THE STRUCTURAL GATE
# --------------------------------------------------------------------------- #
def test_the_baseline_artifact_is_a_LIST_not_a_COUNT():
    assert check_is_a_list_not_a_count(_load()) == []


def test_every_emittable_entry_is_an_identity_in_the_scanned_scope():
    """file + qualname, and the file really lives under the declared scan
    scope — a list of labels that cannot be located is a count with steps."""
    data = _load()
    roots = tuple(data["condition"]["scan_scope"])
    for e in data["term_emittable"]["entries"]:
        assert e["file"].startswith(roots), e
        assert e["qualname"], e


def test_the_frozen_battery_is_the_26_item_curriculum_battery_verbatim():
    """The protected-control arm (PROGRAM_SYNTHESIS_PREREG.md): the frozen
    battery must BE code_curriculum_run.WRITE_BATTERY, byte-identical and in
    order — a battery that drifts from its source is a new instrument
    wearing the control's name."""
    from scripts.code_curriculum_run import WRITE_BATTERY
    data = _load()
    assert [i["request"] for i in data["write_battery"]["items"]] == WRITE_BATTERY


# --------------------------------------------------------------------------- #
#  POSITIVE CONTROLS — the gate must be able to go RED (protocol 12.3)
# --------------------------------------------------------------------------- #
def _mutate(fn):
    data = copy.deepcopy(_load())
    fn(data)
    return check_is_a_list_not_a_count(data)


def test_the_structural_gate_BITES_an_authored_emittable_count():
    bad = _mutate(lambda d: d["term_emittable"].update(
        total=d["term_emittable"]["total"] + 1))
    assert any("AUTHORED" in b for b in bad), bad


def test_the_structural_gate_BITES_an_authored_battery_score():
    bad = _mutate(lambda d: d["write_battery"].update(
        n_ok=d["write_battery"]["n_ok"] + 1))
    assert any("AUTHORED" in b for b in bad), bad


def test_the_structural_gate_BITES_a_desynchronised_emittable_list():
    def degrade(d):
        e = dict(d["term_emittable"]["entries"][0])
        e["qualname"] = e["qualname"] + "_never_scanned"
        d["term_emittable"]["entries"][0] = e
    bad = _mutate(degrade)
    assert any("not in the scan list" in b for b in bad), bad


def test_the_structural_gate_BITES_an_unreasoned_failure():
    def degrade(d):
        it = next(i for i in d["write_battery"]["items"] if not i["ok"])
        it["reason"] = ""
    bad = _mutate(degrade)
    assert any("NO reason" in b for b in bad), bad


def test_the_structural_gate_BITES_a_missing_scope_declaration():
    bad = _mutate(lambda d: d["condition"].pop("scan_scope"))
    assert any("scan_scope" in b for b in bad), bad


def test_the_structural_gate_PASSES_the_real_artifact():
    """Negative control for the five above: the mutations are what is being
    detected, not some property the real file happens to lack."""
    assert check_is_a_list_not_a_count(_load()) == []


# --------------------------------------------------------------------------- #
#  LIVE RE-VERIFICATION — a small deterministic subset, so the frozen lists
#  cannot silently rot against the code paths that produced them. One boot,
#  module-scoped; runtime well under the gate budget.
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def live_agent():
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def test_live_reverify_three_held_starter_battery_items(live_agent):
    """The first three battery items are held-starter shapes; re-run them
    through the SAME path the builder used (run_write_battery →
    write_function_from_request) and require outcome + construction to match
    the frozen entries exactly."""
    from domains import code_curriculum as cc
    data = _load()
    frozen = data["write_battery"]["items"][:3]
    live = cc.run_write_battery(live_agent, [i["request"] for i in frozen])
    for want, got in zip(frozen, live["rows"]):
        assert got["request"] == want["request"]
        assert bool(got["ok"]) == want["ok"], (want, got)
        assert got["construction"] == want["construction"], (want, got)


def test_live_reverify_fixture_corpus_scan(live_agent):
    """Re-scan the isolated 2-file fixture corpus and require per-function
    (file, qualname, construction, emittable) to match the frozen list —
    the same corpus test_code_curriculum_migrated.py already pins, chosen so
    concurrent edits to real domains/ files can never flake this gate."""
    from domains import code_curriculum as cc
    data = _load()
    frozen = {(f["file"], f["qualname"]): (f["construction"], f["emittable"])
              for f in data["fixture_scan"]["functions"]}
    scan = cc.scan_repo_functions(live_agent, [FIXTURE_ROOT])
    live = {(r["file"], r["name"]): (r["construction"], bool(r["emittable"]))
            for r in scan["rows"]}
    assert live == frozen
