"""HANDS, not brain: train ONE architecture the jabberwock chose; print ACC/PARAMS."""
import os as _os; _os.environ["PYTORCH_CUDA_ALLOC_CONF"]="expandable_segments:True"
import sys, math, numpy as np, torch, torch.nn as nn, torch.nn.functional as F
DEV="cuda"; NS,NQ=5,5; EPISODES=7000
d=int(sys.argv[1]); w=int(sys.argv[2]); scale=sys.argv[3]; tw=int(sys.argv[4])
B28=torch.tensor(np.load("/tmp/asm_28.npz")["bg"]).float(); E28=torch.tensor(np.load("/tmp/asm_28.npz")["ev"]).float()
B56=torch.tensor(np.load("/tmp/asm_56.npz")["bg"]).float(); E56=torch.tensor(np.load("/tmp/asm_56.npz")["ev"]).float()
NC=B28.shape[0]; BG_DRAW=B28.shape[1]
class Branch(nn.Module):
    def __init__(s,d,w):
        super().__init__(); L=[]; ci=1
        for _ in range(d): L+=[nn.Conv2d(ci,w,3,padding=1),nn.BatchNorm2d(w),nn.ReLU()]; ci=w
        s.L=nn.ModuleList(L)
    def forward(s,x):
        i=0
        while i<len(s.L):
            x=s.L[i](x); x=s.L[i+1](x); x=s.L[i+2](x); i+=3
            if x.shape[-1]>1: x=F.max_pool2d(x,2)
        return x.flatten(1)
class Net(nn.Module):
    def __init__(s,d,w,sc):
        super().__init__(); s.sc=sc
        if sc in ("lo","hi"): s.b=Branch(d,w)
        else: s.b28=Branch(d,w); s.b56=Branch(d+1,w)
    def forward(s,x28,x56):
        if s.sc=="lo": return s.b(x28)
        if s.sc=="hi": return s.b(x56)
        return torch.cat([s.b28(x28),s.b56(x56)],1)
net=Net(d,w,scale).to(DEV); opt=torch.optim.Adam(net.parameters(),lr=1e-3); best=0.0
for ep in range(1,EPISODES+1):
    for g in opt.param_groups: g["lr"]=1e-3*(0.05+0.95*0.5*(1+math.cos(math.pi*ep/EPISODES)))
    cls=np.random.choice(NC,tw,replace=False); di=np.stack([np.random.choice(BG_DRAW,NS+NQ,replace=False) for _ in cls])
    x28=B28[cls[:,None],di].reshape(-1,1,28,28).to(DEV) if scale!="hi" else None
    x56=B56[cls[:,None],di].reshape(-1,1,56,56).to(DEV) if scale!="lo" else None
    e=net(x28,x56).reshape(tw,NS+NQ,-1); pr=e[:,:NS].mean(1); q=e[:,NS:].reshape(tw*NQ,-1)
    ql=torch.arange(tw,device=DEV).repeat_interleave(NQ); d2=((q[:,None,:]-pr[None,:,:])**2).sum(-1)
    loss=F.cross_entropy(-d2,ql); opt.zero_grad(); loss.backward(); opt.step()
    if ep==EPISODES:
        net.eval()
        with torch.no_grad():
            s28=E28[:,0][:,None].to(DEV) if scale!="hi" else None; s56=E56[:,0][:,None].to(DEV) if scale!="lo" else None
            q28=E28[:,1][:,None].to(DEV) if scale!="hi" else None; q56=E56[:,1][:,None].to(DEV) if scale!="lo" else None
            S=net(s28,s56); Q=net(q28,q56)
        r=np.random.default_rng(123); cor=0
        for _ in range(3000):
            cl=r.choice(len(S),20,replace=False); qi=int(r.integers(20)); cor+=int(((S[cl]-Q[cl[qi]])**2).sum(1).argmin().item()==qi)
        best=cor/30.0
print(f"ACC={best:.2f} PARAMS={sum(p.numel() for p in net.parameters())}")
