"""SCRATCH: verify a numpy reimplementation of the RetinaCell STATE CA is
byte-identical to the engine's state field. Positive control for the 'exact'
arm. NOT committed as a result; a calibration harness."""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()
import numpy as np
from substrate.boot_core import boot_core
from substrate.boot_core import load_seeds_into
import domains.seed_registry  # noqa
from domains.wave_world import WaveWorld

REST, ACT, REC, REF = 0, 1, 2, 3
NAME = {"rested": REST, "active": ACT, "recruited": REC, "refractory": REF}
REFRACTORY_STEPS = 4.0


def boot(g, seed=0):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves"])
    s.set_attr(s.nodes("WaveParams")[0], "propagate", 1.0)
    w = WaveWorld(s, h=g, w=g, seed=seed, fovea_radius=0)
    return s, w


def read_fields(s, w):
    """(state, activated_at, fired_at) as (g,g) int/float arrays, in grid coords."""
    ids = w._cell_ids
    st = s.get_attr_many(ids, "state")
    aa = s.get_attr_many(ids, "activated_at")
    fa = s.get_attr_many(ids, "fired_at")
    S = np.zeros((w.h, w.w), np.int8)
    A = np.zeros((w.h, w.w), np.float64)
    F = np.zeros((w.h, w.w), np.float64)
    for (r, c), stt, a, f in zip(w._cell_rc, st, aa, fa):
        S[r, c] = NAME[stt]
        A[r, c] = float(a)
        F[r, c] = float(f)
    return S, A, F


def ca_tick(S, A, F, step):
    """Exact reimplementation of ONE s.tick() wave relaxation on the STATE field.
    Inputs are POST commit+ignite (i.e. the pre-tick field at `step`). Returns
    post-tick (S,A,F). Radius-1, deterministic. Mirrors wv_propagate / wv_refract
    / wv_recover with disjoint activated_at==step vs <step phase guards.

    Order within the fixpoint does not matter for the final state because the
    three rules act on DISJOINT cell sets:
      propagate: reads active&activated_at==step, writes rested->recruited
      refract:   active & activated_at<step -> refractory (fired_at=step)
      recover:   refractory & step-fired_at>=refractory_steps -> rested
    A recruited cell is inert this tick (commit is next step). Recover frees a
    cell to rested; propagate can then recruit it only if it has a fresh-active
    neighbour AND is rested at read time -- but recover and propagate read the
    SAME pre-tick snapshot in the engine's first pass, and a cell cannot be both
    refractory and rested. New recruits are 'recruited' (not active) so they do
    not themselves propagate this tick. So a single synchronous pass suffices."""
    S2 = S.copy(); A2 = A.copy(); F2 = F.copy()
    fresh_active = (S == ACT) & (A == step)     # activated this step
    old_active = (S == ACT) & (A < step)
    refr = (S == REF)
    recover = refr & ((step - F) >= REFRACTORY_STEPS)
    # refract: old actives -> refractory, fired_at=step
    S2[old_active] = REF
    F2[old_active] = step
    # recover: refractory long enough -> rested
    S2[recover] = REST
    # propagate: rested neighbour of a fresh-active cell -> recruited.
    # A cell recovering to rested THIS tick is eligible (engine: recover fires,
    # then propagate can match it since state is now rested and it has a
    # fresh-active neighbour). Model the post-recover rested set.
    rested_now = (S2 == REST)
    fa = fresh_active
    nbr_fresh = np.zeros_like(fresh_active)
    nbr_fresh[1:, :] |= fa[:-1, :]
    nbr_fresh[:-1, :] |= fa[1:, :]
    nbr_fresh[:, 1:] |= fa[:, :-1]
    nbr_fresh[:, :-1] |= fa[:, 1:]
    recruit = rested_now & nbr_fresh
    S2[recruit] = REC
    return S2, A2, F2


def main():
    print(provenance_line())
    for g in (12, 16, 24):
        for seed in (0, 1, 7):
            s, w = boot(g, seed=seed)
            # wrap ignite to capture ignited cells per step
            ignited = {}
            o_ignite = w.ignite
            def wrapped(k, _o=o_ignite, _store=ignited, _w=w):
                out = _o(k)
                st = int(float(_w.s.node(_w.retina)["attrs"]["step"]))
                rc = []
                idmap = {nid: rc_ for rc_, nid in zip(_w._cell_rc, _w._cell_ids)}
                for nid in out:
                    rc.append(idmap[nid])
                _store[st] = rc
                return out
            w.ignite = wrapped
            mism = 0
            checks = 0
            S, A, F = read_fields(s, w)   # step 0 field
            IGNITE_EVERY = 5
            for i in range(60):
                # replicate step(): commit recruited->active(activated_at=step+1),
                # driven reset (irrelevant to state), ignite, drive(None), tick.
                stp = float(s.node(w.retina)["attrs"]["step"]) + 1.0
                # our model of commit+ignite happens INSIDE engine step; we just
                # read engine truth and reproduce the tick from the pre-tick field.
                k = 1 if (i % IGNITE_EVERY == 0) else 0
                w.step(ignite_k=k, frame=None)
                S_post, A_post, F_post = read_fields(s, w)
                # reconstruct the pre-tick field: commit recruited->active(step),
                # ignite the recorded cells->active(step). Start from previous post.
                Spre = S.copy(); Apre = A.copy(); Fpre = F.copy()
                commit = (Spre == REC)
                Spre[commit] = ACT; Apre[commit] = stp
                for (r, c) in ignited.get(int(stp), []):
                    Spre[r, c] = ACT; Apre[r, c] = stp
                Sca, Aca, Fca = ca_tick(Spre, Apre, Fpre, stp)
                checks += 1
                if not (np.array_equal(Sca, S_post) and np.array_equal(Aca, A_post)
                        and np.array_equal(Fca, F_post)):
                    mism += 1
                    if mism <= 2:
                        d = np.argwhere(Sca != S_post)
                        print(f"  g={g} seed={seed} step={int(stp)} STATE mism at {d[:5].tolist()}"
                              f" ca={[int(Sca[r,c]) for r,c in d[:5]]}"
                              f" eng={[int(S_post[r,c]) for r,c in d[:5]]}")
                        dA = np.argwhere(Aca != A_post)
                        if len(dA):
                            print(f"      A mism {len(dA)} e.g {dA[:3].tolist()}")
                        dF = np.argwhere(Fca != F_post)
                        if len(dF):
                            print(f"      F mism {len(dF)} e.g {dF[:3].tolist()}")
                S, A, F = S_post, A_post, F_post
            print(f"g={g} seed={seed}: {checks-mism}/{checks} ticks byte-identical")


if __name__ == "__main__":
    main()
