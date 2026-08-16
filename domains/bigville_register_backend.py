"""bigville_register_backend -- the ocelot-side half of the CAN register wiring.

CAN_REGISTER_QUANTIZATION_RESULTS.md Sec8 named two unbuilt halves of a real
end-to-end integration: (1) bigville-side context plumbing exposing
tie_strength/band_code on ActorContext -- LANDED, bigville commit 1b79a0f,
recorded in BIGVILLE_TOPIC_AND_STYLE_SCOPING.md; (2) "an ocelot-side backend
... that calls this rung's can_register_decode_band rule per encounter" --
THIS module. Rendering register_label into actual phrasing is explicitly a
LATER step (Sec8 item 2's own wording) and is out of scope here.

Per CLAUDE.md: this is a pure capability class over the Rust engine, not a
decision-maker. The register DECISION is `can_register_decode_band`'s own
Argmin call, evaluated by `run_rules()`; this module only mints the rule's
required input nodes from data ActorContext already carries, ticks, reads
the result back, and retires its own scratch nodes so a per-encounter caller
does not grow the graph without bound (verified empirically -- 50 repeated
calls leave zero net RegisterProfile/RegisterObservation nodes behind).

Ocelot does not import bigville (the converse of bigville/backends/ocelot.py's
own "this package does not import or bundle Ocelot" boundary, ported here as
the same discipline in the other direction -- precedent:
scripts/can_register_quantization_demo.py already ports
`_draw_resolution_bins` verbatim rather than importing bigville's copy). A
caller wires this class's `decide_registers` output onto its own
ActorResponse/backend_state shape; this module returns plain dicts.
"""
from __future__ import annotations

import json
from pathlib import Path

import substrate_rs as sr
from substrate.seed_loader import engine_rules_only

_SEED_PATH = Path(__file__).resolve().parent.parent / "seeds" / "can_register_quantization.json"

# `resolution_level` has no live source anywhere in bigville today
# (CAN_REGISTER_QUANTIZATION_RESULTS.md Sec8 item 1: "bigville_motivation.json
# exists only in bigville and is not wired to ocelot's _native.Substrate() at
# all") and `resolution_bins` is not yet exposed via ActorContext.personality
# (bigville's own _characters_from_world personality filter has no entry for
# it). Both fall back to a fixed, documented, UN-FITTED default -- the same
# honesty class this rung already uses for resolution_level=1.0 in its own
# demo (CAN_REGISTER_QUANTIZATION_PREREG.md Sec3/RESULTS.md Sec5): a midpoint
# of the registered [2, 12] resolution_bins range, not a fitted or cherry
# picked value.
DEFAULT_RESOLUTION_BINS = 6
DEFAULT_RESOLUTION_LEVEL = 1.0


class RegisterDecisionEngine:
    """Decodes a per-encounter register label for a held (resolution_bins,
    resolution_level, band_code) triple via the engine's own
    can_register_decode_band rule. One instance boots the seed once and can
    be reused across many decode calls."""

    def __init__(self):
        self._s = sr.Substrate()
        self._inner = self._s._inner
        manifest = json.loads(_SEED_PATH.read_text())
        self._inner.load_seed_manifest(engine_rules_only(manifest))
        self._anchors = {
            self._inner.node(n)["attrs"]["band_code"]: n
            for n in self._inner.nodes("BandAffinityAnchor")
        }

    def decode_band(self, resolution_bins: int, resolution_level: float,
                     band_code: int) -> dict | None:
        """Decode one (resident, interlocutor) encounter's register.

        Returns None for a band_code outside the codebook's 0..5 scope (in
        particular the -1 rival/feud band -- CAT's divergence mechanism is a
        named, separate, un-built rung, RESULTS.md Sec8 item 3, not silently
        approximated here).
        """
        if band_code not in self._anchors:
            return None
        anchor_attrs = self._inner.node(self._anchors[band_code])["attrs"]
        prof = self._inner.add_node("RegisterProfile", {
            "resolution_bins": int(resolution_bins),
            "resolution_level": float(resolution_level),
        })
        obs = self._inner.add_node("RegisterObservation", {
            "band_code": band_code,
            "true_affinity": anchor_attrs["true_affinity"],
            "status": "pending",
        })
        self._inner.add_edge(prof, "observed_band", obs, {})
        self._inner.run_rules(200)
        result = dict(self._inner.node(obs)["attrs"])
        self._inner.remove_node(obs)
        self._inner.remove_node(prof)
        return {
            "band_code": band_code,
            "effective_bins": result["effective_bins"],
            "register_level_index": result["register_level_index"],
            "quantized_value": result["quantized_value"],
            "register_label": result["register_label"],
        }

    def decide_registers(self, character_personality: dict,
                          nearby_residents: list[dict]) -> dict[str, dict]:
        """Per-encounter register decode over an ActorContext-shaped input.

        `character_personality` is `context.character.personality` (a dict;
        `resolution_bins`/`resolution_level` fall back to the fixed defaults
        above when absent, which is every real call today). Each entry of
        `nearby_residents` is `context.observations["nearby_residents"]`'s
        own dict shape (bigville commit 1b79a0f: `id`/`band_code`/
        `tie_strength`/...). Returns {resident_id: decoded_dict}, skipping
        residents with no band_code or an out-of-codebook band (e.g. -1).
        """
        resolution_bins = character_personality.get("resolution_bins", DEFAULT_RESOLUTION_BINS)
        resolution_level = character_personality.get("resolution_level", DEFAULT_RESOLUTION_LEVEL)
        decisions = {}
        for resident in nearby_residents:
            band_code = resident.get("band_code")
            if band_code is None:
                continue
            decoded = self.decode_band(resolution_bins, resolution_level, int(band_code))
            if decoded is not None:
                decisions[resident["id"]] = decoded
        return decisions
