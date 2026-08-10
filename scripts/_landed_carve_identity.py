"""Reproduce the LANDED 160x120 Doom carve (4 polys / union_iou 0.1215 /
carve_precision 0.9784 / 0 false) on BOTH the graph-native event path and the
Python-loop oracle, and prove the two are byte-identical. Uses the committed
carve fixture + the exact doom_carve_scale flow. Slow (full 19200-cell run_rules
per tick); run once, record in RESULTS."""
import sys, os, json
sys.path.insert(0, "runners/dsl/python"); sys.path.insert(0, ".")
import numpy as np
import scripts.doom_carve_scale_measure as D
from domains.photon_eye import GraphEye


def build(n_el, n_az, event_native):
    return GraphEye(n_az=n_az, n_el=n_el, adapt_rate=D.ADAPT_RATE,
        context={"retina_2d": True, "synchronous": True, "worker_capacity": 1,
                 "onset_threshold_db": D.ONSET_DB, "onset_refractory_epochs": 0.0,
                 "visual_carve": True, "carve_min_coherence": D.CARVE_MIN_COH,
                 "carve_min_events": D.CARVE_MIN_EVENTS,
                 "event_native": event_native}).build()


def run(lumas, lg, nm, n_el, n_az, event_native):
    eye = build(n_el, n_az, event_native)
    rng = np.random.default_rng(D.SEED)
    f0, motion = lumas[0], lumas[1:]
    for _ in range(D.WARMUP):
        D._tick(eye, f0, rng)
    for nid in list(eye.substrate.nodes("RetinalOnsetEvent")):
        eye.substrate.remove_node(nid)
    since = eye._epoch + 1
    for luma in motion:
        D._tick(eye, luma, rng)
    eye.settle_carve_2d(since_epoch=since)
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()
    polys = eye.carve_polygons_2d()
    sc = D.score_carve(polys, nm, lg, n_el, n_az)
    eye.stop()
    return polys, sc


def main():
    FIX = os.path.join("tests", "fixtures", "doom_carve_scale")
    d = np.load(os.path.join(FIX, "frames_160x120.npz"))
    names = json.load(open(os.path.join(FIX, "label_names.json")))
    lumas, labs = d["lumas"], d["labels"]
    n_el, n_az = labs.shape[1], labs.shape[2]
    lseq = [lumas[i] for i in range(lumas.shape[0])]
    lg = [labs[i] for i in range(1, labs.shape[0])]
    nm = [names[i] for i in range(1, labs.shape[0])]
    out = {}
    for native, tag in ((True, "native"), (False, "oracle")):
        polys, sc = run(lseq, lg, nm, n_el, n_az, native)
        out[tag] = {"polys": polys, "n_polygons": sc["n_polygons"],
                    "union_iou": sc["union_iou"],
                    "carve_precision": sc["carve_precision"],
                    "false_polygons": sc["false_polygons"]}
        print(tag, "n_polys", sc["n_polygons"], "union_iou", sc["union_iou"],
              "prec", sc["carve_precision"], "false", sc["false_polygons"],
              flush=True)
    ident = json.dumps(out["native"]["polys"], sort_keys=True) == \
        json.dumps(out["oracle"]["polys"], sort_keys=True)
    out["byte_identical"] = ident
    print("BYTE-IDENTICAL native==oracle:", ident)
    os.makedirs(os.path.join("results", "eye_graphnative_event"), exist_ok=True)
    with open(os.path.join("results", "eye_graphnative_event",
                           "landed_carve_identity.json"), "w") as f:
        json.dump(out, f, indent=2)


if __name__ == "__main__":
    main()
