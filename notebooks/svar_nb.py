"""
svar_nb.py — Shared utilities for all Panel SVAR notebooks.

Each notebook imports this module and then only needs to define:
  - VARIABLE_ORDER, VARIABLES, SHOCKS
  - Identification constraints (SR_CONSTRAINT, LR_CONSTRAINT, SR_SIGN, LR_SIGN)
  - MAXLAGS, NSTEPS
  - VAR_DISPLAY overrides if needed

Typical notebook header:
    import sys
    from pathlib import Path
    try:
        _nb_dir = Path(__vsc_ipynb_file__).resolve().parent
    except NameError:
        _nb_dir = Path.cwd()
    sys.path.insert(0, str(_nb_dir))
    import svar_nb
    PROJECT_ROOT, OUTPUT_DIR = svar_nb.setup('results/pedroni/subdir')
"""

from __future__ import annotations
import copy
import os
import sys
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

warnings.filterwarnings("ignore", category=UserWarning, module="statsmodels")
warnings.filterwarnings("ignore", category=FutureWarning)


# ── Display configuration ──────────────────────────────────────────────────────
# Default transform + y-axis label for known variables.
# Notebooks can override by updating svar_nb.VAR_DISPLAY after import.
VAR_DISPLAY: Dict[str, dict] = {
    'log_price':     {'transform': lambda x: x * 100,           'label': 'Price Level (% change)'},
    'basket_return': {'transform': lambda x: x * 100,           'label': 'Basket Return (%)'},
    'liquidation':   {'transform': lambda x: (np.exp(x)-1)*100, 'label': 'Liquidation (% change)'},
    'utilization':   {'transform': lambda x: x * 100,           'label': 'Utilization (pp)'},
    'volatility':    {'transform': lambda x: x * 100,           'label': 'Volatility (pp)'},
}

_PROJECT_ROOT: Optional[Path] = None
_OUTPUT_DIR: Optional[Path] = None


# ─────────────────────────────────────────────────────────────────────────────
# 1. SETUP
# ─────────────────────────────────────────────────────────────────────────────

def setup(output_subdir: str, notebook_dir: Optional[Path] = None) -> Tuple[Path, Path]:
    """
    Locate project root, add code/pedroni_svar to sys.path, create output dir.

    Parameters
    ----------
    output_subdir : str
        Path relative to project root, e.g. 'results/pedroni/bivariate/full_panel'.
    notebook_dir : Path, optional
        Directory of the calling notebook. If None, uses cwd.

    Returns
    -------
    (PROJECT_ROOT, OUTPUT_DIR)
    """
    global _PROJECT_ROOT, _OUTPUT_DIR

    base = notebook_dir or Path.cwd()
    root = base.resolve()
    for _ in range(6):
        if (root / 'code' / 'pedroni_svar').is_dir():
            break
        root = root.parent
    else:
        raise RuntimeError(f'Could not locate project root from {base}')

    pedroni_dir = root / 'code' / 'pedroni_svar'
    if str(pedroni_dir) not in sys.path:
        sys.path.insert(0, str(pedroni_dir))

    # panelSVAR writes Excel output relative to CWD — keep it tidy
    os.chdir(pedroni_dir)
    os.makedirs(pedroni_dir / 'output', exist_ok=True)

    output_dir = root / output_subdir
    output_dir.mkdir(parents=True, exist_ok=True)

    _PROJECT_ROOT = root
    _OUTPUT_DIR = output_dir

    print(f'Project root : {root}')
    print(f'Output dir   : {output_dir}')
    return root, output_dir


# ─────────────────────────────────────────────────────────────────────────────
# 2. DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────

