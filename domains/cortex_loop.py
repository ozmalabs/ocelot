"""cortex_loop — the UNIVERSAL CORTEX: one front-end-AGNOSTIC analysis-by-synthesis
loop, driven entirely through a swappable sense-Hat (domains/hat.Hat).

This is the validated Phase-C loop (scripts/universal_loop_phaseC.py) refactored to
contain ZERO sense-specifics. It calls ONLY hat.encode / hat.synth / hat.compare and
the hat's generic search scaffolding (contents / style_init / style_neighbours /
library). The same code runs on ANY hat (audio, toy-objects, ...) — swap the hat,
the cortex is unchanged. One engine + many sense-hats + plasticity = the thesis.

The loop, per heard observation H (already a raw observation the hat will encode):

  1. COARSE MATCH. Rank the hat's prebuilt (content, style) library by hat.compare to
     H's features; take the top-k candidate CONTENTS, each seeded from its best library
     style (multi-start -> dodges local minima).
  2. ADAPT-STYLE (the nonlinear lever). For each candidate content C, ADAPT the style
     S by OWNED coordinate descent over the hat's style axes to MINIMISE
     compare(H, synth(C, S)). Live re-synth via the hat at each step (the forward model
     inverted by search, never a linear approximation).
  3. ITERATE (order-N). A couple of refine passes; residual monotonicity tracked.
  4. READOUT. recognised content = argmin_C [ min_S compare(H, synth(C, S_adapted)) ].
     The style S is INFERRED (the per-content best-fitting style) and FACTORED OUT ->
     style-invariant BY CONSTRUCTION.

DONKEY BOUNDARY: the loop owns coarse-match / adapt / iterate / argmin — a coordinate
search + residual-min over the hat's OWNED compare. NO net, NO fit, NO gradient in the
loop. The only world calls are hat.synth (re-render) and hat.encode (front end). The
metric (compare) is the hat's owned graph op. Held-out test items never bias the loop.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from domains.hat import Hat


class CortexLoop:
    """The universal analysis-by-synthesis cortex. Holds only a Hat + search budgets;
    no sense-specifics. recognise(raw) -> (content, per_content_residual, curves)."""

    def __init__(self, hat: Hat, max_synths_per_content: int = 8,
                 n_passes: int = 2, k: int = 3):
        self.hat = hat
        self.max_synths = max_synths_per_content
        self.n_passes = n_passes
        self.k = k
        self.n_synths = 0          # world-call (synth) accounting

    # ---- the OWNED residual: compare(H_feats, synth(C, S)) ----
    def _residual(self, h_feats: Any, content: Any, style: Dict[str, Any]) -> float:
        cand = self.hat.synth(content, style)
        self.n_synths += 1
        if cand is None:
            return float("inf")
        return float(self.hat.compare(h_feats, cand))

    # ---- COARSE MATCH: top-k candidate (content, seed-style) from the library ----
    def _coarse_topk(self, h_feats: Any) -> List[Tuple[Any, Dict[str, Any]]]:
        best_per_content: Dict[Any, Tuple[float, Dict[str, Any]]] = {}
        for (content, style, feats) in self.hat.library():
            d = float(self.hat.compare(h_feats, feats))
            cur = best_per_content.get(content)
            if cur is None or d < cur[0]:
                best_per_content[content] = (d, style)
        ranked = sorted(best_per_content.items(), key=lambda kv: kv[1][0])
        return [(c, st) for (c, (d, st)) in ranked[:self.k]]

    # ---- ADAPT-STYLE: coordinate descent over the hat's style axes, live synth ----
    def _adapt_style(self, h_feats: Any, content: Any, s0: Dict[str, Any],
                     budget: int) -> Tuple[float, Dict[str, Any], List[float]]:
        """Minimise compare(H, synth(content, S)) by OWNED coarse-to-fine coordinate
        descent over the hat's style neighbours. Returns (best_resid, best_style,
        curve). Caps at `budget` synths. The nonlinear inversion: it searches the real
        forward model, never a linear feature approximation."""
        style = dict(s0)
        best = self._residual(h_feats, content, style)
        curve = [best]
        used = 1
        for stage in range(self.hat.n_stages()):
            improved = True
            while improved and used < budget:
                improved = False
                for cand_style in self.hat.style_neighbours(style, stage):
                    if used >= budget:
                        break
                    r = self._residual(h_feats, content, cand_style)
                    used += 1
                    if r < best - 1e-9:
                        best, style = r, dict(cand_style)
                        curve.append(best)
                        improved = True
                        break
        return best, style, curve

    # ---- the full loop on one heard observation ----
    def recognise(self, raw: Any) -> Tuple[Any, Dict[Any, float], Dict[Any, List[float]]]:
        """argmin_C [ min_S compare(H, synth(C, S_adapted)) ] with the order-N iterate.
        Returns (content, per_content_best_resid, adapt_curves)."""
        h_feats = self.hat.encode(raw)
        cands = self._coarse_topk(h_feats)
        per_content: Dict[Any, float] = {}
        curves: Dict[Any, List[float]] = {}
        per_pass = max(2, self.max_synths // self.n_passes)
        for (content, s0) in cands:
            style = dict(s0)
            best_resid = self._residual(h_feats, content, style)
            content_curve = [best_resid]
            for _pass in range(self.n_passes):          # order-N refine passes
                r, style, curve = self._adapt_style(h_feats, content, style, per_pass)
                if r < best_resid - 1e-9:
                    best_resid = r
                content_curve.extend(curve[1:])
            per_content[content] = best_resid
            curves[content] = content_curve
        content = (min(per_content.items(), key=lambda kv: kv[1])[0]
                   if per_content else None)
        return content, per_content, curves
