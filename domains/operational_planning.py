"""operational_planning — THE META-LAYER: the jabberwock PLANS + ORCHESTRATES its
OWN operational work from an arbitrary-length, multi-layer natural-language
instruction. This closes the four META-GAPS the probe (scripts/
jabberwock_plans_bulk_load.py) named:

  GAP 1  no instruction->plan faculty      -> parse_instruction (below)
  GAP 2  composer codebook has no ops      -> seeds/operational_capabilities.json
                                              + the capability_match Program
  GAP 3  self-improvement cycles are fixed -> a plan is COMMANDABLE (built per
                                              instruction, not a fixed cycle)
  GAP 4  no load->measure->judge->report   -> run_plan (the mechanical executor)
         orchestrator

WHAT IS GRAPH (the DECISIONS) vs BOUNDARY (the mechanics):

  * THE CLAUSE->CAPABILITY MATCH is a GRAPH DECISION — the seeded `capability_match`
    Argmax Program (seeds/operational_planning.json): it scores each
    OperationalCapability by the token-overlap between the clause's content tokens
    (the has_token neighbours of the clause node) and the capability's token_blob
    (Count of clause tokens found via StringIndexOf), and returns the best. This is
    the exact twin of control_kinds' classify_kind_family StringIndexOf-overlap
    Argmax — the sense/fix-selection shape. NO Python `if` maps a clause to a
    capability; the parser only reads the Argmax's pick + its score.

  * THE IF-THEN GUARD is a GRAPH DECISION — an authored cond Term
    (Gt(it.norm_salience, FixWorthPolicy.threshold)) evaluated in Rust at execution;
    the branch outcome is the Term's, not Python's. The threshold is stated POLICY
    (graph data). The stop guard is the seeded should_continue Program.

  * THE PLAN is GRAPH DATA — Plan / PlanStep nodes + has_step / next / substep /
    uses_capability / foreach_source edges. A plan TREE (sequence + for-each +
    if-then) is graph structure, walked by the executor.

  * THE EXECUTOR (run_plan) is a MECHANICAL enactor — the twin of
    world_adapter._enact_advance / issue_reopen._reopened_concern_pursue_advance: it
    walks the plan tree, dispatches each act step to its capability's bound boundary
    fn (a name-keyed registry lookup on binding_key — NOT a decision), evaluates each
    control step's graph cond/foreach Term, and threads a plan-context dict so a
    step's output feeds the next. It NEVER branches on graph state to decide the
    work — the WHICH-capability is the Argmax's, the WHETHER-branch is the cond
    Term's.

  * READING is COGNITION, not I/O — the ONLY I/O is the raw text -> a CHARACTER
    stream in the graph (domains/instruction_reading.char_stream). The WORDS EMERGE
    by RECOGNITION (segmentation-by-recognition: lexicon decode + forward_segmentation
    TP-troughs over the Char stream, whitespace a WEAK cue — a run-together
    'bulkload' still recovers [bulk, load]). The clause/control/coordination
    decisions over the recognised words are GRAPH TERMS (connective In-Terms + the
    verb-head boundary Term), NOT regex and NOT a whitespace .split(). This module
    holds NO `import re` and NO whitespace tokeniser.

  * THE CAPABILITY BINDINGS are BOUNDARY I/O — _CAPABILITY_REGISTRY maps a
    capability's binding_key to the EXISTING object capability fn (consume /
    where_does_load_time_go / should_continue / perceive_consumption_gaps / the gap
    drivers / ...). We register + call them; we do NOT reimplement them.

CONTROL-FLOW COVERAGE (implemented): SEQUENCE (next), FOR-EACH (foreach over a
graph-produced item set), IF-THEN (an authored graph cond Term). RESIDUALS (honest):
deeper (>2-level) nesting is parsed recursively but only exercised to 2 levels;
complex inter-step data dependencies beyond the threaded context dict; a genuinely
OOV joined span falls back to forward_segmentation's char-TP troughs whose quality is
bounded by the lexicon's char-bigram structure (whitespace consulted only as the
last-resort weak cue); if-ELSE and while/until are not yet control kinds; the
reflex-driven (tick-loop) executor variant is a documented residual (run_plan is the
direct executor). The capability_match content tokens still lean on a closed-class
STOP-WORD set (a small lexical constant, not a decision). donkey=0 (no LLM in the
recognition, the match, the plan, the guards, or the executor).
"""
from __future__ import annotations

import json
from typing import Any, Callable, Optional

from domains.reflective_faculty import _load_program, _agent_root_node, _ensure_seed_chain
from domains import instruction_reading as ir

# the EXISTING object capabilities — imported to BIND (not reimplement).
from domains import wikipedia_consumption as wc
from domains import dictionary_lexicon as dl
from domains import load_timing as lt
from domains import performance_self_improvement as psi
from domains import stopping_policy as sp
from domains import consumption_quality as cq
from domains import gap_prioritization as gp


