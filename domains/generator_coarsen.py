"""Brick 7 — COARSENING (renormalization) for the ORDER-N COLLAPSE.

THE BOUNDARY order-n hit. The committed OrderNCollapse (domains/generator_order_n.py)
is a fundamental crack for ADDITIVELY-SEPARABLE targets: it collapses candidates in
order-n (finite-difference) space, constants land in the null space and VANISH, and
the greedy matching-pursuit peels off the independent components one at a time, at
cost ~ #components. It FAILS on COUPLED targets — products-of-sums ((a+b)*(c+d)),
deep-nested ((a*b+c)*d), 3-term cross-sums (a*b+b*c+c*a) — because the fine-grain
pursuit can't peel long-range variable coupling: the curvature of a product lives in
a MIXED partial that the per-axis (others-held-fixed) order-n profile cannot read, so
the profile doesn't factor into peelable per-axis components.

THE LEVER (multi-scale / RG; cf. arXiv:2501.06003 graph grammars + coarsening
short-cuts for long-range dependencies). Don't fight the coupling at the fine grain —
DETECT it, HOIST the coupled sub-structure to a COARSE VARIABLE, and let order-n solve
the now-SEPARABLE coarse problem; then SUBSTITUTE the coarse variable's defining term
back, RECURSING if the coarse problem is itself coupled (multi-scale).

DERIVED FROM THE ORDER-N COUPLING STRUCTURE — not a new heuristic:
  1. COUPLING GRAPH via MIXED SECOND DIFFERENCES. For each pair (i,j) compute
     d2_ij = Delta_i Delta_j f over the grid (the agent's OWN nth_order_terms applied
     ACROSS two axes — order-1 along i then order-1 along j, evaluated natively).
     d2_ij == 0 everywhere => i,j do NOT interact (separable in that pair);
     != 0 => COUPLED. This is a weightless, order-n READING of the interaction
     structure, the same finite-difference operator the collapse uses, lifted to the
     META level to read how variables couple.
       a*a+b*b      -> a,b uncoupled (separable)
       (a+b)(c+d)   -> a-c,a-d,b-c,b-d coupled; a-b, c-d UNCOUPLED -> bipartition
       a*b+b*c+c*a  -> all three mutually coupled (triangle, no bipartition)
  2. GROUP by coupling SIGNATURE. Variables that couple to the SAME set of others
     form a group ({a,b} both couple {c,d} -> group {a,b}; {c,d} -> group {c,d}).
     The triangle has no clean grouping (every var's signature differs / all-coupled)
     -> predict NO coarsening (stays hard — reported honestly).
  3. HYPOTHESIZE coarse variables: small combiners over each group — sum(G),
     product(G), (diff for 2-var groups). Each u_G is a tiny graph-resident Term.
  4. COARSE SYNTHESIS: project the examples into coarse space (u,v,... values per
     example), form the coarse spec, and run the COMMITTED OrderNCollapse on it (few
     coarse vars, low degree -> tiny). Accept the SIMPLEST (MDL) coarse hypothesis
     whose coarse problem solves.
  5. ASSEMBLE / RECURSE: substitute each coarse var's defining term back into the
     coarse solution -> the full fine-grain Term. If coarse vars are themselves
     coupled, recurse the whole pass on them. Verify target-match + held-out.

Weightless, no net, no LLM, no Rust. The coarse variables are graph-resident
Term-trees; assembly is substitution. ADDITIVE — reuses build_grid / OrderNCollapse /
nth_order_terms unchanged; does NOT modify the committed order-n files.
"""

from __future__ import annotations

import itertools
import time
from typing import Any, Callable, Sequence

from substrate_rs import Lit, Var, Plus, Times, Minus, Div, Neg, Abs, Min, Max

from domains.order_n_concepts import nth_order_terms
from domains.generator import synthesize
from domains.generator_order_n import (
    OrderNCollapse, build_grid, GRID_LO, GRID_SPAN, GRID_BASE,
)


# ---------------------------------------------------------------------------
# dict -> substrate_rs Term rebuilder (+ coarse-variable substitution).
#
# The coarse synthesis returns a Term over coarse vars (Var("u"), Var("v"), ...).
# To assemble the fine-grain answer we substitute each coarse Var with its defining
# fine-grain term. We rebuild from the term's .to_dict() form, swapping coarse Vars.
# Self-contained over the small arithmetic vocabulary the synthesizer emits.
# ---------------------------------------------------------------------------

