import math
import numpy as np
from backhaul import Demand,Option,Instance,solve_monolithic,solve_benders,solve_accelerated
from backhaul.cutsets import separate_cutsets
from backhaul.demo import example


def test_cutset_finds_missing_capacity():
    inst=Instance(['A','B','D'],[('A','B'),('B','D')], [Demand('A','D',20)],
                  [Option(7,3.6,.999,1)],sigma=1,alpha=1,protect_nodes=['B'])
    violations=separate_cutsets(inst,np.zeros(len(inst.ykeys)))
    assert violations and violations[0][0]>=20


def test_accelerated_equals_milp_on_demo():
    inst=example()
    ref=solve_monolithic(inst)
    out=solve_accelerated(inst)
    assert ref['optimal'] and out['optimal']
    assert math.isclose(ref['cost'],out['cost'],abs_tol=1e-6)
    assert out['joint_reliability']>=1-inst.epsilon-1e-10
    assert out['cutset_cuts']>0


def test_simple_low_traffic():
    inst=Instance(['A','D'],[('A','D')],[Demand('A','D',5)],
                  [Option(7,3.6,.999,7)],sigma=1.,alpha=1.,protect_nodes=[])
    assert solve_accelerated(inst)['cost']==solve_benders(inst)['cost']==7


def test_infeasible_missing_backup():
    inst=Instance(['A','B','D'],[('A','B'),('B','D')], [Demand('A','D',20)],
                  [Option(14,3.6,.999,1)],sigma=1,alpha=1,protect_nodes=['B'])
    assert not solve_accelerated(inst)['feasible']


def test_counterflow_not_subtracted_from_cut():
    inst=Instance(['A','D'],[('A','D'),('D','A')],
                  [Demand('A','D',8),Demand('D','A',8)],
                  [Option(7,3.6,.999,1)],sigma=1,alpha=0,protect_nodes=[])
    cuts=separate_cutsets(inst,np.zeros(len(inst.ykeys)))
    assert len(cuts)==2
    assert all(abs(c[0]-8)<1e-7 for c in cuts)
