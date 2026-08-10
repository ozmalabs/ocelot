"""Vision primitives as graph-resident data.

The biology-faithful move (Hubel & Wiesel 1959; LGN center-surround;
the V1→V2→V4→IT hierarchy): convolution kernels ARE the substrate of
biological visual processing. A V1 simple cell is a Gabor filter; an
LGN ON-center cell is a Difference-of-Gaussians kernel. The receptive
field IS the primitive.

This module exposes that view to the substrate:

* `Image` nodes carry pixels (raw bytes) + metadata (width, height,
  channels, dtype, origin).
* `Kernel` nodes carry weights (a `List[f64]` attr) + metadata (name,
  kh, kw, origin). The matrix is exposed via `kernel_to_array` AND
  as a queryable attr — the agent can `Attr(Var("k"), "weights")` it
  and inspect / compare receptive fields as graph data, and the Rust
  `ChangeDetect` Term reads the same attr to run the convolve math.
* `convolve` / `pool` / `threshold` consume Image+Kernel nodes and
  produce new Image nodes via the substrate's mutation surface. The
  pipeline is graph-resident: each intermediate Image is a node with
  edges to the kernel that produced it, so the agent can trace its
  perceptual derivation back to first principles.

What this buys: a vision pipeline becomes **introspectable and
editable graph data**, not opaque Python. The agent can ask "what
kernels do I have? what does each detect? which kernel produced this
percept?" via the existing DSL. It can author a new V1 simple cell at
a novel orientation by adding a Kernel node. It can compose pipelines
by wiring `has_kernel` and `produces` edges.

Compare `domains/vision.py` — same OpenCV operations, but kernels
are inlined and invisible. Same biology, two different commitments:
this module commits to graph-resident primitives.
"""
from __future__ import annotations

import math
import struct
from typing import Any, Iterable, Optional

import numpy as np

from . import Substrate as _PySubstrate
from . import _native

# Optional cv2 — used as the fastest path for convolution when present.
try:
    import cv2 as _cv2
    _HAS_CV2 = True
except ImportError:
    _cv2 = None
    _HAS_CV2 = False

# Scipy is the fallback for the convolution; if neither cv2 nor scipy
# is present we use a pure-numpy convolution (slower but correct).
try:
    from scipy import ndimage as _ndi
    _HAS_SCIPY = True
except ImportError:
    _ndi = None
    _HAS_SCIPY = False


# --- Node type names + edge types --------------------------------------

IMAGE = "Image"
KERNEL = "Kernel"
PIPELINE = "VisualPipeline"

# Edges between vision-domain nodes — make the perceptual derivation
# visible. `produced_by` points an Image at the Kernel that filtered
# it; `from_input` points it at the source Image. The agent can walk
# these to ask "where did this percept come from?".
PRODUCED_BY = "produced_by"
FROM_INPUT = "from_input"
HAS_KERNEL = "has_kernel"
HAS_INPUT = "has_input"
PRODUCES = "produces"


# --- Substrate plumbing -------------------------------------------------

def _native_substrate(s):
    return s._inner if isinstance(s, _PySubstrate) else s


def seed_vision_grammar(s, namespace: str | None = None) -> int:
    """Seed productions for the vision-domain types + edges.

    Returns the number of productions added. Idempotent in spirit —
    re-calling will add duplicate productions (each gets its own
    provenance); callers who care should track this themselves.

    `namespace` (optional) prefixes every type with `<ns>:` via the
    same shape `substrate_rs.ext.import_grammar` uses. Useful when
    integrating into an agent whose grammar already has e.g. an
    `Image` type for a different domain.
    """
    from . import NodePattern, Production
    inner = _native_substrate(s)

    def _t(name: str) -> str:
        if namespace is None or ":" in name:
            return name
        return f"{namespace}:{name}"

    def _et(name: str) -> str:
        if namespace is None or ":" in name:
            return name
        return f"{namespace}:{name}"

    # Every Image / Kernel / Pipeline node insertion needs an
    # admissibility-free path so the operations below can create them
    # freely. Use permissive productions on the structural edges.
    prods = [
        # has_kernel: a pipeline / image points at the kernel that
        # processed it
        Production(
            src=NodePattern(type=_t(IMAGE), var="src"),
            edge_type=_et(PRODUCED_BY),
            tgt=NodePattern(type=_t(KERNEL), var="tgt"),
            where=None, weight=None,
            provenance=f"{namespace or 'vision'}:image_produced_by_kernel",
        ),
        Production(
            src=NodePattern(type=_t(IMAGE), var="src"),
            edge_type=_et(FROM_INPUT),
            tgt=NodePattern(type=_t(IMAGE), var="tgt"),
            where=None, weight=None,
            provenance=f"{namespace or 'vision'}:image_from_input_image",
        ),
        Production(
            src=NodePattern(type=_t(PIPELINE), var="src"),
            edge_type=_et(HAS_KERNEL),
            tgt=NodePattern(type=_t(KERNEL), var="tgt"),
            where=None, weight=None,
            provenance=f"{namespace or 'vision'}:pipeline_has_kernel",
        ),
        Production(
            src=NodePattern(type=_t(PIPELINE), var="src"),
            edge_type=_et(HAS_INPUT),
            tgt=NodePattern(type=_t(IMAGE), var="tgt"),
            where=None, weight=None,
            provenance=f"{namespace or 'vision'}:pipeline_has_input",
        ),
        Production(
            src=NodePattern(type=_t(PIPELINE), var="src"),
            edge_type=_et(PRODUCES),
            tgt=NodePattern(type=_t(IMAGE), var="tgt"),
            where=None, weight=None,
            provenance=f"{namespace or 'vision'}:pipeline_produces",
        ),
    ]
    for p in prods:
        inner.add_production(p.to_dict() if hasattr(p, "to_dict") else p)
    return len(prods)