_BUILDERS = {
    "Plus":  lambda kids, d: Plus(kids),
    "Times": lambda kids, d: Times(kids),
    "Min":   lambda kids, d: Min(kids),
    "Max":   lambda kids, d: Max(kids),
}
_BINARY = {"Minus": Minus, "Div": Div}
_UNARY = {"Neg": Neg, "Abs": Abs}


def _rebuild(d: dict, subst: dict[str, Any]) -> Any:
    """Rebuild a substrate_rs Term from its dict, substituting any Var whose name is
    a key in `subst` with the (already-built) replacement Term."""
    t = d.get("type")
    if t == "Var":
        name = d.get("name")
        if name in subst:
            return subst[name]
        return Var(name)
    if t == "Lit":
        return Lit(d.get("value"))
    if t in _BUILDERS:
        kids = [_rebuild(k, subst) for k in d.get("items", [])]
        return _BUILDERS[t](kids, d)
    if t in _BINARY:
        return _BINARY[t](_rebuild(d["a"], subst), _rebuild(d["b"], subst))
    if t in _UNARY:
        return _UNARY[t](_rebuild(d["arg"], subst))
    raise ValueError(f"coarsen: cannot rebuild term type {t!r}")


# ---------------------------------------------------------------------------
# 1. COUPLING GRAPH via mixed second differences (the agent's nth_order_terms,
#    applied ACROSS two axes — order-1 over i, then order-1 over j).
# ---------------------------------------------------------------------------

def _eval(fn, env) -> float | None:
    try:
        v = fn(**env)
    except Exception:
        return None
    if isinstance(v, bool):
        return 1.0 if v else 0.0
    f = float(v)
    if f != f or f in (float("inf"), float("-inf")):
        return None
    return f


def mixed_second_diff(substrate, fn, var_names, vi, vj,
                      lo=GRID_LO, span=GRID_SPAN, base=GRID_BASE) -> float:
    """Sum of |mixed 2nd difference| Delta_vi Delta_vj f over a small (vi,vj) grid
    (others held at base). Computed natively via the agent's OWN nth_order_terms
    finite difference: first order-1 along vi at each vj-line, then order-1 of those
    across the vj-lines. 0 => vi,vj do not interact; >0 => COUPLED."""
    pts = list(range(lo, lo + span))
    # f[a][b] grid over the two swept axes
    grid_vals: list[list[float]] = []
    for a in pts:
        row = []
        for b in pts:
            env = {u: float(base) for u in var_names}
            env[vi] = float(a)
            env[vj] = float(b)
            v = _eval(fn, env)
            if v is None:
                return 0.0  # inadmissible region -> treat as no readable coupling
            row.append(v)
        grid_vals.append(row)

    # order-1 along vi (rows) using the agent's operator, per fixed vj column.
    # d1[a][b] = f[a+1][b] - f[a][b]
    col_diffs: list[list[float]] = []  # indexed [b][a]
    for bi in range(len(pts)):
        column = [Lit(grid_vals[ai][bi]) for ai in range(len(pts))]
        d1 = nth_order_terms(column, 1)
        try:
            vals = [float(substrate.evaluate(t, {})) for t in d1]
        except Exception:
            return 0.0
        col_diffs.append(vals)

    # now order-1 of d1 across vj: for each (a-diff index), difference over b.
    total = 0.0
    n_adiff = len(col_diffs[0]) if col_diffs else 0
    for ai in range(n_adiff):
        line = [Lit(col_diffs[bi][ai]) for bi in range(len(pts))]
        d2 = nth_order_terms(line, 1)
        try:
            vals = [float(substrate.evaluate(t, {})) for t in d2]
        except Exception:
            return 0.0
        total += sum(abs(x) for x in vals)
    return total


