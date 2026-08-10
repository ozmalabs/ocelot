"""question_driver — THE DRIVER REFLEX: the self-running loop that takes a RAW
question off the bank, COMPREHENDS it into a target, RIDES the elevator on it, and
EMITS a verified + honestly-labeled answer-or-wall + the read-vs-derived LEDGER +
the native-collapse CONFIDENCE — with NO per-question hand-shell and NO assistant
in the loop.

GRAPH-NATIVE FORM (this migration). `drive(pack)` is now a THIN WORLD ADAPTER:

    drive(pack)
      1. STIMULUS  — mint a Question node (unchanged: the raw text enters the graph).
      2. COMPREHEND — comprehend_question.comprehend(text) -> the TargetSpec (the
                     boundary faculty, unchanged) -> INGEST it as a graph-resident
                     Goal tree (`_ingest_target`): kind/raw/op/params/concept/
                     meta_target/meta_arg/gap_depth attrs, recursing into
                     compound/compare subgoals and a contrast leaf's own two
                     know-children. Ungrounded: run the ASK loop (the one true
                     I/O boundary, kept), then parse_with_gaps + ingest the gap
                     frame as GapSpec children of a "gap"-kind root Goal.
      3. PUMP      — a bounded tick loop (`_pump`): each iteration fires the
                     `question_pursue` reflex (seeds/question_driving.json) —
                     which advances ONE dispatched Goal via its bound Resolver's
                     module-level callable (`substrate/world_adapter.py`'s
                     `_question_pursue_advance`, wired through
                     `wire_question_faculty`) — then runs the seeded rules
                     (`qd_bind_resolver`/`qd_decompose`.../`qd_gap_guard`/
                     `qd_contrast_compare`) to fixpoint. Repeats until the root
                     Goal resolves or walls.
      4. EMIT      — `_fill_emission_from_goal` MECHANICALLY reads the resolved
                     Goal tree back into the SAME `Emission` shape this module
                     always returned (answer/verified/confidence/wall_kind/
                     know_answer/meta_answer/subgoals/note) — a pure graph read,
                     no reasoning.

The kind-DISPATCH (which faculty resolves a goal) is a JOIN in the graph
(`qd_bind_resolver`: `Agent -has_goal-> Goal` / `Agent -has_resolver-> Resolver`
sharing the kind), not a Python if/elif; the recursion depth for gap-grounding is
DATA on the Goal node (`gap_depth`), not Python state (`self._gap_depth` is gone).
The five RESOLVER CALLABLES (`elevator_compute`/`know_ground`/`reflect_resolver`/
`contrast_resolver`/`gap_parse`) are MODULE-LEVEL functions below: each is a thin
boundary invocation of the existing faculty (the elevator ride / wiki_local lookup
/ reflective_faculty.reflect / construction_grammar's gap composer) plus a
MECHANICAL write-back of that faculty's own result onto the Goal node's attrs —
including honest walls (e.g. an ungrounded ascent -> status "walled" + wall_kind,
the faculty's own verdict written down, not a new Python decision).

`_ask_until_grounded` remains the ASK-ACTION's boundary executor (it talks to an
external parent — genuine I/O); its lexicon now lives as graph `LexEntry` nodes
for whatever it incorporates, per the design.

THE SUPPLY LINE (#3, the named residual — NOT closed here). The driver RIDES + reaches
the deep-read walls + uses the FED supply: per question the host stages the reduction
GLOSSES (the elevator READS them), the DEEP-READS (the cited prior results the spike
classifies read-not-derived), and the KNOWN VALUES (the falsifiable verify ground
truth). The deep-read RETRIEVAL (autonomously fetching + citing ABP / ko / Najman) and
the ground-truth SOURCING (the known values) remain FED — that is plumbing-gap #3, the
supply line, the named next plumb. The driver closes #1 (comprehend) + #2 (the self-
running loop, now graph-resident); it does NOT close #3.

A QUESTION PACK is the unit the host stages: the raw text (off the bank) + the fed
supply (#3). The driver runs on ANY pack with NO per-question shell — the ONE loop, on
any question. A pack whose question the comprehension can parse + whose target the
elevator can ride is driven end-to-end; a novel question SHAPE is the comprehension
frontier; a deep target with no fed supply walls honestly (the supply line).
"""
from __future__ import annotations

import os
import sys
import types
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
_DSLPY = os.path.join(ROOT, "runners", "dsl", "python")
if _DSLPY not in sys.path:
    sys.path.insert(0, _DSLPY)

from substrate_rs import _native                          # noqa: E402
from substrate.world_adapter import WorldAdapter           # noqa: E402
from domains.reflective_faculty import _agent_root_node, _ensure_seed_chain  # noqa: E402
from domains import comprehend_question as _cq            # noqa: E402
from domains import construction_grammar as _cg           # noqa: E402
from domains import grounded_representation as _gr        # noqa: E402
from domains import reason as _reason                     # noqa: E402
from domains import elevator as _elev                     # noqa: E402
from domains import verify_collapse as _vc                # noqa: E402
from domains import read_and_ground as _rag                # noqa: E402
from domains import self_ascent as _sa                     # noqa: E402


# ---------------------------------------------------------------------------
# THE QUESTION PACK — the unit the host stages: the raw question text (off the
# bank) + the FED SUPPLY (#3, the supply line that remains fed). The driver runs
# on ANY pack with NO per-question shell.
# ---------------------------------------------------------------------------

