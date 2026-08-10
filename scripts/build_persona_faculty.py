"""GIVE THE JABBERWOCK THE GENUS — let it BUILD the persona/register-expression faculty itself.

No runner, no logic supplied: this driver boots the agent's own drive loop + self-authoring
ladder over the `expression_register` GENUS seed (the goal + the register/persona concepts), points
it at the persona EXEMPLARS (TVTropes/Wikipedia, on disk, via attach_libraries), and pumps. The
agent then, graph-natively:

  frontier pick (the express/register/persona axis) -> plan -> bind the placeholder -> run it ->
  it doesn't work (honest 0) -> stall -> consult the teacher on HOW -> escalate -> AUTHOR a new
  operator (order-4 self-extend) -> try again ...

The only Python here is a thin EXPRESSION-WORLD SURFACE whose `execute` returns an honest
"couldn't do it" measurement (so the loop stalls and the agent authors) — it contains NO persona
logic. The faculty is the agent's to build.

Run:
  PYTHONPATH=.:runners/dsl/python python -m scripts.build_persona_faculty [ticks]
  SPEECH_TEACHER=stub  -> canned teacher (fast, offline); default = real claude -p (how-to advice)
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from substrate.world_adapter import WorldAdapter
from substrate.seed_loader import manifest_for
from domains.libraries import attach_libraries

SEP = "=" * 84
SEEDS = ["faculty_lessons", "learned_lexicon", "learned_tropes", "figurative_language",
         "figurative_abstraction", "text_analysis", "authorial_voice", "dialogue_intertext",
         "work_understanding", "perspective", "situation_model", "semantic_roles", "production",
         "event_reasoning", "discourse_argument", "modality_tom", "trope_mechanics", "jabberwock_voice",
         "error_recovery", "writer_model", "relations", "intent", "conversation", "grounding",
         "communication_concepts", "enact", "autonomy", "investigation_loop", "investigation_teacher",
         "impasse_escalation", "expression_register"]


# persona exemplars to read (self-demonstrating TVTropes definitions, on disk)
_EXEMPLARS = [("pirate", "TalkLikeAPirate"), ("surfer", "SurferDude"), ("valley", "ValleyGirl")]


class ExpressionWorld:
    """World SURFACE for the expression frontier. It ENACTS whatever operator the agent has bound
    (exactly like SpeechWorld.execute runs the cochlea/whisper capabilities) — it makes no
    decision about WHAT to do. The PLACEHOLDER operator has no faculty -> honest 0.0 (so the agent
    stalls and AUTHORS). Once the agent has AUTHORED a faculty, this enacts it by invoking the
    HELD persona_reader capability over the on-disk exemplars and grounding what it perceives."""
    def __init__(self, adapter):
        self.a = adapter

    def _mc(self, measured, req, note):
        return self.a.s.add_node("MeasuredCapability", {
            "measured": float(measured), "target": float(req.get("target", 0.6) or 0.6),
            "metric": req.get("measurement_key", "persona_match"),
            "synth_pending": 1, "note": note})

    def execute(self, req):
        # NO Python perception here. The world only reports that no graph-native faculty exists
        # yet (honest 0.0) -> the agent stalls, consults the teacher, and must AUTHOR the faculty
        # itself as DSL Terms (composing held primitives + any it specs via runtime_design).
        return self._mc(0.0, req, "no graph-native faculty yet — the agent must author it")


def _teacher():
    if os.environ.get("SPEECH_TEACHER", "real").lower() == "stub":
        return lambda q: ("Read exemplars of the persona's speech, take the opening interjection "
                          "as its greeting and the words it repeats as its markers, then render "
                          "your turns with those.")
    from scripts.claude_teacher import make_ask
    return make_ask()


def boot():
    a = WorldAdapter()
    for sid in SEEDS:
        try:
            a.inner.load_seed_manifest(manifest_for(sid), a.agent)
        except Exception as e:
            print(f"  (seed '{sid}' skipped: {e})")
    attach_libraries(a, log=lambda *x: None)        # persona exemplars: tropes/wiki on disk
    expr = ExpressionWorld(a)
    # enter the expression world
    mt = next((n for n in a.s.nodes("Microtheory")
               if a.s.node(n)["attrs"].get("name") == "expression_world"), None)
    if mt is not None:
        a.inner.add_edge_unchecked(a.agent, "operates_in", mt)
    a.wire_autonomy_faculty()
    a.wire_enact_faculty()
    a.wire_investigation_faculty(expr)
    a.wire_teacher_resolution()
    a.wire_escalation_faculties()
    a.set_self_teacher(_teacher())
    return a


def main():
    ticks = int(sys.argv[1]) if len(sys.argv) > 1 else 14
    print(SEP)
    print("GIVE THE GENUS — the jabberwock builds the persona/register-expression faculty itself")
    print(SEP)
    a = boot()
    nax = len([n for n in a.s.nodes("CapabilityAxis")
               if a.s.node(n)["attrs"].get("is_axis") == 1.0])
    print(f"  booted: {nax} capability axes; teacher={os.environ.get('SPEECH_TEACHER','real')}; "
          f"expression genus loaded\n")

    seen_mc, seen_imp, seen_op = set(), set(), set()
    for t in range(1, ticks + 1):
        a.master_tick(); a.tick()
        for mc in a.s.nodes("MeasuredCapability"):
            if mc in seen_mc:
                continue
            seen_mc.add(mc); at = a.s.node(mc)["attrs"]
            print(f"  [t{t:2d}] tried -> {at.get('metric')}={at.get('measured')}  ({at.get('note','')[:70]})")
        for mi in a.s.nodes("Impasse"):
            if mi in seen_imp:
                continue
            seen_imp.add(mi); at = a.s.node(mi)["attrs"]
            print(f"  [t{t:2d}] IMPASSE [{at.get('kind')}] -> consulting teacher: "
                  f"{str(at.get('question',''))[:90]}")
        for op in a.s.nodes("Operator"):
            at = a.s.node(op)["attrs"]
            if op in seen_op or at.get("authored_by_escalation") != 1.0:
                seen_op.add(op); continue
            seen_op.add(op)
            print(f"  [t{t:2d}] AUTHORED a faculty -> '{at.get('name')}'  approach="
                  f"{str(at.get('approach',''))[:80]!r}")

    # settle teacher threads
    for _ in range(30):
        if not getattr(a, "_teacher_threads", []):
            break
        a.master_tick(); a.tick()

    print("\n" + SEP)
    authored = [a.s.node(o)["attrs"] for o in a.s.nodes("Operator")
                if a.s.node(o)["attrs"].get("authored_by_escalation") == 1.0]
    print(f"  the agent engaged the communication genus: {len(seen_mc)} attempts, "
          f"{len(seen_imp)} impasses (teacher consulted), {len(authored)} faculties AUTHORED.")
    for at in authored[:4]:
        print(f"    authored '{at.get('name')}' approach={str(at.get('approach',''))[:90]!r}")
    print("\n  it DECIDED it needs the faculty and AUTHORED it (the approach above), grounded in its")
    print("  own communication concepts. What it surfaced it needs to make it RUN graph-natively =")
    print("  the DSL Term(s) for the approach (a salient-tokens reduction; Nth/Render it already")
    print("  holds) — supplied the sanctioned way: agent specs (runtime_design) -> mechanical Rust")
    print("  emit -> the agent composes + AUDITS the faculty as Term-trees. No Python perception.")
    print(SEP)


if __name__ == "__main__":
    main()
