"""code_reading — CODE-1: CODE AS A READ REGISTER.

The smallest vertical slice proving the register closes: read a real repo
function into graph + Terms + concepts + comments, answer what it returns /
what it does / why (against its own comment), round-trip the compute-core
through the existing renderer.

This module is `domains/reading_collapse.py`'s recognize-or-mint discipline,
structurally copied and pointed at Python source instead of English clauses:

  FUNCTION -ingest-> AST-GRAPH -root-shape-> SKELETON -ShapeDecode-> WINNING
  CODE_CONSTRUCTION -template-> "what it does"
                              |
                              +- residual (no held construction covers) -sd
                                 loop-> MINT -install-> re-decode -> grounds

  1. INGEST. `ast_to_term.ingest_ast` (unmodified world-adapter: a Python
     source string -> a typed AstNode graph, mechanical translation, "a
     diagram is a graph"). `ast_to_term.ingest_ast` was extended (additively)
     to carry each FunctionDef's own docstring (`ast.get_docstring`, a stdlib
     parser fact) as an attr — mechanical I/O, not a new decision.

  2. SKELETON. A function's compute-core is read at ROOT-SHAPE granularity
     (CODE-1's smallest-vertical-slice scope — full nested-AST-shape depth is
     a later wave's residual, named honestly below): the Return expression's
     own root ast_type normalises to ONE marker class via `_root_marker`, the
     SAME fixed/mechanical status `ast_to_term.py`'s own BinOp->Term map
     already has ("the SAME for every faculty", not a decision) — every
     BinOp/UnaryOp root collapses to ARITH (an arithmetic expression is one
     construction regardless of which operator sits at the root); a
     Compare/IfExp/Attribute/Subscript root keeps its own normalised class
     (COMPARE/COND/FIELD); anything else keeps its bare ast_type as a
     single-token marker (e.g. BOOL for BoolOp) so a genuinely uncovered
     shape produces a real residual rather than silently reporting
     "unrecognised".

  3. CODEBOOK = held `ShapeSignature{kind:'code_construction'}` nodes
     (`seeds/code_constructions.json`): arithmetic_expression / comparison_
     predicate / conditional_expression / field_access, each a one-token
     skeleton + a role-slotted `ground_template`.

  4. READ = ShapeDecode. The skeleton is decoded against the codebook by
     `reflective_faculty.compose_design_for_goal` — the SAME Rust ShapeDecode
     Term `reading_collapse.py` uses for English clauses; the construction
     with the best `shape_fit` wins (the decode decides, not a Python
     branch); its `ground_template` fills the roles (the function's own
     Name/Attribute identifiers) into a one-sentence "what it does" readout.

  5. LEARN. A shape no held construction covers (a non-empty residual) drives
     `reflective_faculty.induce_concern` (the sd loop, `seeds/shape_decode_
     loop.json`) — the residual MINTS a CapabilityAxis quantum; this module
     then installs the shape as a NEW `code_construction` ShapeSignature and
     bumps `codebook_epoch`; the re-decode GROUNDS it. Exactly
     `reading_collapse._install_construction`'s idiom, applied to code.

  6. TERM EMISSION is a SEPARATE, STRICTER concern from construction
     recognition — `ast_to_term.AstTermEmitter` (unmodified: its honest
     pure-single-Return-expression boundary is CODE-2's, not this wave's, to
     widen) only succeeds for arithmetic compute-cores. A recognised
     comparison_predicate/conditional_expression/field_access construction
     is still READ (the codebook covers its shape, "what it does" answers)
     even when it cannot be EVALUATED as a native Term — an honest EmitError
     is reported rather than a lossy or fabricated Term. When emission does
     succeed, the Term round-trips through the EXISTING graph-resident
     Python renderer (`WorldAdapter.render`, unmodified) — the read-side
     emitter vocabulary and the write-side RenderRule set already cover the
     same arithmetic algebra (Plus/Minus/Times/Div/Pow/Var/Lit), so the
     round-trip is composition, not new code.

  7. COMMENTS AS NL. The docstring's first sentence (a mechanical text-prep
     — see `_first_sentence`'s own docstring for the honest scope note about
     embedded ASCII-art formula blocks) is read through the EXISTING
     `reading_collapse.read_clause` collapse pipeline (the same construction-
     codebook mechanism, pointed at English) and its predications' argument
     concepts are content-word-split (`_split_identifier`, snake_case/
     camelCase — mechanical string tokenisation, no regex, the identifier
     analogue of `reading_collapse._norm`). The AGREEMENT stratum
     (`_agreement`) is deliberately coarse: shared content words between what
     the CODE names (its own Name/Attribute identifiers, split) and what the
     COMMENT claims (its read predications' arguments, split) — honest about
     its coarseness, exactly as the interlocutor four-strata law is honest
     that a self-report is evidence, not ground truth: the code IS; the
     comment CLAIMS.

ARCHITECTURE (CLAUDE.md). The DECISION that carries meaning — WHICH
construction, WHETHER to mint — is the ShapeDecode collapse's / the seeded
sd_* rules', read off their own verdicts; this module only (a) turns an
ingested Return expression into a one-token skeleton via a FIXED mechanical
map (the same status as ast_to_term.py's own BinOp map), (b) reads the
decode's verdict, (c) fills the winning construction's own `ground_template`
(one general routine, never a per-construction branch), (d) installs a
minted construction as graph data, (e) attempts Term emission + render
(unmodified existing machinery), (f) reads the docstring through the
existing English-reading collapse and reports the coarse word-overlap
agreement. No new hardcoded per-construction logic; no Python rule engine;
no agent decisions.

NAMED RESIDUALS (honest, not silently patched): root-shape granularity only
(a nested arithmetic-vs-comparison mix inside one expression reads by its
ROOT alone); the docstring read is first-sentence-only (embedded formula
blocks are out of scope); agreement is a coarse word-overlap set (no
semantic paraphrase detection); `_read_docstring` never mints a new reading
construction of its own (it reuses `reading_collapse`'s codebook + growth
unmodified, so an unusual comment sentence may itself mint a NEW English
construction — that is `reading_collapse`'s own documented growth path, not
this module's).
"""
from __future__ import annotations

