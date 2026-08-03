"""One-time Primary confirmation for frozen Q3 M3 at k=5 and k=100."""
from __future__ import annotations
import hashlib, json, platform, sys
from datetime import datetime, timezone
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams.update({"font.family":"sans-serif","font.sans-serif":["Microsoft YaHei","SimHei","DejaVu Sans"],"axes.unicode_minus":False,"svg.fonttype":"none"})
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.impute import SimpleImputer
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SCRIPT=Path(__file__).resolve(); ROOT=SCRIPT.parents[2]; OUT=ROOT/"results"/"Q3"/"experiments"/"primary_confirmation_round1"
TABLES,FIGURES,METRICS,LOGS=(OUT/name for name in ("tables","figures","metrics","logs"))
P0=ROOT/"data"/"processed"/"p0_summary.json"; LABELS=ROOT/"data"/"processed"/"cell_labels.csv"; VIEW=ROOT/"data"/"processed"/"cycle_model_view.csv"; PROTOCOL=ROOT/"methods"/"Q3"/"q3_primary_confirmation_protocol.md"
KS=[5,100]; ALPHAS=[.01,.1,1.,3.,10.,30.,100.]; GRID=np.linspace(.001,1,1000); SEED=20260802
COLS=["QDischarge_mean","QDischarge_slope","QDischarge_delta_cycle2_to_k","QCharge_mean","QCharge_slope","IR_mean","IR_slope","Tmax_mean","Tavg_mean","Tmin_mean","chargetime_mean","chargetime_slope"]

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def mask(s): return s.fillna(False) if pd.api.types.is_bool_dtype(s) else s.astype(str).str.strip().str.lower().isin(["true","1"])
def mdl(a): return make_pipeline(SimpleImputer(strategy="median"),StandardScaler(),Ridge(alpha=a))
def choose(X,y,g):
    cv=GroupKFold(n_splits=min(4,pd.Series(g).nunique())); score=[]
    for a in ALPHAS: score.append(np.mean([mean_squared_error(y[va],mdl(a).fit(X[tr],y[tr]).predict(X[va])) for tr,va in cv.split(X,y,g)]))
    return float(ALPHAS[int(np.argmin(score))])
def template(bars,life,view):
    rows=[]
    for b in bars:
        c=view.loc[(view.barcode.eq(b))&mask(view.valid_QDischarge),["global_cycle_index","SOH_nom"]]; u=c.global_cycle_index.to_numpy(float)/life[b]
        if len(u)>=10:
            z=np.full(len(GRID),np.nan); ok=(GRID>=u.min())&(GRID<=u.max()); z[ok]=np.interp(GRID[ok],u,c.SOH_nom); rows.append(z)
    if not rows: raise RuntimeError("No Train curve has at least ten valid QDischarge values.")
    a=np.vstack(rows); ok=np.sum(np.isfinite(a),axis=0)>=5
    if not ok.any(): raise RuntimeError("Train SOH template support is below five cells.")
    x=np.r_[GRID[ok],1.]; y=np.r_[np.nanmedian(a[:,ok],axis=0),.8]
    return IsotonicRegression(increasing=False,out_of_bounds="clip").fit_transform(GRID,np.interp(GRID,x,y))
def life_metrics(a,p):
    ac,pc=np.exp(a),np.exp(p)
    return {"rmse_log":float(mean_squared_error(a,p)**.5),"mae_log":float(mean_absolute_error(a,p)),"rmse_cycle":float(mean_squared_error(ac,pc)**.5),"mae_cycle":float(mean_absolute_error(ac,pc)),"overprediction_rate":float(np.mean(p>a))}
def curve_error(barcode,k,predlife,actlife,G,view):
    if predlife<=k: return None,None,"predicted_life_not_after_k"
    c=view.loc[(view.barcode.eq(barcode))&mask(view.valid_QDischarge),["global_cycle_index","SOH_nom"]]; anchor=c.loc[c.global_cycle_index.eq(k),"SOH_nom"]; future=c.loc[(c.global_cycle_index.gt(k))&(c.global_cycle_index.lt(actlife))]
    if anchor.empty:return None,None,"missing_anchor"
    if future.empty:return None,None,"no_future_observation"
    gk=np.interp(k/predlife,GRID,G); den=.8-gk
    if abs(den)<1e-6:return None,None,"template_anchor_denominator"
    q=(np.interp(np.minimum(future.global_cycle_index.to_numpy(float)/predlife,1),GRID,G)-gk)/den; pred=float(anchor.iloc[0])+(.8-float(anchor.iloc[0]))*q; pred=np.where(future.global_cycle_index.to_numpy(float)>=predlife,.8,pred)
    soh120=float(anchor.iloc[0])+(.8-float(anchor.iloc[0]))*((np.interp(min(120/predlife,1),GRID,G)-gk)/den)
    if 120>=predlife: soh120=.8
    return pred-future.SOH_nom.to_numpy(float),soh120,None
