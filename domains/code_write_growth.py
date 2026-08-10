"""code_write_growth — CODE-4: THE AGENT GROWS ITS OWN WRITE-CODEBOOK.

CODE-1 made code a READ register with a mintable codebook. CODE-2 made
understanding = prediction. CODE-3 made writing reading-reversed, from a
SMALL, hand-authored `code_write_constructions.json` starter vocabulary --
"a request outside the small starter vocabulary ... abstains honestly ...
growing the vocabulary is CODE-4's, not silently approximated here."

CODE-4 hands that growth to the agent itself. An out-of-vocabulary write
request no longer just abstains -- `world_adapter._write_function_reply`
records a mechanical outcome datum, `seeds/code_write_gap.json`'s
`note_code_write_gap` rule DECIDES that's a capability gap and files a
`SelfConcern{kind:'code_write'}` (the gap_awareness precedent, zero new
plumbing for surfacing/promotion). THIS module supplies the two sanctioned
ways the gap closes -- both by WIDENING `seeds/code_write_constructions.json`
via `teach()` (the cue-adoption precedent: adoption = teach(), revert =
remove the node), never by a Python if/elif over request text:

  1. TEACH BY EXAMPLE (`teach_write_shape_from_example`) -- the DEEPEST
     close: a human pastes a real, runnable example function in chat. The
     agent READS it (`code_reading.read_function`, the SAME faculty CODE-1/2
     already use on its own repo) -- the read Term + args + desc BECOME the
     new write construction, with trigger tokens taken from the ORIGINAL
     unresolved request's own content words (so the taught shape answers the
     SAME request that filed the gap). Reading closes the write gap: this is
     "writing is reading reversed" one level up -- now the WRITE CODEBOOK
     ITSELF is grown by a read.

  2. COMPOSE FROM PREDICATION (`compose_write_shape_from_predication`) -- a
     narrower, example-free close for a SMALL closed family: a request whose
     predicate is a held morphological multiplier/offset word
     (`seeds/write_shape_predication.json` -- "doubles" stems to "double",
     which resolves to Concept{multiplier_factor:2}) composes an arithmetic
     Term (`Times(Var(arg), Lit(factor))` / `Plus(Var(arg), Lit(delta))`)
     from vocabulary CODE-1/2 already hold. Outside that small family this
     HONESTLY EXHAUSTS ({ok: False, reason: "composition exhausted: ..."}) --
     the documented CODE-4 boundary: general English-predicate-to-Term
     synthesis is NOT attempted here; the teach-by-example path is the
     general close.

Both paths VALIDATE before adoption (`validate_written_function_by_running`,
item 5 of the CODE-4 spec): the candidate Term is rendered as a real function
and EXEC'd on sample inputs, checked against the SAME Term's own native
evaluation (`native.evaluate`) -- the agent validates its new ability by
prediction, agreeing with itself, before teaching it.

`ground_identifier_words` closes the CODE-4 identifier-grounding item: a
read/written function's identifier words (case-split via
`code_reading._split_identifier`, unchanged) are run through the EXISTING
teacher chain (`WorldAdapter.ground_unknowns`) -- previously a dead end (no
caller ever did this), now wired so an unknown identifier word is queued for
grounding/inquiry exactly like any other unknown word in a message.

ARCHITECTURE (CLAUDE.md): the only DECISIONS here are (a) whether a
predicate resolves in the held vocabulary (a graph lookup, not a branch over
meaning) and (b) whether the two Terms/execs AGREE (a boolean comparison of
two already-computed values) -- everything else is text prep, calls into the
existing read/write/render faculties, and `teach()`.
"""
from __future__ import annotations

import ast
import json
from typing import Any, Optional

from domains import code_reading as cdr
from domains import code_writing as cw
from domains.teach import teach


