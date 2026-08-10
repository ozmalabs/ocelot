"""prog_moves -- Arc5 MOVE A (orbit augmentation) / MOVE B (intermediate
decomposition), selected by WEIGHTED COLLAPSE (PROGRAM_SYNTHESIS_ARC5_
MOVES.md; the measurements this productionises are PROGRAM_SYNTHESIS_ARC5_
ORBIT_RESULT.md, PROGRAM_SYNTHESIS_ARC5_WIDEST_GAP.md, and task 59 in
PROGRAM_SYNTHESIS_ARC5_THREE_MOVES.md). Sits alongside the exact-first rung
(PROGRAM_SYNTHESIS_ARC5_EXACT_FIRST.md) between descent and enumerate.

CLAUDE.md's split, applied here exactly as `prog_exact.py` applies it:

  MECHANICAL (this file):
    moves_eligible          type-level pre-filter (I/O-boundary translation
                            of the raw `examples` argument -- the
                            `_examples_numeric_eligible` precedent).
    orbit_refute            a FIXED FORMULA over revealed rows: do any two
                            rows, related by a candidate permutation, carry
                            different outputs? (soundness rule 1, ARC5_
                            ORBIT_RESULT.md sec 3).
    orbit_augment           mechanical translation: the orbit of the
                            revealed rows under a (already-refutation-
                            survived) relaxation's generators, deduped.
    orbit_candidates /
    intermediate_candidates  a BOUNDED, DETERMINISTIC probe search (the
                            `fit_family` precedent -- a fixed algorithm
                            applied to data, using the REAL, unmodified
                            `SynthEnumerate` Term at a bounded budget,
                            never a Python re-implementation of the
                            arithmetic engine) that computes per-candidate
                            FACTS (refuted / gap / arity_gap / mdl_bits).
                            It records; it decides nothing -- the RULE
                            (`ps_move_select`, seeds/program_synthesis.json)
                            does the Argmax.
    run_structural_moves    the adapter verb: reads revealed rows, calls
                            the two candidate generators above, MINTS one
                            MoveCandidate node per candidate (a fact node,
                            the `Rejection{detectors}` precedent -- every
                            refusal/consideration is explainable). Records
                            `ps_moves_scan_done`; the RULE picks the winner.
    apply_selected_move     mechanical execution of whichever move the RULE
                            selected (`ps_move_sel_kind`, `ps_move_sel_key`
                            -- graph-data facts the Argmax wrote onto the
                            goal): orbit_augment mints augmented ExampleRow
                            nodes and hands off to the SAME unchanged
                            enumerate rung; intermediate_factor derives the
                            inner rows, runs the SAME real SynthEnumerate
                            Term the enumerate rung itself calls, and
                            composes `Times(Var(arg), inner)` on success.
                            Branching on `ps_move_sel_kind` here is the
                            SAME "name-keyed dispatch on rule verdicts"
                            idiom `pump`'s own `_DISPATCH` already uses
                            (sanctioned) -- the RULE decided which kind;
                            this only executes the matching mechanical
                            translation.

  DECISIONS (seeds/program_synthesis.json, NOT this file):
    ps_move_mark            WHETHER to enter the rung at all (Occam-ordered
                            between descent and exact-or-inapplicable, and
                            enumerate).
    ps_move_select          WHICH candidate wins: Argmax over a WEIGHT
                            EXPRESSION the goal itself carries as graph
                            data (`ps_move_w_gap` / `ps_move_w_arity` /
                            `ps_move_w_mdl`, stamped by `ps_move_mark`) --
                            "the weighting is graph data and tunable
                            without code." Refutation is a hard VETO: the
                            Argmax filters `refuted==1.0` OUT of its
                            candidate pool entirely, never scores it low.
    ps_move_none            no non-refuted candidate exists -> fall
                            through to the next rung (enumerate) exactly
                            like `ps_exact_failed` does.

WEIGHTED COLLAPSE, NOT A FIXED LADDER: both move FAMILIES feed the SAME
`MoveCandidate` pool and the SAME `ps_move_select` Argmax -- there is no
"try orbit first, then try intermediate" ordering anywhere in this file or
in the seed. Whichever candidate (of either kind) has the highest weight
wins; a low-gap orbit relaxation loses to a high-gap intermediate
decomposition on the SAME goal, and vice versa, purely by the weight
formula's own arithmetic.

GAP, OPERATIONALLY (a REAL, engine-grounded analogue of PROGRAM_SYNTHESIS_
ARC5_WIDEST_GAP.md's own V0-V1 version-space count, not a re-implementation
of it): every candidate's `gap` is measured by calling the REAL, unmodified
`SynthEnumerate` Term at a bounded scoring budget (`_PROBE_MAX_CANDIDATES`,
well under the engine's own 200,000 default so a genuinely hard/impossible
spec reads as hard within the probe, and well over every measured target
in this arc -- 25,240 for the br_10 orbit, 28,490 for task 59's inner
factor -- so a genuinely informative move is never starved of budget) on
the REVEALED rows alone versus the move's own augmented/decomposed rows.
A move that forces the search to try MORE candidates before converging (or
to newly converge where the plain search could not) is exactly a move that
ELIMINATED wrong small candidates from the reachable set -- the same
direction PROGRAM_SYNTHESIS_ARC5_ORBIT_RESULT.md measured directly
(532 -> 25,240 tested, `Max(a,b)` -> `Max(a,Max(b,c))`, WRONG -> CORRECT).
`gap = max(0, moved_tested - direct_tested)`.

ARITY_GAP, OPERATIONALLY: the same "declared parameters the accepted
program never reads" signal PROGRAM_SYNTHESIS_ARC5_WIDEST_GAP.md's own
`intent_evidence.arity_gap` names, computed here from the REAL direct
probe's own returned Term-JSON (a plain recursive `Var` walk over the
JSON, no substrate needed) rather than hand-waved -- for br_10 this
reproduces the SAME arity_gap==1 the widest-gap probe measured (the
accepted `Max(a,b)` reads 2 of the 3 declared args).
"""
from __future__ import annotations

