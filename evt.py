"""
OPEX EVT Analysis Script
========================
This script performs Operating Expense (OPEX) analysis using Extreme Value Theory (EVT)
instead of empirical distribution methods. It maintains the same data preparation and
cleaning pipeline as opex.py but applies GPD (Generalized Pareto Distribution) for
tail risk modeling.

Key Features:
- Panel data EVT modeling
- Backtesting with 2008-2009 financial crisis data
- Performance metrics: MAE, RMSE, Coverage, Exception Rate
- Comprehensive diagnostic plots
"""

from log_file import TimestampLog
import sys
from Opex_config import *
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import warnings
from io import BytesIO
from openpyxl import load_workbook
from openpyxl.drawing.image import Image
from sklearn.metrics import mean_absolute_error, mean_squared_error
from scipy.stats import genpareto
from scipy.optimize import minimize

warnings.filterwarnings("ignore")


# ==================================================================================
# THRESHOLD SELECTION TOOLS
# ==================================================================================

class ThresholdSelector:
    """
    Comprehensive threshold selection toolkit for EVT.

    Implements multiple diagnostic methods:
    1. Mean Residual Life (MRL) Plot
    2. Parameter Stability Plot
    3. Goodness-of-Fit across thresholds
    4. Automated selection algorithm
    """

    def __init__(self, data, value_col='delta_opex/rev'):
        """
        Initialize threshold selector.

        Parameters:
        -----------
        data : pd.Series or pd.DataFrame
            Data to analyze (if DataFrame, specify value_col)
        value_col : str
            Column name if data is DataFrame
        """
        if isinstance(data, pd.DataFrame):
            self.data = data[value_col].dropna().values
        else:
            self.data = data.dropna().values

        self.n = len(self.data)

    def mean_residual_life(self, thresholds=None, n_thresholds=50):
        """
        Calculate Mean Residual Life (MRL) for threshold selection.

        The MRL plot shows the average excess over threshold vs the threshold.
        For GPD, this should be approximately linear above the optimal threshold.

        Parameters:
        -----------
        thresholds : array-like, optional
            Specific thresholds to test
        n_thresholds : int
            Number of thresholds to test (if thresholds not specified)

        Returns:
        --------
        pd.DataFrame : Threshold, MRL, confidence bounds
        """
        if thresholds is None:
            # Use quantiles from 75th to 99th percentile
            percentiles = np.linspace(75, 99, n_thresholds)
            thresholds = np.percentile(self.data, percentiles)

        results = []

        for u in thresholds:
            excesses = self.data[self.data > u] - u

            if len(excesses) < 10:  # Need minimum excesses
                continue

            mrl = excesses.mean()
            std_err = excesses.std() / np.sqrt(len(excesses))

            # 95% confidence interval
            lower_ci = mrl - 1.96 * std_err
            upper_ci = mrl + 1.96 * std_err

            results.append({
                'threshold': u,
                'n_exceedances': len(excesses),
                'mrl': mrl,
                'std_err': std_err,
                'lower_ci': lower_ci,
                'upper_ci': upper_ci
            })

        return pd.DataFrame(results)

    def parameter_stability(self, thresholds=None, n_thresholds=50):
        """
        Assess parameter stability across thresholds.

        Good threshold shows stable shape (xi) and modified scale parameters.
        Modified scale = sigma - xi * u should be constant above optimal threshold.

        Parameters:
        -----------
        thresholds : array-like, optional
            Specific thresholds to test
        n_thresholds : int
            Number of thresholds to test

        Returns:
        --------
        pd.DataFrame : Threshold, xi, sigma, modified_scale, n_exceedances
        """
        if thresholds is None:
            percentiles = np.linspace(75, 99, n_thresholds)
            thresholds = np.percentile(self.data, percentiles)

        results = []

        for u in thresholds:
            excesses = self.data[self.data > u] - u

            if len(excesses) < 20:  # Need reasonable sample
                continue

            try:
                # Fit GPD
                xi, loc, sigma = genpareto.fit(excesses, floc=0)

                # Modified scale parameter
                modified_scale = sigma - xi * u

                # Standard errors (approximate)
                n_exc = len(excesses)
                xi_se = np.sqrt((1 + xi)**2 / n_exc)
                sigma_se = sigma * np.sqrt((1 + 2*xi) / n_exc)

                results.append({
                    'threshold': u,
                    'threshold_percentile': (self.data <= u).mean() * 100,
                    'n_exceedances': n_exc,
                    'xi': xi,
                    'sigma': sigma,
                    'modified_scale': modified_scale,
                    'xi_se': xi_se,
                    'sigma_se': sigma_se,
                    'xi_lower_ci': xi - 1.96 * xi_se,
                    'xi_upper_ci': xi + 1.96 * xi_se
                })

            except Exception as e:
                # Fitting failed for this threshold
                continue

        return pd.DataFrame(results)

    def goodness_of_fit_scores(self, thresholds=None, n_thresholds=30):
        """
        Calculate goodness-of-fit scores across thresholds.

        Uses Anderson-Darling statistic and KS statistic to assess fit quality.
        Lower values indicate better fit.

        Parameters:
        -----------
        thresholds : array-like, optional
            Specific thresholds to test
        n_thresholds : int
            Number of thresholds to test

        Returns:
        --------
        pd.DataFrame : Threshold, KS statistic, AD statistic, p-values
        """
        from scipy.stats import kstest, anderson

        if thresholds is None:
            percentiles = np.linspace(80, 98, n_thresholds)
            thresholds = np.percentile(self.data, percentiles)

        results = []

        for u in thresholds:
            excesses = self.data[self.data > u] - u

            if len(excesses) < 25:
                continue

            try:
                # Fit GPD
                xi, loc, sigma = genpareto.fit(excesses, floc=0)

                # Kolmogorov-Smirnov test
                ks_stat, ks_pval = kstest(
                    excesses,
                    lambda x: genpareto.cdf(x, xi, loc=0, scale=sigma)
                )

                # Anderson-Darling test (for exponential, approximation)
                # Transform to standard exponential if xi ≈ 0
                if abs(xi) < 0.1:
                    transformed = excesses / sigma
                    ad_result = anderson(transformed, dist='expon')
                    ad_stat = ad_result.statistic
                else:
                    ad_stat = np.nan

                results.append({
                    'threshold': u,
                    'threshold_percentile': (self.data <= u).mean() * 100,
                    'n_exceedances': len(excesses),
                    'xi': xi,
                    'ks_statistic': ks_stat,
                    'ks_pvalue': ks_pval,
                    'ad_statistic': ad_stat,
                    'fit_quality': 'Good' if ks_pval > 0.05 else 'Poor'
                })

            except Exception as e:
                continue

        return pd.DataFrame(results)

    def automated_selection(self, min_exceedances=30, max_exceedances=200,
                          stability_weight=0.4, gof_weight=0.3, exceedance_weight=0.3):
        """
        Automated threshold selection using composite scoring.

        Combines multiple criteria:
        1. Parameter stability (low variance in xi)
        2. Goodness-of-fit (high p-value)
        3. Number of exceedances (balance bias-variance)

        Parameters:
        -----------
        min_exceedances : int
            Minimum exceedances required
        max_exceedances : int
            Maximum exceedances to consider (beyond this, bias increases)
        stability_weight : float
            Weight for stability criterion (0-1)
        gof_weight : float
            Weight for goodness-of-fit criterion (0-1)
        exceedance_weight : float
            Weight for exceedance count criterion (0-1)

        Returns:
        --------
        dict : Optimal threshold info including scores
        """
        # Get parameter stability
        param_df = self.parameter_stability(n_thresholds=60)

        if param_df.empty:
            return {
                'optimal_threshold': np.percentile(self.data, 95),
                'optimal_percentile': 95,
                'method': 'default (insufficient data)',
                'n_exceedances': (self.data > np.percentile(self.data, 95)).sum()
            }

        # Filter by exceedance count
        param_df = param_df[
            (param_df['n_exceedances'] >= min_exceedances) &
            (param_df['n_exceedances'] <= max_exceedances)
        ]

        if param_df.empty:
            # Relax constraints
            param_df = self.parameter_stability(n_thresholds=60)
            param_df = param_df[param_df['n_exceedances'] >= min_exceedances * 0.6]

        if param_df.empty:
            return {
                'optimal_threshold': np.percentile(self.data, 95),
                'optimal_percentile': 95,
                'method': 'default (constraints too strict)',
                'n_exceedances': (self.data > np.percentile(self.data, 95)).sum()
            }

        # Score 1: Parameter Stability (lower variance in xi is better)
        # Use rolling window to assess local stability
        window = min(5, len(param_df) // 3)
        param_df['xi_rolling_std'] = param_df['xi'].rolling(window=window, center=True).std()
        param_df['xi_rolling_std'] = param_df['xi_rolling_std'].fillna(param_df['xi_rolling_std'].mean())

        # Normalize (lower is better, so invert)
        max_std = param_df['xi_rolling_std'].max()
        if max_std > 0:
            param_df['stability_score'] = 1 - (param_df['xi_rolling_std'] / max_std)
        else:
            param_df['stability_score'] = 1.0

        # Score 2: Goodness-of-fit
        gof_df = self.goodness_of_fit_scores(
            thresholds=param_df['threshold'].values,
            n_thresholds=len(param_df)
        )

        if not gof_df.empty:
            # Merge GOF scores
            param_df = param_df.merge(
                gof_df[['threshold', 'ks_pvalue']],
                on='threshold',
                how='left'
            )

            # Normalize p-value (higher is better)
            param_df['ks_pvalue'] = param_df['ks_pvalue'].fillna(0.5)
            param_df['gof_score'] = param_df['ks_pvalue']
        else:
            param_df['gof_score'] = 0.5

        # Score 3: Exceedance count (prefer middle range)
        # Optimal is around 50-100 exceedances
        target_exceedances = 75
        param_df['exceedance_distance'] = np.abs(param_df['n_exceedances'] - target_exceedances)
        max_distance = param_df['exceedance_distance'].max()
        if max_distance > 0:
            param_df['exceedance_score'] = 1 - (param_df['exceedance_distance'] / max_distance)
        else:
            param_df['exceedance_score'] = 1.0

        # Composite score
        param_df['composite_score'] = (
            stability_weight * param_df['stability_score'] +
            gof_weight * param_df['gof_score'] +
            exceedance_weight * param_df['exceedance_score']
        )

        # Select optimal
        optimal_idx = param_df['composite_score'].idxmax()
        optimal_row = param_df.loc[optimal_idx]

        return {
            'optimal_threshold': optimal_row['threshold'],
            'optimal_percentile': optimal_row['threshold_percentile'],
            'n_exceedances': int(optimal_row['n_exceedances']),
            'xi': optimal_row['xi'],
            'sigma': optimal_row['sigma'],
            'stability_score': optimal_row['stability_score'],
            'gof_score': optimal_row.get('gof_score', np.nan),
            'exceedance_score': optimal_row['exceedance_score'],
            'composite_score': optimal_row['composite_score'],
            'method': 'automated_composite',
            'all_candidates': param_df[['threshold', 'threshold_percentile', 'n_exceedances',
                                       'xi', 'composite_score']].to_dict('records')
        }

    def plot_diagnostics(self, save_path=None, figsize=(16, 12)):
        """
        Create comprehensive threshold diagnostic plots.

        Generates 4 diagnostic plots:
        1. Mean Residual Life Plot
        2. Parameter Stability Plots (xi and modified scale)
        3. Goodness-of-Fit across thresholds
        4. Recommended threshold summary

        Parameters:
        -----------
        save_path : str, optional
            Path to save figure
        figsize : tuple
            Figure size

        Returns:
        --------
        matplotlib.figure.Figure
        """
        fig = plt.figure(figsize=figsize)
        gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

        # 1. Mean Residual Life Plot
        ax1 = fig.add_subplot(gs[0, :])
        mrl_df = self.mean_residual_life(n_thresholds=60)

        if not mrl_df.empty:
            ax1.plot(mrl_df['threshold'], mrl_df['mrl'], 'b-', linewidth=2, label='MRL')
            ax1.fill_between(
                mrl_df['threshold'],
                mrl_df['lower_ci'],
                mrl_df['upper_ci'],
                alpha=0.3,
                color='blue',
                label='95% CI'
            )
            ax1.set_xlabel('Threshold', fontsize=11)
            ax1.set_ylabel('Mean Residual Life', fontsize=11)
            ax1.set_title('Mean Residual Life Plot\n(Look for linear trend above optimal threshold)',
                         fontsize=12, fontweight='bold')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
        else:
            ax1.text(0.5, 0.5, 'Insufficient data for MRL plot',
                    ha='center', va='center', fontsize=12)

        # 2. Parameter Stability - Shape (xi)
        ax2 = fig.add_subplot(gs[1, 0])
        param_df = self.parameter_stability(n_thresholds=60)

        if not param_df.empty:
            ax2.plot(param_df['threshold'], param_df['xi'], 'ro-', markersize=4, linewidth=1.5)
            ax2.fill_between(
                param_df['threshold'],
                param_df['xi_lower_ci'],
                param_df['xi_upper_ci'],
                alpha=0.2,
                color='red'
            )
            ax2.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
            ax2.set_xlabel('Threshold', fontsize=11)
            ax2.set_ylabel('Shape Parameter (ξ)', fontsize=11)
            ax2.set_title('Shape Parameter Stability\n(Should be stable above optimal threshold)',
                         fontsize=11, fontweight='bold')
            ax2.grid(True, alpha=0.3)

            # Add percentile labels
            ax2_top = ax2.twiny()
            percentiles = param_df['threshold_percentile'].values[::max(1, len(param_df)//5)]
            thresholds = param_df['threshold'].values[::max(1, len(param_df)//5)]
            ax2_top.set_xticks(thresholds)
            ax2_top.set_xticklabels([f'{p:.0f}%' for p in percentiles], fontsize=9)
            ax2_top.set_xlim(ax2.get_xlim())
        else:
            ax2.text(0.5, 0.5, 'Insufficient data',
                    ha='center', va='center', fontsize=11)

        # 3. Parameter Stability - Modified Scale
        ax3 = fig.add_subplot(gs[1, 1])

        if not param_df.empty:
            ax3.plot(param_df['threshold'], param_df['modified_scale'], 'go-',
                    markersize=4, linewidth=1.5, label='σ - ξu')
            ax3.set_xlabel('Threshold', fontsize=11)
            ax3.set_ylabel('Modified Scale (σ - ξu)', fontsize=11)
            ax3.set_title('Modified Scale Stability\n(Should be constant above optimal threshold)',
                         fontsize=11, fontweight='bold')
            ax3.legend()
            ax3.grid(True, alpha=0.3)

            # Add percentile labels
            ax3_top = ax3.twiny()
            ax3_top.set_xticks(thresholds)
            ax3_top.set_xticklabels([f'{p:.0f}%' for p in percentiles], fontsize=9)
            ax3_top.set_xlim(ax3.get_xlim())
        else:
            ax3.text(0.5, 0.5, 'Insufficient data',
                    ha='center', va='center', fontsize=11)

        # 4. Goodness-of-Fit
        ax4 = fig.add_subplot(gs[2, 0])
        gof_df = self.goodness_of_fit_scores(n_thresholds=40)

        if not gof_df.empty:
            ax4.scatter(gof_df['threshold'], gof_df['ks_pvalue'],
                       c=gof_df['n_exceedances'], cmap='viridis', s=50, alpha=0.7)
            ax4.axhline(y=0.05, color='red', linestyle='--', linewidth=1.5,
                       label='p=0.05 threshold', alpha=0.7)
            ax4.set_xlabel('Threshold', fontsize=11)
            ax4.set_ylabel('KS Test P-Value', fontsize=11)
            ax4.set_title('Goodness-of-Fit (KS Test)\n(Higher p-value = better fit, aim for >0.05)',
                         fontsize=11, fontweight='bold')
            ax4.legend()
            ax4.grid(True, alpha=0.3)

            # Colorbar
            cbar = plt.colorbar(ax4.collections[0], ax=ax4)
            cbar.set_label('# Exceedances', fontsize=10)
        else:
            ax4.text(0.5, 0.5, 'Insufficient data',
                    ha='center', va='center', fontsize=11)

        # 5. Automated Selection Summary
        ax5 = fig.add_subplot(gs[2, 1])
        ax5.axis('off')

        # Run automated selection
        selection = self.automated_selection()

        summary_text = f"""
╔═══════════════════════════════════════════╗
║   RECOMMENDED THRESHOLD                   ║
╚═══════════════════════════════════════════╝

Optimal Threshold: {selection['optimal_threshold']:.4f}
Percentile: {selection['optimal_percentile']:.1f}%
Number of Exceedances: {selection['n_exceedances']}

GPD Parameters (at optimal threshold):
  • Shape (ξ): {selection.get('xi', np.nan):.4f}
  • Scale (σ): {selection.get('sigma', np.nan):.4f}

Selection Scores:
  • Stability: {selection.get('stability_score', np.nan):.3f}
  • Goodness-of-Fit: {selection.get('gof_score', np.nan):.3f}
  • Exceedance Balance: {selection.get('exceedance_score', np.nan):.3f}
  • Composite: {selection.get('composite_score', np.nan):.3f}

Method: {selection['method']}

Alternative Thresholds to Consider:
"""

        # Add top 3 alternatives
        if 'all_candidates' in selection:
            candidates = pd.DataFrame(selection['all_candidates'])
            candidates = candidates.nlargest(4, 'composite_score')

            for i, row in candidates.iterrows():
                if i == 0:  # Skip first (already shown)
                    continue
                if len(candidates) - i <= 3:  # Show top 3 alternatives
                    summary_text += f"  • {row['threshold_percentile']:.1f}% (score: {row['composite_score']:.3f})\n"

        summary_text += """
───────────────────────────────────────────

Interpretation Guidelines:
─────────────────────────────
1. MRL Plot: Linear above threshold → good
2. Shape ξ: Stable above threshold → good
3. Modified Scale: Constant → good
4. KS p-value: > 0.05 → good fit

Adjust if:
• Too few exceedances (< 30): lower threshold
• Parameters unstable: try nearby percentiles
• Poor GOF: consider different range
"""

        ax5.text(0.05, 0.95, summary_text, transform=ax5.transAxes,
                fontsize=9, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

        plt.suptitle('Threshold Selection Diagnostic Suite',
                    fontsize=14, fontweight='bold', y=0.995)

        if save_path:
            plt.savefig(save_path, bbox_inches='tight', dpi=300)
            print(f"Threshold diagnostics saved to: {save_path}")

        return fig, selection


def select_threshold_interactive(data, segment_name="", value_col='delta_opex/rev'):
    """
    Interactive threshold selection with visual feedback.

    Parameters:
    -----------
    data : pd.DataFrame or pd.Series
        Data to analyze
    segment_name : str
        Name of segment (for display)
    value_col : str
        Column name if data is DataFrame

    Returns:
    --------
    dict : Threshold selection results
    """
    print("\n" + "="*70)
    print(f"THRESHOLD SELECTION: {segment_name}")
    print("="*70)

    selector = ThresholdSelector(data, value_col=value_col)

    # Run automated selection
    print("\nRunning automated threshold selection...")
    result = selector.automated_selection()

    print(f"\n✓ Recommended Threshold: {result['optimal_threshold']:.4f}")
    print(f"  Percentile: {result['optimal_percentile']:.1f}%")
    print(f"  Exceedances: {result['n_exceedances']}")
    print(f"  Shape (ξ): {result.get('xi', np.nan):.4f}")
    print(f"  Composite Score: {result.get('composite_score', np.nan):.3f}")

    if 'all_candidates' in result and len(result['all_candidates']) > 1:
        print("\n  Alternative thresholds:")
        candidates = pd.DataFrame(result['all_candidates'])
        top_candidates = candidates.nlargest(4, 'composite_score')

        for i, row in top_candidates.iterrows():
            if i == 0:
                continue  # Skip the optimal (already shown)
            print(f"    • {row['threshold_percentile']:.1f}% " +
                  f"(n={int(row['n_exceedances'])}, " +
                  f"ξ={row['xi']:.3f}, " +
                  f"score={row['composite_score']:.3f})")

    print("\n" + "="*70 + "\n")

    return result


# ==================================================================================
# EVT MODELING CLASSES
# ==================================================================================

class PanelEVT:
    """
    Extreme Value Theory model for panel data using Peaks Over Threshold (POT) approach.
    Implements GPD fitting with flexible pooling strategies.
    """

    def __init__(self, data, value_col='delta_opex/rev', segment_col='TOPS',
                 entity_col='spread_id', date_col='DATE_OF_FINANCIALS'):
        """
        Initialize Panel EVT model.

        Parameters:
        -----------
        data : pd.DataFrame
            Panel data with entities observed over time
        value_col : str
            Column name for the variable to model (e.g., delta_opex/rev)
        segment_col : str
            Column name for segments (e.g., country, sub-sector)
        entity_col : str
            Column name for entity IDs
        date_col : str
            Column name for dates
        """
        self.data = data.copy()
        self.value_col = value_col
        self.segment_col = segment_col
        self.entity_col = entity_col
        self.date_col = date_col

        # Model parameters (will be fitted)
        self.segment_models = {}  # Store model params per segment

    def fit_segment(self, segment_name, threshold_percentile=0.95,
                   min_exceedances=30, verbose=True):
        """
        Fit GPD model for a specific segment.

        Parameters:
        -----------
        segment_name : str
            Name of the segment to fit
        threshold_percentile : float
            Percentile for threshold selection (e.g., 0.95 = 95th percentile)
        min_exceedances : int
            Minimum number of exceedances required
        verbose : bool
            Print fitting information

        Returns:
        --------
        dict : Model parameters and diagnostics
        """
        # Filter data for this segment
        segment_data = self.data[self.data[self.segment_col] == segment_name][self.value_col].dropna()

        if len(segment_data) == 0:
            return None

        # Select threshold
        threshold = segment_data.quantile(threshold_percentile)

        # Extract exceedances
        exceedances = segment_data[segment_data > threshold] - threshold
        n_exceedances = len(exceedances)

        if n_exceedances < min_exceedances:
            if verbose:
                print(f"  WARNING: {segment_name} has only {n_exceedances} exceedances (< {min_exceedances})")
                print(f"  Consider lowering threshold. Using empirical fallback.")
            return self._empirical_fallback(segment_name, segment_data)

        # Fit GPD using MLE
        try:
            xi, loc, sigma = genpareto.fit(exceedances, floc=0)

            # Store model parameters
            model = {
                'segment': segment_name,
                'threshold': threshold,
                'threshold_percentile': threshold_percentile,
                'xi': xi,  # shape parameter
                'sigma': sigma,  # scale parameter
                'n_exceedances': n_exceedances,
                'n_total': len(segment_data),
                'exceedance_rate': n_exceedances / len(segment_data),
                'data_min': segment_data.min(),
                'data_max': segment_data.max(),
                'baseline': segment_data.median(),
                'method': 'GPD'
            }

            if verbose:
                print(f"\n{segment_name}:")
                print(f"  Threshold: {threshold:.4f} ({threshold_percentile:.0%})")
                print(f"  Exceedances: {n_exceedances} / {len(segment_data)}")
                print(f"  Shape (ξ): {xi:.4f}")
                print(f"  Scale (σ): {sigma:.4f}")
                self._interpret_tail(xi)

            return model

        except Exception as e:
            if verbose:
                print(f"  ERROR fitting {segment_name}: {e}")
                print(f"  Using empirical fallback.")
            return self._empirical_fallback(segment_name, segment_data)

    def _empirical_fallback(self, segment_name, segment_data):
        """Fallback to empirical distribution if GPD fitting fails"""
        return {
            'segment': segment_name,
            'threshold': segment_data.quantile(0.95),
            'threshold_percentile': 0.95,
            'xi': None,
            'sigma': None,
            'n_exceedances': 0,
            'n_total': len(segment_data),
            'exceedance_rate': 0,
            'data_min': segment_data.min(),
            'data_max': segment_data.max(),
            'baseline': segment_data.median(),
            'method': 'EMPIRICAL',
            'empirical_data': segment_data
        }

    def _interpret_tail(self, xi):
        """Interpret tail behavior based on shape parameter"""
        if xi > 0.5:
            print(f"  → Very heavy tail (infinite variance)")
        elif xi > 0.2:
            print(f"  → Heavy tail")
        elif xi > 0:
            print(f"  → Moderately heavy tail")
        elif abs(xi) < 0.05:
            print(f"  → Exponential-like tail")
        else:
            print(f"  → Light/bounded tail")

    def fit_all_segments(self, segments, threshold_percentile=0.95,
                        min_exceedances=30, verbose=True):
        """
        Fit GPD models for all segments.

        Parameters:
        -----------
        segments : list
            List of segment names to fit
        threshold_percentile : float
            Percentile for threshold selection
        min_exceedances : int
            Minimum exceedances required
        verbose : bool
            Print fitting information
        """
        if verbose:
            print("="*70)
            print("FITTING EVT MODELS FOR ALL SEGMENTS")
            print("="*70)

        for segment in segments:
            model = self.fit_segment(segment, threshold_percentile,
                                    min_exceedances, verbose)
            if model:
                self.segment_models[segment] = model

        if verbose:
            print("\n" + "="*70)
            print(f"Successfully fitted {len(self.segment_models)} segment models")
            print("="*70 + "\n")

    def calculate_var(self, segment_name, confidence_level):
        """
        Calculate Value at Risk using GPD for a given segment.

        Parameters:
        -----------
        segment_name : str
            Segment name
        confidence_level : float
            Confidence level (e.g., 0.99 for 99%)

        Returns:
        --------
        float : VaR estimate
        """
        if segment_name not in self.segment_models:
            return np.nan

        model = self.segment_models[segment_name]

        # Fallback to empirical if GPD failed
        if model['method'] == 'EMPIRICAL':
            return model['empirical_data'].quantile(confidence_level)

        threshold = model['threshold']
        xi = model['xi']
        sigma = model['sigma']
        zeta_u = model['exceedance_rate']

        p = 1 - confidence_level

        # GPD VaR formula
        if abs(xi) < 1e-6:  # Exponential case
            var = threshold + sigma * np.log(zeta_u / p)
        else:
            var = threshold + (sigma / xi) * ((zeta_u / p)**(-xi) - 1)

        return var

    def calculate_es(self, segment_name, confidence_level):
        """
        Calculate Expected Shortfall (CVaR) using GPD.

        Parameters:
        -----------
        segment_name : str
            Segment name
        confidence_level : float
            Confidence level

        Returns:
        --------
        float : ES estimate
        """
        if segment_name not in self.segment_models:
            return np.nan

        model = self.segment_models[segment_name]

        # Fallback to empirical if GPD failed
        if model['method'] == 'EMPIRICAL':
            data = model['empirical_data']
            var = data.quantile(confidence_level)
            return data[data >= var].mean()

        threshold = model['threshold']
        xi = model['xi']
        sigma = model['sigma']

        var = self.calculate_var(segment_name, confidence_level)

        # ES formula for GPD
        if xi < 1:
            es = (var + sigma - xi * threshold) / (1 - xi)
        else:
            es = np.inf  # Undefined for very heavy tails

        return es

    def calculate_stress_impacts(self, segment_name, percentiles, baseline_percentile=50):
        """
        Calculate stress impacts as incremental change from baseline.

        Parameters:
        -----------
        segment_name : str
            Segment name
        percentiles : list
            List of percentiles to calculate (e.g., [50, 60, 67, 75, 90, 97.5])
        baseline_percentile : float
            Baseline percentile (typically 50 for median)

        Returns:
        --------
        dict : Contains percentile values and stress impacts
        """
        # Calculate all percentile values using EVT
        percentile_values = {}
        for p in percentiles:
            confidence_level = p / 100
            percentile_values[p] = self.calculate_var(segment_name, confidence_level)

        # Baseline value (median)
        baseline = percentile_values[baseline_percentile]

        # Calculate stress impacts
        stress_impacts = {}
        for p in percentiles:
            if p != baseline_percentile:
                stress_impacts[p] = percentile_values[p] - baseline

        return {
            'percentile_values': percentile_values,
            'stress_impacts': stress_impacts,
            'baseline': baseline
        }


# ==================================================================================
# BACKTESTING AND PERFORMANCE METRICS
# ==================================================================================

class EVTBacktester:
    """
    Backtesting framework for EVT models.
    Evaluates model performance using historical crisis data and standard metrics.
    """

    def __init__(self, evt_model, data, value_col='delta_opex/rev'):
        """
        Initialize backtester.

        Parameters:
        -----------
        evt_model : PanelEVT
            Fitted EVT model
        data : pd.DataFrame
            Full dataset including test period
        value_col : str
            Column name for values
        """
        self.evt_model = evt_model
        self.data = data
        self.value_col = value_col
        self.results = {}

    def backtest_crisis(self, segment_name, crisis_years=[2008, 2009],
                       target_percentile=96):
        """
        Backtest model using financial crisis data.

        Parameters:
        -----------
        segment_name : str
            Segment to backtest
        crisis_years : list
            Years considered as crisis period
        target_percentile : float
            Target percentile for comparison (e.g., 96 = 1 in 25)

        Returns:
        --------
        dict : Backtesting results
        """
        segment_data = self.data[self.data[self.evt_model.segment_col] == segment_name]

        # Split into training (excluding crisis) and test (crisis years)
        train_data = segment_data[~segment_data['Year'].isin(crisis_years)]
        test_data = segment_data[segment_data['Year'].isin(crisis_years)]

        if len(test_data) == 0:
            return None

        # Get actual crisis values
        actual_crisis_values = test_data[self.value_col].dropna()

        # Get EVT prediction at target percentile
        predicted_var = self.evt_model.calculate_var(
            segment_name,
            target_percentile / 100
        )

        # Calculate metrics
        mae = mean_absolute_error(
            actual_crisis_values,
            [predicted_var] * len(actual_crisis_values)
        )
        rmse = np.sqrt(mean_squared_error(
            actual_crisis_values,
            [predicted_var] * len(actual_crisis_values)
        ))

        # Coverage: what % of crisis observations are below predicted VaR
        coverage = (actual_crisis_values <= predicted_var).mean()

        # Exception rate: what % exceed the predicted VaR
        exception_rate = (actual_crisis_values > predicted_var).mean()

        # Average crisis value
        avg_crisis_value = actual_crisis_values.mean()

        # Find what percentile the avg crisis value represents
        model = self.evt_model.segment_models[segment_name]
        if model['method'] == 'GPD':
            # Calculate empirical percentile rank in full data
            all_data = segment_data[self.value_col].dropna()
            empirical_percentile = (all_data <= avg_crisis_value).mean() * 100
        else:
            empirical_percentile = (model['empirical_data'] <= avg_crisis_value).mean() * 100

        results = {
            'segment': segment_name,
            'crisis_years': crisis_years,
            'n_crisis_obs': len(actual_crisis_values),
            'avg_crisis_value': avg_crisis_value,
            'predicted_var': predicted_var,
            'target_percentile': target_percentile,
            'mae': mae,
            'rmse': rmse,
            'coverage': coverage,
            'exception_rate': exception_rate,
            'empirical_percentile': empirical_percentile,
            'underprediction': max(0, avg_crisis_value - predicted_var),
            'overprediction': max(0, predicted_var - avg_crisis_value)
        }

        return results

    def calculate_coverage_by_percentile(self, segment_name, percentiles):
        """
        Calculate coverage for multiple percentiles.

        Parameters:
        -----------
        segment_name : str
            Segment name
        percentiles : list
            List of percentiles to test

        Returns:
        --------
        dict : Coverage and exception rates per percentile
        """
        segment_data = self.data[
            self.data[self.evt_model.segment_col] == segment_name
        ][self.value_col].dropna()

        coverage = {}
        exception_rate = {}

        for p in percentiles:
            var = self.evt_model.calculate_var(segment_name, p / 100)
            coverage[p] = (segment_data <= var).mean()
            exception_rate[p] = (segment_data > var).mean()

        return {
            'coverage': coverage,
            'exception_rate': exception_rate
        }

    def kupiec_test(self, segment_name, confidence_level=0.99,
                   test_period_years=None):
        """
        Kupiec (1995) test for unconditional coverage.
        Tests if the number of VaR exceptions is consistent with the confidence level.

        Parameters:
        -----------
        segment_name : str
            Segment name
        confidence_level : float
            VaR confidence level
        test_period_years : list, optional
            Specific years to test (if None, uses all data)

        Returns:
        --------
        dict : Test statistic and p-value
        """
        from scipy.stats import chi2

        segment_data = self.data[self.data[self.evt_model.segment_col] == segment_name]

        if test_period_years:
            segment_data = segment_data[segment_data['Year'].isin(test_period_years)]

        actual_values = segment_data[self.value_col].dropna()
        n = len(actual_values)

        # Calculate VaR
        var = self.evt_model.calculate_var(segment_name, confidence_level)

        # Count exceptions
        exceptions = (actual_values > var).sum()

        # Expected exception rate
        p = 1 - confidence_level

        # Likelihood ratio test statistic
        if exceptions == 0:
            lr_stat = -2 * np.log((1 - p)**n)
        elif exceptions == n:
            lr_stat = -2 * np.log(p**n)
        else:
            lr_stat = -2 * (
                n * np.log(1 - p) + exceptions * np.log(p / (exceptions / n))
                + (n - exceptions) * np.log((1 - p) / (1 - exceptions / n))
            )

        # P-value from chi-squared distribution with 1 df
        p_value = 1 - chi2.cdf(lr_stat, df=1)

        return {
            'segment': segment_name,
            'n_observations': n,
            'n_exceptions': exceptions,
            'exception_rate': exceptions / n,
            'expected_exception_rate': p,
            'lr_statistic': lr_stat,
            'p_value': p_value,
            'reject_null': p_value < 0.05  # Reject if model is inadequate
        }


# ==================================================================================
# DATA PREPARATION FUNCTIONS (from original opex.py)
# ==================================================================================

def compute_delta(group, change='relative'):
    """
    Compute year-over-year change in Opex/Revenue ratio.

    Parameters:
    -----------
    group : pd.DataFrame
        Data for a single entity (grouped by ID)
    change : str
        'abs' for absolute change, 'relative' for percentage change, 'none' for no change

    Returns:
    --------
    pd.DataFrame : Group with delta_opex/rev column added
    """
    # Ensure data is sorted
    group = group.sort_values(by=["Year", "Month"])

    if change == "abs":
        # Absolute difference
        group["Opex/Revenue_prev"] = group["Opex/Revenue"].shift(1)
        group["Month_prev"] = group["Month"].shift(1)
        group["Year_prev"] = group["Year"].shift(1)

        group["delta_opex/rev"] = group["Opex/Revenue"].diff()
        group["delta_opex/rev"] = group.apply(
            lambda row: (
                row["delta_opex/rev"]
                if (row["Month"] == row["Month_prev"] and row["Year"] - row["Year_prev"] == 1)
                else np.nan
            ),
            axis=1,
        )

    elif change == "relative":
        # Relative (percentage) change
        group["Opex/Revenue_prev"] = group["Opex/Revenue"].shift(1)
        group["Month_prev"] = group["Month"].shift(1)
        group["Year_prev"] = group["Year"].shift(1)

        group["delta_opex/rev"] = np.where(
            (group["Month"] == group["Month_prev"])
            & (group["Year"] - group["Year_prev"] == 1)
            & (group["Opex/Revenue_prev"] != 0),
            (group["Opex/Revenue"] - group["Opex/Revenue_prev"]) / group["Opex/Revenue_prev"],
            np.nan,
        )

    elif change == "none":
        # No change calculation
        pass

    # Clean up helper columns
    group.drop(
        columns=["Opex/Revenue_prev", "Month_prev", "Year_prev"],
        inplace=True,
        errors="ignore",
    )

    return group


def revenue_adjustment(df, exclusion_file_path, id_column_name="spread_id"):
    """
    Adjust revenue for identified outliers based on exclusion file.

    Parameters:
    -----------
    df : pd.DataFrame
        Financial data
    exclusion_file_path : str
        Path to exclusion file with outlier adjustments
    id_column_name : str
        Name of ID column

    Returns:
    --------
    pd.DataFrame : Data with adjusted revenues
    """
    # Load exclusion data
    if exclusion_file_path.endswith("xlsx"):
        exclusion = pd.read_excel(exclusion_file_path, sheet_name="Outlier Panel Data")
    elif exclusion_file_path.endswith("csv"):
        exclusion = pd.read_csv(exclusion_file_path)
    else:
        raise ValueError("Invalid file type for exclusion data")

    original_fin = df.copy()
    original_fin["DATE_OF_FINANCIALS"] = original_fin["DATE_OF_FINANCIALS"].astype("str")

    # Split by quarter endings
    dates = ["-12-31", "-03-31", "-06-30", "-09-30"]
    quarterly_dfs = []

    for date in dates:
        date_df = original_fin[original_fin["DATE_OF_FINANCIALS"].str.endswith(date)]
        date_df = date_df.sort_values([id_column_name, "DATE_OF_FINANCIALS"], ascending=[True, True])
        quarterly_dfs.append(date_df)

    original_fin = pd.concat(quarterly_dfs, axis=0, ignore_index=True)

    # Calculate previous revenue
    original_fin["Prev_Rev"] = original_fin["SLS_REVENUES"].shift()
    original_fin["DATE_OF_FINANCIALS"] = pd.to_datetime(original_fin["DATE_OF_FINANCIALS"])
    exclusion["Date"] = pd.to_datetime(exclusion["Date"])

    # Mark valid previous revenues (365-366 days apart, same entity)
    original_fin["Prev_Rev"] = np.where(
        (
            original_fin["DATE_OF_FINANCIALS"]
            .diff()
            .abs()
            .between(pd.Timedelta(days=365), pd.Timedelta(days=366))
        )
        & (original_fin[id_column_name] == original_fin[id_column_name].shift()),
        original_fin["Prev_Rev"],
        "Not applicable",
    )

    # Merge with exclusion data
    rev_ref = pd.merge(
        exclusion,
        original_fin,
        how="right",
        left_on=["Date", id_column_name],
        right_on=["DATE_OF_FINANCIALS", id_column_name],
    )

    # Adjust revenue for outliers
    rev_ref["Prev_Rev"] = pd.to_numeric(rev_ref["Prev_Rev"], errors="coerce")
    rev_ref["SLS_REVENUES"] = np.where(
        (rev_ref["outlier_weight"] == 0.00001),
        rev_ref["Prev_Rev"] * (1 + rev_ref["y_winsor"]),
        rev_ref["SLS_REVENUES"],
    )

    return rev_ref


def summarize_step(df, top_segments, sub_segment_column_name, includeOthers,
                  step_name, id_column_name="spread_id"):
    """
    Create summary statistics for a data cleaning step.

    Parameters:
    -----------
    df : pd.DataFrame
        Data at current step
    top_segments : list
        List of top segments to track
    sub_segment_column_name : str
        Column name for segments
    includeOthers : bool
        Whether to include "Others" category
    step_name : str
        Description of the step
    id_column_name : str
        Name of ID column

    Returns:
    --------
    pd.DataFrame : Summary with unique IDs and datapoint counts per segment
    """
    financials = df.copy()

    # Create grouping column
    if includeOthers:
        region_list = top_segments + ["Others"]
        financials["__region__"] = financials[sub_segment_column_name].apply(
            lambda x: x if x in top_segments else "Others"
        )
    else:
        region_list = top_segments
        financials["__region__"] = financials[sub_segment_column_name]

    # Generate summary
    summary = []
    for region in region_list:
        df_region = financials[financials["__region__"] == region]
        summary.append(
            {
                "Step": step_name,
                "Region": region,
                "Unique spread IDs": df_region[id_column_name].nunique(),
                "Total datapoints": df_region.shape[0],
            }
        )

    return pd.DataFrame(summary)


# ==================================================================================
# VISUALIZATION FUNCTIONS
# ==================================================================================

def plot_evt_diagnostics(evt_model, segment_name, data, value_col='delta_opex/rev'):
    """
    Create comprehensive diagnostic plots for EVT model.

    Parameters:
    -----------
    evt_model : PanelEVT
        Fitted EVT model
    segment_name : str
        Segment to plot
    data : pd.DataFrame
        Full dataset
    value_col : str
        Column name for values

    Returns:
    --------
    matplotlib.figure.Figure
    """
    if segment_name not in evt_model.segment_models:
        return None

    model = evt_model.segment_models[segment_name]
    segment_data = data[data[evt_model.segment_col] == segment_name][value_col].dropna()

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle(f'EVT Diagnostic Plots: {segment_name}', fontsize=16, fontweight='bold')

    # 1. Histogram with EVT quantiles
    axes[0, 0].hist(segment_data, bins=50, alpha=0.7, edgecolor='black', color='lightblue')

    percentiles = [50, 60, 67, 75, 90, 97.5]
    colors = ['green', 'orange', 'orange', 'red', 'red', 'darkred']

    for p, color in zip(percentiles, colors):
        var = evt_model.calculate_var(segment_name, p/100)
        axes[0, 0].axvline(var, color=color, linestyle='--', linewidth=2,
                          label=f'{p}th percentile: {var:.4f}')

    axes[0, 0].set_xlabel('Delta Opex/Revenue')
    axes[0, 0].set_ylabel('Frequency')
    axes[0, 0].set_title('Distribution with EVT Quantiles')
    axes[0, 0].legend(fontsize=8)
    axes[0, 0].grid(axis='y', alpha=0.3)

    # 2. QQ-Plot
    if model['method'] == 'GPD':
        threshold = model['threshold']
        exceedances = segment_data[segment_data > threshold] - threshold
        sorted_exc = np.sort(exceedances)
        n = len(sorted_exc)

        theoretical = genpareto.ppf(
            np.arange(1, n+1)/(n+1),
            model['xi'],
            loc=0,
            scale=model['sigma']
        )

        axes[0, 1].scatter(theoretical, sorted_exc, alpha=0.6, s=20)
        axes[0, 1].plot([sorted_exc.min(), sorted_exc.max()],
                       [sorted_exc.min(), sorted_exc.max()],
                       'r--', lw=2, label='Perfect fit')
        axes[0, 1].set_xlabel('Theoretical Quantiles')
        axes[0, 1].set_ylabel('Sample Quantiles')
        axes[0, 1].set_title('QQ-Plot (GPD)')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
    else:
        axes[0, 1].text(0.5, 0.5, 'Empirical Model\n(No GPD fit)',
                       ha='center', va='center', fontsize=12)
        axes[0, 1].set_title('QQ-Plot (Not Available)')

    # 3. PP-Plot
    if model['method'] == 'GPD':
        empirical_prob = np.arange(1, n+1) / (n+1)
        theoretical_prob = genpareto.cdf(sorted_exc, model['xi'], loc=0, scale=model['sigma'])

        axes[0, 2].scatter(theoretical_prob, empirical_prob, alpha=0.6, s=20)
        axes[0, 2].plot([0, 1], [0, 1], 'r--', lw=2, label='Perfect fit')
        axes[0, 2].set_xlabel('Theoretical Probabilities')
        axes[0, 2].set_ylabel('Empirical Probabilities')
        axes[0, 2].set_title('PP-Plot (GPD)')
        axes[0, 2].legend()
        axes[0, 2].grid(True, alpha=0.3)
    else:
        axes[0, 2].text(0.5, 0.5, 'Empirical Model\n(No GPD fit)',
                       ha='center', va='center', fontsize=12)
        axes[0, 2].set_title('PP-Plot (Not Available)')

    # 4. Return Level Plot
    return_periods = np.logspace(0, 2, 50)  # 1 to 100
    return_levels = []

    for rp in return_periods:
        confidence = 1 - 1/rp
        rl = evt_model.calculate_var(segment_name, confidence)
        return_levels.append(rl)

    axes[1, 0].plot(return_periods, return_levels, 'b-', linewidth=2)
    axes[1, 0].set_xscale('log')
    axes[1, 0].set_xlabel('Return Period (years)')
    axes[1, 0].set_ylabel('Return Level')
    axes[1, 0].set_title('Return Level Plot')
    axes[1, 0].grid(True, alpha=0.3)

    # Add reference lines for common return periods
    for rp in [10, 25, 50, 100]:
        if rp <= return_periods.max():
            rl = evt_model.calculate_var(segment_name, 1 - 1/rp)
            axes[1, 0].axhline(rl, color='red', linestyle=':', alpha=0.5)
            axes[1, 0].text(return_periods.max() * 0.7, rl, f'{rp}-year',
                          fontsize=8, va='bottom')

    # 5. Exceedances over time
    segment_df = data[data[evt_model.segment_col] == segment_name]

    if model['method'] == 'GPD':
        exceed_by_year = segment_df[segment_df[value_col] > model['threshold']].groupby('Year').size()

        axes[1, 1].bar(exceed_by_year.index, exceed_by_year.values, alpha=0.7, color='coral')
        axes[1, 1].axhline(model['n_exceedances'] / model['n_total'] *
                          segment_df.groupby('Year').size().mean(),
                          color='red', linestyle='--', linewidth=2,
                          label=f'Expected rate')
        axes[1, 1].set_xlabel('Year')
        axes[1, 1].set_ylabel('Number of Exceedances')
        axes[1, 1].set_title(f'Threshold Exceedances Over Time (u={model["threshold"]:.4f})')
        axes[1, 1].legend()
        axes[1, 1].grid(axis='y', alpha=0.3)
    else:
        axes[1, 1].text(0.5, 0.5, 'Empirical Model\n(No threshold)',
                       ha='center', va='center', fontsize=12)
        axes[1, 1].set_title('Exceedances (Not Available)')

    # 6. Model Summary
    axes[1, 2].axis('off')

    summary_text = f"""
    Model Summary
    ─────────────────────────
    Method: {model['method']}

    Data:
      • Total observations: {model['n_total']}
      • Exceedances: {model['n_exceedances']}
      • Min: {model['data_min']:.4f}
      • Max: {model['data_max']:.4f}
      • Median: {model['baseline']:.4f}

    """

    if model['method'] == 'GPD':
        summary_text += f"""
    GPD Parameters:
      • Threshold (u): {model['threshold']:.4f}
      • Shape (ξ): {model['xi']:.4f}
      • Scale (σ): {model['sigma']:.4f}

    Tail Interpretation:
    """
        xi = model['xi']
        if xi > 0.5:
            summary_text += "  → Very heavy tail"
        elif xi > 0.2:
            summary_text += "  → Heavy tail"
        elif xi > 0:
            summary_text += "  → Moderately heavy"
        elif abs(xi) < 0.05:
            summary_text += "  → Exponential-like"
        else:
            summary_text += "  → Light/bounded"

    axes[1, 2].text(0.05, 0.95, summary_text, transform=axes[1, 2].transAxes,
                   fontsize=10, verticalalignment='top', fontfamily='monospace',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

    plt.tight_layout()

    return fig


def plot_backtesting_results(backtester, segment_name, percentiles=[50, 60, 67, 75, 90, 97.5]):
    """
    Plot backtesting results including coverage and crisis comparison.

    Parameters:
    -----------
    backtester : EVTBacktester
        Backtester with results
    segment_name : str
        Segment to plot
    percentiles : list
        Percentiles to show

    Returns:
    --------
    matplotlib.figure.Figure
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'Backtesting Results: {segment_name}', fontsize=16, fontweight='bold')

    # 1. Coverage by percentile
    coverage_results = backtester.calculate_coverage_by_percentile(segment_name, percentiles)

    percentile_labels = [f'{p}th' for p in percentiles]
    coverage_values = [coverage_results['coverage'][p] for p in percentiles]
    expected_coverage = [p/100 for p in percentiles]

    x = np.arange(len(percentiles))
    width = 0.35

    axes[0, 0].bar(x - width/2, coverage_values, width, label='Actual Coverage',
                  alpha=0.7, color='steelblue')
    axes[0, 0].bar(x + width/2, expected_coverage, width, label='Expected Coverage',
                  alpha=0.7, color='lightcoral')
    axes[0, 0].set_xlabel('Percentile')
    axes[0, 0].set_ylabel('Coverage')
    axes[0, 0].set_title('Actual vs Expected Coverage')
    axes[0, 0].set_xticks(x)
    axes[0, 0].set_xticklabels(percentile_labels, rotation=45)
    axes[0, 0].legend()
    axes[0, 0].grid(axis='y', alpha=0.3)
    axes[0, 0].axhline(y=1.0, color='green', linestyle='--', linewidth=1, alpha=0.5)

    # 2. Exception Rate by percentile
    exception_values = [coverage_results['exception_rate'][p] for p in percentiles]
    expected_exception = [1 - p/100 for p in percentiles]

    axes[0, 1].bar(x - width/2, exception_values, width, label='Actual Exception Rate',
                  alpha=0.7, color='coral')
    axes[0, 1].bar(x + width/2, expected_exception, width, label='Expected Exception Rate',
                  alpha=0.7, color='lightgreen')
    axes[0, 1].set_xlabel('Percentile')
    axes[0, 1].set_ylabel('Exception Rate')
    axes[0, 1].set_title('Actual vs Expected Exception Rate')
    axes[0, 1].set_xticks(x)
    axes[0, 1].set_xticklabels(percentile_labels, rotation=45)
    axes[0, 1].legend()
    axes[0, 1].grid(axis='y', alpha=0.3)

    # 3. Crisis period analysis (2008-2009)
    crisis_2008 = backtester.backtest_crisis(segment_name, [2008], target_percentile=96)
    crisis_2009 = backtester.backtest_crisis(segment_name, [2009], target_percentile=96)

    if crisis_2008 and crisis_2009:
        crisis_labels = ['2008', '2009']
        actual_values = [crisis_2008['avg_crisis_value'], crisis_2009['avg_crisis_value']]
        predicted_values = [crisis_2008['predicted_var'], crisis_2009['predicted_var']]

        x_crisis = np.arange(len(crisis_labels))

        axes[1, 0].bar(x_crisis - width/2, actual_values, width,
                      label='Actual Crisis Value', alpha=0.7, color='darkred')
        axes[1, 0].bar(x_crisis + width/2, predicted_values, width,
                      label='Predicted VaR (96th %ile)', alpha=0.7, color='navy')
        axes[1, 0].set_xlabel('Crisis Year')
        axes[1, 0].set_ylabel('Delta Opex/Revenue')
        axes[1, 0].set_title('Crisis Period: Actual vs Predicted')
        axes[1, 0].set_xticks(x_crisis)
        axes[1, 0].set_xticklabels(crisis_labels)
        axes[1, 0].legend()
        axes[1, 0].grid(axis='y', alpha=0.3)

        # 4. Performance Metrics Summary
        axes[1, 1].axis('off')

        metrics_text = f"""
        Performance Metrics Summary
        ═══════════════════════════════════

        2008 Crisis:
        ────────────────────────────────
          • Actual avg value: {crisis_2008['avg_crisis_value']:.4f}
          • Predicted VaR (96th): {crisis_2008['predicted_var']:.4f}
          • MAE: {crisis_2008['mae']:.4f}
          • RMSE: {crisis_2008['rmse']:.4f}
          • Coverage: {crisis_2008['coverage']:.2%}
          • Exception rate: {crisis_2008['exception_rate']:.2%}
          • Empirical %ile: {crisis_2008['empirical_percentile']:.1f}th

        2009 Crisis:
        ────────────────────────────────
          • Actual avg value: {crisis_2009['avg_crisis_value']:.4f}
          • Predicted VaR (96th): {crisis_2009['predicted_var']:.4f}
          • MAE: {crisis_2009['mae']:.4f}
          • RMSE: {crisis_2009['rmse']:.4f}
          • Coverage: {crisis_2009['coverage']:.2%}
          • Exception rate: {crisis_2009['exception_rate']:.2%}
          • Empirical %ile: {crisis_2009['empirical_percentile']:.1f}th

        Model Assessment:
        ────────────────────────────────
        """

        # Assess model performance
        avg_coverage_error = np.mean([
            abs(crisis_2008['coverage'] - 0.96),
            abs(crisis_2009['coverage'] - 0.96)
        ])

        if avg_coverage_error < 0.1:
            metrics_text += "  ✓ Good coverage accuracy"
        elif avg_coverage_error < 0.2:
            metrics_text += "  ~ Moderate coverage accuracy"
        else:
            metrics_text += "  ✗ Poor coverage accuracy"

        axes[1, 1].text(0.05, 0.95, metrics_text, transform=axes[1, 1].transAxes,
                       fontsize=9, verticalalignment='top', fontfamily='monospace',
                       bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))
    else:
        axes[1, 0].text(0.5, 0.5, 'No crisis data available',
                       ha='center', va='center', fontsize=12)
        axes[1, 1].text(0.5, 0.5, 'No crisis data available',
                       ha='center', va='center', fontsize=12)

    plt.tight_layout()

    return fig


# ==================================================================================
# MAIN OPEX EVT FUNCTION
# ==================================================================================

def Opex_EVT(sector_name, threshold_percentile=0.95, min_exceedances=30,
             run_threshold_diagnostics=True, use_auto_threshold=False):
    """
    Main function to run OPEX analysis using EVT methodology.

    Parameters:
    -----------
    sector_name : str
        Name of the sector to analyze (must be in SECTORS config)
    threshold_percentile : float
        Percentile for EVT threshold selection (default: 0.95)
        Ignored if use_auto_threshold=True
    min_exceedances : int
        Minimum number of exceedances required for GPD fitting (default: 30)
    run_threshold_diagnostics : bool
        Whether to generate threshold selection diagnostic plots (default: True)
    use_auto_threshold : bool
        Whether to use automated threshold selection instead of fixed percentile (default: False)
    """

    print("\n" + "="*80)
    print(f"OPEX EVT ANALYSIS: {sector_name}")
    print("="*80 + "\n")

    # --- Load Configuration ---
    Opex_config = SECTORS[sector_name]

    sector = Opex_config.sector
    sector_short = Opex_config.sector_short
    segmentByCountry = Opex_config.segmentByCountry
    top_segments = Opex_config.top_segments.copy()  # Make a copy to avoid modifying original
    includeOthers = Opex_config.includeOthers
    sub_segment_column_name = Opex_config.sub_segment_column_name
    sub_segment_function = Opex_config.sub_segment_function
    sub_segment_mapping = Opex_config.sub_segment_mapping
    sub_segment_replacement_dict = Opex_config.sub_segment_replacement_dict
    applyingDampener = Opex_config.applyingDampener
    dampenerPercentileBySegment = Opex_config.dampenerPercentileBySegment
    id_column_name = Opex_config.id_column_name
    includeZeroOpex = Opex_config.includeZeroOpex
    percentiles_for_file = Opex_config.percentiles_for_file
    percentiles_for_chart = Opex_config.percentiles_for_chart
    groupCountry = Opex_config.groupCountry
    groupSector = Opex_config.groupSector
    ISIC_mapping = Opex_config.ISIC_mapping
    country_group_mapping = Opex_config.country_group_mapping
    exclude_sub_na = Opex_config.exclude_sub_na
    dampned_for_revenue_outlier = Opex_config.dampned_for_revenue_outlier
    step_2_quantile = Opex_config.step_2_quantile
    globalmodel = Opex_config.globalmodel
    global_exclude_sectors = Opex_config.global_exclude_sectors
    sub_segment_case = Opex_config.sub_segment_case

    # Input paths
    isic_file_path = Opex_config.isic_file_path
    fin_file_path = Opex_config.fin_file_path
    exclusion_file_path = Opex_config.exclusion_file_path
    exclusion_file_path_gen2 = Opex_config.exclusion_file_path_gen2

    # Output paths (EVT-specific)
    output_dir = f"{OUT_DIR}/{sector_name}/EVT"
    os.makedirs(output_dir, exist_ok=True)

    stress_result_file_path = windows_long_path(
        f"{output_dir}/Opex_{sector_short}_EVT_Stress_Impacts.xlsx"
    )
    full_result_file_path = windows_long_path(
        f"{output_dir}/Opex_{sector_short}_EVT_Full_Data.xlsx"
    )
    diagnostics_pdf_path = windows_long_path(
        f"{output_dir}/Opex_{sector_short}_EVT_Diagnostics.pdf"
    )
    backtesting_pdf_path = windows_long_path(
        f"{output_dir}/Opex_{sector_short}_EVT_Backtesting.pdf"
    )
    summary_path = windows_long_path(
        f"{output_dir}/Opex_{sector_short}_EVT_Consolidated.xlsx"
    )

    # ==================================================================================
    # STEP 1: LOAD AND PREPARE DATA (same as original opex.py)
    # ==================================================================================

    print("STEP 1: Loading and preparing data...")

    # Load data
    financials = pd.read_csv(fin_file_path).iloc[:, 1:]

    # Apply revenue adjustment if configured
    if not dampned_for_revenue_outlier:
        financials = revenue_adjustment(financials.copy(), exclusion_file_path_gen2, id_column_name)

    isic_data = pd.read_excel(isic_file_path)
    financials["country_of_risk"] = financials["country_of_risk"].str.upper()

    # ISIC mapping
    if ISIC_mapping:
        financials.rename(columns={"RA_Industry": "RA_Industry_Old"}, inplace=True)

        isic_map = isic_data.set_index("ISIC Code")["Risk Industry_April 2025"].to_dict()
        subseg_map = isic_data.set_index("ISIC Code")["Biz L1_Apr 2025.1"].to_dict()

        if globalmodel:
            financials["RA_Industry"] = financials["isic_code"].map(isic_map).fillna("NA")
            financials = financials[~financials["RA_Industry"].isin(global_exclude_sectors)]
            financials = financials[financials["RA_Industry"] != "NA"]
        else:
            isic_data_filtered = isic_data[isic_data["Risk Industry_April 2025"] == sector]
            financials["RA_Industry"] = np.where(
                financials["isic_code"].isin(isic_data_filtered["ISIC Code"].unique()),
                sector,
                "Not Applicable",
            )
            financials["sub_segment"] = financials["isic_code"].map(subseg_map).fillna("NA")
            financials = financials[financials["RA_Industry"] == sector]
            if sub_segment_case:
                financials["sub_segment"] = financials["sub_segment"].str.title()
    else:
        financials = financials[financials["RA_Industry"] == sector]

    # Country/Sector grouping
    if groupCountry:
        reverse_country_map = {}
        for group_label, countries in country_group_mapping.items():
            for country in countries:
                reverse_country_map[country] = group_label
        financials["country_of_risk_grouped"] = financials["country_of_risk"].apply(
            lambda x: reverse_country_map.get(x, x)
        )

    if groupSector:
        reverse_country_map = {}
        for group_label, countries in country_group_mapping.items():
            for country in countries:
                reverse_country_map[country] = group_label
        financials["sub_segment_group"] = financials["sub_segment"].apply(
            lambda x: reverse_country_map.get(x, x)
        )

    # Sub-segment processing
    if sub_segment_replacement_dict:
        financials.replace({sub_segment_column_name: sub_segment_replacement_dict}, inplace=True)

    financials[sub_segment_column_name] = financials[sub_segment_column_name].fillna("Others")

    if sub_segment_function:
        financials[sub_segment_column_name] = (
            financials["isic_code"].map(sub_segment_mapping).fillna("Others")
        )

    if exclude_sub_na:
        financials = financials[financials["sub_segment"] != "Not applicable"]

    if sector_name == "Consumer Durables & Apparel":
        financials["sub_segment"] = financials["sub_segment"].str.upper()

    # Summary step 1
    summary_1 = summarize_step(
        financials, top_segments, sub_segment_column_name,
        includeOthers, "Step 1: Initial data", id_column_name
    )

    # ==================================================================================
    # STEP 2: DATA CLEANING PIPELINE (9 steps - same as original)
    # ==================================================================================

    print("STEP 2: Applying data cleaning pipeline...")

    financials[id_column_name] = financials[id_column_name].astype(str)
    financials["DATE_OF_FINANCIALS"] = pd.to_datetime(financials["DATE_OF_FINANCIALS"])
    financials["Year"] = financials["DATE_OF_FINANCIALS"].dt.year
    financials["Month"] = financials["DATE_OF_FINANCIALS"].dt.month

    # Step 2: Drop Revenue 'Not applicable'
    financials["SLS_REVENUES"] = financials["SLS_REVENUES"].replace("Not applicable", None)
    summary_2 = summarize_step(
        financials, top_segments, sub_segment_column_name,
        includeOthers, "Step 2: Data after dropping Revenue 'Not applicable'", id_column_name
    )

    # Step 3: Drop Revenue 'Missing'
    financials["SLS_REVENUES"] = financials["SLS_REVENUES"].replace("Missing", None)
    summary_3 = summarize_step(
        financials, top_segments, sub_segment_column_name,
        includeOthers, "Step 3: Data after dropping Revenue 'Missing'", id_column_name
    )

    # Step 4: Drop Revenue = 0
    financials["SLS_REVENUES"] = financials["SLS_REVENUES"].astype(float)
    financials = financials[financials["SLS_REVENUES"] != 0]
    summary_4 = summarize_step(
        financials, top_segments, sub_segment_column_name,
        includeOthers, "Step 4: Data after dropping Revenue 0", id_column_name
    )

    # Process OPEX
    financials["Opex"] = financials["Opex"].replace("Missing", None)
    financials["Opex"] = financials["Opex"].replace("Not applicable", None)
    financials["Opex"] = financials["Opex"].astype(float)

    # Step 5: Calculate Opex/Revenue and filter
    financials["Opex/Revenue"] = financials["Opex"] / financials["SLS_REVENUES"]

    if includeZeroOpex:
        financials = financials[financials["Opex/Revenue"] >= 0]
    else:
        financials = financials[financials["Opex/Revenue"] > 0]

    summary_5 = summarize_step(
        financials, top_segments, sub_segment_column_name,
        includeOthers, "Step 5: Data after keeping only OPEX/REVENUE > 0", id_column_name
    )

    # Step 6: Drop NAs
    Opex = financials.dropna(subset=["Opex/Revenue", "SLS_REVENUES"])
    summary_6 = summarize_step(
        Opex, top_segments, sub_segment_column_name,
        includeOthers, "Step 6: Data after dropping 'Opex/Revenue' or Revenue NA", id_column_name
    )

    # Step 7: Remove quarterly duplicates (keep annual)
    Opex = Opex.sort_values(by=[id_column_name, "Year", "Month"], ascending=[True, True, False])
    Opex_end = Opex.drop_duplicates(subset=[id_column_name, "Year"], keep="first")
    summary_7 = summarize_step(
        Opex_end, top_segments, sub_segment_column_name,
        includeOthers, "Step 7: Data after removing duplicates by spread_id and Date", id_column_name
    )

    # Step 8: Remove infinity values
    Opex_clean = Opex_end[~Opex_end["Opex/Revenue"].isin([float("inf")])]
    summary_8 = summarize_step(
        Opex_clean, top_segments, sub_segment_column_name,
        includeOthers, "Step 8: Data after removing inf values in 'Opex/Revenue'", id_column_name
    )

    # Step 9: Final data
    summary_9 = summarize_step(
        Opex_clean, top_segments, sub_segment_column_name,
        includeOthers, "Step 9: Final modelling data", id_column_name
    )

    # ==================================================================================
    # STEP 3: COMPUTE DELTA (year-over-year change)
    # ==================================================================================

    print("STEP 3: Computing year-over-year delta...")

    change_type = "relative"  # Relative change
    Opex_clean_rel = Opex_clean.groupby(id_column_name, group_keys=False).apply(
        lambda x: compute_delta(x, change=change_type)
    )

    # Create TOPS column (top segments + Others)
    Opex_clean_rel["TOPS"] = np.where(
        Opex_clean_rel[sub_segment_column_name].isin(top_segments),
        Opex_clean_rel[sub_segment_column_name],
        "Others",
    )

    if includeOthers:
        top_segments_with_others = top_segments + ["Others"]
    else:
        top_segments_with_others = top_segments

    # ==================================================================================
    # STEP 4: APPLY DAMPENERS (same logic as original opex.py)
    # ==================================================================================

    print("STEP 4: Applying dampeners...")

    Opex_clean_rel_exclude = Opex_clean_rel.copy()
    dampening_n = 0
    dampened_counts = pd.Series(dtype=int)
    shrink_summary_df = pd.DataFrame()

    if applyingDampener:
        # Load exclusion data
        if dampned_for_revenue_outlier:
            if exclusion_file_path.endswith("xlsx"):
                exclude = pd.read_excel(exclusion_file_path)
            elif exclusion_file_path.endswith("csv"):
                exclude = pd.read_csv(exclusion_file_path)
            else:
                raise ValueError("Invalid file type for exclusion data")
            dampner_val = 0.0001
        else:
            if exclusion_file_path_gen2.endswith("xlsx"):
                exclusion = pd.read_excel(exclusion_file_path_gen2, sheet_name="Outlier Panel Data")
            elif exclusion_file_path_gen2.endswith("csv"):
                exclusion = pd.read_csv(exclusion_file_path_gen2)
            else:
                raise ValueError("Invalid file type for exclusion data")
            exclude = exclusion[exclusion["outlier_weight"] == 0.00001]
            dampner_val = 1

        exclude["Date"] = pd.to_datetime(exclude["Date"])
        Opex_clean_rel_exclude["DATE_OF_FINANCIALS"] = pd.to_datetime(
            Opex_clean_rel_exclude["DATE_OF_FINANCIALS"]
        )
        exclude[id_column_name] = exclude[id_column_name].astype(str)

        # Create exclusion set
        exclude_set = set(zip(exclude["Date"], exclude[id_column_name]))

        # Step 1: First dampener - based on exclude set
        dampening_mask = (
            Opex_clean_rel_exclude[["DATE_OF_FINANCIALS", id_column_name]]
            .apply(tuple, axis=1)
            .isin(exclude_set)
        )
        dampening_n = dampening_mask.sum()

        dampened_segments = Opex_clean_rel_exclude.loc[dampening_mask, "TOPS"]
        dampened_counts = dampened_segments.value_counts()

        # Apply dampening
        Opex_clean_rel_exclude.loc[
            dampening_mask,
            "delta_opex/rev",
        ] *= dampner_val

        # Step 2: Percentile-based dampener
        percentile_dict = {}
        for segment in Opex_clean_rel_exclude["TOPS"].unique():
            segment_mask = Opex_clean_rel_exclude["TOPS"] == segment
            if dampenerPercentileBySegment:
                percentile_dict[segment] = Opex_clean_rel_exclude.loc[
                    segment_mask, "delta_opex/rev"
                ].quantile(step_2_quantile)
            else:
                percentile_dict[segment] = Opex_clean_rel_exclude[
                    "delta_opex/rev"
                ].quantile(step_2_quantile)

        # Counter for shrunk values
        counter = {"total_shrunk": 0}
        for c in Opex_clean_rel_exclude["TOPS"].unique():
            counter[c] = 0

        # Apply shrink logic (winsorization)
        def shrink_value(row):
            segment = row["TOPS"]
            if (
                (row["DATE_OF_FINANCIALS"], row[id_column_name]) not in exclude_set
                and row["delta_opex/rev"] > percentile_dict[segment]
            ):
                counter["total_shrunk"] += 1
                counter[segment] += 1
                if dampned_for_revenue_outlier:
                    return row["delta_opex/rev"] * 0.0001
                else:
                    return percentile_dict[segment]  # Winsorize to threshold
            return row["delta_opex/rev"]

        if dampned_for_revenue_outlier:
            Opex_clean_rel_exclude["delta_opex/rev"] = Opex_clean_rel_exclude.apply(
                shrink_value, axis=1
            )
        else:
            # Apply clipping per segment
            for segment in Opex_clean_rel_exclude["TOPS"].unique():
                segment_mask = Opex_clean_rel_exclude["TOPS"] == segment
                quantile_value = percentile_dict[segment]

                # Mark winsorized values
                winsorized_mask = (
                    segment_mask
                    & (Opex_clean_rel_exclude["delta_opex/rev"] > quantile_value)
                    & (~Opex_clean_rel_exclude[["DATE_OF_FINANCIALS", id_column_name]]
                       .apply(tuple, axis=1).isin(exclude_set))
                )

                counter[segment] = winsorized_mask.sum()
                counter["total_shrunk"] += winsorized_mask.sum()

                # Apply winsorization
                Opex_clean_rel_exclude.loc[winsorized_mask, "delta_opex/rev"] = quantile_value

        # Create shrink summary
        shrink_summary_df = pd.DataFrame(
            [
                {"TOPS": seg, f"Outliers {int(100*(step_2_quantile))}th Percentile": val}
                for seg, val in counter.items()
                if seg != "total_shrunk"
            ]
        )
        shrink_summary_df = pd.concat(
            [
                shrink_summary_df,
                pd.DataFrame(
                    [
                        {
                            "TOPS": "TOTAL",
                            f"Outliers {int(100*(step_2_quantile))}th Percentile": counter["total_shrunk"],
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )

    print(f"  Dampened {dampening_n} datapoints from exclusion list")
    print(f"  Winsorized {counter.get('total_shrunk', 0)} datapoints at {step_2_quantile:.0%} percentile")

    # ==================================================================================
    # STEP 4.5: THRESHOLD SELECTION DIAGNOSTICS (Optional)
    # ==================================================================================

    threshold_selection_pdf_path = windows_long_path(
        f"{output_dir}/Opex_{sector_short}_EVT_Threshold_Selection.pdf"
    )

    segment_thresholds = {}  # Store optimal thresholds per segment

    if run_threshold_diagnostics or use_auto_threshold:
        print("\nSTEP 4.5: Running threshold selection diagnostics...")

        with PdfPages(threshold_selection_pdf_path) as pdf:
            for segment in top_segments_with_others:
                segment_data = Opex_clean_rel_exclude[
                    Opex_clean_rel_exclude["TOPS"] == segment
                ]["delta_opex/rev"].dropna()

                if len(segment_data) < 50:
                    print(f"  Skipping {segment} (insufficient data: n={len(segment_data)})")
                    continue

                print(f"\n  Analyzing threshold for: {segment}")
                print(f"    Data points: {len(segment_data)}")

                # Create threshold selector
                selector = ThresholdSelector(segment_data)

                # Generate diagnostic plots and get recommendation
                fig, selection = selector.plot_diagnostics(save_path=None)
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)

                # Store the recommendation
                segment_thresholds[segment] = {
                    'threshold': selection['optimal_threshold'],
                    'threshold_percentile': selection['optimal_percentile'],
                    'n_exceedances': selection['n_exceedances'],
                    'method': selection['method']
                }

                if use_auto_threshold:
                    print(f"    ✓ Auto-selected threshold: {selection['optimal_threshold']:.4f} " +
                          f"({selection['optimal_percentile']:.1f}%)")
                else:
                    print(f"    ℹ Recommended: {selection['optimal_threshold']:.4f} " +
                          f"({selection['optimal_percentile']:.1f}%), " +
                          f"Using fixed: {threshold_percentile:.0%}")

        print(f"\n  ✓ Threshold diagnostics saved to: {threshold_selection_pdf_path}")

    # ==================================================================================
    # STEP 5: FIT EVT MODELS FOR EACH SEGMENT
    # ==================================================================================

    print("\nSTEP 5: Fitting EVT models for each segment...")

    # Initialize EVT model
    evt_model = PanelEVT(
        data=Opex_clean_rel_exclude,
        value_col='delta_opex/rev',
        segment_col='TOPS',
        entity_col=id_column_name,
        date_col='DATE_OF_FINANCIALS'
    )

    # Fit models for all segments
    if use_auto_threshold:
        # Use segment-specific thresholds
        print("\n  Using automated threshold selection per segment...")
        for segment in top_segments_with_others:
            if segment in segment_thresholds:
                # Convert percentile to decimal
                seg_threshold_pct = segment_thresholds[segment]['threshold_percentile'] / 100
                model = evt_model.fit_segment(
                    segment,
                    threshold_percentile=seg_threshold_pct,
                    min_exceedances=min_exceedances,
                    verbose=True
                )
                if model:
                    evt_model.segment_models[segment] = model
            else:
                # Fallback to default threshold
                model = evt_model.fit_segment(
                    segment,
                    threshold_percentile=threshold_percentile,
                    min_exceedances=min_exceedances,
                    verbose=True
                )
                if model:
                    evt_model.segment_models[segment] = model
    else:
        # Use fixed threshold for all segments
        evt_model.fit_all_segments(
            segments=top_segments_with_others,
            threshold_percentile=threshold_percentile,
            min_exceedances=min_exceedances,
            verbose=True
        )

    # ==================================================================================
    # STEP 6: CALCULATE STRESS IMPACTS USING EVT
    # ==================================================================================

    print("\nSTEP 6: Calculating stress impacts using EVT...")

    result_data_full = []

    for top_segment in top_segments_with_others:
        subset = Opex_clean_rel_exclude[Opex_clean_rel_exclude["TOPS"] == top_segment]

        # Calculate unique IDs and datapoints
        unique_spread_id = subset[id_column_name].nunique()
        data_points = len(subset)

        # Calculate EVT-based stress impacts
        stress_results = evt_model.calculate_stress_impacts(
            top_segment,
            percentiles=percentiles_for_file,
            baseline_percentile=50
        )

        percentile_values = [stress_results['percentile_values'][p] for p in percentiles_for_file]
        stress_impacts = [stress_results['stress_impacts'].get(p, 0) for p in percentiles_for_file if p != 50]

        # Crisis data (2008-2009) - for backtesting
        crisis_data2008 = subset[subset["Year"].isin([2008])]
        crisis_data2009 = subset[subset["Year"].isin([2009])]
        x_crisis_08 = crisis_data2008["delta_opex/rev"].mean() if len(crisis_data2008) > 0 else np.nan
        x_crisis_09 = crisis_data2009["delta_opex/rev"].mean() if len(crisis_data2009) > 0 else np.nan

        model_data = subset["delta_opex/rev"].dropna()

        # Calculate empirical percentile rank for crisis values
        if not np.isnan(x_crisis_08):
            percentile_rank_08 = (model_data <= x_crisis_08).mean()
            tail_prob_08 = 1 - percentile_rank_08
            return_period_08 = 1/tail_prob_08 if tail_prob_08 > 0 else np.inf
            percentile_08 = np.interp(x_crisis_08, percentile_values, percentiles_for_file)
            percentile_08 = np.clip(percentile_08, percentiles_for_file[0], percentiles_for_file[-1])
        else:
            percentile_rank_08 = np.nan
            percentile_08 = np.nan

        if not np.isnan(x_crisis_09):
            percentile_rank_09 = (model_data <= x_crisis_09).mean()
            tail_prob_09 = 1 - percentile_rank_09
            return_period_09 = 1/tail_prob_09 if tail_prob_09 > 0 else np.inf
            percentile_09 = np.interp(x_crisis_09, percentile_values, percentiles_for_file)
            percentile_09 = np.clip(percentile_09, percentiles_for_file[0], percentiles_for_file[-1])
        else:
            percentile_rank_09 = np.nan
            percentile_09 = np.nan

        # MAE/RMSE for crisis periods
        target_perc = 96  # 1 in 25 scenario
        target_idx = np.abs(np.array(percentiles_for_file) - target_perc).argmin()
        forecasted_stress = percentile_values[target_idx] - percentile_values[0]

        crisis_data_clean_2008 = crisis_data2008["delta_opex/rev"].dropna()
        crisis_data_clean_2009 = crisis_data2009["delta_opex/rev"].dropna()

        if len(crisis_data_clean_2008) > 0:
            mae_2008 = mean_absolute_error(
                crisis_data_clean_2008,
                [forecasted_stress] * len(crisis_data_clean_2008)
            )
            rmse_2008 = np.sqrt(mean_squared_error(
                crisis_data_clean_2008,
                [forecasted_stress] * len(crisis_data_clean_2008)
            ))
        else:
            mae_2008, rmse_2008 = np.nan, np.nan

        if len(crisis_data_clean_2009) > 0:
            mae_2009 = mean_absolute_error(
                crisis_data_clean_2009,
                [forecasted_stress] * len(crisis_data_clean_2009)
            )
            rmse_2009 = np.sqrt(mean_squared_error(
                crisis_data_clean_2009,
                [forecasted_stress] * len(crisis_data_clean_2009)
            ))
        else:
            mae_2009, rmse_2009 = np.nan, np.nan

        # Coverage and exception rate
        actual = subset["delta_opex/rev"].dropna()
        coverage = {}
        exception_rate = {}

        for i, p in enumerate(percentiles_for_file):
            if p != 50:  # Skip baseline
                var_value = percentile_values[percentiles_for_file.index(p)]
                coverage[p] = (actual <= var_value).mean()
                exception_rate[p] = (actual > var_value).mean()

        coverage_list = [coverage.get(p, np.nan) for p in percentiles_for_file if p != 50]
        exception_list = [exception_rate.get(p, np.nan) for p in percentiles_for_file if p != 50]

        # Append results
        result_data_full.append(
            [
                top_segment,
                unique_spread_id,
                data_points,
                *percentile_values,
                *stress_impacts,
                *coverage_list,
                *exception_list,
                x_crisis_08,
                x_crisis_09,
                percentile_rank_08,
                percentile_rank_09,
                percentile_08,
                percentile_09,
                mae_2008,
                rmse_2008,
                mae_2009,
                rmse_2009,
            ]
        )

    # Create DataFrame
    percentiles_str = [f"{p:.2f}".rstrip("0").rstrip(".") for p in percentiles_for_file]
    stress_impact_columns = ["Stress Impact - " + ps + "th Perc" for ps in percentiles_str[1:]]
    stress_percentiles_str = percentiles_str[1:]
    coverage_columns = [f"Coverage - {ps}th Perc" for ps in stress_percentiles_str]
    exception_columns = [f"Exception - {ps}th Perc" for ps in stress_percentiles_str]
    crisis_columns = [
        "Historical 2008", "Historical 2009",
        "Historical Percentile 2008", "Historical Percentile 2009",
        "Relative Percentile 2008", "Relative Percentile 2009"
    ]
    error_columns = [
        "MAE - financial crisis08", "RMSE - financial crisis08",
        "MAE - financial crisis09", "RMSE - financial crisis09"
    ]

    columns = [
        "TOPS",
        f'Unique {"LEID" if id_column_name.upper() == "LEID" else "Spread_ID"}s',
        "Data Points",
        *[ps + "th Perc" for ps in percentiles_str],
        *stress_impact_columns,
        *coverage_columns,
        *exception_columns,
        *crisis_columns,
        *error_columns,
    ]

    result_df = pd.DataFrame(result_data_full, columns=columns)
    result_df = result_df.reset_index(drop=True)

    # ==================================================================================
    # STEP 7: BACKTESTING
    # ==================================================================================

    print("\nSTEP 7: Running comprehensive backtesting...")

    # Initialize backtester
    backtester = EVTBacktester(evt_model, Opex_clean_rel_exclude, value_col='delta_opex/rev')

    # Run backtesting for each segment
    backtesting_results = []

    for segment in top_segments_with_others:
        # Crisis period backtesting
        crisis_2008 = backtester.backtest_crisis(segment, [2008], target_percentile=96)
        crisis_2009 = backtester.backtest_crisis(segment, [2009], target_percentile=96)

        # Kupiec test
        kupiec = backtester.kupiec_test(segment, confidence_level=0.96)

        if crisis_2008:
            backtesting_results.append({
                'Segment': segment,
                'Test': 'Crisis 2008',
                'MAE': crisis_2008['mae'],
                'RMSE': crisis_2008['rmse'],
                'Coverage': crisis_2008['coverage'],
                'Exception_Rate': crisis_2008['exception_rate'],
                'Empirical_Percentile': crisis_2008['empirical_percentile']
            })

        if crisis_2009:
            backtesting_results.append({
                'Segment': segment,
                'Test': 'Crisis 2009',
                'MAE': crisis_2009['mae'],
                'RMSE': crisis_2009['rmse'],
                'Coverage': crisis_2009['coverage'],
                'Exception_Rate': crisis_2009['exception_rate'],
                'Empirical_Percentile': crisis_2009['empirical_percentile']
            })

        backtesting_results.append({
            'Segment': segment,
            'Test': 'Kupiec Test',
            'N_Observations': kupiec['n_observations'],
            'N_Exceptions': kupiec['n_exceptions'],
            'Exception_Rate': kupiec['exception_rate'],
            'Expected_Exception_Rate': kupiec['expected_exception_rate'],
            'LR_Statistic': kupiec['lr_statistic'],
            'P_Value': kupiec['p_value'],
            'Reject_Null': kupiec['reject_null']
        })

    backtesting_df = pd.DataFrame(backtesting_results)

    print("\nBacktesting Summary:")
    print(backtesting_df.to_string())

    # ==================================================================================
    # STEP 8: CREATE OUTPUT FILES
    # ==================================================================================

    print("\nSTEP 8: Creating output files...")

    # Prepare stress impact output (long format)
    result_st_df = pd.melt(
        result_df,
        id_vars=["TOPS"],
        value_vars=stress_impact_columns,
    )

    coverage_df = pd.melt(
        result_df,
        id_vars=["TOPS"],
        value_vars=coverage_columns,
    )

    exception_df = pd.melt(
        result_df,
        id_vars=["TOPS"],
        value_vars=exception_columns,
    )

    def extract_perc_key(col):
        return col.split("-")[-1].strip()

    for df in (result_st_df, coverage_df, exception_df):
        df["perc_key"] = df["variable"].apply(extract_perc_key)

    coverage_df = coverage_df.rename(columns={"value": "coverage"})
    exception_df = exception_df.rename(columns={"value": "exception_rate"})

    result_st_df = (
        result_st_df
        .merge(coverage_df.drop(columns=["variable"]), on=["TOPS", "perc_key"])
        .merge(exception_df.drop(columns=["variable"]), on=["TOPS", "perc_key"])
    )

    # Add crisis data
    crisis_df = result_df[["TOPS"] + crisis_columns]
    result_st_df = result_st_df.merge(crisis_df, on="TOPS", how="left")

    # Add error metrics
    error_df = result_df[["TOPS"] + error_columns]
    result_st_df = result_st_df.merge(error_df, on="TOPS", how="left")

    # Rename columns
    segmentColumn = "Country" if segmentByCountry else "Sub-sector"
    result_st_df = result_st_df.rename(
        columns={
            "TOPS": segmentColumn,
            "variable": "Stress Impact - percentile",
            "value": "Stress Impact",
        }
    )

    # Extract percentile for sorting
    result_st_df["Percentile"] = result_st_df["Stress Impact - percentile"].apply(
        lambda x: x.split("-")[1].strip().split(" ")[0] if "Stress" in x else "-"
    )
    result_st_df["Percentile"] = result_st_df["Percentile"].str[:-2]

    result_st_df = result_st_df.sort_values(
        by=[segmentColumn, "Percentile"], ascending=[False, True]
    )

    # Add scenario severity
    lenDF = len(result_st_df)
    pctiles_for_1_in_x = percentiles_for_file[1:]
    lenPercTile = len(pctiles_for_1_in_x)
    nRepeat_for_subsegment = lenDF // lenPercTile

    severity_1_in_x = [
        round(100.0 / (100.0 - p), 1) for p in pctiles_for_1_in_x
    ] * nRepeat_for_subsegment

    result_st_df["Driver"] = "OPEX"
    result_st_df["Scenario Severity (1 in x)"] = severity_1_in_x
    result_st_df["As of Date"] = datetime.now().strftime("%Y-%m-%d")
    result_st_df["Sector"] = sector
    result_st_df["Method"] = "EVT-GPD"

    if segmentByCountry:
        result_st_df["Sub-sector"] = "-"
    else:
        result_st_df["Country"] = "-"

    new_column_order = [
        "Driver",
        "Method",
        "Stress Impact - percentile",
        "Scenario Severity (1 in x)",
        "Sector",
        "Sub-sector",
        "Country",
        "Stress Impact",
        "As of Date",
        "coverage",
        "exception_rate",
        *crisis_columns,
        *error_columns,
    ]

    result_st_df = result_st_df[new_column_order]
    result_st_df = result_st_df.sort_values(
        by=[segmentColumn, "Scenario Severity (1 in x)"], ascending=[False, True]
    )
    result_st_df = result_st_df.reset_index(drop=True)

    # Prepare summary statistics
    summary_all = pd.concat(
        [summary_1, summary_2, summary_3, summary_4, summary_5,
         summary_6, summary_7, summary_8, summary_9],
        ignore_index=True,
    )

    preferred_order = top_segments_with_others

    datapoints_wide = summary_all.pivot(
        index="Step", columns="Region", values="Total datapoints"
    )
    datapoints_wide = datapoints_wide.reindex(columns=preferred_order)
    datapoints_wide = datapoints_wide.fillna(0).astype(int)

    spread_ids_wide = summary_all.pivot(
        index="Step", columns="Region", values="Unique spread IDs"
    )
    spread_ids_wide = spread_ids_wide.reindex(columns=preferred_order)
    spread_ids_wide = spread_ids_wide.fillna(0).astype(int)

    # Dampening summary
    dampening_summary = pd.DataFrame(dampened_counts).reset_index()
    dampening_summary.columns = ["Sub-Segment", "Exclusions from Revenue Model"]
    total_row = pd.DataFrame(
        [["TOTAL", dampening_n]],
        columns=["Sub-Segment", "Exclusions from Revenue Model"],
    )
    dampening_summary = pd.concat([dampening_summary, total_row], ignore_index=True)

    # Model summary (EVT-specific)
    model_summary_data = []
    for segment in top_segments_with_others:
        if segment in evt_model.segment_models:
            model = evt_model.segment_models[segment]
            row_data = {
                'Segment': segment,
                'Method': model['method'],
                'Threshold': model['threshold'],
                'Threshold_Percentile': model['threshold_percentile'] * 100,  # Convert to percentage
                'Shape_Xi': model.get('xi', np.nan),
                'Scale_Sigma': model.get('sigma', np.nan),
                'N_Exceedances': model['n_exceedances'],
                'N_Total': model['n_total'],
                'Exceedance_Rate': model['exceedance_rate']
            }

            # Add threshold selection info if available
            if segment in segment_thresholds:
                row_data['Recommended_Threshold'] = segment_thresholds[segment]['threshold']
                row_data['Recommended_Percentile'] = segment_thresholds[segment]['threshold_percentile']
                row_data['Selection_Method'] = segment_thresholds[segment]['method']

            model_summary_data.append(row_data)

    model_summary_df = pd.DataFrame(model_summary_data)

    # Threshold selection summary (if available)
    if segment_thresholds:
        threshold_selection_summary = []
        for segment, info in segment_thresholds.items():
            threshold_selection_summary.append({
                'Segment': segment,
                'Recommended_Threshold': info['threshold'],
                'Recommended_Percentile': info['threshold_percentile'],
                'N_Exceedances': info['n_exceedances'],
                'Selection_Method': info['method'],
                'Used': 'Yes' if use_auto_threshold else 'No (used fixed threshold)'
            })
        threshold_selection_df = pd.DataFrame(threshold_selection_summary)
    else:
        threshold_selection_df = pd.DataFrame()

    # Write to Excel
    print(f"  Writing to {summary_path}...")

    with pd.ExcelWriter(summary_path, engine="openpyxl") as writer:
        # Data statistics
        datapoints_wide.to_excel(writer, sheet_name="DataStats_Datapoints")
        spread_ids_wide.to_excel(writer, sheet_name="DataStats_SpreadIDs")

        # Dampening
        dampening_summary.to_excel(writer, sheet_name="Exclusions", index=False)
        if not shrink_summary_df.empty:
            shrink_summary_df.to_excel(writer, sheet_name="Outliers_Winsorized", index=False)

        # Threshold selection (if available)
        if not threshold_selection_df.empty:
            threshold_selection_df.to_excel(writer, sheet_name="Threshold_Selection", index=False)

        # EVT model summary
        model_summary_df.to_excel(writer, sheet_name="EVT_Model_Summary", index=False)

        # Full results
        result_df.to_excel(writer, sheet_name="Full_Results_EVT", index=False)

        # Stress impacts
        result_st_df.to_excel(writer, sheet_name="Stress_Impacts_EVT", index=False)

        # Backtesting
        backtesting_df.to_excel(writer, sheet_name="Backtesting_Results", index=False)

        # Raw data (for transparency)
        Opex_clean_rel_exclude[
            [
                "DATE_OF_FINANCIALS",
                id_column_name,
                "TOPS",
                "Year",
                "SLS_REVENUES",
                "Opex",
                "Opex/Revenue",
                "delta_opex/rev",
            ]
        ].to_excel(writer, sheet_name="Model_Data", index=False)

    print(f"  ✓ Saved: {summary_path}")

    # ==================================================================================
    # STEP 9: GENERATE DIAGNOSTIC PLOTS
    # ==================================================================================

    print("\nSTEP 9: Generating diagnostic plots...")

    with PdfPages(diagnostics_pdf_path) as pdf:
        for segment in top_segments_with_others:
            print(f"  Creating diagnostics for {segment}...")

            fig = plot_evt_diagnostics(
                evt_model,
                segment,
                Opex_clean_rel_exclude,
                value_col='delta_opex/rev'
            )

            if fig:
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)

    print(f"  ✓ Saved: {diagnostics_pdf_path}")

    # ==================================================================================
    # STEP 10: GENERATE BACKTESTING PLOTS
    # ==================================================================================

    print("\nSTEP 10: Generating backtesting plots...")

    with PdfPages(backtesting_pdf_path) as pdf:
        for segment in top_segments_with_others:
            print(f"  Creating backtesting plots for {segment}...")

            fig = plot_backtesting_results(
                backtester,
                segment,
                percentiles=percentiles_for_file
            )

            if fig:
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)

    print(f"  ✓ Saved: {backtesting_pdf_path}")

    # ==================================================================================
    # COMPLETION
    # ==================================================================================

    print("\n" + "="*80)
    print(f"✓ OPEX EVT ANALYSIS COMPLETE: {sector_name}")
    print("="*80)
    print(f"\nOutput files saved to: {output_dir}")
    print(f"  - Consolidated results: {os.path.basename(summary_path)}")
    if run_threshold_diagnostics or use_auto_threshold:
        print(f"  - Threshold selection: {os.path.basename(threshold_selection_pdf_path)}")
    print(f"  - Diagnostic plots: {os.path.basename(diagnostics_pdf_path)}")
    print(f"  - Backtesting plots: {os.path.basename(backtesting_pdf_path)}")
    if use_auto_threshold:
        print(f"\n  ℹ Used automated threshold selection for each segment")
    print("\n")


# ==================================================================================
# MAIN EXECUTION
# ==================================================================================

if __name__ == "__main__":
    # List of sectors to process
    sectors_to_process = [
        "Commodity Traders",
        # "O&G",
        # "Metals & Mining",
        # "Automobiles & Components",
        # "Consumer Durables & Apparel",
        # "Technology Hardware & Equipment",
        # "Building Products, Construction & Engineering",
        # "CRE",
        # "Other Capital Goods",
        # "Transportation and Storage",
        # "Global",
    ]

    for sector in sectors_to_process:
        try:
            # Option 1: Use fixed threshold with diagnostics (recommended for first run)
            Opex_EVT(
                sector_name=sector,
                threshold_percentile=0.95,  # 95th percentile threshold
                min_exceedances=30,  # Minimum 30 exceedances for GPD fitting
                run_threshold_diagnostics=True,  # Generate threshold selection plots
                use_auto_threshold=False  # Use fixed threshold (review diagnostics first)
            )

            # Option 2: Use automated threshold selection (after reviewing diagnostics)
            # Uncomment to use:
            # Opex_EVT(
            #     sector_name=sector,
            #     threshold_percentile=0.95,  # Ignored when use_auto_threshold=True
            #     min_exceedances=30,
            #     run_threshold_diagnostics=True,  # Still generate diagnostic plots
            #     use_auto_threshold=True  # Use optimal threshold per segment
            # )

            # Option 3: Skip threshold diagnostics for faster execution
            # Uncomment to use:
            # Opex_EVT(
            #     sector_name=sector,
            #     threshold_percentile=0.95,
            #     min_exceedances=30,
            #     run_threshold_diagnostics=False,  # Skip threshold selection plots
            #     use_auto_threshold=False
            # )

            sys.stdout = TimestampLog("Opex_EVT_master")
        except Exception as e:
            print(f"\n{'='*80}")
            print(f"ERROR processing {sector}: {e}")
            print(f"{'='*80}\n")
            import traceback
            traceback.print_exc()
            continue
