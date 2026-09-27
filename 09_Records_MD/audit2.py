import pandas as pd, numpy as np, math
from scipy import stats
D="/home/claude/grail_cfd/10_dataset/"
d=pd.read_csv(D+"GRAIL_CFD_dataset_rev4_richardson.csv")
a=pd.read_csv(D+"GRAIL_CFD_dataset_rev4_nx110.csv").set_index("case_id").loc[d.case_id].reset_index()
b=pd.read_csv(D+"GRAIL_CFD_dataset_rev4_nx220.csv").set_index("case_id").loc[d.case_id].reset_index()
A=0.528
def rep(n,x,y):
    e=np.abs(x-y); print("%-44s maxabs %.3e maxrel %.3e"%(n,e.max(),(e/np.abs(y).clip(1e-300)).max()))
print("== T^4 definitions")
rep("R4 vs T_R4^4",d.T_R4_K**4,d.R4_K4)
rep("mean_T_pow4 vs (T_mean)^4 [Richardson file]",d.T_plate_mean_K**4,d.mean_T_pow4_K4)
rep("mean_T_pow4 vs (T_mean)^4 [raw nx220]",b.T_plate_mean_K**4,b.mean_T_pow4_K4)
dif=d.T_R4_K-d.T_plate_mean_K; difb=b.T_R4_K-b.T_plate_mean_K
print("T_R4 - T_mean  richardson: min %.4f max %.4f ; raw220: min %.4f max %.4f"%(dif.min(),dif.max(),difb.min(),difb.max()))
print("corr (T_R4-Tmean)_raw220 vs std^2/Tmean:",np.corrcoef(difb,1.5*b.plate_std_K**2/b.T_plate_mean_K)[0,1], " ratio median",np.median(difb/(1.5*b.plate_std_K**2/b.T_plate_mean_K)))
shift=d.T_plate_mean_K-b.T_plate_mean_K; print("Richardson shift of T_mean vs raw220: min %.4f max %.4f K"%(shift.min(),shift.max()))
print("\n== U_L")
UL=(d.Q_solar_W-d.Qu_W)/(A*(d.T_plate_mean_K-d.T_amb_K))
rep("U_L = (Qsolar-Qu)/(A(Tp-Ta)) richardson",UL,d.U_L_W_m2K)
ULb=(b.Q_solar_W-b.Qu_W)/(A*(b.T_plate_mean_K-b.T_amb_K)); rep("same, raw220",ULb,b.U_L_W_m2K)
neg=d[d.U_L_W_m2K<=0]; print("U_L<=0 cases:",len(neg))
cols=["case_id","T_plate_mean_K","T_amb_K","T_glass_mean_K","T_sky_K","Q_rad_W","Q_conv_W","Q_rear_W","U_L_W_m2K"]
print(neg[cols].to_string(index=False,float_format=lambda v:"%.4f"%v))
x=d.copy(); x["UL_recalc"]=UL; x["loss"]=d.Q_rad_W+d.Q_conv_W+d.Q_rear_W; x["dTpa"]=d.T_plate_mean_K-d.T_amb_K
big=x[(x.dTpa.abs()<2)][["case_id","dTpa","loss","U_L_W_m2K","UL_recalc"]]; print("near-singular |Tp-Ta|<2 K:",len(big)); print(big.to_string(index=False,float_format=lambda v:"%.4f"%v))
print("\n== signs")
for q,ref in [("Q_rad_W","T_sky_K"),("Q_conv_W","T_amb_K"),("Q_rear_W","T_amb_K")]:
    n=d[d[q]<0]; print(q,"negative:",len(n),"| of those Tp<Tamb:",int((n.T_plate_mean_K<n.T_amb_K).sum()),"| Tglass<Tamb:",int((n.T_glass_mean_K<n.T_amb_K).sum()), "| Tglass<Tsky:", int((n.T_glass_mean_K<n.T_sky_K).sum()))
    pos=d[d[q]>0]; print("   positive with Tp<Tamb:",int((pos.T_plate_mean_K<pos.T_amb_K).sum()))
