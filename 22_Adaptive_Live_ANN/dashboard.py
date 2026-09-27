"""
Adaptive / Live ANN dashboard (Stage 2).

    pip install -r requirements.txt
    streamlit run dashboard.py

Put the `ann_artifacts/` folder from train_ann.py next to this file (or type its path in the sidebar).
"""
import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ann_core import LiveANN, DEGRADED, KS_P, PSI_HIGH, PSI_MOD

BLUE, ORANGE, GRAY = "#2a78d6", "#eb6834", "#8a8984"
HERE = os.path.dirname(os.path.abspath(__file__))

st.set_page_config(page_title="Adaptive Live ANN", page_icon="🧠", layout="wide")


# ---------------- load model ----------------
st.sidebar.title("🧠 Adaptive Live ANN")
art_dir = st.sidebar.text_input("Artifacts folder", os.path.join(HERE, "ann_artifacts"))
if not os.path.exists(os.path.join(art_dir, "metadata.json")):
    st.error(f"No trained model found in `{art_dir}`. Copy the `ann_artifacts` folder from Kaggle/Colab "
             "next to dashboard.py, or enter its path in the sidebar.")
    st.stop()

if st.session_state.get("art_dir") != art_dir or st.sidebar.button("🔄 Reload from disk"):
    with st.spinner("Loading model..."):
        st.session_state.ann = LiveANN(art_dir)
        st.session_state.art_dir = art_dir
        for k in ["new_df", "analysis", "cand"]:
            st.session_state.pop(k, None)
ann: LiveANN = st.session_state.ann

st.sidebar.metric("Live model version", f"v{ann.version}")
c1, c2 = st.sidebar.columns(2)
c1.metric("Reference rows", f"{len(ann.ref):,}")
c2.metric("Mean skill", f"{ann.meta.get('mean_r2', float('nan')):.3f}")
st.sidebar.caption(f"{len(ann.inputs)} inputs → {len(ann.num_tg)} regression + "
                   f"{len(ann.cat_tg)} classification targets in {len(ann.heads)} heads")

tab_pred, tab_adapt, tab_hist = st.tabs(["🔮 Live prediction", "📥 New data & adaptation", "📈 Model history"])


def fmt(v):
    if isinstance(v, str):
        return v
    a = abs(v)
    return f"{v:.3e}" if (a >= 1e5 or (0 < a < 1e-3)) else f"{v:,.4g}"


