"""A WORLD the agent inhabits: written language in MANY fonts — the reading
analogue of domains/persona_speech_world.py.

The persona_speech_world gives the agent several VOICES (personas: pitch /
resonance / vocal-tract) so the speaker-INVARIANT identity of a word (its
MEANING) is something it can GROUND by hearing the same word across voices,
while the voice itself stays a RECOVERABLE nuance. This world is the same move
for READING: it gives the agent several FONTS (typefaces / weights / styles)
and renders the same text across them, so the agent can ground the
font-INVARIANT identity of a LETTER (the WHAT — 'a' is one concept across every
typeface) by SEEING it varied, while the font/style stays a RECOVERABLE SIGNAL
(the HOW — the nuance a person reads off handwriting).

Why this is the right world for developing READING: a single fixed bitmap font
is a speaker-DEPENDENT recogniser — its letterform prototypes are per-font, and
a new typeface shifts the eye's signatures so the prototypes miss (the per-font
residual). Experiencing VARIETY dissolves that residual exactly as hearing many
speakers dissolved speaker-dependence: the agent grounds each letter to the
INVARIANT across fonts (cluster the eye's signatures of 'a' over many fonts ->
the invariant 'a'), and reads text in a font it has experienced variety from
where a cold single-prototype would fail.

Faithful to the architecture (CLAUDE.md): this is a WORLD ADAPTER. Python only
RENDERS glyphs to pixels (the world — a screen/printer; no agent decisions) and
moves the pixel arrays. The PERCEPTION is the substrate's real vision cortex
(substrate_rs.vision: Image nodes + real convolutions vs graph-resident Sobel +
V1 Gabor kernels — the same Eye as scripts/agent_reads_through_its_eye.py). The
GROUNDING is perceptual nearest-prototype matching over the eye's signatures
(the speech-recogniser mechanism, GENERALISED across fonts: speaker-invariant ->
font-invariant). No LLM, no pretrained OCR/font model, no Rust.
"""
from __future__ import annotations

import os
from typing import Optional

import numpy as np

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    _HAVE_PIL = True
except Exception:  # pragma: no cover - PIL is the world rendering dep
    _HAVE_PIL = False


# ---------------------------------------------------------------------------
# THE FONT INVENTORY — real TrueType faces (the world's variety). Each entry is
# (name, path, family, weight, style). The agent grounds the WHAT (letter) across
# these and recovers the HOW (which family/weight/style) from a rendering.
# ---------------------------------------------------------------------------

