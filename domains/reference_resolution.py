"""reference_resolution — cross-utterance REFERENCE RESOLUTION for the
gamma-substrate conversation, built to the taught ``reference_resolution``
model (seeds/reference_resolution.json).

Before this, ConversationWorld was AMNESIAC about entities across turns: a
pronoun ("it" / "she" / "him") or a definite re-mention ("the cat") in a later
turn bound to nothing, so the question silently lost its subject. This module
adds the cross-utterance STATE the conversation lacked — a
``discourse_referent_store`` updated every turn — and a resolution procedure
that reads it.

ARCHITECTURE (CLAUDE.md). The store + centering state are GRAPH DATA:

  * ``DiscourseReferent`` nodes — one per entity in the conversation, carrying
    ``concept`` + ``category``/``animacy`` (grounded from the Concept node's
    ``category`` attr, seeds/conceptual_categories.json), ``cognitive_status``
    (givenness_hierarchy), ``recency`` (turn last mentioned), ``last_role``
    (grammatical role of last mention), and ``mentions`` (frequency).
  * ``CenteringState`` nodes — one per turn, carrying the forward_looking_centers
    (Cf, ranked by cf_ranking), the backward_looking_center (Cb), the
    preferred_center (Cp), and the centering_transition.

Resolution (``reference_resolution_procedure``) is a graph-driven READ over
those nodes: form_status_licensing -> agreement_filter -> rank-survivors
(centering_rule_1 favors Cb, else salience_factors) -> bind. No ML, no Rust.

This file is a world-side helper: it MUTATES graph state (adds/updates
DiscourseReferent + CenteringState nodes) and READS it back to resolve. The
"decisions" it makes are the documented procedure of the taught model, applied
mechanically — the same status as conversation_world's order-N glue
(domains/order_n_reasoning.py): a graph walk implementing a named operator.

HONEST COVERAGE (see scripts/reference_resolution_test.py):
  * GROUNDED: animacy/number agreement from the Concept ``category`` attr
    (person/animal/object); recency + grammatical-role salience; Cb/centering.
  * COARSE: gender (he vs she). There is NO grounded gender data on Mary/John
    (only category=person), so he/she both filter to PERSON; when two persons
    are in focus they are disambiguated by salience/Cb, NOT by gender. Reported
    honestly per binding (the resolving mechanism is named).
  * NOT BUILT: bridging_anaphora + deixis are seed scaffolding only (they need a
    relation model / an utterance-context model the store does not supply).
"""
from __future__ import annotations

import re
from typing import Any, Optional

try:
    from domains import interrogative_reference as _ireg
    _WH = set(_ireg.ALL_PLACEHOLDERS)
except Exception:  # pragma: no cover
    _WH = {"?WHO", "?WHAT", "?WHERE", "?WHEN", "?WHY", "?HOW"}


# ---------------------------------------------------------------------------
# cf_ranking — the salience order on forward_looking_centers (the taught
# concept). SUBJECT > OBJECT(S) > OTHER, read off the frame's grammatical
# roles: agent (subject) > patient (object) > recipient > location/other.
# ---------------------------------------------------------------------------
_CF_RANK = {
    "agent": 0, "patient": 1, "recipient": 2, "beneficiary": 3,
    "instrument": 4, "source": 5, "topic": 6, "standard": 7,
    "location": 8, "time": 9, "cause": 10, "manner": 11,
}
# The frame slots that name a discourse entity (the event is not an entity).
_ENTITY_SLOTS = tuple(_CF_RANK.keys())


