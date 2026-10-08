#!/usr/bin/env python3
"""GEN-MINT — the confirmatory measurement (`VISION_GENMINT_PREREG.md`).

Every arm is deterministic EXCEPT the floor gate, whose 400 random colourings
draw from seeds 25000-25399 (declared). Run from the gamma-substrate dir:

    PYTHONPATH=runners/dsl/python:. python scripts/genmint_measure.py
"""
from __future__ import annotations
import hashlib, json, os, random, sys, time
from pathlib import Path

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

from substrate.boot_core import boot_core          # noqa: E402
from domains import reflective_faculty as rf        # noqa: E402
from substrate_rs import _native                   # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

DT = ["pred", "coord:r", "coord:c", "val"]
# asymmetric L-tetromino: its shear/unimodular images land on distinct cell
# sets no held rotation/reflection/scale/cycle image or rung-1 delta reaches,
# and its only setwise linear self-map is the (excluded) identity.
BASE = [["cell", 0, 0, "red"], ["cell", 1, 0, "red"],
        ["cell", 2, 0, "red"], ["cell", 2, 1, "red"]]


def lin(M, base, val=None):
    rs = [c[1] for c in base]; cs = [c[2] for c in base]
    mr, mc = min(rs), min(cs); out = []
    for _, r, c, v in base:
        r0, c0 = r - mr, c - mc
        out.append(["cell", M[0] * r0 + M[1] * c0, M[2] * r0 + M[3] * c0, val or v])
    return out


def boot(enabled):
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    if enabled:
        s.set_attr(ag, "gen_infer_enabled", 1.0)
    s.add_node("ShapeSignature", {"name": "base_L", "signature": json.dumps(BASE),
               "kind": "faculty", "faculty": "base_L", "dim_types": DT})
    return s, ag, native


def observe(s, ag, goal):
    ep = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
    obs = s.add_node("Observation", {"signature": goal, "key": ["probe"],
                     "status": "decoded", "residual": goal, "decoded_epoch": ep,
                     "dim_types": DT})
    s.add_edge(ag, "observed", obs)
    return obs


def lingens(s):
    return [tuple(s.node(n)["attrs"].get("matrix"))
            for n in s.nodes("DimensionGenerator")
            if s.node(n)["attrs"].get("kind") == "linear"]


def run_one(enabled, goal):
    s, ag, native = boot(enabled)
    ax0 = len(list(s.nodes("CapabilityAxis")))
    obs = observe(s, ag, goal)
    native.run_rules()
    at = s.node(obs)["attrs"]
    return dict(status=at.get("status"), quanta=len(list(s.nodes("CapabilityAxis"))) - ax0,
                lingens=lingens(s))