_CANDIDATE_FONTS = [
    # name              path                                                          family  weight   style
    ("lib-sans",        "/usr/share/fonts/liberation/LiberationSans-Regular.ttf",     "sans",  "regular", "upright"),
    ("lib-sans-bold",   "/usr/share/fonts/liberation/LiberationSans-Bold.ttf",        "sans",  "bold",    "upright"),
    ("lib-sans-italic", "/usr/share/fonts/liberation/LiberationSans-Italic.ttf",      "sans",  "regular", "italic"),
    ("lib-serif",       "/usr/share/fonts/liberation/LiberationSerif-Regular.ttf",    "serif", "regular", "upright"),
    ("lib-serif-bold",  "/usr/share/fonts/liberation/LiberationSerif-Bold.ttf",       "serif", "bold",    "upright"),
    ("lib-serif-italic","/usr/share/fonts/liberation/LiberationSerif-Italic.ttf",     "serif", "regular", "italic"),
    ("lib-mono",        "/usr/share/fonts/liberation/LiberationMono-Regular.ttf",     "mono",  "regular", "upright"),
    ("dejavu-sans",     "/usr/share/fonts/TTF/DejaVuSans.ttf",                         "sans",  "regular", "upright"),
    ("dejavu-serif",    "/usr/share/fonts/TTF/DejaVuSerif.ttf",                        "serif", "regular", "upright"),
    ("dejavu-mono",     "/usr/share/fonts/TTF/DejaVuSansMono.ttf",                     "mono",  "regular", "upright"),
    ("adwaita-sans",    "/usr/share/fonts/Adwaita/AdwaitaSans-Regular.ttf",           "sans",  "regular", "upright"),
    ("inter",           "/usr/share/fonts/inter/InterVariable.ttf",                   "sans",  "regular", "upright"),
    # ---- larger inventory: more families / weights / styles (the harder world) ----
    ("free-sans",       "/usr/share/fonts/gnu-free/FreeSans.otf",                      "sans",  "regular", "upright"),
    ("free-serif",      "/usr/share/fonts/gnu-free/FreeSerif.otf",                     "serif", "regular", "upright"),
    ("free-mono",       "/usr/share/fonts/gnu-free/FreeMono.otf",                      "mono",  "regular", "upright"),
    ("free-sans-bold",  "/usr/share/fonts/gnu-free/FreeSansBold.otf",                  "sans",  "bold",    "upright"),
    ("free-serif-ital", "/usr/share/fonts/gnu-free/FreeSerifItalic.otf",              "serif", "regular", "italic"),
    ("nimbus-sans",     "/usr/share/fonts/gsfonts/NimbusSans-Regular.otf",             "sans",  "regular", "upright"),
    ("nimbus-roman",    "/usr/share/fonts/gsfonts/NimbusRoman-Regular.otf",            "serif", "regular", "upright"),
    ("nimbus-mono",     "/usr/share/fonts/gsfonts/NimbusMonoPS-Regular.otf",           "mono",  "regular", "upright"),
    ("nimbus-roman-it", "/usr/share/fonts/gsfonts/NimbusRoman-Italic.otf",             "serif", "regular", "italic"),
    ("urw-gothic",      "/usr/share/fonts/gsfonts/URWGothic-Book.otf",                 "sans",  "regular", "upright"),
    ("urw-bookman",     "/usr/share/fonts/gsfonts/URWBookman-Light.otf",               "serif", "regular", "upright"),
    ("c059",            "/usr/share/fonts/gsfonts/C059-Roman.otf",                     "serif", "regular", "upright"),
    ("p052",            "/usr/share/fonts/gsfonts/P052-Roman.otf",                     "serif", "regular", "upright"),
    ("open-sans",       "/usr/share/fonts/TTF/OpenSans-Regular.ttf",                   "sans",  "regular", "upright"),
    ("fira-sans",       "/usr/share/fonts/TTF/FiraSans-Regular.ttf",                   "sans",  "regular", "upright"),
    ("fira-sans-ital",  "/usr/share/fonts/TTF/FiraSans-Italic.ttf",                    "sans",  "regular", "italic"),
    ("hack",            "/usr/share/fonts/TTF/Hack-Regular.ttf",                       "mono",  "regular", "upright"),
    ("cantarell",       "/usr/share/fonts/cantarell/Cantarell-VF.otf",                 "sans",  "regular", "upright"),
]

# CURSIVE faces — connected-script. No genuine script TTF is present on the host
# (no Dancing Script / Pacifico / Allura), so the world SIMULATES connected
# script (per the prompt's allowed fallback): render with NEGATIVE letter-spacing
# so adjacent glyphs touch + draw a baseline JOIN STROKE linking them, plus a
# slant. This is the genuine frontier for the segmenter: the fixed grid no longer
# isolates glyphs. If a real cursive face IS installed it is preferred (listed
# first); the simulation is a separate, declared mode (see render_cursive_text).
_CANDIDATE_CURSIVE_FONTS = [
    # name        path                                              base-face
    # Z003 (URW Chancery, a calligraphic chancery-italic script face) is the
    # closest GENUINE script face on the host — strongly slanted, calligraphic
    # strokes. We render it with negative tracking + a join stroke to produce
    # CONNECTED script (the cursive frontier). C059/Z003 italics are the bases.
    ("z003-script", "/usr/share/fonts/gsfonts/Z003-MediumItalic.otf",  "chancery"),
    ("c059-italic", "/usr/share/fonts/gsfonts/C059-Italic.otf",        "chancery"),
    ("p052-italic", "/usr/share/fonts/gsfonts/P052-Italic.otf",        "italic"),
]


