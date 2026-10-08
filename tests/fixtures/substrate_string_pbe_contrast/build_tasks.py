#!/usr/bin/env python3
"""Generate held-out string tasks contrasting retrieval and search routes."""
from __future__ import annotations

import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "tasks.json"

SPECS = [
    ("replace_first", "replaces only the first occurrence of {old!r} with {new!r}",
     [("a", "x"), ("e", "q"), ("-", "_")]),
    ("reverse_split", "splits a string on {sep!r} and returns the parts in reverse order",
     ["|", ",", ";"]),
    ("replace_all", "replaces every occurrence of {old!r} with {new!r}",
     [("a", "x"), ("e", "q"), ("-", "_")]),
    ("reverse_string", "returns the string in reverse order", [None, None, None]),
    ("fold_suffix", "converts the string to lowercase and then appends {suffix!r}",
     ["!", "::", "_done"]),
    ("fold_replace", "converts the string to lowercase and then replaces {old!r} with {new!r}",
     [("a", "x"), ("e", "q"), ("-", "_")]),
]
ALPHABET = "abcdeABCDE xyz-_,!?"


def text(rng, min_len=5, max_len=16):
    return "".join(rng.choice(ALPHABET) for _ in range(rng.randint(min_len, max_len)))


def rows_for(rng, family, arg):
    rows, seen = [], set()
    while len(rows) < 7:
        if family == "reverse_split":
            sep = arg
            if len(rows) < 4:
                token = "".join(rng.choice("abcdefXYZ") for _ in range(4))
                value = sep.join((token, token))
            else:
                words = ["".join(rng.choice("abcdefXYZ") for _ in range(3 + i))
                         for i in range(3)]
                value = sep.join(words)
            expected = list(reversed(value.split(sep)))
        elif family == "replace_first":
            old, new = arg
            value = text(rng)
            if len(rows) < 4:
                value = value.replace(old, "") + old
            else:
                value = value.replace(old, "") + old + "_" + old
            expected = value.replace(old, new, 1)
        elif family == "replace_all":
            old, new = arg
            value = text(rng)
            value = value.replace(old, "") + old + "_" + old
            expected = value.replace(old, new)
        elif family == "reverse_string":
            value = text(rng)
            expected = value[::-1]
        elif family == "fold_suffix":
            value = text(rng)
            expected = value.casefold() + arg
        elif family == "fold_replace":
            old, new = arg
            value = text(rng).replace(old, "") + old.upper()
            value = value.replace(old.upper(), old).replace(old, old.upper())
            expected = value.casefold().replace(old, new)
        else:
            raise ValueError(family)
        if value in seen:
            continue
        seen.add(value)
        rows.append({"inputs": {"s": value}, "expected": expected})
    return rows


def build():
    tasks = []
    ordinal = 0
    for family, template, params in SPECS:
        for within, arg in enumerate(params, 1):
            ordinal += 1
            if family in {"replace_first", "replace_all", "fold_replace"}:
                old, new = arg
                fmt = {"old": old, "new": new}
            elif family in {"reverse_split"}:
                fmt = {"sep": arg}
            elif family == "fold_suffix":
                fmt = {"suffix": arg}
            else:
                fmt = {}
            request = "Write a function that " + template.format(**fmt) + "."
            examples = rows_for(random.Random(920260925 + ordinal * 6151), family, arg)
            tasks.append({"id": f"contrast_{family}_{within:02d}", "family": family,
                          "request_text": request, "example_rows": examples[:4],
                          "held_out_rows": examples[4:]})
    return {"suite_id": "substrate-string-pbe-contrast-v1",
            "task_count": len(tasks),
            "design": "18 generated string tasks in six strata, four revealed and three held out; two adversarial near-retrieval families, two operator controls, and two compositions",
            "generation_seed_rule": "per-task random.Random(920260925 + one_based_index * 6151)",
            "tasks": tasks}


def main():
    OUT.write_text(json.dumps(build(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