@dataclass
class QuestionPack:
    """A question + its fed supply (#3). `text` is the RAW question (off the bank);
    everything else is the staged supply line the driver RIDES on but does NOT
    autonomously retrieve (the named residual). All supply is OPTIONAL — a pack with
    no supply rides the bare elevator (and walls where it lacks a definition)."""
    text: str
    question_id: Optional[str] = None
    # the reduction GLOSSES the elevator READS (name -> definition) — the supply line.
    feed: dict[str, str] = field(default_factory=dict)
    # the DEEP-READS (sub-op names acquired by READING, cited, labeled) — supply line.
    deep_reads: set = field(default_factory=set)
    # the per-target VERIFY hook (name, caps) -> the native-collapse verdict; the
    # KNOWN VALUES it checks are the fed ground truth — supply line. None = weak verify.
    verify: Optional[Callable[[str, dict], dict]] = None
    # the ASSEMBLE binding: the params (read by the comprehension / supplied by a deep
    # read) the held op is CALLED with to produce the answer value (e.g. the maximal
    # torsion pair (3,6) the read supplied). The driver solves the grounded op with it.
    answer_call: Optional[Callable[[str, dict, dict], Any]] = None
    # the REFLECT hook (a SELF/META question only): a world-adapter callable
    # ``(meta_target, meta_arg, substrate) -> dict`` that runs the agent's HELD
    # REFLECTIVE faculty (epistemic_access / order_n_postulates / diagnose_wall) over
    # a substrate carrying the held machinery, and returns its structured self-answer.
    # The driver ROUTES to it for a meta question (the same way it rides the elevator
    # for a world question); it does NOT itself author any reflective reasoning. The
    # meta-faculty sequencer is domains/reflective_faculty.py (the held machinery).
    reflect: Optional[Callable[[str, Optional[str], Any], dict]] = None
    # the ASK ACTION's PARENT hook (the strict-pants experiment + general): a
    # world-adapter callable ``(question: str, meta: dict) -> Optional[dict]`` that
    # POSES the agent's formulated question to an external answerer (here the strict
    # parent) and returns ITS one-step answer, or None if the answerer is mute /
    # cannot one-step. The AGENT formulates the question (comprehend_question.
    # formulate_ask); ASK only POSES it through this hook and INCORPORATES the
    # one-step answer to advance the goal. None = ASK is not available as an action
    # for this pack (the pursuit walls honestly, as before).
    ask: Optional[Callable[[str, dict], Optional[dict]]] = None
    # the construction prose (when the question's OBJECT is given by a construction):
    # the source the agent's gluing reader reads + names its unparsed constructions
    # from. drive sets it to the raw question text by default; the formulate_ask
    # faculty reads it to name the construction-operator gap. NOT the answer.
    prose: Optional[str] = None
    # the INCORPORATE hook for the ASK action: a world-adapter callable
    # ``(one_step: dict, meta: dict, caps: dict) -> Optional[dict]`` that takes the
    # parent's ONE-STEP answer + advances the goal by it — installs the named lexicon
    # entry / construction word / sub-op fact into the agent's held data, returning a
    # structured 'advance' (what the goal can now do). The strict harness supplies a
    # MECHANICAL incorporate (no reasoning) that wires the one fact the parent named.
    incorporate: Optional[Callable[[dict, dict, dict], Optional[dict]]] = None


# ---------------------------------------------------------------------------
# THE EMISSION — the answer (or honest wall) + the read-vs-derived LEDGER + the
# collapse CONFIDENCE. This is the read-vs-derived provenance of the self-run.
# ---------------------------------------------------------------------------

