import os, sys, random; sys.path.insert(0, os.getcwd()); random.seed(2)
import numpy as np
from substrate_rs import Substrate
import scripts.fsdd_learner_world as fl
from domains.stt_pipeline import STTPipeline, STTParams
from domains.speech_cortex import SpeechCortex
from domains.acoustic_resolution import enrich_sign_bands, enrich_sign_windows, _root
from domains.hint_grounding import onset_tilt_term
R=12
class P:
    def __init__(s,d): s._json=d
sub=Substrate(); pipe=STTPipeline(STTParams(sample_rate=8000)); pipe.attach(sub); pipe._ensure_audio_pipeline(sub)
SpeechCortex(sub,lexicon_name="stt",tick_period_ms=99999).install(); sub.set_attr(_root(sub),"resolution",R)
af=fl.gather_files(limit=None)
def clips(word, n):
    d=fl._DIGITS.index(word)
    return [f for f in af if f[1]==d][:n]
def features(path):
    s,fs=fl.load_wav(path); pipe.ingest(sub, s); sub.tick(50000)
    st=None
    for n in sub.nodes("AudioStream"): st=n
    sg=fl._collect_signs_from_stream(sub,st) if st else []
    enrich_sign_bands(sub,resolution=R,signs=sg); enrich_sign_windows(sub,resolution=R,signs=sg)
    onset=[]; wholeband=[]   # the agent's GROUNDED onset feature vs whole-word band-mean
    for g in sg:
        a=sub.node(g)["attrs"]
        try: onset.append(float(sub.evaluate(P(onset_tilt_term(R)),{"s":g})))
        except: pass
        v=[a.get(f"band{R}_{i}") for i in range(R)]
        if all(x is not None for x in v): wholeband.append(float(np.mean(v)))
    return (np.mean(onset) if onset else None, np.mean(wholeband) if wholeband else None)
def fisher(a,b):
    a,b=np.array(a),np.array(b)
    return abs(a.mean()-b.mean())/(a.std()+b.std()+1e-6)
one_on=[]; three_on=[]; one_wb=[]; three_wb=[]
for w,onl,wbl in [("one",one_on,one_wb),("three",three_on,three_wb)]:
    for path,*_ in clips(w,20):
        o,wb=features(path)
        if o is not None: onl.append(o)
        if wb is not None: (one_wb if w=="one" else three_wb).append(wb)
print("Separating 'one' from 'three':")
print(f"  whole-word band-mean (what it was stuck on):  Fisher {fisher(one_wb,three_wb):.2f}")
print(f"  GROUNDED onset-tilt (what the peer taught it): Fisher {fisher(one_on,three_on):.2f}")
print(f"    one onset-tilt mean {np.mean(one_on):+.3f} (expect low hum, negative)")
print(f"    three onset-tilt mean {np.mean(three_on):+.3f} (expect hiss, positive)")
sep=sum(1 for o in three_on if o> (np.mean(one_on)+np.mean(three_on))/2)+sum(1 for o in one_on if o<=(np.mean(one_on)+np.mean(three_on))/2)
print(f"  pairwise one-vs-three by the grounded feature: {sep}/{len(one_on)+len(three_on)} = {100*sep//(len(one_on)+len(three_on))}%")