def available_fonts() -> list[dict]:
    """The WORLD's font inventory that is actually present on disk. Each is a
    dict {name, path, family, weight, style}. A pure filesystem read — no agent
    decision. Empty when PIL or the faces are unavailable (then the caller falls
    back to the bitmap typefaces below)."""
    if not _HAVE_PIL:
        return []
    out = []
    for name, path, family, weight, style in _CANDIDATE_FONTS:
        if os.path.exists(path):
            out.append({"name": name, "path": path, "family": family,
                        "weight": weight, "style": style})
    return out


# ---------------------------------------------------------------------------
# THE WORLD — render text to a pixel image in a chosen font. Mechanical glyph
# blitting onto a fixed cell grid (the eye slices the same grid). NO agent
# involvement: the agent never sees `text`, only the pixels.
# ---------------------------------------------------------------------------

CELL = 28            # per-glyph cell (square) in pixels
FONT_PX = 22         # nominal glyph size; the world centres each glyph in CELL


def render_glyph(ch: str, font_path: str, cell: int = CELL,
                 size: int = FONT_PX) -> np.ndarray:
    """WORLD: render ONE character `ch` in the TrueType face at `font_path` to a
    (cell, cell) uint8 pixel patch (0=background, 255=ink), glyph centred. Pure
    rendering — the agent's eye perceives this patch, it never sees `ch`."""
    fnt = ImageFont.truetype(font_path, size)
    img = Image.new("L", (cell, cell), 0)
    d = ImageDraw.Draw(img)
    bb = d.textbbox((0, 0), ch, font=fnt)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    x = (cell - w) // 2 - bb[0]
    y = (cell - h) // 2 - bb[1]
    d.text((x, y), ch, fill=255, font=fnt)
    return np.array(img, dtype=np.uint8)


def render_text(text: str, font_path: str, cell: int = CELL,
                size: int = FONT_PX) -> tuple[np.ndarray, int]:
    """WORLD: render `text` to a (cell, cell*n) line image in one font, one cell
    per character (mono-grid; spaces are blank cells). Returns (image, n_glyphs).
    The eye slices the same fixed grid — mechanical, no agent decision."""
    text = text.lower()
    cells = []
    for ch in text:
        if ch == " ":
            cells.append(np.zeros((cell, cell), dtype=np.uint8))
        else:
            cells.append(render_glyph(ch, font_path, cell=cell, size=size))
    if not cells:
        return np.zeros((cell, cell), dtype=np.uint8), 0
    return np.concatenate(cells, axis=1), len(cells)


def line_cells(img: np.ndarray, n_glyphs: int, cell: int = CELL
               ) -> list[np.ndarray]:
    """Segment a line image into per-glyph (cell, cell) patches by column —
    the eye slices the same grid the world laid the glyphs on."""
    out = []
    for i in range(n_glyphs):
        patch = img[:, i * cell:(i + 1) * cell]
        if patch.shape[1] < cell:
            patch = np.pad(patch, ((0, 0), (0, cell - patch.shape[1])))
        out.append(patch)
    return out


# ---------------------------------------------------------------------------
# A BITMAP FALLBACK — if PIL/real fonts are unavailable, the mechanism still
# runs on >=3 distinct hand-drawn bitmap typefaces (smaller variety; the same
# font-invariant grounding). Each face is a dict ch -> 7x5 bit-rows.
# ---------------------------------------------------------------------------

