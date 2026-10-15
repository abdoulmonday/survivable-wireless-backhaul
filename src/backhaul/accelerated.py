"""Teaching-oriented Benders with lazy directed capacity cutset separation.

Not the paper's complete accelerated algorithm. Cutsets are valid necessary
inequalities, added to the master before invoking the elastic flow LP oracle.
"""
import numpy as np
from .model import Instance
from .benders import elastic_oracle
from .cutsets import separate_cutsets


def solve_accelerated(inst:Instance,max_iterations=200,tol=1e-7,max_nodes=12,
                      max_cuts_per_iteration=20):
    cuts=[];history=[];n_cutsets=0;n_benders=0;oracle_calls=0
    for iteration in range(1,max_iterations+1):
        master=inst.master(cuts)
        if master.x is None:
            return {'feasible':False,'status':master.message,'iterations':iteration,
                    'history':history,'cutset_cuts':n_cutsets,'benders_cuts':n_benders,
                    'oracle_calls':oracle_calls}
        # Never claim optimality when the master solver does not finish.
        if master.status!=0:
            return {'feasible':False,'status':f'Master did not finish optimally: {master.message}',
                    'iterations':iteration,'history':history,'cutset_cuts':n_cutsets,
                    'benders_cuts':n_benders,'oracle_calls':oracle_calls}
        y=np.round(master.x).astype(float)
        separated=separate_cutsets(inst,y,max_nodes=max_nodes,tol=tol,
                                  limit=max_cuts_per_iteration)
        if separated:
            cuts.extend((coeff.copy(),rhs) for _,coeff,rhs,_ in separated)
            n_cutsets+=len(separated)
            history.append({'iteration':iteration,'master_lower_bound':float(master.fun),
                            'kind':'cutsets','added':len(separated),
                            'max_cutset_violation':float(separated[0][0])})
            continue
        violation,gradient,rhs,_=elastic_oracle(inst,y)
        oracle_calls+=1
        history.append({'iteration':iteration,'master_lower_bound':float(master.fun),
                        'kind':'flow_oracle','feasibility_violation':violation})
        if violation<=tol:
            return inst.format_solution(y,feasible=True,optimal=True,status='optimal',
                                        iterations=iteration,history=history,
                                        cutset_cuts=n_cutsets,benders_cuts=n_benders,
                                        oracle_calls=oracle_calls)
        if np.max(np.abs(gradient),initial=0)<tol:
            return {'feasible':False,'status':'No capacity decision repairs routing',
                    'iterations':iteration,'history':history,'cutset_cuts':n_cutsets,
                    'benders_cuts':n_benders,'oracle_calls':oracle_calls}
        cuts.append((gradient.copy(),rhs));n_benders+=1
    return {'feasible':False,'status':'iteration_limit','iterations':max_iterations,
            'history':history,'cutset_cuts':n_cutsets,'benders_cuts':n_benders,
            'oracle_calls':oracle_calls}
