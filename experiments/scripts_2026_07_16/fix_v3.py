"""Final fixes: better real strategy + per-region + walk-forward."""
import numpy as np
import pandas as pd
import json, os
import torch
import torch.nn as nn
import torch.optim as optim
from scipy.stats import spearmanr
import warnings
warnings.filterwarnings('ignore')
np.random.seed(42); torch.manual_seed(42)
INNER_W=10; ZSCORE_LOOKBACK=120; FORWARD_DAYS=5; N_ORDERS=4
SEQ_LEN=20; BATCH_SIZE=256; LR=1e-3

us_returns = pd.read_csv('/home/user/data/returns_us.csv', index_col=0, parse_dates=True)
intl_returns = pd.read_csv('/home/user/data/returns_intl.csv', index_col=0, parse_dates=True)

def realized_vol(r, w=INNER_W): return np.sqrt((r**2).rolling(w).sum())
def rolling_std(s, w=INNER_W): return s.rolling(w).std()
def zscore(s, lookback=ZSCORE_LOOKBACK): return (s - s.rolling(lookback).mean()) / s.rolling(lookback).std()
def compute_cascade(r, K=N_ORDERS):
    V1 = realized_vol(r, INNER_W)
    levels = [V1]
    for k in range(2, K+1): levels.append(rolling_std(levels[-1], INNER_W))
    levels = [zscore(v, ZSCORE_LOOKBACK) for v in levels]
    return pd.concat(levels, axis=1, keys=[f"V{k+1}" for k in range(K)])
def spearman_p(x, y):
    if len(x) < 5 or np.std(x) < 1e-8 or np.std(y) < 1e-8: return 0.0, 1.0
    res = spearmanr(x, y)
    return float(res[0]), float(res[1])
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
class TransformerModel(nn.Module):
    def __init__(self, in_channels=4, d_model=16, nhead=2, n_layers=2):
        super().__init__()
        self.proj = nn.Linear(in_channels, d_model)
        layer = nn.TransformerEncoderLayer(d_model=d_model, nhead=nhead, dim_feedforward=32, batch_first=True, dropout=0.0)
        self.transformer = nn.TransformerEncoder(layer, num_layers=n_layers)
        self.fc = nn.Linear(d_model, 1)
    def forward(self, x):
        x = self.proj(x); x = self.transformer(x)
        return self.fc(x[:, -1, :]).squeeze(-1)
def train_nn(model, X_train, y_train, X_val, y_val, epochs=15, lr=LR, batch_size=BATCH_SIZE, seed=42):
    torch.manual_seed(seed); np.random.seed(seed)
    opt = optim.Adam(model.parameters(), lr=lr)
    crit = nn.MSELoss()
    Xt = torch.FloatTensor(X_train); yt = torch.FloatTensor(y_train)
    Xv = torch.FloatTensor(X_val); yv = torch.FloatTensor(y_val)
    n = len(Xt); best_vl = float("inf"); best_st = None
    for ep in range(epochs):
        model.train()
        perm = np.random.permutation(n)
        for i in range(0, n, batch_size):
            idx = perm[i:i+batch_size]
            opt.zero_grad()
            p = model(Xt[idx])
            l = crit(p, yt[idx])
            if not torch.isnan(l):
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

train_end = pd.Timestamp('2014-12-31')
val_end = pd.Timestamp('2024-12-31')
test_start = pd.Timestamp('2025-01-01')
test_end = pd.Timestamp('2026-07-15')

# Better real strategy: vol-targeting clipped + vol-timing
US_TICKERS = ['SPY', 'XLK', 'XLF', 'XLV', 'XLE']
strategy_results = {"vol_target_clipped": {}, "vol_timing_cascade": {}}

for ticker in US_TICKERS:
    r = us_returns[ticker]
    fwd = np.sqrt((r**2).rolling(FORWARD_DAYS).sum().shift(-FORWARD_DAYS))
    cascade = compute_cascade(r)
    X, y_z, y_raw, seq_idx, (ym, ys) = prepare_data(cascade, fwd)
    seq_dates = us_returns.index.values[seq_idx]
    is_train = seq_dates <= train_end
    is_val = (seq_dates > train_end) & (seq_dates <= val_end)
    is_test = (seq_dates >= test_start) & (seq_dates <= test_end)
    if is_train.sum() < 500: continue
    model = TransformerModel()
    model, _ = train_nn(model, X[is_train], y_z[is_train], X[is_val], y_z[is_val], epochs=15)
    model.eval()
    with torch.no_grad():
        pred_vol = model(torch.FloatTensor(X[is_test])).numpy() * ys + ym
    test_dates = seq_dates[is_test]
    r_test = r.loc[test_dates].values
    hist_mean = r_test[1:].std() * np.sqrt(252)
    daily_mean = hist_mean / np.sqrt(252)
    pred_vol_clipped = np.clip(pred_vol, 0.5 * daily_mean, 2.0 * daily_mean)
    target_vol = 0.10; annualize = np.sqrt(252)
    pos1 = np.clip((target_vol / annualize) / pred_vol_clipped, 0, 5)
    sr1 = float((pos1[:-1] * r_test[1:]).mean() / (pos1[:-1] * r_test[1:]).std() * annualize) if (pos1[:-1] * r_test[1:]).std() > 0 else 0.0
    cs_s = []
    for d in cascade.index:
        z = cascade.loc[d].values
        if np.any(np.isnan(z)): continue
        k = np.arange(1, 5); km = k.mean(); zm = z.mean()
        s = np.sum((k-km)*(z-zm))/np.sum((k-km)**2)
        cs_s.append(s)
    cs_pred = pd.Series(cs_s, index=cascade.index[~cascade.isna().any(axis=1)])
    cs_in_test = cs_pred.reindex(test_dates).values
    cs_z = (cs_in_test - np.nanmean(cs_in_test)) / np.nanstd(cs_in_test)
    pos2 = 1.0 + 0.5 * cs_z
    pos2 = np.clip(pos2, 0, 3)
    sr2 = float((pos2[:-1] * r_test[1:]).mean() / (pos2[:-1] * r_test[1:]).std() * annualize) if (pos2[:-1] * r_test[1:]).std() > 0 else 0.0
    sr_bh = float(r_test[1:].mean() / r_test[1:].std() * annualize) if r_test[1:].std() > 0 else 0.0
    strategy_results["vol_target_clipped"][ticker] = {"sharpe": sr1, "bh_sharpe": sr_bh, "win": sr1 > sr_bh}
    strategy_results["vol_timing_cascade"][ticker] = {"sharpe": sr2, "bh_sharpe": sr_bh, "win": sr2 > sr_bh}
    print(f"  {ticker}: vol-target={sr1:.3f} (B&H={sr_bh:.3f}) | vol-timing={sr2:.3f} | wins: T={sr1>sr_bh}, C={sr2>sr_bh}", flush=True)