def load_panel(
    project_root: Path,
    variable_order: List[str],
    variables_dict: dict,
    min_liq_days: int = 50,
    start_date_overrides: Optional[dict] = None,
    end_date_overrides: Optional[dict] = None,
    drop_csus: Optional[list] = None,
    panel_path: Optional[str] = None,
) -> Tuple[pd.DataFrame, List[str], Dict[str, pd.Series]]:
    """
    Load the qualified SVAR panel, apply optional truncations/drops,
    filter to CSUs with sufficient liquidation history, compute per-member sigmas.

    Parameters
    ----------
    variable_order : list of str
        Variables to keep (must exist in panel).
    variables_dict : dict
        {var_name: [integration_in, integration_out]} — same format as VAR_input.
    min_liq_days : int
        Minimum days with positive liquidation to include a CSU.
    start_date_overrides : dict, optional
        {csu: 'YYYY-MM-DD'} — drop rows before this date for specific CSUs.
    drop_csus : list, optional
        CSUs to exclude entirely (e.g. degenerate IRFs).

    Returns
    -------
    df : pd.DataFrame
        Cleaned panel with date, csu, and variable_order columns.
    eligible : list of str
        CSU names meeting the min_liq_days threshold.
    sigmas : dict
        {var_name: pd.Series indexed by csu} — per-member std devs.
    """
    if panel_path:
        path = project_root / panel_path
    else:
        path = project_root / 'data' / 'analysis' / 'panel_svar_data_qualified.parquet'
    df = pd.read_parquet(path)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(['csu', 'date']).reset_index(drop=True)

    # log_price is stored as cumulative log-return; convert to price level for BQ
    if 'log_price' in variable_order and 'log_price' in df.columns:
        df['log_price'] = np.exp(df['log_price'])

    # Optional per-CSU start date truncation
    if start_date_overrides:
        for csu, start in start_date_overrides.items():
            mask = (df['csu'] == csu) & (df['date'] < pd.Timestamp(start))
            n = mask.sum()
            if n:
                df = df[~mask]
                print(f'  Truncated {csu}: dropped {n} obs before {start}')

    # Optional per-CSU end date truncation
    if end_date_overrides:
        for csu, end in end_date_overrides.items():
            mask = (df['csu'] == csu) & (df['date'] > pd.Timestamp(end))
            n = mask.sum()
            if n:
                df = df[~mask]
                print(f'  Truncated {csu}: dropped {n} obs after {end}')

    # Optional CSU exclusions
    if drop_csus:
        for csu in drop_csus:
            n = (df['csu'] == csu).sum()
            if n:
                df = df[df['csu'] != csu]
                print(f'  Dropped {csu} ({n} obs)')

    # Keep only needed columns (preserve denomination if present)
    keep = ['date', 'csu'] + [v for v in variable_order if v in df.columns]
    if 'denomination' in df.columns:
        keep.append('denomination')
    # liquidation is needed by the eligibility filter below, even if not in the VAR
    if 'liquidation' in df.columns and 'liquidation' not in keep:
        keep.append('liquidation')
    df = df[keep].dropna(subset=variable_order).copy()

    # Eligible CSUs
    eligible = []
    for csu, g in df.groupby('csu'):
        if (g['liquidation'] > 0).sum() >= min_liq_days:
            eligible.append(csu)
    eligible = sorted(eligible)

    print(f'\nPanel: {df["csu"].nunique()} CSUs total, {len(eligible)} eligible '
          f'(>= {min_liq_days} liq days), {len(df):,} obs')

    # Per-member sigmas — mirrors panelSVAR.py z-scoring logic
    sigmas = {}
    csu_df = df[df['csu'].isin(eligible)]
    for var in variable_order:
        integration_order = variables_dict[var][0]
        if integration_order == 1:
            # I(1): sigma = std of log-differences (panelSVAR log-diffs before z-score)
            s = (csu_df.groupby('csu')[var]
                 .transform(lambda x: np.log(x) - np.log(x).shift(1))
                 .groupby(csu_df['csu']).std())
        else:
            s = csu_df.groupby('csu')[var].std()
        sigmas[var] = s
        print(f'  sigma_{var}: median={s.median():.4f}')

    return df, eligible, sigmas


# ─────────────────────────────────────────────────────────────────────────────
# 3. PANEL SVAR RUNNER
# ─────────────────────────────────────────────────────────────────────────────

