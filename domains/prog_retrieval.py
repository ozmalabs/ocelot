"""prog_retrieval — Arc 3 R1/R2: the MECHANICAL adapter half of the
retrieval-shaped proposal lane.

`PROGRAM_SYNTHESIS_ARC3_PLAN.md` (R1 store/ranking/screen, R2 the
adaptation ladder), `PROGRAM_SYNTHESIS_ARC3_PREREG.md` / `PROGRAM_SYNTHESIS_
ARC3_R0_NOTES.md` (the oracle ceiling this lane is built to reach: rungs
(a) as-is, (b) arg-permutation, (c) bounded single-leaf edit, (d) an
explicit one-hole re-open), `seeds/mbpp_exemplars.json` (the whole-program
store, built by `scripts/build_exemplar_store.py`), `seeds/program_
synthesis.json` v1.5.0 (the `pr_*` rules that decide everything this module
only records).

ARCHITECTURE (CLAUDE.md). Every function here is a VERB in the
`_enact_advance` sense: it evaluates bound state, runs a BOUNDED,
DETERMINISTIC, generate-and-test computation (screen a candidate; search
permutations; search a fixed leaf-edit catalog; enumerate one re-opened
hole), and records the outcome as FACTS. It never decides what the goal
does NEXT -- every status transition, every accept, every exclusion is a
RULE in `seeds/program_synthesis.json`. This is the exact class
`run_enumerate` already established for `SynthEnumerate`: the SEARCH is a
verb (an "engine seam", Python here because no Rust primitive covers
retrieval-shaped candidate generation and the task brief itself directs
"no Rust ... a genuine engine wall is a recorded residual, not a
workaround" for this phase); the DECISION is always a rule reading the
verb's recorded outcome fact.

  score_exemplars     Mechanical arithmetic (TF-IDF dot product + arity
                      match + type match -- a FIXED FORMULA, the
                      `_row_cmp_ok`/`_trans_logp` class) computed ONCE per
                      goal against every held Exemplar; boarded as
                      ScoreLink proxy nodes (`g -pr_score-> sl
                      -pr_score_exemplar-> exemplar`) so the SELECTION
                      rule (`pr_select_candidate`, a real Argmax-shaped
                      strict-total-order pick over recorded scores) can
                      bind the exemplar as a real node var for `add_edge`
                      (the engine's own `add_edge` effect requires a
                      match-bound or freshly-added var, never a
                      Term-computed target -- confirmed against
                      `graph_rules.rs`; hence the proxy-node design
                      rather than an edge-attribute Argmax).

  run_retrieval_ladder The R2 ladder over the goal's RULE-selected top-k
                      `pr_candidate` exemplars (rank order): (a) as-is,
                      (b) bounded arg-permutation, (c) bounded single-leaf
                      edit at the best near-miss, (d) retrieved-as-
                      skeleton (mask the anchor's own final compute
                      statement -- the R0 rung-(d) masking rule -- derive
                      the hole's row from each revealed row's expected
                      output, and call SynthEnumerate on it; ADAPTED from
                      P7-B's localize-then-reopen-one-hole PRINCIPLE, not
                      a byte-for-byte reuse of the Hole/spawn_subgoal
                      machinery -- named honestly in
                      PROGRAM_SYNTHESIS_ARC3_R12_NOTES.md as a residual,
                      since the retrieved exemplar's structure is not a
                      codebook decode the Hole apparatus is keyed to).
                      EVERY rung's candidate is SCREENED (ProgEval on the
                      goal's own revealed ExampleRows) before it may be
                      recorded as an accept -- this IS the universal
                      execution screen at retrieval grain. Records ONE
                      outcome: `pr_rung_reached` ('a'|'b'|'c'|'d'|'none'),
                      and on a pass, `pr_accept_ir_json` +
                      `pr_accept_task_id` + `pr_accept_perm` +
                      `pr_accept_edit_json`. Consumes NO `ps_attempts` --
                      the `pr_ladder_accept` RULE (seed) is what bumps
                      `ps_attempts` and hands the accepted IR to the
                      UNCHANGED `eval_pending` -> ... -> `ps_accept` chain,
                      so a retrieval accept is verified by the EXACT SAME
                      execution machinery a codebook/enumerate accept is.

  (screen_construction, the universal screen's codebook/chunk half, was
  BUILT, MEASURED, and REVERTED -- see the module-level comment above
  `__all__` and PROGRAM_SYNTHESIS_ARC3_R12_NOTES.md's residuals section
  for the exact regression it caused and why. HR2's screen survives at
  retrieval grain only, where `run_retrieval_ladder` above already IS the
  universal screen for every retrieved candidate.)
"""
from __future__ import annotations