# Three perceptually-distinct 5x7 faces: a plain face, a heavy/bold face, and a
# slanted face. (Lowercase + space only — the tractable bitmap case.)
_BITMAP_PLAIN = {
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    "a": ["00000", "00000", "01110", "00001", "01111", "10001", "01111"],
    "c": ["00000", "00000", "01110", "10001", "10000", "10001", "01110"],
    "e": ["00000", "00000", "01110", "10001", "11111", "10000", "01110"],
    "n": ["00000", "00000", "10110", "11001", "10001", "10001", "10001"],
    "o": ["00000", "00000", "01110", "10001", "10001", "10001", "01110"],
    "r": ["00000", "00000", "10110", "11001", "10000", "10000", "10000"],
    "s": ["00000", "00000", "01111", "10000", "01110", "00001", "11110"],
    "t": ["01000", "01000", "11100", "01000", "01000", "01001", "00110"],
}
_BITMAP_BOLD = {  # thicker strokes (a different "weight" -> shifted signatures)
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    "a": ["00000", "00000", "11110", "00011", "11111", "11011", "11111"],
    "c": ["00000", "00000", "11110", "11011", "11000", "11011", "11110"],
    "e": ["00000", "00000", "11110", "11011", "11111", "11000", "11110"],
    "n": ["00000", "00000", "11110", "11011", "11011", "11011", "11011"],
    "o": ["00000", "00000", "11110", "11011", "11011", "11011", "11110"],
    "r": ["00000", "00000", "11110", "11011", "11000", "11000", "11000"],
    "s": ["00000", "00000", "11111", "11000", "11110", "00011", "11110"],
    "t": ["11000", "11000", "11110", "11000", "11000", "11011", "01110"],
}
_BITMAP_SLANT = {  # right-shifted upper rows (a slant -> an "italic" face)
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    "a": ["00000", "00000", "00111", "00001", "00111", "01001", "00111"],
    "c": ["00000", "00000", "00111", "01001", "01000", "10001", "01110"],
    "e": ["00000", "00000", "00111", "01001", "01111", "10000", "01110"],
    "n": ["00000", "00000", "00110", "01001", "01001", "10001", "10001"],
    "o": ["00000", "00000", "00110", "01001", "01001", "10001", "01110"],
    "r": ["00000", "00000", "00110", "01001", "01000", "10000", "10000"],
    "s": ["00000", "00000", "00111", "01000", "00110", "00001", "11110"],
    "t": ["00010", "00010", "00111", "00010", "01000", "01001", "00110"],
}
BITMAP_FACES = {"plain": _BITMAP_PLAIN, "bold": _BITMAP_BOLD,
                "slant": _BITMAP_SLANT}
_BIT_SCALE = 4


def render_glyph_bitmap(ch: str, face: dict, scale: int = _BIT_SCALE
                        ) -> np.ndarray:
    bits = face.get(ch, face[" "])
    g = np.array([[255 if c == "1" else 0 for c in row] for row in bits],
                 dtype=np.uint8)
    return np.repeat(np.repeat(g, scale, 0), scale, 1)


def render_text_bitmap(text: str, face: dict, scale: int = _BIT_SCALE
                       ) -> tuple[np.ndarray, int]:
    text = text.lower()
    cells = [render_glyph_bitmap(ch, face, scale) for ch in text]
    if not cells:
        return np.zeros((7 * scale, 5 * scale), dtype=np.uint8), 0
    return np.concatenate(cells, axis=1), len(cells)


# ---------------------------------------------------------------------------
# THE HARDER WORLD — geometric TRANSFORMS + ERRORS + CONNECTED (cursive) script.
# Each is a pure WORLD operation on the pixel array (the screen/printer distorts
# the marks; no agent decision). The agent's eye sees the distorted pixels and
# must DEVELOP tolerance (augmentation) and/or NORMALISE (deskew/rescale) before
# grounding. All operate on a (cell, cell) uint8 glyph patch (0=bg, 255=ink).
# ---------------------------------------------------------------------------


