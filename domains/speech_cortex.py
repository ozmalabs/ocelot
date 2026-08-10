"""SpeechCortex — first-class cognitive module for speech.

Speech is not a script-level concern; it's a specialised cortex of
the agent's mind. This module makes that explicit: a `SpeechCortex`
graph node OWNS its sub-state — its AcousticLexicon, its phonology
Microtheory, its predicate Concepts, its Reflex set, its
PhonologyRoot for state counts — and it has its own `tick()`
method that fires the reflex loop until quiescent.

Matches the meta-cognitive structure pattern (`agent.create_cortex`)
from prior work. A SpeechCortex is the OWNER of everything the
phonology stack produces: signs flow into it, reflexes fire,
hypotheses get raised, predicates retune, signatures revise.

External callers see one API:

    cortex = SpeechCortex(substrate, lexicon_name="stt")
    cortex.install()
    cortex.tick(vote_counts=vote_counts)
    # …
    cortex.report()

`tick()` is the agent's speech-center's own loop: surface state,
fire reflexes in priority order, loop until no Reflex fires.
Equivalent to a brain area pulsing on its own schedule, driven
by its internal preconditions rather than external orchestration.

Graph layout:

    SpeechCortex
      ├─ owns_lexicon       → AcousticLexicon
      ├─ owns_microtheory   → Microtheory(phonology)
      ├─ owns_root          → PhonologyRoot (state counts)
      ├─ has_reflex         → Reflex(phonology_perceive)
      ├─ has_reflex         → Reflex(phonology_abstract)
      ├─ has_reflex         → Reflex(phonology_detect)
      ├─ has_reflex         → Reflex(phonology_investigate)
      ├─ has_reflex         → Reflex(phonology_analyse)
      ├─ has_reflex         → Reflex(phonology_act)
      └─ has_reflex         → Reflex(phonology_verify)

Other cortices (visual, motor, somatosensory, etc.) can be built
on the same shape. A future MasterTick walks each cortex and
calls its `.tick()` — true concurrent cognitive activity.
"""
from __future__ import annotations

from .phonology import (
    install_phonology,
    install_phonology_reflexes,
    fire_phonology_reflexes,
    surface_phonology_state,
    _phonology_root,
    teach_word_signature,
    classify_signs,
    learn_word_signatures,
    detect_phonology_impasses,
)


_CORTEX_PRODUCTIONS = [
    ("SpeechCortex", "owns_lexicon", "AcousticLexicon",
     "speech_cortex:owns_lexicon"),
    ("SpeechCortex", "owns_microtheory", "Microtheory",
     "speech_cortex:owns_microtheory"),
    ("SpeechCortex", "owns_root", "PhonologyRoot",
     "speech_cortex:owns_root"),
    ("SpeechCortex", "has_reflex", "Reflex",
     "speech_cortex:cortex_has_reflex"),
]


