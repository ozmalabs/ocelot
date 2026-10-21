"""Shared rule-authoring helpers for the Track I seed generators.

Track I (`docs/research/engine_substrate/COGNITION_BUILD_TRACK_I_PROCESS_INVENTION.md`)
adds process schemas, an invention algebra, invariant walls, lifting,
library learning and understanding seeds. Every generator imports the term
helpers from `gen_capability_collapse_seed` (the project's rule DSL) and the
few extra constructors below, so all Track I seeds share one spelling.

Conventions used by every Track I seed:

* Opt-in: each seed's policy node starts `enabled: 0.0` and each seed is
  `self_load_only`, so no existing boot profile changes.
* Offline organisation rules run in area `memory_consolidation` (the area the
  consolidation scheduler recruits), online task rules in `process_solving`.
  Both use latency class `background`. Under the plain
  `StructRulesOnly` cycle every rule runs; under the dual-process cycle they
  run only when recruited (documented limit).
"""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from gen_capability_collapse_seed import (  # noqa: E402,F401
    A,
    And,
    Count,
    Eq,
    Filter,
    Gt,
    Gte,
    L,
    Lte,
    Max,
    N,
    Not,
    Or,
    Plus,
    T,
    V,
    ONE,
    ZERO,
)

OFFLINE_AREA = "memory_consolidation"
ONLINE_AREA = "process_solving"
LATENCY = "background"
NONE = L(None)


def Lt(a, b):
    return {"type": "Lt", "a": a, "b": b}


def Exists(source, var_name, predicate):
    return {"type": "Exists", "source": source, "var_name": var_name, "predicate": predicate}


def Min(*items):
    return {"type": "Min", "items": list(items)}


def Minus(a, b):
    return {"type": "Minus", "a": a, "b": b}


def Times(*items):
    return {"type": "Times", "items": list(items)}


def Div(a, b):
    return {"type": "Div", "a": a, "b": b}


def Log(arg):
    return {"type": "Log", "arg": arg}


def IfThenElse(cond, then, other):
    return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}


def Let(name, value, body):
    return {"type": "Let", "name": name, "value": value, "body": body}


def In(member, container):
    return {"type": "In", "member": member, "container": container}


def Vec(*items):
    return {"type": "Vec", "items": list(items)}


def SetT(*items):
    return {"type": "SetT", "items": list(items)}


def Union(a, b):
    return {"type": "Union", "a": a, "b": b}


def IndexAt(seq, index):
    return {"type": "IndexAt", "seq": seq, "index": index}


def Nth(items, index):
    return {"type": "Nth", "items": items, "index": index}


def Append(seq, item):
    return {"type": "Append", "seq": seq, "item": item}


def Slice(seq, start, stop):
    return {"type": "Slice", "seq": seq, "start": start, "stop": stop}


def Sort(seq):
    return {"type": "Sort", "seq": seq}


def Pick(source):
    return {"type": "Pick", "source": source}


def NodesOfType(node_type):
    return {"type": "NodesOfType", "node_type": node_type}


def NodesWhere(node_type, attr_key, value):
    return {"type": "NodesWhere", "node_type": node_type, "attr_key": attr_key, "value": value}


def InN(var, edge_type):
    return {"type": "InNeighbours", "node": V(var), "edge_type": edge_type}


def MapSet(source, var_name, value):
    return {"type": "MapSet", "source": source, "var_name": var_name, "value": value}


def MapList(source, var_name, value):
    return {"type": "MapList", "source": source, "var_name": var_name, "value": value}


def FilterList(source, var_name, predicate):
    return {"type": "FilterList", "source": source, "var_name": var_name, "predicate": predicate}


def Sum(source, var_name, value):
    return {"type": "Sum", "source": source, "var_name": var_name, "value": value}


def MinOver(source, var_name, value, default=None):
    t = {"type": "MinOver", "source": source, "var_name": var_name, "value": value}
    if default is not None:
        t["default"] = default
    return t


def Argmin(source, var_name, value, default=None):
    t = {"type": "Argmin", "source": source, "var_name": var_name, "value": value}
    if default is not None:
        t["default"] = default
    return t


def Argmax(source, var_name, value, default=None):
    t = {"type": "Argmax", "source": source, "var_name": var_name, "value": value}
    if default is not None:
        t["default"] = default
    return t


def ZipWith(a, b, a_name, b_name, value):
    return {"type": "ZipWith", "a": a, "b": b, "a_name": a_name, "b_name": b_name, "value": value}


def SoftWeights(source, var_name, value, temperature, default=None):
    t = {"type": "SoftWeights", "source": source, "var_name": var_name, "value": value,
         "temperature": temperature}
    if default is not None:
        t["default"] = default
    return t


def AntiUnify(values):
    return {"type": "AntiUnify", "values": values}


def Covers(pattern, instance):
    return {"type": "Covers", "pattern": pattern, "instance": instance}


def VecSub(a, b):
    return {"type": "VecSub", "a": a, "b": b}


def StringConcat(*parts):
    return {"type": "StringConcat", "parts": list(parts)}


def ToJsonString(value):
    return {"type": "ToJsonString", "value": value}


def Mod(a, b):
    return {"type": "Mod", "a": a, "b": b}


# --- Track I process-algebra Terms (runners/dsl/src/process_algebra.rs) ---

def PCompose(a, b):
    return {"type": "ProcessCompose", "a": a, "b": b}


def PInverse(a):
    return {"type": "ProcessInverse", "a": a}


def PApply(p, state):
    return {"type": "ProcessApply", "p": p, "state": state}


def PSupport(p):
    return {"type": "EffectSupport", "p": p}


def PFingerprint(p, probes):
    return {"type": "EffectFingerprint", "p": p, "probes": probes}


def PParity(p):
    return {"type": "PermParity", "p": p}


def PCommutator(a, b):
    """[a, b] = a, b, a⁻¹, b⁻¹ (the probe's convention)."""
    return PCompose(PCompose(PCompose(a, b), PInverse(a)), PInverse(b))


def PConjugate(a, s):
    """s, a, s⁻¹ — "do a in s's frame"."""
    return PCompose(PCompose(s, a), PInverse(s))


def PPower(a, k):
    out = a
    for _ in range(k - 1):
        out = PCompose(out, a)
    return out


def is_none(term):
    return Eq(term, NONE)


def not_none(term):
    return Not(Eq(term, NONE))


def hamming(x, y):
    """Number of positions where two equal-length sequences differ."""
    return Sum(ZipWith(x, y, "hx", "hy", IfThenElse(Eq(V("hx"), V("hy")), ZERO, ONE)), "hd", V("hd"))


def rule(name, area, order, comment, match, where, effects, batch=None):
    r = {
        "name": name,
        "area": area,
        "order": order,
        "latency_class": LATENCY,
        "comment": comment,
        "match": match,
        "where": where,
        "effects": effects,
    }
    if batch is not None:
        r["batch"] = batch
    return r


def productions(seed_id, specs):
    return [
        {
            "provenance": f"seed:{seed_id}:{edge_type}:{src}:{tgt}",
            "src": {"type": src, "var": "src"},
            "edge_type": edge_type,
            "tgt": {"type": tgt, "var": "tgt"},
        }
        for src, edge_type, tgt in specs
    ]


def policy_on(var="pol"):
    return Eq(A(var, "enabled"), L(1.0))