def transform_glyph(patch: np.ndarray, rotate: float = 0.0, scale: float = 1.0,
                    shear: float = 0.0) -> np.ndarray:
    """WORLD geometric transform of a glyph patch, in a FIXED (cell, cell) frame:
      rotate  — degrees (counter-clockwise), about the patch centre,
      scale   — uniform glyph scale (0.7 shrinks, 1.5 enlarges; clipped to cell),
      shear   — horizontal shear factor (italic-beyond-italic; x += shear*y).
    The eye's fixed signatures CHANGE under this — the whole point. Pure PIL ops;
    the canvas size is preserved so segmentation/grid stays comparable."""
    cell = patch.shape[0]
    im = Image.fromarray(patch, mode="L")
    if abs(scale - 1.0) > 1e-3:
        # scale the glyph about the centre by resizing then re-centring on cell.
        ns = max(4, int(round(cell * scale)))
        im2 = im.resize((ns, ns), Image.BILINEAR)
        canvas = Image.new("L", (cell, cell), 0)
        off = (cell - ns) // 2
        canvas.paste(im2, (off, off))
        im = canvas
    if abs(shear) > 1e-3:
        # affine horizontal shear about the centre (x' = x + shear*(y - cy)).
        cy = cell / 2.0
        im = im.transform((cell, cell), Image.AFFINE,
                          (1, shear, -shear * cy, 0, 1, 0), Image.BILINEAR)
    if abs(rotate) > 1e-3:
        im = im.rotate(rotate, resample=Image.BILINEAR, expand=False, fillcolor=0)
    return np.array(im, dtype=np.uint8)


def add_noise(patch: np.ndarray, gaussian: float = 0.0, salt_pepper: float = 0.0,
              rng: Optional[np.random.Generator] = None) -> np.ndarray:
    """WORLD additive corruption:
      gaussian    — std of additive gaussian noise as a FRACTION of 255,
      salt_pepper — fraction of pixels flipped to a random extreme (0 or 255).
    Returns a uint8 patch. Redundancy/voting in the grounding is what tolerates
    this; the degradation curve says how much."""
    if rng is None:
        rng = np.random.default_rng()
    a = patch.astype(np.float32)
    if gaussian > 0:
        a = a + rng.normal(0.0, gaussian * 255.0, size=a.shape)
    if salt_pepper > 0:
        m = rng.random(a.shape) < salt_pepper
        sp = rng.random(a.shape) < 0.5
        a[m & sp] = 0.0
        a[m & ~sp] = 255.0
    return np.clip(a, 0, 255).astype(np.uint8)


def blur_glyph(patch: np.ndarray, radius: float = 1.0) -> np.ndarray:
    """WORLD optical blur (gaussian, `radius` px) — defocus / low resolution."""
    if radius <= 0:
        return patch
    im = Image.fromarray(patch, mode="L").filter(
        ImageFilter.GaussianBlur(radius=radius))
    return np.array(im, dtype=np.uint8)


def occlude_glyph(patch: np.ndarray, frac: float = 0.0,
                  rng: Optional[np.random.Generator] = None) -> np.ndarray:
    """WORLD partial OCCLUSION / smudge: blank a single rectangular region whose
    area is ~`frac` of the cell (a smudge / sticker / coffee ring over the mark).
    Returns a uint8 patch."""
    if frac <= 0:
        return patch
    if rng is None:
        rng = np.random.default_rng()
    a = patch.copy()
    cell = patch.shape[0]
    side = int(round(cell * (frac ** 0.5)))
    side = max(1, min(cell, side))
    r0 = int(rng.integers(0, max(1, cell - side + 1)))
    c0 = int(rng.integers(0, max(1, cell - side + 1)))
    a[r0:r0 + side, c0:c0 + side] = 0
    return a


def dropout_strokes(patch: np.ndarray, frac: float = 0.0,
                    rng: Optional[np.random.Generator] = None) -> np.ndarray:
    """WORLD stroke DROPOUT: erase a fraction `frac` of the INK pixels (a failing
    pen / faded ink — gaps along the strokes, not a solid smudge). Returns uint8."""
    if frac <= 0:
        return patch
    if rng is None:
        rng = np.random.default_rng()
    a = patch.copy()
    ink = a > 64
    drop = (rng.random(a.shape) < frac) & ink
    a[drop] = 0
    return a