# expected sign of Q_rad from glass-sky: eps sigma (Tg^4 - Tsky^4)
print("Q_rad sign vs sign(Tg-Tsky) mismatches:",int((np.sign(d.Q_rad_W)!=np.sign(d.T_glass_mean_K-d.T_sky_K)).sum()))
print("Q_conv sign vs sign(Tg-Tamb) mismatches:",int((np.sign(d.Q_conv_W)!=np.sign(d.T_glass_mean_K-d.T_amb_K)).sum()))
print("Q_rear sign vs sign(Tp-Tamb) mismatches:",int((np.sign(d.Q_rear_W)!=np.sign(d.T_plate_mean_K-d.T_amb_K)).sum()))
mm=d[(np.sign(d.Q_rear_W)!=np.sign(d.T_plate_mean_K-d.T_amb_K))][["case_id","T_plate_mean_K","T_plate_min_K","T_plate_max_K","T_amb_K","Q_rear_W"]]
print(mm.to_string(index=False))
mm=d[(np.sign(d.Q_conv_W)!=np.sign(d.T_glass_mean_K-d.T_amb_K))][["case_id","T_glass_mean_K","T_amb_K","Q_conv_W"]]; print(mm.to_string(index=False))
mm=d[(np.sign(d.Q_rad_W)!=np.sign(d.T_glass_mean_K-d.T_sky_K))][["case_id","T_glass_mean_K","T_sky_K","Q_rad_W"]]; print(mm.to_string(index=False))
print("Tp_mean<T_in cases:",int((d.T_plate_mean_K<d.T_in_K).sum()),"Tout<Tamb:",int((d.T_out_K<d.T_amb_K).sum()))
print("T_sky = 0.0552 Tamb^1.5:",np.abs(0.0552*d.T_amb_K**1.5-d.T_sky_K).max(),"h_wind=5.7+3.8v:",np.abs(5.7+3.8*d.v_wind_m_s-d.h_wind_W_m2K).max())
print("\n== hydraulics")
mu=2.414e-5*10**(247.8/(0.5*(b.T_in_K+b.T_out_K)-140))
rep("mu = Vogel(0.5(Tin+Tout_raw220))",mu,d.mu_Pa_s)
mu_r=2.414e-5*10**(247.8/(0.5*(d.T_in_K+d.T_out_K)-140)); print("mu if recomputed with Richardson T_out: max rel change %.2e"%(np.abs(mu_r/d.mu_Pa_s-1).max()))
rep("Re_in = 4 mdot_ch/(pi Dh mu)",4*d.mdot_channel_kg_s/(math.pi*d.Dh_in_mm/1e3*d.mu_Pa_s),d.Re_in)
Re_true=d.mdot_channel_kg_s*(d.Dh_in_mm/1e3)/(d.A_in_mm2/1e6*d.mu_Pa_s)
print("Re_in(col)/Re_in(=mdot Dh/(A mu)): min %.4f max %.4f"%((d.Re_in/Re_true).min(),(d.Re_in/Re_true).max()))
Re_to=d.mdot_channel_kg_s*(d.Dh_out_mm/1e3)/(d.A_out_mm2/1e6*d.mu_Pa_s)
print("Re_out(col)/Re_out(proper): min %.4f max %.4f"%((d.Re_out/Re_to).min(),(d.Re_out/Re_to).max()))
print("A_out/A_in vs (Dh_out/Dh_in)^2:",np.abs(d.A_out_mm2/d.A_in_mm2-(d.Dh_out_mm/d.Dh_in_mm)**2).max())
print("max Re proper out:",Re_to.max(), " laminar? ",Re_to.max()<2300)
Pr=d.mu_Pa_s*4180/0.6; print("Pr range %.2f-%.2f"%(Pr.min(),Pr.max()))
print("dp/(mdot_ch*mu) cv across cases (geometry-only factor): varies w/ geometry", (d.dp_channel_Pa/(d.mdot_channel_kg_s*d.mu_Pa_s)).describe()[["min","max"]].to_dict())
print("\n== grid dependence 110->220 (raw)")
for c in ["eta","T_plate_mean_K","plate_std_K","plate_spread_K","U_L_W_m2K","Q_rad_W","lateral_bridge_W"]:
    ch=(b[c]-a[c]); print("%-18s |f220-f110| max %.4g  median %.4g ; richardson correction = same"%(c,ch.abs().max(),ch.abs().median()))
ex=d.lateral_bridge_W; print("lateral_bridge min",ex.min(),"parallel median",d[d.f_interdig==0].lateral_bridge_W.median(),"alt median",d[d.f_interdig==1].lateral_bridge_W.median())