def run_panel(
    label: str,
    df: pd.DataFrame,
    csus: List[str],
    variable_order: List[str],
    variables_dict: dict,
    shocks: List[str],
    sr_constraint: np.ndarray,
    lr_constraint: np.ndarray,
    sr_sign: np.ndarray,
    lr_sign: np.ndarray,
    maxlags: int = 5,
    nsteps: int = 20,
    lagmethod: str = 'aic',
) -> dict:
    """
    Run Pedroni (2013) Panel SVAR for the given CSU subset.

    Returns
    -------
    member_irfs : dict
        {csu: {'composite', 'common', 'idiosyncratic': ndarray (nsteps+1, n, n),
               'lambda': ndarray (n, n)}}
    """
    from SVAR import VAR_input
    from panelSVAR import panelSVAR

    n = len(variable_order)
    subset = df[df['csu'].isin(csus)].copy()
    print(f'\n{label}  (N={len(csus)} CSUs, {len(subset):,} obs)')

    var_input = VAR_input(
        variables=copy.deepcopy(variables_dict),
        variable_order=variable_order,
        shocks=shocks,
        td_col=['date'],
        member_col='csu',
        M=None,
        sr_constraint=sr_constraint.copy() if sr_constraint.size > 0 else sr_constraint,
        lr_constraint=lr_constraint.copy() if lr_constraint.size > 0 else lr_constraint,
        sr_sign=sr_sign.copy() if sr_sign.size > 0 else sr_sign,
        lr_sign=lr_sign.copy() if lr_sign.size > 0 else lr_sign,
        maxlags=maxlags,
        nsteps=nsteps,
        lagmethod=lagmethod,
        bootstrap=False,
        ndraws=0,
        plot=False,
        df=subset,
    )

    panel_out = panelSVAR(var_input)
    member_irfs = _parse_panel_output(panel_out, nsteps, n, variable_order)
    print(f'  Converged: {len(member_irfs)} / {len(csus)}')
    return member_irfs


def _parse_panel_output(panel_out, nsteps: int, n: int, variable_order: List[str]) -> dict:
    """Unpack panelSVAR Panel_output into a per-member dict."""
    member_irfs = {}
    for member in panel_out.comp_df.index:
        row = panel_out.comp_df.loc[member]
        if row.isna().any():
            continue

        def _unpack(df_row):
            arr = np.zeros((nsteps + 1, n, n))
            for vr in range(n):
                for sk in range(n):
                    for lg in range(nsteps + 1):
                        key = f'IR{vr+1}{sk+1}_{lg}'
                        arr[lg, vr, sk] = float(df_row[key])
            return arr

        lam_vals = panel_out.lambda_df.loc[member].values.astype(float)
        member_irfs[member] = {
            'composite':     _unpack(panel_out.comp_df.loc[member]),
            'common':        _unpack(panel_out.comm_df.loc[member]),
            'idiosyncratic': _unpack(panel_out.idio_df.loc[member]),
            'lambda':        lam_vals.reshape(n, n),
        }
    return member_irfs


# ─────────────────────────────────────────────────────────────────────────────
# 4. IRF TRANSFORMATIONS
# ─────────────────────────────────────────────────────────────────────────────

def undo_zscore(
    member_irfs: dict,
    sigmas: Dict[str, pd.Series],
    variable_order: List[str],
) -> dict:
    """
    Multiply each variable row of every IRF by its per-member sigma,
    reversing the z-scoring applied inside panelSVAR.py.
    """
    out = copy.deepcopy(member_irfs)
    for member in out:
        for var_idx, var in enumerate(variable_order):
            s = sigmas[var].get(member, sigmas[var].median())
            for key in ('composite', 'common', 'idiosyncratic'):
                out[member][key][:, var_idx, :] *= s
    return out


def normalize_shock(
    member_irfs: dict,
    shock_idx: int,
    var_idx: int,
    target: float,
    horizon: int,
) -> Tuple[dict, float]:
    """
    Rescale shock column `shock_idx` so that the median response of
    variable `var_idx` at `horizon` equals `target` (in current IRF units).

    E.g. normalize_shock(irfs, shock_idx=0, var_idx=0, target=-0.01, horizon=0)
    sets the median basket_return response to the market shock at h=0 to -1%.

    Returns (rescaled_irfs, scale_factor).
    """
    stacked = np.stack([member_irfs[m]['composite'] for m in member_irfs])
    median_val = np.median(stacked[:, horizon, var_idx, shock_idx])

    if abs(median_val) < 1e-12:
        print(f'WARNING: normalization target near zero at h={horizon} — skipping')
        return member_irfs, 1.0

    scale = target / median_val
    print(f'  Normalize shock {shock_idx}: median h={horizon} response = {median_val:.5f} '
          f'→ {target:.5f}  (scale = {scale:.3f}x)')

    out = copy.deepcopy(member_irfs)
    for member in out:
        for key in ('composite', 'common', 'idiosyncratic'):
            out[member][key][:, :, shock_idx] *= scale
    return out, scale


