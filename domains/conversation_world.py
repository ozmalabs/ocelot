"""ConversationWorld — the end-to-end conversational world adapter that
wires the whole gamma-substrate language stack into a multi-turn dialogue:

    text in -> COMPREHEND -> KNOW (graph) -> PRODUCE -> SELF-MONITOR -> text out

Per CLAUDE.md this is a WORLD ADAPTER: mechanical text->graph translation
and graph->text emission. It owns no agent reasoning. Every DECISION is
graph-resident:

  * COMPREHENSION is the grounded-grammar parse (LanguageWorld) — text to a
    SemanticFrame {event, agent, patient, location, ..., tense, speech_act}.
  * KNOWLEDGE is stored as ``KnownFact`` graph NODES (slots as attrs +
    ``frame_role`` edges to Concept nodes). Storing a fact = adding a node.
  * QUESTION ANSWERING is a GRAPH MATCH over KnownFact nodes — an indexed
    ``nodes_where`` lookup on the question's first bound slot, then a
    bound-slot equality check reading node attrs (NodesWhere semantics).
    NOT a Python dict lookup of adapter state; the substrate's KnownFact
    nodes are the source of truth (a cold-loaded adapter re-derives the
    same answers by walking them).
  * RESPONSE GOAL reuses the production stack's intent->mood (mood_assignment)
    hook: an answer is a declarative goal (intent="inform"); an unmatched
    question is an honest "don't know"; an assertion gets an acknowledgement.
  * PRODUCTION + SELF-MONITOR is SelfMonitorLoop.produce_and_repair verbatim —
    the goal frame is realized and the round-trip is iterated to convergence.

Nothing here re-implements comprehension, production, or the monitor; it
only sequences them and turns the comprehended frame into KnownFact graph
mutations + a response goal.

Honest scope (see scripts/conversation_test.py for the live transcript):
  * assert -> store, question -> answer-by-graph-match, unmatched -> honest
    "I don't know" all work end-to-end on the grounded vocabulary.
  * commands/imperatives are acknowledged only — there is no world to act on.
  * answers are produced at the grammar/lexicon level the production caps
    allow (lemma + grounded function words), not free fluent text.
  * object-wh questions ("Who does Mary love?") are handled via wh-gap
    reconstruction in comprehension: a fronted wh-word marked by a grounded
    object cue (en do-support auxiliary, es personal-a, ja を particle) fills
    the object gap (patient/queried), the intervening NP fills agent. So
    "Who does Mary love?" matches the stored "Mary loves John" and answers.
"""
from __future__ import annotations

from typing import Any, Optional

from domains import language_world as lw
from domains import order_n_reasoning as onr
from domains import conjecture as conj
from domains import interrogative_reference as ireg
from domains import relative_clause_reference as rcref
from domains import reference_resolution as refres
from domains import epistemic_access as epa
from domains import dynamic_depth as dd
from domains import coherence_graph as cohg
from domains import grounded_representation as _gr
from domains import read_and_ground as rag
from domains.self_monitor import SelfMonitorLoop


def _install_request_markers(s) -> set:
    """TEACH the agent the directive-request markers (math register) as graph
    data. Reads seeds/math_request_markers.json, installs each surface as a
    RequestMarker node (idempotent), and returns the surface set. The verbs
    live in graph data (a seed -> nodes); the boundary classifier only READS
    what the agent was taught — no Python word-list decision."""
    import json
    from pathlib import Path
    surfaces: set = set()
    existing = {}
    for nid in s.nodes("RequestMarker"):
        sf = s.node(nid)["attrs"].get("surface")
        if sf:
            existing[sf] = nid
            surfaces.add(sf)
    try:
        path = Path(__file__).resolve().parent.parent / "seeds" / \
            "math_request_markers.json"
        data = json.loads(path.read_text())
    except Exception:
        return surfaces
    for sf in data.get("markers", []):
        sf = str(sf).lower().strip()
        if not sf or sf in existing:
            continue
        try:
            s.add_node("RequestMarker", {"surface": sf, "register": "math",
                                         "speech_act": "directive"})
        except Exception:
            pass
        surfaces.add(sf)
    return surfaces


# Content roles a KnownFact stores + matches on (the frame's filled slots,
# minus tense/speech_act which are not match keys for the QA). Includes the
# oblique roles the interrogative proforms query (time/cause/manner) + the
# comparative `standard`.
_FACT_SLOTS = ("event", "agent", "patient", "location", "recipient",
               "instrument", "source", "beneficiary", "topic",
               "time", "cause", "manner", "standard")
# Every interrogative placeholder is a queried (wh) slot filler — one source of
# truth in interrogative_reference (?WHO … ?HOW).
_WH = ireg.ALL_PLACEHOLDERS


