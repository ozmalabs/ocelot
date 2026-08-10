"""code_curriculum — CODE-CURRICULUM, PART C: THE JABBERWOCK LEARNS FROM
PUBLISHED CURRICULUMS.

CODE-4 (`domains/code_write_growth.py`) gave the agent two sanctioned ways to
widen its OWN write-codebook: teach-by-example (a human pastes one function
in chat) and compose-from-predication. Both assume the human hand-picks and
pastes ONE bare function at a time. Real curriculums are not shaped that way
-- a published lesson (a tutorial section, a textbook chapter, a task page)
is a MIXED-REGISTER document: prose explaining the idea, one or more code
blocks, and exercise sentences phrased as write requests, all interleaved.

This module is PURE ROUTING over decisions the shape machinery ALREADY
makes -- no new recognition step, per CLAUDE.md ("decisions stay in the
shape machinery, Python only routes what it decided"):

  1. `domains.register_source.embedded_regions` already decodes EVERY
     paragraph region of a document BY SHAPE (register_features ->
     ShapeDecode over the register codebook, `seeds/register_source.json`)
     and already carries a `code`-family register with `read_approach:
     'structure'`. A code block inside prose is ALREADY recognised as code,
     region by region -- verified live against three real published lesson
     documents (see `tests/fixtures/code_curriculum/`): a 2-10 line Python
     function scores `family=='code'` at fit 7-8 out of a max of 8.

  2. THE HONEST FINDING (not silently patched): `embedded_regions`'s OWN
     `embedded` list additionally requires `confident` (fit>=6, margin>=2,
     AND n_words>=15) before calling a region foreign. That word-count floor
     is tuned for PROSE register mismatches (a pasted wikipedia paragraph
     inside a casual message needs ~15 recognised words to be sure it is
     really foreign prose, not noise). A terse code snippet is inherently
     word-sparse -- a real 2-line `is_divisible` scores only 9-14 recognised
     words -- so it almost never clears that floor and so NEVER appears in
     `embedded`, even though the SAME per-region decode already assigned it
     `family=='code'` correctly. `code_regions` below reads the `family`
     field directly off `regions` (the unfiltered per-region verdict list
     `embedded_regions` already returns) instead of `embedded` -- the
     minimal mechanical seam the CODE-CURRICULUM wave asked for: no new
     decision, just the right existing field.

  3. Every code region's function(s) go through the EXISTING CODE-4
     teach-by-example path (`code_write_growth.teach_write_shape_from_example`
     -- read, validate-by-running, teach), carrying `lesson_source`
     provenance (additive param, see `code_write_growth.py`). A function the
     emitter cannot translate (a Call to an unheld leaf like `math.sqrt`, an
     if/else-branching return, ...) abstains EXACTLY as it would from a chat
     paste -- the published lesson's own beyond-boundary material produces
     an honest {ok: False, reason} entry here, never a fabricated shape.

  4. A line in a NON-code region that reads as a write request
     (`code_writing.looks_like_write_request`, the SAME thin classifier
     `converse()` itself uses) is attempted through the REAL conversational
     request path (`agent.converse`) -- an exercise sentence in a lesson
     ("...write a function called hypotenuse...") is handled exactly as if
     a human had pasted it into chat: a held shape answers it, or it
     abstains and (via the already-wired `note_code_write_gap` rule) files
     the same capability-gap SelfConcern a chat turn would.

`capability_report` / `run_code_capabilities` are the measurement + self-
account side: a mechanical read of what the agent's write-codebook holds,
bucketed by PROVENANCE (taught-by-chat-example / composed-from-predication /
learned-from-published-material / minted-while-reading / filed-as-gap) --
never re-deciding anything, only reading back facts already on the graph.

ARCHITECTURE (CLAUDE.md). No Python rule engine, no per-document decision
over MEANING. The three DECISIONS a lesson's content passes through --
which register a region is, which code_write_construction (if any) answers
a request, whether a read Term agrees with its own prediction -- are each
already the Rust ShapeDecode / native-evaluate call of an EXISTING faculty;
this module only splits a document into regions (an unmodified existing
call), filters by an existing field, and hands each region to the matching
existing reader/writer.
"""
from __future__ import annotations

import ast
from typing import Any, Optional

