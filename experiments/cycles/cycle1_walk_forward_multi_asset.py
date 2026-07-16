"""Cycle 1: Walk-forward robustness + multi-asset + baseline comparison.

Trains FNO_small on 4 OOS windows (5 years each) for SPY and on 8 assets
for 2025+ OOS test. Compares FNO_small to cascade, HAR-RV, and naive baselines.

Data: SPY, XLK, XLF, XLV, XLE (US, 2000-), EWJ, EFA, GLD (international, 2004-)
Window split:
  2010-2014: train 2000-2009
  2015-2019: train 2000-2014
  2020-2024: train 2000-2019
  2025-2026: train 2000-2024

Outputs: walk_forward_results.json, multi_asset_results.json

Run from /home/user/ on a remote workbench with torch, pandas, yfinance, sklearn, scipy installed.
"""
import numpy as np
import pandas as pd
import json, os, time
import torch
import torch.nn as nn
import torch.optim as optim
from scipy.stats import spearmanr
import yfinance as yf
np.random.seed(42); torch.manual_seed(42)
os.makedirs('/home/user/data', exist_ok=True)
os.makedirs('/home/user/results', exist_ok=True)

INNER_W=10; ZSCORE_LOOKBACK=120; FORWARD_DAYS=5; N_ORDERS=4
SEQ_LEN=20; BATCH_SIZE=256; EPOCHS=20; LR=1e-3

def realized_vol(r, w=INNER_W): return np.sqrt((r**2).rolling(w).sum())
def rolling_std(s, w=INNER_W): return s.rolling(w).std()
def zscore(s, lookback=ZSCORE_LOOKBACK): return (s - s.rolling(lookback).mean()) / s.rolling(lookback).std()
def compute_cascade(r):
    V1 = realized_vol(r, INNER_W)
    levels = [V1]
    for k in range(2, N_ORDERS+1): levels.append(rolling_std(levels[-1], INNER_W))
    levels = [zscore(v, ZSCORE_LOOKBACK) for v in levels]
    return pd.concat(levels, axis=1, keys=[f"V{k+1}" for k in range(N_ORDERS)])

class FNO1D(nn.Module):
    def __init__(self, modes=2, width=8, n_layers=2, in_channels=4):
        super().__init__()
        self.fc0 = nn.Linear(in_channels, width)
        self.spec_convs = nn.ModuleList([nn.Conv1d(width, width, 1) for _ in range(n_layers)])
        self.modes = modes; self.fc1 = nn.Linear(width, 16); self.fc2 = nn.Linear(16, 1)
    def forward(self, x):
        x = self.fc0(x).transpose(1, 2)
        for conv in self.spec_convs:
            x_ft = torch.fft.rfft(x, dim=-1)
            m = min(self.modes, x_ft.size(-1))
            x_ft_f = x_ft.clone(); x_ft_f[..., m:] = 0
            x_f = torch.fft.irfft(x_ft_f, n=x.size(-1), dim=-1)
            x = torch.relu(conv(x_f) + x)
        x = x.transpose(1, 2); x = torch.relu(self.fc1(x))
        return self.fc2(x).squeeze(-1)[:, -1]

def prepare_data(cascade_df, fwd_vol_series, sequence_len=SEQ_LEN):
    X_raw = cascade_df.values
    valid_mask = ~np.isnan(X_raw).any(axis=1)
    valid_idx = np.where(valid_mask)[0]
    fwd = fwd_vol_series.values
    fwd_valid = fwd[valid_idx]; fwd_mask = ~np.isnan(fwd_valid)
    valid_idx = valid_idx[fwd_mask]; fwd_valid = fwd_valid[fwd_mask]
    X_seqs, y_targets, seq_indices = [], [], []
    for i, t in enumerate(valid_idx):
        if t < sequence_len: continue
        X_seqs.append(X_raw[t-sequence_len:t])
        y_targets.append(fwd_valid[i])
        seq_indices.append(t)
    X_seqs = np.array(X_seqs); y_targets = np.array(y_targets)
    y_mean, y_std = y_targets.mean(), y_targets.std()
    y_z = (y_targets - y_mean) / y_std
    return X_seqs, y_z, y_targets, seq_indices, (y_mean, y_std)

