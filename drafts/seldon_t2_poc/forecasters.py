"""
Forecasters, all emitting the SAME object type so CRPS compares apples to apples:
a stepped predictive distribution per (entity, horizon) as (values, masses),
values being INTEGER cells (frame/continuum invariant).

Three forecasters:

  1. ClimatologyForecaster (text-blind baseline A)
     The empirical distribution of the entity's own history up to the cutoff.
     A "cone of uncertainty" with no dynamics — the reachable set is just the
     historical support, credence = historical frequency. Horizon-invariant.

  2. GaussianAR1Forecaster (text-blind baseline B)
     Fit AR(1) mean/phi/sigma from history; propagate h steps; the h-step
     predictive is Gaussian with known mean and variance, then DISCRETISED onto
     integer cells (so it is scored as a stepped dist, same as the others).
     This is the standard statistical baseline T2 wants uplift over.

  3. SeldonConfidenceForecaster (the thing under test)
     OCELOT-native framing:
       - CODEBOOK: quantise recent history into "shape" quanta = the recent
         local level (which regime cell-band we're in) via a short window.
       - REACHABLE SET (manifold support over horizon h): from the current
         cell, roll the learned transition dynamics forward to enumerate the
         set of integer cells reachable within h steps at operative resolution.
         Adaptive/foveated: support is truncated to cells carrying non-trivial
         credence (finer where decision-relevant, coarse tails dropped).
       - CONFIDENCE DIMENSION: a stepped credence mass over those cells,
         obtained by propagating an empirical one-step transition/innovation
         kernel h times (a discrete convolution), NOT a Gaussian assumption.
       - TEXT OVERLAY (optional): if as-of text signals an incoming regime,
         shift/sharpen the confidence mass toward that regime's cell-band.
         This is the "text shifts/sharpens the confidence mass" mechanism.

All three are deliberately simple. The point is the FRAMING and the MECHANISM,
not squeezing maximal accuracy.
"""

from __future__ import annotations

import numpy as np


# ---------------------------------------------------------------------------
# Baseline A: climatology / empirical quantile (text-blind)
# ---------------------------------------------------------------------------
def climatology_forecast(history, horizon):
    """Empirical distribution of the entity's own past values (integer cells)."""
    h = np.asarray(history, dtype=int)
    vals, counts = np.unique(h, return_counts=True)
    masses = counts / counts.sum()
    return vals.astype(float), masses


# ---------------------------------------------------------------------------
# Baseline B: Gaussian AR(1), discretised to integer cells (text-blind)
# ---------------------------------------------------------------------------
def _fit_ar1(history):
    x = np.asarray(history, dtype=float)
    if len(x) < 3:
        return float(x.mean()), 0.0, float(x.std() + 1e-6)
    mu = x.mean()
    xc = x - mu
    # phi = lag-1 autocorrelation (OLS through origin on centred series)
    num = np.sum(xc[:-1] * xc[1:])
    den = np.sum(xc[:-1] ** 2) + 1e-12
    phi = num / den
    phi = float(np.clip(phi, -0.98, 0.98))
    resid = xc[1:] - phi * xc[:-1]
    sigma = float(resid.std() + 1e-6)
    return mu, phi, sigma


def gaussian_ar1_forecast(history, horizon):
    """h-step AR(1) predictive: Gaussian(mean_h, var_h), discretised to cells."""
    mu, phi, sigma = _fit_ar1(history)
    x0 = float(history[-1])
    mean_h = mu + (phi ** horizon) * (x0 - mu)
    # var of h-step forecast: sigma^2 * sum_{k=0}^{h-1} phi^{2k}
    if abs(phi) < 1e-9:
        var_h = sigma ** 2
    else:
        var_h = sigma ** 2 * (1 - phi ** (2 * horizon)) / (1 - phi ** 2)
    sd = np.sqrt(var_h)
    # discretise onto integer cells within +-4 sd
    lo = int(np.floor(mean_h - 4 * sd))
    hi = int(np.ceil(mean_h + 4 * sd))
    cells = np.arange(lo, hi + 1)
    # mass of cell c = Phi(c+0.5) - Phi(c-0.5)
    from math import erf, sqrt
    def cdf(z):
        return 0.5 * (1 + erf((z - mean_h) / (sd * sqrt(2))))
    masses = np.array([cdf(c + 0.5) - cdf(c - 0.5) for c in cells])
    masses = np.clip(masses, 1e-12, None)
    masses /= masses.sum()
    return cells.astype(float), masses