# the seeds this faculty needs (idempotent load).
_OP_SEEDS = ("operational_capabilities", "operational_planning")

# a small, definitional wiki_local batch (the same spread the probe uses) — the WHICH
# for bulk_load; concepts come from each article.
TITLES = ["Photosynthesis", "Cryptography", "Volcano", "Glacier", "Antibiotic",
          "Mitochondrion", "Evolution", "Gravity", "Electron", "Enzyme",
          "Ecosystem", "Vaccine", "Photon", "Neuron", "Antibody", "Bacteria",
          "Virus", "Galaxy", "Earthquake", "Tsunami", "Compiler", "Database",
          "Algorithm", "Semiconductor"]
DEFAULT_LOAD = 6      # articles when the instruction names no N
_TEST_MAX_LOAD = None  # a test may cap the real load for speed (module-level knob)


# ---------------------------------------------------------------------------
# resolve — the duck-typing the sibling faculties use.
# ---------------------------------------------------------------------------
def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    ag_node = getattr(agent, "agent", None)
    if ag_node is None:
        ag_node = _agent_root_node(sub)
    return sub, native, ag_node


def _ensure_seed(agent) -> None:
    """Idempotently load the operational capability codebook + planning Programs."""
    sub, native, ag_node = _resolve(agent)
    if _load_program(sub, "capability_match") is not None:
        return
    _ensure_seed_chain(sub, native, ag_node, _OP_SEEDS)


# ===========================================================================
# THE CAPABILITY BINDINGS — boundary I/O. Each (agent, ctx) -> dict CALLS the
# EXISTING object capability and threads its result through the plan-context dict.
# NO agent decision here — mechanical invocation + a graph read-back.
# ===========================================================================
def _cap_bulk_load(agent, ctx: dict) -> dict:
    n = int(ctx.get("n_articles_requested") or DEFAULT_LOAD)
    cap = _TEST_MAX_LOAD if _TEST_MAX_LOAD is not None else len(TITLES)
    n = max(1, min(n, cap, len(TITLES)))
    timer = lt.LoadTimer(agent)
    res = wc.consume(agent, titles=TITLES[:n], timing=timer, warm=True, quality=True)
    ctx["timer"] = timer
    ctx["load"] = res
    consumed = sum(1 for r in res["results"] if r["consumed"])
    return {"requested": n, "n_articles": res["n_articles"], "consumed": consumed,
            "admitted": res["admitted_total"]}


def _cap_warm(agent, ctx: dict) -> dict:
    ms = dl.warm_wordnet("en")
    return {"warm_ms": ms}


def _cap_measure_timing(agent, ctx: dict) -> dict:
    rep = lt.where_does_load_time_go(agent)
    ctx["timing"] = rep
    return {"cold": rep.get("cold"), "warm": rep.get("warm"),
            "dominant_stage": rep.get("dominant_stage")}


def _cap_judge_sufficiency(agent, ctx: dict) -> dict:
    # judge_sufficiency ENTAILS measure_timing: it reads where the load time goes
    # (the agent's own introspection) THEN produces the sufficiency verdict via the
    # agent's OWN stopping Program (should_continue) — this single step covers the
    # "measure timing + judge sufficiency" the instruction's clause names.
    rep = lt.where_does_load_time_go(agent)
    ctx["timing"] = rep
    pg = psi.perceive_performance_gap(agent, mint=True)
    cont = sp.should_continue(agent)
    thr = sp.sufficiency_threshold(agent)
    sufficient = not cont
    return {"timing_text": rep.get("text"), "cold": rep.get("cold"),
            "warm": rep.get("warm"), "dominant_stage": rep.get("dominant_stage"),
            "performance_gap": pg.get("gap"), "threshold": thr,
            "should_continue": cont, "sufficient": sufficient,
            "verdict": ("SUFFICIENT (below threshold)" if sufficient
                        else "LIVE GAP (above threshold)")}


def _cap_perceive_gaps(agent, ctx: dict) -> dict:
    # DRIVERED gaps (efficiency + understanding — carry kind+salience+a driver) for a
    # downstream fix loop, PLUS the probe-style consumption gaps for the "other object
    # gaps" report. Both are perceived by the agent's OWN graph collapse (donkey=0).
    agenda = gp.perceive_gaps(agent)
    gp.normalize_all(agent, agenda)
    ctx["gaps"] = agenda
    cg = cq.perceive_consumption_gaps(agent, mint=True)
    cons = cg.get("gaps") or []
    ctx["consumption_gaps"] = cons
    return {"gaps": [str(g) for g in agenda], "n_gaps": len(agenda),
            "consumption_gaps": [str(g) for g in cons], "n_consumption": len(cons),
            "consumption_residual": cg.get("residual")}


def _cap_prioritize(agent, ctx: dict) -> dict:
    agenda = ctx.get("gaps") or gp.perceive_gaps(agent)
    order = gp.prioritize(agent, agenda)
    ctx["order"] = order
    return {"order": [str(g) for g in order], "n": len(order),
            "view": gp.order_view(agent, order)}


