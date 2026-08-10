"""HarlowDistWorld -- HARLOW D1b (block 235000): the D1 wire/cloth apparatus,
but each infant's TEMPERAMENT (its contact-comfort / hunger drive weights in the
real regulator) is seeded per-individual from a POPULATION distribution, to
reproduce the GRADED individual variation real monkeys show. D1 was a near
step-function (cloth_frac sd 0.039, flee sd 0.000) because every infant was the
IDENTICAL individual (W_CONTACT = W_HUNGER = 1 for all); a population is a
DISTRIBUTION over temperaments.

ARCHITECTURE RULE COMPLIANCE (experiments/gamma-substrate/CLAUDE.md):
this is a WORLD ADAPTER and does NOTHING D1's adapter did not. It only WRITES
the per-infant drawn drive weights as `Drive` node attrs (mechanical world
setup -- exactly like HarvestWorld seeding heterogeneous agents with different
pool constants) and re-runs the graph. Drawing the weights ~Normal is the
RUNNER's mechanical job. The attachment DECISION is UNCHANGED: it is still the
Argmax `approach_target` rule in seeds/harlow_attachment.json riding the real
drive+regulator machinery. seeds/harlow_attachment.json and worlds/harlow_world.py
are REUSED UNCHANGED; this file is additive.

NO agent decision in Python: no if/else selects the infant's action; the world
adapter only publishes world facts (which mother provides what, time, stress,
and now the seeded temperament) and reads the graph's approach_target edge.
"""
from __future__ import annotations

from worlds.harlow_world import HarlowWorld


class HarlowDistWorld(HarlowWorld):
    """D1's infant, with its contact/hunger drive weights SEEDED per-individual.

    ``w_contact`` / ``w_hunger`` are the population-drawn drive weights (the
    infant's temperament). The RUNNER draws them ~Normal across the population;
    this adapter only writes them onto the real ``Drive`` nodes as attrs and
    re-runs the graph so the value rules recompute. Everything else -- the
    regulator, the attachment rules, the metabolism, the Argmax decision --
    is D1, unchanged.

    Under ablation (``contact_drive=False``) there is no contact Drive to carry
    a weight, so ``w_contact`` is simply not applied -- the falsifier is the
    same paired population with the contact drive removed.
    """

    def __init__(self, *, w_contact: float = 1.0, w_hunger: float = 1.0, **kw):
        super().__init__(**kw)
        # MECHANICAL world setup: write the drawn temperament as node attrs.
        # (No decision -- this is data, like a per-agent pool constant.)
        if self.contact is not None:
            self.s.set_attr(self.contact, "weight", float(w_contact))
        self.s.set_attr(self.hunger, "weight", float(w_hunger))
        self.w_contact = float(w_contact)
        self.w_hunger = float(w_hunger)
        # re-run so the value rules recompute against the seeded temperament
        self.inner.run_rules()

    def drawn_weights(self):
        """READ the seeded temperament back from the graph (glass-box)."""
        wc = self._attrs(self.contact)["weight"] if self.contact is not None else None
        wh = self._attrs(self.hunger)["weight"]
        return dict(w_contact=wc, w_hunger=wh)
