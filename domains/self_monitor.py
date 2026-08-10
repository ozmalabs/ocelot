"""SelfMonitorLoop — the ITERATED produce -> monitor -> diagnose -> repair
loop that makes the taught ``self_monitoring_loop`` concept real (Levelt's
perceptual loop; seeds/lang_production.json).

This extends the SINGLE-SHOT self-monitor already in
``language_production.py`` (produce -> parse-back -> compare -> one
alternative-surface swap) into an ITERATED, TARGETED loop: "say it to
yourself", iterated, with harder cases taking more passes — order-N
analysis-by-synthesis applied to PRODUCTION.

WHICH MONITORING MECHANISM (monitoring_mechanism_debate, lang_production.json)
============================================================================
This is the COMPREHENSION-BASED PERCEPTUAL LOOP variant (Levelt/Roelofs):
the monitor IS the comprehension stack — we parse the produced utterance
back with the SAME ``LanguageWorld`` parser the comprehension bank uses and
compare the recovered representation to the production-selected one. The
FORWARD-MODEL variant (Pickering & Garrod: compare a PREDICTED against the
IMPLEMENTED representation) is the same "say it to yourself" loop seen from
the other side — here the recovered_frame plays the role of the implemented
representation and the goal_frame the predicted one; the loop structure is
identical. We note this rather than build a separate forward model, because
the substrate's comprehension parser already gives us the implemented read.

THE LOOP
========
``produce_and_repair(goal_frame, language, max_passes) ->
  {utterance, passes, converged, trace}``

  1. PRODUCE  — a BARE realization from the goal frame: content words in the
     language's grounded word order, NO function words yet. (Bare lemma-level
     production is what comprehension grounds first; the markers are added
     only as the monitor reveals they are needed. This is what makes the
     iteration visible: a frame needing two markers takes two passes.)
  2. MONITOR  — parse the utterance back with the comprehension stack ->
     recovered_frame. (THE MONITOR IS THE COMPREHENSION STACK; we do not
     build a second parser.)
  3. DIAGNOSE — a structured, per-slot discrepancy between goal and recovered,
     each mismatch CLASSIFIED (localizes the error to a slot + kind):
       slot_missing  goal has the role, recovered doesn't
       wrong_role    right concept, wrong slot (e.g. a location recovered as
                     patient because its preposition is missing)
       wrong_filler  recovered a DIFFERENT concept for the slot
       wrong_tense   tense feature differs
       extra_slot    recovered a role the goal didn't ask for
  4. CONVERGED — no discrepancy -> accept.
  5. REPAIR   — ONE repair, targeted at the top discrepancy, from GROUNDED
     ALTERNATIVES only (driven by the recovered discrepancy, not a hardcoded
     English fix table):
       wrong_role / slot_missing on an oblique-marked role -> insert the
         grounded role-marking function word (preposition for en/es,
         case particle for ja/zh) so comprehension recovers the right role.
       wrong_filler -> re-select the slot's surface from the grounded
         alternatives (other LexEntry surfaces for the concept).
       slot_missing with no grounded marker AND no alternative surface ->
         mark UNREALIZABLE.
       wrong_tense -> re-inflect from an alternative grounded inflected
         surface for the concept.
     Apply ONE repair, record it.
  6. RE-PRODUCE with the repair applied; loop to step 2. STOP on: converged,
     max_passes reached, or NO-PROGRESS (the discrepancy set did not shrink
     after a repair, or the only available repair was already tried) —
     deadlock detection so it cannot loop forever.
  7. TRACE    — each pass records a MonitorPass node wired to the goal:
     {pass_index, utterance, recovered_frame_summary, discrepancy,
      repair_applied, outcome}. Inspectable self-correction history.

``max_passes`` defaults to (number of content slots + 1) so harder
(more-slot) cases get more passes — "harder cases take more passes".

ARCHITECTURE (CLAUDE.md). This is a WORLD ADAPTER. The iterate-until-converge
CONTROL FLOW is a loop here; the MONITOR is the comprehension stack; the
DIAGNOSIS reads graph-recovered frames; the REPAIR choices come from GROUNDED
graph data (LexEntry surfaces, FunctionWord nodes, the VerbNet-derived
role->preposition table). No new agent decisions: every repair is a grounded
alternative selected by the recovered discrepancy. The trace is graph data.
"""
from __future__ import annotations

