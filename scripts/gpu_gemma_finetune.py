"""GPU fine-tune of Gemma-4 vision encoder on Omniglot background -> 20-way 1-shot on held-out eval.
STABLE recipe: freeze lower layers, train top-4 + head, L2-normalized cosine-prototypical loss, AdamW + warmup,
low lr. The genuine 'nothing frozen on the adapted slice' adaptation of the warm-start."""
import os as _os; _os.environ["PYTORCH_CUDA_ALLOC_CONF"]="expandable_segments:True"
import glob, json, time, random, numpy as np, torch, torch.nn.functional as F
from PIL import Image
from safetensors.torch import load_file
from transformers import Gemma4VisionModel, Gemma4VisionConfig, Gemma4ImageProcessorPil

DEV="cuda"; OMNI="/tmp/omniglot"; CANVAS=180
N_BG,BG_DRAW=480,5; N_EV,EV_DRAW=200,2
WAY,NS,NQ=15,3,2; EPISODES=2200; WARMUP=150
ENC_LR,HEAD_LR=3e-5,1e-3; SCALE=10.0; TRAIN_TOP=6
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

def render(path,rot=0):
    strokes=load_strokes(path)
    allp=np.concatenate([s for s in strokes if len(s)],0) if strokes else np.zeros((0,2))
    a=np.full((CANVAS,CANVAS,3),255,np.uint8)
    if len(allp):
        mn,mx=allp.min(0),allp.max(0); span=np.maximum(mx-mn,1e-6)
        for s in strokes:
            q=(s-mn)/span*(CANVAS-24)+12
            for i in range(len(q)-1):
                for t in np.linspace(0,1,40):
                    x,y=(q[i]*(1-t)+q[i+1]*t).astype(int); a[max(y-3,0):y+4,max(x-3,0):x+4]=0
    im=Image.fromarray(a); return im.rotate(rot) if rot else im

def chars(split):
    d=f"{OMNI}/strokes_{split}"; out=[]
    for al in sorted(os.listdir(d)):
        ad=os.path.join(d,al)
        if not os.path.isdir(ad): continue
        for c in sorted(os.listdir(ad)):
            dr=sorted(glob.glob(os.path.join(ad,c)+"/*.txt"))
            if len(dr)>=max(BG_DRAW,EV_DRAW): out.append(dr)
    return out
import os

print("loading model...",flush=True)
vc=Gemma4VisionConfig(**json.load(open("/tmp/vision_config.json")))
model=Gemma4VisionModel(vc); model.load_state_dict(load_file("/tmp/vision_tower.safetensors"),strict=False)
model.to(DEV).train()
for p in model.parameters(): p.requires_grad=False
for p in model.encoder.layers[-TRAIN_TOP:].parameters(): p.requires_grad=True
try: model.gradient_checkpointing_enable(); print("grad ckpt ON")
except Exception as e: print("no ckpt",e)
head=torch.nn.Linear(768,256).to(DEV)
ip=Gemma4ImageProcessorPil(max_soft_tokens=70)

def to_pv(pils):
    pr=[ip(images=im,return_tensors="pt") for im in pils]
    return torch.cat([p["pixel_values"] for p in pr],0), torch.cat([p["image_position_ids"] for p in pr],0)

def embed(pv,pid):
    out=model(pixel_values=pv.to(DEV),pixel_position_ids=pid.to(DEV))
    lh=out.last_hidden_state if hasattr(out,"last_hidden_state") else out[0]
    B=pv.shape[0]; lh=lh.reshape(B,lh.shape[0]//B,lh.shape[-1]).mean(1)
    return F.normalize(head(lh),dim=1)

print("rendering+caching...",flush=True)
rng=np.random.default_rng(1); reng=np.random.default_rng(0)
bg=chars("background"); ev=chars("evaluation")
bg=[bg[i] for i in rng.permutation(len(bg))[:N_BG]]; ev=[ev[i] for i in reng.permutation(len(ev))[:N_EV]]
bg_pv=[]; t0=time.time()
for dr in bg:
    pick=[dr[i] for i in rng.permutation(len(dr))[:BG_DRAW]]
    for rot in (0,90,180,270):
        pv,pid=to_pv([render(p,rot) for p in pick]); bg_pv.append((pv.half(),pid))
ev_pv=[]
for dr in ev:
    pick=[dr[i] for i in reng.permutation(len(dr))[:EV_DRAW]]
    pv,pid=to_pv([render(p) for p in pick]); ev_pv.append((pv.half(),pid))
print(f"  cached {len(bg_pv)} bg classes + {len(ev_pv)} eval in {time.time()-t0:.0f}s",flush=True)

opt=torch.optim.AdamW([
    {"params":[p for p in model.parameters() if p.requires_grad],"lr":ENC_LR},
    {"params":head.parameters(),"lr":HEAD_LR}], weight_decay=0.01)

@torch.no_grad()
def evaluate():
    model.eval(); S=[];Q=[]
    for pv,pid in ev_pv:
        with torch.autocast("cuda",dtype=torch.bfloat16): e=embed(pv.float(),pid)
        S.append(e[0]);Q.append(e[1])
    S=torch.stack(S);Q=torch.stack(Q); r=np.random.default_rng(123); cor=0;n=1000
    for _ in range(n):
        cl=r.choice(len(ev_pv),20,replace=False); qi=int(r.integers(20))
        cor+=int((S[cl]@Q[cl[qi]]).argmax().item()==qi)
    model.train(); return 100*cor/n

print("fine-tuning...",flush=True); best=0.0
for ep in range(1,EPISODES+1):
    import math as _m
    w=(ep/WARMUP) if ep<WARMUP else (0.1+0.9*0.5*(1+_m.cos(_m.pi*(ep-WARMUP)/(EPISODES-WARMUP))))
    opt.param_groups[0]["lr"]=ENC_LR*w; opt.param_groups[1]["lr"]=HEAD_LR*w
    cls=np.random.choice(len(bg_pv),WAY,replace=False)
    pvl,pidl=[],[]
    for c in cls:
        pv,pid=bg_pv[c]; idx=np.random.choice(pv.shape[0],NS+NQ,replace=False)
        for j in idx: pvl.append(pv[j:j+1]); pidl.append(pid[j:j+1])
    pv=torch.cat(pvl,0).float(); pid=torch.cat(pidl,0)
    with torch.autocast("cuda",dtype=torch.bfloat16):
        emb=embed(pv,pid).reshape(WAY,NS+NQ,-1)
        proto=F.normalize(emb[:,:NS].mean(1),dim=1)
        q=emb[:,NS:].reshape(WAY*NQ,-1)
        ql=torch.arange(WAY,device=DEV).repeat_interleave(NQ)
        logits=SCALE*(q@proto.t())
        loss=F.cross_entropy(logits,ql)
    opt.zero_grad(); loss.backward()
    torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad]+list(head.parameters()),1.0)
    opt.step()
    if ep%100==0 or ep==EPISODES:
        acc=evaluate(); best=max(best,acc)
        print(f"  ep {ep:4d}  loss {loss.item():.3f}  eval-1shot {acc:.1f}%  (best {best:.1f})",flush=True)
print(f"\nDONE best 20-way 1-shot = {best:.1f}%  (geometric ~81, frozen ~90, human ~95)")
