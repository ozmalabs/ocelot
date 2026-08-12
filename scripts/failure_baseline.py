#!/usr/bin/env python3
"""THE BASELINE, AS A LIST — build it, and verify it.

    A BASELINE MUST BE A LIST OF NODE IDS WITH LAST-GREEN COMMITS, NEVER A COUNT.
    A COUNT CAN BE HELD; A LIST HAS TO BE READ.

WHY (VISION_GATE_SCOPE_B_RESULTS.md section 10). The convention in this tree is a COUNT:
*"held the bench at the exact pre-existing 19-failure baseline throughout."* 19 became 144
over ~10 days with **no rung on the path negligent** — each honestly held a number that had
stopped meaning anything.

A COUNT IS A SUBSTRING SELECTOR'S COUSIN: it matches the SHAPE of the answer without
touching its CONTENT. This arc is 0-for-6 on substring selectors, and this is the same
defect one level up, at the level of a policy. Concretely, a count cannot distinguish:

  * a NEW red from an OLD one            (so a regression lands inside the number),
  * a red that has been FIXED            (so a success is reported as a failure forever),
  * a test that has NEVER ONCE PASSED    (test_codec_graph_resident: 30 nodes, ~48 days)
    from one that broke this morning.

A list can. Every entry has to be read, and every entry either gets fixed, re-pinned or
deleted.

SUBCOMMANDS
  build   raw sweep JSON  ->  results/failure_baseline.json   (the LIST)
  verify  re-run the listed node ids and report NEW / STALE / held

A `total` field is emitted, but it is DERIVED from the list and never authored — a count
computed FROM content is a summary; a count standing IN FOR content is the defect.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIST_PATH = ROOT / "results" / "failure_baseline.json"

# Classification is by the failure's own message, and every class is one a READER has to
# act on differently. UNCLASSIFIED is a first-class outcome: an entry nobody has diagnosed
# is exactly the entry a count would hide, so it is labelled, never defaulted.
_CLASSES = {
    "ENVIRONMENTAL_ENGINE_OR_IMPORT": (
        "EngineProvenanceError", "importorskip", "ModuleNotFoundError",
        "ImportError", "No module named"),
    # Protocol 12.3. ZERO of these remain at this HEAD -- the two that produced them were
    # range-pinned by this rung. The class is KEPT so a re-introduction is named on sight.
    "PROVENANCE_FALSE_ACCUSATION": (
        "Rust source moved", "CHANGED since", "CHANGED between"),
    # Protocol 10.2: `data/` is gitignored, so a fresh worktree has no slab. These are the
    # LOUD instances -- and 10.2's whole point is that the loud ones are the MINORITY: a
    # missing slab usually produces a fluent, well-formed, WRONG answer that surfaces as an
    # ordinary AssertionError. So this class is a FLOOR on data-conditional entries, never
    # an estimate of them.
    "GITIGNORED_DATA_ABSENT": ("FileNotFoundError", "data/"),
    # 10.3-proposed: `results/*_checkpoints/` is the THIRD gitignored class, red in every
    # worktree and green in canonical, with nothing announcing it.
    "GITIGNORED_RESULTS_ARTIFACT_ABSENT": ("results/run", "_checkpoints"),
    # ----------------------------------------------------------------------- #
    # THE FIVE CLASSES THE RED-TEST TRIAGE RUNG CLOSED (2026-08-12). Every one
    # is EXPECTED TO BE ZERO at this HEAD -- they are kept, exactly like
    # PROVENANCE_FALSE_ACCUSATION above, so a RE-INTRODUCTION IS NAMED ON SIGHT
    # rather than re-diagnosed from scratch by the next twenty rungs. A count
    # cannot do that; a class on a listed node id can.
    # ----------------------------------------------------------------------- #
    # `build_is_stale` compared mtimes, and `git worktree add` writes .rs files
    # milliseconds after the .so -- 117 node ids / 88 files refusing to measure on
    # the correct committed engine. Fixed: staleness is CONTENT.
    "ENGINE_FALSE_STALE_REFUSAL": ("REFUSING TO MEASURE", "EngineProvenanceError"),
    # a DECLARED-optional dependency (see tests/optional_deps.OPTIONAL) with no
    # guard on the tests that need it -- a skip wearing a red's clothes.
    "OPTIONAL_DEP_UNGUARDED": ("No module named", "pybullet and numpy are required"),
    # a section-12.3 rung-provenance pin whose commits are not in THIS repository
    # (history re-exported; root commit 26ca9ff). See tests/provenance_pins.py.
    "PROVENANCE_PIN_UNRESOLVABLE": ("returned non-zero exit status 128",
                                    "unknown revision or path not in the working tree",
                                    "Not a valid object name"),
    # a seeds/*.json scan that did not guard for the one LIST-rooted file the
    # seed LOADER itself skips (`_recovered_f16_rules.json`).
    "LIST_ROOTED_SEED_UNGUARDED": ("'list' object has no attribute 'get'",),
}


def classify(message: str) -> str:
    # Order matters: the two gitignored classes are distinguished by PATH, so they are
    # tested on the specific path fragment before the generic exception name.
    if "FileNotFoundError" in message:
        if "/results/" in message or "results/run" in message:
            return "GITIGNORED_RESULTS_ARTIFACT_ABSENT"
        if "/data/" in message:
            return "GITIGNORED_DATA_ABSENT"
    # The 2026-08-12 triage classes are tested FIRST: each is a SPECIFIC, closed
    # cause, and the generic ENVIRONMENTAL_ENGINE_OR_IMPORT bucket would otherwise
    # swallow two of them and hand the reader back the vague answer the class was
    # created to replace.
    for cls in ("ENGINE_FALSE_STALE_REFUSAL", "OPTIONAL_DEP_UNGUARDED",
                "PROVENANCE_PIN_UNRESOLVABLE", "LIST_ROOTED_SEED_UNGUARDED"):
        if any(n in message for n in _CLASSES[cls]):
            return cls
    for cls, needles in _CLASSES.items():
        if cls.startswith("GITIGNORED"):
            continue
        if any(n in message for n in needles):
            return cls
    return "UNCLASSIFIED"


# Per-file annotations for entries whose cause has actually been DIAGNOSED. The whole
# point of a list over a count is that entries carry what a reader needs in order to
# fix / re-pin / delete them, so a diagnosis lands HERE rather than in prose nobody
# joins back up to the node id.
#
# `last_green_commit` is MEASURED or STATIC — never inferred from a behavioural re-run
# of an old tree against today's engine (the confound that cost the Scope B peer two
# headline durations).
_ANNOTATIONS = {
    # ----------------------------------------------------------------------- #
    #  DIAGNOSED BY THE RED-TEST TRIAGE RUNG (2026-08-12/13). Every one of these
    #  was READ, not guessed; each says what a reader has to do differently.
    #  See docs/research/engine_substrate/RED_TEST_TRIAGE_RESULTS.md.
    # ----------------------------------------------------------------------- #
    "tests/test_seed_claim_migrated.py": {
        "class": "GATE_KILLED_BY_ITS_OWN_FIX",
        "last_green_commit": "UNKNOWN (pre-export history; root commit is 26ca9ff)",
        "diagnosis":
            "The gate SAYS SO ITSELF, verbatim in its own failure messages: '38000-38099 "
            "is now DECLARED at [(38000, 38099)]. The ledger-blindness this gate documents "
            "has been FIXED' and 'baseline entries no longer measured (runner deleted, or a "
            "section-11 row was added)'. This is the exact specimen "
            "tests/test_failure_baseline_migrated.py's own docstring names -- a gate killed "
            "by the fix it asked for, reporting that success as a failure ever since. NOT "
            "retired here: the action is to re-read the VISION_PROTOCOL section-11 ledger "
            "rows and update the gate's baseline, which is a judgement about the seed ledger, "
            "not a triage call.",
    },
    "tests/test_prog_moves_migrated.py": {
        "class": "NEW_AT_THIS_HEAD_NOT_CAUSED_BY_THE_TRIAGE_RUNG",
        "last_green_commit": "GREEN in this rung's own BEFORE sweep at the same commit",
        "diagnosis":
            "test_named_regression_sweep_only_known_pins_drift spawns a NESTED multi-file "
            "pytest run and fails on test_reject_informs_repair_migrated.py::"
            "test_no_wrong_accept_regression_vs_v1_7_0_baseline, which is GREEN when run "
            "alone -- i.e. cross-file state leakage inside the nested sweep, not a defect in "
            "either file's own subject. CONTROLLED: the only change of this rung plausibly in "
            "its path (domains/morpheme_decomposition.py) was reverted and the failure "
            "reproduced unchanged, twice.",
    },
    "tests/test_rust_engine_ext_7b.py": {
        "class": "PERF_THRESHOLD_AT_THE_BOUNDARY",
        "last_green_commit": "GREEN in this rung's own BEFORE sweep at the same commit",
        "diagnosis":
            "test_attr_index_perf_beats_linear asserts a >=3x speedup and measures 2.7-2.8x "
            "(linear 0.027-0.028ms vs indexed 0.010-0.011ms), reproducibly, at LOW load as "
            "well as high. A hard-coded ratio sitting ~7% from its own boundary is a scalar "
            "knob where a shape belongs (CLAUDE.md, SHAPES NOT NUMBERS) -- it will flip on "
            "any machine, either way, forever. NOT relaxed here: choosing the bar is the "
            "creator's call, and moving it to make a number green is the thing this tree "
            "forbids.",
    },
    "tests/test_arc_magnitude_migrated.py": {
        "class": "SWEEP_SELF_CONTAMINATION_TRACKED_FILE_MUTATED_BY_THE_RUN",
        "last_green_commit": "GREEN on a clean tree, verified after the sweep",
        "diagnosis":
            "test_mg5_the_EXISTING_seeds_are_BYTE_IDENTICAL_to_HEAD fails on a git diff of "
            "seeds/program_synthesis.json. RUNNING THE TEST SUITE MUTATES GIT-TRACKED FILES: "
            "after every full sweep, `git status` showed seeds/metonymy_patterns.json and "
            "tests/fixtures/comprehension_divergence/divergence.json modified. tests/"
            "conftest.py's session-wide OZMA_SEED_PERSIST_DISABLED guard does not cover "
            "these writers. Re-run on a restored tree: PASSES. A byte-identity gate in a "
            "suite that mutates tracked files is measuring the run, not the tree.",
    },
    "tests/test_guard_coalesce_lint_migrated.py": {
        "class": "LINT_BASELINE_DRIFT",
        "last_green_commit": "UNKNOWN (masked by the engine false-stale refusal before this rung)",
        "diagnosis":
            "509 NEW coalesced guard reads vs results/guard_coalesce_baseline, and 6 baseline "
            "entries that no longer exist. CONFIRMED NOT the LIST-rooted seed file: the count "
            "is unchanged when that file is skipped. The lint's recorded debt has simply "
            "drifted from the tree. Action is to re-baseline the lint, deliberately, which is "
            "a decision about accepted debt.",
    },
    "tests/test_graph_rewrite.py": {
        "class": "AMBIGUOUS_NEEDS_THE_CREATOR",
        "last_green_commit": "UNKNOWN (pre-export history)",
        "diagnosis":
            "Two tests build a TypedGraph() and hand it to domains.linear_algebra.make_matrix, "
            "which calls graph.add_node -- TypedGraph has no public add_node (mutation is "
            "_insert_node; the public path is the Rust Substrate). The sibling "
            "tests/test_linear_algebra.py is GREEN because it uses la.new_graph() (a native "
            "Substrate). The genuinely open question, which only the creator can answer: is "
            "test_graph_rewrite's coverage of the PYTHON search layer (gr.search_count) still "
            "wanted now that linear_algebra runs native, or is that layer itself retired? "
            "NOT fixed and NOT retired on a triage rung's judgement.",
    },
    "tests/test_codec_graph_resident.py": {
        "class": "HEVC_GRAMMAR_INCOMPLETE_SECOND_CAUSE",
        "last_green_commit": "f23849f5 (STATIC, not a behavioural re-run)",
        "re_read_2026_08_13":
            "STILL 8 nodes, and the CAUSE BELOW IS THE OLD ONE. The dead-install bug it "
            "describes was fixed in rung 121000-121999; what remains is the SECOND cause that "
            "fix unmasked -- an incomplete HEVC / fixed-arity-array grammar. Today's messages "
            "are `TypeError: cannot convert NoneType object to bytes` (x4), `assert 0 == 1`, "
            "`assert 4 == 128`, `assert [(0, 0)] == []`, and a loop-count literal -- none of "
            "them the 'expected 10 rule firings, got 0' signature below. The paragraph is kept "
            "verbatim as the historical record it is (a historical record is never converted); "
            "the ACTIONABLE diagnosis is this line.",
        "diagnosis":
            "runners/dsl/src/codec.rs::install_field_grammar_rules does "
            "`substrate.rules.push(rule)`, bypassing Substrate::add_rule -- the function "
            "whose own comment calls itself 'the sole path that pushes into self.rules, "
            "so it owns making a newly-installed rule live'. All 20 codec rules install "
            "with active:false and the matcher skips every one. PROVEN: same 20 rules via "
            "add_rule -> 10 firings, 10/10 PPS fields byte-correct; via the Rust install "
            "-> 0 firings, 0 fields. export_rules() reads 20x False vs 20x True. "
            "THE GATE'S EXPECTATION ('expected 10 rule firings, got 0') WAS RIGHT ON BOTH "
            "NUMBERS. Do NOT retract the claim and do NOT edit the test. "
            "Broke at 79a05702 ('codec field-grammar Rules native in Rust runner', "
            "2026-06-01), SIX commits after the file was born green at f23849f5 the same "
            "day -- so it is NOT 'never green', it is 'green for six commits, then "
            "absorbed into a baseline for ~2875 commits'. "
            "See VISION_BASELINE_LIST_RESULTS.md section 1.",
    },
}


def build(raw_path: str, out_path: Path, messages_from: str | None = None,
          condition: str | None = None) -> int:
    raw = json.loads(Path(raw_path).read_text())

    # The FIRST full sweep captured correct node ids but truncated messages at column 80
    # (see failure_baseline_sweep.sweep_one). A targeted re-run of the red files with
    # COLUMNS=250 supplies the diagnoses. Overlaying is only legitimate if the two runs
    # AGREE on the red set, so that agreement is CHECKED here and RECORDED in the
    # artifact -- it is also an independent reproducibility measurement of the verdict.
    overlay, repro = {}, None
    if messages_from:
        m = json.loads(Path(messages_from).read_text())
        overlay = {n["node"]: n["message"]
                   for r in m["results"] for n in r["nodes"]}
        first = {n["node"] for r in raw["results"] for n in r["nodes"]}
        repro = {
            "messages_from": messages_from,
            "nodes_first_sweep": len(first),
            "nodes_re_run": len(overlay),
            "identical_node_set": sorted(first) == sorted(overlay),
            "only_in_first": sorted(first - set(overlay))[:20],
            "only_in_re_run": sorted(set(overlay) - first)[:20],
        }
    entries, not_established, nonzero, all_skipped = [], [], [], []
    green_files = 0
    for r in raw["results"]:
        if r["status"] == "NOT_ESTABLISHED":
            not_established.append({"file": r["file"], "reason": r["reason"],
                                    "seconds": r["seconds"]})
            continue
        if r["status"] == "GREEN":
            green_files += 1
            continue
        if r["status"] == "ALL_SKIPPED":
            # every test guarded (absent optional dep / unresolvable pin) — not a
            # red, and NOT silently green either: recorded, so a reader can see how
            # much of the tree was guarded rather than measured.
            all_skipped.append(r["file"])
            continue
        if r["status"] == "NONZERO_NO_NODES":
            nonzero.append({"file": r["file"], "returncode": r["returncode"],
                            "tail": r.get("tail", "")[:300]})
            continue
        for n in r["nodes"]:
            msg = overlay.get(n["node"], n["message"])
            e = {
                "node": n["node"],
                "file": r["file"],
                "kind": n["kind"],
                "message": msg,
                "class": classify(msg),
                # LAST-GREEN is UNKNOWN unless MEASURED on a single engine. The Scope B
                # peer retracted two headline durations to exactly this confound
                # (historical tree x current engine), so it is never inferred here.
                "last_green_commit": "UNKNOWN",
                "file_seconds": r["seconds"],
            }
            e.update(_ANNOTATIONS.get(r["file"], {}))
            entries.append(e)
    entries.sort(key=lambda e: e["node"])
    payload = {
        "_README": "A BASELINE IS A LIST, NEVER A COUNT. Every entry must be fixed, "
                   "re-pinned or deleted. `total` is DERIVED from `entries`; do not "
                   "author it, and never quote it in place of the list.",
        "head": raw["head"],
        "engine": _engine_line(),
        # THE CONDITION IS PART OF THE NUMBER. CLAUDE.md measures this same tree at
        # 144-145 red node ids with data/ symlinked and 565 without — a 3.9x spread
        # on one engine at one commit — so a baseline whose condition is hard-coded
        # to the condition of the FIRST sweep that ever ran is a rumour the moment
        # anyone measures under another one. Passed in, never assumed.
        "condition": condition or "no data/ symlink; own engine build; per-file subprocess",
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "loadavg_start": raw["loadavg_start"],
        "loadavg_end": raw["loadavg_end"],
        "workers": raw["workers"],
        "per_file_timeout_s": raw["per_file_timeout_s"],
        "reproducibility": repro,
        "total": len(entries),                      # DERIVED, not authored
        "by_class": dict(Counter(e["class"] for e in entries)),
        "files_green": green_files,
        "files_red": len({e["file"] for e in entries}),
        "coverage": {
            "files_swept": raw["files"],
            "NOT_ESTABLISHED": not_established,     # never green, never red
            "NONZERO_NO_NODES": nonzero,
            "ALL_SKIPPED": all_skipped,          # guarded, not measured, not red
        },
        "entries": entries,
    }
    out_path.write_text(json.dumps(payload, indent=1))
    print(f"wrote {out_path}: {len(entries)} node ids across "
          f"{payload['files_red']} files; "
          f"{len(not_established)} NOT_ESTABLISHED; classes={payload['by_class']}")
    return 0


def _engine_line() -> str:
    """The engine THE SWEEP ACTUALLY USED — which is not what a bare interpreter loads.

    BUG FOUND IN THIS FUNCTION MID-RUN, and it is the disease this arc keeps finding: an
    instrument mis-recording the very thing it exists to record. Without
    `engine_preamble()` a plain `python3` resolves `substrate_rs` through the global
    `.pth`, which is an ABSOLUTE PATH INTO THE CANONICAL TREE (protocol 10.1). This
    function therefore reported `engine b06e02ed9323 @ <CANONICAL>` while every swept file
    — run under pytest, whose `conftest.py` DOES call `engine_preamble()` — was measured on
    this worktree's own `engine d657468d9e1f`. The artifact would have carried a provenance
    line naming a binary that produced none of its numbers, inside the one field its own
    gate requires.

    Protocol 10.1 rule 3 says it in as many words: *any non-pytest entrypoint (a rung
    script) must call `engine_preamble()` itself.* This is a rung script. It now does.
    """
    sys.path.insert(0, str(ROOT))
    try:
        from domains import engine_provenance
        engine_provenance.engine_preamble()          # <- the missing line
        return engine_provenance.provenance_line()
    except Exception as e:                                  # pragma: no cover
        return f"UNAVAILABLE: {e}"


def verify(list_path: Path, only_fast: float | None, limit: int | None) -> int:
    """Re-run the listed node ids. NEW reds and STALE entries are BOTH failures."""
    data = json.loads(list_path.read_text())
    entries = data["entries"]
    if only_fast is not None:
        entries = [e for e in entries if e["file_seconds"] <= only_fast]
    if limit:
        entries = entries[:limit]
    by_file: dict[str, list[str]] = {}
    for e in entries:
        by_file.setdefault(e["file"], []).append(e["node"])

    listed = {e["node"] for e in entries}
    still_red, now_green, new_red = set(), set(), set()
    for f, nodes in sorted(by_file.items()):
        r = subprocess.run(
            [sys.executable, "-W", "ignore", "-m", "pytest", "-q", "-p", "no:randomly",
             "--tb=no", "-rfE", f], cwd=ROOT, capture_output=True, text=True, timeout=900)
        red_now = {ln.split()[1] for ln in (r.stdout + r.stderr).splitlines()
                   if ln.strip().startswith(("FAILED ", "ERROR "))
                   and len(ln.split()) > 1}
        for n in nodes:
            (still_red if n in red_now else now_green).add(n)
        new_red |= {n for n in red_now if n not in listed and n.split("::")[0] == f}

    print(f"held (still red): {len(still_red)}")
    print(f"STALE (listed but now GREEN — the list must be updated): {len(now_green)}")
    for n in sorted(now_green):
        print(f"    STALE {n}")
    print(f"NEW (red but not on the list): {len(new_red)}")
    for n in sorted(new_red):
        print(f"    NEW   {n}")
    print("LOADAVG:", os.getloadavg())
    return 1 if (now_green or new_red) else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--raw", default="results/failure_baseline_sweep_raw.json")
    b.add_argument("--out", default=str(LIST_PATH))
    b.add_argument("--messages-from", default=None)
    b.add_argument("--condition", default=None,
                   help="the measurement condition, stamped into the artifact "
                        "(data/ symlink? optional deps? engine?) — protocol 10/12")
    v = sub.add_parser("verify")
    v.add_argument("--list", default=str(LIST_PATH))
    v.add_argument("--only-fast", type=float, default=None,
                   help="only re-run entries whose FILE ran in <= this many seconds")
    v.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    if a.cmd == "build":
        return build(a.raw, Path(a.out), a.messages_from, a.condition)
    return verify(Path(a.list), a.only_fast, a.limit)


if __name__ == "__main__":
    raise SystemExit(main())