# =====================================================================
# TAB 1 - live prediction: move sliders, all outputs update instantly
# =====================================================================
with tab_pred:
    st.subheader("Change the inputs → the ANN predicts every output instantly")
    widen = st.toggle("Allow values outside the training range (extrapolation)", False)

    row = {}
    cols = st.columns(4)
    for i, c in enumerate(ann.num_in):
        s = ann.stats[c]
        lo, hi, mean = s["min"], s["max"], s["mean"]
        if widen:
            span = (hi - lo) or abs(hi) or 1.0
            lo, hi = lo - 0.5 * span, hi + 0.5 * span
        if lo == hi:
            row[c] = lo
            cols[i % 4].text_input(c, fmt(lo), disabled=True)
            continue
        is_int = float(s["min"]).is_integer() and float(s["max"]).is_integer() and (s["max"] - s["min"]) >= 1 \
            and float(ann.ref[c].dropna().sub(ann.ref[c].dropna().round()).abs().max()) == 0
        if is_int:
            row[c] = cols[i % 4].slider(c, int(np.floor(lo)), int(np.ceil(hi)), int(round(mean)), key=f"in_{c}")
        else:
            row[c] = cols[i % 4].slider(c, float(lo), float(hi), float(mean), (hi - lo) / 200,
                                        format="%.4g", key=f"in_{c}")
    for j, c in enumerate(ann.cat_in, start=len(ann.num_in)):
        opts = list(ann.stats[c]["freq"].keys())
        row[c] = cols[j % 4].selectbox(c, opts, key=f"in_{c}")

    x = pd.DataFrame([row])
    pred = ann.predict(x).iloc[0]
    bad = ann.out_of_range(row)
    if bad:
        st.warning("⚠️ Outside the training range (prediction is an extrapolation): " + ", ".join(bad))

    for t in ann.cat_tg:
        conf = pred[f"{t}_confidence"]
        st.info(f"**{t}** predicted: **{pred[t]}** (confidence {conf:.0%})")

    for g, ts in ann.heads.items():
        st.markdown(f"**{g.capitalize()}**")
        mc = st.columns(min(6, len(ts)))
        for k, t in enumerate(ts):
            mc[k % len(mc)].metric(t, fmt(float(pred[t])))

    st.divider()
    st.subheader("Sensitivity: sweep one input, keep the others fixed")
    s1, s2 = st.columns(2)
    xin = s1.selectbox("Input to sweep", ann.num_in, index=ann.num_in.index("G_T_W_m2") if "G_T_W_m2" in ann.num_in else 0)
    yt = s2.selectbox("Output to plot", ann.num_tg, index=ann.num_tg.index("eta") if "eta" in ann.num_tg else 0)
    st_ = ann.stats[xin]
    lo, hi = st_["min"], st_["max"]
    if widen:
        span = (hi - lo) or 1.0
        lo, hi = lo - 0.5 * span, hi + 0.5 * span
    grid = pd.DataFrame([row] * 60)
    grid[xin] = np.linspace(lo, hi, 60)
    yv = ann.predict(grid)[yt]
    fig = go.Figure()
    fig.add_vrect(x0=st_["min"], x1=st_["max"], fillcolor=GRAY, opacity=0.08, line_width=0,
                  annotation_text="training range", annotation_position="top left")
    fig.add_trace(go.Scatter(x=grid[xin], y=yv, mode="lines", line=dict(color=BLUE, width=2), name=yt,
                             hovertemplate=f"{xin}=%{{x:.4g}}<br>{yt}=%{{y:.4g}}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[row[xin]], y=[pred[yt]], mode="markers", marker=dict(size=10, color=ORANGE,
                             line=dict(width=2, color="white")), name="current point",
                             hovertemplate="current: %{y:.4g}<extra></extra>"))
    fig.update_layout(title=f"{yt} vs {xin}", xaxis_title=xin, yaxis_title=yt, height=380,
                      showlegend=False, margin=dict(t=50, b=40), hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)


# =====================================================================
# TAB 3 - history & rollback
# =====================================================================
with tab_hist:
    st.subheader("Model versions and adaptation log")
    h = pd.DataFrame(ann.history)
    st.dataframe(h, use_container_width=True, hide_index=True)
    dep = h[(h.get("deployed", False) == True) & h.get("cand_new", pd.Series(dtype=float)).notna()] \
        if "cand_new" in h else pd.DataFrame()
    if len(dep):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dep.version.astype(int).astype(str).radd("v"), y=dep.cand_new, name="new data",
                                 mode="lines+markers", line=dict(color=ORANGE, width=2), marker=dict(size=8)))
        fig.add_trace(go.Scatter(x=dep.version.astype(int).astype(str).radd("v"), y=dep.cand_ref, name="old data",
                                 mode="lines+markers", line=dict(color=BLUE, width=2), marker=dict(size=8)))
        fig.update_layout(title="Skill of each deployed version", yaxis_title="skill", height=320,
                          hovermode="x unified", legend=dict(orientation="h", y=1.1, x=0))
        st.plotly_chart(fig, use_container_width=True)

    vs = ann.available_versions()
    if len(vs) > 1:
        r1, r2 = st.columns([1, 3])
        v = r1.selectbox("Roll back to", [x for x in vs if x != ann.version])
        if r1.button("↩️ Roll back"):
            ann.rollback(v)
            st.rerun()


