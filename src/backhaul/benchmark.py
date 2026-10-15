"""Repeatable small-graph timing experiment (not a scalability claim)."""
import json
from pathlib import Path
from time import perf_counter
import argparse
from .demo import example
from .model import Demand, Option, Instance, solve_monolithic
from .benders import solve_benders
from .accelerated import solve_accelerated


def cases():
    base = example()
    low = Instance(base.nodes, base.arcs, [Demand('A','D',10)], base.options,
                   sigma=.5,alpha=1.,epsilon=.05,protect_nodes=['B','C'])
    return [('demo_30mbps',base),('light_10mbps',low)]


def run(path='outputs/benchmark.json'):
    results=[]
    for name,ins in cases():
        for method,solver in [('milp',solve_monolithic),('benders',solve_benders),('cutset_benders',solve_accelerated)]:
            start=perf_counter()
            result=solver(ins)
            elapsed=perf_counter()-start
            results.append({'case':name,'method':method,'seconds':round(elapsed,6),
                            'feasible':result['feasible'],'optimal':result.get('optimal',False),
                            'cost':result.get('cost'),'iterations':result.get('iterations'),
                            'cutset_cuts':result.get('cutset_cuts'),
                            'oracle_calls':result.get('oracle_calls')})
    output=Path(path);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(results,indent=2),encoding='utf-8')
    for x in results:print(f"{x['case']:15} {x['method']:16} cost={str(x['cost']):>6} seconds={x['seconds']:.4f} iterations={x['iterations']}")
    return results

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',default='outputs/benchmark.json')
    args=parser.parse_args();run(args.output)
