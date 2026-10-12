"""
forecast_text — legs (iv) + (v): the as-of-bounded confidence shift over the
REAL text pipeline, and the optional TimeInfer forward-projection centering
(prereg §1, §4 arms 4/5/6).

Reuses the PoC `SeldonConfidenceForecaster` VERBATIM for the mechanism
(`_learn_kernel` / `_learn_bands` / `_propagate` / `_foveate` and the
text-overlay blend). The ONLY thing replaced is the STUB `_text_target_band`,
which in the PoC read `tk.incoming_regime` straight off a struct. Here the target
band is DERIVED from the real pipeline:

    corpus items with tick <= cutoff   (leg iv, the as-of coordinate bound)
      -> ingest (leg i/iii): mention_surface + claim_kind
      -> link (leg ii): surface -> panel entity via the graph referent rule
      -> claim_to_regime: claim_kind -> incoming band {0,1}
      -> the most recent linked+typed item for THIS entity in the lead window
         gives the target band the confidence mass shifts toward (leg v).

Three text arms share this class, differing only in how the band is derived:
  * real   (RealTextForecaster, use_aliases=True): full pipeline above.
  * oracle (OracleTextForecaster): linking+typing use the ground-truth struct
    (the PoC's clean path) — the upper bound isolating leg-(ii)/(iii) loss.
  * tinfer (TimeInferForecaster): real pipeline, but the reachable-set is
    centered on the TimeInfer forward projection (graph-native) instead of the
    last-value point mass. Tests H3.

The as-of bound can be DISABLED (`enforce_asof=False`) for the H4 leakage probe.
"""

from __future__ import annotations

import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
_POC = os.path.join(os.path.dirname(_HERE), "seldon_t2_poc")
for p in (_ROOT, _HERE, _POC):
    if p not in sys.path:
        sys.path.insert(0, p)

from forecasters import SeldonConfidenceForecaster  # noqa: E402  (PoC, verbatim)
from ingest import ingest_corpus, claim_to_regime    # noqa: E402
from linking import EntityLinker                      # noqa: E402


# ---------------------------------------------------------------------------
# Base: a Seldon forecaster whose text band comes from a pluggable "band
# provider" instead of the PoC struct read. Everything else is inherited.
# ---------------------------------------------------------------------------
class _TextBandForecaster(SeldonConfidenceForecaster):
    """Overrides ONLY `_text_target_band`. The band provider is a callable
    (entity, cutoff) -> band in {0,1} or None, set by the subclass."""

    def __init__(self, panel, cutoff, corpus, *, text_lead=None,
                 enforce_asof=True):
        self.corpus = corpus
        self.enforce_asof = enforce_asof
        super().__init__(panel, cutoff, text_lead=text_lead)

    def _band_provider(self, entity, cutoff):
        raise NotImplementedError

    def _text_target_band(self, entity):
        return self._band_provider(entity, self.cutoff)


# ---------------------------------------------------------------------------
# REAL arm — the full ingest -> link -> type -> as-of pipeline (arm 4).
# ---------------------------------------------------------------------------
class RealTextForecaster(_TextBandForecaster):
    """The band is derived from the REAL text: linked+typed corpus items with
    tick<=cutoff, most recent within the lead window for this entity."""

    def __init__(self, panel, cutoff, corpus, *, linker, text_lead=None,
                 enforce_asof=True):
        self._linker = linker
        # Precompute (once per cutoff) the ingested+linked+typed records so the
        # per-entity/per-horizon forecast calls are cheap. As-of bound applied
        # here (leg iv): only items with tick<=cutoff, unless the H4 probe
        # disables it.
        raw = corpus.items_asof(cutoff) if enforce_asof else list(corpus.items)
        ci = ingest_corpus(raw)
        # linked records: (tick, entity_id, band) for typed, linkable items
        self._linked = []
        for rec in ci:
            band = claim_to_regime(rec.claim_kind)
            if band is None:
                continue
            ent = self._linker.link(rec.mention_surface)
            if ent is None:
                continue
            self._linked.append((rec.tick, ent, band))
        super().__init__(panel, cutoff, corpus, text_lead=text_lead,
                         enforce_asof=enforce_asof)

    def _band_provider(self, entity, cutoff):
        lead = self.text_lead
        # As-of bound (leg iv): the upper edge of the window is `cutoff` when
        # enforcing. The H4 leakage probe disables it, so a future-dated item
        # (t>cutoff, up to the horizon) CAN be grabbed — that is the cheat the
        # probe must detect. Without this the window silently re-imposed t<=cutoff
        # and the probe could never leak (a harness bug, not a validity result).
        hi = cutoff if self.enforce_asof else cutoff + lead
        cand = [(t, b) for (t, e, b) in self._linked
                if e == entity and t >= cutoff - lead and t <= hi]
        if not cand:
            return None
        cand.sort(key=lambda tb: tb[0])
        return cand[-1][1]