import ast
import json
from typing import Any, Optional

from domains import ast_to_term
from domains import reading_collapse as rc
from domains import reflective_faculty as rf
from substrate.jsonio import term_from_json

_ROOT = __file__.rsplit("/domains/", 1)[0]


# --------------------------------------------------------------------------- #
#  resolution + codebook install (mechanical adapter I/O — no decision).
# --------------------------------------------------------------------------- #
def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    ag_node = None
    for n in sub.nodes("Agent"):
        if not sub.node(n)["attrs"].get("is_class"):
            ag_node = n
            break
    return sub, native, ag_node


def ensure_codebook(agent) -> None:
    """Idempotently install the code-construction codebook
    (`ShapeSignature{kind:'code_construction'}` nodes, `seeds/code_
    constructions.json`). Guarded by a graph-resident `Seed{id:
    'code_constructions'}` node — the SAME idempotency idiom
    `reading_collapse.ensure_codebook` uses. Mechanical seed I/O."""
    import os
    sub, _native, ag_node = _resolve(agent)
    for n in sub.nodes("Seed"):
        if sub.node(n)["attrs"].get("id") == "code_constructions":
            return
    path = os.path.join(_ROOT, "seeds", "code_constructions.json")
    with open(path) as f:
        manifest = json.load(f)
    for nd in manifest.get("nodes", []):
        sub.add_node(nd["type"], dict(nd.get("attrs", {})))
    sub.add_node("Seed", {"id": "code_constructions",
                          "version": manifest.get("version", "1.0.0")})
    if ag_node is not None and sub.node(ag_node)["attrs"].get("codebook_epoch") is None:
        sub.set_attr(ag_node, "codebook_epoch", 0.0)


# --------------------------------------------------------------------------- #
#  SKELETON — a Return expression's ROOT ast_type -> ONE marker class. Fixed,
#  mechanical map, the SAME status ast_to_term.py's own BinOp->Term map has.
# --------------------------------------------------------------------------- #
_ROOT_MARKER_MAP = {
    "Compare": "COMPARE",
    "IfExp": "COND",
    "Attribute": "FIELD",
    "Subscript": "FIELD",
}


def _root_marker(ast_type: str) -> str:
    if ast_type.startswith("BinOp:") or ast_type == "UnaryOp:USub":
        return "ARITH"
    if ast_type in _ROOT_MARKER_MAP:
        return _ROOT_MARKER_MAP[ast_type]
    # anything else keeps its OWN normalised class -- a genuinely novel root
    # shape (e.g. BoolOp) produces a real residual for the sd loop to mint,
    # rather than silently collapsing to "unrecognised".
    return ast_type.split(":", 1)[0].upper()


