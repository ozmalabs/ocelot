"""THE JABBERWOCK ASSEMBLES NETS VIA ITS GRAPH — the agent's substrate makes every assembly decision; the GPU
is only its hands. Each round the agent's GRAPH (substrate_rs Argmin/Argmax + gate Terms) decides which banked
architecture to expand and whether to ESCALATE (still < human bar) or SHRINK (find the cheapest net that holds
>=95). The host mechanically applies the chosen mutation, trains it on the GPU (the world), and banks the
measured (accuracy, params) back as a graph node. Compose-search-gate over architecture, driven by the agent.

Run: PYTHONPATH=runners/dsl/python:. python3 scripts/jabberwock_assembles_via_graph.py
"""
from __future__ import annotations
import json, os, re, subprocess, sys, time
BANKF = "/tmp/asm_bank.json"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))
import substrate_rs as srs

HOST = "192.168.40.253"; TARGET = 95.0; ROUNDS = 9
SC = {"lo": 0.0, "hi": 1.0, "dual": 2.0}


def _V(n): return {"type": "Var", "name": n}
def _L(v): return {"type": "Lit", "value": v}
def _A(n, k): return {"type": "Attr", "node": _V(n), "key": k}
def _Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def _Ite(c, t, e): return {"type": "IfThenElse", "cond": c, "then": t, "other": e}
def _Argmin(src, var, val): return {"type": "Argmin", "source": src, "var_name": var, "value": val, "default": _L(-1.0)}
def _Argmax(src, var, val): return {"type": "Argmax", "source": src, "var_name": var, "value": val, "default": _L(-1.0)}
def _NW(t, k, v): return {"type": "NodesWhere", "node_type": t, "attr_key": k, "value": v}


class _P:
    __slots__ = ("_json",)

    def __init__(s, d): s._json = d


def grow(g):
    d, w, s, tw = g; out = []
    if s == "lo": out.append((d, w, "dual", tw))
    if tw < 60: out.append((d, w, s, 60))
    if w < 96: out.append((d, (96 if w >= 64 else w * 2), s, tw))
    if d < 5: out.append((d + 1, w, s, tw))
    return out


def shrink(g):
    d, w, s, tw = g; out = []
    if w > 32: out.append((d, (32 if w <= 48 else w // 2), s, tw))
    if d > 3: out.append((d - 1, w, s, tw))
    if s == "dual": out.append((d, w, "lo", tw))
    if tw > 20: out.append((d, w, s, 20))
    return out


def agent_decide(bank):
    """THE AGENT'S GRAPH decides: pick the banked genome to expand + the mode (escalate/shrink), graph-natively."""
    s = srs.Substrate()
    for gi, (g, a, p) in enumerate(bank):
        s.add_node("Cand", {"is_c": 1.0, "acc": float(a), "params": float(p), "gi": float(gi)})
    src = _NW("Cand", "is_c", _L(1.0))
    # cheapest genome that ALREADY clears the bar (gate: qualifying -> params, else +inf) -> floor candidate
    floor_val = _Ite(_Gt(_A("c", "acc"), _L(TARGET)), _A("c", "params"), _L(1e12))
    fp = s.evaluate(_P(_Argmin(src, "c", floor_val)), {})
    if s.node(fp)["attrs"]["acc"] >= TARGET:
        return int(s.node(fp)["attrs"]["gi"]), "floor"
    # else escalate the highest-accuracy genome so far
    ep = s.evaluate(_P(_Argmax(src, "c", _A("c", "acc"))), {})
    return int(s.node(ep)["attrs"]["gi"]), "escalate"


def train(genome):
    d, w, sc, tw = genome
    out = subprocess.run(["ssh", "-o", "ConnectTimeout=6", HOST,
                          f"/tmp/venv/bin/python /tmp/gpu_train_one.py {d} {w} {sc} {tw}"],
                         capture_output=True, text=True, timeout=600).stdout
    m = re.search(r"ACC=([\d.]+) PARAMS=(\d+)", out)
    return (float(m.group(1)), int(m.group(2))) if m else (0.0, 0)


def main():
    print("=" * 92)
    print("THE JABBERWOCK ASSEMBLES NETS VIA ITS GRAPH (substrate decides; GPU trains).")
    print("=" * 92, flush=True)
    bank = []; tried = set()
    if os.path.exists(BANKF):                      # resume across crashes/kills
        for g, a, p in json.load(open(BANKF)):
            g = tuple(g); bank.append((g, a, p)); tried.add(g)
        print(f"  resumed: {len(bank)} banked", flush=True)
    seed = (4, 64, "lo", 20)
    for rnd in range(len(bank), ROUNDS):
        if not bank:
            g = seed
        else:
            gi, mode = agent_decide(bank)           # <-- the agent's graph picks
            base = bank[gi][0]
            cands = (shrink(base) if mode == "floor" else grow(base))
            g = next((m for m in cands if m not in tried), None)
            if g is None:  # the picked genome is exhausted; expand the next best untried-neighbour genome
                g = next((m for (bg, _, _) in sorted(bank, key=lambda x: -x[1])
                          for m in grow(bg) + shrink(bg) if m not in tried), None)
            if g is None:
                print("  search exhausted"); break
        tried.add(g); t0 = time.time(); acc, params = train(g)
        bank.append((g, acc, params))
        json.dump([[list(gg), a, p] for gg, a, p in bank], open(BANKF, "w"))
        cleared = max(b[1] for b in bank) >= TARGET
        print(f"  [{rnd}] graph chose d{g[0]} w{g[1]} {g[2]} tw{g[3]} -> {acc:.1f}% / {params/1000:.0f}K  "
              f"({time.time()-t0:.0f}s)  mode={'FLOOR' if cleared else 'escalate'}", flush=True)

    print("\n" + "=" * 92)
    print("  ASSEMBLED FRONTIER (the agent's graph drove every pick):")
    for g, a, p in sorted(bank, key=lambda x: -x[1]):
        print(f"    d{g[0]} w{g[1]} {g[2]} tw{g[3]}: {a:.1f}% / {p/1000:.0f}K")
    clear = [b for b in bank if b[1] >= TARGET]
    if clear:
        g, a, p = min(clear, key=lambda x: x[2])
        print(f"\n  FLOOR (cheapest net the agent assembled that holds >=95): d{g[0]} w{g[1]} {g[2]} tw{g[3]} "
              f"= {a:.1f}% / {p/1000:.0f}K params (Gemma 96.3/167.6M = {167.6e6/p:.0f}x larger)")
    else:
        b = max(bank, key=lambda x: x[1]); print(f"\n  best so far {b[1]:.1f}% / {b[2]/1000:.0f}K (not yet >=95)")
    print("=" * 92)


if __name__ == "__main__":
    raise SystemExit(main())