# --------------------------------------------------------------------------- #
#  THIN I/O-BOUNDARY CLASSIFIER — "is this chat message a Python function
#  example?" Mechanical (ast.parse + a FunctionDef walk); never decides WHAT
#  the function means (code_reading's job, downstream). Same legal status as
#  code_writing.looks_like_write_request (CLAUDE.md's own carve-out).
# --------------------------------------------------------------------------- #
def looks_like_code_example(text: str) -> bool:
    if not text or "def " not in text:
        return False
    stripped = text.strip()
    tree = _try_parse(stripped)
    if tree is None:
        idx = stripped.find("def ")
        tree = _try_parse(stripped[idx:]) if idx >= 0 else None
    if tree is None:
        return False
    return any(isinstance(n, ast.FunctionDef) for n in ast.walk(tree))


def _try_parse(src: str):
    try:
        return ast.parse(src)
    except SyntaxError:
        return None


# --------------------------------------------------------------------------- #
#  IDENTIFIER GROUNDING — wires code_reading._split_identifier's word-split
#  into the EXISTING teacher chain (WorldAdapter.ground_unknowns), previously
#  a dead end: no caller ever passed identifier words through it.
# --------------------------------------------------------------------------- #
def ground_identifier_words(agent, names: list) -> list:
    """Case-split every name in `names` (`code_reading._split_identifier`,
    unchanged) and run the joined words through `agent.ground_unknowns` — the
    SAME per-word teacher I/O loop any other unknown word in a message goes
    through. Returns the words newly grounded (mirrors `ground_unknowns`'s
    own return). No-ops (returns []) when the agent carries no `_self_teacher`
    and no explicit teacher is supplied — `ground_unknowns`'s own contract."""
    ground = getattr(agent, "ground_unknowns", None)
    if ground is None or not names:
        return []
    words: list = []
    for nm in names:
        for w in cdr._split_identifier(nm):
            if w not in words:
                words.append(w)
    if not words:
        return []
    return ground(" ".join(words))


# --------------------------------------------------------------------------- #
#  VALIDATE BY RUNNING (item 5) — exec the candidate function in ISOLATION,
#  compare against the agent's OWN model prediction (native evaluation of the
#  held Term). Agreement gates adoption/reply; never fabricated.
# --------------------------------------------------------------------------- #
def validate_written_function_by_running(source: str, name: str, args: list,
                                         sample_env: dict, expected: Any) -> dict:
    ns: dict = {}
    try:
        exec(source, ns)  # noqa: S102 -- isolated namespace, agent's own written source
    except Exception as e:  # noqa: BLE001
        return {"ran": False, "agree": False,
               "reason": "%s: %s" % (type(e).__name__, e)}
    fn = ns.get(name)
    if fn is None:
        return {"ran": False, "agree": False,
               "reason": "no %r in the exec'd namespace" % name}
    try:
        got = fn(*[sample_env[a] for a in args])
    except Exception as e:  # noqa: BLE001
        return {"ran": False, "agree": False,
               "reason": "%s: %s" % (type(e).__name__, e)}
    return {"ran": True, "agree": got == expected, "observed": got, "expected": expected}


# --------------------------------------------------------------------------- #
#  TRIGGER TOKENS — the taught/composed shape's signature. From the ORIGINAL
#  unresolved request's own content words when we have one (so the new shape
#  answers the SAME request that filed the gap); else from the function's own
#  name, case-split (the read-side identifier tokenisation, reused).
# --------------------------------------------------------------------------- #
def _trigger_tokens(request_text: Optional[str], func_name: str, agent=None) -> list:
    if request_text:
        toks = cw._content_tokens(request_text, agent)
        if toks:
            return toks
    return [w.upper() for w in cdr._split_identifier(func_name)]


