"""Policy-free body-relative receipts for arbitrary planar path geometry."""
from __future__ import annotations

from dataclasses import dataclass
import math


def wrap_angle(value: float) -> float:
    return (value + math.pi) % (2.0 * math.pi) - math.pi


@dataclass(frozen=True)
class PreviewReceipt:
    forward_m: float
    lateral_m: float
    bearing_error_rad: float
    heading_error_rad: float


def preview_receipt(
    *,
    observer_x_m: float,
    observer_y_m: float,
    observer_yaw_rad: float,
    target_x_m: float,
    target_y_m: float,
    target_heading_rad: float,
) -> PreviewReceipt:
    """Express one externally supplied path sample in the observer body frame."""
    delta_x = target_x_m - observer_x_m
    delta_y = target_y_m - observer_y_m
    cosine = math.cos(observer_yaw_rad)
    sine = math.sin(observer_yaw_rad)
    forward = cosine * delta_x + sine * delta_y
    lateral = -sine * delta_x + cosine * delta_y
    return PreviewReceipt(
        forward_m=forward,
        lateral_m=lateral,
        bearing_error_rad=math.atan2(lateral, forward),
        heading_error_rad=wrap_angle(
            target_heading_rad - observer_yaw_rad
        ),
    )


__all__ = ["PreviewReceipt", "preview_receipt", "wrap_angle"]
