"""faculty_generator — PART 2/3: THE GENERATOR (the flex).

cmsg157: the template (faculty_template.make_faculty) is the frozen core (re-derived
>=2 existing faculties — faculty_template_redrive.py). THE GENERATOR is the flex: the
agent INSTANTIATES the template from READING — it recognizes a gap, READS the math
(GET-only full text), EXTRACTS the four params (grammar / target-form / grounding /
knowns) from the read text + its HELD primitives, INSTANTIATES the template, and
SELF-VERIFIES. Only a self-verified generated faculty is returned/wired.

    generate_faculty(gap)  ->  a Faculty (instantiated template)  OR  a named stall.

THE GENERABLE CLASS (the honest reach, inherited from prose_to_operation): a faculty
that READS a GROUP-CONSTRUCTION article and grounds its operation to the HELD glue
machinery. The four params come from READING + held primitives, NOT injected:

  · grammar     = parse_presentations  — the input register is the group-presentation
                  notation <gens | rels> EVERY group-construction article writes (a
                  linguistic universal of the prose, cmsg156). HELD; selected because
                  the read text CARRIES presentations (the generator CONFIRMS this by
                  parsing >=1 from the fetched text — provenance, not assumed).
  · target_form = extract_operations    — the structured FORM is the DELTA the prose's
                  presentation states (generators/relations ADDED). HELD; the OP KIND
                  is READ off the prose (add_stable_generator_conjugation / union_only
                  / union_plus_identify), not supplied.
  · grounding   = ground_operation      — the extracted op -> the generic held glue-
                  applier. HELD; selected because the form is a presentation-delta.
  · knowns      = the textbook glue cases, KEYED to the op KIND the generator READ
                  (a union op -> the separate-component known [rank 0]; an HNN op ->
                  the connected known [rank 2]). The known-objects are HELD textbook
                  surfaces (NONE a question's answer); WHICH known applies is fixed by
                  what was READ (the op kind), not injected.

The gap parameterizes WHICH article to read; the params fall out of READING that
article + the held primitives. DIFFERENT gaps -> DIFFERENT articles -> (potentially)
DIFFERENT op-kinds + DIFFERENT generated faculties. The generality (>=2 different
faculties from the SAME generator) is the donkey-check.

THE SELF-VERIFY GATE (cmsg133): a mis-instantiated faculty FAILS its knowns ->
REJECTED. A deliberately-wrong param-set (e.g. the union op verified against the HNN
known) self-rejects — shown in the demo.

THE META-SUB-WALL (honest reach): the generator inherits prose_to_operation's reach —
it generates faculties whose params are FORMULA/STRUCTURE-extractable from prose +
held-groundable, and STALLS where the params need INFERENCE (an article with no
presentation formula -> no grammar confirms -> the named stall). Report N generated /
which / the stall.

Faithful (CLAUDE.md): a WORLD-ADAPTER shell — it FETCHES (GET-only) + SEQUENCES the
extraction (the held parse/extract/ground) + instantiates the held template + runs the
held self-verify. The shell injects NO param (the grammar/form/grounding are HELD
primitives selected by what the text carries; the knowns are HELD textbook objects
keyed by the READ op kind). NO LLM. NO Rust. Math/reading/web domain only. The answer
(671579) is NEVER read. The speech path is untouched.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, Tuple

from domains import faculty_template as _FT
from domains import prose_to_operation as _p2o


# ===========================================================================
# THE GAP — what input/output the agent needs (cmsg143-145 articulation). A gap
# names the CONSTRUCTION the agent wants a faculty for + WHERE to read it (the article
# titles, the agent's retrieval decision) + a human-readable need. The params are NOT
# in the gap — they are EXTRACTED from reading the article.
# ===========================================================================

@dataclass
class Gap:
    name: str                          # the construction the agent needs a faculty for
    titles: List[str]                  # the article(s) to READ (GET-only)
    need: str                          # the articulated need (what input->output)


# ===========================================================================
# THE GENERATED FACULTY — the instantiated template + the PROVENANCE (the read text +
# the held grounding selected). The provenance is the proof the params came from
# READING, not injection.
# ===========================================================================

@dataclass
class GeneratedFaculty:
    gap: Gap
    faculty: Optional[_FT.Faculty] = None
    generated: bool = False
    op_kind: Optional[str] = None             # the op kind READ off the prose
    operation: Any = None                     # the extracted Operation (the read delta)
    glue: Optional[Callable] = None           # the verified glue applier (piece,i,j)->piece
    provenance: dict = field(default_factory=dict)
    self_verify_rows: List[dict] = field(default_factory=list)
    self_verified: bool = False
    stall: str = ""


# ---------------------------------------------------------------------------
# THE HELD KNOWN-OBJECTS for the SELF-VERIFY — textbook glue cases (NONE the answer).
# WHICH known applies is keyed by the READ op kind (the existing pipeline's
# discrimination): a union/amalgam op must read rank 0 on the separate-component
# cases; an HNN op must read rank 2 on the connected case. These are HELD surfaces.
# ---------------------------------------------------------------------------

def _held_known_probes():
    """The held textbook glue cases (the SAME the prose_to_operation pipeline holds).
    Built lazily from held Pieces; NONE is a question's answer."""
    from scripts.strict_compose_pants_structure import Piece
    from scripts import strict_compose_pants_structure as _CMP
    d1 = Piece(gens="", relators=[], boundaries=[""], components=1, note="disk")
    d2 = Piece(gens="", relators=[], boundaries=[""], components=1, note="disk")
    two_disks = (_CMP.disjoint_union(d1, d2), 0, 1)        # = S^2, rank 0
    ann0 = Piece(gens="t", relators=[], boundaries=["t", "t"], components=1,
                 note="annulus")
    dsk = Piece(gens="", relators=[], boundaries=[""], components=1, note="disk")
    ann_disk = (_CMP.disjoint_union(ann0, dsk), 0, 2)      # = disk, rank 0
    ann = Piece(gens="s", relators=[], boundaries=["s", "s"], components=1,
                note="annulus")
    ann_self = (ann, 0, 1)                                 # = torus, rank 2
    return two_disks, ann_disk, ann_self


