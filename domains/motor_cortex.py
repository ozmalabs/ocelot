"""Legacy Python MotorCortex compatibility wrapper.

.. warning::
   This class contains pre-graph-native cognitive policy: it scans intents,
   dispatches work, retains counters, and mints plans in Python.  It is kept
   only so historical speech experiments can still be reproduced.  It is not
   the Jabberwock motor core; new motor cognition must be Rust-evaluated graph
   rules with Python restricted to physical transduction.

When IntentCortex mints an Intent (because a sign was grounded to a
Concept), the agent should ACT on it. MotorCortex is the actor: it
walks unprocessed Intents, looks up the SpeechCortex's synthesised
output for the relevant word, mints an UtterancePlan recording what
would be spoken, and marks the Intent motor_processed.

This closes the perception → cognition → action loop:

    audio in → SpeechCortex perceives + grounds sign to Concept(word)
            → propagate-groundings reflex flags pending_intent
            → IntentCortex mints Intent
            → MotorCortex synthesises response + mints UtterancePlan
            → (audio out — optional, depending on synthesiser passed)

The synthesiser is pluggable: pass `synthesise=pipe.speak` and the
cortex actually produces audio buffers. Pass None and it just
records the plan (useful for testing the loop without speakers).

Pattern matches SpeechCortex / IntentCortex: own root, own period
(default 200ms — between speech 2000ms and intent 1000ms), own
reflex set, attr/edge/node interests for hook-driven wake routing.
"""
from __future__ import annotations

import warnings


LEGACY_COMPATIBILITY_ONLY = True


_MOTOR_PRODUCTIONS = [
    ("MotorCortex", "owns_root", "MotorRoot",
     "motor_cortex:owns_root"),
    ("MotorCortex", "has_reflex", "Reflex",
     "motor_cortex:has_reflex"),
    ("UtterancePlan", "for_intent", "Intent",
     "motor_cortex:plan_for_intent"),
    ("UtterancePlan", "of_concept", "Concept",
     "motor_cortex:plan_of_concept"),
    ("UtterancePlan", "produced_sign", "AcousticSign",
     "motor_cortex:plan_produced_sign"),
    ("MotorRoot", "has_reflex", "Reflex",
     "motor_cortex:root_has_reflex"),
]


def _motor_root(substrate):
    """Find or mint the MotorRoot state node."""
    for n in substrate.nodes("MotorRoot"):
        return n
    return substrate.add_node("MotorRoot", {
        "origin": "motor_cortex",
        "n_plans_minted": 0,
    })


