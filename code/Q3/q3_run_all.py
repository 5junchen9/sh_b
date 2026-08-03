"""Q3 Round 1: nested policy-group life Ridge with fold-specific monotone SOH templates."""
from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams.update({"font.family":"sans-serif","font.sans-serif":["Microsoft YaHei","SimHei","DejaVu Sans"],"axes.unicode_minus":False})
import matplotlib.pyplot as plt
import numpy as np,pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error,mean_squared_error
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
SCRIPT=Path(__file__).resolve(); ROOT=SCRIPT.parents[2]; OUT=ROOT/"results"/"Q3"/"experiments"/"round1"; SEED=20260802; KS=[5,10,20,50,100]; ALPHAS=[.01,.1,1.,3.,10.,30.,100.]; GRID=np.linspace(.001,1,1000)
for d in [OUT/"tables",OUT/"figures",OUT/"metrics",OUT/"logs"]: d.mkdir(parents=True,exist_ok=True)
COLS=["QDischarge_mean","QDischarge_slope","QDischarge_delta_cycle2_to_k","QCharge_mean","QCharge_slope","IR_mean","IR_slope","Tmax_mean","Tavg_mean","Tmin_mean","chargetime_mean","chargetime_slope"]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def bool_mask(s):
 if pd.api.types.is_bool_dtype(s): return s.fillna(False)
 return s.astype(str).str.strip().str.lower().isin(["true","1"])
def model(a): return make_pipeline(SimpleImputer(strategy="median"),StandardScaler(),Ridge(alpha=a))
def choose(X,y,g):
 cv=GroupKFold(n_splits=min(4,pd.Series(g).nunique())); scores=[]
 for a in ALPHAS:
  e=[]
  for tr,va in cv.split(X,y,g): e.append(mean_squared_error(y[va],model(a).fit(X[tr],y[tr]).predict(X[va])))
  scores.append(np.mean(e))
 return ALPHAS[int(np.argmin(scores))]
def template(bars,life,view):
 rows=[]
 for b in bars:
  c=view.loc[(view.barcode.eq(b))&bool_mask(view.valid_QDischarge),["global_cycle_index","SOH_nom"]]; u=c.global_cycle_index.to_numpy(float)/life[b]
  if len(u)>=10:
   z=np.full(1000,np.nan); ok=(GRID>=u.min())&(GRID<=u.max()); z[ok]=np.interp(GRID[ok],u,c.SOH_nom); rows.append(z)
 if not rows: raise RuntimeError("No outer-training SOH curve has at least 10 valid points.")
 a=np.vstack(rows); ok=np.sum(np.isfinite(a),axis=0)>=5
 if not ok.any(): raise RuntimeError("template support <5")
 x=np.r_[GRID[ok],1.]; y=np.r_[np.nanmedian(a[:,ok],axis=0),.8]
 return IsotonicRegression(increasing=False,out_of_bounds="clip").fit_transform(GRID,np.interp(GRID,x,y))
def predict_soh(anchor,k,predlife,G,cycle):
 gk=np.interp(k/predlife,GRID,G); den=.8-gk
 if abs(den)<1e-6: return None
 q=(np.interp(min(cycle/predlife,1),GRID,G)-gk)/den
 value=float(anchor)+(.8-float(anchor))*q
 return .8 if cycle>=predlife else value