@dataclass
class Emission:
    question_id: Optional[str]
    raw: str
    target: Optional[_cq.TargetSpec]            # the comprehended target (#1)
    ascent: Optional[_elev.Ascent]              # the elevator's ride (#2)
    answer: Any = None                          # the emitted answer value (or None)
    is_wall: bool = False                       # an honest wall instead of an answer?
    confidence: Optional[float] = None          # the native-collapse confidence
    verified: Optional[bool] = None             # the falsifiable verify verdict
    wall_kind: Optional[str] = None             # the climbing-spike's wall-kind
    missing: Optional[str] = None               # the precise missing input (a wall)
    # META emission (a SELF/META question routed to a reflective faculty): the
    # faculty's structured self-answer (the retrieval design / the frontier / the
    # needed-input diagnosis). `kind` mirrors the target kind for the report.
    kind: str = "world"
    meta_answer: Optional[dict] = None
    # KNOW emission (a KNOW goal grounded via the reference wall): the agent's SHORT
    # grounded answer (the comprehended genus/concept) + the grounding provenance
    # (which article was present in wiki_local). NOT a verbatim Wikipedia excerpt.
    know_answer: Optional[dict] = None
    # COMPOUND emission (a COMPOUND goal decomposed into subgoals): the child
    # Emissions, one per subgoal, each resolved by ITS leaf faculty. The goal/
    # subgoal TREE is this list of child emissions (+ the has_subgoal graph edges).
    subgoals: list["Emission"] = field(default_factory=list)
    # THE ASK-TRANSCRIPT — one entry per fired ASK action: the agent's posed question
    # (from its faculty), the parent's one-step answer, and how the goal advanced.
    # Empty when ASK never fired (the goal advanced without asking, or ASK was not an
    # available action). The count len(asks) is the number of asks the goal needed.
    asks: list[dict] = field(default_factory=list)
    gap_frame: Optional[dict] = None            # a walled SHAPE parsed into typed gaps (parts of speech)
    note: str = ""

    def report(self, _indent: int = 0) -> str:
        pad = "  " * _indent
        lines = [f"{pad}RAW: {self.raw[:72]!r}"]
        if self.target is None or not self.target.grounded:
            lines.append(f"{pad}  COMPREHENSION FRONTIER: "
                         + (self.target.reason if self.target else "no target"))
            return "\n".join(lines)
        if self.target.kind in ("compound", "compare"):
            n = len(self.subgoals)
            gw = ("comparison (ACQUIRED construction)"
                  if self.target.kind == "compare" else "compound")
            lines.append(f"{pad}  COMPREHEND -> SEED GOAL = {gw} "
                         f"({n} subgoals) -> DECOMPOSE (the goal tree)")
            for i, sub in enumerate(self.subgoals):
                fac = {"world": "elevator", "know": "wiki_local",
                       "meta": "reflective", "compound": "decompose",
                       "compare": "decompose",
                       "contrast": "contrast-over-grounded"}.get(
                           sub.kind, sub.kind)
                tag = "WALL" if sub.is_wall else "RESOLVED"
                lines.append(f"{pad}  +- SUBGOAL[{i}] kind={sub.kind} "
                             f"-> faculty={fac}  [{tag}]")
                lines.append(sub.report(_indent + 2))
            lines.append(f"{pad}  COMPOSE -> {self.note}")
            return "\n".join(lines)
        if self.target.kind == "contrast":
            ka = self.know_answer or {}
            lines.append(f"{pad}  CONTRAST -> over the two grounded genera")
            if self.is_wall:
                lines.append(f"{pad}  -> WALL: {self.note}")
            else:
                lines.append(f"{pad}  -> {ka.get('answer')}")
            return "\n".join(lines)
        if self.target.kind == "meta":
            lines.append(f"{pad}  COMPREHEND -> [META] meta_target="
                         f"{self.target.meta_target} -> faculty={self.target.faculty}"
                         + (f" arg={self.target.meta_arg!r}"
                            if self.target.meta_arg else ""))
            ma = self.meta_answer or {}
            lines.append(f"{pad}  ROUTE -> the reflective faculty "
                         f"({self.target.faculty})")
            for k, v in ma.items():
                lines.append(f"{pad}    {k}: {v}")
            if self.note:
                lines.append(f"{pad}  " + self.note)
            return "\n".join(lines)
        if self.target.kind == "know":
            ka = self.know_answer or {}
            lines.append(f"{pad}  COMPREHEND -> SEED GOAL = "
                         f"know({self.target.know_concept!r})")
            lines.append(f"{pad}  PURSUE -> not-held -> REFERENCE WALL -> retrieval "
                         f"looks up wiki_local")
            if self.is_wall:
                lines.append(f"{pad}  -> HONEST WALL: {self.note}")
            else:
                lines.append(f"{pad}  -> wiki_local article: {ka.get('article')!r} "
                             f"(present={ka.get('present')})")
                lines.append(f"{pad}  GROUND -> the agent's SHORT answer: "
                             f"{ka.get('answer')}")
                if ka.get("grounded") is not None:
                    lines.append(f"{pad}     (grounded-to-primitive="
                                 f"{ka.get('grounded')}, comprehension-depth limit "
                                 f"noted honestly)")
            if self.note and not self.is_wall:
                lines.append(f"{pad}  " + self.note)
            return "\n".join(lines)
        lines.append(f"{pad}  COMPREHEND -> [WORLD] target = {self.target.op}"
                     f"({self.target.params})")
        if self.is_wall:
            lines.append(f"{pad}  RIDE -> HONEST WALL: missing={self.missing!r} "
                         f"kind={self.wall_kind}")
        else:
            lines.append(f"{pad}  RIDE -> ANSWER = {self.answer}  "
                         f"(verified={self.verified}, confidence={self.confidence})")
        if self.ascent is not None:
            lines.append(f"{pad}  LEDGER (the read-vs-derived ascent):")
            lines.append(f"{pad}    derived=%s  reads=%s  walls=%s"
                         % (self.ascent.derived(), self.ascent.reads(),
                            self.ascent.walls()))
        if self.note:
            lines.append(f"{pad}  " + self.note)
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# THE RESOLVER CALLABLES — module-level functions (not methods, not classes).
# Each is a thin boundary invocation of an existing faculty + a MECHANICAL
# write-back of that faculty's own result onto the Goal node's attrs. Bound
# into `adapter._master["goal_resolvers"]` by name (via `wire_question_faculty`)
# and invoked by `substrate/world_adapter.py`'s `_question_pursue_advance` — the
# executor only LOOKS UP which resolver is bound (a Rule JOIN, `qd_bind_
# resolver`), it never decides. A resolver reads whatever kind-specific fields
# `_ingest_target` wrote (op/params, concept, meta_target/meta_arg); when those
# are absent (a Goal materialized by a seeded rule that only copies kind/raw —
# not applicable to any of THESE five today, since every Goal this driver mints
# carries its own full attrs, but kept as an honest fallback) it re-comprehends
# the Goal's own `raw` text — the SAME boundary faculty `drive()` itself uses.
# ---------------------------------------------------------------------------

def _pack_caps(adapter) -> dict:
    return adapter._master.get("pack_caps") or {}


def elevator_compute(adapter, goal_node) -> None:
    """WORLD goal resolver: ride the elevator (unchanged `_elev.Elevator.
    ascend_with_spikes`) over the pack's fed supply, then CALL the grounded op
    with the comprehended params (`pack.answer_call`) and VERIFY (`pack.verify`)
    — exactly the pre-migration `_pursue`'s compute branch, just writing its
    result onto the Goal node instead of an Emission."""
    at = adapter.s.node(goal_node)["attrs"]
    op = at.get("op")
    params = at.get("params")
    if op is None:
        spec = _cq.comprehend(at.get("raw") or "", substrate=adapter.s)
        op = spec.op
        params = dict(spec.params or {})
    params = dict(params or {})
    if not op:
        adapter.s.set_attr(goal_node, "status", "walled")
        adapter.s.set_attr(goal_node, "note",
                           "no world op comprehended for this goal (honest wall)")
        return
    caps = dict(_reason.CAPABILITIES)
    pc = _pack_caps(adapter)
    conv = type("Conv", (), {"_definition_feed": dict(pc.get("feed") or {})})()
    deep = set(pc.get("deep_reads") or set())
    elevator = _elev.Elevator(
        adapter.s, capabilities=caps, conversation=conv,
        verify=pc.get("verify"),
        read_deep=(lambda name, _d=deep: name in _d))
    ascent = elevator.ascend_with_spikes(op)
    if not ascent.grounded:
        adapter.s.set_attr(goal_node, "missing", ascent.stalled_at)
        adapter.s.set_attr(goal_node, "note", ascent.reason or "")
        if ascent.diagnosis is not None:
            adapter.s.set_attr(goal_node, "wall_kind", ascent.diagnosis.wall_kind)
        adapter.s.set_attr(goal_node, "status", "walled")
        return
    answer, note = None, ""
    answer_call = pc.get("answer_call")
    if answer_call is not None:
        try:
            answer = answer_call(op, dict(params), caps)
        except Exception as e:                                # noqa: BLE001
            note = f"answer_call error: {e}"
    verified, confidence = None, None
    verify_fn = pc.get("verify")
    if verify_fn is not None:
        try:
            v = verify_fn(op, caps)
            verified = bool(v.get("verified"))
            confidence = v.get("confidence")
        except Exception as e:                                # noqa: BLE001
            note = (note + f" | verify error: {e}").strip(" |")
    adapter.s.set_attr(goal_node, "answer", answer)
    adapter.s.set_attr(goal_node, "verified", verified)
    adapter.s.set_attr(goal_node, "confidence", confidence)
    adapter.s.set_attr(goal_node, "note", note)
    adapter.s.set_attr(goal_node, "status", "resolved")