# --- Image bridge: numpy ↔ graph node ----------------------------------

def image_from_array(s, arr: np.ndarray, origin: str = "external") -> Any:
    """Create an Image node holding `arr`. Stores width / height /
    channels / dtype as attrs and the raw bytes in `pixels`. Returns
    the new NodeID.

    Accepts H×W or H×W×C arrays in any numeric dtype; canonicalises
    layout in-graph. The dtype attr lets `image_to_array` reconstruct
    without ambiguity.
    """
    inner = _native_substrate(s)
    if arr.ndim == 2:
        h, w = arr.shape
        c = 1
    elif arr.ndim == 3:
        h, w, c = arr.shape
    else:
        raise ValueError(f"image array must be 2-D or 3-D, got shape {arr.shape}")
    dtype = str(arr.dtype)
    pixels = arr.tobytes()
    return inner.add_node(IMAGE, {
        "width": w, "height": h, "channels": c,
        "dtype": dtype, "pixels": pixels,
        "origin": origin,
    })


def image_to_array(s, image_nid: Any) -> np.ndarray:
    """Reconstruct the numpy array stored in an Image node. Shape is
    HxW for single-channel images, HxWxC otherwise — matching how
    `image_from_array` accepts them."""
    inner = _native_substrate(s)
    node = inner.node(image_nid)
    a = node["attrs"]
    arr = np.frombuffer(a["pixels"], dtype=np.dtype(a["dtype"]))
    h, w, c = int(a["height"]), int(a["width"]), int(a["channels"])
    if c == 1:
        return arr.reshape(h, w)
    return arr.reshape(h, w, c)


def image_shape(s, image_nid: Any) -> tuple[int, int, int]:
    """Cheap accessor — (height, width, channels) without
    deserialising the pixel bytes."""
    inner = _native_substrate(s)
    a = inner.node(image_nid)["attrs"]
    return int(a["height"]), int(a["width"]), int(a["channels"])


# --- Kernel bridge: numpy ↔ graph node ---------------------------------

def kernel_from_matrix(s, name: str, weights: np.ndarray,
                       origin: str = "user_authored") -> Any:
    """Build a Kernel node from a numpy weight matrix.

    The matrix is stored as a `List[f64]` in the `weights` attr (row-major
    flattened) so the agent and the Rust `ChangeDetect` Term can read it
    directly via ``Attr(k, "weights")`` as a graph-resident value (the T7
    contract: ``Kernel node attrs {weights: List<f64>, kh: Int, kw: Int}``).
    The `kh` / `kw` attrs describe its shape; `name` is the diagnostic
    label (e.g. "gabor:theta=0,sigma=2"), `origin` is provenance
    ("v1_bank", "user_authored", "learned:step=42").
    """
    if weights.ndim != 2:
        raise ValueError(f"kernel weights must be 2-D, got {weights.shape}")
    weights = weights.astype(np.float32, copy=False)
    kh, kw = weights.shape
    inner = _native_substrate(s)
    return inner.add_node(KERNEL, {
        "name": name,
        "kh": int(kh), "kw": int(kw),
        "dtype": "float32",
        "weights": weights.flatten().tolist(),
        "origin": origin,
    })


def kernel_to_array(s, kernel_nid: Any) -> np.ndarray:
    """Reconstruct the float32 weight matrix from a Kernel node."""
    inner = _native_substrate(s)
    a = inner.node(kernel_nid)["attrs"]
    arr = np.array(a["weights"], dtype=np.float32)
    return arr.reshape(int(a["kh"]), int(a["kw"]))


def kernel_describe(s, kernel_nid: Any) -> dict:
    """Cheap snapshot — name, shape, stats. For the agent's
    introspection. Doesn't materialise the full matrix unnecessarily."""
    inner = _native_substrate(s)
    a = inner.node(kernel_nid)["attrs"]
    arr = np.array(a["weights"], dtype=np.float32)
    return {
        "name": a["name"],
        "shape": (int(a["kh"]), int(a["kw"])),
        "origin": a.get("origin", ""),
        "mean": float(arr.mean()),
        "std": float(arr.std()),
        "min": float(arr.min()),
        "max": float(arr.max()),
        "sum": float(arr.sum()),
    }


