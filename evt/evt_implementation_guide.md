# Extreme Value Theory (EVT) Implementation Guide for Opex Stress Testing

## Overview

EVT is specifically designed to model tail events (extremes), making it ideal for stress testing where you care about 96th, 99th percentiles and beyond.

### Two Main EVT Approaches

1. **Block Maxima Method (GEV - Generalized Extreme Value)**
   - Takes maximum value from each time block (e.g., annual max)
   - Fits GEV distribution to these maxima
   - Good when you have long time series

2. **Peaks Over Threshold (POT/GPD - Generalized Pareto Distribution)**
   - Models exceedances above a high threshold
   - More data-efficient (uses all extreme values, not just maxima)
   - **Recommended for your use case**

---

## Why EVT for Opex Stress Testing?

### Current Model Limitations
- Empirical percentiles are unreliable at extremes (few observations at 99th percentile)
- Can't extrapolate beyond observed data
- Vulnerable to outliers

### EVT Advantages
- ✅ Statistically rigorous tail modeling
- ✅ Can extrapolate to 99.5th, 99.9th percentiles
- ✅ Provides confidence intervals
- ✅ Backed by mathematical theory (Fisher-Tippett-Gnedenko theorem)

---

## Implementation: Peaks Over Threshold (POT/GPD)

### Step 1: Install Required Libraries

```bash
pip install scipy numpy pandas matplotlib
# Optional: For advanced EVT
pip install pyextremes
```

### Step 2: Core EVT Functions