with open('/home/user/results/better_strategy.json', 'w') as f:
    json.dump(strategy_results, f, indent=2)

# Per-region Transformer (intl)
print("\n=== Per-region Transformer (intl) ===", flush=True)
intl_train_start = pd.Timestamp('2010-01-01')
intl_train_end = pd.Timestamp('2016-12-31')
intl_val_end = pd.Timestamp('2019-12-31')
intl_h1_start = pd.Timestamp('2020-01-01')
intl_h1_end = pd.Timestamp('2024-12-31')
INTL_TICKERS = ['EWJ', 'EFA', 'GLD', 'TSM', 'ASHR']
intl_results = {}
for ticker in INTL_TICKERS:
    r = intl_returns[ticker].dropna()
    if len(r) < 1500: continue
    cascade = compute_cascade(r)
    fwd = np.sqrt((r**2).rolling(FORWARD_DAYS).sum().shift(-FORWARD_DAYS))
    X, y_z, y_raw, seq_idx, (ym, ys) = prepare_data(cascade, fwd)
    seq_dates = r.index.values[seq_idx]
    is_train = (seq_dates >= intl_train_start) & (seq_dates <= intl_train_end)
    is_val = (seq_dates > intl_train_end) & (seq_dates <= intl_val_end)
    is_test_h1 = (seq_dates >= intl_h1_start) & (seq_dates <= intl_h1_end)
    if is_train.sum() < 500 or is_val.sum() < 100: continue
    model = TransformerModel()
    model, _ = train_nn(model, X[is_train], y_z[is_train], X[is_val], y_z[is_val], epochs=15)
    model.eval()
    with torch.no_grad():
        pred_h1 = model(torch.FloatTensor(X[is_test_h1])).numpy() * ys + ym
    intl_results[ticker] = float(spearman_p(pred_h1, y_raw[is_test_h1])[0])
    print(f"  {ticker} (per-region): H1={intl_results[ticker]:.4f}", flush=True)

with open('/home/user/results/intl_per_region.json', 'w') as f:
    json.dump(intl_results, f, indent=2)

# Walk-forward
print("\n=== Walk-forward US (4 windows) ===", flush=True)
wf_results = {}
windows = [
    ('2005-2010', pd.Timestamp('2004-12-31'), pd.Timestamp('2005-01-01'), pd.Timestamp('2010-12-31')),
    ('2010-2015', pd.Timestamp('2009-12-31'), pd.Timestamp('2010-01-01'), pd.Timestamp('2015-12-31')),
    ('2015-2020', pd.Timestamp('2014-12-31'), pd.Timestamp('2015-01-01'), pd.Timestamp('2020-12-31')),
    ('2020-2025', pd.Timestamp('2019-12-31'), pd.Timestamp('2020-01-01'), pd.Timestamp('2025-12-31')),
]
for ticker in US_TICKERS:
    r = us_returns[ticker]
    fwd = np.sqrt((r**2).rolling(FORWARD_DAYS).sum().shift(-FORWARD_DAYS))
    cascade = compute_cascade(r)
    X, y_z, y_raw, seq_idx, (ym, ys) = prepare_data(cascade, fwd)
    seq_dates = us_returns.index.values[seq_idx]
    ticker_wf = {}
    for win_name, train_end_dt, test_start_dt, test_end_dt in windows:
        is_train = seq_dates <= train_end_dt
        is_test = (seq_dates >= test_start_dt) & (seq_dates <= test_end_dt)
        if is_train.sum() < 500 or is_test.sum() < 30: continue
        val_start = train_end_dt - pd.DateOffset(years=1)
        is_val = (seq_dates >= val_start) & (seq_dates <= train_end_dt)
        if is_val.sum() < 50: is_val = is_train
        model = TransformerModel()
        model, _ = train_nn(model, X[is_train], y_z[is_train], X[is_val], y_z[is_val], epochs=12)
        model.eval()
        with torch.no_grad():
            pred = model(torch.FloatTensor(X[is_test])).numpy() * ys + ym
        sp = spearman_p(pred, y_raw[is_test])[0]
        ticker_wf[win_name] = sp
    wf_results[ticker] = ticker_wf
    sps = list(ticker_wf.values())
    print(f"  {ticker}: {len(sps)} windows, mean Spearman={np.mean(sps):.3f}", flush=True)

with open('/home/user/results/walk_forward.json', 'w') as f:
    json.dump(wf_results, f, indent=2)
print("All fixes done.", flush=True)
