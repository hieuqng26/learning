"""
GMM-Based Currency Denomination Correction
============================================
Detects and corrects revenue values reported in non-USD currencies
using Gaussian Mixture Models in log10 space, per spread ID group.

Method:
    For each spread_id group, fit a GMM on log10(revenue). The dominant
    component (highest mixing weight π_k) is treated as the USD cluster.
    Minority-component observations are corrected by dividing by the
    estimated FX factor: 10^(μ_k - μ_k*).

References:
    - Dempster, Laird & Rubin (1977). Maximum likelihood from incomplete
      data via the EM algorithm. JRSS-B, 39(1), 1–38.
    - McLachlan & Peel (2000). Finite Mixture Models. Wiley.
    - Hampel et al. (1986). Robust Statistics: The Approach Based on
      Influence Functions. Wiley.
"""

import warnings
import numpy as np
import pandas as pd
from sklearn.mixture import GaussianMixture
from sklearn.exceptions import ConvergenceWarning
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec


# ---------------------------------------------------------------------------
# Known FX rates (local currency units per 1 USD)
# Extend this dict with your relevant currencies / reference date
# ---------------------------------------------------------------------------
KNOWN_FX_RATES: dict[str, float] = {
    "VND": 25_000,
    "KRW":  1_350,
    "JPY":    150,
    "INR":     83,
    "IDR": 15_500,
    "MYR":      4.7,
    "THB":     35,
    "PHP":     56,
    "CNY":      7.2,
    "HKD":      7.8,
    "TWD":     32,
    "PKR":    280,
    "BDT":    110,
    "EUR":      0.92,
    "GBP":      0.79,
    "AUD":      1.53,
    "CAD":      1.36,
    "BRL":      5.0,
    "MXN":     17,
    "COP":  4_000,
    "CLP":    900,
    "ARS":    350,
    "NGN":    800,
    "EGP":     31,
    "ZAR":     19,
}


# ---------------------------------------------------------------------------
# Core GMM correction
# ---------------------------------------------------------------------------

def _select_n_components(
    log_vals: np.ndarray,
    max_k: int = 4,
    criterion: str = "bic",
) -> int:
    """
    Use BIC (or AIC) to select the optimal number of GMM components.

    BIC penalises complexity more strongly than AIC, which is preferred
    here to avoid over-segmenting small groups.
    """
    best_score = np.inf
    best_k = 1
    for k in range(1, min(max_k, len(log_vals)) + 1):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", ConvergenceWarning)
                gm = GaussianMixture(
                    n_components=k,
                    covariance_type="full",
                    n_init=5,
                    random_state=42,
                )
                gm.fit(log_vals.reshape(-1, 1))
            score = gm.bic(log_vals.reshape(-1, 1)) if criterion == "bic" \
                    else gm.aic(log_vals.reshape(-1, 1))
            if score < best_score:
                best_score = score
                best_k = k
        except Exception:
            break
    return best_k


def _match_fx(estimated_log_fx: float, tolerance: float = 0.15) -> tuple[str | None, float | None]:
    """
    Match an estimated log10(FX) to the nearest known FX rate.

    Parameters
    ----------
    estimated_log_fx : float
        log10 of the estimated FX factor.
    tolerance : float
        Maximum allowed |log10(estimated) - log10(known)| to accept a match.
        Default 0.15 ≈ 40% relative error in FX space.

    Returns
    -------
    (currency_code, fx_rate) or (None, None) if no match found.
    """
    best_currency = None
    best_fx = None
    best_dist = np.inf

    for currency, fx in KNOWN_FX_RATES.items():
        dist = abs(estimated_log_fx - np.log10(fx))
        if dist < best_dist:
            best_dist = dist
            best_currency = currency
            best_fx = fx

    if best_dist <= tolerance:
        return best_currency, best_fx
    return None, None