# --------------------------------------------------------------------------- #
#  AST-GRAPH READS (reuse `AstTermEmitter`'s own accessors — same graph, same
#  child_field/child_index bookkeeping; no duplicated traversal logic).
# --------------------------------------------------------------------------- #
def _single_return_value(em: "ast_to_term.AstTermEmitter", func_root) -> Optional[int]:
    """The function's sole Return expression node, iff its body is EXACTLY one
    Return statement -- MODULO a leading DOCSTRING statement (an `Expr` whose
    sole child is a string `Constant`), which is metadata, not code, already
    peeled off separately as the `docstring` attr (`ast.get_docstring`,
    mechanical -- the exact same stdlib peeling `ast.get_docstring` itself
    performs). Skipping it here is NOT a relaxation of `AstTermEmitter.
    emit_function`'s own "no loops/branches/comprehensions/mutation" boundary
    (that function is untouched, and is called only via the lower-level
    `emit_term` on the node this function locates -- see `_read_one`): ANY
    OTHER preceding statement still disqualifies the function, exactly as
    before. `None` = honest out-of-scope."""
    body = em._children_of_field(func_root, "body")
    if body and em._attrs(body[0]).get("ast_type") == "Expr":
        val = em._child_by_field(body[0], "value")
        if (val is not None and em._attrs(val).get("ast_type") == "Constant"
                and isinstance(em._attrs(val).get("value"), str)):
            body = body[1:]
    if len(body) != 1 or em._attrs(body[0]).get("ast_type") != "Return":
        return None
    return em._child_by_field(body[0], "value")


def _function_args(em: "ast_to_term.AstTermEmitter", func_root) -> list[str]:
    args_node = em._child_by_field(func_root, "args")
    if args_node is None:
        return []
    out = []
    for a in em._children_of_field(args_node, "args"):
        nm = em._attrs(a).get("arg")
        if nm:
            out.append(nm)
    return out


def _collect_names(em: "ast_to_term.AstTermEmitter", nid: int) -> list[str]:
    """Every Name/Attribute identifier in the expression subtree, preorder,
    deduped — the operand vocabulary a construction's ground_template names
    and the docstring-agreement check compares against."""
    names: list[str] = []

    def walk(n):
        a = em._attrs(n)
        t = a.get("ast_type", "")
        if t == "Name":
            nm = a.get("id")
            if nm and nm not in names:
                names.append(nm)
        elif t == "Attribute":
            at = a.get("attr")
            if at and at not in names:
                names.append(at)
        for c in em._children(n):
            walk(c)

    walk(nid)
    return names


def _collect_names_multi(em: "ast_to_term.AstTermEmitter", stmts: list) -> list:
    """CODE-2: `_collect_names` over a WHOLE multi-statement body -- walks
    every statement (targets included, e.g. an accumulator/loop-var name),
    deduped in first-seen order. Reuses `_collect_names` unmodified per
    statement; no new traversal logic."""
    names: list = []
    for s in stmts:
        for nm in _collect_names(em, s):
            if nm not in names:
                names.append(nm)
    return names


# --------------------------------------------------------------------------- #
#  CODE-2: STATEMENT-LEVEL SKELETON — a function body wider than one pure
#  expression Return gets a NEW skeleton kind (CODE-1's root-marker skeleton
#  is untouched for the single-Return case). Two shapes collapse to a FIXED
#  marker sequence -- the SAME "shape, not instance-count" discipline
#  `_root_marker` already has (any BinOp -> ARITH regardless of operator):
#    * a straight-line N-assignment-then-Return body is the SEQUENTIAL-
#      BINDING shape (ONE 'LET' token whatever N is -- the let-chain
#      construction cares that the shape is sequential rebinding, not the
#      count);
#    * an init/for-loop-with-one-accumulate-step/Return body is the FIXED
#      four-token 'ASSIGN, FOR, <inner>, RETURN' skeleton -- this shape
#      genuinely HAS an internal sequence, so its skeleton carries it
#      (residual (2)'s first real depth beyond the Return root; `<inner>`
#      is 'AUGASSIGN' for the recognised accumulation construction, or
#      whatever the loop's single body statement actually is otherwise --
#      an honest, undisguised residual, e.g. an early-break's inner `IF`).
#  Any other multi-statement shape keeps its own per-statement marker
#  sequence -- a real residual for the sd loop to mint against.
# --------------------------------------------------------------------------- #
def _stmt_marker(em: "ast_to_term.AstTermEmitter", stmt_nid: int) -> str:
    """A single statement AstNode's TYPE -> a marker token -- the statement-
    level analogue of `_root_marker` (same fixed/mechanical status)."""
    at = em._attrs(stmt_nid).get("ast_type", "")
    if at.startswith("AugAssign:"):
        return "AUGASSIGN"
    return at.split(":", 1)[0].upper()