```python
import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import minimize
import matplotlib.pyplot as plt
from typing import Tuple, Dict

class GPDModel:
    """
    Generalized Pareto Distribution model for EVT analysis
    """

    def __init__(self, data: np.array, threshold: float = None, threshold_quantile: float = 0.90):
        """
        Initialize GPD model

        Parameters:
        -----------
        data : array-like
            The data series (e.g., delta_opex/rev)
        threshold : float
            Absolute threshold value (if None, uses threshold_quantile)
        threshold_quantile : float
            Quantile to use as threshold (default 0.90 = 90th percentile)
        """
        self.data = np.array(data)
        self.data_clean = self.data[~np.isnan(self.data)]

        # Set threshold
        if threshold is None:
            self.threshold = np.quantile(self.data_clean, threshold_quantile)
        else:
            self.threshold = threshold

        # Extract exceedances
        self.exceedances = self.data_clean[self.data_clean > self.threshold] - self.threshold
        self.n_exceedances = len(self.exceedances)
        self.n_total = len(self.data_clean)

        # Fit parameters
        self.shape = None  # xi (ξ)
        self.scale = None  # sigma (σ)

    def fit(self, method='mle'):
        """
        Fit GPD parameters using Maximum Likelihood Estimation

        Returns:
        --------
        shape, scale : float
            Fitted GPD parameters
        """
        if method == 'mle':
            # Use scipy's built-in GPD fit
            # Note: scipy uses (c, loc, scale) where c = -shape
            self.shape, loc, self.scale = stats.genpareto.fit(self.exceedances, floc=0)

        return self.shape, self.scale

    def quantile(self, p: float) -> float:
        """
        Calculate quantile of the full distribution

        Parameters:
        -----------
        p : float
            Quantile level (e.g., 0.96 for 96th percentile)

        Returns:
        --------
        q : float
            Quantile value
        """
        if self.shape is None or self.scale is None:
            raise ValueError("Model must be fitted first. Call .fit()")

        # Probability of exceeding threshold
        p_u = self.n_exceedances / self.n_total

        # Quantile of exceedances
        if p <= (1 - p_u):
            # Below threshold - use empirical quantile
            return np.quantile(self.data_clean, p)
        else:
            # Above threshold - use GPD
            p_conditional = (p - (1 - p_u)) / p_u

            if abs(self.shape) < 1e-6:
                # shape ≈ 0: Exponential distribution
                q_excess = -self.scale * np.log(1 - p_conditional)
            else:
                q_excess = (self.scale / self.shape) * ((1 - p_conditional)**(-self.shape) - 1)

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
            Return level
        """
        p = 1 - 1/return_period
        return self.quantile(p)

    def confidence_interval(self, p: float, confidence: float = 0.95, n_bootstrap: int = 1000) -> Tuple[float, float]:
        """
        Calculate confidence interval for quantile using bootstrap

        Parameters:
        -----------
        p : float
            Quantile level
        confidence : float
            Confidence level (default 0.95)
        n_bootstrap : int
            Number of bootstrap samples

        Returns:
        --------
        lower, upper : float
            Confidence interval bounds
        """
        quantiles = []

        for _ in range(n_bootstrap):
            # Resample with replacement
            sample = np.random.choice(self.data_clean, size=len(self.data_clean), replace=True)

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

    def diagnostic_plots(self, figsize=(15, 10)):
        """
        Generate diagnostic plots to assess model fit
        """
        fig, axes = plt.subplots(2, 2, figsize=figsize)

        # 1. Probability plot
        ax = axes[0, 0]
        sorted_exceedances = np.sort(self.exceedances)
        theoretical_quantiles = stats.genpareto.ppf(
            np.linspace(0.01, 0.99, len(sorted_exceedances)),
            self.shape, scale=self.scale
        )
        ax.scatter(theoretical_quantiles, sorted_exceedances, alpha=0.5)
        ax.plot([0, max(theoretical_quantiles)], [0, max(theoretical_quantiles)], 'r--')
        ax.set_xlabel('Theoretical Quantiles')
        ax.set_ylabel('Empirical Quantiles')
        ax.set_title('Probability Plot')
        ax.grid(True, alpha=0.3)

        # 2. Quantile plot
        ax = axes[0, 1]
        empirical_p = np.linspace(0.01, 0.99, len(sorted_exceedances))
        model_quantiles = stats.genpareto.ppf(empirical_p, self.shape, scale=self.scale)
        ax.scatter(model_quantiles, sorted_exceedances, alpha=0.5)
        ax.plot([0, max(model_quantiles)], [0, max(model_quantiles)], 'r--')
        ax.set_xlabel('Model Quantiles')
        ax.set_ylabel('Empirical Quantiles')
        ax.set_title('Q-Q Plot')
        ax.grid(True, alpha=0.3)

        # 3. Density plot
        ax = axes[1, 0]
        ax.hist(self.exceedances, bins=30, density=True, alpha=0.5, label='Empirical')
        x_plot = np.linspace(0, max(self.exceedances), 100)
        ax.plot(x_plot, stats.genpareto.pdf(x_plot, self.shape, scale=self.scale), 'r-', label='GPD Fit')
        ax.set_xlabel('Exceedances')
        ax.set_ylabel('Density')
        ax.set_title('Density Plot')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # 4. Return level plot
        ax = axes[1, 1]
        return_periods = np.logspace(0, 2, 50)  # 1 to 100 years
        return_levels = [self.return_level(rp) for rp in return_periods]
        ax.semilogx(return_periods, return_levels, 'b-', linewidth=2)
        ax.set_xlabel('Return Period (years)')
        ax.set_ylabel('Return Level')
        ax.set_title('Return Level Plot')
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    def summary(self) -> Dict:
        """
        Return summary statistics of the model
        """
        return {
            'threshold': self.threshold,
            'n_exceedances': self.n_exceedances,
            'exceedance_rate': self.n_exceedances / self.n_total,
            'shape_parameter': self.shape,
            'scale_parameter': self.scale,
            'tail_type': 'Heavy tail' if self.shape > 0 else 'Light tail' if self.shape < 0 else 'Exponential',
            '96th_percentile': self.quantile(0.96),
            '99th_percentile': self.quantile(0.99),
            '1_in_25_year': self.return_level(25),
            '1_in_100_year': self.return_level(100),
        }
```

---

## Backtesting EVT Model

### Proper Out-of-Sample Backtesting

