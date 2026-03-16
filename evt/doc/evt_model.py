"""
Extreme Value Theory (EVT) Model Implementation
For Opex Stress Testing

This module provides GPD-based tail modeling and backtesting functionality.
"""

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
from typing import Tuple, Dict, Optional, List
import warnings

warnings.filterwarnings('ignore')


class GPDModel:
    """
    Generalized Pareto Distribution model for Extreme Value Theory

    Uses Peaks Over Threshold (POT) method to model tail distributions.
    Ideal for stress testing and risk modeling at high percentiles (95th+).
    """

    def __init__(
        self,
        data: np.ndarray,
        threshold: Optional[float] = None,
        threshold_quantile: float = 0.90
    ):
        """
        Initialize GPD model

        Parameters:
        -----------
        data : np.ndarray
            Data series (e.g., delta_opex/rev)
        threshold : float, optional
            Absolute threshold value. If None, uses threshold_quantile
        threshold_quantile : float
            Quantile to use as threshold (default 0.90 = 90th percentile)

        Notes:
        ------
        - Typical thresholds: 0.85-0.95
        - Higher threshold = fewer data points but better tail fit
        - Lower threshold = more data but potential bias
        """
        self.data = np.array(data)
        self.data_clean = self.data[~np.isnan(self.data)]

        # Set threshold
        if threshold is None:
            self.threshold = np.quantile(self.data_clean, threshold_quantile)
        else:
            self.threshold = threshold

        # Extract exceedances (values above threshold)
        self.exceedances = self.data_clean[self.data_clean > self.threshold] - self.threshold
        self.n_exceedances = len(self.exceedances)
        self.n_total = len(self.data_clean)

        # GPD parameters (to be fitted)
        self.shape = None  # ξ (xi) - tail index
        self.scale = None  # σ (sigma) - scale parameter

        # Validation
        if self.n_exceedances < 10:
            warnings.warn(
                f"Very few exceedances ({self.n_exceedances}). "
                "Consider lowering threshold or using empirical percentiles."
            )

    def fit(self) -> Tuple[float, float]:
        """
        Fit GPD parameters using Maximum Likelihood Estimation

        Returns:
        --------
        shape, scale : Tuple[float, float]
            Fitted GPD parameters

        Notes:
        ------
        Shape parameter interpretation:
        - ξ > 0: Heavy tail (Fréchet) - extreme values more likely
        - ξ = 0: Exponential tail (Gumbel) - moderate tail
        - ξ < 0: Light tail (Weibull) - bounded distribution
        """
        # scipy.stats.genpareto uses (c, loc, scale) where c = shape
        self.shape, loc, self.scale = stats.genpareto.fit(self.exceedances, floc=0)

        return self.shape, self.scale

    def quantile(self, p: float) -> float:
        """
        Calculate quantile of the full distribution

        Parameters:
        -----------
        p : float
            Quantile level between 0 and 1 (e.g., 0.96 for 96th percentile)

        Returns:
        --------
        q : float
            Quantile value

        Raises:
        -------
        ValueError
            If model hasn't been fitted yet
        """
        if self.shape is None or self.scale is None:
            raise ValueError("Model must be fitted first. Call .fit()")

        # Probability of exceeding threshold
        p_u = self.n_exceedances / self.n_total

        if p <= (1 - p_u):
            # Below threshold - use empirical quantile
            return np.quantile(self.data_clean, p)
        else:
            # Above threshold - use GPD
            p_conditional = (p - (1 - p_u)) / p_u

            if abs(self.shape) < 1e-6:
                # shape ≈ 0: Exponential distribution limit
                q_excess = -self.scale * np.log(1 - p_conditional)
            else:
                # General GPD formula
                q_excess = (self.scale / self.shape) * (
                    (1 - p_conditional)**(-self.shape) - 1
                )

            return self.threshold + q_excess

    def return_level(self, return_period: int) -> float:
        """
        Calculate return level for a given return period

        Parameters:
        -----------
        return_period : int
            Return period in years (e.g., 25 for 1-in-25 year event)

        Returns:
        --------
        level : float
            Return level corresponding to the return period

        Example:
        --------
        >>> model.return_level(25)  # 1-in-25 year event (96th percentile)
        """
        p = 1 - 1/return_period
        return self.quantile(p)

    def confidence_interval(
        self,
        p: float,
        confidence: float = 0.95,
        n_bootstrap: int = 1000
    ) -> Tuple[float, float]:
        """
        Calculate confidence interval for quantile using bootstrap

        Parameters:
        -----------
        p : float
            Quantile level
        confidence : float
            Confidence level (default 0.95 for 95% CI)
        n_bootstrap : int
            Number of bootstrap samples (default 1000)

        Returns:
        --------
        lower, upper : Tuple[float, float]
            Confidence interval bounds
        """
        quantiles = []

        for _ in range(n_bootstrap):
            # Resample with replacement
            sample = np.random.choice(
                self.data_clean,
                size=len(self.data_clean),
                replace=True
            )

            # Fit GPD to bootstrap sample
            try:
                boot_model = GPDModel(sample, threshold=self.threshold)
                boot_model.fit()
                quantiles.append(boot_model.quantile(p))
            except:
                continue

        alpha = 1 - confidence
        lower = np.quantile(quantiles, alpha/2)
        upper = np.quantile(quantiles, 1 - alpha/2)

        return lower, upper

    def diagnostic_plots(self, figsize: Tuple[int, int] = (15, 10)):
        """
        Generate diagnostic plots to assess model fit

        Parameters:
        -----------
        figsize : Tuple[int, int]
            Figure size (width, height)

        Returns:
        --------
        fig : matplotlib.figure.Figure
            Figure object containing diagnostic plots

        Plots:
        ------
        1. Probability Plot: Should follow 45° line if fit is good
        2. Q-Q Plot: Quantile-quantile comparison
        3. Density Plot: Empirical vs fitted density
        4. Return Level Plot: Extrapolation to extreme events
        """
        if self.shape is None or self.scale is None:
            raise ValueError("Model must be fitted first. Call .fit()")

        fig, axes = plt.subplots(2, 2, figsize=figsize)

        # 1. Probability plot
        ax = axes[0, 0]
        sorted_exceedances = np.sort(self.exceedances)
        n = len(sorted_exceedances)
        empirical_p = np.arange(1, n + 1) / (n + 1)
        theoretical_quantiles = stats.genpareto.ppf(
            empirical_p, self.shape, scale=self.scale
        )
        ax.scatter(theoretical_quantiles, sorted_exceedances, alpha=0.5, s=20)
        lim = max(theoretical_quantiles.max(), sorted_exceedances.max())
        ax.plot([0, lim], [0, lim], 'r--', linewidth=2, label='Perfect fit')
        ax.set_xlabel('Theoretical Quantiles')
        ax.set_ylabel('Empirical Quantiles')
        ax.set_title('Probability Plot')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # 2. Q-Q plot
        ax = axes[0, 1]
        model_quantiles = stats.genpareto.ppf(
            empirical_p, self.shape, scale=self.scale
        )
        ax.scatter(model_quantiles, sorted_exceedances, alpha=0.5, s=20)
        ax.plot([0, lim], [0, lim], 'r--', linewidth=2, label='Perfect fit')
        ax.set_xlabel('Model Quantiles')
        ax.set_ylabel('Empirical Quantiles')
        ax.set_title('Q-Q Plot')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # 3. Density plot
        ax = axes[1, 0]
        ax.hist(self.exceedances, bins=30, density=True, alpha=0.6,
                color='skyblue', edgecolor='black', label='Empirical')
        x_plot = np.linspace(0, max(self.exceedances), 200)
        pdf = stats.genpareto.pdf(x_plot, self.shape, scale=self.scale)
        ax.plot(x_plot, pdf, 'r-', linewidth=2, label='GPD Fit')
        ax.set_xlabel('Exceedances')
        ax.set_ylabel('Density')
        ax.set_title('Density Plot')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # 4. Return level plot
        ax = axes[1, 1]
        return_periods = np.logspace(0, 2.5, 100)  # 1 to ~316 years
        return_levels = [self.return_level(rp) for rp in return_periods]
        ax.semilogx(return_periods, return_levels, 'b-', linewidth=2)

        # Add reference lines for common return periods
        common_rps = [10, 25, 50, 100]
        for rp in common_rps:
            rl = self.return_level(rp)
            ax.scatter([rp], [rl], s=100, c='red', zorder=5)
            ax.annotate(f'{rp}yr', xy=(rp, rl), xytext=(10, 10),
                       textcoords='offset points', fontsize=9)

        ax.set_xlabel('Return Period (years)')
        ax.set_ylabel('Return Level')
        ax.set_title('Return Level Plot')
        ax.grid(True, alpha=0.3, which='both')

        plt.tight_layout()
        return fig

    def summary(self) -> Dict:
        """
        Return summary statistics of the model

        Returns:
        --------
        summary : Dict
            Dictionary containing key model parameters and quantiles
        """
        if self.shape is None or self.scale is None:
            raise ValueError("Model must be fitted first. Call .fit()")

        # Determine tail type
        if self.shape > 0.1:
            tail_type = 'Heavy tail (Fréchet)'
        elif self.shape < -0.1:
            tail_type = 'Light tail (Weibull)'
        else:
            tail_type = 'Exponential tail (Gumbel)'

        return {
            'threshold': self.threshold,
            'n_total': self.n_total,
            'n_exceedances': self.n_exceedances,
            'exceedance_rate': self.n_exceedances / self.n_total,
            'shape_parameter': self.shape,
            'scale_parameter': self.scale,
            'tail_type': tail_type,
            '80th_percentile': self.quantile(0.80),
            '90th_percentile': self.quantile(0.90),
            '96th_percentile': self.quantile(0.96),
            '99th_percentile': self.quantile(0.99),
            '1_in_10_year': self.return_level(10),
            '1_in_25_year': self.return_level(25),
            '1_in_50_year': self.return_level(50),
            '1_in_100_year': self.return_level(100),
        }

    def __repr__(self) -> str:
        if self.shape is None:
            return f"GPDModel(threshold={self.threshold:.4f}, n_exceedances={self.n_exceedances}, fitted=False)"
        else:
            return (f"GPDModel(threshold={self.threshold:.4f}, "
                   f"shape={self.shape:.4f}, scale={self.scale:.4f}, "
                   f"n_exceedances={self.n_exceedances})")


