"""prog_synthesis — P4-B: the MECHANICAL adapter half of the generation loop.

PROGRAM_SYNTHESIS_PLAN.md §2 / §4-P4, PROGRAM_SYNTHESIS_PREREG.md §6 (H4).
The loop itself — propose → build → verify → accept / counterexample / gap —
is `seeds/program_synthesis.json` (43 rules; every status transition is a
rule; v1.1.0 adds ps_enumerate_fresh_attempt — the P6.5 fix that gives the
enumerate rung's evaluation a fresh attempt number after a consumed codebook
attempt, closing the powered battery's stalled:evaluated defect; v1.2.0 adds
the P7-A RECURSIVE DESCENT rung, PROGRAM_SYNTHESIS_P7_PREREG.md H7a — see
the descent verbs below; v1.3.0 adds the P7-B TRACE-GUIDED LOCAL REPAIR
lane, prereg H7b — see the repair verbs below).
This module is ONLY the world-adapter rim, the `_enact_advance`
precedent: evaluate bound Terms, apply results, never branch on graph state.

What each verb does (and why it is admissible under CLAUDE.md):

  ingest_spec        NL request text + example rows → Message attrs +
                     ExampleRow nodes. The write-request verdict is the
                     EXISTING sanctioned thin classifier
                     (`code_writing.looks_like_write_request` over the held
                     code_write_request_cues Concepts) recorded as a fact
                     (`ps_write_request`) — the `_write_function_reply`
                     outcome-datum precedent. Token prep is
                     `code_writing._content_tokens` (fixed text prep).
                     The target name is a fixed positional extraction
                     (token after a function-noun cue) — I/O-boundary
                     parse, no graph-state conditional.

  stamp_lattice      The ink_decode._lattice_partition precedent, at
                     statement grain: stamps Hyp/LatEdge candidates for the
                     rule-chosen template's statement parts on a FRESH
                     throwaway substrate, scored by the boarded
                     ConstructionBigram trans_logp (P3's corpus statistics),
                     ticks active_pos, seeds the backtrace, reads the
                     on_path sequence back. The DECODE is the unchanged
                     seeds/viterbi_decode.json vit_step/vit_backtrace.
                     `ps_spine_ok` (decoded sequence is a permutation of
                     the parts) is a recorded FACT (ink's fixed-formula
                     class); the ps_latticed / ps_lattice_failed RULES
                     decide what to do with it.

  splice_binding     Mechanical splice of the RULE-chosen construction's
                     template into concrete hub IR: params from the
                     template's args, body = ProgReturn(term) for an
                     expression-grain template, or the template's statement
                     parts in the LATTICE-decided order for a spine
                     template. Writes `ps_ir` (Term-JSON) + `ps_ir_built`.

  eval_and_record    Reflects the IR (add_term_subgraph), records the
                     round-trip fact `ps_reflect_ok` (byte-stable canonical
                     JSON — the structural verdict datum), then evaluates
                     ProgEval OVER THE REFLECTED SUBGRAPH per ExampleRow
                     and records got / eval_ok / eval_attempt facts. The
                     pass/fail DECISIONS are ps_row_pass / ps_row_fail /
                     ps_verified — rules.

  run_enumerate      The P4-A seam: feature-detects the SynthEnumerate Term
                     with a tiny evaluate probe and records
                     `ps_enumerate_outcome` ('unavailable' | 'ok' |
                     'failed'). Rules read ONLY the outcome fact, so wiring
                     the landed Term is zero rule changes.

  screen_construction  Arc3-R2.5 (seed v1.5.1): the SCOPED codebook-side
                     half of the universal execution screen — a dry run of
                     `splice_binding`'s own template->IR logic against the
                     goal's REVEALED rows, spending NO `ps_attempts`.
                     `ps_screen_mark` only ever arms this verb when the
                     goal is NOT DESCEND_APPLICABLE (the same predicate
                     ps_descend_mark/ps_enumerate_mark embed), so every
                     candidate it judges can ONLY ever be used as a
                     complete, stand-alone program — the false-negative
                     class that sank Attempt 1 (PROGRAM_SYNTHESIS_
                     ARC3_R12_NOTES.md) cannot occur here by construction.
                     Records `ps_screen_verdict`; `ps_screen_reject` /
                     `ps_screen_admit` decide everything downstream.

  read_off_accepted  Mechanical read-back of an accepted goal's Program +
                     IR JSON; links the reflected IR root onto the Program
                     node (`ir_subgraph` edge — both representations, the
                     scope pin's "do both").

  P7-A descent verbs (seed v1.2.0 — "shapedecode will tell you what is
  going on"; every DECISION is a ps_descend_* / ps_plan_* / ps_hole_* /
  ps_foldup_* rule, these verbs only evaluate bound Terms and record):

  build_descent      Evaluates the SAME ShapeDecode the propose rule binds
                     (goal skeleton vs the held codebook) and records the
                     decode's coverage assignment as goal facts
                     (ps_cover_parts / ps_cover_first / ps_cover_count /
                     ps_residual_tokens) — boundaries come from the decode,
                     never a Python cut (the ink lattice precedent).

  derive_hole_rows   Mechanically derives the current Hole's local
                     (inputs, expected) rows where the skeleton makes them
                     DETERMINABLE (prereg H7a scope): fold_step — the
                     one-iteration unroll (a singleton-list outer row pins
                     acc_before = init, acc_after = the outer output; no
                     inversion, no arithmetic); final_expr — outer rows
                     over LIVE VARS (each covered construction's template
                     term evaluated on the row's own inputs — prefix
                     evaluation + record). Non-determinable rows are
                     counted, never guessed; the ps_hole_derived /
                     ps_hole_underivable RULES judge the recorded facts.

  spawn_subgoal      Transcribes the rule-decided sub-goal: a Message
                     carrying the decode's RESIDUAL tokens as the sub-spec
                     (+ derived ExampleRows). ps_goal mints the sub-Goal
                     and the SAME ladder runs one grain finer with its own
                     fresh integer counters (collision-free, the P6.5
                     lesson applied from the start).

  fold_up            Splices the accepted sub-IR into the skeleton
                     (mechanical structural substitution), reflects it,
                     and re-runs ProgEval over the FULL outer rows into
                     the descent-scoped fu_* row lane (NEVER the
                     eval_attempt/verdict_attempt lane — the P6.5 attempt
                     collision cannot re-arm by construction). The
                     ps_foldup_accept / ps_foldup_reject rules give the
                     execution verdict at the outer level.

  P7-B repair verbs (seed v1.3.0 — trace-guided LOCAL repair,
  PROGRAM_SYNTHESIS_P7_PREREG.md H7b; the decisions are the ps_repair_* /
  ps_localize_* rules, these verbs only record facts):

  ingest_counterexample  CEGIS at the accept boundary: an externally-observed
                     failing row (the environment's/verifier's report) becomes
                     an ExampleRow{ce_pending:1.0} on the goal's spec Message —
                     a recorded datum (the ps_write_request precedent). The
                     ps_repair_mark RULE decides the accept is refuted.

  record_trace       Boundary facts for the failing row(s): prefix evaluation
                     of the accepted IR at each statement boundary, compared
                     against expectations DERIVED by descent's own
                     row-derivation machinery (final_expr: each covered
                     construction's template re-evaluated per row — the
                     _derive_final_expr walk; fold_step: the one-iteration
                     unroll on a SINGLETON counterexample row — the
                     _derive_fold_step scope). Where no expectation is
                     derivable the facts say so and the ps_localize_refuse_*
                     rules fall to the untouched global CEGIS path. Facts:
                     ps_trace_skel_agree / ps_trace_diverge_hole /
                     ps_trace_derivable / ps_trace_json (+ per-row consume
                     markers). Fixed formulas, ink's ps_spine_ok class.

  (repair re-solve)  No new verbs: ps_localize_hole re-opens ONLY the
                     localized hole as a fresh Hole{repair:1} on the same
                     collision-free plan_seq counter, and the UNCHANGED
                     descent verbs run it — derive_hole_rows now derives from
                     the outer rows INCLUDING the counterexample row (the
                     propagation that kills first-fit overfitting),
                     spawn_subgoal carries the hole-scope exclusion facts
                     (ExcludedSub → ps_enum_excluded / ps_enum_drop_consts on
                     the sub-message; drops are the excluded bare-Lit values
                     the SynthEnumerate contract can actually remove — NON-
                     output consts only, the Term re-appends integer spec
                     outputs by contract), fold_up re-verifies the FULL rows.

  pump               The fixpoint driver: run_rules, then dispatch the
                     pending mechanical verb per goal STATUS — a name-keyed
                     dispatch on rule verdicts (sanctioned), not a decision.

Bigram boarding (`ensure_construction_bigrams`) consumes P3 residual 4: the
131 ConstructionBigram rows of results/prog_construction_scan.json board the
agent substrate HERE, aggregated to statement-HEAD grain (the quantum-name →
head projection is mechanical: signature[0][1]; counts summed, add-1
smoothing recomputed with the SAME formula the scan registered) — the P4
lattice scores label sequences at the grain the write templates speak.
"""
from __future__ import annotations

import json
import math
import os
from fractions import Fraction
from typing import Any, Dict, List, Optional

import substrate_rs as srs
from substrate.seed_loader import manifest_for

from domains import code_writing as cw
from domains import prog_ir_signature as pis
from domains.prog_ir_emit import NATIVE_ORACLES
from domains import prog_retrieval as pr
from domains import prog_exact as pex
from domains import prog_property as pp
from domains import prog_moves as pmv

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SEED_ID = "program_synthesis"
_GROUNDING_SEED_ID = "program_synthesis_grounding"
_BIGRAM_SEED_ID = "program_synthesis_bigrams"
_BIGRAM_ARTIFACT = os.path.join(_ROOT, "results", "prog_construction_scan.json")
_FUEL = 10000
_SCALARS = (int, float, str, bool)
_BOUNDARY = ("<s>", "</s>")


# --------------------------------------------------------------------------- #
#  ensure — idempotent seed install + bigram boarding (mechanical I/O).
# --------------------------------------------------------------------------- #
def _has_seed(sub, seed_id: str) -> bool:
    for n in sub.nodes("Seed"):
        if sub.node(n)["attrs"].get("id") == seed_id:
            return True
    return False


def ensure_program_synthesis(sub, native, ag_node) -> None:
    """Install the program_synthesis seed + the write codebook + the request
    cue Concepts, normalise write-shape triggers, board the P3 bigrams.
    All idempotent (Seed-marker guard, the `_ensure_shape_decode_loop`
    idiom); no decisions. v1.5.0 (Arc3-R1): also installs the whole-program
    exemplar store the retrieval ladder scores/adapts against
    (`prog_retrieval.ensure_exemplar_store`, its own idempotent seed)."""
    if not _has_seed(sub, _SEED_ID):
        summary = native.load_seed_manifest(manifest_for(_SEED_ID), ag_node)
        if summary.get("rules_skipped") or summary.get("reflexes_skipped"):
            raise RuntimeError(
                "program_synthesis did not install cleanly: %r" % (summary,))
        sub.add_node("Seed", {"id": _SEED_ID, "version": "1.5.0"})
    # the write codebook (the 8 starter shapes) + the cue Concepts the
    # sanctioned classifier reads — both existing facilities, reused.
    cw.ensure_write_codebook(sub)
    if not _has_seed(sub, "code_write_request_cues"):
        summary = native.load_seed_manifest(
            manifest_for("code_write_request_cues"), ag_node)
        sub.add_node("Seed", {"id": "code_write_request_cues",
                              "version": "1.1.0"})
    if not _has_seed(sub, "exact_families"):
        summary = native.load_seed_manifest(
            manifest_for("exact_families"), ag_node)
        if summary.get("rules_skipped") or summary.get("reflexes_skipped"):
            raise RuntimeError(
                "exact_families did not install cleanly: %r" % (summary,))
        sub.add_node("Seed", {"id": "exact_families", "version": "1.0.0"})
    if not _has_seed(sub, _GROUNDING_SEED_ID):
        summary = native.load_seed_manifest(
            manifest_for(_GROUNDING_SEED_ID), ag_node)
        if summary.get("rules_skipped") or summary.get("reflexes_skipped"):
            raise RuntimeError(
                "program_synthesis_grounding did not install cleanly: %r"
                % (summary,))
        sub.add_node("Seed", {
            "id": _GROUNDING_SEED_ID,
            "version": "1.0.0",
        })
    ensure_program_synthesis_opgrammar(sub, native, ag_node)
    _normalise_triggers(sub)
    _normalise_fold_marks(sub)
    ensure_construction_bigrams(sub)
    pr.ensure_exemplar_store(sub, native, ag_node)


def _normalise_triggers(sub) -> None:
    """Mechanical migration: every code_write_construction quantum whose
    trigger vocabulary lives only in the JSON-string `signature` attr gets a
    flat `trigger_tokens` LIST attr (parse + flatten — a fixed translation,
    the rules' Exists/In guards read lists, not JSON strings)."""
    for n in sub.nodes("ShapeSignature"):
        at = sub.node(n)["attrs"]
        if at.get("kind") != "code_write_construction":
            continue
        if at.get("trigger_tokens") is not None:
            continue
        sig = at.get("signature")
        if not isinstance(sig, (str, bytes)):
            continue
        try:
            rels = json.loads(sig)
        except Exception:
            continue
        tokens: List[str] = []
        for rel in rels if isinstance(rels, list) else []:
            for tok in rel if isinstance(rel, list) else []:
                tokens.append(str(tok))
        sub.set_attr(n, "trigger_tokens", tokens)


def _normalise_fold_marks(sub) -> None:
    """Mechanical migration (the `_normalise_triggers` idiom, P7-A /
    Arc2-Q4): every code_write_construction quantum's ground_template JSON
    gets flat STRUCTURAL FACTS the plan rules' Exists guards read — no
    decision, a parse + flag translation exactly like `_normalise_triggers`.

    `tmpl_fold`         P7-A: the template is a Fold with a literal init.
    `tmpl_scalar_fold`  Arc2-Q4: ALSO a Fold, but its `source` is NOT a
                        bare `Var` (i.e. a COMPUTED source — a range()-class
                        extern call, the factorial/sum-to-n scalar
                        accumulation class) rather than a Var bound to a
                        list input.
    `tmpl_branch`       Arc2-Q4: the template is an IfThenElse (the
                        decided-condition branch class, e.g.
                        max_of_two/min_of_two) — the SAME structural-fact
                        idiom as tmpl_fold, one level up the op tree;
                        ps_plan_branch_arm's Exists guard reads it exactly
                        as ps_plan_fold_step reads tmpl_fold."""
    for n in sub.nodes("ShapeSignature"):
        at = sub.node(n)["attrs"]
        if at.get("kind") != "code_write_construction":
            continue
        if at.get("tmpl_fold") is not None:
            continue
        tmpl = at.get("ground_template")
        if not isinstance(tmpl, (str, bytes)):
            continue
        try:
            t = json.loads(_text(tmpl))
        except Exception:
            continue
        term = t.get("term") if isinstance(t, dict) else None
        is_code_write = isinstance(t, dict) and t.get("mode") == "code_write"
        is_fold = (is_code_write and isinstance(term, dict)
                   and term.get("type") == "Fold"
                   and isinstance(term.get("init"), dict)
                   and term["init"].get("type") == "Lit")
        sub.set_attr(n, "tmpl_fold", 1.0 if is_fold else 0.0)
        source = term.get("source") if (is_fold and isinstance(term, dict)) \
            else None
        is_scalar_fold = bool(is_fold and isinstance(source, dict)
                              and source.get("type") != "Var")
        sub.set_attr(n, "tmpl_scalar_fold", 1.0 if is_scalar_fold else 0.0)
        is_branch = bool(is_code_write and isinstance(term, dict)
                         and term.get("type") == "IfThenElse")
        sub.set_attr(n, "tmpl_branch", 1.0 if is_branch else 0.0)


def ensure_construction_bigrams(sub, artifact: str = _BIGRAM_ARTIFACT) -> int:
    """Board the P3 transition statistics onto the agent substrate
    (P3 residual 4, consumed here): ConstructionBigram{prev, next, count,
    prev_total, trans_logp, grain:'head'} nodes at statement-HEAD grain.
    The quantum-name → head projection reads the artifact codebook's own
    signature[0][1] (mechanical); counts are summed per head pair and add-1
    smoothing is recomputed with the SAME formula the scan registered
    (ln((c+1)/(prev_total+|V|))). Returns the number of boarded rows."""
    if _has_seed(sub, _BIGRAM_SEED_ID):
        return 0
    with open(artifact) as f:
        art = json.load(f)
    head_of = {row["name"]: row["signature"][0][1] for row in art["codebook"]}

    def head(label: str) -> str:
        if label in _BOUNDARY:
            return label
        return head_of.get(label, label)

    counts: Dict[tuple, int] = {}
    prev_tot: Dict[str, int] = {}
    for r in art["bigrams"]:
        k = (head(r["prev"]), head(r["next"]))
        counts[k] = counts.get(k, 0) + int(r["count"])
        prev_tot[k[0]] = prev_tot.get(k[0], 0) + int(r["count"])
    vocab = {n for (_, n) in counts} | {p for (p, _) in counts if p != "<s>"}
    v = len(vocab)
    boarded = 0
    for (p, nx), c in counts.items():
        sub.add_node("ConstructionBigram", {
            "prev": p, "next": nx, "count": int(c),
            "prev_total": int(prev_tot[p]),
            "trans_logp": math.log((c + 1) / (prev_tot[p] + v)),
            "grain": "head",
            "vocab_size": int(v),
            "source": os.path.basename(artifact),
        })
        boarded += 1
    sub.add_node("Seed", {"id": _BIGRAM_SEED_ID, "version": "1.0.0"})
    return boarded


def _bigram_tables(sub) -> tuple:
    """Mechanical read-back of the boarded bigram rows into lookup maps
    (a performance cache; the substrate stays the source of truth)."""
    logp: Dict[tuple, float] = {}
    prev_tot: Dict[str, int] = {}
    v = 0
    for n in sub.nodes("ConstructionBigram"):
        at = sub.node(n)["attrs"]
        logp[(at["prev"], at["next"])] = float(at["trans_logp"])
        prev_tot[at["prev"]] = int(at["prev_total"])
        v = int(at.get("vocab_size") or v)
    return logp, prev_tot, max(v, 1)