```python
class EVTBacktester:
    """
    Backtest EVT models using walk-forward validation
    """

    def __init__(self, data: pd.DataFrame, date_col: str, value_col: str, group_col: str = None):
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
        group_col : str
            Name of grouping column (e.g., 'TOPS' for sub-sectors)
        """
        self.data = data.copy()
        self.date_col = date_col
        self.value_col = value_col
        self.group_col = group_col

        # Extract year if not already present
        if 'Year' not in self.data.columns:
            self.data['Year'] = pd.to_datetime(self.data[date_col]).dt.year

    def backtest_crisis_year(self, crisis_year: int, training_years: int = 10,
                            test_percentiles: list = [0.96, 0.99]) -> pd.DataFrame:
        """
        Backtest a specific crisis year (e.g., 2008, 2009)

        Parameters:
        -----------
        crisis_year : int
            Year to test (e.g., 2008)
        training_years : int
            Number of years before crisis to use for training
        test_percentiles : list
            Percentiles to evaluate

        Returns:
        --------
        results : pd.DataFrame
            Comparison of forecasted vs actual values
        """
        # Split data
        train_start = crisis_year - training_years
        train_data = self.data[(self.data['Year'] >= train_start) & (self.data['Year'] < crisis_year)]
        test_data = self.data[self.data['Year'] == crisis_year]

        results = []

        if self.group_col:
            groups = train_data[self.group_col].unique()
        else:
            groups = [None]

        for group in groups:
            # Filter by group
            if group is not None:
                train_subset = train_data[train_data[self.group_col] == group][self.value_col].dropna()
                test_subset = test_data[test_data[self.group_col] == group][self.value_col].dropna()
            else:
                train_subset = train_data[self.value_col].dropna()
                test_subset = test_data[self.value_col].dropna()

            if len(train_subset) < 50 or len(test_subset) == 0:
                continue

            # Fit EVT model on training data
            try:
                evt_model = GPDModel(train_subset.values, threshold_quantile=0.90)
                evt_model.fit()

                # Get forecasts
                forecasts = {f'EVT_{int(p*100)}th': evt_model.quantile(p) for p in test_percentiles}

                # Get confidence intervals
                ci_95 = {f'EVT_{int(p*100)}th_CI': evt_model.confidence_interval(p, confidence=0.95)
                        for p in test_percentiles}

                # Get actuals
                actuals = {f'Actual_{int(p*100)}th': test_subset.quantile(p) for p in test_percentiles}
                actual_mean = test_subset.mean()

                # Calculate errors
                errors = {f'Error_{int(p*100)}th': actuals[f'Actual_{int(p*100)}th'] - forecasts[f'EVT_{int(p*100)}th']
                         for p in test_percentiles}

                # Check coverage (did actual fall within CI?)
                coverage = {}
                for p in test_percentiles:
                    ci_lower, ci_upper = ci_95[f'EVT_{int(p*100)}th_CI']
                    actual = actuals[f'Actual_{int(p*100)}th']
                    coverage[f'Coverage_{int(p*100)}th'] = (ci_lower <= actual <= ci_upper)

                # Compile results
                result = {
                    'Group': group if group else 'All',
                    'Crisis_Year': crisis_year,
                    'Train_N': len(train_subset),
                    'Test_N': len(test_subset),
                    'Actual_Mean': actual_mean,
                    **forecasts,
                    **actuals,
                    **errors,
                    **coverage,
                }

                # Add CI bounds
                for p in test_percentiles:
                    ci_lower, ci_upper = ci_95[f'EVT_{int(p*100)}th_CI']
                    result[f'EVT_{int(p*100)}th_CI_Lower'] = ci_lower
                    result[f'EVT_{int(p*100)}th_CI_Upper'] = ci_upper

                results.append(result)

            except Exception as e:
                print(f"Error fitting {group}: {e}")
                continue

        return pd.DataFrame(results)

    def walk_forward_backtest(self, start_year: int, end_year: int,
                             training_years: int = 10, step: int = 1) -> pd.DataFrame:
        """
        Perform walk-forward backtesting

        Parameters:
        -----------
        start_year : int
            First year to test
        end_year : int
            Last year to test
        training_years : int
            Training window size
        step : int
            Step size for moving window

        Returns:
        --------
        results : pd.DataFrame
            Backtesting results across all periods
        """
        all_results = []

        for year in range(start_year, end_year + 1, step):
            print(f"Backtesting year {year}...")
            year_results = self.backtest_crisis_year(year, training_years)
            all_results.append(year_results)

        return pd.concat(all_results, ignore_index=True)

    def compare_methods(self, crisis_year: int, training_years: int = 10) -> pd.DataFrame:
        """
        Compare EVT vs Empirical Percentiles vs Current Model

        Returns:
        --------
        comparison : pd.DataFrame
            Side-by-side comparison of methods
        """
        train_start = crisis_year - training_years
        train_data = self.data[(self.data['Year'] >= train_start) & (self.data['Year'] < crisis_year)]
        test_data = self.data[self.data['Year'] == crisis_year]

        results = []
        test_percentiles = [0.80, 0.90, 0.96, 0.99]

        groups = train_data[self.group_col].unique() if self.group_col else [None]

        for group in groups:
            if group is not None:
                train_subset = train_data[train_data[self.group_col] == group][self.value_col].dropna()
                test_subset = test_data[test_data[self.group_col] == group][self.value_col].dropna()
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
                        'Percentile': f'{int(p*100)}th',
                        'EVT_Forecast': evt_forecast,
                        'Empirical_Forecast': empirical_forecast,
                        'Actual': actual,
                        'EVT_Error': evt_error,
                        'Empirical_Error': empirical_error,
                        'EVT_Abs_Error': abs(evt_error),
                        'Empirical_Abs_Error': abs(empirical_error),
                        'EVT_Better': abs(evt_error) < abs(empirical_error)
                    })

            except Exception as e:
                print(f"Error for {group}: {e}")
                continue

        return pd.DataFrame(results)
```