import json
from typing import Any, Optional

from domains import language_world as lw
from domains import preposition_roles as preprole
from domains import language_production as lp


# Roles that surface as an oblique PP / particle-marked NP — the ones a
# grounded function word marks. location is the coarse spatial role;
# FINE_ROLES are the VerbNet-derived oblique roles.
_MARKED_ROLES = {"location"} | set(preprole.FINE_ROLES)


class SelfMonitorLoop:
    """The iterated monitor+repair loop over LanguageProduction's grounded
    pipeline. Construct with an already-trained LanguageWorld (run the
    comprehension bank first), same as LanguageProduction."""

    def __init__(self, world: "lw.LanguageWorld"):
        self.world = world
        self.s = world.s
        self.prod = lp.LanguageProduction(world)
        # Open the trace productions so the Rust grammar admits the
        # ProductionGoal -[has_monitor_pass]-> MonitorPass edges. Same
        # best-effort idiom LanguageWorld uses for its own node/edge types.
        for src in ("ProductionGoal", "MonitorPass"):
            for tgt in ("ProductionGoal", "MonitorPass"):
                try:
                    self.s.add_production({
                        "src": {"type": src, "var": "a"},
                        "edge_type": "has_monitor_pass",
                        "tgt": {"type": tgt, "var": "b"},
                        "where": None,
                        "weight": {"type": "Lit", "value": 1.0},
                        "provenance": "self_monitor",
                    })
                except Exception:
                    pass

    # ----- grounded reverse views (mechanical reads) ----------------------

    def _surface_alternatives(self, language: str) -> dict[str, list[str]]:
        """concept -> [grounded surfaces], ALL LexEntry surfaces for the
        concept in this language (the alternatives the repair re-selects
        from). Confirmed surfaces first, then tentative; de-duplicated,
        order-stable."""
        confirmed: dict[str, list[str]] = {}
        tentative: dict[str, list[str]] = {}
        for eid in self.s.nodes("LexEntry"):
            a = self.s.node(eid)["attrs"]
            if a.get("language") != language:
                continue
            c, sfc = a.get("concept"), a.get("surface")
            if not c or not sfc:
                continue
            bucket = (confirmed if a.get("status") != "tentative"
                      else tentative)
            bucket.setdefault(c, [])
            if sfc not in bucket[c]:
                bucket[c].append(sfc)
        out: dict[str, list[str]] = {}
        for c in set(confirmed) | set(tentative):
            out[c] = list(confirmed.get(c, [])) + [
                s for s in tentative.get(c, []) if s not in confirmed.get(c, [])
            ]
        return out

    def _first_surface(self, language: str, concept: str) -> Optional[str]:
        alts = self._surface_alternatives(language).get(concept)
        return alts[0] if alts else None

    # ----- the bare initial production ------------------------------------

    def _bare_words(self, language: str,
                    surface_structure: dict[str, Any]) -> list[dict[str, Any]]:
        """The pass-0 realization: ONE phonological word per filled role, in
        the grounded grammar order, content surfaces only — NO function words.
        ``realized`` is False (and ``surface`` falls back to the concept name)
        for a concept with no grounded surface, so the loop can detect an
        UNREALIZABLE slot honestly."""
        alts = self._surface_alternatives(language)
        words: list[dict[str, Any]] = []
        for role, concept in surface_structure["ordered_slots"]:
            surface = (alts.get(concept) or [None])[0]
            words.append({
                "role": role,
                "concept": concept,
                "surface": surface if surface is not None else concept,
                "realized": surface is not None,
                "function_word": False,
                # which grounded alternative index we are using (for
                # wrong_filler re-selection).
                "alt_index": 0,
            })
        return words

    # ----- diagnosis -------------------------------------------------------

    def _diagnose(self, goal_frame: dict[str, Any],
                  recovered: dict[str, Any],
                  mood: str) -> list[dict[str, Any]]:
        """Structured, per-slot discrepancy between goal and recovered.

        Returns a list of {kind, slot, goal_value, recovered_value,
        recovered_slot} dicts — one per mismatch, localizing the error to a
        slot + kind. Kinds: slot_missing / wrong_filler / wrong_role /
        wrong_tense / extra_slot. Empty list == converged."""
        discreps: list[dict[str, Any]] = []
        content_roles = ("event", "agent", "patient", "location",
                         *preprole.FINE_ROLES)
        # Where did each goal concept actually land in the recovered frame?
        # (so a right-concept/wrong-slot is a wrong_role, not a bare missing.)
        rec_by_concept: dict[str, str] = {}
        for r, v in recovered.items():
            if r in content_roles and isinstance(v, str):
                rec_by_concept.setdefault(v, r)

        for role in content_roles:
            if role not in goal_frame:
                continue
            gv = goal_frame[role]
            rv = recovered.get(role)
            if rv is None:
                # The goal's concept may have landed in ANOTHER slot.
                landed = None
                for rc, rrole in rec_by_concept.items():
                    if isinstance(gv, str) and lw._concepts_equiv(gv, rc):
                        landed = rrole
                        break
                if landed is not None:
                    discreps.append({
                        "kind": "wrong_role", "slot": role,
                        "goal_value": gv, "recovered_value": gv,
                        "recovered_slot": landed,
                    })
                else:
                    discreps.append({
                        "kind": "slot_missing", "slot": role,
                        "goal_value": gv, "recovered_value": None,
                        "recovered_slot": None,
                    })
            elif isinstance(gv, str) and isinstance(rv, str):
                if not lw._concepts_equiv(gv, rv):
                    # Right slot, wrong concept -> wrong_filler. But if the
                    # goal's concept landed in a DIFFERENT slot too, the
                    # primary error is the role swap there; record both.
                    discreps.append({
                        "kind": "wrong_filler", "slot": role,
                        "goal_value": gv, "recovered_value": rv,
                        "recovered_slot": role,
                    })
            elif gv != rv:
                discreps.append({
                    "kind": "wrong_filler", "slot": role,
                    "goal_value": str(gv), "recovered_value": str(rv),
                    "recovered_slot": role,
                })

        # Tense (lenient: only a mismatch when both present and differ).
        if "tense" in goal_frame:
            gt, rt = goal_frame.get("tense"), recovered.get("tense")
            if rt and gt and gt != rt:
                discreps.append({
                    "kind": "wrong_tense", "slot": "tense",
                    "goal_value": str(gt), "recovered_value": str(rt),
                    "recovered_slot": "tense",
                })

        # extra_slot: a recovered content role the goal didn't ask for and
        # whose filler isn't one of the goal's concepts (a genuinely spurious
        # role, e.g. a stray patient). Reported but lower priority than the
        # localizing errors above.
        goal_concepts = {goal_frame[r] for r in content_roles
                         if r in goal_frame and isinstance(goal_frame[r], str)}
        for role in content_roles:
            if role in goal_frame:
                continue
            rv = recovered.get(role)
            if isinstance(rv, str) and not any(
                    lw._concepts_equiv(rv, gc) for gc in goal_concepts
                    if isinstance(gc, str)):
                discreps.append({
                    "kind": "extra_slot", "slot": role,
                    "goal_value": None, "recovered_value": rv,
                    "recovered_slot": role,
                })

        # Mood -> speech-act check for questions (a missing terminator-driven
        # speech act). Lowest priority; surfaced so the trace is honest.
        if mood == "interrogative" and recovered.get("speech_act") != "question":
            discreps.append({
                "kind": "wrong_feature", "slot": "speech_act",
                "goal_value": "question",
                "recovered_value": str(recovered.get("speech_act")),
                "recovered_slot": "speech_act",
            })

        return discreps

    @staticmethod
    def _priority(d: dict[str, Any]) -> int:
        """Repair-targeting priority: fix localizing errors first."""
        order = {
            "wrong_role": 0, "wrong_filler": 1, "slot_missing": 2,
            "wrong_tense": 3, "wrong_feature": 4, "extra_slot": 5,
        }
        return order.get(d["kind"], 9)

    # ----- repair (grounded alternatives) ---------------------------------

    def _repair(self, language: str, preverbal: dict[str, Any],
                words: list[dict[str, Any]], discrep: dict[str, Any],
                tried: set[str]) -> dict[str, Any]:
        """Apply ONE grounded repair for the top ``discrep``. Returns
        {applied, description, words, unrealizable, repair_key} — words is the
        new phonological-word list. ``applied`` is False when no grounded
        alternative exists (UNREALIZABLE / no-progress signal). ``repair_key``
        keys the deduplication so the same repair isn't tried twice."""
        kind = discrep["kind"]
        slot = discrep["slot"]
        fws = lp._grounded_function_words(self.world, language)

        # --- UNREALIZABLE short-circuit: the slot's content word has NO
        # grounded surface (the bare production emitted the concept name).
        # No grounded alternative exists, so no repair can help — mark it
        # UNREALIZABLE rather than chase the downstream mis-parse. (This is
        # what catches open/door honestly: the words were never grounded.)
        target_word = next((w for w in words
                            if w["role"] == slot and not w.get("function_word")),
                           None)
        if (kind in ("wrong_role", "wrong_filler", "slot_missing")
                and target_word is not None
                and not target_word.get("realized", True)):
            alts = self._surface_alternatives(language).get(
                target_word["concept"], [])
            if len(alts) <= target_word.get("alt_index", 0) + 1:
                return {"applied": False, "description":
                        f"{slot} concept {target_word['concept']!r} has NO "
                        f"grounded surface -> UNREALIZABLE",
                        "words": words, "unrealizable": True,
                        "repair_key": f"unrealizable:{slot}"}

        # --- wrong_role / slot_missing on a marked oblique role: insert the
        # grounded role-marking function word so comprehension recovers the
        # right role. The marker comes from a grounded FunctionWord whose
        # grammatical_role matches, falling back to the VerbNet-derived
        # role_preposition table (also grounded reference data, not a hand
        # fix list).
        if kind in ("wrong_role", "slot_missing") and slot in _MARKED_ROLES:
            key = f"insert_marker:{slot}"
            if key in tried:
                return {"applied": False, "description":
                        f"marker for {slot} already inserted (no progress)",
                        "words": words, "unrealizable": False,
                        "repair_key": key}
            new_words, marker_surface, attaches = self._insert_role_marker(
                language, slot, words, fws)
            if marker_surface is None:
                return {"applied": False, "description":
                        f"no grounded marker for role {slot} -> UNREALIZABLE",
                        "words": words, "unrealizable": True,
                        "repair_key": key}
            return {"applied": True, "description":
                    f"insert grounded {slot}-marker {marker_surface!r} "
                    f"({attaches})", "words": new_words,
                    "unrealizable": False, "repair_key": key}

        # --- wrong_filler: re-select the slot's surface from the grounded
        # alternatives (a different LexEntry surface for the same concept).
        if kind == "wrong_filler":
            for i, w in enumerate(words):
                if w["role"] != slot or w.get("function_word"):
                    continue
                alts = self._surface_alternatives(language).get(w["concept"], [])
                nxt = w.get("alt_index", 0) + 1
                key = f"reselect:{slot}:{nxt}"
                if nxt < len(alts) and key not in tried:
                    new_words = [dict(x) for x in words]
                    new_words[i]["surface"] = alts[nxt]
                    new_words[i]["alt_index"] = nxt
                    new_words[i]["realized"] = True
                    return {"applied": True, "description":
                            f"re-select {slot} surface "
                            f"{w['surface']!r}->{alts[nxt]!r} (grounded alt)",
                            "words": new_words, "unrealizable": False,
                            "repair_key": key}
            return {"applied": False, "description":
                    f"no alternative grounded surface for {slot} "
                    f"-> UNREALIZABLE", "words": words,
                    "unrealizable": True, "repair_key": f"reselect:{slot}"}

        # --- slot_missing where the slot was never realized (no grounded
        # surface): try an alternative surface; else UNREALIZABLE.
        if kind == "slot_missing":
            concept = discrep["goal_value"]
            alts = self._surface_alternatives(language).get(concept, [])
            key = f"realize:{slot}"
            if alts and key not in tried:
                # The slot has a grounded surface but wasn't laid out (e.g.
                # it was dropped); re-add it. Rare — production lays all
                # filled roles. Treat as UNREALIZABLE if already present.
                present = any(w["role"] == slot and not w.get("function_word")
                              for w in words)
                if not present:
                    new_words = list(words)
                    new_words.append({"role": slot, "concept": concept,
                                      "surface": alts[0], "realized": True,
                                      "function_word": False, "alt_index": 0})
                    return {"applied": True, "description":
                            f"realize missing {slot} as {alts[0]!r}",
                            "words": new_words, "unrealizable": False,
                            "repair_key": key}
            return {"applied": False, "description":
                    f"no grounded realization for {slot} ({concept}) "
                    f"-> UNREALIZABLE", "words": words,
                    "unrealizable": True, "repair_key": key}

        # --- wrong_tense: re-inflect from an alternative grounded inflected
        # surface for the event concept.
        if kind == "wrong_tense":
            for i, w in enumerate(words):
                if w["role"] != "event" or w.get("function_word"):
                    continue
                alts = self._surface_alternatives(language).get(w["concept"], [])
                nxt = w.get("alt_index", 0) + 1
                key = f"reinflect:{nxt}"
                if nxt < len(alts) and key not in tried:
                    new_words = [dict(x) for x in words]
                    new_words[i]["surface"] = alts[nxt]
                    new_words[i]["alt_index"] = nxt
                    return {"applied": True, "description":
                            f"re-inflect event {w['surface']!r}->{alts[nxt]!r}"
                            " (grounded alt form)", "words": new_words,
                            "unrealizable": False, "repair_key": key}
            return {"applied": False, "description":
                    "no alternative grounded inflected surface -> UNREALIZABLE",
                    "words": words, "unrealizable": True,
                    "repair_key": "reinflect"}

        # --- extra_slot / wrong_feature: no grounded repair (these are
        # comprehension-side artefacts, not production gaps). Report, no-op.
        return {"applied": False, "description":
                f"no grounded repair for {kind} on {slot}", "words": words,
                "unrealizable": False, "repair_key": f"{kind}:{slot}"}

    def _insert_role_marker(self, language: str, role: str,
                            words: list[dict[str, Any]],
                            fws: list[dict[str, Any]]
                            ) -> tuple[list[dict[str, Any]], Optional[str], str]:
        """Insert the grounded role-marking function word around the content
        word that fills ``role``. en/es: a preposition that PRECEDES; ja/zh:
        a case particle that FOLLOWS. The marker surface comes from a grounded
        FunctionWord whose grammatical_role == role, else the VerbNet-derived
        role_preposition table. Returns (new_words, marker_surface, attaches);
        marker_surface is None when no grounded marker exists."""
        # Find the content word for this role.
        idx = next((i for i, w in enumerate(words)
                    if w["role"] == role and not w.get("function_word")), None)
        if idx is None:
            return words, None, ""

        if language in ("ja", "zh"):
            part = lp._pick_function_word(fws, function="particle", role=role)
            if part is not None and part.get("attaches") == "follows":
                surface, attaches = part["surface"], "follows"
            else:
                surface = preprole.role_preposition(role, language)
                attaches = "follows"
            if not surface:
                return words, None, ""
            marker = {"role": f"fn:particle", "concept": role,
                      "surface": surface, "realized": True,
                      "function_word": True}
            new_words = words[:idx + 1] + [marker] + words[idx + 1:]
            return new_words, surface, attaches

        # en/es: preposition PRECEDES.
        prep = lp._pick_function_word(fws, function="preposition", role=role)
        if prep is not None and prep.get("attaches") == "precedes":
            surface, attaches = prep["surface"], "precedes"
        else:
            surface = preprole.role_preposition(role, language)
            attaches = "precedes"
        if not surface:
            return words, None, ""
        marker = {"role": f"fn:preposition", "concept": role,
                  "surface": surface, "realized": True, "function_word": True}
        new_words = words[:idx] + [marker] + words[idx:]
        return new_words, surface, attaches

    # ----- the iterated loop ----------------------------------------------

    def produce_and_repair(self, language: str, goal: dict[str, Any],
                           max_passes: Optional[int] = None) -> dict[str, Any]:
        """The iterated produce -> monitor -> diagnose -> repair loop.

        Returns {utterance, passes, converged, unrealizable, residual, trace,
        goal_node, max_passes}. ``trace`` is the per-pass record (also written
        as MonitorPass graph nodes wired to a Goal node)."""
        preverbal = self.prod.conceptual_preparation(goal)
        surface_structure = self.prod.grammatical_encoding(language, preverbal)
        mood = preverbal["mood"]
        goal_frame = preverbal["frame"]

        # max_passes scales with difficulty: content slots + 1.
        n_slots = len([1 for r in surface_structure["ordered_slots"]])
        if max_passes is None:
            max_passes = n_slots + 1

        # A Goal node anchors the trace.
        goal_node = self._add_goal_node(language, goal, mood, max_passes)

        words = self._bare_words(language, surface_structure)
        tried: set[str] = set()
        trace: list[dict[str, Any]] = []
        converged = False
        unrealizable = False
        prev_discrep_count: Optional[int] = None
        residual: list[dict[str, Any]] = []

        pass_index = 0
        while True:
            articulated = self.prod.articulation(language, mood, {"words": words})
            utterance = articulated["overt_speech"]
            recovered = self.prod._comprehend(language, utterance)
            discreps = self._diagnose(goal_frame, recovered, mood)
            residual = discreps

            if not discreps:
                converged = True
                self._record_pass(goal_node, pass_index, utterance, recovered,
                                  [], None, "converged")
                trace.append(self._pass_summary(pass_index, utterance,
                             recovered, [], None, "converged"))
                break

            # Pick the top (highest-priority) discrepancy to repair.
            discreps_sorted = sorted(discreps, key=self._priority)
            top = discreps_sorted[0]

            # Stop conditions BEFORE repairing: max passes reached.
            if pass_index + 1 >= max_passes:
                self._record_pass(goal_node, pass_index, utterance, recovered,
                                  discreps, None, "max_passes")
                trace.append(self._pass_summary(pass_index, utterance,
                             recovered, discreps, None, "max_passes"))
                break

            repair = self._repair(language, preverbal, words, top, tried)
            outcome = ("repaired" if repair["applied"]
                       else ("unrealizable" if repair["unrealizable"]
                             else "no_repair"))
            self._record_pass(goal_node, pass_index, utterance, recovered,
                              discreps, repair, outcome)
            trace.append(self._pass_summary(pass_index, utterance, recovered,
                         discreps, repair, outcome))

            if not repair["applied"]:
                # No grounded repair available -> deadlock, stop honestly.
                unrealizable = repair["unrealizable"]
                break

            tried.add(repair["repair_key"])
            words = repair["words"]

            # No-progress guard: if the discrepancy set didn't shrink after a
            # repair on the SAME slot last time, we'd loop; the tried-set on
            # repair_key already prevents re-applying an identical repair, and
            # max_passes bounds the rest. Track count for the trace.
            prev_discrep_count = len(discreps)
            pass_index += 1

        return {
            "language": language,
            "goal": goal,
            "utterance": utterance,
            "passes": pass_index + 1,
            "converged": converged,
            "unrealizable": unrealizable,
            "residual": residual,
            "trace": trace,
            "goal_node": goal_node,
            "max_passes": max_passes,
        }

    # ----- trace as graph data --------------------------------------------

    def _add_goal_node(self, language: str, goal: dict[str, Any],
                       mood: str, max_passes: int) -> Any:
        return self.s.add_node("ProductionGoal", {
            "language": language,
            "goal_json": json.dumps(goal, ensure_ascii=False),
            "mood": mood,
            "max_passes": int(max_passes),
        })

    def _record_pass(self, goal_node: Any, pass_index: int, utterance: str,
                     recovered: dict[str, Any],
                     discreps: list[dict[str, Any]],
                     repair: Optional[dict[str, Any]], outcome: str) -> Any:
        """Write a MonitorPass node (the pass's self-correction record) wired
        to the goal via has_monitor_pass — graph data, inspectable."""
        attrs = {
            "pass_index": int(pass_index),
            "utterance": utterance,
            "recovered_frame_summary": json.dumps(
                {k: v for k, v in recovered.items()}, ensure_ascii=False),
            "discrepancy": json.dumps(discreps, ensure_ascii=False),
            "repair_applied": (repair["description"] if repair else ""),
            "outcome": outcome,
        }
        nid = self.s.add_node("MonitorPass", attrs)
        try:
            self.s.add_edge(goal_node, "has_monitor_pass", nid, None)
        except Exception:
            pass
        return nid

    @staticmethod
    def _pass_summary(pass_index: int, utterance: str,
                      recovered: dict[str, Any],
                      discreps: list[dict[str, Any]],
                      repair: Optional[dict[str, Any]],
                      outcome: str) -> dict[str, Any]:
        return {
            "pass_index": pass_index,
            "utterance": utterance,
            "recovered_frame": dict(recovered),
            "discrepancy": [dict(d) for d in discreps],
            "repair": (repair["description"] if repair else None),
            "outcome": outcome,
        }


__all__ = ["SelfMonitorLoop"]