def coupling_matrix(substrate, fn, var_names, tol=1e-9) -> dict:
    """{(vi,vj): coupled_bool} for every pair, via mixed 2nd differences."""
    M = {}
    for i in range(len(var_names)):
        for j in range(i + 1, len(var_names)):
            vi, vj = var_names[i], var_names[j]
            d = mixed_second_diff(substrate, fn, var_names, vi, vj)
            M[(vi, vj)] = abs(d) > tol
    return M


# ---------------------------------------------------------------------------
# 2. GROUP by coupling signature.
# ---------------------------------------------------------------------------

def _partners(var, var_names, M) -> frozenset:
    s = set()
    for u in var_names:
        if u == var:
            continue
        key = (var, u) if (var, u) in M else (u, var)
        if M.get(key):
            s.add(u)
    return frozenset(s)


def coupling_groups(var_names, M) -> list[list[str]]:
    """Group variables that couple to the SAME set of OTHER variables.

    For (a+b)(c+d): partners(a)={c,d}, partners(b)={c,d} -> {a,b}; partners(c)=
    partners(d)={a,b} -> {c,d}. Clean bipartition. For the triangle every partner
    set differs (partners(a)={b,c} but the group test below also requires the group
    to be INTERNALLY uncoupled), so no clean grouping emerges."""
    sig = {v: _partners(v, var_names, M) for v in var_names}
    groups: list[list[str]] = []
    used = set()
    for v in var_names:
        if v in used:
            continue
        # candidate group: all vars with the SAME external partner signature AND
        # internally UNCOUPLED (a real coarse group combines vars that don't
        # interact with each other but jointly interact with the rest).
        grp = [v]
        used.add(v)
        for u in var_names:
            if u in used or u == v:
                continue
            if sig[u] != sig[v]:
                continue
            # internal-uncoupling: u must not couple to anything already in grp
            key_ok = all(
                not M.get((g, u), False) and not M.get((u, g), False)
                for g in grp)
            if key_ok:
                grp.append(u)
                used.add(u)
        groups.append(grp)
    return groups


def is_clean_grouping(groups, var_names) -> bool:
    """A grouping is COARSENABLE iff it partitions the vars into >=2 groups OR one
    group strictly smaller than all vars with a remainder — i.e. it actually
    reduces the variable count below the fine-grain count, and no group is the whole
    set (which would be no coarsening at all)."""
    if len(groups) >= 2 and any(len(g) >= 2 for g in groups):
        return True
    return False


def universal_vars(var_names, M) -> list[str]:
    """Variables that couple to EVERY other variable — candidate OUTER FACTORS of a
    deep-nested form. In (a*b+c)*d, d couples a,b,c (all) -> d is universal -> the
    HIERARCHY is OUTER(d) * INNER(a,b,c). In ((a+b)*c+d)*e, e is universal. The flat
    bipartition rule can't see this (d/e share no partner-signature with the inner
    vars); the hierarchy is the second coarsening axis."""
    out = []
    for v in var_names:
        if len(_partners(v, var_names, M)) == len(var_names) - 1 and len(var_names) > 1:
            out.append(v)
    return out


# ---------------------------------------------------------------------------
# 3. HYPOTHESIZE coarse variables: combiners over each group.
# ---------------------------------------------------------------------------

def _combiner_terms(group: list[str]) -> list[tuple[str, Any]]:
    """Candidate coarse-variable definitions over a group's fine-grain vars.
    Returns [(tag, term)] — tag for the trace, term the graph-resident definition."""
    vs = [Var(g) for g in group]
    out = [("sum", Plus(vs) if len(vs) > 1 else vs[0])]
    out.append(("prod", Times(vs) if len(vs) > 1 else vs[0]))
    if len(group) == 2:
        out.append(("diff", Minus(vs[0], vs[1])))
    return out


# ---------------------------------------------------------------------------
# 5. ASSEMBLE — substitute coarse-var definitions into the coarse solution.
# ---------------------------------------------------------------------------

def _assemble(coarse_term, coarse_defs: dict[str, Any]):
    """Substitute each coarse Var (by name) with its fine-grain defining term."""
    return _rebuild(coarse_term.to_dict(), coarse_defs)


def _verify(term, fn, var_names, substrate, check_envs) -> bool:
    for env in check_envs:
        try:
            got = term.evaluate(env, substrate)
        except Exception:
            return False
        gotn = (1.0 if got is True else 0.0) if isinstance(got, bool) else got
        try:
            if abs(float(gotn) - float(fn(**env))) > 1e-9:
                return False
        except Exception:
            return False
    return True