# the textbook rank each op KIND must reproduce on each known (the held discrimination
# — read off the op kind the generator EXTRACTED, not injected per faculty).
_KIND_KNOWNS = {
    # union family: rank 0 on the two separate-component cases (the loop is killed).
    "union_only": [("two disks glued = S^2 (separate)", "two_disks", 0),
                   ("annulus->disk = disk (separate)", "ann_disk", 0)],
    "union_plus_identify": [("two disks glued = S^2 (separate)", "two_disks", 0),
                            ("annulus->disk = disk (separate)", "ann_disk", 0)],
    # HNN: rank 2 on the connected self-glue (= torus).
    "add_stable_generator_conjugation":
        [("annulus self-glue = torus (connected)", "ann_self", 2)],
}


def _rank_of(piece):
    return piece.h1().free_rank if piece else None


# ===========================================================================
# THE GENERATOR — generate_faculty(gap): READ -> EXTRACT 4 params -> INSTANTIATE ->
# SELF-VERIFY. The params come from READING + held primitives; the shell injects none.
# ===========================================================================

def generate_faculty(gap: Gap, http_get: Optional[Callable] = None,
                     *, force_wrong_known: Optional[str] = None) -> GeneratedFaculty:
    """GENERATE a Faculty for `gap` by INSTANTIATING the template from READING.

    1. READ      — fetch the gap's article full text (GET-only; the provenance).
    2. EXTRACT   — the four params from the read text + held primitives:
         grammar=parse_presentations (CONFIRMED by parsing >=1 presentation from the
         text — provenance), target_form=extract_operations (the OP KIND read off the
         prose), grounding=ground_operation (held), knowns=the textbook glue cases
         KEYED to the READ op kind.
    3. INSTANTIATE — make_faculty(the four extracted params).
    4. SELF-VERIFY — run the grounded op on its keyed textbook knowns; a mis-
       instantiated faculty FAILS -> REJECTED (returned generated=False + the stall).

    `force_wrong_known` (donkey-check only): override the keyed known with a WRONG op
    kind's known -> the self-verify REJECTS the deliberately-wrong param-set. Off in
    normal generation.

    Returns a GeneratedFaculty; `generated=True` only for a self-verified faculty.
    The answer (671579) is never read. No param is injected by the shell."""
    result = GeneratedFaculty(gap=gap)

    # 1. READ (GET-only) — the provenance.
    fetched = _p2o.fetch_full_text(gap.titles, http_get)
    if fetched is None:
        result.stall = (f"corpus gap: no full-text article among {gap.titles} "
                        f"(GET-only) — cannot read the params from prose")
        return result
    result.provenance["read"] = {"title": fetched["title"], "url": fetched["url"],
                                 "source": fetched["source"],
                                 "textlen": len(fetched["text"])}
    text = fetched["text"]

    # 2a. EXTRACT grammar — CONFIRM the input register is the presentation notation by
    #     parsing >=1 presentation from the read text (provenance, not assumed). If the
    #     prose carries NO presentation, the grammar does not confirm -> the meta-sub-
    #     wall (a needs-inference construction).
    presentations = _p2o.parse_presentations(text)
    if not presentations:
        result.stall = (f"the read text carries NO group-presentation <gens|rels> — "
                        f"the grammar (parse_presentations) does not confirm; the "
                        f"operation needs INFERENCE, not formula-extraction (the meta-"
                        f"sub-wall: formula-extractable vs needs-inference)")
        result.provenance["grammar"] = "parse_presentations (UNCONFIRMED: 0 presentations)"
        return result
    result.provenance["grammar"] = (
        f"parse_presentations [HELD] — CONFIRMED: parsed "
        f"{len(presentations)} presentation(s) from the read text "
        f"(e.g. {presentations[0].raw[:60]!r})")

    # 2b. EXTRACT target_form — the OP KIND read off the prose's presentation delta.
    ops = [op for op in _p2o.extract_operations(text) if op.parse_ok]
    if not ops:
        result.stall = (f"presentations parsed but NO operational delta extracted "
                        f"(the prose states a presentation but no add/identify/union "
                        f"delta the held extractor reads) — needs-inference sub-wall")
        result.provenance["target_form"] = "extract_operations (0 parse_ok ops)"
        return result
    op = ops[0]
    result.op_kind = op.kind
    result.provenance["target_form"] = (
        f"extract_operations [HELD] -> op KIND READ off the prose: {op.kind!r}; "
        f"evidence: {op.evidence[:110]!r}")

    # 2c. EXTRACT grounding — the held glue applier for the extracted op.
    apply_fn = _p2o.ground_operation(op)
    if apply_fn is None:
        result.stall = f"the extracted op {op.kind!r} did not ground to a held applier"
        return result
    result.provenance["grounding"] = (
        f"ground_operation [HELD] -> the generic glue-applier, parameterized by the "
        f"read op kind {op.kind!r} (gens+{op.gens_added}, rels+{op.rels_added})")

    # 2d. EXTRACT knowns — the textbook glue cases KEYED to the READ op kind (the held
    #     discrimination). The known-objects are HELD textbook surfaces.
    kind_for_known = force_wrong_known or op.kind          # donkey-check override
    known_specs = _KIND_KNOWNS.get(kind_for_known)
    if known_specs is None:
        result.stall = (f"no textbook known for op kind {kind_for_known!r} "
                        f"(cannot self-verify this op family)")
        return result
    two_disks, ann_disk, ann_self = _held_known_probes()
    probe_table = {"two_disks": two_disks, "ann_disk": ann_disk, "ann_self": ann_self}
    knowns = [_FT.Known(name, probe_table[probe_key], expected_rank)
              for (name, probe_key, expected_rank) in known_specs]
    result.provenance["knowns"] = (
        f"textbook glue cases [HELD], KEYED to the READ op kind {kind_for_known!r}: "
        f"{[k.name for k in knowns]} (NONE a question's answer)")

    # 3. INSTANTIATE the template with the four EXTRACTED params.
    def grammar(raw_text):
        return raw_text

    def target_form(raw_text):
        ex = [o for o in _p2o.extract_operations(raw_text) if o.parse_ok]
        return (ex, f"extracted {len(ex)} parse_ok op(s) from the read prose")

    def grounding(form_op):
        af = _p2o.ground_operation(form_op)
        if af is None:
            return None

        def run(probe):                 # probe = (piece, i, j) -> the glued free rank
            piece, i, j = probe
            return _rank_of(af(piece, i, j))
        return run

    faculty = _FT.make_faculty(f"generated::{gap.name}", grammar, target_form,
                               grounding, knowns)
    result.faculty = faculty

    # 4. SELF-VERIFY — run the grounded op on its keyed textbook knowns (the gate).
    #    Build the runnable for the SPECIFIC extracted op + check its knowns.
    runnable = grounding(op)
    if runnable is None:
        result.stall = "the extracted op did not yield a runnable (grounding failed)"
        return result
    ok, rows = faculty.self_verify(runnable)
    result.self_verify_rows = rows
    result.self_verified = ok
    if not ok:
        result.stall = (f"SELF-VERIFY REJECTED the generated faculty: the grounded op "
                        f"{op.kind!r} did not reproduce its textbook known(s) "
                        f"(mis-instantiated -> the gate held)")
        result.generated = False
        return result

    # the verified faculty carries its extracted Operation + the held glue applier so
    # the agent can APPLY it (the fixpoint: generated + used). The applier is the SAME
    # held ground_operation the self-verify passed on.
    result.operation = op
    result.glue = apply_fn
    result.generated = True
    return result