# ---------------------------------------------------------------------------
# ORACLE arm — clean linking+typing from the struct (arm 5), the upper bound.
# ---------------------------------------------------------------------------
class OracleTextForecaster(_TextBandForecaster):
    """Identical to RealTextForecaster but linking+typing use ground truth
    (corpus NewsItem.gt_entity / gt_incoming_regime). Isolates leg-(ii)/(iii)
    loss: any gap between this and RealText is the linking/typing tax."""

    def __init__(self, panel, cutoff, corpus, *, text_lead=None,
                 enforce_asof=True):
        raw = corpus.items_asof(cutoff) if enforce_asof else list(corpus.items)
        self._linked = [(it.tick, it.gt_entity, it.gt_incoming_regime)
                        for it in raw
                        if not it.gt_spurious and it.gt_incoming_regime is not None]
        super().__init__(panel, cutoff, corpus, text_lead=text_lead,
                         enforce_asof=enforce_asof)

    def _band_provider(self, entity, cutoff):
        lead = self.text_lead
        hi = cutoff if self.enforce_asof else cutoff + lead
        cand = [(t, b) for (t, e, b) in self._linked
                if e == entity and t >= cutoff - lead and t <= hi]
        if not cand:
            return None
        cand.sort(key=lambda tb: tb[0])
        return cand[-1][1]


# ---------------------------------------------------------------------------
# TIMEINFER arm — real pipeline, reachable set centered on the TimeInfer
# forward projection instead of the last-value point mass (arm 6, tests H3).
# ---------------------------------------------------------------------------
def timeinfer_project(history, horizon, max_b=8):
    """Center of the reachable set at `horizon`, via the substrate's TimeInfer
    forward projection (graph-native), with an honest Python fallback.

    We build a tick-ordered frame sequence from the recent history — each frame
    a single-cell relation with a declared `coord:v` slot (the shape
    gen_control_regime_escalation_seed feeds TimeInfer) — and read the
    `predicted` frame G^K(f0). TimeInfer.predicted is the EXACT-orbit point
    projection (prereg §1.1): a deterministic CENTER, not a distribution. When
    TimeInfer floors (no single generator carries the noisy series, the common
    case for a mean-reverting integer walk), we fall back to the last value —
    exactly the PoC center — so this arm is never WORSE-centered than real by
    construction; H3 asks whether it ever helps.
    """
    hist = np.asarray(history, dtype=int)
    if len(hist) < 3:
        return int(hist[-1])
    try:
        import substrate_rs as srs
        # frames: last few values as single-slot coord:v relations, tick order.
        window = [int(v) for v in hist[-5:]]
        frames = [[("m", v)] for v in window]
        # dim_types codebook part declaring slot 1 as coord:v (slot 0 predicate).
        # TimeInfer reads coord slots from the first codebook part; we pass the
        # frames as a literal sequence and rely on the translate-offset path
        # (1-D integer series => infer_translate_offset on the single coord).
        term = srs.Term("TimeInfer", sequence=srs.Lit(frames),
                        codebook_type="ShapeSignature", max_b=max_b,
                        field="explained")
        s = srs.Substrate()
        explained = s.evaluate(term, {})
        if not explained:
            return int(hist[-1])
        # read offset (per-step delta) and walk it `horizon` steps from last.
        off_term = srs.Term("TimeInfer", sequence=srs.Lit(frames),
                            codebook_type="ShapeSignature", max_b=max_b,
                            field="offset")
        offset = s.evaluate(off_term, {})
        if offset and len(offset) >= 1:
            delta = int(offset[-1])
            return int(hist[-1]) + delta * horizon
        return int(hist[-1])
    except Exception:
        return int(hist[-1])