def know_ground(adapter, goal_node) -> None:
    """KNOW goal resolver — the pre-migration `_pursue_know`, unchanged in
    substance: is-held check (`self_ascent._is_grounded`) -> the climbing
    spike's REFERENCE wall (`elevator.diagnose_wall`) -> the retrieval
    (`read_and_ground.read_and_ground`, wiki_local first) -> the SHORT grounded
    answer. Writes `know_answer` (the rich dict) + a top-level `genus` attr
    (so the seeded `qd_contrast_compare` rule's `Attr(child,"genus")` read
    works) + status resolved/walled."""
    at = adapter.s.node(goal_node)["attrs"]
    concept = at.get("concept")
    if concept is None:
        spec = _cq.comprehend(at.get("raw") or "", substrate=adapter.s)
        concept = spec.know_concept or at.get("raw")
    display_concept = concept
    concept = _sa._name_norm(concept or "")
    caps = dict(_reason.CAPABILITIES)
    conv = type("Conv", (), {"_definition_feed": {}})()

    if _sa._is_grounded(adapter.s, concept, caps):
        adapter.s.set_attr(goal_node, "know_answer", {
            "answer": f"{display_concept} is already held (grounded) — no reference needed",
            "present": True, "article": None, "grounded": True})
        adapter.s.set_attr(goal_node, "note", "the KNOW goal was already held (base case)")
        adapter.s.set_attr(goal_node, "status", "resolved")
        return

    ev = _elev.Elevator(adapter.s, capabilities=caps, conversation=conv,
                        read_deep=lambda _n: True)
    diag = ev.diagnose_wall(concept)
    adapter.s.set_attr(goal_node, "wall_kind", diag.wall_kind)

    res = _rag.read_and_ground(adapter.s, concept, conv)
    st = res.get("structure") or {}
    genus = st.get("genus")
    prov = st.get("provenance") or {}
    article = prov.get("where")
    present = article is not None

    if not present and genus is None:
        adapter.s.set_attr(goal_node, "note",
                           f"REFERENCE WALL: wiki_local holds no article for "
                           f"{display_concept!r} (the reference store did not "
                           f"cover the KNOW goal) — honest wall, nothing fabricated")
        adapter.s.set_attr(goal_node, "know_answer",
                           {"answer": None, "present": False, "article": None, "grounded": False})
        adapter.s.set_attr(goal_node, "status", "walled")
        return

    short = (f"{display_concept} is a {genus.replace('_', ' ')}"
             if genus else f"{display_concept} (grounded, genus not comprehended)")
    know_answer = {
        "answer": short, "concept": display_concept, "genus": genus,
        "article": article, "present": present, "grounded": bool(res.get("grounded")),
        "source": prov.get("source"), "snapshot": prov.get("when"),
    }
    adapter.s.set_attr(goal_node, "know_answer", know_answer)
    adapter.s.set_attr(goal_node, "genus", genus)
    if not res.get("grounded"):
        adapter.s.set_attr(goal_node, "note",
                           "the genus is comprehended + grounded one hop from "
                           "wiki_local; the cone does not yet reach a seeded "
                           "primitive (the honest comprehension-depth limit)")
    adapter.s.set_attr(goal_node, "status", "resolved")


def reflect_resolver(adapter, goal_node) -> None:
    """META goal resolver: route to the pack's REFLECT hook (domains/
    reflective_faculty.py's `reflect`, the held machinery sequencer), exactly
    the pre-migration `_pursue`'s meta branch. Writes `meta_answer` + status."""
    at = adapter.s.node(goal_node)["attrs"]
    reflect_fn = _pack_caps(adapter).get("reflect")
    if reflect_fn is None:
        adapter.s.set_attr(goal_node, "status", "walled")
        adapter.s.set_attr(goal_node, "note",
                           "a SELF/META goal, but no reflective faculty wired "
                           "(pack.reflect is None) — the goal exists, the "
                           "faculty hook is unsupplied")
        return
    try:
        result = reflect_fn(at.get("meta_target"), at.get("meta_arg"), adapter.s)
        adapter.s.set_attr(goal_node, "meta_answer", result)
        adapter.s.set_attr(goal_node, "status", "resolved")
    except Exception as e:                                    # noqa: BLE001
        adapter.s.set_attr(goal_node, "status", "walled")
        adapter.s.set_attr(goal_node, "note", f"reflective faculty error: {e}")


def contrast_resolver(adapter, goal_node) -> None:
    """CONTRAST leaf resolver — a deliberate NO-OP boundary invocation. The
    comparison itself (reading the contrast Goal's two know-children's genus,
    deciding same/different, resolving status) is the seeded `qd_contrast_
    compare` RULE (seeds/question_driving.json) — pure graph data, no Python
    decision. This callable exists only so a dispatched contrast Goal doesn't
    sit un-acknowledged; the rich `know_answer` sentence (genus text + concept
    names) is filled in at the MECHANICAL Emission read-off (`_fill_emission_
    from_goal`), from the SAME already-resolved children the rule read."""
    return


