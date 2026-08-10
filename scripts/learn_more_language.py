import os, sys, random; sys.path.insert(0, os.getcwd()); random.seed(2)
import numpy as np
from substrate_rs import Substrate
import scripts.fsdd_learner_world as fl
from domains.stt_pipeline import STTPipeline, STTParams
from domains.speech_cortex import SpeechCortex
from domains.acoustic_resolution import enrich_sign_bands, enrich_sign_windows, _root
from domains.hint_grounding import compose_from_spec
R=12
class P:
    def __init__(s,d): s._json=d
sub=Substrate(); pipe=STTPipeline(STTParams(sample_rate=8000)); pipe.attach(sub); pipe._ensure_audio_pipeline(sub)
SpeechCortex(sub,lexicon_name="stt",tick_period_ms=99999).install(); sub.set_attr(_root(sub),"resolution",R)
af=fl.gather_files(limit=None)
def clips(word,n):
    d=fl._DIGITS.index(word); return [f for f in af if f[1]==d][:n]
def feat(path, term):
    s,fs=fl.load_wav(path); pipe.ingest(sub, s); sub.tick(50000)
    st=None
    for n in sub.nodes("AudioStream"): st=n
    sg=fl._collect_signs_from_stream(sub,st) if st else []
    enrich_sign_bands(sub,resolution=R,signs=sg); enrich_sign_windows(sub,resolution=R,signs=sg)
    onset=[]; wb=[]
    for g in sg:
        try: onset.append(float(sub.evaluate(P(term),{"s":g})))
        except: pass
        v=[sub.node(g)["attrs"].get(f"band{R}_{i}") for i in range(R)]
        if all(x is not None for x in v): wb.append(float(np.mean(v)))
    return (np.mean(onset) if onset else None, np.mean(wb) if wb else None)
def fish(a,b):
    a,b=np.array(a),np.array(b); return abs(a.mean()-b.mean())/(a.std()+b.std()+1e-6)
specs = [("nine","zero","ending_nasal"),("one","zero","ending_nasal"),
         ("two","three","onset_tilt"),("three","zero","onset_tilt"),
         ("four","five","movement"),("four","eight","onset_tilt")]
# peer said a=positive word; spec rows give (a,b,cue) — but our pair order may differ;
# use the peer's a,b directly:
peer = {("nine","zero"):("ending_nasal","nine"),("one","zero"):("ending_nasal","one"),
        ("two","three"):("onset_tilt","three"),("three","zero"):("onset_tilt","three"),
        ("four","five"):("movement","four"),("four","eight"):("onset_tilt","four")}
print(f"{'pair':>11} | cue          | whole-word | GROUNDED | learned?")
learned=0
for (X,Y),(cue,aw) in peer.items():
    term=compose_from_spec(R,cue)
    xa=[feat(p,term) for p,*_ in clips(X,16)]; ya=[feat(p,term) for p,*_ in clips(Y,16)]
    xo=[o for o,_ in xa if o is not None]; yo=[o for o,_ in ya if o is not None]
    xw=[w for _,w in xa if w is not None]; yw=[w for _,w in ya if w is not None]
    fg=fish(xo,yo); fw=fish(xw,yw)
    ok = fg>fw and fg>0.8
    learned += ok
    print(f"{X+'|'+Y:>11} | {cue:<12} |   {fw:.2f}     |  {fg:.2f}   | {'YES' if ok else 'no'}")
print(f"\nthe agent learned {learned}/6 new distinctions from the teacher (grounded features "
      f"that beat its whole-word average + separate the pair).")
