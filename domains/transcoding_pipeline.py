"""TranscodingPipeline — a non-agent world adapter that drives a real
ladder transcode through the substrate.

The transcoding seed gives the ontology: TranscodeJob, Ladder,
LadderRung, plus a default 3-tier ABR ladder. This adapter is the
"world": it ingests an external frame (raw luma plane bytes), mints
the graph structure for a full ladder transcode, then walks the
graph and dispatches each TranscodeJob to the appropriate Rust
primitive.

Same shape as ChatWorld / AudioWorld — attach loads the seeds, an
ingest method translates external data into substrate mutations,
an execute method walks the graph. The difference: no agent. The
pipeline operates on a bare ``substrate_rs.Substrate``.

What's wired
------------
Each TranscodeJob currently dispatches to one of:
  * ``kind = "downscale"`` — chained 2:1 area-average until the
    output dimensions are hit (uses ``h264_area_average_2to1``,
    the same SIMD primitive the H.264 transcoder uses internally).

The dispatch is graph-driven: the job's ``kind`` attr decides which
primitive runs. Adding a new transcode kind = adding a new dispatch
case here (and ideally a new graph-resident Rule the pipeline
consults — that's a follow-up).

Plane storage
-------------
Raw plane bytes don't live in graph attrs — they live in
``self._planes`` keyed by NodeID. The graph holds the lightweight
schema (which streams feed which jobs, what dimensions, what
status), the pipeline holds the bytes. This keeps the substrate
free of multi-megabyte attr values while still letting the graph
drive every decision.
"""
from __future__ import annotations

import json as _json
import math
import pathlib as _pathlib
from dataclasses import dataclass, field
from typing import Any

_SEED_DIR = _pathlib.Path(__file__).resolve().parent.parent / "seeds"


def _manifest_for(seed_id: str) -> dict:
    """Read seeds/<id>.json (pure file I/O); the Rust runtime's
    ``Substrate.load_seed_manifest`` does the graph mutation. Replaces
    the legacy ``substrate.seed_loader.manifest_for``."""
    return _json.loads((_SEED_DIR / f"{seed_id}.json").read_text())