class ConversationWorld:
    """Multi-turn conversation over an already-trained LanguageWorld.

    Construct with a LanguageWorld whose comprehension bank has been run
    (so the grammar / lexicon / function-words are grounded), exactly as
    LanguageProduction / SelfMonitorLoop require. Disable its teacher for
    the conversation so the replies are the agent's own grounded stack.
    """

    def __init__(self, world: "lw.LanguageWorld",
                 interlocutor: str = "user"):
        self.world = world
        self.s = world.s
        # Production + iterated self-monitor/repair — reused verbatim.
        self.loop = SelfMonitorLoop(world)
        # Per-turn trace for the transcript.
        self.transcript: list[dict[str, Any]] = []
        # The current interlocutor (a transactive source label for the
        # epistemic_access route-finder). World-side identity, not a decision.
        self.interlocutor = interlocutor
        # Optional off-path reference lookup (a world-adapter callable a host
        # may set to resolve banked REFERENCE gaps, e.g. via dictionary_lexicon
        # / wiktionary_reference). Default: the ConceptNet commonsense resolver
        # (returns None for any non-ConceptNet store, so it's purely additive —
        # a banked ConceptNet relation gap resolves off-path; a host may override
        # with a richer chained resolver). None -> banked reference gaps stay
        # pending.
        try:
            from domains import conceptnet_reference as _cn
            from domains import reference_route as _rr
            # CHAINED reference resolver: ConceptNet FIRST (cheap, local,
            # offline commonsense), then the WIKIPEDIA resolver (web_world) — the
            # taught 'reference' route's external store. Each link returns None
            # for a store it does not handle, so the chain is additive + graceful
            # (web unreachable -> None -> existing bank/ask behaviour unchanged).
            self.reference_lookup = _rr.chained_reference_lookup(
                _cn.reference_lookup, _rr.reference_lookup)
        except Exception:
            try:
                from domains import conceptnet_reference as _cn
                self.reference_lookup = _cn.reference_lookup
            except Exception:
                self.reference_lookup = None
        # Cross-utterance REFERENCE RESOLUTION state — the discourse_referent
        # store + centering, graph-resident (domains/reference_resolution.py,
        # built to seeds/reference_resolution.json). Resolves "it"/"she"/"the
        # cat" in a later turn to the entity introduced earlier.
        self.discourse = refres.DiscourseStore(self.s, world)

        # INSTALL the generator-COMPOSED capabilities (capability_compose:
        # sum_first_n / _squares / _cubes) into the LIVE reason.CAPABILITIES the
        # conversation path dispatches to — so the composed Term-trees are
        # reachable FROM TALK (the taught lexicon forms parse a question to the
        # concept; this registers the concept's composed-tree router). Additive +
        # idempotent: loads the persisted trees, evaluates them on THIS substrate,
        # never alters an existing capability. Best-effort (absent file -> no-op).
        try:
            from domains import capability_compose as _cc
            self._composed_caps = _cc.install_composed_capabilities(self.s)
        except Exception:
            self._composed_caps = {}

        # INSTALL the SELF-AUTHORED faculties (seeds/self_authored/) into the LIVE
        # reason.CAPABILITIES — the boot loader that GENERALIZES the composed-caps
        # install above (capability_compose's persist/install loop, lifted to the
        # managed dir). For each self-verified faculty: a term-tier faculty installs a
        # Term-tree router; a composition-tier faculty (e.g. a self-authored
        # betti_number) RE-GROUNDS its read gloss over the held primitives. This is
        # what makes a self-authored faculty DURABLE — it reloads here on boot rather
        # than being lost after a restart. Additive + idempotent + best-effort (absent
        # dir -> no-op); never alters an existing capability.
        try:
            from domains import self_authored as _sa
            self._self_authored = _sa.install_self_authored(self.s)
        except Exception:
            self._self_authored = {}

        # TAUGHT: directive-request markers (math register) as RequestMarker
        # graph nodes. The agent learns that an imperative opener ("Compute /
        # Find / Determine ...") is a DIRECTIVE that REQUESTS an answer, so a
        # question buried in an imperative clause ("Let X be ...; Compute Y")
        # routes to the capability layer instead of being mis-stored as an
        # assertion. The boundary classifier reads these grounded markers.
        self._request_starts = _install_request_markers(self.s)

        # TAUGHT constructions (form->meaning), graph data: e.g. the copula/
        # equative "X is the N of Y" mapping onto the seeded `relation` concept.
        # A GENERAL matcher applies whichever are present (adding one is data,
        # not code) — the agent parses by the construction it was taught.
        try:
            from domains import construction_grammar as _cg
            self._constructions = _cg.load_constructions()
        except Exception:
            self._constructions = []

        # COMPREHEND ITS SOURCE: install the agent's UNDERSTANDING of what a
        # source / encyclopedia / Wikipedia IS as graph data (seeds/
        # communication_concepts.json's source cluster: source -> reference_work
        # -> encyclopedia -> wikipedia, grounded, carrying the genre CONVENTIONS
        # + RELIABILITY the agent reads). A competent reader knows what it reads;
        # the source frames HOW it reads (lead-defines, 'In <field>,') and sets
        # the EPISTEMIC WEIGHT of what it grounds. Idempotent (the loader skips
        # held concepts). This is what makes provenance attributable + the
        # epistemic status readable OFF the held concept, not a Python constant.
        try:
            from domains import communication_concepts as _comm
            _comm.install_communication_concepts_seed(self.s)
        except Exception:
            pass

        # MATHEMATICAL BEDROCK — the math analogue of the NSM primes: seed the
        # foundational math concepts (set, relation, space, number, point,
        # boundary, ...) as the agent's grounded PRIMITIVES, so the recursive
        # Wikipedia descent over a math concept (cobordism/manifold) BOTTOMS OUT
        # at them instead of climbing one hop too far into a disambiguation page.
        # Idempotent; reuses the seeded `relation` prime (links, not duplicates).
        try:
            from domains import math_foundations as _mf
            _mf.install_math_foundations_seed(self.s)
        except Exception:
            pass

        # Open the KnownFact node/edge productions so the Rust grammar admits
        # them. Same best-effort idiom LanguageWorld uses for its own types.
        node_types = ("KnownFact", "Concept")
        edge_types = ("frame_role", "fact_event")
        for a in node_types:
            for b in node_types:
                for et in edge_types:
                    try:
                        self.s.add_production({
                            "src": {"type": a, "var": "x"},
                            "edge_type": et,
                            "tgt": {"type": b, "var": "y"},
                            "where": None,
                            "weight": {"type": "Lit", "value": 1.0},
                            "provenance": "conversation_world",
                        })
                    except Exception:
                        pass
        # Open the ReasoningChain productions so the order-N inference trace
        # (domains.order_n_reasoning) can be recorded as graph data.
        try:
            self.s.add_production({
                "src": {"type": "ReasoningChain", "var": "a"},
                "edge_type": "composed_fact",
                "tgt": {"type": "KnownFact", "var": "b"},
                "where": None,
                "weight": {"type": "Lit", "value": 1.0},
                "provenance": "conversation_world:reasoning_chain",
            })
        except Exception:
            pass
        # Open the Conjecture node so a low-weight shape-guess is recorded as
        # graph data (a Conjecture node carrying weight + basis + band), and
        # load the held epistemic markers (band -> surface hedge per language)
        # so the graded reply form reads them off the graph, not a Python dict.
        try:
            self.s.declare_attr_index("EpistemicMarker", "band")
        except Exception:
            pass
        try:
            conj.load_epistemic_markers(self.s)
        except Exception:
            pass
        # Open the epistemic_access node productions (SocialCapital budget,
        # PendingGap banked-gap nodes, EpistemicAccessStance trace) so the Rust
        # grammar admits them. Best-effort, same idiom as above.
        for nt in ("SocialCapital", "PendingGap", "EpistemicAccessStance",
                   "DepthDecision"):
            for et in ("banked_route", "stance_of"):
                try:
                    self.s.add_production({
                        "src": {"type": nt, "var": "x"},
                        "edge_type": et,
                        "tgt": {"type": "KnownFact", "var": "y"},
                        "where": None,
                        "weight": {"type": "Lit", "value": 1.0},
                        "provenance": "conversation_world:epistemic_access",
                    })
                except Exception:
                    pass
        # Initialise the social_capital budget node (graph state on the
        # conversation). Idempotent — creates one at the initial balance.
        try:
            epa._get_or_create_social_capital(self.s)
        except Exception:
            pass
        # Declare an attr index per fact slot so the QA match is an O(1)
        # graph lookup (nodes_where = NodesWhere over KnownFact), not a scan.
        for slot in _FACT_SLOTS:
            try:
                self.s.declare_attr_index("KnownFact", slot)
            except Exception:
                pass

        # COMPOSE + store the agent's graph-native COHERENCE schema (a
        # composed_by:agent Concept carrying the grounded+connected Term-tree —
        # domains/coherence_graph.py, the order_n_concepts idiom). The abstain
        # below reads this: the agent KNOWS it doesn't understand a question when
        # the engine-computed coherence of its frame falls below the
        # context-set bar. Best-effort, idempotent.
        try:
            cohg.compose_coherence_concept(self.s)
        except Exception:
            pass

        # OPEN the Concept->Concept grounding productions (built_from / depends_on
        # / grounds / genls) so the READ-AND-GROUND loop's grounding edges are
        # ADMISSIBLE in Γ (else they're silently dropped). This is what lets the
        # agent, on hitting an ungrounded concept at the abstain below, GO AND
        # LEARN it: read its definition, comprehend it, and GROUND it by composing
        # built_from edges over concepts it already holds (read_and_ground).
        # Best-effort, idempotent.
        try:
            _gr.open_grounding_productions(self.s)
        except Exception:
            pass

    # ----- speech act classification (I/O-boundary read of the frame) -----

    def _speech_act(self, frame: dict[str, Any], text: str) -> str:
        """Read the comprehended frame's speech_act. The grounded parser
        sets speech_act='question' for interrogatives; an imperative cue is
        a thin surface probe (no subject + bare verb-initial) the parser
        doesn't yet mark. Default: assertion."""
        if frame.get("speech_act") == "question":
            return "question"
        # TAUGHT directive-request markers (RequestMarker graph nodes): if any
        # CLAUSE opens with a grounded request marker ("... Compute Y", "Find
        # all ..."), this is a DIRECTIVE requesting an answer -> route like a
        # question. Reads what the agent was taught; not a hardcoded word list.
        markers = getattr(self, "_request_starts", None)
        if markers:
            for clause in text.replace("?", ".").replace(";", ".").split("."):
                toks = clause.strip().lower().split()
                if toks and toks[0].strip(",:") in markers:
                    return "question"
        # Surface imperative probe: an assertion with an event but NO agent
        # and NO wh-slot reads as a command ("Open the door."). Thin
        # I/O-boundary classifier, the kind CLAUDE.md permits.
        if (frame.get("event") and "agent" not in frame
                and not _has_wh(frame)):
            return "command"
        return "assertion"

    # ----- KNOWLEDGE: store an asserted frame as a KnownFact graph node ----

    def _store_fact(self, language: str, frame: dict[str, Any]) -> Any:
        """Store the asserted frame as a KnownFact NODE: its content slots
        as attrs (the match keys) + a frame_role edge to each filler Concept
        + a fact_event edge to the event Concept. Graph mutation only."""
        attrs: dict[str, Any] = {"language": language}
        for slot in _FACT_SLOTS:
            v = frame.get(slot)
            if isinstance(v, str) and v and v not in _WH:
                attrs[slot] = v
        if isinstance(frame.get("tense"), str):
            attrs["tense"] = frame["tense"]
        fact = self.s.add_node("KnownFact", attrs)
        # Wire the event + role concepts (graph-resident relations).
        event = frame.get("event")
        if isinstance(event, str) and event:
            ev = self.world._get_or_create_concept(event)
            try:
                self.s.add_edge(fact, "fact_event", ev, None)
            except Exception:
                pass
        for slot in _FACT_SLOTS:
            if slot == "event":
                continue
            v = frame.get(slot)
            if isinstance(v, str) and v and v not in _WH:
                cn = self.world._get_or_create_concept(v)
                try:
                    self.s.add_edge(fact, "frame_role", cn, {"role": slot})
                except Exception:
                    pass
        return fact

    # ----- KNOWLEDGE: answer a question by GRAPH MATCH over KnownFacts -----

    def _match_facts(self, frame: dict[str, Any]) -> list[Any]:
        """GRAPH MATCH: find KnownFact nodes whose BOUND slots all equal the
        question's bound slots. The queried slot (the ?WHO/?WHAT position) is
        left free. Implemented as an indexed nodes_where on the first bound
        slot (a NodesWhere over KnownFact) followed by a bound-slot equality
        check reading each candidate's node attrs — a graph operation, not a
        Python dict lookup of adapter state."""
        bound = {s: frame[s] for s in _FACT_SLOTS
                 if isinstance(frame.get(s), str) and frame[s] not in _WH}
        if not bound:
            return []
        # Seed candidates with the indexed lookup on one discriminating slot
        # (prefer event; else the first bound slot). nodes_where = NodesWhere.
        seed_slot = "event" if "event" in bound else next(iter(bound))
        candidates = self.s.nodes_where("KnownFact", seed_slot, bound[seed_slot])
        if not candidates:  # index may be absent on a cold load -> full scan
            candidates = self.s.nodes("KnownFact")
        matched: list[Any] = []
        for nid in candidates:
            a = self.s.node(nid)["attrs"]
            if all(a.get(s) == v for s, v in bound.items()):
                matched.append(nid)
        return matched

    def _answer_goal(self, frame: dict[str, Any],
                     fact_attrs: dict[str, Any]) -> dict[str, Any]:
        """Build the answer GOAL = a declarative frame filling the queried
        slot from the matched fact. intent='inform' -> declarative mood via
        the taught mood_assignment hook."""
        queried = _queried_slot(frame)
        goal: dict[str, Any] = {"intent": "inform"}
        # Start from the fact's content slots (the full known proposition),
        # so the answer is a complete restatement with the queried slot filled.
        for slot in _FACT_SLOTS:
            if isinstance(fact_attrs.get(slot), str):
                goal[slot] = fact_attrs[slot]
        if isinstance(fact_attrs.get("tense"), str):
            goal["tense"] = fact_attrs["tense"]
        # Mark which slot was the question's focus (for the transcript).
        goal["_queried_slot"] = queried
        return goal

    # ----- ORDER-N inference: chain facts when single-hop misses ----------

    def _depth_decision(self, frame: dict[str, Any]) -> dict[str, Any]:
        """Allocate the depth BUDGET for a question the single-hop match missed,
        by its RELEVANCE (domains.dynamic_depth). The user's actual question is
        HIGH relevance -> a deep budget (high max_order, costly reference tiers);
        an immaterial aside is LOW -> a shallow budget (order-1, local only). The
        decision is recorded as a DepthDecision graph node. Mechanical
        translation of the parsed frame into the controller's arguments — the
        controller (dynamic_depth) holds the relevance -> budget mapping.

        A question reaching the QA path IS the user's asked question, so
        `_asked` is marked True (HIGH relevance) unless the frame carries an
        explicit `_immaterial` aside flag (a world-adapter mark)."""
        query = dict(frame)
        query["_queried_slot"] = _queried_slot(frame)
        if not query.get("_immaterial"):
            query["_asked"] = True
        return dd.decide_depth(self.s, query, discourse_store=self.discourse,
                               interlocutor=self.interlocutor)

    def _required_coherence(self, frame: dict[str, Any],
                            question_text: str) -> dict[str, Any]:
        """The coherence BAR this question must clear to be answered, set
        DYNAMICALLY by CONTEXT via dynamic_depth.relevance (the SAME relevance
        the depth controller uses — not a new context metric). A high-relevance /
        asked / material 'compute' question demands HIGH coherence (the agent
        must really understand it before answering); a low-relevance aside
        tolerates a loose frame. The relevance SCORE in [0,1] is the bar: the
        engine-computed coherence of the frame must reach the relevance the
        question carries. Returns {required, relevance}."""
        query = dict(frame)
        query["_queried_slot"] = _queried_slot(frame)
        if not query.get("_immaterial"):
            query["_asked"] = True
        rel = dd.relevance(query, discourse_store=self.discourse,
                           interlocutor=self.interlocutor)
        # The required coherence IS the relevance the question carries: a HIGH-
        # relevance question (score ~0.9) demands a near-fully-grounded frame; a
        # LOW aside (~0.1) clears on almost anything. Heuristic mapping (the
        # same calibratable status as dynamic_depth's budget dials).
        return {"required": float(rel.get("score", 0.0)), "relevance": rel}

    def _order_n_answer(self, frame: dict[str, Any],
                        budget: Optional[dict[str, Any]] = None
                        ) -> Optional[dict[str, Any]]:
        """Order-N escalation for a question the single-hop match missed.

        Reads the comprehended question frame for an ANCHOR (a bound entity in a
        bound role) + the QUERIED relation (the event) + the QUERIED slot (the
        wh-slot), then runs the order-N operator with the DYNAMIC depth budget
        (dynamic_depth.reason_dynamic — max_order from the query's relevance +
        the jROL perseverance cutoff): chain facts over the KnownFact graph
        until the queried slot resolves, the budget caps, or the dive stalls
        (going nowhere). Mechanical translation of the parsed frame into the
        operator's arguments. Returns None if no chain resolves (the caller then
        escalates to conjecture / epistemic-access). The dynamic-depth metadata
        (order_reached, stop_reason, progress) rides on the returned dict."""
        queried = _queried_slot(frame)
        if queried is None:
            return None
        # anchor = a bound role filler (the entity the question grounds out from).
        anchor_slot = None
        anchor_entity = None
        for slot in _FACT_SLOTS:
            if slot == "event":
                continue
            v = frame.get(slot)
            if isinstance(v, str) and v and v not in _WH:
                anchor_slot, anchor_entity = slot, v
                break
        if anchor_entity is None:
            return None
        queried_relation = frame.get("event")
        if not isinstance(queried_relation, str) or not queried_relation:
            return None
        res = dd.reason_dynamic(self.s, anchor_entity=anchor_entity,
                                queried_relation=queried_relation,
                                queried_slot=queried, anchor_slot=anchor_slot,
                                budget=budget)
        if res.get("answer") is None:
            # carry the (failed) dive's depth trace so the turn can report it.
            self._last_depth_trace = res
            return None
        self._last_depth_trace = res
        return res

    def _conjecture_answer(
            self, frame: dict[str, Any]) -> Optional[dict[str, Any]]:
        """PURE CONJECTURE escalation for a question no grounded fact and no
        grounded chain resolved. Reads the same anchor + queried relation/slot
        the order-N path reads, then asks the conjecture generator
        (domains.conjecture) for an abstract-shape guess at epsilon weight
        (type/role prior + analogy), OR a partly-grounded chain completed by one
        conjectured hop. Returns the graded answer dict {answer, confidence,
        band, conjectured, basis, source} — source='inadmissible' when there is
        no shape at all. Mechanical translation of the parsed frame into the
        generator's arguments; the generator holds the shape machinery."""
        queried = _queried_slot(frame)
        if queried is None:
            return None
        anchor_slot = None
        anchor_entity = None
        for slot in _FACT_SLOTS:
            if slot == "event":
                continue
            v = frame.get(slot)
            if isinstance(v, str) and v and v not in _WH:
                anchor_slot, anchor_entity = slot, v
                break
        queried_relation = frame.get("event")
        if not isinstance(queried_relation, str):
            queried_relation = None
        return conj.answer(
            self.s, anchor_entity=anchor_entity,
            queried_relation=queried_relation, queried_slot=queried,
            anchor_slot=anchor_slot or "agent", grounded=None, record=False)

    def _reply_for_conjecture(self, language: str, frame: dict[str, Any],
                              cres: dict[str, Any]) -> str:
        """Graded reply for a conjectured answer. A type/role guess is a
        TYPE-LEVEL gloss ("a place") not a producible frame, so it is wrapped
        directly with the band's held epistemic marker ("I think it's like a
        place."). An analogy/chain conjecture names a concrete entity; it is
        produced through the normal goal->utterance path, then hedged. The hedge
        marker surface is read off the EpistemicMarker graph nodes."""
        ans = cres.get("answer")
        band = cres.get("band", "LOW")
        # Type/role gloss (answer is "a place"/"a person"/...) — not a frame.
        if isinstance(ans, str) and ans.startswith(("a ", "an ", "some ")):
            base = f"{ans}."
            return conj.hedge(self.s, base, band, language)
        # Concrete entity (analogy / conjectured-chain): produce then hedge.
        queried = _queried_slot(frame)
        goal: dict[str, Any] = {"intent": "inform"}
        if isinstance(ans, str):
            goal[queried] = ans
        if isinstance(cres.get("queried_relation"), str) and \
                cres["queried_relation"]:
            goal["event"] = cres["queried_relation"]
        goal["_queried_slot"] = queried
        try:
            r = self._produce(language, goal)
            base = r["utterance"]
        except Exception:
            base = f"{ans}."
        return conj.hedge(self.s, base, band, language)

    def _epistemic_access_stance(
            self, frame: dict[str, Any],
            budget: Optional[dict[str, Any]] = None,
            question_text: Optional[str] = None) -> dict[str, Any]:
        """Compute the epistemic_access_stance for a gap no grounded fact /
        chain / (separately) conjecture resolved: find an acquisition_route
        (transactive over the discourse store + the external references), then
        decide ask / bank / drop by the SOCIAL cost-benefit, spending
        social_capital + banking a PendingGap as graph data. Mechanical
        translation of the parsed frame into the operator's arguments — the
        operator (domains.epistemic_access) holds the route + cost machinery.

        The query frame is annotated with `_queried_slot` so the route-finder's
        reference / solved-class judgments can read it. The `budget` (from the
        depth controller) is passed so a REFERENCE route is RELEVANCE-GATED: a
        costlier reference tier (e.g. the web) is only admitted when the query's
        relevance budget affords it."""
        query = dict(frame)
        query["_queried_slot"] = _queried_slot(frame)
        # Carry the question SURFACE so the route-finder can gate the Wikipedia
        # reference to the DEFINITIONAL wh-frame (a where/when/who question is a
        # contingent person-fact -> the interlocutor route, not the encyclopedia).
        if isinstance(question_text, str) and question_text.strip():
            query["_question_text"] = question_text
        # Build a QUESTION-AWARE reference resolver for the in-turn auto-resolve:
        # the Wikipedia link reads the question text to pull a salient VALUE
        # ('what is the CAPITAL of France' -> 'Paris') over the lead sentence.
        # Falls back to self.reference_lookup (no question text) when none built.
        ref_lookup = self._reference_lookup_for_question(question_text)
        # A parallel DETAIL resolver returns the full reference hit (carrying the
        # answer's KIND: a queried-property VALUE vs the entity's definitional
        # lead) so the epistemic-access answer path can CHECK the answer coheres
        # with the queried property (Gap 2) before answering.
        ref_detail = self._reference_detail_for_question(question_text)
        return epa.decide_and_record(
            self.s, query, turn=len(self.transcript) + 1,
            discourse_store=self.discourse, interlocutor=self.interlocutor,
            depth_budget=budget, reference_lookup=ref_lookup,
            reference_detail=ref_detail)

    def _reference_lookup_for_question(self, question_text: Optional[str]):
        """A per-question chained ``reference_lookup(store, key)``: ConceptNet
        first, then the Wikipedia resolver CLOSED OVER the question text (so a
        'what is the CAPITAL of France' pulls the salient value, not just the
        lead sentence). Falls back to self.reference_lookup when the modules are
        unavailable. Mechanical world-adapter I/O; no decisions over graph
        state."""
        try:
            from domains import conceptnet_reference as _cn
            from domains import reference_route as _rr

            def _wiki(store: str, key: str):
                return _rr.reference_lookup(store, key,
                                            question_text=question_text)

            return _rr.chained_reference_lookup(_cn.reference_lookup, _wiki)
        except Exception:
            return self.reference_lookup

    def _reference_detail_for_question(self, question_text: Optional[str]):
        """A per-question ``reference_detail(store, key) -> hit-dict|None`` for the
        Wikipedia store: returns the FULL reference hit (answer + KIND — whether
        the answer fills the queried property with a VALUE or is the entity's
        definitional lead). The epistemic-access answer path reads the kind to
        check the answer coheres with the queried property (Gap 2). Returns None
        for a non-Wikipedia store. Mechanical world-adapter I/O; no decisions."""
        try:
            from domains import reference_route as _rr

            def _detail(store: str, key: str):
                low = (store or "").lower()
                if not any(h in low for h in _rr._WIKI_STORE_HINTS):
                    return None
                if not key:
                    return None
                return _rr.wikipedia_answer(key, question_text=question_text)

            return _detail
        except Exception:
            return None

    @staticmethod
    def _stance_op_str(stance: dict[str, Any]) -> str:
        """A readable knowledge-op line for the epistemic_access stance (the
        band + route + decision + rationale), for the transcript."""
        if stance.get("band") == "INADMISSIBLE":
            return ("no route -> INADMISSIBLE (honest 'I don't know'): "
                    + stance.get("why", ""))
        route = stance.get("route") or {}
        bal = stance.get("balance")
        bal_s = f"{bal:.2f}" if isinstance(bal, (int, float)) else str(bal)
        return (f"RESOLVABLE_VIA_ROUTE [{route.get('route_type')}:"
                f"{route.get('source')}] -> {stance.get('decision', '').upper()} "
                f"(social_capital {bal_s}): {stance.get('why', '')}")

    def _polar_transitive_answer(
            self, frame: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Answer a POLAR COMPARATIVE question via order-N transitive closure.

        Reads the comprehended comparative frame for the RELATION (the event,
        e.g. bigger), the SUBJECT (agent), and the STANDARD, then runs the
        transitive operator (onr.reason_transitive): is subject R standard
        derivable by chaining R-facts subject -> … -> standard? Mechanical
        translation of the parsed frame into the operator's arguments. Returns
        the resolution (yes + chain + order) or None (not derivable)."""
        relation = frame.get("event")
        subject = frame.get("agent")
        standard = frame.get("standard")
        if not all(isinstance(x, str) and x and x not in _WH
                   for x in (relation, subject, standard)):
            return None
        return onr.reason_transitive(
            self.s, relation=relation, subject=subject, obj=standard,
            left_slot="agent", right_slot="standard")

    # ----- EMBEDDED RELATIVE CLAUSE: comprehension calls reasoning --------

    def _resolve_relative_clause(
            self, text: str, language: str
    ) -> Optional[dict[str, Any]]:
        """Detect a BOUNDED embedded relative clause "[the] HEAD (REL)? SUBJ
        VERB" naming an entity, RESOLVE that entity by calling the reasoner
        (order-1: the open argument of VERB(SUBJ, ?)), and return a rewrite of
        the surface with the resolved entity substituted for the clause span.

        This is comprehension CALLING reasoning to resolve an embedded entity,
        then handing the rewritten matrix back to the normal parser — the
        genuine 2-hop surface (the inner resolve is hop 1; the matrix question
        is hop 2). Returns {rewritten, entity, clause, span} or None when no
        recognizable relative clause is present (the matrix is parsed as-is).

        BOUNDED (honest): only the generic-head + transitive zero/overt-relative
        template (relative_clause_reference). Subject-gap relatives, specific
        heads, and stacked relatives are out of scope."""
        if language not in ("en",):
            return None  # template grounded for English only (honest)
        import re as _re
        toks = _re.findall(r"[A-Za-z]+", text)
        low = [t.lower() for t in toks]
        lex = self.world._lexicon_cache.get(language, {})

        def _concept(i: int) -> Optional[str]:
            return lex.get(low[i]) if i < len(low) else None

        def _verb(i: int) -> Optional[str]:
            """The concept at i if its surface is morphologically a verb."""
            if i >= len(low):
                return None
            c = _concept(i)
            if c is None:
                return None
            return c if lw._event_tense_probe(language, low[i], c) is not None \
                else None

        for hpos in range(len(low)):
            if not rcref.is_generic_head(low[hpos], language):
                continue
            # After the head: optional relative pronoun, then SUBJ (a content
            # concept), then VERB.
            j = hpos + 1
            if j < len(low) and rcref.is_rel_pronoun(low[j], language):
                j += 1
            subj = _concept(j)
            if subj is None or subj in _WH:
                continue
            verb = _verb(j + 1)
            if verb is None:
                continue
            clause_end = j + 1  # token index of the verb
            # RESOLVE the open (object) argument of VERB(SUBJ, ?) via the
            # reasoner — order-1, the inner hop. anchor = the overt subject.
            res = onr.reason(self.s, anchor_entity=subj,
                             queried_relation=verb, queried_slot="patient",
                             anchor_slot="agent", max_order=2, record=False)
            if res is None:
                continue
            entity = res["answer"]
            # Rewrite: replace the clause span [the? HEAD … VERB] with the
            # resolved entity surface. The span starts at the head's preceding
            # determiner when present.
            start = hpos
            if hpos > 0 and low[hpos - 1] in ("the", "a", "an"):
                start = hpos - 1
            # Map token indices back to a surface rewrite over the word tokens.
            new_words = toks[:start] + [entity] + toks[clause_end + 1:]
            rewritten = " ".join(new_words)
            # Carry the question mark / terminator.
            if text.rstrip().endswith("?"):
                rewritten = rewritten + "?"
            elif text.rstrip().endswith("."):
                rewritten = rewritten + "."
            return {
                "rewritten": rewritten,
                "entity": entity,
                "clause": f"{verb}({subj}, ?) = {entity}",
                "inner_order": res["order"],
            }
        return None

    # ----- REFERENCE RESOLUTION: bind referring expressions ---------------

    def _resolve_references(self, text: str, language: str,
                            frame: dict[str, Any],
                            rec: dict[str, Any]) -> None:
        """Detect + resolve referring expressions, substitute the bound concept
        into the frame, then UPDATE the discourse store + centering from the
        (bound) frame. Records the per-expression resolution trace + the store/
        centering snapshot on ``rec``. World-side glue around the taught
        procedure (domains/reference_resolution.py); no decisions of its own."""
        store = self.discourse
        lex = self.world._lexicon_cache.get(language, {})
        exprs = refres.detect_referring_expressions(text, lex, language)
        res_trace: list[dict[str, Any]] = []
        for e in exprs:
            slot = e["slot"]
            if e["kind"] == "pronoun":
                r = store.reference_resolution_procedure(
                    e["surface"], store._turn_index + 1)
            else:  # definite "the N"
                # Only ANAPHORIC definites are resolved here: the head must
                # already be a known DiscourseReferent (uniquely_identifiable).
                # A FIRST-mention definite ("The cat sat ...") is introduced by
                # the normal parse, not bound — skip it (not anaphoric; honest).
                if e["head"] not in store._ref_nodes:
                    continue
                r = store.resolve_definite(e["head"], store._turn_index + 1)
            r["slot"] = slot
            r["kind"] = e["kind"]
            res_trace.append(r)
            if r.get("resolved") and r.get("concept"):
                concept = r["concept"]
                # Don't double-place an entity the parser already put in the
                # frame (e.g. a definite "the mat" the parser already typed as
                # location): if the concept is present in ANY slot, it's already
                # bound — record the binding, substitute nothing.
                already = any(frame.get(s) == concept for s in _FACT_SLOTS)
                if already:
                    r["substituted"] = False
                    continue
                # Substitute the bound concept into the frame slot — only into a
                # GAP (a wh-placeholder or empty slot), never over a directly-
                # named entity. The gap is exactly what the dropped pronoun left.
                cur = frame.get(slot)
                if cur is None or cur in _WH:
                    frame[slot] = concept
                    r["substituted"] = True
                else:
                    r["substituted"] = False
        if res_trace:
            rec["reference_resolution"] = res_trace

        # UPDATE the store + centering from the BOUND frame (the entities
        # realized this turn). Done every turn so the NEXT turn resolves
        # against this turn's referents (the cross-utterance state).
        realized = store.update_from_frame(frame)
        centering = store.update_centering(realized)
        rec["centering"] = {k: v for k, v in centering.items() if k != "node"}
        rec["discourse_store"] = store.snapshot()

    # ----- PRODUCE: a goal -> self-monitored reply ------------------------

    def _produce(self, language: str, goal: dict[str, Any]) -> dict[str, Any]:
        """Run the answer goal through production + the iterated self-monitor
        / repair loop. Strips the bookkeeping ``_queried_slot`` key before
        handing the goal to production."""
        clean = {k: v for k, v in goal.items() if not k.startswith("_")}
        return self.loop.produce_and_repair(language, clean)

    # ----- the turn -------------------------------------------------------

    def _capability_answer(self, text):
        """Dispatch the question to the agent's GROUNDED CAPABILITY layer (the
        math tower etc.) via reason.answer_within — the SAME faculty that
        answers a math question directly, reached from the conversation so the
        agent is ONE ENTITY, not a menu. Returns {answer, strategy} when a
        capability genuinely computes; None when the question is not a grounded
        capability (it raises there, and the turn falls through to the
        discourse/reasoning ladder). Mechanical routing of the comprehended
        question to the capability that grounds it — no decision here."""
        try:
            from domains.reason import answer_within
            ans, _est, strat = answer_within(
                str(text), {}, 1e8, teacher=None, agent=None)
        except Exception:
            return None
        if ans is None:
            return None
        # Reject a DEGENERATE parse: a bare alphabetic single-token 'answer' is
        # a Name the comprehension echoed from the question (e.g. 'G' / 'order' /
        # 'X'), not a real computation. Returning it would fabricate a garbage
        # token instead of letting the turn DECLINE honestly. A genuine grounded
        # compute is a number / bool / structured value -> keep those; fall
        # through (return None) on a name-echo so the epistemic stack answers.
        if (isinstance(ans, str) and ans.replace("_", "").isalpha()
                and len(ans.split()) == 1):
            return None
        return {"answer": ans, "strategy": strat}

    @staticmethod
    def _is_surface_number_echo(answer: Any, question_text: str) -> bool:
        """True iff the capability 'answer' is a number that appears VERBATIM in
        the question surface (an ordinal/number grabbed from the prose, e.g.
        '12th Spin bordism' -> 12, '24th letter' -> 24) rather than a value
        COMPUTED from the question (gcd 48,36 -> 12 is NOT in '48 and 36'; sum of
        squares up to 10 -> 385 is NOT in the surface). A surface echo over an
        INCOHERENT frame is the degenerate compute the abstain must catch — the
        number was lifted, not derived. A thin I/O-boundary read of the surface,
        no arithmetic on the score."""
        import re as _re
        if not isinstance(answer, (int, float)) or isinstance(answer, bool):
            return False
        nums = set(_re.findall(r"\d+", str(question_text)))
        return str(answer) in nums

    def _capability_is_genuine(self, cap: Optional[dict[str, Any]],
                               question_text: str) -> bool:
        """A capability result is a GENUINE compute (an instantiated known
        computational structure -> coherent-by-capability, the construction-match
        analog) iff it produced a numeric/bool/structured value that was NOT
        merely echoed from the question surface. A bare-name echo is already
        filtered in _capability_answer; this additionally rejects a number
        LIFTED from the prose over an incoherent frame."""
        if cap is None:
            return False
        ans = cap.get("answer")
        if ans is None:
            return False
        return not self._is_surface_number_echo(ans, question_text)

    def _consult_reference(self, question_text: str, language: str) -> int:
        """The agent doesn't know -> it LOOKS IT UP. The looked-up text enters as
        INPUT and the agent READS it with its OWN comprehension — the SAME
        grounded parse + KnownFact store it uses for a heard assertion — deciding
        per sentence (via its speech-act read) what to take as a fact. The answer
        then falls out of the NORMAL match over what it now knows. This is
        reading-and-acting, NOT forced extraction; what it can use is bounded by
        the agent's comprehension, which is the honest constraint. Returns the
        number of sentences it actually comprehended into KnownFacts."""
        try:
            from domains import web_world as ww
            from domains import reference_route as _rr
            import re as _re
        except Exception:
            return 0
        # Candidate surfaces to look up: the relation phrase ("capital of
        # France") and the bare owner noun after "of". web_world finds the page.
        surfaces: list[str] = []
        ph = _rr._relation_phrase(question_text) if hasattr(
            _rr, "_relation_phrase") else None
        if ph:
            surfaces.append(ph)
            if " of " in ph:
                surfaces.append(ph.rsplit(" of ", 1)[-1].strip())
        text = None
        for surf in surfaces:
            if not surf:
                continue
            try:
                titles = ww.wikipedia_search(surf, limit=1)
                summ = ww.wikipedia_summary(titles[0]) if titles else None
                if summ and summ.get("extract"):
                    text = summ["extract"]
                    break
            except Exception:
                continue
        if not text:
            return 0
        # READ each sentence through the agent's own comprehension + store.
        n = 0
        for sent in _re.split(r"(?<=[.!?])\s+", text):
            sent = sent.strip()
            if not sent or len(sent.split()) > 40:
                continue
            try:
                from domains import construction_grammar as _cg
                cf = _cg.apply_constructions(sent, self._constructions, language)
                if cf is None:
                    _l, _sk, shape = self.world._identify(sent, language)
                    frames = [self.world._parse_with_grounded(sent, language, shape)]
                else:
                    frames = cf if isinstance(cf, list) else [cf]
                for fr in frames:
                    if fr and self._speech_act(fr, sent) == "assertion":
                        self._store_fact(language, fr)
                        n += 1
            except Exception:
                continue
        return n

    def turn(self, text: str, language: str = "en") -> str:
        """One conversational turn: comprehend -> know -> produce -> reply.
        Returns the reply text; appends a full trace to self.transcript."""
        # 0a. EPISTEMIC-ACCESS HOUSEKEEPING (per-turn, off the social path):
        # regenerate the social_capital budget + cool the cumulative-question
        # burden, then run the deliberate babble loop — resolve any banked
        # PendingGaps via their off-path route (a reference lookup, if a host
        # supplied one) WITHOUT burdening the audience. Pure graph maintenance.
        try:
            epa.tick_social_capital(self.s)
        except Exception:
            pass
        try:
            self._banked_resolution_trace = epa.resolve_banked_gaps(
                self.s, discourse_store=self.discourse,
                interlocutor=self.interlocutor,
                reference_lookup=self.reference_lookup)
        except Exception:
            self._banked_resolution_trace = []

        # 0. EMBEDDED RELATIVE CLAUSE — comprehension calls reasoning to resolve
        # an entity named by a fact ("the person Mary loves" = the patient of
        # love(Mary,?) = John), then rewrites the matrix surface. The matrix is
        # then a normal question, run order-N end-to-end on the resolved entity
        # (the inner resolve is hop-1; the matrix question is hop-2). Bounded
        # template (relative_clause_reference); None when no clause is present.
        rel_info: Optional[dict[str, Any]] = None
        parse_text = text
        try:
            rel_info = self._resolve_relative_clause(text, language)
        except Exception:
            rel_info = None
        if rel_info is not None:
            parse_text = rel_info["rewritten"]

        # 1. COMPREHEND (grounded parse — LanguageWorld, teacher disabled).
        _lang, _shape_key, shape = self.world._identify(parse_text, language)
        frame = self.world._parse_with_grounded(parse_text, language, shape)
        # CONSTRUCTION override: if a TAUGHT form->meaning construction matches the
        # surface (e.g. "X is the N of Y" / "what is the N of Y" -> the seeded
        # `relation` concept), parse by THAT — the SVO heuristic can't see the
        # copula, but the taught construction can. Graph-data driven, not a rule.
        construction_matched = False
        try:
            from domains import construction_grammar as _cg
            _cf = _cg.apply_constructions(parse_text, self._constructions, language)
            if _cf:
                construction_matched = True  # an instantiated KNOWN structure
                if isinstance(_cf, list):
                    # a coordination yields a LIST of frames; the turn proceeds on
                    # the first, and the EXTRA conjuncts are stored now (a typed
                    # "X is the A and B of Y" asserts both A and B of Y = X).
                    frame = _cf[0]
                    for _extra in _cf[1:]:
                        if (isinstance(_extra, dict)
                                and self._speech_act(_extra, parse_text) == "assertion"):
                            try:
                                self._store_fact(language, _extra)
                            except Exception:
                                pass
                else:
                    frame = _cf
        except Exception:
            pass
        act = self._speech_act(frame, text)

        rec: dict[str, Any] = {
            "user": text, "language": language,
            "frame": dict(frame), "speech_act": act,
        }
        if rel_info is not None:
            rec["relative_clause"] = rel_info
            rec["rewritten_matrix"] = parse_text

        # 1b. CROSS-UTTERANCE REFERENCE RESOLUTION (reference_resolution_*).
        # Detect referring expressions (pronouns it/he/she/they/him/her/them;
        # definite "the N" re-mentions) in the surface, RESOLVE each to a
        # discourse_referent's concept via the store's procedure, and SUBSTITUTE
        # the bound concept into the frame slot it fills — so the rest of the
        # turn (store fact / answer / produce) runs on the BOUND frame. The
        # parser drops bare pronouns, so the binding restores the lost slot.
        self._resolve_references(text, language, frame, rec)
        rec["frame"] = dict(frame)  # the BOUND frame the turn proceeds on

        # 2. UPDATE / QUERY KNOWLEDGE (graph-resident).
        if act == "assertion":
            fact = self._store_fact(language, frame)
            rec["knowledge_op"] = f"stored KnownFact {_nid(fact)}"
            goal = {"intent": "acknowledge", "_kind": "ack"}
            reply, prod = self._reply_for_ack(language)
            rec["response_goal"] = goal
            rec["reply"] = reply
            rec["monitor_passes"] = prod
            self.transcript.append(rec)
            return reply

        if act == "command":
            rec["knowledge_op"] = "no world to act on (honest)"
            goal = {"intent": "acknowledge", "_kind": "ack"}
            reply, prod = self._reply_for_ack(language)
            rec["response_goal"] = goal
            rec["reply"] = reply
            rec["monitor_passes"] = prod
            self.transcript.append(rec)
            return reply

        # act == question.
        # GROUNDED CAPABILITY first — single entity, not a menu: talking reaches
        # EVERY faculty. Dispatch the question to the agent's grounded capability
        # layer (reason.answer_within -> the math tower etc.) — the same faculty
        # that computes a math answer, reached from the conversation. A genuine
        # capability match computes the answer; a conversational question raises
        # there and falls through to the discourse/reasoning ladder below
        # (verified: chat questions all raise, so this never hijacks talk).
        cap = self._capability_answer(text)
        cap_genuine = self._capability_is_genuine(cap, text)

        # COHERENCE ABSTAIN — the agent reads its OWN graph-native coherence of
        # the comprehended frame (domains/coherence_graph: the composed-by:agent
        # grounded+connected Term-tree, computed by substrate.evaluate) against a
        # bar set DYNAMICALLY by CONTEXT (dynamic_depth.relevance: a high-
        # relevance/material/asked question demands HIGH coherence to answer; a
        # casual aside tolerates low). A construction match OR a GENUINE
        # capability compute is an instantiated KNOWN structure -> coherent. If
        # the engine-computed coherence falls below the bar, the agent KNOWS it
        # doesn't understand this question well enough HERE -> it abstains
        # HONESTLY and runs NONE of the capability / reference / conjecture
        # token-grab below (which would fabricate a confidently-wrong answer
        # from a degenerate parse). This is how a person knows a question won't
        # cohere and says 'I don't understand', not a guess.
        # SHORT-CIRCUIT FIX — a `what is the {relation} of {owner}` construction
        # match is an instantiated KNOWN structure (coherence 1.0) ONLY IF the
        # queried RELATION actually grounds (is a held concept OR the agent can
        # ground it by the deep recursive descent — read_and_ground.relation_
        # grounds). A relation the agent neither holds NOR can ground ("largest
        # order of a non-cyclic torsion subgroup of an elliptic curve") must NOT
        # force coherence to 1.0 — otherwise the agent fabricates a confident
        # answer (a RolePrior conjecture, "I think it's like an animal") for a
        # question it doesn't understand. When the relation is un-grounded the
        # short-circuit is DENIED, the frame's real (low) coherence stands, and
        # the conjecture token-grab is suppressed below so the agent ABSTAINS —
        # while the reference route (which answers "capital of France" -> Paris)
        # is still allowed to run. The relation is the queried `event` slot.
        relation_construction_ungrounded = False
        if construction_matched and not cap_genuine \
                and frame.get("construction") == "relation":
            _rel = frame.get("event")
            try:
                if not rag.relation_grounds(self.s, _rel, self):
                    relation_construction_ungrounded = True
            except Exception:
                relation_construction_ungrounded = False
        _construction_for_coherence = (construction_matched
                                       and not relation_construction_ungrounded)

        coh = cohg.coherence(self.s, frame,
                             _construction_for_coherence or cap_genuine)
        cbar = self._required_coherence(frame, text)
        _coh_fillers = cohg.content_fillers(frame)
        rec["coherence"] = {
            "value": coh, "required": cbar["required"],
            "relevance_band": cbar["relevance"].get("band"),
            "construction_matched": construction_matched,
            "relation_construction_ungrounded": relation_construction_ungrounded,
            "capability_genuine": cap_genuine,
            "fillers": _coh_fillers}
        # READ-AND-GROUND (live learning): BEFORE abstaining on a low-coherence
        # frame, the agent GOES AND LEARNS the ungrounded content fillers — it
        # READS each one's definition, COMPREHENDS it with its construction
        # grammar, and GROUNDS it by composing built_from edges over concepts it
        # already holds (recursively, toward the seeded primitives —
        # domains/read_and_ground.py). Then it RE-COMPUTES coherence: if the
        # learning closed the gap it proceeds (it LEARNED the concept live); if a
        # definition would not comprehend, the filler stays ungrounded and the
        # agent abstains HONESTLY below (comprehension is the named bottleneck).
        # Only fires on the abstain path — already-coherent questions never reach
        # here. Best-effort; a failed lookup leaves coherence unchanged.
        if _coh_fillers and coh < cbar["required"]:
            try:
                learned = rag.learn_ungrounded_fillers(self.s, frame, self)
                rec["read_and_ground"] = learned
                if learned.get("any_grounded"):
                    coh = cohg.coherence(self.s, frame,
                                         _construction_for_coherence
                                         or cap_genuine)
                    rec["coherence"]["value_after_learning"] = coh
                    rec["coherence"]["value"] = coh
            except Exception:
                pass

        # Abstain only when there IS content to judge AND it fails to cohere. A
        # CONTENTLESS frame (a bare "Why?", no content fillers) is not an
        # incomprehension of CONTENT — it falls through to the existing
        # epistemic ladder, which declines it honestly (INADMISSIBLE) on its own
        # terms. The coherence abstain is for an ungrounded/disconnected CONTENT
        # frame (research prose), not for an empty one. After read-and-ground, the
        # agent only abstains if the learning could NOT ground the fillers.
        #
        # EXCEPTION — a relation-construction question whose RELATION did not
        # ground (the short-circuit fix) does NOT abstain HERE: the reference
        # route below still answers "what is the capital of France?" (a held
        # external fact), so we let it flow through the normal pipeline and only
        # abstain at the BOTTOM — suppressing the weak conjecture token-grab
        # (which is what produced the confidently-wrong "I think it's like an
        # animal") — if no grounded route resolves it. This keeps a real lookup
        # answerable while killing the fabrication.
        if (_coh_fillers and coh < cbar["required"]
                and not relation_construction_ungrounded):
            rec["knowledge_op"] = (
                f"NOT_COMPREHENDED: graph-native coherence {coh:.3f} < required "
                f"{cbar['required']:.3f} (relevance {cbar['relevance'].get('band')}"
                f") -> the agent doesn't understand this; abstain honestly "
                f"(no capability/reference token-grab)")
            rec["band"] = "NOT_COMPREHENDED"
            rec["confidence"] = 0.0
            reply, prod = self._reply_for_not_comprehended(language)
            rec["response_goal"] = {"intent": "inform",
                                    "_kind": "not_comprehended"}
            rec["reply"] = reply
            rec["monitor_passes"] = prod
            self.transcript.append(rec)
            return reply

        if cap is not None and cap_genuine:
            rec["knowledge_op"] = (
                f"grounded capability (compute, {cap['strategy']}): "
                f"{cap['answer']!r}")
            rec["response_goal"] = {"intent": "inform", "_kind": "capability"}
            reply = f"{cap['answer']}."
            rec["reply"] = reply
            rec["monitor_passes"] = 0
            self.transcript.append(rec)
            return reply

        # POLAR (yes/no) question — no wh slot, a truth-value query. A POLAR
        # COMPARATIVE ("Is the cat bigger than the mouse?") asks whether the
        # ordering relation holds between agent and standard; answer it with the
        # order-N TRANSITIVE closure (onr.reason_transitive — bigger(cat,dog) +
        # bigger(dog,mouse) => bigger(cat,mouse)). N scales with the question.
        if frame.get("polar"):
            res = self._polar_transitive_answer(frame)
            if res is not None:
                rec["knowledge_op"] = (
                    f"order-{res['order']} transitive closure "
                    f"(ReasoningChain {_nid(res['node'])}): {res['chain_str']}")
                rec["reasoning_chain"] = res
                reply = _YES_TOKEN.get(language, "Yes.")
                rec["response_goal"] = {"intent": "inform", "_kind": "polar_yes"}
                rec["reply"] = reply
                rec["monitor_passes"] = 0
                self.transcript.append(rec)
                return reply
            # No derivation -> honest unknown (we cannot prove it; we do NOT
            # assert "no" — absence of a derivation is not a disproof).
            rec["knowledge_op"] = (
                "polar question: no transitive derivation -> honest unknown")
            goal = {"intent": "inform", "_kind": "dont_know"}
            reply, prod = self._reply_for_dont_know(language)
            rec["response_goal"] = goal
            rec["reply"] = reply
            rec["monitor_passes"] = prod
            self.transcript.append(rec)
            return reply

        matches = self._match_facts(frame)
        if not matches:
            # CONSULT the reference: the agent doesn't know, so it LOOKS IT UP.
            # The looked-up text enters as INPUT; the agent READS it with its own
            # comprehension into KnownFacts and then RE-ANSWERS from the normal
            # match — like a person opening Wikipedia. Reading, not extraction;
            # bounded by what the agent can comprehend.
            try:
                if self._consult_reference(text, language):
                    matches = self._match_facts(frame)
            except Exception:
                pass
        if not matches:
            # ESCALATE to order-N inference: no single (order-1) fact matched,
            # so try CHAINING facts over the KnownFact graph (the agent's
            # order-N operator, lifted to relations — domains.order_n_reasoning).
            # The DEPTH is now DYNAMIC + RELEVANCE-WEIGHTED (domains.dynamic_
            # depth): the query's relevance sets the budget (max_order +
            # affordable reference tiers), and the dive abandons early when it
            # stops progressing (the jROL perseverance cutoff). A HIGH-relevance
            # asked question dives deep; a LOW-relevance aside is capped at
            # order-1 + local-only and stops fast.
            depth = self._depth_decision(frame)
            rec["depth_decision"] = {
                "relevance": depth["relevance"], "budget": depth["budget"]}
            res = self._order_n_answer(frame, budget=depth["budget"])
            if res is not None:
                # record the resolving dive's outcome on the DepthDecision node.
                try:
                    dd.record_outcome(
                        self.s, depth,
                        order_reached=res.get("order_reached", res.get("order")),
                        stop_reason=res.get("stop_reason", "resolved"),
                        resolved=True)
                except Exception:
                    pass
                rec["depth_decision"]["order_reached"] = res.get("order_reached")
                rec["depth_decision"]["stop_reason"] = res.get("stop_reason")
                rec["knowledge_op"] = (
                    f"order-{res['order']} chain resolved "
                    f"(ReasoningChain {_nid(res['node'])}): {res['chain_str']}")
                rec["reasoning_chain"] = res
                goal = {"intent": "inform"}
                queried = _queried_slot(frame)
                goal[queried] = res["answer"]
                goal["event"] = res["queried_relation"]
                goal["_queried_slot"] = queried
                rec["response_goal"] = goal
                r = self._produce(language, goal)
                rec["reply"] = r["utterance"]
                rec["monitor_passes"] = r["passes"]
                rec["converged"] = r["converged"]
                rec["monitor_trace"] = r["trace"]
                rec["confidence"] = conj.chain_confidence(res["order"])
                rec["band"] = conj.band(rec["confidence"])
                self.transcript.append(rec)
                return rec["reply"]
            # The order-N dive missed — record its OUTCOME (order reached, why it
            # stopped: budget / no_progress / no_chain) on the DepthDecision node,
            # so the trace shows a dive that abandoned early (jROL) vs ran to the
            # budget cap.
            dive = getattr(self, "_last_depth_trace", None) or {}
            try:
                dd.record_outcome(
                    self.s, depth,
                    order_reached=dive.get("order_reached", 0),
                    stop_reason=dive.get("stop_reason", "no_chain"),
                    resolved=False)
            except Exception:
                pass
            rec["depth_decision"]["order_reached"] = dive.get("order_reached", 0)
            rec["depth_decision"]["stop_reason"] = dive.get("stop_reason",
                                                            "no_chain")

            # ESCALATE to CONJECTURE: no grounded fact, no grounded chain — but
            # the agent may still hold an abstract SHAPE to guess from (the
            # queried slot's expected category; an analogous same-slot fact; or a
            # partly-grounded chain completed by one conjectured hop at epsilon).
            cres = self._conjecture_answer(frame)
            has_shape = cres is not None and cres["source"] != "inadmissible"

            # EPISTEMIC ACCESS: independently of the shape, ask whether the gap
            # is RESOLVABLE_VIA_ROUTE (an interlocutor who'd know / an external
            # reference / a lookupable class) and DECIDE ask / bank / drop by the
            # SOCIAL cost-benefit (materiality vs social_capital + cumulative
            # burden + flow + face). This inserts a band between conjecture and
            # the categorical inadmissible. The decision SPENDS social_capital on
            # an ask and BANKS a PendingGap when banked (graph-resident). The
            # reference escalation it routes to is RELEVANCE-GATED by the depth
            # budget — a low-relevance gap never reaches the costly (web) tier.
            stance = self._epistemic_access_stance(
                frame, budget=depth["budget"], question_text=text)
            rec["epistemic_access"] = stance

            # A REFERENCE route that RESOLVED off-path in this turn beats a
            # conjecture SHAPE: a grounded looked-up fact is preferred over a
            # guess, so suppress the conjecture-combine and answer from the
            # reference (the lookupable/definitional gap converted to a fact).
            if stance.get("decision") == "answered":
                has_shape = False

            # SHORT-CIRCUIT FIX (bottom half) — a relation-construction question
            # whose RELATION did not ground and which NO grounded route resolved
            # must ABSTAIN, not conjecture. The construction matched the surface
            # ("what is the {relation} of {owner}") but the queried relation is
            # un-held and un-groundable, so a RolePrior guess ("I think it's like
            # an animal") would be confidently wrong. We deferred the coherence
            # abstain past the reference route (so "capital of France" still got
            # Paris); here, with the route having failed, the agent abstains
            # honestly instead of grabbing a token from a degenerate parse.
            if relation_construction_ungrounded \
                    and stance.get("decision") != "answered":
                rec["knowledge_op"] = (
                    f"NOT_COMPREHENDED: relation-construction matched but the "
                    f"queried relation {frame.get('event')!r} does not ground "
                    f"(un-held + un-groundable) and no route resolved it -> "
                    f"abstain honestly (no conjecture token-grab)")
                rec["band"] = "NOT_COMPREHENDED"
                rec["confidence"] = 0.0
                reply, prod = self._reply_for_not_comprehended(language)
                rec["response_goal"] = {"intent": "inform",
                                        "_kind": "not_comprehended"}
                rec["reply"] = reply
                rec["monitor_passes"] = prod
                self.transcript.append(rec)
                return reply

            # --- combine the shape (conjecture) with the route decision -------
            conj_reply: Optional[str] = None
            if has_shape:
                rec["confidence"] = cres["confidence"]
                rec["band"] = cres["band"]
                rec["conjecture"] = cres
                cnode = conj.record_conjecture(self.s, cres)
                conj_reply = self._reply_for_conjecture(language, frame, cres)
                rec["knowledge_op"] = (
                    f"no grounded fact/chain -> {cres['source'].upper()} "
                    f"(weight={cres['confidence']:.3f}, band={cres['band']}, "
                    f"Conjecture {_nid(cnode)}): {cres['basis']}")
            # Reply form integrates conjecture + the route stance (combine where
            # natural: "I think it's like X — want me to find out for sure?").
            reply = epa.reply_for_stance(stance, frame, language,
                                         conjecture_reply=conj_reply)

            # The band a turn REPORTS: a conjecture shape keeps its LOW band; a
            # pure route gap (no shape) reports RESOLVABLE_VIA_ROUTE; nothing at
            # all is INADMISSIBLE.
            if not has_shape:
                rec["band"] = stance["band"]
                rec["confidence"] = 0.0
            rec["knowledge_op"] = (
                (rec.get("knowledge_op", "") + "  |  " if has_shape else "")
                + self._stance_op_str(stance))
            rec["response_goal"] = {"intent": "inform",
                                    "_kind": ("conjecture" if has_shape
                                              else stance["decision"])}
            rec["reply"] = reply
            rec["monitor_passes"] = 0
            self.transcript.append(rec)
            return reply

        fact_attrs = self.s.node(matches[0])["attrs"]
        ambiguous = len(matches) > 1
        rec["knowledge_op"] = (
            f"matched KnownFact {_nid(matches[0])} {dict(fact_attrs)}"
            + (f"  (AMBIGUOUS: {len(matches)} facts matched, picking one)"
               if ambiguous else ""))
        goal = self._answer_goal(frame, fact_attrs)
        rec["response_goal"] = goal
        # TERSE wh-answer: a wh-question asks for ONE slot's filler, so the reply
        # is that filler as a noun-phrase answer ("Paris.") — how a person answers
        # "what is the capital of France?" — not a full restatement of the fact.
        _q = _queried_slot(frame)
        _ans = fact_attrs.get(_q) if _q else None
        if isinstance(_ans, str) and _ans and _ans not in _WH:
            reply = _ans[:1].upper() + _ans[1:]
            if reply[-1:] not in ".?!":
                reply += "."
            r = {"utterance": reply, "passes": 0, "converged": True, "trace": []}
        else:
            r = self._produce(language, goal)
        # The articulator already terminates the utterance; emit as-is.
        reply = r["utterance"]
        rec["reply"] = reply
        rec["monitor_passes"] = r["passes"]
        rec["converged"] = r["converged"]
        rec["monitor_trace"] = r["trace"]
        rec["ambiguous"] = ambiguous
        # A directly stored, directly read grounded fact = full confidence.
        rec["confidence"] = conj.grounded_confidence()
        rec["band"] = conj.band(rec["confidence"])
        self.transcript.append(rec)
        return reply

    # ----- minimal grounded replies for ack / dont_know -------------------

    def _reply_for_ack(self, language: str) -> tuple[str, int]:
        """Acknowledgement. There is no propositional content to produce, so
        the reply is a fixed grounded discourse token ("OK." / "Vale." / ...).
        HONEST: this is a canned acknowledgement token, NOT a produced frame
        — there is nothing to say back beyond 'understood'."""
        return _ACK_TOKEN.get(language, "OK."), 0

    def _reply_for_dont_know(self, language: str) -> tuple[str, int]:
        """Honest 'I don't know' for an unmatched question. A fixed grounded
        token (the FEATURE: the agent declines rather than fabricating). Also
        canned, reported as such."""
        return _DONT_KNOW_TOKEN.get(language, "I don't know."), 0

    def _reply_for_not_comprehended(self, language: str) -> tuple[str, int]:
        """Honest 'I don't understand this' — the agent read its OWN
        engine-computed coherence of the question's frame against the
        context-set bar (dynamic_depth.relevance) and found the frame does NOT
        cohere in its concept graph: it has not understood the question well
        enough to answer here. A fixed grounded token (the FEATURE: the agent
        declines on NON-COMPREHENSION rather than fabricating from a token-grab).
        Distinct from 'I don't know' (comprehended-but-no-fact)."""
        return _NOT_COMPREHENDED_TOKEN.get(
            language, "I don't understand this."), 0


