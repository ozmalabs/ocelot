"""composition_engine — multi-premise relational composition (the faculty
synthesize_gaps lacked: it transfers ONE shape; this CONJOINS premises).

Premises are signed relations (A, rel, B). Monotone relations carry a sign:
+1 (increases/causes/requires/constitutes/enables/implies/raises) or
-1 (reduces/prevents/dissolves/removes/lowers/blocks). Composition chains them
and MULTIPLIES the signs along the path — qualitative/causal sign-propagation —
so A→B(-) then B→C(+) yields A→C(-). Forward-chained to a depth bound, shortest
chain wins (MDL). This is general: it composes ANY relational premises, not a
fixed answer. Returns derived conclusions with net sign + the chain that proves
them (so every conclusion is explainable).
"""
from __future__ import annotations
from collections import defaultdict, deque

POS = {"increases", "causes", "requires", "constitutes", "enables", "implies",
       "raises", "drives", "is", "via", "amplifies"}
NEG = {"reduces", "prevents", "dissolves", "removes", "lowers", "blocks", "defuses"}


def _sign(rel: str) -> int:
    if rel in NEG:
        return -1
    return +1  # default + (POS or unknown monotone)


def compose(premises, max_depth: int = 8):
    """premises: iterable of (A, rel, B). Returns {(src,tgt): (net_sign, chain)}
    for every DERIVED (multi-step) conclusion, shortest chain, net sign."""
    edges = defaultdict(list)
    nodes = set()
    for A, rel, B in premises:
        edges[A].append((B, _sign(rel), rel))
        nodes.add(A); nodes.add(B)

    results = {}
    for src in nodes:
        q = deque([(src, 1, [])])
        seen = {src}
        while q:
            node, s, chain = q.popleft()
            if len(chain) >= max_depth:
                continue
            for nb, es, rel in edges.get(node, []):
                if nb in seen:
                    continue
                ns, nchain = s * es, chain + [(node, rel, nb)]
                key = (src, nb)
                if key not in results:           # BFS ⇒ first found = shortest
                    results[key] = (ns, nchain)
                seen.add(nb)
                q.append((nb, ns, nchain))
    # keep only multi-step derivations (length >= 2 = genuinely composed)
    return {k: v for k, v in results.items() if len(v[1]) >= 2}


def query(derived, src, tgt):
    return derived.get((src, tgt))


def fmt_chain(chain) -> str:
    out = chain[0][0]
    for a, rel, b in chain:
        arrow = "—" + rel + "→"
        out += f" {arrow} {b}"
    return out


def verdict(net: int, src: str, tgt: str) -> str:
    return f"{src} {'INCREASES' if net > 0 else 'REDUCES'} {tgt}  (net {'+' if net>0 else '−'})"
