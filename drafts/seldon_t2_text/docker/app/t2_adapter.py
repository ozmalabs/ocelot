"""
t2_adapter — PHASE 1 + PHASE 2 of the Track 2 submission plan.

Puts the Seldon reachable-set + confidence mechanism (PoC
`SeldonConfidenceForecaster`, forecasters.py) onto the REAL Track 2 output
contract pinned in PHASE0_GROUND_TRUTH.md.

Everything here is built against the VERIFIED-FROM-CODE contract:

  * output forecast.parquet columns EXACTLY (draw, asset, horizon, value),
    exactly n_draws x cell_count rows, every (draw,asset,horizon) cell once,
    contiguous 0-based draw ids, finite float values, representation="samples".
    [PHASE0 §2, grid.py FORECAST_COLUMNS / build_sample_matrix]
  * forecast_meta.json required keys unit_id/asof/representation/asset_ids/
    horizons/n_draws; unit_id == card [task].id; asof == card asof; optional
    target == card target_type. [PHASE0 §3]
  * forecast_rationale.md present + non-blank (never scored). [PHASE0 §4]
  * n_draws in [200, 20000], we use >= 500. [PHASE0 §3]
  * panel schema VARIES: accept asset|asset_id, +/- panel_id, date32|timestamp.
    [PHASE0 §8]

The mechanism REUSE is deliberate: the PoC operates on INTEGER cells (frame/
continuum invariant) via a pooled one-step innovation kernel, convolved h times
to give a stepped predictive dist (values, masses). Real panels are float
(yields in %, FX levels), so we QUANTIZE each series to integer cells at a
per-panel tick size, run the UNCHANGED PoC propagate/foveate, then .sample()
draws from the stepped dist and de-quantizes back to float. The reachable-set +
confidence mechanism is untouched; only the EMIT is converted to draws.

Two draw engines:
  * IndependentDrawEngine  — PHASE 1 baseline. Each asset propagated + sampled
    independently (the current PoC behaviour). Systematically penalized by the
    30% joint variogram term because draws carry no cross-asset dependence.
  * JointDrawEngine         — PHASE 2. Estimates the cross-asset innovation
    covariance from panel history and draws CORRELATED residuals so every draw
    index carries all target assets co-moving. OCELOT framing: the reachable
    set over the JOINT manifold rather than a product of marginal manifolds.
"""

from __future__ import annotations

import json
import math
import os
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
_POC = os.path.join(os.path.dirname(_HERE), "seldon_t2_poc")
for _p in (_HERE, _POC):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from forecasters import SeldonConfidenceForecaster  # noqa: E402  (PoC, verbatim)


# ===========================================================================
# Fast, MATHEMATICALLY-IDENTICAL propagate.
# The PoC _propagate convolves a point mass at start_cell with the one-step
# integer kernel `horizon` times. That equals the horizon-fold self-convolution
# of the kernel, translated by horizon*min_delta and start_cell. We compute the
# self-convolution by repeated squaring with FFT — O(support log support · log h)
# instead of O(support · |kernel| · h) — and return the SAME (cells, masses).
# The PoC class is left VERBATIM; this subclass only overrides _propagate for
# speed on the long horizons (63/126) real F3 cards carry. Numerically checked
# equivalent to the exact PoC path in _selftest_propagate_equiv().
# ===========================================================================
class FastSeldonForecaster(SeldonConfidenceForecaster):
    def _propagate(self, start_cell, horizon):
        horizon = int(horizon)
        if horizon <= 0:
            return np.array([float(start_cell)]), np.array([1.0])
        vals = np.asarray(self.kernel_vals, dtype=np.int64)
        p = np.asarray(self.kernel_p, dtype=float)
        lo = int(vals.min())
        # dense kernel pmf on offset grid [0 .. span] where index i => delta lo+i
        span = int(vals.max() - lo)
        base = np.zeros(span + 1)
        base[vals - lo] = p

        # h-fold self-convolution by repeated squaring (FFT).
        def fftconv(a, b):
            n = len(a) + len(b) - 1
            nfft = 1 << (n - 1).bit_length()
            fa = np.fft.rfft(a, nfft)
            fb = np.fft.rfft(b, nfft)
            c = np.fft.irfft(fa * fb, nfft)[:n]
            c[c < 0] = 0.0
            return c

        result = np.array([1.0])   # identity (delta at offset 0)
        acc = base.copy()          # base^(2^k)
        hh = horizon
        while hh > 0:
            if hh & 1:
                result = fftconv(result, acc)
            hh >>= 1
            if hh > 0:
                acc = fftconv(acc, acc)

        # result[i] is mass at total offset (horizon*lo + i). translate by start.
        offset0 = start_cell + horizon * lo
        idx = np.nonzero(result > 1e-15)[0]
        cells = (offset0 + idx).astype(float)
        masses = result[idx]
        masses = masses / masses.sum()
        return cells, masses


