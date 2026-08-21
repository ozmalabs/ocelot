"""Parser for results/eye_confirm.log — the eye's confirmatory block.

The log is the committed artefact (prereg VISION_EYE_PREREG.md, committed
BEFORE the run; seeds 11000-11999, n=12). These figures READ it. Nothing here
recomputes a statistic: means, CI95s and percentages are taken as recorded.
"""
from __future__ import annotations

import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LOG = os.path.join(ROOT, "results", "eye_confirm.log")

_SEED = re.compile(
    r"^\s+(LOG|LINEAR) seed (\d+): k=1000\s+patdiff=([\d.]+) k=10000\s+"
    r"patdiff=([\d.]+)\s+floor=([\d.]+)")
_SUM = re.compile(
    r"^\s+--- (LOG|LINEAR): patdiff\(k=(\d+)\) mean=([\d.]+) sd=([\d.]+) "
    r"CI95=\[([\d.]+), ([\d.]+)\] = ([\d.]+)% of floor")
_FLOOR = re.compile(
    r"^\s+--- (LOG|LINEAR): FLOOR mean=([\d.]+) sd=([\d.]+) -> SESOI=([\d.]+)")
_SLOPE = re.compile(r"^\s+(LOG|LINEAR):\s+drive vs ln\(I\) slope = ([\d.]+)")
_DRIVES = re.compile(r"drives=\[([^\]]+)\]")
_STEP = re.compile(r"per-decade step = \[([^\]]+)\]")
_ALPHA = re.compile(
    r"^\s+(SAW \(full\)|ABLATED \(saw_lam=0, no potential\))\s+"
    r"(alpha_short|alpha_long|anisotropy): mean=([\d.]+) "
    r"CI95=\[([\d.]+), ([\d.]+)\]")


def load(path: str = LOG) -> dict:
    text = open(path).read()
    out: dict = {"seeds": {"LOG": [], "LINEAR": []}, "summary": {},
                 "floor": {}, "slope": {}, "alpha": {}, "path": path}
    for line in text.splitlines():
        if (m := _SEED.match(line)):
            arm, seed, p1, p2, fl = m.groups()
            out["seeds"][arm].append(
                {"seed": int(seed), "k1000": float(p1), "k10000": float(p2),
                 "floor": float(fl)})
        elif (m := _SUM.match(line)):
            arm, k, mean, sd, lo, hi, pct = m.groups()
            out["summary"][(arm, int(k))] = {
                "mean": float(mean), "sd": float(sd),
                "ci": (float(lo), float(hi)), "pct_of_floor": float(pct)}
        elif (m := _FLOOR.match(line)):
            arm, mean, sd, sesoi = m.groups()
            out["floor"][arm] = {"mean": float(mean), "sd": float(sd),
                                 "sesoi": float(sesoi)}
        elif (m := _SLOPE.match(line)):
            arm, slope = m.groups()
            out["slope"][arm] = {"slope": float(slope)}
            if (d := _DRIVES.search(line)):
                out["slope"][arm]["drives"] = [
                    float(x) for x in d.group(1).split()]
            if (s := _STEP.search(line)):
                out["slope"][arm]["steps"] = [
                    float(x) for x in s.group(1).split()]
        elif (m := _ALPHA.match(line)):
            arm, stat, mean, lo, hi = m.groups()
            arm = "SAW" if arm.startswith("SAW") else "ABLATED"
            out["alpha"].setdefault(arm, {})[stat] = {
                "mean": float(mean), "ci": (float(lo), float(hi))}
    # the per-decade steps line follows the LOG slope line, not on it
    for arm in ("LOG", "LINEAR"):
        if arm in out["slope"] and "steps" not in out["slope"][arm]:
            blk = text.split(f"{arm}: drive vs ln(I) slope")[1][:400]
            if (s := _STEP.search(blk)):
                out["slope"][arm]["steps"] = [
                    float(x) for x in s.group(1).split()]
            if (d := _DRIVES.search(blk)):
                out["slope"][arm].setdefault(
                    "drives", [float(x) for x in d.group(1).split()])
    return out


if __name__ == "__main__":
    d = load()
    print("seeds:", {k: len(v) for k, v in d["seeds"].items()})
    print("summary keys:", sorted(d["summary"]))
    print("floor:", d["floor"])
    print("slope:", d["slope"])
    print("alpha:", d["alpha"])