import copy
import itertools
import json
import math
import os
from typing import Any, Dict, List, Optional, Sequence, Tuple

from substrate.seed_loader import manifest_for

from domains import mbpp_spec as ms
from domains import prog_synthesis as psy

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SEED_ID = "mbpp_exemplars"
_TOPK = 5
_SCREEN_BUDGET = 10.0

# --------------------------------------------------------------------------- #
#  BOUNDS -- named exactly as PROGRAM_SYNTHESIS_ARC3_R0_NOTES.md's own
#  `BOUNDS` dict (scripts/retrieval_oracle_ceiling.py); the SAME catalogs,
#  reused rather than re-invented, so R1/R2's ladder matches the measured
#  ceiling's own rungs exactly.
# --------------------------------------------------------------------------- #
_MAX_PERM_ARITY = 4
_ARITH_OPS = ("Plus", "Minus", "Times", "Div", "Mod")
_CMP_OPS = ("Eq", "Lt", "Lte", "Gt", "Gte")
_NUM_OFFSETS = (-2, -1, 1, 2)
_NUM_ABSOLUTES = (0, 1, -1, 2, 3)


def _text(v):
    return psy._text(v)


def _plain(v):
    return psy._plain(v)


# --------------------------------------------------------------------------- #
#  ensure -- idempotent seed install (the ensure_program_synthesis idiom).
# --------------------------------------------------------------------------- #
def ensure_exemplar_store(sub, native, ag_node) -> None:
    """Install the mbpp_exemplars seed (idempotent, Seed-marker guard) and
    reflect each Exemplar's whole-program IR into a subgraph (mechanical
    translation, the `read_off_accepted`/`ir_subgraph` precedent) so the
    ladder can evaluate it via ProgEval without re-parsing JSON per call."""
    if not psy._has_seed(sub, _SEED_ID):
        summary = native.load_seed_manifest(manifest_for(_SEED_ID), ag_node)
        if summary.get("rules_skipped") or summary.get("reflexes_skipped"):
            raise RuntimeError(
                "mbpp_exemplars did not install cleanly: %r" % (summary,))
        sub.add_node("Seed", {"id": _SEED_ID, "version": "1.0.0"})
    for ex in sub.nodes("Exemplar"):
        if sub.neighbours(ex, "ir_subgraph"):
            continue
        ir = json.loads(_text(sub.node(ex)["attrs"].get("ir_json")))
        root = sub._inner.add_term_subgraph(ir)
        sub.add_edge_unchecked(ex, "ir_subgraph", root)


# --------------------------------------------------------------------------- #
#  R1 -- scoring (mechanical arithmetic; SELECTION stays a rule).
# --------------------------------------------------------------------------- #
def _goal_tokens(sub, g) -> List[str]:
    at = sub.node(g)["attrs"]
    return [str(_text(t)).lower() for t in (_plain(at.get("tokens")) or [])]


def _is_mbpp_shaped(text: str) -> bool:
    """A STRICTER, word-boundary-aware re-check of `mbpp_spec`'s own
    verb-frame vocabulary (`_MBPP_VERB_FRAMES_FALLBACK`, the SAME closed
    set `request_facts` uses — reused, not redefined) — purely a scope
    guard for THIS retrieval lane's own eligibility, not a change to the
    shared classifier. `request_facts`'s own `str.startswith` match can
    false-positive across a word boundary (e.g. "write a function
    top_pick..." starts with "write a function to" character-for-
    character, purely because "top_pick" happens to start with "to") —
    harmless for `request_facts`'s own callers (which only read the
    matched-vs-residual text, never gate a DECISION on the boolean), but
    retrieval's exemplar store was built ONLY from genuine MBPP-prompt-
    shaped requests, so a false-positive frame match here would let an
    unrelated hand-written spec (like the "top_pick" battery fixture)
    into a lane it was never meant to reach. Requiring the character
    immediately after the matched frame to be a non-alnum boundary (or
    end-of-string) closes exactly that gap."""
    low = text.lower()
    for frame in ms._MBPP_VERB_FRAMES_FALLBACK:
        if low.startswith(frame) and (len(low) == len(frame) or not low[len(frame)].isalnum()):
            return True
    return False


