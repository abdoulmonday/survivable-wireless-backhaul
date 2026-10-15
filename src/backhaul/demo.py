import json
from pathlib import Path
from .model import Demand,Option,Instance,solve_monolithic
from .benders import solve_benders

def example():
    return Instance(['A','B','C','D'], [('A','B'),('B','D'),('A','C'),('C','D'),('B','C'),('C','B')],
                    [Demand('A','D',30)],
                    [Option(7,3.6,.999,7),Option(14,3.6,.999,14),Option(28,3.6,.999,28),Option(14,5.4,.98,14)],
                    sigma=.5,alpha=1.,epsilon=.05,protect_nodes=['B','C'])

def main():
    ins=example()
    mon=solve_monolithic(ins); ben=solve_benders(ins)
    Path('outputs').mkdir(exist_ok=True)
    Path('outputs/comparison.json').write_text(json.dumps({'monolithic':mon,'benders':ben},indent=2))
    print('Monolithic:',mon['cost'],' Benders:',ben.get('cost'),' iterations:',ben['iterations'])
    print('Results: outputs/comparison.json')
if __name__=='__main__':main()
