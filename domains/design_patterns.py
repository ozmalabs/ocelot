"""Design-pattern selection — graph-native loader + selector.

Coding is "given a spec, produce code". Design is "given a problem,
produce a spec". The substrate already has the machinery (concepts +
match conditions + scoring) for both.

ALL pattern data lives in `seeds/design_patterns.json` — not in
Python. `install_design_patterns_mt` reads the seed and installs
`DesignPattern` graph nodes + an `excludes_with` edge between each
exclusion pair. `pick_design_pattern` is a thin selector that READS
those nodes — there is no hardcoded pattern data or scoring weights
in this module.

Add a pattern by editing the JSON; the cortex picks it up next
install. Update an attr → the answer changes. Pure data-driven.
"""
from __future__ import annotations

import json
from pathlib import Path


_SEED_PATH = (Path(__file__).resolve().parent.parent
              / "seeds" / "design_patterns.json")


def _load_seed() -> dict:
    with _SEED_PATH.open() as f:
        return json.load(f)


def install_design_patterns_mt(substrate) -> int:
    """Install the `design_patterns` Microtheory + DesignPattern nodes
    + Exclusion nodes from the seed at `seeds/design_patterns.json`.
    Idempotent. Returns the Mt's NodeID."""
    seed = _load_seed()

    # Find or mint the Mt.
    mt = None
    for n in substrate.nodes("Microtheory"):
        if substrate.node(n)["attrs"].get("name") == "design_patterns":
            mt = n
            break
    if mt is None:
        mt = substrate.add_node("Microtheory", {
            "name": "design_patterns",
            "description": seed.get("description", ""),
            "category_inheritance": seed.get("category_inheritance", ""),
        })
        # genlMt → compiler_theory: design patterns inherit the
        # soundness vocabulary the optimizer layer already knows.
        for mt2 in substrate.nodes("Microtheory"):
            if substrate.node(mt2)["attrs"].get("name") == "compiler_theory":
                try:
                    substrate.add_edge(mt, "genlMt", mt2, {})
                except Exception:
                    pass
                break

    # Install each pattern as a DesignPattern graph node.
    for pat in seed.get("patterns", []):
        existing = None
        for n in substrate.nodes("DesignPattern"):
            if substrate.node(n)["attrs"].get("name") == pat["name"]:
                existing = n
                break
        if existing is not None:
            continue
        substrate.add_node("DesignPattern", {
            **{k: v for k, v in pat.items() if k != "name"},
            "name": pat["name"],
            "origin": "design_patterns",
        })

    # Install exclusion pairs as DesignExclusion nodes so the selector
    # can read them from the graph (rather than from a Python list).
    for excl in seed.get("exclusions", []):
        pattern_tag, target_anti_tag = excl
        existing = None
        for n in substrate.nodes("DesignExclusion"):
            attrs = substrate.node(n)["attrs"]
            if (attrs.get("pattern_tag") == pattern_tag
                    and attrs.get("target_anti_tag") == target_anti_tag):
                existing = n
                break
        if existing is not None:
            continue
        substrate.add_node("DesignExclusion", {
            "pattern_tag": pattern_tag,
            "target_anti_tag": target_anti_tag,
            "origin": "design_patterns",
        })

    return mt


def _read_exclusions(substrate) -> list[tuple[str, str]]:
    """Read exclusion pairs from DesignExclusion graph nodes."""
    out = []
    for n in substrate.nodes("DesignExclusion"):
        a = substrate.node(n)["attrs"]
        out.append((a.get("pattern_tag", ""), a.get("target_anti_tag", "")))
    return out


def pick_design_pattern(substrate, target_tags: list[str]) -> dict | None:
    """Rank DesignPattern graph nodes against `target_tags` and return
    the winning pattern's attrs (or None if nothing matches).

    Reads BOTH the patterns AND the exclusion rules from the graph —
    this function does no domain reasoning of its own, just orchestrates
    a query. Update a pattern's `applies_when`/`expected_speedup` on
    the node → the answer changes.
    """
    req = set(target_tags)
    exclusions = _read_exclusions(substrate)

    best = None
    best_score = (-1, 0.0)
    for nid in substrate.nodes("DesignPattern"):
        attrs = substrate.node(nid)["attrs"]
        applies = set(attrs.get("applies_when", []))
        # Hard exclusion: pattern's positive tag collides with target's
        # negative tag.
        if any(p_tag in applies and t_neg in req
               for p_tag, t_neg in exclusions):
            continue
        matches = len(req & applies)
        if matches == 0:
            continue
        speedup = float(attrs.get("expected_speedup", 1.0))
        score = (matches, speedup)
        if score > best_score:
            best_score = score
            best = dict(attrs)
    return best


__all__ = [
    "install_design_patterns_mt",
    "pick_design_pattern",
]
