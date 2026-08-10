import os, sys; sys.path.insert(0, os.getcwd())
import numpy as np
from substrate_rs import Substrate
import scripts.fsdd_learner_world as fl
from domains.stt_pipeline import STTPipeline, STTParams
from domains.speech_cortex import SpeechCortex
from domains.acoustic_resolution import enrich_sign_bands, _root
R=12
sub=Substrate(); pipe=STTPipeline(STTParams(sample_rate=8000)); pipe.attach(sub); pipe._ensure_audio_pipeline(sub)
SpeechCortex(sub,lexicon_name="stt",tick_period_ms=99999).install(); sub.set_attr(_root(sub),"resolution",R)
af=fl.gather_files(limit=None)
def first_ear(s):           # the gammatone: whole-word band-mean (what hit the wall)
    pipe.ingest(sub,s); sub.tick(50000); st=None
    for n in sub.nodes("AudioStream"): st=n
    sg=fl._collect_signs_from_stream(sub,st) if st else []
    enrich_sign_bands(sub,resolution=R,signs=sg)
    vs=[np.mean([sub.node(g)["attrs"].get(f"band{R}_{i}",0) for i in range(R)]) for g in sg]
    return np.mean(vs) if vs else np.nan
def second_ear(s,fs=8000):  # a frequency-SHARP ear: F2 formant from a 4096-pt FFT, mid window
    seg=s[int(len(s)*0.3):int(len(s)*0.7)]
    if len(seg)<64: return np.nan
    mag=np.abs(np.fft.rfft(seg*np.hanning(len(seg)),n=4096)); fr=np.fft.rfftfreq(4096,1/fs)
    m=(fr>=900)&(fr<2500)
    return fr[m][np.argmax(mag[m])] if m.any() else np.nan
def fish(a,b):
    a=np.array([x for x in a if x==x]); b=np.array([x for x in b if x==x])
    return abs(a.mean()-b.mean())/(a.std()+b.std()+1e-6) if len(a)>1 and len(b)>1 else 0.0
def vals(word,n):
    d=fl._DIGITS.index(word); e1=[];e2=[]
    for path,*_ in [f for f in af if f[1]==d][:n]:
        s,fs=fl.load_wav(path); e1.append(first_ear(s)); e2.append(second_ear(s,fs))
    return e1,e2
pairs=[("two","three"),("three","zero"),("nine","zero"),("one","zero"),("four","five")]
cache={}
for X,Y in pairs:
    for w in (X,Y):
        if w not in cache: cache[w]=vals(w,14)
print(f"{'pair':>11} | gammatone ear | SHARP 2nd ear (F2) | wall blocked?")
for X,Y in pairs:
    f1=fish(cache[X][0],cache[Y][0]); f2=fish(cache[X][1],cache[Y][1])
    blocked = f1<0.8 and f2>f1
    print(f"{X+'|'+Y:>11} |     {f1:.2f}      |       {f2:.2f}        | {'YES -> 2nd ear opens it' if blocked else ('both fine' if f1>=0.8 else 'still hard')}")