def main():
    started = time.perf_counter()
    native_path = Path(_native.__file__).resolve()
    R = {"engine": provenance_line(),
         "provenance": {
             "source_sha256": {
                 rel: sha256(ROOT / rel) for rel in (
                     "scripts/genmint_measure.py", "seeds/shape_decode_loop.json",
                     "domains/reflective_faculty.py", "domains/engine_provenance.py",
                     "runners/dsl/src/shape_decode.rs", "runners/dsl/src/term.rs",
                     "runners/dsl/python/substrate_rs/_native.build.json")},
             "native_extension_path": str(native_path),
             "native_extension_sha256": sha256(native_path),
         }}
    ok = {}
    print("ENGINE:", R["engine"])

    # --- H_discovery: multi-held-out, FROZEN machinery, different-per-orbit ---
    print("\n[H_discovery] multi-held-out — frozen machinery, correct DIFFERENT generator per orbit")
    targets = {"shearA": [1, 0, 1, 1], "shearB": [1, 1, 0, 1], "unimodular_det1": [2, 1, 1, 1]}
    disc = {}
    for name, M in targets.items():
        r = run_one(True, lin(M, BASE))
        correct = (r["status"] == "recognized_transformed" and r["quanta"] == 0
                   and r["lingens"] == [tuple(M)])
        disc[name] = {"target": M, **r, "correct": correct}
        print(f"  {name:16} -> status={r['status']:22} quanta={r['quanta']} minted={r['lingens']} CORRECT={correct}")
    ok["H_discovery"] = all(d["correct"] for d in disc.values()) and \
        len({tuple(d["lingens"][0]) for d in disc.values() if d["lingens"]}) == 3
    R["H_discovery"] = disc
    print(f"  => 3/3 correct AND all different: {ok['H_discovery']}")

    # --- H_compression (the MDL headline): a minted generator must PAY ---
    # ONE MDL principle — mint whatever compresses most. Present a K-member
    # ordered orbit {M(base)..M^K(base)}: WITHOUT gen-infer each member grounds
    # at enumeration (K quanta); WITH it, member 1 mints ONE generator that
    # grounds the whole orbit (0 quanta). Description length (predicate tokens):
    # a quantum stores its ~cells residual predicates; a generator stores its
    # n*n matrix + n coord_dims ONCE, plus one k-index per recognized member.
    print("\n[H_compression] MDL — a minted generator must COMPRESS (MDL_with < MDL_without)")
    M = [1, 0, 1, 1]
    K = 6
    members = []
    cur = BASE
    for _ in range(K):
        cur = lin(M, cur)
        members.append(cur)
    ncell = len(BASE)
    # WITHOUT: present all K members, gen-infer OFF -> K quanta.
    s, ag, native = boot(False)
    ax0 = len(list(s.nodes("CapabilityAxis")))
    for g in members:
        observe(s, ag, g)
    native.run_rules()
    quanta_without = len(list(s.nodes("CapabilityAxis"))) - ax0
    # WITH: present in ORBIT ORDER; member 1 mints the unit generator, the rest
    # are recognized as its powers.
    s, ag, native = boot(True)
    ax0 = len(list(s.nodes("CapabilityAxis")))
    recognized = 0
    for g in members:
        obs = observe(s, ag, g)
        native.run_rules()
        if s.node(obs)["attrs"].get("status") == "recognized_transformed":
            recognized += 1
    quanta_with = len(list(s.nodes("CapabilityAxis"))) - ax0
    gens_with = lingens(s)
    mdl_without = quanta_without * ncell
    mdl_with = (len(gens_with) * (4 + 2)) + recognized  # matrix+coord_dims once + one k-index/member
    ratio = mdl_without / mdl_with if mdl_with else float("inf")
    ok["H_compression"] = (len(gens_with) == 1 and quanta_with == 0 and mdl_with < mdl_without)
    R["H_compression"] = {"K": K, "quanta_without": quanta_without, "quanta_with": quanta_with,
                          "generators": [list(x) for x in gens_with], "recognized": recognized,
                          "mdl_without": mdl_without, "mdl_with": mdl_with, "ratio": round(ratio, 3)}
    print(f"  => WITHOUT: {quanta_without} quanta  WITH: {len(gens_with)} generator + {quanta_with} quanta "
          f"({recognized}/{K} recognized)")
    print(f"     MDL_without={mdl_without}  MDL_with={mdl_with}  ratio={ratio:.2f}x  PAYS={ok['H_compression']}")

    # --- H_floor: the honest MDL floor (NOT a "noise" category) ---
    # "Noise doesn't exist — only signals you haven't grounded." A signal with
    # no coherent value-substitution grounds at ENUMERATION (one quantum each);
    # the honest report is "no generator shorter than enumeration FOUND (at
    # these seeds, this window)" — provisional, never "incompressible". The gate
    # relocated: no minted generator may FAIL to compress. Here: 0 generators
    # minted => 0 non-paying generators hallucinated.
    print("\n[H_floor] MDL floor — an ungrounded signal grounds at enumeration; n=400 (seeds 25000-25399)")
    print("          gate: NO minted generator fails to compress (0 non-paying mints)")
    palette = ["blue", "green", "yellow", "purple", "orange", "cyan", "magenta",
               "black", "white", "brown", "pink", "gray", "teal", "navy", "lime"]
    minted = 0; examples = []
    for i in range(400):
        random.seed(25000 + i)
        # base's OWN coords, each cell a DISTINCT random colour -> no coherent
        # value-substitution and only the excluded identity fixes the coords,
        # so no linear map can explain it, at ANY window.
        cols = random.sample(palette, 4)
        goal = [["cell", c[1], c[2], cols[j]] for j, c in enumerate(BASE)]
        r = run_one(True, goal)
        if r["lingens"]:
            minted += 1
            if len(examples) < 3:
                examples.append((25000 + i, r["lingens"]))
    ok["H_floor"] = (minted == 0)
    R["H_floor"] = {"n": 400, "non_paying_generators_minted": minted, "examples": examples,
                    "report": "grounded at enumeration; no generator shorter than enumeration "
                              "found at seeds 25000-25399 (provisional, not incompressible)"}
    print(f"  => generators minted over 400 ungrounded presentations: {minted}  (gate: 0)  PASS={ok['H_floor']}")

    # --- H_occam: a HELD transform is SELECTED upstream, no spurious mint ---
    print("\n[H_occam] held rotation90 orbit — SELECTED upstream, no linear generator")
    ROT = [["cell", 0, 2, "red"], ["cell", 0, 1, "red"], ["cell", 0, 0, "red"], ["cell", 1, 0, "red"]]
    r = run_one(True, ROT)
    ok["H_occam"] = (r["status"] == "recognized_transformed" and r["lingens"] == [] and r["quanta"] == 0)
    R["H_occam"] = r
    print(f"  => status={r['status']} lingens={r['lingens']} quanta={r['quanta']} PASS={ok['H_occam']}")

    # --- H_downstream (§1 clause 5): the mint moves a LATER decode ---
    # ON: present member1 (mints the generator) then a NEW member M^2(base);
    # the new member is recognized THROUGH the minted generator. Compare to OFF
    # (no mint) where the same new member is a quantum. max|on-off| must be >0.
    print("\n[H_downstream] §1 clause5 — generator minted from member1 recognizes a NEW member M^2(base)")
    M = [1, 0, 1, 1]
    m2 = lin(M, lin(M, BASE))          # M^2(base): a DIFFERENT member, unused for minting
    # ON: same graph, mint from member1 then decode m2.
    s, ag, native = boot(True)
    observe(s, ag, lin(M, BASE)); native.run_rules()      # member1 -> mints generator
    obs2 = observe(s, ag, m2); native.run_rules()         # the NEW member
    on = s.node(obs2)["attrs"].get("status")
    on_gens = lingens(s)
    # OFF: m2 alone, no gen-infer -> quantum
    off = run_one(False, m2)
    ok["H_downstream"] = (on == "recognized_transformed" and off["status"] == "minted")
    R["H_downstream"] = {"new_member_status_ON": on, "new_member_status_OFF": off["status"],
                         "generators_present": on_gens}
    print(f"  => NEW member ON={on} (via minted gen {on_gens}) vs OFF={off['status']}  moves-downstream={ok['H_downstream']}")

    # --- H_nonlinear: the transform outside the seeded generality — grounds at
    #     enumeration, PROVISIONALLY (a nonlinear seed might compress it; door open) ---
    print("\n[H_nonlinear] NON-linear warp (c -> c + r^2) — outside the linear seed, grounds at enumeration (provisional)")
    quad = []
    rs = [c[1] for c in BASE]; cs = [c[2] for c in BASE]; mr, mc = min(rs), min(cs)
    for _, r0, c0, v in BASE:
        rr, cc = r0 - mr, c0 - mc
        quad.append(["cell", rr, cc + rr * rr, v])
    r = run_one(True, quad)
    ok["H_nonlinear"] = (r["lingens"] == [] and r["status"] == "minted")
    R["H_nonlinear"] = r
    print(f"  => status={r['status']} lingens={r['lingens']} correctly-refused={ok['H_nonlinear']}")

    # --- seed-minimality / starvation threshold ---
    print("\n[seed] size = 4 integer parameters (a 2x2 matrix); NOT a universal container")
    print("  - named-codebook seed (5 atoms): shear NOT discoverable (pilot: quantum) -> discovery OFF below the linear family")
    print("  - 4-param linear seed: shearA/shearB/unimodular ALL discoverable -> discovery ON")
    print("  - the linear seed CANNOT express a HELD generator (modular/cycle4 wrap is nonlinear) nor the quadratic warp -> not universal")

    R["verdict"] = ok
    overturn = all(ok.values())
    R["overturn_bounded_to_linear_class"] = overturn
    print("\n" + "=" * 68)
    for k, v in ok.items():
        print(f"  {k:14} {'PASS' if v else 'FAIL'}")
    print(f"  OVERTURN (bounded to integer-linear class): {overturn}")
    print("=" * 68)

    R["runtime_seconds"] = round(time.perf_counter() - started, 6)
    output = Path(os.environ.get("GENMINT_OUTPUT", "results/genmint_measure.json"))
    if not output.is_absolute():
        output = Path.cwd() / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(R, indent=1, default=str) + "\n")
    print(f"wrote {output}")
    return 0 if overturn else 1


if __name__ == "__main__":
    sys.exit(main())