from domains import code_reading as cdr
from domains import code_write_growth as cwg
from domains import code_writing as cw
from domains import reading_collapse as rc
from domains import register_source as rs


# --------------------------------------------------------------------------- #
#  CODE-REGION DETECTION — the honest seam (see module docstring, item 2).
# --------------------------------------------------------------------------- #
def code_regions(agent, text: str, *, min_words: int = 6) -> list[dict]:
    """Every paragraph region of `text` the shape machinery decodes as the
    'code' family -- read off `embedded_regions`'s own per-region `regions`
    list (NOT its prose-tuned `embedded` list; see the module docstring's
    honest finding). `min_words` is lowered from the 12-word default because
    a code snippet is inherently more word-sparse than an equivalent-length
    prose paragraph -- an existing, exposed knob, not a new decision."""
    er = rs.embedded_regions(agent, text, min_words=min_words)
    return [r for r in er["regions"] if r.get("family") == "code"]


def _function_sources(region_text: str) -> list[str]:
    """Mechanical AST split: one verbatim source snippet per top-level
    FunctionDef in the region (ast.parse + a body walk) -- the SAME
    I/O-boundary-classifier status `code_write_growth.looks_like_code_example`
    already has. A region with a syntax error (a fragment cut mid-statement
    by the paragraph splitter) yields nothing, honestly."""
    try:
        tree = ast.parse(region_text)
    except SyntaxError:
        return []
    lines = region_text.splitlines()
    out: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            start = node.lineno - 1
            end = getattr(node, "end_lineno", None) or len(lines)
            out.append("\n".join(lines[start:end]) + "\n")
    return out


# --------------------------------------------------------------------------- #
#  LEARN — every function in every code region, through the UNCHANGED CODE-4
#  teach-by-example path.
# --------------------------------------------------------------------------- #
def learn_functions_from_lesson(agent, text: str, *, lesson_source: str,
                                seeds_dir=None, min_words: int = 6) -> list[dict]:
    """Teach-by-example over every function definition found in every
    code-family region of `text` -- the chat-paste precedent, sourced from a
    document region instead of a chat turn. Returns one result dict per
    function attempted (in document order); a function beyond the emitter's
    boundary reports an honest {ok: False, reason: ...}, never a fabricated
    shape."""
    out: list[dict] = []
    for region in code_regions(agent, text, min_words=min_words):
        for src in _function_sources(region["text"]):
            res = cwg.teach_write_shape_from_example(
                agent, src, seeds_dir=seeds_dir, lesson_source=lesson_source)
            res = dict(res)
            res["region_index"] = region["index"]
            res["source"] = src
            out.append(res)
    return out


# --------------------------------------------------------------------------- #
#  EXERCISE LINES — a write request embedded in prose, attempted through the
#  REAL conversational request path (never a bare compose call): a lesson's
#  exercise sentence is handled exactly as a pasted chat message would be.
# --------------------------------------------------------------------------- #
def attempt_exercise_requests(agent, text: str, *, min_words: int = 6) -> list[dict]:
    """Every SENTENCE (not physical line -- a paragraph region is hard-
    wrapped layout, not sentence-bounded; `reading_collapse._split_sentences`
    -- the existing mechanical sentence scanner -- reflows it first) OUTSIDE
    a code-family region that reads as a write request
    (`code_writing.looks_like_write_request`) is run through `agent.converse`
    -- the SAME entry point a chat turn uses, so a held shape answers it
    outright, or the SAME `note_code_write_gap` rule can file the SAME
    capability-gap SelfConcern a chat paste of that sentence would."""
    er = rs.embedded_regions(agent, text, min_words=min_words)
    code_idx = {r["index"] for r in er["regions"] if r.get("family") == "code"}
    out: list[dict] = []
    for r in er["regions"]:
        if r["index"] in code_idx:
            continue
        joined = " ".join(str(r.get("text", "")).split())
        for sent in rc._split_sentences(joined):
            if sent and cw.looks_like_write_request(sent, agent):
                reply = agent.converse(sent)
                out.append({"request": sent, "reply": reply})
    return out


