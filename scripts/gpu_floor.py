"""THE FLOOR (v2) — directly-trained compositional sub-feature net, ALL 964 background chars, thicker render,
disk-cached. Target >=95 one-shot at ~100x fewer params than the Gemma teacher (96.3% / 167.6M)."""
import os as _os; _os.environ["PYTORCH_CUDA_ALLOC_CONF"]="expandable_segments:True"
import os, glob, math, time, random, numpy as np, torch, torch.nn as nn, torch.nn.functional as F
from PIL import Image
DEV="cuda"; OMNI="/tmp/omniglot"; SMALL=48; TH=2
BG_DRAW=12; N_EV,EV_DRAW=200,2
WAY,NS,NQ=20,5,5; EPISODES=15000; SCALE=10.0; FILT=128
CACHE="/tmp/floor_render.npz"
torch.manual_seed(0); np.random.seed(0); random.seed(0)
def load_strokes(p):
    st,cur=[],[]
    for line in open(p):
        s=line.strip()
        if not s or s=="START": continue
        if s=="BREAK":
            if cur: st.append(np.asarray(cur,float)); cur=[]
            continue
        q=s.split(",")
        if len(q)>=2: cur.append((float(q[0]),float(q[1])))
    if cur: st.append(np.asarray(cur,float))
    return [s for s in st if len(s)>=1]
def render_small(path,rot=0):
    strokes=load_strokes(path); allp=np.concatenate([s for s in strokes if len(s)],0) if strokes else np.zeros((0,2))
    a=np.zeros((SMALL,SMALL),np.uint8)
    if len(allp):
        mn,mx=allp.min(0),allp.max(0); span=np.maximum(mx-mn,1e-6)
        for s in strokes:
            qq=(s-mn)/span*(SMALL-2*TH-2)+TH+1
            for i in range(len(qq)-1):
                for t in np.linspace(0,1,30):
                    x,y=(qq[i]*(1-t)+qq[i+1]*t).astype(int); a[max(y-TH,0):y+TH+1,max(x-TH,0):x+TH+1]=255
    im=Image.fromarray(a)
    if rot: im=im.rotate(rot)
    return np.asarray(im,np.float32)/255.0
def chars(split):
    d=f"{OMNI}/strokes_{split}"; out=[]
    for al in sorted(os.listdir(d)):
        ad=os.path.join(d,al)
        if not os.path.isdir(ad): continue
        for c in sorted(os.listdir(ad)):
            dr=sorted(glob.glob(os.path.join(ad,c)+"/*.txt"))
            if len(dr)>=max(BG_DRAW,EV_DRAW): out.append(dr)
    return out
if os.path.exists(CACHE):
    print("loading render cache...",flush=True); d=np.load(CACHE)
    bg_small=torch.tensor(d["bg"]).float(); ev_small=torch.tensor(d["ev"]).float()
else:
    print("render+cache ALL bg chars...",flush=True); t0=time.time()
    rng=np.random.default_rng(1); reng=np.random.default_rng(0)
    bg=chars("background"); ev=chars("evaluation")
    ev=[ev[i] for i in reng.permutation(len(ev))[:N_EV]]
    bgL=[]
    for dr in bg:
        pick=[dr[i] for i in rng.permutation(len(dr))[:BG_DRAW]]
        base=[render_small(p,0) for p in pick]
        for rot in (0,90,180,270):
            bgL.append(np.stack([np.asarray(Image.fromarray((b*255).astype(np.uint8)).rotate(rot),np.float32)/255.0 for b in base]) if rot else np.stack(base))
    evL=[np.stack([render_small(p) for p in [dr[i] for i in reng.permutation(len(dr))[:EV_DRAW]]]) for dr in ev]
    bg_small=torch.tensor(np.stack(bgL)).float(); ev_small=torch.tensor(np.stack(evL)).float()
    np.savez(CACHE, bg=bg_small.numpy().astype(np.float16), ev=ev_small.numpy().astype(np.float16))
    print(f"  rendered {len(bg_small)} classes in {time.time()-t0:.0f}s",flush=True)
print(f"  {len(bg_small)} bg classes, {len(ev_small)} eval",flush=True)
class Floor(nn.Module):
    def __init__(self,f=64):
        super().__init__()
        def blk(i,o): return nn.Sequential(nn.Conv2d(i,o,3,padding=1),nn.BatchNorm2d(o),nn.ReLU(),nn.MaxPool2d(2))
        self.net=nn.Sequential(blk(1,f),blk(f,f),blk(f,f),blk(f,f),blk(f,f))
    def forward(self,x): return F.normalize(self.net(x).flatten(1),dim=1)
st=Floor(FILT).to(DEV); opt=torch.optim.AdamW(st.parameters(),lr=1e-3,weight_decay=1e-4)
def evaluate():
    st.eval()
    with torch.no_grad():
        S=st(ev_small[:,0].unsqueeze(1).to(DEV)); Q=st(ev_small[:,1].unsqueeze(1).to(DEV))
    r=np.random.default_rng(123); cor=0
    for _ in range(3000):
        cl=r.choice(len(ev_small),20,replace=False); qi=int(r.integers(20)); cor+=int((S[cl]@Q[cl[qi]]).argmax().item()==qi)
    st.train(); return cor/30.0
print("train...",flush=True); best=0.0
for ep in range(1,EPISODES+1):
    lr=1e-3*(0.05+0.95*0.5*(1+math.cos(math.pi*ep/EPISODES)))
    for g in opt.param_groups: g["lr"]=lr
    cls=np.random.choice(len(bg_small),WAY,replace=False); xs=[]
    for c in cls:
        idx=np.random.choice(BG_DRAW,NS+NQ,replace=False); xs.append(bg_small[c,idx])
    x=torch.cat(xs,0).unsqueeze(1).to(DEV)
    emb=st(x).reshape(WAY,NS+NQ,-1); proto=F.normalize(emb[:,:NS].mean(1),dim=1)
    q=emb[:,NS:].reshape(WAY*NQ,-1); ql=torch.arange(WAY,device=DEV).repeat_interleave(NQ)
    loss=F.cross_entropy(SCALE*(q@proto.t()),ql)
    opt.zero_grad(); loss.backward(); opt.step()
    if ep%2000==0 or ep==EPISODES:
        a=evaluate(); best=max(best,a); print(f"  ep {ep:5d} loss {loss.item():.3f} one-shot {a:.1f} (best {best:.1f})",flush=True)
sp=sum(p.numel() for p in st.parameters())
print(f"\nDONE  sub-feature FLOOR ({len(bg_small)} classes) = {best:.1f}% / {sp/1e3:.0f}K params  (Gemma 96.3%/167.6M = {167.6e6/sp:.0f}x larger)")