def plot(metrics,pred):
    fig,ax=plt.subplots(1,2,figsize=(11,4.5))
    for k,d in pred.groupby("k"):ax[0].scatter(d.cycle_life_table9,d.predicted_cycle_life,s=42,label=f"k={k}")
    lo=float(min(pred.cycle_life_table9.min(),pred.predicted_cycle_life.min())); hi=float(max(pred.cycle_life_table9.max(),pred.predicted_cycle_life.max())); ax[0].plot([lo,hi],[lo,hi],"--",color="#555555",label="理想预测线"); ax[0].set(title="主确认集：寿命观察—预测",xlabel="实际循环寿命（循环）",ylabel="预测循环寿命（循环）");ax[0].legend();ax[0].grid(alpha=.2)
    ax[1].bar(metrics.k.astype(str),metrics.cell_equal_soh_rmse,color=["#4C72B0","#DD8452"]);ax[1].set(title="主确认集：电芯等权未来 SOH 误差",xlabel="早期窗口截止循环 k（循环）",ylabel="电芯等权 SOH RMSE");ax[1].grid(axis="y",alpha=.2)
    for i,v in enumerate(metrics.cell_equal_soh_rmse):ax[1].text(i,v,f"{v:.4f}",ha="center",va="bottom")
    fig.suptitle("Q3：主确认集双窗口一次受限确认");fig.tight_layout()
    for ext,kw in (("png",{"dpi":300}),("svg",{})):fig.savefig(FIGURES/f"q3_primary_confirmation.{ext}",bbox_inches="tight",**kw)
    plt.close(fig)