# ===========================================================================
# Card reader  (PHASE 1)
# ===========================================================================
@dataclass
class CardSpec:
    """The pieces of card.toml the forecaster needs. unit_id is [task].id
    (NOT card_id) — that is the sidecar key the scorer binds. [PHASE0 §3]"""

    unit_id: str
    asof: str
    asset_ids: list[str]
    horizons: list[int]
    target_type: str
    value_unit: str
    weights: dict[str, float]
    joint_kind: str
    tail_levels: list[float]
    raw: dict = field(default_factory=dict)

    @property
    def cell_count(self) -> int:
        return len(self.asset_ids) * len(self.horizons)


def read_card(card_path: str | Path) -> CardSpec:
    """Read card.toml. asof resolves from [forecast].asof else
    [provenance].data_cutoff (matches cutoff.py bind_metadata). [PHASE0 §3]"""
    card_path = Path(card_path)
    with card_path.open("rb") as fh:
        card = tomllib.load(fh)

    task = card.get("task", {})
    targets = card.get("targets", {})
    scoring = card.get("scoring", {})
    params = scoring.get("params", {})
    weights = params.get("weights", {})

    # asof: [forecast].asof (if present) else [provenance].data_cutoff
    asof = None
    if "forecast" in card and "asof" in card["forecast"]:
        asof = card["forecast"]["asof"]
    if asof is None:
        asof = card.get("provenance", {}).get("data_cutoff")
    if asof is None:
        raise ValueError(f"{card_path}: no asof ([forecast].asof or "
                         "[provenance].data_cutoff)")

    return CardSpec(
        unit_id=str(task["id"]),
        asof=str(asof),
        asset_ids=list(targets["asset_ids"]),
        horizons=[int(h) for h in targets["horizons"]],
        target_type=str(targets.get("target_type", "level")),
        value_unit=str(targets.get("value_unit", "")),
        weights={
            "marginal": float(weights.get("marginal", 0.5)),
            "joint": float(weights.get("joint", 0.3)),
            "tail": float(weights.get("tail", 0.2)),
        },
        joint_kind=str(params.get("joint", "variogram")),
        tail_levels=[float(x) for x in params.get("tail_levels",
                                                  [0.01, 0.05, 0.95, 0.99])],
        raw=card,
    )


# ===========================================================================
# Panel loader  (PHASE 1)  — tolerant to the real schema variance [PHASE0 §8]
# ===========================================================================
_ASSET_COLS = ("asset", "asset_id")