class MotorCortex:
    """Action cortex. Consumes Intent nodes, produces UtterancePlan
    nodes (and optionally audio via a synthesise callable).

    Synthesiser signature: `(substrate, word: str) -> np.ndarray |
    None`. Most often bound to `STTPipeline.speak` with a partial
    application. None means the cortex only PLANS (records what it
    would say) without producing audio — fine for testing the
    cognitive loop without speaker integration.

    Faster intrinsic period than SpeechCortex by default: response
    should chase intent on a tighter timescale than perception
    integrates. Biology: motor cortex isn't bound to perceptual
    integration; it pulses on its own."""

    LEGACY_COMPATIBILITY_ONLY = True

    def __init__(self, substrate, synthesise=None,
                  re_ingest=None,
                  tick_period_ms: int = 200):
        """`synthesise(word)` → audio numpy array (or None).
        `re_ingest(audio)` → re-ingests the synthesised audio into
        SpeechCortex (closing the loop). When set, the cortex
        becomes self-monitoring: the agent perceives its own
        output, and the resulting signs are tagged
        `from_self_motor: True` + `self_word: <word>` so the
        comparison "did my articulation produce the expected
        percept?" is a graph walk away."""
        warnings.warn(
            "MotorCortex is legacy Python cognitive policy; use graph-native "
            "motor rules for new systems",
            DeprecationWarning,
            stacklevel=2,
        )
        self.s = substrate
        self.synthesise = synthesise
        self.re_ingest = re_ingest
        self.tick_period_ms = int(tick_period_ms)
        self.cortex_nid = None
        self._tick_count = 0
        self._wake_count = 0
        self._installed = False

    def install(self) -> "MotorCortex":
        for src_t, et, tgt_t, prov in _MOTOR_PRODUCTIONS:
            try:
                self.s.add_production({
                    "src": {"type": src_t, "var": "src"},
                    "edge_type": et,
                    "tgt": {"type": tgt_t, "var": "tgt"},
                    "provenance": prov,
                })
            except Exception:
                pass
        existing = None
        for n in self.s.nodes("MotorCortex"):
            existing = n
            break
        if existing is None:
            self.cortex_nid = self.s.add_node("MotorCortex", {
                "tick_count": 0,
                "wake_count": 0,
                "tick_period_ms": int(self.tick_period_ms),
                "origin": "motor_cortex",
            })
        else:
            self.cortex_nid = existing
            stored = self.s.node(existing)["attrs"].get(
                "tick_period_ms")
            if stored is not None:
                self.tick_period_ms = int(stored)
        root = _motor_root(self.s)
        if root not in self.s.neighbours(self.cortex_nid,
                                              "owns_root"):
            try:
                self.s.add_edge(self.cortex_nid, "owns_root", root)
            except Exception:
                pass
        self._installed = True
        return self

    def attr_interests(self) -> set:
        """`motor_processed` flips when this cortex processes an
        Intent — included so a re-processed Intent (rare) is
        re-detected."""
        return {"motor_processed"}

    def edge_interests(self) -> set:
        return set()

    def node_interests(self) -> set:
        """Newly-inserted Intent nodes wake this cortex via the
        scheduler's node_inserted hook routing."""
        return {"Intent"}

    def has_pending_work(self, vote_counts=None) -> bool:
        for i in self.s.nodes("Intent"):
            if not self.s.node(i)["attrs"].get("motor_processed",
                                                       False):
                return True
        return False

    def state_counts(self, vote_counts=None) -> dict:
        root = _motor_root(self.s)
        n = 0
        for i in self.s.nodes("Intent"):
            if not self.s.node(i)["attrs"].get("motor_processed",
                                                       False):
                n += 1
        self.s.set_attr(root, "n_intents_unprocessed", int(n))
        return {"n_intents_unprocessed": int(n)}

    def tick(self, vote_counts=None) -> list:
        if not self._installed:
            raise RuntimeError("MotorCortex.install() not called")
        return self._dispatch("tick")

    def wake(self, vote_counts=None) -> list:
        if not self._installed:
            raise RuntimeError("MotorCortex.install() not called")
        self._wake_count += 1
        self.s.set_attr(self.cortex_nid, "wake_count",
                          int(self._wake_count))
        return self._dispatch("wake")

    def _dispatch(self, reason) -> list:
        """Walk unprocessed Intents, synthesise (or plan), mint
        UtterancePlan per Intent, mark processed."""
        root = _motor_root(self.s)
        self._tick_count += 1
        self.s.set_attr(self.cortex_nid, "tick_count",
                          int(self._tick_count))
        audit: list = []
        for intent in self.s.nodes("Intent"):
            ia = self.s.node(intent)["attrs"]
            if ia.get("motor_processed", False):
                continue
            word = ia.get("word", "?")
            concepts = list(self.s.neighbours(intent,
                                                    "about_concept"))
            # Optionally synthesise. The cortex's plan exists
            # whether or not audio is produced — the cognitive
            # output is the plan; the audio is the effector.
            audio_len = None
            audio_max = None
            self_signs: list = []
            if self.synthesise is not None:
                try:
                    audio = self.synthesise(word)
                    if audio is not None:
                        audio_len = int(len(audio))
                        try:
                            audio_max = float(
                                max(abs(x) for x in audio)
                                if audio_len else 0.0)
                        except Exception:
                            audio_max = None
                        # Self-monitoring: re-ingest the audio so
                        # SpeechCortex perceives it. FROZEN-LEXICON
                        # path: the matcher binds the self-audio
                        # to existing signs (no EMA update, no
                        # hearings increment), but DOES mint a new
                        # Utterance with `heard_as → matched_sign`.
                        # We track new Utterances post-ingest and
                        # tag the signs they point at as
                        # from_self_motor + self_word.
                        if (self.re_ingest is not None
                                and audio_max
                                and audio_max > 0.005):
                            utts_before = set(
                                self.s.nodes("Utterance"))
                            try:
                                try:
                                    self.re_ingest(audio, word)
                                except TypeError:
                                    self.re_ingest(audio)
                            except Exception:
                                pass
                            new_utts = (set(self.s.nodes("Utterance"))
                                            - utts_before)
                            matched_signs: set = set()
                            for u in new_utts:
                                for s in self.s.neighbours(
                                        u, "heard_as"):
                                    matched_signs.add(s)
                            for s in matched_signs:
                                self.s.set_attr(s,
                                    "from_self_motor", True)
                                self.s.set_attr(s,
                                    "self_word", str(word))
                                self_signs.append(s)
                            # W: cross-cortex coevolution signal.
                            # If the matched sign denotes a word
                            # OTHER than what the motor was trying
                            # to say, that's evidence that the
                            # agent's perception OR articulation
                            # is mis-calibrated. Increment a
                            # `motor_mismatch_count` on the
                            # WORD-IT-TRIED-TO-SAY's concept. The
                            # SpeechCortex has this attr in its
                            # interests, so the mismatch triggers
                            # a wake — the belief_revision layer
                            # can use this as evidence the word's
                            # signature/predicates need work.
                            try:
                                word_cid = None
                                for c in self.s.nodes("Concept"):
                                    if (self.s.node(c)["attrs"]
                                            .get("name")
                                            == str(word)):
                                        word_cid = c
                                        break
                                if word_cid is not None:
                                    n_motor_mismatch = 0
                                    n_motor_match = 0
                                    for s in matched_signs:
                                        denoted = [
                                            self.s.node(c)["attrs"]
                                                .get("name")
                                            for c in
                                            self.s.neighbours(
                                                s, "denotes")
                                        ]
                                        if str(word) in denoted:
                                            n_motor_match += 1
                                        elif denoted:
                                            n_motor_mismatch += 1
                                    if (n_motor_mismatch
                                            or n_motor_match):
                                        wa = (self.s.node(word_cid)
                                                  ["attrs"])
                                        prev_mm = int(wa.get(
                                            "motor_mismatch_count",
                                            0))
                                        prev_mc = int(wa.get(
                                            "motor_match_count",
                                            0))
                                        self.s.set_attr(
                                            word_cid,
                                            "motor_mismatch_count",
                                            prev_mm
                                            + n_motor_mismatch)
                                        self.s.set_attr(
                                            word_cid,
                                            "motor_match_count",
                                            prev_mc
                                            + n_motor_match)
                            except Exception:
                                pass
                except Exception:
                    pass
            plan_attrs = {
                "word": word,
                "origin": "motor_cortex",
            }
            if audio_len is not None:
                plan_attrs["audio_samples"] = int(audio_len)
            if audio_max is not None:
                plan_attrs["audio_peak"] = float(audio_max)
            if self_signs:
                plan_attrs["n_self_signs"] = int(len(self_signs))
            plan = self.s.add_node("UtterancePlan", plan_attrs)
            for s in self_signs:
                try:
                    self.s.add_edge(plan, "produced_sign", s)
                except Exception:
                    pass
            try:
                self.s.add_edge(plan, "for_intent", intent)
                if concepts:
                    self.s.add_edge(plan, "of_concept",
                                       concepts[0])
            except Exception:
                pass
            self.s.set_attr(intent, "motor_processed", True)
            audit.append((self._tick_count, "plan_minted", word,
                              audio_len))
        n_minted = int(self.s.node(root)["attrs"]
                           .get("n_plans_minted", 0)) + len(audit)
        self.s.set_attr(root, "n_plans_minted", n_minted)
        self.s.set_attr(self.cortex_nid, "last_audit",
                          f"reason:{reason} n_planned:{len(audit)}")
        return audit

    def report(self) -> dict:
        root = _motor_root(self.s)
        n_minted = int(self.s.node(root)["attrs"]
                           .get("n_plans_minted", 0))
        plans = list(self.s.nodes("UtterancePlan"))
        word_hist: dict = {}
        for p in plans:
            w = self.s.node(p)["attrs"].get("word", "?")
            word_hist[w] = word_hist.get(w, 0) + 1
        return {
            "tick_count": self._tick_count,
            "wake_count": self._wake_count,
            "n_plans_total": len(plans),
            "n_plans_minted_this_run": n_minted,
            "word_histogram": word_hist,
        }


__all__ = ["LEGACY_COMPATIBILITY_ONLY", "MotorCortex"]