import itertools
import json
import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

# Bounded scoring-probe budget: comfortably above every measured target in
# this arc (25,240 / 28,490) and comfortably below the engine's own 200,000
# default, so a genuinely hard/impossible direct search reads as hard
# WITHIN the probe (an honest, cheap signal) while a genuinely informative
# move is never starved. The FINAL apply step (below) always re-runs at
# the engine's own full default budget -- this cap only bounds the
# SELECTION-TIME cost of scoring several candidates per goal.
_PROBE_MAX_CANDIDATES = 40000
_PROBE_MAX_SIZE = 9


# --------------------------------------------------------------------------- #
#  tiny local helpers -- this module is deliberately self-contained (the
#  `prog_exact.py` precedent: `domains.prog_synthesis` imports THIS module,
#  so this module must never import it back).
# --------------------------------------------------------------------------- #
def _text(v) -> Optional[str]:
    if v is None:
        return None
    if isinstance(v, bytes):
        return v.decode("utf-8", "replace")
    return str(v)


def _numeric(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


# --------------------------------------------------------------------------- #
#  eligibility -- mechanical, type-level ONLY (the `_examples_numeric_
#  eligible` precedent). The REAL candidate search (below) is what decides
#  whether a specific spec's DATA admits a refutable conjecture.
# --------------------------------------------------------------------------- #
def _parsed_examples(examples) -> List[Tuple[Dict[str, Any], Any]]:
    out = []
    for ex in examples:
        if isinstance(ex, dict):
            out.append((ex["inputs"], ex["expected"]))
        else:
            out.append((ex[0], ex[1]))
    return out


def orbit_type_eligible(examples) -> bool:
    """MOVE A pre-filter: arity 2..4, every row's inputs numeric and of a
    SINGLE consistent Python kind (all-int or all-float -- swapping
    argument POSITIONS only makes sense between comparable slots)."""
    rows = _parsed_examples(examples)
    if not rows:
        return False
    arity = None
    kind = None
    for inputs, _expected in rows:
        vals = list(inputs.values())
        if not all(_numeric(v) for v in vals):
            return False
        n = len(vals)
        if arity is None:
            arity = n
        elif arity != n:
            return False
        k = "int" if all(_is_int(v) for v in vals) else "float"
        if kind is None:
            kind = k
        elif kind != k:
            return False
    return arity is not None and 2 <= arity <= 4


def intermediate_type_eligible(examples) -> bool:
    """MOVE B pre-filter: arity 1..3, every input AND the output an
    integer (PROGRAM_SYNTHESIS_ARC5_THREE_MOVES.md's own scope: "an exact
    INTEGER factorisation")."""
    rows = _parsed_examples(examples)
    if not rows:
        return False
    arity = None
    for inputs, expected in rows:
        vals = list(inputs.values())
        if not all(_is_int(v) for v in vals):
            return False
        if not _is_int(expected):
            return False
        n = len(vals)
        if arity is None:
            arity = n
        elif arity != n:
            return False
    return arity is not None and 1 <= arity <= 3


def moves_eligible(examples) -> bool:
    """The Message-level fact `ps_moves_eligible`: EITHER move's type-level
    pre-filter passes. The REAL per-candidate refutation/gap search only
    ever runs once a goal has already reached this rung (mechanical,
    cheap, no engine calls)."""
    return orbit_type_eligible(examples) or intermediate_type_eligible(examples)


# --------------------------------------------------------------------------- #
#  MOVE A -- orbit augmentation.
# --------------------------------------------------------------------------- #
def relaxations_for_arity(n: int) -> List[Dict[str, Any]]:
    """The candidate relaxation family (PROGRAM_SYNTHESIS_ARC5_WIDEST_GAP.md
    sec 0): full S_n PLUS every 2-cycle subgroup, over the arity actually
    present (2..4). A FIXED, deterministic enumeration -- no decision."""
    perms = list(itertools.permutations(range(n)))
    out = [{"name": "sym_full_S%d" % n, "generators": perms, "order": len(perms)}]
    for i, j in itertools.combinations(range(n), 2):
        swap = list(range(n))
        swap[i], swap[j] = swap[j], swap[i]
        out.append({"name": "sym_2cycle_%d_%d" % (i, j),
                    "generators": [tuple(range(n)), tuple(swap)], "order": 2})
    return out


def orbit_refute(relaxation: Dict[str, Any],
                  rows: Sequence[Dict[str, Any]]) -> bool:
    """SOUNDNESS RULE 1 (ARC5_ORBIT_RESULT.md sec 3): refuted iff some
    generator maps one revealed row's argument VALUES onto another
    revealed row's argument values while the two rows carry DIFFERENT
    outputs. Checked from the REVEALED rows alone, before any scoring or
    augmentation -- a fixed formula, never a search."""
    for (ra, rb) in itertools.permutations(rows, 2):
        va, ea = ra["vals"], ra["expected"]
        vb, eb = rb["vals"], rb["expected"]
        if ea == eb:
            continue
        for perm in relaxation["generators"]:
            if tuple(va[p] for p in perm) == tuple(vb):
                return True
    return False


def orbit_augment(relaxation: Dict[str, Any],
                   rows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Mechanical translation: the orbit of the revealed rows under this
    relaxation's generators, deduped by argument-value tuple. ONLY ever
    called on a relaxation that has already SURVIVED `orbit_refute` --
    soundness is the caller's responsibility (the RULE decides whether a
    candidate is eligible to be applied at all)."""
    seen: Dict[Tuple[Any, ...], Any] = {}
    for r in rows:
        vals, expected = r["vals"], r["expected"]
        for perm in relaxation["generators"]:
            permuted = tuple(vals[p] for p in perm)
            if permuted not in seen:
                seen[permuted] = expected
    return [{"vals": list(k), "expected": v} for k, v in seen.items()]


def _relaxation_by_name(name: str, n: int) -> Optional[Dict[str, Any]]:
    for r in relaxations_for_arity(n):
        if r["name"] == name:
            return r
    return None


# --------------------------------------------------------------------------- #
#  MOVE B -- intermediate decomposition (scalar/arithmetic factor).
# --------------------------------------------------------------------------- #
def factor_candidates(args: Sequence[str],
                       rows: Sequence[Dict[str, Any]]
                       ) -> List[Tuple[str, List[Dict[str, Any]]]]:
    """For each argument, mechanically check whether `expected / arg` is an
    EXACT integer across every revealed row (PROGRAM_SYNTHESIS_ARC5_THREE_
    MOVES.md's own "out/n is integral across all rows"). Returns
    `(arg_name, inner_rows)` for every argument that qualifies -- the
    caller (the real search below) scores and the RULE selects; this is
    pure arithmetic, no decision about which one to USE."""
    out = []
    for idx, arg in enumerate(args):
        inner_rows: List[Dict[str, Any]] = []
        ok = True
        for r in rows:
            v = r["vals"][idx]
            expected = r["expected"]
            # Defensive, not merely a repeat of `intermediate_type_eligible`:
            # `moves_eligible` is EITHER move's type-level pre-filter (an
            # OR), so a goal can reach here purely on MOVE A's (int-input-
            # only) eligibility while its OWN output is non-numeric (e.g. a
            # tuple/None-valued spec, arity-3 int inputs) -- verified live
            # (MBPP tasks 160/257 crashed here before this guard, `expected`
            # a tuple). Non-integer expected values are simply INAPPLICABLE
            # to this move, not an error.
            if not _is_int(v) or v == 0 or not _is_int(expected) or \
                    expected % v != 0:
                ok = False
                break
            inner_rows.append({"vals": [v], "expected": expected // v})
        if not ok or not inner_rows:
            continue
        # a genuine function of arg alone must agree on repeats: same v ->
        # same expected/v across every row that shares it.
        seen: Dict[Any, Any] = {}
        consistent = True
        for ir in inner_rows:
            k = ir["vals"][0]
            if k in seen and seen[k] != ir["expected"]:
                consistent = False
                break
            seen[k] = ir["expected"]
        out.append((arg, inner_rows, consistent))
    return out


# --------------------------------------------------------------------------- #
#  the real, engine-grounded scoring probe (bounded SynthEnumerate calls --
#  the `fit_family` precedent: a fixed algorithm applied to data, never a
#  parallel re-implementation of the arithmetic engine).
# --------------------------------------------------------------------------- #
def _rows_to_spec(rows: Sequence[Dict[str, Any]], args: Sequence[str]
                   ) -> List[Dict[str, Any]]:
    return [{"inputs": dict(zip(args, r["vals"])), "output": r["expected"]}
            for r in rows]


def _run_synth_enumerate(sub, spec_rows: List[Dict[str, Any]], *,
                          max_size: int, max_candidates: int) -> Dict[str, Any]:
    # ARC6 value layer: JSON erases list-vs-tuple at the `Lit` boundary.
    # Function-local import — `prog_synthesis` imports THIS module.
    from domains.prog_synthesis import _wire_rows
    try:
        out = sub._inner.evaluate(
            {"type": "SynthEnumerate",
             "examples": {"type": "Lit", "value": _wire_rows(spec_rows)},
             "max_size": max_size, "max_candidates": max_candidates,
             "saturate_k": 0, "field": ""}, {})
    except Exception:
        return {"found": False, "tested": 0, "term": None, "term_str": None,
                "halt_reason": "error"}
    if not isinstance(out, dict):
        return {"found": False, "tested": 0, "term": None, "term_str": None,
                "halt_reason": "bad_result"}
    return out


def _term_var_refs(node) -> set:
    """Mechanical recursive JSON walk -- every `{"type":"Var","name":...}`
    occurrence. No substrate needed (the direct probe's own Term-JSON
    string, `json.loads`-ed); the same class of computation as
    `prog_synthesis._st_var_refs`, just over raw JSON instead of a
    reflected subgraph, because this module is self-contained."""
    out: set = set()

    def walk(x):
        if isinstance(x, dict):
            if x.get("type") == "Var" and isinstance(x.get("name"), str):
                out.add(x["name"])
            for k, v in x.items():
                if k == "type":
                    continue
                walk(v)
        elif isinstance(x, list):
            for it in x:
                walk(it)

    walk(node)
    return out


def _compose(p: Tuple[int, ...], q: Tuple[int, ...]) -> Tuple[int, ...]:
    """Permutation composition: apply p, then q (both 0-indexed position
    maps, `orbit_refute`/`orbit_augment`'s own convention)."""
    return tuple(q[p[i]] for i in range(len(p)))


def _group_closure(generators: Sequence[Tuple[int, ...]], n: int
                    ) -> List[Tuple[int, ...]]:
    """The permutation subgroup GENERATED by `generators`, by BFS closure
    under composition (n<=4, so this is always small and fast). Used so a
    function's symmetry is never tested/applied one WEAK generator at a
    time -- see `_sound_closure_relaxation`'s docstring for why."""
    identity = tuple(range(n))
    seen = {identity}
    frontier = [identity]
    gens = list(generators) or [identity]
    while frontier:
        nxt = []
        for g in frontier:
            for gen in gens:
                h = _compose(g, gen)
                if h not in seen:
                    seen.add(h)
                    nxt.append(h)
        frontier = nxt
    return sorted(seen)


def _sound_closure_relaxation(args: Sequence[str],
                               rows: Sequence[Dict[str, Any]]
                               ) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    """SOUNDNESS FIX (PROGRAM_SYNTHESIS_ARC5_MOVES.md -- the median-of-
    three coincidental-fit this arc caught and corrected): a function can
    be ACCIDENTALLY symmetric under one WEAK 2-cycle (e.g. `Max(a,Min(b,c))`
    is genuinely symmetric in b,c) without respecting the FULL symmetry
    the revealed data does not refute -- accepting a candidate off that
    lone 2-cycle's orbit alone can therefore admit a program that is
    WRONG outside the tested inputs (verified: `Max(a,Min(b,c))` passes
    task 397's own held-out row by coincidence and fails a constructed
    witness where the first argument is the true maximum). The fix:
    every individually rule-1-sound 2-cycle is recorded for AUDIT (its
    own refutation status, gap always pinned to 0 -- never independently
    selectable), but the only relaxation ever eligible for SELECTION is
    the GROUP CLOSURE of every rule-1-sound 2-cycle taken TOGETHER,
    re-checked for rule-1 soundness as a whole (composing two sound
    generators can produce a THIRD permutation the data does refute, even
    when neither generator alone does). If the closure itself is refuted,
    or no 2-cycle survives at all, orbit augmentation contributes no
    selectable candidate for this goal -- there is no partial fallback to
    a weaker, unverified subgroup.

    Returns `(closure_relaxation_or_None, audit_2cycle_dicts)`."""
    n = len(args)
    audit: List[Dict[str, Any]] = []
    sound_gens: List[Tuple[int, ...]] = []
    for i, j in itertools.combinations(range(n), 2):
        swap = list(range(n))
        swap[i], swap[j] = swap[j], swap[i]
        gens = [tuple(range(n)), tuple(swap)]
        refuted = orbit_refute({"generators": gens}, rows)
        audit.append({"name": "sym_2cycle_%d_%d" % (i, j), "refuted": refuted})
        if not refuted:
            sound_gens.append(tuple(swap))
    if not sound_gens:
        return None, audit
    closure = _group_closure(sound_gens, n)
    if orbit_refute({"generators": closure}, rows):
        # a COMPOSITION of individually-sound generators collided with the
        # data even though no single generator did -- withdraw entirely.
        return None, audit
    # name the candidate by which individually-sound generators the
    # closure was built from (full S_n gets its own clearer name).
    sound_pairs = []
    idx = 0
    for i, j in itertools.combinations(range(n), 2):
        if not audit[idx]["refuted"]:
            sound_pairs.append("%d_%d" % (i, j))
        idx += 1
    name = ("sym_full_S%d" % n) if len(closure) == math.factorial(n) else \
        "sym_closure_of_" + "-".join(sound_pairs)
    return {"name": name, "generators": closure, "order": len(closure)}, audit


def orbit_candidates(sub, args: Sequence[str], rows: Sequence[Dict[str, Any]]
                      ) -> List[Dict[str, Any]]:
    """AUDIT candidates for every individual 2-cycle (refuted status only,
    gap pinned to 0 -- never independently selectable), PLUS at most ONE
    scored, selectable candidate: the GROUP CLOSURE of every rule-1-sound
    2-cycle (`_sound_closure_relaxation`) -- the soundness fix above."""
    n = len(args)
    if not (2 <= n <= 4) or not rows:
        return []
    direct = _run_synth_enumerate(sub, _rows_to_spec(rows, args),
                                  max_size=_PROBE_MAX_SIZE,
                                  max_candidates=_PROBE_MAX_CANDIDATES)
    direct_tested = float(direct.get("tested") or 0.0)
    arity_gap = 0.0
    if direct.get("found") and direct.get("term"):
        try:
            used = _term_var_refs(json.loads(_text(direct["term"])))
            arity_gap = float(len(set(args) - used))
        except Exception:
            arity_gap = 0.0

    closure_relax, audit = _sound_closure_relaxation(args, rows)
    out: List[Dict[str, Any]] = []
    for a in audit:
        out.append({
            "move": "orbit_augment",
            "key": a["name"],
            "refuted": 1.0 if a["refuted"] else 0.0,
            "gap": 0.0,  # audit-only: NEVER independently selectable.
            "arity_gap": arity_gap,
            "mdl_bits": 1.0,
            "n_rows_added": 0.0,
        })
    if closure_relax is None:
        return out
    cand = {
        "move": "orbit_augment",
        "key": closure_relax["name"],
        "refuted": 0.0,
        "gap": 0.0,
        "arity_gap": arity_gap,
        "mdl_bits": math.log2(max(closure_relax["order"], 2)),
        "n_rows_added": 0.0,
    }
    aug_rows = orbit_augment(closure_relax, rows)
    if len(aug_rows) > len(rows):
        aug = _run_synth_enumerate(sub, _rows_to_spec(aug_rows, args),
                                   max_size=_PROBE_MAX_SIZE,
                                   max_candidates=_PROBE_MAX_CANDIDATES)
        if not aug.get("found"):
            # SOUNDNESS RULE 2 (ARC5_ORBIT_RESULT.md sec 3): augmenting
            # with the FULL closure made the row set unsatisfiable within
            # a generous budget -- evidence AGAINST the conjecture (or
            # against this op inventory's ability to express it);
            # withdraw. There is no fallback to a weaker subgroup (that
            # is exactly the coincidental-fit risk this fix closes).
            cand["refuted"] = 1.0
        else:
            aug_tested = float(aug.get("tested") or 0.0)
            cand["gap"] = max(0.0, aug_tested - direct_tested)
            cand["n_rows_added"] = float(len(aug_rows) - len(rows))
    out.append(cand)
    return out


def intermediate_candidates(sub, args: Sequence[str],
                             rows: Sequence[Dict[str, Any]]
                             ) -> List[Dict[str, Any]]:
    """One MoveCandidate dict per argument whose exact-integer-factor
    property holds across every revealed row."""
    n = len(args)
    if not (1 <= n <= 3) or not rows:
        return []
    direct = _run_synth_enumerate(sub, _rows_to_spec(rows, args),
                                  max_size=_PROBE_MAX_SIZE,
                                  max_candidates=_PROBE_MAX_CANDIDATES)
    direct_tested = float(direct.get("tested") or 0.0)
    direct_found = bool(direct.get("found"))
    censored_direct = direct_tested if direct_found else float(_PROBE_MAX_CANDIDATES)
    out: List[Dict[str, Any]] = []
    for arg, inner_rows, consistent in factor_candidates(args, rows):
        # EARNS-ITS-KEEP GATE (PROGRAM_SYNTHESIS_ARC5_THREE_MOVES.md's own
        # framing: "intermediate problems UNLOCK TRACTABILITY" -- a move
        # whose whole justification is unblocking a search that doesn't
        # converge has no justification when the DIRECT search already
        # converges. `direct_found` (within a generous bounded probe) true
        # means blind search already works -- decomposition would only
        # ever preempt a rung that needed no help, which is exactly the
        # collateral-interception failure mode measured against several
        # trivially-factorable fixtures elsewhere in the regression suite
        # (see PROGRAM_SYNTHESIS_ARC5_MOVES.md). This is a distinct
        # from the raw candidate-count `gap` below (task 59's direct
        # search is hard AND its inner factor is easy; a fixture like
        # `2*a` is EASY both ways, so `gap` alone can still read positive
        # by a small margin -- direct_found is the sharper, doc-faithful
        # discriminator).
        refuted = not consistent or direct_found
        gap = 0.0
        inner_tested = 0.0
        if not refuted:
            inner = _run_synth_enumerate(sub, _rows_to_spec(inner_rows, [arg]),
                                         max_size=_PROBE_MAX_SIZE,
                                         max_candidates=_PROBE_MAX_CANDIDATES)
            inner_tested = float(inner.get("tested") or 0.0)
            if not inner.get("found"):
                # SOUNDNESS RULE 2's twin for MOVE B: the inner sub-problem
                # itself is unsatisfiable within a generous budget --
                # withdraw, do not force a decomposition that leads
                # nowhere.
                refuted = True
            else:
                gap = max(0.0, censored_direct - inner_tested)
        out.append({
            "move": "intermediate_factor",
            "key": "factor:%s" % arg,
            "refuted": 1.0 if refuted else 0.0,
            "gap": gap,
            "arity_gap": 0.0,
            "mdl_bits": 1.0,
            "n_rows_added": 0.0,
        })
    return out


# --------------------------------------------------------------------------- #
#  row I/O shared by the two adapter verbs.
# --------------------------------------------------------------------------- #
def _goal_message(sub, g):
    for n in sub.neighbours(g, "about_message"):
        return n
    return None


def _goal_rows(sub, msg) -> Tuple[List[str], List[Dict[str, Any]]]:
    row_nodes = list(sub.neighbours(msg, "has_example")) if msg is not None else []
    args: List[str] = []
    envs: List[Tuple[Dict[str, Any], Any]] = []
    for r in row_nodes:
        rat = sub.node(r)["attrs"]
        env = json.loads(_text(rat.get("inputs_json")) or "{}")
        for k in env:
            if k not in args:
                args.append(k)
        envs.append((env, rat.get("expected")))
    args = sorted(args)
    rows = [{"vals": [env[a] for a in args], "expected": expected}
            for env, expected in envs]
    return args, rows


def _mint_example_row(sub, inputs: Dict[str, Any], expected: Any):
    """A manufactured row, honestly labelled (`row_source`) -- the
    `_add_example_row` precedent (`domains/prog_synthesis.py`), duplicated
    here in miniature so this module stays import-independent of it."""
    return sub.add_node("ExampleRow", {
        "inputs_json": json.dumps(inputs, sort_keys=True),
        "expected": expected,
        "has_list_input": 0.0,
        "eval_attempt": -1.0,
        "verdict_attempt": -1.0,
        "eval_ok": 0.0,
        "row_source": "orbit_augment",
    })


# --------------------------------------------------------------------------- #
#  run_structural_moves -- the adapter verb (dispatched on 'moves_scan').
#  Mints MoveCandidate facts; decides NOTHING. `ps_move_select`/
#  `ps_move_none` (seeds/program_synthesis.json) do the Argmax.
# --------------------------------------------------------------------------- #
def run_structural_moves(sub, ag_node, g) -> bool:
    at = sub.node(g)["attrs"]
    if at.get("ps_moves_scan_done") == 1.0:
        return False
    msg = _goal_message(sub, g)
    args, rows = _goal_rows(sub, msg)
    cands: List[Dict[str, Any]] = []
    cands.extend(orbit_candidates(sub, args, rows))
    cands.extend(intermediate_candidates(sub, args, rows))
    for c in cands:
        mc = sub.add_node("MoveCandidate", {
            "move": c["move"], "key": c["key"], "refuted": c["refuted"],
            "gap": c["gap"], "arity_gap": c["arity_gap"],
            "mdl_bits": c["mdl_bits"],
        })
        sub.add_edge_unchecked(g, "has_move_candidate", mc)
    sub.set_attr(g, "ps_moves_n_candidates", float(len(cands)))
    sub.set_attr(g, "ps_moves_n_refuted", float(sum(c["refuted"] for c in cands)))
    sub.set_attr(g, "ps_moves_scan_done", 1.0)
    return True


# --------------------------------------------------------------------------- #
#  apply_selected_move -- the adapter verb (dispatched on
#  'move_apply_pending'). Branches on `ps_move_sel_kind`, a fact the
#  `ps_move_select` RULE's own Argmax already wrote onto the goal -- the
#  SAME "name-keyed dispatch on rule verdicts" idiom `pump`'s own
#  `_DISPATCH` uses (sanctioned, per its own docstring).
# --------------------------------------------------------------------------- #
def apply_selected_move(sub, ag_node, g) -> bool:
    at = sub.node(g)["attrs"]
    if at.get("ps_move_applied") == 1.0:
        return False
    kind = _text(at.get("ps_move_sel_kind"))
    key = _text(at.get("ps_move_sel_key"))
    msg = _goal_message(sub, g)
    args, rows = _goal_rows(sub, msg)

    if kind == "orbit_augment":
        # re-derive the SAME group closure `orbit_candidates` scored (a
        # pure function of args+rows -- deterministic, no lookup table:
        # the selected key names it but is not itself parsed back into a
        # generator set, since a closure's name does not uniquely encode
        # its generators for every n).
        relax, _audit = _sound_closure_relaxation(args, rows)
        n_added = 0
        if relax is not None and msg is not None:
            existing = {tuple(r["vals"]) for r in rows}
            for a in orbit_augment(relax, rows):
                vt = tuple(a["vals"])
                if vt in existing:
                    continue
                existing.add(vt)
                new_row = _mint_example_row(sub, dict(zip(args, a["vals"])),
                                            a["expected"])
                sub.add_edge_unchecked(msg, "has_example", new_row)
                n_added += 1
        sub.set_attr(g, "ps_move_rows_added", float(n_added))
        sub.set_attr(g, "ps_move_applied", 1.0)
        # hand off to the SAME unchanged enumerate rung -- ps_rung_moves is
        # already stamped (mint-once), so this rung cannot re-engage.
        sub.set_attr(g, "status", "pending")
        return True

    if kind == "intermediate_factor" and key and key.startswith("factor:"):
        arg = key.split(":", 1)[1]
        if arg in args:
            idx = args.index(arg)
            inner_rows = [{"inputs": {arg: r["vals"][idx]},
                          "output": r["expected"] // r["vals"][idx]}
                          for r in rows]
            out = _run_synth_enumerate(sub, inner_rows, max_size=9,
                                       max_candidates=0)
            sub.set_attr(g, "ps_move_inner_candidates",
                        float(out.get("tested") or 0.0))
            sub.set_attr(g, "ps_move_inner_found", 1.0 if out.get("found") else 0.0)
            if out.get("found") and out.get("term"):
                inner_term = json.loads(_text(out["term"]))
                outer_term = {"type": "Times",
                              "items": [{"type": "Var", "name": arg}, inner_term]}
                stmts = [{"type": "ProgDefFnParam", "name": a, "default": None}
                         for a in args]
                stmts.append({"type": "ProgReturn", "value": outer_term})
                attempts = float(at.get("ps_attempts") or 0.0)
                sub.set_attr(g, "ps_ir",
                            json.dumps({"type": "ProgSeq", "stmts": stmts}))
                sub.set_attr(g, "ps_ir_built", attempts)
                sub.set_attr(g, "ps_move_inner_term", _text(out.get("term_str")) or "")
                sub.set_attr(g, "ps_move_applied", 1.0)
                sub.set_attr(g, "status", "eval_pending")
                return True
        sub.set_attr(g, "ps_move_applied", 1.0)
        sub.set_attr(g, "status", "pending")
        return True

    # Defensive only -- ps_move_select never writes an unrecognised kind
    # (it only ever copies a MoveCandidate's own `move` field, and this
    # module is the sole minter of MoveCandidate nodes).
    sub.set_attr(g, "ps_move_applied", 1.0)
    sub.set_attr(g, "status", "pending")
    return True


__all__ = [
    "moves_eligible", "orbit_type_eligible", "intermediate_type_eligible",
    "relaxations_for_arity", "orbit_refute", "orbit_augment",
    "factor_candidates", "orbit_candidates", "intermediate_candidates",
    "run_structural_moves", "apply_selected_move",
]
