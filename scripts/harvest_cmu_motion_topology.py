#!/usr/bin/env python3
"""Distil CMU ASF/AMC poses into morphology-neutral motion topology.

This is an offline interface tool.  It uses floating point to reconstruct the
source skeleton, then discards all poses, angles, positions, thresholds, and
command-like values.  Its checked-in output contains only integer counts and
categorical relations suitable for output-null graph hints.
"""
from __future__ import annotations

from dataclasses import dataclass
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Iterable

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "cmu_mocap"
RAW = DATA / "raw"
MANIFEST = DATA / "manifest.json"
OUTPUT = DATA / "topology.json"
LENGTH_SCALE_METRES = (1.0 / 0.45) * (2.54 / 100.0)


@dataclass(frozen=True)
class Bone:
    name: str
    direction: np.ndarray
    length: float
    axis_angles: tuple[float, float, float]
    axis_order: str
    dof: tuple[str, ...]


@dataclass(frozen=True)
class Skeleton:
    bones: dict[str, Bone]
    children: dict[str, tuple[str, ...]]
    root_order: tuple[str, ...]
    root_axis_order: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _rotation(axis: str, angle_degrees: float) -> np.ndarray:
    angle = np.deg2rad(angle_degrees)
    cosine = np.cos(angle)
    sine = np.sin(angle)
    if axis == "x":
        return np.array(((1, 0, 0), (0, cosine, -sine), (0, sine, cosine)))
    if axis == "y":
        return np.array(((cosine, 0, sine), (0, 1, 0), (-sine, 0, cosine)))
    if axis == "z":
        return np.array(((cosine, -sine, 0), (sine, cosine, 0), (0, 0, 1)))
    raise ValueError(f"unknown rotation axis: {axis!r}")


def _euler(angles: Iterable[float], order: Iterable[str]) -> np.ndarray:
    result = np.eye(3)
    for angle, axis in zip(angles, order):
        # CMU's reference viewer prepends each channel rotation
        # (Skeleton.cpp:get_dof_rot / ordered_rotation).
        result = _rotation(axis.lower().removeprefix("r"), angle) @ result
    return result


def parse_asf(path: Path) -> Skeleton:
    lines = [line.strip() for line in path.read_text(
        encoding="utf-8", errors="replace"
    ).splitlines()]
    bones: dict[str, Bone] = {}
    children: dict[str, list[str]] = {"root": []}
    root_order: tuple[str, ...] = ("tx", "ty", "tz", "rx", "ry", "rz")
    root_axis_order = "XYZ"
    section = ""
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith(":"):
            section = line.lower()
            index += 1
            continue
        if section == ":root":
            fields = line.split()
            if fields[:1] == ["order"]:
                root_order = tuple(value.lower() for value in fields[1:])
            elif fields[:1] == ["axis"]:
                root_axis_order = fields[1]
        elif section == ":bonedata" and line == "begin":
            attrs: dict[str, list[str]] = {}
            index += 1
            while index < len(lines) and lines[index] != "end":
                fields = lines[index].split()
                if fields and fields[0] in {
                    "name", "direction", "length", "axis", "dof"
                }:
                    attrs[fields[0]] = fields[1:]
                index += 1
            name = attrs["name"][0]
            axis = attrs.get("axis", ["0", "0", "0", "XYZ"])
            bones[name] = Bone(
                name=name,
                direction=np.array(tuple(map(float, attrs["direction"]))),
                length=float(attrs["length"][0]),
                axis_angles=tuple(map(float, axis[:3])),
                axis_order=axis[3],
                dof=tuple(value.lower() for value in attrs.get("dof", [])),
            )
            children.setdefault(name, [])
        elif section == ":hierarchy" and line not in {"", "begin", "end"}:
            fields = line.split()
            if len(fields) > 1:
                children.setdefault(fields[0], []).extend(fields[1:])
        index += 1
    return Skeleton(
        bones=bones,
        children={key: tuple(value) for key, value in children.items()},
        root_order=root_order,
        root_axis_order=root_axis_order,
    )


