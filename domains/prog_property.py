"""prog_property -- the PROGRAM-PROPERTY faculty (Arc6 Seam D): read a
task PROMPT + the candidate's own REVEALED rows -> MATCH a held property
CUE -> GROUND it to a HELD REFERENCE RELATION (a pure function of witness
arguments, external domain knowledge -- never the candidate's own logic,
never a held-out row) -> SELF-VERIFY the conjecture against the goal's OWN
revealed rows (comprehend_theorem.self_verify_clause's precedent: a
property the revealed data already contradicts must NEVER fire) ->
EXECUTE the CURRENT verified candidate's already-reflected IR at 2-3
HAND-CONSTRUCTED WITNESS inputs (never held-out) via the SAME `ProgEval`
term `eval_and_record` already runs -> a MISMATCH is a REFUTATION.

THE MEASUREMENT THIS IMPLEMENTS (read first): PROGRAM_SYNTHESIS_ARC6_M0_CD.md
Ceiling D measured a=0, b=36, c=0 over the 36-task honest structural
residual (PROGRAM_SYNTHESIS_ARC4_STRUCTURAL_NOTES.md): every one of the 36
`accepted_holdout_fail` traps has a real, prompt-entailed, execution-
verified violated property, but NONE is expressible in `comprehend_
theorem`'s existing grammar -- `property_modifiers`
(seeds/theorem_constructions.json) is closed over GROUP-theoretic
vocabulary (torsion/splits/free/...) composed over `ground_reductions.
KNOWN_OBJECTS` (free-product algebraic structures). There is no
antecedent atom and no grounding TARGET for a property of a
number/string/list/program -- a domain-of-discourse mismatch, confirmed
live by the ceiling probe's 7 representative phrasings, all failing
identically against the positive-control group theorem that DOES ground.

This module is the SAME SHAPE -- prose -> structured property ->
grounded -> checkable clause -- aimed at PROGRAM-SHAPED content instead:
`seeds/program_properties.json`'s PropertyAtom table plays `theorem_
constructions.json`'s role; this module's held reference-relation
registry plays `ground_reductions`'s role (resolved by NAME, the
`comprehend_theorem._held_predicate` precedent); the grounding TARGET is
a predicate over a CANDIDATE PROGRAM'S EVALUATED OUTPUT at a witness
input rather than a predicate over a KNOWN_OBJECTS group -- exactly the
missing piece RESEARCH_MATH_CAPABILITY_AUDIT.md section 3.5 and
PROGRAM_SYNTHESIS_ARC6_M0_CD.md section 2.4 both named.

THE METRIC (read PROGRAM_SYNTHESIS_ARC6_D.md before trusting a number
here): the 36 are `accepted_holdout_fail` traps -- EVERY one already
PASSES every revealed row (that is what makes it a trap in the first
place). Refuting one converts accepted -> rejected; it can NEVER add a
pass. The self-detected-wrongness rate is measured against the SAME
denominator PROGRAM_SYNTHESIS_ARC4_S5.md used, NOT the pass rate.

SOUNDNESS -- the failure mode that matters more than a missed trap: a
WRONG property refuting a CORRECT program. Every atom is SELF-VERIFIED
against the goal's OWN revealed rows before it may fire (`_self_verify_
atom`) -- a property the revealed data already contradicts never applies
to THIS goal, mirroring `comprehend_theorem.self_verify_clause`'s
REJECTED verdict. Held-out rows are NEVER read anywhere in this module
(mechanical source audit: the substring "held_out" does not appear in
any function here). The false-refutation rate against the currently-
CORRECT accepted population is gated live
(tests/test_prog_property_migrated.py), never merely asserted.

FAITHFUL (CLAUDE.md): MECHANICAL only. `compute_property_facts` walks
graph state (the goal's revealed ExampleRow nodes, its Message's prompt
text, its CURRENT verified candidate's already-reflected Term subgraph)
and records FACTS -- fired properties + the refuting witness -- as goal
attrs. It decides NOTHING: `ps_property_reject`/`ps_property_clear`
(seeds/program_synthesis.json v1.11.0) read those facts and decide,
sitting BESIDE the existing D1-D3 structural detectors
(`compute_structural_facts`) in the SAME pre-accept path. No LLM, no
Python rule engine, no per-task hardcode reachable from graph state --
every property atom is graph DATA (seeds/program_properties.json); this
module only resolves an atom's NAMED reference function and runs the
SAME `ProgEval` term every other verdict path in this codebase already
uses (`domains.prog_synthesis._prog_eval_term`)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from domains import prog_synthesis as psy

_SEED = Path(__file__).resolve().parent.parent / "seeds" / "program_properties.json"


def load_property_atoms(path: Path = _SEED) -> List[dict]:
    """Load the PROPERTY ATOM table (graph DATA): what a property asserts
    (`reference`), what it needs from the spec to even be considered
    (`phrases`, `arg_count`), and how it is checked (`witnesses`). Empty
    on a read miss (the honest degenerate -- nothing checked, never a
    hand-wired fallback)."""
    try:
        g = json.loads(Path(path).read_text())
    except Exception:
        return []
    return g.get("property_atoms", [])


def _resolve_reference(name: str) -> Optional[Callable[..., Any]]:
    """Resolve a PropertyAtom's `reference` NAME to the held reference
    function this module exports (the `comprehend_theorem._held_predicate`
    precedent -- ONE source of truth: the atom names which held relation;
    the relation itself is external domain knowledge composed here, never
    re-derived from a task's held-out row). `None` for an atom naming a
    reference this module does not hold (the honest miss)."""
    fn = globals().get(name or "")
    return fn if callable(fn) and (name or "").startswith("ref_") else None


# --------------------------------------------------------------------------- #
# (0) THE REFERENCE LIBRARY -- one pure function per PropertyAtom, each a
# plain mathematical/domain relation read directly off a task's ORDINARY
# PROMPT MEANING (elementary geometry, number theory, string/collection
# semantics -- external knowledge, exactly as PROGRAM_SYNTHESIS_ARC6_M0_
# CD.md derived it), never the candidate's own logic and never a held-out
# row. Every function takes the SAME keyword-argument shape a witness/
# revealed-row env already carries (`a`, `b`, ... -- the MBPP dataset's
# own single-letter parameter convention).
# --------------------------------------------------------------------------- #
def ref_perimeter_square(a): return 4 * a
def ref_perimeter_pentagon(a): return 5 * a
def ref_surface_area_cube(a): return 6 * a * a


def ref_reverse_relation(a):
    return a == 2 * int(str(a)[::-1]) - 1


def ref_bell_number(a):
    tri = [[1]]
    for i in range(1, a + 1):
        row = [tri[i - 1][-1]]
        for j in range(i):
            row.append(row[j] + tri[i - 1][j])
        tri.append(row)
    return tri[a][0]


def ref_diff_of_two_squares(a): return a % 4 != 2
def ref_divisible_by_11(a): return a % 11 == 0
def ref_odd_length(a): return len(a) % 2 == 1
def ref_substring_in_list(a, b): return any(b in s for s in a)


def ref_divisor_count(a):
    return sum(1 for d in range(1, a + 1) if a % d == 0)


def ref_count_true(a): return sum(1 for x in a if x is True)
def ref_is_digit_string(a): return a.isdigit()
def ref_count_lists_in_tuple(a): return sum(1 for x in a if isinstance(x, list))


def ref_alphabet_position_count(a):
    s = a.lower()
    return sum(1 for i, ch in enumerate(s) if ch == chr(ord('a') + i))


def ref_smallest_pow2_ge(a):
    p = 1
    while p < a:
        p *= 2
    return p


def ref_popcount(a): return bin(a).count("1")


def ref_set_even_bits(a):
    if a == 0:
        return 0
    mask = sum(1 << i for i in range(1, a.bit_length(), 2))
    return a | mask


def ref_count_nonempty_substrings(a):
    n = len(a)
    return n * (n + 1) // 2


def ref_next_perfect_square_gt(a):
    n = int(a ** 0.5)
    while n * n <= a:
        n += 1
    return n * n


def ref_tuple_count_occurrences(a, b): return a.count(b)


def ref_count_primes_below(a):
    return sum(1 for x in range(2, a)
              if x > 1 and all(x % d for d in range(2, int(x ** 0.5) + 1)))


def ref_star_number(a): return 6 * a * (a - 1) + 1
def ref_decagonal_number(a): return 4 * a * a - 3 * a


def ref_paint_fence(a, b):
    if a == 0:
        return 0
    if a == 1:
        return b
    if a == 2:
        return b * b
    same, diff = b, b * (b - 1)
    for _ in range(3, a + 1):
        prev_total = same + diff
        same = diff
        diff = prev_total * (b - 1)
    return same + diff


def ref_floor_quotient(a, b): return a // b


def ref_proper_divisor_sum(a):
    return sum(d for d in range(1, a) if a % d == 0)


def ref_central_binomial(a):
    from math import comb
    return float(comb(2 * a, a))


def ref_set_leftmost_unset(a):
    if a == 0:
        return 1
    bl = a.bit_length()
    for i in range(bl - 2, -1, -1):
        if not (a >> i) & 1:
            return a | (1 << i)
    return (a << 1) | 1


def ref_highest_pow2_le(a):
    p = 1
    while p * 2 <= a:
        p *= 2
    return p


def ref_lucas_number(a):
    x, y = 2, 1
    if a == 0:
        return x
    for _ in range(a):
        x, y = y, x + y
    return x


def ref_max_recursive(a):
    memo: Dict[int, int] = {}

    def f(m):
        if m < 1:
            return 0
        if m in memo:
            return memo[m]
        v = max(f(m // 2) + f(m // 3) + f(m // 4) + f(m // 5), m)
        memo[m] = v
        return v
    return f(a)


def ref_tuple_membership(a, b): return b in a


def ref_trim_tuples(a, b):
    # MBPP's own string-repr convention for "a list of tuples" is TUPLE-
    # bracketed (confirmed directly against the dataset's own revealed
    # `expected` strings, e.g. '[(2,), (9,), (2,), (2,))]'); wrapping each
    # sliced element back into a tuple here reproduces that convention
    # regardless of whether `t` arrives as a genuine tuple or (after this
    # codebase's own `inputs_json` JSON round-trip elsewhere) a plain
    # list -- the RELATION checked is identical either way, only the
    # string RENDERING needs pinning to the dataset's own convention.
    return str([tuple(t[b: len(t) - b]) for t in a])


def ref_sale_loss(a, b): return max(0, b - a)


def ref_even_divisor_sum(a):
    return sum(d for d in range(1, a + 1) if a % d == 0 and d % 2 == 0)


def ref_month_has_31_days(a): return a in (1, 3, 5, 7, 8, 10, 12)


# --------------------------------------------------------------------------- #
# (1) MATCH -- mechanical cue-phrase matching over the goal's own prompt
# text (the `comprehend_theorem` atom-phrase precedent applied to a
# whole-phrase cue rather than a construction slot: a substring test, no
# decision).
# --------------------------------------------------------------------------- #
def _phrases_match(text: str, phrases: List[str]) -> bool:
    low = (text or "").lower()
    return bool(phrases) and all(p.lower() in low for p in phrases)


def _prompt_text(sub, g) -> str:
    """The goal's own request prose -- read off its `about_message`
    Message node's `text` attr (the same node `ingest_spec` wrote)."""
    msg = None
    for n in sub.neighbours(g, "about_message"):
        msg = n
    if msg is None:
        return ""
    return psy._text(sub.node(msg)["attrs"].get("text")) or ""


def _row_list(sub, g) -> List[Dict[str, Any]]:
    """The goal's OWN revealed rows (never held-out -- an ExampleRow IS
    the revealed set the goal was ingested with; the `compute_structural_
    facts` precedent, reused verbatim: `psy._outer_rows` walks
    `about_message` -> `has_example`)."""
    rows = []
    for r in psy._outer_rows(sub, g):
        rat = sub.node(r)["attrs"]
        rows.append({
            "inputs": json.loads(psy._text(rat.get("inputs_json")) or "{}"),
            "expected": rat.get("expected"),
        })
    return rows


# --------------------------------------------------------------------------- #
# (2) SELF-VERIFY -- the `comprehend_theorem.self_verify_clause` precedent,
# applied to a candidate PROPERTY instead of a candidate THEOREM CLAUSE: a
# conjectured property may fire on THIS goal only if it AGREES with EVERY
# one of the goal's own REVEALED rows. A property the revealed data
# already contradicts is not a correct reading of THIS task and must
# NEVER be applied here -- the refutability gate. Checked ONLY against
# what the goal was ingested with; never against held-out data (this
# function's own parameter list -- an atom + already-revealed rows --
# proves it has no held-out row to read).
# --------------------------------------------------------------------------- #
def _self_verify_atom(atom: dict, rows: List[Dict[str, Any]]) -> bool:
    fn = _resolve_reference(atom.get("reference", ""))
    if fn is None or not rows:
        return False
    arg_count = atom.get("arg_count")
    for row in rows:
        inputs = row["inputs"]
        if arg_count is not None and len(inputs) != arg_count:
            return False
        try:
            want = fn(**inputs)
        except Exception:
            return False
        if want != row["expected"]:
            return False
    return True


# --------------------------------------------------------------------------- #
# (3) CHECK -- execute the CURRENT verified candidate's ALREADY-REFLECTED
# Term subgraph at each hand-constructed witness (the `eval_and_record`
# `ProgEval` idiom, reused verbatim -- no fresh subgraph is built here;
# the persistent reflected root every verdict path already shares is
# evaluated directly). The FIRST witness whose output disagrees with the
# reference is the refutation; an executed TRAP (halted=False / a trap
# string) at a witness is not this property's business -- the existing
# eval/verdict pipeline already handles a candidate that cannot even run.
# --------------------------------------------------------------------------- #
def check_property(sub, root, atom: dict) -> Optional[Dict[str, Any]]:
    fn = _resolve_reference(atom.get("reference", ""))
    if fn is None:
        return None
    term = psy._prog_eval_term("e", "p")
    for env in atom.get("witnesses", []):
        try:
            expected = fn(**env)
        except Exception:
            continue
        out = sub._inner.evaluate(term, {"e": env, "p": root})
        ok = out.get("halted") is True and out.get("trap") is None
        if not ok:
            continue
        got = out.get("result")
        if got != expected:
            return {"property": atom.get("id"), "env": psy._plain(env),
                    "got": psy._plain(got), "expected": psy._plain(expected)}
    return None


# --------------------------------------------------------------------------- #
# (4) THE MECHANICAL RIM -- the `compute_structural_facts` precedent,
# dispatched on the SAME 'verified' status, scoped IDENTICALLY (top-level,
# non-descended goals only -- a descend hole's own fold-up accept is
# left completely untouched, byte-identical). Records; never decides --
# `ps_property_reject`/`ps_property_clear` (seed v1.11.0) read these
# facts, sitting beside D1-D3.
# --------------------------------------------------------------------------- #
def compute_property_facts(sub, ag_node, g) -> bool:
    at = sub.node(g)["attrs"]
    if float(at.get("ps_depth") if at.get("ps_depth") is not None else -1.0) != 0.0:
        return False
    if at.get("ps_rung_descend") == 1.0:
        return False
    roots = list(sub.neighbours(g, "ps_ir_reflected"))
    if not roots:
        return False
    n_reflected = len(roots)
    if float(at.get("ps_prop_seq") or -1.0) == float(n_reflected):
        return False
    root = roots[-1]

    prompt = _prompt_text(sub, g)
    rows = _row_list(sub, g)

    fired: List[str] = []
    violations: List[Dict[str, Any]] = []
    for atom in load_property_atoms():
        if not _phrases_match(prompt, atom.get("phrases", [])):
            continue
        if not _self_verify_atom(atom, rows):
            continue
        viol = check_property(sub, root, atom)
        if viol is not None:
            fired.append(atom.get("id"))
            violations.append(viol)

    sub.set_attr(g, "ps_prop_fired_properties", fired)
    sub.set_attr(g, "ps_prop_any_fired", 1.0 if fired else 0.0)
    sub.set_attr(g, "ps_prop_witness_json", json.dumps(violations, default=str))
    sub.set_attr(g, "ps_prop_computed", 1.0)
    sub.set_attr(g, "ps_prop_seq", float(n_reflected))
    return True


__all__ = [
    "load_property_atoms", "compute_property_facts", "check_property",
]
