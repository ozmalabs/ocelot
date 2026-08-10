import sys; sys.path.insert(0,'/home/matt/ozma/internal/research/experiments/gamma-substrate')
import numpy as np, math
from scripts.mine_whisper import gather, load_wav, gammatone_env, BANDS, _PATCHES

def traj_matrix(x,fs,n_frames=32,log_comp=False):
    envs=[gammatone_env(x,fs,fc) for fc in BANDS]; bc=np.array(BANDS); pb=[]
    for name,c,sigma in _PATCHES:
        w=np.exp(-0.5*((bc-c)/sigma)**2); w=w/(w.sum()+1e-9)
        comb=np.zeros_like(envs[0])
        for bi,e in enumerate(envs): comb+=w[bi]*e
        cut=1000.0/(2*math.pi*80.0); tau=1.0/(2*math.pi*cut); a=math.exp(-1/(tau*fs))
        sm=np.empty_like(comb); acc=0.0
        for i in range(len(comb)): acc=a*acc+(1-a)*comb[i]; sm[i]=acc
        pb.append(sm)
    ns=len(pb[0]); rows=[]
    for tf in range(n_frames):
        sp=tf*ns/n_frames; i0=int(sp); i1=min(i0+1,ns-1); fr=sp-i0
        rows.append([b[i0]*(1-fr)+b[i1]*fr for b in pb])
    M=np.array(rows,dtype=np.float32)
    if log_comp:
        M=np.log10(np.maximum(M,1e-10)); M=np.maximum(M,M.max()-8.0); M=(M+4.0)/4.0
    n=np.linalg.norm(M)
    if n>1e-9: M=M/n
    return M  # frames x patches, globally L2

def dtw(A,B,band=8):
    nf=A.shape[0]; INF=1e18
    prev=[INF]*(nf+1); prev[0]=0.0
    for i in range(1,nf+1):
        cur=[INF]*(nf+1); jl=max(1,i-band); jh=min(nf,i+band)
        for j in range(jl,jh+1):
            d=np.linalg.norm(A[i-1]-B[j-1])
            cur[j]=d+min(prev[j],cur[j-1],prev[j-1])
        prev=cur
    return prev[nf]/nf

items=gather(3); audio=[(*load_wav(p),str(d),s) for p,d,s in items]
words=np.array([a[2] for a in audio]); spk=np.array([a[3] for a in audio])
for tag,lc in [("DTW linear-mag",False),("DTW +log-compression",True)]:
    Ms=[traj_matrix(x,fs,log_comp=lc) for x,fs,_,_ in audio]
    corr=tot=0
    for held in set(spk):
        te=np.where(spk==held)[0]; tr=np.where(spk!=held)[0]
        for i in te:
            best=1e18; bw=None
            for j in tr:
                d=dtw(Ms[i],Ms[j])
                if d<best: best=d; bw=words[j]
            corr+=int(bw==words[i]); tot+=1
    print(f"{tag:28s} LOSO-DTW-1NN={corr/tot:.3f}")