def parse_amc(path: Path) -> list[dict[str, tuple[float, ...]]]:
    frames: list[dict[str, tuple[float, ...]]] = []
    current: dict[str, tuple[float, ...]] | None = None
    for raw_line in path.read_text(
        encoding="utf-8", errors="replace"
    ).splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("#", ":")):
            continue
        if line.isdigit():
            current = {}
            frames.append(current)
            continue
        if current is None:
            continue
        fields = line.split()
        current[fields[0]] = tuple(map(float, fields[1:]))
    return frames


def forward_kinematics(
    skeleton: Skeleton,
    frame: dict[str, tuple[float, ...]],
) -> dict[str, np.ndarray]:
    root_values = dict(zip(skeleton.root_order, frame["root"]))
    root_position = LENGTH_SCALE_METRES * np.array(tuple(
        root_values.get(axis, 0.0) for axis in ("tx", "ty", "tz")
    ))
    root_rotation = _euler(
        tuple(root_values.get(f"r{axis.lower()}", 0.0)
              for axis in skeleton.root_axis_order),
        skeleton.root_axis_order,
    )
    positions = {"root": root_position}
    rotations = {"root": root_rotation}

    def place(parent: str) -> None:
        for name in skeleton.children.get(parent, ()):
            bone = skeleton.bones[name]
            values = frame.get(name, ())
            motion = _euler(values, bone.dof)
            basis = _euler(bone.axis_angles, bone.axis_order)
            rotation = rotations[parent] @ basis @ motion @ basis.T
            positions[name] = positions[parent] + rotation @ (
                bone.direction * bone.length * LENGTH_SCALE_METRES
            )
            rotations[name] = rotation
            place(name)

    place("root")
    return positions


def _two_means_low_centroid(values: np.ndarray) -> float:
    centroids = np.array((float(values.min()), float(values.max())))
    previous: bytes | None = None
    seen: set[bytes] = set()
    while True:
        labels = np.abs(values[:, None] - centroids[None, :]).argmin(axis=1)
        encoded = labels.tobytes()
        if encoded == previous or encoded in seen:
            break
        seen.add(encoded)
        previous = encoded
        for cluster in (0, 1):
            members = values[labels == cluster]
            if len(members):
                centroids[cluster] = float(members.mean())
    return float(centroids.min())


def _deadband(values: np.ndarray) -> float:
    median = float(np.median(values))
    return float(np.median(np.abs(values - median)))


def _sign(value: float, deadband: float) -> str:
    if value > deadband:
        return "increasing"
    if value < -deadband:
        return "decreasing"
    return "held"


def _rle(states: list[tuple[str, ...]]) -> list[tuple[tuple[str, ...], int]]:
    runs: list[tuple[tuple[str, ...], int]] = []
    for state in states:
        if runs and runs[-1][0] == state:
            runs[-1] = (state, runs[-1][1] + 1)
        else:
            runs.append((state, 1))
    return runs