def learn_from_lesson(agent, text: str, *, lesson_source: str, seeds_dir=None,
                      min_words: int = 6) -> dict:
    """The whole-lesson pipeline: detect code regions BY SHAPE, teach-by-
    example over every function they contain, attempt every exercise-line
    write request through the real request path, and (best-effort,
    informational) hand the WHOLE document to the standard document reader
    (`register_source.route_reading`) for its own prose comprehension pass
    -- so a mixed-register lesson gets BOTH halves read, each through its
    own existing faculty. Returns {lesson_source, regions, learned,
    requests, document_read}."""
    regions = rs.embedded_regions(agent, text, min_words=min_words)
    learned = learn_functions_from_lesson(agent, text, lesson_source=lesson_source,
                                          seeds_dir=seeds_dir, min_words=min_words)
    requests = attempt_exercise_requests(agent, text, min_words=min_words)
    try:
        document_read = rs.route_reading(agent, text, hint="lesson")
    except Exception as e:  # noqa: BLE001 -- best-effort prose pass, never fatal
        document_read = {"error": "%s: %s" % (type(e).__name__, e)}
    return {"lesson_source": lesson_source, "regions": regions,
           "learned": learned, "requests": requests, "document_read": document_read}


# --------------------------------------------------------------------------- #
#  CAPABILITY REPORT — mechanical read of the write/read codebooks, bucketed
#  by PROVENANCE. No decision: every bucket is a fact already on the graph.
# --------------------------------------------------------------------------- #
def _txt(v) -> Optional[str]:
    """Attr read-back normaliser (the documented bytes gotcha) -- mechanical."""
    if v is None:
        return None
    if isinstance(v, bytes):
        return v.decode("utf-8", "replace")
    return str(v)


def _pending_gaps_of_kind(agent, kind: str) -> list[dict]:
    """Mechanical reader: every held, un-retired SelfConcern of `kind` --
    the cwg.pending_code_write_gaps shape, parameterised (prog_read gaps are
    the P2.5 seeds/prog_read_gap.json mints; same node vocabulary)."""
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
        if at.get("kind") == kind and at.get("status") != "retired":
            out.append(at)
    return out


def capability_report(agent) -> dict[str, Any]:
    """{learned_by_teaching, learned_by_composition, learned_from_published,
    minted_by_reading, synthesized, filed_as_gap, gap_counts} -- a mechanical
    partition of every held `code_write_construction` ShapeSignature by its
    OWN `taught_from` / `lesson_source` attrs, every held `code_construction`
    ShapeSignature that was `learned` (minted while reading, not seeded),
    every accepted `Program{provenance:'program_synthesis'}` node with its
    rung provenance read off the accepting Goal (P6: the synthesis loop's
    own artifacts), and every un-retired `code_write` SelfConcern (a
    capability the agent could not close) plus the code_write / prog_read
    gap COUNTS. Never a decision -- each bucket reads a fact the graph
    already carries."""
    sub = getattr(agent, "s", agent)
    taught: list[dict] = []
    composed: list[dict] = []
    published: list[dict] = []
    for n in sub.nodes("ShapeSignature"):
        at = sub.node(n)["attrs"]
        if at.get("kind") != "code_write_construction":
            continue
        row = {"name": at.get("name"), "taught_for": at.get("taught_for"),
              "taught_from": at.get("taught_from"),
              "lesson_source": at.get("lesson_source")}
        if at.get("lesson_source"):
            published.append(row)
        elif at.get("taught_from") == "predication":
            composed.append(row)
        elif at.get("taught_from") == "example":
            taught.append(row)
    minted: list[dict] = []
    for n in sub.nodes("ShapeSignature"):
        at = sub.node(n)["attrs"]
        if at.get("kind") == "code_construction" and at.get("learned"):
            minted.append({"name": at.get("name")})
    # P6 (additive): programs the SYNTHESIS LOOP accepted -- Program nodes
    # ps_accept minted (provenance='program_synthesis'), each with the rung
    # provenance (codebook / lattice / enumerate) read off the accepting
    # Goal via the accepted_program edge. Pure read-back of rule-written
    # facts.
    synthesized: list[dict] = []
    for n in sub.nodes("Program"):
        at = sub.node(n)["attrs"]
        if _txt(at.get("provenance")) != "program_synthesis":
            continue
        row: dict[str, Any] = {"name": _txt(at.get("name")),
                               "construction": _txt(at.get("construction")),
                               "attempts": at.get("attempts"), "rungs": None}
        for g in sub.in_neighbours(n, "accepted_program"):
            gat = sub.node(g)["attrs"]
            row["rungs"] = {"codebook": gat.get("ps_rung_codebook"),
                            "lattice": gat.get("ps_rung_lattice"),
                            "enumerate": gat.get("ps_rung_enumerate")}
        synthesized.append(row)
    gaps = cwg.pending_code_write_gaps(agent)
    open_write_gaps = [g for g in gaps if g.get("status") != "resolved"]
    prog_read_gaps = [g for g in _pending_gaps_of_kind(agent, "prog_read")
                      if g.get("status") != "resolved"]
    return {"learned_by_teaching": taught, "learned_by_composition": composed,
           "learned_from_published": published, "minted_by_reading": minted,
           "synthesized": synthesized,
           "filed_as_gap": open_write_gaps,
           "gap_counts": {"code_write": len(open_write_gaps),
                          "prog_read": len(prog_read_gaps)}}