# ---------------------------------------------------------------------------
# THE COARSENING PASS.
# ---------------------------------------------------------------------------

def coarsen_synthesize(substrate, examples, var_names,
                       fn=None, order=2, K=14, coarse_budget=20.0,
                       max_coarse_size=9, depth=0, max_depth=2,
                       deadline: float | None = None,
                       verbose=False) -> dict:
    """Detect coupling -> group -> hypothesize coarse vars -> coarse order-n
    synthesis -> assemble (recursing on coupled coarse problems).

    `fn` (true target) is used ONLY to (a) build the order-n target profile on the
    grid and (b) project examples into coarse space + verify — exactly as the
    committed OrderNCollapse already reads the target fn to build its reference
    profile. Returns {solved, term, term_str, trace, explored, time}.

    The trace records: coupling matrix, groups, whether the grouping is clean, the
    chosen coarse vars + their defining terms, the coarse spec, the coarse solution,
    and the assembled fine-grain term (+ any recursion)."""
    t0 = time.time()
    if deadline is None:
        deadline = t0 + 4 * coarse_budget
    trace: dict[str, Any] = {"depth": depth, "var_names": list(var_names)}

    if fn is None:
        return {"solved": False, "term": None, "term_str": None,
                "trace": {**trace, "reason": "no target fn"},
                "explored": 0, "time": 0.0}

    # 1. COUPLING GRAPH
    M = coupling_matrix(substrate, fn, var_names)
    trace["coupling"] = {f"{i}-{j}": c for (i, j), c in M.items()}

    # 2. GROUP
    groups = coupling_groups(var_names, M)
    trace["groups"] = [list(g) for g in groups]
    clean = is_clean_grouping(groups, var_names)
    trace["clean_grouping"] = clean
    univ = universal_vars(var_names, M)
    trace["universal_vars"] = univ

    explored = 0

    # If an OUTER FACTOR exists (a universal var that divides out cleanly), the form
    # is a HIERARCHY (deep-nested) and the outer-factor peel is both the likelier
    # structure AND cheap to verify — try it FIRST so we don't burn the budget on a
    # false-positive flat grouping (e.g. ((a+b)*c+d)*e has a stray {a,b} flat group
    # but is really an e-factored hierarchy).
    if univ:
        of = _coarsen_outer_factor(substrate, examples, var_names, fn, M, univ,
                                   order, K, coarse_budget, max_coarse_size,
                                   depth, max_depth, deadline)
        explored += (of["explored"] if of else 0)
        if of is not None and of["solved"]:
            of["trace"] = {**trace, **of["trace"]}
            of["explored"] = of.get("explored", 0)
            return of

    if not clean:
        # No flat bipartition (and outer-factor above, if any, did not solve).
        trace["reason"] = ("no clean coarse grouping (all-to-all / arbitrary "
                           "coupling) and no clean outer factor — coarsening has "
                           "nothing to hoist")
        return {"solved": False, "term": None, "term_str": None, "trace": trace,
                "explored": explored, "time": time.time() - t0}

    # 3. HYPOTHESIZE coarse-variable definitions per group (groups of size 1 keep
    #    the single var directly — no coarsening needed for it).
    coarse_groups = [g for g in groups]
    per_group_choices = [_combiner_terms(g) for g in coarse_groups]

    # coarse-var names must avoid a leading underscore (the evaluator treats those
    # as unbound) and must not collide with any fine var name.
    coarse_names = []
    for idx in range(len(coarse_groups)):
        nm = f"cv{idx}"
        while nm in var_names:
            nm += "x"
        coarse_names.append(nm)

    # build the example INPUT envs (we project these into coarse space per hypothesis)
    fine_envs = [env for env, _ in examples]
    targets = [out for _, out in examples]

    # 4. COARSE SYNTHESIS over each assignment of coarse-var definitions.
    #    Prefer simpler combiners first (sum before prod before diff) = MDL.
    best = None
    assignments = list(itertools.product(*per_group_choices))
    # MDL order: fewest non-trivial combiners (singletons are free), prefer 'sum'.
    def _cost(asg):
        rank = {"sum": 0, "diff": 1, "prod": 2}
        return sum(rank.get(tag, 3) for (tag, _t) in asg)
    assignments.sort(key=_cost)

    for asg in assignments:
        if time.time() > deadline:
            trace["reason"] = "deadline reached during coarse search"
            break
        coarse_defs = {coarse_names[i]: term for i, (tag, term) in enumerate(asg)}
        coarse_tags = {coarse_names[i]: tag for i, (tag, _t) in enumerate(asg)}

        # project examples into coarse space
        coarse_examples = []
        ok = True
        for env, out in zip(fine_envs, targets):
            cenv = {}
            for cn, cterm in coarse_defs.items():
                try:
                    cv = cterm.evaluate(env, substrate)
                except Exception:
                    ok = False
                    break
                cenv[cn] = float(cv) if not isinstance(cv, bool) else (1.0 if cv else 0.0)
            if not ok:
                break
            coarse_examples.append((cenv, out))
        if not ok:
            continue

        # the coarse true-fn: given coarse-var values, we cannot invert in general,
        # BUT order-n needs the target profile on the COARSE grid. We build a coarse
        # target fn by composing: evaluate the FINE fn at a fine env that realizes
        # the coarse grid point. For sum/prod coarse vars the grid point (one coarse
        # var swept, others at base) must map to a concrete fine env. We realize a
        # coarse value v for group G by setting the FIRST var of G to (v - base*(|G|-1))
        # for sum, or to v / base**(|G|-1) for prod, and the rest to base. This gives
        # a fine env whose coarse-projection equals the swept coarse grid — so the
        # order-n collapse sees the true coarse target curvature.
        coarse_fn = _make_coarse_fn(fn, coarse_groups, coarse_names, coarse_tags,
                                    var_names)
        if coarse_fn is None:
            continue

        cvars = list(coarse_names)
        rem = max(1.0, min(coarse_budget, deadline - time.time()))

        # 4a/5. SOLVE THE COARSE PROBLEM. It has FEWER variables than the fine one.
        #   Multi-scale: if the coarse problem ITSELF has clean coupling structure
        #   AND depth budget remains, RECURSE the whole coarsening pass on it. Else
        #   (the coarse kernel is small + irreducible, e.g. u*v — 2 mutually-coupled
        #   coarse vars) solve it by ORDER-N collapse first (cracks separable coarse
        #   problems like u+v cheaply), and FALL BACK to bounded UNGUIDED enumeration
        #   when collapse can't peel the coarse product — faithful, because the LEVER
        #   is the variable-count reduction (the coarse search space is tiny), not the
        #   coarse solver's guide.
        coarse_term = None
        coarse_r = None
        sub_trace = None
        cM = coupling_matrix(substrate, coarse_fn, cvars)
        cgroups = coupling_groups(cvars, cM)
        if (depth + 1 < max_depth and is_clean_grouping(cgroups, cvars)
                and len(cvars) > 2):
            sub = coarsen_synthesize(
                substrate, coarse_examples, cvars, fn=coarse_fn, order=order,
                K=K, coarse_budget=rem, max_coarse_size=max_coarse_size,
                depth=depth + 1, max_depth=max_depth, deadline=deadline)
            explored += sub["explored"]
            sub_trace = sub["trace"]
            if sub["solved"]:
                coarse_term = sub["term"]
        if coarse_term is None:
            try:
                col = OrderNCollapse(substrate, cvars, order=order).set_target_fn(coarse_fn)
                rr = synthesize(substrate, coarse_examples, max_size=max_coarse_size,
                                timeout_s=max(1.0, rem * 0.4),
                                guide_select=col, guide_beam=K)
                explored += rr["explored"]
                if rr["fits"]:
                    coarse_term, coarse_r = rr["term"], rr
            except Exception:
                pass
        if coarse_term is None:
            # FALL BACK: bounded unguided enumeration on the now-tiny coarse problem.
            rem2 = max(1.0, min(coarse_budget, deadline - time.time()))
            rr = synthesize(substrate, coarse_examples, max_size=max_coarse_size,
                            timeout_s=rem2)
            explored += rr["explored"]
            if rr["fits"]:
                coarse_term, coarse_r = rr["term"], rr
        if coarse_term is None:
            continue

        # ASSEMBLE: substitute coarse-var definitions back into the coarse solution.
        assembled = _assemble(coarse_term, coarse_defs)

        # verify target-match on the training inputs
        if not _verify(assembled, fn, var_names, substrate, fine_envs):
            continue

        best = {
            "assembled": assembled,
            "coarse_term": coarse_term,
            "coarse_term_str": _term_repr(coarse_term),
            "coarse_size": coarse_r["size"] if coarse_r else None,
            "coarse_defs": {cn: _short(coarse_tags[cn], coarse_groups[i])
                            for i, cn in enumerate(coarse_names)},
            "sub_trace": sub_trace,
            "assignment_cost": _cost(asg),
        }
        break  # first (= simplest by MDL order) solving assignment wins

    if best is None:
        trace["reason"] = "no coarse-variable hypothesis solved the coarse problem"
        return {"solved": False, "term": None, "term_str": None, "trace": trace,
                "explored": explored, "time": time.time() - t0}

    trace["coarse_vars"] = best["coarse_defs"]
    trace["coarse_term"] = best["coarse_term_str"]
    trace["coarse_size"] = best["coarse_size"]
    trace["assembled"] = _term_repr(best["assembled"])
    if best.get("sub_trace") is not None:
        trace["recursed_into"] = best["sub_trace"]
    return {"solved": True, "term": best["assembled"],
            "term_str": _term_repr(best["assembled"]), "trace": trace,
            "explored": explored, "time": time.time() - t0}