def _denoise_runs(
    runs: list[tuple[tuple[str, ...], int]],
) -> list[tuple[tuple[str, ...], int]]:
    if len(runs) < 3:
        return runs
    persistence = max(1, int(np.median([length for _, length in runs])) // 2)
    states = [state for state, length in runs for _ in range(length)]
    cursor = 0
    for index, (_, length) in enumerate(runs):
        if length < persistence:
            left = runs[index - 1] if index else None
            right = runs[index + 1] if index + 1 < len(runs) else None
            replacement = max(
                (candidate for candidate in (left, right) if candidate),
                key=lambda row: row[1],
                default=None,
            )
            if replacement:
                states[cursor:cursor + length] = [replacement[0]] * length
        cursor += length
    return _rle(states)


def _support_mode(contact_groups: tuple[str, ...]) -> str:
    groups = set(contact_groups)
    if not groups:
        return "unsupported"
    if groups == {"lower_left", "lower_right"}:
        return "paired_lower_support"
    if groups <= {"lower_left", "lower_right"}:
        return "single_lower_support"
    if groups <= {"upper_left", "upper_right"}:
        return "upper_support"
    if "axial" in groups and len(groups) == 1:
        return "axial_support"
    return "distributed_support"


def _phase(previous_support: str | None, state: tuple[str, ...]) -> str:
    support, height_energy = state[:2]
    if support == "unsupported":
        return "flight"
    if previous_support == "unsupported":
        return "landing"
    if height_energy == "increasing":
        return "launch"
    if height_energy == "decreasing":
        return "landing"
    return "preparation"


def harvest_clip(
    skeleton: Skeleton,
    frames: list[dict[str, tuple[float, ...]]],
) -> dict:
    tracked = {
        "lower_left": ("ltoes", "lfoot"),
        "lower_right": ("rtoes", "rfoot"),
        "upper_left": ("lhand",),
        "upper_right": ("rhand",),
        "axial": ("head", "thorax", "lowerback"),
    }
    poses = [forward_kinematics(skeleton, frame) for frame in frames]
    root = np.stack([pose["root"] for pose in poses])
    available = {
        group: tuple(name for name in names if name in poses[0])
        for group, names in tracked.items()
    }
    frame_minimum_heights = np.array([
        min(
            pose[name][1]
            for names in available.values() for name in names
        )
        for pose in poses
    ])
    ground_reference = _two_means_low_centroid(frame_minimum_heights)
    # Contact clearance comes from the held skeleton's smallest tracked
    # terminal segment, not a tuned distance threshold.
    lower_terminal_chain = tuple(
        name for name in ("lfoot", "ltoes", "rfoot", "rtoes")
        if name in skeleton.bones
    )
    contact_clearance = min(
        skeleton.bones[name].length * LENGTH_SCALE_METRES
        for name in lower_terminal_chain
    )
    flight_clearance = max(
        skeleton.bones[name].length * LENGTH_SCALE_METRES
        for name in lower_terminal_chain
    )
    ground_threshold = ground_reference + contact_clearance
    flight_threshold = ground_reference + flight_clearance

    contact_by_frame: list[tuple[str, ...]] = []
    for pose in poses:
        contacts = set(
            group for group, names in available.items()
            if names and min(pose[name][1] for name in names) <= ground_threshold
        )
        if not contacts:
            lower_heights = {
                group: min(pose[name][1] for name in available[group])
                for group in ("lower_left", "lower_right")
            }
            lowest_group = min(lower_heights, key=lower_heights.get)
            if lower_heights[lowest_group] <= flight_threshold:
                contacts.add(lowest_group)
        contact_by_frame.append(tuple(sorted(contacts)))

    displacement = np.diff(root, axis=0, prepend=root[:1])
    vertical = displacement[:, 1]
    vertical_deadband = _deadband(vertical)
    horizontal = root[:, (0, 2)]
    centered = horizontal - horizontal.mean(axis=0)
    _, _, vectors = np.linalg.svd(centered, full_matrices=False)
    principal = vectors[0]
    projected = np.diff(horizontal @ principal, prepend=(horizontal @ principal)[:1])
    translation_deadband = _deadband(projected)
    first_clear = next((
        value for value in projected if abs(value) > translation_deadband
    ), 1.0)
    projected *= 1.0 if first_clear >= 0 else -1.0
    speed_energy = np.sum(displacement[:, (0, 2)] ** 2, axis=1)
    kinetic_change = np.diff(speed_energy, prepend=speed_energy[:1])
    kinetic_deadband = _deadband(kinetic_change)

    annotated_frame_states = [
        (
            _support_mode(contacts),
            _sign(float(vertical[index]), vertical_deadband),
            _sign(float(kinetic_change[index]), kinetic_deadband),
            _sign(float(projected[index]), translation_deadband),
        )
        for index, contacts in enumerate(contact_by_frame)
    ]
    # Contact topology and mass-height energy define a program stage.  Kinetic
    # and translation trends annotate that stage but must not multiply it into
    # a new stage for every noisy fluctuation.
    frame_states = [state[:2] for state in annotated_frame_states]
    runs = _denoise_runs(_rle(frame_states))
    distinct_states: list[tuple[str, str]] = []
    state_index: dict[tuple[str, str], int] = {}
    for state, _ in runs:
        if state not in state_index:
            state_index[state] = len(distinct_states)
            distinct_states.append(state)
    transitions: dict[tuple[int, int], int] = {}
    for (source, _), (target, _) in zip(runs, runs[1:]):
        edge = (state_index[source], state_index[target])
        transitions[edge] = transitions.get(edge, 0) + 1

    # A hint visits each observed basin once.  Recurrent sequencing remains in
    # the counted transition graph rather than being unrolled into a trajectory.
    stage_state_ids = list(range(len(distinct_states)))

    annotations: dict[tuple[str, str], tuple[Counter, Counter]] = {}
    for support, height_energy, kinetic_energy, translation in annotated_frame_states:
        kinetic_counts, translation_counts = annotations.setdefault(
            (support, height_energy), (Counter(), Counter())
        )
        kinetic_counts[kinetic_energy] += 1
        translation_counts[translation] += 1

    def dominant(counter: Counter) -> str:
        return min(counter, key=lambda value: (-counter[value], value))

    states = []
    for identifier, state in enumerate(distinct_states):
        support, height_energy = state
        kinetic_counts, translation_counts = annotations[state]
        contact_dimension = {
            "unsupported": 0,
            "single_lower_support": 1,
            "paired_lower_support": 2,
            "upper_support": 1,
            "axial_support": 1,
            "distributed_support": 3,
        }[support]
        states.append({
            "id": identifier,
            "support_topology": support,
            "contact_dimension": contact_dimension,
            "height_energy_relation": height_energy,
            "kinetic_energy_relation": dominant(kinetic_counts),
            "translation_relation": dominant(translation_counts),
        })
    state_rows = {row["id"]: row for row in states}
    stages = []
    previous_support: str | None = None
    for ordinal, identifier in enumerate(stage_state_ids):
        row = state_rows[identifier]
        state = distinct_states[identifier]
        stages.append({
            "ordinal": ordinal,
            "state_id": identifier,
            "phase": _phase(previous_support, state),
            "support_topology": row["support_topology"],
            "contact_dimension": row["contact_dimension"],
            "height_energy_relation": row["height_energy_relation"],
            "kinetic_energy_relation": row["kinetic_energy_relation"],
            "translation_relation": row["translation_relation"],
        })
        previous_support = row["support_topology"]
    return {
        "frame_count": len(frames),
        "state_count": len(states),
        "transition_count": len(transitions),
        "stage_count": len(stages),
        "opposed_translation_observed": int(
            any(state[3] == "increasing" for state in annotated_frame_states)
            and any(state[3] == "decreasing" for state in annotated_frame_states)
        ),
        "states": states,
        "transitions": [
            {"from_state": source, "to_state": target, "count": count}
            for (source, target), count in sorted(transitions.items())
        ],
        "stages": stages,
    }


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    clips = []
    skeletons: dict[int, Skeleton] = {}
    for row in manifest["clips"]:
        subject = int(row["subject"])
        trial = int(row["trial"])
        asf = RAW / f"{subject}.asf"
        amc = RAW / f"{subject}_{trial:02d}.amc"
        if _sha256(asf) != row["asf_sha256"]:
            raise ValueError(f"held ASF checksum mismatch: {asf}")
        if _sha256(amc) != row["amc_sha256"]:
            raise ValueError(f"held AMC checksum mismatch: {amc}")
        skeleton = skeletons.setdefault(subject, parse_asf(asf))
        topology = harvest_clip(skeleton, parse_amc(amc))
        clips.append({
            "source": f"cmu:{subject}:{trial:02d}",
            "subject": subject,
            "trial": trial,
            "description": row["description"],
            "task_context": row["task_context"],
            "frame_rate_hz": 120,
            "source_amc_sha256": row["amc_sha256"],
            **topology,
        })
    payload = {
        "version": 1,
        "dataset": manifest["dataset"],
        "dataset_url": manifest["dataset_url"],
        "acknowledgement": manifest["acknowledgement"],
        "raw_data_redistributed": False,
        "raw_pose_values_retained": False,
        "numeric_kinematic_values_retained": False,
        "clips": clips,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "clips": len(clips),
        "frames": sum(row["frame_count"] for row in clips),
        "states": sum(row["state_count"] for row in clips),
        "transitions": sum(row["transition_count"] for row in clips),
        "stages": sum(row["stage_count"] for row in clips),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