# ===========================================================================
# THE FIXPOINT-CLOSURE (cmsg159) — generate_faculty_grounded: the faculty-generator
# now GENERATES THE GROUNDING from reading (grounding_generator.generate_grounding),
# instead of FIXING it to prose_to_operation's glue applier. The GROUNDING param of
# the template is no longer a single fixed shape — it is GENERATED per operation by
# reading the operation's defining formula and composing its HELD primitives. So the
# SAME generator produces GENUINELY DIFFERENT faculties (different groundings): an
# euler faculty grounded as betti+alternating-fold, a genus faculty grounded as
# euler+divide. The meta-ability TURNS: generate the SHAPE, not just the operation.
# ===========================================================================

@dataclass
class FormulaGap:
    """A gap whose faculty's GROUNDING is GENERATED from reading a defining formula
    (not fixed to prose_to_operation). Names the operation + where its formula lives."""
    name: str
    operation: str                     # the operation whose grounding to generate
    titles: List[str]                  # the article(s) the defining formula lives in
    need: str


@dataclass
class GroundedFaculty:
    gap: "FormulaGap"
    faculty: Optional[_FT.Faculty] = None
    generated: bool = False
    grounding: Any = None              # the GeneratedGrounding (read+composed+verified)
    composition_parts: List[str] = field(default_factory=list)
    self_verified: bool = False
    provenance: dict = field(default_factory=dict)
    stall: str = ""


