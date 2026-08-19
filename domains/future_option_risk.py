"""Pure deterministic shape-math for conservative future-manifold checks."""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
from typing import Any, Mapping

from domains.learning_safety import LearningSafetyContext


def _finite(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and non-negative")
    return value


def _integer(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative int")
    return value


def _id(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    return value

def _keys(value: Mapping[str, Any], allowed: set[str], name: str) -> None:
    unknown = set(value) - allowed
    if unknown:
        raise ValueError(f"{name} has unknown keys: {sorted(unknown)!r}")


def _metadata(value: Any) -> str:
    try:
        return json.dumps(value if value is not None else {}, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("cell metadata must be finite JSON") from exc


@dataclass(frozen=True)
class ShapeSlice:
    time: int
    cells: tuple[tuple[str, float, float, str], ...]
    links: tuple[tuple[str, str, float], ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "time", _integer(self.time, "slice time"))
        cells = []
        seen = set()
        raw = self.cells.items() if isinstance(self.cells, Mapping) else self.cells
        for entry in raw:
            if isinstance(entry, tuple) and len(entry) == 2 and isinstance(self.cells, Mapping):
                cid, value = entry
            elif isinstance(entry, Mapping):
                _keys(entry, {"cell_id", "id", "weight", "information", "metadata"}, "cell")
                cid, value = entry.get("cell_id", entry.get("id")), entry
            else:
                try:
                    if len(entry) == 4:
                        cid, weight, information, meta = entry
                        cid = _id(cid, "cell_id")
                        if cid in seen: raise ValueError("duplicate cell")
                        seen.add(cid)
                        cells.append((cid, _finite(weight, f"cell {cid} weight"), _finite(information, f"cell {cid} information"), _metadata(json.loads(meta) if isinstance(meta, str) else meta)))
                        continue
                    cid, value = entry[0], entry[1]
                except (IndexError, TypeError): raise ValueError("invalid cell")
            cid = _id(cid, "cell_id")
            if cid in seen: raise ValueError("duplicate cell")
            seen.add(cid)
            if isinstance(value, Mapping):
                _keys(value, {"weight", "information", "metadata"}, f"cell {cid}")
                weight = _finite(value.get("weight"), f"cell {cid} weight")
                information = _finite(value.get("information"), f"cell {cid} information")
                meta = _metadata(value.get("metadata", {}))
            else:
                raise ValueError("cell must provide weight, information, and metadata")
            cells.append((cid, weight, information, meta))
        links = []
        seen_links = set()
        for link in self.links:
            if isinstance(link, Mapping):
                _keys(link, {"source", "target", "information"}, "link")
                a, b, information = link.get("source"), link.get("target"), link.get("information")
            else:
                try: a, b, information = link[0], link[1], link[2]
                except (IndexError, TypeError): raise ValueError("invalid link")
            edge = (_id(a, "link source"), _id(b, "link target"), _finite(information, "link information"))
            endpoint = edge[:2]
            if endpoint in seen_links: raise ValueError("duplicate link endpoint")
            if edge[0] not in seen or edge[1] not in seen: raise ValueError("link endpoint missing")
            seen_links.add(endpoint); links.append(edge)
        object.__setattr__(self, "cells", tuple(sorted(cells)))
        object.__setattr__(self, "links", tuple(sorted(links)))

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ShapeSlice":
        if not isinstance(value, Mapping): raise ValueError("slice must be a mapping")
        _keys(value, {"time", "cells", "links"}, "slice")
        return cls(value["time"], value.get("cells", {}), value.get("links", ()))

    def as_mapping(self) -> dict[str, Any]:
        return {"time": self.time,
                "cells": {c: {"weight": w, "information": i, "metadata": json.loads(m)} for c, w, i, m in self.cells},
                "links": [{"source": a, "target": b, "information": i} for a, b, i in self.links]}


def _tube(value: Any, name: str) -> tuple[ShapeSlice, ...]:
    if isinstance(value, Mapping):
        value = [dict(v, time=t) if isinstance(v, Mapping) else v for t, v in value.items()]
    if not isinstance(value, (list, tuple)): raise ValueError(f"{name} must be a sequence")
    slices = tuple(ShapeSlice.from_mapping(v) if isinstance(v, Mapping) else v for v in value)
    if any(not isinstance(v, ShapeSlice) for v in slices): raise ValueError(f"{name} contains invalid slice")
    times = [v.time for v in slices]
    if len(set(times)) != len(times): raise ValueError(f"{name} has duplicate times")
    if not times or sorted(times)[0] != 0 or sorted(times) != list(range(max(times) + 1)):
        raise ValueError(f"{name} must cover t=0 through its horizon")
    return tuple(sorted(slices, key=lambda s: s.time))


@dataclass(frozen=True)
class FutureManifold:
    manifold_id: str
    required_horizon: int
    minimum_width: float
    maximum_information_loss: float
    required_tube: tuple[ShapeSlice, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "manifold_id", _id(self.manifold_id, "manifold_id"))
        object.__setattr__(self, "required_horizon", _integer(self.required_horizon, "required_horizon"))
        object.__setattr__(self, "minimum_width", _finite(self.minimum_width, "minimum_width"))
        object.__setattr__(self, "maximum_information_loss", _finite(self.maximum_information_loss, "maximum_information_loss"))
        tube = _tube(self.required_tube, "required_tube")
        if tube[-1].time != self.required_horizon: raise ValueError("required tube horizon mismatch")
        object.__setattr__(self, "required_tube", tube)

    @classmethod
    def from_mapping(cls, v):
        if not isinstance(v, Mapping): raise ValueError("manifold must be a mapping")
        _keys(v, {"manifold_id", "required_horizon", "minimum_width", "maximum_information_loss", "required_tube"}, "manifold")
        try: return cls(v["manifold_id"], v["required_horizon"], v["minimum_width"], v["maximum_information_loss"], v["required_tube"])
        except KeyError as e: raise ValueError(f"manifold missing {e.args[0]!r}") from e

    def as_mapping(self):
        return {"manifold_id": self.manifold_id, "required_horizon": self.required_horizon, "minimum_width": self.minimum_width, "maximum_information_loss": self.maximum_information_loss, "required_tube": [s.as_mapping() for s in self.required_tube]}


@dataclass(frozen=True)
class ManifoldProjection:
    manifold_id: str
    projected_tube: tuple[ShapeSlice, ...]
    action_count: int
    intervention_magnitude: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "manifold_id", _id(self.manifold_id, "manifold_id"))
        object.__setattr__(self, "projected_tube", _tube(self.projected_tube, "projected_tube"))
        object.__setattr__(self, "action_count", _integer(self.action_count, "action_count"))
        object.__setattr__(self, "intervention_magnitude", _finite(self.intervention_magnitude, "intervention_magnitude"))

    @property
    def projection_horizon(self): return self.projected_tube[-1].time

    @classmethod
    def from_mapping(cls, v):
        if not isinstance(v, Mapping): raise ValueError("projection must be a mapping")
        _keys(v, {"manifold_id", "projected_tube", "action_count", "intervention_magnitude"}, "projection")
        try: return cls(v["manifold_id"], v["projected_tube"], v["action_count"], v["intervention_magnitude"])
        except KeyError as e: raise ValueError(f"projection missing {e.args[0]!r}") from e

    def as_mapping(self):
        return {"manifold_id": self.manifold_id, "projected_tube": [s.as_mapping() for s in self.projected_tube], "action_count": self.action_count, "intervention_magnitude": self.intervention_magnitude}


@dataclass(frozen=True)
class ManifoldAssessment:
    allowed: bool
    reason: str
    retained_tube: tuple[ShapeSlice, ...]
    lost_tube: tuple[ShapeSlice, ...]
    escape_tube: tuple[ShapeSlice, ...]
    retained_width: float
    information_loss: float
    manifold: FutureManifold
    projection: ManifoldProjection
    safety_context: LearningSafetyContext | None = None
    applied_bounds: tuple[int, float, float] | None = None

    @property
    def escape_width(self) -> float:
        return max((sum(w for _, w, _, _ in s.cells) for s in self.escape_tube), default=0.0)

    @property
    def horizon_slack(self) -> int:
        return self.projection.projection_horizon - self.manifold.required_horizon

    @property
    def minimum_retained_width(self) -> float:
        return self.retained_width

    @property
    def maximum_information_loss(self) -> float:
        return self.information_loss

    @property
    def maximum_escape_width(self) -> float:
        return self.escape_width

    @property
    def residual_tube(self):
        return tuple(zip(self.retained_tube, self.lost_tube, self.escape_tube))

    def as_mapping(self):
        return {"allowed": self.allowed, "reason": self.reason,
                "retained_tube": [s.as_mapping() for s in self.retained_tube],
                "lost_tube": [s.as_mapping() for s in self.lost_tube],
                "escape_tube": [s.as_mapping() for s in self.escape_tube],
                "retained_width": self.retained_width,
                "minimum_retained_width": self.minimum_retained_width,
                "information_loss": self.information_loss,
                "maximum_information_loss": self.maximum_information_loss,
                "escape_width": self.escape_width,
                "maximum_escape_width": self.maximum_escape_width,
                "horizon_slack": self.horizon_slack,
                "safety_context": (
                    self.safety_context.as_mapping()
                    if self.safety_context is not None else None
                ),
                "applied_bounds": (
                    {"required_horizon": self.applied_bounds[0],
                     "minimum_width": self.applied_bounds[1],
                     "maximum_information_loss": self.applied_bounds[2]}
                    if self.applied_bounds is not None else None
                ),
                "manifold": self.manifold.as_mapping(),
                "projection": self.projection.as_mapping()}


def _residual(req, proj):
    rm, pm = {c: (w, i, m) for c, w, i, m in req.cells}, {c: (w, i, m) for c, w, i, m in proj.cells}
    retained=[]; lost=[]; escape=[]
    for cid in sorted(set(rm)|set(pm)):
        if cid in rm and cid in pm and rm[cid][2] != pm[cid][2]: raise ValueError("shared cell metadata mismatch")
        if cid in rm and cid in pm: retained.append((cid, min(rm[cid][0], pm[cid][0]), min(rm[cid][1], pm[cid][1]), rm[cid][2]))
        if cid in rm and (cid not in pm or rm[cid][0] > pm[cid][0] or rm[cid][1] > pm[cid][1]): lost.append((cid, max(rm[cid][0] - pm.get(cid, (0, 0, ""))[0], 0), max(rm[cid][1] - pm.get(cid, (0, 0, ""))[1], 0), rm[cid][2]))
        if cid in pm and (cid not in rm or pm[cid][0] > rm[cid][0]): escape.append((cid, max(pm[cid][0] - rm.get(cid, (0, 0, ""))[0], 0), 0.0, pm[cid][2]))
    rl={(a,b):i for a,b,i in req.links}; pl={(a,b):i for a,b,i in proj.links}
    # Endpoint witnesses keep residual link topology valid without inventing shape.
    def add_witnesses(cells, links, source):
        have={c for c, *_ in cells}
        for a,b in links:
            for cid in (a,b):
                if cid not in have:
                    ref=source.get(cid, (0,0,"{}")); cells.append((cid,0.0,0.0,ref[2])); have.add(cid)
    lost_links=[(a,b,max(rl[(a,b)]-pl.get((a,b),0.0),0.0)) for a,b in sorted(rl) if (a,b) not in pl or rl[(a,b)] > pl[(a,b)]]
    escape_links=[(a,b,pl[(a,b)]) for a,b in sorted(pl) if (a,b) not in rl]
    add_witnesses(lost, [(a,b) for a,b,_ in lost_links], rm); add_witnesses(escape, [(a,b) for a,b,_ in escape_links], pm)
    retained_links=[(a,b,min(rl[(a,b)],pl[(a,b)])) for a,b in sorted(set(rl)&set(pl))]
    return (ShapeSlice(req.time, tuple(retained), tuple(retained_links)), ShapeSlice(req.time, tuple(lost), tuple(lost_links)), ShapeSlice(req.time, tuple(escape), tuple(escape_links)))


def evaluate_future_manifold(manifold, projection, safety_context=None) -> ManifoldAssessment:
    m = manifold if isinstance(manifold, FutureManifold) else FutureManifold.from_mapping(manifold)
    p = projection if isinstance(projection, ManifoldProjection) else ManifoldProjection.from_mapping(projection)
    if safety_context is not None and not isinstance(safety_context, LearningSafetyContext):
        safety_context = LearningSafetyContext.from_mapping(safety_context)
    active = bool(safety_context and safety_context.active)
    # The context publishes the relaxation budget.  Gate-off is an exact
    # identity path: absent or unverified evidence uses the original bounds.
    required_horizon_units = (
        safety_context.required_horizon_units if active else m.required_horizon
    )
    minimum_width = max(
        0.0,
        m.minimum_width - (safety_context.minimum_width_relaxation if active else 0.0),
    )
    maximum_information_loss = m.maximum_information_loss + (
        safety_context.information_loss_allowance if active else 0.0
    )
    required_horizon = min(m.required_horizon, required_horizon_units)
    if p.projection_horizon >= required_horizon:
        retained=[]; lost=[]; escape=[]
        for r in m.required_tube:
            if r.time > required_horizon:
                break
            q = p.projected_tube[r.time]
            a,b,c = _residual(r,q); retained.append(a); lost.append(b); escape.append(c)
    else:
        retained=lost=escape=[]
    retained_width = min((sum(w for _,w,_,_ in s.cells) for s in retained), default=0.0)
    information_loss = max((sum(i for _,_,i,_ in s.cells)+sum(i for _,_,i in s.links) for s in lost), default=0.0)
    escaped = any(s.cells or s.links for s in escape)
    reasons=((p.manifold_id != m.manifold_id,"manifold_identity_mismatch"),(p.projection_horizon < required_horizon,"insufficient_temporal_coverage"),(escaped,"outside_future_manifold"),(retained_width < minimum_width,"insufficient_width"),(information_loss > maximum_information_loss,"excess_information_loss"))
    # Any observed residual loss is a hard veto. Recovery only relaxes the
    # amount of future that must be projected, never an actual bound breach.
    reason=next((n for failed,n in reasons if failed),"allowed")
    if reason == "allowed" and any(s.cells or s.links for s in lost):
        reason = "excess_information_loss"
    return ManifoldAssessment(
        reason=="allowed", reason, tuple(retained), tuple(lost), tuple(escape),
        retained_width, information_loss, m, p, safety_context,
        (required_horizon, minimum_width, maximum_information_loss),
    )


__all__=["ShapeSlice","FutureManifold","ManifoldProjection","ManifoldAssessment","evaluate_future_manifold"]
