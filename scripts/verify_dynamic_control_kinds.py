"""Control types are DYNAMIC and graph-native: the agent RECOGNISES a control from a grounded (wiki) prior when
it can, and MINTS ITS OWN ControlKind from OBSERVATION when it can't (a novel/alien control with no article),
then ADJUSTS that self-minted type as it observes more. No LLM: wiki is the non-LLM prior, observation is the
non-LLM minter, recognise/mint/refine are all graph rules.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/verify_dynamic_control_kinds.py
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

def run(a,n=5):
    for _ in range(n): a.tick()

def main():
    a=WorldAdapter(seeds=()); load_all_seeds(a)
    calls={"n":0}; a.set_self_teacher(lambda q:(calls.__setitem__("n",calls["n"]+1),"D")[1])
    lib=WikipediaLibrary()
    g=a.s.add_node("WorldInstance",{"world_type":"Game"})

    # KNOWN control: its kind grounds from wiki (the prior) -> recognise, no minting.
    ground_control_kind(a,"Push-button",lib)                      # mints ControlKind Push-button from wiki
    c_known=a.s.add_node("Control",{"name":"button_A","kind_name":"Push-button","wiki_grounded":1.0})
    a.inner.add_edge_unchecked(g,"has_control",c_known)

    # NOVEL control: NO wiki article -> the agent must MINT ITS OWN type from observation.
    print("  grounding novel control 'Zorblatt' from wiki:", ground_control_kind(a,"Zorblatt",lib), "(None = no prior)")
    c_novel=a.s.add_node("Control",{"name":"Zorblatt","kind_name":"Zorblatt","wiki_grounded":0.0,
                                    "obs_family":"continuous_rotation","obs_param":20.0,"obs_set":1.0,"obs_seq":1.0})
    a.inner.add_edge_unchecked(g,"has_control",c_novel)
    run(a)                                                        # recognise (known) + mint_own_kind (novel)

    def kind_of(c):
        ks=list(a.inner.neighbours(c,"is_kind"));  return a.s.node(ks[0])["attrs"] if ks else None
    k_known=kind_of(c_known); k_novel=kind_of(c_novel)
    minted_rep0 = k_novel.get("rep_param") if k_novel else None

    # SECOND observation of the novel control -> the self-minted type ADJUSTS (EMA toward 28).
    a.s.set_attr(c_novel,"obs_param",28.0); a.s.set_attr(c_novel,"obs_seq",2.0)
    run(a)
    k_novel2=kind_of(c_novel); minted_rep1=k_novel2.get("rep_param") if k_novel2 else None

    recognised = bool(k_known) and k_known.get("name")=="Push-button" and k_known.get("source")!="observation"
    minted_own = bool(k_novel) and k_novel.get("name")=="Zorblatt" and k_novel.get("source")=="observation" \
                 and k_novel.get("learned")==1.0 and k_novel.get("effect_family")=="continuous_rotation"
    adjusted = minted_rep0==20.0 and minted_rep1 is not None and 20.0 < minted_rep1 <= 28.0
    print(f"  KNOWN control 'button_A': is_kind -> {k_known.get('name') if k_known else None} "
          f"(source={k_known.get('source') if k_known else None})  recognised-from-prior={recognised}")
    print(f"  NOVEL control 'Zorblatt': MINTED its OWN kind -> name={k_novel.get('name') if k_novel else None} "
          f"family={k_novel.get('effect_family') if k_novel else None} learned={k_novel.get('learned') if k_novel else None} "
          f"source={k_novel.get('source') if k_novel else None}")
    print(f"  self-minted type ADJUSTED: rep_param {minted_rep0} -> {minted_rep1} (EMA toward the new observation 28)")
    print(f"  DONKEY calls: {calls['n']}")
    ok = recognised and minted_own and adjusted and calls["n"]==0
    print("\n"+"="*96)
    print(f"  {'PASS' if ok else 'PARTIAL'} — control types are DYNAMIC + graph-native: a known control is "
          f"recognised from its wiki PRIOR, a NOVEL control (no article) MINTS ITS OWN ControlKind from "
          f"observation, and that self-minted type ADJUSTS as more is observed — recognise/mint/refine all "
          f"graph rules, donkey=0, no LLM. The agent authors and tunes its own control taxonomy.")
    print("="*96)
    return 0 if ok else 1

if __name__=="__main__":
    raise SystemExit(main())
