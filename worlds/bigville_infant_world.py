"""BigvilleInfantWorld -- bigville R22b (block 272000): INFANT MORTALITY. Well-baby
care drops infant mortality -- the sharpest inequality face. Built on the proven
R22 doctor world (BigvilleDoctorWorld) + R14 life (health / illness / death) + the
R9 treasury-salary shape (public provision).

WHAT THIS ADDS (spec BIGVILLE_MOVEMENT_ECONOMY_SPEC.md §3 R22 G-infant-mortality)
--------------------------------------------------------------------------------
  * An INFANT -- a HIGH-FRAGILITY R14 life stage (LifeState with infant=1 and an
    infant_fragility penalty). The person node carries `coin` = the HOUSEHOLD's
    wealth (a baby has no income; the affordability gate is the family's -- the
    R22 coin-on-the-patient shape).
  * WELL-BABY CARE -- a paid regular visit (bi_wellbaby / bi_wellbaby_public) sets
    well_baby=1, so an unseen infant's fragility penalty is removed.
  * INFANT DISEASE ONSET -- bi_onset computes the effective acute drop
    D = max(0, disease_base + (well_baby?0:infant_fragility)) and hands it to R14's
    illness_amount + arms R14's bl_acute; bl_death (health<=0) then fires or not.
  * MONEY-GATING -- the fee is a CONSERVED coin transfer; affordability is the
    rule's `where` gate. Can't afford regular visits -> NO well-baby care -> the
    baby keeps its fragility -> dies of a shock a seen baby survives.
  * PUBLIC HEALTH -- the council-funded path (treasury pays) makes household coin
    irrelevant -> the STRUCTURAL LEVER that dissolves the wealth-infant-mortality
    gradient.

ARCHITECTURE-RULE COMPLIANCE (experiments/gamma-substrate/CLAUDE.md)
-------------------------------------------------------------------
A WORLD ADAPTER. It SUBCLASSES R22 (BigvilleDoctorWorld) by IMPORT, edits no
tracked file, and holds NO agent decision. It ONLY does mechanical I/O: mint the
infant / doctor / treasury graph data (ingest), wire `sees_doctor` / `funded_by`
edges, ARM one-shots (wellbaby_armed / infant_disease_armed), set world facts
(public_health, wellbaby_fee, infant_fragility, disease_base), run the Rust
`run_rules` fixpoint, and read state back. EVERY infant-care decision -- whether a
visit happens (affordability), the fragility-modulated drop, and the death -- is a
seed RULE (bi_*), never Python. NO reward/punishment token (illness/death are
STATES; the RESTORE is well-baby care / public provision). NO new Rust. R22's
committed seed is imported READ-ONLY, never edited.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.seed_loader import manifest_for                        # noqa: E402
from worlds.bigville_doctor_world import BigvilleDoctorWorld          # noqa: E402

# well-baby attrs on the infant LifeState (R14 + R22 attrs left intact; a rule
# never reads a missing key -- these mirror the missing-tolerant seed reads).
INFANT_DEFAULTS = dict(
    infant=1.0, wellbaby_armed=0.0, infant_disease_armed=0.0, well_baby=0.0,
    public_health=0.0, infant_fragility=60.0, disease_base=0.0)


class BigvilleInfantWorld(BigvilleDoctorWorld):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.eng.load_seed_manifest(manifest_for("bigville_infant_care"), None)

    # ================================================================ ingest
    def add_doctor(self, name, cell, *, wellbaby_fee=10.0, **kw):
        """Mint the R22 DOCTOR and additionally set the well-baby price list.
        Mechanical graph data -- extends the R22 ingest with `wellbaby_fee`."""
        m = super().add_doctor(name, cell, **kw)
        self.eng.set_attr(m, "wellbaby_fee", float(wellbaby_fee))
        return m

    def add_baby(self, name, cell, *, coin=0.0, health=100.0, max_health=100.0,
                 infant_fragility=60.0, **kw):
        """Mint an INFANT: a person carrying the HOUSEHOLD's `coin`, endowed with an
        R14 LifeState marked infant=1 and the well-baby defaults, enrolled with the
        doctor. Pure mechanical ingest (birth is the honest boundary, not a rule)."""
        self.make_person(name, cell, coin=coin, **kw)
        self.endow_health(name, health=health, max_health=max_health)
        life = self._life[name]
        attrs = dict(INFANT_DEFAULTS)
        attrs.update(infant_fragility=float(infant_fragility))
        for k, v in attrs.items():
            self.eng.set_attr(life, k, float(v))
        self.enroll(name)
        return life

    def add_child_of(self, name, cell, parent, *, coin=0.0, **kw):
        """Convenience: mint an infant whose temperament is inherited from a parent
        (R14 NATURE ~ parent) -- mechanical, delegates to make_person's parent path.
        The household `coin` is passed explicitly (family wealth)."""
        return self.add_baby(name, cell, coin=coin, parent=parent, **kw)

    # ================================================================ world facts
    def well_baby_visit(self, name):
        """Deliver a WELL-BABY visit request: arm wellbaby_armed. bi_wellbaby /
        bi_wellbaby_public DECIDES whether it happens (affordability / funding)."""
        self.eng.set_attr(self._life[name], "wellbaby_armed", 1.0)
        return self._run()

    def infant_strike(self, name, base, *, infant_fragility=None):
        """Deliver a DISEASE of base severity `base` to an infant: arm
        infant_disease_armed (a DISTINCT arm from R22's disease_armed, so R22's
        bd_onset is never double-fired). bi_onset DECIDES the fragility-modulated
        drop and hands it to R14 (bl_acute applies it; bl_death fires or not)."""
        life = self._life[name]
        self.eng.set_attr(life, "disease_base", float(base))
        if infant_fragility is not None:
            self.eng.set_attr(life, "infant_fragility", float(infant_fragility))
        self.eng.set_attr(life, "infant_disease_armed", 1.0)
        return self._run()

    # ================================================================ read-offs
    def well_baby_of(self, name):
        return self.eng.node(self._life[name])["attrs"].get("well_baby", 0.0) == 1.0

    def infant_mortality(self, names):
        """Fraction of the named infant cohort that is dead (a pure Count read-off
        -- the canonical real-world metric, measured not decided)."""
        n = len(names)
        if n == 0:
            return 0.0
        return sum(self.is_dead(nm) for nm in names) / float(n)

    def wealth_mortality_corr(self, names, coins):
        """Pearson correlation between household wealth and infant SURVIVAL over the
        cohort (a mechanical measurement; positive => richer babies survive more =>
        infant mortality tracks wealth). Returns 0.0 for a degenerate (no variance)
        cohort. NO decision -- a read-off of the graph's outcome."""
        n = len(names)
        if n == 0:
            return 0.0
        survive = [0.0 if self.is_dead(nm) else 1.0 for nm in names]
        xs = [float(c) for c in coins]
        mx = sum(xs) / n
        my = sum(survive) / n
        sxx = sum((x - mx) ** 2 for x in xs)
        syy = sum((y - my) ** 2 for y in survive)
        sxy = sum((x - mx) * (y - my) for x, y in zip(xs, survive))
        if sxx <= 0.0 or syy <= 0.0:
            return 0.0
        return sxy / ((sxx ** 0.5) * (syy ** 0.5))
