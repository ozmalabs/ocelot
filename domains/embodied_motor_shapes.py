"""Mechanical relation-system encodings for motor memory shape math."""
from __future__ import annotations

from typing import Any, Mapping, Sequence


def motor_program_shape_signature(
    program_attrs: Mapping[str, Any],
    members: Sequence[Mapping[str, Any]],
) -> tuple[tuple[Any, ...], ...]:
    """Expose program structure to ShapeDecode without judging its value."""
    relations: list[tuple[Any, ...]] = [
        (
            "motor_task_context",
            str(program_attrs.get("motor_task_context", "locomotion")),
        ),
        (
            "motor_task_phase",
            str(program_attrs.get("motor_task_phase", "preparation")),
        ),
        (
            "motor_task",
            str(program_attrs.get("motor_task_context", "locomotion")),
            str(program_attrs.get("motor_task_phase", "preparation")),
        ),
        (
            "support_context",
            float(program_attrs.get("support_phase", -1.0)),
            float(program_attrs.get("jump_schema_id", 0.0)),
        ),
    ]
    for role_ordinal, member in enumerate(sorted(
        members,
        key=lambda row: (
            float(row.get("ordinal", 0.0)),
            str(row.get("token", "")),
        ),
    )):
        relations.append((
            "motor_member",
            float(role_ordinal),
            str(member.get("token", "")),
            float(member.get("support_phase", -1.0)),
        ))
    return tuple(relations)


__all__ = ["motor_program_shape_signature"]