def gap_parse(adapter, goal_node) -> None:
    """GAP-PATH resolver: once every typed GapSpec (`qd_gap_guard`'s "What is
    X?" KNOW children, seeds/question_driving.json) has materialized AND every
    resulting KNOW subgoal has resolved/walled, COMPOSE the focus over the
    typed-gap frame (`construction_grammar.compose_relation/render_relation`)
    and RESOLVE it from held knowledge (`resolve_focus`) — exactly the
    pre-migration `drive()`'s gap-path tail, moved here. Returns (a wait, not a
    decision) while the GapSpecs/children are still in flight."""
    at = adapter.s.node(goal_node)["attrs"]
    gap_specs = adapter.inner.neighbours(goal_node, "has_gap_spec")
    if gap_specs and not all(adapter.s.node(sp)["attrs"].get("materialized") for sp in gap_specs):
        return
    children = adapter.inner.neighbours(goal_node, "has_subgoal")
    gf = at.get("gap_frame") or {}
    foc = gf.get("focus")
    if not children:
        adapter.s.set_attr(goal_node, "status", "walled")
        adapter.s.set_attr(goal_node, "note", at.get("_frontier_note") or
                           "the comprehension frontier (a question shape not parsed)")
        return
    unresolved = [c for c in children
                  if adapter.s.node(c)["attrs"].get("status") not in ("resolved", "walled")]
    if unresolved:
        return
    proxies = [_goal_as_subgoal_proxy(adapter, c) for c in children]
    grounded = [p for p in proxies if not p.is_wall]
    rel = _cg.compose_relation(gf)
    answer = _cg.render_relation(rel)
    gaps_str = ", ".join(f"{g['surface']}:{g['pos']}" for g in gf.get("gaps", []))
    held = sorted({p.target.know_concept for p in proxies
                   if not p.is_wall and p.target.know_concept})
    resolved = _cg.resolve_focus(rel, proxies, adapter.s)
    if resolved:
        adapter.s.set_attr(goal_node, "answer", resolved)
        adapter.s.set_attr(goal_node, "status", "resolved")
        adapter.s.set_attr(goal_node, "note",
                           f"parsed into typed gaps (focus={foc}); COMPOSED "
                           f"{_cg.render_relation(rel)}; RESOLVED from held "
                           f"knowledge: {resolved}")
    else:
        adapter.s.set_attr(goal_node, "answer", answer)
        adapter.s.set_attr(goal_node, "status", "walled" if not grounded else "resolved")
        adapter.s.set_attr(goal_node, "note",
                           f"parsed into typed gaps (focus={foc}; gaps={gaps_str}); "
                           f"seeded {len(children)} grounding goals, {len(grounded)} "
                           f"grounded; COMPOSED {answer}; RESOLUTION: concepts held="
                           f"{held}; the {foc} over the relation is a WELL-POSED "
                           f"FRONTIER — the relation/cause is not yet held (now "
                           f"learnable, not a wall to interpret)")


def _goal_as_subgoal_proxy(adapter, goal_node):
    """A minimal `resolve_focus`-shaped proxy (`.target.know_concept`, `.is_wall`,
    `.know_answer`) read straight off a KNOW Goal node's attrs — the graph-native
    twin of the Emission objects `resolve_focus` used to read pre-migration."""
    at = adapter.s.node(goal_node)["attrs"]
    return types.SimpleNamespace(
        target=types.SimpleNamespace(know_concept=at.get("concept")),
        is_wall=(at.get("status") == "walled"),
        know_answer=at.get("know_answer"))


_RESOLVER_FUNCTIONS = {
    "elevator_compute": elevator_compute,
    "know_ground": know_ground,
    "reflect": reflect_resolver,
    "contrast": contrast_resolver,
    "gap_parse": gap_parse,
}


# ---------------------------------------------------------------------------
# _QDAdapter — a minimal WorldAdapter-shaped facade reusing its reflex/tick
# machinery (fire_reflexes / wire_question_faculty / _question_pursue_advance,
# all substrate/world_adapter.py) over an EXISTING substrate, instead of
# re-booting a fresh boot_core() substrate every time. Bypasses WorldAdapter.
# __init__'s boot_core() call + its (irrelevant, world-specific) bookkeeping
# attributes; the only WorldAdapter methods this driver calls only touch
# .s / .inner / .agent / ._master, which this facade supplies directly.
# ---------------------------------------------------------------------------

class _QDAdapter(WorldAdapter):
    def __init__(self, s):
        self.s = s
        self.inner = getattr(s, "_inner", s)
        agent = _agent_root_node(s)
        if agent is None:
            agent = s.add_node("Agent", {})
        self.agent = agent
        self._master_state = None


_QD_SEEDS = ("math_capability_shapes", "self_design_axis", "shape_decode_loop",
             "composer_dispatch", "question_driving")


def _ensure_question_driving_seeds(adapter) -> None:
    _ensure_seed_chain(adapter.s, adapter.inner, adapter.agent, _QD_SEEDS)


# ---------------------------------------------------------------------------
# INGEST — a comprehended TargetSpec becomes a graph-resident Goal (+ SubgoalSpec-
# free recursion for compound/compare + contrast's own 2 know-children). Mechanical
# translation: writes the target's own fields onto the node; no decision over
# graph state (the kind-DISPATCH the OLD `_pursue`/`_decompose` if/elif did is now
# the seeded `qd_bind_resolver`/`qd_compound_resolve`/`qd_contrast_compare` JOINs).
# ---------------------------------------------------------------------------

