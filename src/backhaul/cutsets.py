"""Valid directed capacity cutset inequalities for survivable multicommodity flows.

For each operational failure scenario h and vertex subset S, the total installed
capacity crossing S -> V_h\S must be at least the sum of demand volumes with
sources in S and destinations outside S. These inequalities are *necessary*,
not sufficient. Their separation here is exhaustive, intended for small graphs.
"""
from itertools import combinations
import numpy as np


def generate_cutsets(inst, max_nodes=12):
    """Yield (master_coefficient, rhs, metadata) with coeff@y <= rhs.

    The coefficients are negative so that a capacity lower bound fits the
    existing master MILP API. Enumerating 2^n cuts is NOT scalable; production
    separation would require min-cut or another dedicated separation algorithm.
    """
    if len(inst.nodes) > max_nodes:
        raise ValueError(f'Exhaustive cutset enumeration is limited to {max_nodes} nodes')
    seen=set()
    for failure in inst.scenarios:
        live=[n for n in inst.nodes if n != failure]
        if len(live)<2:
            continue
        for size in range(1,len(live)):
            for subset in combinations(live,size):
                S=set(subset)
                volume=sum(d.rate*(1 if failure is None else inst.alpha)
                           for d in inst.demands
                           if failure not in (d.source,d.target)
                           and d.source in S and d.target not in S)
                if volume <= 1e-10:
                    continue
                coeff=np.zeros(len(inst.ykeys))
                for e in inst.arcs:
                    if failure in e or e[0] not in S or e[1] in S:
                        continue
                    for j,o in enumerate(inst.options):
                        coeff[inst.yindex[e,j]]=-o.capacity
                # Ignore duplicates across scenarios (retain strongest RHS).
                key=tuple(np.round(coeff,10))
                if key not in seen:
                    seen.add(key)
                    yield coeff,-float(volume),{'failure':failure,'subset':list(subset),'required_mbps':float(volume)}
                else:
                    # identical coefficients may have different rhs; caller merges strongest
                    yield coeff,-float(volume),{'failure':failure,'subset':list(subset),'required_mbps':float(volume)}


def separate_cutsets(inst,y,max_nodes=12,tol=1e-7,limit=20):
    """Return the most violated capacity cuts for candidate binary design y."""
    by_coeff={}
    for coeff,rhs,metadata in generate_cutsets(inst,max_nodes=max_nodes):
        violation=float(coeff@y-rhs)
        if violation<=tol:
            continue
        key=tuple(np.round(coeff,10))
        old=by_coeff.get(key)
        if old is None or violation>old[0]:
            by_coeff[key]=(violation,coeff,rhs,metadata)
    return sorted(by_coeff.values(),key=lambda t:-t[0])[:limit]