def _cap_fix(agent, ctx: dict) -> dict:
    # fix the CURRENT foreach item (ctx['it']) if inside a foreach; else every gap.
    item = ctx.get("it")
    targets = [item] if item is not None else list(ctx.get("gaps") or [])
    recs = []
    for g in targets:
        kind = agent.s.node(g)["attrs"].get("kind")
        driver = gp._DRIVER_REGISTRY.get(kind)   # name-keyed lookup, not a decision
        if driver is None:
            recs.append({"gap": str(g), "kind": kind, "fixed": False,
                         "note": "no driver registered for this gap kind"})
            continue
        rec = driver(agent, g)                    # diagnose->select->#2->apply (graph)
        recs.append({"gap": str(g), "kind": kind, "fixed": bool(rec.get("accepted")),
                     "fix": rec.get("fix")})
    ctx.setdefault("fixed_records", []).extend(recs)
    return {"records": recs, "n_fixed": sum(1 for r in recs if r.get("fixed"))}


def _cap_report(agent, ctx: dict) -> dict:
    fr = ctx.get("fixed_records") or []
    n_fixed = sum(1 for r in fr if r.get("fixed"))
    return {"n_considered": len(fr), "n_fixed": n_fixed,
            "records": fr, "summary": f"{n_fixed} of {len(fr)} gaps fixed"}


def _cap_stop(agent, ctx: dict) -> dict:
    cont = sp.should_continue(agent)     # the agent's OWN stopping Program (graph)
    return {"should_continue": cont, "stopped": (not cont),
            "threshold": sp.sufficiency_threshold(agent)}


_CAPABILITY_REGISTRY: dict[str, Callable[[Any, dict], dict]] = {
    "bulk_load": _cap_bulk_load,
    "warm": _cap_warm,
    "measure_timing": _cap_measure_timing,
    "judge_sufficiency": _cap_judge_sufficiency,
    "perceive_gaps": _cap_perceive_gaps,
    "prioritize": _cap_prioritize,
    "fix": _cap_fix,
    "report": _cap_report,
    "stop": _cap_stop,
}


# ===========================================================================
# THE CLAUSE->CAPABILITY MATCH — the GRAPH DECISION (capability_match Argmax).
# Mint the clause + its content-token nodes (segmentation boundary I/O), then
# evaluate the seeded Argmax Program to pick the capability + read its score.
# ===========================================================================
_STOP_WORDS = {
    "the", "a", "an", "of", "to", "and", "or", "is", "it", "its", "are", "be",
    "do", "does", "did", "if", "then", "there", "this", "that", "you", "your",
    "how", "when", "on", "in", "for", "each", "with", "as", "so", "we", "i",
    "was", "were", "will", "would", "can", "could", "should", "many", "much",
    "rest", "them", "they", "he", "she", "at", "by", "up", "out", "no", "not",
}


def _content_tokens(words: list[str]) -> list[str]:
    """The clause's content tokens: the RECOGNISED words (from segmentation-by-
    recognition) minus the closed-class stop words, deduped in order. NO whitespace
    split, NO regex — the words already emerged from the char-stream recogniser."""
    out: list[str] = []
    seen: set = set()
    for w in words:
        w = (w or "").lower()
        if not w or w in _STOP_WORDS or w in seen:
            continue
        seen.add(w)
        out.append(w)
    return out


def _mint_clause(agent, content: list[str]) -> tuple[Any, list[str]]:
    """Mint the PlanClause + one PlanClauseToken per content token, PLUS a HEAD-BOOST:
    the clause's leading token (the imperative VERB head — the primary intent signal)
    is minted a second time so a two-way overlap tie breaks toward the head's
    capability (e.g. 'report ... which gaps ...' -> report, not perceive_gaps). The
    match remains the graph Argmax's; this only weights the head token in the bag."""
    sub, native, _ = _resolve(agent)
    cl = sub.add_node("PlanClause", {"text": " ".join(content)})
    for w in content:
        t = sub.add_node("PlanClauseToken", {"word": w})
        native.add_edge_unchecked(cl, "has_token", t)
    if content:
        h = sub.add_node("PlanClauseToken", {"word": content[0]})
        native.add_edge_unchecked(cl, "has_token", h)
    return cl, content