def normalize_shock_per_type(
    member_irfs: dict,
    shock_idx: int,
    var_idx: int,
    target: float,
    horizon: int,
) -> Tuple[dict, Dict[str, float]]:
    """
    Like `normalize_shock`, but compute a separate scale factor per IRF type
    (composite / common / idiosyncratic) and apply each scale only to its
    own type.  After this call, the median response at `(horizon, var_idx,
    shock_idx)` equals `target` independently in each of the three types.

    Use case: when each panel (common, idio) should hit the same h=0 reference
    so the panels can be read on a common scale.  In contrast, `normalize_shock`
    preserves the relative magnitude between common and idio by applying a
    single composite-derived scale to all three.

    Returns (rescaled_irfs, {type: scale}).
    """
    out = copy.deepcopy(member_irfs)
    scales = {}
    for key in ('composite', 'common', 'idiosyncratic'):
        stacked = np.stack([out[m][key] for m in out])
        median_val = float(np.median(stacked[:, horizon, var_idx, shock_idx]))
        if abs(median_val) < 1e-12:
            print(f'  [{key}] median at h={horizon} near zero — skipping')
            scales[key] = 1.0
            continue
        scale = target / median_val
        print(f'  Normalize shock {shock_idx} [{key}]: median h={horizon} response = {median_val:+.5f} '
              f'→ {target:+.5f}  (scale = {scale:+.3f}x)')
        for m in out:
            out[m][key][:, :, shock_idx] *= scale
        scales[key] = scale
    return out, scales


# ─────────────────────────────────────────────────────────────────────────────
# 5. AGGREGATION HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def median_irf(member_irfs: dict, irf_type: str = 'composite') -> Optional[np.ndarray]:
    vals = [member_irfs[m][irf_type] for m in member_irfs]
    return np.median(np.stack(vals), axis=0) if vals else None


def iqr_irf(member_irfs: dict, irf_type: str = 'composite') -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    vals = [member_irfs[m][irf_type] for m in member_irfs]
    if not vals:
        return None, None
    s = np.stack(vals)
    return np.percentile(s, 25, axis=0), np.percentile(s, 75, axis=0)


def compute_fevd(member_irfs: dict, irf_type: str = 'composite') -> dict:
    """
    Forecast Error Variance Decomposition from structural IRFs.
    fevd[member][h, var, shock] = share of var's FEV at horizon h from shock.
    """
    out = {}
    for member, data in member_irfs.items():
        ir = data[irf_type]
        cum_sq = (ir ** 2).cumsum(axis=0)
        total = cum_sq.sum(axis=2, keepdims=True)
        out[member] = cum_sq / np.where(total > 1e-12, total, 1.0)
    return out


def lambda_summary(member_irfs: dict, variable_order: List[str]) -> pd.DataFrame:
    """Return a DataFrame of diagonal Lambda values (one row per CSU)."""
    rows = []
    for member in sorted(member_irfs):
        lam = member_irfs[member]['lambda']
        row = {'csu': member}
        for i, var in enumerate(variable_order):
            row[f'lambda_{var}'] = lam[i, i]
        rows.append(row)
    df = pd.DataFrame(rows).set_index('csu')
    print(df.to_string())
    print()
    print('Medians:')
    for col in df.columns:
        print(f'  {col}: {df[col].median():.4f}')
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 6. PLOTTING
# ─────────────────────────────────────────────────────────────────────────────

def _display(var: str, values: np.ndarray) -> np.ndarray:
    """Apply the registered display transform for a variable."""
    transform = VAR_DISPLAY.get(var, {}).get('transform', lambda x: x)
    return transform(values)


def _label(var: str) -> str:
    return VAR_DISPLAY.get(var, {}).get('label', var)