def kernel_to_image(s, kernel_nid: Any, scale: bool = True) -> Any:
    """Render a Kernel's weight matrix as an Image node — for the
    agent to LOOK AT its own receptive fields (the same trick
    visualisation papers use).

    `scale=True` normalises weights into [0, 255] uint8 so the result
    displays cleanly; False keeps the float values.
    """
    arr = kernel_to_array(s, kernel_nid)
    if scale:
        lo, hi = arr.min(), arr.max()
        if hi > lo:
            arr = ((arr - lo) / (hi - lo) * 255).astype(np.uint8)
        else:
            arr = np.zeros_like(arr, dtype=np.uint8)
    name = _native_substrate(s).node(kernel_nid)["attrs"].get("name", "kernel")
    return image_from_array(s, arr, origin=f"kernel_viz:{name}")


# --- Canonical kernel constructors --------------------------------------
# Each returns a NodeID; the matrices follow the textbook definitions.

def _odd_ksize(ksize: int | None, default: int) -> int:
    if ksize is None:
        return default
    if ksize % 2 == 0:
        raise ValueError(f"ksize must be odd; got {ksize}")
    return ksize


def gabor(s, sigma: float = 2.0, theta: float = 0.0,
          lambda_: float = 4.0, gamma: float = 0.5,
          psi: float = 0.0, ksize: int | None = None) -> Any:
    """V1 simple cell — a Gabor filter.

    Hubel & Wiesel (1959) found V1 simple cells respond to oriented
    edges at a preferred angle; Daugman (1985) showed Gabor functions
    fit those receptive fields. Build the V1 column by calling this
    at a bank of orientations (see `v1_bank`).

    Parameters match cv2.getGaborKernel: sigma is envelope sigma,
    theta is orientation (radians), lambda_ is wavelength, gamma is
    spatial-aspect ratio, psi is phase offset.
    """
    if ksize is None:
        ksize = max(5, int(2 * round(2.5 * sigma) + 1))
    ksize = _odd_ksize(ksize, ksize)
    if _HAS_CV2:
        k = _cv2.getGaborKernel(
            (ksize, ksize), sigma, theta, lambda_, gamma, psi,
            ktype=_cv2.CV_32F,
        )
    else:
        k = _gabor_pure(ksize, sigma, theta, lambda_, gamma, psi)
    name = f"gabor:θ={theta:.2f},σ={sigma:.1f},λ={lambda_:.1f}"
    return kernel_from_matrix(s, name=name, weights=k, origin="gabor")


def _gabor_pure(ksize: int, sigma: float, theta: float,
                lambda_: float, gamma: float, psi: float) -> np.ndarray:
    """Fallback Gabor construction without OpenCV. Matches the
    canonical Daugman 1985 formulation."""
    half = ksize // 2
    y, x = np.mgrid[-half:half + 1, -half:half + 1].astype(np.float32)
    ct, st = math.cos(theta), math.sin(theta)
    x_ = x * ct + y * st
    y_ = -x * st + y * ct
    envelope = np.exp(-(x_**2 + (gamma * y_)**2) / (2 * sigma**2))
    carrier = np.cos(2 * math.pi * x_ / lambda_ + psi)
    return (envelope * carrier).astype(np.float32)


def gaussian(s, sigma: float = 1.0, ksize: int | None = None) -> Any:
    """Smoothing kernel. Used at every level of biological vision
    (LGN, V1, …) to set the scale at which features are detected."""
    if ksize is None:
        ksize = max(3, int(2 * round(3.0 * sigma) + 1))
    ksize = _odd_ksize(ksize, ksize)
    half = ksize // 2
    y, x = np.mgrid[-half:half + 1, -half:half + 1].astype(np.float32)
    g = np.exp(-(x**2 + y**2) / (2 * sigma**2))
    g /= g.sum()
    return kernel_from_matrix(
        s, name=f"gaussian:σ={sigma:.2f}",
        weights=g, origin="gaussian",
    )


def dog(s, sigma_center: float = 1.0, sigma_surround: float = 2.0,
        ksize: int | None = None) -> Any:
    """Difference-of-Gaussians — the LGN center-surround receptive
    field. Marr & Hildreth (1980) showed DoG approximates the
    Laplacian-of-Gaussian edge detector; matches Enroth-Cugell &
    Robson's (1966) LGN measurements.

    `sigma_center < sigma_surround` gives an ON-center cell (positive
    in the middle, negative ring around); swap to get OFF-center.
    """
    if ksize is None:
        # Size against the WIDER Gaussian so the kernel is large
        # enough to resolve it without truncation distorting the
        # normalised centre weight. Either σ may be the larger one
        # (ON-center vs OFF-center).
        sigma_max = max(sigma_center, sigma_surround)
        ksize = max(7, int(2 * round(3.0 * sigma_max) + 1))
    ksize = _odd_ksize(ksize, ksize)
    half = ksize // 2
    y, x = np.mgrid[-half:half + 1, -half:half + 1].astype(np.float32)
    g_c = np.exp(-(x**2 + y**2) / (2 * sigma_center**2))
    g_s = np.exp(-(x**2 + y**2) / (2 * sigma_surround**2))
    g_c /= g_c.sum()
    g_s /= g_s.sum()
    name = f"dog:σc={sigma_center:.1f},σs={sigma_surround:.1f}"
    return kernel_from_matrix(s, name=name, weights=g_c - g_s, origin="dog")