def main():
    for d in (TABLES,FIGURES,METRICS,LOGS):d.mkdir(parents=True,exist_ok=True)
    p0=json.loads(P0.read_text(encoding="utf-8"));
    if p0.get("p0_status")!="pass":raise RuntimeError("P0 is not passed; Q3 Primary confirmation is blocked.")
    lab=pd.read_csv(LABELS); view=pd.read_csv(VIEW,low_memory=False); train=lab.loc[lab.dataset_table9.eq("Train")].copy(); primary=lab.loc[lab.dataset_table9.eq("Prim. Test")].copy()
    if len(train)!=41 or len(primary)!=43 or train.barcode.duplicated().any() or primary.barcode.duplicated().any():raise RuntimeError("Frozen Train/Primary partitions must contain unique 41/43 barcodes.")
    G=template(set(train.barcode),dict(zip(train.barcode,train.cycle_life_table9)),view); rows=[]; preds=[]; curves=[]; soh120=[]; tuning=[]
    for k in KS:
        feature=pd.read_csv(ROOT/"data"/"processed"/f"early_features_k{k}.csv")
        if set(["barcode",*COLS]).difference(feature.columns):raise RuntimeError(f"k={k} missing frozen Q3 features.")
        tr=train.merge(feature[["barcode",*COLS]],on="barcode",validate="one_to_one");te=primary.merge(feature[["barcode",*COLS]],on="barcode",validate="one_to_one")
        if len(tr)!=41 or len(te)!=43:raise RuntimeError(f"k={k} feature merge changed frozen partitions.")
        X=tr[COLS].to_numpy(float); y=np.log(tr.cycle_life_table9.to_numpy(float)); a=choose(X,y,tr.policy_table9.to_numpy()); pp=mdl(a).fit(X,y).predict(te[COLS].to_numpy(float)); yy=np.log(te.cycle_life_table9.to_numpy(float)); tuning.append({"k":k,"alpha":a,"train_cells":41,"train_policy_groups":int(tr.policy_table9.nunique())}); errs=[]; pooled=[]; fails={x:0 for x in ["predicted_life_not_after_k","missing_anchor","no_future_observation","template_anchor_denominator"]}
        for i,r in te.reset_index(drop=True).iterrows():
            life=float(np.exp(pp[i])); residual,pred_soh120,reason=curve_error(r.barcode,k,life,float(r.cycle_life_table9),G,view);preds.append({"barcode":r.barcode,"policy_table9":r.policy_table9,"k":k,"cycle_life_table9":r.cycle_life_table9,"actual_log_life":yy[i],"predicted_log_life":pp[i],"predicted_cycle_life":life,"confirmation_role":"Primary_restricted_confirmation"})
            if reason:fails[reason]+=1;continue
            if k<120:
                c120=view.loc[(view.barcode.eq(r.barcode))&mask(view.valid_QDischarge)&view.global_cycle_index.eq(120),"SOH_nom"]
                soh120.append({"barcode":r.barcode,"policy_table9":r.policy_table9,"k":k,"predicted_cycle_life":life,"predicted_soh_nom_120":pred_soh120,"actual_soh_nom_120":float(c120.iloc[0]) if len(c120) else np.nan,"prediction_role":"Primary_restricted_confirmation"})
            mse=float(np.mean(residual**2));errs.append(mse);pooled.extend(residual.tolist());curves.append({"barcode":r.barcode,"policy_table9":r.policy_table9,"k":k,"future_point_count":len(residual),"soh_mse":mse,"soh_rmse":float(mse**.5),"soh_mae":float(np.mean(abs(residual))),"confirmation_role":"Primary_restricted_confirmation"})
        if not errs:raise RuntimeError(f"k={k} has no evaluable Primary SOH curve.")
        rows.append({"k":k,**life_metrics(yy,pp),"cell_equal_soh_rmse":float(np.mean(errs)**.5),"future_point_pooled_soh_rmse":float(np.mean(np.square(pooled))**.5),"curve_cells":len(errs),"template_failures":sum(fails.values()),**{f"failure_{x}":v for x,v in fails.items()}})
    metrics=pd.DataFrame(rows);pred=pd.DataFrame(preds);curve=pd.DataFrame(curves);tune=pd.DataFrame(tuning);metrics.to_csv(TABLES/"q3_primary_window_metrics.csv",index=False);pred.to_csv(TABLES/"q3_primary_life_predictions.csv",index=False,encoding="utf-8-sig");curve.to_csv(TABLES/"q3_primary_cell_curve_errors.csv",index=False,encoding="utf-8-sig");pd.DataFrame(soh120).to_csv(TABLES/"q3_primary_soh120_predictions.csv",index=False,encoding="utf-8-sig");tune.to_csv(TABLES/"q3_primary_train_tuning.csv",index=False);plot(metrics,pred)
    payload={"confirmation_status":"observed_not_adjudicated","scope":"One-time frozen M3 confirmation on Primary; alpha and template use Train only.","windows":rows,"selected_alpha_by_window":tuning,"soh_metric":"cell_equal_soh_rmse is formal; pooled is diagnostic."};(METRICS/"q3_primary_metrics.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    tab="\n".join(f"| {r['k']} | {r['rmse_log']:.6f} | {r['mae_log']:.6f} | {r['cell_equal_soh_rmse']:.6f} | {r['curve_cells']} |" for r in rows);report=f"""# Q3 主确认集双窗口一次受限确认\n\n> 状态：**observed_not_adjudicated**。此处只报告冻结 M3 的受限确认观察，不自动决定模型通过或最终泛化。\n\n| k | RMSE_log（ln） | MAE_log（ln） | 电芯等权 SOH RMSE | 可评价电芯 |\n|---:|---:|---:|---:|---:|\n{tab}\n\n窗口角色：k=5 为最早筛查；k=100 为正式窗口且仍待外部确认。每个 alpha 和 SOH 模板只由 Train 构造；Primary 已有探索暴露，不能据此写成最终独立泛化。\n""";(OUT/"q3_primary_confirmation_report.md").write_text(report,encoding="utf-8")
    inp={"p0_summary.json":sha(P0),"cell_labels.csv":sha(LABELS),"cycle_model_view.csv":sha(VIEW),"q3_primary_confirmation_protocol.md":sha(PROTOCOL)};inp.update({f"early_features_k{k}.csv":sha(ROOT/"data"/"processed"/f"early_features_k{k}.csv") for k in KS})
    summary={"question":"Q3","round":"primary_confirmation_round1","execution_timestamp":datetime.now(timezone.utc).isoformat(),"implementation_target":"python","random_seed":SEED,"scope":payload["scope"],"windows":KS,"partitions":{"train":"Train","primary":"Prim. Test","train_cells":41,"primary_cells":43},"target_transform":"natural_log","inverse_transform":"exp","metric_definitions":{"cell_equal_soh_rmse":"正式 SOH 指标","future_point_pooled_soh_rmse":"补充诊断","predicted_soh_nom_120":"冻结 Train 模板与 Primary 真实 k 锚点得到的第120循环预测，仅用于 Q4 已有策略的受限聚合"},"metrics":rows,"input_sha256":inp,"script_sha256":sha(SCRIPT),"environment":{"python":sys.version,"platform":platform.platform(),"scikit_learn":sklearn.__version__},"outputs":["tables/q3_primary_window_metrics.csv","tables/q3_primary_life_predictions.csv","tables/q3_primary_cell_curve_errors.csv","tables/q3_primary_soh120_predictions.csv","tables/q3_primary_train_tuning.csv","metrics/q3_primary_metrics.json","figures/q3_primary_confirmation.png","figures/q3_primary_confirmation.svg","q3_primary_confirmation_report.md"]};text=json.dumps(summary,ensure_ascii=False,indent=2);(OUT/"run_summary.json").write_text(text,encoding="utf-8");(LOGS/"run.log").write_text(text+"\n",encoding="utf-8");print(json.dumps({"status":payload["confirmation_status"],"metrics":rows},ensure_ascii=False))
if __name__=="__main__":main()
