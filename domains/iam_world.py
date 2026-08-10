"""iam_world.py -- MECHANICAL world adapter for IAM-OnDB (the authoritative online-handwriting
benchmark), RUN 63.

IAM-OnDB (Liwicki & Bunke, ICDAR'05) is REAL whiteboard online handwriting: 12,195 handwritten
LINE trajectories (lineStrokes-all) with per-line ground-truth transcription (ascii-all, CSR
section). This adapter is pure host I/O -- it reads the stroke XML into absolute ink, reads the
CSR transcription, ALIGNS stroke-line <-> text-line by ID, and slices a line's ink into WORD
segments by inter-stroke horizontal gaps. NO agent decision, NO graph state -- exactly the
ChatWorld / pen_world / deepwriting_world class of adapter.

FORMAT (decoded from the corpus, documented for reproducibility):
  * lineStrokes/<pfx>/<form>/<form>-<NN>.xml : one LINE. WhiteboardCaptureSession /
      WhiteboardDescription (DiagonallyOppositeCoords = board bounds) / StrokeSet /
      Stroke[colour,start_time,end_time] / Point[x,y,time]. <NN> = 1-based line index within the
      form. Coordinates: whiteboard pixels, y INCREASES DOWNWARD (top_left sensor) -- SAME
      convention as the DeepWriting bank (verified: top of 'T'/'A' = smaller y, descenders =
      larger y), so NO y-flip is applied.
  * ascii/<pfx>/<form>.txt : OCR: (clean) and CSR: (as-written) sections. The CSR text lines are
      the authoritative per-LINE ground truth and correspond 1:1, in order, to the -01,-02,...
      stroke line files (verified: form a01-000u has 6 stroke lines and 6 CSR lines).

62-CLASS MAP: reused verbatim from deepwriting_world (digits 0-9 -> 0..9, a-z -> 10..35,
A-Z -> 36..61) so run 61/62 decoders + the DeepWriting geometry bank apply unchanged.

WRITER/FORM SPLIT: IAM's per-form writer id is not carried in lineStrokes; this adapter groups by
FORM PREFIX (a01, a02, ...) as a writer proxy and exposes it as `writer`. For RUN 63 this matters
little: the geometry BANK is a DIFFERENT corpus (DeepWriting), so bank<->test writer-independence
is structural (cross-corpus), and the language model is corpus-general (Brown/WordNet + IAM CSR
counts). The split is a seeded held-out-FORM split, stated as such.
"""
from __future__ import annotations

import glob
import os
import re
import xml.etree.ElementTree as ET
from collections import defaultdict

import numpy as np

from domains.dataset_root import dataset_dir
from domains.deepwriting_world import CANON_SYM2CLASS, CANON_SYMBOLS, canon_class  # noqa: F401

IAM_STROKES_DIR = os.environ.get(
    "IAM_STROKES_DIR", dataset_dir("handwriting", "iam_onbd", "lineStrokes"))
IAM_ASCII_DIR = os.environ.get(
    "IAM_ASCII_DIR", dataset_dir("handwriting", "iam_ascii", "ascii"))

_LINE_RE = re.compile(r"^(?P<form>.+)-(?P<idx>\d+)$")


# ------------------------------------------------------------------------------------------- #
#  Stroke XML parse (mechanical).
# ------------------------------------------------------------------------------------------- #
def parse_line_strokes(xml_path: str) -> dict:
    """Parse one lineStrokes XML -> {'strokes': [ (N,3) float array x,y,time ], 'bounds':(x0,y0,x1,y1)}.
    Pure I/O -- no decision."""
    root = ET.parse(xml_path).getroot()
    bounds = None
    diag = root.find(".//DiagonallyOppositeCoords")
    vert = root.find(".//VerticallyOppositeCoords")
    horiz = root.find(".//HorizontallyOppositeCoords")
    if diag is not None and vert is not None and horiz is not None:
        # board rectangle corners; take min/max over the three given points.
        xs = [float(vert.get("x")), float(horiz.get("x")), float(diag.get("x"))]
        ys = [float(vert.get("y")), float(horiz.get("y")), float(diag.get("y"))]
        bounds = (min(xs), min(ys), max(xs), max(ys))
    strokes = []
    for st in root.findall(".//StrokeSet/Stroke"):
        pts = []
        for p in st.findall("Point"):
            t = p.get("time")
            pts.append([float(p.get("x")), float(p.get("y")),
                        float(t) if t is not None else 0.0])
        if len(pts) >= 1:
            strokes.append(np.asarray(pts, float))
    return {"strokes": strokes, "bounds": bounds}


