"""Construct the synthetic baseline; also provide a command-line demo."""
import json
from pathlib import Path
from .model import Demand,Option,Instance,solve_monolithic
from .benders import solve_benders
from .accelerated import solve_accelerated

def example():
    return Instance(['A','B','C','D'], [('A','B'),('B','D'),('A','C'),('C','D'),('B','C'),('C','B')],
                    [Demand('A','D',30)],
                    [Option(7,3.6,.999,7),Option(14,3.6,.999,14),Option(28,3.6,.999,28),Option(14,5.4,.98,14)],
                    sigma=.5,alpha=1.,epsilon=.05,protect_nodes=['B','C'])

def main():
    ins=example()
    results={'monolithic':solve_monolithic(ins),'benders':solve_benders(ins),
             'cutset_benders':solve_accelerated(ins)}
    Path('outputs').mkdir(exist_ok=True)
    Path('outputs/comparison.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    for key,value in results.items():
        print(f'{key}: cost={value.get("cost")}, feasible={value["feasible"]}, iterations={value.get("iterations", "n/a")}')
    print('Results: outputs/comparison.json')
if __name__=='__main__':main()