def sobel(s, dx: int = 1, dy: int = 0, ksize: int = 3) -> Any:
    """Edge gradient — first derivative. dx=1,dy=0 is the x-gradient
    (vertical edges), dx=0,dy=1 the y-gradient. Used at the very
    front of the V1 pipeline alongside the Gabor bank."""
    ksize = _odd_ksize(ksize, ksize)
    if _HAS_CV2:
        kx, ky = _cv2.getDerivKernels(dx, dy, ksize, normalize=False)
        # Outer product of the two 1-D kernels gives the 2-D conv kernel.
        k = (ky @ kx.T).astype(np.float32)
    else:
        # Textbook 3×3 sobels; ksize=3 only in the pure fallback.
        if ksize != 3:
            raise ValueError("sobel without cv2 only supports ksize=3")
        if dx == 1 and dy == 0:
            k = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
        elif dx == 0 and dy == 1:
            k = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32)
        else:
            raise ValueError(f"sobel without cv2 only supports (dx,dy)=(1,0) or (0,1)")
    return kernel_from_matrix(
        s, name=f"sobel:dx={dx},dy={dy},k={ksize}",
        weights=k, origin="sobel",
    )


def laplacian(s, ksize: int = 3) -> Any:
    """Second derivative — pure edge detector (zero-crossings).
    The Laplacian-of-Gaussian (LoG) — laplacian applied after a
    Gaussian smooth — is Marr's classic edge primitive."""
    if ksize == 3:
        k = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32)
    elif ksize == 5:
        k = np.array([
            [0, 0, 1, 0, 0],
            [0, 1, 2, 1, 0],
            [1, 2, -16, 2, 1],
            [0, 1, 2, 1, 0],
            [0, 0, 1, 0, 0],
        ], dtype=np.float32)
    else:
        raise ValueError(f"laplacian ksize must be 3 or 5; got {ksize}")
    return kernel_from_matrix(s, name=f"laplacian:k={ksize}",
                              weights=k, origin="laplacian")


def identity(s, ksize: int = 1) -> Any:
    """Pass-through — useful as a no-op placeholder in a pipeline."""
    ksize = _odd_ksize(ksize, ksize)
    half = ksize // 2
    k = np.zeros((ksize, ksize), dtype=np.float32)
    k[half, half] = 1.0
    return kernel_from_matrix(s, name=f"identity:k={ksize}",
                              weights=k, origin="identity")


# --- Biology-shaped banks ------------------------------------------------

def v1_bank(s, n_orientations: int = 8, sigma: float = 2.0,
            lambda_: float = 4.0, ksize: int | None = None) -> list:
    """A V1 column — Gabor bank at evenly-spaced orientations.

    Hubel & Wiesel's orientation columns sample ~10–15 orientations
    in macaque V1; we default to 8 (the common engineering choice).
    Returns a list of Kernel NodeIDs.
    """
    return [
        gabor(s, sigma=sigma, theta=i * math.pi / n_orientations,
              lambda_=lambda_, ksize=ksize)
        for i in range(n_orientations)
    ]


def lgn_pair(s, sigma_on: float = 1.0, sigma_off: float = 2.0,
             ksize: int | None = None) -> tuple:
    """An ON-center / OFF-center pair — the LGN's two parallel
    channels. The brain runs both continuously; downstream stages
    consume whichever one is more informative for the local task."""
    on = dog(s, sigma_center=sigma_on, sigma_surround=sigma_off, ksize=ksize)
    off = dog(s, sigma_center=sigma_off, sigma_surround=sigma_on, ksize=ksize)
    return on, off


# --- Operations: produce new Image nodes via Π --------------------------

