"""Mary's Room stage 4.3-4.5 world adapter: perceived, persistent surfaces,
their colour properties and the looking episodes that present them.

MECHANICAL ONLY (CLAUDE.md "What Python is allowed to do"):
  * build a 2-D colour GraphEye (retina_2d + retina_2d_cones, uniform layout so
    the sheet carries symmetric 4-neighbour `adjacent_receptor` edges);
  * load the two graph seeds `surface_segmentation` and `surface_persistence`
    onto the eye's agent, and (stage 4.5, `stage45=True`) `colour_property`,
    `looking_episode` and `look_property_link`;
  * blind-write their enable flags;
  * submit one exposure (packets from `domains.spectral_scene.render`), drive
    the sheet synchronously (submit_photons_2d -> run_cognitive_tasks(1) ->
    run_rules), prune settled retina tasks;
  * read SurfaceSegment / PersistentSurface nodes and per-cell labels back,
    and (4.5) ColourProperty / FrameStats / PropertyCheck / LookingEpisode /
    SurfaceLook / FieldLook nodes plus the link edges.

Every segmentation / identity decision is a graph rule in the seeds; nothing
here reads graph state to decide anything.
"""
from __future__ import annotations

import time

from domains.engine_provenance import engine_preamble

engine_preamble()

from domains.photon_eye import GraphEye  # noqa: E402
from substrate.seed_loader import manifest_for  # noqa: E402

SEGMENTATION_SEED = "surface_segmentation"
PERSISTENCE_SEED = "surface_persistence"
STAGE45_SEEDS = ("colour_property", "looking_episode", "look_property_link")
STAGE45_TYPES = ("ColourProperty", "FrameStats", "PropertyCheck",
                 "LookingEpisode", "SurfaceLook", "FieldLook")
LINK_EDGES = ("presents_property", "presents_unrecognised")


def eye_context(extra: dict | None = None) -> dict:
    ctx = {"retina_2d": True, "retina_2d_cones": True,
           "retinal_layout": "uniform", "synchronous": True,
           "worker_capacity": 1}
    ctx.update(extra or {})
    return ctx