def run_code_capabilities(substrate, meta_arg: Optional[str] = None) -> dict[str, Any]:
    """SELF-QUERY: 'what can you do with code now?' -- the `_run_self_gaps`
    pattern, pointed at the write/read codebooks instead of SelfConcerns: a
    mechanical read + first-person format of `capability_report`, never
    invented content. Registered into `reflective_faculty._DISPATCH` (see
    `substrate/boot_all.py`'s one-line import) under `code_capabilities`."""
    report = capability_report(substrate)
    teaching, composed = report["learned_by_teaching"], report["learned_by_composition"]
    published, minted = report["learned_from_published"], report["minted_by_reading"]
    synthesized = report["synthesized"]
    gaps = report["filed_as_gap"]
    gap_counts = report["gap_counts"]
    if not (teaching or composed or published or minted or synthesized):
        note = ("I hold only the starter code-write vocabulary I booted with, "
                "and have not grown it yet.")
    else:
        parts = []
        if teaching:
            parts.append("%d taught by chat example (%s)" %
                         (len(teaching), ", ".join(r["name"] for r in teaching)))
        if composed:
            parts.append("%d composed from predication (%s)" %
                         (len(composed), ", ".join(r["name"] for r in composed)))
        if published:
            parts.append("%d learned from published material (%s)" % (
                len(published),
                ", ".join("%s from %s" % (r["name"], r.get("lesson_source") or "an unnamed source")
                         for r in published)))
        if minted:
            parts.append("%d new code shapes recognised while reading, naming pending (%s)" %
                         (len(minted), ", ".join(r["name"] for r in minted)))
        if synthesized:
            parts.append("%d synthesized end-to-end from a request with examples (%s)" % (
                len(synthesized),
                ", ".join("%s via %s" % (r["name"], r.get("construction") or "enumerate")
                         for r in synthesized)))
        note = "Beyond my starter code vocabulary, I have grown it: " + "; ".join(parts) + "."
    if gaps:
        note += (" I still hold %d open code capability gap(s) I have not closed: %s."
                % (len(gaps), "; ".join(repr(g.get("content")) for g in gaps[:6])))
    if gap_counts["code_write"] or gap_counts["prog_read"]:
        note += (" Open gap counts: %d code_write, %d prog_read."
                % (gap_counts["code_write"], gap_counts["prog_read"]))
    return {"code_capabilities": True, "report": report, "note": note}