---

## Integration with Your Opex Model

### Complete Example

```python
import pandas as pd
import numpy as np

def run_evt_analysis(opex_data: pd.DataFrame, sector: str):
    """
    Run EVT analysis on Opex data

    Parameters:
    -----------
    opex_data : pd.DataFrame
        Must contain: 'TOPS', 'delta_opex/rev', 'Year', 'DATE_OF_FINANCIALS'
    sector : str
        Sector name
    """

    # Filter clean data (already processed through your pipeline)
    data = opex_data.dropna(subset=['delta_opex/rev'])

    print(f"\n{'='*80}")
    print(f"EVT ANALYSIS FOR {sector}")
    print(f"{'='*80}\n")

    # 1. Fit EVT by sub-sector
    print("1. FITTING EVT MODELS BY SUB-SECTOR")
    print("-" * 80)

    evt_results = []

    for subsector in data['TOPS'].unique():
        subset = data[data['TOPS'] == subsector]['delta_opex/rev'].values

        if len(subset) < 50:
            print(f"⚠️  {subsector}: Insufficient data ({len(subset)} points)")
            continue

        # Fit EVT model
        evt = GPDModel(subset, threshold_quantile=0.90)
        evt.fit()

        summary = evt.summary()
        summary['Subsector'] = subsector
        evt_results.append(summary)

        print(f"\n{subsector}:")
        print(f"  • Shape parameter (ξ): {summary['shape_parameter']:.4f} ({summary['tail_type']})")
        print(f"  • 96th percentile: {summary['96th_percentile']:.4f}")
        print(f"  • 99th percentile: {summary['99th_percentile']:.4f}")
        print(f"  • 1-in-25 year: {summary['1_in_25_year']:.4f}")

    evt_summary_df = pd.DataFrame(evt_results)

    # 2. Backtest 2008 Financial Crisis
    print(f"\n\n2. BACKTESTING: 2008 FINANCIAL CRISIS")
    print("-" * 80)

    backtester = EVTBacktester(
        data=data,
        date_col='DATE_OF_FINANCIALS',
        value_col='delta_opex/rev',
        group_col='TOPS'
    )

    backtest_2008 = backtester.backtest_crisis_year(
        crisis_year=2008,
        training_years=10,
        test_percentiles=[0.96, 0.99]
    )

    print("\nBacktest Results (2008):")
    print(backtest_2008[['Group', 'EVT_96th', 'Actual_96th', 'Error_96th', 'Coverage_96th']])

    # 3. Backtest 2009
    print(f"\n\n3. BACKTESTING: 2009 FINANCIAL CRISIS")
    print("-" * 80)

    backtest_2009 = backtester.backtest_crisis_year(
        crisis_year=2009,
        training_years=10,
        test_percentiles=[0.96, 0.99]
    )

    print("\nBacktest Results (2009):")
    print(backtest_2009[['Group', 'EVT_96th', 'Actual_96th', 'Error_96th', 'Coverage_96th']])

    # 4. Compare EVT vs Current Method
    print(f"\n\n4. MODEL COMPARISON: EVT vs EMPIRICAL PERCENTILES")
    print("-" * 80)

    comparison = backtester.compare_methods(crisis_year=2008, training_years=10)

    print("\nMethod Comparison (2008):")
    print(comparison[['Group', 'Percentile', 'EVT_Forecast', 'Empirical_Forecast',
                      'Actual', 'EVT_Error', 'Empirical_Error', 'EVT_Better']])

    # Summary statistics
    print("\n\nSUMMARY STATISTICS:")
    print(f"EVT Mean Absolute Error: {comparison['EVT_Abs_Error'].mean():.4f}")
    print(f"Empirical Mean Absolute Error: {comparison['Empirical_Abs_Error'].mean():.4f}")
    print(f"EVT Wins: {comparison['EVT_Better'].sum()} / {len(comparison)} cases")

    return {
        'evt_summary': evt_summary_df,
        'backtest_2008': backtest_2008,
        'backtest_2009': backtest_2009,
        'comparison': comparison
    }


# USAGE IN YOUR opex.py:
# Add this at the end of the Opex() function, before the final output

if __name__ == "__main__":
    # After you've created Opex_clean_rel_exclude_add_cat in your main script:

    evt_results = run_evt_analysis(
        opex_data=Opex_clean_rel_exclude_add_cat,
        sector=sector
    )

    # Save results
    with pd.ExcelWriter(f"{output_temp}/{sector_name}/EVT_Analysis.xlsx") as writer:
        evt_results['evt_summary'].to_excel(writer, sheet_name='EVT_Summary', index=False)
        evt_results['backtest_2008'].to_excel(writer, sheet_name='Backtest_2008', index=False)
        evt_results['backtest_2009'].to_excel(writer, sheet_name='Backtest_2009', index=False)
        evt_results['comparison'].to_excel(writer, sheet_name='Method_Comparison', index=False)
```