def _coarsen_outer_factor(substrate, examples, var_names, fn, M, univ,
                          order, K, coarse_budget, max_coarse_size,
                          depth, max_depth, deadline):
    """HIERARCHY coarsening for deep-nested forms: peel an OUTER FACTOR.

    A universal var w (couples to all others) that is a clean MULTIPLICATIVE factor
    satisfies inner := f / w being w-INDEPENDENT. Then f = w * inner; we recover the
    inner target g(rest) = f/w, RECURSE the coarsening pass on the inner sub-problem
    (fewer vars), and assemble w * inner. Symmetric ADDITIVE-outer case: f - w is
    w-independent -> f = w + inner. Reuses the agent's mixed-difference reading (w
    universal) to pick the candidate; verifies the factorization holds on the grid."""
    if not univ or len(var_names) <= 2 or depth >= max_depth:
        return None
    t0 = time.time()
    fine_envs = [env for env, _ in examples]
    explored = 0

    for w in univ:
        rest = [v for v in var_names if v != w]
        # test MULTIPLICATIVE outer: is f/w independent of w? probe on a small grid.
        mult_ok = _factor_independent(fn, var_names, w, rest, kind="mult")
        add_ok = _factor_independent(fn, var_names, w, rest, kind="add")
        for kind, ok in (("mult", mult_ok), ("add", add_ok)):
            if not ok:
                continue
            # inner target over `rest`: g(rest) = f / w  (mult)  or  f - w  (add).
            def inner_fn(_k=kind, _w=w, **kw):
                full = dict(kw)
                full[_w] = float(_INNER_PROBE)  # any nonzero value; factor is indep
                val = float(fn(**full))
                return val / _INNER_PROBE if _k == "mult" else val - _INNER_PROBE
            # project examples onto inner target
            inner_examples = []
            okp = True
            for env in fine_envs:
                renv = {v: env[v] for v in rest}
                try:
                    g = inner_fn(**renv)
                except Exception:
                    okp = False
                    break
                inner_examples.append((renv, g))
            if not okp:
                continue
            # SOLVE the inner sub-problem: recurse coarsening first (it may itself be
            # nested/coupled), else bounded unguided enumeration (now fewer vars).
            rem = max(1.0, min(coarse_budget, deadline - time.time()))
            inner_term = None
            sub = coarsen_synthesize(
                substrate, inner_examples, rest, fn=inner_fn, order=order, K=K,
                coarse_budget=rem, max_coarse_size=max_coarse_size,
                depth=depth + 1, max_depth=max_depth, deadline=deadline)
            explored += sub["explored"]
            sub_trace = sub["trace"]
            if sub["solved"]:
                inner_term = sub["term"]
            if inner_term is None:
                rem2 = max(1.0, min(coarse_budget, deadline - time.time()))
                rr = synthesize(substrate, inner_examples,
                                max_size=max_coarse_size, timeout_s=rem2)
                explored += rr["explored"]
                if rr["fits"]:
                    inner_term = rr["term"]
            if inner_term is None:
                continue
            # ASSEMBLE: w * inner  or  w + inner
            assembled = (Times([Var(w), inner_term]) if kind == "mult"
                         else Plus([Var(w), inner_term]))
            if not _verify(assembled, fn, var_names, substrate, fine_envs):
                continue
            tr = {
                "strategy": "outer-factor",
                "outer_var": w, "outer_kind": kind,
                "inner_vars": rest,
                "inner_term": _term_repr(inner_term),
                "assembled": _term_repr(assembled),
            }
            if sub.get("solved"):
                tr["inner_recursed_into"] = sub_trace
            return {"solved": True, "term": assembled,
                    "term_str": _term_repr(assembled), "trace": tr,
                    "explored": explored, "time": time.time() - t0}
    return {"solved": False, "term": None, "term_str": None,
            "trace": {"strategy": "outer-factor", "result": "no clean factor"},
            "explored": explored, "time": time.time() - t0}