@dataclass
class TranscodingPipeline:
    """A bare-substrate transcoding pipeline.

    Lifecycle: attach → ingest_frame → execute. attach is idempotent.
    Each ingest_frame builds a fresh Ladder for that input frame
    (so multiple frames + multiple ladders coexist; the graph keeps
    the relationships straight).
    """
    # External plane storage. The graph holds VideoStream NodeIDs;
    # this dict maps each NodeID to the raw plane bytes. Output
    # streams' planes are populated by execute().
    _planes: dict = field(default_factory=dict)

    # --- attach -----------------------------------------------------

    def attach(self, sub) -> None:
        """Load the video + transcoding seeds onto a bare substrate.
        Idempotent: a seed already present (productions + default
        ladder rungs already there) is a no-op via the loader's
        own idempotence."""
        for seed_id in ("video", "transcoding"):
            try:
                sub.load_seed_manifest(_manifest_for(seed_id))
            except Exception:
                # Idempotent re-attach: duplicate productions raise
                # under the hood; the seed nodes themselves are
                # additive but we don't re-mint the default ladder
                # — check before adding.
                pass

    # --- ingest -----------------------------------------------------

    def ingest_frame(self, sub, luma_bytes: bytes,
                       width: int, height: int,
                       *, kind: str = "downscale") -> dict:
        """Take a single luma plane + its dimensions. Mints:

          * a VideoStream node for the source (the plane bytes go
            into self._planes under that NodeID)
          * a Ladder node with a `has_input` edge to the source
          * for each LadderRung the transcoding seed installed,
            an output VideoStream + a TranscodeJob{kind} wiring it up

        ``kind`` chooses how each rung is realised:
          - ``"downscale"`` — pixel-domain area-average (default;
            cheap, produces raw luma plane bytes)
          - ``"transrate"`` — full H.264 re-encode at a target QP
            (produces CABAC bytes ready for container mux)

        The kind lands on each TranscodeJob; the dispatch Rules
        installed by the transcoding seed translate it to a
        primitive name at tick time. Returns NodeIDs for the source,
        ladder, and per-rung output streams.
        """
        if len(luma_bytes) != width * height:
            raise ValueError(
                f"luma plane size {len(luma_bytes)} != "
                f"width*height {width*height}")
        source = sub.add_node("VideoStream", {
            "codec": "h264_planar",
            "role": "source",
            "width": width,
            "height": height,
        })
        self._planes[source] = luma_bytes

        ladder = sub.add_node("Ladder", {"profile": "hls_3tier"})
        sub.add_edge(ladder, "has_input", source)

        outputs: dict = {}
        for rung in sub.nodes("LadderRung"):
            rung_attrs = sub.node(rung)["attrs"]
            target_w = rung_attrs["width"]
            target_h = rung_attrs["height"]
            # Only downscale by 2:1 powers — non-power-of-2 ratios
            # need a different primitive, which is a follow-up.
            ratio = width / target_w
            if ratio < 1 or abs(ratio - round(ratio)) > 1e-6 \
                    or (int(ratio) & (int(ratio) - 1)) != 0:
                # Skip rungs we can't currently realise.
                continue

            output = sub.add_node("VideoStream", {
                "codec": "h264_planar",
                "role": "rung_output",
                "width": target_w,
                "height": target_h,
                "bitrate_kbps": rung_attrs["bitrate_kbps"],
            })
            job = sub.add_node("TranscodeJob", {
                "kind": kind,
                "status": "pending",
            })
            sub.add_edge(job, "input", source)
            sub.add_edge(job, "output", output)
            sub.add_edge(rung, "produces", output)
            sub.add_edge(rung, "realised_by", job)
            outputs[rung_attrs["name"]] = output

        return {"source": source, "ladder": ladder, "outputs": outputs}

    # --- execute ----------------------------------------------------
    #
    # Dispatch (kind → primitive_name) is decided by graph-resident
    # Rules the transcoding seed installs — see _build_dispatch_rule_
    # attrs in domains/transcoding.py. Each Rule fires once per
    # pending job whose `kind` matches and whose `primitive` attr is
    # unset; the effect sets `primitive` to the named callable.
    #
    # This loop is pure mechanical translation from graph state to
    # external Rust calls. It does NOT know "downscale" maps to
    # h264_area_average_2to1 — the substrate's tick wrote that fact
    # to job.primitive. Adding a new transcode kind = adding a new
    # Rule (graph data, no code change here) + adding a new entry in
    # _PRIMITIVES below.

    def execute(self, sub) -> int:
        """Tick the substrate so dispatch Rules fire, then walk
        TranscodeJobs whose `primitive` attr has been set and run
        the named Rust primitive. Output planes land in self._planes,
        job status flips to 'done'. Returns the count executed."""
        # Fire the substrate's tick — runs every graph-resident Rule
        # to fixed point. For transcoding that includes the
        # dispatch_<kind> Rules; for an agent that also includes the
        # intent / referent-resolution / response-goal Rules.
        sub.tick()

        executed = 0
        for job in list(sub.nodes("TranscodeJob")):
            attrs = sub.node(job)["attrs"]
            if attrs.get("status") == "done":
                continue
            primitive_name = attrs.get("primitive")
            if not primitive_name:
                # The dispatch Rule hasn't fired for this job (its
                # `kind` is unknown to any installed Rule, or the
                # tick hasn't reached it). Skip; the pipeline isn't
                # responsible for the decision.
                continue
            primitive_fn = self._PRIMITIVES.get(primitive_name)
            if primitive_fn is None:
                # Graph says to call X, pipeline doesn't know X. This
                # is a config bug; leave the job pending so the
                # mismatch is visible.
                continue
            primitive_fn(self, sub, job)
            sub.set_attr(job, "status", "done")
            executed += 1
        return executed

    def _execute_format_hop(self, sub, job) -> None:
        """H.264 NAL repacking: same codec, different container
        framing. Reads the input stream's bytes, rewraps them
        according to the job's ``target_framing`` attr, stores the
        result on the output stream.

        Real ffmpeg-pattern transcode step. Doesn't touch the
        sample / pixel domain — pure bitstream manipulation.

        target_framing values:
          - ``"annex_b"``: prepend a 4-byte 0x00 00 00 01 start code
            to each NAL unit (used by raw .h264 files + MPEG-TS).
          - ``"avcc"``: prepend a 4-byte big-endian length to each
            NAL unit (used inside MP4 / fMP4).
        """
        in_stream = next(iter(sub.neighbours(job, "input")))
        out_stream = next(iter(sub.neighbours(job, "output")))
        job_attrs = sub.node(job)["attrs"]

        target = job_attrs.get("target_framing", "annex_b")
        in_bytes = self._planes[in_stream]
        # The pipeline currently treats the input as one NAL unit
        # (an I-slice or P-slice payload). Real multi-NAL inputs
        # need splitting first — that's a future executor case
        # (a SubGOP / GOP node type would carry NAL boundaries).
        if target == "annex_b":
            out_bytes = b"\x00\x00\x00\x01" + in_bytes
        elif target == "avcc":
            out_bytes = len(in_bytes).to_bytes(4, "big") + in_bytes
        else:
            raise ValueError(
                f"format_hop: unknown target_framing {target!r}; "
                f"expected 'annex_b' or 'avcc'")
        self._planes[out_stream] = out_bytes
        sub.set_attr(out_stream, "framing", target)

    def chain_format_hop(self, sub, source_stream, target_framing: str,
                          output_codec: str = "h264") -> dict:
        """Append a format_hop TranscodeJob downstream of an existing
        output stream. The source stream is whatever upstream job
        produced (typically a transrate output); the new job rewraps
        its bytes into the requested framing and stores them on a
        fresh VideoStream.

        Returns ``{"job": NodeID, "output": NodeID}``. After calling,
        the caller runs ``pipe.execute(sub)`` to fire the chain.
        """
        src_attrs = sub.node(source_stream)["attrs"]
        output = sub.add_node("VideoStream", {
            "codec": output_codec,
            "role": "format_hop_output",
            "width": src_attrs.get("width", 0),
            "height": src_attrs.get("height", 0),
            "framing": target_framing,
        })
        job = sub.add_node("TranscodeJob", {
            "kind": "format_hop",
            "status": "pending",
            "target_framing": target_framing,
        })
        sub.add_edge(job, "input", source_stream)
        sub.add_edge(job, "output", output)
        return {"job": job, "output": output}

    def _execute_transrate(self, sub, job) -> None:
        """Real H.264 transrate: input luma plane → CABAC-encoded
        I-slice bytes at the rung's target resolution and QP.

        Uses ``h264_transcode_pyramid_full``, which produces N
        pyramid levels in a single SIMD pass — level i is a
        2**(i+1):1 downscale, fully encoded as H.264. We compute
        which level matches the output stream's target width and
        take its CABAC payload.

        Output dimensions must be a power-of-2 ratio of the input;
        non-power-of-2 transrates need a different primitive (a
        future row in _DISPATCH).
        """
        in_stream = next(iter(sub.neighbours(job, "input")))
        out_stream = next(iter(sub.neighbours(job, "output")))
        in_attrs = sub.node(in_stream)["attrs"]
        out_attrs = sub.node(out_stream)["attrs"]

        in_w = int(in_attrs["width"])
        in_h = int(in_attrs["height"])
        out_w = int(out_attrs["width"])
        n_levels = int(round(math.log2(in_w / out_w)))
        if n_levels < 1:
            raise ValueError(
                f"transrate requires out_w < in_w (got "
                f"{in_w} → {out_w})")

        qp = int(out_attrs.get("qp", 28))
        plane = self._planes[in_stream]
        rust = sub._inner if hasattr(sub, "_inner") else sub
        levels = rust.h264_transcode_pyramid_full(
            plane, in_w, in_h, qp, n_levels)
        # Level i is 2**(i+1):1; the deepest level matches the
        # target output width.
        out_w_actual, out_h_actual, mb_w, mb_h, payload = levels[-1]
        self._planes[out_stream] = bytes(payload)
        # Record the encoding metadata on the output stream so a
        # downstream container-mux step has the macroblock count
        # without parsing the bytes.
        sub.set_attr(out_stream, "encoded_width", int(out_w_actual))
        sub.set_attr(out_stream, "encoded_height", int(out_h_actual))
        sub.set_attr(out_stream, "mb_width", int(mb_w))
        sub.set_attr(out_stream, "mb_height", int(mb_h))
        sub.set_attr(out_stream, "qp", qp)

    def _execute_downscale(self, sub, job) -> None:
        """Chain 2:1 area-average halvings until the output stream's
        target dimensions are hit. Uses the SIMD-optimised Rust
        primitive ``h264_area_average_2to1``."""
        in_stream = next(iter(sub.neighbours(job, "input")))
        out_stream = next(iter(sub.neighbours(job, "output")))
        in_attrs = sub.node(in_stream)["attrs"]
        out_attrs = sub.node(out_stream)["attrs"]

        in_w = int(in_attrs["width"])
        in_h = int(in_attrs["height"])
        out_w = int(out_attrs["width"])

        n_halvings = int(round(math.log2(in_w / out_w)))
        plane = self._planes[in_stream]
        cur_w, cur_h = in_w, in_h
        # Reach through the Python wrapper to the Rust pyclass for the
        # codec primitive — the wrapper layer exposes graph ops but
        # not the codec helpers (those live as inherent methods on
        # the inner pyclass).
        rust = sub._inner if hasattr(sub, "_inner") else sub
        for _ in range(n_halvings):
            plane = rust.h264_area_average_2to1(plane, cur_w, cur_h)
            cur_w //= 2
            cur_h //= 2

        self._planes[out_stream] = bytes(plane)

    # --- helpers ----------------------------------------------------

    def plane(self, stream_node_id) -> bytes:
        """Look up the plane bytes for a VideoStream NodeID. The
        pipeline holds these out-of-band so the graph stays light."""
        return self._planes.get(stream_node_id, b"")

    # --- primitive registry -----------------------------------------
    #
    # Mapping from primitive-name (the string the dispatch Rules
    # write to job.primitive) to the Python callable that runs it.
    # The pipeline is responsible only for this mechanical lookup;
    # the decision of which primitive a given kind needs is in the
    # graph Rules. Each callable takes (self, sub, job_node_id).
    _PRIMITIVES = {
        "h264_area_average_2to1": _execute_downscale,
        "h264_transcode_pyramid_full": _execute_transrate,
        "h264_repack_nal": _execute_format_hop,
    }


__all__ = ["TranscodingPipeline"]
