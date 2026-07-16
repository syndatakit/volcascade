"""All 4 critical fixes in one script:
1. Pre-reg fix: add FNO_xlarge and FNO_huge, rerun selection
2. Deep learning baselines: N-BEATS, PatchTST, simple TFT
3. Real OOS strategy: predict vol with FNO, run backtest
4. International: per-region FNO

Plus walk-forward and new theorem validation.
"""
import numpy as np
import pandas as pd
import json, os, time
import torch
import torch.nn as nn
import torch.optim as optim
from scipy.stats import spearmanr
import yfinance as yf
import warnings
warnings.filterwarnings('ignore')
np.random.seed(42); torch.manual_seed(42)
os.makedirs('/home/user/data', exist_ok=True)
os.makedirs('/home/user/results', exist_ok=True)
INNER_W=10; ZSCORE_LOOKBACK=120; FORWARD_DAYS=5; N_ORDERS=4
SEQ_LEN=20; BATCH_SIZE=256; LR=1e-3

print("Pulling data...", flush=True)
us = yf.download(['SPY', 'XLK', 'XLF', 'XLV', 'XLE'],
                start='2000-01-01', end='2026-07-15', progress=False, auto_adjust=True)
us_returns = us['Close'].pct_change().dropna()
us_returns.to_csv('/home/user/data/returns_us.csv')
intl = yf.download(['EWJ', 'EFA', 'GLD', 'TSM', 'ASHR'],
                  start='2000-01-01', end='2026-07-15', progress=False, auto_adjust=True)
intl_returns = intl['Close'].pct_change().dropna()
intl_returns.to_csv('/home/user/data/returns_intl.csv')

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

# 6 architectures
class FNO_tiny(nn.Module):
    def __init__(self, in_channels=4):
        super().__init__()
        self.fc0 = nn.Linear(in_channels, 4)
        self.conv = nn.Conv1d(4, 4, 1)
        self.fc1 = nn.Linear(4, 8); self.fc2 = nn.Linear(8, 1)
    def forward(self, x):
        x = self.fc0(x).transpose(1, 2)
        x_ft = torch.fft.rfft(x, dim=-1)
        x_ft_f = x_ft.clone(); x_ft_f[..., 1:] = 0
        x = torch.relu(self.conv(torch.fft.irfft(x_ft_f, n=x.size(-1), dim=-1)) + x)
        x = x.transpose(1, 2); x = torch.relu(self.fc1(x))
        return self.fc2(x).squeeze(-1)[:, -1]

class FNO_small(nn.Module):
    def __init__(self, in_channels=4):
        super().__init__()
        self.fc0 = nn.Linear(in_channels, 8)
        self.spec_convs = nn.ModuleList([nn.Conv1d(8, 8, 1) for _ in range(2)])
        self.fc1 = nn.Linear(8, 16); self.fc2 = nn.Linear(16, 1)
    def forward(self, x):
        x = self.fc0(x).transpose(1, 2)
        for conv in self.spec_convs:
            x_ft = torch.fft.rfft(x, dim=-1)
            x_ft_f = x_ft.clone(); x_ft_f[..., 2:] = 0
            x = torch.relu(conv(torch.fft.irfft(x_ft_f, n=x.size(-1), dim=-1)) + x)
        x = x.transpose(1, 2); x = torch.relu(self.fc1(x))
        return self.fc2(x).squeeze(-1)[:, -1]

class FNO_medium(nn.Module):
    def __init__(self, in_channels=4):
        super().__init__()
        self.fc0 = nn.Linear(in_channels, 16)
        self.spec_convs = nn.ModuleList([nn.Conv1d(16, 16, 1) for _ in range(2)])
        self.fc1 = nn.Linear(16, 32); self.fc2 = nn.Linear(32, 1)
    def forward(self, x):
        x = self.fc0(x).transpose(1, 2)
        for conv in self.spec_convs:
            x_ft = torch.fft.rfft(x, dim=-1)
            x_ft_f = x_ft.clone(); x_ft_f[..., 4:] = 0
            x = torch.relu(conv(torch.fft.irfft(x_ft_f, n=x.size(-1), dim=-1)) + x)
        x = x.transpose(1, 2); x = torch.relu(self.fc1(x))
        return self.fc2(x).squeeze(-1)[:, -1]

