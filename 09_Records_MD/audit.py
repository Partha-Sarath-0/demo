import pandas as pd, numpy as np, json, sys
D="/home/claude/grail_cfd/10_dataset/"
d=pd.read_csv(D+"GRAIL_CFD_dataset_rev4_richardson.csv")
a=pd.read_csv(D+"GRAIL_CFD_dataset_rev4_nx110.csv").set_index("case_id")
b=pd.read_csv(D+"GRAIL_CFD_dataset_rev4_nx220.csv").set_index("case_id")
out={}
def P(*x): print(*x)
P("== 1 integrity"); P(d.shape)
num=d.select_dtypes("number")
P("NaN total",int(d.isna().sum().sum()),"inf",int(np.isinf(num).sum().sum()))
P("dup rows",int(d.duplicated().sum()),"dup ids",int(d.case_id.duplicated().sum()))
ind=["G_T_W_m2","T_in_K","T_amb_K","v_wind_m_s","mdot_total_kg_s","bridge_mm","g_ratio"]
P("dup operating conditions (incl arrangement)",int(d.duplicated(ind+["arrangement"]).sum()),"; excl arrangement",int(d.duplicated(ind).sum()))
const=[c for c in d.columns if d[c].nunique()==1]; P("constant cols",const)
for c in d.select_dtypes(exclude="number").columns: P(" cat",c,d[c].unique()[:5],d[c].nunique())
P("arrangement vs f_interdig",pd.crosstab(d.arrangement,d.f_interdig).to_dict())
P("\n== 2 ranges")
st=num.describe(percentiles=[.01,.5,.99]).T[["min","1%","50%","mean","std","99%","max"]]
pd.set_option("display.width",200); P(st.to_string(float_format=lambda v:"%.6g"%v))
P("\n== 3 reconstruction")
cp=4180.0; A=0.528; N=12
def rep(name,x,y):
    e=np.abs(x-y); r=e/np.maximum(np.abs(y),1e-300)
    P("%-38s maxabs %.3e meanabs %.3e maxrel %.3e"%(name,e.max(),e.mean(),r.max())); return e
rep("mdot_ch = mdot/12",d.mdot_total_kg_s/N,d.mdot_channel_kg_s)
rep("dT = Tout-Tin",d.T_out_K-d.T_in_K,d.dT_fluid_K)
rep("spread = max-min",d.T_plate_max_K-d.T_plate_min_K,d.plate_spread_K)
rep("Qu = mdot cp dT",d.mdot_total_kg_s*cp*d.dT_fluid_K,d.Qu_W)
rep("q_abs = G*0.833*0.82*0.95",d.G_T_W_m2*0.833*0.82*0.95,d.q_abs_W_m2)
rep("Q_solar = q_abs*0.528",d.q_abs_W_m2*A,d.Q_solar_W)
rep("eta = Qu/(G*0.528)",d.Qu_W/(d.G_T_W_m2*A),d.eta)
rep("eta_conv = Qu/Q_solar vs eta",d.Qu_W/d.Q_solar_W,d.eta)
rep("eta/(Qu/Qsolar) = 0.833*0.82*0.95",d.eta/(d.Qu_W/d.Q_solar_W),pd.Series(0.833*0.82*0.95,index=d.index))
rep("R4 = T_R4^4",d.T_R4_K**4,d.R4_K4)
rep("T_R4 = mean_T_pow4^0.25",d.mean_T_pow4_K4**0.25,d.T_R4_K)
rep("W_pump = 12 dp mdot_ch/rho(997)",12*d.dp_channel_Pa*d.mdot_channel_kg_s/997,d.W_pump_W)
res=d.Q_solar_W-(d.Qu_W+d.Q_rad_W+d.Q_conv_W+d.Q_rear_W)
P("\n== 4 energy: residual W min %.3e max %.3e maxabs %.3e meanabs %.3e rms %.3e ; pct maxabs %.3e"%(res.min(),res.max(),res.abs().max(),res.abs().mean(),np.sqrt((res**2).mean()),(100*res/d.Q_solar_W).abs().max()))
P("energy_error_pct column maxabs",d.energy_error_pct.abs().max())
rep("energy_error_pct vs recomputed",100*res/d.Q_solar_W,d.energy_error_pct)
P("\n== order checks")
for n,c in [("min<=mean",d.T_plate_min_K<=d.T_plate_mean_K),("mean<=max",d.T_plate_mean_K<=d.T_plate_max_K),("P90<=P95",d.P90_K<=d.P95_K),("P95<=P99",d.P95_K<=d.P99_K),("P99<=max",d.P99_K<=d.T_plate_max_K),("T_R4>=mean (power-mean)",d.T_R4_K>=d.T_plate_mean_K),("Tout>Tin",d.T_out_K>d.T_in_K),("std>0",d.plate_std_K>0),("R4>=meanT4",d.R4_K4>=d.mean_T_pow4_K4)]:
    bad=d.case_id[~c].tolist(); P("%-28s violations %d %s"%(n,len(bad),bad[:8]))
P("\n== provenance: which columns equal nx220 exactly, which equal 2*220-110")
prov={}
for c in num.columns:
    x=d.set_index("case_id")[c]; y2=b.loc[x.index,c]; y1=a.loc[x.index,c]
    if np.allclose(x,y2,rtol=0,atol=0): prov[c]="nx220"
    elif np.allclose(x,2*y2-y1,rtol=1e-12,atol=1e-9): prov[c]="richardson"
    else: prov[c]="other"
P({k:[c for c in prov if prov[c]==k] for k in set(prov.values())})
# consistency in nx220 raw for the non-linear items
P("\n== same checks on raw nx220")
bb=b.reset_index()
for n,c in [("T_R4>=mean",bb.T_R4_K>=bb.T_plate_mean_K),("P95<=P99",bb.P95_K<=bb.P99_K),("P99<=max",bb.P99_K<=bb.T_plate_max_K)]:
    P(n,(~c).sum())
rep("raw220 energy",bb.Q_solar_W-(bb.Qu_W+bb.Q_rad_W+bb.Q_conv_W+bb.Q_rear_W),pd.Series(0.0,index=bb.index)+1e-300)
d.to_pickle("/tmp/claude-0/-home-claude/09cdd886-3a71-5b52-bd3e-e373da90433a/scratchpad/d.pkl")