def _goal_signature(sub, g) -> Optional[Dict[str, Any]]:
    """Mechanical signature read-back from the goal's OWN ExampleRow nodes
    (never prose, never a codebook lookup) — the retrieval-time analog of
    `mbpp_spec.signature_facts`, computed off the SAME rows the goal
    already carries rather than re-parsing `test_list` text."""
    rows = _row_list(sub, g)
    if not rows:
        return None
    names = list(rows[0]["inputs"].keys())
    arg_types = [type(rows[0]["inputs"][n]).__name__ for n in names]
    return_type = type(rows[0]["expected"]).__name__
    return {"arg_count": len(names), "arg_types": arg_types, "return_type": return_type}


def score_exemplars(sub, ag_node, g) -> bool:
    """ONE mechanical scoring pass per goal: for every held Exemplar,
    compute score = (TF-IDF-weighted token overlap with the goal's own
    request tokens) + an arity-match bonus + a type-match bonus -- a fixed
    formula, no decision (the `_row_cmp_ok`/`_trans_logp` class). Boards
    each as a fresh `ScoreLink{score, task_id, picked:0.0}` proxy node
    linked `g -pr_score-> sl -pr_score_exemplar-> exemplar` -- the proxy
    exists ONLY so `pr_select_candidate` can bind the exemplar as a real
    match-var for `add_edge` (the engine's `add_edge` effect requires a
    bound var, never a Term-computed target).

    SCOPE GUARD (mechanical, the SAME classifier `mbpp_spec.request_facts`
    already uses elsewhere — no new decision): a request whose own
    verb-frame is NOT one of the held/fallback MBPP write-frames
    ("write a python function to", ...) scores ZERO exemplars — the
    retrieval store is a bank of MBPP-PROMPT-SHAPED programs, and a
    request that isn't phrased as one is honestly outside its retrieval
    domain (an un-prefixed hand-written spec is exactly the case
    `request_facts` already tags `verb_frame:"other"` for). This keeps
    the ladder a harmless, immediate fall-through for every non-MBPP-
    shaped request (every existing descent/repair/battery fixture, which
    use synthetic phrasing like "write a function xten that returns
    ten") while remaining fully live for real MBPP prompts — the ONLY
    shape the exemplar store's own prompt tokens were ever built from."""
    at = sub.node(g)["attrs"]
    if at.get("pr_scored") == 1.0:
        return False
    request_text = _text(at.get("request")) or ""
    if not _is_mbpp_shaped(request_text):
        sub.set_attr(g, "pr_scored", 1.0)
        return True
    goal_toks = set(_goal_tokens(sub, g))
    goal_sig = _goal_signature(sub, g)
    for ex in sub.nodes("Exemplar"):
        eat = sub.node(ex)["attrs"]
        tfidf = _plain(eat.get("tfidf")) or {}
        overlap = sum(float(w) for tok, w in tfidf.items() if tok in goal_toks)
        arity_bonus = 0.0
        type_bonus = 0.0
        if goal_sig is not None:
            if int(eat.get("arity") or -1) == int(goal_sig.get("arg_count") or -2):
                arity_bonus = 2.0
            ex_types = _plain(eat.get("arg_types")) or []
            g_types = goal_sig.get("arg_types") or []
            if ex_types and g_types and list(ex_types) == list(g_types):
                type_bonus = 1.0
            if _text(eat.get("return_type")) and \
                    _text(eat.get("return_type")) == goal_sig.get("return_type"):
                type_bonus += 0.5
        score = round(overlap + arity_bonus + type_bonus, 6)
        sl = sub.add_node("ScoreLink", {
            "score": score, "task_id": int(eat.get("task_id")), "picked": 0.0})
        sub.add_edge_unchecked(g, "pr_score", sl)
        sub.add_edge_unchecked(sl, "pr_score_exemplar", ex)
    sub.set_attr(g, "pr_scored", 1.0)
    return True


