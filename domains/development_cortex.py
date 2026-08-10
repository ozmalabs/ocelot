"""DevelopmentCortex — meta-cognitive cortex that manages the
substrate's own developmental trajectory.

The substrate has cortices for perception (SpeechCortex), intent
(IntentCortex), action (MotorCortex). What was missing: a cortex
whose JOB is to watch the others develop, apply taught
developmental theory to interpret what it sees, and adjust the
substrate's own configuration toward better development.

Architecture:
  reads:   cross-cortex state (motor_coherence, predicate
           thresholds, impasse rates, entropy)
  reads:   the speech_development Microtheory (taught knowledge
           about how development works)
  writes:  recommendations on a DevelopmentRoot graph node:
             babble_per_cycle, apply_min_score,
             invention_balance_threshold, request_teaching_word
  effects: the world adapter reads these recommendations + acts
           on them (drives the cycle)

The agent uses its OWN model of speech development to direct its
OWN development. Same recursive structure as a human child who
has read about babbling and decides to babble more.

Period: slow (default 5000ms). Meta-cognition runs slower than
perception/action.
"""
from __future__ import annotations

from .speech_development import install_speech_development


_DEV_CORTEX_PRODUCTIONS = [
    ("DevelopmentCortex", "owns_root", "DevelopmentRoot",
     "development_cortex:owns_root"),
]


def _dev_root(substrate):
    """Find or mint the DevelopmentRoot state node."""
    for n in substrate.nodes("DevelopmentRoot"):
        return n
    return substrate.add_node("DevelopmentRoot", {
        "origin": "development_cortex",
        # Recommended values. The world adapter reads + applies.
        "babble_per_cycle": 1,           # 1 babble of each word
        "apply_min_score": 0.7,          # default
        # invention_balance_threshold is seeded by install_invention_management
        # (seeds/invention_management.json) — not hardcoded here.
        "predicate_stable_cycles": 0,    # tracking
        "stage": "pre_canonical",
    })


_STAGE_TRANSITIONS = [
    # (stage_name, from_stage, condition_description)
    ("canonical_babbling", "pre_canonical",
     "motor_coherence_avg >= 0.2"),
    ("variegated_babbling", "canonical_babbling",
     "motor_coherence_avg >= 0.4 AND predicate_stable_cycles >= 3"),
    ("first_words", "variegated_babbling",
     "motor_coherence_avg >= 0.5 AND predicate_stable_cycles >= 5"),
    ("vocabulary_explosion", "first_words",
     "motor_coherence_avg >= 0.6 AND impasses_recent_avg < 5"),
]