def _teach_shape(agent, *, shape_name: str, tokens: list, desc: str,
                 term: dict, args: list, taught_from: str,
                 taught_for: Optional[str] = None,
                 lesson_source: Optional[str] = None,
                 seeds_dir=None) -> dict:
    ground_template = {"desc": desc, "term": term, "args": list(args), "mode": "code_write"}
    attrs = {
        "name": shape_name,
        "kind": "code_write_construction",
        # CODE-CURRICULUM finding: every PRE-EXISTING code_write_construction
        # (seeds/code_write_constructions.json) stores its signature as ONE
        # TOKEN PER PART (e.g. [["LARGER"]]) -- the SAME convention
        # compose_function_from_request's own skeleton build uses for a
        # REQUEST's tokens (`[[t] for t in tokens]`). `json.dumps([tokens])`
        # instead packed EVERY trigger token into a SINGLE part -- invisible
        # while every taught/gate example reduced to exactly one content
        # word ('doubles', 'triples', ...), but a taught shape whose content
        # genuinely spans 2+ tokens (e.g. 'is_divisible' -> IS, DIVISIBLE)
        # could never be matched by ANY later request through the SAME
        # decode path. Fixed to the established one-token-per-part shape.
        "signature": json.dumps([[t] for t in tokens]),
        "ground_template": json.dumps(ground_template),
        "taught_from": taught_from,
    }
    if taught_for:
        # PROVENANCE the resolve_code_write_gap rule reads: this shape was
        # taught FOR that exact request text, so the rule (not Python) can
        # decide the matching code_write SelfConcern is now closed.
        attrs["taught_for"] = taught_for
    if lesson_source:
        # CODE-CURRICULUM (part C): PROVENANCE for a shape learned by
        # reading a PUBLISHED lesson document rather than a hand-pasted
        # chat example -- a mechanical datum copied onto the taught node
        # (never a decision), read back by domains.code_curriculum's
        # capability report / self-account so the agent can name WHERE a
        # shape came from.
        attrs["lesson_source"] = lesson_source
    kwargs = {"category": "code_write_constructions"}
    if seeds_dir is not None:
        kwargs["seeds_dir"] = seeds_dir
    # CURRICULUM WAVE 1, REOPEN SIGNAL: check LIVE-GRAPH novelty BEFORE
    # calling teach() -- teach()'s own `saved` return means "written to the
    # seed FILE", which is unconditionally False whenever
    # OZMA_SEED_PERSIST_DISABLED is set (the convention every measurement /
    # test / curriculum run in this repo already uses), so it is the WRONG
    # signal for "did the agent's live capability set grow". A ShapeSignature
    # already present in the live graph under this exact `name` means this is
    # a re-teach (not new); its absence beforehand, followed by teach()'s
    # unconditional live `agent.s.add_node` (step 1, always runs regardless
    # of persistence), means genuine growth.
    _sub2, _native2, ag2 = cdr._resolve(agent)
    already_held = any(
        _sub2.node(n)["attrs"].get("name") == shape_name
        for n in _sub2.nodes("ShapeSignature"))
    result = teach(agent, "ShapeSignature", attrs, **kwargs)
    if not already_held:
        # A dedicated `write_codebook_epoch` counter on the Agent node -- the
        # SAME mechanical "Python builder bumps an epoch" idiom
        # `grow_part_library` uses for `agent.codebook_epoch`
        # (seeds/shape_decode_loop.json's sd_redecode), kept as its OWN
        # counter (not the shared dynamic-quantization one) so this bump
        # never perturbs the unrelated shape-decode re-arm loop. A seed rule
        # (seeds/curriculum_study.json) reads this counter to re-arm a
        # blocked StudyLesson for re-attempt -- no Python decision, just the
        # fact that growth happened.
        cur_epoch = _sub2.node(ag2)["attrs"].get("write_codebook_epoch", 0) or 0
        _sub2.set_attr(ag2, "write_codebook_epoch", cur_epoch + 1)
    return result