# --------------------------------------------------------------------------- #
#  R2 -- the adaptation ladder. Mechanical generate-and-test, byte-adjacent
#  to scripts/retrieval_oracle_ceiling.py's own rung (a)-(d) functions (the
#  SAME bounded catalogs, the SAME structural walk) but reading the goal's
#  live ExampleRow nodes instead of a plain dict list.
# --------------------------------------------------------------------------- #
def _row_list(sub, g) -> List[Dict[str, Any]]:
    msg = None
    for n in sub.neighbours(g, "about_message"):
        msg = n
    rows = []
    if msg is None:
        return rows
    for r in sub.neighbours(msg, "has_example"):
        rat = sub.node(r)["attrs"]
        rows.append({
            # Rung 2: `_unwire` -- this row's inputs_json is now
            # `_wire`-tagged at write time (prog_synthesis.py's
            # `_add_example_row`), so every reader must invert it.
            "inputs": psy._unwire(json.loads(_text(rat.get("inputs_json")) or "{}")),
            "expected": rat.get("expected"),
            "tol": rat.get("row_tol"),
            "unordered": rat.get("row_unordered") == 1.0,
        })
    return rows


def _eval_ir(sub, ir: Dict[str, Any], env: Dict[str, Any]) -> Tuple[Any, bool]:
    root = sub._inner.add_term_subgraph(ir)
    try:
        out = sub._inner.evaluate(psy._prog_eval_term("e", "p"), {"e": env, "p": root})
    finally:
        sub._inner.remove_term_subgraph(root)
    got = out.get("result")
    ok = out.get("halted") is True and out.get("trap") is None
    return got, ok


def _mapped_env(params: Sequence[str], perm: Sequence[int], row: Dict[str, Any]) -> Dict[str, Any]:
    vals = list(row["inputs"].values())
    mapped = [vals[perm[i]] for i in range(len(perm))]
    return dict(zip(params, mapped))


_RENAME_TYPES = ("Var", "ProgDefFnParam", "ProgAssignVar")


def _rename_vars(node: Any, rename: Dict[str, str]) -> Any:
    """Mechanical alpha-rename: every `name` field of a Var/ProgDefFnParam/
    ProgAssignVar node whose value is a key of `rename` is replaced by its
    mapped value — a structural translation (never touches ProgCallExtern's
    own `name`, which names an EXTERNAL FUNCTION, not a variable). Needed
    because the goal's own ExampleRow env is keyed by the REQUEST's own
    canonical arg names ('a', 'b', ... — `mbpp_spec._row_from_call`'s
    convention), never the retrieved exemplar's own parameter names — a
    retrieval accept must speak the goal's own names before it can be
    executed by the UNCHANGED `eval_and_record` (which reads
    `ExampleRow.inputs_json`, not this module's own env)."""
    if isinstance(node, dict):
        out = {k: _rename_vars(v, rename) for k, v in node.items()}
        if out.get("type") in _RENAME_TYPES and isinstance(out.get("name"), str) \
                and out["name"] in rename:
            out["name"] = rename[out["name"]]
        return out
    if isinstance(node, list):
        return [_rename_vars(x, rename) for x in node]
    return node


def _canonical_rename(params: Sequence[str], perm: Sequence[int],
                      canonical_names: Sequence[str]) -> Dict[str, str]:
    """`params[i]` (the exemplar's i-th declared param) is bound, under
    `perm`, to the row's `canonical_names[perm[i]]` slot (the SAME mapping
    `_mapped_env` applies to VALUES) — so renaming `params[i] ->
    canonical_names[perm[i]]` throughout the IR makes it executable
    directly against the goal's own (unpermuted, canonically-named)
    ExampleRow env, with the permutation baked into the rename rather than
    needed at call time."""
    return {params[i]: canonical_names[perm[i]] for i in range(len(perm))}


