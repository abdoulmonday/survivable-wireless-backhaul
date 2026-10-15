import math
from backhaul import Instance,Demand,Option,solve_benders,solve_monolithic
from backhaul.demo import example

def test_benders_equals_monolithic():
    ins=example(); a=solve_monolithic(ins); b=solve_benders(ins)
    assert a['optimal'] and b['optimal']
    assert math.isclose(a['cost'],b['cost'],abs_tol=1e-5)
    assert b['joint_reliability']>=1-ins.epsilon-1e-10
    assert b['iterations']>1

def test_no_redundancy_is_infeasible():
    ins=Instance(['A','B','D'],[('A','B'),('B','D')],[Demand('A','D',20)],
                 [Option(14,3.6,.999,1)],sigma=1.,alpha=1.,protect_nodes=['B'])
    assert not solve_benders(ins)['feasible']
    assert not solve_monolithic(ins)['feasible']

def test_minimum_reliability():
    ins=Instance(['A','D'],[('A','D')],[Demand('A','D',20)],
                 [Option(7,3.6,.8,1),Option(7,3.6,.99,2)],sigma=1.,alpha=0.,protect_nodes=[])
    b=solve_benders(ins)
    assert b['optimal'] and b['cost']==2

def test_low_traffic_simple_route():
    ins=Instance(['A','D'],[('A','D')],[Demand('A','D',5)],
                 [Option(7,3.6,.999,7)],sigma=1.,alpha=1.,protect_nodes=[])
    assert solve_monolithic(ins)['cost']==solve_benders(ins)['cost']==7