def _multi_stmt_skeleton_and_kind(em: "ast_to_term.AstTermEmitter", func_root: int):
    """Returns (skeleton, kind) with kind in {'let_chain', 'accumulation',
    'branching_return', 'other'}, or (None, None) when the body is fewer
    than 2 statements AND is not a branching-return (out of scope for
    both the single-expression AND multi-statement paths -- `_read_one`
    falls back to CODE-1's original 'out of scope' note).

    WAVE 2: `branching_return` (`if cond: return a; [elif ...] else:
    return b`) is a ONE-statement body (the whole thing is a single `If`),
    so it is checked FIRST, before the `len(stmts) < 2` "out of scope"
    gate that every other multi-statement shape sits behind -- a
    non-exhaustive if (a fall-through with no final `else`, or a branch
    that does something other than return) does NOT match
    `is_return_chain` and falls through to that same gate honestly. The
    skeleton collapses to a SINGLE 'BRANCH_RETURN' token regardless of
    elif depth -- the SAME shape-not-count discipline `let_chain` already
    has for its 'LET' token -- deliberately NOT a two-token 'IF,RETURN'
    sequence: ShapeDecode's fit score is a positional cross-correlation
    over same-length skeletons, so a two-token signature ending in
    'RETURN' partially (mis)matches ANY OTHER two-token 'X,RETURN' shape
    (e.g. a `while ...: ...; return n` body's own ['WHILE','RETURN']
    skeleton) purely because they share a suffix -- verified live as a
    real regression during this wave. A single unique token cannot
    collide that way."""
    stmts = em.body_statements(func_root)
    if (len(stmts) == 1 and em._attrs(stmts[0]).get("ast_type") == "If"
            and em.is_return_chain(stmts[0])):
        return [["BRANCH_RETURN"]], "branching_return"
    if len(stmts) < 2:
        return None, None
    if (len(stmts) == 3
            and em._attrs(stmts[0]).get("ast_type") == "Assign"
            and em._attrs(stmts[1]).get("ast_type") == "For"
            and em._attrs(stmts[2]).get("ast_type") == "Return"):
        for_body = em._children_of_field(stmts[1], "body")
        if len(for_body) == 1:
            inner = _stmt_marker(em, for_body[0])
            skeleton = [["ASSIGN"], ["FOR"], [inner], ["RETURN"]]
            kind = "accumulation" if inner == "AUGASSIGN" else "other"
            return skeleton, kind
    if (all(em._attrs(s).get("ast_type") == "Assign" for s in stmts[:-1])
            and em._attrs(stmts[-1]).get("ast_type") == "Return"):
        return [["LET"]], "let_chain"
    tokens = []
    for s in stmts:
        tokens.append(_stmt_marker(em, s))
        if em._attrs(s).get("ast_type") == "For":
            for_body = em._children_of_field(s, "body")
            if len(for_body) == 1:
                tokens.append(_stmt_marker(em, for_body[0]))
    return [[t] for t in tokens], "other"


def _maybe_render(agent, term_json: dict):
    """Render `term_json` to Python source when the agent's renderer is
    available (mechanical query, no decision) -- factored out of `_read_one`
    so both the single-expression and multi-statement emission branches
    share ONE render call."""
    if not (hasattr(agent, "render") and hasattr(agent, "seed_python_renderer")):
        return None
    if agent.language("python") is None:
        agent.seed_python_renderer()
    term_obj = term_from_json(term_json)
    return agent.render(term_obj, "python")


# --------------------------------------------------------------------------- #
#  DECODE + WINNER read-off (the decode decides — this only reads its verdict).
# --------------------------------------------------------------------------- #
def _decode(agent, skeleton: list) -> dict:
    sub, _, _ = _resolve(agent)
    res = rf.compose_design_for_goal(sub, skeleton)
    if not isinstance(res, dict):
        return {"plan": [], "residual": list(skeleton), "ordered_parts": []}
    return res


def _decode_and_ground(agent, skeleton: list, name_hint: str) -> tuple:
    """CODE-2: the decode-or-mint sequence CODE-1's `_read_one` had inlined
    for its single-token skeleton, factored out unchanged so the NEW
    multi-statement skeletons (let-chain / accumulation / other) share the
    SAME recognize-or-mint discipline instead of a second copy of it. Byte-
    identical behaviour for a single-token skeleton (the only kind CODE-1
    ever built): returns (winner, shape_fit, residual, minted)."""
    decode = _decode(agent, skeleton)
    winner, fit = _winner(decode, kind="code_construction")
    residual = [list(r) for r in (decode.get("residual") or [])]
    minted = False
    if winner is None or fit <= 0:
        ind = rf.induce_concern(agent, skeleton, name_hint=name_hint)
        minted = bool(ind.get("minted"))
        _install_code_construction(agent, skeleton)
        decode = _decode(agent, skeleton)
        winner, fit = _winner(decode, kind="code_construction")
        residual = [list(r) for r in (decode.get("residual") or [])]
    return winner, fit, residual, minted