# =====================================================================
# TAB 2 - new data -> drift check -> decide -> update -> validate -> deploy
# =====================================================================
with tab_adapt:
    st.subheader("1 · Bring in new data")
    src = st.radio("Source", ["Upload CSV", "Edit data in a table", "Simulate a change"], horizontal=True)
    new_df = None

    if src == "Upload CSV":
        f = st.file_uploader("CSV with the same columns as the training data (targets optional)", type="csv")
        if f is not None:
            new_df = pd.read_csv(f)

    elif src == "Edit data in a table":
        st.caption("Rows are taken from the reference data. Edit any value (inputs or targets), add or delete "
                   "rows, then press *Use this data*.")
        n = st.number_input("Rows to start from", 5, 500, 30, 5)
        base = ann.ref.sample(int(n), random_state=0).reset_index(drop=True)
        edited = st.data_editor(base, num_rows="dynamic", use_container_width=True, height=300, key=f"ed_{n}")
        if st.button("Use this data"):
            st.session_state.new_df = edited
            st.session_state.pop("analysis", None); st.session_state.pop("cand", None)

    else:
        st.caption("Build a labelled batch from the reference data and change it in a controlled way - "
                   "useful for demonstrating the adaptive behaviour in the thesis.")
        a1, a2 = st.columns(2)
        with a1:
            st.markdown("**Data drift** - select only part of the operating range (real labels, shifted inputs)")
            dfeat = st.selectbox("Input", ann.num_in, key="sim_feat",
                                 index=ann.num_in.index("G_T_W_m2") if "G_T_W_m2" in ann.num_in else 0)
            s = ann.stats[dfeat]
            rng = st.slider("Keep rows with this input in", float(s["min"]), float(s["max"]),
                            (float(s["min"]), float(s["max"])), key="sim_rng")
            n = st.slider("Number of rows", 20, 1000, 200, 10)
        with a2:
            st.markdown("**Concept drift** - change how the outputs respond (e.g. fouling, ageing, new material)")
            ctg = st.multiselect("Targets to change", ann.num_tg,
                                 default=[t for t in ["Qu_W", "eta"] if t in ann.num_tg])
            factor = st.slider("Multiply them by", 0.3, 1.7, 1.0, 0.05)
            noise = st.slider("Extra measurement noise (% of value)", 0.0, 20.0, 0.0, 0.5)
        if st.button("Generate batch"):
            pool = ann.ref[(ann.ref[dfeat] >= rng[0]) & (ann.ref[dfeat] <= rng[1])]
            if len(pool) == 0:
                st.error("No rows in that range.")
            else:
                b = pool.sample(min(n, len(pool)), replace=len(pool) < n, random_state=None).reset_index(drop=True)
                r = np.random.default_rng()
                for t in ctg:
                    b[t] = b[t] * factor
                if noise:
                    for t in ann.num_tg:
                        b[t] = b[t] * (1 + r.normal(0, noise / 100, len(b)))
                st.session_state.new_df = b
                st.session_state.pop("analysis", None); st.session_state.pop("cand", None)

    if new_df is not None:
        if st.session_state.get("upload_id") != (f.name, f.size):
            st.session_state.upload_id = (f.name, f.size)
            st.session_state.new_df = new_df
            st.session_state.pop("analysis", None); st.session_state.pop("cand", None)

    new_df = st.session_state.get("new_df")
    if new_df is None:
        st.info("Load or create a batch of new data to continue.")
        st.stop()

    missing_in = [c for c in ann.inputs if c not in new_df]
    if missing_in:
        st.warning(f"Missing input columns (filled with training mean / 'missing'): {missing_in}")
    labelled = ann.has_labels(new_df)
    st.success(f"New batch: **{len(new_df)} rows** · {'with' if labelled else 'without'} target values")

    with st.expander("Predictions for the new batch"):
        p = ann.predict(new_df)
        st.dataframe(pd.concat([new_df[[c for c in ann.inputs if c in new_df]], p.add_prefix("pred_")], axis=1),
                     use_container_width=True, height=250)
        st.download_button("Download predictions CSV", p.to_csv(index=False), "predictions.csv")

    # ---------- analysis ----------
    st.subheader("2 · Check for drift and performance loss")
    if st.button("Analyse new data", type="primary") or "analysis" in st.session_state:
        if "analysis" not in st.session_state:
            with st.spinner("Analysing..."):
                d = ann.drift_report(new_df)
                perf = ann.evaluate(new_df)
                st.session_state.analysis = (d, perf, *ann.decide(d, perf))
        d, perf, decision, why = st.session_state.analysis

        m1, m2, m3 = st.columns(3)
        m1.metric("Drifted inputs", f"{int(d['drift'].sum()) if len(d) else 0} / {len(d)}")
        if perf is not None and "rmse_ratio" in perf:
            deg = int((perf.rmse_ratio > DEGRADED).sum())
            m2.metric("Degraded targets", f"{deg} / {perf.rmse_ratio.notna().sum()}")
            m3.metric("Skill on new data", f"{ann.mean_r2(perf):.3f}",
                      f"{ann.mean_r2(perf) - ann.meta.get('mean_r2', 0):+.3f} vs baseline")
        label = {"keep": "✅ KEEP current model", "incremental": "🔧 INCREMENTAL UPDATE",
                 "full_retrain": "🔁 FULL RETRAIN", "need_labels": "🏷️ NEED LABELLED DATA"}[decision]
        (st.success if decision == "keep" else st.warning)(f"**Decision: {label}**  \n{why}")

        dc, pc = st.columns(2)
        with dc:
            st.markdown("**Input drift** (population stability index)")
            num = d[d.type == "numeric"].sort_values("psi") if len(d) else d
            if len(num):
                fig = go.Figure(go.Bar(
                    x=num.psi, y=num.feature, orientation="h",
                    marker_color=[ORANGE if v else BLUE for v in num.drift],
                    customdata=np.c_[num.ks_p, num.ref_mean, num.new_mean, num.out_of_range * 100],
                    hovertemplate="%{y}<br>PSI %{x:.3f}<br>KS p=%{customdata[0]:.2g}<br>"
                                  "mean %{customdata[1]:.4g} → %{customdata[2]:.4g}<br>"
                                  "outside range %{customdata[3]:.0f}%<extra></extra>"))
                fig.add_vline(PSI_HIGH, line_dash="dash", line_color=GRAY, annotation_text=f"PSI {PSI_HIGH}")
                fig.update_layout(height=max(300, 22 * len(num)), margin=dict(t=20, l=10), xaxis_title="PSI")
                st.plotly_chart(fig, use_container_width=True)
                st.caption(f"Orange = drift (KS p < {KS_P} and PSI > {PSI_MOD}, or PSI > {PSI_HIGH}, "
                           "or > 10 % outside training range).")
            cat = d[d.type == "categorical"] if len(d) else d
            if len(cat):
                st.dataframe(cat[["feature", "tvd", "out_of_range", "drift"]], hide_index=True)
        with pc:
            st.markdown("**Accuracy per target on the new data** (RMSE ÷ training RMSE)")
            if perf is not None and "rmse_ratio" in perf:
                q = perf.dropna(subset=["rmse_ratio"]).sort_values("rmse_ratio")
                fig = go.Figure(go.Bar(
                    x=q.rmse_ratio, y=q.index, orientation="h",
                    marker_color=[ORANGE if v > DEGRADED else BLUE for v in q.rmse_ratio],
                    customdata=np.c_[q.rmse, q.baseline_rmse, q.skill],
                    hovertemplate="%{y}<br>ratio ×%{x:.2f}<br>RMSE %{customdata[0]:.4g} "
                                  "(train %{customdata[1]:.4g})<br>skill %{customdata[2]:.3f}<extra></extra>"))
                fig.add_vline(DEGRADED, line_dash="dash", line_color=GRAY, annotation_text=f"×{DEGRADED}")
                fig.add_vline(1, line_color=GRAY, opacity=0.4)
                fig.update_layout(height=max(300, 22 * len(q)), margin=dict(t=20, l=10), xaxis_title="RMSE ratio")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No target columns in the new data - only drift can be checked.")

        # ---------- update ----------
        if perf is not None:
            st.subheader("3 · Update the model and validate it")
            modes = ["incremental", "full_retrain"]
            u1, u2, u3 = st.columns(3)
            mode = u1.selectbox("Update type", modes,
                                index=modes.index(decision) if decision in modes else 0,
                                format_func={"incremental": "Incremental (fine-tune + replay)",
                                             "full_retrain": "Full retrain (old + new data)"}.get)
            epochs = u2.number_input("Max epochs", 5, 500, 40 if mode == "incremental" else 200, 5)
            auto = u3.toggle("Auto-deploy if better", True)
            if decision == "keep":
                st.caption("The system recommends keeping the model - you can still force an update to compare.")

            if st.button("Train candidate model"):
                bar = st.progress(0.0, "Training...")
                chart = st.empty()
                losses = {"loss": [], "val_loss": []}

                def on_epoch(e, total, logs):
                    losses["loss"].append(logs["loss"]); losses["val_loss"].append(logs["val_loss"])
                    bar.progress(min(1.0, (e + 1) / total), f"Epoch {e + 1}/{total} · val loss {logs['val_loss']:.4f}")
                    if e % 2 == 0:
                        chart.line_chart(pd.DataFrame(losses), color=[BLUE, ORANGE], height=200)

                res = ann.train_candidate(new_df, mode, int(epochs), on_epoch)
                bar.progress(1.0, "Done")
                if auto and res["accept"]:
                    v = ann.deploy(res)
                    res["deployed"] = v
                elif not res["accept"]:
                    ann.log_rejected(res)
                st.session_state.cand = res
                st.rerun()           # refresh sidebar + history with the new state

            res = st.session_state.get("cand")
            if res:
                sc = res["scores"]
                k1, k2, k3, k4 = st.columns(4)
                k1.metric("Old model · new data", f"{sc['old_new']:.3f}")
                k2.metric("Candidate · new data", f"{sc['cand_new']:.3f}", f"{sc['cand_new'] - sc['old_new']:+.3f}")
                k3.metric("Old model · old data", f"{sc['old_ref']:.3f}")
                k4.metric("Candidate · old data", f"{sc['cand_ref']:.3f}", f"{sc['cand_ref'] - sc['old_ref']:+.3f}")
                st.caption("Scores = mean skill (1 − MSE / variance of the reference data) on held-out rows "
                           "that were not used for training.")

                cmp = pd.DataFrame({"old": res["old_new"]["skill"], "candidate": res["cand_new"]["skill"]}).dropna()
                cmp = cmp.loc[(cmp.candidate - cmp.old).abs().sort_values(ascending=False).index[:15]]
                fig = go.Figure()
                for name, col in [("old", BLUE), ("candidate", ORANGE)]:
                    fig.add_trace(go.Bar(name=f"{name} model", y=cmp.index, x=cmp[name], orientation="h",
                                         marker_color=col,
                                         hovertemplate="%{y}: %{x:.3f}<extra>" + name + "</extra>"))
                fig.update_layout(barmode="group", bargap=0.3, bargroupgap=0.1, height=max(320, 40 * len(cmp)),
                                  title="Skill on new data - 15 targets that changed most", xaxis_title="skill",
                                  legend=dict(orientation="h", y=1.02, x=0), margin=dict(l=10))
                st.plotly_chart(fig, use_container_width=True)

                if res.get("deployed"):
                    st.success(f"🚀 {res['reason']} Deployed as **v{res['deployed']}**; the new data was added "
                               "to the reference set.")
                elif res["accept"]:
                    st.info(res["reason"])
                    if st.button("🚀 Deploy candidate"):
                        res["deployed"] = ann.deploy(res)
                        st.rerun()
                else:
                    st.error(f"🛑 {res['reason']} The live model was not changed.")
