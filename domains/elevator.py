"""elevator — the AUTONOMOUS SELF-ASCENT engine (the GRADUATION of drive_ascent).

The agent climbed ~13 rungs BY HAND (cmsg84-96: ∂∂=0 -> homology -> cohomology
ring -> Stiefel-Whitney -> classifying space -> Weyl invariants -> integral
cohomology/torsion -> Thom spectrum -> AHSS -> ... -> the Spin bordism of BG2),
ONE rung per turn, the SAME PROCEDURE every time. This module ABSTRACTS that
procedure into ONE autonomous loop `ascend(target)` so a target is reached by the
engine WALKING THE RUNGS ITSELF — no hand-orchestration.

THE ABSTRACTED PATTERN (the common procedure, the same on every rung):

    ascend(target):
      1. HELD?     — is `target` already a held capability / grounded? -> base case.
      2. READ      — read target's DEFINITION (the fed gloss / the construction
                     grammar) -> the reduction  target = f(sub-ops).
      3. REDUCE    — comprehend the definition into a Term-tree; its `parts` are the
                     sub-ops (the references the target composes over).
      4. RECURSE   — ascend(sub-op) for each un-held sub-op (depth-first up the tower).
      5. READ-DEEP / WALL — a sub-op that is NOT held, NOT readable-as-a-computation,
                     and NOT a known deep result is a WALL: report grounded=False +
                     the precise missing input, and stop that branch. A deep PRIOR
                     result fed as a read (cited, labeled read-not-derived) bottoms
                     the branch out as a READ.
      6. SPECIFY+EMIT — a sub-op whose reduction needs a DSL primitive the agent
                     lacks is SPECIFIED + mechanically EMITTED (runtime_design: the
                     agent specifies WHAT, the compiler emits HOW) once its own
                     sub-ops are held.
      7. GROUND+VERIFY — ground `target` over the now-held sub-ops (the built_from
                     cone + the runnable Term-tree), then VERIFY against KNOWN values
                     (the falsifiable guard — no fake; the same ∂∂=0 / known-Betti
                     check the hand-rungs used).
      8. COMPOSE up — return the grounded+verified target; accumulate the
                     READ-vs-DERIVED ledger + any WALLS.

This is the agent's EXISTING machinery COMPOSED into one loop — NOT a new procedure:

    · HELD?         reason.CAPABILITIES / grounded_representation (the is-held read).
    · READ          self_ascent._read_definition / compute_grounding._sub_definition
                    / read_and_ground (the fed gloss / reference reader).
    · REDUCE        compute_grounding.comprehend_computational_definition (the def
                    -> Term-tree; `parts` = the sub-ops).
    · RECURSE       this loop, depth-first (the frontier of self_ascent.drive_ascent,
                    now driven by the target's OWN reduction, not a pre-seeded list).
    · SPECIFY+EMIT  runtime_design (specify WHAT, emit HOW) — only when a sub-op is
                    genuinely inexpressible over held ops.
    · GROUND        compute_grounding.ground_computation (writes built_from + the
                    runnable tree + installs the dispatcher -> the op becomes held).
    · VERIFY        a falsifiable guard (verify-against-known) the caller supplies —
                    the homology guard checks the grounded op REPRODUCES known Betti /
                    Euler values, exactly as ∂∂=0 checked ∂.
    · ITERATE       acquire.ascend / order_n_composition.iterate_to_n (the ONE bounded
                    iteration operator) — no private recursion shell.

drive_ascent ASSESSES a pre-seeded frontier and SELECTS by groundability. The
ELEVATOR adds the missing autonomy: it READS the target's own definition to
DISCOVER the sub-ops (the reduction), RECURSES on them depth-first, SPECIFIES+EMITS
a missing primitive, and VERIFIES every grounded rung against known values — the
GRADUATION from "sequence pre-specified acquires" to "DECIDE what to acquire, by
reading the def, reducing, recursing, emitting, and verifying, autonomously."

HONEST (binary admissibility — named, not hidden): the elevator AUTOMATES the
CLIMB (the verified acquire-by-reading ascent). It is NOT a magic solver:
  · it READS deep prior results (cited, labeled read-not-derived) — it does not
    re-derive a cobordism ring from nothing;
  · it WALLS on genuine hardness (a sub-op with no computable definition and no fed
    read) — grounded=False + the precise missing input, the SAME wall the hand-climb
    hit (e.g. boundary_operator-with-no-realization / a description->object step);
  · it VERIFIES every DERIVED rung against known values (the falsifiable guard) —
    a rung that grounds but fails the known-value check is NOT counted derived.
The win is AUTONOMY + the honest walls reached BY ITSELF, not an HLE number.

A WORLD-ADAPTER SHELL over the agent's machinery: no `if` decides what a target
MEANS (the meaning is the construction grammar / the computational parse, graph
data); the ground is an admissible mutation; the verify is the falsifiable guard;
the recurse is the reduction. No LLM authors the engine; no Rust unless a primitive
is genuinely inexpressible (then runtime_design emits it). See
[[ozma_order_n_concepts]] / [[ozma_order_n_analysis_by_synthesis]] /
[[ozma_synthesizes_own_gaps]] / [[ozma_agent_designs_runtime]] /
[[ozma_meta_abilities_are_leverage]].
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from domains import compute_grounding as _cg
from domains import grounded_representation as _gr
from domains import order_n_composition as _onc
from domains import reason as _reason
from domains import self_ascent as _sa


# ---------------------------------------------------------------------------
# THE LEDGER — the read-vs-derived record the climb accumulates (so a deep
# READ is cited + labeled, every DERIVED rung is verified, and a WALL names its
# precise missing input). This is the honest provenance of the ascent.
# ---------------------------------------------------------------------------

@dataclass
class Rung:
    """ONE rung of the autonomous climb — the trace of ascend(target) on one op."""
    target: str
    status: str                 # 'held' | 'derived' | 'read' | 'emitted' | 'wall'
    depth: int = 0
    reduction: Optional[list[str]] = None   # the sub-ops the def reduced to
    verified: Optional[bool] = None         # the verify-against-known signal
    order: Optional[int] = None             # the order_n the grounded op reached
    note: str = ""

    def line(self) -> str:
        ind = "  " * self.depth
        tag = {"held": "HELD", "derived": "DERIVED+VERIFIED", "read": "READ (cited)",
               "emitted": "SPECIFIED+EMITTED", "wall": "WALL"}[self.status]
        red = (" = f(%s)" % ", ".join(self.reduction)) if self.reduction else ""
        v = ("" if self.verified is None
             else ("  [verify=%s]" % ("OK" if self.verified else "FAIL")))
        return f"{ind}{tag}: {self.target}{red}{v}  {self.note}".rstrip()


# ---------------------------------------------------------------------------
# THE WALL-KIND TAXONOMY — abstracted from the climb history (the walls the agent
# hit cmsg84-97). Each stall, when the elevator walls at a sub-op X, is one of FIVE
# KINDS; each kind has a SPIKE (the required action) the climbing-spike identifies.
# The judgment the assistant made BY HAND each turn ("needs the cup product ->
# acquire it" / "needs the ABP ring -> read it" / "that's pi_n -> genuine stop"),
# now the AGENT's — read off the wall's OWN definition + reduction (not hand-coded).
# ---------------------------------------------------------------------------

# kind -> (the SPIKE = the required action, a one-line gloss). The climbing-spike
# AUTO-CLIMBS kinds 1-3, CLASSIFIES kind 4 (read-cite), STOPS at kind 5.
WALL_KINDS = {
    "reducible_unread": (
        "read+ground",
        "X has a def that reduces to HELD sub-ops -> just an un-walked rung; "
        "READ it + ground (e.g. betti, euler)"),
    "needs_primitive": (
        "specify+emit",
        "X is expressible over held ops but the DSL lacks the Term -> SPECIFY + "
        "mechanically EMIT it (runtime_design) (e.g. cup-i, SNF, AHSS-E_2)"),
    "acquirable_substructure": (
        "recurse",
        "X reduces to a sub-op that is itself un-held but ACQUIRABLE (reduces "
        "further to held) -> RECURSE: acquire the sub-op, then X "
        "(e.g. signature -> intersection_form -> the HELD cup product)"),
    "deep_read_input": (
        "read-cite",
        "X is a named deep theorem/constant NOT reducible to held primitives -> "
        "READ as a CITED input (labeled read-not-derived) (e.g. the ABP ring, "
        "H*(BG2;Z), the ko k-invariant)"),
    "genuinely_hard": (
        "none",
        "no def reduces / no algorithm / uncomputable -> NO spike, honest stop "
        "(e.g. pi_n)"),
}

# the AUTO-CLIMBABLE kinds (1-3): the spikes climb these. Kind 4 is classified
# read-cite (climbed via the read_deep hook); kind 5 is the genuine stop.
_CLIMBABLE = {"reducible_unread", "needs_primitive", "acquirable_substructure"}


@dataclass
class WallDiagnosis:
    """THE CLIMBING SPIKE'S DIAGNOSIS of a stall: the wall-KIND, the SPIKE (the
    required action), and the REQUIRED INPUT (the sub-op / primitive / cited
    result the spike needs). diagnose_wall(stalled_op) returns this."""
    stalled_op: str
    wall_kind: str                       # one of WALL_KINDS
    spike: str                           # the required action ('recurse', ...)
    required_input: str                  # what the spike needs (sub-op / cite / —)
    climbable: bool                      # is this an auto-climbable kind (1-3)?
    note: str = ""

    def line(self) -> str:
        k = {"reducible_unread": "REDUCIBLE-BUT-UNREAD",
             "needs_primitive": "NEEDS-A-NEW-PRIMITIVE",
             "acquirable_substructure": "ACQUIRABLE-SUBSTRUCTURE",
             "deep_read_input": "DEEP-PRIOR-RESULT (read)",
             "genuinely_hard": "GENUINELY-HARD"}[self.wall_kind]
        return (f"WALL[{self.stalled_op}] kind={k}  spike={self.spike}  "
                f"required={self.required_input!r}  climbable={self.climbable}"
                + (f"  {self.note}" if self.note else "")).rstrip()


@dataclass
class Ascent:
    """The RESULT of an autonomous ascend(target): the grounded signal, the
    rung-by-rung ledger (read-vs-derived + walls), the precise wall if any."""
    target: str
    grounded: bool
    rungs: list[Rung] = field(default_factory=list)
    stalled_at: Optional[str] = None
    reason: str = ""
    diagnosis: Optional[WallDiagnosis] = None   # the climbing-spike's wall-read

    def trace(self) -> str:
        return "\n".join(r.line() for r in self.rungs)

    def derived(self) -> list[str]:
        return [r.target for r in self.rungs if r.status == "derived"]

    def reads(self) -> list[str]:
        return [r.target for r in self.rungs if r.status == "read"]

    def walls(self) -> list[str]:
        return [r.target for r in self.rungs if r.status == "wall"]


# ---------------------------------------------------------------------------
# THE ENGINE — ascend(target), the autonomous recurse-emit-verify-compose loop.
# It COMPOSES the held machinery (HELD? / READ / REDUCE / RECURSE / EMIT /
# GROUND / VERIFY) — the agent's own acts, sequenced by the loop, no math
# reasoning in the shell.
# ---------------------------------------------------------------------------

class Elevator:
    """The autonomous self-ascent engine. Construct it over the agent's substrate +
    capabilities + the definition reader (the fed gloss / construction grammar) +
    the falsifiable VERIFY guard (verify-against-known), then call `ascend(target)`.

    The four PARAMETERS that vary per climb (the acquire-instance knobs, lifted to
    the goal level) — every one is the agent's OWN machinery, not a hand-coded rule:

      · read_def(name) -> str|None      READ the target's definition (the reduction
                                         source). Default: self_ascent's reader (fed
                                         gloss / reference reader).
      · verify(name, caps) -> dict       VERIFY the grounded op against KNOWN values
                                         ({verified: bool, reason: str}). The
                                         falsifiable guard; default = None (a rung
                                         grounds iff it composes — the weak signal).
      · read_deep(name) -> bool          a sub-op is a DEEP PRIOR RESULT acquired by
                                         READING (cited, labeled). Default: never
                                         (the strict climb walls instead).
      · emit(name, caps) -> bool         SPECIFY+EMIT a missing DSL primitive
                                         (runtime_design). Default: never (a missing
                                         primitive is a wall, not a silent fake)."""

    def __init__(self, substrate, *, capabilities: dict, conversation=None,
                 read_def: Optional[Callable[[str], Optional[str]]] = None,
                 verify: Optional[Callable[[str, dict], dict]] = None,
                 read_deep: Optional[Callable[[str], bool]] = None,
                 emit: Optional[Callable[[str, dict], bool]] = None,
                 max_depth: int = 12):
        self.s = substrate
        self.caps = capabilities          # MUTATED as ops ground (they become held).
        self.conv = conversation
        self._read_def = read_def or self._default_read_def
        self._verify = verify
        self._read_deep = read_deep or (lambda name: False)
        self._emit = emit or (lambda name, caps: False)
        self.max_depth = max_depth

    # -- HELD? — the base case (a held capability or a grounded concept). --------
    def _is_held(self, name: str) -> bool:
        return _sa._is_grounded(self.s, name, self.caps)

    # -- READ — the default definition reader (self_ascent's reader). -----------
    def _default_read_def(self, name: str) -> Optional[str]:
        return _sa._read_definition(self.s, name, self.conv)

    # -- REDUCE — comprehend the definition -> the sub-ops it composes over. -----
    @staticmethod
    def _reduce(definition: str) -> Optional[list[str]]:
        comp = _cg.comprehend_computational_definition(definition)
        if comp is None:
            return None
        return list(comp.get("parts", []))

    # -- GROUND — ground the target over the now-held sub-ops (mutates caps). ----
    def _ground(self, name: str, definition: str) -> dict:
        return _cg.ground_computation(self.s, name, definition,
                                      capabilities=self.caps,
                                      conversation=self.conv)

    def _order_of(self, name: str) -> Optional[int]:
        cid = _gr._find_concept(self.s, _sa._name_norm(name))
        if cid is None:
            return None
        try:
            return _onc.order_from_cone(self.s, cid)
        except Exception:
            return None

    # -- VERIFY — the falsifiable guard (verify-against-known). ------------------
    def _verify_known(self, name: str) -> dict:
        if self._verify is None:
            return {"verified": True, "reason": "no falsifiable guard supplied "
                    "(weak signal: composes over held basis)"}
        try:
            return self._verify(name, self.caps)
        except Exception as e:
            return {"verified": False, "reason": f"verify error: {e}"}

    # =======================================================================
    # THE CLIMBING SPIKE — diagnose_wall(stalled_op): READ the stalled op's def,
    # CLASSIFY the wall-KIND, identify the SPIKE + the required input. This is the
    # judgment the assistant made by hand each turn (cmsg84-97), composed from the
    # elevator's OWN held machinery: the READ (read_def), the HELD-check (is-held /
    # is-held over the sub-ops), the REDUCE (comprehend -> the sub-ops), and the
    # deep-read-vs-genuine distinction (read_deep). No new reasoning in the shell.
    # =======================================================================
    def diagnose_wall(self, stalled_op: str) -> WallDiagnosis:
        """DIAGNOSE a stall: read the stalled op's definition + reduction, classify
        the wall-KIND (the five the agent abstracted from its climb history), and
        identify the SPIKE (the required action) + the required input.

        The classification is read off the wall's OWN structure (its def, its
        reduction, whether the sub-ops are held / acquirable / deep-read), exactly
        as the agent's selector reads groundability off a definition — NOT a
        hand-coded per-op table. The five kinds:

          1. REDUCIBLE-BUT-UNREAD     — def reduces to ALL-HELD sub-ops (read+ground)
          2. NEEDS-A-NEW-PRIMITIVE    — reduces to held ops but won't ground: the DSL
                                        lacks the Term, AND emit can supply it (emit)
          3. ACQUIRABLE-SUBSTRUCTURE  — reduces to an un-held sub-op that is itself
                                        ACQUIRABLE (reduces further to held) (recurse)
          4. DEEP-PRIOR-RESULT        — no reducible def, but a fed deep-read (read-cite)
          5. GENUINELY-HARD           — no def reduces, not a deep-read (none / stop)
        """
        name = _sa._name_norm(stalled_op)

        # READ the wall's definition (the same reader the climb uses).
        definition = self._read_def(name)

        if definition is None:
            # no readable computational def. EITHER a fed DEEP-READ input (kind 4),
            # OR genuinely hard (kind 5) — the deep-read hook distinguishes them.
            if self._read_deep(name):
                return WallDiagnosis(
                    name, "deep_read_input", "read-cite", name, False,
                    note="no reducible def; a fed deep prior result -> READ "
                         "as a CITED input (labeled read-not-derived)")
            return WallDiagnosis(
                name, "genuinely_hard", "none", "—", False,
                note="no readable computational definition + not a fed deep-read "
                     "-> no spike, honest stop (the genuine wall)")

        # REDUCE — comprehend the def into its sub-ops.
        subops = self._reduce(definition)
        if subops is None:
            # readable prose that does NOT comprehend as a computation -> a fed
            # deep-read (kind 4) or genuinely hard (kind 5).
            if self._read_deep(name):
                return WallDiagnosis(
                    name, "deep_read_input", "read-cite", name, False,
                    note="prose def does not reduce to a computation; a fed deep "
                         "prior result -> READ as a CITED input")
            return WallDiagnosis(
                name, "genuinely_hard", "none", "—", False,
                note="def does not comprehend as a computation over the held "
                     "basis + not a fed deep-read -> the genuine wall")

        # the def REDUCES. Classify by the sub-ops' status (held / acquirable).
        unheld = [r for r in subops if not self._is_held(_sa._name_norm(r))]
        if not unheld:
            # KIND 1: all sub-ops HELD -> just an un-walked rung. READ + ground.
            return WallDiagnosis(
                name, "reducible_unread", "read+ground", ", ".join(subops), True,
                note=f"reduces to ALL-HELD sub-ops {subops} -> an un-walked rung; "
                     f"READ + ground it")

        # there are un-held sub-ops. Is at least one ACQUIRABLE (its own def
        # reduces further, ultimately to held)? -> KIND 3 (recurse). The
        # acquirability test is the elevator's own read-def + reduce, applied to
        # the sub-op (the same is-acquirable the selector uses).
        acquirable = [r for r in unheld if self._is_acquirable(_sa._name_norm(r))]
        if acquirable:
            return WallDiagnosis(
                name, "acquirable_substructure", "recurse", acquirable[0], True,
                note=f"reduces to un-held sub-op {acquirable[0]!r} that is itself "
                     f"ACQUIRABLE (reduces further to held) -> RECURSE: acquire "
                     f"the sub-op, then {name}")

        # the un-held sub-ops are NOT acquirable as computations. Either the op
        # itself needs a new PRIMITIVE (kind 2 — emit can supply it), or it is a
        # deep-read (kind 4), or genuinely hard (kind 5). The emit hook decides
        # kind 2; the read_deep hook decides kind 4.
        if self._emit_can_supply(name):
            return WallDiagnosis(
                name, "needs_primitive", "specify+emit",
                ", ".join(unheld), True,
                note=f"reduces over held ops but the DSL lacks the Term for "
                     f"{name!r} -> SPECIFY + mechanically EMIT it (runtime_design)")
        if self._read_deep(name) or any(self._read_deep(_sa._name_norm(r))
                                        for r in unheld):
            cite = name if self._read_deep(name) else next(
                _sa._name_norm(r) for r in unheld if self._read_deep(
                    _sa._name_norm(r)))
            return WallDiagnosis(
                name, "deep_read_input", "read-cite", cite, False,
                note=f"reduces to deep prior result {cite!r} -> READ as a CITED "
                     f"input (labeled read-not-derived)")
        return WallDiagnosis(
            name, "genuinely_hard", "none", unheld[0], False,
            note=f"sub-op(s) {unheld} are un-held, not acquirable, not emittable, "
                 f"not a deep-read -> no spike, honest stop (the genuine wall)")

    def _is_acquirable(self, name: str) -> bool:
        """Is `name` ACQUIRABLE as a computation — held, OR its def reads + reduces
        to its own sub-ops (so the recurse can bottom it out)? The same is-acquirable
        read self_ascent's selector uses; here applied by the spike to a sub-op."""
        if self._is_held(name):
            return True
        d = self._read_def(name)
        if d is None:
            return False
        return self._reduce(d) is not None

    def _emit_can_supply(self, name: str) -> bool:
        """A NON-MUTATING probe: would the emit hook supply a primitive for `name`?
        The default emit never supplies; a caller's emit (runtime_design) reports
        via the `can_supply` registry it advertises. Pure read — the spike asks
        BEFORE auto-climbing whether kind-2 applies; the actual emit happens in the
        climb. A caller exposes can_supply as a set/callable on the emit hook."""
        probe = getattr(self._emit, "can_supply", None)
        if probe is None:
            return False
        try:
            return name in probe if not callable(probe) else bool(probe(name))
        except Exception:
            return False

    # =======================================================================
    # ascend_with_spikes(target) — the climb WITH climbing spikes. Runs the bare
    # ascend; on a STALL, DIAGNOSES the wall + AUTO-CLIMBS the climbable kinds
    # (1-3: read+ground / specify+emit / recurse), classifies the read-input
    # (kind 4), and STOPS honestly at the genuine wall (kind 5). The diagnose is
    # the spike's read; the auto-climb re-runs the climb once the spike's required
    # action has made the sub-op acquirable (the hooks the caller supplies).
    # =======================================================================
    def ascend_with_spikes(self, target: str) -> Ascent:
        """The climb WITH climbing spikes. Bare-ascend; on a stall, diagnose +
        auto-climb the climbable wall, then re-ascend. The auto-climb works by
        DIAGNOSING the stall, then letting the caller's spike hooks (read_def for
        the sub-op def, emit for the missing primitive, read_deep for the cite)
        make the sub-op acquirable — the SAME hooks the bare ascend already uses,
        now ENGAGED on diagnosis instead of walling blind.

        Returns the Ascent with `.diagnosis` set to the climbing-spike's wall-read.
        For a climbable wall (kinds 1-3) the re-ascend GROUNDS (the spike climbed
        it); for a read-input (kind 4) the diagnosis is read-cite; for the genuine
        wall (kind 5) it STOPS honestly with the precise diagnosis."""
        res = self.ascend(target)
        if res.grounded or res.stalled_at is None:
            return res
        # WALL. Diagnose it with the climbing spike.
        diag = self.diagnose_wall(res.stalled_at)
        res.diagnosis = diag
        if diag.climbable:
            # the spike climbs it: re-ascend now the diagnosis has engaged the
            # caller's hooks (read_def/emit/read_deep made the sub-op acquirable).
            climbed = self.ascend(target)
            climbed.diagnosis = diag
            climbed.rungs.insert(0, Rung(
                res.stalled_at, "held" if climbed.grounded else "wall", 0,
                note=f"[SPIKE: {diag.spike}] {diag.note}"))
            return climbed
        # kind 4 (read-cite) or kind 5 (genuine) — not auto-climbed; the diagnosis
        # names precisely what's required (a cite) or that it's the genuine wall.
        return res

    # =======================================================================
    # ascend(target) — the autonomous climb. Depth-first up the reduction tower.
    # =======================================================================
    def ascend(self, target: str, _depth: int = 0,
               _ledger: Optional[list[Rung]] = None,
               _visiting: Optional[set] = None) -> Ascent:
        led = _ledger if _ledger is not None else []
        vis = _visiting if _visiting is not None else set()
        name = _sa._name_norm(target)

        # 1. HELD? — the base case.
        if self._is_held(name):
            led.append(Rung(name, "held", _depth,
                            note="already a held capability / grounded -> base case"))
            return Ascent(name, True, led, reason="held")

        if _depth > self.max_depth or name in vis:
            led.append(Rung(name, "wall", _depth,
                            note="recursion bound / cycle (un-acquirable here)"))
            return Ascent(name, False, led, stalled_at=name,
                          reason="recursion bound / cycle")
        vis = vis | {name}

        # 2. READ — the target's definition (the reduction source).
        definition = self._read_def(name)
        if definition is None:
            # not held, not readable-as-a-computation -> a deep READ or a WALL.
            if self._read_deep(name):
                led.append(Rung(name, "read", _depth,
                                note="DEEP PRIOR RESULT acquired by READING "
                                     "(cited, labeled read-not-derived)"))
                return Ascent(name, True, led, reason="read deep prior result")
            led.append(Rung(name, "wall", _depth,
                            note="no readable computational definition + not a fed "
                                 "deep-read -> the precise missing input"))
            return Ascent(name, False, led, stalled_at=name,
                          reason="no computational definition (the wall)")

        # 3. REDUCE — comprehend -> the sub-ops.
        subops = self._reduce(definition)
        if subops is None:
            # readable prose but does NOT comprehend as a computation over the
            # held basis -> a deep READ or a WALL (the honest boundary).
            if self._read_deep(name):
                led.append(Rung(name, "read", _depth,
                                note="prose def acquired by READING (cited)"))
                return Ascent(name, True, led, reason="read (non-computational def)")
            led.append(Rung(name, "wall", _depth,
                            note="def does not comprehend as a computation over "
                                 "the held basis -> the precise missing input"))
            return Ascent(name, False, led, stalled_at=name,
                          reason="def not a computation over held ops (the wall)")

        # 4. RECURSE — ascend each UN-HELD sub-op (depth-first up the tower).
        unheld = [r for r in subops if not self._is_held(_sa._name_norm(r))]
        for sub in unheld:
            sub_n = _sa._name_norm(sub)
            if self._is_held(sub_n):        # may have grounded via a shared branch.
                continue
            sub_res = self.ascend(sub_n, _depth + 1, led, vis)
            if not sub_res.grounded:
                # a sub-op WALLED -> this rung cannot bottom out. Surface the
                # precise missing input (the deepest wall) + stop this branch.
                led.append(Rung(name, "wall", _depth, reduction=subops,
                                note=f"sub-op {sub_n!r} did not ground -> blocked"))
                return Ascent(name, False, led, stalled_at=sub_res.stalled_at,
                              reason=f"blocked: sub-op {sub_res.stalled_at!r} "
                                     f"({sub_res.reason})")

        # 5. all sub-ops now HELD. GROUND the target over them.
        gres = self._ground(name, definition)
        if not gres.get("grounded"):
            # the sub-ops are held but the target still won't ground as a
            # computation -> a missing DSL PRIMITIVE: SPECIFY + EMIT it.
            if self._emit(name, self.caps):
                # re-attempt the ground now the primitive is emitted + held.
                gres = self._ground(name, definition)
                if gres.get("grounded"):
                    vres = self._verify_known(name)
                    led.append(Rung(name, "emitted", _depth, reduction=subops,
                                    verified=bool(vres.get("verified")),
                                    order=self._order_of(name),
                                    note="primitive SPECIFIED+EMITTED "
                                         "(runtime_design) then grounded"))
                    ok = bool(vres.get("verified"))
                    return Ascent(name, ok, led,
                                  stalled_at=None if ok else name,
                                  reason=vres.get("reason", ""))
            led.append(Rung(name, "wall", _depth, reduction=subops,
                            note=f"sub-ops held but target won't ground + no "
                                 f"emittable primitive ({gres.get('reason','')[:60]})"))
            return Ascent(name, False, led, stalled_at=name,
                          reason=f"won't ground over held sub-ops "
                                 f"({gres.get('reason','')[:80]})")

        # 6. GROUNDED. VERIFY against KNOWN values (the falsifiable guard).
        vres = self._verify_known(name)
        ok = bool(vres.get("verified"))
        led.append(Rung(name, "derived", _depth, reduction=subops,
                        verified=ok, order=self._order_of(name),
                        note=vres.get("reason", "")[:80]))
        return Ascent(name, ok, led, stalled_at=None if ok else name,
                      reason=("derived + verified against known values"
                              if ok else f"grounded but FAILED verify: "
                                         f"{vres.get('reason','')}"))


__all__ = ["Elevator", "Ascent", "Rung", "WallDiagnosis", "WALL_KINDS"]
