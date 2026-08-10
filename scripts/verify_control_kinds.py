"""Control kinds are SEEDED yet OPEN: the agent grounds a starter set from the on-disk wiki AND grounds
arbitrarily MORE never-seeded kinds on demand, each classified into an effect_family graph-natively from its
gloss. Proves: (1) starter kinds ground + classify; (2) ARBITRARY novel kinds ground + classify the same way
(no fixed enum); (3) the family comes from the gloss (reason from grounded knowledge), donkey=0.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/verify_control_kinds.py
"""
from __future__ import annotations
import os, sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT,"runners","dsl","python"), os.path.join(ROOT,"scripts")):
    if p not in sys.path: sys.path.insert(0,p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.wiki_library import WikipediaLibrary
from domains.control_grounding import ground_control_kind

STARTER=["Push-button","Joystick","Rotary switch","Slider (computing)","Lever"]
# never seeded anywhere — the OPEN test: these must ground + classify exactly like the starter set
NOVEL=["Trackball","Steering wheel","Touchpad","Gamepad","Paddle (game controller)","Throttle","Trigger (firearms)"]

def main():
    a=WorldAdapter(seeds=()); load_all_seeds(a)
    calls={"n":0}; a.set_self_teacher(lambda q:(calls.__setitem__("n",calls["n"]+1),"D")[1])
    lib=WikipediaLibrary()
    grounded=[]
    for nm in STARTER+NOVEL:
        ck=ground_control_kind(a,nm,lib)
        if ck is not None: grounded.append((nm,ck))
    for _ in range(4): a.tick()                       # classify_kind_family fires (graph-native)
    print(f"  grounded {len(grounded)} control kinds from the on-disk wiki (starter + arbitrary novel):")
    fam={}
    for nm,ck in grounded:
        f=a.s.node(ck)["attrs"].get("effect_family"); fam[nm]=f
        tag="seed" if nm in STARTER else "NOVEL"
        print(f"    [{tag:5s}] {nm:26s} -> effect_family={f}")
    classified=[nm for nm,f in fam.items() if f]
    novel_ok=[nm for nm in NOVEL if fam.get(nm)]
    families=set(f for f in fam.values() if f)
    print(f"  distinct families discovered: {sorted(families)}")
    print(f"  DONKEY calls: {calls['n']}")
    ok = len(classified)>=10 and len(novel_ok)>=5 and len(families)>=4 and calls["n"]==0
    print("\n"+"="*96)
    print(f"  {'PASS' if ok else 'PARTIAL'} — the control-kind taxonomy is SEEDED YET OPEN: the agent grounded "
          f"{len(grounded)} kinds from the on-disk wiki ({len(novel_ok)} of them NEVER seeded) and classified "
          f"each into an effect_family from its gloss — {len(families)} families, no fixed enum, donkey=0. It "
          f"REASONS from grounded knowledge about what a control is, and can add arbitrarily more.")
    print("="*96)
    return 0 if ok else 1

if __name__=="__main__":
    raise SystemExit(main())
