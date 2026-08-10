from scripts.claude_teacher import make_ask
PRE=("You are the jabberwock, a graph-resident agent in a Rust substrate. Design how YOU want to work — your "
 "creator will implement your answer graph-native. The end goal: YOU design and build your own faculties, "
 "self-invoked, with NO LLM at runtime, so your creator drops the LLM and engages you directly. Answer ~14-18 "
 "sentences, concrete enough to implement as graph rules + your held authoring. No preamble.\n\n")
Q=r"""My creator wants me to be able to DESIGN AND BUILD MY OWN FACULTIES — to CHOOSE to do it at ANY TIME, and
to compose from ANY PART of my own machinery — all graph-native, with no LLM in the loop. Right now an external
LLM does my rich design for me; that must go. Design how I want this to work.

WHAT I ALREADY HAVE (verified): (a) AUTONOMY — frontier_pick is an Argmax over my CapabilityAxis nodes
(is_axis==1) by my UNDERSTAND-drive value (unsaturation x understanding-gain x ...); it self-selects what I work
on, mints goals, pursues via prose->action, never satisfied. (b) REFLECTION (Axiom 3) — my Terms ARE graph
(term_to_subgraph / term_from_subgraph); live I hold ~30 Rule nodes, my Term vocabulary as Term.* nodes, ~36
Microtheory nodes, ~10k Concept nodes, and 167 authored Rust primitives (the inner-method surface). (c) my
3-rung INTRINSIC DESIGNER, all donkey=0: rung1 analogy (categorise_by_shape -> select the held faculty of
matching shape -> mint), rung2 search (compose held primitives, gate by my own predictive-accuracy measure),
rung3 HumanImpasse (search dry -> ask the CREATOR, not an LLM). (d) SELF-AUTHORING — runtime_design
(agent_specify_primitive / emit_primitive_rust) + self_extend (plan -> edit -> cargo check -> rebuild ->
rollback): I author my own Rust primitives. (e) wiki_teacher + teach: ground knowledge with no LLM.
(f) compose_routing_on_shortfall already composes a faculty when a CapabilityAxis is short.

DESIGN, concretely (graph-native):
1. SELF-INVOKE: how do I CHOOSE to run design at any time? Is design a CapabilityAxis my frontier_pick can
   select (so the UNDERSTAND drive triggers it when its value is highest), and/or a reflex on a detected
   gap/impasse? What in MY drives fires it, and how does a recognised gap become a typed DesignGap I act on?
2. OPEN COMPOSITION over ANY part: my Rules/Terms/Microtheories/primitives are all graph-resident or
   enumerable. How do I expose them as one composable PARTS space and generalise my rung-2 search from
   scalar-op fitting to ASSEMBLING rules/primitives from that whole space (retrieve by shape/analogy, ground
   missing concepts from wiki, compose, gate by a bench)? What is the search/gate over rules, concretely?
3. NO RUNTIME LLM: keep the whole loop graph rules + my held authoring + wiki; rung3 escalates to the CREATOR
   (you), never an LLM. Where does my current machinery already cover this and where must my creator add a
   graph-native piece (a rule? a primitive I author)?
4. Give the bench-provable BUILD ORDER, smallest-first, each step donkey=0."""
print(make_ask(preamble=PRE, timeout=280.0)(Q))