def parse_csr(txt_path: str) -> list:
    """Return the CSR (as-written) transcription lines, in order. Pure I/O."""
    lines = []
    in_csr = False
    with open(txt_path, encoding="latin-1") as f:
        for raw in f:
            s = raw.rstrip("\n")
            if s.strip() == "CSR:":
                in_csr = True
                continue
            if in_csr:
                if s.strip():
                    lines.append(s.strip())
    return lines


def form_of(line_id: str):
    """'a01-000u-01' -> ('a01-000u', 1)."""
    m = _LINE_RE.match(line_id)
    if not m:
        return None, None
    return m.group("form"), int(m.group("idx"))


def _ascii_path(form: str, ascii_root: str = None) -> str:
    # form 'a01-000u' -> ascii/a01/a01-000/a01-000u.txt (middle dir = form minus trailing letters).
    ascii_root = ascii_root or IAM_ASCII_DIR
    pfx = form.split("-")[0]
    m = re.match(r"([a-z]\d+-\d+)", form)
    sub = m.group(1) if m else form
    return os.path.join(ascii_root, pfx, sub, form + ".txt")


def _alpha_tokens(text: str) -> list:
    """Whitespace tokens that are purely alphabetic (drops punctuation tokens like '.' ',')."""
    return [t for t in text.split() if t.isalpha()]


# ------------------------------------------------------------------------------------------- #
#  Line loader -- align stroke-line <-> CSR text-line by ID.
# ------------------------------------------------------------------------------------------- #
def iter_forms(strokes_root: str = None):
    """Yield form directories (each holds a form's line XMLs)."""
    strokes_root = strokes_root or IAM_STROKES_DIR
    for d in sorted(glob.glob(os.path.join(strokes_root, "*", "*"))):
        if os.path.isdir(d):
            yield d


def load_lines(strokes_root: str = None, ascii_root: str = None, *, max_forms: int = None,
               forms: set = None) -> list:
    """Load aligned (strokes, text) per LINE. Returns list of
    {line_id, form, writer, idx, strokes[list of (N,3)], text, words[alpha tokens], bounds}.
    Only lines with BOTH stroke XML and an aligned CSR line are kept. Mechanical."""
    strokes_root = strokes_root or IAM_STROKES_DIR
    ascii_root = ascii_root or IAM_ASCII_DIR
    out = []
    n_forms = 0
    for fdir in iter_forms(strokes_root):
        xmls = sorted(glob.glob(os.path.join(fdir, "*.xml")))
        if not xmls:
            continue
        # group by form.
        by_form = defaultdict(list)
        for x in xmls:
            lid = os.path.splitext(os.path.basename(x))[0]
            form, idx = form_of(lid)
            if form is None:
                continue
            by_form[form].append((idx, lid, x))
        for form, items in by_form.items():
            if forms is not None and form not in forms:
                continue
            csr_path = _ascii_path(form, ascii_root)
            if not os.path.exists(csr_path):
                continue
            csr = parse_csr(csr_path)
            items.sort(key=lambda t: t[0])
            writer = form.split("-")[0]
            for idx, lid, x in items:
                if not (1 <= idx <= len(csr)):
                    continue
                text = csr[idx - 1]
                parsed = parse_line_strokes(x)
                if not parsed["strokes"]:
                    continue
                out.append({"line_id": lid, "form": form, "writer": writer, "idx": idx,
                            "strokes": parsed["strokes"], "text": text,
                            "words": _alpha_tokens(text), "bounds": parsed["bounds"]})
            n_forms += 1
            if max_forms is not None and n_forms >= max_forms:
                return out
    return out