def plot_irfs_grid(
    member_irfs: dict,
    variable_order: List[str],
    shock_names: List[str],
    title: str,
    irf_type: str = 'composite',
    nsteps: int = 20,
    show_members: bool = True,
    save_path: Optional[Path] = None,
) -> None:
    """
    Plot an N×N grid of IRFs (rows = variables, columns = shocks).
    Display transforms and y-axis labels come from VAR_DISPLAY.
    Shaded band = IQR across members. Gray lines = individual members.

    nsteps controls the x-axis length. Can be smaller than NSTEPS used
    during estimation — set PLOT_STEPS in the notebook config to zoom in.
    """
    n = len(variable_order)
    # Clip to actual IRF array length so PLOT_STEPS can be < NSTEPS safely
    max_steps = next(iter(member_irfs.values()))[irf_type].shape[0] - 1
    nsteps = min(nsteps, max_steps)
    horizons = np.arange(nsteps + 1)
    med = median_irf(member_irfs, irf_type)
    lo, hi = iqr_irf(member_irfs, irf_type)

    fig, axes = plt.subplots(n, n, figsize=(4.5 * n, 3.5 * n))
    if n == 1:
        axes = np.array([[axes]])
    elif n > 1 and axes.ndim == 1:
        axes = axes.reshape(n, n)

    fig.suptitle(title, fontsize=13, fontweight='bold', y=1.01)

    for vr, var in enumerate(variable_order):
        for sk, shock in enumerate(shock_names):
            ax = axes[vr, sk]

            if show_members:
                for m in member_irfs:
                    y = _display(var, member_irfs[m][irf_type][:nsteps+1, vr, sk])
                    ax.plot(horizons, y, color='lightgray', lw=0.6, alpha=0.6, zorder=1)

            ax.fill_between(horizons,
                            _display(var, lo[:nsteps+1, vr, sk]),
                            _display(var, hi[:nsteps+1, vr, sk]),
                            alpha=0.25, color='steelblue', zorder=2)
            ax.plot(horizons, _display(var, med[:nsteps+1, vr, sk]),
                    color='steelblue', lw=2.2, zorder=3)
            ax.axhline(0, color='black', lw=0.8, ls='--')

            ax.set_title(f'{shock}  →  {var}', fontsize=10, fontweight='bold')
            if sk == 0:
                ax.set_ylabel(_label(var), fontsize=9)
            if vr == n - 1:
                ax.set_xlabel('Horizon (days)', fontsize=9)
            ax.tick_params(labelsize=8)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f'  Saved: {save_path}')
    plt.show()
    plt.close()


def plot_fevd_grid(
    member_fevds: dict,
    variable_order: List[str],
    shock_names: List[str],
    title: str,
    nsteps: int = 20,
    save_path: Optional[Path] = None,
) -> None:
    """
    Stacked-area FEVD plot for each variable.
    One subplot per variable; each subplot shows the shock shares stacked.
    """
    n_vars = len(variable_order)
    stacked = np.stack(list(member_fevds.values()))  # (N, T, n, n)
    med_fevd = np.median(stacked, axis=0)
    horizons = np.arange(nsteps + 1)
    colors = plt.cm.tab10(np.linspace(0, 0.6, len(shock_names)))

    fig, axes = plt.subplots(1, n_vars, figsize=(5 * n_vars, 4), sharey=True)
    if n_vars == 1:
        axes = [axes]
    fig.suptitle(title, fontsize=12, fontweight='bold')

    for vr, var in enumerate(variable_order):
        ax = axes[vr]
        bottom = np.zeros(nsteps + 1)
        for sk, (shock, color) in enumerate(zip(shock_names, colors)):
            share = med_fevd[:nsteps+1, vr, sk]
            ax.fill_between(horizons, bottom, bottom + share,
                            alpha=0.85, color=color, label=shock)
            bottom += share
        ax.set_xlim(0, nsteps)
        ax.set_ylim(0, 1)
        ax.set_title(_label(var), fontsize=10)
        ax.set_xlabel('Horizon (days)')
        if vr == 0:
            ax.set_ylabel('Fraction of variance')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

    axes[-1].legend(fontsize=9, loc='lower right')
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f'  Saved: {save_path}')
    plt.show()
    plt.close()


