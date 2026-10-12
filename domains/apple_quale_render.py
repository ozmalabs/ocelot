"""Render a graph-structured apple visual quale as a staged image series.

The substrate stores qualitative concepts and their relations (form, skin,
light, scene). The rasterizer is an interpretation layer: its RGB values,
mesh tessellation, camera, and pixel positions are renderer choices, never
QualiaDimension values. Run with ``python3 -m domains.apple_quale_render``.
"""
from __future__ import annotations

import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (_ROOT, os.path.join(_ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate_rs import _native
import domains.analogical_thinking as at
import domains.analogy_search as asr
from substrate.seed_loader import manifest_for


def _graph_node(s, type_, name, **attrs):
    data = {"name": name}
    data.update(attrs)
    return s.add_node(type_, data)


def _substrate():
    """Load the existing qualia system without adding renderer feature axes."""
    s = _native.Substrate()
    for cache in (at._CONCEPT_READING_CACHE, at._VOCAB_KEYS_CACHE,
                  at._METASHAPE_COUNT_CACHE, asr._QUALIA_SCHEMA_CACHE):
        cache.clear()
    agent = s.add_node("Agent", {})
    for filename in ("shape_vocabulary.json", "qualia_space.json",
                     "analogy_search.json", "observer_aperture.json"):
        with open(os.path.join(_ROOT, "seeds", filename), encoding="utf-8") as f:
            summary = s.load_seed_manifest(json.load(f), agent)
        assert not summary.get("rules_skipped"), (filename, summary)
    # Load the actual held apple concept and the held geometric circle concept
    # from their seed homes. Only the needed concepts are loaded from each.
    lexicon = dict(manifest_for("learned_lexicon"))
    lexicon["nodes"] = [n for n in lexicon.get("nodes", [])
                        if n.get("type") == "Concept"
                        and n.get("attrs", {}).get("name") == "apples"]
    lexicon["edges"] = []
    summary = s.load_seed_manifest(lexicon, agent)
    assert not summary.get("rules_skipped"), summary
    geometry = dict(manifest_for("geometry_microtheory"))
    geometry["nodes"] = [n for n in geometry.get("nodes", [])
                         if n.get("type") == "Concept"
                         and n.get("attrs", {}).get("name") == "circle"]
    geometry["edges"] = []
    summary = s.load_seed_manifest(geometry, agent)
    assert not summary.get("rules_skipped"), summary
    return s


def _edge(s, src, edge_type, tgt):
    s.add_edge_unchecked(src, edge_type, tgt)


def build_apple_quale():
    """Extend held apple/circle concepts into an evidence-anchored quale graph."""
    s = _substrate()
    concepts = list(s.nodes("Concept"))
    apple = next(n for n in concepts if _attrs(s, n).get("name") == "apples")
    circle = next(n for n in concepts if _attrs(s, n).get("name") == "circle"
                  and _attrs(s, n).get("category") == "geometry")
    quale = _graph_node(s, "VisualQuale", "apple visual quale")
    form = _graph_node(s, "FormQuale", "apple pome form", morphology="globose_pome",
                       volume="rounded_fruit_body")
    body = _graph_node(s, "FormRegion", "fruit body", role="main_volume")
    crown = _graph_node(s, "FormRegion", "depressed crown", role="stem_cavity")
    base = _graph_node(s, "FormRegion", "calyx cavity", role="calyx_cavity")
    skin = _graph_node(s, "SurfaceQuale", "apple skin color",
                       appearance="red_over_yellow")
    pattern = _graph_node(s, "SurfacePatternQuale", "lenticels and color distribution",
                          pattern="lenticels_with_cultivar_color_pattern")
    finish = _graph_node(s, "SurfaceFinishQuale", "apple cuticle",
                         finish="cuticular_wax")
    lighting = _graph_node(s, "IlluminationQuale", "light from above",
                           character="single_soft_source_above")
    shadow = _graph_node(s, "ShadowQuale", "soft contact shadow",
                         relation="cast_shadow_on_ground")
    scene = _graph_node(s, "SceneQuale", "apple on a studio table",
                        content="fruit_resting_on_surface")
    ground = _graph_node(s, "SceneSurfaceQuale", "warm wooden tabletop",
                         material="warm_grained_wood")
    backdrop = _graph_node(s, "SceneBackdropQuale", "muted sage backdrop",
                           appearance="muted_sage_studio")
    leaf = _graph_node(s, "Concept", "apple leaf", category="leaf",
                       appearance="small_green_leaf")

    for src, et, tgt in (
        (apple, "abstracts_as", circle),
        (circle, "refined_as", quale),
        (apple, "has_visual_quale", quale),
        (quale, "has_form", form), (form, "has_region", body),
        (form, "has_region", crown), (form, "has_region", base),
        (quale, "has_surface", skin), (skin, "has_pattern", pattern),
        (skin, "has_finish", finish), (quale, "illuminated_by", lighting),
        (lighting, "casts", shadow), (quale, "situated_in", scene),
        (scene, "has_ground", ground), (scene, "has_backdrop", backdrop),
        (scene, "has_illumination", lighting), (scene, "has_subject", apple),
        (scene, "contains", leaf),
    ):
        _edge(s, src, et, tgt)
    return s, {"apple": apple, "circle": circle, "quale": quale,
               "form": form, "body": body,
               "crown": crown, "base": base, "skin": skin, "pattern": pattern,
               "finish": finish, "lighting": lighting, "shadow": shadow,
               "scene": scene, "ground": ground, "backdrop": backdrop,
               "leaf": leaf}


def _font(size=18, bold=False):
    candidates = ("DejaVuSans-Bold.ttf", "DejaVuSans.ttf") if bold else ("DejaVuSans.ttf",)
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def _attrs(s, node):
    return s.node(node)["attrs"]


def _quale_card(s, nodes, path):
    """Draw the abstract graph as a diagram, without depicting an apple."""
    im = Image.new("RGB", (1000, 600), (250, 249, 245))
    d = ImageDraw.Draw(im)
    d.text((36, 22), "HELD APPLE CONCEPT → CIRCLE OF FRUIT → VISUAL QUALE",
           fill=(40, 43, 43), font=_font(26, True))
    cx, cy = 500, 82
    d.rounded_rectangle((cx - 112, cy - 31, cx + 112, cy + 31), 18,
                        fill=(235, 227, 198), outline=(82, 76, 62), width=2)
    apple_label = _attrs(s, nodes["apple"]).get("name", "apple").upper()
    d.text((cx - d.textlength(apple_label, font=_font(20, True)) / 2, cy - 12),
           apple_label, fill=(57, 50, 38), font=_font(20, True))
    apple_definition = _attrs(s, nodes["apple"]).get("definition", "")
    d.text((36, 124), "Held lexical concept (learned_lexicon): " + apple_definition[:110],
           fill=(82, 80, 72), font=_font(13))
    d.line((cx, cy + 31, cx, 170), fill=(90, 94, 92), width=2)
    d.ellipse((cx - 21, 150, cx + 21, 192), fill=(249, 248, 244),
              outline=(97, 102, 92), width=2)
    d.rounded_rectangle((cx - 169, 202, cx + 169, 249), 16,
                        fill=(234, 232, 217), outline=(106, 101, 79), width=2)
    d.text((cx - 86, 207), "CIRCLE OF FRUIT", fill=(69, 65, 48), font=_font(17, True))
    circle_definition = _attrs(s, nodes["circle"]).get("definition", "")
    d.text((cx - 155, 253), "Held geometry (geometry_microtheory): " + circle_definition[:62],
           fill=(82, 80, 72), font=_font(12))
    qy = 335
    d.line((cx, 266, cx, qy - 27), fill=(90, 94, 92), width=2)
    d.rounded_rectangle((cx - 176, qy - 27, cx + 176, qy + 27), 16,
                        fill=(220, 232, 224), outline=(74, 104, 91), width=2)
    d.text((cx - 131, qy - 10), "APPLE-SPECIFIC VISUAL QUALE",
           fill=(42, 75, 61), font=_font(17, True))
    region_names = [_attrs(s, n).get("name") for n in s.neighbours(nodes["form"], "has_region")]
    columns = [
        (160, "FORM", [_attrs(s, nodes["form"]).get("volume"),
                        _attrs(s, nodes["form"]).get("morphology")] + region_names),
        (390, "SURFACE", [_attrs(s, nodes["skin"]).get("appearance"),
                           _attrs(s, nodes["pattern"]).get("pattern"),
                           _attrs(s, nodes["finish"]).get("finish")]),
        (610, "LIGHT", [_attrs(s, nodes["lighting"]).get("character"),
                         _attrs(s, nodes["shadow"]).get("relation")]),
        (840, "SCENE", [_attrs(s, nodes["ground"]).get("material"),
                         _attrs(s, nodes["backdrop"]).get("appearance"),
                         "contains " + _attrs(s, nodes["leaf"]).get("name", "leaf")]),
    ]
    for x, heading, labels in columns:
        d.line((cx, qy + 28, x, 383), fill=(90, 94, 92), width=2)
        d.rounded_rectangle((x - 82, 374, x + 82, 416), 12,
                            fill=(229, 232, 226), outline=(107, 112, 104), width=2)
        d.text((x - d.textlength(heading, font=_font(17, True)) / 2, 385),
               heading, fill=(48, 52, 49), font=_font(17, True))
        for i, label in enumerate(labels):
            yy = 440 + i * 27
            d.line((x, 416, x, yy - 5), fill=(175, 176, 168), width=1)
            d.ellipse((x - 4, yy - 3, x + 4, yy + 5), fill=(118, 130, 119))
            d.text((x - 76, yy + 8), str(label), fill=(75, 77, 73), font=_font(12))
    d.text((36, 578), "Apple → circle is the proposed substrate abstraction; studies ground visual cues, not this ordering.",
           fill=(91, 92, 87), font=_font(14))
    im.save(path)


def _mesh(morphology="globose_pome", rings=88, sectors=144):
    """Build renderer geometry from qualitative form labels, not graph floats."""
    vertices = []
    for ri in range(rings + 1):
        theta = math.pi * (ri + .0001) / (rings + .0002)
        row = []
        for si in range(sectors):
            phi = 2 * math.pi * si / sectors
            y = 1.02 * math.cos(theta)
            radius = math.sin(theta) * (.88 + .06 * math.cos(theta))
            if morphology == "globose_pome":
                # A restrained renderer choice for an irregular rounded fruit;
                # this does not encode a universal apple lobe count.
                radius *= 1 + .025 * math.cos(5 * phi) * (math.sin(theta) ** 2)
            # A depressed crown and gently tapered base are structural readings
            # of the FormQuale's named regions.
            radial_center = radius
            crown_depth = max(0.0, (y - .52) / .50)
            y -= .20 * math.exp(-((radial_center / .25) ** 2)) * crown_depth ** 2
            x, z = radius * math.cos(phi), radius * math.sin(phi) * .82
            row.append((x, y, z, theta, phi))
        vertices.append(row)
    faces = []
    for ri in range(rings):
        for si in range(sectors):
            sj = (si + 1) % sectors
            a, b = vertices[ri][si], vertices[ri][sj]
            c, e = vertices[ri + 1][si], vertices[ri + 1][sj]
            faces.append((a, c, e))
            faces.append((a, e, b))
    return faces


def _face_normal(a, b, c):
    u = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    v = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    n = (u[1]*v[2] - u[2]*v[1], u[2]*v[0] - u[0]*v[2],
         u[0]*v[1] - u[1]*v[0])
    length = math.sqrt(sum(q*q for q in n)) or 1
    # The current ring-walk face order is inward-facing; flip it to recover
    # the outward surface normal used by visibility and diffuse light.
    return tuple(-q / length for q in n)


def _skin_colour(theta, phi, appearance, pattern, speckle_seed):
    """Interpret qualitative skin/pattern nodes as a renderer material."""
    # Honey-gold base plus irregular red blush, a common bi-colour apple look.
    blush_wave = math.sin(2.5 * phi + 1.7 * theta) * math.cos(3.2 * theta - phi)
    blush = max(0.0, min(1.0, .38 + .34 * blush_wave))
    if pattern != "lenticels_with_cultivar_color_pattern":
        blush = 0.0
    if appearance == "red_over_yellow":
        gold, red = (220, 164, 57), (171, 38, 36)
    else:
        gold = red = (142, 153, 88)
    rgb = tuple(int(gold[i] * (1 - blush) + red[i] * blush) for i in range(3))
    # Deterministic fine skin flecks, independent from the raster seed.
    noise = math.sin((theta * 311 + phi * 197 + speckle_seed) * 12.9898) * 43758.5453
    frac = noise - math.floor(noise)
    if pattern == "lenticels_with_cultivar_color_pattern" and frac > .994:
        rgb = tuple(min(255, c + 40) for c in rgb)
    return rgb


def _render_mesh(s, nodes, path, *, stage):
    """Software-render the quale mesh with progressive material/light/scene."""
    scale = 165
    w, h = 720, 640
    if stage == 1:
        # Render the held geometry concept as its own sparse visual reading.
        # Its circular silhouette is an adapter interpretation, not an apple.
        im = Image.new("RGB", (720, 640), (249, 248, 244))
        d = ImageDraw.Draw(im)
        d.ellipse((250, 155, 470, 375), fill=(226, 224, 211),
                  outline=(108, 105, 91), width=4)
        d.text((275, 410), "CIRCLE OF FRUIT", fill=(56, 57, 52), font=_font(21, True))
        d.text((186, 446), _attrs(s, nodes["circle"]).get("definition", ""),
               fill=(86, 86, 79), font=_font(14))
        d.rectangle((0, 0, 720, 52), fill=(249, 248, 244))
        d.text((24, 16), "1  HELD GEOMETRY CONCEPT  /  circle", fill=(48, 50, 46), font=_font(18, True))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        im.save(path)
        return
    scene_on = stage >= 5
    form_data = _attrs(s, nodes["form"])
    skin_data = _attrs(s, nodes["skin"])
    pattern_data = _attrs(s, nodes["pattern"])
    light_data = _attrs(s, nodes["lighting"])
    ground_data = _attrs(s, nodes["ground"])
    backdrop_data = _attrs(s, nodes["backdrop"])
    morphology = form_data.get("morphology", "rounded_pome")
    appearance = skin_data.get("appearance", "unknown_skin")
    pattern = pattern_data.get("pattern", "plain")
    illumination = light_data.get("character", "ambient")
    scene_contains_leaf = nodes["leaf"] in s.neighbours(nodes["scene"], "contains")
    bg_colour = ((190, 202, 178) if backdrop_data.get("appearance") == "muted_sage_studio"
                 else (222, 222, 218))
    ground_colour = ((155, 112, 70) if ground_data.get("material") == "warm_grained_wood"
                     else (166, 166, 160))
    im = Image.new("RGB", (w, h), bg_colour if scene_on else (249, 248, 244))
    draw = ImageDraw.Draw(im)
    if scene_on:
        # Sage backdrop and tabletop are scene concepts interpreted here.
        draw.rectangle((0, 0, w, 420), fill=bg_colour)
        draw.rectangle((0, 420, w, h), fill=ground_colour)
        for y in (451, 507, 579):
            draw.arc((-30, y - 20, 765, y + 30), 0, 180, fill=(132, 91, 57), width=2)
        draw.line((0, 420, w, 420), fill=(128, 142, 120), width=3)
    if stage >= 4 and s.neighbours(nodes["lighting"], "casts"):
        shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        sd.ellipse((295, 405, 476, 450), fill=(38, 35, 28, 105 if scene_on else 55))
        shadow = shadow.filter(ImageFilter.GaussianBlur(18 if scene_on else 12))
        im = Image.alpha_composite(im.convert("RGBA"), shadow).convert("RGB")
    draw = ImageDraw.Draw(im)

    flat = (193, 193, 187) if stage == 2 else None
    yaw, pitch = .28, .10
    center_x, center_y = 360, 255
    lit = stage >= 4
    faces = _mesh(morphology=morphology)
    projected = []
    for face in faces:
        pts = []
        for x, y, z, theta, phi in face:
            xr = x * math.cos(yaw) - z * math.sin(yaw)
            zr = x * math.sin(yaw) + z * math.cos(yaw)
            yr = y * math.cos(pitch) - zr * math.sin(pitch)
            depth = y * math.sin(pitch) + zr * math.cos(pitch)
            pts.append((center_x + xr * scale, center_y - yr * scale, depth,
                        theta, phi, (x, y, z)))
        normal = _face_normal(*(p[5] for p in pts))
        # Keep only faces oriented toward the camera; painter-sort the visible shell.
        if normal[2] < -.02:
            continue
        avg_depth = sum(p[2] for p in pts) / 3
        if stage == 1:
            colour = flat
        else:
            theta = sum(p[3] for p in pts) / 3
            phi = sum(p[4] for p in pts) / 3
            colour = (_skin_colour(theta, phi, appearance,
                                   pattern if stage >= 3 else "plain", 31)
                      if stage >= 3 else flat)
            if lit and "above" in illumination:
                light = (-.55, .72, .62)
                dot = max(0, sum(normal[i] * light[i] for i in range(3)))
                diffuse = .40 + .60 * dot
                colour = tuple(max(0, min(255, int(c * diffuse))) for c in colour)
        projected.append((avg_depth, pts, colour))
    for _depth, pts, colour in sorted(projected, key=lambda item: item[0]):
        draw.polygon([(p[0], p[1]) for p in pts], fill=colour)

    # Subtle wax highlight is a renderer interpretation of the finish concept.
    if stage >= 3 and _attrs(s, nodes["finish"]).get("finish") == "cuticular_wax":
        hi = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        hd = ImageDraw.Draw(hi)
        hd.ellipse((306, 240, 351, 294), fill=(255, 246, 219, 72))
        hi = hi.filter(ImageFilter.GaussianBlur(16))
        im = Image.alpha_composite(im.convert("RGBA"), hi).convert("RGB")
        draw = ImageDraw.Draw(im)

    # Crown cavity, calyx, stem, and a leaf are rendered only after their
    # corresponding structural quale is introduced.
    if stage >= 2:
        crown_y = center_y - int(.81 * scale)
        draw.ellipse((center_x - 15, crown_y - 3, center_x + 15, crown_y + 11),
                     fill=(102, 76, 44), outline=(81, 62, 39))
        draw.line((center_x, crown_y + 2, center_x + 13, crown_y - 48),
                  fill=(82, 60, 39), width=8)
        draw.line((center_x - 5, crown_y + 3, center_x - 14, crown_y + 12),
                  fill=(89, 74, 46), width=2)
        draw.line((center_x + 4, crown_y + 3, center_x + 13, crown_y + 12),
                  fill=(89, 74, 46), width=2)
    if scene_on and scene_contains_leaf:
        # The graph says the scene contains a small leaf beside the fruit.
        lx, ly = center_x + int(.54 * scale), center_y - int(.25 * scale)
        draw.line((center_x + 12, crown_y - 43, lx + 2, ly - 12),
                  fill=(87, 69, 43), width=2)
        draw.ellipse((lx - 8, ly - 31, lx + 55, ly - 4),
                     fill=(71, 119, 62), outline=(53, 83, 47), width=2)
        draw.line((lx - 1, ly - 11, lx + 45, ly - 27), fill=(207, 211, 157), width=2)

    # Stage labels are explanatory presentation, not part of the quale graph.
    labels = {
        2: "2  FORM REFINEMENT  /  rounded apple body and cavities",
        3: "3  SURFACE REFINEMENT  /  cultivar color, lenticels, cuticle",
        4: "4  ILLUMINATION  /  light from above, shading, contact shadow",
        5: "5  SCENE  /  fruit situated on a surface",
        6: "6  RENDERED CONCEPT  /  apple visual quale in a scene",
    }
    draw.rectangle((0, 0, w, 52), fill=(249, 248, 244))
    draw.text((24, 16), labels[stage], fill=(48, 50, 46), font=_font(18, True))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)


def render_series(s, nodes, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    _quale_card(s, nodes, os.path.join(out_dir, "00_abstract_quale_graph.png"))
    labels = [
        (1, "01_circle_of_fruit.png"),
        (2, "02_apple_form.png"),
        (3, "03_apple_skin_pattern.png"),
        (4, "04_light_and_shading.png"),
        (5, "05_apple_in_scene.png"),
        (6, "06_rendered_apple_concept.png"),
    ]
    for stage, filename in labels:
        _render_mesh(s, nodes, os.path.join(out_dir, filename), stage=stage)
    # Contact sheet, in the intended abstraction-to-render order.
    thumbs = []
    for _stage, filename in [(0, "00_abstract_quale_graph.png")] + labels:
        im = Image.open(os.path.join(out_dir, filename)).convert("RGB")
        im.thumbnail((360, 280))
        thumbs.append((filename, im.copy()))
    sheet = Image.new("RGB", (1080, 3 * 330), (243, 243, 239))
    sd = ImageDraw.Draw(sheet)
    for i, (filename, im) in enumerate(thumbs):
        x, y = (i % 3) * 360, (i // 3) * 330
        sheet.paste(im, (x, y + 28))
        sd.text((x + 10, y + 7), filename.replace("_", " "),
                fill=(58, 60, 56), font=_font(13, True))
    grid_path = os.path.join(out_dir, "apple_abstraction_series.png")
    sheet.save(grid_path)
    return [name for _stage, name in labels], grid_path


def run():
    s, nodes = build_apple_quale()
    out_dir = os.path.join(_ROOT, "results", "apple_quale_render")
    images, grid = render_series(s, nodes, out_dir)
    # Record the substrate reading separately from pixel values. The quale's
    # signature is qualitative graph structure; no RGB or camera values enter it.
    quale_edges = [
        "has_visual_quale", "has_form", "has_region", "has_surface",
        "has_pattern", "has_finish", "illuminated_by", "casts",
        "situated_in", "contains", "has_ground", "has_backdrop",
        "has_illumination", "has_subject",
    ]
    signature = set()
    for node in nodes.values():
        signature.update(asr.concept_signature(s, node, edge_types=quale_edges))
    result = {
        "status": "exploratory graph-to-image interpretation",
        "semantic_boundary": "qualia are graph concepts and relations; RGB, mesh tessellation, camera, and pixel layout are renderer output",
        "qualia_signature": sorted([list(t) for t in signature]),
        "graph_nodes": {name: s.node(n)["attrs"].get("name") for name, n in nodes.items()},
        "held_concepts": {
            "apple": {"seed": "learned_lexicon", "name": "apples",
                      "definition": _attrs(s, nodes["apple"]).get("definition")},
            "circle": {"seed": "geometry_microtheory", "name": "circle",
                       "definition": _attrs(s, nodes["circle"]).get("definition")},
        },
        "abstraction_order": {
            "sequence": ["held apple concept", "held circle concept / circle of fruit",
                         "apple-specific form", "surface", "illumination", "scene", "render"],
            "status": "user-proposed substrate model; not established by the cited visual-science studies",
        },
        "scientific_observations": [
            {"claim": "Apple peel colors vary across cultivars, including green, yellow, and red.",
             "source": "https://www.sciencedirect.com/science/article/pii/S096399691400194X"},
            {"claim": "Apple shape and cavity traits vary across cultivars.",
             "source": "https://www.genresj.org/index.php/grj/article/download/genresj.HJIF8839/131"},
            {"claim": "Lenticels are observable apple-surface structures; cuticle and wax are studied surface features.",
             "sources": ["https://pmc.ncbi.nlm.nih.gov/articles/PMC3659274/",
                         "https://pmc.ncbi.nlm.nih.gov/articles/PMC7767305/"]},
            {"claim": "Human shape-from-shading judgments are influenced by assumptions of a single light source from above.",
             "source": "https://pubmed.ncbi.nlm.nih.gov/1635855"},
        ],
        "images": [os.path.join("results/apple_quale_render", x)
                   for x in ["00_abstract_quale_graph.png"] + images],
        "contact_sheet": os.path.relpath(grid, _ROOT),
    }
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(json.dumps({"contact_sheet": result["contact_sheet"],
                      "images": result["images"],
                      "qualia_signature_terms": len(signature)}, indent=2))
    return result


if __name__ == "__main__":
    run()