def match_capability(agent, text: Optional[str] = None, *,
                     words: Optional[list[str]] = None) -> dict:
    """MATCH a clause to an OperationalCapability — the GRAPH DECISION. Segment the
    clause into recognised words (unless `words` is supplied pre-recognised), mint the
    clause + its content-token nodes, evaluate the seeded `capability_match` Argmax
    Program (env `cl`), and read the pick + its overlap score (via
    `capability_match_score`). Returns {capability(node), name, binding_key, score,
    tokens, clause(node)}. `name`/`binding_key` are None when the best overlap is
    zero (an honest no-match residual). The WHICH is the Argmax's; Python only reads
    the pick + threshold-reads the score (a mechanical 0/n boolean, the should_continue
    twin) — no Python maps clause->capability."""
    _ensure_seed(agent)
    sub, native, _ = _resolve(agent)
    if words is None:
        words = ir.segment(agent, text or "")["words"]
    content = _content_tokens(words)
    cl, toks = _mint_clause(agent, content)
    prog = _load_program(sub, "capability_match")
    score_prog = _load_program(sub, "capability_match_score")
    if prog is None:
        return {"capability": None, "name": None, "binding_key": None,
                "score": 0, "tokens": toks, "clause": cl}
    pick = native.evaluate(prog, {"cl": cl})
    if pick is None:
        return {"capability": None, "name": None, "binding_key": None,
                "score": 0, "tokens": toks, "clause": cl}
    try:
        score = int(native.evaluate(score_prog, {"cl": cl, "cap": pick}) or 0)
    except Exception:
        score = 0
    at = sub.node(pick)["attrs"]
    if score < 1:
        # the Argmax always returns SOME capability; a zero overlap is no real match.
        return {"capability": None, "name": None, "binding_key": None,
                "score": score, "tokens": toks, "clause": cl}
    return {"capability": pick, "name": at.get("name"),
            "binding_key": at.get("binding_key"), "score": score,
            "tokens": toks, "clause": cl}


# ===========================================================================
# CONDITION AUTHORING — build a graph cond Term from an if-clause's phrase. This is
# AUTHORING graph data (the twin of the _compose_*_rule builders that assemble Rule
# JSON), NOT a decision over graph state: the branch OUTCOME is the Term's Rust
# evaluation at execution time. env var `it` = the current foreach item.
# ===========================================================================
def _authored_cond_term(phrase: str) -> Optional[dict]:
    """A graph predicate Term for an if-clause. 'worth fixing' / 'salient' -> the
    gap's norm_salience clears the FixWorthPolicy threshold (both reads in-graph).
    Returns None (with cond_program handled by the caller) for a should_continue-style
    'sufficient' guard."""
    p = (phrase or "").lower()
    if "worth" in p or "salien" in p or "fix" in p or "big" in p:
        return {"type": "Gt",
                "a": {"type": "Attr", "node": {"type": "Var", "name": "it"},
                      "key": "norm_salience"},
                "b": {"type": "Attr", "key": "threshold",
                      "node": {"type": "Argmin",
                               "source": {"type": "NodesOfType", "node_type": "FixWorthPolicy"},
                               "var_name": "pp",
                               "value": {"type": "Attr", "node": {"type": "Var", "name": "pp"},
                                         "key": "priority"},
                               "default": None}}}
    return None


def _cond_program_for(phrase: str) -> Optional[str]:
    """A named graph Program for a guard the authored Term doesn't cover: a
    'sufficient / enough' guard -> should_continue (the seeded stopping Program)."""
    p = (phrase or "").lower()
    if "suffic" in p or "enough" in p:
        return "should_continue"
    return None


# ===========================================================================
# THE PARSER — parse_instruction(agent, text) -> a PLAN GRAPH. RECOGNISE the
# instruction into words (segmentation-by-recognition, domains/instruction_reading);
# split into sentences/clauses over the RECOGNISED tokens (graph connective matches +
# the graph verb-head boundary Term — NO regex, NO whitespace delimiter); match each
# clause to a capability (the graph Argmax); nest for-each / if-then into a plan TREE.
# ===========================================================================
_TERMINALS = frozenset(".!?")
_DISCOURSE = frozenset({"then", "next", "first", "finally", "also"})
_IF_CONNECTIVES = frozenset({"if", "when"})
_COND_DELIMS = frozenset({",", "then"})


def _is_word(tok, text: str) -> bool:
    return tok.kind == "word" and tok.text == text


def _first_word(toks: list) -> Optional[Any]:
    for t in toks:
        if t.kind == "word":
            return t
    return None


def _clause_str(toks: list) -> str:
    """The clause's surface (recognised word texts joined) — for the `clause` attr /
    views. Display only; matching uses the recognised word list directly."""
    return " ".join(t.text for t in toks if t.kind == "word")


def _words_of(toks: list) -> list[str]:
    return [t.text for t in toks if t.kind == "word"]


def _split_on(toks: list, seps: frozenset) -> list[list]:
    """Split a token list on the given PUNCT-mark separators (';' / '.' / …).
    Mechanical structural split on hard marks — punctuation, never whitespace."""
    out: list[list] = []
    cur: list = []
    for t in toks:
        if t.kind == "punct" and t.text in seps:
            out.append(cur); cur = []
        else:
            cur.append(t)
    out.append(cur)
    return [seg for seg in out]