def plot_shock_comparison(
    irfs_dict: Dict[str, dict],
    shock_idx: int,
    var_idx: int,
    variable_order: List[str],
    title: str,
    irf_type: str = 'composite',
    nsteps: int = 20,
    save_path: Optional[Path] = None,
) -> None:
    """
    Overlay median IRFs for one shock × one variable across multiple subpanels.

    Parameters
    ----------
    irfs_dict : dict
        {label: member_irfs} — e.g. {'Stablecoin': stable_irfs, 'Volatile': vol_irfs}
    shock_idx, var_idx : int
        Which shock and variable to plot.
    """
    var = variable_order[var_idx]
    horizons = np.arange(nsteps + 1)
    colors = plt.cm.tab10(np.linspace(0, 0.7, len(irfs_dict)))

    fig, ax = plt.subplots(figsize=(8, 4))
    fig.suptitle(title, fontsize=12, fontweight='bold')

    for (label, irfs), color in zip(irfs_dict.items(), colors):
        med = median_irf(irfs, irf_type)
        if med is None:
            continue
        lo, hi = iqr_irf(irfs, irf_type)
        y = _display(var, med[:nsteps+1, var_idx, shock_idx])
        ax.plot(horizons, y, color=color, lw=2.5, label=f'{label} (N={len(irfs)})')
        ax.fill_between(horizons,
                        _display(var, lo[:nsteps+1, var_idx, shock_idx]),
                        _display(var, hi[:nsteps+1, var_idx, shock_idx]),
                        color=color, alpha=0.12)

    ax.axhline(0, color='black', lw=0.8, ls='--')
    ax.set_xlabel('Horizon (days)')
    ax.set_ylabel(_label(var))
    ax.legend(fontsize=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f'  Saved: {save_path}')
    plt.show()
    plt.close()


# ─────────────────────────────────────────────────────────────────────────────
# 7. SAVING RESULTS
# ─────────────────────────────────────────────────────────────────────────────

def save_results(
    member_irfs: dict,
    variable_order: List[str],
    shock_names: List[str],
    output_dir: Path,
    prefix: str = '',
) -> None:
    """
    Save IRFs (composite/common/idiosyncratic), lambda, and FEVD to CSV.
    All files are written to output_dir with optional prefix.
    """
    n = len(variable_order)

    # IRF CSVs
    for irf_type in ('composite', 'common', 'idiosyncratic'):
        rows = []
        for member, data in member_irfs.items():
            ir = data[irf_type]
            T = ir.shape[0]
            for vr, var in enumerate(variable_order):
                for sk, shock in enumerate(shock_names):
                    for h in range(T):
                        rows.append({
                            'csu': member, 'variable': var, 'shock': shock,
                            'horizon': h, 'irf': ir[h, vr, sk],
                        })
        fname = f'{prefix}irfs_{irf_type}.csv'
        pd.DataFrame(rows).to_csv(output_dir / fname, index=False)
        print(f'  Saved: {fname}')

    # Lambda CSV
    lam_rows = []
    for member, data in member_irfs.items():
        lam = data['lambda']
        row = {'csu': member}
        for i in range(n):
            for j in range(n):
                row[f'lam_{variable_order[i]}_{variable_order[j]}'] = lam[i, j]
        lam_rows.append(row)
    fname = f'{prefix}lambda.csv'
    pd.DataFrame(lam_rows).to_csv(output_dir / fname, index=False)
    print(f'  Saved: {fname}')

    # FEVD CSV
    fevd = compute_fevd(member_irfs)
    fevd_rows = []
    for member, fv in fevd.items():
        T = fv.shape[0]
        for vr, var in enumerate(variable_order):
            for sk, shock in enumerate(shock_names):
                for h in range(T):
                    fevd_rows.append({
                        'csu': member, 'variable': var, 'shock': shock,
                        'horizon': h, 'fevd_share': fv[h, vr, sk],
                    })
    fname = f'{prefix}fevd.csv'
    pd.DataFrame(fevd_rows).to_csv(output_dir / fname, index=False)
    print(f'  Saved: {fname}')

    print(f'\nAll results saved to: {output_dir}')


print('svar_nb loaded.')
