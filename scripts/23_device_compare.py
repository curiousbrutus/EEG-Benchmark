"""P1 — 23: within-subject device comparison on overlapping subjects.

Compares high-end full montage, low-cost Emotiv and high-end single-channel accuracy
on the subjects present in both datasets, with paired differences and 95% CI.
"""
import json, pathlib, re
import numpy as np
from scipy.stats import t as _t

def subj_from_rec(name):
    m = re.search(r'eegbci(\d+)-', name)
    return int(m.group(1)) if m else None

def mean_ci(v):
    a = np.asarray(v, float); n = len(a)
    if n < 2: return float(a.mean()), float('nan'), float('nan')
    sem = a.std(ddof=1)/np.sqrt(n)
    t = float(_t.ppf(0.975, max(n - 1, 1)))
    return float(a.mean()), float(a.mean()-t*sem), float(a.mean()+t*sem)

aff = json.loads(pathlib.Path('results/affective.json').read_text())
emo = json.loads(pathlib.Path('results/emotiv.json').read_text())

high = {}
for r in aff['recordings']:
    s = subj_from_rec(r['recording'])
    if s is not None:
        high[s] = r['targets']
low = {r['subject']: r['targets'] for r in emo['recordings']}
common = sorted(set(high) & set(low))
out = {'n_common': len(common), 'subjects': common, 'targets': {}}
for tgt in ['valence', 'arousal', 'quadrant']:
    hv = [high[s][f'{tgt}_full']['balanced_accuracy'] for s in common]
    sv = [high[s][f'{tgt}_single']['balanced_accuracy'] for s in common]
    lv = [low[s][tgt] for s in common]
    d_low = [l-h for l,h in zip(lv,hv)]
    d_single = [s-h for s,h in zip(sv,hv)]
    out['targets'][tgt] = {
        'high_end': dict(zip(['mean','ci_low','ci_high'], mean_ci(hv))),
        'low_cost': dict(zip(['mean','ci_low','ci_high'], mean_ci(lv))),
        'single_channel': dict(zip(['mean','ci_low','ci_high'], mean_ci(sv))),
        'low_minus_high': dict(zip(['mean','ci_low','ci_high'], mean_ci(d_low))),
        'single_minus_high': dict(zip(['mean','ci_low','ci_high'], mean_ci(d_single))),
    }
pathlib.Path('results/device_compare.json').write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))
