"""P1 — 29: decomposition figure (full -> chain -> single sites, plus band controls)."""
import json, pathlib
import numpy as np

def main():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    d=json.loads(pathlib.Path('results/affective_decomp.json').read_text())['summary']
    conds=[("full","full"),("hz128","128 Hz"),("quant","+quant"),("band","+band"),
           ("full_theta_alpha","θ+α only"),("full_beta","β only"),
           ("single_Fz","Fz"),("single_Cz","Cz"),("single_Pz","Pz"),("single_Oz","Oz")]
    targs=[("valence","valence",0.5),("arousal","arousal",0.5),("quadrant","4-class",0.25)]
    fig,ax=plt.subplots(figsize=(12,4.6))
    width=0.26
    for ti,(key,lab,chance) in enumerate(targs):
        vals=[d[key][c]['mean'] for c,_ in conds]
        err=[[v-d[key][c]['ci_low'] for v,(c,_) in zip(vals,conds)],
             [d[key][c]['ci_high']-v for v,(c,_) in zip(vals,conds)]]
        ax.bar(np.arange(len(conds))+ti*width, vals, width, yerr=err, capsize=3, label=lab)
    ax.set_xticks(np.arange(len(conds))+width)
    ax.set_xticklabels([l for _,l in conds], rotation=20, fontsize=8)
    ax.axhline(0.5,color='k',ls='--',lw=1); ax.axhline(0.25,color='gray',ls=':',lw=1)
    ax.set_ylabel('balanced accuracy'); ax.set_ylim(0.2,0.8)
    ax.legend(ncol=3, fontsize=8)
    fig.tight_layout()
    pathlib.Path('figures').mkdir(exist_ok=True)
    fig.savefig('figures/fig4_decomp.pdf'); fig.savefig('figures/fig4_decomp.png',dpi=300)
    print('wrote figures/fig4_decomp.pdf')

if __name__=='__main__': main()