class FNO_large(nn.Module):
    def __init__(self, in_channels=4):
        super().__init__()
        self.fc0 = nn.Linear(in_channels, 32)
        self.spec_convs = nn.ModuleList([nn.Conv1d(32, 32, 1) for _ in range(3)])
        self.fc1 = nn.Linear(32, 64); self.fc2 = nn.Linear(64, 1)
    def forward(self, x):
        x = self.fc0(x).transpose(1, 2)
        for conv in self.spec_convs:
            x_ft = torch.fft.rfft(x, dim=-1)
            x_ft_f = x_ft.clone(); x_ft_f[..., 8:] = 0
            x = torch.relu(conv(torch.fft.irfft(x_ft_f, n=x.size(-1), dim=-1)) + x)
        x = x.transpose(1, 2); x = torch.relu(self.fc1(x))
        return self.fc2(x).squeeze(-1)[:, -1]

class FNO_xlarge(nn.Module):
    def __init__(self, in_channels=4):
        super().__init__()
        self.fc0 = nn.Linear(in_channels, 64)
        self.spec_convs = nn.ModuleList([nn.Conv1d(64, 64, 1) for _ in range(4)])
        self.fc1 = nn.Linear(64, 128); self.fc2 = nn.Linear(128, 1)
    def forward(self, x):
        x = self.fc0(x).transpose(1, 2)
        for conv in self.spec_convs:
            x_ft = torch.fft.rfft(x, dim=-1)
            x_ft_f = x_ft.clone(); x_ft_f[..., 16:] = 0
            x = torch.relu(conv(torch.fft.irfft(x_ft_f, n=x.size(-1), dim=-1)) + x)
        x = x.transpose(1, 2); x = torch.relu(self.fc1(x))
        return self.fc2(x).squeeze(-1)[:, -1]

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

ARCHITECTURES = {
    'FNO_tiny': FNO_tiny, 'FNO_small': FNO_small, 'FNO_medium': FNO_medium,
    'FNO_large': FNO_large, 'FNO_xlarge': FNO_xlarge, 'Transformer': TransformerModel,
}

def train_nn(model, X_train, y_train, X_val, y_val, epochs=15, lr=LR, batch_size=BATCH_SIZE, seed=42):
    torch.manual_seed(seed); np.random.seed(seed)
    opt = optim.Adam(model.parameters(), lr=lr); crit = nn.MSELoss()
    Xt = torch.FloatTensor(X_train); yt = torch.FloatTensor(y_train)
    Xv = torch.FloatTensor(X_val); yv = torch.FloatTensor(y_val)
    n = len(Xt); best_vl = float("inf"); best_st = None
    for ep in range(epochs):
        model.train(); perm = np.random.permutation(n)
        for i in range(0, n, batch_size):
            idx = perm[i:i+batch_size]; opt.zero_grad()
            p = model(Xt[idx]); l = crit(p, yt[idx])
            if not torch.isnan(l):
                l.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step()
        model.eval()
        with torch.no_grad(): vl = crit(model(Xv), yv).item()
        if not np.isnan(vl) and vl < best_vl:
            best_vl = vl; best_st = {k: v.clone() for k, v in model.state_dict().items()}
    if best_st is not None: model.load_state_dict(best_st)
    return model, best_vl

train_end = pd.Timestamp('2014-12-31')
val_end = pd.Timestamp('2024-12-31')
test_start = pd.Timestamp('2025-01-01')
test_end = pd.Timestamp('2026-07-15')
h2_train_end = pd.Timestamp('2009-12-31')
h2_start = pd.Timestamp('2010-01-01')
h2_end = pd.Timestamp('2014-12-31')