def correct_group(
    group: pd.DataFrame,
    revenue_col: str = "revenue",
    max_k: int = 4,
    min_group_size: int = 5,
    fx_tolerance: float = 0.15,
) -> pd.DataFrame:
    """
    Apply GMM-based FX correction to a single spread_id group.

    Parameters
    ----------
    group : pd.DataFrame
        Rows belonging to one spread_id.
    revenue_col : str
        Column name for revenue values.
    max_k : int
        Maximum number of GMM components to consider.
    min_group_size : int
        Groups smaller than this use log-median fallback instead of GMM.
    fx_tolerance : float
        Passed to _match_fx for known-rate matching.

    Returns
    -------
    pd.DataFrame with added columns:
        corrected_revenue, fx_factor, matched_currency, correction_method,
        gmm_component, component_is_dominant
    """
    out = group.copy()
    revenues = group[revenue_col].values.astype(float)

    # Drop non-positive revenues from fitting (log undefined)
    valid_mask = revenues > 0
    log_vals = np.log10(revenues[valid_mask])

    # Initialise output columns
    out["corrected_revenue"]   = out[revenue_col]
    out["fx_factor"]           = 1.0
    out["matched_currency"]    = None
    out["correction_method"]   = "none"
    out["gmm_component"]       = -1
    out["component_is_dominant"] = True

    if valid_mask.sum() < 2:
        out["correction_method"] = "insufficient_data"
        return out

    # --- Small-group fallback: log-median pull ---
    if valid_mask.sum() < min_group_size:
        log_median = np.median(log_vals)
        fx_factors = 10 ** (log_median - np.log10(revenues))
        valid_idx = group.index[valid_mask]
        out.loc[valid_idx, "fx_factor"] = fx_factors[valid_mask]
        out.loc[valid_idx, "corrected_revenue"] = revenues[valid_mask] * fx_factors[valid_mask]
        out.loc[valid_idx, "correction_method"] = "log_median_fallback"
        return out

    # --- GMM path ---
    n_components = _select_n_components(log_vals, max_k=max_k)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        gm = GaussianMixture(
            n_components=n_components,
            covariance_type="full",
            n_init=10,
            random_state=42,
        )
        gm.fit(log_vals.reshape(-1, 1))

    labels     = gm.predict(log_vals.reshape(-1, 1))
    means      = gm.means_.flatten()          # μ_k for each component
    weights    = gm.weights_.flatten()        # π_k for each component

    # Dominant component = highest mixing weight = USD cluster
    dominant_k = int(np.argmax(weights))
    mu_dominant = means[dominant_k]

    valid_idx = group.index[valid_mask]

    for k in range(n_components):
        mask_k = labels == k
        idx_k  = valid_idx[mask_k]

        out.loc[idx_k, "gmm_component"]       = k
        out.loc[idx_k, "component_is_dominant"] = (k == dominant_k)

        if k == dominant_k:
            # No correction needed for dominant (USD) cluster
            out.loc[idx_k, "correction_method"] = "dominant_cluster_no_change"
            continue

        # Estimated FX factor for this minority component
        log_fx_est = means[k] - mu_dominant          # log10(FX)
        fx_est     = 10 ** log_fx_est

        # Try to match to a known currency
        matched_ccy, matched_fx = _match_fx(log_fx_est, fx_tolerance)

        if matched_fx is not None:
            fx_used   = matched_fx
            method    = f"gmm_fx_matched_{matched_ccy}"
        else:
            fx_used   = fx_est
            method    = "gmm_fx_estimated"

        out.loc[idx_k, "fx_factor"]         = fx_used
        out.loc[idx_k, "matched_currency"]  = matched_ccy
        out.loc[idx_k, "correction_method"] = method
        out.loc[idx_k, "corrected_revenue"] = (
            out.loc[idx_k, revenue_col] / fx_used
        )

    return out


def correct_denominations(
    df: pd.DataFrame,
    spread_id_col: str = "spread_id",
    revenue_col: str   = "revenue",
    max_k: int         = 4,
    min_group_size: int = 5,
    fx_tolerance: float = 0.15,
    verbose: bool       = True,
) -> pd.DataFrame:
    """
    Apply GMM currency-denomination correction across all spread_id groups.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    spread_id_col : str
        Column identifying the spread/company group.
    revenue_col : str
        Column with raw revenue values (in possibly mixed currencies).
    max_k : int
        Max GMM components. Default 4 covers up to 4 distinct currencies
        per group.
    min_group_size : int
        Groups below this size fall back to log-median correction.
    fx_tolerance : float
        log10 tolerance for matching estimated FX to known rates.
    verbose : bool
        Print a summary of corrections applied.

    Returns
    -------
    pd.DataFrame with correction columns added.
    """
    result_parts = []
    for gid, group in df.groupby(spread_id_col):
        corrected = correct_group(
            group,
            revenue_col    = revenue_col,
            max_k          = max_k,
            min_group_size = min_group_size,
            fx_tolerance   = fx_tolerance,
        )
        result_parts.append(corrected)
    result = pd.concat(result_parts, ignore_index=True)

    if verbose:
        _print_summary(result)

    return result


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------

def _print_summary(df: pd.DataFrame) -> None:
    total       = len(df)
    corrected   = (df["correction_method"] != "dominant_cluster_no_change").sum()
    method_cts  = df["correction_method"].value_counts()

    print("\n" + "=" * 55)
    print("  GMM Currency Correction Summary")
    print("=" * 55)
    print(f"  Total rows         : {total:,}")
    print(f"  Rows corrected     : {corrected:,}  ({100*corrected/total:.1f}%)")
    print("\n  By method:")
    for method, count in method_cts.items():
        print(f"    {method:<40s} {count:>6,}")
    print("=" * 55 + "\n")