def mean_excess_plot(data: np.ndarray, thresholds: Optional[List[float]] = None,
                     figsize: Tuple[int, int] = (10, 6)):
    """
    Generate Mean Excess Plot to help select threshold

    If the plot shows a roughly linear increasing trend above some threshold,
    that's a good indicator for GPD applicability at that threshold.

    Parameters:
    -----------
    data : np.ndarray
        Data series
    thresholds : List[float], optional
        Specific thresholds to test. If None, uses percentiles from 50th to 98th
    figsize : Tuple[int, int]
        Figure size

    Returns:
    --------
    fig : matplotlib.figure.Figure
        Figure object
    """
    data_clean = data[~np.isnan(data)]

    if thresholds is None:
        thresholds = np.percentile(data_clean, np.linspace(50, 98, 50))

    mean_excesses = []
    counts = []

    for u in thresholds:
        exceedances = data_clean[data_clean > u] - u
        if len(exceedances) > 0:
            mean_excesses.append(exceedances.mean())
            counts.append(len(exceedances))
        else:
            mean_excesses.append(np.nan)
            counts.append(0)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    # Mean excess plot
    ax1.plot(thresholds, mean_excesses, 'b-', linewidth=2)
    ax1.scatter(thresholds, mean_excesses, c=counts, cmap='viridis', s=30)
    ax1.set_xlabel('Threshold')
    ax1.set_ylabel('Mean Excess')
    ax1.set_title('Mean Excess Plot\n(Look for linear trend)')
    ax1.grid(True, alpha=0.3)

    # Count of exceedances
    ax2.plot(thresholds, counts, 'r-', linewidth=2)
    ax2.set_xlabel('Threshold')
    ax2.set_ylabel('Number of Exceedances')
    ax2.set_title('Exceedance Count')
    ax2.grid(True, alpha=0.3)

    # Add reference line for common thresholds
    for pct in [0.90, 0.95]:
        thresh = np.percentile(data_clean, pct * 100)
        ax1.axvline(thresh, color='green', linestyle='--', alpha=0.5,
                   label=f'{int(pct*100)}th %ile')
        ax2.axvline(thresh, color='green', linestyle='--', alpha=0.5)

    ax1.legend()
    plt.tight_layout()

    return fig


if __name__ == "__main__":
    # Example usage
    print("EVT Model Module")
    print("=" * 80)
    print("\nThis module provides GPD-based tail modeling for stress testing.")
    print("\nExample usage:")
    print("""
    from evt_model import GPDModel

    # Fit model
    model = GPDModel(data, threshold_quantile=0.90)
    model.fit()

    # Get quantiles
    p96 = model.quantile(0.96)
    p99 = model.quantile(0.99)

    # Get return level
    one_in_25 = model.return_level(25)

    # Confidence interval
    ci_lower, ci_upper = model.confidence_interval(0.96)

    # Summary
    summary = model.summary()

    # Diagnostic plots
    fig = model.diagnostic_plots()
    """)
