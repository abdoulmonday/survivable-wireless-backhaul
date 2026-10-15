"""Small-instance MILP inspired by Raayatpanah et al. (2023), Eq. (5).

Demands in Mbit/s, bandwidth in MHz, spectral efficiency in bit/s/Hz.
"""
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
    def capacity(self):
        return self.bandwidth * self.efficiency


def solve(nodes, arcs, demands, options, sigma=0.5, alpha=1.0, epsilon=0.05,
          protect_nodes=None, time_limit=60):
    """Solve a deterministic-equivalent joint reliability and failure routing MILP.

    Scenario 0 is intact; each protected relay failure removes that node and
    incident arcs. Diversification applies only to intact scenario.
    Radio options are synthetic unless independently calibrated.
    """
    nodes=list(nodes); arcs=list(map(tuple,arcs)); demands=list(demands)
    assert 0 < sigma <= 1 and 0 <= alpha <= 1 and 0 < epsilon < 1
    assert all(0 < o.probability <= 1 for o in options)
    protected=list(protect_nodes if protect_nodes is not None else
                   [n for n in nodes if n not in {d.source for d in demands}|{d.target for d in demands}])
    scenarios=[None]+protected
    variables=[]; costs=[]; binary=[]
    y={}; x={}
    for e in arcs:
        for j,opt in enumerate(options):
            y[e,j]=len(variables); variables.append(('y',e,j)); costs.append(opt.cost); binary.append(1)
    for h in scenarios:
        live=[e for e in arcs if h not in e]
        for k,d in enumerate(demands):
            if h in (d.source,d.target): continue
            for e in live:
                x[h,k,e]=len(variables); variables.append(('x',h,k,e)); costs.append(0); binary.append(0)
    rows=[]
    def add(coeff, lb=-np.inf, ub=np.inf):
        rows.append((coeff,lb,ub))
    for e in arcs:
        add({y[e,j]:1 for j in range(len(options))},ub=1)
    # Joint reliability (the inactive link is a factor of 1).
    add({y[e,j]:log(o.probability) for e in arcs for j,o in enumerate(options)},lb=log(1-epsilon))
    for h in scenarios:
        live_nodes=[n for n in nodes if n!=h]; live=[e for e in arcs if h not in e]
        for k,d in enumerate(demands):
            if h in (d.source,d.target): continue
            amount=d.rate*(1 if h is None else alpha)
            for n in live_nodes:
                co={}
                for e in live:
                    idx=x[h,k,e]
                    if e[0]==n: co[idx]=co.get(idx,0)+1
                    if e[1]==n: co[idx]=co.get(idx,0)-1
                rhs=amount if n==d.source else (-amount if n==d.target else 0)
                add(co,lb=rhs,ub=rhs)
            if h is None:
                for e in live:
                    add({x[h,k,e]:1},ub=sigma*d.rate)
                # Outflow diversification; omit source as in Eq. 5d.
                for n in live_nodes:
                    if n!=d.source:
                        add({x[h,k,e]:1 for e in live if e[0]==n},ub=sigma*d.rate)
        for e in live:
            co={x[h,k,e]:1 for k,d in enumerate(demands) if (h,k,e) in x}
            for j,opt in enumerate(options): co[y[e,j]]=-opt.capacity
            add(co,ub=0)
    mat=lil_matrix((len(rows),len(variables)),dtype=float)
    for r,(co,_,_) in enumerate(rows):
        for i,v in co.items():mat[r,i]=v
    res=milp(np.array(costs),integrality=np.array(binary),bounds=Bounds(np.zeros(len(variables)),np.full(len(variables),np.inf)),
             constraints=LinearConstraint(mat.tocsr(),[r[1] for r in rows],[r[2] for r in rows]),
             options={'time_limit':time_limit,'mip_rel_gap':1e-6})
    if res.x is None: return {'status':str(res.message),'feasible':False}
    chosen=[]
    for e in arcs:
        for j,opt in enumerate(options):
            if res.x[y[e,j]]>0.5:
                chosen.append({'arc':list(e),'bandwidth_mhz':opt.bandwidth,'efficiency':opt.efficiency,
                               'capacity_mbps':opt.capacity,'probability':opt.probability,'cost':opt.cost})
    flows=[]
    for (h,k,e),idx in x.items():
        if res.x[idx]>1e-6:
            flows.append({'failure':h if h is not None else 'none','demand':k,'arc':list(e),'mbps':round(float(res.x[idx]),6)})
    reliability=float(np.prod([c['probability'] for c in chosen]))
    return {'status':str(res.message),'feasible':True,'optimal':res.status==0,
            'cost':float(res.fun),'joint_reliability':reliability,
            'selected_links':chosen,'flows':flows,'scenarios':['none']+protected,
            'mip_gap':float(res.mip_gap) if res.mip_gap is not None else None}