def _ingest_target(adapter, target, *, parent_goal=None, gap_depth: int = 0):
    """Mint a Goal node for `target` (+ recursively for compound/compare
    subgoals, + a contrast leaf's own 2 know-children), wire it to the shared
    Agent hub (`has_goal`) and its parent (`has_subgoal`), and return the new
    Goal's NodeID. `qd_bind_resolver`/`qd_compound_resolve`/`qd_compound_wall`/
    `qd_contrast_compare` — all seeded rules — do the rest via `_pump`."""
    is_branch = target.kind in ("compound", "compare")
    attrs = {"kind": target.kind, "raw": (target.raw or "")[:160],
             "gap_depth": float(gap_depth), "status": "waiting" if is_branch else "pending"}
    if target.kind == "world" and target.op:
        attrs["op"] = target.op
        attrs["params"] = dict(target.params or {})
    elif target.kind == "know" and target.know_concept:
        attrs["concept"] = target.know_concept
    elif target.kind == "meta":
        attrs["meta_target"] = target.meta_target
        attrs["meta_arg"] = target.meta_arg
    elif target.kind == "contrast":
        attrs["x_concept"] = target.params.get("x")
        attrs["y_concept"] = target.params.get("y")
    goal = adapter.s.add_node("Goal", attrs)
    adapter.s.add_edge(adapter.agent, "has_goal", goal)
    from domains import interlocutor_model as _im
    _im.wanted_by(adapter, goal)
    if parent_goal is not None:
        adapter.s.add_edge(parent_goal, "has_subgoal", goal)
    if is_branch:
        for sub in target.subgoals:
            _ingest_target(adapter, sub, parent_goal=goal, gap_depth=gap_depth)
    elif target.kind == "contrast":
        # contrast is a LEAF relative to compound/compare recursion, but needs its
        # OWN 2 know-children for `qd_contrast_compare` to read (Neighbours(goal,
        # "has_subgoal")) — minted directly (mechanical ingest, not a decision;
        # mirrors the pre-migration `_pursue_contrast`'s two `_pursue_know` calls).
        for concept in (target.params.get("x"), target.params.get("y")):
            kgoal = adapter.s.add_node("Goal", {
                "kind": "know", "raw": f"What is {concept}?"[:160], "concept": concept,
                "gap_depth": float(gap_depth), "status": "pending"})
            adapter.s.add_edge(adapter.agent, "has_goal", kgoal)
            adapter.s.add_edge(goal, "has_subgoal", kgoal)
            _im.wanted_by(adapter, kgoal)
    return goal


def _ingest_gap_frame(adapter, gf: dict, *, missing: Optional[str] = None) -> Any:
    """Mint the "gap" root Goal (routes to the `gap_parse` Resolver via
    `qd_bind_resolver`) + a GapSpec child per typed content gap the held
    construction grammar's `parse_with_gaps` frame carries — `qd_gap_guard`
    (seeds/question_driving.json) mints the "What is X?" KNOW subgoal per spec
    (gap_depth<1 guard = the recursion bound, as DATA, replacing `self._gap_
    depth`). The noun/verb/adj/adv + dedup FILTER (which raw gaps become
    GapSpec nodes at all) is data SELECTION at ingest, mirroring the
    pre-migration Python loop's own filter verbatim — not a new decision."""
    goal = adapter.s.add_node("Goal", {
        "kind": "gap", "raw": (gf.get("focus") or "")[:160], "gap_depth": 0.0,
        "status": "pending", "gap_frame": gf, "missing": missing,
        "_frontier_note": "the comprehension frontier (a question shape not parsed)"})
    adapter.s.add_edge(adapter.agent, "has_goal", goal)
    from domains import interlocutor_model as _im
    _im.wanted_by(adapter, goal)
    seen: set = set()
    for g in gf.get("gaps", []):
        surf = g["surface"].strip(",.;:?!").lower()
        if g["pos"] not in ("noun", "verb", "adj", "adv") or not surf or surf in seen:
            continue
        seen.add(surf)
        spec = adapter.s.add_node("GapSpec", {"surface": surf, "pos": g["pos"], "materialized": 0.0})
        adapter.s.add_edge(goal, "has_gap_spec", spec)
    return goal


# ---------------------------------------------------------------------------
# THE PUMP — schedules, decides nothing: fire the `question_pursue` reflex
# (advances ONE dispatched Goal via its bound resolver) then run the seeded
# rules to fixpoint, until the root Goal resolves or walls. Same shape as the
# `agent_understands_autonomously.py` pump precedent (master_tick-then-tick),
# simplified here to fire_reflexes()+run_rules() directly (this driver's
# `_QDAdapter` facade doesn't carry WorldAdapter's thread/impasse/concurrency
# bookkeeping master_tick() also drives, which this driver has no use for).
# ---------------------------------------------------------------------------

def _wire_orphan_goals_to_agent(adapter) -> None:
    """Mechanical graph hygiene: `qd_bind_resolver`'s dispatch JOIN requires
    `Agent -has_goal-> Goal` for EVERY Goal (the shared hub both sides of the
    join key off) — a structural invariant `seeds/question_driving.json`'s own
    productions declare. Rule-MATERIALIZED children (`qd_gap_guard`'s "What is
    X?" KNOW subgoals) only wire the parent `-has_subgoal->` edge (their match
    pattern has no `ag` var to add the hub edge with); this completes the
    invariant every pump iteration so those children become dispatchable. Pure
    bookkeeping — which Goals exist is already decided (by the seeded rules or
    this driver's own ingest); this only completes their required hub edge."""
    have = set(adapter.inner.neighbours(adapter.agent, "has_goal"))
    for g in adapter.s.nodes("Goal"):
        if g not in have:
            adapter.s.add_edge(adapter.agent, "has_goal", g)


def _pump(adapter, root_goal, max_iters: int = 64) -> None:
    for _ in range(max_iters):
        _wire_orphan_goals_to_agent(adapter)
        adapter.fire_reflexes()
        adapter.inner.run_rules()
        status = adapter.s.node(root_goal)["attrs"].get("status")
        if status in ("resolved", "walled"):
            break