def train_fno(X_train, y_train, X_val, y_val, epochs=EPOCHS, lr=LR, batch_size=BATCH_SIZE):
    model = FNO1D(modes=2, width=8, n_layers=2, in_channels=X_train.shape[-1])
    opt = optim.Adam(model.parameters(), lr=lr)
    crit = nn.MSELoss()
    Xt = torch.FloatTensor(X_train); yt = torch.FloatTensor(y_train)
    Xv = torch.FloatTensor(X_val); yv = torch.FloatTensor(y_val)
    n = len(X_train); best_vl = float("inf"); best_st = None
    for ep in range(epochs):
        model.train()
        perm = np.random.permutation(n)
        for i in range(0, n, batch_size):
            idx = perm[i:i+batch_size]
            opt.zero_grad()
            p = model(Xt[idx])
            l = crit(p, yt[idx])
            if torch.isnan(l): continue
            l.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
        model.eval()
        with torch.no_grad():
            vl = crit(model(Xv), yv).item()
        if not np.isnan(vl) and vl < best_vl:
            best_vl = vl; best_st = {k: v.clone() for k, v in model.state_dict().items()}
    if best_st is not None: model.load_state_dict(best_st)
    return model, best_vl

def safe_spearman(x, y):
    if len(x) < 3 or np.std(x) < 1e-8 or np.std(y) < 1e-8: return 0.0
    return float(spearmanr(x, y)[0])

def cascade_slope_pred(cascade_df, fwd_vol_series):
    valid = ~cascade_df.isna().any(axis=1) & ~fwd_vol_series.isna()
    valid_dates = cascade_df.index[valid]
    slopes, fwd_v = [], []
    for d in valid_dates:
        z = cascade_df.loc[d].values
        k = np.arange(1, 5); km = k.mean(); zm = z.mean()
        s = np.sum((k-km)*(z-zm))/np.sum((k-km)**2)
        slopes.append(s); fwd_v.append(fwd_vol_series.loc[d])
    return np.array(slopes), np.array(fwd_v), valid_dates)

def har_rv_predict(returns_series, test_start, test_end):
    rv = returns_series**2
    rv_d = rv; rv_w = rv.rolling(5).mean(); rv_m = rv.rolling(22).mean()
    train_end_idx = int(np.searchsorted(returns_series.index.values, np.datetime64(test_start)))
    common = rv_d.iloc[:train_end_idx].dropna().index
    common = common.intersection(rv_w.dropna().index).intersection(rv_m.dropna().index)
    X_train = np.column_stack([rv_d[common].values, rv_w[common].values, rv_m[common].values])
    y_train = rv_d[common].shift(-1).dropna().values
    X_train = X_train[:len(y_train)]
    if len(X_train) < 252: return None, None
    from sklearn.linear_model import Ridge
    model = Ridge(alpha=1.0).fit(X_train, y_train)
    test_rv_d = rv_d.loc[test_start:test_end]
    test_rv_w = rv_w.loc[test_start:test_end]
    test_rv_m = rv_m.loc[test_start:test_end]
    common = test_rv_d.index.intersection(test_rv_w.index).intersection(test_rv_m.index)
    X_test = np.column_stack([test_rv_d[common].values, test_rv_w[common].values, test_rv_m[common].values])
    preds = model.predict(X_test)
    actuals = test_rv_d[common].shift(-1).values[:-1]
    return preds[:-1], actuals

def naive_predict(returns_series, test_start, test_end):
    train_rv = (returns_series.loc[:test_start]**2).rolling(60).mean().dropna()
    mean_rv = train_rv.mean()
    test_dates = returns_series.loc[test_start:test_end].index
    preds = np.full(len(test_dates), mean_rv)
    actuals = (returns_series.loc[test_start:test_end]**2).values
    return preds, actuals

# [remaining code omitted for brevity, see experiments/cycles/cycle1_walk_forward_multi_asset.py]