def _strip_discourse(agent, toks: list) -> list:
    """Drop a LEADING discourse-marker word (then/next/first/finally/also) + a
    following comma. The membership test is the graph connective In-Term."""
    i = 0
    while i < len(toks) and toks[i].kind == "word" and \
            ir.word_in(agent, toks[i], _DISCOURSE):
        i += 1
        if i < len(toks) and toks[i].kind == "punct" and toks[i].text == ",":
            i += 1
    return toks[i:]


def _find_foreach(agent, toks: list) -> Optional[tuple]:
    """Locate a for-each control: a 'for' word immediately followed by 'each'.
    Returns (subject_toks, body_toks) or None. Subject = words after 'each' up to the
    first comma; body = the rest. Connective recognition is the graph In-Term."""
    for i in range(len(toks) - 1):
        if toks[i].kind == "word" and ir.word_in(agent, toks[i], frozenset({"for"})) \
                and toks[i + 1].kind == "word" \
                and ir.word_in(agent, toks[i + 1], frozenset({"each"})):
            after = toks[i + 2:]
            # subject up to first comma, body after it
            for k, t in enumerate(after):
                if t.kind == "punct" and t.text == ",":
                    return after[:k], after[k + 1:]
            return after, []
    return None


def _find_ifthen(agent, toks: list) -> Optional[tuple]:
    """Locate an if/when control WITH a cond/body delimiter (a comma or 'then').
    Returns (cond_toks, body_toks) or None. 'if it is sufficiently fast' with NO
    delimiter is NOT a control clause (stays a plain act). Recognition is graph
    In-Terms over the recognised words."""
    for i, t in enumerate(toks):
        if t.kind == "word" and ir.word_in(agent, t, _IF_CONNECTIVES):
            rest = toks[i + 1:]
            for k, r in enumerate(rest):
                is_comma = (r.kind == "punct" and r.text == ",")
                is_then = (r.kind == "word" and ir.word_in(agent, r, frozenset({"then"})))
                if is_comma or is_then:
                    return rest[:k], rest[k + 1:]
            return None
    return None


def _split_verb_headed_and(agent, toks: list) -> list[list]:
    """Split a coordinate segment on 'and' — but ONLY where the 'and' joins TWO
    VERB-HEADED clauses (the graph verb-head Term on each side's lead). So
    'Measure … and judge …' (both verb-headed) -> TWO clauses, while
    'report what was loaded and which gaps were fixed' (right side led by 'which',
    not verb-headed) stays ONE. THE boundary decision is the verb-head Term's."""
    and_idx = [i for i, t in enumerate(toks)
               if t.kind == "word" and ir.word_in(agent, t, frozenset({"and"}))]
    if not and_idx:
        return [toks]
    clauses: list[list] = []
    start = 0
    ai = 0
    while ai < len(and_idx):
        a = and_idx[ai]
        left = toks[start:a]
        nxt = and_idx[ai + 1] if ai + 1 < len(and_idx) else len(toks)
        right = toks[a + 1:nxt]
        left_lead = _first_word(left)
        right_lead = _first_word(right)
        both_verb = (left_lead is not None and right_lead is not None
                     and ir.is_verb_headed(left_lead.text)
                     and ir.is_verb_headed(right_lead.text))
        if both_verb:
            clauses.append(toks[start:a])
            start = a + 1
        ai += 1
    clauses.append(toks[start:])
    return [c for c in clauses if _first_word(c) is not None]


def _new_step(agent, kind: str, clause: str, order: int) -> Any:
    sub, _, _ = _resolve(agent)
    return sub.add_node("PlanStep", {"kind": kind, "clause": clause,
                                     "order": float(order)})


def _bind_capability(agent, step, words: list[str]) -> dict:
    """Run the graph match on the recognised words and wire
    step -uses_capability-> the picked capability + record binding_key/score."""
    sub, native, _ = _resolve(agent)
    m = match_capability(agent, words=words)
    if m["capability"] is not None:
        native.add_edge_unchecked(step, "uses_capability", m["capability"])
        sub.set_attr(step, "capability", m["name"])
        sub.set_attr(step, "binding_key", m["binding_key"])
    sub.set_attr(step, "match_score", float(m["score"]))
    return m


