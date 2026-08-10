"""DISCONNECTION — grounding is a MAINTAINED dependency, not a possessed trait. Cut the world-residual
from a healthy articulate brain and it slides into the ungrounded quadrant (hallucination), in real
time; reconnect and it snaps back.

Creator adds the clearest natural occupant of the ungrounded-articulate quadrant: a brain alive but
DISCONNECTED FROM ITS BODY — deafferentation (Ian Waterman, total proprioceptive loss), total locked-
in syndrome, sensory-deprivation tanks. A fully grounded, fully articulate mind, cut off from world
and body — and what reliably follows is HALLUCINATION: deprived of the world-residual, the brain fills
in from its own prior and drifts into confabulation (sensory deprivation -> hallucination onset within
tens of minutes). REM dreaming is a nightly transient version (atonia + sensory gating = the body
disconnected).

This is the natural EXPERIMENT the rest of the arc predicts: take a grounded self-model, WITHDRAW the
world-residual, watch it drift into the quadrant; restore it, watch it recapture. It shows grounding
is not a trait you HAVE but a contact you MAINTAIN — and reframes the LLM precisely: the disconnected
brain shows the TRAJECTORY out of grounding; the LLM is the case that was never connected.

TEST: a self-model tracks a drifting truth. CONNECTED = world-residual every step. At t_cut it is
DISCONNECTED (residual withdrawn -> runs on its own prior = hallucination). At t_reconnect, restored.
Measure error over time: low -> rises (hallucination onset) -> low (recovery).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_disconnection.py
"""
import numpy as np


def trajectory(n=180, t_cut=60, t_reconnect=120, drift=0.05, self_pull=0.3, seed=0):
    rng = np.random.default_rng(seed)
    truth = np.cumsum(rng.normal(0, drift, n)) + 1.0
    prior = 0.0                                      # the self's resting belief (its own prior)
    s, e, connected = 0.0, [], []
    for t in range(n):
        e.append(abs(s - truth[t]))
        on = (t < t_cut) or (t >= t_reconnect)       # body/world connected?
        connected.append(on)
        s += self_pull * (prior - s)                 # the self-model's own pull (toward its prior)
        if on:
            s += 1.0 * (truth[t] - s)                # WORLD-residual: contact with reality
    return np.array(e), np.array(connected)


def main():
    n, t_cut, t_rec = 180, 60, 120
    E = np.mean([trajectory(n, t_cut, t_rec, seed=i)[0] for i in range(30)], axis=0)
    conn = trajectory(n, t_cut, t_rec)[1]
    nb = 18
    eb = [np.mean(c) for c in np.array_split(E, nb)]
    cb = [bool(np.mean(c) > 0.5) for c in np.array_split(conn, nb)]
    mx = max(eb)
    print("=" * 84)
    print("DISCONNECTION — grounding is a contact you MAINTAIN; cut it and an articulate brain drifts")
    print("  (connected -> DISCONNECTED at ~1/3 -> reconnected at ~2/3); err over time, bar ~ error")
    print("=" * 84)
    for i, (e, c) in enumerate(zip(eb, cb)):
        bar = "#" * int(round(40 * e / mx))
        phase = "connected " if c else "CUT (halluc)"
        print(f"  t{i:02d} {phase:12} {e:5.3f} |{bar}")
    print("=" * 84)
    # hallucination onset: steps after the cut to cross half the eventual drift
    e_full, _ = trajectory(n, t_cut, t_rec)
    base = np.mean(e_full[:t_cut]); peak = np.max(e_full[t_cut:t_rec]); thr = base + 0.5 * (peak - base)
    onset = next((t - t_cut for t in range(t_cut, t_rec) if e_full[t] >= thr), None)
    print(f"  connected error ~{base:.3f}; after the cut it climbs to ~{peak:.3f} (HALLUCINATION — the")
    print(f"  self-model filling in from its own prior); onset ~{onset} steps; on reconnection it SNAPS")
    print(f"  back (recapture). Grounding is not a TRAIT the brain has — it is CONTACT it must keep.")
    print("=" * 84)
    print("  The natural experiment the arc predicts: deafferentation / locked-in / sensory-deprivation")
    print("  = a grounded, articulate brain cut from the world -> it drifts into the ungrounded quadrant")
    print("  (hallucination), then recovers when reconnected. The LLM is the limiting case: never")
    print("  connected, so the 'hallucination' is its steady state. Grounding it = restoring the contact.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