# ---------------------------------------------------------------------------
# Referring-expression forms (closed class) + their form_status_licensing
# lower bound (the taught givenness_hierarchy). A finite list, like the
# interrogative proforms / do-support auxiliaries.
# ---------------------------------------------------------------------------
# Pronoun surface -> (number, person_constraint). person_constraint:
#   "person"     -> referent must be animate-person (he/she/him/her)
#   "non_person" -> referent must be non-person (it: animal/object)
#   "any_animate"-> any (they/them)
# All pronouns license an IN_FOCUS referent (form_status_licensing).
_PRONOUNS = {
    "it":   {"number": "singular", "agree": "non_person", "case": "any"},
    "he":   {"number": "singular", "agree": "person", "case": "subject"},
    "she":  {"number": "singular", "agree": "person", "case": "subject"},
    "him":  {"number": "singular", "agree": "person", "case": "object"},
    "her":  {"number": "singular", "agree": "person", "case": "object"},
    "they": {"number": "plural", "agree": "any", "case": "subject"},
    "them": {"number": "plural", "agree": "any", "case": "object"},
}
_SUBJECT_PRONOUNS = {p for p, v in _PRONOUNS.items() if v["case"] == "subject"}
_OBJECT_PRONOUNS = {p for p, v in _PRONOUNS.items() if v["case"] == "object"}

# FIRST / SECOND PERSON are DEIXIS, not anaphora: 'I'/'me'/'my' point at whoever is
# SPEAKING, 'you'/'thou'/'thee'/'thy' at whoever is ADDRESSED — the discourse DEICTIC
# CENTRE, not a salient antecedent in the entity pool. `person` = first -> speaker,
# second -> addressee. Kept SEPARATE from `_PRONOUNS` (the third-person SALIENCE
# table) on purpose: the anaphora paths and their derived `_SUBJECT/_OBJECT_PRONOUNS`
# sets stay byte-identical, and the deictic resolver consults THIS table BEFORE the
# salience Argmax so a first-person form never competes in the SmEntity resonance
# pool (which is exactly how a self-epithet 'unlucky wretch that I am' mis-spawned a
# 'wretch' entity). A closed-class table, the same grandfathered status as _PRONOUNS.
_DEIXIS = {
    "i":      {"person": "first",  "number": "singular"},
    "me":     {"person": "first",  "number": "singular"},
    "my":     {"person": "first",  "number": "singular"},
    "mine":   {"person": "first",  "number": "singular"},
    "myself": {"person": "first",  "number": "singular"},
    "we":     {"person": "first",  "number": "plural"},
    "us":     {"person": "first",  "number": "plural"},
    "our":    {"person": "first",  "number": "plural"},
    "ours":   {"person": "first",  "number": "plural"},
    "ourselves": {"person": "first", "number": "plural"},
    "you":    {"person": "second", "number": "any"},
    "your":   {"person": "second", "number": "any"},
    "yours":  {"person": "second", "number": "any"},
    "yourself": {"person": "second", "number": "singular"},
    "thou":   {"person": "second", "number": "singular"},
    "thee":   {"person": "second", "number": "singular"},
    "thy":    {"person": "second", "number": "singular"},
    "thine":  {"person": "second", "number": "singular"},
    "thyself": {"person": "second", "number": "singular"},
}

# Givenness lower bounds.
_STATUS_RANK = {
    "in_focus": 0, "activated": 1, "familiar": 2,
    "uniquely_identifiable": 3, "referential": 4, "type_identifiable": 5,
}


# ---------------------------------------------------------------------------
# discourse_referent_store — graph-resident state.
# ---------------------------------------------------------------------------