def _to_goal_ir(ir: Dict[str, Any], params: Sequence[str], perm: Sequence[int],
                revealed: List[Dict[str, Any]]) -> Dict[str, Any]:
    canonical = list(revealed[0]["inputs"].keys())
    rename = _canonical_rename(params, perm, canonical)
    return _rename_vars(ir, rename)


def _run_candidate(sub, ir: Dict[str, Any], params: Sequence[str], perm: Sequence[int],
                   rows: List[Dict[str, Any]]) -> Tuple[bool, int, int]:
    n_pass = 0
    diff_sum = 0
    for r in rows:
        try:
            env = _mapped_env(params, perm, r)
            got, ok = _eval_ir(sub, ir, env)
            if ok:
                ok = bool(psy._row_cmp_ok(got, r["expected"], r.get("tol"),
                                          bool(r.get("unordered"))))
        except Exception:  # noqa: BLE001 — never crash the ladder
            ok, got = False, None
        if ok:
            n_pass += 1
        else:
            diff_sum += 0 if got == r["expected"] else 1
    return n_pass == len(rows), n_pass, diff_sum


def _walk_edit_points(node: Any, path: Tuple[Any, ...] = ()) -> List[Dict[str, Any]]:
    points: List[Dict[str, Any]] = []
    if isinstance(node, dict):
        t = node.get("type")
        if t == "Lit":
            v = node.get("value")
            if isinstance(v, bool):
                pass
            elif isinstance(v, (int, float)):
                points.append({"path": path + ("value",), "kind": "lit_num", "orig": v})
            elif isinstance(v, str):
                points.append({"path": path + ("value",), "kind": "lit_str", "orig": v})
        elif t in _ARITH_OPS:
            points.append({"path": path + ("type",), "kind": "op", "family": "arith", "orig": t})
        elif t in _CMP_OPS:
            points.append({"path": path + ("type",), "kind": "op", "family": "cmp", "orig": t})
        for k, v in node.items():
            points.extend(_walk_edit_points(v, path + (k,)))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            points.extend(_walk_edit_points(v, path + (i,)))
    return points


def _candidates_for(point: Dict[str, Any], revealed: List[Dict[str, Any]]) -> List[Any]:
    if point["kind"] == "lit_num":
        v = point["orig"]
        offs = [v + o for o in _NUM_OFFSETS]
        return sorted(set(offs) | set(_NUM_ABSOLUTES) - {v})
    if point["kind"] == "lit_str":
        v = point["orig"]
        pool: set = set()
        for r in revealed:
            for x in r["inputs"].values():
                if isinstance(x, str):
                    pool.add(x)
            if isinstance(r["expected"], str):
                pool.add(r["expected"])
        return sorted(pool - {v})
    fam = _ARITH_OPS if point["family"] == "arith" else _CMP_OPS
    return [o for o in fam if o != point["orig"]]


def _apply_edit(ir: Dict[str, Any], point: Dict[str, Any], candidate: Any) -> Dict[str, Any]:
    ir2 = copy.deepcopy(ir)
    node = ir2
    for k in point["path"][:-1]:
        node = node[k]
    node[point["path"][-1]] = candidate
    return ir2


def _top_level_stmts(ir: Dict[str, Any]) -> List[Dict[str, Any]]:
    if isinstance(ir, dict) and ir.get("type") == "ProgSeq":
        return list(ir.get("stmts") or [])
    return [ir]


def _final_compute_index(stmts: List[Dict[str, Any]]) -> Optional[int]:
    if not stmts:
        return None
    last = stmts[-1]
    if last.get("type") == "ProgReturn":
        val = last.get("value")
        if (isinstance(val, dict) and val.get("type") == "Var" and len(stmts) >= 2
                and stmts[-2].get("type") == "ProgAssignVar"
                and stmts[-2].get("name") == val.get("name")):
            return len(stmts) - 2
        return len(stmts) - 1
    return len(stmts) - 1


