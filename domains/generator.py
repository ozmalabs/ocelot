"""Brick 6 — THE GENERATOR.

A bottom-up enumerative SYNTHESIZER over the DSL Term grammar. The agent's
gap-generator (brick 5) flagged that it needs "a FOLD/SEARCH over the
production space under a selection criterion". This is exactly that, built
weightlessly:

  - SEARCH over the production space = enumerate Term-trees from the DSL ops.
  - SELECTION by compression = enumerate by increasing SIZE (MDL/Occam: the
    shortest program that fits the spec is returned first).
  - TRACTABILITY/compression key = OBSERVATIONAL-EQUIVALENCE pruning: two
    terms with the same output signature on the spec inputs are the same
    BEHAVIOUR; keep only the smallest. This collapses the combinatorial
    space to distinct behaviours.
  - EARLY-STOP = SATURATION: if the distinct-behaviour count stops growing
    for K sizes, no new behaviours are reachable -> halt.

No weights, no gradient descent, no LLM, no templates. The agent composes
admissible structure (Term-trees the existing Rust engine evaluates) under
its own native selector (compression).

This is the WEIGHTLESS DUAL of GRAM:
  - MDL (size-ordered enumeration) replaces GRAM's learned reward model (LPRM).
  - Observational-equivalence collapse replaces GRAM's latent sampling.
  - Saturation halt replaces GRAM's ACT (adaptive computation time) halting.

The synthesizer composes EXISTING Term types only (no Rust, no rebuild).
Evaluation is the existing engine: `substrate.evaluate(term_dict, env)`.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Sequence

# Term factories — the DSL production grammar the agent composes from.
from substrate_rs import (
    Var, Lit,
    Plus, Times, Minus, Div,
    Abs, Neg,
    Min, Max,
    Gt, Lt, Gte, Lte, Eq,
    IfThenElse,
    And, Or, Not,
)


# ---------------------------------------------------------------------------
# Operator table. Each entry: (name, arity_kind, builder, term-size-cost).
#   arity_kind:
#     "u"  -> unary  builder(a)
#     "b"  -> binary builder(a, b)            (ordered: a,b and b,a both tried)
#     "bc" -> binary commutative              (only a,b; a<=b by index)
#     "t"  -> ternary builder(a, b, c)        (IfThenElse)
# Every produced Term has size = 1 (the node) + sum(child sizes).
# ---------------------------------------------------------------------------

def _op_table() -> dict[str, dict[str, Any]]:
    return {
        # arithmetic
        "Plus":  {"kind": "bc", "build": lambda a, b: Plus([a, b])},
        "Times": {"kind": "bc", "build": lambda a, b: Times([a, b])},
        "Minus": {"kind": "b",  "build": lambda a, b: Minus(a, b)},
        "Div":   {"kind": "b",  "build": lambda a, b: Div(a, b)},
        "Min":   {"kind": "bc", "build": lambda a, b: Min([a, b])},
        "Max":   {"kind": "bc", "build": lambda a, b: Max([a, b])},
        "Abs":   {"kind": "u",  "build": lambda a: Abs(a)},
        "Neg":   {"kind": "u",  "build": lambda a: Neg(a)},
        # comparison (produce booleans)
        "Gt":    {"kind": "b",  "build": lambda a, b: Gt(a, b)},
        "Lt":    {"kind": "b",  "build": lambda a, b: Lt(a, b)},
        "Gte":   {"kind": "b",  "build": lambda a, b: Gte(a, b)},
        "Lte":   {"kind": "b",  "build": lambda a, b: Lte(a, b)},
        "Eq":    {"kind": "bc", "build": lambda a, b: Eq(a, b)},
        # boolean
        "And":   {"kind": "bc", "build": lambda a, b: And([a, b])},
        "Or":    {"kind": "bc", "build": lambda a, b: Or([a, b])},
        "Not":   {"kind": "u",  "build": lambda a: Not(a)},
        # control
        "IfThenElse": {"kind": "t", "build": lambda a, b, c: IfThenElse(a, b, c)},
    }


DEFAULT_OPS = (
    "Plus", "Times", "Minus", "Div", "Min", "Max", "Abs", "Neg",
    "Gt", "Lt", "Eq", "IfThenElse",
)


# ---------------------------------------------------------------------------
# Observational-equivalence signatures.
#
# A signature is the tuple of outputs on the spec inputs. Two terms with the
# same signature are observationally equivalent (same behaviour on the spec).
#
# Care: the engine returns Python bools for comparisons and ints/floats for
# arithmetic. In Python `True == 1` and `1 == 1.0`, which would WRONGLY
# collapse a boolean term with an integer term (and 1 with 1.0). We canonical-
# ise each value into a (type-tag, number) pair so bool/int/float stay
# distinct in the signature key, while numeric equality for the TARGET match
# is checked separately (numeric, type-agnostic).
# ---------------------------------------------------------------------------

def _canon(v: Any) -> Any:
    """Canonical signature key for one output value (type-aware)."""
    if isinstance(v, bool):
        return ("bool", v)
    if isinstance(v, int):
        return ("num", float(v))
    if isinstance(v, float):
        # NaN/inf are legitimate (Div-by-zero -> 0.0 here, but Pow etc. may
        # produce inf); fold them to a stable token.
        if v != v:
            return ("num", "nan")
        return ("num", v)
    # anything else (shouldn't happen for numeric specs) -> repr
    return ("other", repr(v))


def _signature(term, envs: Sequence[dict], substrate) -> tuple | None:
    """Evaluate `term` on every spec input. Return its canonical signature,
    or None if it errors on ANY input (inadmissible -> discarded)."""
    sig = []
    for env in envs:
        try:
            out = term.evaluate(env, substrate)
        except Exception:
            return None
        # Reject non-numeric/bool leakage (e.g. a list/dict) -> not a scalar
        # program; treat as inadmissible for this spec class.
        if not isinstance(out, (bool, int, float)):
            return None
        sig.append(_canon(out))
    return tuple(sig)


def _num(v: Any) -> float:
    return float(v)


def _matches_target(sig: tuple, target: tuple[float, ...]) -> bool:
    """True iff the term's outputs equal the target numerically (type-agnostic,
    small tolerance for float)."""
    if len(sig) != len(target):
        return False
    for (tag, val), want in zip(sig, target):
        if val == "nan":
            return False
        got = (1.0 if val is True else 0.0) if tag == "bool" else float(val)
        if abs(got - want) > 1e-9:
            return False
    return True


def _term_str(term) -> str:
    """Readable infix-ish rendering of a Term dict."""
    d = term.to_dict() if hasattr(term, "to_dict") else term
    t = d["type"]
    if t == "Var":
        return d["name"]
    if t == "Lit":
        return repr(d["value"])
    if t in ("Plus", "Times", "Min", "Max", "And", "Or"):
        sym = {"Plus": "+", "Times": "*", "Min": "min", "Max": "max",
               "And": "and", "Or": "or"}[t]
        kids = [_term_str(_wrap(k)) for k in d["items"]]
        if t in ("Min", "Max"):
            return f"{sym}({', '.join(kids)})"
        return "(" + f" {sym} ".join(kids) + ")"
    if t in ("Minus", "Div", "Gt", "Lt", "Gte", "Lte", "Eq"):
        sym = {"Minus": "-", "Div": "/", "Gt": ">", "Lt": "<",
               "Gte": ">=", "Lte": "<=", "Eq": "=="}[t]
        return f"({_term_str(_wrap(d['a']))} {sym} {_term_str(_wrap(d['b']))})"
    if t in ("Abs", "Neg", "Not"):
        sym = {"Abs": "abs", "Neg": "neg", "Not": "not"}[t]
        return f"{sym}({_term_str(_wrap(d['arg']))})"
    if t == "IfThenElse":
        return (f"(if {_term_str(_wrap(d['cond']))} "
                f"then {_term_str(_wrap(d['then']))} "
                f"else {_term_str(_wrap(d['other']))})")
    return d.get("type", "?")


class _DictTerm:
    """Minimal wrapper so _term_str can recurse on raw child dicts."""
    def __init__(self, d):
        self._d = d
    def to_dict(self):
        return self._d


def _wrap(d):
    return _DictTerm(d)


# ---------------------------------------------------------------------------
# The synthesizer.
# ---------------------------------------------------------------------------

def synthesize(
    substrate,
    examples: Sequence[tuple[dict, Any]],
    ops: Sequence[str] = DEFAULT_OPS,
    consts: Sequence[Any] = (0, 1, 2, -1),
    max_size: int = 9,
    beam: int | None = None,
    timeout_s: float = 30.0,
    saturate_k: int = 3,
    guide: Callable[[tuple, tuple], float] | None = None,
    guide_beam: int | None = None,
    guide_select: Callable[[list, tuple, int], list] | None = None,
    exclude: Callable[[Any, tuple, tuple], bool] | None = None,
    return_trace: bool = False,
    probe_envs: Sequence[dict] = (),
    max_solutions: int = 1,
    include_output_constants: bool = True,
    stream_cohort: bool = False,
) -> dict | None:
    """Bottom-up, size-ordered, observational-equivalence-pruned synthesis.

    `examples`: list of (env: dict[varname->value], expected_output). The SPEC.
    Returns the smallest (MDL) Term fitting the spec, or None.

    Optional version-space collection (`probe_envs`, `max_solutions>1`):
      retain distinct hypotheses that fit the training examples while using
      their predictions on `probe_envs` to separate functionally different
      candidates. Stops after `max_solutions` MDL-ordered distinct behaviors,
      the size/fuel limit, or saturation. Probe environments have no labels and
      do not affect target matching. This mode cannot be combined with guided
      selection or exclusions because those interfaces assume training-only
      signatures. `include_output_constants=False` fixes the literal grammar
      to `consts`, preventing training labels from silently expanding it; the
      default remains True for compatibility with existing synthesis calls.

    `stream_cohort=True` registers each generated term immediately instead of
    first materializing every term at a given size. This preserves the
    size/operator/child enumeration order while bounding temporary candidate
    storage and checking the timeout during generation. It is opt-in until
    parity and workload-cost measurements justify changing the default.

    Optional GUIDED search (weightless, no LLM, no trained net):
      `guide(term_output_signature, target_signature) -> score`  — a smaller
        score = more promising (e.g. a distance between the term's outputs and
        the target outputs). The signature passed is the tuple of canonical
        per-input outputs already computed for observational-equivalence; the
        target is the numeric target tuple.
      `guide_beam` (= K) — after each size, keep only the top-K
        distinct-signature terms by guide score (lowest score first). Pruned
        terms are NOT carried as building blocks for larger sizes.
      `guide=None` (default) reproduces the unguided behaviour EXACTLY.

    Optional EXCLUSION hook (the admissibility grammar Γ over the search):
      `exclude(term, signature, target) -> bool` — if True, the term is DROPPED
        entirely (not stored, not carried as a building block for larger sizes).
        This HARD-prunes a region of the production space. SOUND exclusions never
        rule out a real solution; LEARNED exclusions are the compounding bet.
        `exclude=None` (default) reproduces the unguided behaviour EXACTLY.

    Result dict: {term, term_str, dict, size, fits, explored, distinct,
                  halt_reason, elapsed_s, beam_bit, guided}.
    """
    t0 = time.time()
    envs = [env for env, _ in examples]
    if max_solutions < 1:
        raise ValueError("max_solutions must be at least one")
    if max_solutions > 1 and (guide is not None or guide_select is not None or exclude is not None):
        raise ValueError("version-space collection is incompatible with guide/exclude hooks")
    signature_envs = envs + (list(probe_envs) if max_solutions > 1 else [])
    target = tuple(_num(out) for _, out in examples)
    training_width = len(envs)

    table = _op_table()
    op_specs = [(name, table[name]) for name in ops if name in table]

    # Variables appearing across the spec.
    var_names: list[str] = []
    for env in envs:
        for k in env:
            if k not in var_names:
                var_names.append(k)

    # Constant set: requested consts + any integer constants appearing in the
    # outputs (so a target like x*x+1 can find the `1`). Keep it small.
    const_set: list[Any] = list(dict.fromkeys(consts))
    if include_output_constants:
        for _, out in examples:
            if isinstance(out, (int, float)) and not isinstance(out, bool):
                iv = int(out)
                if iv == out and iv not in const_set:
                    const_set.append(iv)

    # by_size[s] = list of (term, signature). seen_sigs = global dedup map
    # signature -> (size, term) keeping the SMALLEST per behaviour.
    by_size: dict[int, list] = {}
    seen_sigs: dict[tuple, Any] = {}
    explored = 0
    beam_bit = False
    solutions = []
    # `guided` covers both the scalar-score beam (guide+guide_beam) and the
    # set-level selector beam (guide_select+guide_beam, e.g. interference).
    guided = guide_beam is not None and (guide is not None or guide_select is not None)

    def make_result(term, size, reason, *, trace=None):
        result = _make_result(term, size, reason, t0, explored, seen_sigs,
                              beam_bit, guided, trace=trace)
        if max_solutions > 1:
            # In collection mode a fitting first hypothesis does not mean the
            # version-space search is done. Preserve the actual collection stop.
            result["halt_reason"] = reason
            result["hypotheses"] = list(solutions)
            result["probe_env_count"] = len(probe_envs)
        return result

    def register(term, size) -> dict | None:
        """Compute sig, prune by observational-equivalence, store. Return a
        solution dict if this term hits the target, else None."""
        nonlocal explored, beam_bit
        explored += 1
        sig = _signature(term, signature_envs, substrate)
        if sig is None:
            return None  # inadmissible on some input
        if sig in seen_sigs:
            return None  # observationally equivalent to a smaller (or =) term
        # Target match FIRST — a matching term is the solution and must NEVER be
        # dropped by an exclusion (keeps the exclude hook from hiding answers).
        if _matches_target(sig[:training_width], target):
            seen_sigs[sig] = (size, term)
            by_size.setdefault(size, []).append((term, sig))
            if max_solutions > 1:
                solutions.append({"term": term, "term_str": _term_str(term),
                                  "size": size, "signature": sig})
                if len(solutions) >= max_solutions:
                    return make_result(solutions[0]["term"],
                                       solutions[0]["size"], "solution_limit",
                                       trace=seen_sigs if return_trace else None)
                return None
            return make_result(term, size, "solved",
                               trace=seen_sigs if return_trace else None)
        # EXCLUSION hook (Γ): drop the term as a building block if excluded.
        if exclude is not None and exclude(term, sig, target):
            return None  # admissibility grammar rules this region out
        seen_sigs[sig] = (size, term)
        by_size.setdefault(size, []).append((term, sig))
        return None

    # --- size 1: leaves ---
    for v in var_names:
        r = register(Var(v), 1)
        if r:
            return r
    for c in const_set:
        r = register(Lit(c), 1)
        if r:
            return r

    distinct_history = [len(seen_sigs)]

    # --- grow sizes 2..max_size ---
    for size in range(2, max_size + 1):
        if time.time() - t0 > timeout_s:
            return make_result(solutions[0]["term"] if solutions else None,
                               solutions[0]["size"] if solutions else None,
                               "timeout")

        produced_this_size = []

        def consider(term):
            if time.time() - t0 > timeout_s:
                return make_result(solutions[0]["term"] if solutions else None,
                                   solutions[0]["size"] if solutions else None,
                                   "timeout")
            return register(term, size)

        def emit(term):
            if stream_cohort:
                return consider(term)
            produced_this_size.append(term)
            return None

        for name, spec in op_specs:
            kind = spec["kind"]
            build = spec["build"]

            if kind == "u":
                # unary: child has size-1
                for child, _ in by_size.get(size - 1, []):
                    r = emit(build(child))
                    if r:
                        return r

            elif kind in ("b", "bc"):
                # binary: child sizes sum to size-1
                for sa in range(1, size - 1):
                    sb = (size - 1) - sa
                    if sb < 1:
                        continue
                    left = by_size.get(sa, [])
                    right = by_size.get(sb, [])
                    for ti, (ca, _) in enumerate(left):
                        for cb, _ in right:
                            if kind == "bc" and sa == sb:
                                # commutative + same-size: avoid (a,b)+(b,a)
                                # by index ordering. (different-size pairs of a
                                # commutative op are still distinct partitions
                                # and both needed.)
                                pass
                            r = emit(build(ca, cb))
                            if r:
                                return r
                if kind == "bc":
                    # de-dup commutative same-size double-counting cheaply:
                    # handled below by signature pruning anyway.
                    pass

            elif kind == "t":
                # ternary IfThenElse: cond+then+other sizes sum to size-1
                for sc in range(1, size - 2):
                    for st in range(1, size - 1 - sc):
                        so = (size - 1) - sc - st
                        if so < 1:
                            continue
                        for cc, _ in by_size.get(sc, []):
                            for tt, _ in by_size.get(st, []):
                                for oo, _ in by_size.get(so, []):
                                    r = emit(build(cc, tt, oo))
                                    if r:
                                        return r

        # Register all produced terms (observational-equivalence prune as we go).
        if not stream_cohort:
            for term in produced_this_size:
                r = consider(term)
                if r:
                    return r

        # GUIDED beam: keep only the top-K distinct-signature terms at this
        # size by guide score (lowest = closest to target = most promising).
        # Pruned terms are dropped as building blocks for larger sizes. This
        # is the trace-derived search guide steering the enumeration.
        if guided and len(by_size.get(size, [])) > guide_beam:
            beam_bit = True
            if guide_select is not None:
                # SET-LEVEL selector (e.g. sign-phase interference): chooses
                # which K terms to KEEP from the whole size cohort at once
                # (so far-but-cancelling partners can survive). Receives the
                # list of (term, signature) and the target; returns the kept
                # (term, signature) list.
                by_size[size] = guide_select(by_size[size], target, guide_beam)
            else:
                # scalar-score beam (turn-1 distance guide): keep smallest score.
                scored = sorted(
                    by_size[size],
                    key=lambda ts: guide(ts[1], target),
                )
                by_size[size] = scored[:guide_beam]
        # Unguided beam (legacy: arbitrary width cap on distinct behaviours).
        elif beam is not None and len(by_size.get(size, [])) > beam:
            beam_bit = True
            by_size[size] = by_size[size][:beam]

        # Saturation early-stop: distinct-behaviour count not growing.
        distinct_history.append(len(seen_sigs))
        if len(distinct_history) > saturate_k:
            recent = distinct_history[-(saturate_k + 1):]
            if recent[0] == recent[-1]:
                return make_result(solutions[0]["term"] if solutions else None,
                                   solutions[0]["size"] if solutions else None,
                                   "saturated")

    return make_result(solutions[0]["term"] if solutions else None,
                       solutions[0]["size"] if solutions else None,
                       "max_size")


def _make_result(term, size, halt_reason, t0, explored, seen_sigs, beam_bit,
                 guided=False, trace=None):
    solved = term is not None
    res = {
        "term": term,
        "term_str": _term_str(term) if solved else None,
        "dict": term.to_dict() if solved else None,
        "size": size,
        "fits": solved,
        "explored": explored,
        "distinct": len(seen_sigs),
        "halt_reason": halt_reason if not solved else "solved",
        "elapsed_s": round(time.time() - t0, 4),
        "beam_bit": beam_bit,
        "guided": guided,
    }
    if trace is not None:
        # trace = {signature: (size, term)} for every DISTINCT-behaviour term
        # the search committed to (the explored/kept frontier). Used to derive
        # a search guide from the agent's own experience.
        res["trace"] = dict(trace)
    return res