# --------------------------------------------------------------------------- #
#  PATH 1 — TEACH BY EXAMPLE. Reading closes the write gap.
# --------------------------------------------------------------------------- #
def teach_write_shape_from_example(agent, example_source: str, *,
                                   request_text: Optional[str] = None,
                                   func_name: Optional[str] = None,
                                   seeds_dir=None,
                                   lesson_source: Optional[str] = None) -> dict:
    """READ a human-supplied example function (code_reading.read_function --
    the SAME faculty CODE-1/2 read the agent's own repo with), VALIDATE its
    Term by running (item 5), then TEACH it as a new code_write_construction
    ShapeSignature (adoption = teach(), the cue-adoption precedent). Returns
    {ok, shape, tokens, reading, validate, teach} or an honest {ok: False,
    reason} at whichever step didn't clear (never a fabricated shape).

    `lesson_source` (CODE-CURRICULUM, part C, additive): when the example
    came from a PUBLISHED document region rather than a chat-pasted example,
    the caller passes a provenance string (e.g. the lesson's file/URL) that
    is carried onto the taught ShapeSignature verbatim -- the SAME teach()
    path, just with one more mechanical fact attached."""
    reading = cdr.read_function(agent, example_source, func_name)
    if reading.get("term") is None:
        return {"ok": False, "reason": reading.get("emit_error") or reading.get("note")
                                        or "read gave no emittable Term",
               "reading": reading}
    term = reading["term"]
    args = list(reading["args"])
    desc = reading.get("what_does") or ("computed by %s" % reading["name"])

    _sub, native, _ag = cdr._resolve(agent)
    sample_env = cw._sample_env(args)
    try:
        model_result = native.evaluate(term, sample_env)
    except Exception as e:  # noqa: BLE001
        return {"ok": False,
               "reason": "held Term does not evaluate: %s: %s" % (type(e).__name__, e),
               "reading": reading}

    written_source = cw.write_function(agent, reading["name"], args, term)
    check = validate_written_function_by_running(
        written_source, reading["name"], args, sample_env, model_result)
    if not check["agree"]:
        return {"ok": False,
               "reason": "validate-by-running disagreement: %r" % (check,),
               "reading": reading, "written_source": written_source, "validate": check}

    # IDENTIFIER GROUNDING (item 4): the example's own arg names + function
    # name are unknown identifier words worth grounding through the teacher
    # chain, exactly like any other unknown word.
    ground_identifier_words(agent, [reading["name"]] + args)

    tokens = _trigger_tokens(request_text, reading["name"], agent)
    shape_name = "taught_%s" % reading["name"]
    result = _teach_shape(agent, shape_name=shape_name, tokens=tokens, desc=desc,
                          term=term, args=args, taught_from="example",
                          taught_for=request_text, lesson_source=lesson_source,
                          seeds_dir=seeds_dir)
    return {"ok": True, "shape": shape_name, "tokens": tokens, "reading": reading,
           "written_source": written_source, "validate": check, "teach": result}


# --------------------------------------------------------------------------- #
#  PATH 2 — COMPOSE FROM PREDICATION. A small closed morphological family;
#  outside it, an HONEST exhausted trail (never a fabricated Term).
# --------------------------------------------------------------------------- #
def _stem(word: str) -> list:
    """Mechanical morphological candidates for a content word: the word
    itself, and (if it ends in 's') the word with the trailing 's' stripped
    ('doubles' -> 'double') -- a fixed text-prep step, the same status
    ast_to_term's fixed maps have, never a decision about MEANING."""
    w = word.lower()
    cands = [w]
    if w.endswith("s") and len(w) > 1:
        cands.append(w[:-1])
    return cands


def _predication_concept(sub, word: str) -> Optional[dict]:
    for cand in _stem(word):
        for n in sub.nodes("Concept"):
            at = sub.node(n)["attrs"]
            if at.get("name") == cand and (
                    "multiplier_factor" in at or "offset_delta" in at):
                return dict(at)
    return None


