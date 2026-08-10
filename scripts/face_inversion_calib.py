"""CALIBRATION (PROTOCOL §1) for FACE-INVERSION / THATCHER — NOT confirmatory.
Deterministic constructions; understands the instrument before pre-registration.
"""
from __future__ import annotations
import json
import scripts.face_inversion_lib as L
from substrate.boot_core import boot_core
from domains import reflective_faculty as rf


def identify_full(codebook, view_cells, gen_infer=False):
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    for n in list(s.nodes("ShapeSignature")):
        s.remove_node(n)
    if gen_infer:
        s.set_attr(ag, "gen_infer_enabled", 1.0)
    for nm, cells in codebook.items():
        s.add_node("ShapeSignature", {"name": nm, "signature": json.dumps(L.sig(cells)),
                   "kind": "faculty", "faculty": nm, "dim_types": L.DT})
    goal = L.sig(view_cells)
    ep = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
    obs = s.add_node("Observation", {"signature": goal, "key": ["probe"],
                     "status": "decoded", "residual": goal, "decoded_epoch": ep,
                     "dim_types": L.DT})
    s.add_edge(ag, "observed", obs)
    native.run_rules()
    at = s.node(obs)["attrs"]
    st = at.get("status")
    tr = None
    for t in s.nodes("Transform"):
        # transform linked to this obs via has_transform
        pass
    return st, at.get("covered_by"), at.get("residual")


# Several distinct configural faces (different anchor arrangements, same atom).
FACES = {
    "A": [(0, 0), (0, 6), (7, 3)],
    "B": [(0, 0), (0, 8), (5, 4)],
    "C": [(0, 2), (0, 7), (8, 0)],
    "D": [(1, 0), (0, 5), (6, 6)],
}
CFG = {k: L.configural(v, atom=L.ATOM_L) for k, v in FACES.items()}
ATOMS3 = [L.ATOM_L, L.ATOM_J, L.ATOM_S]  # three ASYMMETRIC atoms (all break under 180)


def main():
    print("=== (a) literal vs transformed for an EXACT upright match ===")
    for k in ("A", "B"):
        st, cov, res = identify_full({k: CFG[k]}, CFG[k])
        print(f"  {k}: status={st} covered_by={cov} residual_len={len(res) if isinstance(res,list) else res}")

    print("=== (b) uniform inversion across faces (invariance rate) ===")
    inv_ok = 0
    for k in CFG:
        st, cov = L.identify(CFG, L.rot180(CFG[k]))
        print(f"  invert({k}) -> status={st} covered_by={cov}")
        inv_ok += (cov == k)
    print(f"  invariance: {inv_ok}/{len(CFG)} inverted faces recognized as OWN identity")

    print("=== (c) THATCHER upright vs inverted across faces (flip each part) ===")
    for k, anch in FACES.items():
        for fi in range(3):
            up = L.configural(anch, atom=L.ATOM_L, flip_idx=fi)
            inv = L.rot180(up)
            _, cu = L.identify({k: CFG[k]}, up)
            _, ci = L.identify({k: CFG[k]}, inv)
            print(f"  {k} flip part{fi}: upright covered_by={cu}  inverted covered_by={ci}")

    print("=== (d) PART-BASED thatcher with ASYMMETRIC flipped part (representation-blind?) ===")
    obj = L.part_based(ATOMS3, FACES["A"])
    for fi in range(3):
        up = L.part_based(ATOMS3, FACES["A"], flip_idx=fi)
        inv = L.rot180(up)
        _, cu = L.identify({"OBJ": obj}, up)
        _, ci = L.identify({"OBJ": obj}, inv)
        print(f"  OBJ flip part{fi}: upright covered_by={cu}  inverted covered_by={ci}")

    print("=== (e) inversion-related discrimination collapse ===")
    for k in ("A", "B"):
        cb = {k: CFG[k], k + "_inv": L.rot180(CFG[k])}
        _, c1 = L.identify(cb, CFG[k])
        _, c2 = L.identify(cb, L.rot180(CFG[k]))
        collapse = (c1 == c2)
        print(f"  {k}: present-upright->{c1}  present-inverted->{c2}  COLLAPSED={collapse}")

    print("=== (f) PART-BASED distinct objects discriminable under inversion? ===")
    objs = {"P": L.part_based([L.ATOM_L, L.ATOM_J, L.ATOM_S], FACES["A"]),
            "Q": L.part_based([L.ATOM_J, L.ATOM_S, L.ATOM_L], FACES["A"])}
    for k in objs:
        _, cu = L.identify(objs, objs[k])
        _, ci = L.identify(objs, L.rot180(objs[k]))
        print(f"  {k}: upright->{cu}  inverted->{ci}")


if __name__ == "__main__":
    main()