def _trans_logp(tables, prev: str, nxt: str) -> float:
    """The P3-registered smoothing formula for unseen pairs: prev_total is
    carried per row exactly so a consumer can score them —
    ln(1/(prev_total+|V|)); a never-seen prev scores ln(1/|V|).
    A fixed formula (the ink `emit = -d*dur` class), not a decision."""
    logp, prev_tot, v = tables
    if (prev, nxt) in logp:
        return logp[(prev, nxt)]
    return math.log(1.0 / (prev_tot.get(prev, 0) + v))


# --------------------------------------------------------------------------- #
#  ingest — NL request + example rows → Message/ExampleRow nodes.
# --------------------------------------------------------------------------- #
def _spec_name_from_text(text: str) -> str:
    """Fixed positional extraction: the token after the first function-noun
    cue word ('function'/'method'/...), skipping 'called'/'named'. An
    I/O-boundary parse (the smallest graph token for 'what is it to be
    named'), never a decision over graph state."""
    toks = [w.strip(cw._STRIP) for w in text.split()]
    lows = [t.lower() for t in toks]
    for i, t in enumerate(lows):
        if t in cw._FUNCTION_NOUNS:
            j = i + 1
            while j < len(toks) and lows[j] in ("called", "named"):
                j += 1
            if j < len(toks) and toks[j]:
                return toks[j]
    return "generated_function"


def _surface_tokens(text: str) -> List[str]:
    """Lossless word-grain boundary tokens used by graph-held lexemes.

    Unlike ``_content_tokens`` this does not discard words such as ``two``:
    stop-word removal is useful for construction retrieval but would erase a
    requested quantity before the graph could ground it.
    """
    out: List[str] = []
    for raw in text.split():
        token = raw.strip(cw._STRIP).upper()
        if token and token not in out:
            out.append(token)
    return out


def _literal_integer_quantities(text: str) -> List[tuple[str, int]]:
    """Mechanical integer-literal parse at the text/graph boundary."""
    found: List[tuple[str, int]] = []
    for token in _surface_tokens(text):
        try:
            value = int(token, 10)
        except ValueError:
            continue
        if str(value) == token or (token.startswith("+") and
                                   str(value) == token[1:]):
            found.append((token, value))
    return found


def _numeric_scalar(v) -> bool:
    """Numeric, non-bool scalar (`bool` is an `int` subclass in Python —
    excluded explicitly, the same guard `mbpp_spec`'s own row typing
    relies on elsewhere)."""
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _examples_numeric_eligible(examples) -> bool:
    """Arc5 exact-first rung eligibility: EVERY example's expected value is
    a FLOAT (not merely numeric — see below) and every input is a numeric
    scalar, with a (consistent) arity within 1..3 — the `ExactFamily`
    schema's own declared bound (seeds/exact_families.json, `min_arity`/
    `max_arity` across both held families). Mechanical translation of the
    raw `examples` argument (exactly as `ingest_spec` receives it — the
    SAME two accepted shapes, `(inputs, expected)` or the Q2 `mbpp_spec`
    dict), never a graph-state decision; the rule (`ps_exact_mark`) is
    what decides whether to act on the recorded fact.

    FLOAT-typed, not merely numeric: PROGRAM_SYNTHESIS_ARC5_SPECS_IMPLY_
    FLOATS.md's own finding is that this method's whole domain is specs
    WRITTEN to imply a float (a decimal literal or a `math.isclose`
    tolerance) — every task this rung recovers (82/85/139/233/276/312/
    606/742/574) has a float-valued assert. Gating on "numeric" alone
    would ALSO admit the many int-valued single/few-row fixtures used
    throughout the existing suite to exercise decoy/screen/isolation/
    repair mechanics (e.g. a lone `{"a": 5} -> 5` row) — an int-valued
    identity relation is trivially inside `scaled_power_product`'s own
    grid (`k=1, exps=(1,)`) and would silently reroute those fixtures
    through this rung before they ever reach the rungs (enumerate/
    descend) those tests pin by name, in files this phase does not own.
    Restricting to float-typed expected values is the narrowest gate that
    covers every measured target and touches none of them (verified: no
    fixture in the arc-4 regression sweep passes a float expected value
    through the synthesis pipeline)."""
    examples = list(examples)
    if not examples:
        return False
    arity = None
    for ex in examples:
        if isinstance(ex, dict):
            inputs, expected = ex["inputs"], ex["expected"]
        else:
            inputs, expected = ex
        if not isinstance(expected, float):
            return False
        if not all(_numeric_scalar(v) for v in inputs.values()):
            return False
        n = len(inputs)
        if arity is None:
            arity = n
        elif n != arity:
            return False
    return arity is not None and 1 <= arity <= 3


def ingest_spec(sub, ag_node, text: str, examples=(), *,
                name: Optional[str] = None,
                quantities: Optional[Dict[str, int]] = None):
    """Mechanical ingest: one Message carrying the request facts + one
    ExampleRow per example. The write-request verdict is the EXISTING cue
    machinery (`looks_like_write_request` over the held cue Concepts),
    recorded as a datum. Returns the Message node.

    Arc2-Q4: each item of `examples` is EITHER the original `(inputs,
    expected)` 2-tuple (byte-unchanged) OR a Q2 `mbpp_spec`-shaped dict
    (`{"inputs", "expected", ["tol"], ["unordered"]}` — `domains/
    mbpp_spec.py`'s own row schema) — a MECHANICAL shape dispatch on the
    Python type of the item, never a decision over graph state."""
    tokens = cw._content_tokens(text, sub)
    m = sub.add_node("Message", {
        "text": text,
        "ps_write_request": 1.0 if cw.looks_like_write_request(text, sub) else 0.0,
        "ps_spec_name": name if name else _spec_name_from_text(text),
        "ps_tokens": tokens,
        "ps_surface_tokens": _surface_tokens(text),
        "ps_skeleton": [[t] for t in tokens],
        # P7-A: a top-level request is depth 0 (in-frame integer); descent
        # sub-specs carry their Hole's depth (spawn_subgoal).
        "ps_depth": 0.0,
        # Arc5 exact-first rung: a mechanical eligibility DATUM (numeric
        # inputs, numeric output, arity within the held ExactFamily
        # schema, 1..3) computed once off the raw `examples` argument —
        # exactly the `_examples_numeric_eligible` I/O-boundary check, the
        # same class as `ps_write_request` above. The RULE (ps_exact_mark)
        # reads this fact; it decides nothing here.
        "ps_exact_eligible": 1.0 if _examples_numeric_eligible(examples) else 0.0,
        # Arc5 MOVE A/B rung (PROGRAM_SYNTHESIS_ARC5_MOVES.md): a mechanical
        # eligibility DATUM (domains.prog_moves.moves_eligible -- numeric/
        # integer type-level pre-filter for orbit augmentation OR
        # intermediate decomposition) computed once off the raw `examples`
        # argument, the SAME idiom as `ps_exact_eligible` above. The RULE
        # (ps_move_mark) decides whether to act on it.
        "ps_moves_eligible": 1.0 if pmv.moves_eligible(examples) else 0.0,
    })
    sub.add_edge_unchecked(ag_node, "received", m)
    literal_quantities = _literal_integer_quantities(text)
    literal_names = {token for token, _value in literal_quantities}
    supplied_quantities = list(literal_quantities)
    if quantities:
        supplied_quantities.extend(quantities.items())
    for quantity_name, quantity_value in supplied_quantities:
        if isinstance(quantity_value, bool) or not isinstance(
                quantity_value, int):
            raise TypeError("synthesis quantities must be integers")
        q = sub.add_node("SynthesisQuantity", {
            "name": str(quantity_name),
            "value": quantity_value,
            "source": (
                "request_literal"
                if str(quantity_name) in literal_names
                else "supplied_graph_quantity"
            ),
        })
        sub.add_edge_unchecked(m, "ps_grounds_quantity", q)
    for ex in examples:
        if isinstance(ex, dict):
            inputs, expected = ex["inputs"], ex["expected"]
            tol, unordered = ex.get("tol"), bool(ex.get("unordered"))
        else:
            inputs, expected = ex
            tol, unordered = None, False
        sub.add_edge_unchecked(
            m, "has_example",
            _add_example_row(sub, inputs, expected, tol=tol,
                             unordered=unordered))
    return m


def _add_example_row(sub, inputs, expected, *, tol=None, unordered=False):
    """One ExampleRow node (shared with spawn_subgoal). `has_list_input` is
    a MECHANICAL fact of the row's own JSON (does any input value carry a
    list?) — the descent rules' scope guard reads it; recording the datum
    is I/O-boundary translation, the decision is the rule's.

    Arc2-Q4 row-verdict widening: `tol`/`unordered` are Q2's `mbpp_spec`
    row-schema flags, carried through as `row_tol`/`row_tol_active`/
    `row_unordered` facts — `eval_and_record` computes the fixed-formula
    comparison (`cmp_ok`) those flags select, and `ps_row_pass_special`/
    `ps_row_fail_special` read it; the ORIGINAL `ps_row_pass`/`ps_row_fail`
    scope themselves OFF these rows (byte-unchanged for every plain row,
    where neither flag is ever set)."""
    attrs: Dict[str, Any] = {
        # Rung 2 (PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_RUNG2_RUNG3_
        # PREREG.md): `_wire` the row's INPUT record before it crosses the
        # JSON round-trip, symmetric to the already-shipped output-side
        # `_wire` — JSON has one array type, so an un-wired tuple ARGUMENT
        # (e.g. task 106's `add_lists([5,6,7], (9,10))`) would arrive at
        # every `inputs_json` reader already flattened to a list. Every
        # reader is updated to `_unwire` in the same rung.
        "inputs_json": json.dumps(_wire(inputs), sort_keys=True),
        "expected": expected,
        "has_list_input": 1.0 if any(isinstance(v, (list, tuple))
                                     for v in inputs.values()) else 0.0,
        # -1 sentinels: no evaluation has happened yet (attempt numbers
        # start at 0 on the enumerate rung, 1 on the codebook rung).
        "eval_attempt": -1.0,
        "verdict_attempt": -1.0,
        "eval_ok": 0.0,
    }
    if tol is not None:
        attrs["row_tol"] = float(tol)
        attrs["row_tol_active"] = 1.0
    if unordered:
        attrs["row_unordered"] = 1.0
    return sub.add_node("ExampleRow", attrs)


# --------------------------------------------------------------------------- #
#  template read-back (mechanical lookup of the rule-chosen construction).
# --------------------------------------------------------------------------- #
def _template_by_name(sub, name: Optional[str]) -> Dict[str, Any]:
    """Mechanical template lookup by construction name."""
    for n in sub.nodes("ShapeSignature"):
        at = sub.node(n)["attrs"]
        if at.get("kind") == "code_write_construction" and \
                _text(at.get("name")) == name:
            tmpl = at.get("ground_template")
            if tmpl:
                try:
                    return json.loads(_text(tmpl))
                except Exception:
                    return {}
    return {}


def _chosen_template(sub, g) -> Dict[str, Any]:
    return _template_by_name(
        sub, _text(sub.node(g)["attrs"].get("ps_construction")))


def _part_label(stmt: Dict[str, Any]) -> str:
    """A template part's construction label = its statement-signature HEAD
    (the P3 extraction walk, reused — pis.statement_signature)."""
    return str(pis.statement_signature(stmt)[0][1])


# --------------------------------------------------------------------------- #
#  stamp_lattice — the ordering lattice (ink_decode precedent, verbatim
#  structure) on a FRESH throwaway substrate; vit rules decide the path.
# --------------------------------------------------------------------------- #
def stamp_lattice(sub, ag_node, g) -> bool:
    at = sub.node(g)["attrs"]
    attempts = float(at.get("ps_attempts") or 0.0)
    if float(at.get("ps_spine_attempt") or -1.0) == attempts:
        return False
    template = _chosen_template(sub, g)
    parts = [dict(p) for p in template.get("stmts") or []]
    labels = [_part_label(p) for p in parts]
    tables = _bigram_tables(sub)
    decoded = _decode_order(labels, tables)
    sub.set_attr(g, "ps_spine_labels", decoded)
    sub.set_attr(g, "ps_spine_ok",
                 1.0 if sorted(decoded) == sorted(labels) else 0.0)
    sub.set_attr(g, "ps_spine_attempt", attempts)
    return True


def _decode_order(labels: List[str], tables, *, keep_substrate: bool = False):
    """Hyp/LatEdge ordering lattice over the part labels, decoded by the
    UNCHANGED vit_step/vit_backtrace seed rules (viterbi_decode.json) on a
    throwaway substrate — `ink_decode._lattice_partition`, at statement
    grain. Position 1..L hyps per label; <s> folds into position-1 emission;
    a terminal END hyp carries the label→</s> transitions; edges connect
    DIFFERENT labels only (each part is to be used once). All stamping is
    mechanical; the path is the graph rules' decision. `keep_substrate`
    (gates only) returns (labels, substrate) so the lattice evidence
    (Hyp/LatEdge/on_path) is inspectable."""
    uniq: List[str] = []
    for lb in labels:
        if lb not in uniq:
            uniq.append(lb)
    n = len(labels)
    if n <= 1:
        return (list(labels), None) if keep_substrate else list(labels)
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    s._inner.load_seed_manifest(manifest_for("viterbi_decode"), ag)
    lat = s.add_node("Lattice", {})
    s.set_attr(lat, "lm_weight", 1.0)
    hyps: Dict[tuple, int] = {}
    for p in range(1, n + 1):
        for lb in uniq:
            h = s.add_node("Hyp", {})
            s.set_attr(h, "pos", float(p))
            s.set_attr(h, "emission",
                       _trans_logp(tables, "<s>", lb) if p == 1 else 0.0)
            for k in ("scored", "vscore", "best_in", "on_path"):
                s.set_attr(h, k, 0.0)
            s.add_edge_unchecked(h, "in_lattice", lat)
            hyps[(p, lb)] = h
    end = s.add_node("Hyp", {})
    s.set_attr(end, "pos", float(n + 1))
    s.set_attr(end, "emission", 0.0)
    for k in ("scored", "vscore", "best_in", "on_path"):
        s.set_attr(end, k, 0.0)
    s.add_edge_unchecked(end, "in_lattice", lat)
    for p in range(2, n + 1):
        for a in uniq:
            for b in uniq:
                if a == b:
                    continue
                ed = s.add_node("LatEdge", {})
                s.set_attr(ed, "trans_logp", _trans_logp(tables, a, b))
                s.add_edge_unchecked(ed, "src", hyps[(p - 1, a)])
                s.add_edge_unchecked(ed, "dst", hyps[(p, b)])
    for a in uniq:
        ed = s.add_node("LatEdge", {})
        s.set_attr(ed, "trans_logp", _trans_logp(tables, a, "</s>"))
        s.add_edge_unchecked(ed, "src", hyps[(n, a)])
        s.add_edge_unchecked(ed, "dst", end)
    for p in range(0, n + 2):                       # FORWARD tick
        s.set_attr(lat, "active_pos", float(p))
        s._inner.run_rules(400000)
    s.set_attr(end, "on_path", 1.0)                 # seed the backtrace
    s._inner.run_rules(400000)                      # BACKTRACE (graph-native)
    seq = [(p, lb) for (p, lb), h in hyps.items()
           if s.node(h)["attrs"].get("on_path") == 1.0]
    seq.sort(key=lambda x: x[0])                    # position read-back order
    decoded = [lb for _, lb in seq]
    if keep_substrate:
        return decoded, s
    return decoded


# --------------------------------------------------------------------------- #
#  splice_binding — rule-chosen template → concrete hub IR (mechanical).
# --------------------------------------------------------------------------- #
def _is_scalar_fold(term) -> bool:
    """Structural test (Arc2-Q4): a Fold whose `source` is a COMPUTED
    extern call (a range()-class scalar accumulation), not a Var-bound
    list. Mirrors `_normalise_fold_marks`'s tmpl_scalar_fold stamp, at
    the Term-dict grain rather than the boarded-attr grain (used at
    splice time, before any attr lookup makes sense)."""
    return (isinstance(term, dict) and term.get("type") == "Fold"
            and isinstance(term.get("source"), dict)
            and term["source"].get("type") != "Var")


def _lower_scalar_fold_stmts(term, *, final):
    """LOWER a computed-source Fold into an EXECUTABLE Prog-IR statement
    triple (Arc2-Q4): confirmed empirically that ProgEval's real executor
    cannot run a bare Fold expression whose `source` is a Prog* node
    (`expr:unsupported_over_prog` — Fold's `source` is evaluated by the
    plain DSL evaluator, which leaves Prog* nodes INERT by contract; a
    `ProgForEach` STATEMENT's `iter`, by contrast, IS evaluated Prog-aware
    — exactly `sum_of_list_spine`'s own working shape, just with a
    computed `iter` instead of a Var-bound one). A FIXED, general
    structural transformation — the write-side twin of `code_writing.
    _term_to_statements`'s OWN 'a Fold becomes an init line + a for-loop'
    rule, reproduced here at Prog-IR JSON grain (that function renders
    Python TEXT for a human reader, not an executable IR). `final` is
    either `{"kind": "return"}` (the whole-goal / fold_step splice sites)
    or `{"kind": "assign", "name": "vK"}` (final_expr's live-var
    assignment site — the accumulator's OWN name is reused as-is since
    every current scalar-fold construction is the SOLE cover of its own
    plan; combining two scalar-fold covers in one final_expr plan would
    need var-renaming, a named residual, not yet exercised)."""
    acc = term.get("acc_name") or "acc"
    var = term.get("var_name") or "x"
    stmts = [
        {"type": "ProgAssignVar", "name": acc, "value": term.get("init")},
        {"type": "ProgForEach", "var": var, "iter": term.get("source"),
         "body": {"type": "ProgAssignVar", "name": acc,
                  "value": term.get("body")},
         "orelse": None},
    ]
    if final["kind"] == "return":
        stmts.append({"type": "ProgReturn", "value": {"type": "Var", "name": acc}})
    else:
        stmts.append({"type": "ProgAssignVar", "name": final["name"],
                      "value": {"type": "Var", "name": acc}})
    return stmts


def splice_binding(sub, ag_node, g) -> bool:
    at = sub.node(g)["attrs"]
    attempts = float(at.get("ps_attempts") or 0.0)
    if float(at.get("ps_ir_built") or -1.0) == attempts:
        return False
    template = _chosen_template(sub, g)
    args = [str(a) for a in template.get("args") or []]
    stmts: List[Dict[str, Any]] = [
        {"type": "ProgDefFnParam", "name": a, "default": None} for a in args]
    if template.get("mode") == "code_write_stmts":
        parts = [dict(p) for p in template.get("stmts") or []]
        pool = [(_part_label(p), p) for p in parts]
        order = [_text(x) for x in (_plain(at.get("ps_spine_labels")) or [])]
        for lb in order:
            for i, (plb, p) in enumerate(pool):
                if plb == lb:
                    stmts.append(p)
                    pool.pop(i)
                    break
    else:
        term = template.get("term")
        if term is not None:
            if _is_scalar_fold(term):
                stmts.extend(_lower_scalar_fold_stmts(term, final={"kind": "return"}))
            else:
                stmts.append({"type": "ProgReturn", "value": term})
    ir = {"type": "ProgSeq", "stmts": stmts}
    sub.set_attr(g, "ps_ir", json.dumps(ir))
    sub.set_attr(g, "ps_ir_built", attempts)
    return True


