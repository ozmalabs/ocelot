"""COMPARATOR for the fixpoint coverage sweep (seeds 98000-98999).

Compares captured result documents field-by-field between arms, against an
EMPIRICALLY DERIVED same-engine noise set.

WHY NOT A HAND-WRITTEN TIMING-KEY LIST: the predecessor shipped one and measured
it INERT -- it excluded 0 fields in every single comparison while real wall-clock
noise flowed straight past it. A filter built from guessed key names covers
guessed key names. So the noise set here is MEASURED: run the FIX arm twice and
take the field paths that differ between two runs of the SAME engine.

SELF-TEST (§9.4): `--selftest` diffs the predecessor's committed
ARM_fix_codebook_axis.json against ARM_revert_codebook_axis.json and REQUIRES the
known `n_exact` movement to be found. A comparator that has never reported a
difference is not a comparator.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def flatten(obj, prefix=""):
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(flatten(v, f"{prefix}.{k}" if prefix else str(k)))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.update(flatten(v, f"{prefix}[{i}]"))
    else:
        out[prefix] = obj
    return out


def diff_paths(a, b):
    fa, fb = flatten(a), flatten(b)
    keys = set(fa) | set(fb)
    return {k for k in keys if fa.get(k, "<<absent>>") != fb.get(k, "<<absent>>")}


PROV_MARKERS = ("engine", "provenance", "_engine", "commit", "sha")


def is_provenance(path):
    """A field naming the BINARY, not a measurement.

    The two arms report DIFFERENT engine hashes BY DESIGN (that is the check
    that the revert took), so these can never be filtered by the same-engine
    noise set -- both fix replicates share one hash. They must be excluded
    explicitly.

    THIS FILTER IS COUNTED, NOT ASSUMED. The predecessor shipped a hand-written
    timing-key filter that excluded ZERO fields in every comparison while real
    noise flowed past it, and only discovered it was decorative by checking
    whether it had ever fired. So `n_provenance_excluded` is reported for every
    document, and a filter that never fires is reported as INERT.
    """
    leaf = path.split(".")[-1].split("[")[0].lower()
    return any(m in leaf for m in PROV_MARKERS)


def load(p):
    try:
        return json.loads(pathlib.Path(p).read_text())
    except Exception:
        return None


def selftest():
    d = ROOT / "results" / "fixpoint_rerun"
    a = load(d / "ARM_fix_codebook_axis.json")
    b = load(d / "ARM_revert_codebook_axis.json")
    assert a and b, "predecessor arms missing -- cannot self-test"
    paths = diff_paths(a, b)
    hits = sorted(p for p in paths if "n_exact" in p)
    print(f"COMPARATOR SELF-TEST: {len(paths)} differing paths found; "
          f"{len(hits)} mention n_exact")
    for h in hits:
        print("   ", h, "->", flatten(a).get(h), "vs", flatten(b).get(h))
    assert hits, "COMPARATOR IS INERT -- it failed to find the KNOWN movement"
    print("SELF-TEST PASSED: the comparator can report a difference.")


def main():
    if "--selftest" in sys.argv:
        selftest()
        return

    fixA = pathlib.Path(sys.argv[1]) / "docs"
    fixB = pathlib.Path(sys.argv[2]) / "docs"
    rev = pathlib.Path(sys.argv[3]) / "docs"
    out = pathlib.Path(sys.argv[4])

    rows, noise_total = {}, set()
    for p in sorted(fixA.glob("*.json")):
        name = p.name
        a, b, r = load(p), load(fixB / name), load(rev / name)
        if b is None or r is None:
            rows[name] = {"verdict": "NOT_RUN",
                          "reason": "missing in " + ("fixB " if b is None else "")
                                    + ("revert" if r is None else "")}
            continue
        noise = diff_paths(a, b)          # SAME engine, two runs = the noise floor
        arm = diff_paths(a, r)            # fix vs revert
        prov = {p for p in arm if is_provenance(p)}
        real = sorted(arm - noise - prov)
        noise_total |= {f"{name}:{n}" for n in noise}
        rows[name] = {
            "verdict": "MOVED" if real else "unmoved",
            "n_noise_paths": len(noise),
            "n_provenance_excluded": len(prov),
            "n_arm_paths": len(arm),
            "n_real_moves": len(real),
            "moved_paths": real[:60],
            "moved_sample": {k: {"fix": flatten(a).get(k), "revert": flatten(r).get(k)}
                             for k in real[:12]},
        }

    prov_fired = sum(v.get("n_provenance_excluded", 0) for v in rows.values())
    noise_fired = sum(v.get("n_noise_paths", 0) for v in rows.values())
    print(f"provenance filter excluded {prov_fired} field(s) total "
          f"{'-- INERT!' if prov_fired == 0 else ''}")
    print(f"derived same-engine noise set covered {noise_fired} field(s) total "
          f"{'-- INERT!' if noise_fired == 0 else ''}")
    out.write_text(json.dumps(
        {"n_docs": len(rows), "n_provenance_excluded_total": prov_fired,
         "n_noise_paths_fired_total": noise_fired, "n_moved": sum(1 for v in rows.values()
                                             if v["verdict"] == "MOVED"),
         "n_noise_paths_total": len(noise_total), "docs": rows}, indent=1))
    moved = [k for k, v in rows.items() if v["verdict"] == "MOVED"]
    print(f"{len(rows)} documents compared; MOVED: {len(moved)}")
    for m in moved:
        print(f"   MOVED {m}: {rows[m]['n_real_moves']} paths")


if __name__ == "__main__":
    main()
