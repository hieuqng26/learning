"""
EVT Backtesting Module

Provides out-of-sample backtesting functionality for EVT models
with proper walk-forward validation.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
import matplotlib.pyplot as plt
from evt_model import GPDModel
import warnings

warnings.filterwarnings('ignore')


class EVTBacktester:
    """
    Backtest EVT models using walk-forward validation

    This class implements proper out-of-sample testing by:
    1. Training on historical data BEFORE a test period
    2. Forecasting stress levels
    3. Comparing to actual outcomes in test period
    """

    def __init__(
        self,
        data: pd.DataFrame,
        date_col: str,
        value_col: str,
        group_col: Optional[str] = None
    ):
        """
        Initialize backtester

        Parameters:
        -----------
        data : pd.DataFrame
            Panel data with dates and values
        date_col : str
            Name of date column
        value_col : str
            Name of value column (e.g., 'delta_opex/rev')
        group_col : str, optional
            Name of grouping column (e.g., 'TOPS' for sub-sectors)
        """
        self.data = data.copy()
        self.date_col = date_col
        self.value_col = value_col
        self.group_col = group_col

        # Extract year if not already present
        if 'Year' not in self.data.columns:
            self.data['Year'] = pd.to_datetime(self.data[date_col]).dt.year

    def backtest_crisis_year(
        self,
        crisis_year: int,
        training_years: int = 10,
        test_percentiles: List[float] = None,
        threshold_quantile: float = 0.90,
        compute_ci: bool = True
    ) -> pd.DataFrame:
        """
        Backtest a specific crisis year (e.g., 2008, 2009)

        Parameters:
        -----------
        crisis_year : int
            Year to test (e.g., 2008)
        training_years : int
            Number of years before crisis to use for training
        test_percentiles : List[float], optional
            Percentiles to evaluate (default [0.80, 0.90, 0.96, 0.99])
        threshold_quantile : float
            Threshold for GPD fitting (default 0.90)
        compute_ci : bool
            Whether to compute confidence intervals (default True)

        Returns:
        --------
        results : pd.DataFrame
            Comparison of forecasted vs actual values with errors
        """
        if test_percentiles is None:
            test_percentiles = [0.80, 0.90, 0.96, 0.99]

        # Split data: training up to crisis year, test = crisis year
        train_start = crisis_year - training_years
        train_data = self.data[
            (self.data['Year'] >= train_start) &
            (self.data['Year'] < crisis_year)
        ]
        test_data = self.data[self.data['Year'] == crisis_year]

        results = []

        # Determine groups
        if self.group_col:
            groups = train_data[self.group_col].unique()
        else:
            groups = [None]

        for group in groups:
            # Filter by group
            if group is not None:
                train_subset = train_data[
                    train_data[self.group_col] == group
                ][self.value_col].dropna()
                test_subset = test_data[
                    test_data[self.group_col] == group
                ][self.value_col].dropna()
            else:
                train_subset = train_data[self.value_col].dropna()
                test_subset = test_data[self.value_col].dropna()

            # Skip if insufficient data
            if len(train_subset) < 50 or len(test_subset) == 0:
                continue

            # Fit EVT model on training data
            try:
                evt_model = GPDModel(
                    train_subset.values,
                    threshold_quantile=threshold_quantile
                )
                evt_model.fit()

                # Initialize result dict
                result = {
                    'Group': group if group else 'All',
                    'Crisis_Year': crisis_year,
                    'Train_Start': train_start,
                    'Train_N': len(train_subset),
                    'Test_N': len(test_subset),
                    'Actual_Mean': test_subset.mean(),
                    'Actual_Median': test_subset.median(),
                    'Actual_Std': test_subset.std(),
                    'EVT_Shape': evt_model.shape,
                    'EVT_Scale': evt_model.scale,
                    'EVT_Threshold': evt_model.threshold,
                }

                # Calculate forecasts and actuals for each percentile
                for p in test_percentiles:
                    p_str = f'{int(p*100)}th'

                    # EVT forecast from training data
                    forecast = evt_model.quantile(p)
                    result[f'EVT_{p_str}'] = forecast

                    # Empirical percentile from training data (for comparison)
                    empirical_forecast = train_subset.quantile(p)
                    result[f'Empirical_{p_str}'] = empirical_forecast

                    # Actual from test data
                    actual = test_subset.quantile(p)
                    result[f'Actual_{p_str}'] = actual

                    # Errors
                    evt_error = actual - forecast
                    empirical_error = actual - empirical_forecast

                    result[f'EVT_Error_{p_str}'] = evt_error
                    result[f'Empirical_Error_{p_str}'] = empirical_error
                    result[f'EVT_AbsError_{p_str}'] = abs(evt_error)
                    result[f'Empirical_AbsError_{p_str}'] = abs(empirical_error)

                    # Relative error (as %)
                    if actual != 0:
                        result[f'EVT_RelError_{p_str}'] = (evt_error / actual) * 100
                        result[f'Empirical_RelError_{p_str}'] = (empirical_error / actual) * 100
                    else:
                        result[f'EVT_RelError_{p_str}'] = np.nan
                        result[f'Empirical_RelError_{p_str}'] = np.nan

                    # Confidence intervals (if requested)
                    if compute_ci:
                        try:
                            ci_lower, ci_upper = evt_model.confidence_interval(
                                p, confidence=0.95, n_bootstrap=500
                            )
                            result[f'EVT_{p_str}_CI_Lower'] = ci_lower
                            result[f'EVT_{p_str}_CI_Upper'] = ci_upper

                            # Check if actual falls within CI
                            coverage = (ci_lower <= actual <= ci_upper)
                            result[f'Coverage_{p_str}'] = coverage
                        except:
                            result[f'EVT_{p_str}_CI_Lower'] = np.nan
                            result[f'EVT_{p_str}_CI_Upper'] = np.nan
                            result[f'Coverage_{p_str}'] = np.nan

                # Which method performed better?
                evt_avg_abs_error = np.mean([
                    result[f'EVT_AbsError_{int(p*100)}th'] for p in test_percentiles
                ])
                empirical_avg_abs_error = np.mean([
                    result[f'Empirical_AbsError_{int(p*100)}th'] for p in test_percentiles
                ])

                result['EVT_AvgAbsError'] = evt_avg_abs_error
                result['Empirical_AvgAbsError'] = empirical_avg_abs_error
                result['EVT_Outperforms'] = evt_avg_abs_error < empirical_avg_abs_error

                results.append(result)

            except Exception as e:
                print(f"Error fitting {group}: {e}")
                continue

        return pd.DataFrame(results)

    def walk_forward_backtest(
        self,
        start_year: int,
        end_year: int,
        training_years: int = 10,
        step: int = 1,
        test_percentiles: List[float] = None
    ) -> pd.DataFrame:
        """
        Perform walk-forward backtesting across multiple years

        Parameters:
        -----------
        start_year : int
            First year to test
        end_year : int
            Last year to test
        training_years : int
            Training window size
        step : int
            Step size for moving window (default 1 = test every year)
        test_percentiles : List[float], optional
            Percentiles to evaluate

        Returns:
        --------
        results : pd.DataFrame
            Backtesting results across all periods
        """
        all_results = []

        for year in range(start_year, end_year + 1, step):
            print(f"Backtesting year {year}...")
            year_results = self.backtest_crisis_year(
                year,
                training_years,
                test_percentiles
            )
            all_results.append(year_results)

        return pd.concat(all_results, ignore_index=True)

    def compare_methods(
        self,
        crisis_year: int,
        training_years: int = 10
    ) -> pd.DataFrame:
        """
        Compare EVT vs Empirical Percentiles in a clean format

        Parameters:
        -----------
        crisis_year : int
            Year to test
        training_years : int
            Training window size

        Returns:
        --------
        comparison : pd.DataFrame
            Side-by-side comparison of methods
        """
        train_start = crisis_year - training_years
        train_data = self.data[
            (self.data['Year'] >= train_start) &
            (self.data['Year'] < crisis_year)
        ]
        test_data = self.data[self.data['Year'] == crisis_year]

        results = []
        test_percentiles = [0.80, 0.90, 0.96, 0.99]

        groups = (
            train_data[self.group_col].unique()
            if self.group_col else [None]
        )

        for group in groups:
            if group is not None:
                train_subset = train_data[
                    train_data[self.group_col] == group
                ][self.value_col].dropna()
                test_subset = test_data[
                    test_data[self.group_col] == group
                ][self.value_col].dropna()
            else:
                train_subset = train_data[self.value_col].dropna()
                test_subset = test_data[self.value_col].dropna()

            if len(train_subset) < 50 or len(test_subset) == 0:
                continue

            try:
                # EVT Model
                evt_model = GPDModel(train_subset.values, threshold_quantile=0.90)
                evt_model.fit()

                for p in test_percentiles:
                    # EVT forecast
                    evt_forecast = evt_model.quantile(p)

                    # Empirical percentile from training data
                    empirical_forecast = train_subset.quantile(p)

                    # Actual from test data
                    actual = test_subset.quantile(p)

                    # Errors
                    evt_error = actual - evt_forecast
                    empirical_error = actual - empirical_forecast

                    results.append({
                        'Group': group if group else 'All',
                        'Crisis_Year': crisis_year,
                        'Percentile': f'{int(p*100)}th',
                        'Percentile_Value': p,
                        'EVT_Forecast': evt_forecast,
                        'Empirical_Forecast': empirical_forecast,
                        'Actual': actual,
                        'EVT_Error': evt_error,
                        'Empirical_Error': empirical_error,
                        'EVT_AbsError': abs(evt_error),
                        'Empirical_AbsError': abs(empirical_error),
                        'EVT_Better': abs(evt_error) < abs(empirical_error),
                        'Train_N': len(train_subset),
                        'Test_N': len(test_subset),
                    })

            except Exception as e:
                print(f"Error for {group}: {e}")
                continue

        return pd.DataFrame(results)

    def plot_backtest_results(
        self,
        backtest_df: pd.DataFrame,
        percentile: str = '96th',
        figsize: Tuple[int, int] = (14, 8)
    ):
        """
        Visualize backtest results

        Parameters:
        -----------
        backtest_df : pd.DataFrame
            Results from backtest_crisis_year()
        percentile : str
            Which percentile to plot (e.g., '96th', '99th')
        figsize : Tuple[int, int]
            Figure size

        Returns:
        --------
        fig : matplotlib.figure.Figure
            Figure object
        """
        fig, axes = plt.subplots(2, 2, figsize=figsize)

        # Prepare data
        groups = backtest_df['Group'].values
        actual = backtest_df[f'Actual_{percentile}'].values
        evt_forecast = backtest_df[f'EVT_{percentile}'].values
        empirical_forecast = backtest_df[f'Empirical_{percentile}'].values

        # 1. Forecast vs Actual
        ax = axes[0, 0]
        x = np.arange(len(groups))
        width = 0.25
        ax.bar(x - width, actual, width, label='Actual', color='black', alpha=0.7)
        ax.bar(x, evt_forecast, width, label='EVT Forecast', color='blue', alpha=0.7)
        ax.bar(x + width, empirical_forecast, width, label='Empirical', color='green', alpha=0.7)
        ax.set_xlabel('Group')
        ax.set_ylabel(f'{percentile} Percentile Value')
        ax.set_title(f'Forecast vs Actual ({percentile} Percentile)')
        ax.set_xticks(x)
        ax.set_xticklabels(groups, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')

        # 2. Errors comparison
        ax = axes[0, 1]
        evt_errors = backtest_df[f'EVT_AbsError_{percentile}'].values
        empirical_errors = backtest_df[f'Empirical_AbsError_{percentile}'].values
        ax.bar(x - width/2, evt_errors, width, label='EVT Error', color='blue', alpha=0.7)
        ax.bar(x + width/2, empirical_errors, width, label='Empirical Error', color='green', alpha=0.7)
        ax.set_xlabel('Group')
        ax.set_ylabel('Absolute Error')
        ax.set_title('Absolute Forecast Errors')
        ax.set_xticks(x)
        ax.set_xticklabels(groups, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')

        # 3. Scatter: EVT forecast vs Actual
        ax = axes[1, 0]
        ax.scatter(evt_forecast, actual, s=100, alpha=0.6, color='blue')
        for i, group in enumerate(groups):
            ax.annotate(group, (evt_forecast[i], actual[i]),
                       fontsize=8, alpha=0.7)
        lim = [
            min(evt_forecast.min(), actual.min()),
            max(evt_forecast.max(), actual.max())
        ]
        ax.plot(lim, lim, 'r--', linewidth=2, label='Perfect forecast')
        ax.set_xlabel('EVT Forecast')
        ax.set_ylabel('Actual')
        ax.set_title('EVT: Forecast vs Actual')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # 4. Coverage indicator (if available)
        ax = axes[1, 1]
        if f'Coverage_{percentile}' in backtest_df.columns:
            coverage = backtest_df[f'Coverage_{percentile}'].values
            colors = ['green' if c else 'red' for c in coverage]
            ax.bar(x, coverage, color=colors, alpha=0.7)
            ax.set_xlabel('Group')
            ax.set_ylabel('Within 95% CI')
            ax.set_title('95% Confidence Interval Coverage')
            ax.set_xticks(x)
            ax.set_xticklabels(groups, rotation=45, ha='right')
            ax.set_ylim([0, 1.2])
            ax.grid(True, alpha=0.3, axis='y')
        else:
            # Error improvement plot
            improvement = ((empirical_errors - evt_errors) / empirical_errors) * 100
            colors = ['green' if i > 0 else 'red' for i in improvement]
            ax.bar(x, improvement, color=colors, alpha=0.7)
            ax.axhline(0, color='black', linewidth=1)
            ax.set_xlabel('Group')
            ax.set_ylabel('Error Reduction (%)')
            ax.set_title('EVT Improvement over Empirical (%)')
            ax.set_xticks(x)
            ax.set_xticklabels(groups, rotation=45, ha='right')
            ax.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        return fig


def print_backtest_summary(backtest_df: pd.DataFrame, percentile: str = '96th'):
    """
    Print a formatted summary of backtest results

    Parameters:
    -----------
    backtest_df : pd.DataFrame
        Results from EVTBacktester
    percentile : str
        Which percentile to summarize
    """
    print("\n" + "="*80)
    print(f"BACKTEST SUMMARY - {percentile} PERCENTILE")
    print("="*80)

    for _, row in backtest_df.iterrows():
        group = row['Group']
        year = row['Crisis_Year']

        print(f"\n{group} ({year}):")
        print(f"  Training: {row['Train_Start']}-{year-1} (N={row['Train_N']})")
        print(f"  Test: {year} (N={row['Test_N']})")
        print(f"\n  Forecasts:")
        print(f"    EVT:       {row[f'EVT_{percentile}']:>8.4f}")
        print(f"    Empirical: {row[f'Empirical_{percentile}']:>8.4f}")
        print(f"    Actual:    {row[f'Actual_{percentile}']:>8.4f}")
        print(f"\n  Errors:")
        print(f"    EVT:       {row[f'EVT_Error_{percentile}']:>8.4f} "
              f"(abs: {row[f'EVT_AbsError_{percentile}']:.4f})")
        print(f"    Empirical: {row[f'Empirical_Error_{percentile}']:>8.4f} "
              f"(abs: {row[f'Empirical_AbsError_{percentile}']:.4f})")

        if row['EVT_Outperforms']:
            print(f"  ✓ EVT outperforms empirical method")
        else:
            print(f"  ✗ Empirical method outperforms EVT")

    # Overall statistics
    print("\n" + "-"*80)
    print("OVERALL STATISTICS:")
    print(f"  EVT Avg Absolute Error:       {backtest_df[f'EVT_AbsError_{percentile}'].mean():.4f}")
    print(f"  Empirical Avg Absolute Error: {backtest_df[f'Empirical_AbsError_{percentile}'].mean():.4f}")
    print(f"  EVT Wins: {backtest_df['EVT_Outperforms'].sum()} / {len(backtest_df)}")

    if f'Coverage_{percentile}' in backtest_df.columns:
        coverage_rate = backtest_df[f'Coverage_{percentile}'].mean()
        print(f"  95% CI Coverage Rate: {coverage_rate:.1%}")

    print("="*80)


if __name__ == "__main__":
    print("EVT Backtesting Module")
    print("="*80)
    print("\nThis module provides out-of-sample backtesting for EVT models.")
    print("\nExample usage:")
    print("""
    from evt_backtest import EVTBacktester

    # Initialize backtester
    backtester = EVTBacktester(
        data=opex_data,
        date_col='DATE_OF_FINANCIALS',
        value_col='delta_opex/rev',
        group_col='TOPS'
    )

    # Backtest 2008 crisis
    results_2008 = backtester.backtest_crisis_year(
        crisis_year=2008,
        training_years=10
    )

    # Walk-forward backtest
    results_all = backtester.walk_forward_backtest(
        start_year=2008,
        end_year=2020,
        training_years=10
    )

    # Compare methods
    comparison = backtester.compare_methods(crisis_year=2008)

    # Visualize
    fig = backtester.plot_backtest_results(results_2008)
    """)
