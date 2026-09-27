# Adaptive / Live ANN – solar collector (GRAIL CFD dataset)

| File | Stage | What it does |
|---|---|---|
| `train_ann.py` | 1 | Trains the multi-task residual ANN on Kaggle/Colab → `ann_artifacts/` |
| `ann_core.py` | 2–4 | Prediction, drift detection, keep/update/retrain decision, candidate training, validation, versioned deployment, rollback |
| `dashboard.py` | 2–5 | Streamlit dashboard on top of `ann_core.py` |

## Run the dashboard (on your PC)

```bash
cd 22_Adaptive_Live_ANN
# put the ann_artifacts/ folder downloaded from Kaggle here
pip install -r requirements.txt
streamlit run dashboard.py          # opens http://localhost:8501
```

Use the same TensorFlow / scikit-learn major versions as the notebook that trained the model.

## Tabs

1. **Live prediction** – sliders for every input; all outputs + convergence update instantly.
   Extrapolation warning outside the training range; sensitivity sweep of any input vs any output.
2. **New data & adaptation**
   - Source: *upload CSV*, *edit a table*, or *simulate a change* (data drift = select part of the
     operating range; concept drift = scale chosen targets; optional noise).
   - **Analyse** → input drift (KS test + PSI + range check) and per-target RMSE vs training RMSE → decision:
     `keep` / `incremental` / `full_retrain` / `need_labels`.
   - **Train candidate** → incremental (fine-tune from current weights, LR 1e-4, replay of old data)
     or full retrain (same architecture, fresh weights, old + new data).
   - **Validate** on held-out new *and* old rows; deploy only if better on new data and not worse
     than 0.02 skill on old data (no catastrophic forgetting). Auto-deploy or manual.
3. **Model history** – every deployed / rejected candidate, skill per version, rollback.

Every deployment saves `ann_artifacts/versions/vN/model.keras`, appends the new data to
`reference_data.csv`, updates the baseline in `metadata.json` and logs to `history.json`.

## Decision thresholds (`ann_core.py`, top of file)

| Rule | Value |
|---|---|
| Input drift | KS p < 0.01 and PSI > 0.10, or PSI > 0.25, or > 10 % of values outside training range |
| Degraded target | RMSE on new data > 1.5 × training RMSE |
| Keep | no degraded targets |
| Incremental | ≤ 30 % of targets degraded and none worse than 4 × |
| Full retrain | otherwise |
| Deploy | candidate skill on new data > old model, and skill on old data drops ≤ 0.02 |

*Skill* = 1 − MSE / variance of the target in the reference data (an R² that stays meaningful on small batches).