def _winner(res: dict, *, kind: Optional[str] = None) -> tuple[Optional[str], int]:
    """The best-fit `part` from a ShapeDecode plan. `kind` (CODE-CURRICULUM
    finding, additive -- default None is the pre-existing, byte-identical
    behaviour): `compose_design_for_goal`'s Rust ShapeDecode ranks EVERY
    held `ShapeSignature` node as a candidate part regardless of its own
    `kind` -- the read (`code_construction`), write
    (`code_write_construction`), and register (`register_sig`) codebooks
    all share ONE flat namespace. Observed live: a WRITE-side request could
    win against a READ-side (or otherwise unrelated) construction that
    carries no term recipe at all -- an impossible answer by construction,
    never merely a low-confidence one. Passing the caller's own intended
    `kind` filters the plan to that domain BEFORE taking the argmax -- each
    plan entry already carries its own `kind` (a fact the decode already
    computed), so this is a read of an existing field, not a new decision.
    This does NOT fix same-kind collisions (two write shapes sharing a
    generic trigger word) -- that is a deeper, un-fixed residual named in
    the CODE-CURRICULUM report."""
    plan = res.get("plan") or []
    best_name, best_fit = None, -1
    for p in plan:
        if kind is not None and p.get("kind") != kind:
            continue
        try:
            fit = int(p.get("shape_fit", 0))
        except (TypeError, ValueError):
            fit = 0
        if fit > best_fit:
            best_fit, best_name = fit, p.get("part")
    return best_name, best_fit


def _construction_template(sub, name: str) -> dict:
    for n in sub.nodes("ShapeSignature"):
        at = sub.node(n)["attrs"]
        if at.get("name") == name and at.get("kind") == "code_construction":
            tmpl = at.get("ground_template")
            if tmpl:
                try:
                    return json.loads(tmpl)
                except Exception:
                    pass
    return {}


def _ground_code(template: dict, names: list[str]) -> str:
    """ONE construction-general routine (never a per-construction branch): the
    template's `desc` + the operand names the AST subtree actually carries."""
    desc = template.get("desc") or "performs a computation"
    if names:
        return "%s, over %s" % (desc, ", ".join(names))
    return desc


# --------------------------------------------------------------------------- #
#  LEARN — install a minted shape as a NEW codebook ShapeSignature.
# --------------------------------------------------------------------------- #
def _install_code_construction(agent, skeleton: list) -> dict:
    """Install a MINTED skeleton as a NEW `code_construction` ShapeSignature.
    CODE-2: generalised from a bare marker string to a full skeleton (a list
    of one-token part-lists) so the SAME installer serves both CODE-1's
    single-token skeletons (`[["BOOLOP"]]`) and CODE-2's multi-token ones
    (`[["ASSIGN"],["FOR"],["IF"],["RETURN"]]`) -- byte-identical output for
    a single-token skeleton (`"_".join([marker]) == marker`)."""
    sub, _, ag_node = _resolve(agent)
    key = json.dumps(skeleton)
    label = "_".join(str(tok[0]) for tok in skeleton).lower()
    name = "learned_code_" + label
    for n in sub.nodes("ShapeSignature"):
        at = sub.node(n)["attrs"]
        if at.get("kind") == "code_construction" and at.get("signature") == key:
            return {"installed": False, "name": at.get("name"), "reason": "already held"}
    tmpl = {"desc": "a %s-shaped code construction" % label, "mode": "code_pair"}
    new_node = sub.add_node("ShapeSignature", {"name": name, "kind": "code_construction",
                                               "signature": key, "learned": 1.0,
                                               "ground_template": json.dumps(tmpl)})
    if ag_node is not None:
        cur = sub.node(ag_node)["attrs"].get("codebook_epoch") or 0.0
        sub.set_attr(ag_node, "codebook_epoch", float(cur) + 1.0)
        # CODE-4: the mint got a GENERIC placeholder desc ("a %s-shaped code
        # construction") -- a naming/teaching residual, never silently left
        # as the agent's permanent understanding of the shape. Wire it as a
        # mechanical edge (a fact: this shape is pending a better name/desc),
        # never a decision here; seeds/code_write_gap.json's
        # note_code_read_naming_gap rule DECIDES that's a low-priority gap
        # and files it. A human can close it over NL (teach() a replacement
        # ShapeSignature.ground_template naming the shape properly).
        try:
            sub.add_edge(ag_node, "mint_pending_naming", new_node, {})
        except Exception:
            pass
    return {"installed": True, "name": name, "template": tmpl, "signature": key}


