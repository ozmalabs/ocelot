"""
Synthetic time-series panel with a known generating process, plus a timestamped
text corpus that carries GENUINE advance information about the future.

Why synthetic: a calibration study needs known ground truth, and a text-uplift
study needs text that provably carries signal (so a null result means "the
mechanism failed", not "the text was uninformative"). Synthetic-with-known-DGP
is the right instrument for a mechanism PoC, and we say so plainly in the report.

Generating process (per entity): a two-regime mean-reverting (AR(1)) series.
  - Regime 0: mean mu0, Regime 1: mean mu1 (mu1 != mu0).
  - x_{t+1} = mu_regime + phi * (x_t - mu_regime) + eps,  eps ~ N(0, sigma^2).
  - Regime switches happen at random times (Poisson-ish via per-step hazard).

The observation is INTEGER at operative resolution (frame/continuum invariant):
we round the latent real series to the nearest integer "cell". So the panel the
forecaster ever sees is integer-valued, exactly as an OCELOT frame would hold it.

The text corpus: a regime switch scheduled to occur at time t_switch emits a
"signal token" at time t_switch - lead (lead >= 1), timestamped. The token names
the entity and the incoming regime. With probability `text_recall` the token is
actually emitted (some switches are unannounced); with probability `text_noise`
a spurious token is emitted with no real switch behind it. This makes the text
imperfect but genuinely informative, and lets strict as-of masking bite: a token
timestamped after the cutoff must not be used.

Everything is seeded and deterministic given a seed.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class TextToken:
    t: int              # timestamp (integer time index)
    entity: int
    incoming_regime: int  # the regime the entity is about to switch INTO
    spurious: bool        # True if this token has no real switch behind it


@dataclass
class Panel:
    # series[entity] = integer-valued observed series, length T
    series: np.ndarray            # shape (E, T), int
    latent: np.ndarray            # shape (E, T), float (pre-rounding, for diagnostics)
    regimes: np.ndarray           # shape (E, T), int in {0,1}, true regime at each t
    tokens: list                  # list[TextToken], the full text corpus
    mu: np.ndarray                # shape (2,), regime means
    phi: float
    sigma: float
    E: int
    T: int
    lead: int
    meta: dict = field(default_factory=dict)

    def tokens_asof(self, cutoff):
        """Strict as-of masking: only tokens with timestamp <= cutoff."""
        return [tk for tk in self.tokens if tk.t <= cutoff]


def generate_panel(
    n_entities=40,
    T=300,
    mu=(0.0, 8.0),
    phi=0.6,
    sigma=1.0,
    switch_hazard=0.02,
    lead=3,
    text_recall=0.85,
    text_noise=0.10,
    seed=0,
):
    """Generate a regime-switching integer panel + timestamped text corpus."""
    rng = np.random.default_rng(seed)
    mu = np.asarray(mu, dtype=float)
    E = n_entities

    latent = np.zeros((E, T), dtype=float)
    regimes = np.zeros((E, T), dtype=int)
    tokens: list[TextToken] = []

    for e in range(E):
        reg = int(rng.integers(0, 2))
        x = mu[reg] + rng.normal(0, sigma)
        # Pre-schedule switches so we can emit a LEAD token before each.
        # Walk forward deciding switches by hazard; record switch times.
        switch_times = {}  # t -> incoming regime
        cur = reg
        for t in range(1, T):
            if rng.random() < switch_hazard:
                nxt = 1 - cur
                switch_times[t] = nxt
                cur = nxt
        # Emit lead tokens (with recall/noise) for each real switch
        for t_sw, inc in switch_times.items():
            emit_t = t_sw - lead
            if emit_t >= 0 and rng.random() < text_recall:
                tokens.append(TextToken(t=emit_t, entity=e, incoming_regime=inc, spurious=False))
        # Spurious tokens: sprinkle a few false alarms
        n_spurious = rng.poisson(text_noise * len(switch_times) + 0.5)
        for _ in range(n_spurious):
            et = int(rng.integers(0, max(1, T - 1)))
            fake_inc = int(rng.integers(0, 2))
            tokens.append(TextToken(t=et, entity=e, incoming_regime=fake_inc, spurious=True))

        # Now simulate the actual series applying the scheduled switches
        cur = reg
        regimes[e, 0] = cur
        latent[e, 0] = x
        for t in range(1, T):
            if t in switch_times:
                cur = switch_times[t]
            regimes[e, t] = cur
            x = mu[cur] + phi * (x - mu[cur]) + rng.normal(0, sigma)
            latent[e, t] = x

    series = np.rint(latent).astype(int)  # integer cells (operative resolution)

    return Panel(
        series=series,
        latent=latent,
        regimes=regimes,
        tokens=tokens,
        mu=mu,
        phi=phi,
        sigma=sigma,
        E=E,
        T=T,
        lead=lead,
        meta=dict(
            switch_hazard=switch_hazard,
            text_recall=text_recall,
            text_noise=text_noise,
            seed=seed,
        ),
    )


if __name__ == "__main__":
    p = generate_panel(seed=1)
    n_real = sum(1 for t in p.tokens if not t.spurious)
    n_spur = sum(1 for t in p.tokens if t.spurious)
    print(f"Panel: {p.E} entities x {p.T} steps, integer range "
          f"[{p.series.min()}, {p.series.max()}]")
    print(f"Regime means mu={p.mu.tolist()}, phi={p.phi}, sigma={p.sigma}, lead={p.lead}")
    print(f"Text corpus: {len(p.tokens)} tokens ({n_real} real-switch, {n_spur} spurious)")
    # sanity: how many switches total
    switches = int((np.diff(p.regimes, axis=1) != 0).sum())
    print(f"Total regime switches across panel: {switches}")
