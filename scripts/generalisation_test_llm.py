"""StructuredDataWorld generalisation test — LLM teacher variant.

Same harness as scripts/generalisation_test.py but:
  * uses teacher_via_claude (real LLM via the `claude` CLI) for grounding;
  * runs on a SMALL bank (~20 training + 8 held-out) sampled across the
    full format / corruption variety to keep wall-clock time reasonable
    (claude --print is ~3-10s per call).

Reports the same metric table as the stub run, plus a side-by-side
comparison against the stub baseline (matched against the actual
generalisation_test.log.json the stub run produced).

This is a world-adapter / harness script per CLAUDE.md: no agent
reasoning, just measurement. The substrate's strategy table is the
learned knowledge; we just compare what each teacher taught it.
"""
from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native
from domains.structured_data_world import (
    StructuredDataWorld,
    teacher_via_claude,
    teacher_stub,
)
from scripts.generalisation_test import (
    training_bank,
    heldout_bank,
    _NoTeacher,
    run_training,
    run_heldout,
    short,
)


# ---------------------------------------------------------------------------
# Sampling — pick variety-balanced subsets of the existing banks.
# ---------------------------------------------------------------------------


def _stratified_sample(bank: list[dict], n_per_shape: int, rng: random.Random
                       ) -> list[dict]:
    """Group by shape, take up to n_per_shape from each group. Returns
    the entries in original-bank order so the world's traversal still
    has the natural clean-before-corrupt progression."""
    by_shape: dict[str, list[dict]] = {}
    order: list[str] = []
    for entry in bank:
        shape = entry.get("shape") or "_unshape"
        if shape not in by_shape:
            by_shape[shape] = []
            order.append(shape)
        by_shape[shape].append(entry)

    chosen: list[dict] = []
    for shape in order:
        group = by_shape[shape]
        picks = group if len(group) <= n_per_shape else rng.sample(group,
                                                                   n_per_shape)
        chosen.extend(picks)
    return chosen


def _trim_to_size(bank: list[dict], target: int, rng: random.Random
                  ) -> list[dict]:
    """Reduce bank to ~target entries by dropping random entries.
    Stratified by shape — drop from the largest shape-group first so
    every shape stays represented."""
    if len(bank) <= target:
        return bank
    by_shape: dict[str, list[dict]] = {}
    for entry in bank:
        shape = entry.get("shape") or "_unshape"
        by_shape.setdefault(shape, []).append(entry)
    while sum(len(g) for g in by_shape.values()) > target:
        biggest = max(by_shape.values(), key=len)
        if len(biggest) <= 1:
            break
        drop = rng.randrange(len(biggest))
        del biggest[drop]
    # Re-flatten preserving original ordering.
    keep_ids = {id(e) for g in by_shape.values() for e in g}
    return [e for e in bank if id(e) in keep_ids]


def sample_training_bank(rng: random.Random, target: int = 20) -> list[dict]:
    """20-ish training items across the full variety: one per shape
    where possible, then top-up to target from the largest groups so
    variety dominates."""
    full = training_bank()
    sampled = _stratified_sample(full, 1, rng)
    if len(sampled) < target:
        # Pad with extras from each shape, round-robin.
        by_shape: dict[str, list[dict]] = {}
        for e in full:
            by_shape.setdefault(e.get("shape") or "_", []).append(e)
        chosen_ids = {id(e) for e in sampled}
        # Round-robin add up to target
        round_idx = 0
        while len(sampled) < target:
            added_this_round = False
            for shape, group in by_shape.items():
                remaining = [e for e in group if id(e) not in chosen_ids]
                if len(remaining) <= round_idx:
                    continue
                pick = remaining[round_idx]
                sampled.append(pick)
                chosen_ids.add(id(pick))
                added_this_round = True
                if len(sampled) >= target:
                    break
            if not added_this_round:
                break
            round_idx += 1
    if len(sampled) > target:
        sampled = _trim_to_size(sampled, target, rng)
    # Re-sort into the full bank's original order so dependency-style
    # clean-before-corrupt progression is preserved.
    order = {id(e): i for i, e in enumerate(full)}
    sampled.sort(key=lambda e: order[id(e)])
    return sampled