def compose_write_shape_from_predication(agent, request_text: str, *,
                                         arg_name: str = "a",
                                         seeds_dir=None) -> dict:
    """Resolve `request_text`'s content-word predicate against the held
    morphological multiplier/offset vocabulary (`seeds/
    write_shape_predication.json`) and compose an arithmetic Term from
    ALREADY-HELD DSL vocabulary. Validates by running, then teaches (same
    contract as `teach_write_shape_from_example`). Outside the held small
    family: {ok: False, reason: "composition exhausted: ..."} — the honest
    boundary this path documents (general predicate-to-Term synthesis is the
    teach-by-example path's job, not this one's)."""
    sub, native, _ag = cdr._resolve(agent)
    tokens = cw._content_tokens(request_text, agent)
    if not tokens:
        return {"ok": False, "reason": "no content words in the request"}
    concept = None
    matched_token = None
    for t in tokens:
        concept = _predication_concept(sub, t)
        if concept is not None:
            matched_token = t
            break
    if concept is None:
        return {"ok": False,
               "reason": "composition exhausted: no held numeric/morphological "
                        "mapping for any of %r" % (tokens,),
               "tokens": tokens}

    args = [arg_name]
    if "multiplier_factor" in concept:
        factor = float(concept["multiplier_factor"])
        term = {"type": "Times", "items": [
            {"type": "Var", "name": arg_name}, {"type": "Lit", "value": factor}]}
        desc = "computes %s of a number" % concept.get("description", concept["name"])
    else:
        delta = float(concept["offset_delta"])
        term = {"type": "Plus", "items": [
            {"type": "Var", "name": arg_name}, {"type": "Lit", "value": delta}]}
        desc = "computes %s of a number" % concept.get("description", concept["name"])

    sample_env = cw._sample_env(args)
    try:
        model_result = native.evaluate(term, sample_env)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "reason": "composed Term does not evaluate: %s: %s"
                                       % (type(e).__name__, e)}
    written_source = cw.write_function(agent, "composed_function", args, term)
    check = validate_written_function_by_running(
        written_source, "composed_function", args, sample_env, model_result)
    if not check["agree"]:
        return {"ok": False, "reason": "validate-by-running disagreement: %r" % (check,),
               "written_source": written_source, "validate": check}

    shape_name = "composed_%s" % concept["name"]
    result = _teach_shape(agent, shape_name=shape_name, tokens=tokens, desc=desc,
                          term=term, args=args, taught_from="predication",
                          taught_for=request_text, seeds_dir=seeds_dir)
    return {"ok": True, "shape": shape_name, "tokens": tokens, "matched": matched_token,
           "term": term, "args": args, "validate": check, "teach": result}


# --------------------------------------------------------------------------- #
#  NL-PROMOTE — "Work on the doubles gap." The gap selection is a mechanical
#  content-word overlap read (the promote_self_concern content_words
#  precedent — daemon plumbing, not agent reasoning); WHETHER the gap closes
#  is the composer's own verdict (held-vocabulary resolution + validation);
#  THAT it closed is the resolve_code_write_gap rule's decision, reading the
#  taught shape's own taught_for provenance in the next run_rules pass.
# --------------------------------------------------------------------------- #
def work_on_code_write_gap(agent, nl_text: str, *, seeds_dir=None) -> dict:
    """The NL surface of the composition path: select the pending code_write
    SelfConcern whose content shares a content word with `nl_text` (word
    overlap, mechanical; latest wins on a tie — the recency precedent), then
    run `compose_write_shape_from_predication` on THE GAP'S OWN request
    content. On success the taught shape carries `taught_for=<the request>`,
    and the seeded `resolve_code_write_gap` rule marks the concern resolved
    in the agent's own next rule pass — never a Python status write here.
    On exhaustion: the honest exhausted trail, naming teach-by-example as
    the remaining sanctioned close."""
    gaps = pending_code_write_gaps(agent)
    if not gaps:
        return {"ok": False, "reason": "no pending code_write gaps"}
    words = {w.strip(".,?!;:()[]\"'").lower() for w in nl_text.split()} - {""}
    picked = None
    for g in gaps:  # latest matching wins (iteration is oldest->newest)
        gap_words = {w.strip(".,?!;:()[]\"'").lower()
                     for w in str(g.get("content", "")).split()}
        if words & gap_words:
            picked = g
    if picked is None:
        picked = gaps[-1]
    request_text = str(picked.get("content", ""))
    result = compose_write_shape_from_predication(agent, request_text,
                                                  seeds_dir=seeds_dir)
    result["gap_content"] = request_text
    if not result.get("ok"):
        result["reason"] = ("%s -- the remaining sanctioned close is "
                           "teach-by-example: paste a real example function "
                           "in chat and I will read it."
                           % result.get("reason", "composition failed"))
    return result


