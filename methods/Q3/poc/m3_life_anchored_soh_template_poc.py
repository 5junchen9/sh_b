"""Q3 PoC M3: policy-group OOF life Ridge plus a fold-specific monotone SOH template."""
from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[3]
P0 = json.loads((ROOT / "data" / "processed" / "p0_summary.json").read_text(encoding="utf-8"))
if P0.get("p0_status") != "pass": raise RuntimeError("P0 must pass")
LABELS = pd.read_csv(ROOT / "data" / "processed" / "cell_labels.csv")
VIEW = pd.read_csv(ROOT / "data" / "processed" / "cycle_model_view.csv", low_memory=False)
COLS = ["QDischarge_mean","QDischarge_slope","QDischarge_delta_cycle2_to_k","QCharge_mean","QCharge_slope","IR_mean","IR_slope","Tmax_mean","Tavg_mean","Tmin_mean","chargetime_mean","chargetime_slope"]
GRID = np.linspace(0.001, 1.0, 1000)

def template(train_barcodes: set[str], life: dict[str, float]) -> np.ndarray:
    rows=[]
    for barcode in train_barcodes:
        c=VIEW.loc[(VIEW.barcode.eq(barcode)) & VIEW.valid_QDischarge.astype(bool), ["global_cycle_index","SOH_nom"]]
        u=c.global_cycle_index.to_numpy(float)/life[barcode]; y=c.SOH_nom.to_numpy(float)
        if len(u)>=10:
            z=np.full(len(GRID),np.nan); inside=(GRID>=u.min())&(GRID<=u.max()); z[inside]=np.interp(GRID[inside],u,y); rows.append(z)
    a=np.vstack(rows); count=np.sum(np.isfinite(a),axis=0); ok=count>=5
    if not ok.any(): raise RuntimeError("No grid location has five supporting cells.")
    med=np.nanmedian(a[:,ok],axis=0)
    x=np.r_[GRID[ok],1.0]; y=np.r_[med,0.8]
    return IsotonicRegression(increasing=False, out_of_bounds="clip").fit_transform(GRID, np.interp(GRID,x,y))

out=[]
for k in [5,10,20,50,100]:
    feat=pd.read_csv(ROOT/"data"/"processed"/f"early_features_k{k}.csv")
    d=LABELS.merge(feat[["barcode",*COLS]],on="barcode").query("dataset_table9 == 'Train'").reset_index(drop=True)
    X=d[COLS].to_numpy(float); y=np.log(d.cycle_life_table9.to_numpy(float)); groups=d.policy_table9.to_numpy(); oof=np.full(len(d),np.nan); errs=[]; usable=0
    for fit, test in GroupKFold(n_splits=min(5,pd.Series(groups).nunique())).split(X,y,groups):
        model=make_pipeline(SimpleImputer(strategy="median"),StandardScaler(),Ridge(alpha=3.0)).fit(X[fit],y[fit]); pred=model.predict(X[test]); oof[test]=pred
        life=dict(zip(d.barcode.iloc[fit],d.cycle_life_table9.iloc[fit])); g=template(set(d.barcode.iloc[fit]),life)
        for idx, log_l in zip(test,pred):
            b=d.barcode.iloc[idx]; hat_l=float(np.exp(log_l)); actual=float(d.cycle_life_table9.iloc[idx])
            c=VIEW.loc[(VIEW.barcode.eq(b))&VIEW.valid_QDischarge.astype(bool),["global_cycle_index","SOH_nom"]]; anchor=c.loc[c.global_cycle_index.eq(k),"SOH_nom"]
            future=c.loc[(c.global_cycle_index.gt(k))&(c.global_cycle_index.lt(actual))]
            if hat_l<=k or anchor.empty or future.empty: continue
            gk=np.interp(k/hat_l,GRID,g); denom=0.8-gk
            if abs(denom)<1e-6: continue
            u=future.global_cycle_index.to_numpy(float)/hat_l; h=(np.interp(np.minimum(u,1),GRID,g)-gk)/denom
            p=float(anchor.iloc[0])+(0.8-float(anchor.iloc[0]))*h; p=np.where(future.global_cycle_index.to_numpy(float)>=hat_l,0.8,p)
            errs.extend((p-future.SOH_nom.to_numpy(float)).tolist()); usable+=1
    out.append({"k":k,"life_rmse_log":float(mean_squared_error(y,oof)**0.5),"soh_rmse":float(np.mean(np.square(errs))**0.5) if errs else None,"curve_cells":usable})
print(json.dumps({"candidate":"Q3-M3","windows":out},ensure_ascii=False))
