"""Brick 6 — the OUT-OF-THE-BOX outer loop (turn 4).

Turn 3 proved EXCLUSION (the admissibility grammar Γ) COMPOUNDS within a
problem-class (~42x explored-reduction once the class Γ has accumulated). It also
exposed two FAILURES of the in-box (Γ-pruned) search:

  (1) OVER-EXCLUSION MISS. A learned exclusion that was true of every simpler
      solution in a class can be FALSE for a harder member. `a*b*c+d` =
      `((a*b)*c)+d` needs a Times-whose-child-is-a-Times — the shape
      `("shape",("Times","Times"))`. No simpler class solution had it, so it was
      learned as an exclusion and the in-box search MISSED the answer.

  (2) CLASS-BOUNDARY NO-TRANSFER. Γ is class-scoped. A genuinely new class
      (`a*b+c*d+e`, arity=bg) has Γ-in=0 — no learned structure transfers, so the
      in-box search runs fully unguided and times out.

The user's thesis: "out-of-the-box thinking is iterating over problems where the
rules you have are insufficient — but in a BOUNDED, finitely possible way." This
module MECHANIZES that. When the in-box (Γ-pruned) search FAILS, the agent does
NOT abandon Γ. It enumerates a FINITE set of Γ-RELAXATION moves, ordered by MDL
(smallest box-expansion first / Occam), and keeps the FIRST relaxation that makes
the problem admissible. That minimal relaxation is the "creative leap" — the
smallest rule-change that lets the box hold the new problem. Then Γ GROWS
principledly: a dropped learned exclusion is RETRACTED (with the counter-example
that retracted it) as graph data; an imported neighbour-Γ becomes the new class's
starting Γ.

SOUND exclusions are NEVER relaxed — they provably never miss, so relaxing them
would only cost search, never recover a solution. Only LEARNED exclusions (the
compounding bet) and the class boundary are touched.

The FINITE move set (this is "out of the box", bounded — every move COUNTED):

  drop-exclusion : for each learned GeneratorExclusion active for this target's
                   class, one candidate Γ' = Γ minus that ONE exclusion.
                   (Finite: one move per active learned exclusion. MDL-ordered:
                   try dropping the FEWEST/smallest-evidence rule first.)
  import-neighbour: if the class has Γ-in=0 (a new class), candidate Γ' = import
                   the learned exclusions of the NEAREST solved class (by
                   class-signature distance), and finally Γ' = empty (the
                   brick-6 box). (Finite: one move per solved class + the empty
                   box.)

MDL selection: relaxations are ORDERED by the SIZE of the box-expansion — drop
the single smallest rule first; for imports, the nearest class first (fewest
foreign rules, then progressively looser). The FIRST relaxation that admits a
solution within budget is kept. That is the minimal creative leap.

Γ grows: the chosen drop marks the GeneratorExclusion `retracted=true` with the
counter-example (the solution that needed it); the chosen import writes a ΓImport
node recording source-class -> target-class. Graph-resident, weightless,
no LLM, no net. Additive — the inner loop (turn 3) is untouched.
"""

from __future__ import annotations

from typing import Any, Callable, Sequence

from domains.generator import synthesize, DEFAULT_OPS
from domains.generator_exclusion import (
    target_class, term_patterns, make_sound_exclude,
    excluded_patterns_for_class, _parse_pattern,
)


# ===========================================================================
# Γ as data: the active LEARNED exclusions for a class, as graph nodes, so a
# relaxation move can name (and retract) exactly ONE of them.
# ===========================================================================

def _learned_exclusion_nodes(substrate, cls: str) -> list[tuple[int, tuple, int]]:
    """Active (non-retracted) learned GeneratorExclusion nodes for `cls`.

    Returns list of (node_id, pattern, evidence), ordered by evidence ASCENDING
    (so the SMALLEST-evidence / least-supported rule is the cheapest to drop —
    MDL: the rule the box leans on least is the smallest box-expansion to give up).
    """
    out = []
    for n in substrate.nodes("GeneratorExclusion"):
        a = substrate.node(n)["attrs"]
        if a.get("cls") != cls:
            continue
        if a.get("retracted"):
            continue
        pat = _parse_pattern(a.get("pattern"))
        ev = int(a.get("evidence", 0))
        out.append((n, pat, ev))
    out.sort(key=lambda t: (t[2], repr(t[1])))  # evidence asc, stable
    return out


def _solved_classes(substrate, exclude_cls: str | None = None) -> list[str]:
    """Every class that has at least one (active) learned GeneratorExclusion —
    i.e. a class the agent has already solved enough to grow a Γ for."""
    seen = []
    for n in substrate.nodes("GeneratorExclusion"):
        a = substrate.node(n)["attrs"]
        c = a.get("cls")
        if c == exclude_cls:
            continue
        if c not in seen:
            seen.append(c)
    return seen


# ===========================================================================
# Class-signature distance — a finite, structural metric over the class string
# "arity=..|int=..|sign=..|parity=..". Distance = number of differing fields.
# Drives "nearest solved class" for the import-neighbour move. Weightless.
# ===========================================================================

