import math
from backhaul.model import Demand, Option, solve


def test_protected_two_routes():
    nodes=['A','B','C','D']
    edges=[('A','B'),('B','D'),('A','C'),('C','D')]
    result=solve(nodes,edges,[Demand('A','D',20)],
                 [Option(14,3.6,.999,1)],sigma=.5,alpha=1.,epsilon=.05,protect_nodes=['B','C'])
    assert result['optimal']
    assert len(result['selected_links'])==4
    assert result['joint_reliability']>=.95
    for failed in ['B','C']:
        injected=sum(f['mbps'] for f in result['flows'] if f['failure']==failed and f['arc'][0]=='A')
        assert math.isclose(injected,20)


def test_infeasible_without_redundancy():
    result=solve(['A','B','D'],[('A','B'),('B','D')],[Demand('A','D',20)],
                 [Option(14,3.6,.999,1)],sigma=1.,alpha=1.,protect_nodes=['B'])
    assert not result['feasible']


def test_joint_probability_restricts_choices():
    r=solve(['A','D'],[('A','D')],[Demand('A','D',20)],
            [Option(7,3.6,.8,1),Option(7,3.6,.99,2)],sigma=1.,alpha=0.,epsilon=.05,protect_nodes=[])
    assert r['optimal'] and r['cost']==2