# --------------------------------------------------------------------------- #
#  COMMENTS AS NL — the docstring's first sentence, read via the EXISTING
#  English reading-collapse pipeline; agreement is coarse content-word overlap.
# --------------------------------------------------------------------------- #
def _first_sentence(doc: Optional[str]) -> Optional[str]:
    """The docstring's first NL sentence (mechanical text prep, no decision):
    the first paragraph (split on a blank line — an embedded ASCII-art
    formula block is typically its OWN paragraph, e.g. `_mp3_gain_to_db`'s
    'Converting to dB: ...' block, out of scope for CODE-1's sentence-level
    reading), whitespace-collapsed, truncated at the first '. '. Honest
    residual: a one-paragraph docstring whose only sentence contains a
    formula reads that formula as prose (reading_collapse either grounds
    what it can recognise or reports a clean non-decode — never crashes)."""
    if not doc:
        return None
    first_para = doc.strip().split("\n\n", 1)[0]
    first_para = " ".join(first_para.split())
    if not first_para:
        return None
    idx = first_para.find(". ")
    if idx == -1:
        return first_para if first_para.endswith(".") else first_para + "."
    return first_para[: idx + 1]


def _split_identifier(name: str) -> list[str]:
    """Mechanical identifier tokenisation (str methods only, no regex): split
    snake_case on '_' and camelCase on upper/lower transitions, lowercase
    every part. World-adapter text prep — naming an identifier is not a
    reading decision — the code-side analogue of `reading_collapse._norm`."""
    parts: list[str] = []
    for chunk in str(name).split("_"):
        if not chunk:
            continue
        cur = chunk[0]
        for ch in chunk[1:]:
            if ch.isupper() and cur and not cur[-1].isupper():
                parts.append(cur)
                cur = ch
            else:
                cur += ch
        if cur:
            parts.append(cur)
    return [p.lower() for p in parts if p]


def _read_docstring(agent, doc: Optional[str]) -> dict:
    sent = _first_sentence(doc)
    if not sent:
        return {"sentence": None, "predications": [], "content_words": set(),
               "construction": None}
    r = rc.read_clause(agent, sent, write=False)
    preds = r.get("predications") or []
    words: set = set()
    for p in preds:
        for tok in p[1:]:
            words.update(_split_identifier(str(tok)))
    return {"sentence": sent, "predications": preds, "content_words": words,
           "construction": r.get("construction")}


def _agreement(code_words: set, comment_words: set) -> dict:
    shared = code_words & comment_words
    return {"shared": sorted(shared), "code_only": sorted(code_words - comment_words),
           "comment_only": sorted(comment_words - code_words),
           "verdict": "agree" if shared else "diverge"}


