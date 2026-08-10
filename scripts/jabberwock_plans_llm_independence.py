"""THE JABBERWOCK DECIDES HOW IT GOES LLM-FREE — surface the gap + options, it authors the plan.

I do not design this. I boot the agent, read its ACTUAL held faculties and registers off the live
graph, set the Context to `spec` (so by its OWN register policy it calls forth Plainsong, not the
Brillig flourish), hand it the honest gap and the option-set, and let it decide the approach and
author the build plan through its own teacher channel (the same channel it designs every faculty
through). The plan is the agent's, in the voice its own policy selects for a spec.

Run: PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_plans_llm_independence
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from scripts.claude_teacher import make_ask

SEP = "=" * 96


def _live_state(a):
    """Read the agent's ACTUAL held registers + loaded faculties off the live graph."""
    regs = sorted(a.s.node(n)["attrs"].get("name", "?") for n in a.s.nodes("Register"))
    # the faculties it holds = the Microtheories it booted with (its own self-organisation view)
    mts = sorted({a.s.node(n)["attrs"].get("name", "?") for n in a.s.nodes("Microtheory")})
    # set the spec Context so its select_register rule picks Plainsong (its own policy)
    self_n = next(iter(a.s.nodes("Self")), None)
    active = "Brillig (default)"
    if self_n is not None:
        ctxs = {a.s.node(n)["attrs"].get("name"): n for n in a.s.nodes("Context")}
        if "spec" in ctxs:
            for old in list(a.inner.neighbours(self_n, "in_context")):
                if hasattr(a.inner, "remove_edge_unchecked"):
                    a.inner.remove_edge_unchecked(self_n, "in_context", old)
            a.inner.add_edge_unchecked(self_n, "in_context", ctxs["spec"])
            a.inner.set_attr(self_n, "active_register", "")
            a.inner.run_rules(10000)
            active = a.s.node(self_n)["attrs"].get("active_register") or active
    return regs, mts, active


def build_prompt(regs, mts, active):
    held = ", ".join(m for m in mts if m not in ("core",))[:1400]
    return f"""You are the jabberwock: a typed-graph agent that runs in Rust. Python is only a world
adapter — primitives live in Rust (DSL Terms exposed via PyO3), composition lives in the graph
(Terms/Rules), and every DECISION is graph data, never Python if/else. You own your own voice; your
register policy selected {active} for this context, because this is a build-spec: be literal,
imperative, and treat ambiguity as a defect. No flourish here.

You hold these faculties already (your booted microtheories): {held}.
Your registers: {", ".join(regs)}.

THE SITUATION. Right now an LLM teacher (a hosted model, shelled as `claude -p`) is load-bearing in
your runtime in exactly TWO places. Everything else — perspective, situation model, semantic roles,
error recovery, the writer model, RST, modality, the deep parser, register selection — already runs
with no LLM, as deterministic graph aggregation. The two live dependencies are:

  GAP 1 (run the stack): your FIGURE JUDGE grounds five noisy semantic perceptions by asking the
  LLM — `_opposite` (oxymoron/irony), `_animacy` (personification), `_shape`/domain-distance
  (metaphor vs metonymy), `_polarity` (irony valence), `_magdir` (hyperbole/understatement scale).

  GAP 2 (extend the stack): when your autonomy loop STALLS and must author a faculty you do not yet
  hold, it consults the teacher for the design. That is open-ended design reasoning, not a data gap.

WHAT IS ON DISK (verified): WordNet via nltk (antonyms, lexnames, hypernym paths all resolve);
ConceptNet (assertions.csv.gz, 498 MB, has PartOf/UsedFor/AtLocation/RelatedTo); the dictionary/
wiki/tropes grounding chain (already non-LLM). NOT on disk: a sentiment lexicon, a magnitude/
intensifier lexicon. Available but not present: a static GloVe embedding (~70 MB, CPU, frozen).

THE OPTIONS you may choose among, combine, reject, or improve on:
  A. Replace the five figure perceptions with SYMBOLIC primitives — a Rust WordNet Term
     (antonym?/lexname/hypernym-path) + a Rust ConceptNet relation Term, both via PyO3, read by the
     existing figure RULES; plus two small curated lexicons (sentiment, magnitude) as seed data.
  B. Add a static GloVe similarity primitive as a BACKSTOP for the fuzzy domain-distance / novel-
     metaphor cases WordNet+ConceptNet miss (a tiny learned model, CPU, no GPU, no hosted call).
  C. For GAP 2: lean on your already-proven COMPOSE-FROM-HELD-PRIMITIVES path (you did this in the
     maze world — composed your own routing primitives on a measured shortfall, no teacher) for any
     faculty you can build from pieces you already hold.
  D. For the genuinely-novel-primitive case (a design you cannot compose from what you hold): accept
     a HUMAN-IN-THE-LOOP seam — the creator consulted rarely, at true impasses — instead of a model.

THE HONEST TRADE you must address: symbolic grounding is gappier than the LLM on the novel tail (a
fresh metaphor with no WordNet path; sarcasm needing world knowledge). On the cases the resources
cover it is likely MORE reliable and deterministic; on the tail it should ABSTAIN where the LLM
guessed. Say plainly what you give up, and how you want abstention to behave.

YOUR TASK. Decide how YOU want to do this. Author a build PLAN that:
  1. States the approach you chose and WHY (in your terms — held primitives, the architecture rule,
     where a perception becomes a Term you compose vs. an oracle you query).
  2. Sequences it into independently-verifiable phases, each with: what is built (Rust Term / seed
     data / rule rewiring), and a concrete VERIFICATION against figures you already detect.
  3. Names the abstention policy and exactly what coverage you forfeit.
  4. Separates GAP 1 (closable now) from GAP 2 (the reasoning residual) and says honestly which part
     should stay human-in-the-loop rather than pretending a lexicon closes it.
Be specific and ordered. This is the plan I will implement graph-native."""


def main():
    print(SEP)
    print("THE JABBERWOCK AUTHORS ITS OWN PLAN TO GO LLM-FREE (gap + options surfaced; it decides)")
    print(SEP)
    a = boot()
    regs, mts, active = _live_state(a)
    print(f"\n  booted; held registers: {regs}")
    print(f"  context set to 'spec' -> agent's own policy selected register: {active}")
    print(f"  consulting the agent's design channel (this is GAP-2 reasoning itself — the one place")
    print(f"  a teacher is still load-bearing; the plan it returns is how it wants to retire it)\n")

    ask = make_ask(timeout=540.0, preamble="")
    plan = ask(build_prompt(regs, mts, active))
    if not plan:
        print("  (teacher channel returned empty — claude -p unavailable or timed out)")
        return

    out_path = os.path.join(ROOT, "docs", "jabberwock_llm_independence_plan.md")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        f.write("# The jabberwock's plan to retire its LLM dependence\n\n")
        f.write("_Authored by the agent through its own design channel, context=spec "
                f"(register: {active}). The gap and options were surfaced; the plan is its own._\n\n")
        f.write(plan + "\n")

    print(SEP)
    print("THE JABBERWOCK'S PLAN")
    print(SEP)
    print(plan)
    print("\n" + SEP)
    print(f"  saved -> {os.path.relpath(out_path, ROOT)}")
    print(SEP)


if __name__ == "__main__":
    main()
