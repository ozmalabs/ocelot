import sys; sys.path.insert(0, '/home/matt/ozma/internal/research/experiments/gamma-substrate')
import numpy as np
from scripts.mine_whisper import (gather, load_wav, gammatone_env, BANDS, _PATCHES,
                                   silhouette_by_word, loso_1nn)
import math

def agent_traj_variant(x, fs, n_frames=32, log_comp=False, per_feat_norm=False,
                       global_stats=None):
    envs = [gammatone_env(x, fs, fc) for fc in BANDS]
    bc = np.array(BANDS)
    patch_bufs = []
    for name, c, sigma in _PATCHES:
        w = np.exp(-0.5*((bc-c)/sigma)**2); w = w/(w.sum()+1e-9)
        combined = np.zeros_like(envs[0])
        for bi, env in enumerate(envs): combined += w[bi]*env
        cut = 1000.0/(2*math.pi*80.0); tau = 1.0/(2*math.pi*cut)
        a = math.exp(-1.0/(tau*fs)); sm=np.empty_like(combined); acc=0.0
        for i in range(len(combined)): acc=a*acc+(1-a)*combined[i]; sm[i]=acc
        patch_bufs.append(sm)
    n_src=len(patch_bufs[0]); rows=[]
    for tf in range(n_frames):
        sp=tf*n_src/n_frames; i0=int(sp); i1=min(i0+1,n_src-1); frac=sp-i0
        rows.append([buf[i0]*(1-frac)+buf[i1]*frac for buf in patch_bufs])
    M=np.array(rows,dtype=np.float32)  # frames x patches
    if log_comp:
        # whisper-style: log10, dynamic-range floor 8 (in log units), affine
        M=np.log10(np.maximum(M,1e-10))
        M=np.maximum(M, M.max()-8.0)
        M=(M+4.0)/4.0
    v=M.flatten()
    if per_feat_norm and global_stats is not None:
        mu,sd=global_stats; v=(v-mu)/(sd+1e-9)
    nrm=np.linalg.norm(v)
    if nrm>1e-9: v=v/nrm
    return v

items=gather(3); audio=[(*load_wav(p),str(d),s) for p,d,s in items]
words=[a[2] for a in audio]; spk=[a[3] for a in audio]
for name,kw in [("baseline linear-mag",{}),
                ("+log-compression(whisper recipe)",dict(log_comp=True))]:
    X=[agent_traj_variant(x,fs,**kw) for x,fs,_,_ in audio]
    print(f"{name:42s} sil={silhouette_by_word(X,words):+.3f} LOSO={loso_1nn(X,words,spk):.3f}")
# per-feature standardisation (global mean/var) on log features
Xraw=[agent_traj_variant(x,fs,log_comp=True) for x,fs,_,_ in audio]
A=np.array(Xraw); mu=A.mean(0); sd=A.std(0)
Xn=[ (v-mu)/(sd+1e-9) for v in Xraw ]; Xn=[v/(np.linalg.norm(v)+1e-9) for v in Xn]
print(f"{'+log +per-feature standardise':42s} sil={silhouette_by_word(Xn,words):+.3f} LOSO={loso_1nn(Xn,words,spk):.3f}")