# --------------------------------------------------------------------------- #
#  READ ONE FUNCTION — the whole pipeline over an already-ingested AstNode.
# --------------------------------------------------------------------------- #
def _read_one(agent, em: "ast_to_term.AstTermEmitter", froot: int, name: str) -> dict:
    sub, _native, _ag = _resolve(agent)
    args = _function_args(em, froot)
    doc = em._attrs(froot).get("docstring")
    out: dict[str, Any] = {"name": name, "args": args, "docstring": doc}
    ret_val = _single_return_value(em, froot)

    if ret_val is not None:
        # CODE-1's original single-pure-expression-Return path — BYTE
        # IDENTICAL: root-marker skeleton, arithmetic/comparison/boolean/
        # ternary emitter, unchanged decode/mint sequence (now shared via
        # `_decode_and_ground`, which behaves identically for a one-token
        # skeleton — see its docstring).
        names = _collect_names(em, ret_val)
        marker = _root_marker(em._attrs(ret_val).get("ast_type", ""))
        skeleton = [[marker]]
        out["names"] = names
        out["skeleton"] = skeleton
        winner, fit, residual, minted = _decode_and_ground(
            agent, skeleton, "code_" + marker.lower())
        out["construction"] = winner
        out["shape_fit"] = fit
        out["residual"] = residual
        out["minted"] = minted
        template = _construction_template(sub, winner) if winner else {}
        out["what_does"] = _ground_code(template, names)

        # Term emission — a separate, STRICTER concern. Calls the per-node
        # `emit_term` directly on the Return value THIS function already
        # located (`_single_return_value`, docstring-aware) rather than
        # `emit_function`'s own body walk (which does not know about
        # docstrings) -- `AstTermEmitter` itself is not modified for this
        # path; its "no loops/branches/comprehensions/mutation" guard
        # already ran, in `_single_return_value`.
        try:
            term_json = em.emit_term(ret_val)
            out["term"] = term_json
            out["emit_error"] = None
            out["rendered_python"] = _maybe_render(agent, term_json)
        except ast_to_term.EmitError as e:
            out["term"] = None
            out["emit_error"] = str(e)
            out["rendered_python"] = None
    else:
        # CODE-2: the body is not a single pure-expression Return -- try the
        # two RECOGNISED multi-statement shapes (let-chain / accumulation)
        # before conceding CODE-1's original "out of scope" note.
        skeleton, kind = _multi_stmt_skeleton_and_kind(em, froot)
        if skeleton is None:
            out["note"] = "not a single pure-expression Return -- out of CODE-1 scope"
            out["construction"] = None
            out["what_does"] = None
            return out

        stmts = em.body_statements(froot)
        names = _collect_names_multi(em, stmts)
        out["names"] = names
        out["skeleton"] = skeleton
        name_hint = "code_" + "_".join(str(tok[0]) for tok in skeleton).lower()
        winner, fit, residual, minted = _decode_and_ground(agent, skeleton, name_hint)
        out["construction"] = winner
        out["shape_fit"] = fit
        out["residual"] = residual
        out["minted"] = minted
        template = _construction_template(sub, winner) if winner else {}
        out["what_does"] = _ground_code(template, names)

        # Term emission — SEPARATE, STRICTER concern, exactly the CODE-1
        # precedent: `kind` says which construction the SKELETON matched;
        # each emitter independently re-validates the STRUCTURE (an
        # 'accumulation'-recognised shape can still honestly abstain if,
        # say, its init calls an un-translatable function) rather than
        # trusting the skeleton's coarser classification.
        try:
            if kind == "let_chain":
                term_json = em.emit_let_chain(froot)
            elif kind == "accumulation":
                term_json = em.emit_accumulation(froot)
            elif kind == "branching_return":
                term_json = em.emit_branching_return(froot)
            else:
                raise ast_to_term.EmitError(
                    f"no Term emitter for this multi-statement shape "
                    f"({kind!r}) -- named residual, not approximated")
            out["term"] = term_json
            out["emit_error"] = None
            out["rendered_python"] = _maybe_render(agent, term_json)
        except ast_to_term.EmitError as e:
            out["term"] = None
            out["emit_error"] = str(e)
            out["rendered_python"] = None

    # Comments as NL + the honest agreement stratum — SHARED by both paths.
    comment = _read_docstring(agent, doc)
    out["comment"] = comment
    code_words: set = set()
    for nm in out.get("names") or []:
        code_words.update(_split_identifier(nm))
    out["agreement"] = _agreement(code_words, comment["content_words"])
    return out


# --------------------------------------------------------------------------- #
#  PUBLIC ENTRIES
# --------------------------------------------------------------------------- #
def read_function(agent, source: str, func_name: Optional[str] = None,
                  *, range_bind: Optional[dict] = None) -> dict:
    """Read ONE function out of `source` (a Python compute-core, or a whole
    file/snippet — `func_name` picks which FunctionDef; `None` = the first).
    Ingest -> skeleton -> decode/mint -> ground -> emit/render -> docstring
    read -> agreement. Returns the structured reading (see `_read_one`).

    `range_bind` (CODE-2, additive, default None = CODE-1 behaviour
    unchanged): concrete int binds threaded to the `AstTermEmitter` for the
    accumulation construction's `range(n)` iterable materialisation --
    `predict_output` passes the call's own args (the SAME concrete-bind
    status `ast_to_term.py`'s pre-existing Sum-fold machinery already had)."""
    ensure_codebook(agent)
    sub, _native, _ag = _resolve(agent)
    ast_to_term.open_ast_productions(sub)
    rec = ast_to_term.ingest_ast(sub, source, root_label="code_reading")
    func_roots = rec["func_roots"]
    if not func_roots:
        return {"note": "no function definition in source -- out of scope",
               "construction": None, "what_does": None}
    name = func_name or next(iter(func_roots))
    if name not in func_roots:
        return {"note": "function %r not found in source" % name,
               "available": list(func_roots), "construction": None, "what_does": None}
    em = ast_to_term.AstTermEmitter(sub, held_leaves={}, range_bind=range_bind)
    return _read_one(agent, em, func_roots[name], name)


