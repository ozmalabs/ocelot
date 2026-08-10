"""faculty_template — THE FACULTY-GENERATOR (the fixpoint / the meta-ability).

cmsg157: every faculty this session (comprehend_theorem, ground_definition,
construction_operators, prose_to_operation, the pi_1-verifier) is the SAME SHAPE:

    COMPREHEND a raw input  --grammar-->  a structured FORM
        -->  GROUND the form to HELD primitives  -->  a RUNNABLE
        -->  SELF-VERIFY the runnable vs KNOWN cases  -->  WIRE (or REJECT).

They differ in FOUR parameters: (grammar, target_form, grounding, knowns). One
shape, four knobs. We have been HAND-instantiating it (the assistant, one at a
time). THE META-ABILITY = the agent INSTANTIATING the template from READING (extract
the 4 params from the math), gated by the self-verify. NOT design-from-scratch (the
cmsg136 wall) — instantiate-a-fixed-template-from-reading (frozen-core + bounded-flex).

This module is PART 1 — THE TEMPLATE (the frozen core). It is a SINGLE held
mechanism `make_faculty(grammar, target_form, grounding, knowns) -> Faculty`. The
Faculty's `apply(raw)` runs the SHARED control loop (parse -> form -> ground ->
runnable) and `self_verify()` runs the runnable on the knowns. There is NO faculty-
specific control flow here — the differences are ALL in the four params.

THE ANTI-VAPOR PROOF (faculty_template_redrive.py): the template RE-DERIVES the
existing faculties as INSTANCES. The instance is built from the existing faculty's
OWN sub-pieces — its grammar (parse), its form constructor, its grounding (compose
over held primitives), its knowns — handed in as the four params; the TEMPLATE's
control loop (not the existing faculty's top-level function) drives them, and the
instantiated faculty REPRODUCES the existing faculty's outputs (same extracted op /
same factor multiset / same verdicts) on the same inputs. If make_faculty just CALLED
prose_to_operation.extract_operations internally it would be a wrapper (VOID); the
params are the faculty's PARTS, the loop is the template's.

No LLM (the loop authors no per-faculty code — it composes the four params). No Rust.
Math/reading domain only. The speech path is untouched.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, Tuple


# ===========================================================================
# THE FOUR PARAMETERS — the knobs every faculty differs in. Each is a callable
# or a data list; the template's control loop composes them. They are NOT the
# faculty (the faculty IS the instantiated template) — they are the faculty's PARTS.
# ===========================================================================

# (1) GRAMMAR: raw input -> a structured FORM (the COMPREHEND step). For
#     prose_to_operation this is "parse the <gens|rels> presentation + read the
#     delta"; for the pi_1-verifier it is "Tietze-simplify + free-product
#     decompose". The grammar OWNS the input register; the template just calls it.
Grammar = Callable[[Any], Any]

# (2) TARGET_FORM: the form-shape CONTRACT — given the grammar's output, return the
#     list of structured forms (candidates) the grounding can consume, or [] when
#     nothing parsed. This NORMALISES the grammar output to the form the grounding
#     expects (a delta-op, a factor-presentation, an implication-triple). It is the
#     "structured form" of the shape — the bridge between an input-grammar and a
#     grounding. Returns (forms, note).
TargetForm = Callable[[Any], Tuple[List[Any], str]]

# (3) GROUNDING: a structured FORM -> a RUNNABLE over held primitives (the GROUND
#     step). Selects/composes the held primitive the form names (the generic
#     glue-applier for an op; the factor-recognizer for a presentation; the held
#     predicate for an implication). Returns None for a form it cannot ground.
Grounding = Callable[[Any], Optional[Callable]]

# (4) KNOWNS: the SELF-VERIFY cases — a list of (name, probe_input, expected). The
#     template runs the grounded runnable on each probe and checks the output. NONE
#     is a question's answer; all are textbook. `check` compares got vs expected.
@dataclass
class Known:
    name: str
    probe: Any                       # the input handed to the runnable
    expected: Any                    # the textbook expected output
    check: Callable[[Any, Any], bool] = lambda got, exp: got == exp


# ===========================================================================
# THE FACULTY — the instantiated template. ONE held mechanism; the control loop is
# IDENTICAL for every faculty, the four params carry all the difference.
# ===========================================================================

@dataclass
class Outcome:
    """The result of applying the faculty to one raw input."""
    raw: Any
    forms: List[Any] = field(default_factory=list)     # the comprehended forms
    grounded: List[Any] = field(default_factory=list)  # the form+runnable pairs
    selected: Optional[Any] = None                      # the self-verified form
    runnable: Optional[Callable] = None                 # its runnable
    ok: bool = False
    note: str = ""
    verify_rows: List[dict] = field(default_factory=list)


@dataclass
class Faculty:
    """A FACULTY = the four params + the shared control loop. Built ONLY by
    make_faculty (the frozen-core mechanism). `apply(raw)` comprehends -> grounds
    -> selects by self-verify; `self_verify(runnable)` is the gate."""
    name: str
    grammar: Grammar
    target_form: TargetForm
    grounding: Grounding
    knowns: List[Known]

    # ---- the SELF-VERIFY gate (the cmsg133 gate) — runs the grounded runnable on
    #      the knowns; a runnable that fails a known is REJECTED. ----
    def self_verify(self, runnable: Callable) -> Tuple[bool, List[dict]]:
        """Run `runnable` on every known probe + check vs the expected textbook
        value. Returns (all_pass, rows). A mis-grounded/wrong runnable FAILS its
        knowns -> the caller rejects it. This is the SAME gate for every faculty."""
        rows: List[dict] = []
        all_ok = True
        for kn in self.knowns:
            try:
                got = runnable(kn.probe)
                passed = bool(kn.check(got, kn.expected))
            except Exception as e:                       # a broken runnable
                got = f"(error: {e})"
                passed = False
            rows.append({"known": kn.name, "expected": kn.expected,
                         "got": got, "pass": passed})
            all_ok = all_ok and passed
        return all_ok, rows

    # ---- the SHARED CONTROL LOOP — comprehend -> form -> ground -> self-verify.
    #      IDENTICAL for every faculty; the params carry all the difference. ----
    def apply(self, raw: Any) -> Outcome:
        """COMPREHEND raw (grammar) -> structured FORMS (target_form) -> GROUND each
        (grounding) -> self-VERIFY -> SELECT the first self-verified form. Returns an
        Outcome. This is the frozen core: no faculty-specific branch lives here."""
        out = Outcome(raw=raw)
        # COMPREHEND: grammar reads the input register into its native structure.
        parsed = self.grammar(raw)
        # FORM: normalise to the structured forms the grounding consumes.
        forms, fnote = self.target_form(parsed)
        out.forms = forms
        out.note = fnote
        if not forms:
            out.note = fnote or "no structured form parsed (the comprehension wall)"
            return out
        # GROUND + SELF-VERIFY each candidate; SELECT the first that passes its knowns.
        for form in forms:
            runnable = self.grounding(form)
            if runnable is None:
                out.grounded.append({"form": form, "runnable": None,
                                     "verified": False,
                                     "note": "form did not ground to a held runnable"})
                continue
            ok, rows = self.self_verify(runnable)
            out.grounded.append({"form": form, "runnable": runnable,
                                 "verified": ok, "rows": rows})
            if ok and out.selected is None:
                out.selected = form
                out.runnable = runnable
                out.ok = True
                out.verify_rows = rows
        if not out.ok:
            out.note = ("comprehended + grounded but NO candidate passed its knowns "
                        "(the self-verify gate REJECTED every grounding)")
        return out


# ===========================================================================
# make_faculty — THE FROZEN-CORE MECHANISM. The SINGLE held producer of a Faculty
# from the four params. It composes NO per-faculty logic; it only wires the params
# into the shared loop. (A wrapper would call an existing faculty's top-level
# function here; this does not — it returns the parameterized Faculty whose loop the
# params drive.)
# ===========================================================================

def make_faculty(name: str, grammar: Grammar, target_form: TargetForm,
                 grounding: Grounding, knowns: List[Known]) -> Faculty:
    """Produce a runnable Faculty from the four parameters (grammar, target_form,
    grounding, knowns). The Faculty's control loop (Faculty.apply / .self_verify) is
    the frozen core — identical for every faculty; the four params are the flex. The
    existing faculties are INSTANCES of this (faculty_template_redrive.py re-derives
    them: same outputs, built from their own grammar/form/grounding/knowns)."""
    if not callable(grammar):
        raise TypeError("grammar must be callable (raw -> parsed)")
    if not callable(target_form):
        raise TypeError("target_form must be callable (parsed -> (forms, note))")
    if not callable(grounding):
        raise TypeError("grounding must be callable (form -> runnable | None)")
    knowns = list(knowns or [])
    return Faculty(name=name, grammar=grammar, target_form=target_form,
                   grounding=grounding, knowns=knowns)


__all__ = ["Grammar", "TargetForm", "Grounding", "Known", "Faculty", "Outcome",
           "make_faculty"]
