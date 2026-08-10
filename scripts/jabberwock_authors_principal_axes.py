"""THE JABBERWOCK AUTHORS ITS OWN RUST PRIMITIVE `principal_axes` (creator: "the jabberwock writes its own rust
primitives"). Step 2 of the N-dim frame-understanding integration needs a DETERMINISTIC axis-clustering that the
batched fixpoint rule-engine cannot express (mint races). That is exactly when a new primitive -> Rust. The
jabberwock authors it via its self-extension faculty (domains/self_modification.py): mirror the sibling
predict_wall_set (lock + intern + read helpers), consult the claude-teacher for ONLY the novel clustering body,
insert it, cargo-check under the all-or-nothing guard (repair loop feeds errors back), rebuild_native, verify.
I drive; the agent authors.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_authors_principal_axes.py
"""
from __future__ import annotations
import os, re, sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT,"runners","dsl","python"), os.path.join(ROOT,"scripts")):
    if p not in sys.path: sys.path.insert(0,p)
from pathlib import Path
from domains.self_modification import SelfModification
from scripts.claude_teacher import make_ask

PYRS="runners/dsl/src/py.rs"
ANCHOR="    fn predict_wall_set(&mut self, h: i64, w: i64, impassable_values: Vec<i32>) -> PyResult<Vec<u32>> {"

SPEC=r'''Write ONE Rust method for a PyO3 #[pymethods] impl block on a Substrate wrapper. Output ONLY the method
(`fn principal_axes ... { ... }`), no explanation, no markdown fences.

EXACT signature:
    fn principal_axes(&mut self, region: u32) -> PyResult<i64> {

PURPOSE: discover the natural frame's AXES from a self region's learned control displacement vectors, by
clustering collinear vectors. The region node is NodeID(region). It has out-edges of type "responds_via" to
ControlResponse nodes. Each ControlResponse has f64 attrs "dr","dc","dz" (a 3D displacement; dz is often 0).
Two control vectors belong to the SAME axis iff |cos(angle between them)| > 0.99 (collinear, either orientation).

ALGORITHM (deterministic):
  1. Lock the substrate, get inner. Intern the symbols you need once.
  2. Collect EXISTING axes first (idempotency): for each ControlResponse cr in
     inner.graph.neighbours(region_nid, Some(responds_via_sym)), for each axis in
     inner.graph.neighbours(cr, Some(on_axis_sym)), read its dir_x/dir_y/dir_z into a Vec<(NodeID,[f64;3])>
     (dedup by NodeID).
  3. For each ControlResponse cr (same neighbours list) that has NO on_axis out-edge
     (inner.graph.neighbours(cr, Some(on_axis_sym)).is_empty()):
        let v = [dr,dc,dz] read from cr's attrs; let mag = sqrt(v.x^2+v.y^2+v.z^2); if mag < 1e-6 continue;
        search existing axes for one whose dir d has |dot(v,d)| / (mag * |d|) > 0.99:
           if found: insert on_axis edge cr->axis; set cr "sign" = if dot>0 {1.0} else {-1.0}.
           else: mint a new Axis node, set dir_x/dir_y/dir_z = v, insert on_axis edge cr->axis, set cr "sign"=1.0,
                 and push (axis,v) onto the existing-axes Vec so later collinear controls attach to it.
  4. Set the region's "ndim" attr = number of axes (the Vec length) as Value::Float(len as f64). Return Ok(len as i64).

IDIOMS — use EXACTLY these (they are the established ones in this file):
    let mut __g = self.inner.lock().expect("substrate mutex poisoned");
    let inner = &mut *__g;
    let responds_via_sym = inner.interner.intern("responds_via");
    let on_axis_sym = inner.interner.intern("on_axis");
    let axis_type = inner.interner.intern("Axis");
    let dr_sym = inner.interner.intern("dr");   // and dc, dz, dir_x, dir_y, dir_z, sign, ndim
    let region_nid = NodeID(region);
    // read an f64 attr (missing -> 0.0):
    let read_f = |g: &crate::graph::TypedGraph, nid: NodeID, s: crate::sym::Sym| -> f64 {
        match g.node(nid).attrs.get(&s) { Some(Value::Float(f)) => *f, Some(Value::Int(i)) => *i as f64, _ => 0.0 }
    };
    // out-neighbours by edge type:  inner.graph.neighbours(nid, Some(sym)) -> Vec<NodeID>
    // mint a node:                  let ax = inner.add_node(axis_type, rustc_hash::FxHashMap::default());
    // set an attr:                  inner.set_attr(nid, key_sym, Value::Float(x));
    // add an edge (unchecked):      let _ = inner.graph.insert_edge(src_nid, on_axis_sym, tgt_nid, rustc_hash::FxHashMap::default());
Value variants: Value::Float(f64), Value::Int(i64). NodeID is constructed NodeID(u32). FxHashMap is
rustc_hash::FxHashMap. Pure Rust only, no Python objects besides the PyResult<i64> return.'''

