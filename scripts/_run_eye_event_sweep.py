import sys, os, json
sys.path.insert(0, "runners/dsl/python"); sys.path.insert(0, ".")
import scripts.eye_graphnative_event_measure as M

# Cheap resolutions: full trials. 160x120: bounded (run_rules ~23s/frame).
plan = {(20, 15): (2, 4, 3), (40, 30): (2, 4, 3), (80, 60): (2, 4, 2),
        (160, 120): (1, 2, 1)}
rows = {"native": [], "oracle": []}
for (a, e), (w, m, t) in plan.items():
    for native, tag in ((True, "native"), (False, "oracle")):
        r = M.measure(a, e, native, warmup=w, motion=m, trials=t)
        rows[tag].append(r)
        print(f"{tag:7s} {a:3d}x{e:3d} cells={r['cells']:6d} ev/f={r['n_events_per_frame']:6d} "
              f"submit={r['submit_ms']:8.3f} settle={r['settle_ms']:9.4f} "
              f"kernel={r['kernel_ms']:8.3f} readout={r['readout_ms']:7.3f} "
              f"FRAME={r['frame_ms']:10.3f}  n_polys={r['n_polys']}", flush=True)
summary = M.summarise(rows)
os.makedirs(M.OUTDIR, exist_ok=True)
with open(os.path.join(M.OUTDIR, "curves.json"), "w") as f:
    json.dump(summary, f, indent=2)
print("\n=== SETTLE (event-path) exponent — the fixed stage ===")
print("  oracle:", summary["fits"]["oracle_settle_exponent"],
      " native:", summary["fits"]["native_settle_exponent"])
print("=== FRAME (end-to-end) exponent ===")
print("  oracle:", summary["fits"]["oracle_frame_exponent"],
      " native:", summary["fits"]["native_frame_exponent"])
print("=== MAX RECEPTORS @ real-time (from FRAME curve) ===")
for k, v in summary["max_receptors"].items():
    print(f"  {k:16s} = {v}")
print("wrote", os.path.join(M.OUTDIR, "curves.json"))
