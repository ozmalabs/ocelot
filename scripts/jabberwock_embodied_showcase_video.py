"""Render an annotated cold-start adaptation reel across embodied body plans.

All actions in the footage come from the existing Rust graph policies.  This
module is a presentation boundary only: it samples simulator cameras, draws
captions over receipts, and streams RGB frames to ffmpeg.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from domains.humanoid_bench_world import HumanoidBenchWorld  # noqa: E402
from domains.pybullet_robot_world import (  # noqa: E402
    MechanicalCondition,
    MechanicalRandomization,
)
from scripts.jabberwock_aerial_direct_recovery import (  # noqa: E402
    run_direct_recovery,
)
from scripts.jabberwock_embodied_adaptation import run_episode  # noqa: E402
from scripts.jabberwock_humanoid_walk import _run_arm  # noqa: E402


DEFAULT_OUTPUT = (
    ROOT
    / "results"
    / "embodied_cold_start_showcase"
    / "jabberwock_cold_start_body_plans.mp4"
)
DEFAULT_HUMANOID_BENCH = Path(
    "/home/matt/ozma/simulators/humanoid-bench"
)
FONT_REGULAR = Path("/usr/share/fonts/TTF/DejaVuSans.ttf")
FONT_BOLD = Path("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf")


class RawVideoWriter:
    """Stream fixed-size annotated RGB frames to an H.264 encoder."""

    def __init__(
        self,
        output: Path,
        *,
        width: int,
        height: int,
        fps: int,
    ) -> None:
        output.parent.mkdir(parents=True, exist_ok=True)
        self.output = output
        self.width = width
        self.height = height
        self.fps = fps
        self.frame_count = 0
        self._process = subprocess.Popen(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-f",
                "rawvideo",
                "-pix_fmt",
                "rgb24",
                "-s:v",
                f"{width}x{height}",
                "-r",
                str(fps),
                "-i",
                "-",
                "-an",
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(output),
            ],
            stdin=subprocess.PIPE,
        )

    def write(self, image: Image.Image, *, repeat: int = 1) -> None:
        if self._process.stdin is None:
            raise RuntimeError("ffmpeg input is closed")
        frame = image.convert("RGB")
        if frame.size != (self.width, self.height):
            frame = _cover(frame, self.width, self.height)
        encoded = np.asarray(frame, dtype=np.uint8).tobytes()
        for _ in range(repeat):
            self._process.stdin.write(encoded)
            self.frame_count += 1

    def close(self) -> None:
        if self._process.stdin is not None:
            self._process.stdin.close()
        return_code = self._process.wait()
        if return_code:
            raise RuntimeError(f"ffmpeg exited with status {return_code}")


def _cover(image: Image.Image, width: int, height: int) -> Image.Image:
    scale = max(width / image.width, height / image.height)
    resized = image.resize(
        (round(image.width * scale), round(image.height * scale)),
        Image.Resampling.LANCZOS,
    )
    left = (resized.width - width) // 2
    top = (resized.height - height) // 2
    return resized.crop((left, top, left + width, top + height))


def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(
        str(FONT_BOLD if bold else FONT_REGULAR),
        size,
    )


def _text_card(
    width: int,
    height: int,
    *,
    eyebrow: str,
    title: str,
    subtitle: str,
) -> Image.Image:
    image = Image.new("RGB", (width, height), "#071017")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 12, height), fill="#44d7b6")
    draw.text((72, 130), eyebrow, font=_font(22, bold=True), fill="#44d7b6")
    draw.text((72, 180), title, font=_font(48, bold=True), fill="white")
    draw.multiline_text(
        (74, 258),
        subtitle,
        font=_font(24),
        fill="#c8d3dc",
        spacing=10,
    )
    return image


class SceneCapture:
    """Turn semantic experiment observer events into annotated video frames."""

    PHASE_LABELS = {
        "cold_start": "FRESH GRAPH",
        "motor_babble": "LEARNING OPAQUE ACTUATORS",
        "goal_navigation": "GRAPH-NATIVE NAVIGATION",
        "goal_flight": "GRAPH-NATIVE FLIGHT",
        "failure_detection": "INFERRING THE FAILURE",
        "direct_recovery": "THREE-ROTOR DIRECT CONTROL",
        "synergy_learning": "LEARNING COMBINED MOVEMENTS",
        "gait_adaptation": "ONLINE GAIT ADAPTATION",
        "walking": "COMPOSING A WALK",
    }

    def __init__(
        self,
        writer: RawVideoWriter,
        *,
        body_name: str,
        simulator: str,
        intervention: str,
        strides: dict[str, int] | None = None,
    ) -> None:
        self.writer = writer
        self.body_name = body_name
        self.simulator = simulator
        self.intervention = intervention
        self.strides = strides or {}
        self.calls: dict[str, int] = {}
        self.event_text: str | None = None
        self.event_frames = 0
        self.scene_start = writer.frame_count
        self.event_start: int | None = None
        self.frames_written = 0

    def __call__(self, world: Any, payload: dict[str, Any]) -> None:
        phase = str(payload["phase"])
        ordinal = self.calls.get(phase, 0)
        self.calls[phase] = ordinal + 1
        event = payload.get("event")
        stride = max(1, int(self.strides.get(phase, 1)))
        if event is None and ordinal % stride:
            return
        if event == "damage_onset":
            self.event_text = self.intervention
            self.event_frames = self.writer.fps * 3
            self.event_start = self.writer.frame_count
        elif event == "perturbation":
            self.event_text = self.intervention
            self.event_frames = self.writer.fps * 3
            self.event_start = self.writer.frame_count
        elif event == "direct_control":
            self.event_text = (
                "GRAPH RESPONSE: inferred failed rotor; direct motor "
                "allocation engaged"
            )
            self.event_frames = self.writer.fps * 3
        # Rendering is deliberately a private presentation hook so simulator
        # adapters do not gain a new public agent/world authority surface.
        frame = world._render_rgb_array(
            width=self.writer.width,
            height=self.writer.height,
        )
        image = _cover(
            Image.fromarray(np.asarray(frame, dtype=np.uint8), mode="RGB"),
            self.writer.width,
            self.writer.height,
        )
        self._annotate(image, payload)
        repeat = self.writer.fps if phase == "cold_start" else 1
        self.writer.write(image, repeat=repeat)
        self.frames_written += repeat
        self.event_frames = max(0, self.event_frames - repeat)
        if self.event_frames == 0:
            self.event_text = None

    def _annotate(self, image: Image.Image, payload: dict[str, Any]) -> None:
        draw = ImageDraw.Draw(image, "RGBA")
        width, height = image.size
        draw.rectangle((0, 0, width, 74), fill=(4, 12, 18, 220))
        draw.rectangle((0, 0, 10, 74), fill=(68, 215, 182, 255))
        draw.text(
            (28, 12),
            f"JABBERWOCK  /  {self.body_name}",
            font=_font(25, bold=True),
            fill="white",
        )
        phase = self.PHASE_LABELS.get(
            str(payload["phase"]),
            str(payload["phase"]).replace("_", " ").upper(),
        )
        draw.text((30, 45), phase, font=_font(15, bold=True), fill="#44d7b6")
        draw.text(
            (width - 265, 18),
            f"COLD START  •  {self.simulator}",
            font=_font(14, bold=True),
            fill="#d7e2e8",
        )

        observation = payload["observation"]
        position = observation["base_position"]
        action = int(payload["action"])
        detail = (
            f"receipt {max(0, action):04d}     "
            f"position  x {position[0]:+.2f}  y {position[1]:+.2f}  "
            f"z {position[2]:+.2f}"
        )
        draw.rounded_rectangle(
            (22, height - 56, width - 22, height - 18),
            radius=10,
            fill=(4, 12, 18, 190),
        )
        draw.text(
            (38, height - 48),
            detail,
            font=_font(16),
            fill="#e5edf2",
        )
        if self.event_text:
            box_top = height - 144
            draw.rounded_rectangle(
                (22, box_top, width - 22, height - 67),
                radius=12,
                fill=(155, 33, 48, 235),
                outline=(255, 190, 80, 255),
                width=3,
            )
            draw.text(
                (42, box_top + 11),
                "INTERVENTION",
                font=_font(15, bold=True),
                fill="#ffd166",
            )
            draw.text(
                (42, box_top + 36),
                self.event_text,
                font=_font(21, bold=True),
                fill="white",
            )

    def manifest(self) -> dict[str, Any]:
        return {
            "body_plan": self.body_name,
            "simulator": self.simulator,
            "intervention": self.intervention,
            "first_frame": self.scene_start,
            "frame_count": self.frames_written,
            "intervention_frame": self.event_start,
        }


def _scene_card(
    writer: RawVideoWriter,
    *,
    body: str,
    description: str,
) -> None:
    writer.write(
        _text_card(
            writer.width,
            writer.height,
            eyebrow="FROM SCRATCH  /  NO PRETRAINED CONTROLLER",
            title=body,
            subtitle=description,
        ),
        repeat=writer.fps,
    )


def _ground_scenes(writer: RawVideoWriter) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    cases = (
        {
            "morphology": "r2d2",
            "name": "R2D2  /  DIFFERENTIAL DRIVE",
            "description": (
                "A fresh graph maps nine opaque actions, then navigates after\n"
                "an abrupt right-drive loss."
            ),
            "intervention": "DAMAGE: right drive effectiveness drops to 20%",
            "condition": MechanicalCondition(
                onset_action=45,
                abrupt_retention=(1.0, 0.2),
            ),
            "randomization": MechanicalRandomization(
                base_mass_scale=0.64,
                lateral_friction=0.39,
                rolling_friction=0.027,
                motor_force_scale=1.12,
            ),
            "offset": (-1.65, -0.9, 0.0),
            "seed": 84301,
        },
        {
            "morphology": "husky",
            "name": "HUSKY  /  SKID STEER",
            "description": (
                "The same substrate starts empty on a four-wheel body, then\n"
                "adapts while one drive channel progressively wears."
            ),
            "intervention": "WEAR BEGINS: left drive degrades with accumulated use",
            "condition": MechanicalCondition(
                onset_action=45,
                wear_per_use=(0.026, 0.0),
                minimum_retention=0.2,
            ),
            "randomization": MechanicalRandomization(
                base_mass_scale=0.86,
                lateral_friction=0.74,
                rolling_friction=0.018,
                motor_force_scale=1.25,
            ),
            "offset": (1.9, 0.45, 0.0),
            "seed": 84303,
        },
        {
            "morphology": "racecar",
            "name": "RACECAR  /  STEER + DRIVE",
            "description": (
                "A nonholonomic body is learned from receipts alone before a\n"
                "severe steering-channel failure."
            ),
            "intervention": "DAMAGE: steering authority drops to 8%",
            "condition": MechanicalCondition(
                onset_action=45,
                abrupt_retention=(1.0, 0.08),
                minimum_retention=0.08,
            ),
            "randomization": MechanicalRandomization(
                base_mass_scale=0.73,
                lateral_friction=1.34,
                rolling_friction=0.001,
                motor_force_scale=0.79,
            ),
            "offset": (1.05, -1.8, 0.0),
            "seed": 84305,
        },
    )
    manifests = []
    results: dict[str, Any] = {}
    for case in cases:
        _scene_card(
            writer,
            body=case["name"],
            description=case["description"],
        )
        capture = SceneCapture(
            writer,
            body_name=case["name"],
            simulator="PYBULLET",
            intervention=case["intervention"],
        )
        result = run_episode(
            case["morphology"],
            "adaptive_damage_navigation",
            steps=150,
            goal=(0.0, 0.0, 0.0),
            seed=case["seed"],
            babble_samples=3,
            mechanical_condition=case["condition"],
            mechanical_randomization=case["randomization"],
            post_calibration_goal_offset=case["offset"],
            goal_change_epoch=45,
            observer=capture,
        )
        manifests.append(capture.manifest())
        results[case["morphology"]] = {
            "final_goal_distance": result["final_goal_distance"],
            "goal_reached": result["goal_reached_graph_assessment"],
            "action_count": len(result["trace"]),
        }
    return manifests, results


def _aerial_scene(writer: RawVideoWriter) -> tuple[dict[str, Any], dict[str, Any]]:
    _scene_card(
        writer,
        body="CRAZYFLIE  /  QUADROTOR",
        description=(
            "The graph learns flight from opaque commands. Mid-air, one\n"
            "propeller disappears completely and direct authority takes over."
        ),
    )
    capture = SceneCapture(
        writer,
        body_name="CRAZYFLIE  /  QUADROTOR",
        simulator="PYBULLET DRONES",
        intervention="DAMAGE: propeller 2 loses all thrust and reaction torque",
        strides={
            "failure_detection": 2,
            "direct_recovery": 30,
        },
    )
    result = run_direct_recovery(observer=capture)
    return capture.manifest(), {
        "detection_latency_seconds": result["detection_latency_seconds"],
        "failed_motor_ordinal_graph": result["failed_motor_ordinal_graph"],
        "recovery_control_hz": result["recovery_control_hz"],
        "hold_position_error": result["hold_position_error"],
    }


def _humanoid_scene(
    writer: RawVideoWriter,
    *,
    benchmark_root: Path,
    benchmark: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if benchmark:
        protocol_path = ROOT / "protocols" / "humanoid_bench_h1_walk_v1.json"
        body_name = "H1  /  HUMANOIDBENCH"
        simulator = "MUJOCO"
        description = (
            "The same graph transfers cold to the official H1 body, learns\n"
            "joint effects and synergies, then receives an unseen lateral shove."
        )
    else:
        protocol_path = ROOT / "protocols" / "humanoid_walking_v1.json"
        body_name = "HUMANOID  /  17 JOINTS"
        simulator = "PYBULLET"
        description = (
            "Single-joint effects become arbitrary combined movements and a\n"
            "walking program, followed by an unexpected two-body-weight shove."
        )
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if benchmark:
        protocol = copy.deepcopy(protocol)
        protocol["locomotion"]["perturbation"] = {
            "onset_fraction": 0.1,
            "world_frame_force_body_weights": [0.0, 2.0, 0.0],
            "frames": 1,
        }
    _scene_card(writer, body=body_name, description=description)
    capture = SceneCapture(
        writer,
        body_name=body_name,
        simulator=simulator,
        intervention=(
            "PERTURBATION: unexpected lateral shove at 2× body weight"
            if benchmark
            else "PERTURBATION: unexpected forward shove at 2× body weight"
        ),
        strides={
            "synergy_learning": 16,
            "gait_adaptation": 4,
            "walking": 3 if not benchmark else 2,
        },
    )
    if benchmark:
        environment_id = str(protocol["environment_id"])

        def world_factory(configuration, seed):
            return HumanoidBenchWorld(
                configuration,
                simulator_root=benchmark_root,
                environment_id=environment_id,
                seed=seed,
            )

        result = _run_arm(
            protocol,
            "directed_walk",
            world_factory=world_factory,
            observer=capture,
        )
    else:
        result = _run_arm(
            protocol,
            "directed_walk",
            observer=capture,
        )
    return capture.manifest(), {
        "directed_progress": result["directed_progress"],
        "support_alternations": result["support_alternations"],
        "first_fall_action": result["first_fall_action"],
        "perturbation_action": result["perturbation"]["onset_action"],
        "recovery_mode_entries": result["recovery_mode_entries"],
    }


def render_showcase(
    output: Path,
    *,
    benchmark_root: Path,
    width: int = 960,
    height: int = 540,
    fps: int = 24,
) -> dict[str, Any]:
    os.environ.setdefault("MUJOCO_GL", "egl")
    writer = RawVideoWriter(output, width=width, height=height, fps=fps)
    manifests: list[dict[str, Any]] = []
    results: dict[str, Any] = {}
    try:
        writer.write(
            _text_card(
                width,
                height,
                eyebrow="ANALYSIS BY SYNTHESIS  /  GRAPH-NATIVE CONTROL",
                title="One substrate. Six bodies.",
                subtitle=(
                    "Cold start → learned action models → composed behaviour\n"
                    "→ perturbation, damage, and online adaptation"
                ),
            ),
            repeat=fps * 2,
        )
        ground_manifests, ground_results = _ground_scenes(writer)
        manifests.extend(ground_manifests)
        results["ground"] = ground_results
        aerial_manifest, aerial_result = _aerial_scene(writer)
        manifests.append(aerial_manifest)
        results["aerial"] = aerial_result
        humanoid_manifest, humanoid_result = _humanoid_scene(
            writer,
            benchmark_root=benchmark_root,
            benchmark=False,
        )
        manifests.append(humanoid_manifest)
        results["humanoid"] = humanoid_result
        benchmark_manifest, benchmark_result = _humanoid_scene(
            writer,
            benchmark_root=benchmark_root,
            benchmark=True,
        )
        manifests.append(benchmark_manifest)
        results["humanoid_bench_h1"] = benchmark_result
        writer.write(
            _text_card(
                width,
                height,
                eyebrow="THE POLICY STAYS IN THE GRAPH",
                title="Learn. Compose. Adapt.",
                subtitle=(
                    "No pretrained controller • no gradient descent\n"
                    "One graph substrate across every body plan shown"
                ),
            ),
            repeat=fps * 2,
        )
    finally:
        writer.close()
    return {
        "video": str(output),
        "width": width,
        "height": height,
        "fps": fps,
        "frame_count": writer.frame_count,
        "duration_seconds": writer.frame_count / fps,
        "scenes": manifests,
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--humanoid-bench-root",
        type=Path,
        default=DEFAULT_HUMANOID_BENCH,
    )
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=540)
    parser.add_argument("--fps", type=int, default=24)
    args = parser.parse_args(argv)
    manifest = render_showcase(
        args.output.resolve(),
        benchmark_root=args.humanoid_bench_root.resolve(),
        width=args.width,
        height=args.height,
        fps=args.fps,
    )
    manifest_path = args.output.with_suffix(".json")
    manifest_path.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "video": str(args.output),
        "manifest": str(manifest_path),
        "duration_seconds": manifest["duration_seconds"],
        "scenes": len(manifest["scenes"]),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
