"""IntentCortex — second cognitive module; consumes groundings.

When SpeechCortex grounds an AcousticSign to a Concept (via the
`denotes` edge), downstream cognition needs to NOTICE — to form
an intent, plan a response, update context. IntentCortex is that
downstream consumer.

The structural shape is intentionally identical to SpeechCortex:
- own root node holding state counts
- own intrinsic period
- own reflex set
- own tick / wake API
- has_pending_work for scheduler-driven interrupts

Cross-cortex signalling works by GRAPH MUTATION: SpeechCortex's
grounding writes `pending_intent: True` on the Concept (done by
the world adapter as the bridge until graph-mutation hooks are
exposed at the substrate level). IntentCortex's reflex reads the
count of such concepts and fires when > 0.

For now the cortex's job is minimal: mint an Intent node per
new grounding, mark the Concept processed. Real cognition would
classify the intent kind, route to a planning subsystem, etc.
"""
from __future__ import annotations


_INTENT_PRODUCTIONS = [
    ("IntentCortex", "owns_root", "IntentRoot",
     "intent_cortex:owns_root"),
    ("IntentCortex", "has_reflex", "Reflex",
     "intent_cortex:has_reflex"),
    ("Intent", "about_concept", "Concept",
     "intent_cortex:intent_about_concept"),
    ("IntentRoot", "has_reflex", "Reflex",
     "intent_cortex:root_has_reflex"),
]


def _intent_root(substrate):
    """Find or mint the IntentRoot state node."""
    for n in substrate.nodes("IntentRoot"):
        return n
    return substrate.add_node("IntentRoot", {
        "origin": "intent_cortex",
        "n_intents_minted": 0,
    })


class IntentCortex:
    """Minimal second cortex. Pulses on its OWN clock (default
    50ms — faster than the 100ms speech cortex, mirroring how
    attention/orienting reflexes fire faster than perceptual
    integration). Watches for Concepts the world adapter has
    marked `pending_intent: True` (the grounding signal) and
    mints an Intent node per concept, then clears the flag."""

    def __init__(self, substrate, tick_period_ms: int = 50):
        self.s = substrate
        self.tick_period_ms = int(tick_period_ms)
        self.cortex_nid = None
        self._tick_count = 0
        self._wake_count = 0
        self._installed = False

    def install(self) -> "IntentCortex":
        for src_t, et, tgt_t, prov in _INTENT_PRODUCTIONS:
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
        for n in self.s.nodes("IntentCortex"):
            existing = n
            break
        if existing is None:
            self.cortex_nid = self.s.add_node("IntentCortex", {
                "tick_count": 0,
                "wake_count": 0,
                "tick_period_ms": int(self.tick_period_ms),
                "origin": "intent_cortex",
            })
        else:
            self.cortex_nid = existing
            stored = self.s.node(existing)["attrs"].get(
                "tick_period_ms")
            if stored is not None:
                self.tick_period_ms = int(stored)
        root = _intent_root(self.s)
        if root not in self.s.neighbours(self.cortex_nid,
                                              "owns_root"):
            try:
                self.s.add_edge(self.cortex_nid, "owns_root", root)
            except Exception:
                pass
        self._installed = True
        return self

    def attr_interests(self) -> set:
        """The cortex's stimulus reads `pending_intent` attrs on
        Concepts. That's the only attr the scheduler needs to
        watch to route wakes to this cortex."""
        return {"pending_intent"}

    def edge_interests(self) -> set:
        return set()

    def has_pending_work(self, vote_counts: dict | None = None) -> bool:
        """True iff any Concept carries `pending_intent: True`.
        The grounding signal SpeechCortex (or the world adapter)
        sets on each newly-denoted concept."""
        for c in self.s.nodes("Concept"):
            if self.s.node(c)["attrs"].get("pending_intent",
                                                  False):
                return True
        return False

    def state_counts(self,
                          vote_counts: dict | None = None) -> dict:
        root = _intent_root(self.s)
        n = 0
        for c in self.s.nodes("Concept"):
            if self.s.node(c)["attrs"].get("pending_intent",
                                                  False):
                n += 1
        self.s.set_attr(root, "n_pending_intents", int(n))
        return {"n_pending_intents": int(n)}

    def tick(self, vote_counts: dict | None = None) -> list:
        if not self._installed:
            raise RuntimeError("IntentCortex.install() not called")
        return self._dispatch("tick")

    def wake(self, vote_counts: dict | None = None) -> list:
        if not self._installed:
            raise RuntimeError("IntentCortex.install() not called")
        self._wake_count += 1
        self.s.set_attr(self.cortex_nid, "wake_count",
                          int(self._wake_count))
        return self._dispatch("wake")

    def _dispatch(self, reason) -> list:
        """The cortex's reflex loop: walk Concepts flagged
        `pending_intent`, mint an Intent node per concept, clear
        the flag. Returns audit (each fire = one minted intent)."""
        root = _intent_root(self.s)
        self._tick_count += 1
        self.s.set_attr(self.cortex_nid, "tick_count",
                          int(self._tick_count))
        audit: list = []
        n_before = int(self.s.node(root)["attrs"]
                           .get("n_intents_minted", 0))
        for c in self.s.nodes("Concept"):
            ca = self.s.node(c)["attrs"]
            if not ca.get("pending_intent", False):
                continue
            wname = ca.get("name", "?")
            intent_nid = self.s.add_node("Intent", {
                "kind": "perception_grounded",
                "word": wname,
                "origin": "intent_cortex",
            })
            try:
                self.s.add_edge(intent_nid, "about_concept", c)
            except Exception:
                pass
            self.s.set_attr(c, "pending_intent", False)
            audit.append((self._tick_count, "intent_minted",
                              wname))
        n_after = n_before + len(audit)
        self.s.set_attr(root, "n_intents_minted", n_after)
        self.s.set_attr(self.cortex_nid, "last_audit",
                          f"reason:{reason} n_minted:{len(audit)}")
        return audit

    def report(self) -> dict:
        root = _intent_root(self.s)
        n_minted = int(self.s.node(root)["attrs"]
                           .get("n_intents_minted", 0))
        intents = list(self.s.nodes("Intent"))
        return {
            "tick_count": self._tick_count,
            "wake_count": self._wake_count,
            "n_intents_total": len(intents),
            "n_intents_minted_this_run": n_minted,
        }


__all__ = ["IntentCortex"]