def main():
 p0=json.loads((ROOT/"data"/"processed"/"p0_summary.json").read_text())
 if p0.get("p0_status")!="pass": raise RuntimeError("P0 is not passed; Q3 is blocked.")
 lab=pd.read_csv(ROOT/"data"/"processed"/"cell_labels.csv"); view=pd.read_csv(ROOT/"data"/"processed"/"cycle_model_view.csv",low_memory=False); rows=[]; allpred=[]; curve_diagnostics=[]; soh120_predictions=[]
 for k in KS:
  f=pd.read_csv(ROOT/"data"/"processed"/f"early_features_k{k}.csv"); d=lab.merge(f[["barcode",*COLS]],on="barcode").query("dataset_table9 == 'Train'").reset_index(drop=True); X=d[COLS].to_numpy(float); y=np.log(d.cycle_life_table9.to_numpy(float)); g=d.policy_table9.to_numpy(); pred=np.full(len(d),np.nan); outer_fold=np.full(len(d),-1,dtype=int); e=[]; usable=0; failures=0; failure_reasons={"predicted_life_not_after_k":0,"missing_anchor":0,"no_future_observation":0,"template_anchor_denominator":0}
  for fold,(tr,te) in enumerate(GroupKFold(n_splits=min(5,pd.Series(g).nunique())).split(X,y,g),1):
   outer_fold[te]=fold
   a=choose(X[tr],y[tr],g[tr]); pred[te]=model(a).fit(X[tr],y[tr]).predict(X[te]); life=dict(zip(d.barcode.iloc[tr],d.cycle_life_table9.iloc[tr])); G=template(set(d.barcode.iloc[tr]),life,view)
   for idx in te:
    b=d.barcode.iloc[idx]; hL=float(np.exp(pred[idx])); L=float(d.cycle_life_table9.iloc[idx]); c=view.loc[(view.barcode.eq(b))&bool_mask(view.valid_QDischarge),["global_cycle_index","SOH_nom"]]; an=c.loc[c.global_cycle_index.eq(k),"SOH_nom"]; fut=c.loc[(c.global_cycle_index.gt(k))&(c.global_cycle_index.lt(L))]
    if hL<=k: failures+=1; failure_reasons["predicted_life_not_after_k"]+=1; continue
    if an.empty: failures+=1; failure_reasons["missing_anchor"]+=1; continue
    if fut.empty: failures+=1; failure_reasons["no_future_observation"]+=1; continue
    gk=np.interp(k/hL,GRID,G); den=.8-gk
    if abs(den)<1e-6: failures+=1; failure_reasons["template_anchor_denominator"]+=1; continue
    q=(np.interp(np.minimum(fut.global_cycle_index.to_numpy(float)/hL,1),GRID,G)-gk)/den; pp=float(an.iloc[0])+(.8-float(an.iloc[0]))*q; pp=np.where(fut.global_cycle_index.to_numpy(float)>=hL,.8,pp); residual=pp-fut.SOH_nom.to_numpy(float); e.extend(residual.tolist()); curve_diagnostics.append({"barcode":b,"policy_table9":d.policy_table9.iloc[idx],"k":k,"outer_fold":fold,"future_point_count":len(residual),"soh_rmse":float(np.mean(np.square(residual))**.5),"soh_mae":float(np.mean(np.abs(residual))),"soh_mse":float(np.mean(np.square(residual)))}); usable+=1
    if 120>k:
     soh120_predictions.append({"barcode":b,"policy_table9":d.policy_table9.iloc[idx],"k":k,"outer_fold":fold,"predicted_cycle_life":hL,"predicted_soh_nom_120":predict_soh(an.iloc[0],k,hL,G,120),"actual_soh_nom_120":float(c.loc[c.global_cycle_index.eq(120),"SOH_nom"].iloc[0]) if c.global_cycle_index.eq(120).any() else np.nan,"prediction_role":"outer_fold_q3_prediction"})
   
  if (outer_fold<1).any(): raise RuntimeError(f"Some Q3 rows at k={k} did not receive an outer-fold assignment.")
  tab=d[["barcode","policy_table9","cycle_life_table9"]].copy(); tab["k"]=k; tab["outer_fold"]=outer_fold; tab["pred_log_life"]=pred; tab["pred_cycle_life"]=np.exp(pred); allpred.append(tab); rows.append({"k":k,"rmse_log":float(mean_squared_error(y,pred)**.5),"mae_log":float(mean_absolute_error(y,pred)),"future_point_pooled_soh_rmse":float(np.mean(np.square(e))**.5),"curve_cells":usable,"template_failures":failures,**{f"failure_{name}":count for name,count in failure_reasons.items()}})
 metrics=pd.DataFrame(rows); metrics.to_csv(OUT/"tables"/"window_metrics.csv",index=False); pd.concat(allpred).to_csv(OUT/"tables"/"m3_oof_life_predictions.csv",index=False,encoding="utf-8-sig"); pd.DataFrame(curve_diagnostics).to_csv(OUT/"tables"/"m3_cell_curve_errors.csv",index=False,encoding="utf-8-sig"); pd.DataFrame(soh120_predictions).to_csv(OUT/"tables"/"m3_oof_soh120_predictions.csv",index=False,encoding="utf-8-sig")
 fig,ax=plt.subplots(figsize=(6,4)); ax.plot(metrics.k,metrics.rmse_log,"o-",label="寿命 RMSE_log"); ax.plot(metrics.k,metrics.future_point_pooled_soh_rmse,"s-",label="未来 SOH RMSE（观测点合并）"); ax.set(xlabel="早期窗口截止循环 k（循环）",ylabel="误差",title="Q3：不同早期窗口的策略分组折外误差"); ax.legend(); fig.tight_layout(); fig.savefig(OUT/"figures"/"m3_window_errors.png",dpi=220); plt.close(fig)
 inputs={"p0_summary.json":sha(ROOT/"data"/"processed"/"p0_summary.json"),"cell_labels.csv":sha(ROOT/"data"/"processed"/"cell_labels.csv"),"cycle_model_view.csv":sha(ROOT/"data"/"processed"/"cycle_model_view.csv")}
 inputs.update({f"early_features_k{k}.csv":sha(ROOT/"data"/"processed"/f"early_features_k{k}.csv") for k in KS})
 summary={"question":"Q3","round":"round1","execution_timestamp":datetime.now(timezone.utc).isoformat(),"implementation_target":"python","random_seed":SEED,"target_transform":"natural_log","inverse_transform":"exp","validation":{"outer":"5-fold GroupKFold by policy_table9","inner":"up to 4-fold GroupKFold by policy_table9","soh_template":"outer-training cells only"},"metric_definitions":{"future_point_pooled_soh_rmse":"将所有成功电芯的未来观测点残差合并后计算 RMSE；论文正式窗口比较改用 robustness/Q3 的 cell_equal_soh_rmse","predicted_soh_nom_120":"外层训练 SOH 模板与电芯在 k 的真实锚点得到的第120循环预测，仅用于 Q4 已有策略的交叉拟合聚合"},"methods":[{"method_id":"M3","method_name":"life_anchored_monotone_soh_template","status":"success","metrics_summary":rows}],"script_sha256":sha(SCRIPT),"input_sha256":inputs}
 (OUT/"metrics"/"m3_metrics.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8"); (OUT/"run_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8"); (OUT/"logs"/"run.log").write_text(json.dumps(summary,ensure_ascii=False),encoding="utf-8"); print(json.dumps(rows,ensure_ascii=False))
if __name__=="__main__": main()