# ---------------------------------------------------------------------------
# THE EMISSION READ-OFF — mechanical: walk the resolved Goal tree, translate
# attrs into Emission fields. No reasoning; `compound`/`compare`'s `note` and
# `contrast`'s `know_answer` are FORMATTED here from the (already-resolved)
# children's own fields — the SAME string-assembly the pre-migration `_decompose`/
# `_pursue_contrast` did, just read off already-resolved graph data instead of
# freshly-computed Python results.
# ---------------------------------------------------------------------------

def _synth_target(at: dict):
    kind = at.get("kind")
    return types.SimpleNamespace(
        kind=kind, raw=at.get("raw"), grounded=(kind != "gap"),
        op=at.get("op"), params=dict(at.get("params") or {}),
        know_concept=at.get("concept"), meta_target=at.get("meta_target"),
        meta_arg=at.get("meta_arg"), faculty=None, reason=at.get("missing") or "",
        subgoals=[])


def _fill_emission_from_goal(adapter, emi: Emission, goal_node) -> Emission:
    at = adapter.s.node(goal_node)["attrs"]
    status = at.get("status")
    emi.is_wall = (status == "walled")
    emi.wall_kind = at.get("wall_kind")
    emi.missing = at.get("missing")
    emi.answer = at.get("answer")
    emi.verified = at.get("verified")
    emi.confidence = at.get("confidence")
    emi.know_answer = at.get("know_answer")
    emi.meta_answer = at.get("meta_answer")
    emi.note = at.get("note") or ""
    if at.get("kind") != "contrast":
        # a contrast Goal's 2 know-children are internal plumbing (fed to
        # `qd_contrast_compare` + `_finalize_contrast_know_answer`), not
        # user-visible subgoals — pre-migration, `_pursue_contrast` never
        # populated `emi.subgoals` either (only compound/compare do).
        for c in adapter.inner.neighbours(goal_node, "has_subgoal"):
            cat = adapter.s.node(c)["attrs"]
            c_emi = Emission(question_id=None, raw=cat.get("raw") or "",
                             target=_synth_target(cat), ascent=None, kind=cat.get("kind"))
            _fill_emission_from_goal(adapter, c_emi, c)
            emi.subgoals.append(c_emi)
    if emi.kind in ("compound", "compare", "contrast"):
        # the RULE-written `answer` (a bare Join/same-or-different string) is
        # NOT the emitted field at this level pre-migration — the rich text
        # lives in `note` (compound/compare) or `know_answer` (contrast).
        emi.answer = None
    if emi.kind in ("compound", "compare"):
        _finalize_compound_note(emi)
    elif emi.kind == "contrast":
        _finalize_contrast_know_answer(adapter, emi, goal_node)
    return emi


def _finalize_compound_note(emi: Emission) -> None:
    kindword = "comparison" if emi.kind == "compare" else "compound"
    walls = [i for i, c in enumerate(emi.subgoals) if c.is_wall]
    if walls:
        emi.note = (f"the {kindword} goal DECOMPOSED into {len(emi.subgoals)} "
                    f"subgoals; subgoal(s) {walls} walled (honest — the "
                    f"composed goal is blocked where a subgoal is)")
        return
    parts = []
    for c in emi.subgoals:
        if c.kind == "know":
            parts.append((c.know_answer or {}).get("answer"))
        elif c.kind == "world":
            parts.append(f"{c.target.op}={c.answer}")
        elif c.kind == "contrast":
            parts.append((c.know_answer or {}).get("answer"))
        elif c.kind == "compound":
            parts.append("(sub-compound resolved)")
        else:
            parts.append(c.kind)
    emi.note = (f"the {kindword} goal RESOLVED — every subgoal resolved by "
                "its faculty: " + " | ".join(str(p) for p in parts))


def _finalize_contrast_know_answer(adapter, emi: Emission, goal_node) -> None:
    kids = adapter.inner.neighbours(goal_node, "has_subgoal")
    if len(kids) != 2:
        return
    x_at = adapter.s.node(kids[0])["attrs"]
    y_at = adapter.s.node(kids[1])["attrs"]
    x_concept, y_concept = x_at.get("concept"), y_at.get("concept")
    wx, wy = x_at.get("status") == "walled", y_at.get("status") == "walled"
    if wx or wy:
        emi.is_wall = True
        emi.know_answer = {"answer": None}
        emi.note = (f"CONTRAST WALL: a concept did not ground "
                    f"({x_concept!r}={not wx}, {y_concept!r}={not wy}) — honest, nothing faked")
        return
    gx, gy = x_at.get("genus"), y_at.get("genus")
    same = (gx is not None and gx == gy)
    gxr, gyr = (gx or "?").replace("_", " "), (gy or "?").replace("_", " ")
    contrast = (f"{x_concept} is a {gxr}; {y_concept} is a {gyr} — "
                + ("SAME genus (they share a kind)" if same
                   else "DIFFERENT genera (they differ in kind)"))
    emi.know_answer = {"answer": contrast, "x_genus": gx, "y_genus": gy,
                       "same_genus": same, "grounded": True}
    emi.note = ("the contrast is over the two grounded genera (one hop from "
                "wiki_local — the honest contrast-leaf comprehension-depth)")
    emi.is_wall = False


# ---------------------------------------------------------------------------
# THE DRIVER — drive(pack): the self-running loop. Stimulus -> comprehend ->
# INGEST a graph-resident Goal tree -> PUMP -> mechanical Emission read-off.
# ---------------------------------------------------------------------------