def _parse_segment(agent, toks: list, order: int) -> Optional[Any]:
    """Parse ONE segment (a recognised-token list) into a PlanStep, recursing into
    for-each / if-then bodies. Control kinds are recognised by graph connective
    In-Terms; the plain case is an imperative act matched by the capability Argmax."""
    sub, native, _ = _resolve(agent)
    if _first_word(toks) is None:
        return None
    clause = _clause_str(toks)

    lead = _first_word(toks)
    # STOP — a segment led by 'stop'.
    if lead is not None and ir.word_in(agent, lead, frozenset({"stop"})):
        step = _new_step(agent, "stop", clause, order)
        # cond phrase = the words after 'when' (if any), for the guard program.
        cond_words = _words_of(toks)
        cond_phrase = " ".join(cond_words)
        prog = _cond_program_for(cond_phrase) or "should_continue"
        sub.set_attr(step, "cond_program", prog)
        sub.set_attr(step, "cond_phrase", cond_phrase)
        _bind_capability(agent, step, ["stop"])
        return step

    # FOR-EACH — nesting control.
    fe = _find_foreach(agent, toks)
    if fe is not None:
        subject_toks, body_toks = fe
        step = _new_step(agent, "foreach", clause, order)
        src = match_capability(agent, words=_words_of(subject_toks))
        if src["capability"] is not None:
            native.add_edge_unchecked(step, "foreach_source", src["capability"])
            sub.set_attr(step, "over_binding_key", src["binding_key"])
        sub.set_attr(step, "foreach_key", "gaps")
        sub.set_attr(step, "foreach_subject", _clause_str(subject_toks))
        for child in _segments_to_steps(agent, body_toks):
            native.add_edge_unchecked(step, "substep", child)
        return step

    # IF-THEN — guarded control (needs a cond/body delimiter).
    it = _find_ifthen(agent, toks)
    if it is not None:
        cond_toks, body_toks = it
        cond_phrase = _clause_str(cond_toks)
        step = _new_step(agent, "ifthen", clause, order)
        term = _authored_cond_term(cond_phrase)
        prog = _cond_program_for(cond_phrase)
        if term is not None:
            sub.set_attr(step, "cond_term", json.dumps(term))
        if prog is not None:
            sub.set_attr(step, "cond_program", prog)
        sub.set_attr(step, "cond_phrase", cond_phrase)
        for child in _segments_to_steps(agent, body_toks):
            native.add_edge_unchecked(step, "substep", child)
        return step

    # plain imperative ACT
    step = _new_step(agent, "act", clause, order)
    _bind_capability(agent, step, _words_of(toks))
    return step


def _leads_with_control(agent, toks: list) -> bool:
    """Does this token list LEAD with a control clause (stop / for-each / if-then-
    with-delimiter)? A control that leads OWNS the rest of the clause — INCLUDING a
    ';' inside its body (NESTED 'For each …, diagnose it; if worth, fix') — so it must
    NOT be ';'-split at the top. A NON-leading ';' (capstone 'Measure …; if …') IS a
    coordinate separator. Recognised by the graph connective In-Terms + verb-head."""
    lead = _first_word(toks)
    if lead is None:
        return False
    if ir.word_in(agent, lead, frozenset({"stop"})):
        return True
    if ir.word_in(agent, lead, frozenset({"for"})) and _find_foreach(agent, toks):
        return True
    if ir.word_in(agent, lead, _IF_CONNECTIVES) and _find_ifthen(agent, toks):
        return True
    return False


def _steps_for_coord_segment(agent, seg: list, base: int) -> list:
    """One ';'-coordinate segment -> its steps. A control-leading segment is ONE step
    (body recurses); a plain segment is split on verb-headed 'and' into act clauses."""
    if _leads_with_control(agent, seg):
        s = _parse_segment(agent, seg, base)
        return [s] if s is not None else []
    out: list = []
    for clause in _split_verb_headed_and(agent, seg):
        s = _parse_segment(agent, clause, base + len(out))
        if s is not None:
            out.append(s)
    return out


def _segments_to_steps(agent, toks: list) -> list:
    """A body / sentence -> its ordered PlanSteps. If the whole list LEADS with a
    control clause, it is ONE step (foreach/ifthen/stop own the rest, incl. any ';' in
    their body). Otherwise split on ';' coordinate marks and expand each segment
    (control-leading -> one step; else verb-headed-'and' split). All boundaries are
    graph decisions (connective In-Terms + the verb-head Term), none regex/whitespace."""
    if _leads_with_control(agent, toks):
        s = _parse_segment(agent, toks, 0)
        return [s] if s is not None else []
    steps: list = []
    for seg in _split_on(toks, frozenset({";"})):
        if _first_word(seg) is None:
            continue
        steps.extend(_steps_for_coord_segment(agent, seg, len(steps)))
    return steps


def parse_instruction(agent, text: str) -> dict:
    """COMPREHEND an operational instruction into a PLAN GRAPH (fixes meta-gap 1 +
    arbitrary length + nesting), with cognition ALL THE WAY DOWN TO THE WORD. The ONLY
    I/O is the raw text -> a Char stream; the words EMERGE by recognition
    (domains/instruction_reading.segment: lexicon decode + forward_segmentation
    TP-troughs over the Char stream, whitespace a weak cue). Over the recognised
    tokens: split into sentences on terminal marks, strip discourse markers, split on
    ';' and verb-headed 'and' (the graph verb-head Term), recurse for-each / if-then
    bodies -> a plan TREE; match each act clause to an OperationalCapability by the
    `capability_match` graph Argmax; wire the ordered `has_step` roots + `next` chain.
    Returns {plan, steps, n_steps}. NO regex, NO whitespace delimiter."""
    _ensure_seed(agent)
    sub, native, ag_node = _resolve(agent)
    plan = sub.add_node("Plan", {"instruction": text})
    toks = ir.segment(agent, text)["tokens"]
    roots: list[Any] = []
    order = 0
    for sent in _split_on(toks, _TERMINALS):
        sent = _strip_discourse(agent, sent)
        if _first_word(sent) is None:
            continue
        for step in _segments_to_steps(agent, sent):
            if step is None:
                continue
            native.add_edge_unchecked(plan, "has_step", step)
            if roots:
                native.add_edge_unchecked(roots[-1], "next", step)
            roots.append(step)
            sub.set_attr(step, "order", float(order))
            order += 1
    sub.set_attr(plan, "n_steps", float(len(roots)))
    return {"plan": plan, "steps": roots, "n_steps": len(roots)}


