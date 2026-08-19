"""Purely observational flicker metrics for generic control traces.

This module deliberately knows nothing about an airframe, a controller, or the
graph substrate.  A trace is an iterable of per-action mappings.  The reducer
only reads those mappings and returns transition counts; it never writes to a
record or infers a new regime.  This makes it suitable for comparing the same
episode manifest across controller arms.

The default names are intentionally small and generic.  A consumer with a
different vocabulary can pass explicit field names to :func:`reduce_trace`.
Missing fields are ignored (rather than treated as a transition to ``None``),
so adding one diagnostic field halfway through a run does not manufacture
flicker.

``ordinal_transitions_per_action`` uses the number of supplied records as its
denominator.  ``*_transition_boundaries`` exposes the number of adjacent
observed pairs as well, making the convention unambiguous for short traces.
Lag is directed: for every confirmed/condensed/model/program transition, the
most recent instantaneous-ordinal transition at or before that action is used.
Thus lag ``0`` is an action-coincident transition, and a positive lag says how
many actions the selection/state transition followed the ordinal transition.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
import math
from typing import Any, Iterable, Mapping, Sequence


# The aliases cover generic controller traces as well as the names used by the
# current embodied-control consumers.  Explicit field arguments should be
# preferred when a trace contains more than one notion of "ordinal".
INSTANTANEOUS_ORDINAL_FIELDS = (
    "instantaneous_ordinal",
    "instantaneous_surprise_ordinal",
    "instantaneous_residual_ordinal",
    "surprise_ordinal",
    "residual_ordinal",
    "current_surprise_ordinal",
    "surprise_shape_ordinal",
)
CONFIRMED_ORDINAL_FIELDS = (
    "confirmed_ordinal",
    "confirmed_regime_ordinal",
    "active_residual_regime_ordinal",
    # The generic control-regime trace currently calls its published state
    # simply `regime_ordinal`; it is a fallback, not an instantaneous signal.
    "regime_ordinal",
)
CONDENSED_FIELDS = (
    "condensed_ordinal",
    "condensed_surprise_ordinal",
    "condensed_regime_ordinal",
    "condensed",
    "is_condensed",
)
MODEL_FIELDS = (
    "selected_model_id",
    "selected_model",
    "active_model_id",
    "active_model",
    "selected_regime_local_model",
    "model_selection",
)
PROGRAM_FIELDS = (
    "selected_program_id",
    "selected_program",
    "active_program_id",
    "active_program",
    "program_selection",
    "selected_program_members",
    "program_members",
    "tokens",
)


def _first(mapping: Mapping[str, Any], fields: Sequence[str]) -> tuple[bool, Any]:
    """Return the first present field, preserving falsey values."""

    for field in fields:
        if field in mapping and mapping[field] is not None:
            return True, mapping[field]
    return False, None


def _normalise_number(value: Any) -> Any:
    """Make integer-like ordinals compare identically across JSON producers."""

    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        value = float(value)
        if not math.isfinite(value):
            return None
        if value.is_integer():
            return int(value)
        return value
    return value


def _freeze(value: Any) -> Any:
    """Convert JSON-like identities into deterministic, hashable values."""

    if isinstance(value, Mapping):
        return tuple(sorted((str(key), _freeze(item)) for key, item in value.items()))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, set):
        return tuple(sorted((_freeze(item) for item in value), key=repr))
    value = _normalise_number(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    # A trace identity should be serialisable.  repr is a deterministic and
    # non-invasive fallback for a caller that supplied an opaque token object.
    return repr(value)


def _identity(value: Any) -> Any:
    """Canonicalise a selected model/program identity without mutating it."""

    return _freeze(value)


def _field_names(explicit: str | Sequence[str] | None, defaults: Sequence[str]) -> tuple[str, ...]:
    if explicit is None:
        return tuple(defaults)
    if isinstance(explicit, str):
        return (explicit,)
    return tuple(explicit)


def _event_indices(values: Sequence[tuple[int, Any]]) -> tuple[int, ...]:
    """Return action positions at which an observed value changes."""

    events: list[int] = []
    previous: Any = None
    have_previous = False
    for position, value in values:
        if have_previous and value != previous:
            events.append(position)
        previous = value
        have_previous = True
    return tuple(events)


def _lags(source: Sequence[int], target: Sequence[int]) -> tuple[int, ...]:
    """Pair each target event with the latest source event at/before it."""

    if not source:
        return ()
    result: list[int] = []
    source_index = 0
    for target_position in target:
        while (
            source_index + 1 < len(source)
            and source[source_index + 1] <= target_position
        ):
            source_index += 1
        if source[source_index] <= target_position:
            result.append(target_position - source[source_index])
    return tuple(result)


def _histogram(values: Iterable[int]) -> dict[str, int]:
    return {str(key): count for key, count in sorted(Counter(values).items())}


@dataclass(frozen=True)
class FlickerMetrics:
    """Deterministic transition metrics for one generic action trace."""

    actions: int
    ordinal_transitions: int
    confirmed_transitions: int
    condensed_transitions: int
    model_selection_transitions: int
    program_selection_transitions: int
    ordinal_transition_actions: tuple[int, ...]
    confirmed_transition_actions: tuple[int, ...]
    condensed_transition_actions: tuple[int, ...]
    model_selection_transition_actions: tuple[int, ...]
    program_selection_transition_actions: tuple[int, ...]
    ordinal_to_confirmed_lags: tuple[int, ...]
    ordinal_to_condensed_lags: tuple[int, ...]
    ordinal_to_model_lags: tuple[int, ...]
    ordinal_to_program_lags: tuple[int, ...]
    missing_fields: tuple[str, ...]

    @property
    def ordinal_transition_boundaries(self) -> int:
        return max(self.actions - 1, 0)

    @property
    def ordinal_transitions_per_action(self) -> float:
        return self.ordinal_transitions / max(self.actions, 1)

    @property
    def confirmed_transitions_per_action(self) -> float:
        return self.confirmed_transitions / max(self.actions, 1)

    @property
    def condensed_transitions_per_action(self) -> float:
        return self.condensed_transitions / max(self.actions, 1)

    @property
    def model_selection_transitions_per_action(self) -> float:
        return self.model_selection_transitions / max(self.actions, 1)

    @property
    def program_selection_transitions_per_action(self) -> float:
        return self.program_selection_transitions / max(self.actions, 1)

    @property
    def ordinal_confirmed_coincident(self) -> int:
        return self.ordinal_to_confirmed_lags.count(0)

    @property
    def ordinal_condensed_coincident(self) -> int:
        return self.ordinal_to_condensed_lags.count(0)

    @property
    def ordinal_model_coincident(self) -> int:
        return self.ordinal_to_model_lags.count(0)

    @property
    def ordinal_program_coincident(self) -> int:
        return self.ordinal_to_program_lags.count(0)

    @property
    def mean_ordinal_to_model_lag(self) -> float | None:
        return _mean(self.ordinal_to_model_lags)

    @property
    def mean_ordinal_to_program_lag(self) -> float | None:
        return _mean(self.ordinal_to_program_lags)

    @property
    def ordinal_to_confirmed_lag_histogram(self) -> dict[str, int]:
        return _histogram(self.ordinal_to_confirmed_lags)

    @property
    def ordinal_to_condensed_lag_histogram(self) -> dict[str, int]:
        return _histogram(self.ordinal_to_condensed_lags)

    @property
    def ordinal_to_model_lag_histogram(self) -> dict[str, int]:
        return _histogram(self.ordinal_to_model_lags)

    @property
    def ordinal_to_program_lag_histogram(self) -> dict[str, int]:
        return _histogram(self.ordinal_to_program_lags)

    def as_dict(self) -> dict[str, Any]:
        """Return JSON-safe metrics for reports and deterministic manifests."""

        return {
            "actions": self.actions,
            "ordinal_transitions": self.ordinal_transitions,
            "confirmed_transitions": self.confirmed_transitions,
            "condensed_transitions": self.condensed_transitions,
            "model_selection_transitions": self.model_selection_transitions,
            "program_selection_transitions": self.program_selection_transitions,
            "ordinal_transition_boundaries": self.ordinal_transition_boundaries,
            "ordinal_transitions_per_action": self.ordinal_transitions_per_action,
            "confirmed_transitions_per_action": self.confirmed_transitions_per_action,
            "condensed_transitions_per_action": self.condensed_transitions_per_action,
            "model_selection_transitions_per_action": self.model_selection_transitions_per_action,
            "program_selection_transitions_per_action": self.program_selection_transitions_per_action,
            "ordinal_transition_actions": list(self.ordinal_transition_actions),
            "confirmed_transition_actions": list(self.confirmed_transition_actions),
            "condensed_transition_actions": list(self.condensed_transition_actions),
            "model_selection_transition_actions": list(self.model_selection_transition_actions),
            "program_selection_transition_actions": list(self.program_selection_transition_actions),
            "ordinal_to_confirmed_lags": list(self.ordinal_to_confirmed_lags),
            "ordinal_to_condensed_lags": list(self.ordinal_to_condensed_lags),
            "ordinal_to_model_lags": list(self.ordinal_to_model_lags),
            "ordinal_to_program_lags": list(self.ordinal_to_program_lags),
            "ordinal_confirmed_coincident": self.ordinal_confirmed_coincident,
            "ordinal_condensed_coincident": self.ordinal_condensed_coincident,
            "ordinal_model_coincident": self.ordinal_model_coincident,
            "ordinal_program_coincident": self.ordinal_program_coincident,
            "mean_ordinal_to_model_lag": self.mean_ordinal_to_model_lag,
            "mean_ordinal_to_program_lag": self.mean_ordinal_to_program_lag,
            "ordinal_to_confirmed_lag_histogram": self.ordinal_to_confirmed_lag_histogram,
            "ordinal_to_condensed_lag_histogram": self.ordinal_to_condensed_lag_histogram,
            "ordinal_to_model_lag_histogram": self.ordinal_to_model_lag_histogram,
            "ordinal_to_program_lag_histogram": self.ordinal_to_program_lag_histogram,
            "missing_fields": list(self.missing_fields),
        }

    def to_json(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True)


def _mean(values: Sequence[int]) -> float | None:
    return None if not values else sum(values) / len(values)


def reduce_trace(
    records: Iterable[Mapping[str, Any]],
    *,
    instantaneous_ordinal_field: str | Sequence[str] | None = None,
    confirmed_ordinal_field: str | Sequence[str] | None = None,
    condensed_field: str | Sequence[str] | None = None,
    model_field: str | Sequence[str] | None = None,
    program_field: str | Sequence[str] | None = None,
) -> FlickerMetrics:
    """Reduce generic per-action records into flicker metrics.

    The iterable is materialised in caller order.  Action numbers in event
    lists are positions in that materialised trace, not values read from a
    possibly sparse ``request_seq`` field.  This keeps lag deterministic even
    when a plant omits or retries an action.
    """

    rows = tuple(records)
    if any(not isinstance(row, Mapping) for row in rows):
        raise TypeError("each control trace record must be a mapping")

    fields = {
        "instantaneous ordinal": _field_names(
            instantaneous_ordinal_field, INSTANTANEOUS_ORDINAL_FIELDS
        ),
        "confirmed ordinal": _field_names(
            confirmed_ordinal_field, CONFIRMED_ORDINAL_FIELDS
        ),
        "condensed": _field_names(condensed_field, CONDENSED_FIELDS),
        "model selection": _field_names(model_field, MODEL_FIELDS),
        "program selection": _field_names(program_field, PROGRAM_FIELDS),
    }
    observed: dict[str, list[tuple[int, Any]]] = {name: [] for name in fields}
    missing: list[str] = []
    for name, names in fields.items():
        if not any(any(field in row for field in names) for row in rows):
            missing.append(name)

    for position, row in enumerate(rows):
        for name, names in fields.items():
            present, value = _first(row, names)
            if present:
                if "ordinal" in name:
                    value = _normalise_number(value)
                elif name in ("model selection", "program selection"):
                    value = _identity(value)
                else:
                    value = _identity(value)
                if value is not None:
                    observed[name].append((position, value))

    ordinal_events = _event_indices(observed["instantaneous ordinal"])
    confirmed_events = _event_indices(observed["confirmed ordinal"])
    condensed_events = _event_indices(observed["condensed"])
    model_events = _event_indices(observed["model selection"])
    program_events = _event_indices(observed["program selection"])
    return FlickerMetrics(
        actions=len(rows),
        ordinal_transitions=len(ordinal_events),
        confirmed_transitions=len(confirmed_events),
        condensed_transitions=len(condensed_events),
        model_selection_transitions=len(model_events),
        program_selection_transitions=len(program_events),
        ordinal_transition_actions=ordinal_events,
        confirmed_transition_actions=confirmed_events,
        condensed_transition_actions=condensed_events,
        model_selection_transition_actions=model_events,
        program_selection_transition_actions=program_events,
        ordinal_to_confirmed_lags=_lags(ordinal_events, confirmed_events),
        ordinal_to_condensed_lags=_lags(ordinal_events, condensed_events),
        ordinal_to_model_lags=_lags(ordinal_events, model_events),
        ordinal_to_program_lags=_lags(ordinal_events, program_events),
        missing_fields=tuple(missing),
    )


# A descriptive alias for callers that prefer the probe terminology.
reduce_control_trace = reduce_trace


__all__ = [
    "FlickerMetrics",
    "INSTANTANEOUS_ORDINAL_FIELDS",
    "CONFIRMED_ORDINAL_FIELDS",
    "CONDENSED_FIELDS",
    "MODEL_FIELDS",
    "PROGRAM_FIELDS",
    "reduce_trace",
    "reduce_control_trace",
]