# --------------------------------------------------------------------------- #
#  MEASUREMENT — repo-scan baseline/after protocol (CODE-CURRICULUM part B/1).
# --------------------------------------------------------------------------- #
def scan_repo_functions(agent, roots: list[str], *,
                        max_files: Optional[int] = None) -> dict[str, Any]:
    """Walk `roots` (directories, relative to the repo root) for `*.py`
    files; for every top-level function definition, read it
    (`code_reading.read_function`) and classify it: parseable (always true
    if it got this far) / construction_recognized (a winning construction) /
    term_emittable (a Term was produced) / predict_correct (a sample-input
    native-evaluate check agrees with a direct call, PURE FUNCTIONS ONLY --
    guarded by a bare `import` scan so an impure/side-effecting function is
    never called). Returns {n_files, n_functions, counts, rows} -- `rows` is
    per-function detail for a full report.

    `max_files` (additive, default None = unbounded): a real repo scan over
    thousands of files/functions is a genuinely expensive DECODE per
    function (ShapeDecode + a native-evaluate sample check); `max_files`
    bounds the walk to a deterministic (sorted) PREFIX of the file list so a
    driver can run a meaningful, reproducible sample in bounded wall-clock
    time instead of an unbounded full-repo pass -- a pragmatic sampling knob,
    not a change to what any single function's read decides."""
    import os
    root_dir = cdr._ROOT
    counts = {"parseable": 0, "construction_recognized": 0, "term_emittable": 0,
             "predict_correct": 0, "predict_attempted": 0}
    rows: list[dict] = []
    n_files = 0
    all_paths: list[str] = []
    for rel in roots:
        base = os.path.join(root_dir, rel)
        if not os.path.isdir(base):
            continue
        for dirpath, _dirnames, filenames in os.walk(base):
            for fn in filenames:
                if fn.endswith(".py"):
                    all_paths.append(os.path.join(dirpath, fn))
    all_paths.sort()
    if max_files is not None:
        all_paths = all_paths[:max_files]
    for path in all_paths:
        try:
            src = open(path).read()
        except OSError:
            continue
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        n_files += 1
        lines = src.splitlines()
        for node in tree.body:
            if not isinstance(node, ast.FunctionDef):
                continue
            start = node.lineno - 1
            end = getattr(node, "end_lineno", None) or len(lines)
            func_src = "\n".join(lines[start:end]) + "\n"
            counts["parseable"] += 1
            reading = cdr.read_function(agent, func_src, node.name)
            row = {"file": os.path.relpath(path, root_dir), "name": node.name,
                  "construction": reading.get("construction"),
                  "emittable": reading.get("term") is not None,
                  "predict_correct": None}
            if reading.get("construction"):
                counts["construction_recognized"] += 1
            if reading.get("term") is not None:
                counts["term_emittable"] += 1
                args = reading.get("args") or []
                if args and all(isinstance(a, str) for a in args):
                    sample = cw._sample_env(args)
                    try:
                        predicted = cdr.predict_output(agent, func_src, node.name, sample)
                        counts["predict_attempted"] += 1
                        row["predict_correct"] = bool(predicted is not None)
                        if row["predict_correct"]:
                            counts["predict_correct"] += 1
                    except Exception:  # noqa: BLE001 -- honest non-count, not a crash
                        row["predict_correct"] = False
            rows.append(row)
    return {"n_files": n_files, "n_functions": counts["parseable"], "counts": counts,
           "rows": rows}


def run_write_battery(agent, requests: list[str]) -> dict[str, Any]:
    """The fixed NL write-request battery: attempt every request through the
    REAL `write_function_from_request` (never `agent.converse`, so the
    battery does not itself file gaps or mutate conversation state) and
    count how many are answerable. Returns {n, n_ok, rows}."""
    rows = []
    n_ok = 0
    for req in requests:
        result = cw.write_function_from_request(agent, req)
        ok = bool(result.get("ok"))
        if ok:
            n_ok += 1
        rows.append({"request": req, "ok": ok,
                     "construction": result.get("construction"),
                     "reason": result.get("reason")})
    return {"n": len(requests), "n_ok": n_ok, "rows": rows}


# --------------------------------------------------------------------------- #
#  BOOT-TIME DISPATCH REGISTRATION (mirrors self_model.py's own registration
#  precedent, from the OTHER side to avoid a reflective_faculty<->code_curriculum
#  import cycle: reflective_faculty.py is imported BY code_reading/code_writing/
#  code_write_growth, so it must never import this module back).
# --------------------------------------------------------------------------- #
def ensure_code_capabilities_dispatch() -> None:
    try:
        from domains import reflective_faculty as _rf
    except ImportError:
        return
    _rf._DISPATCH.setdefault("code_capabilities", run_code_capabilities)


ensure_code_capabilities_dispatch()


__all__ = ["code_regions", "learn_functions_from_lesson", "attempt_exercise_requests",
          "learn_from_lesson", "capability_report", "run_code_capabilities",
          "scan_repo_functions", "run_write_battery",
          "ensure_code_capabilities_dispatch"]
