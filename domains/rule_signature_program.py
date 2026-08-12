"""domains/rule_signature_program.py — the rule-signature flattening
written in the **P1 Program-IR subset**, so it can leave Python entirely.

WHAT THIS IS. `domains/rule_signature.py::rule_signature` computes the
`where`-clause signature that `_pick_acting_rule` / `_pick_reply_rule` now
read in production (`RULE_SIGNATURE_PRODUCTION_WIRING_RESULTS.md` Part 1).
`SHAPE_TYPE_VOCABULARY_SPIKE.md` §10.1 flags that computation as the arc's
"largest unpriced item": a signature the agent's own decisions depend on is
Python, and Python is the one thing the agent's self-repair machinery
structurally cannot reach.

The function below is the SAME algorithm, restricted to the subset
`domains/prog_ir_emit.py` can emit as hub Program IR (`Prog*` Terms) and
`ProgEval` can execute. Once emitted, the algorithm is **graph data** — a
Term subgraph that reflects, round-trips, and is matched / decoded /
rendered / repaired by the existing prog_read machinery, exactly like every
other Program the agent holds. That is the residency this rung is for; see
`RULE_SIGNATURE_TO_RUST_RESULTS.md`.

IT IS ALSO ORDINARY PYTHON, ON PURPOSE. CPython executes it, so the
three-way differential gate is available: CPython(`rule_signature`) ==
CPython(this) == ProgEval(this-as-IR), over the whole real seed corpus.

WHY IT IS SHAPED THE WAY IT IS. Four engine/emitter boundaries, each
measured (`scripts/rule_signature_to_rust_probe.py`), force the shape. None
is a stylistic choice:

  1. **No nested `def`, no recursion** (`DefFn` blocker). Both of
     `rule_signature`'s recursive walks (`_collect_var_names`, the inner
     `walk`) become explicit LIFO stacks. Pass 1 pushes children in REVERSE
     sorted-key order so the pop order is exactly CPython's pre-order
     recursion — the alpha-rename indices depend on that order.
  2. **No mutating methods** (`RecvMethod:append` / `:add` blockers —
     `ProgCallExtern` is a pure expression with no lvalue write-back).
     Everything accumulates with `+=` (`ProgAugAssign` "add" concatenates
     Tuples, measured).
  2b. **Rows come back as a TUPLE, and the caller makes the frozenset.**
     The natural form — a set (or a dict keyed by row) built inside the
     program — is UNAVAILABLE, because of an engine defect this rung
     found: `cmp_value` (`value.rs:319`) has arms for `(Str, Str)`,
     `(Tuple, Tuple)`, … but **none for `(Surface, Surface)`**, so two
     runtime-BUILT strings fall through to the tag compare and read
     `Equal`. `Value::make_set` / `make_frozenset` dedup by
     `cmp_value == Equal` and `Value::Dict` is a cmp-sorted vec, so a set
     or dict of computed strings COLLAPSES TO ONE ELEMENT (measured:
     `{f"a{i}" for i in range(3)}` → `frozenset({'a0'})`; the same
     program with literal keys is correct). `PartialEq` gets it right
     (`ba == bb`), so this is an Ord/Eq inconsistency, not a missing
     feature — see `RULE_SIGNATURE_TO_RUST_RESULTS.md` §5. Because every
     row's `path` is an f-string, the rows are collected positionally
     instead; the row set has no duplicates by construction (one `rt` row
     per path, one `ra` row per (path, field)), so `frozenset(rows)` in
     the caller is a container conversion, not a dedup that hides a bug.
  3. **`sorted()` does not sort strings lexicographically.** The engine's
     `cmp_value` compares `Value::Str` by INTERNER SYMBOL ID
     (`value.rs:363`), i.e. by the order strings were first seen in the
     process — so `sorted`/`min`/`max`/`Lt` over strings are all
     boot-history dependent, not lexicographic (measured: engine
     `['where','source','var_name','a_zzz','b']` vs CPython
     `['a_zzz','b','source','var_name','where']`). Pass 1's key order is
     LOAD-BEARING (it fixes the variable numbering), so this function
     carries its OWN lexicographic comparator, built from `ord()` on
     `s[i]` (both measured working) — a selection sort, twice inlined
     because the subset has no user-defined functions to share it with.
     ASCII/BMP note: CPython's `<` compares code points and `ord(s[i])`
     yields code points, so the two agree for every key in the corpus
     (Term field names are ASCII identifiers).
  4. **No `isinstance(x, (A, B))`** (`IsinstanceMultiType` blocker) and no
     dict comprehension (`ComprehensionDict`) — both expanded.

`_atomize`'s recursion is likewise stack-shaped: a discovery pass numbers
every sub-value in pre-order, then a rebuild pass walks the numbering
BACKWARDS (children always discovered after their parent, so reverse
discovery order is a valid post-order) and assembles the hashable atom
bottom-up. Nested containers do not occur in the current seed corpus (2917
where-clauses: max atom container depth 1, measured), so this generality is
for rules the agent AUTHORS later, not for anything in the corpus today.

NOT AN AGENT DECISION. Same class as `rule_signature` itself: a pure
`dict -> tuple-of-rows` function with no Substrate handle, no graph write, no
conditional over graph state. The difference is that this one compiles to
graph data.
"""
from __future__ import annotations