# --------------------------------------------------------------------------- #
#  eval_and_record — reflect + ProgEval over the reflected subgraph; facts
#  only (the verdict rules decide).
# --------------------------------------------------------------------------- #
def _prog_eval_term(env_var: str, prog_var: str) -> Dict[str, Any]:
    oracle_items: List[Dict[str, Any]] = []
    for name in sorted(NATIVE_ORACLES):
        oracle_items.append({"type": "Lit", "value": name})
        oracle_items.append({"type": "Lit", "value": "builtin"})
    return {"type": "ProgEval",
            "prog": {"type": "Var", "name": prog_var},
            "env": {"type": "Var", "name": env_var},
            "oracles": {"type": "MkDict", "items": oracle_items},
            "fuel": _FUEL, "field": ""}


def eval_and_record(sub, ag_node, g) -> bool:
    at = sub.node(g)["attrs"]
    attempts = float(at.get("ps_attempts") or 0.0)
    if float(at.get("ps_eval_done") or -1.0) == attempts:
        return False
    ir = json.loads(_text(at.get("ps_ir")))
    # 1) REFLECT + round-trip fact (the structural verdict datum): IR →
    #    subgraph → canonical JSON → subgraph → canonical JSON, byte-stable.
    root = sub._inner.add_term_subgraph(ir)
    back = sub._inner.term_subgraph_json(root)
    root2 = sub._inner.add_term_subgraph(json.loads(back))
    reflect_ok = 1.0 if sub._inner.term_subgraph_json(root2) == back else 0.0
    sub.remove_node(root2)
    sub.set_attr(g, "ps_reflect_ok", reflect_ok)
    sub.add_edge_unchecked(g, "ps_ir_reflected", root)
    # 2) ProgEval over the REFLECTED subgraph per example row — the executed
    #    artifact IS the graph-resident form.
    msg = None
    for n in sub.neighbours(g, "about_message"):
        msg = n
    rows = sub.neighbours(msg, "has_example") if msg is not None else []
    term = _prog_eval_term("e", "p")
    for r in rows:
        rat = sub.node(r)["attrs"]
        env = _unwire(json.loads(_text(rat.get("inputs_json")) or "{}"))
        out = sub._inner.evaluate(term, {"e": env, "p": root})
        got = out.get("result")
        ok = 1.0 if (out.get("halted") is True and out.get("trap") is None) \
            else 0.0
        sub.set_attr(r, "eval_ok", ok)
        # ARC6 value layer: the non-scalar cast is GONE. `got` is now
        # stored as-is, carrying its container type (list vs tuple), so
        # `ps_row_pass`'s own `Eq(got, expected)` is a type-faithful
        # comparison. The RULE is byte-unchanged; only this mechanical
        # record stopped discarding what the rule needs to decide on.
        sub.set_attr(r, "got", got)
        sub.set_attr(r, "got_json", json.dumps(_plain(got)))
        sub.set_attr(r, "trap", _text(out.get("trap")) or "")
        sub.set_attr(r, "eval_attempt", attempts)
        # Arc2-Q4 row-verdict widening: a fixed-formula comparison fact
        # (the ink ps_spine_ok class) computed off the RAW `got` (before
        # the _SCALARS cast above discards non-scalar shapes) so an
        # `unordered` row's list/set-shaped result is still comparable.
        # ps_row_pass/ps_row_fail never read this attr (plain rows); only
        # ps_row_pass_special/ps_row_fail_special do.
        sub.set_attr(r, "cmp_ok", _row_cmp_ok(
            got, rat.get("expected"), rat.get("row_tol"),
            rat.get("row_unordered") == 1.0))
    sub.set_attr(g, "ps_eval_done", attempts)
    return True


def _wire(v):
    """TYPE-FAITHFUL WIRE ENCODING of a spec value for the `Lit` boundary.
    Mechanical translation; no decision.

    `Substrate.evaluate()` serialises its Term dict with `json.dumps`, and
    JSON has ONE array type — so a Python `tuple` and a Python `list`
    arrive at `persist::decode_value` indistinguishable, and a BARE array
    decodes as `Value::Tuple`. That was harmless while list and tuple were
    one `Value::Tuple`. Under the ARC6 value layer it silently retypes
    every list-valued expected output as a TUPLE, and `SynthEnumerate`
    then rejects the correct list-producing candidate it just built —
    measured: 161/272/413/436/450/460 all evaluate to the exactly-correct
    LIST and were still reported `enumerate_failed`.

    WIRE_BOUNDARY_SYSTEMIC_AUDIT (2026-08): this function used to be a
    hand-rolled hand-authored hand-tagged (`__tuple__`/`__list__`/
    `__fset__`/`__set__`/`__dict__`) re-derivation of the engine's own
    ALREADY-COMPLETE, ALREADY-EXPOSED codec — three separate coverage
    gaps (frozenset, Fraction, non-string dict keys) were found and
    patched into this hand-rolled copy across three separate rungs
    (PROGRAM_SYNTHESIS_SETLIT_DICTITEMS_RESULTS.md,
    PROGRAM_SYNTHESIS_CEILING_REASSESSMENT_3_RESULTS.md,
    PROGRAM_SYNTHESIS_GROUPCOUNT_DICTMERGE_RESULTS.md), each patch
    correct in isolation and each one re-deriving a strict subset of a
    tag scheme `runners/dsl/src/persist.rs::encode_value` already
    implements COMPLETELY over the engine's own `Value` enum (all 13
    variants, including `Rational`/`Node`/`Surface` this hand-rolled copy
    never covered at all) and already exposes to Python, unused, as
    `substrate_rs.encode`/`substrate_rs.decode` (`py.rs`'s `encode`/
    `decode` `#[pyfunction]`s, wrapping the exact same `py_to_value` /
    `encode_value` chain `set_attr`/`node()`/`evaluate()` already use for
    every OTHER attr on this graph). Per CLAUDE.md's Rust-primitive-reuse
    rule ("Never 'primitive in Python'"), `_wire` now delegates to that
    primitive instead of re-deriving a fourth, narrower copy of it. The
    function NAME and call sites are kept byte-unchanged (call-site
    compatibility, `test_arc6_lit_wire_migrated.py`'s own
    `callable(getattr(prog_synthesis, "_wire", None))` pin); the tag
    vocabulary emitted is IDENTICAL to the hand-rolled version's (same
    `persist.rs` tag family), so every already-stored `inputs_json`
    string decodes unchanged under the new `_unwire`.
    WIRE_BOUNDARY_SYSTEMIC_AUDIT_RESULTS.md documents the audit.
    """
    return srs.encode(v)


def _unwire(v):
    """Inverse of `_wire` — recovers a native Python tuple/list/set/
    frozenset/Fraction/dict-with-any-key from a wire-tagged JSON value.
    Mechanical translation; no decision.

    WIRE_BOUNDARY_SYSTEMIC_AUDIT (2026-08): delegates to
    `substrate_rs.decode` (see `_wire`'s docstring) instead of a
    hand-rolled tag match — same tag vocabulary, so already-stored
    `inputs_json` strings decode identically.
    """
    return srs.decode(v)


def _wire_rows(rows):
    """`_wire` every value inside a SynthEnumerate example row, leaving the
    row list and the row dicts as plain JSON."""
    out = []
    for r in rows:
        row = dict(r)
        if isinstance(row.get("inputs"), dict):
            row["inputs"] = {k: _wire(v) for k, v in row["inputs"].items()}
        for k in ("output", "expected"):
            if k in row:
                row[k] = _wire(row[k])
        out.append(row)
    return out


def _row_cmp_ok(got, expected, tol, unordered) -> float:
    """Fixed-formula row comparator consuming Q2's `mbpp_spec` row schema:
    `unordered` -> SET equality (order- and duplicate-insensitive, the
    documented `set(...) == set(...)` semantics `mbpp_spec.py` names —
    never multiset/bag equality); `tol` -> float-within-tolerance; neither
    -> plain equality (the ORIGINAL ps_row_pass/ps_row_fail semantics,
    reproduced here only as an extra, unused-by-them fact for plain
    rows — those two rules keep their own direct Eq check, untouched).

    2026-08-01 (Arc5 exact-first): `tol` is `mbpp_spec.py`'s own field,
    documented there as `math.isclose`'s `rel_tol` value (item 1 of that
    module's docstring). This comparator used to read it as an ABSOLUTE
    bound (`abs(got-expected)<=tol`) — harmless for the small-magnitude
    rows it was exercised on before, but WRONG for the corpus's own
    geometry family (task 139 etc.): those asserts carry the reference
    solution's hand-truncated `3.1415`, so a textbook-exact answer using
    real `math.pi` diverges from the literal by more than 0.001 in
    ABSOLUTE terms at scale, while the RELATIVE error (~3e-5, the
    precision gap between 3.1415 and pi) stays far inside the assert's
    OWN declared `rel_tol=0.001` — exactly what the assert says it means.
    Fixed to real `math.isclose` semantics; both existing pins
    (`_row_cmp_ok(3.0, 3.001, 0.01, False) == 1.0`,
    `_row_cmp_ok(3.0, 3.5, 0.01, False) == 0.0`) hold unchanged under
    either reading (verified) — this closes a latent absolute/relative
    mismatch, it does not touch the verdict RULES."""
    if unordered:
        try:
            a = frozenset(got) if isinstance(got, (list, tuple, set, frozenset)) \
                else frozenset([got])
            b = frozenset(expected) if isinstance(expected, (list, tuple, set, frozenset)) \
                else frozenset([expected])
        except TypeError:
            return 0.0
        return 1.0 if a == b else 0.0
    if tol is not None:
        try:
            return 1.0 if math.isclose(float(got), float(expected),
                                       rel_tol=float(tol), abs_tol=1e-9) else 0.0
        except (TypeError, ValueError):
            return 0.0
    return 1.0 if got == expected else 0.0


