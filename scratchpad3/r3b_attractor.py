"""POST-HOC DIAGNOSTIC (burned seeds 0-7, NOT a hypothesis test, NOT pre-registered).

THE QUESTION THE NULL RAISES: bistability DID break symmetry (dark and normal both
sit ~+0.038 over the floor, 4x rung 3), but normal == dark, so the direction it
picked cannot be coming from the INPUT's direction statistics. Where does it come
from? THE HYPOTHESIS: from the unit's OWN random delays -- the innate bias, latched
and amplified. If so, a trained unit's PREFERRED DIRECTION should be the SAME
direction the untrained unit already preferred, and it should be the same in dark
and normal even though those inputs are unrelated.

Measured as: agreement between the untrained unit's preferred direction and the
trained unit's, per unit; and dark-vs-normal agreement. Chance = 1/8 = 0.125."""
import numpy as np, sys
sys.path.insert(0, ".")
from scratchpad3.r3b_lib import boot, retinal_stream, P1, P2, VIDEO32
from domains.dorsal_world import sweep_response, N_DIR

def pref_dirs(world, dunits, seed):
    s = world.s
    dp = s.nodes("DorsalParams")[0]; wp = s.nodes("WaveParams")[0]
    e0 = float(s.node(dp)["attrs"]["oja_eta"]); b0 = float(s.node(dp)["attrs"]["bi_eta"])
    p0 = float(s.node(wp)["attrs"]["propagate"])
    s.set_attr(dp, "oja_eta", 0.0); s.set_attr(dp, "bi_eta", 0.0); s.set_attr(wp, "propagate", 0.0)
    try:
        rng = np.random.default_rng(seed + 5_150_000)
        ph = rng.random((N_DIR // 2, 4))
        R = np.zeros((N_DIR, len(dunits)))
        for k in range(N_DIR):
            for rep in range(4):
                R[k] += sweep_response(world, dunits, k, phase=float(ph[k % 4, rep])) / 4
    finally:
        s.set_attr(dp, "oja_eta", e0); s.set_attr(dp, "bi_eta", b0); s.set_attr(wp, "propagate", p0)
    return R.argmax(axis=0)

def arm_pref(arm, seed, v):
    s, w, us, dp, wp = boot(seed, bistable=1.0, bi_eta=1e-2)
    if arm == "untrained":
        return pref_dirs(w, us, seed)
    for i in range(P1):
        w.step(ignite_k=1 if i % 5 == 0 else 0, frame=None)
    if arm == "dark":
        for i in range(P2):
            w.step(ignite_k=1 if i % 5 == 0 else 0, frame=None)
    else:
        s.set_attr(wp, "propagate", 0.0)
        fr = retinal_stream(v, seed)
        for i in range(P2):
            w.step(ignite_k=0, frame=fr[i])
    return pref_dirs(w, us, seed)

v = np.load(VIDEO32)
U, D, Nm = [], [], []
for seed in range(8):
    U.append(arm_pref("untrained", seed, v))
    D.append(arm_pref("dark", seed, v))
    Nm.append(arm_pref("normal", seed, v))
    print(f"  seed {seed} done", flush=True)
U, D, Nm = np.concatenate(U), np.concatenate(D), np.concatenate(Nm)
print(f"\nPOST-HOC ATTRACTOR DIAGNOSTIC — n={len(U)} units, 8 burned seeds. Chance = 0.125\n")
print(f"  untrained -> dark    agreement: {np.mean(U == D):.3f}")
print(f"  untrained -> normal  agreement: {np.mean(U == Nm):.3f}")
print(f"  dark      -> normal  agreement: {np.mean(D == Nm):.3f}   <-- unrelated INPUTS")