def _class_fields(cls: str) -> dict:
    out = {}
    for part in cls.split("|"):
        if "=" in part:
            k, v = part.split("=", 1)
            out[k] = v
    return out


def class_distance(a: str, b: str) -> int:
    fa, fb = _class_fields(a), _class_fields(b)
    keys = set(fa) | set(fb)
    return sum(1 for k in keys if fa.get(k) != fb.get(k))


# ===========================================================================
# An exclude hook built from an EXPLICIT learned-pattern set (so a relaxation
# move can pass Γ-minus-one or an imported Γ). SOUND part is always on and is
# NEVER relaxed.
# ===========================================================================

def _exclude_from_patterns(best_known_size: int | None,
                           learned: set,
                           use_sound: bool = True,
                           collisions: dict | None = None) -> Callable:
    """Build an exclude hook from an EXPLICIT learned-pattern set. SOUND part
    always on (and never relaxed). If `collisions` is a dict, every time a LEARNED
    pattern is the reason a term is dropped, its count is incremented — this is
    the (weightless) signal of WHICH learned rule actually bit the search, used to
    order the drop-relaxation moves by how often they collided (the likeliest
    blocker first), instead of a blind evidence sort."""
    sound = make_sound_exclude(best_known_size, False) if use_sound else None
    learned = set(learned)

    def exclude(term, sig, target) -> bool:
        if sound is not None and sound(term, sig, target):
            return True
        if learned:
            d = term.to_dict() if hasattr(term, "to_dict") else term
            hit = term_patterns(d) & learned
            if hit:
                if collisions is not None:
                    for p in hit:
                        collisions[p] = collisions.get(p, 0) + 1
                return True
        return False

    return exclude


# ===========================================================================
# The FINITE relaxation move set, MDL-ordered.
# Each move: {"kind", "label", "learned" (the Γ' pattern set), plus move-specific
# bookkeeping for growing Γ on success}.
# ===========================================================================

def enumerate_relaxations(substrate, cls: str,
                          collisions: dict | None = None) -> list[dict]:
    """Build the finite, MDL-ordered list of Γ-relaxation candidates for `cls`.

    Order (smallest box-expansion first — Occam):
      1. drop-exclusion moves: Γ minus ONE active learned exclusion. ORDER —
         if `collisions` is given (a {pattern: hit-count} harvested from the
         FAILED in-box run), order by collision-count DESCENDING: the learned
         rule that actually BIT the search most is the likeliest blocker, so try
         dropping it first. (This is a weightless diagnostic — the count of which
         rule fired during the run that already happened, no extra search.) Ties
         and the no-collision case fall back to least-evidence-first (Occam:
         the least-supported rule is the smallest box-expansion to give up).
         (Finite: one move per active learned exclusion.)
      2. import-neighbour moves: import the NEAREST solved class's Γ first, then
         progressively-farther classes, then the empty box.
         (Finite: #solved classes + 1.)

    A drop is a SMALLER box-expansion than an import (it removes one rule vs.
    swapping in a foreign rule-set / opening the whole box), so drops are ordered
    before imports. Within imports, nearest class first.
    """
    moves: list[dict] = []
    base = excluded_patterns_for_class(substrate, cls)
    col = collisions or {}

    # 1) drop-exclusion: one move per active learned exclusion. Order by
    #    collision-count DESC (likeliest blocker first), then evidence ASC (Occam).
    nodes = _learned_exclusion_nodes(substrate, cls)
    nodes.sort(key=lambda t: (-col.get(t[1], 0), t[2], repr(t[1])))
    for nid, pat, ev in nodes:
        moves.append({
            "kind": "drop",
            "label": f"drop {pat!r} (ev={ev}, collisions={col.get(pat, 0)})",
            "node_id": nid,
            "pattern": pat,
            "evidence": ev,
            "collisions": col.get(pat, 0),
            "learned": base - {pat},
        })

    # 2) import-neighbour: nearest solved class first, then farther, then empty.
    others = _solved_classes(substrate, exclude_cls=cls)
    others.sort(key=lambda c: (class_distance(cls, c), c))
    for src in others:
        imported = excluded_patterns_for_class(substrate, src)
        moves.append({
            "kind": "import",
            "label": f"import Γ from {src} (dist={class_distance(cls, src)}, "
                     f"{len(imported)} rules)",
            "src_class": src,
            "distance": class_distance(cls, src),
            "learned": set(imported),
        })
    # empty box = brick-6 (no learned exclusions at all) — the loosest relaxation.
    moves.append({
        "kind": "empty",
        "label": "empty box (no learned Γ — brick-6)",
        "learned": set(),
    })
    return moves


# ===========================================================================
# Growing Γ principledly on a successful relaxation.
# ===========================================================================

def _retract_exclusion(substrate, node_id: int, counterexample: str) -> None:
    """Mark a learned exclusion RETRACTED with the counter-example that retracted
    it (the solution that needed the dropped pattern). Graph-resident data."""
    substrate.set_attr(node_id, "retracted", True)
    substrate.set_attr(node_id, "retracted_by", counterexample)