def convolve(s, image_nid: Any, kernel_nid: Any,
             padding: str = "same", origin: str | None = None,
             wire_provenance: bool = True) -> Any:
    """Apply `kernel_nid` to `image_nid`; return a new Image NodeID
    holding the filtered result.

    `padding` is "same" (output same size, edges reflect-padded) or
    "valid" (no padding, output shrinks by kernel size − 1).
    `wire_provenance` (default True) adds `produced_by` and
    `from_input` edges so the agent can trace the perceptual
    derivation by walking the graph.

    Uses cv2.filter2D when available (fast), scipy.ndimage as
    fallback, pure numpy as last resort.
    """
    img = image_to_array(s, image_nid)
    k = kernel_to_array(s, kernel_nid)
    # cv2.filter2D wants single- or multi-channel uint8/float32.
    if _HAS_CV2:
        # cv2 expects BorderTypes; 'same' = reflect-padding.
        if padding == "same":
            border = _cv2.BORDER_REFLECT
        elif padding == "valid":
            border = _cv2.BORDER_CONSTANT
        else:
            raise ValueError(f"unknown padding: {padding}")
        # Work in float32 to keep edge information; cast back later.
        src = img.astype(np.float32)
        out = _cv2.filter2D(src, ddepth=-1, kernel=k, borderType=border)
        if padding == "valid":
            kh, kw = k.shape
            ph, pw = kh // 2, kw // 2
            out = out[ph:out.shape[0] - ph, pw:out.shape[1] - pw]
    elif _HAS_SCIPY:
        if padding == "same":
            mode = "reflect"
        elif padding == "valid":
            mode = "constant"
        else:
            raise ValueError(f"unknown padding: {padding}")
        if img.ndim == 2:
            out = _ndi.convolve(img.astype(np.float32), k, mode=mode)
        else:
            # Per-channel convolve.
            channels = [_ndi.convolve(img[..., c].astype(np.float32), k, mode=mode)
                        for c in range(img.shape[-1])]
            out = np.stack(channels, axis=-1)
        if padding == "valid":
            kh, kw = k.shape
            ph, pw = kh // 2, kw // 2
            out = out[ph:out.shape[0] - ph, pw:out.shape[1] - pw]
    else:
        out = _pure_numpy_convolve(img, k, padding)
    out_arr = out.astype(np.float32)
    # Origin string lets the agent trace where this image came from.
    if origin is None:
        kname = _native_substrate(s).node(kernel_nid)["attrs"].get("name", "kernel")
        origin = f"convolve({kname})"
    out_nid = image_from_array(s, out_arr, origin=origin)
    if wire_provenance:
        inner = _native_substrate(s)
        inner.add_edge(out_nid, PRODUCED_BY, kernel_nid)
        inner.add_edge(out_nid, FROM_INPUT, image_nid)
    return out_nid


def _pure_numpy_convolve(img: np.ndarray, k: np.ndarray,
                         padding: str) -> np.ndarray:
    """Slow but always-correct fallback. For tests where neither cv2
    nor scipy is available — practically never hit, but we don't
    want a missing optional dep to mean missing convolution."""
    kh, kw = k.shape
    ph, pw = kh // 2, kw // 2
    if img.ndim == 2:
        if padding == "same":
            padded = np.pad(img.astype(np.float32),
                            ((ph, ph), (pw, pw)), mode="reflect")
        else:
            padded = img.astype(np.float32)
        oh, ow = padded.shape[0] - kh + 1, padded.shape[1] - kw + 1
        out = np.zeros((oh, ow), dtype=np.float32)
        # Flip the kernel for true convolution (vs cross-correlation).
        kf = np.flipud(np.fliplr(k))
        for i in range(oh):
            for j in range(ow):
                out[i, j] = (padded[i:i + kh, j:j + kw] * kf).sum()
        return out
    return np.stack([_pure_numpy_convolve(img[..., c], k, padding)
                     for c in range(img.shape[-1])], axis=-1)


def pool(s, image_nid: Any, kh: int = 2, kw: int = 2,
         mode: str = "max", origin: str | None = None) -> Any:
    """Pooling — kh×kw window, stride = (kh, kw). `mode` is "max" or
    "mean". Pooling models V2/V4 complex cells (Rolls 2012): a single
    output unit summarises the strongest response across a small
    receptive field, giving translation tolerance."""
    img = image_to_array(s, image_nid)
    h, w = img.shape[:2]
    oh, ow = h // kh, w // kw
    cropped = img[:oh * kh, :ow * kw]
    if img.ndim == 2:
        reshaped = cropped.reshape(oh, kh, ow, kw)
        if mode == "max":
            out = reshaped.max(axis=(1, 3))
        elif mode == "mean":
            out = reshaped.mean(axis=(1, 3))
        else:
            raise ValueError(f"unknown pool mode: {mode}")
    else:
        c = img.shape[-1]
        reshaped = cropped.reshape(oh, kh, ow, kw, c)
        if mode == "max":
            out = reshaped.max(axis=(1, 3))
        elif mode == "mean":
            out = reshaped.mean(axis=(1, 3))
        else:
            raise ValueError(f"unknown pool mode: {mode}")
    if origin is None:
        origin = f"pool({mode},{kh}x{kw})"
    out_nid = image_from_array(s, out, origin=origin)
    _native_substrate(s).add_edge(out_nid, FROM_INPUT, image_nid)
    return out_nid


def threshold(s, image_nid: Any, t: float, mode: str = "binary",
              origin: str | None = None) -> Any:
    """Threshold an image. `mode` is "binary" (above t → 1, else 0)
    or "trunc" (above t → t, else value). Models the output
    nonlinearity at every stage of biological vision (a neuron fires
    above its threshold, not below)."""
    img = image_to_array(s, image_nid).astype(np.float32)
    if mode == "binary":
        out = (img > t).astype(np.float32)
    elif mode == "trunc":
        out = np.minimum(img, t)
    else:
        raise ValueError(f"unknown threshold mode: {mode}")
    if origin is None:
        origin = f"threshold({mode},t={t:.3f})"
    out_nid = image_from_array(s, out, origin=origin)
    _native_substrate(s).add_edge(out_nid, FROM_INPUT, image_nid)
    return out_nid


