"""Small-instance design MILP based on Eq. (5) of Raayatpanah et al. (2023)."""
from dataclasses import dataclass
from math import log
import numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint
from scipy.sparse import lil_matrix

@dataclass(frozen=True)
class Demand:
    source: str
    target: str
    rate: float

@dataclass(frozen=True)
class Option:
    bandwidth: float
    efficiency: float
    probability: float
    cost: float
    @property
    def capacity(self): return self.bandwidth * self.efficiency

class Instance:
    def __init__(self, nodes, arcs, demands, options, sigma=.5, alpha=1., epsilon=.05, protect_nodes=None):
        self.nodes=list(nodes); self.arcs=list(map(tuple,arcs)); self.demands=list(demands); self.options=list(options)
        self.sigma=sigma; self.alpha=alpha; self.epsilon=epsilon
        self.protect_nodes=list(protect_nodes if protect_nodes is not None else [n for n in self.nodes if n not in {d.source for d in demands}|{d.target for d in demands}])
        if not 0<sigma<=1 or not 0<=alpha<=1 or not 0<epsilon<1: raise ValueError('invalid alpha, sigma, epsilon')
        if not self.options or any(not 0<o.probability<=1 or o.capacity<=0 or o.cost<0 for o in self.options): raise ValueError('invalid radio options')
        if any(d.rate<=0 for d in demands): raise ValueError('invalid traffic rate')
        self.scenarios=[None]+self.protect_nodes
        self.ykeys=[(e,j) for e in self.arcs for j in range(len(self.options))]
        self.yindex={k:i for i,k in enumerate(self.ykeys)}
        self.cost=np.array([self.options[j].cost for e,j in self.ykeys])
        self.capacity=np.array([self.options[j].capacity for e,j in self.ykeys])
        self.log_probability=np.array([log(self.options[j].probability) for e,j in self.ykeys])
        self.xkeys=[(h,k,e) for h in self.scenarios for k,d in enumerate(self.demands) if h not in (d.source,d.target) for e in self.arcs if h not in e]
        self.xindex={k:i for i,k in enumerate(self.xkeys)}

    def flow_matrices(self):
        """Return A_eq x=b_eq, A_ub x <= B_ub y + d; B rows capacity only."""
        ne=len(self.xkeys); ny=len(self.ykeys)
        eq=[]; rhs=[]; ub=[]; brhs=[]; B=[]
        for h in self.scenarios:
            for k,d in enumerate(self.demands):
                if h in (d.source,d.target): continue
                for n in self.nodes:
                    if n==h: continue
                    row=np.zeros(ne)
                    for e in self.arcs:
                        key=(h,k,e)
                        if key in self.xindex:
                            if e[0]==n: row[self.xindex[key]]+=1
                            if e[1]==n: row[self.xindex[key]]-=1
                    eq.append(row); rhs.append((d.rate if h is None else d.rate*self.alpha)*(1 if n==d.source else -1 if n==d.target else 0))
                if h is None:
                    for e in self.arcs:
                        row=np.zeros(ne);row[self.xindex[h,k,e]]=1
                        ub.append(row);brhs.append(self.sigma*d.rate);B.append(np.zeros(ny))
                    for n in self.nodes:
                        if n==d.source: continue
                        row=np.zeros(ne)
                        for e in self.arcs:
                            if e[0]==n: row[self.xindex[h,k,e]]+=1
                        ub.append(row);brhs.append(self.sigma*d.rate);B.append(np.zeros(ny))
            for e in self.arcs:
                if h in e:continue
                row=np.zeros(ne);br=np.zeros(ny)
                for k,d in enumerate(self.demands):
                    if (h,k,e) in self.xindex: row[self.xindex[h,k,e]]=1
                for j,opt in enumerate(self.options):br[self.yindex[e,j]]=opt.capacity
                ub.append(row);brhs.append(0.);B.append(br)
        return (np.array(eq).reshape(-1,ne),np.array(rhs),np.array(ub).reshape(-1,ne),
                np.array(brhs),np.array(B).reshape(-1,ny))

    def master(self,cuts=()):
        """MILP master: one radio configuration per edge + joint reliability + cuts."""
        ny=len(self.ykeys); rows=[]; lowers=[]; uppers=[]
        for e in self.arcs:
            a=np.zeros(ny)
            for j in range(len(self.options)):a[self.yindex[e,j]]=1
            rows.append(a);lowers.append(-np.inf);uppers.append(1.)
        rows.append(self.log_probability);lowers.append(log(1-self.epsilon));uppers.append(np.inf)
        for a,b in cuts:
            rows.append(a);lowers.append(-np.inf);uppers.append(b)
        return milp(self.cost,integrality=np.ones(ny),bounds=Bounds(np.zeros(ny),np.ones(ny)),
                    constraints=LinearConstraint(np.array(rows),np.array(lowers),np.array(uppers)),
                    options={'mip_rel_gap':1e-9})

    def format_solution(self,y,flows=None,**kw):
        selected=[{'arc':list(e),'capacity_mbps':self.options[j].capacity,'bandwidth_mhz':self.options[j].bandwidth,
                   'probability':self.options[j].probability,'cost':self.options[j].cost}
                  for (e,j),val in zip(self.ykeys,y) if val>.5]
        return dict(cost=float(self.cost@y),joint_reliability=float(np.prod([v['probability'] for v in selected])),
                    selected_links=selected,**kw)

def solve_monolithic(inst):
    """Baseline MILP solving binary options and scenario-specific continuous flows jointly."""
    ny=len(inst.ykeys); nx=len(inst.xkeys)
    Aeq,beq,Aub,d,B=inst.flow_matrices()
    matrix=lil_matrix((len(beq)+len(d)+len(inst.arcs)+1,ny+nx))
    lb=[];ub=[];r=0
    for i,row in enumerate(Aeq):matrix[r,ny:]=row;lb.append(beq[i]);ub.append(beq[i]);r+=1
    for i,row in enumerate(Aub):matrix[r,:ny]=-B[i];matrix[r,ny:]=row;lb.append(-np.inf);ub.append(d[i]);r+=1
    for e in inst.arcs:
        for j in range(len(inst.options)):matrix[r,inst.yindex[e,j]]=1
        lb.append(-np.inf);ub.append(1);r+=1
    matrix[r,:ny]=inst.log_probability;lb.append(log(1-inst.epsilon));ub.append(np.inf)
    res=milp(np.r_[inst.cost,np.zeros(nx)],integrality=np.r_[np.ones(ny),np.zeros(nx)],
             bounds=Bounds(np.zeros(ny+nx),np.r_[np.ones(ny),np.full(nx,np.inf)]),
             constraints=LinearConstraint(matrix.tocsr(),lb,ub),options={'mip_rel_gap':1e-9})
    if res.x is None:return {'feasible':False,'status':res.message}
    return inst.format_solution(res.x[:ny],feasible=True,optimal=res.status==0,status=res.message,
                                flows={str(key):float(res.x[ny+i]) for key,i in inst.xindex.items() if res.x[ny+i]>1e-7})
