"""D6.1 executable contract for lattice-preserving detached rotation work."""
from __future__ import annotations

from dataclasses import dataclass

LATTICE = (0, 90, 180, 270)


def shortest_rotation(source_angle: int, target_angle: int) -> tuple[int, ...]:
    """Return signed 90-degree increments on the registered square lattice."""
    if source_angle not in LATTICE or target_angle not in LATTICE:
        raise ValueError("angle is outside the registered lattice")
    clockwise = ((target_angle - source_angle) % 360) // 90
    counterclockwise = ((source_angle - target_angle) % 360) // 90
    if clockwise <= counterclockwise:
        return (90,) * clockwise
    return (-90,) * counterclockwise


def rotate(points: frozenset[tuple[int, int]], direction: int) -> frozenset[tuple[int, int]]:
    """One exact quarter turn, normalized to the minimum row/column origin."""
    if direction == 90:
        transformed = {(c, -r) for r, c in points}
    elif direction == -90:
        transformed = {(-c, r) for r, c in points}
    else:
        raise ValueError("only quarter-turn increments are supported")
    min_r = min(r for r, _ in transformed)
    min_c = min(c for _, c in transformed)
    return frozenset((r - min_r, c - min_c) for r, c in transformed)


@dataclass(frozen=True)
class ImageryBuffer:
    source: frozenset[tuple[int, int]]
    imagined: frozenset[tuple[int, int]]
    witnesses: tuple[frozenset[tuple[int, int]], ...]
    grounded: bool = False


def imagine_rotation(source, source_angle, target_angle):
    state = frozenset(source)
    witnesses = [state]
    for step in shortest_rotation(source_angle, target_angle):
        state = rotate(state, step)
        witnesses.append(state)
    return ImageryBuffer(frozenset(source), state, tuple(witnesses))


def test_angle_wrap_and_identity():
    assert shortest_rotation(270, 0) == (90,)
    assert shortest_rotation(0, 270) == (-90,)
    assert shortest_rotation(180, 180) == ()
    source = {(0, 0), (0, 1), (1, 1)}
    assert imagine_rotation(source, 90, 90).imagined == frozenset(source)


def test_intermediate_witnesses():
    buffer = imagine_rotation({(0, 0), (0, 1), (1, 1)}, 0, 180)
    assert len(buffer.witnesses) == 3
    assert buffer.witnesses[0] == buffer.source
    assert buffer.witnesses[-1] == buffer.imagined
    assert buffer.witnesses[1] != buffer.witnesses[0]


def test_buffer_never_grounds():
    buffer = imagine_rotation({(0, 0), (0, 1)}, 0, 90)
    assert buffer.grounded is False
    assert buffer.source == frozenset({(0, 0), (0, 1)})


def test_cost_counts_executed_transforms():
    for start, end, expected in ((0, 0, 0), (0, 90, 1), (0, 180, 2), (270, 0, 1)):
        assert len(imagine_rotation({(0, 0), (0, 1)}, start, end).witnesses) - 1 == expected


def test_arbitrary_angles_remain_unresolved():
    try:
        shortest_rotation(0, 45)
    except ValueError:
        pass
    else:
        raise AssertionError("unsupported arbitrary angle was accepted")