def where_signature_rows(where_clause):
    """The §5.3 flattening — P1-subset twin of
    `domains.rule_signature.rule_signature`. Returns the rows
    `("rt", path, term_type)` / `("ra", path, field, atom)` as a TUPLE
    (see docstring note 2b — the caller makes the frozenset), with
    `Var.name` / binder `var_name` positionally alpha-renamed."""
    rows = ()
    if not isinstance(where_clause, dict):
        return rows
    if "type" not in where_clause:
        return rows

    # ---- pass 1: first-appearance order of every variable identifier ----
    # Explicit pre-order DFS. Children are pushed in REVERSE sorted-key
    # order so the LIFO pop order matches CPython's recursion exactly.
    order = ()
    stack = (where_clause,)
    while len(stack) > 0:
        node = stack[len(stack) - 1]
        stack = stack[:len(stack) - 1]
        if isinstance(node, list):
            i = len(node) - 1
            while i >= 0:
                stack += (node[i],)
                i = i - 1
        elif isinstance(node, dict):
            if node.get("type") == "Var":
                nm = node.get("name")
                if isinstance(nm, str):
                    if nm not in order:
                        order += (nm,)
            vn = node.get("var_name")
            if isinstance(vn, str):
                if vn not in order:
                    order += (vn,)
            rem = ()
            for k in node.keys():
                if k != "type":
                    rem += (k,)
            # selection sort, lexicographic by code point (the engine's own
            # string order is interner-symbol-id — see the module docstring)
            ks = ()
            while len(rem) > 0:
                best = rem[0]
                bi = 0
                m = 1
                while m < len(rem):
                    cand = rem[m]
                    lt = 0
                    ci = 0
                    while ci < len(cand):
                        if ci >= len(best):
                            break
                        ca = ord(cand[ci])
                        cb = ord(best[ci])
                        if ca < cb:
                            lt = 1
                            break
                        if ca > cb:
                            break
                        ci = ci + 1
                    if ci >= len(cand):
                        if len(cand) < len(best):
                            lt = 1
                    if lt == 1:
                        best = cand
                        bi = m
                    m = m + 1
                ks += (best,)
                head = rem[:bi]
                head += rem[bi + 1:]
                rem = head
            i = len(ks) - 1
            while i >= 0:
                stack += (node[ks[i]],)
                i = i - 1

    rename = {}
    ri = 0
    while ri < len(order):
        rename[order[ri]] = f"?{ri}"
        ri = ri + 1

    # ---- pass 2: the path-addressed walk over Term nodes ----
    # Row order is irrelevant (every path is absolute and the caller
    # frozensets), so this stack needs no reversal discipline.
    wstack = ((where_clause, ""),)
    while len(wstack) > 0:
        top = wstack[len(wstack) - 1]
        wstack = wstack[:len(wstack) - 1]
        node = top[0]
        path = top[1]
        term_type = node.get("type")
        rows += (("rt", path, term_type),)
        for key in node.keys():
            if key == "type":
                continue
            val = node[key]
            is_term = 0
            if isinstance(val, dict):
                if "type" in val:
                    is_term = 1
            is_list = 0
            if is_term == 0:
                if isinstance(val, list):
                    if len(val) > 0:
                        is_list = 1
                        m = 0
                        while m < len(val):
                            it = val[m]
                            if isinstance(it, dict):
                                if "type" not in it:
                                    is_list = 0
                            else:
                                is_list = 0
                            m = m + 1
            if is_term == 1:
                if path == "":
                    wstack += ((val, key),)
                else:
                    wstack += ((val, f"{path}.{key}"),)
            elif is_list == 1:
                m = 0
                while m < len(val):
                    if path == "":
                        wstack += ((val[m], f"{key}[{m}]"),)
                    else:
                        wstack += ((val[m], f"{path}.{key}[{m}]"),)
                    m = m + 1
            else:
                is_var = 0
                if term_type == "Var":
                    if key == "name":
                        if isinstance(val, str):
                            is_var = 1
                if key == "var_name":
                    if isinstance(val, str):
                        is_var = 1
                if is_var == 1:
                    rows += (("ra", path, key, rename.get(val, val)),)
                else:
                    # ---- inline `_atomize(val)`: discover, then rebuild ----
                    az = (val,)
                    azk = ()
                    azc = ()
                    azn = ()
                    ai = 0
                    while ai < len(az):
                        av = az[ai]
                        if isinstance(av, dict):
                            arem = ()
                            for ak in av.keys():
                                arem += (ak,)
                            asort = ()
                            while len(arem) > 0:
                                abest = arem[0]
                                abi = 0
                                am = 1
                                while am < len(arem):
                                    acand = arem[am]
                                    alt = 0
                                    aci = 0
                                    while aci < len(acand):
                                        if aci >= len(abest):
                                            break
                                        aca = ord(acand[aci])
                                        acb = ord(abest[aci])
                                        if aca < acb:
                                            alt = 1
                                            break
                                        if aca > acb:
                                            break
                                        aci = aci + 1
                                    if aci >= len(acand):
                                        if len(acand) < len(abest):
                                            alt = 1
                                    if alt == 1:
                                        abest = acand
                                        abi = am
                                    am = am + 1
                                asort += (abest,)
                                ahead = arem[:abi]
                                ahead += arem[abi + 1:]
                                arem = ahead
                            achild = ()
                            aj = 0
                            while aj < len(asort):
                                achild += (len(az),)
                                az += (av[asort[aj]],)
                                aj = aj + 1
                            azk += (1,)
                            azc += (achild,)
                            azn += (asort,)
                        else:
                            aseq = 0
                            if isinstance(av, list):
                                aseq = 1
                            if isinstance(av, tuple):
                                aseq = 1
                            if aseq == 1:
                                achild = ()
                                aj = 0
                                while aj < len(av):
                                    achild += (len(az),)
                                    az += (av[aj],)
                                    aj = aj + 1
                                azk += (2,)
                                azc += (achild,)
                                azn += ((),)
                            else:
                                azk += (0,)
                                azc += ((),)
                                azn += ((),)
                        ai = ai + 1
                    abuilt = {}
                    ab = len(az) - 1
                    while ab >= 0:
                        if azk[ab] == 0:
                            abuilt[ab] = az[ab]
                        elif azk[ab] == 2:
                            aout = ()
                            achild = azc[ab]
                            aq = 0
                            while aq < len(achild):
                                aout += (abuilt[achild[aq]],)
                                aq = aq + 1
                            abuilt[ab] = aout
                        else:
                            aout = ()
                            achild = azc[ab]
                            akeys = azn[ab]
                            aq = 0
                            while aq < len(akeys):
                                aout += ((akeys[aq], abuilt[achild[aq]]),)
                                aq = aq + 1
                            abuilt[ab] = aout
                        ab = ab - 1
                    rows += (("ra", path, key, abuilt[0]),)
    return rows
