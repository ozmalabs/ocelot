"""hat — the SENSE-HAT interface for the universal cortex.

The universal cortex (domains/cortex_loop.CortexLoop) is a single analysis-by-
synthesis engine: coarse-match -> adapt-style (coordinate descent) -> order-N
iterate -> readout argmin_content[ min_style residual ]. It is FRONT-END-AGNOSTIC:
it contains ZERO sense-specifics. Everything a sense needs lives behind this Hat
interface, the swappable part. One engine + many hats = the thesis.

A Hat provides three core methods (the sense's whole identity):

  · encode(raw) -> features          : turn a raw observation into the cortex's
                                        feature representation (its front end).
  · synth(content, style) -> features: the FORWARD MODEL — render the candidate
                                        `content` under `style`, in the SAME feature
                                        space encode() produces. This is the world
                                        the cortex controls; it is never inverted by
                                        a net, only re-rendered and re-compared.
  · compare(a, b) -> residual        : the METRIC — a residual (lower = closer)
                                        between two feature objects, evaluated by an
                                        OWNED graph op (no net, no fit). This is the
                                        loop's minimisation target.

Plus the search scaffolding the loop drives generically (no sense-specifics leak
into the loop):

  · contents()                        : the candidate content labels (e.g. words /
                                        shapes) the readout argmin ranges over.
  · style_init()                      : the neutral starting style (a dict of axes).
  · style_neighbours(style, stage)    : coordinate-descent neighbours of `style` at
                                        a coarse-to-fine `stage` — the discrete
                                        realisation of the continuous style axes. The
                                        loop hill-climbs these; the hat decides the
                                        axes and their step schedule.
  · library()                         : a prebuilt [(content, style, features)] set
                                        for the COARSE match (multi-start seeding).

DONKEY BOUNDARY: all sense-specifics (TTS, cochlea, rendering, the metric) live in
the Hat. The CortexLoop calls only the methods above and owns the search (order-N /
predict-subtract style adapt / argmin) — no net in the loop.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Sequence, Tuple


class Hat:
    """Abstract sense-hat. Subclasses implement the three core methods + the search
    scaffolding. The CortexLoop is written against THIS interface only."""

    name: str = "hat"

    # ---- the three core methods (a sense's whole identity) ----
    def encode(self, raw: Any) -> Any:
        """Raw observation -> cortex feature representation (the front end)."""
        raise NotImplementedError

    def synth(self, content: Any, style: Dict[str, Any]) -> Any:
        """The FORWARD MODEL: render `content` under `style` into feature space."""
        raise NotImplementedError

    def compare(self, a: Any, b: Any) -> float:
        """The METRIC: residual between two feature objects (lower = closer)."""
        raise NotImplementedError

    # ---- the search scaffolding the loop drives generically ----
    def contents(self) -> Sequence[Any]:
        """The candidate content labels the readout argmin ranges over."""
        raise NotImplementedError

    def style_init(self) -> Dict[str, Any]:
        """The neutral starting style (a dict of axes)."""
        raise NotImplementedError

    def style_neighbours(self, style: Dict[str, Any],
                         stage: int) -> Iterable[Dict[str, Any]]:
        """Coordinate-descent neighbours of `style` at coarse-to-fine `stage`."""
        raise NotImplementedError

    def n_stages(self) -> int:
        """How many coarse-to-fine stages style_neighbours supports."""
        return 2

    def library(self) -> List[Tuple[Any, Dict[str, Any], Any]]:
        """Prebuilt [(content, style, features)] for the coarse match (multi-start)."""
        raise NotImplementedError