# ===========================================================================
# THE ORCHESTRATOR — run_plan(agent, plan) — a MECHANICAL executor (the twin of
# _enact_advance / _reopened_concern_pursue_advance). Walk the plan tree in order;
# dispatch each act step to its capability's bound fn (registry lookup on
# binding_key), evaluate each control step's graph cond/foreach Term, thread the ctx.
# NO agent-decision branching in Python.
# ===========================================================================
def _run_act(agent, step, ctx: dict, trace: list) -> None:
    at = agent.s.node(step)["attrs"]
    bk = at.get("binding_key")
    fn = _CAPABILITY_REGISTRY.get(bk) if bk else None
    if fn is None:
        trace.append({"step": str(step), "kind": "act", "clause": at.get("clause"),
                      "capability": at.get("capability"), "executed": False,
                      "note": "no capability bound (comprehension/coverage residual)"})
        return
    out = fn(agent, ctx)
    trace.append({"step": str(step), "kind": "act", "clause": at.get("clause"),
                  "capability": at.get("capability"), "executed": True, "output": out})


def _eval_cond(agent, step, ctx: dict) -> Optional[bool]:
    """Evaluate a control step's GRAPH guard: the authored cond_term (Rust, env
    it=current foreach item) OR the named cond_program (e.g. should_continue). Returns
    the boolean the graph decided, or None if no guard. The executor READS it; the
    DECISION is the Term/Program's."""
    sub, native, _ = _resolve(agent)
    at = sub.node(step)["attrs"]
    ct_json = at.get("cond_term")
    if ct_json:
        env = {}
        it = ctx.get("it")
        if it is not None:
            env["it"] = it
        try:
            return bool(native.evaluate(json.loads(ct_json), env))
        except Exception:
            return None
    prog_name = at.get("cond_program")
    if prog_name == "should_continue":
        return sp.should_continue(agent)
    if prog_name:
        prog = _load_program(sub, prog_name)
        if prog is not None:
            try:
                return bool(native.evaluate(prog, {}))
            except Exception:
                return None
    return None


def _run_step(agent, step, ctx: dict, trace: list, control: dict) -> None:
    sub, native, _ = _resolve(agent)
    at = sub.node(step)["attrs"]
    kind = at.get("kind")
    if kind == "act":
        _run_act(agent, step, ctx, trace)
        return
    if kind == "foreach":
        # produce the item set via the source capability (graph-picked), then iterate.
        bk = at.get("over_binding_key")
        fn = _CAPABILITY_REGISTRY.get(bk) if bk else None
        if fn is not None:
            fn(agent, ctx)
        key = at.get("foreach_key") or "gaps"
        items = list(ctx.get(key) or [])
        subs = native.neighbours(step, "substep")
        subs = sorted(subs, key=lambda n: sub.node(n)["attrs"].get("order", 0.0))
        rec = {"step": str(step), "kind": "foreach", "clause": at.get("clause"),
               "subject": at.get("foreach_subject"), "n_items": len(items),
               "iterations": []}
        for item in items:
            ctx["it"] = item
            it_trace: list = []
            for c in subs:
                _run_step(agent, c, ctx, it_trace, control)
            rec["iterations"].append({"item": str(item), "trace": it_trace})
        ctx.pop("it", None)
        trace.append(rec)
        return
    if kind == "ifthen":
        cond = _eval_cond(agent, step, ctx)
        subs = native.neighbours(step, "substep")
        subs = sorted(subs, key=lambda n: sub.node(n)["attrs"].get("order", 0.0))
        taken = bool(cond)
        sub_trace: list = []
        if taken:
            for c in subs:
                _run_step(agent, c, ctx, sub_trace, control)
        trace.append({"step": str(step), "kind": "ifthen", "clause": at.get("clause"),
                      "cond_phrase": at.get("cond_phrase"), "cond": cond,
                      "branch_taken": taken, "trace": sub_trace})
        return
    if kind == "stop":
        cond = _eval_cond(agent, step, ctx)   # should_continue
        stopped = (cond is False)
        control["stopped"] = control.get("stopped") or stopped
        _run_act(agent, step, ctx, trace) if at.get("binding_key") else None
        trace.append({"step": str(step), "kind": "stop", "clause": at.get("clause"),
                      "should_continue": cond, "stopped": stopped})
        return
    # unknown kind — honest no-op
    trace.append({"step": str(step), "kind": kind, "executed": False,
                  "note": "unknown step kind"})