class DevelopmentCortex:
    """Meta-cognitive cortex managing the substrate's own
    developmental trajectory. Reads cross-cortex state, applies
    rules from the taught speech_development theory, writes
    recommendations the world adapter reads."""

    def __init__(self, substrate, tick_period_ms: int = 5000):
        self.s = substrate
        self.tick_period_ms = int(tick_period_ms)
        self.cortex_nid = None
        self._tick_count = 0
        self._wake_count = 0
        self._installed = False
        # History buffers — for trend rules.
        self._motor_coherence_hist: list = []
        self._impasses_hist: list = []
        self._delta_thr_hist: list = []
        self._predicate_stable_count = 0

    def install(self) -> "DevelopmentCortex":
        for src_t, et, tgt_t, prov in _DEV_CORTEX_PRODUCTIONS:
            try:
                self.s.add_production({
                    "src": {"type": src_t, "var": "src"},
                    "edge_type": et,
                    "tgt": {"type": tgt_t, "var": "tgt"},
                    "provenance": prov,
                })
            except Exception:
                pass
        # Install the underlying Mt the cortex reasons against.
        install_speech_development(self.s)
        existing = None
        for n in self.s.nodes("DevelopmentCortex"):
            existing = n
            break
        if existing is None:
            self.cortex_nid = self.s.add_node("DevelopmentCortex", {
                "tick_count": 0,
                "wake_count": 0,
                "tick_period_ms": int(self.tick_period_ms),
                "origin": "development_cortex",
            })
        else:
            self.cortex_nid = existing
        root = _dev_root(self.s)
        if root not in self.s.neighbours(self.cortex_nid,
                                              "owns_root"):
            try:
                self.s.add_edge(self.cortex_nid, "owns_root", root)
            except Exception:
                pass
        # Cortex operates_in the speech_development Mt — graph-
        # resident link from this cortex to the body of theory it
        # reasons against.
        for n in self.s.nodes("Microtheory"):
            if (self.s.node(n)["attrs"].get("name")
                    == "speech_development"):
                if n not in self.s.neighbours(self.cortex_nid,
                                                  "operates_in"):
                    try:
                        self.s.add_edge(self.cortex_nid,
                                           "operates_in", n)
                    except Exception:
                        pass
                break
        # The agent's feature-invention management is a GRAPH-RESIDENT rule,
        # not a Python decision (CLAUDE.md). observe() only records the signals
        # the rule reads + fires it.
        from domains.invention_management import install_invention_management
        info = install_invention_management(self.s)
        self._inv_rule_idx = info["rule_index"]
        self._inv_native = self.s._inner if hasattr(self.s, "_inner") else self.s
        self._installed = True
        return self

    def attr_interests(self) -> set:
        # The cortex polls state explicitly per tick; no hook-
        # driven wakes needed beyond its own intrinsic clock.
        return set()

    def edge_interests(self) -> set:
        return set()

    def node_interests(self) -> set:
        return set()

    def has_pending_work(self, vote_counts=None) -> bool:
        # Always tick on schedule — meta-cognition observes
        # accumulated state, doesn't have "pending events."
        return False

    def observe(self, *,
                  motor_coherence_avg: float,
                  predicate_delta_norm: float,
                  impasses_raised: int,
                  hypotheses_kinds: dict | None = None,
                  exhibits_entropy: float = 0.0) -> dict:
        """Take a per-cycle observation from the world adapter +
        return the cortex's recommendations. Updates the cortex's
        history buffers."""
        self._motor_coherence_hist.append(motor_coherence_avg)
        self._impasses_hist.append(impasses_raised)
        self._delta_thr_hist.append(predicate_delta_norm)
        # Trim history.
        for h in (self._motor_coherence_hist,
                     self._impasses_hist,
                     self._delta_thr_hist):
            if len(h) > 20:
                del h[:-20]

        root = _dev_root(self.s)

        # === Apply rules from speech_development theory ===

        # Rule 1 (babbling concept):
        # If motor_coherence < 0.5, increase babble per cycle.
        # If > 0.7, decrease.
        babble_rec = int(self.s.node(root)["attrs"]
                            .get("babble_per_cycle", 1))
        if motor_coherence_avg < 0.3:
            babble_rec = min(5, babble_rec + 1)
        elif motor_coherence_avg > 0.7:
            babble_rec = max(1, babble_rec - 1)
        self.s.set_attr(root, "babble_per_cycle", int(babble_rec))

        # Rule 2 (predicate convergence tracking):
        # Track how long predicates have been stable.
        if predicate_delta_norm < 1e-6:
            self._predicate_stable_count += 1
        else:
            self._predicate_stable_count = 0
        self.s.set_attr(root, "predicate_stable_cycles",
                          int(self._predicate_stable_count))

        # Rules 3+4 (mismatch_signal + feature_invention concepts):
        # The invention-threshold DECISION is graph-resident — the
        # `manage_feature_invention` Rule on the DevelopmentRoot
        # (domains/invention_management.py). Here the cortex only RECORDS the
        # observations the rule reads, then fires it. No Python decides the
        # threshold (CLAUDE.md).
        recent_impasses = (sum(self._impasses_hist[-5:])
                              / max(1, len(self._impasses_hist[-5:])))
        self.s.set_attr(root, "recent_impasses", float(recent_impasses))
        self.s.set_attr(root, "predicate_delta_norm",
                          float(predicate_delta_norm))
        self.s.set_attr(root, "invention_eval_pending", 1)
        if getattr(self, "_inv_rule_idx", None) is not None:
            self._inv_native.apply_rule_once(self._inv_rule_idx)
        invention_thresh = float(self.s.node(root)["attrs"]
                                    .get("invention_balance_threshold", 0.7))

        # Rule 5 (developmental stage):
        # Identify which stage the substrate is currently in.
        stage = self._determine_stage(motor_coherence_avg,
                                            recent_impasses)
        prev_stage = self.s.node(root)["attrs"].get("stage")
        self.s.set_attr(root, "stage", stage)

        self._tick_count += 1
        self.s.set_attr(self.cortex_nid, "tick_count",
                          int(self._tick_count))

        return {
            "babble_per_cycle": babble_rec,
            "invention_balance_threshold": invention_thresh,
            "predicate_stable_cycles":
                self._predicate_stable_count,
            "stage": stage,
            "stage_transitioned": stage != prev_stage,
        }

    def _determine_stage(self, motor_coherence_avg,
                              recent_impasses) -> str:
        if (motor_coherence_avg >= 0.6
                and recent_impasses < 5):
            return "vocabulary_explosion"
        if (motor_coherence_avg >= 0.5
                and self._predicate_stable_count >= 5):
            return "first_words"
        if (motor_coherence_avg >= 0.4
                and self._predicate_stable_count >= 3):
            return "variegated_babbling"
        if motor_coherence_avg >= 0.2:
            return "canonical_babbling"
        return "pre_canonical"

    def tick(self, vote_counts=None) -> list:
        if not self._installed:
            raise RuntimeError(
                "DevelopmentCortex.install() not called")
        # Tick is empty by default — the world adapter calls
        # `observe()` directly to pump state through the cortex.
        # This keeps the scheduler from polling without context.
        self._tick_count += 1
        self.s.set_attr(self.cortex_nid, "tick_count",
                          int(self._tick_count))
        return []

    def wake(self, vote_counts=None) -> list:
        return self.tick(vote_counts)

    def state_counts(self, vote_counts=None) -> dict:
        return {}

    def report(self) -> dict:
        root = _dev_root(self.s)
        a = self.s.node(root)["attrs"]
        return {
            "stage": a.get("stage"),
            "babble_per_cycle": int(a.get("babble_per_cycle", 1)),
            "invention_balance_threshold": float(a.get(
                "invention_balance_threshold", 0.7)),
            "predicate_stable_cycles": int(a.get(
                "predicate_stable_cycles", 0)),
            "tick_count": self._tick_count,
        }


__all__ = ["DevelopmentCortex"]
