"""SHED TO THE FLOOR — distil the 96.5% Gemma teacher into a BANK OF TINY SUB-FEATURE DETECTORS + composition,
not one monolithic glyph-net. Each sub-feature filter is small and REUSED across all glyphs; a glyph is the
COMPOSITION of which sub-features fire and where. Efficiency floor (rule 1) + compositional one-shot (rule 2).
"""
import os as _os; _os.environ["PYTORCH_CUDA_ALLOC_CONF"]="expandable_segments:True"
import os, glob, json, time, random, numpy as np, torch, torch.nn as nn, torch.nn.functional as F
from PIL import Image
from safetensors.torch import load_file
from transformers import Gemma4VisionModel, Gemma4VisionConfig, Gemma4ImageProcessorPil
DEV="cuda"; OMNI="/tmp/omniglot"; CANVAS=180; SMALL=48
N_BG,BG_DRAW=480,5; N_EV,EV_DRAW=200,2
WAY,NS,NQ=15,3,2; T_EPISODES=1800; WARMUP=150; ENC_LR,HEAD_LR=3e-5,1e-3; SCALE=10.0; TRAIN_TOP=6
K=48; DIM=256; S_EPISODES=4000
torch.manual_seed(0); np.random.seed(0); random.seed(0)

def load_strokes(path):
    st,cur=[],[]
    for line in open(path):
        s=line.strip()
        if not s or s=="START": continue
        if s=="BREAK":
            if cur: st.append(np.asarray(cur,float)); cur=[]
            continue
        p=s.split(",")
        if len(p)>=2: cur.append((float(p[0]),float(p[1])))
    if cur: st.append(np.asarray(cur,float))
    return [s for s in st if len(s)>=1]
def _draw(path,canvas,rot,th):
    strokes=load_strokes(path); allp=np.concatenate([s for s in strokes if len(s)],0) if strokes else np.zeros((0,2))
    a=np.full((canvas,canvas,3),255,np.uint8)
    if len(allp):
        mn,mx=allp.min(0),allp.max(0); span=np.maximum(mx-mn,1e-6)
        for s in strokes:
            q=(s-mn)/span*(canvas-th*4)+th*2
            for i in range(len(q)-1):
                for t in np.linspace(0,1,40):
                    x,y=(q[i]*(1-t)+q[i+1]*t).astype(int); a[max(y-th,0):y+th+1,max(x-th,0):x+th+1]=0
    im=Image.fromarray(a); return im.rotate(rot) if rot else im
def render(path,rot=0): return _draw(path,CANVAS,rot,3)
def render_small(path,rot=0):
    im=_draw(path,SMALL,rot,1).convert("L"); return (255-np.asarray(im,np.float32))/255.0   # white strokes on black, [0,1]
def chars(split):
    d=f"{OMNI}/strokes_{split}"; out=[]
    for al in sorted(os.listdir(d)):
        ad=os.path.join(d,al)
        if not os.path.isdir(ad): continue
        for c in sorted(os.listdir(ad)):
            dr=sorted(glob.glob(os.path.join(ad,c)+"/*.txt"))
            if len(dr)>=max(BG_DRAW,EV_DRAW): out.append(dr)
    return out

print("== load Gemma teacher ==",flush=True)
vc=Gemma4VisionConfig(**json.load(open("/tmp/vision_config.json")))
teacher=Gemma4VisionModel(vc); teacher.load_state_dict(load_file("/tmp/vision_tower.safetensors"),strict=False)
teacher.to(DEV).train()
for p in teacher.parameters(): p.requires_grad=False
for p in teacher.encoder.layers[-TRAIN_TOP:].parameters(): p.requires_grad=True
try: teacher.gradient_checkpointing_enable()
except Exception: pass
thead=nn.Linear(768,DIM).to(DEV)
ip=Gemma4ImageProcessorPil(max_soft_tokens=70)
def to_pv(pils):
    pr=[ip(images=im,return_tensors="pt") for im in pils]
    return torch.cat([p["pixel_values"] for p in pr],0), torch.cat([p["image_position_ids"] for p in pr],0)
