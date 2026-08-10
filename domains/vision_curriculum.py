"""vision_curriculum — the DEVELOPMENTAL VISION CURRICULUM (Stage 2).

The world-adapter grounder the standing study loop (`curriculum_study.
study_tick`) routes a vision `StudyLesson` to, so the agent SELF-RUNS a staged
visual curriculum over real material and grows its own visual codebook -- no
human per-lesson call, donkey=0 throughout (BSDS300 photographs, real
children's television via the existing Jellyfin world, and real Omniglot pen
ink are all offline/real references, never an LLM).

This mirrors `voice_curriculum.py` exactly: `prepare_lesson_plan` chunks real
source material into lesson files, `install_vision_curriculum` hands them to
`curriculum_study.install_curriculum`, and `learn_vision_from_lesson` is the
ONE entry point `study_tick` dispatches to on the lesson's OWN `kind` graph
attr. The lesson lifecycle DECISIONS (blocked / done / reopen-on-growth) are
the EXISTING kind-agnostic seed rules in `seeds/curriculum_study.json`,
unchanged but for one added `vision_codebook_epoch` Or-arm -- the same single
edit the voice wave needed.

ARCHITECTURE (CLAUDE.md). Every function here is mechanical I/O: load a frame
from disk, hand its pixels to `VisionWorld.ingest`, `tick()`, and COUNT what
the graph did. It decides nothing. In particular the growth decisions -- when
an unexplained patch becomes a new receptive field, which kernel learns from a
patch, how fast -- are `seeds/vision_growth.json`'s rules
(`vg_mint_kernel_from_patch` / `vg_learn_kernel_oja`) and the `KernelGrowth`
node's graph-data knobs. `_bump_vision_epoch` is the SAME "Python builder bumps
an epoch on measured novelty" idiom `voice_curriculum._bump_voice_epoch` uses:
a FACT (n genuinely new kernels exist after this call), never a decision about
which lesson cares.

WHAT IS AND IS NOT CLAIMED (see VISION_DEVELOPMENT_ARC.md, "The T9/T11
retraction"). The `babble` level grows receptive fields from real image
statistics -- genuinely: the pool starts EMPTY and a kernel's initial weights
ARE an image patch the agent could not already explain. What that does NOT
license is the older "biology emerged" claim: patches arrive DC-removed and
contrast-normalised (`vision_corpus.preprocess_patches`), which is itself a
retina-like front end, and a minted kernel inherits whatever orientation
natural-image statistics already carry. The honest measure is a DELTA over a
raw-patch control, reported in the Stage-2 arc notes.
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

import numpy as np

from domains import vision_corpus as vcorp

_ROOT = __file__.rsplit("/domains/", 1)[0]
_DATA_DIR = os.path.join(_ROOT, "data", "vision_curriculum")
_LESSON_DIR = os.path.join(_DATA_DIR, "lessons")
_FRAME_DIR = os.path.join(_DATA_DIR, "frames")

# The lesson kinds `study_tick` routes here. `babble` (L0) is the level this
# wave implements end-to-end; the remaining levels of the plan's ladder
# (tracking / permanence / transform-invariance / composition) are NOT built
# yet and are deliberately absent rather than stubbed, so a lesson can never
# silently "pass" a level that does not exist.
VISION_KINDS = ("babble",)


def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    ag_node = None
    for n in sub.nodes("Agent"):
        if not sub.node(n)["attrs"].get("is_class"):
            ag_node = n
            break
    return sub, native, ag_node


def fresh_vision_world(agent):
    """A `VisionWorld` over the agent's OWN live substrate + agent root -- a
    rebuildable query/ingest handle, never agent state (the substrate is the
    source of truth). Mirrors `voice_curriculum.fresh_voice_world`."""
    from domains.vision_world import VisionWorld
    sub, _native, ag = _resolve(agent)
    return VisionWorld(sub, ag)


def _bump_vision_epoch(sub, ag, delta: int) -> None:
    """Mechanical epoch bump. `delta` is a COUNT of genuinely new grown Kernel
    nodes this call produced (measured from a before/after count), never a
    decision. Bumping it re-arms `study_lesson_reopen_on_growth`'s vision arm."""
    if ag is None or delta <= 0:
        return
    cur = sub.node(ag)["attrs"].get("vision_codebook_epoch")
    if cur is None:
        cur = 0.0
    sub.set_attr(ag, "vision_codebook_epoch", float(cur) + float(delta))


def _grown_kernels(sub) -> list:
    return [k for k in sub.nodes("Kernel")
            if sub.node(k)["attrs"].get("grown") == 1.0]


def _tabula_rasa(sub) -> int:
    """Detach the six hand-designed `designed:1.0` kernels from the candidate
    pool so growth starts from ZERO.

    Mechanical (it removes edges; it decides nothing), and load-bearing for the
    claim: leaving the designed pool in place would let hand-authored
    centre_surround/edge_axis1 kernels win the winner-take-all competition, so
    any structure measured afterwards would again be structure that was
    planted. Returns how many were detached."""
    facs = sub.nodes("ConvFaculty")
    if not facs:
        return 0
    fac = facs[0]
    n = 0
    for k in list(sub.neighbours(fac, "has_kernel")):
        if sub.node(k)["attrs"].get("designed") == 1.0:
            sub.remove_edge(fac, "has_kernel", k)
            n += 1
    return n