# --- Pipeline helper ---------------------------------------------------

def apply_pipeline(s, image_nid: Any, kernel_nids: Iterable[Any]) -> list:
    """Chain `convolve` through each kernel in order. Returns the
    list of intermediate Image NodeIDs, in pipeline order. Each is
    wired with `produced_by` + `from_input` edges so the agent can
    introspect the cascade."""
    results = []
    cur = image_nid
    for k in kernel_nids:
        cur = convolve(s, cur, k)
        results.append(cur)
    return results


def v1_responses(s, image_nid: Any, bank: Iterable[Any]) -> list:
    """Apply each kernel in `bank` to `image_nid`; return the list
    of response Image NodeIDs. Models the parallel response of a
    V1 column to a single retinal input."""
    return [convolve(s, image_nid, k) for k in bank]


# --- V2 / V4: hierarchical layers (HMAX-shape) ---------------------------
#
# Riesenhuber & Poggio (1999) "Hierarchical models of object
# recognition in cortex" — alternating S (simple, like V1) and C
# (complex, pooled) layers. The C-cell pools over a small spatial
# neighbourhood of S-cell responses, giving translation tolerance.
# Combining C-cells across orientations gives junction / corner /
# more complex feature detectors (V2-shape).
#
# Each output here is a fresh Image node wired with the same
# `produced_by` / `from_input` provenance edges as a convolution
# output — so the agent can trace V4 → V2 → V1 → retina the same
# way it traces a single conv. The hierarchy IS the graph.


def complex_cell(s, simple_response_nid: Any, kh: int = 4, kw: int = 4,
                 mode: str = "max", origin: str | None = None) -> Any:
    """One HMAX C-cell over an S-cell response. Pools a kh×kw window
    (stride = (kh, kw)) — gives translation tolerance: a stimulus
    that moves by ≤ (kh, kw) pixels produces the same C response.

    `simple_response_nid` is an Image NodeID (typically a V1 response).
    Returns a new (smaller) Image. Same shape as `pool` — exposed
    under the biological name so caller intent is clear.
    """
    if origin is None:
        origin = f"complex_cell({mode},{kh}x{kw})"
    return pool(s, simple_response_nid, kh=kh, kw=kw, mode=mode, origin=origin)


def v2_pool_layer(s, v1_response_nids: Iterable[Any],
                  kh: int = 4, kw: int = 4) -> list:
    """Apply a complex-cell pool to every V1 response in parallel —
    the HMAX C1 layer. Returns the list of pooled Image NodeIDs in
    the same orientation order as the input bank. Each carries the
    `from_input` provenance edge so the agent can trace it back."""
    return [complex_cell(s, r, kh=kh, kw=kw, mode="max",
                         origin=f"v2_pool[{i}]")
            for i, r in enumerate(v1_response_nids)]


def combine_orientations(s, response_nids: list,
                         weights: list[float] | None = None,
                         origin: str = "v2_combination") -> Any:
    """Linear combination of orientation responses — the building
    block for junction / corner detectors. Two orientations with
    equal positive weights at orthogonal angles approximates a
    corner-pop-out cell (peaks where both edges are present, low
    where only one is). Generalises HMAX's S2 stage where multiple
    C1 channels combine into a tuned feature.

    `weights` defaults to uniform 1.0 across all inputs (additive
    combination). For an X-junction detector use [1.0, 1.0] over the
    two orientations; for an edge-vs-anti-edge contrast use [1.0,
    -1.0]. Returns a new Image node.
    """
    if not response_nids:
        raise ValueError("combine_orientations: at least one response required")
    if weights is None:
        weights = [1.0] * len(response_nids)
    if len(weights) != len(response_nids):
        raise ValueError(
            f"weights length {len(weights)} ≠ responses {len(response_nids)}")
    # Read every response, do the linear combo in float space.
    arrays = [image_to_array(s, nid).astype(np.float32) for nid in response_nids]
    shape = arrays[0].shape
    for a in arrays[1:]:
        if a.shape != shape:
            raise ValueError(
                f"all responses must have the same shape; got {a.shape} vs {shape}")
    out = np.zeros(shape, dtype=np.float32)
    for w, a in zip(weights, arrays):
        out += w * a
    out_nid = image_from_array(s, out, origin=origin)
    # Wire provenance to every input — the V2 cell's receptive field
    # spans multiple V1 inputs, and the graph reflects that.
    inner = _native_substrate(s)
    for r in response_nids:
        inner.add_edge(out_nid, FROM_INPUT, r)
    return out_nid