_INNER_PROBE = 3.0  # arbitrary nonzero w-value to evaluate a w-independent inner fn


def _factor_independent(fn, var_names, w, rest, kind, lo=1, span=4, base=2):
    """Does f / w (mult) or f - w (add) NOT depend on w? Probe: for several fixed
    `rest` envs, vary w over the grid and check the factored quantity is constant."""
    rest_settings = []
    # a few distinct rest-envs (cycle small values so we don't sit on a degenerate pt)
    cyc = [(1, 2, 3, 4, 2, 3), (2, 3, 1, 2, 3, 1), (3, 1, 2, 1, 2, 3)]
    for c in cyc:
        rest_settings.append({v: float(c[i % len(c)]) for i, v in enumerate(rest)})
    for renv in rest_settings:
        vals = []
        for wv in range(lo, lo + span):
            if wv == 0:
                continue
            env = dict(renv)
            env[w] = float(wv)
            try:
                f = float(fn(**env))
            except Exception:
                return False
            q = f / wv if kind == "mult" else f - wv
            vals.append(q)
        if len(vals) >= 2 and max(vals) - min(vals) > 1e-9:
            return False
    return True


def _short(tag, group):
    op = {"sum": "+", "prod": "*", "diff": "-"}[tag]
    return f"({op.join(group)})" if len(group) > 1 else group[0]


