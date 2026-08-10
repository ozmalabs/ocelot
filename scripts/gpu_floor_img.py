"""APPLES-TO-APPLES — same 4-depth 64-filter compositional sub-feature protonet, but on the STANDARD Omniglot
IMAGE set (28px binary, what the literature uses) instead of our stroke renders. Tests whether the ~91 floor
plateau was a data/render artifact or a real limit. Same eval protocol (200-char pool, 20-way 1-shot)."""
import os as _os; _os.environ["PYTORCH_CUDA_ALLOC_CONF"]="expandable_segments:True"
import os, glob, math, time, random, numpy as np, torch, torch.nn as nn, torch.nn.functional as F
from PIL import Image
DEV="cuda"; IMG="/tmp/omniglot_img"; SZ=28
BG_DRAW=12; N_EV,EV_DRAW=200,2
WAY,NS,NQ=20,5,5; EPISODES=20000; SCALE=10.0; FILT=64
CACHE="/tmp/floor_img.npz"
torch.manual_seed(0); np.random.seed(0); random.seed(0)
def load_img(path,rot=0):
    im=Image.open(path).convert("L").resize((SZ,SZ),Image.LANCZOS)
    if rot: im=im.rotate(rot)
    a=1.0-np.asarray(im,np.float32)/255.0   # stroke=1 on 0 bg
    return a
def chars(split):
    out=[]
    for al in sorted(glob.glob(f"{IMG}/images_{split}/*")):
        for c in sorted(glob.glob(al+"/*")):
            dr=sorted(glob.glob(c+"/*.png"))
            if len(dr)>=max(BG_DRAW,EV_DRAW): out.append(dr)
    return out
if os.path.exists(CACHE):
    print("load cache...",flush=True); d=np.load(CACHE); bg_small=torch.tensor(d["bg"]).float(); ev_small=torch.tensor(d["ev"]).float()
else:
    print("loading+resizing standard images (all bg + eval)...",flush=True); t0=time.time()
    rng=np.random.default_rng(1); reng=np.random.default_rng(0)
    bg=chars("background"); ev=chars("evaluation")
    ev=[ev[i] for i in reng.permutation(len(ev))[:N_EV]]
    bgL=[]
    for dr in bg:
        pick=[dr[i] for i in rng.permutation(len(dr))[:BG_DRAW]]
        base=[load_img(p,0) for p in pick]
        for rot in (0,90,180,270):
            bgL.append(np.stack(base) if rot==0 else np.stack([np.asarray(Image.fromarray(((1-b)*255).astype(np.uint8)).rotate(rot),np.float32)/255.0 for b in base]).__rsub__(1.0))
    evL=[np.stack([load_img(p) for p in [dr[i] for i in reng.permutation(len(dr))[:EV_DRAW]]]) for dr in ev]
    bg_small=torch.tensor(np.stack(bgL)).float(); ev_small=torch.tensor(np.stack(evL)).float()
    np.savez(CACHE, bg=bg_small.numpy().astype(np.float16), ev=ev_small.numpy().astype(np.float16))
    print(f"  {len(bg_small)} bg classes in {time.time()-t0:.0f}s",flush=True)
print(f"  {len(bg_small)} bg classes, {len(ev_small)} eval",flush=True)
class Floor(nn.Module):
    def __init__(self,f=64):
        super().__init__()
        def blk(i,o): return nn.Sequential(nn.Conv2d(i,o,3,padding=1),nn.BatchNorm2d(o),nn.ReLU(),nn.MaxPool2d(2))
        self.net=nn.Sequential(blk(1,f),blk(f,f),blk(f,f),blk(f,f))   # 28->14->7->3->1
    def forward(self,x): return self.net(x).flatten(1)   # UNnormalized (euclidean metric)
st=Floor(FILT).to(DEV); opt=torch.optim.AdamW(st.parameters(),lr=1e-3,weight_decay=1e-4)
def evaluate():
    st.eval()
    with torch.no_grad():
        S=st(ev_small[:,0].unsqueeze(1).to(DEV)); Q=st(ev_small[:,1].unsqueeze(1).to(DEV))
    r=np.random.default_rng(123); cor=0
    for _ in range(3000):
        cl=r.choice(len(ev_small),20,replace=False); qi=int(r.integers(20)); cor+=int(((S[cl]-Q[cl[qi]])**2).sum(1).argmin().item()==qi)
    st.train(); return cor/30.0
print("train...",flush=True); best=0.0
for ep in range(1,EPISODES+1):
    lr=1e-3*(0.05+0.95*0.5*(1+math.cos(math.pi*ep/EPISODES)))
    for g in opt.param_groups: g["lr"]=lr
    cls=np.random.choice(len(bg_small),WAY,replace=False); xs=[]
    for c in cls:
        idx=np.random.choice(BG_DRAW,NS+NQ,replace=False); xs.append(bg_small[c,idx])
    x=torch.cat(xs,0).unsqueeze(1).to(DEV)
    emb=st(x).reshape(WAY,NS+NQ,-1); proto=emb[:,:NS].mean(1)
    q=emb[:,NS:].reshape(WAY*NQ,-1); ql=torch.arange(WAY,device=DEV).repeat_interleave(NQ)
    d2=((q[:,None,:]-proto[None,:,:])**2).sum(-1); loss=F.cross_entropy(-d2,ql)
    opt.zero_grad(); loss.backward(); opt.step()
    if ep%2000==0 or ep==EPISODES:
        a=evaluate(); best=max(best,a); print(f"  ep {ep:5d} loss {loss.item():.3f} one-shot {a:.1f} (best {best:.1f})",flush=True)
sp=sum(p.numel() for p in st.parameters())
print(f"\nDONE  IMAGE-set EUCLIDEAN protonet (4-depth {FILT}f) = {best:.1f}% / {sp/1e3:.0f}K params  (stroke-render was ~91; Gemma 96.3/167.6M)")