def v2_corner_detector(s, image_nid: Any,
                       theta_a: float = 0.0,
                       theta_b: float = math.pi / 2,
                       sigma: float = 2.0, lambda_: float = 6.0,
                       ksize: int | None = None,
                       pool_kh: int = 3, pool_kw: int = 3) -> Any:
    """A V2-shaped corner detector — V1 simple cells at two
    orientations → C1 pool → linear combination. Responds strongly
    at locations where BOTH oriented edges are present (a corner /
    junction), weakly to either edge alone.

    Default θ_a=0, θ_b=π/2 builds an axis-aligned corner cell. Pass
    e.g. θ_a=π/4, θ_b=3π/4 for a 45°-diagonal X-junction detector.

    Returns the final pooled+combined Image NodeID. Every
    intermediate (the two convolutions, the two pools) is also a
    Image node in the graph — provenance traced via `produced_by` /
    `from_input` as usual.
    """
    k_a = gabor(s, sigma=sigma, theta=theta_a, lambda_=lambda_, ksize=ksize)
    k_b = gabor(s, sigma=sigma, theta=theta_b, lambda_=lambda_, ksize=ksize)
    # Take the ABSOLUTE response (cells fire on edge magnitude, not
    # signed phase) — needed so both bars of a +/- contrast corner
    # contribute positively.
    resp_a_signed = convolve(s, image_nid, k_a)
    resp_b_signed = convolve(s, image_nid, k_b)
    resp_a = image_from_array(s, np.abs(image_to_array(s, resp_a_signed)),
                              origin=f"abs(conv:θ={theta_a:.2f})")
    resp_b = image_from_array(s, np.abs(image_to_array(s, resp_b_signed)),
                              origin=f"abs(conv:θ={theta_b:.2f})")
    # C1 pool — translation tolerance per orientation.
    pool_a = complex_cell(s, resp_a, kh=pool_kh, kw=pool_kw,
                          origin=f"v2_pool(θ={theta_a:.2f})")
    pool_b = complex_cell(s, resp_b, kh=pool_kh, kw=pool_kw,
                          origin=f"v2_pool(θ={theta_b:.2f})")
    # Combine: both edges must fire for a strong corner response.
    return combine_orientations(
        s, [pool_a, pool_b], weights=[1.0, 1.0],
        origin=f"v2_corner(θ={theta_a:.2f},{theta_b:.2f})")


def v4_pool_layer(s, v2_response_nids: Iterable[Any],
                  kh: int = 2, kw: int = 2) -> list:
    """V4-shape: another pooling stage on top of V2. The HMAX C2
    layer. Same op as `v2_pool_layer` with a smaller default window
    (V4 cells have larger receptive fields but operate on already-
    pooled V2 input — kh=kw=2 is a typical scaling)."""
    return [complex_cell(s, r, kh=kh, kw=kw, mode="max",
                         origin=f"v4_pool[{i}]")
            for i, r in enumerate(v2_response_nids)]


# --- Kernel learning: Hebbian + Oja's rule ------------------------------
#
# The agent rewrites its OWN receptive fields based on experience —
# the biological story:
#
#   "Cells that fire together, wire together" — Hebb (1949)
#
# A kernel's weight at position (i,j) grows when the input intensity
# at the corresponding location coincides with a strong kernel
# response. The kernel adapts toward the patches the agent has been
# convolving it against — biological feature learning.
#
# Plain Hebbian has runaway feedback (strong responses → bigger
# weights → even stronger responses). Oja's rule (1982) adds a
# decay term that drives the weight vector to unit norm — provably
# extracts the first principal component of the input distribution.
#
# Implementation: pure Python. The kernel weights are mutated in
# place on the substrate via set_attr; the agent calls
# `refresh_kernels()` on its GraphEye to push the new weights into
# the worker cache. (We don't auto-refresh — that's a master-thread
# concern.)


def _extract_patches(image: np.ndarray, kh: int, kw: int,
                     stride: int = 1) -> np.ndarray:
    """Extract every kh×kw patch from `image` (stride=1 by default).
    Returns shape (n_patches, kh, kw). Used by the learning rules
    so the kernel sees the same patches the convolution did."""
    if image.ndim != 2:
        raise ValueError(f"_extract_patches: 2-D image only, got {image.shape}")
    h, w = image.shape
    n_h = (h - kh) // stride + 1
    n_w = (w - kw) // stride + 1
    if n_h <= 0 or n_w <= 0:
        raise ValueError(
            f"image {image.shape} too small for kernel {kh}x{kw}")
    patches = np.zeros((n_h * n_w, kh, kw), dtype=image.dtype)
    for r in range(n_h):
        for c in range(n_w):
            patches[r * n_w + c] = image[r * stride:r * stride + kh,
                                         c * stride:c * stride + kw]
    return patches