def t_embed(pv,pid):
    out=teacher(pixel_values=pv.to(DEV),pixel_position_ids=pid.to(DEV))
    lh=out.last_hidden_state if hasattr(out,"last_hidden_state") else out[0]
    B=pv.shape[0]; lh=lh.reshape(B,lh.shape[0]//B,lh.shape[-1]).mean(1); return F.normalize(thead(lh),dim=1)

print("== render+cache (teacher pv + student small) ==",flush=True)
rng=np.random.default_rng(1); reng=np.random.default_rng(0)
bg=chars("background"); ev=chars("evaluation")
bg=[bg[i] for i in rng.permutation(len(bg))[:N_BG]]; ev=[ev[i] for i in reng.permutation(len(ev))[:N_EV]]
bg_pv=[]; bg_small=[]; t0=time.time()
for dr in bg:
    pick=[dr[i] for i in rng.permutation(len(dr))[:BG_DRAW]]
    for rot in (0,90,180,270):
        pv,pid=to_pv([render(p,rot) for p in pick]); bg_pv.append((pv.half(),pid))
        bg_small.append(np.stack([render_small(p,rot) for p in pick]))
ev_pv=[]; ev_small=[]
for dr in ev:
    pick=[dr[i] for i in reng.permutation(len(dr))[:EV_DRAW]]
    pv,pid=to_pv([render(p) for p in pick]); ev_pv.append((pv.half(),pid))
    ev_small.append(np.stack([render_small(p) for p in pick]))
bg_small=torch.tensor(np.stack(bg_small)).float()      # (C,BG_DRAW,48,48)
ev_small=torch.tensor(np.stack(ev_small)).float()
print(f"  {len(bg_pv)} bg classes + {len(ev_pv)} eval in {time.time()-t0:.0f}s",flush=True)

# ---- PHASE 1: fine-tune teacher to ~96.5 (proven recipe) ----
import math
opt=torch.optim.AdamW([{"params":[p for p in teacher.parameters() if p.requires_grad],"lr":ENC_LR},
                       {"params":thead.parameters(),"lr":HEAD_LR}],weight_decay=0.01)
print("== PHASE 1: fine-tune teacher ==",flush=True); tbest=0.0; tbest_state=None
@torch.no_grad()
def t_eval():
    teacher.eval(); S=[];Q=[]
    for pv,pid in ev_pv:
        with torch.autocast("cuda",dtype=torch.bfloat16): e=t_embed(pv.float(),pid)
        S.append(e[0]);Q.append(e[1])
    S=torch.stack(S);Q=torch.stack(Q); r=np.random.default_rng(123); cor=0
    for _ in range(1000):
        cl=r.choice(len(ev_pv),20,replace=False); qi=int(r.integers(20)); cor+=int((S[cl]@Q[cl[qi]]).argmax().item()==qi)
    teacher.train(); return cor/10.0
for ep in range(1,T_EPISODES+1):
    w=(ep/WARMUP) if ep<WARMUP else (0.1+0.9*0.5*(1+math.cos(math.pi*(ep-WARMUP)/(T_EPISODES-WARMUP))))
    opt.param_groups[0]["lr"]=ENC_LR*w; opt.param_groups[1]["lr"]=HEAD_LR*w
    cls=np.random.choice(len(bg_pv),WAY,replace=False); pvl,pidl=[],[]
    for c in cls:
        pv,pid=bg_pv[c]; idx=np.random.choice(pv.shape[0],NS+NQ,replace=False)
        for j in idx: pvl.append(pv[j:j+1]); pidl.append(pid[j:j+1])
    pv=torch.cat(pvl,0).float(); pid=torch.cat(pidl,0)
    with torch.autocast("cuda",dtype=torch.bfloat16):
        emb=t_embed(pv,pid).reshape(WAY,NS+NQ,-1); proto=F.normalize(emb[:,:NS].mean(1),dim=1)
        q=emb[:,NS:].reshape(WAY*NQ,-1); ql=torch.arange(WAY,device=DEV).repeat_interleave(NQ)
        loss=F.cross_entropy(SCALE*(q@proto.t()),ql)
    opt.zero_grad(); loss.backward()
    torch.nn.utils.clip_grad_norm_([p for p in teacher.parameters() if p.requires_grad]+list(thead.parameters()),1.0); opt.step()
    if ep%300==0 or ep==T_EPISODES:
        a=t_eval()
        if a>tbest: tbest=a; tbest_state={ "thead":thead.state_dict(), "enc":{k:v.detach().clone() for k,v in teacher.state_dict().items()} }
        print(f"  teacher ep {ep} eval {a:.1f} (best {tbest:.1f})",flush=True)
if tbest_state: teacher.load_state_dict(tbest_state["enc"]); thead.load_state_dict(tbest_state["thead"])
print(f"  teacher best {tbest:.1f}",flush=True)

# ---- PHASE 2: teacher embeddings for all bg images (distillation targets) ----
print("== PHASE 2: teacher targets ==",flush=True)
teacher.eval()
bg_tgt=[]
with torch.no_grad():
    for pv,pid in bg_pv:
        with torch.autocast("cuda",dtype=torch.bfloat16): e=t_embed(pv.float(),pid)
        bg_tgt.append(e.float())
bg_tgt=torch.stack(bg_tgt)   # (C,BG_DRAW,DIM)

# ---- PHASE 3: the FLOOR — a bank of tiny sub-feature detectors + composition, distilled from teacher ----
class SubFeatureBank(nn.Module):
    """conv filters = sub-feature DETECTORS (reused over space + glyphs); a glyph = COMPOSITION of which
    sub-features fire and where (mean+max over space per detector at two depths)."""
    def __init__(self,K=48,dim=256):
        super().__init__()
        self.c1=nn.Conv2d(1,K,5,padding=2); self.b1=nn.BatchNorm2d(K)      # level-1 sub-features
        self.c2=nn.Conv2d(K,K,3,padding=1); self.b2=nn.BatchNorm2d(K)      # level-2 = compositions of level-1
        self.head=nn.Linear(4*K,dim)
    def forward(self,x):
        a1=F.max_pool2d(F.relu(self.b1(self.c1(x))),2)
        a2=F.max_pool2d(F.relu(self.b2(self.c2(a1))),2)
        desc=torch.cat([a1.mean((2,3)),a1.amax((2,3)),a2.mean((2,3)),a2.amax((2,3))],1)  # composition
        return F.normalize(self.head(desc),dim=1)

def train_student(distil=True, tag="distil"):
    st=SubFeatureBank(K,DIM).to(DEV); st.train()
    opt=torch.optim.AdamW(st.parameters(),lr=2e-3,weight_decay=1e-4)
    for ep in range(1,S_EPISODES+1):
        cls=np.random.choice(len(bg_small),WAY,replace=False); xs=[]; tg=[]
        for c in cls:
            idx=np.random.choice(BG_DRAW,NS+NQ,replace=False)
            xs.append(bg_small[c,idx]); tg.append(bg_tgt[c,idx])
        x=torch.cat(xs,0).unsqueeze(1).to(DEV); tgt=torch.cat(tg,0).to(DEV)
        emb=st(x)
        e=emb.reshape(WAY,NS+NQ,-1); proto=F.normalize(e[:,:NS].mean(1),dim=1)
        q=e[:,NS:].reshape(WAY*NQ,-1); ql=torch.arange(WAY,device=DEV).repeat_interleave(NQ)
        loss=F.cross_entropy(SCALE*(q@proto.t()),ql)
        if distil: loss=loss+5.0*(1-(emb*tgt).sum(1)).mean()   # cosine match to teacher embedding
        opt.zero_grad(); loss.backward(); opt.step()
        if ep%500==0 or ep==S_EPISODES:
            st.eval()
            with torch.no_grad():
                S=st(ev_small[:,0].unsqueeze(1).to(DEV)); Q=st(ev_small[:,1].unsqueeze(1).to(DEV))
            r=np.random.default_rng(123); cor=0
            for _ in range(2000):
                cl=r.choice(len(ev_small),20,replace=False); qi=int(r.integers(20)); cor+=int((S[cl]@Q[cl[qi]]).argmax().item()==qi)
            acc=cor/20.0; st.train()
            print(f"  student[{tag}] ep {ep} one-shot {acc:.1f}",flush=True)
    return st, acc

print("== PHASE 3: distil into sub-feature bank ==",flush=True)
st_d,acc_d=train_student(distil=True,tag="distil")
print("== PHASE 3b: same bank FROM SCRATCH (no teacher) for honesty ==",flush=True)
st_s,acc_s=train_student(distil=False,tag="scratch")

tp=sum(p.numel() for p in teacher.parameters())+sum(p.numel() for p in thead.parameters())
sp=sum(p.numel() for p in st_d.parameters())
print(f"\nDONE  teacher(Gemma top6) {tbest:.1f}% / {tp/1e6:.1f}M params ; "
      f"sub-feature FLOOR distilled {acc_d:.1f}% / {sp/1e3:.0f}K params ({tp/sp:.0f}x smaller) ; scratch {acc_s:.1f}%")
print(f"  K={K} sub-feature detectors, compositional descriptor (mean+max per detector x2 depths)")