def _record_import(substrate, src_class: str, tgt_class: str,
                   n_rules: int) -> int:
    """Record a ΓImport node: the new class's starting Γ came from src_class."""
    return substrate.add_node("GammaImport", {
        "src_class": src_class, "tgt_class": tgt_class,
        "n_rules": n_rules, "origin": "generator_outofbox",
    })


# ===========================================================================
# THE OUTER LOOP.
# ===========================================================================

def outofbox_solve(
    substrate,
    examples: Sequence[tuple[dict, Any]],
    max_size: int,
    ops: Sequence[str] = DEFAULT_OPS,
    timeout_s: float = 60.0,
    grow_gamma: bool = True,
) -> dict:
    """Run the in-box (Γ-pruned) search; if it FAILS, do the bounded, MDL-ordered
    out-of-box relaxation search; grow Γ on the minimal relaxation that admits a
    solution.

    Returns a dict:
      {solved, term, term_str, size, route ("in-box" | relaxation-kind | "none"),
       relaxations_tried, chosen (the winning move's label or None),
       inbox (the in-box result), trace (list of per-move {label, kind, solved,
       explored})}.

    SOUND exclusions are always on and never relaxed. The MATCH is verified by
    synthesize() itself (it only returns a target-matching term); we re-confirm.
    """
    cls = target_class(examples)

    # --- IN-BOX: current class Γ (SOUND + accumulated LEARNED), turn-3 guide. ---
    # A collisions dict records WHICH learned rule fires during the run — the
    # weightless signal that orders the drop-relaxations if the in-box run fails.
    base_learned = excluded_patterns_for_class(substrate, cls)
    collisions: dict = {}
    inbox_excl = _exclude_from_patterns(max_size, base_learned, use_sound=True,
                                        collisions=collisions)
    inbox = synthesize(substrate, examples, ops=ops, max_size=max_size,
                       timeout_s=timeout_s, return_trace=False,
                       exclude=inbox_excl)
    if inbox["fits"]:
        return {
            "solved": True, "term": inbox["term"], "term_str": inbox["term_str"],
            "size": inbox["size"], "route": "in-box", "relaxations_tried": 0,
            "chosen": None, "inbox": inbox, "trace": [],
            "cls": cls, "gamma_in": len(base_learned),
        }

    # --- IN-BOX FAILED -> OUT-OF-BOX: bounded, MDL-ordered relaxation search. ---
    # Drops ordered by which learned rule actually bit the failed in-box run
    # (collision-count) — the likeliest blocker first.
    moves = enumerate_relaxations(substrate, cls, collisions=collisions)
    trace = []
    tried = 0
    for mv in moves:
        tried += 1
        excl = _exclude_from_patterns(max_size, mv["learned"], use_sound=True)
        r = synthesize(substrate, examples, ops=ops, max_size=max_size,
                       timeout_s=timeout_s, return_trace=False, exclude=excl)
        trace.append({"label": mv["label"], "kind": mv["kind"],
                      "solved": bool(r["fits"]), "explored": r["explored"]})
        if r["fits"]:
            # MINIMAL relaxation found (first in MDL order). Grow Γ.
            chosen = mv["label"]
            if grow_gamma:
                if mv["kind"] == "drop":
                    _retract_exclusion(substrate, mv["node_id"], r["term_str"])
                elif mv["kind"] == "import":
                    # The imported Γ becomes the new class's starting Γ: copy the
                    # foreign exclusions in under THIS class (so future in-box
                    # search for this class uses them) + record the import.
                    _record_import(substrate, mv["src_class"], cls,
                                   len(mv["learned"]))
                    _install_imported_gamma(substrate, cls, mv["src_class"],
                                            mv["learned"])
                # "empty" grows nothing (no rules to keep).
            return {
                "solved": True, "term": r["term"], "term_str": r["term_str"],
                "size": r["size"], "route": mv["kind"],
                "relaxations_tried": tried, "chosen": chosen,
                "inbox": inbox, "trace": trace,
                "cls": cls, "gamma_in": len(base_learned),
            }

    return {
        "solved": False, "term": None, "term_str": None, "size": None,
        "route": "none", "relaxations_tried": tried, "chosen": None,
        "inbox": inbox, "trace": trace,
        "cls": cls, "gamma_in": len(base_learned),
    }


def _install_imported_gamma(substrate, tgt_cls: str, src_cls: str,
                            patterns: set) -> None:
    """Write the imported learned exclusions in under `tgt_cls` (so subsequent
    in-box search for the new class reuses them). Marked imported_from for
    provenance. Idempotent: skips patterns already present for tgt_cls."""
    existing = set()
    for n in substrate.nodes("GeneratorExclusion"):
        a = substrate.node(n)["attrs"]
        if a.get("cls") == tgt_cls:
            existing.add(a.get("pattern"))
    for p in patterns:
        rep = repr(p)
        if rep in existing:
            continue
        substrate.add_node("GeneratorExclusion", {
            "cls": tgt_cls, "pattern": rep, "evidence": 0,
            "origin": "generator_outofbox", "imported_from": src_cls,
        })