# ---------------------------------------------------------------------------
# Helpers — pure reads, no graph decisions.
# ---------------------------------------------------------------------------


def _has_wh(frame: dict[str, Any]) -> bool:
    return any(frame.get(s) in _WH for s in _FACT_SLOTS)


def _queried_slot(frame: dict[str, Any]) -> Optional[str]:
    for s in _FACT_SLOTS:
        if frame.get(s) in _WH:
            return s
    return None


def _nid(node) -> str:
    """A NodeID's display string (for the trace). The native NodeID already
    str()s to '#<n>'."""
    return str(node)


# Fixed grounded discourse tokens. These are the only canned strings — used
# only where there is no propositional frame to produce (acknowledgement;
# honest unknown). Everything propositional goes through production.
_ACK_TOKEN = {
    "en": "OK.", "es": "Vale.", "zh": "好。", "ja": "はい。",
}
_DONT_KNOW_TOKEN = {
    "en": "I don't know.", "es": "No lo sé.",
    "zh": "我不知道。", "ja": "わかりません。",
}
# Honest NON-COMPREHENSION token — the question did not cohere in the agent's
# concept graph at the context-set bar, so it declines to answer (it doesn't
# understand), distinct from a comprehended-but-unknown gap.
_NOT_COMPREHENDED_TOKEN = {
    "en": "I don't understand this.", "es": "No entiendo esto.",
    "zh": "我不理解这个。", "ja": "これは理解できません。",
}
# Polar-question affirmative. A fixed grounded discourse token (like the ack /
# don't-know tokens) — a yes/no answer has no propositional frame to produce.
_YES_TOKEN = {
    "en": "Yes.", "es": "Sí.", "zh": "是。", "ja": "はい。",
}