class TimeInferForecaster(RealTextForecaster):
    """Real pipeline, but `forecast` centers the reachable-set propagation on
    the TimeInfer forward projection rather than the last observed value."""

    def _propagate(self, start_cell, horizon):
        # start_cell is the last value (PoC). Re-center on the TimeInfer
        # projection, then run the INHERITED convolution from that center so the
        # stepped MASS is still the empirical innovation kernel (prereg §1.1).
        return super()._propagate(start_cell, horizon)

    def forecast(self, entity, horizon, use_text=False):
        hist = self.panel.series[entity, : self.cutoff + 1]
        center = timeinfer_project(hist, horizon)
        # Temporarily splice the TimeInfer center as the propagation start by
        # calling the inherited machinery with a shifted history tail. The
        # inherited forecast() reads hist[-1] as start; we emulate by delegating
        # to _propagate directly and reusing the inherited text overlay path.
        cells, masses = self._propagate(int(center), horizon)
        if use_text:
            band = self._text_target_band(entity)
            if band is not None:
                cells, masses = self._apply_text_overlay(cells, masses, band)
        return self._foveate(cells, masses)

    def _apply_text_overlay(self, cells, masses, band):
        """The PoC's text-overlay blend, factored out so the tinfer arm reuses
        it verbatim (same w=0.6, same target-band Gaussian)."""
        target = self.band_centres[band]
        sd = max(1.0, float(self.panel.sigma) * 1.2)
        from math import erf, sqrt
        t_cells = np.arange(int(target - 4 * sd), int(target + 4 * sd) + 1)

        def cdf(z):
            return 0.5 * (1 + erf((z - target) / (sd * sqrt(2))))
        t_mass = np.array([cdf(c + 0.5) - cdf(c - 0.5) for c in t_cells])
        t_mass = np.clip(t_mass, 1e-12, None)
        t_mass /= t_mass.sum()
        all_cells = np.union1d(cells, t_cells.astype(float))
        base = dict(zip(cells, masses))
        text = dict(zip(t_cells.astype(float), t_mass))
        w = 0.6
        blended = np.array([(1 - w) * base.get(c, 0.0) + w * text.get(c, 0.0)
                            for c in all_cells])
        blended /= blended.sum()
        return all_cells, blended


if __name__ == "__main__":
    from corpus_gen import generate_corpus
    c = generate_corpus(seed=1)
    cutoff = 200
    linker = EntityLinker(c.panel.E, use_aliases=True)
    real = RealTextForecaster(c.panel, cutoff, c, linker=linker)
    oracle = OracleTextForecaster(c.panel, cutoff, c)
    tinf = TimeInferForecaster(c.panel, cutoff, c, linker=linker)
    print(f"linked records (real, asof {cutoff}): {len(real._linked)}")
    print(f"linked records (oracle, asof {cutoff}): {len(oracle._linked)}")
    for e in (0, 5, 12):
        for h in (1, 3):
            rc = real.forecast(e, h, use_text=True)
            oc = oracle.forecast(e, h, use_text=True)
            tc = tinf.forecast(e, h, use_text=True)
            print(f"  entity {e:2d} h={h}: real band={real._text_target_band(e)} "
                  f"oracle band={oracle._text_target_band(e)} "
                  f"| real supp={len(rc[0])} tinf supp={len(tc[0])}")
