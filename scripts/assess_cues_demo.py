import os, sys, random; sys.path.insert(0, os.getcwd()); random.seed(2)
import numpy as np
from substrate_rs import Substrate
import scripts.fsdd_learner_world as fl
from domains.stt_pipeline import STTPipeline, STTParams
from domains.speech_cortex import SpeechCortex
from domains.acoustic_resolution import enrich_sign_bands, enrich_sign_windows, _root
from domains.hint_grounding import compose_from_spec, CUE_MENU
R=12
class P:
    def __init__(s,d): s._json=d
sub=Substrate(); pipe=STTPipeline(STTParams(sample_rate=8000)); pipe.attach(sub); pipe._ensure_audio_pipeline(sub)
SpeechCortex(sub,lexicon_name="stt",tick_period_ms=99999).install(); sub.set_attr(_root(sub),"resolution",R)
af=fl.gather_files(limit=None)
terms={c:compose_from_spec(R,c) for c in CUE_MENU}
def clipvals(word,n):
    d=fl._DIGITS.index(word); rows=[]
    for path,*_ in [f for f in af if f[1]==d][:n]:
        s,fs=fl.load_wav(path); pipe.ingest(sub,s); sub.tick(50000)
        st=None
        for x in sub.nodes("AudioStream"): st=x
        sg=fl._collect_signs_from_stream(sub,st) if st else []
        enrich_sign_bands(sub,resolution=R,signs=sg); enrich_sign_windows(sub,resolution=R,signs=sg)
        row={}
        for c,t in terms.items():
            vs=[]
            for g in sg:
                try: vs.append(float(sub.evaluate(P(t),{"s":g})))
                except: pass
            row[c]=np.mean(vs) if vs else np.nan
        wb=[]
        for g in sg:
            v=[sub.node(g)["attrs"].get(f"band{R}_{i}") for i in range(R)]
            if all(x is not None for x in v): wb.append(np.mean(v))
        row["_whole"]=np.mean(wb) if wb else np.nan
        rows.append(row)
    return rows
def fish(a,b):
    a=np.array([x for x in a if x==x]); b=np.array([x for x in b if x==x])
    if len(a)<2 or len(b)<2: return 0.0
    return abs(a.mean()-b.mean())/(a.std()+b.std()+1e-6)
words=set(); pairs=[("nine","zero"),("one","zero"),("two","three"),("three","zero"),("four","five"),("four","eight")]
for X,Y in pairs: words|={X,Y}
cache={w:clipvals(w,14) for w in words}
print(f"{'pair':>11} | best cue it found        | its Fisher | whole-word | learned?")
learned=0
for X,Y in pairs:
    base=fish([r['_whole'] for r in cache[X]],[r['_whole'] for r in cache[Y]])
    scored=[(fish([r[c] for r in cache[X]],[r[c] for r in cache[Y]]),c) for c in CUE_MENU]
    bf,bc=max(scored)
    ok = bf>base and bf>0.8
    learned+=ok
    print(f"{X+'|'+Y:>11} | {bc:<22} |   {bf:.2f}    |   {base:.2f}    | {'YES' if ok else 'no'}")
print(f"\nBy ASSESSING the menu itself, the agent found a separating cue for {learned}/6 pairs "
      f"(vs 1/6 when it took the peer's single guess).")