---

## Advanced: Using PyExtremes Library

For more advanced features, you can use the `pyextremes` library:

```python
from pyextremes import EVA

def advanced_evt_analysis(data: np.array):
    """
    Advanced EVT using pyextremes library
    """
    # Create EVA object
    model = EVA(data)

    # Fit using POT method
    model.get_extremes(method="POT", threshold=0.9, r="24H")
    model.fit_model()

    # Get return values
    return_values = model.get_return_value(
        return_period=[10, 25, 50, 100],
        alpha=0.95  # confidence level
    )

    # Plot diagnostics
    fig = model.plot_diagnostic(return_period=[10, 25, 50, 100])

    return model, return_values, fig
```

---

## Key Recommendations

### 1. Threshold Selection
- Start with 90th percentile (captures top 10% as extremes)
- Check stability: Fit models with thresholds from 85th to 95th percentile
- Use Mean Excess Plot to guide selection

### 2. Model Validation
- Always use out-of-sample backtesting
- Check diagnostic plots (Q-Q plot, probability plot)
- Bootstrap confidence intervals
- Compare multiple crisis years (2008, 2009, 2020 COVID)

### 3. Practical Implementation
- Use EVT for 96th percentile and above
- Can combine: Empirical percentiles for 50-90th, EVT for 90th+
- Report confidence intervals to stakeholders
- Re-fit quarterly/semi-annually as new data arrives

### 4. When EVT May Not Work Well
- Very small samples (< 50 observations)
- Data with structural breaks (changing regimes)
- Heavy discretization or rounding

---

## Next Steps

1. **Implement basic GPD model** on one sub-sector first
2. **Run 2008/2009 backtest** and compare to current method
3. **Generate diagnostic plots** and check model assumptions
4. **If successful**, roll out across all sub-sectors
5. **Document findings** and update stress testing methodology