def sample_heldout_bank(rng: random.Random, target: int = 8) -> list[dict]:
    """8-ish held-out items balanced across same_shape / novel_corruption
    / ambiguous categories — the three slices the comparison table
    reports on."""
    full = heldout_bank()
    by_cat: dict[str, list[dict]] = {}
    order: list[str] = []
    for e in full:
        cat = e.get("category") or "_"
        if cat not in by_cat:
            by_cat[cat] = []
            order.append(cat)
        by_cat[cat].append(e)
    # Roughly equal per category — 8 = 3 same_shape + 3 novel_corruption + 2 ambiguous.
    per_cat = {"same_shape": 3, "novel_corruption": 3, "ambiguous": 2}
    chosen: list[dict] = []
    for cat in order:
        group = by_cat[cat]
        k = per_cat.get(cat, max(1, target // max(1, len(order))))
        k = min(k, len(group))
        picks = group if k >= len(group) else rng.sample(group, k)
        chosen.extend(picks)
    # Sort back into original order.
    pos = {id(e): i for i, e in enumerate(full)}
    chosen.sort(key=lambda e: pos[id(e)])
    return chosen


# ---------------------------------------------------------------------------
# Stub baseline numbers — read from the existing generalisation_test
# log so the comparison table reports actual measured values, not
# the spec's placeholders.
# ---------------------------------------------------------------------------


def load_stub_baseline() -> dict[str, Any] | None:
    log_path = ROOT / "scripts" / "generalisation_test.log.json"
    if not log_path.exists():
        return None
    data = json.loads(log_path.read_text())
    n_train = len(data["training"])
    train_match = sum(1 for e in data["training"] if e["matched"])
    train_teach = sum(e["teacher_calls"] for e in data["training"])
    n_held = len(data["heldout"])
    by_cat: dict[str, list[int]] = {}
    for e in data["heldout"]:
        c = e["category"]
        s = by_cat.setdefault(c, [0, 0])
        s[0] += 1
        if e["matched"]:
            s[1] += 1
    return {
        "n_train": n_train,
        "train_match": train_match,
        "train_teach": train_teach,
        "n_held": n_held,
        "held_match": sum(1 for e in data["heldout"] if e["matched"]),
        "by_cat": {c: tuple(v) for c, v in by_cat.items()},
    }


# ---------------------------------------------------------------------------
# Wrapped LLM teacher — logs each call for the report.
# ---------------------------------------------------------------------------


class _LoggingTeacher:
    """Wraps teacher_via_claude with a per-call log so the script
    can report wall-clock + per-input outcomes after the run."""

    def __init__(self):
        self.entries: list[dict] = []

    def __call__(self, gap: str, text: str) -> dict:
        t0 = time.time()
        spec = teacher_via_claude(gap, text)
        dt = time.time() - t0
        self.entries.append({
            "gap": gap,
            "text_short": short(repr(text), 60),
            "elapsed_s": round(dt, 2),
            "format": spec.get("format"),
            "corruption": spec.get("corruption_pattern"),
            "parsed_repr_short": short(repr(spec.get("parsed")), 60),
            "reasoning": spec.get("reasoning"),
        })
        return spec


# ---------------------------------------------------------------------------
# Format + compare
# ---------------------------------------------------------------------------


def _pct(num: int, denom: int) -> str:
    return f"{100 * num / denom:.1f}%" if denom else "n/a"


def _delta(stub_num: int, stub_den: int, llm_num: int, llm_den: int) -> str:
    if not stub_den or not llm_den:
        return "n/a"
    d = 100 * (llm_num / llm_den - stub_num / stub_den)
    sign = "+" if d >= 0 else ""
    return f"{sign}{d:.1f} pp"


def report_comparison(stub: dict | None,
                      train_log: list[dict],
                      held_log: list[dict],
                      n_train_llm: int,
                      n_held_llm: int,
                      teacher_log: list[dict],
                      wall_clock_s: float,
                      out_json: Path) -> None:
    print("=" * 76)
    print("StructuredDataWorld generalisation test — LLM TEACHER")
    print("=" * 76)
    print()

    n_train = len(train_log)
    train_match = sum(1 for e in train_log if e["matched"])
    train_teach = sum(e["teacher_calls"] for e in train_log)

    n_held = len(held_log)
    held_match = sum(1 for e in held_log if e["matched"])
    held_would_call = sum(1 for e in held_log if e["gaps_asked"])

    by_cat_llm: dict[str, list[int]] = {}
    for e in held_log:
        c = e["category"]
        s = by_cat_llm.setdefault(c, [0, 0])
        s[0] += 1
        if e["matched"]:
            s[1] += 1
    by_cat_llm = {c: tuple(v) for c, v in by_cat_llm.items()}

    print(f"LLM-teacher wall clock: {wall_clock_s:.1f}s "
          f"({len(teacher_log)} teacher calls, "
          f"~{(wall_clock_s/max(1,len(teacher_log))):.1f}s/call)")
    print()

    # Comparison table
    print("-" * 76)
    print(f"{'metric':32s} {'stub_baseline':>16s} {'llm_teacher':>16s}"
          f" {'delta':>10s}")
    print("-" * 76)
    if stub is None:
        print("  (no stub baseline log found; run scripts/generalisation_test.py"
              " first)")
        return

    # Training matched
    print(f"{'training matched':32s}"
          f" {_pct(stub['train_match'], stub['n_train']):>16s}"
          f" {_pct(train_match, n_train):>16s}"
          f" {_delta(stub['train_match'], stub['n_train'], train_match, n_train):>10s}")
    # Training teacher calls
    stub_tc = f"{stub['train_teach']}/{stub['n_train']}"
    llm_tc = f"{train_teach}/{n_train}"
    print(f"{'training teacher calls':32s}"
          f" {stub_tc:>16s}"
          f" {llm_tc:>16s}"
          f" {_delta(stub['train_teach'], stub['n_train'], train_teach, n_train):>10s}")
    # Held-out by category
    cat_order = ["same_shape", "novel_corruption", "ambiguous"]
    for cat in cat_order:
        s = stub["by_cat"].get(cat)
        l = by_cat_llm.get(cat)
        label = f"held-out {cat}"
        sval = _pct(s[1], s[0]) if s else "n/a"
        lval = _pct(l[1], l[0]) if l else "n/a"
        dval = (_delta(s[1], s[0], l[1], l[0])
                if s and l else "n/a")
        print(f"{label:32s} {sval:>16s} {lval:>16s} {dval:>10s}")
    # Held-out overall
    print(f"{'held-out overall':32s}"
          f" {_pct(stub['held_match'], stub['n_held']):>16s}"
          f" {_pct(held_match, n_held):>16s}"
          f" {_delta(stub['held_match'], stub['n_held'], held_match, n_held):>10s}")
    print("-" * 76)
    print()

    # Per-shape matching detail on held-out, both runs side-by-side
    print("Held-out per-input outcomes (llm_teacher run):")
    for e in held_log:
        ok = "PASS" if e["matched"] else "MISS"
        print(f"  [{ok}] cat={e['category']:18s} shape={(e.get('shape') or '-'):28s}"
              f" text={short(repr(e['text']), 32)}")
        if not e["matched"]:
            print(f"         expected={short(repr(e['expected']), 50)}"
                  f"  got={short(repr(e['parsed']), 50)}")
    print()

    print("Teacher-call log (chronological):")
    for i, t in enumerate(teacher_log, 1):
        print(f"  #{i:02d}  {t['elapsed_s']:>5.1f}s  fmt={t['format']:8s}"
              f"  corr={t['corruption']:18s}  text={t['text_short']}")
    print()

    # Dump JSON
    summary = {
        "n_train_llm": n_train,
        "n_held_llm": n_held,
        "train_match_llm": train_match,
        "train_teach_llm": train_teach,
        "held_match_llm": held_match,
        "held_would_call_llm": held_would_call,
        "wall_clock_s": wall_clock_s,
        "by_cat_llm": {c: list(v) for c, v in by_cat_llm.items()},
        "stub_baseline": stub,
    }
    full = {
        "summary": summary,
        "training": [
            {
                "text": e["text"],
                "expected_repr": repr(e["expected"]),
                "parsed_repr": repr(e["parsed"]),
                "format_id": e["format_id"],
                "corruption": e["corruption"],
                "matched": e["matched"],
                "teacher_calls": e["teacher_calls"],
                "gaps_asked": e["gaps_asked"],
                "shape": e.get("shape"),
            } for e in train_log
        ],
        "heldout": [
            {
                "text": e["text"],
                "expected_repr": repr(e["expected"]),
                "parsed_repr": repr(e["parsed"]),
                "format_id": e["format_id"],
                "corruption": e["corruption"],
                "matched": e["matched"],
                "teacher_calls": e["teacher_calls"],
                "gaps_asked": e["gaps_asked"],
                "category": e["category"],
                "shape": e.get("shape"),
            } for e in held_log
        ],
        "teacher_calls": teacher_log,
    }
    out_json.write_text(json.dumps(full, indent=2, default=str))
    print(f"Per-input log written to: {out_json}")


def main() -> int:
    rng = random.Random(0xA17A)  # stable sample for reproducibility
    train = sample_training_bank(rng, target=20)
    held = sample_heldout_bank(rng, target=8)
    print(f"Sampled training bank: {len(train)} entries (stratified by shape)")
    print(f"Sampled held-out bank: {len(held)} entries"
          f" (stratified by category)")
    print()

    # Smoke-check the CLI on the first call. If it fails we abort early
    # rather than wasting time on a doomed run.
    print("Smoke-checking claude CLI...")
    t0 = time.time()
    probe = teacher_via_claude("smoke test", "{}")
    dt = time.time() - t0
    print(f"  probe round-trip: {dt:.1f}s; format={probe.get('format')!r},"
          f" reasoning={probe.get('reasoning')!r}")
    if probe.get("format") == "unknown" and "default" in (
            probe.get("reasoning") or ""):
        print("ABORT: claude --print returned no usable response on probe.")
        print("Proposal: re-run with teacher_stub (the stub baseline already"
              " exists in generalisation_test.log.json); the LLM wiring is"
              " in place and can be retried when the CLI is available.")
        return 2
    print()

    s = _native.Substrate()
    teacher = _LoggingTeacher()
    world = StructuredDataWorld(s, train, teacher)

    print("Running training pass with teacher_via_claude...")
    t_train_start = time.time()
    train_log = run_training(world, train)
    t_train = time.time() - t_train_start
    print(f"  training pass done in {t_train:.1f}s")

    print("Running held-out pass (teacher disabled)...")
    t_held_start = time.time()
    held_log, blocked = run_heldout(s, held)
    t_held = time.time() - t_held_start
    print(f"  held-out pass done in {t_held:.1f}s; blocked teacher calls"
          f"={blocked}")
    print()

    wall_clock = t_train + t_held
    stub = load_stub_baseline()
    out_json = ROOT / "scripts" / "generalisation_test_llm.log.json"
    report_comparison(stub, train_log, held_log, len(train), len(held),
                      teacher.entries, wall_clock, out_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
