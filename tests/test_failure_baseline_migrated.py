"""THE BASELINE IS A LIST — the gate that makes it stay one.

    A BASELINE MUST BE A LIST OF NODE IDS WITH LAST-GREEN COMMITS, NEVER A COUNT.
    A COUNT CAN BE HELD; A LIST HAS TO BE READ.

`VISION_GATE_SCOPE_B_RESULTS.md` section 10: a declared 19-failure baseline became 53 files
and 144 nodes over ~10 days with **no rung on the path negligent**. A COUNT IS A SUBSTRING
SELECTOR'S COUSIN — it matches the SHAPE of the answer without touching its CONTENT, and
this arc is 0-for-6 on substring selectors.

WHAT THIS FILE GUARANTEES, and the thing that makes it a gate rather than a schema check:

  * the artifact enumerates NODE IDS, and its `total` is DERIVED from the list
    (a `total` that disagrees with `len(entries)` means somebody authored the number —
    the exact regression back to a count, and it is a FAILURE here);
  * every entry carries a CLASS and a LAST-GREEN field, so no entry can be inherited
    anonymously;
  * COVERAGE IS DECLARED — files that did not complete are NOT_ESTABLISHED, never
    silently green and never RED (a wall-clock cutoff is an authored constant on the
    measurement path, and reading an exit-124 as a red already manufactured one false
    failure in this tree);
  * and the STALE direction bites: a listed node that now PASSES is a FAILURE, because
    that is precisely the information a count destroys. A count absorbs a fix silently
    and reports it as a failure forever (`test_seed_claim`'s gate was killed by the fix
    it asked for, in 8 minutes, and reported that success as a failure ever since).

The STALE/NEW check over the WHOLE list is a sweep, not a unit test; it lives in
`scripts/failure_baseline.py verify`. What runs here is the cheap, always-on half.

POSITIVE-CONTROLLED IN BOTH DIRECTIONS (protocol 12.3 — a gate you have only ever seen
pass is not a gate you have tested): see `test_the_structural_gate_BITES_*` below, which
mutate a copy of the artifact and require the checker to reject it.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
LIST_PATH = ROOT / "results" / "failure_baseline.json"

REQUIRED_ENTRY_KEYS = {"node", "file", "kind", "message", "class",
                       "last_green_commit", "file_seconds"}


def _load():
    if not LIST_PATH.exists():
        pytest.skip(f"{LIST_PATH.name} absent — run scripts/failure_baseline_sweep.py "
                    "then scripts/failure_baseline.py build")
    return json.loads(LIST_PATH.read_text())


# --------------------------------------------------------------------------- #
#  THE CHECKER — one function, so the positive controls exercise the REAL code
# --------------------------------------------------------------------------- #
def check_is_a_list_not_a_count(data) -> list[str]:
    """Return a list of violations. EMPTY means the artifact is list-shaped."""
    bad = []
    entries = data.get("entries")
    if not isinstance(entries, list):
        return ["`entries` is not a list — the artifact is not list-shaped at all"]
    if not entries:
        bad.append("`entries` is EMPTY while the artifact claims to record a baseline")

    # THE CENTRAL CHECK: the count must be DERIVED, never authored.
    if data.get("total") != len(entries):
        bad.append(f"`total` ({data.get('total')}) != len(entries) ({len(entries)}) — "
                   "a count was AUTHORED instead of derived; this is the regression "
                   "back to a held number")

    seen = set()
    for i, e in enumerate(entries):
        missing = REQUIRED_ENTRY_KEYS - set(e)
        if missing:
            bad.append(f"entry {i} ({e.get('node','?')}) missing {sorted(missing)}")
            continue
        # A FAILED entry must be a real node id. A collection ERROR legitimately has
        # no node — pytest reports it at file granularity — so it is admitted, but
        # ONLY when it is labelled as such, so "file-level" can never become a
        # hiding place for un-enumerated failures.
        if "::" not in e["node"] and e.get("kind") != "ERROR":
            bad.append(f"entry {i} `node` is {e['node']!r} — not a pytest NODE ID; "
                       "a baseline of file names is a count with extra steps")
        if e["node"] in seen:
            bad.append(f"duplicate node id {e['node']}")
        seen.add(e["node"])
        if not e.get("class"):
            bad.append(f"entry {e['node']} has no CLASS — an entry nobody has "
                       "diagnosed is exactly the entry a count hides")
        if "last_green_commit" not in e:
            bad.append(f"entry {e['node']} has no last_green_commit field")

    if "coverage" not in data:
        bad.append("no `coverage` block — a list that does not declare what it did "
                   "NOT measure is claiming a completeness it has not earned")
    else:
        cov = data["coverage"]
        for k in ("files_swept", "NOT_ESTABLISHED"):
            if k not in cov:
                bad.append(f"`coverage` missing {k}")
    for k in ("head", "engine", "condition"):
        if not data.get(k):
            bad.append(f"missing `{k}` — a number without its engine, commit and "
                       "condition is a rumour (protocol 10 / 12)")
    return bad


# --------------------------------------------------------------------------- #
#  THE GATE
# --------------------------------------------------------------------------- #
def test_the_baseline_artifact_is_a_LIST_not_a_COUNT():
    assert check_is_a_list_not_a_count(_load()) == []


def test_every_entry_is_actionable():
    """Fixed, re-pinned or deleted — an entry must say enough to choose."""
    data = _load()
    for e in data["entries"]:
        assert e["class"], e
        assert e["file"] and e["file"].endswith(".py"), e
        # §8.1-proposed: a brief's file attribution is a CLAIM, not a location — so the
        # list checks that each node really does live in the file it is filed under,
        # rather than trusting the pairing. (Scope B's brief mis-located a gate and cost
        # a peer a cycle.)
        assert e["node"].startswith(e["file"]), \
            f"{e['node']} does not live in {e['file']}"


def test_coverage_is_declared_and_unfinished_files_are_NOT_ESTABLISHED():
    """A timeout is an authored constant. Under contention it converts SLOW into
    FAILED — a green 501-second file was logged as a timeout red in this tree. An
    unfinished file is NOT_ESTABLISHED, never RED and never silently green."""
    cov = _load()["coverage"]
    ne_files = {x["file"] for x in cov["NOT_ESTABLISHED"]}
    red_files = {e["file"] for e in _load()["entries"]}
    assert not (ne_files & red_files), \
        f"file counted BOTH not-established and red: {sorted(ne_files & red_files)}"
    for x in cov["NOT_ESTABLISHED"]:
        assert "reason" in x and x["reason"], x


def test_the_known_never_green_entries_are_recorded_as_such():
    """`test_codec_graph_resident` is the type specimen the whole rule is for: it entered
    the tree as 30 nodes red since the file was born, inside every baseline this tree has
    ever declared, because a count cannot distinguish 'never once passed' from 'broke this
    morning'.

    UPDATED 2026-07-21 (rung 121000-121999): the dead-install bug was FIXED (codec.rs now
    routes through `Substrate::add_rule`), and the list was RE-READ — exactly what a list is
    for. 23 of the 30 went green and were DELETED; 8 remain red for a SECOND, distinct cause
    (an incomplete HEVC / fixed-arity-array grammar the dead install had masked — see
    VISION_CODEC_ACTIVATE_RESULTS.md and each entry's `diagnosis`). So codec is still present
    in the list, now correctly at 8 nodes with the honest cause, not 30 with a stale one.

    If those 8 are ever fixed too, this assertion goes red and the list MUST be re-read
    again — which is the entire point of a list."""
    data = _load()
    codec = [e for e in data["entries"] if "test_codec_graph_resident" in e["node"]]
    assert codec, ("test_codec_graph_resident is absent from the baseline list. Either "
                   "its remaining reds were fixed — in which case UPDATE THE LIST and this "
                   "doc — or the sweep did not reach it, which the coverage block must say.")


# --------------------------------------------------------------------------- #
#  POSITIVE CONTROLS — the gate must be able to go RED
# --------------------------------------------------------------------------- #
def _mutate(fn):
    data = copy.deepcopy(_load())
    fn(data)
    return check_is_a_list_not_a_count(data)


def test_the_structural_gate_BITES_an_authored_count():
    """The regression this whole rung exists to prevent: someone replaces the list
    with a number, or lets the number drift from the list."""
    bad = _mutate(lambda d: d.update(total=d["total"] + 1))
    assert any("AUTHORED" in b for b in bad), bad


def test_the_structural_gate_BITES_a_bare_file_list():
    """A baseline of FILE names is a count with extra steps — it still cannot tell a
    new red from an old one inside the same file."""
    def degrade(d):
        e = next(x for x in d["entries"] if x["kind"] == "FAILED")
        e["node"] = e["file"]
    bad = _mutate(degrade)
    assert any("not a pytest NODE ID" in b for b in bad), bad


def test_the_structural_gate_BITES_an_undiagnosed_entry():
    bad = _mutate(lambda d: d["entries"][0].update(**{"class": ""}))
    assert any("no CLASS" in b for b in bad), bad


def test_the_structural_gate_BITES_a_missing_last_green_field():
    bad = _mutate(lambda d: d["entries"][0].pop("last_green_commit"))
    assert any("last_green_commit" in b for b in bad), bad


def test_the_structural_gate_BITES_an_undeclared_coverage():
    bad = _mutate(lambda d: d.pop("coverage"))
    assert any("coverage" in b for b in bad), bad


def test_the_structural_gate_BITES_a_missing_engine():
    """Protocol 10: a number without an engine is not a result."""
    bad = _mutate(lambda d: d.update(engine=""))
    assert any("engine" in b for b in bad), bad


def test_the_structural_gate_PASSES_the_real_artifact():
    """The negative control for the six above: the mutations are what is being
    detected, not some property the real file happens to lack."""
    assert check_is_a_list_not_a_count(_load()) == []