def _make_coarse_fn(fn, groups, coarse_names, coarse_tags, var_names,
                    base=GRID_BASE):
    """A callable over coarse-var kwargs that returns the TRUE target value, by
    realizing each coarse value as a concrete fine env (so the order-n grid reads the
    true coarse curvature). Returns None if a coarse var can't be realized cleanly."""
    def coarse_fn(**ckw):
        env = {}
        for gi, grp in enumerate(groups):
            cn = coarse_names[gi]
            cval = float(ckw[cn])
            tag = coarse_tags[cn]
            if len(grp) == 1:
                env[grp[0]] = cval
                continue
            if tag == "sum":
                env[grp[0]] = cval - base * (len(grp) - 1)
                for g in grp[1:]:
                    env[g] = float(base)
            elif tag == "prod":
                denom = base ** (len(grp) - 1)
                env[grp[0]] = cval / denom if denom else cval
                for g in grp[1:]:
                    env[g] = float(base)
            elif tag == "diff":
                # group of 2: u = g0 - g1; realize g0 = cval + base, g1 = base
                env[grp[0]] = cval + base
                env[grp[1]] = float(base)
            else:
                return None
        return float(fn(**env))
    return coarse_fn


def _term_repr(term) -> str:
    from domains.generator import _term_str
    try:
        return _term_str(term)
    except Exception:
        return str(term.to_dict())


__all__ = [
    "mixed_second_diff", "coupling_matrix", "coupling_groups",
    "is_clean_grouping", "coarsen_synthesize",
]