def plot_correction_diagnostics(
    df: pd.DataFrame,
    spread_id_col: str = "spread_id",
    revenue_col: str   = "revenue",
    n_groups: int      = 6,
    figsize: tuple     = (16, 10),
) -> plt.Figure:
    """
    Plot before/after log10(revenue) distributions for a sample of groups.
    """
    group_ids = df[spread_id_col].unique()[:n_groups]
    n_cols = 3
    n_rows = int(np.ceil(len(group_ids) / n_cols))

    fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
    axes = axes.flatten()

    for ax, gid in zip(axes, group_ids):
        sub = df[df[spread_id_col] == gid]
        valid = sub[sub[revenue_col] > 0]

        log_before = np.log10(valid[revenue_col])
        log_after  = np.log10(valid["corrected_revenue"].clip(lower=1e-6))

        bins = np.linspace(
            min(log_before.min(), log_after.min()),
            max(log_before.max(), log_after.max()),
            30,
        )

        ax.hist(log_before, bins=bins, alpha=0.5, label="Before", color="tomato")
        ax.hist(log_after,  bins=bins, alpha=0.5, label="After",  color="steelblue")
        ax.set_title(f"Spread ID: {gid}\n(n={len(sub)})", fontsize=9)
        ax.set_xlabel("log₁₀(Revenue)")
        ax.set_ylabel("Count")
        ax.legend(fontsize=7)

    for ax in axes[len(group_ids):]:
        ax.set_visible(False)

    fig.suptitle("GMM Denomination Correction: Before vs After", fontsize=13, y=1.01)
    plt.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Synthetic demo
# ---------------------------------------------------------------------------

def _make_synthetic_data(seed: int = 42) -> pd.DataFrame:
    """
    Generate a synthetic dataset mixing USD and VND revenues in the same
    spread_id groups, to validate the GMM correction.
    """
    rng = np.random.default_rng(seed)
    rows = []

    for spread_id in range(1, 16):           # 15 spread groups
        n_usd = rng.integers(30, 60)
        n_vnd = rng.integers(5, 15)          # minority currency

        # USD revenues: log-normal centred around $50k
        usd_revs = rng.lognormal(mean=np.log(50_000), sigma=0.6, size=n_usd)
        for r in usd_revs:
            rows.append({"spread_id": spread_id, "revenue": r, "true_currency": "USD"})

        # VND revenues: same USD value × 25,000
        vnd_revs = usd_revs[:n_vnd] * 25_000 * rng.lognormal(0, 0.05, size=n_vnd)
        for r in vnd_revs:
            rows.append({"spread_id": spread_id, "revenue": r, "true_currency": "VND"})

    df = pd.DataFrame(rows).sample(frac=1, random_state=seed).reset_index(drop=True)
    return df


if __name__ == "__main__":
    # ------------------------------------------------------------------ #
    #  Demo on synthetic data                                             #
    # ------------------------------------------------------------------ #
    print("Generating synthetic data...")
    df_raw = _make_synthetic_data()

    print(f"Dataset: {len(df_raw):,} rows, {df_raw['spread_id'].nunique()} spread IDs")
    print(f"  USD rows : {(df_raw['true_currency']=='USD').sum()}")
    print(f"  VND rows : {(df_raw['true_currency']=='VND').sum()}")

    # Run correction
    df_corrected = correct_denominations(
        df_raw,
        spread_id_col = "spread_id",
        revenue_col   = "revenue",
        max_k         = 3,
        min_group_size= 5,
        fx_tolerance  = 0.15,
        verbose       = True,
    )

    # ------------------------------------------------------------------ #
    #  Evaluate: for VND rows, corrected_revenue should ≈ original USD   #
    # ------------------------------------------------------------------ #
    vnd_rows = df_corrected[df_corrected["true_currency"] == "VND"].copy()
    vnd_rows["error_pct"] = (
        (vnd_rows["corrected_revenue"] - vnd_rows["revenue"] / 25_000)
        / (vnd_rows["revenue"] / 25_000)
        * 100
    )

    print("\nVND correction accuracy:")
    print(f"  Median abs error : {vnd_rows['error_pct'].abs().median():.2f}%")
    print(f"  Max abs error    : {vnd_rows['error_pct'].abs().max():.2f}%")
    print(f"  Rows with matched_currency='VND' : "
          f"{(vnd_rows['matched_currency']=='VND').sum()} / {len(vnd_rows)}")

    # ------------------------------------------------------------------ #
    #  Plot                                                               #
    # ------------------------------------------------------------------ #
    fig = plot_correction_diagnostics(
        df_corrected,
        spread_id_col = "spread_id",
        revenue_col   = "revenue",
        n_groups      = 6,
    )
    fig.savefig("/mnt/user-data/outputs/gmm_correction_diagnostics.png",
                dpi=150, bbox_inches="tight")
    print("\nDiagnostic plot saved to gmm_correction_diagnostics.png")

    # ------------------------------------------------------------------ #
    #  Show sample output                                                  #
    # ------------------------------------------------------------------ #
    cols = ["spread_id", "revenue", "corrected_revenue",
            "fx_factor", "matched_currency", "correction_method", "true_currency"]
    print("\nSample corrected rows (VND):")
    print(df_corrected[df_corrected["true_currency"] == "VND"][cols].head(10).to_string(index=False))
