"""A small process-level probe of visual reconstruction under observer apertures.

This is an exploratory substrate experiment, not a human aphantasia model.
It separates a sparse apple cue from a randomized visual-memory node, reads
that memory through the existing qualia signature/aperture path, and records
the resulting imagined scene as a sequence of graph states. The cue retains
category knowledge while the episode-specific visual details live elsewhere.

Run with: python3 -m domains.qualia_visualization_world
Writes: results/qualia_visualization/results.json
"""
from __future__ import annotations

import json
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (_ROOT, os.path.join(_ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate_rs import _native
import domains.analogical_thinking as at
import domains.analogy_search as asr


FEATURES = {
    "hue": ("visual:hue", "apple_hue"),
    "stem": ("visual:stem_orientation", "stem_orientation"),
    "bite": ("visual:bite_location", "bite_location"),
    "light": ("visual:light_direction", "light_direction"),
    "shape": ("visual:contour", "contour"),
}
VALUES = {
    "hue": {-2: "deep_green", -1: "green", 1: "red", 2: "yellow"},
    "stem": {-1: "left", 1: "upright", 2: "right"},
    "bite": {-1: "left_side", 1: "right_side", 2: "none"},
    "light": {-1: "below", 1: "above"},
    "shape": {-1: "angular", 1: "round"},
}
HUE_COLOURS = {
    "deep_green": (39, 111, 55), "green": (92, 164, 67),
    "red": (200, 54, 43), "yellow": (224, 184, 46),
}


def _render_apple(features, path, title):
    """Rasterize the projected scene; unknown visual features stay neutral."""
    width, height = 360, 410
    bg = (248, 248, 245)
    image = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 13)
        title_font = ImageFont.truetype("DejaVuSans.ttf", 17)
    except OSError:
        font = ImageFont.load_default()
        title_font = font
    draw.text((14, 12), title, fill=(35, 39, 42), font=title_font)

    hue = features.get("hue")
    colour = HUE_COLOURS.get(VALUES["hue"].get(hue), (170, 170, 165))
    shape = VALUES["shape"].get(features.get("shape"))
    outline = (72, 65, 54) if shape else (135, 135, 130)
    fill = colour if shape else tuple(int(c * .62 + 255 * .38) for c in colour)
    mask = Image.new("L", (width, height), 0)
    mask_draw = ImageDraw.Draw(mask)
    if shape == "angular":
        body = [(178, 88), (224, 100), (259, 144), (250, 210), (218, 267),
                (178, 283), (138, 267), (106, 210), (97, 144), (132, 100)]
        mask_draw.polygon(body, fill=255)
    else:
        # Union overlapping lobes into one apple silhouette, avoiding internal
        # seams between the component ellipses.
        mask_draw.ellipse((91, 108, 207, 258), fill=255)
        mask_draw.ellipse((151, 108, 267, 258), fill=255)
        mask_draw.ellipse((112, 123, 246, 282), fill=255)
        mask_draw.ellipse((126, 95, 180, 143), fill=255)
        mask_draw.ellipse((178, 95, 232, 143), fill=255)
    body_image = Image.new("RGB", (width, height), fill)
    image.paste(body_image, (0, 0), mask)
    # Draw just the outer contour of the union mask.
    expanded = mask.filter(ImageFilter.MaxFilter(9))
    border = ImageChops.subtract(expanded, mask)
    border_draw = ImageDraw.Draw(image)
    border_draw.bitmap((0, 0), border, fill=outline)
    draw = ImageDraw.Draw(image)

    # A color wash communicates an unknown hue without inventing a recovered one.
    if hue is None:
        draw.rectangle((13, 39, 25, 51), fill=(170, 170, 165))
        draw.text((30, 37), "hue unresolved", fill=(88, 88, 84), font=font)

    stem = VALUES["stem"].get(features.get("stem"))
    x_stem = {"left": 157, "upright": 178, "right": 198}.get(stem, 178)
    stem_colour = (92, 67, 42) if stem else (150, 150, 145)
    draw.line((178, 105, x_stem, 63), fill=stem_colour, width=9)
    draw.ellipse((x_stem - 3, 59, x_stem + 3, 67), fill=stem_colour)
    if stem is None:
        draw.text((244, 72), "? stem", fill=(88, 88, 84), font=font)

    # Render the stored light direction as a perceptual highlight.
    light = VALUES["light"].get(features.get("light"))
    highlight_y = 123 if light == "above" else 225 if light == "below" else 169
    highlight_colour = (255, 255, 255) if light else (218, 218, 214)
    draw.ellipse((112, highlight_y, 143, highlight_y + 20),
                 fill=highlight_colour)
    if light is None:
        draw.text((242, 187), "? light", fill=(88, 88, 84), font=font)

    bite = VALUES["bite"].get(features.get("bite"))
    if bite in ("left_side", "right_side"):
        bx = 103 if bite == "left_side" else 252
        draw.ellipse((bx - 14, 164, bx + 14, 194), fill=bg)
        draw.arc((bx - 14, 164, bx + 14, 194), 210, 150,
                 fill=(125, 99, 70), width=2)
    elif bite is None:
        draw.text((15, 281), "bite detail unresolved", fill=(88, 88, 84), font=font)

    if shape is None:
        draw.text((15, 298), "contour unresolved", fill=(88, 88, 84), font=font)

    labels = []
    for key in FEATURES:
        value = features.get(key)
        labels.append("%s=%s" % (key, VALUES[key].get(value, "?")))
    draw.text((14, 365), "  ".join(labels[:2]), fill=(55, 57, 58), font=font)
    draw.text((14, 384), "  ".join(labels[2:]), fill=(55, 57, 58), font=font)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    image.save(path)


def _edge(s, src, edge_type, tgt):
    """Install world-observation links directly; they carry no decision."""
    s.add_edge_unchecked(src, edge_type, tgt)


def _boot():
    s = _native.Substrate()
    for cache in (at._CONCEPT_READING_CACHE, at._VOCAB_KEYS_CACHE,
                  at._METASHAPE_COUNT_CACHE, asr._QUALIA_SCHEMA_CACHE):
        cache.clear()
    agent = s.add_node("Agent", {})
    for fname in ("shape_vocabulary.json", "qualia_space.json",
                  "analogy_search.json", "observer_aperture.json"):
        with open(os.path.join(_ROOT, "seeds", fname), encoding="utf-8") as f:
            summary = s.load_seed_manifest(json.load(f), agent)
        assert not summary.get("rules_skipped"), (fname, summary)
    # Visual feature axes are graph-resident qualia dimensions. Values are
    # discrete coordinate codes; quantum 1 preserves each code exactly.
    for dim, attr in FEATURES.values():
        s.add_node("QualiaDimension", {
            "name": dim, "family": "visual", "source": "field:" + attr,
            "seeded": 0.0, "quantum": 1.0, "half_width": 2.0,
            "gloss": "Episode-specific visual feature used by imagery probe",
        })
    return s, agent


def _signature_features(sig, scale=1):
    by_dim = {d: int(v) * scale for d, pred, v in sig if d.startswith("visual:")}
    return {name: by_dim.get(dim) for name, (dim, _attr) in FEATURES.items()}


def _make_observer(s, name, dims, grain=None):
    attrs = {"name": name, "resolves": list(dims)}
    if grain:
        attrs["grain"] = grain
    return s.add_node("Observer", attrs)


def run(verbose=True):
    s, agent = _boot()
    mt = s.add_node("Microtheory", {"name": "visual_episode"})
    cue = s.add_node("Concept", {"name": "apple", "category": "fruit",
                                 "state": 1.0, "identity_field": 0.8})
    _edge(s, mt, "has_concept", cue)
    # Fixed, declared episode battery. Each axis has a balanced, arbitrary
    # episode value so apple-world priors cannot predict the correct answer.
    episodes = [
        {"hue": 2, "stem": -1, "bite": 1, "light": -1, "shape": -1},
        {"hue": -2, "stem": 1, "bite": -1, "light": 1, "shape": 1},
        {"hue": 1, "stem": 1, "bite": 2, "light": -1, "shape": -1},
        {"hue": -1, "stem": -1, "bite": -1, "light": 1, "shape": 1},
        {"hue": 2, "stem": 1, "bite": 1, "light": 1, "shape": -1},
        {"hue": -2, "stem": 1, "bite": 1, "light": -1, "shape": 1},
        {"hue": 1, "stem": -1, "bite": -1, "light": 1, "shape": -1},
        {"hue": -1, "stem": 1, "bite": 2, "light": -1, "shape": 1},
    ]
    dims = [dim for dim, _attr in FEATURES.values()]
    full = _make_observer(s, "full_imagery", dims)
    coarse = _make_observer(s, "coarse_imagery", dims,
                            {dim: 2.0 for dim in dims})
    absent = _make_observer(s, "imagery_absent", [])
    render_dir = os.path.join(_ROOT, "results", "qualia_visualization", "rendered")

    rows = []
    for idx, code in enumerate(episodes):
        attrs = {"name": "apple_episode_%02d" % idx, "category": "episodic_visual_memory",
                 "state": 1.0, "identity_field": 0.8, "sharpness": 1.0}
        attrs.update({FEATURES[k][1]: float(v) for k, v in code.items()})
        memory = s.add_node("VisualMemory", attrs)
        _edge(s, cue, "retrieves_visual_memory", memory)
        _edge(s, mt, "has_visual_memory", memory)
        targets = {k: VALUES[k][v] for k, v in code.items()}
        semantic_category = s.node(cue)["attrs"].get("category")
        arms = {
            "perception": _signature_features(asr.concept_signature(s, memory)),
            "full_imagery": _signature_features(
                asr.concept_signature(s, memory, observer=full)),
            "coarse_imagery": _signature_features(
                asr.concept_signature(s, memory, observer=coarse), scale=2),
            "imagery_absent": _signature_features(
                asr.concept_signature(s, memory, observer=absent)),
            # Semantic control knows the category, not this episode's details.
            "semantic_control": {k: None for k in FEATURES},
        }
        for arm, recovered in arms.items():
            # Store the projection as an explicit evolving scene trace. Each
            # state adds one feature slot in a fixed sequence.
            scene = s.add_node("ImaginedVisualScene", {
                "episode": idx, "arm": arm,
                "visual_feature_count": sum(v is not None for v in recovered.values()),
                "semantic_category": semantic_category,
            })
            _edge(s, cue, "produces_visual_scene", scene)
            _edge(s, scene, "from_visual_memory", memory)
            render_path = os.path.join(
                render_dir, "episode_%02d_%s.png" % (idx, arm))
            _render_apple(recovered, render_path,
                          "apple episode %02d | %s" % (idx, arm))
            prior = None
            for step, (name, (dim, _attr)) in enumerate(FEATURES.items(), 1):
                value = recovered[name]
                state = s.add_node("ImaginedVisualState", {
                    "episode": idx, "arm": arm, "step": step,
                    "feature": name, "dimension": dim,
                    "value": -999.0 if value is None else float(value),
                    "resolved": value is not None,
                })
                _edge(s, scene, "has_visual_state", state)
                if prior is not None:
                    _edge(s, prior, "next_visual_state", state)
                prior = state
        scores = {}
        for arm, recovered in arms.items():
            valid = [k for k, v in recovered.items() if v is not None]
            scores[arm] = {"correct": sum(recovered[k] == code[k] for k in valid),
                           "available": len(valid), "total": len(code)}
        rows.append({"episode": idx, "targets": targets, "scores": scores,
                     "semantic_category_known": semantic_category == "fruit",
                     "reconstructed_codes": arms,
                     "rendered_images": {
                         arm: os.path.relpath(os.path.join(
                             render_dir, "episode_%02d_%s.png" % (idx, arm)), _ROOT)
                         for arm in arms
                     }})

    summary = {}
    for arm in rows[0]["scores"]:
        correct = sum(r["scores"][arm]["correct"] for r in rows)
        available = sum(r["scores"][arm]["available"] for r in rows)
        summary[arm] = {"correct": correct, "available": available,
                        "total": len(rows) * len(FEATURES),
                        "accuracy_when_available": (
                            correct / available if available else None),
                        "coverage": available / (len(rows) * len(FEATURES))}
    conditions = list(rows[0]["rendered_images"])
    tile_w, tile_h = 180, 205
    grid = Image.new("RGB", (tile_w * len(conditions), tile_h * len(rows)),
                     (238, 238, 235))
    for row_idx, row in enumerate(rows):
        for col_idx, condition in enumerate(conditions):
            tile = Image.open(os.path.join(_ROOT,
                               row["rendered_images"][condition])).convert("RGB")
            tile.thumbnail((tile_w, tile_h))
            grid.paste(tile, (col_idx * tile_w, row_idx * tile_h))
    grid_path = os.path.join(_ROOT, "results", "qualia_visualization",
                             "comparison_grid.png")
    grid.save(grid_path)
    result = {
        "status": "exploratory substrate probe; not a human replication",
        "process": "concept/episode -> observer projection -> ordered visual-state trace -> feature probe",
        "episodes": rows,
        "rendering": {
            "format": "PNG",
            "files": len(rows) * len(rows[0]["reconstructed_codes"]),
            "directory": "results/qualia_visualization/rendered",
            "comparison_grid": "results/qualia_visualization/comparison_grid.png",
            "unknown_features": "shown as neutral or marked unresolved; no source-memory fallback",
        },
        "summary": summary,
        "semantic_category_accuracy": {
            arm: sum(r["semantic_category_known"] for r in rows) / len(rows)
            for arm in summary
        },
        "trace_counts": {
            "visual_memories": len(s.nodes("VisualMemory")),
            "imagined_scenes": len(s.nodes("ImaginedVisualScene")),
            "imagined_feature_states": len(s.nodes("ImaginedVisualState")),
        },
        "limitations": [
            "Episode values are already stored on a separate VisualMemory node; this measures aperture-governed retrieval/projection, not image generation from a sparse semantic quale.",
            "ImaginedVisualState traces are emitted by this world adapter, not by a graph-authored recurrent imagery rule.",
            "Semantic-control answers are intentionally absent for arbitrary episode details; this is a representational control, not a learned semantic model.",
        ],
    }
    out_dir = os.path.join(_ROOT, "results", "qualia_visualization")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "results.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    if verbose:
        print(json.dumps(summary, indent=2))
        print("wrote results/qualia_visualization/results.json")
    return result


if __name__ == "__main__":
    run()
