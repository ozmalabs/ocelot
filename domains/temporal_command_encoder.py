"""Deterministic temporal (sigma--delta) command encoding.

The encoder is deliberately agnostic about the plant and about the meaning of a
channel.  A controller can request a continuous value for each channel while an
actuator interface exposes only a fixed command alphabet.  Quantisation error is
carried into the next action, so a request between two alphabet entries is
represented by a deterministic sequence whose average converges to the request.

This is stateful by design.  :meth:`TemporalCommandEncoder.snapshot` is the
complete state needed to replay or branch an action sequence.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Sequence


@dataclass(frozen=True)
class TemporalEncoderSnapshot:
    """Serializable state of a :class:`TemporalCommandEncoder`."""

    step: int
    residuals: tuple[tuple[str, float], ...]
    requests: tuple[tuple[str, float], ...]

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation of this snapshot."""

        return {
            "step": self.step,
            "residuals": {name: value for name, value in self.residuals},
            "requests": {name: value for name, value in self.requests},
        }


class TemporalCommandEncoder:
    """Encode continuous channel requests into a fixed command alphabet.

    ``alphabet`` is ordered numerically and is shared by all channels.  Each
    channel has its own error accumulator; channels therefore cannot influence
    one another.  Requests outside the alphabet range are saturated before
    encoding.  ``tie_break`` declares which command is selected when a value is
    exactly halfway between adjacent commands (``"lower"`` or ``"upper"``).

    The accumulator invariant is useful to callers: after every action,
    ``sum(clamped_request - emitted_command)`` equals the channel residual and
    is bounded by half the largest adjacent alphabet gap.  Thus the long-run
    average error is zero for a constant request, while the instantaneous
    command remains in the declared alphabet.
    """

    def __init__(
        self,
        alphabet: Sequence[float],
        channels: Sequence[str],
        *,
        tie_break: str = "lower",
    ) -> None:
        values = tuple(float(value) for value in alphabet)
        if len(values) < 2:
            raise ValueError("alphabet must contain at least two commands")
        if any(not math.isfinite(value) for value in values):
            raise ValueError("alphabet commands must be finite")
        if any(left >= right for left, right in zip(values, values[1:])):
            raise ValueError("alphabet must be strictly increasing")
        names = tuple(channels)
        if not names or any(not isinstance(name, str) or not name for name in names):
            raise ValueError("channels must contain non-empty names")
        if len(set(names)) != len(names):
            raise ValueError("channels must be unique")
        if tie_break not in {"lower", "upper"}:
            raise ValueError("tie_break must be 'lower' or 'upper'")

        self.alphabet = values
        self.channels = names
        self.tie_break = tie_break
        self._residuals = {name: 0.0 for name in names}
        self._requests = {name: 0.0 for name in names}
        self._step = 0

    @property
    def step(self) -> int:
        """Number of actions emitted since construction or the last reset."""

        return self._step

    @property
    def error_bound(self) -> float:
        """Maximum absolute accumulated quantisation error per channel."""

        return max(right - left for left, right in zip(self.alphabet, self.alphabet[1:])) / 2.0

    @property
    def residuals(self) -> dict[str, float]:
        """A copy of each channel's accumulated request-minus-command error."""

        return dict(self._residuals)

    @property
    def last_requests(self) -> dict[str, float]:
        """The saturated requests used for the most recently emitted action."""

        return dict(self._requests)

    def encode(self, requests: Mapping[str, float]) -> dict[str, float]:
        """Emit one command per channel in the declared channel order.

        A missing channel holds its previous saturated request.  Unknown channel
        names are rejected, making accidental misspellings deterministic errors.
        """

        unknown = set(requests).difference(self.channels)
        if unknown:
            raise KeyError("unknown channel(s): " + ", ".join(sorted(unknown)))

        commands: dict[str, float] = {}
        for name in self.channels:
            if name in requests:
                request = float(requests[name])
                if not math.isfinite(request):
                    raise ValueError(f"request for {name!r} must be finite")
                request = min(self.alphabet[-1], max(self.alphabet[0], request))
                self._requests[name] = request
            request = self._requests[name]
            target = request + self._residuals[name]
            command = self._quantize(target)
            self._residuals[name] = target - command
            # Keep tiny round-off residues from becoming replay-visible drift.
            if abs(self._residuals[name]) < 1e-15:
                self._residuals[name] = 0.0
            commands[name] = command
        self._step += 1
        return commands

    def reset(self) -> None:
        """Clear all temporal state and return to step zero."""

        self._residuals = {name: 0.0 for name in self.channels}
        self._requests = {name: 0.0 for name in self.channels}
        self._step = 0

    def snapshot(self) -> TemporalEncoderSnapshot:
        """Capture complete deterministic state for replay or branching."""

        return TemporalEncoderSnapshot(
            step=self._step,
            residuals=tuple((name, self._residuals[name]) for name in self.channels),
            requests=tuple((name, self._requests[name]) for name in self.channels),
        )

    def restore(self, snapshot: TemporalEncoderSnapshot | Mapping[str, object]) -> None:
        """Restore a snapshot produced by :meth:`snapshot` or ``to_dict``."""

        if isinstance(snapshot, TemporalEncoderSnapshot):
            step = snapshot.step
            residuals = dict(snapshot.residuals)
            requests = dict(snapshot.requests)
        elif isinstance(snapshot, Mapping):
            try:
                step = int(snapshot["step"])
                residuals = dict(snapshot["residuals"])  # type: ignore[arg-type]
                requests = dict(snapshot["requests"])  # type: ignore[arg-type]
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError("invalid temporal encoder snapshot") from exc
        else:
            raise TypeError("snapshot must be TemporalEncoderSnapshot or mapping")

        if step < 0 or set(residuals) != set(self.channels) or set(requests) != set(self.channels):
            raise ValueError("snapshot does not match encoder channels")
        for name in self.channels:
            residual = float(residuals[name])
            request = float(requests[name])
            if not math.isfinite(residual) or not math.isfinite(request):
                raise ValueError("snapshot values must be finite")
            if request < self.alphabet[0] or request > self.alphabet[-1]:
                raise ValueError("snapshot request is outside the alphabet range")
        self._step = step
        self._residuals = {name: float(residuals[name]) for name in self.channels}
        self._requests = {name: float(requests[name]) for name in self.channels}

    def _quantize(self, target: float) -> float:
        """Nearest alphabet entry, with the configured deterministic tie rule."""

        if target <= self.alphabet[0]:
            return self.alphabet[0]
        if target >= self.alphabet[-1]:
            return self.alphabet[-1]
        for lower, upper in zip(self.alphabet, self.alphabet[1:]):
            if target <= upper:
                lower_distance = target - lower
                upper_distance = upper - target
                if lower_distance < upper_distance:
                    return lower
                if upper_distance < lower_distance:
                    return upper
                return lower if self.tie_break == "lower" else upper
        return self.alphabet[-1]  # pragma: no cover - bounds above are exhaustive


__all__ = ["TemporalCommandEncoder", "TemporalEncoderSnapshot"]
