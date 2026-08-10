"""VisionWorld — the thin vision world adapter (CLAUDE.md: mechanical
ingest -> tick -> read, NO decisions). Mirrors ChatWorld's shape: it only
translates external image bytes into substrate mutations and reads grown
graph state back out. Every DECISION is graph-resident (the vision_floor
seed rules + the reused sensory_convolution keep_discriminative_kernel).

    image in -> Image + Sense + Field + Patch nodes -> tick() -> read
    kept codebook + recognized shapes out

What this adapter does (mechanical I/O only):
  * INGEST — lay an Image node {vals, h, w, status:"raw"} and wire it
    ``agent -observed-> img``. Lay ONE vision Sense node and wire
    ``agent -has_vision_sense-> sense`` + ``agent -has_conv_faculty-> fac``
    (the sensory_convolution ConvFaculty, found by type — there is exactly
    one). Slice the image into non-overlapping kxk windows; each window
    becomes a Patch (flattened vals) under its own labelled Field
    (``sense -has_field-> field -has_patch-> patch``). The field label is
    the window's grid INDEX — a positional label, mechanical like ChatWorld
    splitting text on whitespace; NO content decision.
  * HAND OFF — ``s.tick()`` runs the vision_floor rules (vf_arm_candidate_pool
    mints sense -considers-> fac; vf_foveate_observation foveates) and the
    REUSED sensory_convolution keep_discriminative_kernel, which KEEPS the
    kernels whose response spread across the labelled fields discriminates
    — so center-surround / oriented kernels EMERGE from the image stats.
  * EMIT — read the sense's ``kept_kernel`` edges back out as the grown
    codebook; read recognized shapes off the ShapeDecode codebook.

No `if` over graph state, no Python rule engine, no agent state. The
``considers`` edge is minted by the graph-native ``vf_arm_candidate_pool``
rule (the agent's own arming decision), NOT by this adapter.
"""
from __future__ import annotations

from typing import Any, Optional


def _add_edge(s, src, et, tgt):
    """Insert an edge, tolerating both add_edge arities (the codebase's
    idempotent helper). Mechanical."""
    try:
        s.add_edge(src, et, tgt, None)
    except TypeError:
        s.add_edge(src, et, tgt)


class VisionWorld:
    """The vision world adapter. Construct with a booted substrate + the
    agent root NodeID (the ``boot_core`` / ``load_seeds_into`` return)."""

    def __init__(self, s, agent_root):
        self.s = s
        self.agent = agent_root

    def _first(self, type_: str) -> Optional[Any]:
        """First node of `type_` (a mechanical singleton query — e.g. the
        sensory_convolution ConvFaculty, the vision_floor SamplingGeometry).
        Returns None if absent (the caller decides whether that's fatal)."""
        ns = self.s.nodes(type_)
        return ns[0] if ns else None

    def ingest(self, vals, h: int, w: int, *, kh: int = 3, kw: int = 3,
               stride: int = 3) -> Any:
        """Ingest one image (a flat row-major `vals` buffer of len h*w) as
        graph data: an Image node + a vision Sense + labelled Field/Patch
        nodes per non-overlapping kxk window. Mechanical slicing (positional
        labels), no content decision. Wires the agent edges the vision_floor
        rules match on (observed / has_vision_sense / has_conv_faculty /
        has_sampling_geometry). Returns the Image node."""
        fvals = [float(v) for v in vals]
        img = self.s.add_node("Image", {"vals": fvals, "h": float(h),
                                        "w": float(w), "status": "raw"})
        _add_edge(self.s, self.agent, "observed", img)

        # One vision Sense + arm the agent edges the rules read. The
        # considers edge is NOT minted here — vf_arm_candidate_pool (a
        # vision_floor rule) mints it as the agent's own arming decision.
        sense = self.s.add_node("Sense", {"name": "vision"})
        _add_edge(self.s, self.agent, "has_vision_sense", sense)
        fac = self._first("ConvFaculty")
        if fac is not None:
            _add_edge(self.s, self.agent, "has_conv_faculty", fac)
        geom = self._first("SamplingGeometry")
        if geom is not None:
            _add_edge(self.s, self.agent, "has_sampling_geometry", geom)

        # Slice into non-overlapping kxk windows; each window -> its own
        # labelled Field (label = grid index, positional) with one Patch.
        win = 0
        for r0 in range(0, h - kh + 1, stride):
            for c0 in range(0, w - kw + 1, stride):
                patch_vals = []
                for ky in range(kh):
                    row = (r0 + ky) * w
                    for kx in range(kw):
                        patch_vals.append(fvals[row + c0 + kx])
                # Mechanical boundary geometry (the same attrs segment_and_track
                # produces: cy/cx center, drow/dcol half-extents). I/O metadata
                # for the region-as-belief rules to copy onto a Region node —
                # NOT a decision (the slicing position is mechanical).
                cy = r0 + (kh - 1) / 2.0
                cx = c0 + (kw - 1) / 2.0
                drow = (kh - 1) / 2.0
                dcol = (kw - 1) / 2.0
                field = self.s.add_node("Field", {
                    "label": str(win), "cy": cy, "cx": cx,
                    "drow": drow, "dcol": dcol})
                _add_edge(self.s, sense, "has_field", field)
                patch = self.s.add_node("Patch", {"vals": patch_vals})
                _add_edge(self.s, field, "has_patch", patch)
                win += 1
        return img

    def kept_kernels(self) -> list:
        """Read the grown codebook back out: every Kernel the vision Sense
        kept (sense -kept_kernel-> Kernel). Pure graph query — the source of
        truth is the substrate, not adapter state. Returns [(kernel_node,
        weights, name)]."""
        out = []
        for sn in self.s.nodes("Sense"):
            for kn in self.s.neighbours(sn, "kept_kernel"):
                a = self.s.node(kn)["attrs"]
                out.append((kn, a.get("weights"), a.get("name")))
        return out

    def recognized_shapes(self) -> list:
        """Read recognized shapes off the ShapeDecode codebook (the ventral
        identity codebook grown via the sd_* loop). Pure query."""
        try:
            return list(self.s.nodes("ShapeSignature"))
        except Exception:
            return []

    def teach_kept_kernels(self, agent, *, seeds_dir=None) -> list:
        """Persist the grown codebook via the recurring teach() facility —
        the teach hook for vision. Files every kept Kernel under the
        ``vision_codebook`` category (the agent's own filing; re-teaching the
        same weights is a no-op, so a fresh boot holds them too). Mechanical
        host I/O — WHICH kernels to keep is the graph's call (the
        keep_discriminative_kernel rule); this only DURABLES what it kept."""
        from domains.teach import teach
        filed = []
        for kn, weights, name in self.kept_kernels():
            if not weights:
                continue
            attrs = {"name": name or "kept", "weights": list(weights),
                     "kh": 3.0, "kw": 3.0, "designed": 0.0,
                     "source": "vision_floor_keep",
                     "comment": "kernel kept by keep_discriminative_kernel"}
            r = teach(agent, "Kernel", attrs,
                      category="vision_codebook", seeds_dir=seeds_dir)
            filed.append(r)
        return filed
