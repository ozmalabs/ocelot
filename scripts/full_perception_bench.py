import os, sys, random; sys.path.insert(0, os.getcwd()); random.seed(1)
import numpy as np
from substrate_rs import Substrate
import scripts.fsdd_learner_world as fl
from domains.stt_pipeline import STTPipeline, STTParams
from domains.speech_cortex import SpeechCortex
from domains.acoustic_resolution import _root
sub=Substrate(); pipe=STTPipeline(STTParams(sample_rate=8000)); pipe.attach(sub); pipe._ensure_audio_pipeline(sub)
SpeechCortex(sub,lexicon_name="stt",tick_period_ms=99999).install(); sub.set_attr(_root(sub),"resolution",12)
af=fl.gather_files(limit=None)
def nrm(v): n=np.linalg.norm(v); return v/n if n>0 else v
def feats(path):
    s,fs=fl.load_wav(path); pipe.ingest(sub,s); sub.tick(50000); st=None
    for n in sub.nodes("AudioStream"): st=n
    sg=fl._collect_signs_from_stream(sub,st) if st else []
    g=[];f=[]
    for sid in sg:
        a=sub.node(sid)["attrs"]; t=a.get("trajectory"); ft=a.get("fft_trajectory")
        if t: g.append(np.array(t,dtype=float))
        if ft: f.append(np.array(ft,dtype=float))
    if not g: return None
    return nrm(np.mean(g,0)), (nrm(np.mean(f,0)) if f else np.zeros(1024))
tr=[]; te=[]
for path,digit,sp,idx in af:
    r=feats(path)
    if r is None: continue
    (te if sp=='jackson' else tr).append((digit,r[0],r[1]))
def knn(q_g,q_f,use_fft,k=5):
    sims=[]
    for d,g,f in tr:
        s=float(np.dot(q_g,g))
        if use_fft: s+=float(np.dot(q_f,f))
        sims.append((s,d))
    sims.sort(reverse=True)
    from collections import Counter
    return Counter(d for _,d in sims[:k]).most_common(1)[0][0]
for use_fft,label in [(False,"gammatone ear only      "),(True,"BOTH ears (gammatone+FFT)")]:
    ok=sum(knn(g,f,use_fft)==d for d,g,f in te)
    print(f"  kNN  {label}: {100*ok/len(te):.0f}%  ({ok}/{len(te)} held-out, 10-way, chance 10%)")
