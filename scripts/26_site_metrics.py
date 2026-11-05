"""P1 — 26: correct site-matched and blink metrics from existing JSONs.

- Reactivity-based acquisition-chain cost: Fz-in-full-recording (condition fz) versus
  Fz after the full chain (fz_128_quant_band), per subject, paired t CI.
- Electrode-site cost: Fz eyes-closed alpha power versus posterior-channel average
  (from alpha_site_sensitivity per-subject rows).
- Blink-vs-clean paired contrast: fz_blink30 minus fz_128_quant_band.
Output: results/site_metrics.json
"""
from __future__ import annotations
import glob, json, pathlib
import numpy as np
from scipy.stats import t as _t


def ci(v):
    a=np.asarray(v,float); n=len(a); m=float(a.mean())
    sem=a.std(ddof=1)/np.sqrt(n) if n>1 else 0.0
    t=float(_t.ppf(0.975,max(n-1,1)))
    return {"n":n,"mean":m,"ci_low":float(m-t*sem),"ci_high":float(m+t*sem)}


def main():
    runs=[json.loads(pathlib.Path(f).read_text()) for f in sorted(glob.glob('results/metrics_S*.json'))]
    chain=[]; blink=[]; fz=[];
    for r in runs:
        a=r['alpha_reactivity']
        chain.append(a['fz_128_quant_band']['log_ratio']-a['fz']['log_ratio'])
        blink.append(a['fz_blink30']['log_ratio']-a['fz_128_quant_band']['log_ratio'])
        fz.append(a['fz']['log_ratio'])
    site=json.loads(pathlib.Path('results/alpha_site_sensitivity.json').read_text())
    post=[np.log(row['ref_fz']/row['ref_posterior']) for row in site['per_subject'] if row.get('ref_posterior')]
    out={
      "n": len(runs),
      "chain_cost_log": ci(chain),
      "chain_retention": {k:(np.exp(v) if k=='mean' else np.exp(v)) for k,v in ci(chain).items() if k!='n'},
      "blink_vs_clean_log": ci(blink),
      "fz_vs_posterior_log": ci(post),
      "fz_posterior_ratio": ci(np.exp(np.asarray(post,float))),
      "note": "chain_cost is the reactivity difference Fz-full vs Fz-degraded; negative means degradation lowers the effect. Blink contrast is blink30 minus clean chain.",
    }
    pathlib.Path('results/site_metrics.json').write_text(json.dumps(out,indent=2))
    print(json.dumps(out,indent=2))

if __name__=='__main__': main()