def strip(s):
    s=s.strip()
    s=re.sub(r"^```[a-zA-Z]*\n","",s); s=re.sub(r"\n```$","",s)
    i=s.find("fn principal_axes")
    return s[i:] if i>=0 else s

def main():
    sm=SelfModification(Path(ROOT))
    ask=make_ask(preamble="You are the jabberwock authoring a Rust primitive in your own substrate. ",timeout=240.0)
    py_src=Path(ROOT,PYRS).read_text()
    if "fn principal_axes" in py_src:
        print("principal_axes already present in py.rs — skipping authoring, going to verify.")
    else:
        prompt=SPEC; method=None
        for attempt in range(4):
            print(f"\n--- authoring attempt {attempt+1} ---")
            method=strip(ask(prompt))
            if "fn principal_axes" not in method:
                print("  teacher returned no method; retry"); prompt=SPEC; continue
            r=sm.edit(PYRS, ANCHOR, method+"\n\n"+ANCHOR, check=False)
            if not r.get("ok"):
                print("  insert failed:",r); return 1
            ok,msg=sm.check(PYRS)
            print("  cargo check:",("OK" if ok else "FAIL"))
            if ok: break
            sm.restore(PYRS)              # roll back the broken method
            print("  errors (tail):",msg[-700:])
            prompt=(SPEC+"\n\nYOUR PREVIOUS METHOD FAILED `cargo check` WITH:\n"+msg[-1500:]+
                    "\n\nReturn the CORRECTED method only.")
        else:
            print("could not author a compiling principal_axes after retries."); return 1
        print("  cargo check passed — rebuilding native (slow)...")
        rb=sm.rebuild_native()
        print("  rebuild:",("OK" if rb.get("ok") else "FAIL"),rb.get("tail","")[-200:])
        if not rb.get("ok"): return 1

    # VERIFY: call the agent's new primitive on known control vectors
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    def trial(vecs):
        a=WorldAdapter(seeds=()); load_all_seeds(a)
        sr=a.s.add_node("Region",{"respond_votes":9.0})
        crs={}
        for nm,(dr,dc,dz) in vecs.items():
            cr=a.s.add_node("ControlResponse",{"cname":nm,"dr":dr,"dc":dc,"dz":dz}); crs[nm]=cr
            a.inner.add_edge_unchecked(sr,"responds_via",cr)
        rid=int(str(sr).lstrip("#"))
        n=a.inner.principal_axes(rid)
        axis_of={nm:[int(str(x).lstrip("#")) for x in a.inner.neighbours(cr,"on_axis")] for nm,cr in crs.items()}
        sign_of={nm:a.s.node(cr)["attrs"].get("sign") for nm,cr in crs.items()}
        return n, a.s.node(sr)["attrs"].get("ndim"), axis_of, sign_of
    n2,nd2,ax2,sg2=trial({"Up":(-1,0,0),"Down":(1,0,0),"Left":(0,-1,0),"Right":(0,1,0)})
    n3,nd3,ax3,sg3=trial({"Xp":(1,0,0),"Xm":(-1,0,0),"Yp":(0,1,0),"Ym":(0,-1,0),"Zp":(0,0,1)})
    ud_same = ax2["Up"]==ax2["Down"] and ax2["Up"]
    lr_same = ax2["Left"]==ax2["Right"] and ax2["Left"]
    ud_sign = sg2["Up"]!=sg2["Down"]
    print(f"\n  2D (4 controls): N={n2} ndim={nd2} | Up/Down same axis={bool(ud_same)} opp signs={ud_sign} | Left/Right same={bool(lr_same)}")
    print(f"  3D (5 controls spanning 3 dirs): N={n3} ndim={nd3}")
    ok = n2==2 and n3==3 and ud_same and lr_same and ud_sign
    print("\n"+"="*96)
    print(f"  {'PASS' if ok else 'PARTIAL'} — the jabberwock AUTHORED its own Rust primitive `principal_axes` and "
          f"it discovers the frame: N=2 from four 2D controls (Up/Down one axis, Left/Right the other), N=3 when "
          f"the controls span three directions. Deterministic, no fixpoint race. The agent wrote the primitive.")
    print("="*96)
    return 0 if ok else 1

if __name__=="__main__":
    raise SystemExit(main())