# ---------------------------------------------------------------------------
# The Seldon-manifold-with-confidence forecaster
# ---------------------------------------------------------------------------
class SeldonConfidenceForecaster:
    """Reachable-set-plus-confidence forecaster with an optional text overlay.

    Learns, from the panel's history up to the cutoff (pooled across entities
    for a stable kernel), an empirical ONE-STEP innovation kernel: the
    distribution of integer deltas (x_{t+1} - x_t) conditioned on nothing
    (text-blind) — this is the manifold's propagation operator. Also learns the
    two regime-band centres by clustering observed levels into low/high bands so
    a text signal can name a target band.
    """

    def __init__(self, panel, cutoff, text_lead=None):
        self.panel = panel
        self.cutoff = cutoff
        self.text_lead = panel.lead if text_lead is None else text_lead
        self._learn_kernel()
        self._learn_bands()

    def _learn_kernel(self):
        # pooled one-step integer deltas over all entities, times <= cutoff
        s = self.panel.series[:, : self.cutoff + 1]
        deltas = np.diff(s, axis=1).ravel()
        vals, counts = np.unique(deltas, return_counts=True)
        self.kernel_vals = vals.astype(int)
        self.kernel_p = counts / counts.sum()

    def _learn_bands(self):
        # cluster observed levels into 2 bands via a simple midpoint split
        s = self.panel.series[:, : self.cutoff + 1].ravel()
        lo_c = float(np.percentile(s, 15))
        hi_c = float(np.percentile(s, 85))
        self.band_centres = np.array([lo_c, hi_c])

    def _propagate(self, start_cell, horizon):
        """Convolve the one-step kernel h times from a point mass at start_cell.

        Returns (cells, masses): the reachable set (support) and confidence mass.
        This IS the Seldon manifold support (reachable integer cells at horizon h)
        with the confidence dimension (stepped credence) attached.
        """
        # represent distribution as dict cell->mass, start as point mass
        dist = {int(start_cell): 1.0}
        for _ in range(horizon):
            nxt = {}
            for cell, m in dist.items():
                for dv, pk in zip(self.kernel_vals, self.kernel_p):
                    c2 = cell + int(dv)
                    nxt[c2] = nxt.get(c2, 0.0) + m * pk
            dist = nxt
        cells = np.array(sorted(dist.keys()), dtype=float)
        masses = np.array([dist[int(c)] for c in cells])
        return cells, masses

    @staticmethod
    def _foveate(cells, masses, keep=0.999):
        """Adaptive resolution: drop negligible tail cells (coarse where the
        answer can't change), renormalise. Keeps the smallest support covering
        `keep` of the mass. This is the foveation/temporal-resolution idea:
        spend representation where credence lives."""
        order = np.argsort(masses)[::-1]
        csum = np.cumsum(masses[order])
        n = int(np.searchsorted(csum, keep) + 1)
        n = min(n, len(cells))
        idx = np.sort(order[:n])
        c, m = cells[idx], masses[idx]
        m = m / m.sum()
        return c, m

    def _text_target_band(self, entity):
        """Most recent as-of token for this entity within its lead window.

        Strict as-of masking: only tokens with t <= cutoff. We also require the
        token to be recent enough that its announced switch could still be
        pending (t >= cutoff - lead), otherwise the switch has likely happened
        already and is baked into the current level.
        Returns incoming_regime in {0,1} or None.
        """
        toks = [
            tk for tk in self.panel.tokens_asof(self.cutoff)
            if tk.entity == entity and tk.t >= self.cutoff - self.text_lead
        ]
        if not toks:
            return None
        toks.sort(key=lambda tk: tk.t)
        return toks[-1].incoming_regime

    def forecast(self, entity, horizon, use_text=False):
        hist = self.panel.series[entity, : self.cutoff + 1]
        start = int(hist[-1])
        cells, masses = self._propagate(start, horizon)

        if use_text:
            band = self._text_target_band(entity)
            if band is not None:
                target = self.band_centres[band]
                # shift+sharpen the confidence mass toward the announced band:
                # build a second, text-conditioned distribution centred on the
                # target band and blend it in. The blend weight reflects how far
                # into the lead window we are (text is strong signal here).
                sd = max(1.0, float(self.panel.sigma) * 1.2)
                t_cells = np.arange(int(target - 4 * sd), int(target + 4 * sd) + 1)
                from math import erf, sqrt
                def cdf(z):
                    return 0.5 * (1 + erf((z - target) / (sd * sqrt(2))))
                t_mass = np.array([cdf(c + 0.5) - cdf(c - 0.5) for c in t_cells])
                t_mass = np.clip(t_mass, 1e-12, None)
                t_mass /= t_mass.sum()
                # union support
                all_cells = np.union1d(cells, t_cells.astype(float))
                base = dict(zip(cells, masses))
                text = dict(zip(t_cells.astype(float), t_mass))
                w = 0.6  # weight on the text-conditioned component
                blended = np.array([
                    (1 - w) * base.get(c, 0.0) + w * text.get(c, 0.0)
                    for c in all_cells
                ])
                blended /= blended.sum()
                cells, masses = all_cells, blended

        return self._foveate(cells, masses)