# ------------------------------------------------------------------------------------------- #
#  Word segmentation by inter-stroke horizontal gaps.
# ------------------------------------------------------------------------------------------- #
def _stroke_xbounds(strokes: list) -> list:
    return [(float(np.asarray(s)[:, 0].min()), float(np.asarray(s)[:, 0].max())) for s in strokes]


def line_height(strokes: list) -> float:
    """Robust vertical text extent of a line (a proxy for character scale)."""
    ys = np.concatenate([np.asarray(s)[:, 1] for s in strokes])
    return float(np.percentile(ys, 95) - np.percentile(ys, 5))


def _gap_sequence(strokes: list):
    """Sort strokes left-to-right by min-x; return (order, gaps) where gaps[k] = horizontal gap
    between the running left-to-right frontier and stroke order[k] (k>=1). Handles back-tracking
    (i-dots, t-bars) via a running max frontier."""
    xb = _stroke_xbounds(strokes)
    order = sorted(range(len(strokes)), key=lambda i: xb[i][0])
    gaps = [0.0]
    frontier = xb[order[0]][1]
    for k in range(1, len(order)):
        lo, hi = xb[order[k]]
        gaps.append(max(0.0, lo - frontier))
        frontier = max(frontier, hi)
    return order, gaps, xb


def segment_words(strokes: list, *, n_words: int = None, gap_frac: float = 0.9) -> list:
    """Split a line's strokes into WORD groups by horizontal gaps.

    ORACLE mode (`n_words` given): cut at the (n_words-1) largest frontier gaps -- isolates the
    READING question from the segmentation question (the run-62 philosophy: hold the axis under
    test open, fix the others by oracle where a separate solved problem).
    ADAPTIVE mode (`n_words` None): cut at every gap exceeding `gap_frac * line_height` (per-line
    adaptive threshold). Returns a list of word groups, each a list of the ORIGINAL stroke arrays
    in left-to-right order."""
    if not strokes:
        return []
    order, gaps, _ = _gap_sequence(strokes)
    K = len(order)
    if K == 1:
        return [[strokes[order[0]]]]
    if n_words is not None:
        n_cuts = max(0, min(K - 1, n_words - 1))
        cut_ks = set(sorted(range(1, K), key=lambda k: -gaps[k])[:n_cuts])
    else:
        thr = gap_frac * max(line_height(strokes), 1e-6)
        cut_ks = {k for k in range(1, K) if gaps[k] > thr}
    groups = []
    cur = [strokes[order[0]]]
    for k in range(1, K):
        if k in cut_ks:
            groups.append(cur)
            cur = []
        cur.append(strokes[order[k]])
    groups.append(cur)
    return groups


def writer_form_split(lines: list, *, n_test_frac: float = 0.5, seed: int = 20260706) -> tuple:
    """Seeded held-out-FORM split (writer proxy = form prefix). Returns (bg_lines, test_lines)."""
    writers = sorted({l["writer"] for l in lines})
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(writers))
    n_test = max(1, int(round(n_test_frac * len(writers))))
    test_w = {writers[int(order[i])] for i in range(n_test)}
    test = [l for l in lines if l["writer"] in test_w]
    bg = [l for l in lines if l["writer"] not in test_w]
    return bg, test


__all__ = ["parse_line_strokes", "parse_csr", "form_of", "load_lines", "iter_forms",
           "segment_words", "line_height", "writer_form_split", "canon_class",
           "CANON_SYMBOLS", "CANON_SYM2CLASS", "IAM_STROKES_DIR", "IAM_ASCII_DIR"]