# --------------------------------------------------------------------------- #
#  GROWTH-RULE INSTALL (mechanical adapter I/O — mirrors code_writing.
#  ensure_write_codebook; for minimal boots that skipped load_all_seeds'
#  glob. A full boot already has seeds/code_write_gap.json installed.)
# --------------------------------------------------------------------------- #
def ensure_growth_rules(agent) -> None:
    sub, native, ag_node = cdr._resolve(agent)
    for n in sub.nodes("Seed"):
        if sub.node(n)["attrs"].get("id") == "code_write_gap":
            return
    import os
    from substrate.seed_loader import engine_rules_only
    path = os.path.join(cdr._ROOT, "seeds", "code_write_gap.json")
    with open(path) as f:
        manifest = json.load(f)
    native.load_seed_manifest(engine_rules_only(manifest), ag_node)
    sub.add_node("Seed", {"id": "code_write_gap",
                          "version": manifest.get("version", "1.0.0")})


# --------------------------------------------------------------------------- #
#  READ-CODEBOOK GROWTH RESIDUAL (item 2) — mechanical reader over the
#  low-priority naming gaps `note_code_read_naming_gap` files (never a
#  decision here; the rule already decided).
# --------------------------------------------------------------------------- #
def pending_naming_gaps(agent) -> list:
    sub = getattr(agent, "s", agent)
    inner = getattr(agent, "inner", None) or getattr(sub, "_inner", sub)
    ag_node = None
    for n in sub.nodes("Agent"):
        if not sub.node(n)["attrs"].get("is_class"):
            ag_node = n
            break
    if ag_node is None:
        return []
    out = []
    for sc in inner.neighbours(ag_node, "has_self_concern"):
        if not inner.has_node(sc):
            continue
        at = sub.node(sc)["attrs"]
        if at.get("kind") == "code_read_naming" and at.get("status") != "retired":
            out.append(at)
    return out


def pending_code_write_gaps(agent) -> list:
    """Mechanical reader: every held, un-retired code_write SelfConcern."""
    sub = getattr(agent, "s", agent)
    inner = getattr(agent, "inner", None) or getattr(sub, "_inner", sub)
    ag_node = None
    for n in sub.nodes("Agent"):
        if not sub.node(n)["attrs"].get("is_class"):
            ag_node = n
            break
    if ag_node is None:
        return []
    out = []
    for sc in inner.neighbours(ag_node, "has_self_concern"):
        if not inner.has_node(sc):
            continue
        at = sub.node(sc)["attrs"]
        if at.get("kind") == "code_write" and at.get("status") != "retired":
            out.append(at)
    return out


__all__ = [
    "looks_like_code_example", "ground_identifier_words",
    "validate_written_function_by_running", "teach_write_shape_from_example",
    "compose_write_shape_from_predication", "work_on_code_write_gap",
    "ensure_growth_rules", "pending_naming_gaps", "pending_code_write_gaps",
]
