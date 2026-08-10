"""Author slice 6 of seeds/projection.json: TRUE ANGULAR RAYCAST."""
import json, copy, pathlib

P = pathlib.Path(__file__).resolve().parent.parent / "seeds" / "projection.json"
d = json.loads(P.read_text())

def var(n):          return {"type": "Var", "name": n}
def lit(v):          return {"type": "Lit", "value": v}
def attr(n, k):      return {"type": "Attr", "node": var(n), "key": k}
def holds(c, n, n2): return {"type": "Holds", "concept": c, "node": var(n), "node2": var(n2)}
def eq(a, b):        return {"type": "Eq", "a": a, "b": b}
def minus(a, b):     return {"type": "Minus", "a": a, "b": b}
def times(*xs):      return {"type": "Times", "items": list(xs)}
def plus(*xs):       return {"type": "Plus", "items": list(xs)}
def div(a, b):       return {"type": "Div", "a": a, "b": b}
def sin(a):          return {"type": "Sin", "arg": a}
def cos(a):          return {"type": "Cos", "arg": a}
def atan2(y, x):     return {"type": "Atan2", "y": y, "x": x}
def sqrt(a):         return {"type": "Sqrt", "arg": a}
def nott(a):         return {"type": "Not", "arg": a}
def ite(c, t, o):    return {"type": "IfThenElse", "cond": c, "then": t, "other": o}
def is_raycast():    return eq(attr("y", "raycast"), lit(1.0))

concepts = {c["name"]: c for c in d["concepts"]}
dx = minus(holds("screen_u", "x", "y"), attr("y", "px"))   # X - px (role-0)
dy = minus(holds("screen_v", "x", "y"), attr("y", "py"))   # Y - py (role-1)

# proj_u: wrap with raycast bearing branch (slice-5 def preserved in `other`)
concepts["proj_u"]["definition"] = ite(
    is_raycast(), minus(atan2(dy, dx), attr("y", "yaw")),
    copy.deepcopy(concepts["proj_u"]["definition"]))
concepts["proj_u"]["comment"] = ("PROJECTED screen-u, kind aware (slice 6). raycast==1 "
    "-> BEARING atan2(Y-py,X-px)-yaw (X=screen_u/role0, Y=screen_v/role1); else slice-5 "
    "persp pinhole / ortho identity. Kinds disjoint via absent-attr fall-through.")

# proj_v: raycast world is 1-D (bearing) -> constant 0 so the occlusion column groups by bearing
concepts["proj_v"]["definition"] = ite(
    is_raycast(), lit(0.0), copy.deepcopy(concepts["proj_v"]["definition"]))
concepts["proj_v"]["comment"] = ("PROJECTED screen-v, kind aware (slice 6). raycast==1 -> "
    "constant 0 (1-D screen) so same-(u,v) column = same-BEARING; else slice-5 / ortho.")

# proj_depth: raycast euclidean range; else == ray_depth (byte-identical for ortho/persp)
proj_depth = {"name": "proj_depth", "domain": "projection",
  "definition": ite(is_raycast(), sqrt(plus(times(dx, dx), times(dy, dy))),
                    holds("ray_depth", "x", "y")),
  "comment": ("DEPTH for occlusion, kind aware (slice 6). raycast==1 -> euclidean range "
    "sqrt((X-px)^2+(Y-py)^2) (near hides far at same bearing); else == ray_depth so "
    "ortho/persp occlusion unchanged. project_sample folds this instead of ray_depth.")}
d["concepts"].insert(
    next(i for i, c in enumerate(d["concepts"]) if c["name"] == "ray_depth") + 1, proj_depth)

# project_sample: occlusion fold reads proj_depth (kind aware) instead of ray_depth
def retarget(node):
    if isinstance(node, dict):
        if node.get("type") == "Holds" and node.get("concept") == "ray_depth":
            node["concept"] = "proj_depth"
        for v in node.values(): retarget(v)
    elif isinstance(node, list):
        for v in node: retarget(v)