class DiscourseStore:
    """The discourse_referent_store as graph data, with the resolution
    procedure + centering update. One per conversation; keyed by concept so a
    re-mention binds to the SAME DiscourseReferent node.

    Owns no agent reasoning beyond the taught procedure. Every datum is a node
    attr; resolution is a read over those attrs."""

    def __init__(self, substrate, world):
        self.s = substrate
        self.world = world
        # concept_name -> DiscourseReferent NodeID (mirror of the graph; the
        # graph is the source of truth — rebuilt on construction).
        self._ref_nodes: dict[str, Any] = {}
        self._turn_index = 0
        # The previous turn's Cf (list of concept names, ranked) for Cb compute.
        self._prev_cf: list[str] = []
        # Open productions so the Rust grammar admits the edges.
        self._open_productions()
        self._reload_from_graph()

    # ----- productions / cache --------------------------------------------

    def _open_productions(self) -> None:
        node_types = ("DiscourseReferent", "CenteringState", "Concept",
                      "DiscourseReferentStore")
        edge_types = ("refers_concept", "cf_member", "cb", "cp",
                      "has_referent", "realized")
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
                            "provenance": "reference_resolution",
                        })
                    except Exception:
                        pass
        try:
            self.s.declare_attr_index("DiscourseReferent", "concept")
        except Exception:
            pass

    def _reload_from_graph(self) -> None:
        for rid in self.s.nodes("DiscourseReferent"):
            c = self.s.node(rid)["attrs"].get("concept")
            if isinstance(c, str):
                self._ref_nodes[c] = rid

    # ----- animacy / agreement — GROUNDED from the Concept category -------

    def _category(self, concept: str) -> Optional[str]:
        """The grounded category (person/animal/object/event) of a concept,
        read off its Concept node's ``category`` attr — the same graph data
        (seeds/conceptual_categories.json) the LanguageWorld inferer reads.
        None when the concept has no grounded category."""
        cid = self.world._concept_nodes.get(concept)
        if cid is None:
            for c in self.s.nodes("Concept"):
                a = self.s.node(c)["attrs"]
                if a.get("name") == concept:
                    cid = c
                    break
        if cid is None:
            return None
        return self.s.node(cid)["attrs"].get("category")

    @staticmethod
    def _animacy_of(category: Optional[str]) -> str:
        """animate / inanimate from the grounded category. person + animal are
        animate; object is inanimate; unknown -> unknown."""
        if category in ("person", "animal"):
            return "animate"
        if category == "object":
            return "inanimate"
        return "unknown"

    # ----- store update — introduce / promote / decay ---------------------

    def _get_or_create_referent(self, concept: str) -> Any:
        rid = self._ref_nodes.get(concept)
        if rid is not None:
            return rid
        cat = self._category(concept)
        rid = self.s.add_node("DiscourseReferent", {
            "concept": concept,
            "category": cat if isinstance(cat, str) else "unknown",
            "animacy": self._animacy_of(cat),
            "number": "singular",          # coarse default (no plural marking yet)
            "cognitive_status": "uniquely_identifiable",
            "recency": -1,
            "last_role": "",
            "mentions": 0,
        })
        cid = self.world._get_or_create_concept(concept)
        try:
            self.s.add_edge(rid, "refers_concept", cid, None)
        except Exception:
            pass
        self._ref_nodes[concept] = rid
        return rid

    def update_from_frame(self, frame: dict[str, Any]) -> dict[str, str]:
        """Update the store from a (resolved) comprehended frame: introduce new
        referents, promote mentioned ones to in_focus (set recency + role +
        bump frequency), decay un-mentioned in_focus referents to activated.

        Returns {concept: grammatical_role} for the entities realized this turn
        (used to compute the centering state)."""
        self._turn_index += 1
        realized: dict[str, str] = {}
        for slot in _ENTITY_SLOTS:
            v = frame.get(slot)
            if isinstance(v, str) and v and v not in _WH:
                realized[v] = slot

        mentioned = set(realized)
        # Decay: any in_focus referent NOT mentioned this turn drops to
        # activated (the taught decay; in_focus -> activated over turns).
        for concept, rid in self._ref_nodes.items():
            if concept in mentioned:
                continue
            a = self.s.node(rid)["attrs"]
            if a.get("cognitive_status") == "in_focus":
                try:
                    self.s.set_attr(rid, "cognitive_status", "activated")
                except Exception:
                    pass

        # Introduce / promote mentioned referents.
        for concept, role in realized.items():
            rid = self._get_or_create_referent(concept)
            a = self.s.node(rid)["attrs"]
            try:
                self.s.set_attr(rid, "cognitive_status", "in_focus")
                self.s.set_attr(rid, "recency", self._turn_index)
                self.s.set_attr(rid, "last_role", role)
                self.s.set_attr(rid, "mentions",
                                int(a.get("mentions", 0) or 0) + 1)
            except Exception:
                pass
        return realized

    # ----- centering state — Cf / Cb / Cp / transition --------------------

    def update_centering(self, realized: dict[str, str]) -> dict[str, Any]:
        """Compute + store the per-turn CenteringState (the taught centering
        concepts):

          Cf  = entities realized this turn, ranked by cf_ranking (subject >
                object > other).
          Cp  = top of Cf (preferred_center; predicted next Cb).
          Cb  = the highest-ranked element of the PREVIOUS turn's Cf realized
                again this turn (backward_looking_center).
          transition = CONTINUE (Cb == prev Cb and Cb == Cp) / RETAIN (Cb same
                but != Cp) / SHIFT (Cb changed) / NONE (no Cb).

        Returns the centering dict + records a CenteringState node."""
        # Cf ranked.
        cf = sorted(realized.keys(),
                    key=lambda c: _CF_RANK.get(realized[c], 99))
        cp = cf[0] if cf else None
        # Cb = highest-ranked prev-Cf entity realized again now.
        cb = None
        for c in self._prev_cf:
            if c in realized:
                cb = c
                break
        prev_cb = getattr(self, "_prev_cb", None)
        if cb is None:
            transition = "none"
        elif cb != prev_cb:
            transition = "shift"
        elif cb == cp:
            transition = "continue"
        else:
            transition = "retain"

        node = self.s.add_node("CenteringState", {
            "turn": self._turn_index,
            "cf": ", ".join(cf),
            "cb": cb or "",
            "cp": cp or "",
            "transition": transition,
        })
        for c in cf:
            rid = self._ref_nodes.get(c)
            if rid is not None:
                try:
                    self.s.add_edge(node, "cf_member", rid,
                                    {"rank": _CF_RANK.get(realized[c], 99)})
                except Exception:
                    pass
        if cb and self._ref_nodes.get(cb) is not None:
            try:
                self.s.add_edge(node, "cb", self._ref_nodes[cb], None)
            except Exception:
                pass

        self._prev_cf = cf
        self._prev_cb = cb
        return {"cf": cf, "cb": cb, "cp": cp, "transition": transition,
                "node": node}

    # ----- the resolution procedure (the taught pipeline) -----------------

    def _candidates(self) -> list[Any]:
        return list(self._ref_nodes.values())

    def _agrees(self, ref_attrs: dict[str, Any],
                spec: dict[str, str]) -> tuple[bool, str]:
        """agreement_filter: does this referent agree with the pronoun's
        number + person/animacy? Returns (ok, reason). GROUNDED on animacy
        (from category); number coarse; gender NOT grounded (he/she both ->
        person)."""
        animacy = ref_attrs.get("animacy", "unknown")
        category = ref_attrs.get("category", "unknown")
        number = ref_attrs.get("number", "singular")
        # number agreement (coarse: all referents singular for now).
        if spec["number"] == "plural" and number != "plural":
            return False, "number mismatch (singular referent, plural pronoun)"
        if spec["number"] == "singular" and number == "plural":
            return False, "number mismatch (plural referent, singular pronoun)"
        # person / animacy agreement (grounded on category).
        if spec["agree"] == "person":
            if category == "person":
                return True, "agree:person"
            if category == "unknown":
                return True, "agree:person? (no grounded category)"
            return False, f"person mismatch (referent category={category})"
        if spec["agree"] == "non_person":
            # 'it' -> non-person (animal / object), reject a person.
            if category == "person":
                return False, "person mismatch ('it' rejects a person)"
            return True, f"agree:non_person (category={category})"
        return True, "agree:any"

    def reference_resolution_procedure(
            self, surface: str, turn: int,
            form: Optional[dict[str, str]] = None) -> dict[str, Any]:
        """Bind a referring expression to a DiscourseReferent — the taught
        reference_resolution_procedure:

          (1) form_status_licensing: a pronoun requires an IN_FOCUS referent;
              a definite "the N" requires UNIQUELY_IDENTIFIABLE (already
              introduced) — handled by resolve_definite.
          (2) agreement_filter: prune by number/person/animacy (grounded).
          (3) rank survivors: a bare pronoun favors the Cb (centering_rule_1);
              else by salience_factors (recency + cf_ranking via last_role).
          (4) bind -> return the referent's concept; promote it to in_focus.

        Returns a trace dict: {resolved, concept, rule, candidates:[...],
        reason}. resolved=False with reason when nothing agrees (HONEST: we do
        NOT bind to a non-agreeing entity to fake success)."""
        spec = form or _PRONOUNS.get(surface.lower())
        if spec is None:
            return {"resolved": False, "surface": surface,
                    "reason": f"'{surface}' is not a known pronoun form",
                    "candidates": []}

        cand_trace: list[dict[str, Any]] = []
        survivors: list[tuple[Any, dict[str, Any]]] = []
        for rid in self._candidates():
            a = self.s.node(rid)["attrs"]
            status = a.get("cognitive_status", "uniquely_identifiable")
            # (1) form_status_licensing: pronoun -> in_focus lower bound.
            licensed = _STATUS_RANK.get(status, 9) <= _STATUS_RANK["in_focus"]
            ok, reason = self._agrees(a, spec)
            entry = {
                "concept": a.get("concept"),
                "status": status,
                "category": a.get("category"),
                "recency": a.get("recency"),
                "last_role": a.get("last_role"),
                "licensed_in_focus": licensed,
                "agreement": reason,
            }
            cand_trace.append(entry)
            if licensed and ok:
                survivors.append((rid, a))

        if not survivors:
            return {"resolved": False, "surface": surface,
                    "reason": ("no in-focus referent agrees with "
                               f"'{surface}' ({spec['agree']})"),
                    "candidates": cand_trace}

        # (3) rank survivors.
        cb = getattr(self, "_prev_cb", None)
        rule = None
        if len(survivors) == 1:
            chosen = survivors[0]
            rule = "agreement (sole agreeing in-focus referent)"
        else:
            # centering_rule_1: a bare pronoun favors the Cb.
            cb_survivor = next((s for s in survivors
                                if s[1].get("concept") == cb), None)
            if cb_survivor is not None:
                chosen = cb_survivor
                rule = f"centering_rule_1 (Cb = {cb})"
            else:
                # salience_factors: recency desc, then cf_ranking (last_role).
                chosen = max(
                    survivors,
                    key=lambda s: (
                        int(s[1].get("recency", -1) or -1),
                        -_CF_RANK.get(s[1].get("last_role", ""), 99),
                        int(s[1].get("mentions", 0) or 0)))
                rule = "salience (recency + role; gender NOT grounded)"

        rid, a = chosen
        concept = a.get("concept")
        # (4) bind -> promote.
        try:
            self.s.set_attr(rid, "cognitive_status", "in_focus")
        except Exception:
            pass
        return {"resolved": True, "surface": surface, "concept": concept,
                "rule": rule, "candidates": cand_trace,
                "agreement": self._agrees(a, spec)[1]}

    def resolve_definite(self, head_concept: str,
                         turn: int) -> dict[str, Any]:
        """Resolve a definite "the N" -> the existing DiscourseReferent for N.
        form_status_licensing: "the N" requires UNIQUELY_IDENTIFIABLE — i.e.
        the entity was already introduced (a DiscourseReferent exists). HONEST:
        if N was never introduced, the definite is unresolved (a first-mention
        definite / bridging case we do not handle)."""
        rid = self._ref_nodes.get(head_concept)
        if rid is None:
            return {"resolved": False, "surface": f"the {head_concept}",
                    "reason": (f"'the {head_concept}' names an entity never "
                               "introduced (not uniquely_identifiable)"),
                    "candidates": []}
        a = self.s.node(rid)["attrs"]
        try:
            self.s.set_attr(rid, "cognitive_status", "in_focus")
        except Exception:
            pass
        return {"resolved": True, "surface": f"the {head_concept}",
                "concept": head_concept,
                "rule": "form_status_licensing (the N -> uniquely_identifiable)",
                "candidates": [{"concept": head_concept,
                                "status": a.get("cognitive_status"),
                                "category": a.get("category")}]}

    # ----- inspection ------------------------------------------------------

    def snapshot(self) -> list[dict[str, Any]]:
        """The discourse_referent_store as a readable list (for the transcript):
        each referent's concept + status + recency + role + animacy."""
        out = []
        for rid in self._ref_nodes.values():
            a = self.s.node(rid)["attrs"]
            out.append({
                "concept": a.get("concept"),
                "status": a.get("cognitive_status"),
                "recency": a.get("recency"),
                "role": a.get("last_role"),
                "animacy": a.get("animacy"),
                "category": a.get("category"),
                "mentions": a.get("mentions"),
            })
        out.sort(key=lambda d: (-(d["recency"] or -1)))
        return out


