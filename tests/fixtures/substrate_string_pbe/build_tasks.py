#!/usr/bin/env python3
"""Generate a held-out string transformation PBE transfer pilot."""
from __future__ import annotations

import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "tasks.json"

FAMILIES = [
    ("replace", "replaces every occurrence of {old!r} with {new!r}",
     [("a", "x"), ("e", "q"), ("-", "_"), ("A", "z")]),
    ("split", "splits a string into parts using {sep!r}", [",", "|", "-", ";"]),
    ("count", "counts occurrences of the substring {sub!r}", ["a", "th", "xy", "!"]),
    ("append", "adds the suffix {suffix!r} to a string", ["!", "__end", "?", " #"]),
    ("prefix", "adds the prefix {prefix!r} to a string", ["pre_", "[", "go:", "Z"]),
    ("fold_suffix", "converts a string to lowercase and then adds {suffix!r}",
     ["!", "::", "_done", "X"]),
]
ALPHABET = "abcdeABCDE xyz-_,!?"


def make_rows(rng: random.Random, kind: str, arg: str, extra: str | None):
    rows = []
    seen = set()
    while len(rows) < 7:
        if kind == "split":
            words = ["".join(rng.choice("abcdefXYZ") for _ in range(rng.randint(2, 6)))
                     for _ in range(rng.randint(2, 5))]
            value = arg.join(words)
            expected = words
        else:
            value = "".join(rng.choice(ALPHABET) for _ in range(rng.randint(5, 16)))
            if kind == "replace":
                old, new = arg, extra
                at = rng.randrange(len(value) + 1)
                value = value[:at] + old + value[at:]
                expected = value.replace(old, new)
            elif kind == "count":
                sub = arg
                at = rng.randrange(len(value) + 1)
                value = value[:at] + sub + value[at:]
                expected = value.count(sub)
            elif kind == "append":
                expected = value + arg
            elif kind == "prefix":
                expected = arg + value
            elif kind == "fold_suffix":
                expected = value.casefold() + arg
            else:
                raise ValueError(kind)
        if value in seen:
            continue
        seen.add(value)
        rows.append({"inputs": {"s": value}, "expected": expected})
    return rows


def build():
    tasks = []
    index = 0
    for kind, template, args in FAMILIES:
        for j, arg in enumerate(args, 1):
            index += 1
            extra = None
            if kind == "replace":
                task_arg, extra = arg
                fmt = {"old": task_arg, "new": extra}
            else:
                task_arg = arg
                fmt = {"sep": arg, "sub": arg, "suffix": arg, "prefix": arg}
            request = "Write a function that " + template.format(**fmt) + "."
            rows = make_rows(random.Random(920260926 + index * 7919), kind,
                             task_arg, extra)
            tasks.append({"id": f"string_{kind}_{j:02d}", "family": kind,
                          "request_text": request,
                          "example_rows": rows[:4], "held_out_rows": rows[4:]})
    return {"suite_id": "substrate-string-pbe-transfer-20260926-v1",
            "task_count": len(tasks),
            "design": "24 generated string transformations across replacement, split, substring count, append, prefix, and casefold-plus-suffix; four revealed and three held-out rows per task",
            "generation_seed_rule": "per-task random.Random(920260926 + one_based_index * 7919)",
            "tasks": tasks}


def main():
    OUT.write_text(json.dumps(build(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