class SpeechCortex:
    """A first-class speech-cognitive module with its OWN intrinsic
    clock. Biological brain regions oscillate at their own rates
    (theta/alpha/beta/gamma); the master clock provides absolute
    time but doesn't synchronize them. Same here: `tick_period_ms`
    is the cortex's intrinsic rhythm. A scheduler dispatches each
    cortex independently when its own period elapses.

    Reflexes are INTERRUPTS within (and across) cortices: `wake()`
    forces an immediate reflex pass off the regular cadence — used
    when an external event (audio ingest, cross-cortex signal)
    requires attention before the next scheduled tick. Mirrors
    sensory drive overriding background oscillation.

    The cortex IS graph data — this class is the world adapter
    that boots it and provides the dispatch API."""

    def __init__(self, substrate, lexicon_name: str = "stt",
                  tick_period_ms: int = 100):
        self.s = substrate
        self.lexicon_name = lexicon_name
        self.tick_period_ms = int(tick_period_ms)
        self.cortex_nid = None
        self._tick_count = 0
        self._wake_count = 0
        self._installed = False

    def install(self) -> "SpeechCortex":
        """Idempotent install. Creates the SpeechCortex graph node,
        the phonology Mt + concepts + predicates, the Reflex set,
        and wires the ownership edges. Re-running on an already-
        installed cortex is a no-op."""
        for src_t, et, tgt_t, prov in _CORTEX_PRODUCTIONS:
            try:
                self.s.add_production({
                    "src": {"type": src_t, "var": "src"},
                    "edge_type": et,
                    "tgt": {"type": tgt_t, "var": "tgt"},
                    "provenance": prov,
                })
            except Exception:
                pass

        # Find or mint the SpeechCortex node.
        existing = None
        for n in self.s.nodes("SpeechCortex"):
            a = self.s.node(n)["attrs"]
            if a.get("lexicon_name") == self.lexicon_name:
                existing = n
                break
        if existing is None:
            self.cortex_nid = self.s.add_node("SpeechCortex", {
                "lexicon_name": self.lexicon_name,
                "tick_count": 0,
                "wake_count": 0,
                "tick_period_ms": int(self.tick_period_ms),
                "last_audit": "",
                "origin": "speech_cortex",
            })
        else:
            self.cortex_nid = existing
            # Refresh period from graph in case the scheduler tuned it.
            stored = self.s.node(existing)["attrs"].get(
                "tick_period_ms")
            if stored is not None:
                self.tick_period_ms = int(stored)
            else:
                self.s.set_attr(existing, "tick_period_ms",
                                   int(self.tick_period_ms))

        # Install Mt + predicates + Reflexes.
        install_phonology(self.s)
        install_phonology_reflexes(self.s)

        # Wire ownership edges.
        root = _phonology_root(self.s)
        self._link("owns_root", root)
        # Lexicon (find by name; mint on demand left to STTPipeline).
        for lex in self.s.nodes("AcousticLexicon"):
            if self.s.node(lex)["attrs"].get("name") == self.lexicon_name:
                self._link("owns_lexicon", lex)
                break
        # Microtheory(phonology).
        for mt in self.s.nodes("Microtheory"):
            if self.s.node(mt)["attrs"].get("name") == "phonology":
                self._link("owns_microtheory", mt)
                break
        # Every phonology Reflex.
        for r in self.s.nodes("Reflex"):
            if self.s.node(r)["attrs"].get("origin") == "phonology":
                self._link("has_reflex", r)
        self._installed = True
        return self

    def _link(self, edge_type: str, target) -> None:
        """Idempotent add_edge from the cortex to target."""
        if target in self.s.neighbours(self.cortex_nid, edge_type):
            return
        try:
            self.s.add_edge(self.cortex_nid, edge_type, target)
        except Exception:
            pass

    def teach(self, word: str, signature: dict) -> int:
        """Top-down teaching path — pass through to the phonology
        layer. The cortex is the addressee of the teaching."""
        return teach_word_signature(self.s, word, signature)

    def tick(self, vote_counts: dict | None = None,
                max_iterations: int = 25) -> list:
        """The cortex's intrinsic pulse — runs on its own period
        (`tick_period_ms`). NOT driven by a master walk-all-
        cortices loop; a scheduler dispatches each cortex when
        ITS own period elapses. Returns the audit trail."""
        if not self._installed:
            raise RuntimeError("SpeechCortex.install() not called")
        return self._dispatch_reflexes(vote_counts, max_iterations,
                                              "tick")

    def wake(self, vote_counts: dict | None = None,
                max_iterations: int = 25) -> list:
        """Interrupt-style fire. Used when an external event
        (audio arrival, cross-cortex signal mutating the graph in
        a way this cortex cares about) requires immediate
        attention, ahead of the next scheduled tick. Biologically:
        sensory drive overrides background oscillation. The reflex
        loop runs the same way; only the dispatch reason differs."""
        if not self._installed:
            raise RuntimeError("SpeechCortex.install() not called")
        self._wake_count += 1
        self.s.set_attr(self.cortex_nid, "wake_count",
                          int(self._wake_count))
        return self._dispatch_reflexes(vote_counts, max_iterations,
                                              "wake")

    def _dispatch_reflexes(self, vote_counts, max_iterations,
                                reason) -> list:
        audit = fire_phonology_reflexes(
            self.s,
            vote_counts=vote_counts or {},
            lexicon_name=self.lexicon_name,
            max_iterations=max_iterations,
        )
        self._tick_count += 1
        self.s.set_attr(self.cortex_nid, "tick_count",
                          int(self._tick_count))
        self.s.set_attr(self.cortex_nid, "last_audit",
                          f"reason:{reason} n_fires:{len(audit)}")
        return audit

    def attr_interests(self) -> set:
        """Attr keys whose mutation MIGHT make this cortex eligible
        for a wake. The scheduler subscribes to these via the
        substrate's attr_set hook and marks the cortex dirty when
        a relevant attr changes — replaces polling on each
        advance(). False positives (dirty but no actual work) are
        fine; has_pending_work verifies on the wake path."""
        base = {
            "low_band_mean",        # signs gain band stats → perceive
            "investigated",         # impasse state → investigate/analyse
            "analysed",             # impasse → analyse
            "acted",                # hypothesis → act
            "threshold",            # predicate retune → verify
            "persistent_taught_mismatch",  # → analyse
            "last_threshold_classified",   # → verify
        }
        # Per-position signature changes (e.g. teaching writes
        # first_marker_prob_voicing). The detect reflex re-walks
        # impasses against these when they change.
        for prefix in ("first_marker_prob_", "last_marker_prob_",
                          "mid_marker_prob_", "marker_prob_"):
            for feat in ("voicing", "sibilant", "sonorant",
                            "formant_present", "noise_burst"):
                base.add(f"{prefix}{feat}")
        # W: cross-cortex coevolution. MotorCortex bumps these
        # attrs when its self-coherence checks fail/succeed on a
        # word — the babble signal. SpeechCortex picks it up and
        # the belief_revision layer can treat sustained motor
        # mismatch as additional evidence the word's signature or
        # predicates are mis-calibrated.
        base.add("motor_mismatch_count")
        base.add("motor_match_count")
        return base

    def edge_interests(self) -> set:
        """Edge types whose insertion/deletion can produce work."""
        return {
            "exhibits",      # classify wrote/removed an edge
            "denotes",       # a sign was grounded → propagate
            "has_entry",     # a sign appeared in the lexicon
        }

    def has_pending_work(self,
                              vote_counts: dict | None = None) -> bool:
        """True iff any of the cortex's state counts > 0. The
        scheduler reads this to decide interrupt-style wakes: a
        cortex with pending work runs ahead of its scheduled
        tick. Biology: sensory drive overrides background
        oscillation."""
        counts = self.state_counts(vote_counts=vote_counts)
        return any(int(v) > 0 for v in counts.values())

    def state_counts(self,
                          vote_counts: dict | None = None) -> dict:
        """Read the current state counts off PhonologyRoot. The
        Reflex stimuli read these same attrs at fire time."""
        return surface_phonology_state(
            self.s, _phonology_root(self.s),
            self.lexicon_name, vote_counts,
        )

    def report(self) -> dict:
        """Snapshot of cortex state — what it knows, what's
        unresolved, what it's tuned. Useful for the world adapter's
        end-of-run report."""
        signs = []
        for n in self.s.nodes("AcousticLexicon"):
            if self.s.node(n)["attrs"].get("name") == self.lexicon_name:
                signs = list(self.s.neighbours(n, "has_entry"))
                break

        thresholds = {}
        for c in self.s.nodes("Concept"):
            a = self.s.node(c)["attrs"]
            if a.get("origin") == "phonology":
                thresholds[a.get("name")] = a.get("threshold")

        n_imps = sum(1 for i in self.s.nodes("Impasse")
                       if self.s.node(i)["attrs"].get("kind")
                           == "phonology_divergence")
        n_resolved = sum(1 for i in self.s.nodes("Impasse")
                            if self.s.node(i)["attrs"].get("kind")
                                == "phonology_divergence"
                            and self.s.node(i)["attrs"].get("investigated"))
        n_hyps = sum(1 for h in self.s.nodes("MismatchHypothesis")
                        if self.s.node(h)["attrs"].get("origin")
                            == "phonology")
        n_acted = sum(1 for h in self.s.nodes("MismatchHypothesis")
                         if self.s.node(h)["attrs"].get("origin")
                             == "phonology"
                         and self.s.node(h)["attrs"].get("acted"))
        n_variants = sum(1 for c in self.s.nodes("Concept")
                            if self.s.node(c)["attrs"].get("origin")
                                == "phonology_variant")

        return {
            "tick_count": self._tick_count,
            "n_signs": len(signs),
            "thresholds": thresholds,
            "impasses_total": n_imps,
            "impasses_resolved": n_resolved,
            "hypotheses_total": n_hyps,
            "hypotheses_acted": n_acted,
            "variants_minted": n_variants,
        }


__all__ = ["SpeechCortex"]