# ---------------------------------------------------------------------------
# Surface detection of referring expressions — the I/O-boundary classifier
# CLAUDE.md permits (pure string + position; no graph decisions). It only
# decides WHICH SURFACE TOKEN is a referring expression and WHICH SLOT it
# would fill; the resolution decision itself is the store's procedure.
# ---------------------------------------------------------------------------

def detect_referring_expressions(text: str, lexicon: dict[str, str],
                                 language: str = "en") -> list[dict[str, Any]]:
    """Find pronoun + definite referring expressions in the surface, with the
    grammatical SLOT each would fill (subject pronoun -> agent; object pronoun
    -> patient). English only (honest — pronoun case/morphology is en data).

    Returns a list of {kind, surface, slot, head?} dicts in surface order. The
    slot is a surface-position guess: a subject pronoun (he/she/they) or the
    first pronoun before the verb -> agent; an object pronoun (him/her/them) or
    a pronoun after the verb -> patient; the copula-locative "where is it" ->
    agent (the entity whose location is queried)."""
    if language != "en":
        return []
    toks = [t.lower() for t in re.findall(r"[A-Za-z]+", text)]
    out: list[dict[str, Any]] = []
    n = len(toks)
    # Locate a verb position (a content word that is in the lexicon AND looks
    # like a predicate is hard here; use a coarse cue: the first known content
    # word that is not a pronoun/determiner). Falls back to position.
    # COPULA-LOCATIVE probe: "where is/are PRON" (or "where is the N") queries
    # the LOCATION of an entity that is the copula SUBJECT -> that entity fills
    # the agent slot (so it matches a stored fact's agent). Detect a leading
    # where + a copula so the case-ambiguous 'it' routes to agent, not patient.
    _copula = {"is", "are", "was", "were", "be"}
    where_copula = (len(toks) >= 2 and toks[0] in ("where",)
                    and any(t in _copula for t in toks[1:3]))
    for i, tok in enumerate(toks):
        if tok in _PRONOUNS:
            case = _PRONOUNS[tok]["case"]
            if case == "subject":
                slot = "agent"
            elif case == "object":
                slot = "patient"
            else:
                # 'it' / case-ambiguous. In a copula-locative ("where is it")
                # the entity is the copula SUBJECT -> agent. Otherwise subject
                # if no preceding verb, else object.
                if where_copula:
                    slot = "agent"
                else:
                    slot = "patient" if _after_verb(toks, i, lexicon) else "agent"
            out.append({"kind": "pronoun", "surface": tok, "slot": slot,
                        "position": i})
        elif tok == "the" and i + 1 < n:
            head = toks[i + 1]
            concept = lexicon.get(head) or _lemma_lookup(head, lexicon)
            if concept is not None:
                # subject vs object by position: a definite before the verb is
                # the subject (agent); after, the object (patient).
                slot = "patient" if _after_verb(toks, i + 1, lexicon) else "agent"
                out.append({"kind": "definite", "surface": f"the {head}",
                            "head": concept, "slot": slot, "position": i})
    return out


def _lemma_lookup(surface: str, lexicon: dict[str, str]) -> Optional[str]:
    for cand in (surface, surface.rstrip("s"), surface + "s"):
        if cand in lexicon:
            return lexicon[cand]
    return None


def _after_verb(toks: list[str], pos: int, lexicon: dict[str, str]) -> bool:
    """Coarse: is there a content verb-ish token BEFORE this position? Used to
    guess subject (no preceding verb) vs object (a preceding verb). The verb
    cue is a known content word ending in a verb inflection, or simply any
    known content word before pos that is not a determiner/pronoun. Surface
    heuristic only."""
    for j in range(pos):
        t = toks[j]
        if t in _PRONOUNS or t in ("the", "a", "an"):
            continue
        # a content word before pos that is not the same noun -> treat as a
        # potential verb boundary. Cheap; good enough for the demo surfaces.
        if t in lexicon or t.endswith(("s", "ed", "es")):
            return True
    return False


__all__ = ["DiscourseStore", "detect_referring_expressions"]
