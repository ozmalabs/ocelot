import os,sys,wave,random; sys.path.insert(0,os.getcwd()); random.seed(2)
import numpy as np
from domains.stt_pipeline import DEFAULT_BANDS
from domains.runtime_design import agent_specify_frontend
spec=agent_specify_frontend(DEFAULT_BANDS, 25)
print("AGENT'S PERCEPTION REDESIGN (its own reasoning, one layer down):")
print("  observation:", spec["observation"])
print("  redesign:", spec["redesign"]); print()
SC="/tmp/sc"
def load(p):
    w=wave.open(p); r=(np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768.0)
    return (r[::2] if w.getframerate()==16000 else r)
def sharp_formants(x):
    # SHARP front-end proxy: framed FFT power spectrum (128 bins ~31Hz, vs 25 patches)
    fr=200; hop=100; S=np.zeros(129)
    n=0
    for i in range(0,len(x)-fr,hop):
        w=x[i:i+fr]*np.hamming(fr)
        S+=np.abs(np.fft.rfft(w,256))**2; n+=1
    if n==0: return None
    S/=n
    f1=8+int(np.argmax(S[8:32]))      # 250-1000 Hz
    f2=32+int(np.argmax(S[32:80]))    # 1000-2500 Hz
    return np.array([f1,f2,(f2+1)/(f1+1)],float)
words=[w for w in ["yes","no","up","down"] if os.path.isdir(f"{SC}/{w}")]
data={w:[(f"{SC}/{w}/{f}",f.split("_")[0]) for f in sorted(os.listdir(f"{SC}/{w}")) if f.endswith(".wav")] for w in words}
tsp=set()
for w in words:
    sp=sorted({s for _,s in data[w]}); tsp|=set(sp[::5])
tr=[(p,w) for w in words for p,s in data[w] if s not in tsp]
te=[(p,w) for w in words for p,s in data[w] if s in tsp]
random.shuffle(tr); random.shuffle(te); tr,te=tr[:120],te[:48]
C={}; A=[]
for p,w in tr:
    f=sharp_formants(load(p))
    if f is not None: C.setdefault(w,[]).append(f); A.append(f)
cen={w:np.mean(v,0) for w,v in C.items()}; std=np.std(A,0)+1e-6
c=n=0
for p,w in te:
    f=sharp_formants(load(p))
    if f is None: continue
    n+=1
    if min(cen,key=lambda x:np.sum(((f-cen[x])/std)**2))==w: c+=1
print(f"SHARP-front-end formant recognition, held-out speakers: {c}/{n} = {100*c/n:.0f}%  (vs 40% with the 25-patch front-end)")