# --------------------------------------------------------------------------- #
#  LEVEL L0 — BABBLE. Chunk format: one `<npy_path>` per line; each .npy is an
#  (m, k, k) float32 batch of DC-removed, contrast-normalised patches.
# --------------------------------------------------------------------------- #
def _learn_babble(agent, world, text: str) -> dict[str, Any]:
    sub, _native, ag = _resolve(agent)
    _tabula_rasa(sub)
    before = len(_grown_kernels(sub))
    attempted = 0
    answered = 0
    for ln in text.splitlines():
        path = ln.strip()
        if not path or path.startswith("#"):
            continue
        if not os.path.isabs(path):
            path = os.path.join(_ROOT, path)
        if not os.path.exists(path):
            continue
        batch = np.load(path)
        for patch in batch:
            attempted += 1
            k = int(patch.shape[0])
            world.ingest(patch.flatten().tolist(), k, k, kh=k, kw=k, stride=k)
            # The GRAPH does the work: vg_mint_kernel_from_patch decides
            # whether this patch is unexplained enough to become a receptive
            # field, and vg_learn_kernel_oja runs one Oja step on the winner.
            # This adapter only handed over the pixels.
            sub.tick(200_000)
            answered += 1
    after = len(_grown_kernels(sub))
    grounded = max(0, after - before)
    _bump_vision_epoch(sub, ag, grounded)
    return {"kind": "babble", "attempted": attempted, "answered": answered,
            "grounded": grounded, "kernels": after}


# --------------------------------------------------------------------------- #
#  DISPATCH — the ONE entry point curriculum_study.study_tick calls, routed by
#  the lesson's OWN `kind` graph attr (a mechanical read, not a content sniff).
# --------------------------------------------------------------------------- #
def learn_vision_from_lesson(agent, world, text: str, kind: str) -> dict[str, Any]:
    if kind == "babble":
        return _learn_babble(agent, world, text)
    # An unbuilt level is reported honestly (attempted 0 / answered 0), never
    # faked -- study_lesson_done_clean will settle it, and the absence shows
    # up in the roadmap rather than passing silently.
    return {"kind": kind, "attempted": 0, "answered": 0, "grounded": 0}


# --------------------------------------------------------------------------- #
#  LESSON PREPARATION — chunk real source material into lesson files. Mechanical,
#  deterministic, idempotent (same params -> same bytes).
# --------------------------------------------------------------------------- #
def prepare_babble_lessons(*, n_patches: int = 400, chunk: int = 100,
                           crop: int = 7, seed: int = 3,
                           source: str = "bsds",
                           episode_id: Optional[str] = None,
                           lesson_dir: Optional[str] = None) -> list[tuple]:
    """Write babble lesson chunks and return `[(order, title, path, kind), ...]`.

    `source="bsds"`     -- BSDS300 natural photographs (the natural-image-
                           statistics setting; the non-circular control).
    `source="jellyfin"` -- real children's developmental television, decoded
                           through the EXISTING `scripts/jellyfin_world`
                           adapter. Closest obtainable stand-in for the
                           literature steer's child-perspective video (SAYCam
                           is gated behind a Databrary application); it is
                           broadcast child-directed video, NOT egocentric --
                           named honestly, not papered over.
    """
    lesson_dir = lesson_dir or _LESSON_DIR
    os.makedirs(lesson_dir, exist_ok=True)
    os.makedirs(_FRAME_DIR, exist_ok=True)

    if source == "bsds":
        raw = vcorp.bsds_crops(n=int(n_patches * 2.4), crop=crop, seed=seed)
    elif source == "jellyfin":
        jf = vcorp._jellyfin()
        if episode_id is None:
            raise ValueError("source='jellyfin' needs episode_id")
        raw = vcorp.episode_crops(jf, episode_id, n=int(n_patches * 2.4),
                                  crop=crop, seed=seed)
    else:
        raise ValueError(f"unknown source {source!r}")
    P = vcorp.preprocess_patches(raw)[:n_patches]

    plan: list[tuple] = []
    for i in range(0, len(P), chunk):
        part = P[i:i + chunk]
        idx = i // chunk
        npy = os.path.join(_FRAME_DIR, f"babble_{source}_{idx:03d}.npy")
        np.save(npy, np.ascontiguousarray(part, np.float32))
        path = os.path.join(lesson_dir, f"babble_{source}_{idx:03d}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# babble L0 — {len(part)} preprocessed {crop}x{crop} "
                    f"patches from {source}\n")
            f.write(npy + "\n")
        plan.append((len(plan), f"babble-{source}-{idx:03d}", path, "babble"))
    return plan


def install_vision_curriculum(agent, *, title: str = "Vision Development",
                              **plan_kwargs) -> dict[str, Any]:
    """Prepare the lesson chunks (idempotent) and install them as one
    `Curriculum` via `curriculum_study.install_curriculum` -- the standing
    study loop then self-runs it, one `study_tick` per lesson, no human
    per-lesson call."""
    from domains import curriculum_study as cs
    plan = prepare_babble_lessons(**plan_kwargs)
    return cs.install_curriculum(agent, title, plan, source=_DATA_DIR)


__all__ = [
    "VISION_KINDS", "fresh_vision_world", "learn_vision_from_lesson",
    "prepare_babble_lessons", "install_vision_curriculum",
]
