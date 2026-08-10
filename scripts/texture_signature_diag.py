"""Diagnostic: capture each door from further back (pose-distance controlled), dump the RAW
mean RGB of the central (door) band vs the peripheral (wall) band, the old-tex / colour /
pattern levels, and save PNGs. Answers: do the FAINT doors differ from their wall in colour
or arrangement in a single frame, when the door is a central blob surrounded by wall?"""
from __future__ import annotations
import json, math, os
import numpy as np
from PIL import Image
import scripts.texture_signature_measure as M

GH, GW = 240, 320
OUT = os.path.join(M.ROOT, "results", "pattern_eye", "diag")


def _dist(p, c):
    return math.hypot(p[0] - c[0], p[1] - c[1])


def capture(door, back=260):
    g, gv = M._game()
    dx, dy = door["center"]
    ux, uy = door["approach"]
    n = math.hypot(ux, uy)
    ax, ay = dx + ux / n * back, dy + uy / n * back        # start further back along the openable face normal
    g.send_game_command("warp %d %d" % (ax, ay)); g.make_action([0, 0, 0, 0], 1)
    px, py, _ = M._pose(g, gv)
    if _dist((px, py), (ax, ay)) > 80:
        g.close(); return []
    want = math.degrees(math.atan2(dy - py, dx - px)) % 360
    for _ in range(50):
        _, _, ang = M._pose(g, gv)
        err = (want - ang + 180) % 360 - 180
        if abs(err) < 5:
            break
        g.make_action([0, 1, 0, 0] if err > 0 else [0, 0, 1, 0], 2)
    rows = []
    saved = []
    for k in range(26):
        if g.is_episode_finished():
            break
        rgb, db = M._grab(g)
        px, py, _ = M._pose(g, gv)
        dist = _dist((px, py), (dx, dy))
        a = rgb.astype(np.int32)[M.CBAND[0]:M.CBAND[1]]
        cen = slice(GW * 3 // 8, GW * 5 // 8)
        edge = np.r_[0:GW * 3 // 8, GW * 5 // 8:GW]
        cen_rgb = [int(a[..., ch][:, cen].mean()) for ch in range(3)]
        edge_rgb = [int(a[..., ch][:, edge].mean()) for ch in range(3)]
        row = {"sector": door["sector"], "class": door["class"], "k": k, "dist": round(dist, 1),
               "cen_rgb": cen_rgb, "edge_rgb": edge_rgb,
               "old_tex": M._central(M.old_tex_level(rgb)), "colour": M._central(M.colour_level(rgb)),
               "hfrac": M._central(M._score_frame(rgb, db, 0, "x", 0)["hfrac"] * 0 + M.pattern_signature(rgb)[0])}
        rows.append(row)
        if 90 <= dist <= 200 and k % 3 == 0:
            os.makedirs(OUT, exist_ok=True)
            p = os.path.join(OUT, "door%d_d%d.png" % (door["sector"], int(dist)))
            Image.fromarray(rgb.astype(np.uint8), "RGB").save(p); saved.append(os.path.basename(p))
        g.make_action([1, 0, 0, 0], 3)
    g.close()
    return rows, saved


def main():
    allrows = {}
    for d in M.DOORS:
        r, saved = capture(d)
        allrows[str(d["sector"])] = r
        print("=== sec %d (%s) saved=%s ===" % (d["sector"], d["class"], saved))
        for x in r:
            if 80 <= x["dist"] <= 210:
                dc = [x["cen_rgb"][i] - x["edge_rgb"][i] for i in range(3)]
                print("  d=%6.1f cen_rgb=%s edge_rgb=%s  cen-edge=%s  old_tex=%d colour=%d"
                      % (x["dist"], x["cen_rgb"], x["edge_rgb"], dc, x["old_tex"], x["colour"]))
    os.makedirs(OUT, exist_ok=True)
    json.dump(allrows, open(os.path.join(OUT, "diag.json"), "w"), indent=2)


if __name__ == "__main__":
    try:
        import vizdoom  # noqa
        if not os.path.exists(M.WAD):
            raise RuntimeError("WAD absent")
    except Exception as e:
        print("SKIP:", e); raise SystemExit(0)
    main()
