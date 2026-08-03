"""Q2 Round 1: nested policy-group CV for M1 baseline and M2 sensitivity Ridge."""
from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams.update({"font.family":"sans-serif","font.sans-serif":["Microsoft YaHei","SimHei","DejaVu Sans"],"axes.unicode_minus":False})
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

SCRIPT=Path(__file__).resolve(); ROOT=SCRIPT.parents[2]; OUT=ROOT/"results"/"Q2"/"experiments"/"round1"; SEED=20260802
for d in [OUT/"tables",OUT/"figures",OUT/"metrics",OUT/"logs"]: d.mkdir(parents=True,exist_ok=True)
ALPHAS=[0.01,0.1,1.,3.,10.,30.,100.]
def sha(p):
 h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def make_model(kind,alpha):
 steps=[]
 if kind=="M2": steps.append(PolynomialFeatures(2,include_bias=False))
 steps += [StandardScaler(),Ridge(alpha=alpha)]
 return make_pipeline(*steps)
def nested(kind,X,y,groups):
 outer=GroupKFold(n_splits=min(5,pd.Series(groups).nunique())); pred=np.full(len(y),np.nan); outer_fold=np.full(len(y),-1,dtype=int); chosen=[]
 for fold,(tr,te) in enumerate(outer.split(X,y,groups),1):
  g=groups[tr]; inner=GroupKFold(n_splits=min(4,pd.Series(g).nunique())); scores=[]
  for a in ALPHAS:
   z=[]
   for itr,iva in inner.split(X[tr],y[tr],g):
    m=make_model(kind,a).fit(X[tr][itr],y[tr][itr]); z.append(mean_squared_error(y[tr][iva],m.predict(X[tr][iva])))
   scores.append(float(np.mean(z)))
  a=ALPHAS[int(np.argmin(scores))]; pred[te]=make_model(kind,a).fit(X[tr],y[tr]).predict(X[te]); outer_fold[te]=fold; chosen += [{"fold":fold,"alpha":a,"inner_mse":min(scores),"test_n":len(te)}]
 if (outer_fold<1).any(): raise RuntimeError("Some Q2 rows did not receive an outer-fold assignment.")
 return pred,pd.DataFrame(chosen),outer_fold
def metrics(y,p): return {"rmse_log":float(mean_squared_error(y,p)**.5),"mae_log":float(mean_absolute_error(y,p)),"rmse_cycle":float(mean_squared_error(np.exp(y),np.exp(p))**.5),"mae_cycle":float(mean_absolute_error(np.exp(y),np.exp(p)))}
def main():
 p0=json.loads((ROOT/"data"/"processed"/"p0_summary.json").read_text())
 if p0.get("p0_status")!="pass": raise RuntimeError("P0 is not passed; Q2 is blocked.")
 labels=pd.read_csv(ROOT/"data"/"processed"/"cell_labels.csv"); d=labels.query("dataset_table9 == 'Train'").copy()
 X=d[["C1","Q1_percent","C2"]].to_numpy(float); y=np.log(d.cycle_life_table9.to_numpy(float)); g=d.policy_table9.to_numpy(); all_metrics={}; methods=[]
 for kind,name in [("M1","main_effect_ridge"),("M2","interaction_ridge")]:
  p,folds,outer_fold=nested(kind,X,y,g); tab=d[["barcode","policy_table9","cycle_life_table9"]].copy(); tab["outer_fold"]=outer_fold; tab["pred_log_life"]=p; tab["pred_cycle_life"]=np.exp(p); tab["absolute_error_cycle"]=(tab.pred_cycle_life-tab.cycle_life_table9).abs(); tab.to_csv(OUT/"tables"/f"{kind.lower()}_oof_predictions.csv",index=False,encoding="utf-8-sig"); folds.to_csv(OUT/"tables"/f"{kind.lower()}_folds.csv",index=False); all_metrics[kind]=metrics(y,p); methods.append({"method_id":kind,"method_name":name,"status":"success","metrics_summary":all_metrics[kind]})
 fig,ax=plt.subplots(figsize=(5.6,5));
 for kind,c in [("M1","#777777"),("M2","#0072B2")]:
  t=pd.read_csv(OUT/"tables"/f"{kind.lower()}_oof_predictions.csv"); ax.scatter(t.cycle_life_table9,t.pred_cycle_life,label={"M1":"M1 主效应岭回归","M2":"M2 二阶交互岭回归"}[kind],color=c,alpha=.75)
 lo,hi=ax.get_xlim(); ax.plot([lo,hi],[lo,hi],"--",color="black"); ax.set(xlabel="官方循环寿命（循环）",ylabel="折外预测循环寿命（循环）",title="Q2：训练集策略分组折外预测"); ax.legend(); fig.tight_layout(); fig.savefig(OUT/"figures"/"m1_m2_oof_comparison.png",dpi=220); plt.close(fig)
 (OUT/"metrics"/"comparison_metrics.json").write_text(json.dumps(all_metrics,ensure_ascii=False,indent=2),encoding="utf-8")
 summary={"question":"Q2","round":"round1","execution_timestamp":datetime.now(timezone.utc).isoformat(),"implementation_target":"python","random_seed":SEED,"target_transform":"natural_log","inverse_transform":"exp","validation":{"outer":"5-fold GroupKFold by policy_table9","inner":"up to 4-fold GroupKFold by policy_table9"},"input_checks":{"p0_status":p0["p0_status"],"train_cells":len(d),"policy_groups":int(d.policy_table9.nunique())},"methods":methods,"script_sha256":sha(SCRIPT),"input_sha256":{"cell_labels.csv":sha(ROOT/"data"/"processed"/"cell_labels.csv"),"p0_summary.json":sha(ROOT/"data"/"processed"/"p0_summary.json")}}
 (OUT/"run_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8"); (OUT/"logs"/"run.log").write_text(json.dumps(summary,ensure_ascii=False),encoding="utf-8"); print(json.dumps(all_metrics,ensure_ascii=False))
if __name__=="__main__": main()