# --------------------------------------------------------------------------- #
#  screen_construction — Arc3-R2.5: the SCOPED codebook-side half of the
#  universal execution screen (PROGRAM_SYNTHESIS_ARC3_R12_NOTES.md's
#  Attempt-1 revert, redone correctly). ps_screen_mark (seed v1.5.1) only
#  ever marks a goal for screening when it is NOT DESCEND_APPLICABLE (the
#  SAME 3-part predicate ps_descend_mark/ps_enumerate_mark already embed) —
#  so this verb is NEVER asked to judge a construction descent might
#  legitimately need as a partial cover; every candidate it sees is,
#  by that scoping, a candidate that can ONLY ever be used as a
#  COMPLETE, stand-alone program for this goal. It dry-runs the SAME
#  template->IR logic `splice_binding` uses (reflect + ProgEval on the
#  goal's own REVEALED rows), touching NO real goal attrs (`ps_ir`,
#  `ps_attempts`, `ps_ir_built`) and spending NO `ps_attempts` — a wrong
#  complete candidate is excluded for FREE, before ps_propose ever gets to
#  spend a real attempt on it (the decoy-tax kill); a right one is marked
#  screen-passed so ps_propose's own (now-widened) eligibility gate can
#  pick it up next round and spend EXACTLY one real, now-guaranteed-good
#  attempt on it.
# --------------------------------------------------------------------------- #
def _build_candidate_ir(sub, template: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Mechanical dry-run mirror of `splice_binding`'s OWN template->IR
    logic (byte-identical structural rules, reused rather than
    re-invented), EXCEPT it never touches any goal attr — the statement
    order for a multi-part template is recomputed directly via the SAME
    pure `_decode_order` function `stamp_lattice` calls (same labels, same
    boarded bigram tables => the SAME deterministic order stamp_lattice
    would later record for the identical construction), so a screen-passed
    verdict is guaranteed to match what the REAL propose->lattice->bind
    chain will build. Returns None for an unrecognised/empty template (the
    Argmax always names a real ShapeSignature, so this is a defensive-only
    branch, never exercised on a live pick)."""
    if not template:
        return None
    args = [str(a) for a in template.get("args") or []]
    stmts: List[Dict[str, Any]] = [
        {"type": "ProgDefFnParam", "name": a, "default": None} for a in args]
    if template.get("mode") == "code_write_stmts":
        parts = [dict(p) for p in template.get("stmts") or []]
        labels = [_part_label(p) for p in parts]
        tables = _bigram_tables(sub)
        order = _decode_order(labels, tables)
        pool = [(_part_label(p), p) for p in parts]
        for lb in order:
            for i, (plb, p) in enumerate(pool):
                if plb == lb:
                    stmts.append(p)
                    pool.pop(i)
                    break
    else:
        term = template.get("term")
        if term is None:
            return None
        if _is_scalar_fold(term):
            stmts.extend(_lower_scalar_fold_stmts(term, final={"kind": "return"}))
        else:
            stmts.append({"type": "ProgReturn", "value": term})
    return {"type": "ProgSeq", "stmts": stmts}


def _screen_eval(sub, ir: Dict[str, Any], env: Dict[str, Any]):
    """The `run_retrieval_ladder._eval_ir` idiom, reproduced here (this
    module owns its own copy rather than reaching into `prog_retrieval`'s
    private helper): reflect a THROWAWAY subgraph, evaluate, remove it —
    no trace left on the real graph, no goal attr touched."""
    root = sub._inner.add_term_subgraph(ir)
    try:
        out = sub._inner.evaluate(_prog_eval_term("e", "p"), {"e": env, "p": root})
    finally:
        sub.remove_node(root)
    got = out.get("result")
    ok = out.get("halted") is True and out.get("trap") is None
    return got, ok


def screen_construction(sub, ag_node, g) -> bool:
    """The `screen_running` verb: dry-run the goal's `ps_screen_candidate`
    against every revealed ExampleRow and record ONE fact,
    `ps_screen_verdict` (1.0 pass / 0.0 fail) — `ps_screen_reject`/
    `ps_screen_admit` decide everything downstream. Mark-once per
    candidate via `ps_screen_name` (the `ps_ir_built`-vs-`ps_attempts`
    idiom, at screen grain instead of attempt grain)."""
    at = sub.node(g)["attrs"]
    name = _text(at.get("ps_screen_candidate"))
    if at.get("ps_screen_name") == name and at.get("ps_screen_verdict") is not None:
        return False
    template = _template_by_name(sub, name)
    ir = _build_candidate_ir(sub, template)
    msg = None
    for n in sub.neighbours(g, "about_message"):
        msg = n
    rows = list(sub.neighbours(msg, "has_example")) if msg is not None else []
    verdict = 1.0 if (ir is not None and rows) else 0.0
    if verdict == 1.0:
        for r in rows:
            rat = sub.node(r)["attrs"]
            env = _unwire(json.loads(_text(rat.get("inputs_json")) or "{}"))
            try:
                got, ok = _screen_eval(sub, ir, env)
                if ok:
                    ok = bool(_row_cmp_ok(got, rat.get("expected"), rat.get("row_tol"),
                                          rat.get("row_unordered") == 1.0))
            except Exception:  # noqa: BLE001 — a screen dry-run never crashes the loop
                ok = False
            if not ok:
                verdict = 0.0
                break
    sub.set_attr(g, "ps_screen_name", name)
    sub.set_attr(g, "ps_screen_verdict", verdict)
    return True


# --------------------------------------------------------------------------- #
#  run_enumerate — the P4-A SynthEnumerate seam (feature-detected).
# --------------------------------------------------------------------------- #
def synth_enumerate_live(sub) -> bool:
    """Tiny evaluate probe for the SynthEnumerate Term (P4-A — LANDED
    mid-flight of this track; absent engines raise UnknownTermType).
    Mechanical capability detection, the `_prog_eval_live` idiom."""
    try:
        sub._inner.evaluate({"type": "SynthEnumerate",
                             "examples": {"type": "Lit", "value": []},
                             "max_size": 1, "max_candidates": 0,
                             "saturate_k": 0, "field": ""}, {})
        return True
    except ValueError as e:
        if "UnknownTermType" in str(e):
            return False
        return True     # present but the probe shape mismatched its schema
    except Exception:
        return True


# --------------------------------------------------------------------------- #
#  Opgrammar slice 1 (OPLIST_ADMISSIBILITY_GRAMMAR_PREREG.md /
#  _RESULTS.md, OPLIST_ADMISSIBILITY_GRAMMAR_SLICE1_RESULTS.md): the
#  op-list boolean gate ladder is Γ-shaped (a real generated multi-
#  production admissible-move SET, CLAUDE.md's own "set of allowed moves"
#  test) — this is the buildable first slice's parity check, `SortBy`
#  only, run ALONGSIDE the existing hand-written Rust ladder, never
#  replacing it. See seeds/program_synthesis_opgrammar.json for the two
#  Γ productions this feeds.
# --------------------------------------------------------------------------- #
_OPGRAMMAR_SEED_ID = "program_synthesis_opgrammar"


def ensure_program_synthesis_opgrammar(sub, native, ag_node) -> None:
    """Idempotent install of the `program_synthesis_opgrammar` seed (the
    `SynthOp` vocabulary + the two hand-authored `SortBy` Γ productions).
    Same `_has_seed` guard idiom `ensure_program_synthesis` already uses
    for every other seed it installs."""
    if not _has_seed(sub, _OPGRAMMAR_SEED_ID):
        summary = native.load_seed_manifest(
            manifest_for(_OPGRAMMAR_SEED_ID), ag_node)
        if summary.get("rules_skipped") or summary.get("reflexes_skipped"):
            raise RuntimeError(
                "program_synthesis_opgrammar did not install cleanly: %r"
                % (summary,))
        sub.add_node("Seed", {"id": _OPGRAMMAR_SEED_ID, "version": "1.0.0"})


# GAMMA_CONSULTATION_FLIP: the candidate ORDER `run_enumerate` supplies to
# `admissible_moves` when consulting Γ for the op-list default (see that
# function's own "Opgrammar consultation" block below). This is a THIRD
# instance of the SAME "own copy, no cross-import, documented tradeoff"
# duplication idiom `_synth_spec_shape_flags` and `_examples_numeric_
# eligible` already use in this file — a 1:1 port of `OP_TABLE`'s live
# declaration order (`synth_enumerate.rs:359-419` as of `main @ de1845d`,
# re-derived by reading the const's body directly, not inherited from any
# prior document's stale count).
#
# GAMMA_CONSULTATION_FLIP_PREREG.md §4 records, with a concrete confirmed
# example (`MapList`/`JoinList` ordered oppositely by `DEFAULT_STR_OPS`
# vs `LIST_EXTRA_OPS`), that NO single static order can reproduce every
# real branch's own internal push order simultaneously — the branches
# that disagree are mutually exclusive per spec, so this is a structural
# property of the ladder, not a bug in this list. `admissible_moves`
# returns admitted candidates in the SAME relative order they are
# supplied (verified against `substrate.rs`), so this order is what
# ultimately reaches `spec["ops"]`. Order-fidelity to the real ladder is
# therefore NOT assumed here; it is verified empirically (the paired MBPP
# battery's exact task-id diff, GAMMA_CONSULTATION_FLIP_RESULTS.md §
# battery).
_GAMMA_OP_CANDIDATE_ORDER: "List[str]" = [
    "Plus", "Times", "Minus", "Div", "Min", "Max", "Abs", "Neg",
    "Gt", "Lt", "Gte", "Lte", "Eq", "And", "Or", "Not", "IfThenElse",
    "Concat", "CaseFold",
    "Len", "SumList", "MaxList", "MinList", "MaxLenOver", "MinLenOver",
    "First", "LastElem", "JoinList", "FilterList", "MapList",
    "TupleOf", "ProdList", "ConcatList", "ArgMaxLenOver",
    "IntersectAll", "UnionAll", "DictFromPairs",
    "Replace", "Str", "Split", "StrCount", "Round", "Reverse",
    "IndexedMap", "Capitalize", "ParseInt", "Slice", "Sort",
    "SetMap", "Intersect", "Union",
    "DictItems", "SortBy", "GroupCount", "DictMerge", "ZipWith",
    "Mod", "Sqrt",
]


def _synth_spec_shape_flags(raw_rows: "List[Dict[str, Any]]") -> "Dict[str, bool]":
    """DUPLICATED EVIDENCE-FLAG COMPUTATION — a Python mirror of the
    evidence flags `eval_synth_enumerate` computes internally in Rust
    (`runners/dsl/src/synth_enumerate.rs`, the `is_listlike` helper
    ~line 473, `items_of` ~line 1012, and the evidence-flag block
    ~lines 1791-1919 as of `main @ c1d0b4c`).

    THIS IS FORK (a) FROM `OPLIST_ADMISSIBILITY_GRAMMAR_RESULTS.md` §7's
    OWN NAMED TRADEOFF TABLE, taken deliberately, not by drift: the Rust
    flag computation is internal to `eval_synth_enumerate` and is not
    exposed via any PyO3 method, so this function is a SECOND,
    independently-maintained copy of the SAME predicates over the SAME
    raw example-row values — never a call into the Rust computation. This
    is a TRACKED DRIFT LIABILITY, the same class of risk `PROGRAM_
    SYNTHESIS_STRUCTURAL_CEILING_REASSESSMENT_PREREG.md`'s own Q1 names
    for `NATIVE_ORACLES`: every other "own copy, no cross-import"
    duplication in this codebase documents itself this way (e.g.
    `_examples_numeric_eligible` above, a different duplication of the
    same discipline). If `eval_synth_enumerate`'s evidence-flag
    predicates ever change, THIS function must be updated to match BY
    HAND — there is no automatic sync. A follow-on rung may close this by
    exposing the Rust computation via a new PyO3 method (fork (b) in the
    same table) — deliberately NOT attempted here (this slice is zero
    `.rs` changes, per its own scope).

    Operates on RAW (pre-`_wire`) Python values — native tuple/list/set/
    frozenset/dict/str/int/float/bool/None, exactly the shape `env`/
    `rat.get("expected")` carry in `run_enumerate` BEFORE `_wire` tags
    them for the JSON `Lit` boundary — so `isinstance` here reads the
    same container kind Rust's own `Value` enum decodes from the wired
    form, without needing the wire round-trip.

    Returns the TWELVE flags `SynthSpecShape` carries as attrs — the
    original ten are a direct 1:1 port of `OPLIST_ADMISSIBILITY_GRAMMAR_
    RESULTS.md` §3.2's flag set: has_dict_value, has_list_of_lists,
    has_string_value, has_float_value, has_repeated_list_element,
    output_is_listlike, output_is_setlike, output_is_bare_int,
    is_string_shaped, is_list_shaped. `output_is_dictlike` was added by
    `PROGRAM_SYNTHESIS_GAMMA_BULK_TRANSCRIPTION_PREREG/RESULTS.md` (a
    direct 1:1 port of `spec_output_is_dictlike`,
    `synth_enumerate.rs:2164`, `outputs.iter().all(is_dict_val)`) — needed
    ONLY so the bare-scalar-fallback `DEFAULT_OPS` Γ production can
    correctly exclude the `DICT_DEFAULT_OPS` branch (inserted into the
    `if`/`else if` chain by the GroupCount/DictMerge rung, after this
    module's original ten flags were written). It does NOT admit any
    `DICT_DEFAULT_OPS`-bucket op (`GroupCount`/`DictMerge`/
    `DictFromPairs` stay out of Γ scope entirely, per that document's
    §1). `has_two_zippable_list_vars` was added by
    `GAMMA_CONSULTATION_FLIP_PREREG/RESULTS.md` — a direct 1:1 port of
    `spec_has_two_zippable_list_vars` (`synth_enumerate.rs:2395-2413`):
    at least two spec variables that are EACH list/tuple/set/frozenset-
    shaped on every row, with some such PAIR having equal length on every
    row. Needed for the new `ZipWith` evidence-gate production — a real
    op-list site that landed in `synth_enumerate.rs` AFTER the bulk
    transcription rung and was found uncovered by that document's own
    14-site table."""
    def is_listlike(v) -> bool:
        return isinstance(v, (tuple, list, set, frozenset))

    def is_dict_val(v) -> bool:
        return isinstance(v, dict)

    def is_str_val(v) -> bool:
        return isinstance(v, str)

    def is_float_val(v) -> bool:
        # Value::Rational has no native Python spec-row equivalent here
        # (a raw example row never carries a fractions.Fraction) — the
        # Rust side's is_float_val also matches Rational, this mirror
        # only sees Float-shaped rows in practice.
        return isinstance(v, float)

    def items_of(v):
        if isinstance(v, (tuple, list, set, frozenset)):
            return list(v)
        return None

    def has_dup(v) -> bool:
        items = items_of(v)
        if not items:
            return False
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                if items[i] == items[j]:
                    return True
        return False

    var_values: Dict[str, List[Any]] = {}
    all_input_values: List[Any] = []
    outputs: List[Any] = []
    for row in raw_rows:
        inputs = row.get("inputs") or {}
        for k, v in inputs.items():
            var_values.setdefault(k, []).append(v)
            all_input_values.append(v)
        outputs.append(row.get("output"))

    def any_nested_all_listlike(values) -> bool:
        for v in values:
            items = items_of(v)
            if items and all(is_listlike(x) for x in items):
                return True
        return False

    is_list_shaped = bool(outputs) and all(is_listlike(v) for v in outputs)
    if not is_list_shaped:
        for name, vals in var_values.items():
            if len(vals) == len(raw_rows) and vals and all(is_listlike(v) for v in vals):
                is_list_shaped = True
                break

    # ZIP_ELEMENTWISE rung's own evidence (`spec_has_two_zippable_list_
    # vars`, synth_enumerate.rs:2395-2413): every var consistently
    # list-shaped on every row is a "zippable" candidate; two DISTINCT
    # such vars with equal length on EVERY row (pairwise) is the genuine
    # two-sequence shape `ZipWith` composes over. A single list-shaped
    # var (e.g. task 88's `a`) never sets this.
    zippable_vars = [
        name for name, vals in var_values.items()
        if len(vals) == len(raw_rows) and vals and all(is_listlike(v) for v in vals)
    ]
    has_two_zippable_list_vars = False
    for i in range(len(zippable_vars)):
        for j in range(i + 1, len(zippable_vars)):
            v1 = var_values[zippable_vars[i]]
            v2 = var_values[zippable_vars[j]]
            lens1 = [len(items_of(v)) for v in v1]
            lens2 = [len(items_of(v)) for v in v2]
            if lens1 == lens2:
                has_two_zippable_list_vars = True
                break
        if has_two_zippable_list_vars:
            break

    return {
        "has_dict_value": any(is_dict_val(v) for v in all_input_values),
        "has_list_of_lists": (any_nested_all_listlike(all_input_values)
                               or any_nested_all_listlike(outputs)),
        "has_string_value": (any(is_str_val(v) for v in all_input_values)
                              or any(is_str_val(v) for v in outputs)),
        "has_float_value": (any(is_float_val(v) for v in all_input_values)
                             or any(is_float_val(v) for v in outputs)),
        "has_repeated_list_element": (any(has_dup(v) for v in all_input_values)
                                       or any(has_dup(v) for v in outputs)),
        "output_is_listlike": bool(outputs) and all(is_listlike(v) for v in outputs),
        "output_is_setlike": bool(outputs) and all(
            isinstance(v, (set, frozenset)) for v in outputs),
        "output_is_bare_int": bool(outputs) and all(
            isinstance(v, int) and not isinstance(v, bool) for v in outputs),
        "output_is_dictlike": bool(outputs) and all(is_dict_val(v) for v in outputs),
        "is_string_shaped": (bool(outputs) and all(is_str_val(v) for v in outputs)
                              and all(is_str_val(v) for v in all_input_values)),
        "is_list_shaped": is_list_shaped,
        "has_two_zippable_list_vars": has_two_zippable_list_vars,
    }


def run_enumerate(sub, ag_node, g) -> bool:
    """The P4-A seam, live: SynthEnumerate{examples, max_size,
    max_candidates, saturate_k, field, exclude} → Dict{found, term
    (Term-JSON STRING), term_str, halt_reason, ...} (the landed contract,
    runners/dsl/src/synth_enumerate.rs). The adapter builds the spec rows
    from the ExampleRows mechanically and records the outcome fact; the
    rules decide everything downstream.

    Arc2-Q4 EXCLUDE-POWERED ITERATION (closing the P7-B 'within-round
    candidate iteration ... contract-blocked' residual at the level P7-B
    could not reach — no Rust in that phase, and Q1 landed the engine's
    `exclude` param): every re-enumeration now passes the Q1 `exclude`
    list — BOTH the hole-scope ExcludedSub terms repair already
    transcribes onto the sub-message (`ps_enum_excluded`, previously used
    ONLY for the coarse const-drop heuristic below, never reaching the
    engine's real exclusion mechanism) AND the top-level round-scope
    ExcludedTerm provenance the NEW ps_enum_retry_mark rule accumulates
    (`g -ps_enum_excluded_term-> ExcludedTerm`). The guard is now
    ROUND-scoped (`ps_enum_outcome_round`), the same 'record which round
    this fact belongs to' idiom every other per-attempt adapter verb
    already uses (`ps_ir_built`/`ps_eval_done` vs `ps_attempts`), so a
    retry genuinely re-runs the search rather than being skipped as
    'already done'."""
    at = sub.node(g)["attrs"]
    round_ = float(at.get("ps_enum_round") or 0.0)
    if at.get("ps_enum_outcome_round") == round_:
        return False
    if not synth_enumerate_live(sub):
        sub.set_attr(g, "ps_enumerate_outcome", "unavailable")
        sub.set_attr(g, "ps_enum_outcome_round", round_)
        return True
    msg = None
    for n in sub.neighbours(g, "about_message"):
        msg = n
    rows = []
    raw_rows: List[Dict[str, Any]] = []
    args: List[str] = []
    for r in (sub.neighbours(msg, "has_example") if msg is not None else []):
        rat = sub.node(r)["attrs"]
        env = _unwire(json.loads(_text(rat.get("inputs_json")) or "{}"))
        for k in env:
            if k not in args:
                args.append(k)
        rows.append({"inputs": {k: _wire(v) for k, v in env.items()},
                     "output": _wire(rat.get("expected"))})
        # Opgrammar slice 1: the SAME rows, kept RAW (pre-`_wire`) so
        # `_synth_spec_shape_flags` can read native container types
        # directly (see that function's own docstring for why).
        raw_rows.append({"inputs": dict(env), "output": rat.get("expected")})
    # GAMMA_CONSULTATION_FLIP (closing residual #41, GAMMA_CONSULTATION_
    # FLIP_PREREG/RESULTS.md): mint a SynthSpecShape node carrying the
    # duplicated evidence flags, then ask Γ (`admissible_moves`, ONE call
    # over every real SynthOp name) which ops it admits for this spec's
    # shape. Superseded is the SLICE1-era single-op `SortBy` parity probe
    # (`is_edge_admissible`) — this now asks Γ for the FULL op set, since
    # that verdict is about to be consulted (below), not merely recorded.
    spec_shape_flags = _synth_spec_shape_flags(raw_rows)
    spec_shape_node = sub.add_node("SynthSpecShape", spec_shape_flags)
    try:
        # `admissible_moves` returns (tgt_TYPE, tgt_attrs, weight) triples
        # — the op NAME lives in `tgt_attrs["name"]`, not the first slot
        # (that slot is always the literal string "SynthOp", the type
        # every candidate was materialised with; verified directly
        # against `substrate.rs::admissible_moves`'s own `for (sym, attrs,
        # w) in moves` construction before writing this).
        admitted = sub._inner.admissible_moves(
            spec_shape_node, "admits_op",
            [("SynthOp", {"name": name}) for name in _GAMMA_OP_CANDIDATE_ORDER])
        gamma_ops = [attrs["name"] for (_typ, attrs, _weight) in admitted]
    except Exception as e:
        gamma_ops = None
        sub.set_attr(g, "ps_enum_gamma_ops_error", str(e)[:200])
    sub.set_attr(g, "ps_enum_gamma_ops_admitted",
                 ",".join(gamma_ops) if gamma_ops is not None else None)
    spec: Dict[str, Any] = {
        "type": "SynthEnumerate",
        "examples": {"type": "Lit", "value": rows},
        "max_size": 20, "max_candidates": 0, "saturate_k": 0,
        "field": ""}
    # The operator inventory is a graph verdict produced by
    # ps_select_synthesis_operator_shape.  This adapter merely transcribes
    # the held list into the existing Term contract.
    graph_ops = _plain(sub.node(msg)["attrs"].get("ps_enum_ops")) \
        if msg is not None else None
    if graph_ops:
        # Explicit op selection (the NL classifier's own verdict) always
        # wins — unchanged, out of this rung's scope.
        spec["ops"] = {
            "type": "Lit",
            "value": [_text(op) for op in graph_ops],
        }
        sub.set_attr(g, "ps_enum_gamma_ops_used", False)
    elif gamma_ops:
        # GAMMA_CONSULTATION_FLIP: Γ's own non-empty verdict is now the
        # SOURCE of the typed-default op list, not merely a recorded fact
        # alongside it. When Γ admits nothing for this spec's shape (the
        # DICT_DEFAULT_OPS branch — GAMMA_CONSULTATION_FLIP_PREREG.md §2
        # point 3, §3.2 — proven empty by exhaustive reading of every
        # production's `where` clause, not assumed), `spec["ops"]` stays
        # unset below and the Rust ladder's own internal default decides,
        # byte-identical to pre-flip behaviour for that branch.
        spec["ops"] = {"type": "Lit", "value": gamma_ops}
        sub.set_attr(g, "ps_enum_gamma_ops_used", True)
    else:
        sub.set_attr(g, "ps_enum_gamma_ops_used", False)
    # P7-B: hole-scope const drops (spawn_subgoal's mechanical transcription
    # of the rule-minted ExcludedSub facts). The passed list mirrors the
    # Term's documented default — (0, 1, 2, -1) — minus the dropped values.
    # HONEST CONTRACT BOUNDARY: the Term APPENDS integer-valued spec outputs
    # to whatever consts are passed (synth_enumerate.rs), so an excluded Lit
    # whose value is a spec output cannot be dropped this way — for those the
    # input shift is the grown row set alone. Arc2-Q4 closes this properly
    # (below): the SAME excluded terms are ALSO passed via `exclude`, which
    # pre-seeds signature-based pruning BEFORE the const-append step, so an
    # output-valued excluded Lit is genuinely pruned regardless.
    drops = _plain(sub.node(msg)["attrs"].get("ps_enum_drop_consts")) \
        if msg is not None else None
    grounded_quantities: List[int] = []
    if msg is not None:
        for quantity in sub.neighbours(msg, "ps_grounds_quantity"):
            value = sub.node(quantity)["attrs"].get("value")
            if isinstance(value, int) and not isinstance(value, bool) and \
                    value not in grounded_quantities:
                grounded_quantities.append(value)
    # A grounded word is evidence, not automatic search authority.  Constants
    # enter enumeration only when the graph also recognized a compatible
    # operator shape; otherwise incidental numbers in ordinary prose would
    # silently widen an unrelated program search.
    active_grounded_quantities = grounded_quantities if graph_ops else []
    if drops or active_grounded_quantities:
        constants: List[int] = []
        for value in (*((0, 1, 2, -1)), *active_grounded_quantities):
            if value not in constants and not any(
                    value == dropped for dropped in (drops or [])):
                constants.append(value)
        spec["consts"] = {"type": "Lit", "value": [
            value for value in constants
        ]}
    exclude_terms: List[str] = []
    excl_msg = _plain(sub.node(msg)["attrs"].get("ps_enum_excluded")) \
        if msg is not None else None
    if excl_msg:
        exclude_terms.extend(_text(x) for x in excl_msg)
    for xt in sub.neighbours(g, "ps_enum_excluded_term"):
        t = _text(sub.node(xt)["attrs"].get("term"))
        if t:
            exclude_terms.append(t)
    if exclude_terms:
        spec["exclude"] = {"type": "Lit", "value": exclude_terms}
    try:
        out = sub._inner.evaluate(spec, {})
    except Exception as e:
        sub.set_attr(g, "ps_enumerate_outcome", "failed")
        sub.set_attr(g, "ps_enumerate_note", str(e)[:200])
        sub.set_attr(g, "ps_enum_outcome_round", round_)
        return True
    if isinstance(out, dict):
        for output_key, fact_key in (
            ("tested", "ps_enum_tested"),
            ("distinct", "ps_enum_distinct"),
            ("size", "ps_enum_solution_size"),
        ):
            value = out.get(output_key)
            if isinstance(value, int) and not isinstance(value, bool):
                sub.set_attr(g, fact_key, value)
    sub.set_attr(g, "ps_enum_operator_shape", _text(
        sub.node(msg)["attrs"].get("ps_enum_operator_shape")
    ) if msg is not None else "")
    sub.set_attr(g, "ps_enum_ops", list(graph_ops or []))
    sub.set_attr(
        g, "ps_enum_grounded_constants", active_grounded_quantities
    )
    found = bool(out.get("found")) if isinstance(out, dict) else False
    term_json = _text(out.get("term")) if isinstance(out, dict) else None
    if not (found and term_json):
        sub.set_attr(g, "ps_enumerate_outcome", "failed")
        sub.set_attr(g, "ps_enumerate_note",
                     _text(out.get("halt_reason")) if isinstance(out, dict)
                     else "no result")
        sub.set_attr(g, "ps_enum_outcome_round", round_)
        return True
    stmts = [{"type": "ProgDefFnParam", "name": a, "default": None}
             for a in sorted(args)]
    stmts.append({"type": "ProgReturn", "value": json.loads(term_json)})
    attempts = float(at.get("ps_attempts") or 0.0)
    sub.set_attr(g, "ps_ir", json.dumps({"type": "ProgSeq", "stmts": stmts}))
    sub.set_attr(g, "ps_ir_built", attempts)
    sub.set_attr(g, "ps_enumerate_note",
                 _text(out.get("term_str")) or "")
    sub.set_attr(g, "ps_enumerate_outcome", "ok")
    sub.set_attr(g, "ps_enum_outcome_round", round_)
    # provenance for a POSSIBLE future retry (ps_enum_retry_mark): the
    # exact candidate this attempt produced, and which attempt it was —
    # ps_exclude_failed/ps_ce_exhausted's added mutual-exclusion guard
    # reads ps_rung_enumerate, not this; this is purely the exclusion seed
    # for the NEXT round, should one be needed.
    sub.set_attr(g, "ps_enum_produced", attempts)
    sub.set_attr(g, "ps_enum_last_term_json", term_json)
    return True


# --------------------------------------------------------------------------- #
#  run_exact_family -- Arc5 EXACT-FIRST rung (PROGRAM_SYNTHESIS_ARC5_
#  EXACT_FIRST.md): shape -> IR, ahead of enumerate. Every DECISION (mark,
#  solved, failed) is a ps_exact_* RULE in seeds/program_synthesis.json;
#  this verb only evaluates `domains.prog_exact`'s bounded search/render
#  and records facts (the `run_enumerate` precedent, verbatim structure).
# --------------------------------------------------------------------------- #
def run_exact_family(sub, ag_node, g) -> bool:
    """Read the goal's revealed ExampleRows, try each held `ExactFamily`
    in Occam order (`prog_exact.all_families_ordered`) via
    `prog_exact.fit_family`, and record ONE outcome fact
    (`ps_exact_outcome` in {'ok','failed'}) plus an honest candidate count
    (`ps_exact_candidates`) — the rules (`ps_exact_solved`/
    `ps_exact_failed`) decide everything downstream. On success this verb
    splices the rendered IR the SAME way `run_enumerate` does (`ps_ir`/
    `ps_ir_built` at the CURRENT attempt number, no increment — a fit
    costs no propose-lane attempt, same as an enumerated candidate) and
    records the recovered PARAMETERS as provenance facts
    (`ps_exact_family`/`ps_exact_k_num`/`ps_exact_k_den`/`ps_exact_const`/
    `ps_exact_exps_json`) — all integers except the named cross-frame
    constant's tag (a string), per the frame invariant this rung exists to
    honour.

    Also stamps `row_tol`/`row_tol_active` onto any of THIS goal's
    revealed rows whose `expected` is a float and that carry no
    already-declared tolerance (a plain `==` compare against a float
    literal, e.g. task 574's `surfacearea_cylinder(10,5)==942.45`) — the
    documented method (PROGRAM_SYNTHESIS_ARC5_SPECS_IMPLY_FLOATS.md)
    applied mechanically: the fit was found and verified WITHIN that same
    implied tolerance right here, so this records the interval the float
    assert always implied, it does not invent a new one. A row that
    already carries a declared tol (a `math.isclose` assert) or is
    `row_unordered` is never touched — this only ever WIDENS what was
    otherwise silent exact-float equality on a row this exact fit already
    passed at that same tolerance."""
    at = sub.node(g)["attrs"]
    attempts = float(at.get("ps_attempts") or 0.0)
    if float(at.get("ps_exact_done") or -1.0) == attempts:
        return False
    msg = None
    for n in sub.neighbours(g, "about_message"):
        msg = n
    row_nodes = list(sub.neighbours(msg, "has_example")) if msg is not None else []
    args: List[str] = []
    row_dicts: List[Dict[str, Any]] = []
    for r in row_nodes:
        rat = sub.node(r)["attrs"]
        env = _unwire(json.loads(_text(rat.get("inputs_json")) or "{}"))
        for k in env:
            if k not in args:
                args.append(k)
        row_dicts.append({"inputs": env, "expected": rat.get("expected"),
                          "tol": rat.get("row_tol")})
    args = sorted(args)
    rows = pex.interval_rows(row_dicts, args)
    n_tested_total = 0
    winner_family = None
    winner_params = None
    for fam in pex.all_families_ordered(sub):
        params, n_tested = pex.fit_family(fam, rows)
        n_tested_total += n_tested
        if params is not None:
            winner_family, winner_params = fam, params
            break
    if winner_family is None:
        sub.set_attr(g, "ps_exact_outcome", "failed")
        sub.set_attr(g, "ps_exact_candidates", float(n_tested_total))
        sub.set_attr(g, "ps_exact_done", attempts)
        return True
    ir = pex.render_family_to_ir(winner_family, winner_params, args)
    sub.set_attr(g, "ps_ir", json.dumps(ir))
    sub.set_attr(g, "ps_ir_built", attempts)
    sub.set_attr(g, "ps_exact_outcome", "ok")
    sub.set_attr(g, "ps_exact_family", winner_family["name"])
    sub.set_attr(g, "ps_exact_k_num", float(winner_params["k_num"]))
    sub.set_attr(g, "ps_exact_k_den", float(winner_params["k_den"]))
    sub.set_attr(g, "ps_exact_const", winner_params["const"])
    sub.set_attr(g, "ps_exact_exps_json", json.dumps(
        winner_params.get("exps") if "exps" in winner_params
        else [winner_params.get("exps1"), winner_params.get("exps2")]))
    sub.set_attr(g, "ps_exact_candidates", float(n_tested_total))
    sub.set_attr(g, "ps_exact_done", attempts)
    default_tol = winner_family["default_tol"]
    for r in row_nodes:
        rat = sub.node(r)["attrs"]
        if rat.get("row_tol_active") == 1.0 or rat.get("row_unordered") == 1.0:
            continue
        if isinstance(rat.get("expected"), float):
            sub.set_attr(r, "row_tol", default_tol)
            sub.set_attr(r, "row_tol_active", 1.0)
    return True


# --------------------------------------------------------------------------- #
#  read_off_accepted + the pump.
# --------------------------------------------------------------------------- #
def read_off_accepted(sub, ag_node, g) -> bool:
    """Link the reflected IR root onto the accepted Program node
    (`ir_subgraph` — the scope pin's 'do both': the Program carries the
    Term-JSON string AND points at the reflected subgraph). Mechanical."""
    prog = None
    for p in sub.neighbours(g, "accepted_program"):
        prog = p
    if prog is None:
        return False
    if sub.neighbours(prog, "ir_subgraph"):
        return False
    root = None
    for n in sub.neighbours(g, "ps_ir_reflected"):
        root = n
    if root is None:
        return False
    sub.add_edge_unchecked(prog, "ir_subgraph", root)
    return True


# --------------------------------------------------------------------------- #
#  Arc4-S2 VERDICT DISCRIMINATION — structural verdicts BEFORE accept.
#
#  PROGRAM_SYNTHESIS_ARC4_STRUCTURAL_NOTES.md measured seven structural
#  detectors against the accepted IR of the 76 accepted_holdout_fail /
#  21 pass FULL-R3 population; three had non-zero recall AND held
#  precision (D1 memo_lookup_table 1.00, D2 dead_code_free_vars 1.00, D3
#  unread_declared_param 0.88 — its 3 "false positives" are label noise,
#  hand-verified genuine defects, PROGRAM_SYNTHESIS_ARC4_S2_NOTES.md §2).
#  That measurement (`scripts/arc4_structural_verdicts.py`) walked a JSON
#  dict OFFLINE, on a frozen artifact. Here the SAME three detectors are
#  landed LIVE, on the graph: the accepted candidate IS a reflected Term
#  subgraph (`Term.<Variant>` nodes, `child.<field>` edges,
#  runners/dsl/src/reflect.rs) already sitting on `g -ps_ir_reflected->
#  root` (written by `eval_and_record`/`fold_up`), so a structural
#  detector is a WALK of graph data, never a re-parse of the `ps_ir` JSON
#  string.
#
#  The three detectors need a TRANSITIVE closure over an unbounded-depth
#  tree (every bound name in the whole program; every literal leaf
#  reachable through a chain of IfThenElse dispatch) — CLAUDE.md's own
#  documented honest split applies exactly as it does for `record_trace`'s
#  boundary walk: the walk EXCEEDS one `where`-clause rule application
#  (a single rule match is a fixed-depth pattern), so this verb performs
#  the walk and records FIXED-FORMULA facts (the `ps_reflect_ok`/
#  `cmp_ok` precedent — a derived comparison, never a decision about what
#  the agent does next); `ps_structural_reject`/`ps_structural_clear`
#  (seed v1.7.0) read those facts and decide the verdict, mint the
#  explaining `Rejection` node, and route a rejected candidate through
#  the SAME reproposal/exhaustion machinery a genuine failing row already
#  uses (status "counterexample") — reject-before-accept, no park.
#
#  SCOPE: top-level goals only (`ps_depth == 0.0`). The measurement was
#  taken on FULL-R3's top-level accepts; a descend hole's own fold-up
#  accept (P7-A/P7-B, `ps_depth != 0.0`) is intentionally untouched —
#  landing an unmeasured detector against a different population (partial
#  covers, where an "unread" hole param can be legitimately consumed only
#  after folding into the outer skeleton) would violate the precision-
#  first discipline this phase is bound by.
# --------------------------------------------------------------------------- #
_ST_BINDING_TERM_TYPES = {
    "Term.ProgDefFnParam", "Term.ProgAssignVar", "Term.ProgAugAssign",
    "Term.ProgTupleUnpack", "Term.ProgForEach", "Term.ProgTryOr",
    "Term.ProgComprehensionList", "Term.ProgComprehensionGen",
}
_ST_EQUALITY_LIKE_TERM_TYPES = {"Term.Eq", "Term.Minus", "Term.Not"}


def _st_hashable(v: Any) -> Any:
    """Type-DISTINGUISHING hashable key — the same bool-vs-numeric
    convention `mbpp_arc3_battery.agree`/`_row_cmp_ok` already use for
    this pipeline's own holdout/row scoring (a `bool` is never conflated
    with numeric 1/0). A fixed formula, not a decision."""
    if isinstance(v, bool):
        return ("bool", v)
    if isinstance(v, (int, float)):
        return ("numeric", float(v))
    if isinstance(v, (list, tuple)):
        return ("seq", tuple(_st_hashable(x) for x in v))
    if isinstance(v, dict):
        return ("dict", tuple(sorted((k, _st_hashable(x)) for k, x in v.items())))
    return (type(v).__name__, v)


def _st_walk(sub, root, visit) -> None:
    """DFS over the reflected Term subgraph rooted at `root`. A Term.*
    node's own outgoing edges are ALWAYS `child.<field>` by the
    reflection contract (runners/dsl/src/reflect.rs) — no other adapter
    code attaches an outgoing edge to a Term node — so `sub.neighbours(n,
    None)` (every outgoing edge, any type) is exactly 'every child, any
    field, any position', with no field-name enumeration needed. A
    `seen` guard makes the walk safe regardless (a Term subgraph is a
    tree by construction)."""
    seen = set()
    stack = [root]
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        node = sub.node(n)
        visit(n, node["type"], node["attrs"])
        stack.extend(sub.neighbours(n, None))


def _st_has_type(sub, root, target_types) -> bool:
    found = [False]

    def visit(n, t, attrs):
        if t in target_types:
            found[0] = True

    _st_walk(sub, root, visit)
    return found[0]


def _st_var_refs(sub, root) -> set:
    """Every name that appears as a `Term.Var` READ anywhere in the
    program (D2's own `collect_var_refs`, on the graph)."""
    names: set = set()

    def visit(n, t, attrs):
        if t == "Term.Var" and attrs.get("name") is not None:
            names.add(_text(attrs["name"]))

    _st_walk(sub, root, visit)
    return names


def _st_bound_names(sub, root) -> set:
    """Every name BOUND anywhere in the whole program (D2's own
    `collect_bound_names`, on the graph) — a WHOLE-PROGRAM, conservative
    set: it can only UNDER-report free variables, never over-report one.

    Two families of binder, both covered:
    (1) the Prog*-statement binders (param/assign/tuple-unpack/for-loop/
        except-var/comprehension-var) — dispatched by Term TYPE, mirroring
        the frozen `arc4_structural_verdicts.py` reference's own
        `_BINDING_TYPES`.
    (2) the plain DSL HIGHER-ORDER-FUNCTION binders (`Filter`,
        `FilterList`, `Exists`, `Sum`, `Prod`, `MinOver`, `MaxOver`,
        `Argmax`, `Argmin`, `ArgminUnique`, `ArgminRefusal`, `Fold`,
        `MapList`, …) — dispatched by FIELD NAME (`var_name`/`acc_name`,
        the codebase's consistent naming convention for a bound iteration
        variable), not by an enumerated type list, so a construction that
        lands via one of these terms (measured live on the CURRENT MBPP
        battery post-S1/S4 — e.g. `MaxOver(MapList(a, ..., var_name=
        '__item'), var_name='__item')`, task 90's real accepted shape)
        is bound correctly rather than mis-flagged as dead code. This was
        the frozen reference's own honest gap (it never encountered a
        HOF-term accept, so its `_BINDING_TYPES` never needed this), found
        and fixed here via the SAME false-positive discipline
        PROGRAM_SYNTHESIS_ARC4_STRUCTURAL_NOTES.md §2.1 documents for D1."""
    names: set = set()

    def visit(n, t, attrs):
        if attrs.get("var_name"):
            names.add(_text(attrs["var_name"]))
        if attrs.get("acc_name"):
            names.add(_text(attrs["acc_name"]))
        # PROGRAM_SYNTHESIS_ZIPWITH_FOLLOWON: `ZipWith` binds ITS OWN two
        # names (`a_name`/`b_name`, `reflect.rs`'s own ScalarSym fields --
        # a THIRD binder-field-naming convention alongside `var_name`/
        # `acc_name`, distinct from both), never previously recognized
        # here -- found live via `zip_structural_probe.py`: D2 was firing
        # on every ZipWith candidate's OWN bound `__za`/`__zb` (and the
        # nested inner `__zi`/`__zj`), a genuine false positive of the
        # exact SAME class this function's own docstring already documents
        # fixing once for the HOF `var_name`/`acc_name` binders. Same
        # unconditional (pre-`_ST_BINDING_TERM_TYPES`-gate) dispatch
        # discipline as the two checks immediately above.
        if attrs.get("a_name"):
            names.add(_text(attrs["a_name"]))
        if attrs.get("b_name"):
            names.add(_text(attrs["b_name"]))
        if t not in _ST_BINDING_TERM_TYPES:
            return
        if t == "Term.ProgTupleUnpack":
            for nm in (attrs.get("targets") or ()):
                if nm:
                    names.add(_text(nm))
        elif t == "Term.ProgForEach":
            if attrs.get("var"):
                names.add(_text(attrs["var"]))
        elif t == "Term.ProgTryOr":
            if attrs.get("exc_var"):
                names.add(_text(attrs["exc_var"]))
        elif t in ("Term.ProgComprehensionList", "Term.ProgComprehensionGen"):
            if attrs.get("var"):
                names.add(_text(attrs["var"]))
        else:
            if attrs.get("name"):
                names.add(_text(attrs["name"]))

    _st_walk(sub, root, visit)
    return names


def _st_returns(sub, root) -> List[Any]:
    """Every `Term.ProgReturn` node id anywhere in the program (D1's own
    'exactly one ProgReturn' count)."""
    out: List[Any] = []

    def visit(n, t, attrs):
        if t == "Term.ProgReturn":
            out.append(n)

    _st_walk(sub, root, visit)
    return out


def _st_single_child(sub, n, field: str):
    """The one `child.<field>` target of a SINGULAR field (never a list
    field — those need `Children`'s own index, not read here), or None
    for an absent OptChild edge."""
    kids = sub.neighbours(n, "child." + field)
    return kids[0] if kids else None


def _st_is_equality_like_literal_test(sub, cond_node) -> bool:
    """D1's own literal-equality-test predicate, on the graph: the
    condition's own top-level Term is Eq/Minus/Not, AND its subtree
    contains BOTH a Lit leaf and a Var leaf — excluding order predicates
    (Gt/Lt/Gte/Lte), the hallmark of generalising logic, not
    memorisation."""
    if cond_node is None:
        return False
    if sub.node(cond_node)["type"] not in _ST_EQUALITY_LIKE_TERM_TYPES:
        return False
    return (_st_has_type(sub, cond_node, {"Term.Lit"})
            and _st_has_type(sub, cond_node, {"Term.Var"}))


def _st_literal_dispatch(sub, expr_node):
    """True + the reachable literal leaf VALUES iff `expr_node` is built
    ENTIRELY from Lit leaves combined by IfThenElse nodes whose OWN
    condition is an equality-like literal test (D1's shape). `cond`/
    `then`/`other` are all SINGULAR fields, so exact edge-type lookup
    needs no ordering information."""
    if expr_node is None:
        return False, []
    node = sub.node(expr_node)
    t, attrs = node["type"], node["attrs"]
    if t == "Term.Lit":
        return True, [attrs.get("value")]
    if t == "Term.IfThenElse":
        cond = _st_single_child(sub, expr_node, "cond")
        if _st_is_equality_like_literal_test(sub, cond):
            ok1, l1 = _st_literal_dispatch(sub, _st_single_child(sub, expr_node, "then"))
            ok2, l2 = _st_literal_dispatch(sub, _st_single_child(sub, expr_node, "other"))
            if ok1 and ok2:
                return True, l1 + l2
    return False, []


def _st_params(sub, root) -> List[str]:
    """The leading `Term.ProgDefFnParam` DIRECT children of the top-level
    `Term.ProgSeq` root (`_param_names`'s own scope, on the graph — by
    construction every splice/enumerate path emits params as the ONLY
    ProgDefFnParam nodes, so a SET read (order-agnostic; edge order for
    list-valued `child.stmts` isn't exposed over this FFI) is exact)."""
    names: List[str] = []
    for n in sub.neighbours(root, None):
        node = sub.node(n)
        if node["type"] == "Term.ProgDefFnParam":
            nm = node["attrs"].get("name")
            if nm:
                names.append(_text(nm))
    return names


def compute_structural_facts(sub, ag_node, g) -> bool:
    """The mechanical rim of Arc4-S2: walk the CURRENT verified
    candidate's reflected Term subgraph + the goal's own revealed
    ExampleRows (never held-out — an ExampleRow IS the revealed set the
    goal was ingested with) and record D1/D2/D3's raw facts as goal
    attrs. Records; never decides — `ps_structural_reject`/
    `ps_structural_clear` (seed v1.7.0) read these facts.

    Scoped to top-level, NON-DESCENDED goals (`ps_depth == 0.0` AND
    `ps_rung_descend != 1.0`, see the module-level comment above): (1) a
    descend hole itself is left with none of these attrs ever set, so its
    own fold-up accept is byte-unchanged; (2) an OUTER goal that engaged
    descent is ALSO excluded — measured live (PROGRAM_SYNTHESIS_ARC4_S2_
    NOTES.md 'reject routing' section): the P7-B repair lane deliberately
    accepts a plausibly-overfit descend/fold-up candidate FIRST and
    corrects it via LOCALIZED counterexample repair when a real held-out
    row is fed back (`test_headline_la10_converts_to_holdout_ok_via_repair`
    and siblings) — a strictly more targeted correction than this rung's
    reject-to-gapped, so this rung stands down and lets repair do its own,
    better job. The measured detector catalogue
    (`results/arc4_structural_verdicts.json`) was taken over FULL-R3's
    FLAT (non-descended) top-level accepts, so this scoping also keeps the
    landing inside its own measured population.

    Freshness key: the COUNT of `ps_ir_reflected` edges on `g`. EVERY
    flat accept path (`eval_and_record`) adds a FRESH edge before a goal
    can reach 'verified', so this count strictly increases per distinct
    verified candidate."""
    at = sub.node(g)["attrs"]
    if float(at.get("ps_depth") if at.get("ps_depth") is not None else -1.0) != 0.0:
        return False
    if at.get("ps_rung_descend") == 1.0:
        return False
    roots = list(sub.neighbours(g, "ps_ir_reflected"))
    if not roots:
        return False
    n_reflected = len(roots)
    if float(at.get("ps_st_seq") or -1.0) == float(n_reflected):
        return False
    root = roots[-1]

    params = _st_params(sub, root)
    var_refs = _st_var_refs(sub, root)
    bound = _st_bound_names(sub, root)
    free_vars = sorted(n for n in var_refs if n not in bound)

    rows = _outer_rows(sub, g)
    revealed_expected: set = set()
    row_inputs: List[Dict[str, Any]] = []
    for r in rows:
        rat = sub.node(r)["attrs"]
        revealed_expected.add(_st_hashable(rat.get("expected")))
        row_inputs.append(_unwire(json.loads(_text(rat.get("inputs_json")) or "{}")))

    unread = [p for p in params if p not in var_refs]
    varying_unread = []
    for p in unread:
        vals = {_st_hashable(inp.get(p)) for inp in row_inputs if p in inp}
        if len(vals) >= 2:
            varying_unread.append(p)

    returns = _st_returns(sub, root)
    d1_fired = False
    d1_leaves: List[Any] = []
    if len(returns) == 1:
        val_node = _st_single_child(sub, returns[0], "value")
        ok, leaves = _st_literal_dispatch(sub, val_node)
        if ok:
            leaves_set = {_st_hashable(x) for x in leaves}
            if len(leaves_set) >= 2 and leaves_set == revealed_expected:
                d1_fired = True
                d1_leaves = leaves

    d2_fired = bool(free_vars)
    d3_fired = bool(varying_unread)

    fired: List[str] = []
    if d1_fired:
        fired.append("d1_memo_lookup_table")
    if d2_fired:
        fired.append("d2_dead_code_free_vars")
    if d3_fired:
        fired.append("d3_unread_declared_param")

    sub.set_attr(g, "ps_st_d1_fired", 1.0 if d1_fired else 0.0)
    sub.set_attr(g, "ps_st_d2_fired", 1.0 if d2_fired else 0.0)
    sub.set_attr(g, "ps_st_d3_fired", 1.0 if d3_fired else 0.0)
    sub.set_attr(g, "ps_st_free_vars", free_vars)
    sub.set_attr(g, "ps_st_varying_unread_params", varying_unread)
    sub.set_attr(g, "ps_st_d1_leaves", [_plain(x) for x in d1_leaves])
    sub.set_attr(g, "ps_st_fired_detectors", fired)
    sub.set_attr(g, "ps_st_any_fired", 1.0 if fired else 0.0)
    sub.set_attr(g, "ps_st_computed", 1.0)
    sub.set_attr(g, "ps_st_seq", float(n_reflected))
    return True


# --------------------------------------------------------------------------- #
#  P7-A descent verbs — the mechanical rim of the ps_descend_* rules
#  (seed v1.2.0). Facts in, facts out; the rules decide.
# --------------------------------------------------------------------------- #
def _decode_skeleton(sub, skeleton) -> Dict[str, Any]:
    """ONE evaluation of the SAME ShapeDecode the ps_propose rule binds
    (same beam/steps/cand_k), whole-Dict form — the decode's coverage
    assignment (plan / covered / residual)."""
    out = sub._inner.evaluate({
        "type": "ShapeDecode",
        "goal": {"type": "Lit", "value": [list(x) for x in (skeleton or [])]},
        "beam": 3, "max_steps": 8, "cand_k": 3,
        "field": "", "wild_objects": False}, {})
    return out if isinstance(out, dict) else {}


def build_descent(sub, ag_node, g) -> bool:
    """Record the decode's coverage assignment as goal FACTS. The hole
    boundaries ARE this assignment (segmentation-by-recognition — the ink
    precedent); no Python cut anywhere downstream."""
    at = sub.node(g)["attrs"]
    if at.get("ps_descent_decoded") is not None:
        return False
    out = _decode_skeleton(sub, _plain(at.get("skeleton")))
    parts = [_text(p) for p in _plain(out.get("ordered_parts")) or []]
    residual = _plain(out.get("residual")) or []
    res_tokens = [_text(x) for rel in residual for x in rel]
    sub.set_attr(g, "ps_cover_parts", parts)
    sub.set_attr(g, "ps_cover_first", parts[0] if parts else "")
    sub.set_attr(g, "ps_cover_count", float(len(parts)))
    sub.set_attr(g, "ps_residual_tokens", res_tokens)
    sub.set_attr(g, "ps_cover_json", json.dumps(
        {"covered": _plain(out.get("covered")) or [], "residual": residual}))
    sub.set_attr(g, "ps_descent_decoded", 1.0)
    return True


def _current_hole(sub, g):
    """The hole of the CURRENT plan (plan_seq == goal.ps_plan_seq) — a
    mechanical read-back of the rule-minted counter."""
    seq = sub.node(g)["attrs"].get("ps_plan_seq")
    for h in sub.neighbours(g, "has_hole"):
        if sub.node(h)["attrs"].get("plan_seq") == seq:
            return h
    return None


def _outer_rows(sub, g):
    msg = None
    for n in sub.neighbours(g, "about_message"):
        msg = n
    return list(sub.neighbours(msg, "has_example")) if msg is not None else []


def _fold_source_list(sub, source_term, env):
    """The FULL materialised list of a Fold's `source` against `env` —
    the generalization (Arc2-Q4) that unifies the list-input and
    scalar-loop cases behind one formula (a singleton-length check at the
    call site is the ORIGINAL P7-A derivability test, unchanged; `_eval_
    covered_term` consumes the whole list for accumulation replay). A
    plain `Var(list)` source reads directly (byte-unchanged behaviour for
    the P7-A list-input class: `env.get`, no execution). Any OTHER source
    (a COMPUTED source — a range()-class extern call, the factorial/
    sum-to-n scalar accumulation class) is executed via `ProgEval`
    (`_eval_ir_on`'s single-statement-IR idiom): raw `evaluate()` leaves
    Prog* structural nodes INERT by contract (`term.rs`'s documented
    structural-honesty gate), so a computed source can only be
    materialised through the SAME execution path every other Prog IR node
    uses. Returns the materialised list/tuple, or None."""
    if isinstance(source_term, dict) and source_term.get("type") == "Var":
        val = env.get(_text(source_term.get("name")))
        return val if isinstance(val, (list, tuple)) else None
    ir = {"type": "ProgSeq", "stmts": [{"type": "ProgReturn",
                                        "value": source_term}]}
    got, ok = _eval_ir_on(sub, ir, env)
    return got if (ok and isinstance(got, (list, tuple))) else None


def _derive_fold_step(sub, g, h):
    """Derivability scope (a) of prereg H7a, GENERALIZED (Arc2-Q4) to the
    scalar-loop class: the covered construction is a Fold with a literal
    init; a SINGLETON-iteration outer row pins ONE iteration exactly
    (acc_before = init, item = the element, acc_after = the outer output).
    'Singleton' now means 'the Fold's `source` materialises to exactly one
    element' (`_fold_source_list`) — a singleton LIST row (the
    original P7-A case, byte-unchanged reach) OR a scalar row whose
    range()-class source yields exactly one iteration (the smallest
    revealed n that does — the singleton-unroll precedent generalized, per
    PROGRAM_SYNTHESIS_ARC2_Q4_NOTES.md). No inversion, no arithmetic — read,
    evaluate init, record. Multi-step rows are counted as non-determinable
    (named blocker, unchanged)."""
    tmpl = _template_by_name(sub, _text(sub.node(h)["attrs"].get("construction")))
    term = tmpl.get("term") or {}
    if not (isinstance(term, dict) and term.get("type") == "Fold"):
        return [], "not_a_fold_template"
    acc = _text(term.get("acc_name")) or "acc"
    itv = _text(term.get("var_name")) or "x"
    source_term = term.get("source") or {}
    try:
        init_val = sub._inner.evaluate(term.get("init"), {})
    except Exception:
        return [], "init_not_evaluable"
    rows, skipped = [], 0
    for r in _outer_rows(sub, g):
        env = _unwire(json.loads(_text(sub.node(r)["attrs"].get("inputs_json")) or "{}"))
        elems = _fold_source_list(sub, source_term, env)
        if elems is not None and len(elems) == 1:
            rows.append({"inputs": {acc: init_val, itv: elems[0]},
                         "expected": sub.node(r)["attrs"].get("expected")})
        else:
            skipped += 1
    note = "ok" if rows else "no_singleton_iteration_rows"
    return rows, "%s;non_determinable=%d" % (note, skipped)


def _eval_covered_term(sub, term, env):
    """Evaluate ONE covered construction's template term on `env` (the
    final_expr live-var prefix evaluation). A Fold whose source is a
    COMPUTED extern call (Arc2-Q4's scalar-accumulation class — a
    range()-sourced Fold, `tmpl_scalar_fold`) needs its accumulation
    reproduced MANUALLY: the source is materialised via `_fold_source_
    list` (ProgEval execution — raw `evaluate()` leaves Prog* structural
    nodes INERT by contract), then the SAME per-iteration `body` is
    evaluated via raw `evaluate()` for each element (`Fold` is a plain
    DSL term, unsupported inside ProgEval's OWN expression evaluator —
    confirmed empirically: `expr:unsupported_over_prog` — so neither
    execution path alone can run a computed-source Fold end to end).
    This reproduces the Term's own, ALREADY-DEFINED accumulation
    semantics — a fixed translation using the primitives available, no
    new decision. Every OTHER covered term (the P7-A reach: Plus/
    Fold-with-Var/etc.) keeps the ORIGINAL raw `evaluate()` path,
    byte-unchanged. Raises on trap/error, exactly like the original bare
    `evaluate()` call did (the caller's `except Exception` already
    handles both)."""
    if isinstance(term, dict) and term.get("type") == "Fold" and \
            isinstance(term.get("source"), dict) and \
            term["source"].get("type") != "Var":
        elems = _fold_source_list(sub, term["source"], env)
        if elems is None:
            raise ValueError("trap")
        acc_name = _text(term.get("acc_name")) or "acc"
        var_name = _text(term.get("var_name")) or "x"
        acc = sub._inner.evaluate(term.get("init"), env)
        body = term.get("body")
        for item in elems:
            acc = sub._inner.evaluate(body, dict(env, **{acc_name: acc,
                                                         var_name: item}))
        return acc
    return sub._inner.evaluate(term, env)


def _derive_final_expr(sub, g, h):
    """Derivability scope (b) of prereg H7a: live vars — each covered
    construction's expression template evaluated on the row's OWN inputs
    (prefix evaluation + record, via `_eval_covered_term` — Arc2-Q4 widens
    this to correctly execute a scalar-accumulation Fold's computed source).
    A trapping or non-scalar part makes that row non-determinable (counted);
    stmts-mode covers are skipped (named blocker)."""
    at = sub.node(g)["attrs"]
    terms = []
    for name in _plain(at.get("ps_cover_parts")) or []:
        tmpl = _template_by_name(sub, _text(name))
        term = tmpl.get("term")
        if tmpl.get("mode") == "code_write" and isinstance(term, dict):
            terms.append(term)
    if not terms:
        return [], "no_expression_grain_covers"
    rows, skipped = [], 0
    for r in _outer_rows(sub, g):
        env = _unwire(json.loads(_text(sub.node(r)["attrs"].get("inputs_json")) or "{}"))
        vals: Dict[str, Any] = {}
        ok = True
        for i, term in enumerate(terms):
            try:
                v = _eval_covered_term(sub, term, env)
            except Exception:
                ok = False
                break
            if not isinstance(v, _SCALARS):
                ok = False
                break
            vals["v%d" % (i + 1)] = v
        if not ok:
            skipped += 1
            continue
        inputs = {k: v for k, v in env.items() if isinstance(v, _SCALARS)}
        inputs.update(vals)
        rows.append({"inputs": inputs,
                     "expected": sub.node(r)["attrs"].get("expected")})
    note = "ok" if rows else "all_rows_trapped"
    return rows, "%s;non_determinable=%d" % (note, skipped)


# name-keyed dispatch on the RULE-minted hole kind (sanctioned).
_DERIVERS = {
    "fold_step": _derive_fold_step,
    "final_expr": _derive_final_expr,
}


def _solve_arm(sub, rows):
    """ONE branch arm, solved DIRECTLY by SynthEnumerate over its own row
    partition (the same primitive the whole-goal/hole ladder already
    uses, called a second time rather than through a further recursive
    sub-goal — the scope-limited-but-real branch_arm design, Arc2-Q4).
    Returns the candidate's Term-JSON string, or None (empty partition or
    the search found nothing — never guessed)."""
    if not rows:
        return None
    spec = {"type": "SynthEnumerate",
            "examples": {"type": "Lit", "value": _wire_rows(rows)},
            "max_size": 7, "max_candidates": 0, "saturate_k": 0, "field": ""}
    try:
        out = sub._inner.evaluate(spec, {})
    except Exception:
        return None
    if isinstance(out, dict) and out.get("found") and out.get("term"):
        return _text(out.get("term"))
    return None


def _derive_branch_arms(sub, g, holes) -> None:
    """BRANCH-ARM DERIVATION (Arc2-Q4, closing the P7-A named blocker): the
    covered construction's OWN decided `cond` (kept verbatim — 'the
    skeleton keeps its structure, only the part in question changes', the
    P7-A precedent applied one op-level up) partitions the OUTER rows into
    a then-set / other-set (a fixed evaluation, never guessed), and EACH
    partition is solved by its own DIRECT SynthEnumerate call
    (`_solve_arm`) — no further sub-goal recursion. A genuinely
    NON-TRIVIAL partition (both sides non-empty) is required, or the plan
    honestly refuses; `arm_found`/`solved_term_json`/`arm_derive_done` are
    recorded on BOTH holes (the `ps_branch_arm_ready`/`_failed` rules
    judge the facts)."""
    by_kind = {_text(sub.node(h)["attrs"].get("kind")): h for h in holes}
    h_then, h_other = by_kind.get("branch_then"), by_kind.get("branch_other")
    anchor = h_then if h_then is not None else h_other
    construction = _text(sub.node(anchor)["attrs"].get("construction"))
    tmpl = _template_by_name(sub, construction)
    term = tmpl.get("term") or {}
    cond = term.get("cond") if isinstance(term, dict) else None
    then_rows, other_rows = [], []
    if isinstance(term, dict) and term.get("type") == "IfThenElse" \
            and cond is not None:
        for r in _outer_rows(sub, g):
            env = _unwire(json.loads(_text(sub.node(r)["attrs"].get("inputs_json")) or "{}"))
            try:
                c = sub._inner.evaluate(cond, env)
            except Exception:
                continue
            row = {"inputs": env, "output": sub.node(r)["attrs"].get("expected")}
            (then_rows if c else other_rows).append(row)
    nontrivial = bool(then_rows) and bool(other_rows)
    then_json = _solve_arm(sub, then_rows) if nontrivial else None
    other_json = _solve_arm(sub, other_rows) if nontrivial else None
    found = bool(nontrivial and then_json is not None and other_json is not None)
    for h, term_json in ((h_then, then_json), (h_other, other_json)):
        if h is None:
            continue
        sub.set_attr(h, "solved_term_json", term_json or "")
        sub.set_attr(h, "arm_found", 1.0 if found else 0.0)
        sub.set_attr(h, "arm_derive_done", 1.0)
    if cond is not None:
        sub.set_attr(g, "ps_branch_cond_json", json.dumps(cond))


def derive_hole_rows(sub, ag_node, g) -> bool:
    """Record the current hole's derived rows + counts. The
    ps_hole_derived / ps_hole_underivable RULES judge the facts.

    Arc2-Q4: branch_then/branch_other holes (minted TOGETHER by
    ps_plan_branch_arm, sharing one plan_seq) take a SHORTER path —
    `_derive_branch_arms` solves BOTH directly and records `arm_derive_
    done`/`arm_found` (never `derive_done`/`n_derived`, so the GENERIC
    ps_hole_derived/ps_hole_underivable rules — keyed on those attrs —
    never fire for them; the NEW ps_branch_arm_ready/_failed rules do)."""
    seq = sub.node(g)["attrs"].get("ps_plan_seq")
    branch_holes = [h for h in sub.neighbours(g, "has_hole")
                    if sub.node(h)["attrs"].get("plan_seq") == seq
                    and _text(sub.node(h)["attrs"].get("kind"))
                    in ("branch_then", "branch_other")]
    if branch_holes:
        if any(sub.node(h)["attrs"].get("arm_derive_done") is not None
               for h in branch_holes):
            return False
        _derive_branch_arms(sub, g, branch_holes)
        return True
    h = _current_hole(sub, g)
    if h is None or sub.node(h)["attrs"].get("derive_done") is not None:
        return False
    kind = _text(sub.node(h)["attrs"].get("kind"))
    deriver = _DERIVERS.get(kind)
    if deriver is None:
        rows, note = [], "unsupported_hole_kind:%s" % kind
    else:
        rows, note = deriver(sub, g, h)
    sub.set_attr(h, "derived_rows_json", json.dumps(rows))
    sub.set_attr(h, "n_derived", float(len(rows)))
    sub.set_attr(h, "derive_note", note)
    sub.set_attr(h, "derive_done", 1.0)
    return True


def spawn_subgoal(sub, ag_node, g) -> bool:
    """Transcribe the rule-decided sub-goal: a Message whose spec IS the
    decode's residual (tokens + skeleton) + the derived ExampleRows.
    ps_write_request=1.0 is the transcription of THIS ladder's decision
    that the hole is a write sub-request (the rules minted the Hole);
    ps_goal then mints the sub-Goal like any request."""
    h = _current_hole(sub, g)
    if h is None or sub.node(h)["attrs"].get("spawned") is not None:
        return False
    at = sub.node(g)["attrs"]
    hat = sub.node(h)["attrs"]
    tokens = [_text(x) for x in _plain(at.get("ps_residual_tokens")) or []]
    m2 = sub.add_node("Message", {
        "text": "[hole:%s] %s" % (_text(hat.get("kind")),
                                  _text(at.get("request"))),
        "ps_write_request": 1.0,
        "ps_spec_name": "%s__%s" % (_text(at.get("name")),
                                    _text(hat.get("name"))),
        "ps_tokens": tokens,
        "ps_skeleton": [[t] for t in tokens],
        "ps_depth": float(hat.get("depth") or 1.0),
        "ps_hole_spec": 1.0,
    })
    sub.add_edge_unchecked(ag_node, "received", m2)
    for row in json.loads(_text(hat.get("derived_rows_json")) or "[]"):
        sub.add_edge_unchecked(m2, "has_example",
                               _add_example_row(sub, row["inputs"],
                                                row["expected"]))
    # P7-B: transcribe the rule-minted hole-scope exclusions (ExcludedSub —
    # ps_localize_hole's decision) onto the sub-spec so the enumerate rung's
    # INPUT changes (SynthEnumerate is deterministic; exclusion without an
    # input shift is a no-op by construction). Mechanical translation:
    # every excluded term of this hole's kind is carried as provenance
    # (ps_enum_excluded); an excluded BARE-LIT numeric value is a droppable
    # const (ps_enum_drop_consts) — run_enumerate mirrors the Term's
    # documented default const set minus these. Empty for non-repair holes:
    # the pre-P7B spawn is byte-identical.
    drops: List[Any] = []
    excl: List[str] = []
    for xs in sub.neighbours(g, "ps_sub_excluded"):
        xat = sub.node(xs)["attrs"]
        if _text(xat.get("kind")) != _text(hat.get("kind")):
            continue
        try:
            t = json.loads(_text(xat.get("term")) or "null")
        except Exception:
            t = None
        if isinstance(t, dict):
            excl.append(json.dumps(t, sort_keys=True))
            if t.get("type") == "Lit" and \
                    isinstance(t.get("value"), (int, float)):
                drops.append(t.get("value"))
    if excl:
        sub.set_attr(m2, "ps_enum_excluded", excl)
    if drops:
        sub.set_attr(m2, "ps_enum_drop_consts", drops)
    sub.add_edge_unchecked(h, "sub_message", m2)
    sub.set_attr(h, "spawned", 1.0)
    return True


def _extract_return_expr(ir):
    """Mechanical structural read of an accepted sub-IR: params + exactly
    one ProgReturn and nothing else → (params, return-expr); anything
    else → (params, None) — the fold-up rules read fu_spliceable."""
    params, expr, extra = [], None, False
    for st in (ir.get("stmts") or []) if isinstance(ir, dict) else []:
        t = st.get("type")
        if t == "ProgDefFnParam":
            params.append(st.get("name"))
        elif t == "ProgReturn" and expr is None:
            expr = st.get("value")
        else:
            extra = True
    return params, (None if extra else expr)


def _splice_fold_step(sub, g, h, expr):
    tmpl = _template_by_name(sub, _text(sub.node(h)["attrs"].get("construction")))
    term = json.loads(json.dumps(tmpl.get("term") or {}))
    if term.get("type") != "Fold":
        return None
    term["body"] = expr
    stmts = [{"type": "ProgDefFnParam", "name": str(a), "default": None}
             for a in tmpl.get("args") or []]
    if _is_scalar_fold(term):
        stmts.extend(_lower_scalar_fold_stmts(term, final={"kind": "return"}))
    else:
        stmts.append({"type": "ProgReturn", "value": term})
    return {"type": "ProgSeq", "stmts": stmts}


def _splice_final_expr(sub, g, h, expr):
    at = sub.node(g)["attrs"]
    args: List[str] = []
    for r in _outer_rows(sub, g):
        env = _unwire(json.loads(_text(sub.node(r)["attrs"].get("inputs_json")) or "{}"))
        for k in env:
            if k not in args:
                args.append(k)
    stmts = [{"type": "ProgDefFnParam", "name": a, "default": None}
             for a in sorted(args)]
    i = 0
    for name in _plain(at.get("ps_cover_parts")) or []:
        tmpl = _template_by_name(sub, _text(name))
        term = tmpl.get("term")
        if tmpl.get("mode") == "code_write" and isinstance(term, dict):
            i += 1
            if _is_scalar_fold(term):
                stmts.extend(_lower_scalar_fold_stmts(
                    term, final={"kind": "assign", "name": "v%d" % i}))
            else:
                stmts.append({"type": "ProgAssignVar", "name": "v%d" % i,
                              "value": term})
    if i == 0:
        return None
    stmts.append({"type": "ProgReturn", "value": expr})
    return {"type": "ProgSeq", "stmts": stmts}


def _splice_branch_arm(sub, g, expr):
    """The recombined IfThenElse (both arms already solved directly, no
    sub-IR to extract from — Arc2-Q4) → a full function body over the
    outer rows' own raw inputs."""
    args: List[str] = []
    for r in _outer_rows(sub, g):
        env = _unwire(json.loads(_text(sub.node(r)["attrs"].get("inputs_json")) or "{}"))
        for k in env:
            if k not in args:
                args.append(k)
    stmts = [{"type": "ProgDefFnParam", "name": a, "default": None}
             for a in sorted(args)]
    stmts.append({"type": "ProgReturn", "value": expr})
    return {"type": "ProgSeq", "stmts": stmts}


_SPLICERS = {
    "fold_step": _splice_fold_step,
    "final_expr": _splice_final_expr,
}


def _foldup_reflect_and_eval(sub, g, ir, seq) -> None:
    """The SHARED fold-up tail (reflect + ProgEval per FULL outer row into
    the fu_* lane, never eval_attempt) — factored out (Arc2-Q4) so the
    branch_arm path and the sub-goal-based paths run byte-identical
    execution/verdict machinery."""
    sub.set_attr(g, "ps_ir", json.dumps(ir))
    root = sub._inner.add_term_subgraph(ir)
    back = sub._inner.term_subgraph_json(root)
    root2 = sub._inner.add_term_subgraph(json.loads(back))
    reflect_ok = 1.0 if sub._inner.term_subgraph_json(root2) == back else 0.0
    sub.remove_node(root2)
    sub.set_attr(g, "ps_reflect_ok", reflect_ok)
    sub.add_edge_unchecked(g, "ps_ir_reflected", root)
    term = _prog_eval_term("e", "p")
    for r in _outer_rows(sub, g):
        env = _unwire(json.loads(_text(sub.node(r)["attrs"].get("inputs_json")) or "{}"))
        out = sub._inner.evaluate(term, {"e": env, "p": root})
        got = out.get("result")
        ok = 1.0 if (out.get("halted") is True and out.get("trap") is None) \
            else 0.0
        sub.set_attr(r, "fu_ok", ok)
        # ARC6 value layer, HV4: the FOLD-UP lane carried the identical
        # scalar-only cast, and `ps_foldup_accept`/`ps_foldup_reject`
        # have no `fu_cmp_ok` to fall back on. Fixed in the same motion,
        # so "the non-scalar verdict is fixed" is not false here.
        sub.set_attr(r, "fu_got", got)
        sub.set_attr(r, "fu_seq", seq)


def fold_up(sub, ag_node, g) -> bool:
    """Splice the accepted sub-IR into the skeleton (mechanical), reflect,
    and record ProgEval facts for the FULL outer rows in the fu_* lane.
    The ps_foldup_accept / ps_foldup_reject rules decide.

    Arc2-Q4: branch_then/branch_other holes (sharing one plan_seq, both
    solved DIRECTLY by `_derive_branch_arms` — no sub-goal, no
    `sub_message` edge) take a dedicated path: read BOTH `solved_term_
    json` values + the recorded decided `cond`, build the recombined
    IfThenElse, and run the SAME shared reflect+eval tail. `fu_done`/
    `fu_spliceable` are set on BOTH holes so ps_foldup_accept/ps_foldup_
    reject (unmodified — they simply match twice, harmlessly, on the two
    hole bindings) read a consistent verdict either way."""
    at = sub.node(g)["attrs"]
    seq = at.get("ps_plan_seq")
    branch_holes = {_text(sub.node(h)["attrs"].get("kind")): h
                    for h in sub.neighbours(g, "has_hole")
                    if sub.node(h)["attrs"].get("plan_seq") == seq}
    h_then, h_other = branch_holes.get("branch_then"), branch_holes.get("branch_other")
    if h_then is not None and h_other is not None:
        if sub.node(h_then)["attrs"].get("fu_done") is not None:
            return False
        then_j = _text(sub.node(h_then)["attrs"].get("solved_term_json"))
        other_j = _text(sub.node(h_other)["attrs"].get("solved_term_json"))
        cond_j = _text(at.get("ps_branch_cond_json"))
        ir = None
        if then_j and other_j and cond_j:
            try:
                expr = {"type": "IfThenElse", "cond": json.loads(cond_j),
                        "then": json.loads(then_j), "other": json.loads(other_j)}
                ir = _splice_branch_arm(sub, g, expr)
            except Exception:
                ir = None
        spliceable = 1.0 if ir is not None else 0.0
        sub.set_attr(h_then, "fu_spliceable", spliceable)
        sub.set_attr(h_other, "fu_spliceable", spliceable)
        if ir is not None:
            _foldup_reflect_and_eval(sub, g, ir, seq)
        sub.set_attr(h_then, "fu_done", 1.0)
        sub.set_attr(h_other, "fu_done", 1.0)
        return True
    h = _current_hole(sub, g)
    if h is None or sub.node(h)["attrs"].get("fu_done") is not None:
        return False
    hat = sub.node(h)["attrs"]
    g2 = None
    for m2 in sub.neighbours(h, "sub_message"):
        for cand in sub.in_neighbours(m2, "about_message"):
            g2 = cand
    sub_ir = json.loads(_text(sub.node(g2)["attrs"].get("ps_ir")) or "{}") \
        if g2 is not None else {}
    _params, expr = _extract_return_expr(sub_ir)
    if expr is not None:
        # P7-B: record the candidate sub-term the fold-up is about to judge —
        # the repair lane's ps_localize_hole copies it into an ExcludedSub
        # when a later counterexample refutes the fold (mechanical record).
        sub.set_attr(h, "solved_term_json", json.dumps(expr))
    splicer = _SPLICERS.get(_text(hat.get("kind")))
    ir = splicer(sub, g, h, expr) if (splicer and expr is not None) else None
    if ir is None:
        sub.set_attr(h, "fu_spliceable", 0.0)
        sub.set_attr(h, "fu_done", 1.0)
        return True
    sub.set_attr(h, "fu_spliceable", 1.0)
    _foldup_reflect_and_eval(sub, g, ir, seq)
    sub.set_attr(h, "fu_done", 1.0)
    return True


# --------------------------------------------------------------------------- #
#  P7-B repair verbs — the mechanical rim of the ps_repair_* / ps_localize_*
#  rules (seed v1.3.0). Facts in, facts out; the rules decide.
# --------------------------------------------------------------------------- #
def ingest_counterexample(sub, ag_node, g, inputs, expected):
    """CEGIS at the accept boundary: an externally-observed failing row (the
    environment's / verifier's report) is transcribed onto the goal's spec
    Message as an ExampleRow{ce_pending:1.0} — a recorded datum, the
    ps_write_request precedent. The ps_repair_mark RULE decides the accept
    is refuted. Mechanical ingest; returns the row node."""
    m = None
    for n in sub.neighbours(g, "about_message"):
        m = n
    r = _add_example_row(sub, inputs, expected)
    sub.set_attr(r, "ce_pending", 1.0)
    sub.set_attr(r, "ce_source", "verify")
    sub.add_edge_unchecked(m, "has_example", r)
    return r


def _eval_ir_on(sub, ir, env):
    """ProgEval of an IR dict on one env (pure, fueled) — the eval_and_record
    evaluation, locally scoped for the trace. Returns (got, ok)."""
    root = sub._inner.add_term_subgraph(ir)
    out = sub._inner.evaluate(_prog_eval_term("e", "p"), {"e": env, "p": root})
    sub.remove_node(root)
    got = out.get("result")
    ok = out.get("halted") is True and out.get("trap") is None
    return got, ok


def _trace_final_expr(sub, g, ir, rows):
    """Boundary trace for a final_expr-folded skeleton: each covered
    construction's template re-evaluated on the row's own inputs IS the
    derivable expectation for its live var (descent's _derive_final_expr
    machinery, reused as prereg'd); the observed boundary is the accepted
    IR's own assign term under prefix evaluation. The final boundary is the
    return: got vs the row's expected. Fixed formulas; facts only."""
    at = sub.node(g)["attrs"]
    terms = []
    for name in _plain(at.get("ps_cover_parts")) or []:
        tmpl = _template_by_name(sub, _text(name))
        term = tmpl.get("term")
        if tmpl.get("mode") == "code_write" and isinstance(term, dict):
            terms.append((str(_text(name)), term))
    assigns = [st for st in (ir.get("stmts") or [])
               if isinstance(st, dict) and st.get("type") == "ProgAssignVar"]
    bounds: List[Dict[str, Any]] = []
    derivable = 0
    skel_agree = 1.0
    diverge = 0.0
    for r in rows:
        env = _unwire(json.loads(_text(sub.node(r)["attrs"].get("inputs_json")) or "{}"))
        vals: Dict[str, Any] = {}
        row_derivable = True
        for i, (name, term) in enumerate(terms):
            entry: Dict[str, Any] = {"row": r, "stmt": "v%d" % (i + 1),
                                     "construction": name}
            try:
                expect = _eval_covered_term(sub, term, dict(env, **vals))
            except Exception:
                entry["derivable"] = 0.0
                bounds.append(entry)
                row_derivable = False
                break
            if not isinstance(expect, _SCALARS):
                entry["derivable"] = 0.0
                bounds.append(entry)
                row_derivable = False
                break
            obs = None
            if i < len(assigns):
                try:
                    obs = _eval_covered_term(sub, assigns[i].get("value"),
                                             dict(env, **vals))
                except Exception:
                    obs = None
            vals["v%d" % (i + 1)] = expect
            agree = 1.0 if _plain(obs) == _plain(expect) else 0.0
            derivable += 1
            if agree != 1.0:
                skel_agree = 0.0
            entry.update({"derivable": 1.0, "expect": _plain(expect),
                          "got": _plain(obs), "agree": agree})
            bounds.append(entry)
        if not row_derivable:
            continue
        got, ok = _eval_ir_on(sub, ir, env)
        exp = sub.node(r)["attrs"].get("expected")
        div = 0.0 if (ok and _plain(got) == _plain(exp)) else 1.0
        bounds.append({"row": r, "stmt": "return", "expect": _plain(exp),
                       "got": _plain(got), "diverge": div})
        derivable += 1
        if div == 1.0:
            diverge = 1.0
    return derivable, skel_agree, diverge, bounds


def _trace_fold_step(sub, g, ir, rows):
    """Boundary trace for a fold_step-folded skeleton, GENERALIZED (Arc2-Q4,
    the same `_fold_source_list` unification as `_derive_fold_step`):
    a SINGLETON-iteration counterexample row (a list row OR a scalar row
    whose range()-class source yields exactly one element) pins the
    one-iteration unroll exactly (acc_before = the fold's literal init,
    item = the element, acc_after = the row's expected — descent's
    _derive_fold_step scope, reused as prereg'd); the observed boundary is
    the held body evaluated at that point. Multi-step rows pin nothing
    (counted non-derivable, never guessed) — with zero derivable
    boundaries the ps_localize_refuse_* rules fall to the global path."""
    fold = None
    for st in (ir.get("stmts") or []) if isinstance(ir, dict) else []:
        if isinstance(st, dict) and st.get("type") == "ProgReturn" and \
                isinstance(st.get("value"), dict) and \
                st["value"].get("type") == "Fold":
            fold = st["value"]
    if fold is None:
        return 0, 0.0, 0.0, []
    acc = _text(fold.get("acc_name")) or "acc"
    itv = _text(fold.get("var_name")) or "x"
    source_term = fold.get("source") or {}
    try:
        init_val = sub._inner.evaluate(fold.get("init"), {})
    except Exception:
        return 0, 0.0, 0.0, []
    bounds: List[Dict[str, Any]] = []
    derivable = 0
    diverge = 0.0
    for r in rows:
        env = _unwire(json.loads(_text(sub.node(r)["attrs"].get("inputs_json")) or "{}"))
        elems = _fold_source_list(sub, source_term, env)
        if elems is not None and len(elems) == 1:
            item = elems[0]
            expect = sub.node(r)["attrs"].get("expected")
            try:
                obs = sub._inner.evaluate(fold.get("body"),
                                          {acc: init_val, itv: item})
            except Exception:
                obs = None
            div = 0.0 if _plain(obs) == _plain(expect) else 1.0
            derivable += 1
            if div == 1.0:
                diverge = 1.0
            bounds.append({"row": r, "stmt": "fold_step", "derivable": 1.0,
                           "acc": _plain(init_val), "item": _plain(item),
                           "expect": _plain(expect), "got": _plain(obs),
                           "diverge": div})
        else:
            bounds.append({"row": r, "stmt": "fold_step", "derivable": 0.0})
    # the skeleton boundary here is the fold's literal init — identical to
    # the template's by construction (recorded vacuously true).
    return derivable, 1.0, diverge, bounds


# name-keyed dispatch on the RULE-minted folded-hole kind (sanctioned).
_TRACERS = {
    "final_expr": _trace_final_expr,
    "fold_step": _trace_fold_step,
}


def record_trace(sub, ag_node, g) -> bool:
    """Record the failing row's boundary facts against derivable expectations
    (prefix evaluation — descent's row-derivation machinery reused). The
    ps_localize_hole / ps_localize_refuse_* / ps_repair_exhausted RULES judge
    the facts; this verb never decides. Freshness via ps_trace_seq ==
    ps_repair_seq (the repair round counter)."""
    at = sub.node(g)["attrs"]
    seq = at.get("ps_repair_seq")
    if at.get("ps_trace_seq") == seq:
        return False
    ce_rows = [r for r in _outer_rows(sub, g)
               if sub.node(r)["attrs"].get("ce_pending") == 1.0]
    folded = None
    for h in sub.neighbours(g, "has_hole"):
        if _text(sub.node(h)["attrs"].get("hole_status")) == "folded":
            folded = h
    kind = _text(sub.node(folded)["attrs"].get("kind")) \
        if folded is not None else None
    tracer = _TRACERS.get(kind or "")
    ir = json.loads(_text(at.get("ps_ir")) or "{}")
    if tracer is None:
        derivable, skel_agree, diverge, bounds = 0, 0.0, 0.0, []
    else:
        derivable, skel_agree, diverge, bounds = tracer(sub, g, ir, ce_rows)
    for r in ce_rows:
        sub.set_attr(r, "ce_pending", 0.0)
        sub.set_attr(r, "ce_traced", seq)
    sub.set_attr(g, "ps_trace_derivable", float(derivable))
    sub.set_attr(g, "ps_trace_skel_agree", float(skel_agree))
    sub.set_attr(g, "ps_trace_diverge_hole", float(diverge))
    sub.set_attr(g, "ps_trace_json", json.dumps(
        [{k: v for k, v in b.items()} for b in bounds], default=str))
    sub.set_attr(g, "ps_trace_seq", seq)
    return True


# name-keyed dispatch on RULE VERDICTS (statuses) — sanctioned; the verbs
# themselves never branch on graph state beyond their own done-markers.
_DISPATCH = (
    ("lattice_pending", stamp_lattice),
    ("bind_pending", splice_binding),
    ("eval_pending", eval_and_record),
    ("exact_pending", run_exact_family),
    # Arc5 MOVE A/B (PROGRAM_SYNTHESIS_ARC5_MOVES.md): scan mints
    # MoveCandidate facts (orbit-augmentation relaxations + intermediate-
    # factor decompositions); ps_move_select/ps_move_none (seed rules) do
    # the weighted-collapse Argmax; apply_selected_move mechanically
    # executes whichever candidate the RULE selected.
    ("moves_scan", pmv.run_structural_moves),
    ("move_apply_pending", pmv.apply_selected_move),
    ("enumerate_pending", run_enumerate),
    ("screen_running", screen_construction),
    ("descend_pending", build_descent),
    ("hole_derive", derive_hole_rows),
    ("hole_spawn", spawn_subgoal),
    ("foldup_pending", fold_up),
    ("trace_pending", record_trace),
    # Arc4-S2: structural verdicts BEFORE accept. Dispatched on 'verified'
    # itself (the SAME status ps_accept reads) -- compute_structural_facts
    # is idempotent per candidate (the ps_ir_reflected-count freshness key)
    # and scoped to top-level goals only, so it is always safe to run
    # whenever a goal is sitting at 'verified', on every path (codebook,
    # enumerate, retrieval, fold-up) that reaches it.
    ("verified", compute_structural_facts),
    # Arc6-D: theorem-derived PROPERTY verdicts BESIDE the D1-D3 structural
    # detectors, on the SAME 'verified' status -- compute_property_facts is
    # idempotent per candidate (the ps_ir_reflected-count freshness key,
    # the compute_structural_facts precedent) and scoped identically
    # (top-level, non-descended goals only), so both dispatch entries are
    # always safe to run together whenever a goal is sitting at 'verified'.
    # The attribute lookup is DEFERRED (a lambda, not `pp.compute_property_
    # facts` inlined) so this tuple's construction never depends on import
    # ORDER between this module and `prog_property` (the two import each
    # other; whichever loads first would otherwise see a not-yet-fully-
    # initialised partial module here).
    ("verified", lambda sub, ag_node, g: pp.compute_property_facts(sub, ag_node, g)),
    ("accepted", read_off_accepted),
    # Arc3-R1: retrieval-shaped proposal (top-level goals only). The
    # universal screen's codebook/chunk half was FIRST attempted and
    # REVERTED (PROGRAM_SYNTHESIS_ARC3_R12_NOTES.md) — it screened
    # PARTIAL-COVER constructions descent legitimately depends on, a false
    # negative. Arc3-R2.5 (`screen_construction` above, `screen_running`
    # dispatch entry) redoes it SCOPED: `ps_screen_mark` (seed v1.5.1) only
    # ever marks a goal screenable when it is NOT DESCEND_APPLICABLE (the
    # SAME predicate ps_descend_mark/ps_enumerate_mark already embed), so
    # every partial-cover-eligible goal's ps_propose path is untouched by
    # construction. The retrieval lane's OWN screen (`run_retrieval_ladder`
    # screens every candidate on revealed rows before it may accept) is
    # unaffected either way — see `domains/prog_retrieval.py`.
    ("retrieve_pending", pr.score_exemplars),
    ("retrieve_ladder", pr.run_retrieval_ladder),
)


def pump(sub, ag_node, *, max_rounds: int = 32) -> None:
    """The fixpoint driver: run_rules to fixpoint, apply the pending
    mechanical verb for each goal status, repeat until nothing moves —
    ingest → tick → query, CLAUDE.md's own loop."""
    for _ in range(max_rounds):
        sub._inner.run_rules(400000)
        moved = False
        for g in sub.nodes("Goal"):
            at = sub.node(g)["attrs"]
            if at.get("kind") != "synth_program":
                continue
            status = _text(at.get("status"))
            for key, verb in _DISPATCH:
                if status == key:
                    moved = bool(verb(sub, ag_node, g)) or moved
        if not moved:
            break
    sub._inner.run_rules(400000)


def synthesize_from_request(sub, ag_node, text: str, examples=(), *,
                            name: Optional[str] = None,
                            quantities: Optional[Dict[str, int]] = None
                            ) -> Dict[str, Any]:
    """ingest → pump → read-off, one call (the QuestionDriver mint → ingest
    → pump → read-off shape). Returns the goal's outcome read-back."""
    ensure_program_synthesis(sub, sub._inner, ag_node)
    m = ingest_spec(
        sub, ag_node, text, examples, name=name, quantities=quantities
    )
    pump(sub, ag_node)
    for g in sub.in_neighbours(m, "about_message"):
        return read_goal(sub, g)
    return {"status": None, "message": m}


def read_goal(sub, g) -> Dict[str, Any]:
    """Mechanical read-back of one goal's loop outcome."""
    at = sub.node(g)["attrs"]
    prog = None
    prog_attrs = None
    for p in sub.neighbours(g, "accepted_program"):
        prog = p
        prog_attrs = {k: _plain(v) for k, v in sub.node(p)["attrs"].items()}
    ces = []
    for ce in sub.neighbours(g, "has_counterexample"):
        ces.append({k: _plain(v) for k, v in sub.node(ce)["attrs"].items()})
    rejections = []
    for rej in sub.neighbours(g, "has_structural_rejection"):
        rejections.append({k: _plain(v) for k, v in sub.node(rej)["attrs"].items()})
    excluded = [_text(sub.node(x)["attrs"].get("name"))
                for x in sub.neighbours(g, "ps_excluded")]
    screen_kills = sum(
        1 for x in sub.neighbours(g, "ps_excluded")
        if sub.node(x)["attrs"].get("screened_failed") == 1.0)
    return {
        "goal": g,
        "status": _text(at.get("status")),
        "name": _text(at.get("name")),
        "construction": _text(at.get("ps_construction")),
        "attempts": at.get("ps_attempts"),
        "budget": at.get("ps_budget"),
        "rungs": {
            "codebook": at.get("ps_rung_codebook"),
            "lattice": at.get("ps_rung_lattice"),
            "descend": at.get("ps_rung_descend"),
            "exact": at.get("ps_rung_exact"),
            "enumerate": at.get("ps_rung_enumerate"),
        },
        # Arc5 exact-first rung's own read-back (mechanical; the DECISION
        # already happened in seed rules — this is the provenance trail).
        "exact": {
            "outcome": _text(at.get("ps_exact_outcome")),
            "family": _text(at.get("ps_exact_family")),
            "k_num": at.get("ps_exact_k_num"),
            "k_den": at.get("ps_exact_k_den"),
            "const": _text(at.get("ps_exact_const")),
            "exps": json.loads(_text(at.get("ps_exact_exps_json")))
                   if at.get("ps_exact_exps_json") else None,
            "candidates": at.get("ps_exact_candidates"),
        },
        "descend_kind": _text(at.get("ps_descend_kind")),
        "cover_parts": [_text(x)
                        for x in _plain(at.get("ps_cover_parts")) or []],
        "residual_tokens": [_text(x)
                            for x in _plain(at.get("ps_residual_tokens")) or []],
        "holes": [
            {k: _plain(v) for k, v in sub.node(h)["attrs"].items()}
            for h in sub.neighbours(g, "has_hole")
        ],
        "spine_labels": [_text(x) for x in (_plain(at.get("ps_spine_labels")) or [])],
        "gap_reason": _text(at.get("ps_gap_reason")),
        "enumerate_outcome": _text(at.get("ps_enumerate_outcome")),
        "enumerate": {
            "operator_shape": _text(at.get("ps_enum_operator_shape")),
            "ops": _plain(at.get("ps_enum_ops")) or [],
            "grounded_constants": (
                _plain(at.get("ps_enum_grounded_constants")) or []
            ),
            "tested": at.get("ps_enum_tested"),
            "distinct": at.get("ps_enum_distinct"),
            "solution_size": at.get("ps_enum_solution_size"),
        },
        "repair": {
            "seq": at.get("ps_repair_seq"),
            "attempts": at.get("ps_repair_attempts"),
            "budget": at.get("ps_repair_budget"),
            "kind": _text(at.get("ps_repair_kind")),
            "localized": at.get("ps_repair_localized"),
            "refused": at.get("ps_repair_refused"),
            "gaveup": at.get("ps_repair_gaveup"),
            "trace_seq": at.get("ps_trace_seq"),
            "trace_skel_agree": at.get("ps_trace_skel_agree"),
            "trace_diverge_hole": at.get("ps_trace_diverge_hole"),
            "trace_derivable": at.get("ps_trace_derivable"),
        },
        "sub_excluded": [
            {k: _plain(v) for k, v in sub.node(x)["attrs"].items()}
            for x in sub.neighbours(g, "ps_sub_excluded")
        ],
        "retrieval": {
            "rung_reached": _text(at.get("pr_rung_reached")),
            "n_candidates": at.get("pr_n_candidates"),
            "accept_task_id": at.get("pr_accept_task_id"),
            "accept_perm": _plain(at.get("pr_accept_perm")),
            "accept_edit": json.loads(_text(at.get("pr_accept_edit_json")))
                          if at.get("pr_accept_edit_json") else None,
        },
        # Arc3-R2.5: the codebook-side screen's own read-back (distinct from
        # `retrieval` above, which is the RETRIEVAL grain's own screen —
        # this is the codebook/chunk grain). `kills` counts Excluded nodes
        # this goal's OWN screen minted (tagged `screened_failed`), never a
        # real counterexample exclusion — the decoy-tax kill count.
        "screen": {
            "kills": float(screen_kills),
            "candidate": _text(at.get("ps_screen_candidate")),
            "verdict": at.get("ps_screen_verdict"),
        },
        # Arc4-S1 BUDGET ISOLATION: the propose lane (codebook + retrieval,
        # ps_propose_attempts/ps_propose_budget) and the RESERVED,
        # untouchable enumerate lane (ps_enum_reserve_used/budget) are
        # separate counters from ps_attempts/ps_budget above — mechanical
        # read-back only, the decision (which lane gates which rung) lives
        # entirely in seeds/program_synthesis.json's rules.
        "isolation": {
            "propose_attempts": at.get("ps_propose_attempts"),
            "propose_budget": at.get("ps_propose_budget"),
            "enum_reserve_used": at.get("ps_enum_reserve_used"),
            "enum_reserve_budget": at.get("ps_enum_reserve_budget"),
            "repair_entered": at.get("ps_repair_entered"),
        },
        "reflect_ok": at.get("ps_reflect_ok"),
        "ir": json.loads(_text(at.get("ps_ir"))) if at.get("ps_ir") else None,
        "program": prog,
        "program_attrs": prog_attrs,
        "counterexamples": ces,
        # Arc4-S2: the structural-verdict facts (compute_structural_facts)
        # and any minted Rejection provenance (ps_structural_reject rule) —
        # mechanical read-back only, the DECISION lives in seed rules.
        "structural": {
            "computed": at.get("ps_st_computed"),
            "any_fired": at.get("ps_st_any_fired"),
            "fired_detectors": [_text(x) for x in
                               (_plain(at.get("ps_st_fired_detectors")) or [])],
            "free_vars": [_text(x) for x in
                         (_plain(at.get("ps_st_free_vars")) or [])],
            "varying_unread_params": [_text(x) for x in
                (_plain(at.get("ps_st_varying_unread_params")) or [])],
            "reject": at.get("ps_structural_reject"),
            # Arc4-S6: how many times THIS goal was routed back into the
            # standing exclude/reproposal lane by a structural rejection
            # (ps_structural_reject_*_reopen) rather than straight to
            # 'gapped' -- mechanical read-back of the rule-minted counter,
            # never a decision.
            "reopen_count": at.get("ps_structural_reopen_count"),
        },
        # Arc6-D: the PropertyAtom verdict facts (compute_property_facts)
        # and any minted Rejection provenance (ps_property_reject_*/
        # ps_property_clear) -- mechanical read-back only, the DECISION
        # lives in seed rules. Sits beside `structural` above.
        "property": {
            "computed": at.get("ps_prop_computed"),
            "any_fired": at.get("ps_prop_any_fired"),
            "fired_properties": [_text(x) for x in
                                 (_plain(at.get("ps_prop_fired_properties")) or [])],
            "witnesses": json.loads(_text(at.get("ps_prop_witness_json")) or "[]"),
            "reject": at.get("ps_property_reject"),
            "reopen_count": at.get("ps_property_reopen_count"),
        },
        "rejections": rejections + [
            {k: _plain(v) for k, v in sub.node(rej)["attrs"].items()}
            for rej in sub.neighbours(g, "has_property_rejection")
        ],
        "excluded": excluded,
    }


# --------------------------------------------------------------------------- #
#  small mechanical helpers (the documented tuple/bytes gotchas).
# --------------------------------------------------------------------------- #
def _text(v) -> Optional[str]:
    if v is None:
        return None
    if isinstance(v, bytes):
        return v.decode("utf-8", "replace")
    return str(v)


def _plain(v):
    if isinstance(v, (list, tuple)):
        return [_plain(x) for x in v]
    # SetLit/DictItems rung: a real Set/FrozenSet-valued program result is
    # now REACHABLE (SetMap/Intersect/Union as SynthEnumerate ops) where
    # before this rung it never was, so this JSON-safe "plain" flattener
    # never needed a case for it -- exactly the same class of latent gap
    # `_wire`/`_unwire` closed one boundary upstream (`inputs_json`/
    # `expected`). Converted via `sorted()` (mirrors `mbpp_endgame_
    # battery.py`'s own `_json_default` set-handling exactly), which is
    # EQUALITY-PRESERVING for any `_plain(a) == _plain(b)` comparison
    # site in this module (two equal sets sort to the same list; two
    # distinct sets never coincidentally sort equal for orderable
    # elements) -- never downgrades a genuine set-equality verdict to a
    # list-order-sensitive one.
    if isinstance(v, (set, frozenset)):
        try:
            return [_plain(x) for x in sorted(v)]
        except TypeError:
            return [_plain(x) for x in v]
    if isinstance(v, dict):
        return {_plain(k): _plain(x) for k, x in v.items()}
    if isinstance(v, bytes):
        return v.decode("utf-8", "replace")
    # CEILING_REASSESSMENT_2 rung: the SAME class of gap the SetLit/DictItems
    # rung already found and fixed for `set`/`frozenset` above (a
    # PyO3-boundary Python type this JSON-safe flattener had no case for,
    # because no program could ever return one before the DSL's exact-
    # division Rational path was reachable). `Value::Rational` (the DSL's
    # exact-fraction division result — CLAUDE.md's own "Rational(9,2) !=
    # 4.5" cost class, `ARC6_STRUCTURAL_CEILING.md` §7.2) realises at the
    # PyO3 boundary as Python's `fractions.Fraction`, and `json.dumps`
    # cannot serialize it — `TypeError: Object of type Fraction is not
    # JSON serializable`, live-reproduced on task 98's own search
    # (`Div(Prod(a), Count(a))` over `(8,2,3,-1,7)` is exactly `-336/5`, a
    # non-integer ratio the engine keeps EXACT). Converted via `float()`,
    # matching every downstream comparator in this module (`agree`/
    # `_row_cmp_ok`/`math.isclose`) which already expects a float and never
    # an exact-rational type — never a second, drifting numeric kind.
    if isinstance(v, Fraction):
        return float(v)
    return v


__all__ = [
    "ensure_program_synthesis", "ensure_construction_bigrams", "ingest_spec",
    "stamp_lattice", "splice_binding", "eval_and_record", "run_enumerate",
    "run_exact_family", "screen_construction",
    "build_descent", "derive_hole_rows", "spawn_subgoal", "fold_up",
    "ingest_counterexample", "record_trace",
    "compute_structural_facts",
    "read_off_accepted", "pump", "synthesize_from_request", "read_goal",
    "pp",
    "synth_enumerate_live",
]
