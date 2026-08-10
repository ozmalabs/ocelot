"""HLE as a WORLD the agent lives in.

A bank of HLE-style questions is the environment; a TEACHER (an LLM, supplied as
a callable) sits in it; the agent traverses the questions. On each one it
recognises what it doesn't yet know, ASKS the teacher, grounds the returned
definition into its own graph-resident vocabulary, then answers — and the
concept stays grounded for every later question. So the agent's capability GROWS
through living in the world (autopoietically), no per-concept code from outside.
"""
from __future__ import annotations

from typing import Callable


class HLEWorld:
    """A small HLE-style environment: a queue of (question, gold-answer) and the
    teacher the agent may consult about unknown words."""

    def __init__(self, questions: list, teacher: Callable = None,
                 agent=None):
        self.questions = list(questions)
        self.teacher = teacher
        self.agent = agent

    def run(self) -> list:
        """The agent traverses the world. Returns a per-question log with what
        was asked, what was answered, whether it matched the gold."""
        log = []
        for text, gold in self.questions:
            asked = self.agent.discover_unknown_words(text)
            ans = self.agent.answer_predicate(text, teacher=self.teacher)
            log.append({"question": text, "asked": asked, "answer": ans,
                        "gold": gold, "correct": ans == gold})
        return log

    def run_parallel(self) -> list:
        """A richer traversal: the entity fires OS threads to ask the teacher
        about EVERY upcoming unknown IN PARALLEL up-front, while a cooperative
        line on the main thread keeps answering question-by-question — joining
        each ask only when the answer needs it. For an I/O-bound teacher
        (real LLM calls) this turns N serial round-trips into ~one."""
        # Phase 1 — fire one OS thread per distinct unknown across the bank
        unknowns: set = set()
        for text, _ in self.questions:
            unknowns.update(w for w in self.agent.discover_unknown_words(text)
                            if self.agent.word_meaning(w) is None)
        ask_threads = {w: self.agent.spawn_python_thread(
                           self.teacher, args=(w,), task=f"ask:{w}")
                       for w in unknowns}
        # Phase 2 — the main line answers sequentially, grounding each ask
        # as the question needs it (most asks are already done by then)
        log = []
        for text, gold in self.questions:
            for w in self.agent.discover_unknown_words(text):
                if w in ask_threads and self.agent.word_meaning(w) is None:
                    spec = self.agent.join_thread(ask_threads[w])
                    if spec is not None:
                        self.agent.ground_from_spec(w, spec)
            ans = self.agent.answer_predicate(text)
            log.append({"question": text, "asked": [], "answer": ans,
                        "gold": gold, "correct": ans == gold})
        return log

    def run_cooperative(self, cortex=None) -> list:
        """The richest mode — OS threads ask the teacher in the background while
        a COOPERATIVE main line keeps answering. On each question the agent
        fires an OS thread for any unknown it hasn't already asked about; if all
        the question's unknowns are already grounded it answers immediately;
        otherwise it DEFERS this question and moves on. Deferred questions are
        drained at the end (most asks have completed by then). So the agent
        doesn't stall on a slow ask — it keeps producing answers in the
        meantime. ``cortex`` (optional) scopes learning to that cortex."""
        ask_threads: dict = {}
        deferred: list = []
        results_by_q: dict = {}

        def _unknowns_now(text):
            return [w for w in self.agent.discover_unknown_words(text, cortex=cortex)
                    if self.agent.word_meaning(w, cortex=cortex) is None]

        for text, gold in self.questions:
            for w in _unknowns_now(text):
                if w not in ask_threads:        # don't re-ask the same word
                    ask_threads[w] = self.agent.spawn_python_thread(
                        self.teacher, args=(w,), task=f"ask:{w}")
            if not _unknowns_now(text):          # all unknowns already grounded?
                ans = self.agent.answer_predicate(text, cortex=cortex)
                results_by_q[text] = {"question": text, "asked": [],
                                      "deferred": False, "answer": ans,
                                      "gold": gold, "correct": ans == gold}
            else:
                deferred.append((text, gold))    # come back when asks land

        # drain the deferred queue — join any threads still in flight
        for text, gold in deferred:
            for w in self.agent.discover_unknown_words(text, cortex=cortex):
                if w in ask_threads and self.agent.word_meaning(w, cortex=cortex) is None:
                    spec = self.agent.join_thread(ask_threads[w])
                    if spec is not None:
                        self.agent.ground_from_spec(w, spec, cortex=cortex)
            ans = self.agent.answer_predicate(text, cortex=cortex)
            results_by_q[text] = {"question": text,
                                  "asked": list(self.agent.discover_unknown_words(
                                                    text, cortex=cortex)),
                                  "deferred": True, "answer": ans,
                                  "gold": gold, "correct": ans == gold}
        return [results_by_q[t] for t, _ in self.questions]

    def run_multi_cortex(self, default_cortex=None) -> list:
        """The agent ROUTES each question to the cortex it most belongs in (by
        vocabulary overlap), grounding new vocabulary into that cortex. So the
        entity grows multiple specialised cortices in parallel — math words
        land in math, biology words in biology — rather than one default
        vocabulary piling up. ``default_cortex`` is used when no cortex matches."""
        log = []
        for text, gold in self.questions:
            cx = self.agent.route_question(text, default=default_cortex)
            asked = []
            for w in self.agent.discover_unknown_words(text, cortex=cx):
                if self.agent.word_meaning(w, cortex=cx) is None:
                    spec = self.teacher(w)
                    if spec is not None:
                        self.agent.ground_from_spec(w, spec, cortex=cx)
                        asked.append(w)
            ans = self.agent.answer_predicate(text, cortex=cx)
            log.append({"question": text, "cortex": cx, "asked": asked,
                        "answer": ans, "gold": gold, "correct": ans == gold})
        return log

    def run_cross_domain(self, cortexes, learning_cortex=None) -> list:
        """Cross-domain mode — comprehension SPANS N lexicons (the listed
        cortexes), so a question may use vocabulary from any of them. New
        vocabulary still grounds into ONE cortex per word — the agent routes
        each unknown to its best-matching cortex (or ``learning_cortex`` if no
        cortex stands out)."""
        log = []
        for text, gold in self.questions:
            asked = []
            for w in self.agent.discover_unknown_words(text, cortex=cortexes):
                if self.agent.word_meaning(w, cortex=cortexes) is None:
                    spec = self.teacher(w)
                    if spec is not None:
                        # route this unknown to the cortex with most overlap
                        target = self.agent.route_question(text,
                                                           default=learning_cortex)
                        if target is None:
                            target = cortexes[0] if cortexes else None
                        self.agent.ground_from_spec(w, spec, cortex=target)
                        asked.append({"word": w, "into": target})
            ans = self.agent.answer_predicate(text, cortex=cortexes)
            log.append({"question": text, "asked": asked, "answer": ans,
                        "gold": gold, "correct": ans == gold})
        return log

    def run_solve(self, bindings_factory=None, budget_ops: float = 1e8,
                  progress=None) -> list:
        """Math-style traversal. Each question is sent through ``reason.answer_within``
        — the function-style reasoning path that estimates the COMPLEXITY of the
        planned computation against an ops budget BEFORE running it. A capability
        whose cost-estimator says it would burn 10^50 trial-divisions is declined
        upfront (``status: "complexity_exceeded"``) — the agent understands its
        own cost. A KeyError is a concept HOLE (``no_capability``). Other
        exceptions are recorded too. ``bindings_factory(question, gold) → dict``
        (optional) supplies the per-question object bindings."""
        from domains.reason import answer_within, BudgetExceeded, UnknownShape
        log = []
        total = len(self.questions)
        for i, (text, gold) in enumerate(self.questions):
            bindings = bindings_factory(text, gold) if bindings_factory else {}
            entry = {"question": text, "gold": gold,
                     "answer": None, "correct": False,
                     "status": "answered", "error": None,
                     "estimated_ops": None, "strategy": None}
            try:
                # the world's teacher is the agent's fallback when its shape
                # library doesn't recognise the question — it asks instead
                # of fabricating a parse
                ans, est, strategy = answer_within(
                    text, bindings, budget_ops,
                    teacher=self.teacher, agent=self.agent)
                entry["answer"] = ans
                entry["estimated_ops"] = est
                entry["strategy"] = strategy
                entry["correct"] = _eq_hle(ans, gold)
                if strategy == "taught":
                    entry["status"] = "taught"
                elif strategy == "learned":
                    entry["status"] = "learned"
                elif strategy != "default":
                    entry["status"] = "reconsidered"
            except UnknownShape as e:
                entry["status"] = "unknown_shape"
                entry["error"] = str(e)
            except BudgetExceeded as e:
                entry["status"] = "complexity_exceeded"
                entry["error"] = str(e)
            except KeyError as e:
                entry["status"] = "no_capability"
                entry["error"] = str(e)
            except Exception as e:
                entry["status"] = "error"
                entry["error"] = f"{type(e).__name__}: {e}"
            log.append(entry)
            if progress is not None:
                progress(i + 1, total, entry)
        return log

    def run_llm_style(self, conversation_world, limit=None,
                      progress=None) -> list:
        """Present each question the SAME WAY an LLM gets it — the full question
        text (and any context) as ONE prompt — through the agent's CURRENT
        comprehension -> reason -> epistemic-access pipeline
        (``ConversationWorld.turn``). No math bindings, no pre-parse, no teacher
        scaffolding: the raw question IS the prompt. Records the response plus
        WHERE the pipeline fell short, read off the turn's transcript.

        Per-question entry: {question, gold, reply, speech_act, comprehended
        (the parser recovered an event + a grounded argument, not just tokens),
        band (INADMISSIBLE / LOW|MID|HIGH conjecture / RESOLVABLE_VIA_ROUTE),
        stance (the knowledge_op line), correct}. Read the gap with
        ``gap_map_llm`` — it bins each response at the FIRST stage it breaks.

        World-adapter work: hand the opaque external question to the agent,
        read the graph state back out. No agent-side decisions here."""
        cw = conversation_world
        items = self.questions if limit is None else self.questions[:limit]
        total = len(items)
        log = []
        for i, item in enumerate(items):
            text, gold = item[0], item[1]
            entry = {"question": text, "gold": gold, "reply": None,
                     "speech_act": None, "comprehended": False,
                     "band": None, "stance": None, "correct": False,
                     "error": None}
            try:
                reply = cw.turn(str(text), "en")
                rec = (cw.transcript[-1]
                       if getattr(cw, "transcript", None) else {})
                frame = rec.get("frame") or {}
                entry["reply"] = reply
                entry["speech_act"] = rec.get("speech_act")
                entry["band"] = rec.get("band")
                entry["stance"] = rec.get("knowledge_op")
                # COMPREHENDED = the parser recovered a real predicate (an event
                # plus at least one GROUNDED argument slot), not just tokens it
                # could not shape into a frame.
                entry["comprehended"] = bool(
                    frame.get("event") and any(
                        isinstance(frame.get(s), str) and frame.get(s)
                        for s in ("agent", "patient", "topic", "location",
                                  "recipient", "instrument", "source")))
                entry["correct"] = _eq_hle(reply, gold)
            except Exception as e:
                entry["error"] = f"{type(e).__name__}: {e}"
            log.append(entry)
            if progress is not None:
                progress(i + 1, total, entry)
        return log

    @staticmethod
    def gap_map_llm(log: list) -> dict:
        """Where the LLM-style response falls short — each question binned at the
        FIRST stage it breaks at, so the counts read off the GAP:

          not_comprehended    — the NL parser could not shape the question into a
                                 frame (built for simple SVO/wh, not exam prose)
          miscomprehended_assert — a QUESTION mis-parsed as an assertion and
                                 silently 'stored' as a fake fact (reply 'OK') —
                                 a false-comprehension gap, NOT an answer
          inadmissible         — comprehended, but no grounded fact/chain/route ->
                                 the honest 'I don't know'
          resolvable_via_route — comprehended, knows a reference/route could supply it
          conjecture           — comprehended, only a low-weight shape-guess
          answered_grounded    — comprehended AND produced a grounded/chain answer
          correct              — the answer matched the gold (a subset of the above)

        For HLE the honest expectation is the mass sits in not_comprehended (the
        agent's comprehension is for simple sentences) then inadmissible (no
        grounded domain knowledge) — that IS the gap map."""
        out = {"questions": len(log), "correct": 0, "answered_grounded": 0,
               "degenerate_echo": 0, "conjecture": 0, "resolvable_via_route": 0,
               "inadmissible": 0, "miscomprehended_assert": 0,
               "not_comprehended": 0, "coherence_abstain": 0, "errors": 0}
        for e in log:
            if e.get("error"):
                out["errors"] += 1
                continue
            if e.get("correct"):
                out["correct"] += 1
            band = (e.get("band") or "").upper()
            stance = e.get("stance") or ""
            # COHERENCE ABSTAIN: the agent read its OWN graph-native coherence of
            # the parsed frame against the context-set bar and found it does NOT
            # cohere -> honest non-comprehension ('I don't understand this'),
            # NOT a fabricated answer. Caught FIRST: this is the win — a question
            # the parser shaped into tokens but the agent KNOWS it doesn't
            # understand (the confidently-wrong degenerate compute / token-grab
            # now declines).
            if "NOT_COMPREHENDED" in band or "NOT_COMPREHENDED" in stance:
                out["coherence_abstain"] += 1
                continue
            if not e.get("comprehended"):
                out["not_comprehended"] += 1
                continue
            # a capability 'answer' that is a single token ECHOED from the
            # question (e.g. 'G' / 'order' / 'X') is a degenerate parse, not a
            # real computation — the comprehension grabbed a name and returned
            # it. Distinguish from a genuine grounded compute (a number/bool).
            reply = str(e.get("reply") or "").rstrip(".").strip()
            is_echo = ("grounded capability" in stance and reply
                       and reply.replace("_", "").isalpha()
                       and len(reply.split()) == 1
                       and reply.lower() in str(e.get("question", "")).lower())
            if "stored KnownFact" in stance or e.get("speech_act") == "assertion":
                # a question read as a statement + silently accepted as a fact —
                # false comprehension, not an answer.
                out["miscomprehended_assert"] += 1
            elif "INADMISSIBLE" in band or "INADMISSIBLE" in stance:
                out["inadmissible"] += 1
            elif "RESOLVABLE_VIA_ROUTE" in band or "RESOLVABLE_VIA_ROUTE" in stance:
                out["resolvable_via_route"] += 1
            elif band in ("LOW", "MID", "HIGH") or "weight=" in stance:
                out["conjecture"] += 1
            elif is_echo:
                out["degenerate_echo"] += 1
            else:
                out["answered_grounded"] += 1
        return out

    @staticmethod
    def summary(log: list) -> dict:
        """Capability growth read off the log: how much was asked vs answered."""
        return {"questions": len(log),
                "correct": sum(1 for e in log if e.get("correct")),
                "asks": sum(len(e.get("asked", [])) for e in log),
                "distinct_words_learned": len(
                    {w for e in log for w in e.get("asked", [])
                     if isinstance(w, str)})}

    @staticmethod
    def gap_map(log: list) -> dict:
        """Counts of question OUTCOMES, the way to read off where the gap is:
        correct / wrong-answer / concept-hole (no_capability) / runtime-error."""
        out = {"questions": len(log), "correct": 0, "reconsidered": 0,
               "taught": 0, "learned": 0, "wrong": 0, "unknown_shape": 0,
               "no_capability": 0, "complexity_exceeded": 0, "errors": 0}
        for e in log:
            status = e.get("status", "answered")
            if e.get("correct"):
                out["correct"] += 1
                if status == "reconsidered":
                    out["reconsidered"] += 1
                elif status == "taught":
                    out["taught"] += 1
                elif status == "learned":
                    out["learned"] += 1
                continue
            if status == "taught":
                out["taught"] += 1               # teacher answered (right/wrong both)
                continue
            if status == "learned":
                out["learned"] += 1              # agent routed via taught capability
                continue
            if status == "unknown_shape":
                out["unknown_shape"] += 1
            elif status == "no_capability":
                out["no_capability"] += 1
            elif status == "complexity_exceeded":
                out["complexity_exceeded"] += 1
            elif status == "error":
                out["errors"] += 1
            else:
                out["wrong"] += 1
        return out