# ---------------------------------------------------------------------------
# CONNECTED (cursive) SCRIPT — the genuine frontier. The fixed grid no longer
# isolates a glyph: letters TOUCH and JOIN. We render a word with NEGATIVE
# tracking (glyphs overlap) and a baseline JOIN STROKE between successive
# glyphs (a pen that never lifts), using a calligraphic script face when present.
# Returns the line image AND the per-glyph TRUE x-centres (ground truth for
# scoring the segmenter — NOT given to the agent; the agent must find boundaries
# from the eye's stroke map).
# ---------------------------------------------------------------------------

CURSIVE_CELL = 40        # taller cell: script has long ascenders/descenders
CURSIVE_PX = 30


def available_cursive_fonts() -> list[dict]:
    """The cursive/script faces present on disk (calligraphic chancery/italic).
    Each is {name, path, base}. Empty when none installed (then the caller uses
    simulate=True over an italic base — connection by negative tracking)."""
    if not _HAVE_PIL:
        return []
    out = []
    for name, path, base in _CANDIDATE_CURSIVE_FONTS:
        if os.path.exists(path):
            out.append({"name": name, "path": path, "base": base})
    return out


def render_cursive_word(word: str, font_path: str, *, cell: int = CURSIVE_CELL,
                        size: int = CURSIVE_PX, overlap: float = 0.22,
                        join: bool = True
                        ) -> tuple[np.ndarray, list[int], list[int]]:
    """WORLD: render `word` as CONNECTED script. Glyphs are placed with NEGATIVE
    tracking (each advance is reduced by `overlap` of the glyph width so strokes
    touch) and, when `join`, a baseline pen-stroke is drawn bridging successive
    glyphs (a hand that never lifts). A calligraphic script face gives the slant
    + stroke modulation. Returns (image, true_centres, true_widths): the per-
    glyph true x-centre and advance (GROUND TRUTH for scoring a segmenter — the
    agent never sees these; it must recover boundaries from the stroke map)."""
    word = word.lower()
    fnt = ImageFont.truetype(font_path, size)
    h = cell
    # First measure advances, then lay out with negative tracking.
    tmp = Image.new("L", (8, 8), 0)
    td = ImageDraw.Draw(tmp)
    advances = []
    for ch in word:
        bb = td.textbbox((0, 0), ch, font=fnt)
        advances.append(max(6, bb[2] - bb[0]))
    pen = 6
    positions = []
    for ad in advances:
        positions.append(pen)
        pen += int(round(ad * (1.0 - overlap)))
    W = pen + 8
    img = Image.new("L", (W, h), 0)
    d = ImageDraw.Draw(img)
    baseline = int(h * 0.72)
    centres, widths = [], []
    prev_join = None
    for ch, x0, ad in zip(word, positions, advances):
        bb = d.textbbox((0, 0), ch, font=fnt)
        gh = bb[3] - bb[1]
        y = baseline - (bb[3] - bb[1]) - bb[1] if gh > 0 else baseline - size // 2
        # vertically place so the glyph body sits on the baseline.
        y = baseline - bb[3]
        d.text((x0 - bb[0], y), ch, fill=255, font=fnt)
        c = x0 + ad // 2
        centres.append(c)
        widths.append(int(round(ad * (1.0 - overlap))))
        if join and prev_join is not None:
            # a connecting pen-stroke along the baseline between glyphs.
            d.line([(prev_join, baseline), (x0, baseline)], fill=255, width=2)
        prev_join = x0 + ad
    return np.array(img, dtype=np.uint8), centres, widths


__all__ = [
    "available_fonts", "render_glyph", "render_text", "line_cells",
    "BITMAP_FACES", "render_glyph_bitmap", "render_text_bitmap",
    "CELL", "FONT_PX",
    # harder world
    "transform_glyph", "add_noise", "blur_glyph", "occlude_glyph",
    "dropout_strokes",
    "available_cursive_fonts", "render_cursive_word",
    "CURSIVE_CELL", "CURSIVE_PX",
]