class QuestionDriver:
    """The driver reflex, now a THIN WORLD ADAPTER over a graph-resident Goal
    tree + the seeded `question_driving` reflex/rules (see module docstring).
    Construct it once; call `drive(pack)` on any question pack."""

    def __init__(self, *, substrate=None):
        if substrate is not None:
            s = substrate
        else:
            s = _native.Substrate()
            _gr.open_grounding_productions(s)
        self.adapter = _QDAdapter(s)
        self.s = self.adapter.s
        _ensure_question_driving_seeds(self.adapter)
        self.adapter.register_reflex_response(
            "question_pursue", lambda ag: ag._question_pursue_advance())

    # -- STIMULUS — the raw question faithfully enters the graph as a Question node.
    def _mint_question(self, pack: QuestionPack):
        attrs = {"text": pack.text}
        if pack.question_id:
            attrs["qid"] = pack.question_id
        try:
            return self.s.add_node("Question", attrs)
        except Exception:
            return None

    def drive(self, pack: QuestionPack) -> Emission:
        """RUN the driver on a question pack: mint the stimulus, comprehend it,
        INGEST the comprehended target as a graph-resident Goal tree, PUMP the
        seeded reflex/rules to fixpoint, and MECHANICALLY read the Emission back
        off the resolved tree. NO top-level route-by-kind in Python — the
        kind-dispatch is the seeded `qd_bind_resolver` JOIN."""
        self.adapter.wire_question_faculty(dict(_RESOLVER_FUNCTIONS))
        self.adapter._master["pack_caps"] = {
            "verify": pack.verify, "answer_call": pack.answer_call,
            "feed": dict(pack.feed), "deep_reads": set(pack.deep_reads),
            "reflect": pack.reflect,
        }

        qnode = self._mint_question(pack)
        text = pack.text
        if qnode is not None:
            try:
                text = self.s.node(qnode)["attrs"].get("text", pack.text)
            except Exception:
                text = pack.text

        emi = Emission(question_id=pack.question_id, raw=text, target=None, ascent=None)
        target = _cq.comprehend(text, question_id=pack.question_id, substrate=self.s)
        emi.target = target
        emi.kind = target.kind
        if not target.grounded:
            if pack.ask is not None:
                target = self._ask_until_grounded(text, pack, emi)
                emi.target = target
                emi.kind = target.kind
            if not target.grounded:
                try:
                    gf = _cg.parse_with_gaps(text, substrate=self.s)
                except Exception:
                    gf = None
                emi.gap_frame = gf
                emi.is_wall = True
                emi.missing = target.reason
                if not (gf and gf.get("gaps")):
                    emi.note = ("the comprehension frontier (a question shape not parsed)"
                                if pack.ask is None
                                else "ASK fired but could not ground the goal "
                                     "(see the ask-transcript on the emission)")
                    return emi
                root = _ingest_gap_frame(self.adapter, gf, missing=target.reason)
                _pump(self.adapter, root)
                return _fill_emission_from_goal(self.adapter, emi, root)

        root = _ingest_target(self.adapter, target)
        _pump(self.adapter, root)
        return _fill_emission_from_goal(self.adapter, emi, root)

    # =======================================================================
    # THE ASK ACTION — a first-class goal-advancing MOVE, fired when the goal
    # CANNOT be furthered by the existing actions (COMPREHEND reached a frontier).
    # ASK = (1) FORMULATE the blocking question with the agent's OWN faculty
    # (comprehend_question.formulate_ask reads what comprehend parsed vs lacks),
    # (2) POSE it to the parent (pack.ask — mute until asked, one step only),
    # (3) INCORPORATE the one-step answer to ADVANCE the goal (pack.incorporate
    # wires the named fact into the agent's held data; the incorporated entry is
    # ALSO mirrored onto the graph as a `LexEntry` node), (4) RE-COMPREHEND. Loop
    # until the goal grounds OR the faculty cannot formulate a usable question
    # (the refined question-quality gap) OR the parent goes mute. The shell does
    # NOT author the question (the faculty does) nor the step (the parent does).
    # This is the one true I/O boundary in this driver (it talks to an external
    # answerer) — kept as a bounded Python loop per the design.
    # =======================================================================
    def _ask_until_grounded(self, text: str, pack: "QuestionPack",
                            emi: "Emission", max_asks: int = 6):
        prose = pack.prose or text
        caps = dict(_reason.CAPABILITIES)
        lex = list(_cq.load_lexicon())
        target = _cq.comprehend(text, question_id=pack.question_id,
                                substrate=self.s, lexicon=lex)
        n = 0
        while (not target.grounded) and n < max_asks:
            ask = _cq.formulate_ask(target, prose=prose)
            if ask is None:
                emi.note = ("ASK fired but the agent's faculty could not FORMULATE "
                            "a usable question from this stall (a still-silent gap "
                            "— the refined question-quality frontier)")
                break
            one_step = pack.ask(ask["question"], ask)
            rec = {"question": ask["question"], "want": ask.get("want"),
                   "lacked": ask.get("lacked"), "one_step": one_step,
                   "advanced": None}
            if one_step is None:
                rec["advanced"] = "parent mute / no one-step"
                emi.asks.append(rec)
                emi.note = ("ASK fired + the agent posed a real question, but the "
                            "parent had no one-step answer (honest halt)")
                break
            adv = None
            if pack.incorporate is not None:
                try:
                    adv = pack.incorporate(one_step, ask, caps)
                except Exception as e:                       # noqa: BLE001
                    adv = {"error": str(e)}
            if adv and isinstance(adv, dict) and adv.get("lexicon_entry"):
                entry = adv["lexicon_entry"]
                lex = [entry] + lex
                try:                                          # mirror onto the graph
                    self.s.add_node("LexEntry", dict(entry) if isinstance(entry, dict)
                                    else {"entry": entry})
                except Exception:
                    pass
            rec["advanced"] = (adv.get("how") if isinstance(adv, dict) else None) \
                or "incorporated one step"
            emi.asks.append(rec)
            target = _cq.comprehend(text, question_id=pack.question_id,
                                    substrate=self.s, lexicon=lex)
            n += 1
        pack._live_lexicon = lex                              # type: ignore[attr-defined]
        return target


__all__ = ["QuestionDriver", "QuestionPack", "Emission"]