def generate_faculty_grounded(gap: "FormulaGap",
                              http_get: Optional[Callable] = None
                              ) -> "GroundedFaculty":
    """GENERATE a faculty for `gap` whose GROUNDING is generated from READING the
    operation's defining formula (grounding_generator.generate_grounding) — the
    fixpoint-closure. The template's GROUNDING param is the generated held-primitive
    composition (NOT prose_to_operation's fixed glue applier), so different gaps yield
    DIFFERENT groundings (different held primitives composed per the read formula).

    The faculty's four params:
      · grammar     = identity over the known-space complex (the input register is a
                      space; the grammar hands it through to the generated grounding);
      · target_form = the generated grounding's verified known spaces (the forms);
      · grounding   = THE GENERATED GROUNDING'S runnable (read+composed+self-verified)
                      — the FLEX: generated per operation, not fixed;
      · knowns      = the operation's known spaces vs known values (held textbook).

    Returns a GroundedFaculty; generated=True only when the grounding GENERATED from
    reading self-verifies. The answer is never read; the shell authors no composition.
    """
    from domains import grounding_generator as _GG
    from domains import reason as _reason
    from domains import gf2_cohomology as _gf2

    result = GroundedFaculty(gap=gap)

    # GENERATE the grounding from reading (read formula -> parsed tree -> composed
    # held primitives -> self-verified). This IS the flex: the grounding shape is
    # generated, not fixed.
    gg = _GG.generate_grounding(gap.operation, gap.titles, http_get)
    result.grounding = gg
    result.provenance = dict(gg.provenance)
    if not gg.generated:
        result.stall = (f"the grounding for {gap.operation!r} did not generate from "
                        f"reading: {gg.stall}")
        return result
    result.composition_parts = list(gg.composition_parts)
    result.self_verified = gg.self_verified

    # build the held capability set carrying the generated grounding (re-derive into a
    # caps dict the faculty's runnable evaluates over — the SAME read+composed tree).
    caps = dict(_reason.CAPABILITIES)
    import substrate_rs as _native
    from domains import grounded_representation as _gr
    sub = _native.Substrate()
    _gr.open_grounding_productions(sub)
    # re-ground the operation (and its leaf chain) into caps via the generated formula.
    leaf = gg.read.leaf
    _GG._ground_leaf(sub, leaf, caps, http_get)
    from domains import compute_grounding as _cg
    _cg.ground_computation(sub, gap.operation, gg.held_formula, capabilities=caps)

    shape = gg.read.operator_shape
    spaces = {"S^2": _gf2.KNOWN_SURF["S^2"], "T^2": _gf2.KNOWN_SURF["T^2"],
              "RP^2": _gf2.KNOWN_SURF["RP^2"]}
    known_vals = _GG._KNOWN_VALUES.get(gap.operation, {})

    # the GROUNDING param = the generated grounding's runnable: a probe (a space name)
    # -> the composed operation evaluated over the held tree. This is the FLEX param —
    # GENERATED from reading, different per operation.
    def grounding(form_op):
        def run(probe):                      # probe = a known-space name
            cx = spaces[probe]
            bind = ({gap.operation: {"complex": cx}}
                    if shape == "divide_by_const"
                    else {gap.operation: {"complex": cx, "n": 3}})
            return _reason.solve(bind, {}, caps)
        return run

    def grammar(raw):
        return raw

    def target_form(raw):
        return ([gap.operation], f"the generated grounding for {gap.operation!r}")

    knowns = [_FT.Known(f"{name} ({gap.operation})", name, val)
              for name, val in known_vals.items()]

    faculty = _FT.make_faculty(f"generated_grounded::{gap.name}", grammar,
                               target_form, grounding, knowns)
    result.faculty = faculty

    # SELF-VERIFY the instantiated faculty (the template's gate on the generated
    # grounding's runnable).
    runnable = grounding(gap.operation)
    ok, rows = faculty.self_verify(runnable)
    result.self_verified = ok
    if not ok:
        result.stall = (f"the instantiated faculty's generated grounding failed its "
                        f"knowns: {rows}")
        result.generated = False
        return result
    result.generated = True
    return result


__all__ = ["Gap", "GeneratedFaculty", "generate_faculty",
           "FormulaGap", "GroundedFaculty", "generate_faculty_grounded"]