rules = {r["name"]: r for r in d["rules"]}
retarget(rules["project_sample"]["where"])
rules["project_sample"]["comment"] += (" | SLICE 6: occlusion fold reads proj_depth "
    "(kind-aware) not ray_depth -> raycast occludes by min euclidean range; ortho/persp "
    "unchanged (proj_depth==ray_depth there).")

# raycast_triangulate LIFT
th1 = plus(attr("vp1", "yaw"), attr("s1", "u"))
th2 = plus(attr("vp2", "yaw"), attr("s2", "u"))
dpx = minus(attr("vp2", "px"), attr("vp1", "px"))   # px2 - px1
dpy = minus(attr("vp2", "py"), attr("vp1", "py"))   # py2 - py1
sin_diff = sin(minus(th2, th1))                      # sin(th2 - th1)
t1 = div(minus(times(dpx, sin(th2)), times(dpy, cos(th2))), sin_diff)
X = plus(attr("vp1", "px"), times(t1, cos(th1)))     # X = px1 + t1*cos(th1)
Y = plus(attr("vp1", "py"), times(t1, sin(th1)))     # Y = py1 + t1*sin(th1)
lid = plus(times(X, lit(1000000)), Y)

rt = {"name": "raycast_triangulate",
 "comment": ("SLICE 6: ANGULAR TRIANGULATION LIFT (true Doom/Quake depth-from-motion; "
   "subsumes slice-5 pinhole as its small-angle limit). Two raycast INPUT vps (vp_mode 1, "
   "raycast 1) at known poses + the two Samples of ONE Feature (of_feature). Sample.u IS "
   "the bearing b_i; th_i = yaw_i + b_i; intersect rays: t1 = ((px2-px1)*sin th2 - "
   "(py2-py1)*cos th2)/sin(th2-th1); X = px1 + t1*cos th1; Y = py1 + t1*sin th1. Mints "
   "Locus at (X role0, Y role1) + recovered_from->f + appearance; Coords on/proj_role so "
   "screen_u/screen_v read it back. GUARDS: Lt(vp2.vp_id,vp1.vp_id); Not(Eq(sin(th2-th1),"
   "0)) (parallel rays / collinear feature -> no mint, dodges Div-by-0). LOOP-FREE (input "
   "vps, no Sample written on them). IDEMPOTENT (lid=X*1e6+Y deterministic). Disjoint from "
   "parallax_lift (persp==1)."),
 "match": [["game","has_viewpoint","vp1"],["game","has_viewpoint","vp2"],
   ["vp1","has_sample","s1"],["vp2","has_sample","s2"],
   ["s1","of_feature","f"],["s2","of_feature","f"],
   ["game","has_axis","latax"],["game","has_axis","otheraxis"]],
 "where": {"type": "And", "items": [
   eq(attr("vp1","vp_mode"),lit(1.0)), eq(attr("vp2","vp_mode"),lit(1.0)),
   eq(attr("vp1","raycast"),lit(1.0)), eq(attr("vp2","raycast"),lit(1.0)),
   {"type":"Lt","a":attr("vp2","vp_id"),"b":attr("vp1","vp_id")},
   eq(attr("latax","proj_role"),lit(0.0)), eq(attr("otheraxis","proj_role"),lit(1.0)),
   nott(eq(sin_diff,lit(0.0)))]},
 "effects": [
   ["add_node_if_absent","loc","Locus",{"lid":{"__term__":lid}}],
   ["add_edge","game","has_locus","loc"],
   ["add_edge","loc","recovered_from","f"],
   ["set_attr","loc","appearance",{"__term__":attr("f","appearance")}],
   ["add_node_if_absent","clat","Coord",
     {"value":{"__term__":X},"proj_role":{"__term__":attr("latax","proj_role")}}],
   ["add_edge","clat","on","latax"],
   ["add_edge","loc","at","clat"],
   ["add_node_if_absent","cother","Coord",
     {"value":{"__term__":Y},"proj_role":{"__term__":attr("otheraxis","proj_role")}}],
   ["add_edge","cother","on","otheraxis"],
   ["add_edge","loc","at","cother"]]}
d["rules"].append(rt)

d["version"] = "1.4.0"
P.write_text(json.dumps(d, indent=1) + "\n")
print("wrote", P, "version", d["version"])
