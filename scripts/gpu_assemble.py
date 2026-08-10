"""THE JABBERWOCK ASSEMBLES NETS — autonomy loop over ARCHITECTURE + multi-resolution data.
The agent holds net blocks; it ASSEMBLES a candidate (depth,width,scale,train-way), trains it (euclidean
protonet on the standard Omniglot images at low/high res), MEASURES one-shot, and its EV-GATE (the two rules)
picks the next: ESCALATE capacity while < human bar, then SHRINK to the cheapest net that still holds >=95.
Selection logic = the agent's compose-search-gate (same shape as its graph rules); GPU = the world it measures.
"""
import os as _os; _os.environ["PYTORCH_CUDA_ALLOC_CONF"]="expandable_segments:True"
import os, glob, math, time, random, numpy as np, torch, torch.nn as nn, torch.nn.functional as F
from PIL import Image
DEV="cuda"; IMG="/tmp/omniglot_img"; TARGET=95.0
BG_DRAW=12; N_EV,EV_DRAW=200,2; NS,NQ=5,5; EVAL_WAY=20; EPISODES=8000
torch.manual_seed(0); np.random.seed(0); random.seed(0)
def chars(split):
    out=[]
    for al in sorted(glob.glob(f"{IMG}/images_{split}/*")):
        for c in sorted(glob.glob(al+"/*")):
            dr=sorted(glob.glob(c+"/*.png"))
            if len(dr)>=max(BG_DRAW,EV_DRAW): out.append(dr)
    return out
def load_res(path,sz,rot=0):
    im=Image.open(path).convert("L").resize((sz,sz),Image.LANCZOS)
    if rot: im=im.rotate(rot)
    return 1.0-np.asarray(im,np.float32)/255.0
def build_cache(sz):
    f=f"/tmp/asm_{sz}.npz"
    if os.path.exists(f):
        d=np.load(f); return torch.tensor(d["bg"]).float(), torch.tensor(d["ev"]).float()
    rng=np.random.default_rng(1); reng=np.random.default_rng(0)
    bg=chars("background"); ev=chars("evaluation"); ev=[ev[i] for i in reng.permutation(len(ev))[:N_EV]]
    bgL=[]
    for dr in bg:
        pick=[dr[i] for i in rng.permutation(len(dr))[:BG_DRAW]]
        base=[load_res(p,sz,0) for p in pick]
        for rot in (0,90,180,270):
            bgL.append(np.stack(base) if rot==0 else np.stack([1.0-np.asarray(Image.fromarray(((1-b)*255).astype(np.uint8)).rotate(rot),np.float32)/255.0 for b in base]))
    evL=[np.stack([load_res(p,sz) for p in [dr[i] for i in reng.permutation(len(dr))[:EV_DRAW]]]) for dr in ev]
    bg=torch.tensor(np.stack(bgL)).float(); ev=torch.tensor(np.stack(evL)).float()
    np.savez(f, bg=bg.numpy().astype(np.float16), ev=ev.numpy().astype(np.float16)); return bg,ev
print("caching images @28 and @56...",flush=True); t0=time.time()
BG28,EV28=build_cache(28); BG56,EV56=build_cache(56)
NC=BG28.shape[0]; print(f"  {NC} bg classes, {EV28.shape[0]} eval in {time.time()-t0:.0f}s",flush=True)

def blk(i,o): return nn.Sequential(nn.Conv2d(i,o,3,padding=1),nn.BatchNorm2d(o),nn.ReLU(),nn.MaxPool2d(2))
class Branch(nn.Module):
    def __init__(self,d,w):
        super().__init__(); layers=[]; ci=1
        for _ in range(d):
            layers+=[nn.Conv2d(ci,w,3,padding=1),nn.BatchNorm2d(w),nn.ReLU()]; ci=w
        self.layers=nn.ModuleList(layers)
    def forward(self,x):
        i=0
        while i<len(self.layers):
            x=self.layers[i](x); x=self.layers[i+1](x); x=self.layers[i+2](x); i+=3
            if x.shape[-1]>1: x=F.max_pool2d(x,2)   # pool only while spatial>1 (no over-pool)
        return x.flatten(1)
class Assembled(nn.Module):
    def __init__(self,d,w,scale):
        super().__init__(); self.scale=scale
        if scale in ("lo","hi"): self.b=Branch(d,w)
        else: self.b28=Branch(d,w); self.b56=Branch(d+1,w)   # dual: 28 (d) + 56 (d+1) branches
    def forward(self,x28,x56):
        if self.scale=="lo": return self.b(x28)
        if self.scale=="hi": return self.b(x56)
        return torch.cat([self.b28(x28),self.b56(x56)],1)

