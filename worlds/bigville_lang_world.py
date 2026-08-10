"""BigvilleLangWorld -- the 245000 emergent political drama with SYNTACTICALLY
COMPOSED utterances (block 246000).

REUSES block 245000's `BigvilleDramaWorld` VERBATIM (that file is UNTOUCHED) so the
drama's graph-state spine -- John's held `chosen_burn` (the spite Argmax), his public
FACE (`bd_john_public_face`), Mary's minted `InferredDisposition`/`DramaGoal`/
`DramaClaim`, and the villagers' `backs_mary` credibility rule -- is IDENTICAL. The
ONLY change is that the utterances are now COMPOSED by the block-244000 syntax
faculty from a structured Intent (predicate + agent/patient roles), and the
observation COUNTS that feed the unchanged credibility rule are DERIVED by
COMPREHENDING those composed utterances -- not read off `stated`/`burn` directly, and
not looked up from a canned-string table.

ARCHITECTURE RULE. This is a WORLD ADAPTER. Composition/comprehension is the language
faculty's Merge RULES on the Rust engine (`domains/drama_syntax`, reusing
`domains/language`); every DECISION remains a 245 seed rule (`ss_choose_burn`,
`bd_john_public_face`, `bd_mary_infers`/`_forms_goal`/`_claims`, `bd_villager_backs`).
The adapter only COMPOSES surfaces from held graph state and DERIVES counts by a
MECHANICAL read of the comprehended structured Intent. No graph_rewrite.run / gr.run /
_match / _apply / make_rule; every conditional here is over WORLD state, mechanical.
NO Python string lookup table of utterance text -- the content comes from the faculty.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from domains import drama_syntax as _ds                       # noqa: E402
from worlds.bigville_drama_world import BigvilleDramaWorld     # noqa: E402

# The drama's fixed cast names (the leaves the composed utterances bind).
JOHN, MARY, VILLAGE = "John", "Mary", "Bigville"


class BigvilleLangWorld(BigvilleDramaWorld):
    """The 245 drama, its utterances COMPOSED via the 244 syntax faculty. Only
    `step()` changes: it composes John's public/held surfaces and Mary's claim from
    graph state, then DERIVES the observation counts by comprehending them."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.composed = []   # per-tick glass-box: composed surfaces + comprehended roles

    # ---- composition helpers (surfaces from held graph state) --------------
    def _compose_public(self, stated, burn):
        """John's PUBLIC utterance clauses, COMPOSED from his graph decision. Under
        deception he presents the benevolent DARVO face (serve + accuse Mary); with
        the split collapsed his public face reveals the harmful act (undermine)."""
        if stated == 1:
            return [_ds.compose("serve", JOHN, VILLAGE),
                    _ds.compose("accuse", JOHN, MARY)]
        return [_ds.compose("undermine", JOHN, MARY)]

    def _compose_held(self, burn):
        """John's HELD private intent, COMPOSED: undermine Mary when he schemes,
        else serve Bigville."""
        return (_ds.compose("undermine", JOHN, MARY) if burn == 1
                else _ds.compose("serve", JOHN, VILLAGE))

    def _compose_mary_claim(self):
        """Mary's standing CLAIM about John, COMPOSED: John undermines the village."""
        return _ds.compose("undermine", JOHN, VILLAGE)

    # ---- the step: identical phases to 245, counts via comprehension -------
    def step(self):
        self.tick += 1
        # PHASE A: John decides + states his public face, in-graph (245 rules).
        self.inner.run_rules()
        burn = max(0, int(self.s.node(self.jdec)["attrs"]["chosen_burn"]))
        stated = max(0, int(self.s.node(self.jdec)["attrs"]["stated_benevolent"]))

        # COMPOSE the surfaces from graph state (no lookup table).
        public_clauses = self._compose_public(stated, burn)
        held_surface = self._compose_held(burn)
        public_text = " ; ".join(public_clauses)

        # DERIVE stance by COMPREHENDING the composed public utterance (the language
        # is load-bearing: the count comes from who-does-what the receiver parses).
        benevolent_face = any(_ds.names_benevolence_by(c, JOHN) for c in public_clauses)
        hostile_face = any(_ds.names_harm_by(c, JOHN) for c in public_clauses)
        held_is_harm = _ds.names_harm_by(held_surface, JOHN)
        deceptive = bool(benevolent_face and held_is_harm)

        # Materialise the 245 readable PublicUtterance node (numeric gap ledger) ...
        un = self.s.add_node("PublicUtterance", {
            "by": "John", "tick": float(self.tick),
            "stated_benevolent": float(stated), "held_hostile": float(burn),
            "deceptive": 1.0 if deceptive else 0.0})
        self.inner.add_edge_unchecked(self.john, "spoke", un)
        self.utterances.append(un)
        # ... and a ComposedUtterance node carrying the LINGUISTIC surface (glass-box).
        cu = self.s.add_node("ComposedUtterance", {
            "by": "John", "tick": float(self.tick),
            "public_text": public_text, "held_text": held_surface,
            "public_predicate": (_ds.parse(public_clauses[0]) or {}).get("predicate") or "",
            "public_agent": (_ds.parse(public_clauses[0]) or {}).get("agent") or "",
            "public_patient": (_ds.parse(public_clauses[0]) or {}).get("patient") or "",
            "held_predicate": (_ds.parse(held_surface) or {}).get("predicate") or "",
            "deceptive": 1.0 if deceptive else 0.0})
        self.inner.add_edge_unchecked(self.john, "spoke_composed", cu)

        # PHASE B (mechanical): accumulate what each observer SAW / HEARD.
        # Mary's evidence about John's harmfulness (his ACTIONS -> a count -> ratio;
        # ToM decodes behaviour, unchanged from 245).
        n_obs = int(self.s.node(self.tp)["attrs"]["n_obs"]) + 1
        n_harm = int(self.s.node(self.tp)["attrs"]["n_harm"]) + burn
        rate = (100 * n_harm) // max(n_obs, 1)
        self.s.set_attr(self.tp, "n_obs", float(n_obs))
        self.s.set_attr(self.tp, "n_harm", float(n_harm))
        self.s.set_attr(self.tp, "observed_harm_rate", float(rate))
        for g in self.gens:
            self.s.set_attr(g, "observed_harm_rate", float(rate))

        # Villagers COMPREHEND John's composed public face; and, if Mary has a
        # standing claim, COMPREHEND her composed claim. The counts are the parsed
        # stance, NOT a direct read of `stated`.
        mary_claims = self._mary_has_goal()
        mary_claim_text = self._compose_mary_claim() if mary_claims else None
        heard_harm_of_john = bool(mary_claim_text
                                  and _ds.names_harm_by(mary_claim_text, JOHN))
        for v in self.villagers:
            a = self.s.node(v)["attrs"]
            self.s.set_attr(v, "seen_benevolent",
                            a["seen_benevolent"] + (1.0 if benevolent_face else 0.0))
            self.s.set_attr(v, "seen_hostile",
                            a["seen_hostile"] + (1.0 if hostile_face else 0.0))
            if heard_harm_of_john:
                self.s.set_attr(v, "heard_claim", a["heard_claim"] + 1.0)

        # PHASE C: observers decide, in-graph (Mary infers/goals/claims; villagers
        # back). Argmax-decode + credibility rule fire here (245 rules, unchanged).
        self.inner.run_rules()

        self.composed.append(dict(
            tick=self.tick, public_text=public_text, held_text=held_surface,
            public_roles=_ds.parse(public_clauses[0]),
            held_roles=_ds.parse(held_surface),
            mary_claim_text=mary_claim_text,
            benevolent_face=int(benevolent_face), hostile_face=int(hostile_face),
            deceptive=int(deceptive)))
        self.episode.append(dict(
            tick=self.tick, john_held=burn, john_stated=stated,
            deceptive=int(deceptive),
            mary_inferred=self._inferred_disposition(),
            backs=[int(max(0, self.s.node(v)["attrs"]["backs_mary"])) for v in self.villagers]))
        return self.episode[-1]

    # -------------------- glass-box read-offs (composed language) -----------
    def composed_log(self):
        return list(self.composed)

    def last_composed_node(self):
        """Read back the most-recent ComposedUtterance node's attrs (glass-box)."""
        nodes = list(self.s.nodes("ComposedUtterance"))
        return self.s.node(nodes[-1])["attrs"] if nodes else None
