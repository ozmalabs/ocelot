"""code_curriculum_run — CODE-CURRICULUM: the jabberwock LEARNS, measured.

The CODE arc (7b9d85a1ee / 670daef769 / dd44690321 / d74856edb2) gave the
agent a read register with a mintable construction codebook, understanding-
as-prediction, function-grain writing, and a growth loop (teach-by-example,
compose-from-predication). THIS wave exercises that growth loop end-to-end,
sanctioned surfaces only, and MEASURES the delta:

  BASELINE  -- scan domains/ (~560 files, ~6250 top-level functions --
              scripts/ was tried and found pathologically slow for at least
              one file; scoped out, see baseline_measurement's own note)
              through the READ faculty; run the fixed write-request battery.
  TEACH     -- ~10-12 hand-picked example functions, taught by example
              through chat (the CODE-4 path) -- the warm-up/control.
  PREDICATE -- teach one new morphological multiplier word, exercise the
              gap through the NEWLY-WIRED daemon spine (part A).
  READ      -- feed unseen-shape functions (while/try/comprehension) through
              the read register; unseen skeletons MINT, naming gaps file.
  PUBLISHED -- THE HEADLINE: three REAL lesson documents (Think Python 2e,
              chapter 6, "Fruitful functions" -- bundled verbatim excerpts,
              tests/fixtures/code_curriculum/, provenance.json) are read as
              MIXED-REGISTER documents: code blocks are found BY SHAPE
              (domains.register_source's existing register codebook) and
              taught; exercise sentences are attempted through the real
              conversational request path.
  AFTER     -- re-run BASELINE's scans/battery; report the delta, self-
              account, and the honest gaps-frontier inventory.

Every learned artifact (taught ShapeSignatures, gap ledger, before/after
scans) is captured to `--out-dir` as JSON. Seed persistence is disabled for
the run itself (OZMA_SEED_PERSIST_DISABLED=1) -- this driver teaches a LIVE
agent and records what it learned; it never mutates the checked-in seeds.

Run: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 \
     python3 scripts/code_curriculum_run.py [--out-dir results/code_curriculum]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
          os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

from substrate.world_adapter import WorldAdapter          # noqa: E402
from substrate.boot_all import load_all_seeds             # noqa: E402
from domains import code_write_growth as cwg              # noqa: E402
from domains import code_reading as cdr                   # noqa: E402
from domains import code_curriculum as cc                 # noqa: E402
from domains.teach import teach                           # noqa: E402
import scripts.jabberwock_daemon as jd                     # noqa: E402


def _say(who: str, text: str) -> None:
    pad = "\n           ".join(str(text).splitlines())
    print(f"  {who:>8}: {pad}")


# --------------------------------------------------------------------------- #
#  THE FIXED NL WRITE-REQUEST BATTERY (~25 requests spanning held + unheld
#  shapes) -- the SAME battery run before and after teaching; the delta is
#  the measured capability gain.
# --------------------------------------------------------------------------- #
WRITE_BATTERY = [
    # held starter vocabulary (code_write_constructions.json) -- should be
    # answerable both before and after.
    "Write a function that returns the larger of two numbers.",
    "Write a function that returns the smaller of two numbers.",
    "Write a function that returns the sum of two numbers.",
    "Write a function that returns the product of two numbers.",
    "Write a function that returns the absolute value of a number.",
    "Write a function that returns the total of a list of numbers.",
    "Write a function that returns the count of items in a list.",
    # the hand-curated TEACH batch's own requests (unheld before, held after).
    "Write a function that clamps a number between a lower and upper bound.",
    "Write a function that flips the sign of a number.",
    "Write a function that computes the squared difference of two numbers.",
    "Write a function that computes the hypotenuse of a right triangle.",
    "Write a function that returns the largest of three numbers.",
    "Write a function that linearly interpolates between two numbers.",
    "Write a function that computes the absolute difference of two numbers.",
    "Write a function that sums the squares of a list of numbers.",
    "Write a function that counts the positive numbers in a list.",
    "Write a function that averages two numbers.",
    "Write a function that checks whether a number is even.",
    "Write a function that computes the perimeter of a rectangle.",
    # the PREDICATION-taught word.
    "Write a function that quintuples a number.",
    # genuinely out-of-scope, both before and after (never claimed as a win).
    "Write a function that reverses a string.",
    "Write a function that sorts a list of numbers.",
    "Write a function that removes duplicates from a list.",
    "Write a function that computes a factorial.",
    "Write a function that checks whether a string is a palindrome.",
    "Write a function that finds the maximum of a list of numbers.",
]

# --------------------------------------------------------------------------- #
#  TEACH-BY-EXAMPLE BATCH -- the hand-curated warm-up/control (10-12 items,
#  chosen to widen the write vocabulary WITHIN the emittable boundary; two
#  are chosen KNOWING they fall outside it, so the honest gap-filing path is
#  exercised too, never hidden).
# --------------------------------------------------------------------------- #
TEACH_BATCH = [
    ("Write a function that clamps a number between a lower and upper bound.",
     "clamp",
     "def clamp(x, lo, hi):\n"
     "    return lo if x < lo else (hi if x > hi else x)\n"),
    ("Write a function that flips the sign of a number.",
     "sign_flip",
     "def sign_flip(x):\n    return -x\n"),
    ("Write a function that computes the squared difference of two numbers.",
     "squared_difference",
     "def squared_difference(a, b):\n    return (a - b) ** 2\n"),
    ("Write a function that computes the hypotenuse of a right triangle.",
     "hypotenuse",
     "def hypotenuse(a, b):\n    return (a ** 2 + b ** 2) ** 0.5\n"),
    ("Write a function that returns the largest of three numbers.",
     "max_of_three",
     "def max_of_three(a, b, c):\n"
     "    return a if a > b and a > c else (b if b > c else c)\n"),
    ("Write a function that linearly interpolates between two numbers.",
     "lerp",
     "def lerp(a, b, t):\n    return a + (b - a) * t\n"),
    ("Write a function that computes the absolute difference of two numbers.",
     "abs_diff",
     "def abs_diff(a, b):\n    return abs(a - b)\n"),          # OOV: builtin abs() Call
    ("Write a function that sums the squares of a list of numbers.",
     "sum_of_squares",
     "def sum_of_squares(items):\n"
     "    total = 0\n"
     "    for x in items:\n"
     "        total += x ** 2\n"
     "    return total\n"),
    ("Write a function that counts the positive numbers in a list.",
     "count_positives",
     "def count_positives(items):\n"
     "    count = 0\n"
     "    for x in items:\n"
     "        if x > 0:\n"
     "            count += 1\n"
     "    return count\n"),                                     # OOV: conditional accumulate
    ("Write a function that averages two numbers.",
     "average_two",
     "def average_two(a, b):\n    return (a + b) / 2\n"),
    ("Write a function that checks whether a number is even.",
     "is_even",
     "def is_even(n):\n    return n % 2 == 0\n"),
    ("Write a function that computes the perimeter of a rectangle.",
     "perimeter_rect",
     "def perimeter_rect(w, h):\n    return 2 * (w + h)\n"),
]

# --------------------------------------------------------------------------- #
#  READ-CODEBOOK GROWTH -- unseen skeletons (while / try / comprehension),
#  fed through the read register directly (no write request involved).
# --------------------------------------------------------------------------- #
READ_GROWTH_BATCH = [
    ("countdown", "def countdown(n):\n    while n > 0:\n        n -= 1\n    return n\n"),
    ("safe_div", "def safe_div(a, b):\n"
                "    try:\n        return a / b\n"
                "    except ZeroDivisionError:\n        return 0\n"),
    ("evens", "def evens(items):\n    return [x for x in items if x % 2 == 0]\n"),
]

LESSON_FILES = [
    "lesson_return_values.txt",
    "lesson_incremental_development.txt",
    "lesson_boolean_functions.txt",
]
LESSON_DIR = os.path.join(ROOT, "tests", "fixtures", "code_curriculum")


def baseline_measurement(a) -> dict:
    # SCOPING NOTE (measured, not guessed): a full `domains/` scan (560
    # files, ~6250 top-level functions) completes in ~50s. `scripts/`
    # (1769 files -- mostly one-off run/demo/experiment scripts, not the
    # agent's code faculty in the same sense) was tried and did not finish
    # in several minutes -- at least one file/function there is genuinely
    # pathological for this scan (not investigated further; out of this
    # wave's scope). The baseline/after measurement is therefore scoped to
    # `domains/` -- still thousands of real functions, still deterministic,
    # and the part this wave's growth actually targets.
    scan = cc.scan_repo_functions(a, ["domains"])
    battery = cc.run_write_battery(a, WRITE_BATTERY)
    return {"scan": {"n_files": scan["n_files"], "n_functions": scan["n_functions"],
                     "counts": scan["counts"]},
           "battery": {"n": battery["n"], "n_ok": battery["n_ok"],
                      "ok_requests": [r["request"] for r in battery["rows"] if r["ok"]]}}


def run(out_dir: str) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    report: dict = {"started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

    print("== BOOT (full seed set) ==")
    a = WorldAdapter(seeds=())
    load_all_seeds(a)

    print("\n== BASELINE MEASUREMENT ==")
    before = baseline_measurement(a)
    print(f"  scan: {before['scan']['n_functions']} functions over "
         f"{before['scan']['n_files']} files -> {before['scan']['counts']}")
    print(f"  battery: {before['battery']['n_ok']}/{before['battery']['n']} answerable")
    report["before"] = before

    print("\n== TEACH-BY-EXAMPLE BATCH (warm-up/control) ==")
    teach_results = []
    for req, name, src in TEACH_BATCH:
        _say("human", req)
        abstain = a.converse(req)
        _say("agent", abstain)
        _say("human", src.rstrip())
        res = cwg.teach_write_shape_from_example(a, src, request_text=req)
        if res.get("ok"):
            _say("agent", "learned the shape %r (validated by running)." % res["shape"])
            reply = a.converse(req)
            _say("agent", reply)
        else:
            _say("agent", "abstains: %s" % res.get("reason"))
        teach_results.append({"request": req, "name": name, "ok": bool(res.get("ok")),
                              "reason": res.get("reason"), "shape": res.get("shape")})
    a.comprehend()
    report["teach_batch"] = teach_results

    print("\n== PREDICATION VOCABULARY (NL-taught, exercised through the "
         "part-A daemon spine) ==")
    pred_req = "Write a function that quintuples a number."
    _say("human", pred_req)
    _say("agent", a.converse(pred_req))
    concept = teach(a, "Concept", {"name": "quintuple", "multiplier_factor": 5.0,
                                   "description": "multiply by five"},
                    category="write_shape_predication")
    print("  [teach] taught Concept 'quintuple' (multiplier_factor=5.0):", concept["saved"])
    sc_id = None
    for n in a.s.nodes("SelfConcern"):
        at = a.s.node(n)["attrs"]
        if at.get("kind") == "code_write" and at.get("content") == pred_req:
            sc_id = n
    promote_res = None
    if sc_id is not None:
        _say("human", "Work on the quintuples gap.")
        promote_res = jd.promote_self_concern(a, str(sc_id.value if hasattr(sc_id, "value") else sc_id))
        jd._concern_tick(a)
        a.comprehend()
        _say("agent", a.converse(pred_req))
    report["predication"] = {"request": pred_req, "promote": promote_res}

    print("\n== READ-CODEBOOK GROWTH (unseen shapes) ==")
    read_growth = []
    for name, src in READ_GROWTH_BATCH:
        r = cdr.read_function(a, src, name)
        row = {"name": name, "construction": r.get("construction"),
              "minted": r.get("minted"), "note": r.get("note")}
        print(f"  {name}: construction={row['construction']!r} minted={row['minted']} "
             f"note={row['note']!r}")
        read_growth.append(row)
    a.comprehend()
    report["read_growth"] = read_growth
    report["naming_gaps_after_read_growth"] = [g["content"] for g in cwg.pending_naming_gaps(a)]

    print("\n== PUBLISHED CURRICULUM (Think Python 2e, ch.6 'Fruitful "
         "functions' -- REAL bundled excerpts) ==")
    lesson_results = []
    for fname in LESSON_FILES:
        path = os.path.join(LESSON_DIR, fname)
        text = open(path).read()
        print(f"  -- lesson: {fname} --")
        res = cc.learn_from_lesson(a, text, lesson_source=fname,
                                   seeds_dir=None, min_words=6)
        for row in res["learned"]:
            print(f"     function -> ok={row['ok']} shape={row.get('shape')} "
                 f"reason={row.get('reason')!r}")
        for row in res["requests"]:
            print(f"     exercise -> {row['request'][:70]!r} -> {row['reply'][:80]!r}")
        lesson_results.append({
            "lesson_source": fname,
            "learned": [{"ok": r["ok"], "shape": r.get("shape"), "reason": r.get("reason"),
                        "region_index": r.get("region_index")} for r in res["learned"]],
            "requests": res["requests"],
        })
    a.comprehend()
    report["published_lessons"] = lesson_results

    print("\n== AFTER MEASUREMENT ==")
    after = baseline_measurement(a)
    print(f"  scan: {after['scan']['n_functions']} functions -> {after['scan']['counts']}")
    print(f"  battery: {after['battery']['n_ok']}/{after['battery']['n']} answerable "
         f"(was {before['battery']['n_ok']}/{before['battery']['n']})")
    report["after"] = after

    print("\n== SELF-ACCOUNT ==")
    cap_note = a.converse("What can you do with code now?")
    _say("agent", cap_note)
    gaps_note = a.converse("What code gaps do you have?")
    _say("agent", gaps_note)
    report["self_account"] = {"capabilities": cap_note, "gaps": gaps_note}

    cap_report = cc.capability_report(a)
    report["capability_report"] = cap_report
    print("\n== CAPABILITY REPORT (provenance-bucketed) ==")
    for k in ("learned_by_teaching", "learned_by_composition", "learned_from_published",
             "minted_by_reading", "filed_as_gap"):
        print(f"  {k}: {len(cap_report[k])}")

    report["finished"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    out_path = os.path.join(out_dir, "code_curriculum_report.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=1, default=str)
    print(f"\n== report written: {out_path} ==")
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=os.path.join(ROOT, "results", "code_curriculum"))
    args = ap.parse_args()
    run(args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