def read_source(agent, source: str) -> dict:
    """The `register_source.route_reading` STRUCTURE-approach entry: read
    EVERY function definition in `source` (one ingest, shared across all of
    them). Returns {functions: {name: reading}, primary_function, answer}."""
    ensure_codebook(agent)
    sub, _native, _ag = _resolve(agent)
    try:
        ast.parse(source)
    except SyntaxError as e:
        return {"note": "not parseable Python source", "error": str(e),
               "functions": {}, "primary_function": None, "answer": None}
    ast_to_term.open_ast_productions(sub)
    rec = ast_to_term.ingest_ast(sub, source, root_label="code_reading")
    func_roots = rec["func_roots"]
    if not func_roots:
        return {"note": "no function definitions found", "functions": {},
               "primary_function": None, "answer": None}
    em = ast_to_term.AstTermEmitter(sub, held_leaves={})
    functions = {nm: _read_one(agent, em, nid, nm) for nm, nid in func_roots.items()}
    primary = next(iter(func_roots))
    return {"functions": functions, "primary_function": primary, "answer": primary}


# --------------------------------------------------------------------------- #
#  CODE-2: UNDERSTANDING = PREDICTION — the agent answers "what does f(...)
#  return" by RUNNING its own Term model (analysis-by-synthesis), never by
#  exec-ing the real Python. Reuses `read_function`'s WHOLE pipeline (the
#  reading IS the model) rather than a second ingest/emit path.
# --------------------------------------------------------------------------- #
def predict_output(agent, source: str, func_name: str, args: Optional[dict] = None):
    """Read `source` through `read_function` (skeleton -> decode/mint ->
    ground -> emit), then EVALUATE the emitted Term natively against `args`
    via the Rust engine (`agent.inner.evaluate`) -- the prediction IS the
    agent's own compiled understanding of the function, run forward. `args`
    doubles as `range_bind` (every int-valued arg is a candidate range(n)
    bound the accumulation construction may need -- concrete call args ARE
    the bind).

    Raises `ast_to_term.EmitError` (never fabricates a guess) when the
    function's shape has no emittable Term -- the SAME honest-abstain
    contract every other emission path in this module has."""
    sub, native, _ag = _resolve(agent)
    call_args = dict(args or {})
    range_bind = {k: v for k, v in call_args.items()
                 if isinstance(v, int) and not isinstance(v, bool)}
    reading = read_function(agent, source, func_name, range_bind=range_bind)
    if reading.get("term") is None:
        raise ast_to_term.EmitError(
            reading.get("emit_error") or reading.get("note")
            or f"predict_output: no emittable Term for {func_name!r}")
    return native.evaluate(reading["term"], call_args)


# --------------------------------------------------------------------------- #
#  QA READOUTS — mechanical readers over an already-produced reading (the
#  `reflective_faculty`-style pattern: read the graph/dict back out, decide
#  nothing new).
# --------------------------------------------------------------------------- #
def answer_return(reading: dict) -> str:
    """"what does <fn> return" — the emitted Term's head, rendered."""
    if reading.get("rendered_python") is not None:
        return "returns %s" % reading["rendered_python"]
    if reading.get("emit_error"):
        return ("returns a %s expression over %s -- not yet Term-evaluable "
                "(named residual: %s)" % (reading.get("construction") or "?",
                                          ", ".join(reading.get("names") or []) or "no operands",
                                          reading["emit_error"]))
    return "unknown -- %s" % reading.get("note", "out of scope")


def answer_what(reading: dict) -> str:
    """"what does it do" — the winning construction's readout."""
    return reading.get("what_does") or ("unrecognised -- %s" % reading.get("note", ""))


def answer_why(reading: dict) -> str:
    """"why" — the docstring's claim + the honest agreement stratum: the code
    IS (what_does); the comment CLAIMS (the first sentence); they agree or
    diverge on the SHARED content words (a coarse, honestly-reported check)."""
    comment = reading.get("comment") or {}
    sent = comment.get("sentence")
    fact = "the code %s" % answer_what(reading)
    if not sent:
        return "%s; the function carries no docstring to compare against." % fact
    agreement = reading.get("agreement") or {}
    verdict = agreement.get("verdict", "diverge")
    shared = agreement.get("shared") or []
    return ("%s; the comment claims: %r -- the two %s (shared terms: %s)"
           % (fact, sent, verdict, ", ".join(shared) if shared else "none"))


__all__ = ["ensure_codebook", "read_function", "read_source", "predict_output",
          "answer_return", "answer_what", "answer_why"]