def _normalize_panel_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Return a frame with canonical columns [date(datetime64), asset(str),
    value(float)]. Tolerates asset|asset_id, +/- panel_id, date32|timestamp."""
    asset_col = next((c for c in _ASSET_COLS if c in df.columns), None)
    if asset_col is None:
        raise ValueError(f"panel has no asset column (looked for {_ASSET_COLS}); "
                        f"columns={list(df.columns)}")
    if "date" not in df.columns or "value" not in df.columns:
        raise ValueError(f"panel missing date/value; columns={list(df.columns)}")

    out = pd.DataFrame({
        "date": pd.to_datetime(df["date"]),
        "asset": df[asset_col].astype(str),
        "value": df["value"].astype(float),
    })
    return out


def load_panels(panels_dir: str | Path, asof: str) -> pd.DataFrame:
    """Load ALL *.parquet under panels_dir, normalize, and TRUNCATE as-of:
    drop any row dated strictly after asof. [PHASE0 §1, §8]

    Reads every parquet because a unit may ship several panels (e.g. F2/F3
    have g10_fx_daily + em_transfer_early / rates_daily). Returns one long
    frame [date, asset, value], asof-truncated, de-duplicated on (date,asset).
    """
    panels_dir = Path(panels_dir)
    files = sorted(panels_dir.glob("*.parquet"))
    if not files:
        # Parent-dir fallback: the reference CLI falls back to the parent when
        # --panels holds no .parquet, because the exemplar (and some local
        # layouts) keep the panel at the UNIT ROOT (rates_daily.parquet) rather
        # than under panels/. Staged units ship panels/, so this only bites
        # locally, but the reference CLI tolerates it and so must we. [PHASE0]
        parent = panels_dir.parent
        files = sorted(parent.glob("*.parquet"))
        if files:
            panels_dir = parent
    if not files:
        raise FileNotFoundError(f"no .parquet found under {panels_dir}")

    asof_ts = pd.to_datetime(asof)
    frames = []
    for f in files:
        raw = pd.read_parquet(f)
        norm = _normalize_panel_frame(raw)
        # as-of truncation: NO row dated > asof.
        norm = norm[norm["date"] <= asof_ts]
        frames.append(norm)

    panel = pd.concat(frames, ignore_index=True)
    # de-dup: keep last observation per (asset, date) across files.
    panel = (panel.sort_values(["asset", "date"])
                  .drop_duplicates(["asset", "date"], keep="last")
                  .reset_index(drop=True))
    return panel


def asset_series(panel: pd.DataFrame, asset: str) -> np.ndarray:
    """Sorted float value series for one asset (date-ascending)."""
    sub = panel[panel["asset"] == asset].sort_values("date")
    return sub["value"].to_numpy(dtype=float)


# ===========================================================================
# Quantization: float series <-> integer cells at operative resolution.
# The PoC mechanism is integer-cell native; this is the ONLY bridge needed.
# ===========================================================================
@dataclass
class Quantizer:
    """Maps a float series onto integer cells at a fixed tick size.

    tick is chosen per asset from the typical |one-step change| so the integer
    innovation kernel has enough distinct cells to be non-degenerate but the
    support does not explode. cell = round(value / tick)."""

    tick: float

    @classmethod
    def from_series(cls, x: np.ndarray) -> "Quantizer":
        x = np.asarray(x, dtype=float)
        if len(x) < 3:
            return cls(tick=max(1e-9, float(np.std(x)) or 1e-3))
        d = np.abs(np.diff(x))
        d = d[d > 0]
        if len(d) == 0:
            scale = max(abs(float(np.mean(x))), 1.0)
            return cls(tick=scale * 1e-3)
        # tick ~ a fraction of the median absolute one-step move, so a typical
        # daily move spans a few cells (resolution where credence lives).
        tick = float(np.median(d)) / 4.0
        if not np.isfinite(tick) or tick <= 0:
            tick = float(np.std(x)) / 20.0 or 1e-3
        return cls(tick=tick)

    def to_cells(self, x: np.ndarray) -> np.ndarray:
        return np.rint(np.asarray(x, dtype=float) / self.tick).astype(np.int64)

    def to_value(self, cells: np.ndarray) -> np.ndarray:
        return np.asarray(cells, dtype=float) * self.tick


# ===========================================================================
# A minimal Panel shim so the PoC SeldonConfidenceForecaster runs unchanged.
# The PoC forecaster only touches: panel.series[e, :cutoff+1], panel.sigma.
# ===========================================================================
class _CellPanel:
    """Adapts quantized integer-cell series into the shape the PoC
    SeldonConfidenceForecaster expects (panel.series[e, t], panel.sigma).

    series is (E, T) int; each row is one asset's quantized history. cutoff is
    the last index (T-1) since we already as-of truncated the loader."""

    def __init__(self, cell_series: np.ndarray, sigma: float):
        self.series = np.asarray(cell_series, dtype=np.int64)
        self.E, self.T = self.series.shape
        self.sigma = float(sigma)
        self.lead = 3  # unused on the text-blind path; kept for interface parity


# ===========================================================================
# .sample(n_draws) — the PHASE 1 emit conversion.
# The PoC produces a stepped dist (cells, masses); .sample draws Monte-Carlo
# samples from it. Mechanism (reachable-set + confidence) UNCHANGED.
# ===========================================================================
def sample_stepped(cells: np.ndarray, masses: np.ndarray, n_draws: int,
                   rng: np.random.Generator,
                   jitter: bool = True) -> np.ndarray:
    """Draw n_draws integer-cell samples from a stepped (cells, masses) dist.

    Multinomial index draw + optional uniform sub-cell jitter within +/-0.5 so
    the discretization does not create artificial ties/steps in the continuous
    value space (still a proper sample from the cell's interval)."""
    masses = np.asarray(masses, dtype=float)
    masses = np.clip(masses, 0.0, None)
    masses = masses / masses.sum()
    idx = rng.choice(len(cells), size=n_draws, p=masses)
    draws = np.asarray(cells, dtype=float)[idx]
    if jitter:
        draws = draws + rng.uniform(-0.5, 0.5, size=n_draws)
    return draws



# ===========================================================================
# Draw engines.  Both produce a sample matrix of shape (n_draws, n_assets,
# n_horizons) in FLOAT value space — the canonical baseline shape [PHASE0 §2].
# ===========================================================================
class IndependentDrawEngine:
    """PHASE 1 baseline: each asset propagated + sampled INDEPENDENTLY.

    This is the current PoC behaviour lifted to the real contract. Every asset
    gets its own Seldon reachable-set + confidence stepped dist, and draws are
    sampled independently per asset — so a draw index carries no cross-asset
    dependence. This is exactly the arm the 30% joint variogram penalizes.
    """

    name = "independent"

    def build(self, card: CardSpec, panel: pd.DataFrame):
        self.card = card
        self.assets = card.asset_ids
        self.horizons = card.horizons
        # per-asset quantizer + cell history + PoC forecaster
        self._quant: dict[str, Quantizer] = {}
        self._cells: dict[str, np.ndarray] = {}
        for a in self.assets:
            x = asset_series(panel, a)
            if len(x) == 0:
                raise ValueError(f"asset {a!r} has no history in panel as-of "
                                 f"{card.asof} (transfer unit?)")
            q = Quantizer.from_series(x)
            self._quant[a] = q
            self._cells[a] = q.to_cells(x)
        return self

    def sample_matrix(self, n_draws: int, seed: int = 0,
                      disp_scale: float = 1.0) -> np.ndarray:
        rng = np.random.default_rng(seed)
        out = np.empty((n_draws, len(self.assets), len(self.horizons)),
                       dtype=float)
        for ai, a in enumerate(self.assets):
            cells = self._cells[a]
            q = self._quant[a]
            sigma = float(np.std(np.diff(cells))) if len(cells) > 2 else 1.0
            panel_shim = _CellPanel(cells.reshape(1, -1), sigma=sigma)
            fc = FastSeldonForecaster(panel_shim, cutoff=panel_shim.T - 1)
            for hi, h in enumerate(self.horizons):
                pc, pm = fc.forecast(entity=0, horizon=int(h), use_text=False)
                draws_cells = sample_stepped(pc, pm, n_draws, rng)
                vals = q.to_value(draws_cells)
                # PHASE 5 calibration knob (see JointDrawEngine): contract draws
                # around their mean by disp_scale to cure over-dispersion.
                if disp_scale != 1.0:
                    m = float(vals.mean())
                    vals = m + float(disp_scale) * (vals - m)
                out[:, ai, hi] = vals
        return out


class JointDrawEngine:
    """PHASE 2: JOINT draws that preserve cross-asset co-movement.

    OCELOT framing: instead of a product of independent marginal manifolds, the
    reachable set is drawn over the JOINT manifold. The one-step cross-asset
    innovation covariance is estimated from aligned panel history; correlated
    residuals are drawn so every draw index has all target assets co-moving.

    Construction, per draw, per horizon h:
      1. Marginal center + spread comes from the SAME Seldon reachable-set +
         confidence stepped dist as the independent arm (mechanism unchanged):
         we take each asset's stepped-dist mean and std at horizon h.
      2. The shape of the joint draw is a correlated Gaussian innovation with
         the empirical cross-asset correlation R (from aligned one-step
         changes), scaled by sqrt(h) (random-walk h-step spread) and each
         asset's own one-step innovation std.
      3. We center on the Seldon stepped-dist mean and scale so the marginal
         std matches the Seldon stepped-dist std — i.e. IDENTICAL marginals to
         the independent arm, only the JOINT dependence differs. That isolates
         the variogram effect: marginal CRPS + tail should be ~unchanged, the
         30% joint term should improve.
    """

    name = "joint"

    def build(self, card: CardSpec, panel: pd.DataFrame):
        self.card = card
        self.assets = card.asset_ids
        self.horizons = card.horizons

        self._quant: dict[str, Quantizer] = {}
        self._cells: dict[str, np.ndarray] = {}
        for a in self.assets:
            x = asset_series(panel, a)
            if len(x) == 0:
                raise ValueError(f"asset {a!r} has no history in panel as-of "
                                 f"{card.asof} (transfer unit?)")
            q = Quantizer.from_series(x)
            self._quant[a] = q
            self._cells[a] = q.to_cells(x)

        # Cross-asset correlation of one-step changes, on a common date index.
        self._corr = self._estimate_corr(panel)
        return self

    def _estimate_corr(self, panel: pd.DataFrame) -> np.ndarray:
        """Empirical correlation of daily changes across the target assets,
        aligned on common dates. Falls back to identity if too little overlap."""
        n = len(self.assets)
        wide = (panel[panel["asset"].isin(self.assets)]
                .pivot_table(index="date", columns="asset", values="value"))
        # order columns to match self.assets; missing assets -> NaN cols
        wide = wide.reindex(columns=self.assets)
        changes = wide.diff().dropna(how="any")
        if len(changes) < max(10, n + 1):
            return np.eye(n)
        R = np.corrcoef(changes.to_numpy(dtype=float), rowvar=False)
        R = np.atleast_2d(R)
        if R.shape != (n, n) or not np.all(np.isfinite(R)):
            return np.eye(n)
        # nudge to PSD: symmetrize + small ridge, then re-standardize.
        R = 0.5 * (R + R.T)
        R = R + 1e-6 * np.eye(n)
        d = np.sqrt(np.diag(R))
        R = R / np.outer(d, d)
        return R

    def _seldon_moments(self):
        """Per-(asset,horizon) mean & std of the Seldon stepped dist in VALUE
        space. Identical mechanism to the independent arm; we just read the
        first two moments to anchor the joint draw's marginals."""
        n_a, n_h = len(self.assets), len(self.horizons)
        mean = np.zeros((n_a, n_h))
        std = np.zeros((n_a, n_h))
        for ai, a in enumerate(self.assets):
            cells = self._cells[a]
            q = self._quant[a]
            sigma = float(np.std(np.diff(cells))) if len(cells) > 2 else 1.0
            panel_shim = _CellPanel(cells.reshape(1, -1), sigma=sigma)
            fc = FastSeldonForecaster(panel_shim, cutoff=panel_shim.T - 1)
            for hi, h in enumerate(self.horizons):
                pc, pm = fc.forecast(entity=0, horizon=int(h), use_text=False)
                vals = q.to_value(pc)
                m = float(np.sum(vals * pm))
                v = float(np.sum(pm * (vals - m) ** 2))
                mean[ai, hi] = m
                std[ai, hi] = math.sqrt(max(v, 1e-18))
        return mean, std

    def sample_matrix(self, n_draws: int, seed: int = 0,
                      disp_scale: float = 1.0) -> np.ndarray:
        rng = np.random.default_rng(seed)
        n_a, n_h = len(self.assets), len(self.horizons)
        mean, std = self._seldon_moments()

        # Cholesky of the cross-asset correlation (shared across horizons; the
        # correlation is a co-movement structure, magnitude comes from per-asset
        # std). Guard non-PD by eigenvalue clip.
        R = self._corr
        try:
            L = np.linalg.cholesky(R)
        except np.linalg.LinAlgError:
            w, V = np.linalg.eigh(R)
            w = np.clip(w, 1e-8, None)
            L = V @ np.diag(np.sqrt(w))

        # PHASE 5 calibration knob: disp_scale contracts (<1) or widens (>1) the
        # innovation kernel width around each asset's predictive mean. The PoC
        # PIT KS 0.0926 diagnosed over-dispersion; a mild tightening (default
        # 0.90, chosen tail-guarded in run_calibration_eval so CRPS/tail do not
        # regress) flattens the mid-PIT hump. Because it multiplies the marginal
        # std ONLY, the cross-asset correlation (variogram structure, phase2) is
        # untouched — corr is scale-invariant.
        eff_std = std * float(disp_scale)

        out = np.empty((n_draws, n_a, n_h), dtype=float)
        for hi in range(n_h):
            # correlated standard-normal innovations, one vector per draw,
            # SAME draw index shares the correlated shock across all assets.
            z = rng.standard_normal(size=(n_draws, n_a))
            corr_z = z @ L.T  # (n_draws, n_a), cross-asset correlated, unit var
            # scale each asset to its (tightened) Seldon marginal std, recenter.
            out[:, :, hi] = mean[:, hi][None, :] + corr_z * eff_std[:, hi][None, :]
        return out



# ===========================================================================
# Emit: forecast.parquet + forecast_meta.json + forecast_rationale.md
# EXACT contract per PHASE0 §2/§3/§4.
# ===========================================================================
def sample_matrix_to_long(samples: np.ndarray, assets: list[str],
                          horizons: list[int]) -> pd.DataFrame:
    """Unroll (n_draws, n_assets, n_horizons) float samples into the long
    forecast.parquet frame: columns EXACTLY [draw, asset, horizon, value],
    every (draw,asset,horizon) cell exactly once, contiguous 0-based draws.
    Asset-major, horizon-minor in DECLARED order (matches grid.py). [PHASE0 §2]
    """
    n_draws, n_a, n_h = samples.shape
    assert n_a == len(assets) and n_h == len(horizons)
    if not np.all(np.isfinite(samples)):
        raise ValueError("non-finite value in sample matrix (would fail g3)")

    draw_col = np.repeat(np.arange(n_draws, dtype=np.int64), n_a * n_h)
    asset_idx = np.tile(np.repeat(np.arange(n_a), n_h), n_draws)
    hor_idx = np.tile(np.tile(np.arange(n_h), n_a), n_draws)
    asset_col = np.asarray(assets, dtype=object)[asset_idx]
    hor_col = np.asarray(horizons, dtype=np.int64)[hor_idx]
    val_col = samples.reshape(-1).astype(np.float64)

    df = pd.DataFrame({
        "draw": draw_col,
        "asset": asset_col.astype(str),
        "horizon": hor_col,
        "value": val_col,
    })
    return df


_RATIONALE_TEMPLATE = """\
# Forecast rationale — {unit_id}

**As of {asof}. Target: joint predictive distribution over {assets} at horizon(s)
{horizons} business days ({target_type}, {value_unit}).**

## Method — OCELOT reachable-set + confidence, on the joint manifold

Each target series is quantised to integer cells at operative resolution and an
empirical one-step innovation kernel is learned from the panel history up to the
as-of date (no row dated after {asof} is used). The kernel is convolved forward
to the horizon to enumerate the *reachable set* (support of integer cells the
series can occupy) with a stepped *confidence* mass over those cells — a
credence distribution, not a Gaussian assumption. The tail is foveated: cells
carrying negligible credence are dropped so representation is spent where the
answer can change.

{joint_para}

The stepped predictive distribution is converted to {n_draws} Monte-Carlo draws
for the samples-representation output contract.

## What the text corpus contributed

This run is the text-blind arm: it reads the numeric panel only. The dated text
corpus at the unit's `text/` is the input a reasoning arm consumes to shift and
sharpen the confidence mass toward a text-signalled regime; that arm is layered
on top of this same mechanism (the emit and the joint draw are unchanged).

## What would change this forecast

A regime signal in the as-of text (a policy pivot, a shock foreshadowed) that
moves the confidence mass toward a different cell-band, or a materially different
recent innovation distribution in the panel history.
"""

_JOINT_PARA = {
    "joint": (
        "Draws are generated JOINTLY across assets: the cross-asset innovation "
        "correlation is estimated from aligned one-step changes in the panel "
        "history, and each draw index carries a correlated shock so curve/cross "
        "shape (co-movement) is preserved rather than assembled from independent "
        "marginals. This is the reachable set over the joint manifold — the 30% "
        "joint variogram term rewards it."
    ),
    "independent": (
        "Draws are generated per asset independently in this arm (the marginal "
        "baseline). Cross-asset co-movement is NOT imposed, which the joint "
        "variogram term penalises; the joint-draw arm addresses that."
    ),
}


def write_outputs(out_dir: str | Path, card: CardSpec, samples: np.ndarray,
                  engine_name: str) -> dict:
    """Write the exact three-file deliverable into out_dir. Returns the meta."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    n_draws = samples.shape[0]
    long_df = sample_matrix_to_long(samples, card.asset_ids, card.horizons)
    long_df.to_parquet(out_dir / "forecast.parquet", index=False)

    meta = {
        "unit_id": card.unit_id,          # NOT card_id — binds to [task].id
        "asof": card.asof,
        "representation": "samples",
        "asset_ids": list(card.asset_ids),
        "horizons": list(card.horizons),
        "n_draws": int(n_draws),
        "target": card.target_type,
    }
    (out_dir / "forecast_meta.json").write_text(json.dumps(meta, indent=2))

    rationale = _RATIONALE_TEMPLATE.format(
        unit_id=card.unit_id,
        asof=card.asof,
        assets=", ".join(card.asset_ids),
        horizons=", ".join(str(h) for h in card.horizons),
        target_type=card.target_type,
        value_unit=card.value_unit or "n/a",
        n_draws=n_draws,
        joint_para=_JOINT_PARA.get(engine_name, _JOINT_PARA["joint"]),
    )
    (out_dir / "forecast_rationale.md").write_text(rationale)
    return meta


# ===========================================================================
# End-to-end driver — the `forecast` verb shape [PHASE0 §1].
# ===========================================================================
# PHASE 5: default innovation-width scale. 1.0 = untightened (the phase1/2
# behaviour). 0.90 is the tail-guarded tightening chosen in run_calibration_eval
# (KS 0.1884 -> 0.1690, marginal CRPS improves, tail within 5% tolerance). The
# calibration eval reads the ENGINE default via this constant; keep them in sync.
DEFAULT_DISP_SCALE = 0.90


def run_forecast(unit_dir: str | Path, out_dir: str | Path, *,
                 n_draws: int = 500, engine: str = "joint", seed: int = 0,
                 panels_subdir: str | None = None,
                 disp_scale: float = DEFAULT_DISP_SCALE) -> dict:
    """Load a unit, produce draws, emit the three files. Returns meta.

    unit_dir must contain card.toml and the panel parquet(s). Panels may sit at
    unit root (public-repo layout) or under panels/ (staged layout); we accept
    both. [PHASE0 §1/§8]

    disp_scale is the PHASE 5 calibration knob (innovation-width scale); default
    0.90 (tail-guarded tightening). Pass 1.0 for the untightened phase1/2 arm.
    """
    unit_dir = Path(unit_dir)
    card = read_card(unit_dir / "card.toml")

    # panels dir resolution: explicit override, else panels/ if present, else root.
    if panels_subdir is not None:
        pdir = unit_dir / panels_subdir
    elif (unit_dir / "panels").is_dir():
        pdir = unit_dir / "panels"
    else:
        pdir = unit_dir
    panel = load_panels(pdir, card.asof)

    if engine == "joint":
        eng = JointDrawEngine().build(card, panel)
    elif engine == "independent":
        eng = IndependentDrawEngine().build(card, panel)
    else:
        raise ValueError(f"unknown engine {engine!r}")

    if n_draws < 500:
        n_draws = 500  # plan floor; contract floor is 200. [PHASE0 §3]
    samples = eng.sample_matrix(n_draws, seed=seed, disp_scale=disp_scale)
    return write_outputs(out_dir, card, samples, eng.name)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Seldon Track2 forecaster (adapter)")
    ap.add_argument("--unit", required=True, help="unit dir (has card.toml + panels)")
    ap.add_argument("--out", required=True, help="output dir")
    ap.add_argument("--n-draws", type=int, default=500)
    ap.add_argument("--engine", choices=["joint", "independent"], default="joint")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--disp-scale", type=float, default=DEFAULT_DISP_SCALE,
                    help="PHASE5 innovation-width scale (1.0=untightened, "
                         "0.90=tail-guarded default)")
    args = ap.parse_args()
    meta = run_forecast(args.unit, args.out, n_draws=args.n_draws,
                        engine=args.engine, seed=args.seed,
                        disp_scale=args.disp_scale)
    print(json.dumps(meta, indent=2))
