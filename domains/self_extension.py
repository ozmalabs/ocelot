"""self_extension — THE FACTORY THAT BUILDS FACTORIES: the agent's OWN self-
extension loop, composed from components it ALREADY holds and RUN by the agent, with
the orchestrator only KICKING OFF and REPORTING.

Across the arc the ORCHESTRATOR hand-fired each rung (the construction operators, the
grounding faculty, the theorem-comprehension, the self-verify, the look-up loop). That
is the orchestrator BEING the factory. This module composes the agent's OWN held
components into ONE autonomous loop the AGENT runs end-to-end on a stalled question:

    extend(stall):                          # ONE stalled (object, asked-invariant)
      1. DIAGNOSE   the structural gap — elevator.diagnose_wall (the climbing spike,
                    cmsg97-98): READ the stalled op's def + reduction, CLASSIFY the
                    wall-KIND (reducible / needs-primitive / acquirable / deep-read /
                    genuinely-hard), name the SPIKE (the required action).
      2. DESIGN     the new structure from the agent's understanding —
                    ground_definition.comprehend_definition (the (operator/family/
                    quantity) read) + _match_invariant: comprehend the gap's DEFINITION
                    into a structure the held tier can carry. NO orchestrator authoring.
      3. BUILD      it — the agent's BUILD path, by the spike's kind:
                      · ACCRETION (a reduction to / composition over HELD structure):
                        ground_definition.seek_reduction -> ground_reductions
                        (read-theorem -> comprehend_theorem -> compose HELD predicates)
                        OR a held FOLD. The new structure REDUCES to the held tier.
                      · DESIGN-FROM-SCRATCH (a genuinely-new representation the agent
                        does NOT hold): runtime_design.specify (the agent specifies
                        WHAT). The honest open core.
      4. SELF-VERIFY it — ground_definition.verify_vs_known / ground_reductions.
                    verify_grounded (cmsg117/133, the gate): RUN the built structure on
                    KNOWN objects + check vs KNOWN values. A structure that FAILS a
                    known is REJECTED (the loop does NOT wire an unverified structure).
      5. WIRE       the verified structure into the held capability registry (it
                    becomes held) — the same additive install the construction
                    operators use.
      6. RE-ATTEMPT the stalled compute over the now-wired structure; READ the answer
                    ONLY here, to check the re-attempt (NO reverse-engineering).
      7. RECURSE    if still stalled, DIAGNOSE the NEXT gap (a different invariant /
                    sub-op) and loop — bounded by max_rungs.

THE COMPOSITION (the agent's OWN components, sequenced by the loop — NOT the
orchestrator's per-step dispatch):

    · DIAGNOSE     elevator.Elevator.diagnose_wall      (the climbing spike)
    · DESIGN       ground_definition.comprehend_definition + _match_invariant
    · BUILD        ground_definition.seek_reduction / ground_reductions / a held FOLD
                   (accretion) | runtime_design.agent_specify_* (design-from-scratch)
    · SELF-VERIFY  ground_definition.verify_vs_known / ground_reductions.verify_grounded
    · WIRE         caps[op] = built.runnable        (the held-tier install)
    · RE-ATTEMPT   the wired compute over the object  (answer read at END only)
    · RECURSE      the loop, on the next gap

THE HONEST DISTINCTION (reported per rung — the deepest point):

  · ACCRETION (the achievable turn): the agent acquires a REDUCTION to / composition
    over structure it ALREADY holds — read a theorem, compose held predicates, fold a
    held quantity — autonomously, self-verified. A real turn of the factory.
  · DESIGN-FROM-SCRATCH (the open problem): the agent designs a NEW REPRESENTATION it
    does NOT hold (a new object encoding, not a reduction to held structure). The hard
    core — the agent has limited architecture-vocabulary. The loop REACHES it and
    NAMES it (the meta-residual), but the BUILD step stalls there: the agent can
    DIAGNOSE the gap + DESIGN the contract (specify WHAT), but cannot BUILD the new
    representation autonomously (it would need the orchestrator to author the operator
    — which is the factory frontier, NOT a success).

The loop reports, per rung, WHICH meta-step it reached: diagnosed / designed / built /
self-verified / wired / re-attempted — and where the AUTONOMOUS LOOP ITSELF stalls
(the meta-residual = the precise location of the factory-that-builds-factories
frontier). One rung ACCRETED autonomously (self-verified) is the factory's first real
turn; a meta-stall is a SUCCESSFUL honest result — it names what the agent can't yet
self-drive.

INTEGRITY (CLAUDE.md — a WORLD-ADAPTER SHELL over the agent's machinery). No `if`
decides what a structure MEANS (the meaning is the comprehended structure / the read
theorem, graph data). Every built structure SELF-VERIFIES vs KNOWN before it is wired;
an unverified structure is REJECTED. The answer is read ONLY at the re-attempt's check
(NO reverse-engineering). The agent designs+builds from its OWN understanding — the
orchestrator does NOT author the structure. NO LLM, NO Rust. Math/reading domain ONLY
— the speech/audio path is untouched.

See [[ozma_agent_designs_runtime]] (specify WHAT, the open from-scratch core) /
[[ozma_synthesizes_own_gaps]] / [[ozma_HLE_derivation_engine]] /
[[ozma_meta_abilities_are_leverage]] / [[ozma_capability_is_binary_admissibility]] /
[[ozma_agent_writes_its_own_code]].
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from domains import ground_definition as _gd
from domains import ground_reductions as _gred
from domains import reason as _reason


# ---------------------------------------------------------------------------
# THE STALL — the unit the loop runs on: a stalled (object, asked-invariant) the
# held pipeline could not close. The `gap_op` is the stalled op (the invariant id /
# def the diagnose reads); `definition` the gap's DEFINITION (the design source, a
# READ gloss — NOT the answer); `object_desc` the held object-description the wired
# compute runs on at the re-attempt; `answer` the key, READ ONLY at the END.
# ---------------------------------------------------------------------------

@dataclass
class Stall:
    """A real stalled question the self-extension loop runs on."""
    question_id: str
    asked: str                       # the asked invariant (prose, for the report)
    gap_ops: list[str]               # the stalled op-id(s) (a tuple => recurse)
    definition: dict[str, str]       # gap_op -> its DEFINITION (the design source)
    object_desc: dict[str, Any]      # the held object-description for the re-attempt
    answer: Any = None               # the key — READ ONLY at the re-attempt check
    # an optional EXPECTED-per-gap key the re-attempt checks against (for a tuple
    # invariant where the asked answer is a tuple; gap_op -> its component value).
    answer_per_gap: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# THE RUNG — the trace of ONE turn of the factory on one gap: which meta-step it
# reached (the factory frontier, located), the built structure, the self-verify, the
# re-attempt. This is the HONEST per-rung provenance.
# ---------------------------------------------------------------------------

# the meta-steps, in order — the rung records the LAST it reached (the others before
# it succeeded; the one after is where the AUTONOMOUS LOOP stalled, if it did).
META_STEPS = ["diagnose", "design", "build", "self_verify", "wire", "re_attempt"]


@dataclass
class Rung:
    gap_op: str
    reached: str                     # the last META_STEP the loop reached
    kind: str = ""                   # 'accretion' | 'design_from_scratch' | ''
    wall_kind: str = ""              # the climbing-spike's wall-KIND (the diagnosis)
    spike: str = ""                  # the spike (the required action)
    designed: str = ""               # the comprehended structure (the design)
    built: bool = False              # did the BUILD produce a runnable structure?
    self_verified: Optional[bool] = None   # the gate verdict (vs KNOWN)
    wired: bool = False
    re_attempt_value: Any = None
    re_attempt_ok: Optional[bool] = None   # vs the key (read at END only)
    note: str = ""

    def line(self) -> str:
        v = ("" if self.self_verified is None
             else ("  verify=%s" % ("OK" if self.self_verified else "REJECTED")))
        r = ("" if self.re_attempt_ok is None
             else ("  re-attempt=%s (%s)" % (
                 "MATCH" if self.re_attempt_ok else "MISMATCH",
                 self.re_attempt_value)))
        return (f"RUNG[{self.gap_op}] reached={self.reached.upper()} "
                f"kind={self.kind or '—'} wall={self.wall_kind or '—'}{v}{r}\n"
                f"        {self.note}").rstrip()


@dataclass
class Extension:
    """The RESULT of the autonomous self-extension run on a stall: the per-gap rungs,
    whether any rung ACCRETED (self-verified + wired + re-attempted), and the
    META-RESIDUAL (the precise meta-step the autonomous loop stalled at — the
    factory-that-builds-factories frontier, located)."""
    question_id: str
    rungs: list[Rung] = field(default_factory=list)
    accreted: list[str] = field(default_factory=list)   # gap_ops accreted autonomously
    meta_residual: str = ""                              # where the autonomous loop stalls

    def trace(self) -> str:
        return "\n".join(r.line() for r in self.rungs)


# ---------------------------------------------------------------------------
# THE DRIVER — the agent's self-extension loop. Construct it over the held capability
# registry (a copy of reason.CAPABILITIES); call `extend(stall)`. The driver
# SEQUENCES the agent's OWN components (diagnose_wall + design + build + self-verify +
# wire + re-attempt); it adds NO reasoning, authors NO structure, holds NO state
# beyond the held caps it MUTATES as structures wire (they become held).
# ---------------------------------------------------------------------------

class SelfExtensionDriver:
    def __init__(self, *, capabilities: Optional[dict] = None, max_rungs: int = 4,
                 persist: bool = False):
        # the held tier the wired structures join (the SAME registry the construction
        # operators / grounded reductions install into). MUTATED as the loop wires.
        self.caps = dict(_reason.CAPABILITIES) if capabilities is None \
            else capabilities
        self.max_rungs = max_rungs
        # PERSIST-ON-WIRE (off by default; the loop's behaviour is otherwise
        # unchanged). When on, a rung that SELF-VERIFIED + WIRED also records a
        # durable provenance manifest of the accreted reduction (the invariant it
        # reduced to held structure + the KNOWN values the gate checked) via the
        # self_authored managed dir — coupling durability to the gate that already
        # ran (the driver self-verifies BEFORE it wires). The faculty's runnable is a
        # closure over held reductions (not a re-derivable gloss), so this persists
        # the agent's READ provenance, NOT a re-groundable composition; the
        # composition-tier RELOAD (re-derive + recompute) is validated on Path A
        # (compute_grounding / betti), where the gloss re-grounds deterministically.
        self.persist = persist
        self.persisted: list[dict] = []   # what this run made durable (for the report)

    # === DIAGNOSE — the climbing spike (elevator.diagnose_wall), the agent's own ===
    # The diagnose reads the gap's DEFINITION + reduction and classifies the wall.
    # Here we run the agent's classification directly over the gap's design source
    # (the comprehended structure), the SAME judgment the elevator's spike makes.
    def _diagnose(self, gap_op: str, definition: str) -> dict:
        """DIAGNOSE the structural gap: comprehend the gap's definition into its
        structure (the agent's ground_definition read), classify whether it REDUCES
        to held structure (ACCRETION) or needs a NEW representation (DESIGN-FROM-
        SCRATCH). This is the climbing-spike's read — the agent's machinery, not a
        hand-coded per-op table.

        The invariant is identified TWO ways, both the agent's own: (1) read off the
        definition's defining markers (ground_definition._match_invariant, the
        prose-structure read), falling back to (2) the gap_op id itself — the agent's
        OWN NAME for the invariant it is diagnosing (the canonical invariant key the
        gap was raised under). Using the gap's own name as the invariant_hint is the
        SAME `invariant_hint` seek_reduction already accepts; it is NOT orchestrator
        authoring (no structure / compute supplied — only the agent identifying WHICH
        held reduction matches the gap it named). A prose-miss must NOT mis-report an
        ACCRETABLE gap as the open core — the held store is consulted under the gap's
        canonical name before concluding design-from-scratch."""
        struct = _gd.comprehend_definition(definition)
        # the agent's prose-structure read, then its OWN canonical name for the gap.
        inv = _gd._match_invariant(struct, None) or gap_op
        # the spike asks: does the gap's invariant have a READ reduction to held
        # structure (a held compute) — i.e. is it ACCRETABLE? seek_reduction is the
        # agent's own is-acquirable read over the reduction store, under the gap's
        # canonical invariant id (the hint), so a comprehension prose-miss does not
        # FALSELY classify a held-reducible gap as design-from-scratch.
        red = _gd.seek_reduction(struct, inv)
        if red is not None:
            return {"wall_kind": "acquirable_substructure", "spike": "recurse",
                    "kind": "accretion", "invariant": inv, "struct": struct,
                    "reduction": red,
                    "note": (f"the gap's definition comprehends to invariant "
                             f"{inv!r}; a READ reduction to HELD structure EXISTS "
                             f"(ground_reductions) -> ACCRETION (reduce to held)")}
        # no read reduction to held structure -> the gap needs a NEW representation
        # the agent does not hold: DESIGN-FROM-SCRATCH (the open core).
        return {"wall_kind": "genuinely_hard", "spike": "specify",
                "kind": "design_from_scratch", "invariant": inv, "struct": struct,
                "reduction": None,
                "note": ("the gap's definition does NOT reduce to held structure "
                         "(no read reduction; comprehends="
                         f"{struct.comprehended}) -> a NEW representation the agent "
                         "does NOT hold (DESIGN-FROM-SCRATCH, the open core)")}

    # === DESIGN — comprehend the gap into a structure the held tier can carry. ===
    # (Folded into _diagnose's comprehend; surfaced on the rung for the report.)

    # === BUILD — the agent's BUILD path, by the diagnosis's kind. ===
    def _build(self, diag: dict) -> dict:
        """BUILD the new structure. ACCRETION: the read reduction's grounded compute
        (ground_reductions: read-theorem -> comprehend_theorem -> compose HELD
        predicates) — a reduction to held structure. DESIGN-FROM-SCRATCH: the agent
        can specify the contract (WHAT) but cannot BUILD a new representation
        autonomously -> the BUILD STALLS (the meta-residual). Returns
        {built, runnable, note}."""
        if diag["kind"] == "accretion":
            red = diag["reduction"]
            # the built structure is the reduction's HELD compute (the grounded
            # reduction's clauses, composed from held predicates). This IS the
            # composition over held structure — the agent's build, not authored here.
            return {"built": True, "runnable": red.held_compute,
                    "reduction": red,
                    "note": (f"BUILT by ACCRETION: the read reduction reduces "
                             f"{diag['invariant']!r} to HELD structure "
                             f"(ground_reductions: read-theorem -> comprehend -> "
                             f"compose held predicates over the held free-product "
                             f"structure). Cite: {red.cite[:90]}")}
        # DESIGN-FROM-SCRATCH: the agent DESIGNS the contract (specify WHAT) but the
        # BUILD of a new REPRESENTATION it does not hold is the open core — it stalls.
        return {"built": False, "runnable": None,
                "note": ("BUILD STALLED (DESIGN-FROM-SCRATCH): the gap needs a NEW "
                         "representation the agent does NOT hold (e.g. a surface-with-"
                         "boundary CW-construction operator, beyond the held polygon-"
                         "word reader). The agent can DIAGNOSE the gap + DESIGN the "
                         "contract (specify WHAT), but cannot autonomously BUILD the "
                         "new object encoding — the orchestrator would have to author "
                         "the operator, which is the factory frontier, NOT a self-"
                         "driven turn.")}

    # === SELF-VERIFY — the gate: RUN the built structure vs KNOWN; reject on fail. ==
    def _self_verify(self, diag: dict) -> dict:
        """SELF-VERIFY the built structure vs KNOWN (cmsg117/133, the gate). RUN the
        reduction's held compute on its KNOWN objects + check vs the KNOWN values; a
        structure that FAILS a known is REJECTED. Returns {ok, got, expected}."""
        red = diag["reduction"]
        # the grounded-reduction store's own verify-vs-known (ground_reductions) —
        # the agent's gate, run over the textbook knowns (NONE the question's answer).
        inv = diag["invariant"]
        if inv in _gred.KNOWN_VALUES:
            return _gred.verify_grounded(inv)
        # fall back to the ground_definition faculty's verify (for ls_category etc.).
        return _gd.verify_vs_known(red)

    # === WIRE — install the verified structure into the held registry. ===
    def _wire(self, gap_op: str, runnable: Callable) -> None:
        """WIRE the self-verified structure into the held capability registry (it
        becomes held). The SAME additive install the construction operators use; the
        runnable takes the held object-description -> the invariant value."""
        self.caps[gap_op] = lambda a, _f=runnable: _f(a)

    # === PERSIST-ON-WIRE — make the accreted reduction durable (gate-coupled). ===
    def _persist_accretion(self, gap_op: str, diag: dict, ver: dict) -> None:
        """Record a self-verified+wired accretion as a durable provenance manifest in
        the self_authored managed dir. Coupled to the gate (called ONLY after the rung
        self-verified). Persists the agent's READ provenance (the invariant, the held
        reduction it accreted to, the KNOWN values the gate checked) — NOT a re-
        groundable composition (the reduction's runnable is a closure over held
        structure). Best-effort; a persist failure does not break the loop."""
        try:
            from domains import self_authored as _sa
            red = diag.get("reduction")
            cite = getattr(red, "cite", "") if red is not None else ""
            faculty = {
                "name": gap_op, "tier": _sa.TIER_COMPOSITION,
                # the accretion's provenance: the gloss is the gap's definition, which
                # the diagnose comprehended + the held reduction it reduced to. Reload
                # re-DIAGNOSES this gap (re-reads the same store); the runnable itself
                # is re-wired by re-running the loop, not from a bare gloss — named.
                "definition": diag.get("invariant", gap_op),
                "params": [], "primitives": ["held_reduction"],
                "composed_by": "self_extension.accretion",
                "verified_against": [{"gate": "verify_grounded/verify_vs_known",
                                      "got": ver.get("got"),
                                      "expected": ver.get("expected"),
                                      "reduction_cite": str(cite)[:120]}],
            }
            p = _sa.persist_self_authored(
                faculty, self_verified=True,
                verified_against=faculty["verified_against"])
            if p is not None:
                self.persisted.append({"gap_op": gap_op, "path": str(p)})
        except Exception:
            pass

    # === RE-ATTEMPT — run the wired compute over the object; check at END only. ===
    def _re_attempt(self, gap_op: str, object_desc: dict,
                    expected: Any) -> dict:
        """RE-ATTEMPT the stalled compute over the now-wired structure, then READ the
        key (END only) to check. NO reverse-engineering — the compute is fixed before
        the key is read."""
        try:
            val = self.caps[gap_op](object_desc)
        except Exception as e:                       # noqa: BLE001
            return {"value": None, "ok": None, "note": f"re-attempt error: {e}"}
        ok = None
        if expected is not None:
            ok = (str(val) == str(expected))
        return {"value": val, "ok": ok, "note": ""}

    # =======================================================================
    # extend(stall) — THE AUTONOMOUS SELF-EXTENSION LOOP. The agent runs every step.
    # =======================================================================
    def extend(self, stall: Stall) -> Extension:
        """RUN the agent's self-extension loop on a stalled question: for each gap op
        (bounded by max_rungs, the RECURSE), DIAGNOSE -> DESIGN -> BUILD -> SELF-
        VERIFY -> WIRE -> RE-ATTEMPT. The agent runs ALL of it; the orchestrator only
        called this. Returns the Extension with the per-gap rungs + the HONEST
        outcome (accreted rungs + the meta-residual)."""
        ext = Extension(question_id=stall.question_id)
        for gap_op in stall.gap_ops[: self.max_rungs]:
            definition = stall.definition.get(gap_op, "")
            rung = Rung(gap_op=gap_op, reached="diagnose")

            # 1. DIAGNOSE — the climbing spike.
            diag = self._diagnose(gap_op, definition)
            rung.wall_kind = diag["wall_kind"]
            rung.spike = diag["spike"]
            rung.kind = diag["kind"]
            # the DESIGN the agent comprehended: the (operator/family/quantity) when
            # the quantifier binder parsed, ELSE the identified invariant id + the
            # READ reduction it accreted to (an accretable gap whose def gloss had no
            # quantifier surface still has a real, named design — the held reduction).
            if diag["struct"].comprehended:
                rung.designed = diag["struct"].line()
            elif diag["kind"] == "accretion":
                rung.designed = (f"invariant={diag['invariant']} -> READ reduction to "
                                 f"held structure ({diag['reduction'].cite[:70]})")
            else:
                rung.designed = f"(uncomprehended: {definition[:60]!r})"
            rung.note = diag["note"]
            rung.reached = "design"        # the diagnose comprehended the design.

            # 3. BUILD.
            built = self._build(diag)
            rung.built = built["built"]
            if not built["built"]:
                # the BUILD stalled (design-from-scratch) — the meta-residual. Record
                # the rung at its frontier + do NOT wire an unbuilt structure.
                rung.note = built["note"]
                ext.rungs.append(rung)
                if not ext.meta_residual:
                    ext.meta_residual = (
                        f"BUILD (gap {gap_op!r}, kind=design-from-scratch): the "
                        f"autonomous loop DIAGNOSED the gap + DESIGNED the contract, "
                        f"but cannot autonomously BUILD a NEW representation it does "
                        f"not hold — the precise factory frontier.")
                continue
            rung.reached = "build"
            rung.note = built["note"]

            # 4. SELF-VERIFY — the gate (reject on a KNOWN failure).
            ver = self._self_verify(diag)
            rung.self_verified = bool(ver.get("ok"))
            if not rung.self_verified:
                rung.note = (rung.note + f" | SELF-VERIFY REJECTED: a KNOWN failed "
                             f"(got {ver.get('got')}, expected {ver.get('expected')})"
                             f" -> NOT wired (the loop does not wire an unverified "
                             f"structure).")
                ext.rungs.append(rung)
                if not ext.meta_residual:
                    ext.meta_residual = (
                        f"SELF-VERIFY (gap {gap_op!r}): the built structure FAILED a "
                        f"KNOWN -> REJECTED (the gate held; an unverified structure "
                        f"is not wired).")
                continue
            rung.reached = "self_verify"

            # 5. WIRE — install the verified structure into the held tier.
            self._wire(gap_op, built["runnable"])
            rung.wired = True
            rung.reached = "wire"

            # PERSIST-ON-WIRE — couple durability to the gate that JUST passed (the
            # rung self-verified before it wired). Record the accreted reduction's
            # provenance to the self_authored managed dir so the accretion is durable.
            # An unverified rung never reaches here (it continued above), so this only
            # persists what the gate passed — the same coupling Path A enforces.
            if self.persist:
                self._persist_accretion(gap_op, diag, ver)

            # 6. RE-ATTEMPT — run the wired compute; check the key (END only).
            expected = stall.answer_per_gap.get(gap_op, stall.answer)
            ra = self._re_attempt(gap_op, stall.object_desc, expected)
            rung.re_attempt_value = ra["value"]
            rung.re_attempt_ok = ra["ok"]
            rung.reached = "re_attempt"
            if ra["note"]:
                rung.note = rung.note + " | " + ra["note"]

            # the rung ACCRETED autonomously: diagnosed -> designed -> built ->
            # self-verified -> wired -> re-attempted, the factory's first real turn.
            ext.accreted.append(gap_op)
            ext.rungs.append(rung)

        if not ext.meta_residual:
            if ext.accreted:
                ext.meta_residual = (
                    "none reached this run: every gap ACCRETED autonomously "
                    "(diagnose->design->build->self-verify->wire->re-attempt, self-"
                    "verified). The factory turned; the next frontier is the first "
                    "DESIGN-FROM-SCRATCH gap (a new representation, not a reduction).")
            else:
                ext.meta_residual = "no gaps run"
        return ext


# ---------------------------------------------------------------------------
# THE GAP-SELECTOR TRIGGER — the agent DECIDES when to extend (not a caller).
#
# The agent's own gap selector (gap_prioritiser: pick_frontier / pick_with_guidance —
# the Argmax-over-CapabilityAxis ranking Term it evaluates natively) names WHICH
# capability axis is the frontier. This wires that pick as the TRIGGER for
# extend(stall): the loop reads the agent's frontier choice + the stalled gaps the
# host staged, and FIRES extend ONLY on the gap the agent's own selector picked — so
# the jabberwock decides when its self-extension loop runs, the orchestrator does not
# poke each gap. The DECISION (which gap) is the gap_prioritiser Term; this is the
# mechanical I/O that routes the agent's own pick into the loop.
# ---------------------------------------------------------------------------

def trigger_from_frontier(substrate, stalls: dict, *, capabilities=None,
                          persist: bool = False, max_rungs: int = 4,
                          guided: bool = False, frontier_rank: float = 0.0):
    """RUN the agent's gap selector, then FIRE extend() on the gap IT picked.

    `stalls` maps a capability-key (or gap_op) -> a Stall the host staged for that gap.
    The agent's gap_prioritiser picks the frontier CapabilityAxis natively; this routes
    the pick to its matching Stall and runs the self-extension loop on it. The agent
    chose WHEN to extend (its own ranking Term), not a caller iterating every gap.

    Returns {pick, matched, extension} — the agent's pick, whether a staged Stall
    matched it, and the Extension result (None if no match / no gaps). Best-effort: if
    the selector finds no axes, returns {pick:None}."""
    from domains import gap_prioritiser as _gp
    if guided:
        pick = _gp.pick_with_guidance(substrate, frontier_rank)
    else:
        pick = _gp.pick_frontier(substrate)
    if pick is None:
        return {"pick": None, "matched": None, "extension": None}
    # route the picked axis (its capability_keys / gap_text) to a staged Stall. The
    # match is mechanical: a Stall keyed by any of the pick's capability_keys, or by a
    # gap_op the pick names. No decision — the DECISION (which axis) was the Term's.
    keys = [str(k).lower() for k in pick.get("capability_keys", [])]
    matched_key = None
    for key, stall in stalls.items():
        kl = str(key).lower()
        if kl in keys or any(kl in k or k in kl for k in keys):
            matched_key = key
            break
        if stall.gap_ops and any(go.lower() in keys for go in stall.gap_ops):
            matched_key = key
            break
    if matched_key is None:
        return {"pick": pick, "matched": None, "extension": None}
    driver = SelfExtensionDriver(capabilities=capabilities, max_rungs=max_rungs,
                                 persist=persist)
    ext = driver.extend(stalls[matched_key])
    return {"pick": pick, "matched": matched_key, "extension": ext,
            "persisted": driver.persisted}


__all__ = ["Stall", "Rung", "Extension", "SelfExtensionDriver", "META_STEPS",
           "trigger_from_frontier"]