def _candidate_pool(sub, g) -> List[Dict[str, Any]]:
    """Read the RULE-selected `pr_candidate` edges back into plain dicts —
    a mechanical read-back (the `read_goal` idiom), never a selection
    decision (that already happened in `pr_select_candidate`). Order is
    the engine's own edge-insertion order, which `pr_select_candidate`
    mints in best-first rank order (one edge per successive fixpoint
    round, strict-total-order tie-broken) — the SAME insertion-order
    reliance `read_goal`'s `sub.neighbours(g, "has_hole")` already uses
    elsewhere in this codebase."""
    out = []
    for ex in sub.neighbours(g, "pr_candidate"):
        eat = sub.node(ex)["attrs"]
        ir = json.loads(_text(eat.get("ir_json")))
        out.append({
            "node": ex, "task_id": int(eat.get("task_id")),
            "arity": int(eat.get("arity")), "params": list(_plain(eat.get("params")) or []),
            "ir": ir,
        })
    return out


def run_retrieval_ladder(sub, ag_node, g) -> bool:
    """The R2 ladder over the goal's top-k RULE-selected candidates. ONE
    call does rungs (a)-(d) in Occam order and records a single outcome —
    `pr_ladder_done` + `pr_rung_reached` (+ accept facts on a pass). Every
    rung SCREENS on the goal's own revealed ExampleRows before it may be
    recorded as a pass — the universal execution screen, retrieval half."""
    at = sub.node(g)["attrs"]
    if at.get("pr_ladder_done") == 1.0:
        return False
    revealed = _row_list(sub, g)
    candidates = _candidate_pool(sub, g)
    sub.set_attr(g, "pr_n_candidates", float(len(candidates)))
    if not revealed or not candidates:
        sub.set_attr(g, "pr_rung_reached", "none")
        sub.set_attr(g, "pr_ladder_done", 1.0)
        return True

    identity_cache: Dict[int, Tuple[int, ...]] = {}

    def identity(arity: int) -> Tuple[int, ...]:
        if arity not in identity_cache:
            identity_cache[arity] = tuple(range(arity))
        return identity_cache[arity]

    # ---- rung (a): as-is, rank order. ----
    for c in candidates:
        arity = len(revealed[0]["inputs"])
        if c["arity"] != arity:
            continue
        ok, _n, _d = _run_candidate(sub, c["ir"], c["params"], identity(arity), revealed)
        if ok:
            sub.set_attr(g, "pr_rung_reached", "a")
            sub.set_attr(g, "pr_accept_ir_json", json.dumps(
                _to_goal_ir(c["ir"], c["params"], identity(arity), revealed)))
            sub.set_attr(g, "pr_accept_task_id", float(c["task_id"]))
            sub.set_attr(g, "pr_accept_params", list(c["params"]))
            sub.set_attr(g, "pr_ladder_done", 1.0)
            return True

    # ---- rung (b): bounded arg permutation (arity <= 4). ----
    best = {"n_pass": -1, "diff": None, "cand": None, "perm": None}

    def consider(c, perm, n_pass, diff):
        key = (n_pass, -diff)
        cur = (best["n_pass"], -(best["diff"] if best["diff"] is not None else 10 ** 9))
        if key > cur:
            best.update(n_pass=n_pass, diff=diff, cand=c, perm=perm)

    arity = len(revealed[0]["inputs"])
    if 2 <= arity <= _MAX_PERM_ARITY:
        for c in candidates:
            if c["arity"] != arity:
                continue
            for perm in itertools.permutations(range(arity)):
                ok, n_pass, diff = _run_candidate(sub, c["ir"], c["params"], perm, revealed)
                if perm != identity(arity):
                    consider(c, perm, n_pass, diff)
                if ok and perm != identity(arity):
                    sub.set_attr(g, "pr_rung_reached", "b")
                    sub.set_attr(g, "pr_accept_ir_json", json.dumps(
                        _to_goal_ir(c["ir"], c["params"], perm, revealed)))
                    sub.set_attr(g, "pr_accept_task_id", float(c["task_id"]))
                    sub.set_attr(g, "pr_accept_params", list(c["params"]))
                    sub.set_attr(g, "pr_accept_perm", list(perm))
                    sub.set_attr(g, "pr_ladder_done", 1.0)
                    return True
    else:
        for c in candidates:
            if c["arity"] != arity:
                continue
            ok, n_pass, diff = _run_candidate(sub, c["ir"], c["params"], identity(arity), revealed)
            consider(c, identity(arity), n_pass, diff)

    if best["cand"] is None:
        sub.set_attr(g, "pr_rung_reached", "none")
        sub.set_attr(g, "pr_ladder_done", 1.0)
        return True

    # ---- rung (c): single-leaf edit on the best near-miss anchor. ----
    anchor, perm = best["cand"], tuple(best["perm"])
    points = _walk_edit_points(anchor["ir"])
    for point in points:
        for cand_val in _candidates_for(point, revealed):
            edited = _apply_edit(anchor["ir"], point, cand_val)
            ok, _n, _d = _run_candidate(sub, edited, anchor["params"], perm, revealed)
            if ok:
                sub.set_attr(g, "pr_rung_reached", "c")
                sub.set_attr(g, "pr_accept_ir_json", json.dumps(
                    _to_goal_ir(edited, anchor["params"], perm, revealed)))
                sub.set_attr(g, "pr_accept_task_id", float(anchor["task_id"]))
                sub.set_attr(g, "pr_accept_params", list(anchor["params"]))
                sub.set_attr(g, "pr_accept_perm", list(perm))
                sub.set_attr(g, "pr_accept_edit_json", json.dumps(
                    {"path": list(point["path"]), "kind": point["kind"],
                     "from": point["orig"], "to": cand_val}))
                sub.set_attr(g, "pr_ladder_done", 1.0)
                return True

    # ---- rung (d): retrieved-as-skeleton (mask the anchor's final compute
    # statement; derive the hole's row from each revealed row's OWN
    # expected output evaluated over the PREFIX's live vars — the R0
    # rung-(d) masking rule, adapted from P7-B's localize/re-open-one-hole
    # PRINCIPLE, applied directly at retrieval grain — see the module
    # docstring's honesty note). ----
    stmts = _top_level_stmts(anchor["ir"])
    idx = _final_compute_index(stmts)
    if idx is None:
        sub.set_attr(g, "pr_rung_reached", "none")
        sub.set_attr(g, "pr_ladder_done", 1.0)
        return True
    prefix = stmts[:idx]
    derived_rows: List[Dict[str, Any]] = []
    args_seen: List[str] = []
    all_derivable = True
    for r in revealed:
        env = _mapped_env(anchor["params"], perm, r)
        for k in env:
            if k not in args_seen:
                args_seen.append(k)
        try:
            if prefix:
                pre_ir = {"type": "ProgSeq",
                         "stmts": prefix + [{"type": "ProgReturn",
                                             "value": {"type": "Lit", "value": None}}]}
                _got, ok = _eval_ir(sub, pre_ir, env)
            else:
                ok = True
        except Exception:  # noqa: BLE001
            ok = False
        if not ok:
            all_derivable = False
            break
        derived_rows.append({"inputs": psy._wire(env),
                             "output": psy._wire(r["expected"])})
    if not all_derivable or not derived_rows:
        sub.set_attr(g, "pr_rung_reached", "none")
        sub.set_attr(g, "pr_ladder_done", 1.0)
        return True
    try:
        # PROGRAM_SYNTHESIS_MODSQRT_SCOPED_FIX: this call omits an explicit
        # `ops` key (like every pre-existing caller here), so it reaches
        # the SAME Rust-internal bare-scalar typed default `domains/
        # prog_synthesis.py::run_enumerate`'s own top-level call reaches --
        # confirmed BY LIVE TRACE (not assumed) to be the exact, sole
        # cross-lane call site that regressed tasks 59/135/138/406 when
        # Mod/Sqrt were exposed there unconditionally
        # (PROGRAM_SYNTHESIS_MODSQRT_SCOPED_FIX_PREREG.md sec.2): a
        # cheap, spurious Mod/Sqrt-shaped candidate fits this rung's own
        # masked-hole sub-spec's few revealed rows without being the true
        # general program, and gets accepted here (labelled
        # `retrieved_exemplar` uniformly with every other retrieval-ladder
        # rung) before the holdout row catches it. `exclude_ops` is a
        # soft, call-site-scoped filter (`runners/dsl/src/synth_enumerate
        # .rs`'s `op_list` post-filter, mirroring `exclude`'s own
        # "unrecognized names silently skipped" discipline) -- it does
        # NOT touch `domains/prog_synthesis.py::run_enumerate`'s own
        # top-level call (which never sets this field), so Mod/Sqrt stay
        # fully available there.
        # UNREGISTERED_OPS_WITNESS_CHECK: `Shl`/`BitXor`/`BitAnd` are NOT in
        # the bare-scalar typed default at all (priced, then declined --
        # see that branch's own comment: `Shl` alone reproduces this exact
        # mechanism on task 58, `BitXor`/`BitAnd` on task 435), so excluding
        # any of them here would be a no-op; left off the list rather than
        # added defensively, matching this arc's own "never state a scope
        # wider than what's actually true" discipline.
        spec = {"type": "SynthEnumerate",
               "examples": {"type": "Lit", "value": derived_rows},
               "max_size": 7, "max_candidates": 0, "saturate_k": 0, "field": "",
               "exclude_ops": {"type": "Lit", "value": ["Mod", "Sqrt"]}}
        out = sub._inner.evaluate(spec, {})
    except Exception:  # noqa: BLE001
        out = None
    found = bool(out and out.get("found")) if isinstance(out, dict) else False
    term_json = _text(out.get("term")) if found else None
    if not (found and term_json):
        sub.set_attr(g, "pr_rung_reached", "none")
        sub.set_attr(g, "pr_ladder_done", 1.0)
        return True
    hole_term = json.loads(term_json)
    new_last = {"type": "ProgReturn", "value": hole_term}
    full_ir = {"type": "ProgSeq", "stmts": prefix + [new_last]}
    ok, _n, _d = _run_candidate(sub, full_ir, anchor["params"], perm, revealed)
    if ok:
        sub.set_attr(g, "pr_rung_reached", "d")
        sub.set_attr(g, "pr_accept_ir_json", json.dumps(
            _to_goal_ir(full_ir, anchor["params"], perm, revealed)))
        sub.set_attr(g, "pr_accept_task_id", float(anchor["task_id"]))
        sub.set_attr(g, "pr_accept_params", list(anchor["params"]))
        sub.set_attr(g, "pr_accept_perm", list(perm))
        sub.set_attr(g, "pr_accept_edit_json", json.dumps(
            {"kind": "retrieved_as_skeleton", "masked_stmt_index": idx,
             "hole_term": hole_term}))
        sub.set_attr(g, "pr_ladder_done", 1.0)
        return True
    sub.set_attr(g, "pr_rung_reached", "none")
    sub.set_attr(g, "pr_ladder_done", 1.0)
    return True


