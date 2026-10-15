import argparse
import json
from pathlib import Path
from .model import Demand, Option, solve


def run(output='outputs', sigma=0.5, alpha=1.0, epsilon=0.05):
    # Deliberately small synthetic example, NOT an instance from the paper.
    nodes=['A','B','C','D']
    arcs=[('A','B'),('B','D'),('A','C'),('C','D'),('B','C'),('C','B')]
    demands=[Demand('A','D',30)]
    options=[Option(7,3.6,.999,7), Option(14,3.6,.999,14),
             Option(28,3.6,.999,28), Option(14,5.4,.98,14)]
    result=solve(nodes,arcs,demands,options,sigma,alpha,epsilon,protect_nodes=['B','C'])
    path=Path(output);path.mkdir(parents=True,exist_ok=True)
    (path/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    if result['feasible']:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import networkx as nx
        g=nx.DiGraph();g.add_nodes_from(nodes)
        for link in result['selected_links']:g.add_edge(*link['arc'],capacity=link['capacity_mbps'])
        pos={'A':(0,0),'B':(1,1),'C':(1,-1),'D':(2,0)}
        fig,ax=plt.subplots(figsize=(7,4))
        nx.draw_networkx(g,pos,ax=ax,arrows=True,node_color='#deecfa',node_size=850,edge_color='#3477aa',font_weight='bold')
        nx.draw_networkx_edge_labels(g,pos,edge_labels={(u,v):f"{p['capacity']:.1f}" for u,v,p in g.edges(data=True)},ax=ax,font_size=8)
        ax.set_title('Provisioned backhaul links (Mbit/s)');ax.axis('off');fig.tight_layout()
        fig.savefig(path/'network.png',dpi=180);plt.close(fig)
    print(json.dumps({k:v for k,v in result.items() if k!='flows'},indent=2))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',default='outputs');p.add_argument('--sigma',type=float,default=.5)
    p.add_argument('--alpha',type=float,default=1.);p.add_argument('--epsilon',type=float,default=.05)
    a=p.parse_args();run(a.output,a.sigma,a.alpha,a.epsilon)