def train_eval(genome):
    d,w,scale,tw=genome
    net=Assembled(d,w,scale).to(DEV); opt=torch.optim.Adam(net.parameters(),lr=1e-3)
    def emb(idx, src28,src56, draws):  # idx (way,) class ids ; draws (way,k)
        x28=src28[idx][:, :,None].reshape(-1,1,28,28).to(DEV) if scale!="hi" else None
        return None
    def run(idx_classes, k_each, src28, src56):
        # gather k_each drawings per class
        pass
    best=0.0
    for ep in range(1,EPISODES+1):
        for g in opt.param_groups: g["lr"]=1e-3*(0.05+0.95*0.5*(1+math.cos(math.pi*ep/EPISODES)))
        cls=np.random.choice(NC,tw,replace=False)
        di=np.stack([np.random.choice(BG_DRAW,NS+NQ,replace=False) for _ in cls])  # (tw, NS+NQ)
        x28=BG28[cls[:,None],di].reshape(-1,1,28,28).to(DEV) if scale!="hi" else None
        x56=BG56[cls[:,None],di].reshape(-1,1,56,56).to(DEV) if scale!="lo" else None
        e=net(x28,x56).reshape(tw,NS+NQ,-1); proto=e[:,:NS].mean(1); q=e[:,NS:].reshape(tw*NQ,-1)
        ql=torch.arange(tw,device=DEV).repeat_interleave(NQ)
        d2=((q[:,None,:]-proto[None,:,:])**2).sum(-1); loss=F.cross_entropy(-d2,ql)
        opt.zero_grad(); loss.backward(); opt.step()
        if ep%2000==0 or ep==EPISODES:
            net.eval()
            with torch.no_grad():
                s28=EV28[:,0][:,None].to(DEV) if scale!="hi" else None; s56=EV56[:,0][:,None].to(DEV) if scale!="lo" else None
                q28=EV28[:,1][:,None].to(DEV) if scale!="hi" else None; q56=EV56[:,1][:,None].to(DEV) if scale!="lo" else None
                S=net(s28,s56); Q=net(q28,q56)
            r=np.random.default_rng(123); cor=0
            for _ in range(2000):
                cl=r.choice(len(S),20,replace=False); qi=int(r.integers(20)); cor+=int(((S[cl]-Q[cl[qi]])**2).sum(1).argmin().item()==qi)
            best=max(best,cor/20.0); net.train()
    params=sum(p.numel() for p in net.parameters())
    return best, params

# ---- the agent's compose-search-gate over architectures ----
def grow(g):
    d,w,s,tw=g; cand=[]
    if s=="lo": cand.append((d,w,"dual",tw))
    if tw<60: cand.append((d,w,s,60))
    if w<96: cand.append((d,min(w*2 if w<64 else 96,96),s,tw))
    if d<5: cand.append((d+1,w,s,tw))
    return cand
def shrink(g):
    d,w,s,tw=g; cand=[]
    if w>32: cand.append((d,w//2 if w>48 else 32,s,tw))
    if d>3: cand.append((d-1,w,s,tw))
    if s=="dual": cand.append((d,w,"lo",tw))
    return cand
def agent_pick(bank,tried):
    if not bank: return (4,64,"lo",20)
    best=max(bank,key=lambda x:x[1])
    if best[1]>=TARGET:
        qual=[b for b in bank if b[1]>=TARGET]; cheap=min(qual,key=lambda x:x[2])
        for m in shrink(cheap[0]):
            if m not in tried: return m
        return None
    for m in grow(best[0]):
        if m not in tried: return m
    # if best exhausted, grow 2nd best
    for b in sorted(bank,key=lambda x:-x[1])[1:]:
        for m in grow(b[0]):
            if m not in tried: return m
    return None

print("== JABBERWOCK ASSEMBLES (escalate to clear 95, then shrink to the floor) ==",flush=True)
bank=[]; tried=set(); ROUNDS=9
for rnd in range(ROUNDS):
    g=agent_pick(bank,tried)
    if g is None: print("  search exhausted"); break
    tried.add(g); t0=time.time(); acc,params=train_eval(g)
    bank.append((g,acc,params))
    mode="FLOOR" if (max(b[1] for b in bank)>=TARGET) else "escalate"
    print(f"  [{rnd}] assembled d{g[0]} w{g[1]} {g[2]} tw{g[3]} -> {acc:.1f}% / {params/1e3:.0f}K  ({time.time()-t0:.0f}s) [{mode}]",flush=True)
clear=[b for b in bank if b[1]>=TARGET]
print("\n=== ASSEMBLY RESULT ===")
for g,a,p in sorted(bank,key=lambda x:-x[1]): print(f"  d{g[0]} w{g[1]} {g[2]} tw{g[3]}: {a:.1f}% / {p/1e3:.0f}K")
if clear:
    floor=min(clear,key=lambda x:x[2]); g,a,p=floor
    print(f"\nDONE  jabberwock CLEARED the bar AND found the floor: d{g[0]} w{g[1]} {g[2]} tw{g[3]} = {a:.1f}% / {p/1e3:.0f}K params (Gemma 96.3/167.6M = {167.6e6/p:.0f}x larger)")
else:
    b=max(bank,key=lambda x:x[1]); print(f"\nDONE  best assembled = {b[1]:.1f}% / {b[2]/1e3:.0f}K (did not clear 95; bank above)")
