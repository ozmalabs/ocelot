"""Vision demo: build a graph-resident V1 cortex and watch it work.

Biology-faithful design: every receptive field is a Kernel NODE in
the substrate's graph. The agent OWNS its visual primitives — readable,
editable, composable, introspectable — instead of them being opaque
cv2 calls.

What this demonstrates:
1. An LGN center-surround pair (2 DoG kernels).
2. A V1 column at 8 orientations (8 Gabor kernels).
3. A test image with both a vertical edge and a horizontal edge.
4. Convolving the image through every kernel — every percept is a
   new Image NODE wired with `produced_by` + `from_input` edges.
5. The agent (using the same DSL it uses for everything else)
   introspects: how many kernels do I have? what does each prefer?
   which kernel responded strongest to this image?

Run: PYTHONPATH=. python3 benchmarks/vision_demo.py
"""
from __future__ import annotations

import math

import numpy as np
import substrate_rs as srs
from substrate_rs import vision as v


def build_visual_cortex():
    """Build the cortex: substrate, grammar, LGN pair, V1 bank.
    Returns (substrate, lgn_pair_NodeIDs, v1_bank_NodeIDs)."""
    s = srs.Substrate()
    v.seed_vision_grammar(s)
    lgn = v.lgn_pair(s, sigma_on=1.0, sigma_off=2.0)
    v1 = v.v1_bank(s, n_orientations=8, sigma=2.5, lambda_=6.0, ksize=11)
    return s, lgn, v1


def test_image() -> np.ndarray:
    """Synthetic 'cross' — vertical stroke + horizontal stroke. Either
    real shape should provoke a strong response from one V1 column
    and weak response from its orthogonal sibling."""
    img = np.zeros((40, 40), dtype=np.uint8)
    img[:, 18:22] = 255         # vertical stroke
    img[18:22, :] = 255         # horizontal stroke
    return img


def main():
    print("Building visual cortex…")
    s, (on_center, off_center), v1 = build_visual_cortex()
    print(f"  LGN: {len(s.nodes(v.KERNEL))} kernel nodes total")
    print(f"       (2 from lgn_pair + 8 from v1_bank)")

    # Feed it a test image.
    img = test_image()
    img_nid = v.image_from_array(s, img, origin="demo:cross_pattern")
    print(f"\nInput image: {img.shape}, {img.sum()} alive pixels")

    # --- LGN stage: ON-center and OFF-center responses --------------
    on_resp = v.convolve(s, img_nid, on_center)
    off_resp = v.convolve(s, img_nid, off_center)
    print(f"\nLGN responses:")
    print(f"  ON-center  mean |response|: {np.abs(v.image_to_array(s, on_resp)).mean():.2f}")
    print(f"  OFF-center mean |response|: {np.abs(v.image_to_array(s, off_resp)).mean():.2f}")

    # --- V1 stage: orientation column responses --------------------
    print(f"\nV1 column responses (by orientation):")
    print(f"  {'θ (deg)':>8s}  {'kernel name':>40s}  {'mean |resp|':>12s}")
    print("  " + "─" * 65)
    responses = v.v1_responses(s, on_resp, v1)
    strengths = []
    for kid, rid in zip(v1, responses):
        name = s.node(kid)["attrs"]["name"]
        theta_str = name.split("θ=")[1].split(",")[0]
        theta_deg = math.degrees(float(theta_str))
        strength = float(np.abs(v.image_to_array(s, rid)).mean())
        strengths.append((theta_deg, name, strength, kid, rid))
        print(f"  {theta_deg:8.1f}  {name:>40s}  {strength:12.2f}")

    # The two strongest should be the cardinal orientations (0° and 90°)
    # since the input has both vertical AND horizontal strokes.
    strengths.sort(key=lambda x: -x[2])
    top_two = sorted([round(s[0]) for s in strengths[:2]])
    print(f"\nStrongest V1 responses at orientations: {top_two}°")
    print("  (Expected ~0° and ~90° — the cross has vertical + horizontal strokes.)")

    # --- The biology story: agent introspects its own cortex ------
    print(f"\n--- Agent introspection (graph-resident, via the DSL) ---")
    n_kernels = len(s.nodes(v.KERNEL))
    n_images = len(s.nodes(v.IMAGE))
    print(f"  Kernels in cortex: {n_kernels}")
    print(f"  Images in graph:   {n_images} (= 1 input + 2 LGN + 8 V1 responses)")

    # The agent traces a percept back to its origin via produced_by /
    # from_input edges — no Python introspection needed.
    print(f"\nProvenance trace for the strongest V1 response:")
    strongest = strengths[0]
    _, _, _, strongest_kid, strongest_rid = strongest
    cur = strongest_rid
    depth = 0
    while True:
        node = s.node(cur)
        attrs = node["attrs"]
        prefix = "  " * (depth + 1)
        print(f"{prefix}↑ Image #{cur.value} — origin: '{attrs.get('origin', '?')}'")
        # produced_by → kernel
        for k in s.neighbours(cur, v.PRODUCED_BY):
            kname = s.node(k)["attrs"]["name"]
            print(f"{prefix}    via kernel: {kname}")
        # from_input → upstream image
        inputs = s.neighbours(cur, v.FROM_INPUT)
        if not inputs:
            break
        cur = inputs[0]
        depth += 1
        if depth > 8:
            print(f"{prefix}    …(truncated)")
            break

    # --- Editing receptive fields: the agent rewrites its own cortex ---
    print(f"\n--- Editing receptive fields ---")
    print(f"The agent inspects a Gabor kernel and could author a new one")
    print(f"at a non-standard orientation. Kernel data is just attrs:")
    sample = v1[0]
    desc = v.kernel_describe(s, sample)
    print(f"  Sample kernel: {desc['name']}")
    print(f"  Shape: {desc['shape']}  mean: {desc['mean']:+.3f}  "
          f"std: {desc['std']:.3f}  range: [{desc['min']:+.3f}, {desc['max']:+.3f}]")

    # Author a new "diagonal" Gabor — biology equivalent of forming
    # a new orientation column.
    new_kid = v.gabor(s, sigma=2.5, theta=math.pi / 6, lambda_=6.0, ksize=11)
    print(f"\nAuthored a new Gabor at θ=30°:  "
          f"{s.node(new_kid)['attrs']['name']}")
    print(f"Total kernels now: {len(s.nodes(v.KERNEL))}")


if __name__ == "__main__":
    main()
