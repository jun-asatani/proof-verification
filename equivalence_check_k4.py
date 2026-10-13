"""Equivalence check at k=4 between the exhaustive verifier (exhaustive_verify.apply_op) and the memory-wide simulator (core_encoder.FlashSim). Run from the repository root. Part 1: all transitions from every reachable state (m=1). Part 2: every write of real run_once() runs with m=4 sub-blocks compared with apply_op on the touched sub-block."""
import sys, collections; sys.path.insert(0,".")
from core_encoder import FlashSim
from exhaustive_verify import apply_op
k=4
def real_step(x,i,q):
    sim=FlashSim(1,k,q,seed=0)
    sim.x=[[0]*(k+1),[0]+list(x)]
    j=1
    if sim.read_alone(j) and (sim.read_maxi(j)%2)==(i%2):
        sim.write_alone(j,i)
    elif sim.active(j) and sim.read_index(j)==i and sim.read_alone(j)==0:
        sim.write(j,i)
    elif (sim.read_index(j)==((i%k)+1) and sim.parity(j)==0 and sim.read_alone(j)==0):
        sim.write_change(j,i)
    elif sim.read_maxnum(j) and sim.read_maxi(j)==i:
        sim.write_max(j,i)
    else:
        done=False
        for layer in range(q):
            if sim.clear(j) and sim.read_layer(j)==layer:
                sim.write_new(j,i); done=True; break
        if not done: return None
    return tuple(sim.x[1][1:k+1])
tot=0;bad=[]
for q in [2,3,4,5,6,8,12]:
    seen={tuple([0]*k)}; fr=[tuple([0]*k)]
    while fr:
        nf=[]
        for x in fr:
            for i in range(1,k+1):
                a=apply_op(x,i,k,q,2)
                try: b=real_step(x,i,q)
                except Exception as e: b=('EXC',repr(e))
                tot+=1
                if a!=b: bad.append((q,x,i,a,b))
                if a is not None and a not in seen:
                    seen.add(a); nf.append(a)
        fr=nf
    print('q',q,'states',len(seen))
print('transitions compared',tot,'mismatches',len(bad)); print(bad[:10])

# ---- Part 2 ----
from core_encoder import FlashSim
import exhaustive_verify as ev
from exhaustive_verify import apply_op
k=4
# (A) bound-path usage in verifier over all reachable states
def bound_hits(q):
    # count transitions where a branch fires but target cell > q-2 (apply_op returns None via bound)
    import exhaustive_primitives as ep
    hits=0
    seen={tuple([0]*k)}; fr=[tuple([0]*k)]
    while fr:
        nf=[]
        for x in fr:
            for i in range(1,k+1):
                a=apply_op(x,i,k,q,2)
                if a is None:
                    # does any non-bound branch condition hold? emulate: compare to write_new only path
                    xl=list(x)
                    # branch conditions
                    cond=False
                    if ep.read_alone(xl,k,2,'pair') and ep.read_maxi(xl,k)%2==i%2: cond=True
                    elif ep.active(xl,k,q) and not ep.read_alone(xl,k,2,'pair') and ep.read_index_c(xl,k,q)==i: cond=True
                    elif (not ep.read_alone(xl,k,2,'pair')) and ep.read_index_c(xl,k,q)==((i%k)+1) and ep.parity(xl)==0: cond=True
                    elif ep.read_maxnum(xl) and ep.read_maxi(xl,k)==i: cond=True
                    if cond: hits+=1
                elif a not in seen: seen.add(a); nf.append(a)
        fr=nf
    return hits
for q in [2,3,4,6,8,12,30]:
    print('q',q,'branch-fires-but-cell-full transitions:',bound_hits(q))

# (B) instrumented real run_once, m=k=4: each real write == apply_op on that sub-block
rec=[]
class Sim(FlashSim):
    pass
def wrap(name):
    orig=getattr(FlashSim,name)
    def f(self,j,i):
        pre=tuple(self.x[j][1:k+1]); orig(self,j,i); post=tuple(self.x[j][1:k+1])
        rec.append((name,j,i,pre,post,self.q))
    setattr(Sim,name,f)
for n in ['write','write_new','write_max','write_alone','write_change']: wrap(n)
tot=0;bad=[];over=0;ph=collections.Counter()
for q in [3,4,6,8]:
    for seed in range(1500):
        s=Sim(4,k,q,seed=seed); rec.clear(); s.run_once()
        for (name,j,i,pre,post,qq) in rec:
            tot+=1; ph[name]+=1
            if max(post)>q-1: over+=1
            if apply_op(pre,i,k,q,2)!=post: bad.append((q,name,pre,i,post,apply_op(pre,i,k,q,2)))
print('real writes compared',tot,'mismatches',len(bad),'cells above q-1:',over); print(dict(ph)); print(bad[:5])