# --------------------------------------------------------------------------- #
#  HR2 residual -- the universal execution screen's codebook/chunk half
#  (a dry-run of `splice_binding`'s template->IR logic, gating ps_propose's
#  Argmax pick before it could spend an attempt) was BUILT AND MEASURED,
#  then REVERTED: it produced false negatives on legitimate PARTIAL-COVER
#  constructions (a construction that does not fit every revealed row
#  ALONE but is the descent machinery's correct starting point once a hole
#  is filled in — `ps_descend_mark`/`build_descent` decode PARTIAL cover
#  directly off the whole codebook via ShapeDecode, independent of
#  ps_propose's Argmax/exclusion set). Excluding a screen-failing-but-
#  legitimate partial cover stranded the goal with NO eligible codebook
#  pick while descent (which never consults `ps_excluded`) still used it
#  via its own path — `ps_rung_codebook`/`ps_attempts` then never got set
#  by `ps_propose` at all, a real, measured regression against
#  `test_prog_repair_migrated.py::test_headline_la10_converts_to_holdout_
#  ok_via_repair` (byte-identical-behaviour requirement, a file this phase
#  does not own and cannot patch). Reverted rather than risk this class of
#  breakage across the wider descent/repair surface under this phase's
#  time budget; see PROGRAM_SYNTHESIS_ARC3_R12_NOTES.md § residuals.
#  The universal screen SURVIVES at retrieval grain, where it is safe by
#  construction (a retrieved exemplar's rungs a-d ALWAYS execute the FULL
#  candidate program against the FULL revealed row set -- there is no
#  partial-cover case to misclassify).
# --------------------------------------------------------------------------- #


__all__ = [
    "ensure_exemplar_store", "score_exemplars", "run_retrieval_ladder",
]