def hebbian_update(s, kernel_nid: Any, image_nid: Any,
                   response_nid: Any | None = None,
                   lr: float = 0.001, decay: float = 0.0) -> Any:
    """Plain Hebbian update: w ← w + lr * mean_i(patch_i * response_i)
    where patch_i is the i-th kh×kw window of the input and
    response_i is the corresponding entry in the convolution output.

    `response_nid` is optional — if omitted we compute it on the fly
    via `convolve(s, image_nid, kernel_nid)`. Providing it skips a
    convolution (useful when the response is already cached).

    `decay` is the optional weight decay (`w ← w * (1 - decay)`
    before the update) — biologically realistic; prevents weights
    from growing unboundedly without the full Oja normalisation.

    Returns the kernel_nid (mutated in place). The agent must call
    its `GraphEye.refresh_kernels()` to push the new weights into
    the worker cache before the next frame uses them.
    """
    img = image_to_array(s, image_nid).astype(np.float32)
    if img.ndim != 2:
        # Multi-channel: learn over the luminance channel for
        # simplicity. A future revision could learn per-channel
        # kernels.
        img = img.mean(axis=-1)
    if response_nid is None:
        response_nid = convolve(s, image_nid, kernel_nid)
    resp = image_to_array(s, response_nid).astype(np.float32)
    if resp.ndim != 2:
        resp = resp.mean(axis=-1)

    weights = kernel_to_array(s, kernel_nid).astype(np.float32)
    kh, kw = weights.shape
    patches = _extract_patches(img, kh, kw)
    # Crop the response to match the patch grid layout — 'valid' shape.
    rh, rw = resp.shape
    # The conv was 'same' so resp.shape == img.shape; we need the
    # central (img.h - kh + 1, img.w - kw + 1) portion to align with
    # the patches we extracted.
    h, w = img.shape
    ph, pw = kh // 2, kw // 2
    resp_valid = resp[ph:ph + (h - kh + 1), pw:pw + (w - kw + 1)]
    flat_resp = resp_valid.reshape(-1).astype(np.float32)
    # Hebbian product: average response-weighted patch.
    update = (patches.astype(np.float32) * flat_resp[:, None, None]).mean(axis=0)
    new_weights = weights * (1.0 - decay) + lr * update
    # Push back to the substrate — the weights attr is the source of truth.
    _native_substrate(s).set_attr(
        kernel_nid, "weights", new_weights.astype(np.float32).flatten().tolist())
    return kernel_nid


def oja_update(s, kernel_nid: Any, image_nid: Any,
               response_nid: Any | None = None,
               lr: float = 0.001) -> Any:
    """Oja's rule (1982): a self-normalising Hebbian variant.

        w ← w + lr * (y * x - y² * w)

    The y² * w term prevents the weights from growing unboundedly
    AND drives the weight vector to unit norm. Provably extracts
    the first principal component of the input distribution — i.e.
    after enough updates, the kernel becomes the dominant edge /
    pattern in the inputs it's been shown.

    Same API as `hebbian_update`. Use this when you want
    self-normalisation without manual weight decay tuning.
    """
    img = image_to_array(s, image_nid).astype(np.float32)
    if img.ndim != 2:
        img = img.mean(axis=-1)
    if response_nid is None:
        response_nid = convolve(s, image_nid, kernel_nid)
    resp = image_to_array(s, response_nid).astype(np.float32)
    if resp.ndim != 2:
        resp = resp.mean(axis=-1)

    weights = kernel_to_array(s, kernel_nid).astype(np.float32)
    kh, kw = weights.shape
    h, w = img.shape
    ph, pw = kh // 2, kw // 2
    patches = _extract_patches(img, kh, kw)
    resp_valid = resp[ph:ph + (h - kh + 1), pw:pw + (w - kw + 1)]
    flat_resp = resp_valid.reshape(-1).astype(np.float32)
    # Oja: per-patch w ← w + lr * (y*x - y² * w); average over patches.
    y2 = (flat_resp ** 2).mean()
    hebb = (patches.astype(np.float32) * flat_resp[:, None, None]).mean(axis=0)
    new_weights = weights + lr * (hebb - y2 * weights)
    _native_substrate(s).set_attr(
        kernel_nid, "weights", new_weights.astype(np.float32).flatten().tolist())
    return kernel_nid


def kernel_norm(s, kernel_nid: Any) -> float:
    """L2 norm of a kernel's weights — useful when running Oja to
    confirm convergence to unit norm."""
    w = kernel_to_array(s, kernel_nid)
    return float(np.linalg.norm(w))


__all__ = [
    "IMAGE", "KERNEL", "PIPELINE",
    "PRODUCED_BY", "FROM_INPUT", "HAS_KERNEL", "HAS_INPUT", "PRODUCES",
    "seed_vision_grammar",
    "image_from_array", "image_to_array", "image_shape",
    "kernel_from_matrix", "kernel_to_array", "kernel_describe", "kernel_to_image",
    "gabor", "gaussian", "dog", "sobel", "laplacian", "identity",
    "v1_bank", "lgn_pair",
    "convolve", "pool", "threshold",
    "apply_pipeline", "v1_responses",
    # V2 / V4 hierarchical layers (HMAX-shape)
    "complex_cell", "v2_pool_layer", "combine_orientations",
    "v2_corner_detector", "v4_pool_layer",
    # Kernel learning (Hebbian / Oja's rule)
    "hebbian_update", "oja_update", "kernel_norm",
]