class PerceivedSurfaceWorld:
    """A GraphEye plus (optionally) the two surface seeds."""

    def __init__(self, n_az: int, n_el: int, *, segmentation: bool = True,
                 persistence: bool = True, load_seeds: bool = True,
                 context: dict | None = None, stage45: bool = False,
                 colour: bool = True, pooled: bool = True,
                 looking: bool = True):
        self.eye = GraphEye(n_az=n_az, n_el=n_el,
                            context=eye_context(context)).build()
        self.n_az, self.n_el = n_az, n_el
        self.s = self.eye.substrate
        self.inner = self.s._inner
        self.load_summaries = []
        self.timings: list[float] = []
        if load_seeds:
            agent = self.eye._agent
            self.load_summaries.append(
                self.inner.load_seed_manifest(manifest_for(SEGMENTATION_SEED), agent))
            self.load_summaries.append(
                self.inner.load_seed_manifest(manifest_for(PERSISTENCE_SEED), agent))
            # blind writes of the declared flags (no read-then-decide)
            for nid in self.s.nodes("SurfaceSegmentationParams"):
                self.s.set_attr(nid, "enabled", 1.0 if segmentation else 0.0)
            for nid in self.s.nodes("SurfacePersistenceParams"):
                self.s.set_attr(nid, "enabled", 1.0 if persistence else 0.0)
        if load_seeds and stage45:
            for seed in STAGE45_SEEDS:
                self.load_summaries.append(
                    self.inner.load_seed_manifest(manifest_for(seed), agent))
            for nid in self.s.nodes("ColourPropertyParams"):
                self.s.set_attr(nid, "enabled", 1.0 if colour else 0.0)
                self.s.set_attr(nid, "pooled", 1.0 if pooled else 0.0)
            for nid in self.s.nodes("LookingEpisodeParams"):
                self.s.set_attr(nid, "enabled", 1.0 if looking else 0.0)

    # ------------------------------------------------------------- ingest
    def expose(self, packets) -> float:
        """Submit one exposure and drive it to the run_rules fixpoint.
        Returns wall seconds for this exposure."""
        t0 = time.perf_counter()
        self.eye.submit_photons_2d(packets)
        self.inner.run_cognitive_tasks(1)
        self.inner.run_rules()
        self.eye.prune_settled_tasks()
        dt = time.perf_counter() - t0
        self.timings.append(dt)
        return dt

    # --------------------------------------------------------------- emit
    def _attrs(self, nid) -> dict:
        return dict(self.s.node(nid)["attrs"])

    def cells(self) -> list[dict]:
        """Per-cell segmentation / persistence attrs in cell_index order."""
        out = [self._attrs(c) for c in self.eye._cells]
        return out

    def label_grid(self, key: str = "seg_label") -> list[list]:
        cells = self.cells()
        return [[cells[r * self.n_az + c].get(key) for c in range(self.n_az)]
                for r in range(self.n_el)]

    def segments(self, epoch: int | None = None,
                 current_only: bool = False) -> list[dict]:
        out = []
        for nid in self.s.nodes("SurfaceSegment"):
            a = self._attrs(nid)
            if epoch is not None and a.get("epoch") != epoch:
                continue
            if current_only and not a.get("current", 0.0) > 0.5:
                continue
            a["_nid"] = nid
            out.append(a)
        return sorted(out, key=lambda a: (a["epoch"], a["root"]))

    def persistent_surfaces(self) -> list[dict]:
        out = [self._attrs(nid) for nid in self.s.nodes("PersistentSurface")]
        return sorted(out, key=lambda a: a["sid"])

    def state(self) -> dict:
        out = {}
        for t in ("SegmentationState", "PersistenceState", "SurfaceCounter",
                  "SurfaceSegmentationParams", "SurfacePersistenceParams"):
            nids = self.s.nodes(t)
            out[t] = [self._attrs(n) for n in nids]
        return out

    # ------------------------------------------------- stage 4.5 readers
    def _typed(self, node_type: str, key=("epoch", "sid")) -> list[dict]:
        out = []
        for nid in self.s.nodes(node_type):
            a = self._attrs(nid)
            a["_nid"] = nid
            out.append(a)
        return sorted(out, key=lambda a: tuple(
            (a.get(k) if a.get(k) is not None else -1) for k in key) + (a["_nid"],))

    def counts(self) -> dict:
        """Node counts by stage-4.5 type and link-edge counts by edge type."""
        out = {t: len(self.s.nodes(t)) for t in STAGE45_TYPES}
        d = self.s.graph_to_dict()
        for e in LINK_EDGES:
            out[e] = sum(1 for x in d["edges"] if x["type"] == e)
        return out

    def colour_properties(self) -> list[dict]:
        return self._typed("ColourProperty", ("sid",))

    def frames(self) -> list[dict]:
        return self._typed("FrameStats", ("epoch",))

    def checks(self, epoch: int | None = None) -> list[dict]:
        return [c for c in self._typed("PropertyCheck")
                if epoch is None or c["epoch"] == epoch]

    def episodes(self) -> list[dict]:
        return self._typed("LookingEpisode", ("epoch",))

    def surface_looks(self, epoch: int | None = None) -> list[dict]:
        out = []
        for a in self._typed("SurfaceLook"):
            if epoch is not None and a["epoch"] != epoch:
                continue
            a["edges"] = {e: len(self.s.neighbours(a["_nid"], e)) for e in LINK_EDGES}
            out.append(a)
        return out

    def field_looks(self) -> list[dict]:
        return self._typed("FieldLook", ("epoch",))

    def edges_of(self, nid, edge_type: str) -> list:
        return list(self.s.neighbours(nid, edge_type))

    def in_edges_of(self, nid, edge_type: str) -> list:
        return list(self.s.in_neighbours(nid, edge_type))

    def stop(self) -> None:
        self.eye.stop()