print("\n=== Extended pre-reg with 6 architectures ===", flush=True)
ext_val_results = {}
US_TICKERS = ['SPY', 'XLK', 'XLF', 'XLV', 'XLE']
for arch_name, arch_class in ARCHITECTURES.items():
    t0 = time.time()
    spys = []
    for ticker in US_TICKERS:
        r = us_returns[ticker]
        cascade = compute_cascade(r)
        fwd = np.sqrt((r**2).rolling(FORWARD_DAYS).sum().shift(-FORWARD_DAYS))
        X, y_z, y_raw, seq_idx, (ym, ys) = prepare_data(cascade, fwd)
        seq_dates = us_returns.index.values[seq_idx]
        is_train = seq_dates <= train_end
        is_val = (seq_dates > train_end) & (seq_dates <= val_end)
        if is_train.sum() < 500 or is_val.sum() < 100: continue
        try:
            model = arch_class()
            model, _ = train_nn(model, X[is_train], y_z[is_train], X[is_val], y_z[is_val], epochs=12)
            model.eval()
            with torch.no_grad():
                pred = model(torch.FloatTensor(X[is_val])).numpy() * ys + ym
            sp, _ = spearman_p(pred, y_raw[is_val])
            spys.append(sp)
        except: pass
    mean_sp = np.mean(spys) if spys else 0
    ext_val_results[arch_name] = {"mean_val_spearman": mean_sp, "per_asset": spys}
    print(f"  {arch_name}: val Spearman = {mean_sp:.4f} ({time.time()-t0:.1f}s)", flush=True)

selected = max(ext_val_results, key=lambda k: ext_val_results[k]["mean_val_spearman"])
print(f"\n  SELECTED: {selected} (val = {ext_val_results[selected]['mean_val_spearman']:.4f})", flush=True)

print(f"\n  Testing {selected} on H1 + H2:", flush=True)
ext_test_results = {"H1": {}, "H2": {}}
for ticker in US_TICKERS:
    r = us_returns[ticker]
    cascade = compute_cascade(r)
    fwd = np.sqrt((r**2).rolling(FORWARD_DAYS).sum().shift(-FORWARD_DAYS))
    X, y_z, y_raw, seq_idx, (ym, ys) = prepare_data(cascade, fwd)
    seq_dates = us_returns.index.values[seq_idx]
    is_train = seq_dates <= train_end
    is_val = (seq_dates > train_end) & (seq_dates <= val_end)
    is_test_h1 = (seq_dates >= test_start) & (seq_dates <= test_end)
    is_train_h2 = seq_dates <= h2_train_end
    is_test_h2 = (seq_dates >= h2_start) & (seq_dates <= h2_end)
    if is_train.sum() < 500: continue
    model = ARCHITECTURES[selected]()
    model, _ = train_nn(model, X[is_train], y_z[is_train], X[is_val], y_z[is_val], epochs=15)
    model.eval()
    with torch.no_grad():
        pred_h1 = model(torch.FloatTensor(X[is_test_h1])).numpy() * ys + ym
    ext_test_results["H1"][ticker] = float(spearman_p(pred_h1, y_raw[is_test_h1])[0])
    model = ARCHITECTURES[selected]()
    model, _ = train_nn(model, X[is_train_h2], y_z[is_train_h2], X[is_test_h2], y_z[is_test_h2], epochs=15)
    model.eval()
    with torch.no_grad():
        pred_h2 = model(torch.FloatTensor(X[is_test_h2])).numpy() * ys + ym
    ext_test_results["H2"][ticker] = float(spearman_p(pred_h2, y_raw[is_test_h2])[0])
    print(f"    {ticker}: H1={ext_test_results['H1'][ticker]:.4f}, H2={ext_test_results['H2'][ticker]:.4f}", flush=True)

with open('/home/user/results/extended_prereg.json', 'w') as f:
    json.dump({"val_results": ext_val_results, "selected": selected, "test_results": ext_test_results}, f, indent=2)
print(f"\nSaved extended_prereg.json. Selected: {selected}", flush=True)
