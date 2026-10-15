"""Classical Benders feasibility-cut decomposition using an elastic LP oracle.

This independently implemented teaching variant is NOT the paper's accelerated
algorithm. SciPy/HiGHS dual marginals produce valid supporting hyperplanes.
"""
import numpy as np
from scipy.optimize import linprog
from .model import Instance


def elastic_oracle(inst:Instance,y):
    """min L1 equality violations + upper-bound violations, with nonnegative flows.

    Value theta(y) >= 0. Every selected design is feasible iff theta(y) ~= 0.
    The LP value is convex in the capacity RHS; its dual marginals give a
    globally valid affine under-estimator and hence a Benders feasibility cut.
    """
    eq, beq, ub, d, B=inst.flow_matrices()
    nx=len(inst.xkeys); me=len(beq); mu=len(d)
    # variables [x>=0, positive equality slack, negative equality slack, inequality slack]
    c=np.r_[np.zeros(nx),np.ones(2*me+mu)]
    Aeq=np.c_[eq,np.eye(me),-np.eye(me),np.zeros((me,mu))]
    Aub=np.c_[ub,np.zeros((mu,2*me)),-np.eye(mu)]
    lp=linprog(c,A_ub=Aub,b_ub=d+B@y,A_eq=Aeq,b_eq=beq,bounds=(0,None),method='highs')
    if not lp.success:raise RuntimeError(f'elastic LP failed: {lp.message}')
    # scipy marginals: d(theta)/d(b_upper); d(b_upper)/dy = B
    gradient=lp.ineqlin.marginals@B
    cut_rhs=float(gradient@y-lp.fun)  # theta_hat + g*(y-y_hat) <= 0
    return float(lp.fun),np.asarray(gradient),cut_rhs,lp


def solve_benders(inst:Instance,max_iterations=200,tol=1e-7):
    cuts=[];history=[]
    for iteration in range(1,max_iterations+1):
        master=inst.master(cuts)
        if master.x is None:
            return {'feasible':False,'status':master.message,'iterations':iteration,'history':history}
        y=np.round(master.x).astype(float)
        violation,gradient,rhs,lp=elastic_oracle(inst,y)
        history.append({'iteration':iteration,'master_lower_bound':float(master.fun),
                        'feasibility_violation':violation,'cuts':len(cuts)})
        if violation<=tol:
            return inst.format_solution(y,feasible=True,optimal=master.status==0,
                                        iterations=iteration,history=history,
                                        status='optimal' if master.status==0 else master.message)
        if abs(gradient).max(initial=0)<tol:
            return {'feasible':False,'status':'No capacity decision can repair violated routing constraints',
                    'iterations':iteration,'history':history}
        # Valid by weak LP duality: theta(y) >= theta(yhat) + gradient@(y-yhat).
        # Necessary condition for feasible y: gradient@y <= gradient@yhat - theta(yhat).
        cuts.append((gradient.copy(),rhs))
    return {'feasible':False,'status':'iteration_limit','iterations':max_iterations,'history':history}
