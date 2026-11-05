"""P1 — 24: decomposition of the affective collapse.

Applies the cumulative acquisition chain and a site sweep to the high-end affective
recordings, decoding valence/arousal/4-class at each step. Answers "which manipulation
causes the collapse?" rather than only comparing 66 channels with one.

Conditions: full | 128 Hz | +quant | +band | single Fz | single Cz | single Pz | single Oz
Output: results/affective_decomp.json
"""
from __future__ import annotations
import argparse, json, pathlib, re
import numpy as np
from scipy.signal import welch
from scipy.stats import t as _t

BANDS=[(4,8),(8,12),(13,30)]
CODE2Q={1:"HVHA",2:"LVHA",3:"HVLA",4:"LVLA",10:"NEUTRAL",14:"NEUTRAL"}
DATA=pathlib.Path("data/raw/emotion_zenodo/Comparativa EEG-BCI/EEG/Experiment_files")
SEED=20261103


def parse_vmrk(path):
    ev=[]
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m=re.match(r"Mk\d+=Stimulus,S\s*(\d+),(\d+),", line.strip())
        if m: ev.append((int(m.group(1)), int(m.group(2))))
    return ev


def feats(ep, fs):
    out=[]
    for e in ep:
        f,p=welch(e, fs=fs, nperseg=min(int(2*fs), e.shape[-1]),
                  noverlap=min(int(fs), e.shape[-1]//2), axis=-1)
        row=[]
        for lo,hi in BANDS:
            m=(f>=lo)&(f<=hi); row.append(np.log(np.mean(p[...,m],axis=-1)+1e-12))
        out.append(np.concatenate(row))
    return np.vstack(out)


def decode(X,y):
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
    from sklearn.model_selection import StratifiedKFold, cross_val_score
    cl,cnt=np.unique(y,return_counts=True)
    if len(cl)<2 or cnt.min()<3: return None
    clf=LinearDiscriminantAnalysis(solver="lsqr",shrinkage="auto")
    cv=StratifiedKFold(n_splits=min(5,int(cnt.min())),shuffle=True,random_state=SEED)
    return float(cross_val_score(clf,X,y,cv=cv,scoring="balanced_accuracy").mean())


def epoched(raw, onsets_sec, picks):
    import mne
    arr=[]
    max_t=raw.times[-1]
    for t0 in onsets_sec:
        if t0 < 0 or t0 + 2.5 > max_t:
            continue
        seg=raw.copy().crop(tmin=t0, tmax=t0+2.5, include_tmax=False)
        arr.append(seg.get_data(picks=picks))
    return np.array(arr) if arr else np.empty((0, len(picks), 1))


def analyse(vhdr):
    import mne
    vm=vhdr.with_suffix(".vmrk")
    ev=[(c,p) for c,p in parse_vmrk(vm) if c in CODE2Q]
    if not ev: return None
    raw=mne.io.read_raw_brainvision(vhdr, preload=True, verbose="ERROR")
    picks=mne.pick_types(raw.info, meg=False, eeg=True, exclude=[])
    onsets=np.array([p for _,p in ev])-1
    onsets_sec=onsets/raw.info["sfreq"]
    codes=np.array([c for c,_ in ev])
    quad=np.array([CODE2Q[c] for c in codes])
    keep=quad!="NEUTRAL"
    res={"recording":vhdr.name,"n_trials":int(keep.sum()),"targets":{}}

    def add(name, raw_cond, picks_cond):
        raw_cond=raw_cond.copy()
        ep=epoched(raw_cond, onsets_sec[keep], picks_cond)
        if len(ep)==0:
            for tgt in ["valence","arousal","quadrant"]:
                res["targets"].setdefault(tgt,{})[name]=None
            return
        X=feats(ep, raw_cond.info["sfreq"])
        # recompute labels for the trials that survived the end-of-recording cut
        kept=[q for q,t0 in zip(quad[keep], onsets_sec[keep])
              if t0 + 2.5 <= raw_cond.times[-1]]
        q=np.array(kept[:len(ep)])
        for tgt,y in [("valence",np.isin(q,["HVHA","HVLA"]).astype(int)),
                     ("arousal",np.isin(q,["HVHA","LVHA"]).astype(int)),
                     ("quadrant",q)]:
            res["targets"].setdefault(tgt,{})[name]=decode(X,y)

    # full montage, all bands
    add("full", raw, picks)
    # EMG control: full montage with theta+alpha only, and beta only
    Xf=feats(epoched(raw, onsets_sec[keep], picks), raw.info["sfreq"])
    kept=[q for q,t0 in zip(quad[keep], onsets_sec[keep]) if t0+2.5 <= raw.times[-1]]
    qf=np.array(kept[:len(Xf)])
    nch=len(picks)
    for cname, cols in [("full_theta_alpha", slice(0, 2*nch)), ("full_beta", slice(2*nch, 3*nch))]:
        for tgt, y in [("valence", np.isin(qf,["HVHA","HVLA"]).astype(int)),
                       ("arousal", np.isin(qf,["HVHA","LVHA"]).astype(int)),
                       ("quadrant", qf)]:
            res["targets"].setdefault(tgt,{})[cname]=decode(Xf[:,cols], y)
    raw128=raw.copy().resample(128, verbose="ERROR")
    add("hz128", raw128, mne.pick_types(raw128.info, meg=False, eeg=True, exclude=[]))
    rawq=raw128.copy(); rawq._data=np.round(rawq.get_data()/1e-6)*1e-6
    add("quant", rawq, mne.pick_types(rawq.info, meg=False, eeg=True, exclude=[]))
    rawb=rawq.copy().filter(1.0,40.0,method="fir",verbose="ERROR")
    add("band", rawb, mne.pick_types(rawb.info, meg=False, eeg=True, exclude=[]))
    canon=lambda s:"".join(ch for ch in s if ch.isalnum()).lower()
    lookup={canon(c):c for c in rawb.ch_names}
    for site in ["Fz","Cz","Pz","Oz"]:
        if canon(site) in lookup:
            rawb.pick([lookup[canon(site)]])
            add(f"single_{site}", rawb, [0])
            # restore full channel set for the next site
            rawb=rawq.copy().filter(1.0,40.0,method="fir",verbose="ERROR")
    return res


def mean_ci(v):
    v=[x for x in v if x is not None and not (isinstance(x,float) and np.isnan(x))]
    a=np.asarray(v,float); n=len(a)
    if n==0: return {"n":0,"mean":None}
    m=float(a.mean()); sem=a.std(ddof=1)/np.sqrt(n) if n>1 else 0
    t=float(_t.ppf(0.975,max(n-1,1)))
    return {"n":n,"mean":m,"ci_low":float(m-t*sem),"ci_high":float(m+t*sem)}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data",type=pathlib.Path,default=DATA)
    ap.add_argument("--limit",type=int,default=0)
    ap.add_argument("--out",type=pathlib.Path,default=pathlib.Path("results/affective_decomp.json"))
    args=ap.parse_args()
    files=sorted(args.data.glob("eegbci*-*.vhdr"))
    if args.limit: files=files[:args.limit]
    rows=[]
    for f in files:
        try: r=analyse(f)
        except Exception as e: print("FAIL",f.name,e); continue
        if r: rows.append(r); print(f.name,"ok")
    summary={}
    for tgt in ["valence","arousal","quadrant"]:
        summary[tgt]={cond:mean_ci([r["targets"][tgt][cond] for r in rows])
                      for cond in rows[0]["targets"][tgt]} if rows else {}
    out={"n_recordings":len(rows),"recordings":rows,"summary":summary}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(out,indent=2))
    print(json.dumps({t:{c:summary[t][c]["mean"] for c in summary[t]} for t in summary},indent=2))

if __name__=="__main__": main()