def _eq_hle(ans, gold) -> bool:
    """Comparison robust to ``5003 == "5003"`` (the gold is a string in the
    bank; the substrate returns an int / list / bool). Numeric strings are
    coerced; lists compare as sorted sequences of strings; otherwise str-eq
    after stripping surrounding whitespace and ``$`` LaTeX delimiters."""
    if isinstance(gold, str):
        g = gold.strip().strip("$").strip()
    else:
        g = gold
    if isinstance(ans, bool):
        return str(ans).lower() == str(g).lower()
    if isinstance(ans, (int, float)):
        try:
            return float(ans) == float(g)
        except (TypeError, ValueError):
            return str(ans) == str(g)
    if isinstance(ans, list):
        return [str(x) for x in ans] == [s.strip() for s in str(g).split(",")]
    return str(ans).strip() == str(g).strip()


def load_hle_math_bank(path: str, only_exact_match: bool = True) -> list:
    """Read an HLE math JSON bank from ``path`` and return ``(question, gold)``
    pairs (the shape ``HLEWorld`` expects). Multiple-choice items are skipped
    by default — the substrate's reasoning path returns values, not letters."""
    import json
    with open(path) as f:
        bank = json.load(f)
    out = []
    for q in bank:
        if only_exact_match and q.get("answer_type") != "exactMatch":
            continue
        out.append((q["question"], q["answer"]))
    return out