def run_plan(agent, parsed: dict, *, max_load: Optional[int] = None) -> dict:
    """EXECUTE a parsed plan (fixes meta-gaps 3+4) — the MECHANICAL orchestrator. Walk
    the ordered root steps; for each, dispatch an act to its capability's bound fn
    (registry lookup on binding_key), iterate a for-each over its graph-produced item
    set, branch an if-then on its graph cond Term, or read the stop guard — threading a
    plan-context dict so a step's output feeds the next. Returns {trace, ctx, stopped}.
    NO Python decides the work: the WHICH-capability was the parse-time Argmax, the
    WHETHER-branch is the cond Term's Rust eval; this only sequences + dispatches +
    reads (the _enact_advance precedent)."""
    global _TEST_MAX_LOAD
    if max_load is not None:
        _TEST_MAX_LOAD = max_load
    ctx: dict = {}
    trace: list = []
    control: dict = {"stopped": False}
    try:
        steps = parsed.get("steps") or []
        for step in steps:
            if control.get("stopped"):
                break
            _run_step(agent, step, ctx, trace, control)
    finally:
        if max_load is not None:
            _TEST_MAX_LOAD = None
    return {"trace": trace, "ctx": ctx, "stopped": control.get("stopped", False)}


# ===========================================================================
# READ-BACK / VIEW — mechanical graph reads for the ledger + verbatim printing.
# ===========================================================================
def plan_view(agent, parsed: dict) -> str:
    """A printable, verbatim view of the plan GRAPH (nodes + edges), walking the tree."""
    sub, native, _ = _resolve(agent)
    plan = parsed["plan"]
    lines = [f"PLAN(instruction={sub.node(plan)['attrs'].get('instruction')!r}, "
             f"n_steps={int(sub.node(plan)['attrs'].get('n_steps') or 0)})"]

    def walk(step, depth):
        at = sub.node(step)["attrs"]
        pad = "  " * depth
        kind = at.get("kind")
        head = f"{pad}STEP[{int(at.get('order') or 0)}] kind={kind}"
        if kind == "act" or kind == "stop":
            head += (f" clause={at.get('clause')!r} -> capability="
                     f"{at.get('capability')} (binding_key={at.get('binding_key')}, "
                     f"score={at.get('match_score')})")
        if kind == "foreach":
            head += (f" subject={at.get('foreach_subject')!r} -> source_capability="
                     f"{at.get('over_binding_key')} (foreach_key={at.get('foreach_key')})")
        if kind == "ifthen":
            head += (f" cond_phrase={at.get('cond_phrase')!r} "
                     f"cond_term={'yes' if at.get('cond_term') else at.get('cond_program')}")
        lines.append(head)
        subs = native.neighbours(step, "substep")
        subs = sorted(subs, key=lambda n: sub.node(n)["attrs"].get("order", 0.0))
        for c in subs:
            walk(c, depth + 1)

    for step in parsed["steps"]:
        walk(step, 1)
    return "\n".join(lines)


def trace_view(trace: list, depth: int = 0) -> str:
    """A printable, verbatim view of an execution trace."""
    pad = "  " * depth
    lines = []
    for rec in trace:
        kind = rec.get("kind")
        if kind == "act":
            ex = "EXECUTED" if rec.get("executed") else "SKIPPED"
            lines.append(f"{pad}[{ex}] act {rec.get('clause')!r} -> "
                         f"{rec.get('capability')}")
            if rec.get("output") is not None:
                lines.append(f"{pad}   output={rec.get('output')}")
            if rec.get("note"):
                lines.append(f"{pad}   note={rec.get('note')}")
        elif kind == "foreach":
            lines.append(f"{pad}[FOREACH] {rec.get('clause')!r}  subject="
                         f"{rec.get('subject')!r}  n_items={rec.get('n_items')}")
            for it in rec.get("iterations", []):
                lines.append(f"{pad}  ITEM {it['item']}:")
                lines.append(trace_view(it["trace"], depth + 2))
        elif kind == "ifthen":
            lines.append(f"{pad}[IF cond={rec.get('cond')} -> "
                         f"branch_taken={rec.get('branch_taken')}] {rec.get('clause')!r}")
            if rec.get("trace"):
                lines.append(trace_view(rec["trace"], depth + 1))
        elif kind == "stop":
            lines.append(f"{pad}[STOP should_continue={rec.get('should_continue')} "
                         f"stopped={rec.get('stopped')}] {rec.get('clause')!r}")
        else:
            lines.append(f"{pad}[{kind}] {rec}")
    return "\n".join(l for l in lines if l.strip())


__all__ = [
    "parse_instruction", "run_plan", "match_capability", "plan_view", "trace_view",
    "_CAPABILITY_REGISTRY", "TITLES",
]
