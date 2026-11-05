"""P1 — 27: inference for the final manuscript.

- Paired contrasts of each degradation condition against the FULL-MONTAGE reference and
  against the CLEAN single-channel chain (fz_128_quant_band), with t-tests.
- Benjamini-Hochberg FDR across the condition family.
- Affective one-sample tests vs chance, and paired full-vs-single tests.
- Equivalence (TOST) for Emotiv vs matched high-end on valence/arousal.
Output: results/inference.json
"""
from __future__ import annotations
import glob, json, pathlib
import numpy as np
from scipy.stats import t as _t, ttest_1samp, ttest_rel

def ci(v):
    a=np.asarray(v,float); n=len(a); m=float(a.mean())
    sem=a.std(ddof=1)/np.sqrt(n) if n>1 else 0
    tc=float(_t.ppf(0.975,max(n-1,1)))
    return {"n":n,"mean":m,"ci_low":float(m-tc*sem),"ci_high":float(m+tc*sem)}

def bh(pvals):
    p=np.asarray(pvals,float); n=len(p); order=np.argsort(p)
    q=np.empty(n); prev=1.0
    for rank,i in enumerate(order[::-1], start=1):
        val=min(prev, p[i]*n/(n-rank+1)); q[i]=val; prev=val
    return q

def main():
    runs=[json.loads(pathlib.Path(f).read_text()) for f in sorted(glob.glob('results/metrics_S*.json'))]
    conds=[c for c in runs[0]['alpha_reactivity'] if c!='ref']
    ref=np.array([r['alpha_reactivity']['ref']['log_ratio'] for r in runs])
    chain=np.array([r['alpha_reactivity']['fz_128_quant_band']['log_ratio'] for r in runs])
    out={"n_subjects":len(runs),"alpha":{}}
    p_ref=[]; p_chain=[]
    for c in conds:
        v=np.array([r['alpha_reactivity'][c]['log_ratio'] for r in runs])
        d_ref=v-ref; d_chain=v-chain
        p_ref.append(float(ttest_rel(v,ref).pvalue)); p_chain.append(float(ttest_rel(v,chain).pvalue))
        out["alpha"][c]={"vs_ref":ci(d_ref),"vs_chain":ci(d_chain),
                         "retention_vs_ref_geometric":float(np.exp(d_ref.mean()))}
    q_ref=bh(p_ref); q_chain=bh(p_chain)
    for c,qr,qc,pr,pc in zip(conds,q_ref,q_chain,p_ref,p_chain):
        out["alpha"][c].update({"p_vs_ref":pr,"q_vs_ref":float(qr),
                                "p_vs_chain":pc,"q_vs_chain":float(qc)})

    aff=json.loads(pathlib.Path('results/affective.json').read_text())
    rows=aff['recordings']
    out["affective"]={}
    aff_keys=[("valence_full",0.5),("valence_single",0.5),
              ("arousal_full",0.5),("arousal_single",0.5),
              ("quadrant_full",0.25),("quadrant_single",0.25)]
    p_aff=[]
    for name,chance in aff_keys:
        vals=[r['targets'][name]['balanced_accuracy'] for r in rows if r['targets'].get(name,{}).get('balanced_accuracy') is not None]
        tt=ttest_1samp(vals,chance)
        p_aff.append(float(tt.pvalue))
        c=ci(vals)
        out["affective"][name]={"mean":float(np.mean(vals)),"ci_low":c['ci_low'],"ci_high":c['ci_high'],
                                "p_vs_chance":float(tt.pvalue),
                                "dz":float((np.mean(vals)-chance)/np.std(vals,ddof=1)) if len(vals)>1 else None,
                                "floor_60pct":bool(c['ci_low']>0.60)}
    q_aff=bh(p_aff)
    for (name,chance),q in zip(aff_keys,q_aff):
        out["affective"][name]["q_vs_chance"]=float(q)
    # paired full-vs-single
    for tgt in ["valence","arousal","quadrant"]:
        f=[r['targets'][f'{tgt}_full']['balanced_accuracy'] for r in rows]
        s=[r['targets'][f'{tgt}_single']['balanced_accuracy'] for r in rows]
        d=np.array(f)-np.array(s)
        out["affective"][f"{tgt}_full_minus_single"]={"mean":float(d.mean()),
            "ci_low":ci(d)["ci_low"],"ci_high":ci(d)["ci_high"],"p":float(ttest_rel(f,s).pvalue)}

    dc=json.loads(pathlib.Path('results/device_compare.json').read_text())
    out["device_equivalence"]={}
    for tgt in ["valence","arousal","quadrant"]:
        t=dc['targets'][tgt]; d=t['low_minus_high']; mean=d['mean']
        n=dc['n_common']; sem=(d['ci_high']-d['mean'])/float(_t.ppf(0.975,max(n-1,1))) if n>1 else 0
        margin=0.10  # equivalence margin +/-10 accuracy points
        p_tost=max(float(1-_t.cdf((mean+margin)/sem, n-1)), float(_t.cdf((mean-margin)/sem, n-1))) if sem>0 else 1.0
        out["device_equivalence"][tgt]={"mean_diff":mean,"ci_low":d['ci_low'],"ci_high":d['ci_high'],
                                        "margin":margin,"tost_p":p_tost}
    pathlib.Path('results/inference.json').write_text(json.dumps(out,indent=2))
    print("n_subjects:", out["n_subjects"])
    print("alpha conditions:", len(out["alpha"]))
    print("affective:", {k: round(v.get("mean",0),3) for k,v in out["affective"].items() if isinstance(v,dict)})
    print("TOST:", {k: round(v["tost_p"],3) for k,v in out["device_equivalence"].items()})

if __name__=='__main__': main()
