# Building a Good EVT (Extreme Value Theory) Model

## Overview
Extreme Value Theory (EVT) is a statistical framework for modeling the tail behavior of distributions - particularly useful in risk management for estimating rare, extreme events like financial losses, operational failures, or climate extremes.

---

## Table of Contents
1. [Understanding EVT Fundamentals](#1-understanding-evt-fundamentals)
2. [Data Requirements & Preparation](#2-data-requirements--preparation)
3. [Choosing the Right EVT Approach](#3-choosing-the-right-evt-approach)
4. [Model Building Steps](#4-model-building-steps)
5. [Parameter Estimation](#5-parameter-estimation)
6. [Model Validation](#6-model-validation)
7. [Practical Implementation](#7-practical-implementation)
8. [Common Pitfalls](#8-common-pitfalls)

---

## 1. Understanding EVT Fundamentals

### Core Concept
EVT focuses on the **statistical behavior of extreme values** rather than the entire distribution. It answers questions like:
- What is the probability of a loss exceeding $X million?
- What is the expected loss given that it exceeds a certain threshold?

### Two Main Approaches

#### A. Block Maxima (GEV Distribution)
- **Method**: Divide data into blocks (e.g., yearly), take maximum from each block
- **Distribution**: Generalized Extreme Value (GEV)
- **Best for**: Regular time-series data with natural blocking periods

#### B. Peaks Over Threshold (POT/GPD)
- **Method**: Select all observations exceeding a high threshold
- **Distribution**: Generalized Pareto Distribution (GPD)
- **Best for**: Making full use of extreme data, more efficient with limited data

### Key Distributions

**GEV Distribution:**
```
F(x) = exp{-[1 + ξ(x-μ)/σ]^(-1/ξ)}
```
Where:
- μ = location parameter
- σ = scale parameter (σ > 0)
- ξ = shape parameter (tail index)

**GPD Distribution:**
```
F(x) = 1 - [1 + ξ(x-u)/σ]^(-1/ξ)
```
Where:
- u = threshold
- σ = scale parameter
- ξ = shape parameter

### Shape Parameter Interpretation

| ξ Value | Distribution Type | Tail Behavior | Examples |
|---------|------------------|---------------|----------|
| ξ > 0 | Fréchet | Heavy tail | Financial losses, insurance claims |
| ξ = 0 | Gumbel | Light tail | Maximum temperatures |
| ξ < 0 | Weibull | Bounded tail | Human lifespan, material strength |

---

## 2. Data Requirements & Preparation

### Minimum Data Requirements
- **Block Maxima**: At least 20-30 blocks (e.g., 20-30 years of data)
- **POT**: At least 50-100 threshold exceedances
- **General Rule**: More extreme data = better tail estimation

### Data Quality Checklist
✅ **Independence**: Observations should be independent or properly de-clustered
✅ **Stationarity**: No trends or structural breaks (or properly adjusted)
✅ **Completeness**: Minimal missing values in extreme periods
✅ **Accuracy**: Extreme values verified (not data errors)
✅ **Relevance**: Data reflects current risk environment

### Data Preparation Steps

#### Step 1: Data Cleaning
```python
# Remove outliers that are clearly data errors
# Handle missing values (do NOT impute extremes)
# Convert to appropriate units
# Ensure correct time ordering
```

#### Step 2: Stationarity Testing
- Perform Augmented Dickey-Fuller test
- Check for trends using Mann-Kendall test
- Plot time series and ACF/PACF
- If non-stationary: detrend or use time-varying parameters

#### Step 3: De-clustering
For dependent data (common in financial/environmental):
- **Runs declustering**: Separate clusters by minimum inter-cluster time
- **Block maxima**: Natural de-clustering through block selection
- **Threshold exceedances**: Use extremal index to adjust

Example de-clustering logic:
```python
def decluster(data, threshold, min_separation_days=5):
    """
    Extract independent clusters of threshold exceedances
    """
    exceedances = data[data > threshold]
    clusters = []
    current_cluster = []

    for i, (date, value) in enumerate(exceedances.items()):
        if not current_cluster or (date - current_cluster[-1][0]).days >= min_separation_days:
            if current_cluster:
                clusters.append(max(current_cluster, key=lambda x: x[1]))
            current_cluster = [(date, value)]
        else:
            current_cluster.append((date, value))

    return [value for date, value in clusters]
```

---

## 3. Choosing the Right EVT Approach

### Decision Framework

```
START
  |
  ├─ Do you have natural time blocks (e.g., annual data)?
  |  ├─ YES → Consider Block Maxima (GEV)
  |  └─ NO → Continue
  |
  ├─ Do you have limited extreme observations (<30)?
  |  ├─ YES → Use POT (more efficient)
  |  └─ NO → Continue
  |
  ├─ Is your data highly clustered in time?
  |  ├─ YES → Block Maxima may work better
  |  └─ NO → POT is likely better
  |
  └─ DEFAULT → POT (GPD) is generally preferred
```

### Comparison Table

| Criteria | Block Maxima (GEV) | Peaks Over Threshold (GPD) |
|----------|-------------------|---------------------------|
| **Data efficiency** | Lower (uses only 1 point per block) | Higher (uses all exceedances) |
| **Sample size needed** | 20-30 blocks minimum | 50-100 exceedances minimum |
| **Threshold selection** | Not required | Critical step |
| **Clustering issues** | Automatically handled | Requires de-clustering |
| **Interpretation** | Simpler | More flexible |
| **Common in practice** | Climate science, hydrology | Finance, insurance |

---

## 4. Model Building Steps

### Approach A: Block Maxima Method

#### Step 1: Define Blocks
```python
# Example: Annual maxima
annual_max = data.groupby(data.index.year).max()

# Or quarterly, monthly, etc.
quarterly_max = data.groupby(data.index.to_period('Q')).max()
```

#### Step 2: Fit GEV Distribution
```python
from scipy.stats import genextreme
import numpy as np

# Fit GEV (note: scipy uses negative ξ convention)
shape, loc, scale = genextreme.fit(annual_max)
xi = -shape  # Convert to standard EVT notation
mu = loc
sigma = scale

print(f"Location (μ): {mu:.4f}")
print(f"Scale (σ): {sigma:.4f}")
print(f"Shape (ξ): {xi:.4f}")
```

#### Step 3: Estimate Return Levels
```python
def gev_return_level(mu, sigma, xi, return_period):
    """
    Calculate return level for given return period
    """
    if abs(xi) < 1e-6:  # Gumbel case
        return mu - sigma * np.log(-np.log(1 - 1/return_period))
    else:
        return mu + (sigma/xi) * ((-np.log(1 - 1/return_period))**(-xi) - 1)

# Example: 100-year return level
return_100 = gev_return_level(mu, sigma, xi, 100)
print(f"100-year return level: {return_100:.4f}")
```

### Approach B: Peaks Over Threshold Method

#### Step 1: Select Threshold

**Methods for threshold selection:**

1. **Mean Residual Life Plot**
   - Plot: Average excess vs threshold
   - Look for linearity above optimal threshold

   ```python
   def mean_residual_life_plot(data, thresholds):
       mean_excess = []
       for u in thresholds:
           excesses = data[data > u] - u
           mean_excess.append(excesses.mean())

       plt.plot(thresholds, mean_excess)
       plt.xlabel('Threshold')
       plt.ylabel('Mean Excess')
       plt.title('Mean Residual Life Plot')
   ```

2. **Parameter Stability Plot**
   - Fit GPD for range of thresholds
   - Plot estimated parameters
   - Look for stability in ξ and modified σ

   ```python
   def parameter_stability_plot(data, threshold_range):
       shapes, scales = [], []

       for u in threshold_range:
           excesses = data[data > u] - u
           if len(excesses) > 20:
               shape, loc, scale = genpareto.fit(excesses, floc=0)
               shapes.append(shape)
               scales.append(scale - shape * u)

       fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
       ax1.plot(threshold_range[:len(shapes)], shapes)
       ax1.set_title('Shape Parameter Stability')
       ax2.plot(threshold_range[:len(scales)], scales)
       ax2.set_title('Modified Scale Parameter Stability')
   ```

3. **Practical Guidelines**
   - Choose threshold that gives **50-100+ exceedances**
   - Balance bias (low threshold) vs variance (high threshold)
   - Typical: 90th-95th percentile for financial data
   - Typical: 95th-99th percentile for operational risk

#### Step 2: De-cluster Exceedances
```python
# Apply de-clustering to get independent peaks
independent_peaks = decluster(data, threshold, min_separation_days=5)
```

#### Step 3: Fit GPD
```python
from scipy.stats import genpareto

# Calculate excesses over threshold
excesses = independent_peaks - threshold

# Fit GPD (floc=0 fixes location at 0)
shape, loc, scale = genpareto.fit(excesses, floc=0)
xi = shape
sigma = scale

print(f"Scale (σ): {sigma:.4f}")
print(f"Shape (ξ): {xi:.4f}")
print(f"Number of exceedances: {len(excesses)}")
```

#### Step 4: Estimate Tail Probabilities
```python
def gpd_tail_probability(data, threshold, xi, sigma, x):
    """
    Estimate P(X > x | X > threshold)
    """
    n = len(data)
    n_u = len(data[data > threshold])

    if x <= threshold:
        return 1.0

    # Empirical probability of exceeding threshold
    zeta_u = n_u / n

    # GPD tail probability
    if abs(xi) < 1e-6:  # Exponential case
        prob = np.exp(-(x - threshold) / sigma)
    else:
        prob = (1 + xi * (x - threshold) / sigma) ** (-1/xi)

    return zeta_u * prob

# Example: Probability of exceeding 2x threshold
prob = gpd_tail_probability(data, threshold, xi, sigma, 2*threshold)
print(f"P(X > {2*threshold}) = {prob:.6f}")
```

#### Step 5: Calculate Value at Risk (VaR) and Expected Shortfall (ES)
```python
def calculate_var_es(data, threshold, xi, sigma, confidence_level=0.99):
    """
    Calculate VaR and ES using GPD
    """
    n = len(data)
    n_u = len(data[data > threshold])
    zeta_u = n_u / n

    # VaR
    p = 1 - confidence_level
    if abs(xi) < 1e-6:
        var = threshold + sigma * np.log(zeta_u / p)
    else:
        var = threshold + (sigma / xi) * ((zeta_u / p)**(-xi) - 1)

    # Expected Shortfall
    if xi < 1:
        es = (var + sigma - xi * threshold) / (1 - xi)
    else:
        es = np.inf  # Undefined for heavy tails

    return var, es

var_99, es_99 = calculate_var_es(data, threshold, xi, sigma, 0.99)
print(f"99% VaR: {var_99:.4f}")
print(f"99% ES: {es_99:.4f}")
```

---

## 5. Parameter Estimation

### Maximum Likelihood Estimation (MLE)
**Advantages:**
- Asymptotically efficient
- Well-understood statistical properties
- Standard errors available

**Implementation:**
```python
from scipy.optimize import minimize
from scipy.stats import genpareto

# Negative log-likelihood for GPD
def gpd_nll(params, data):
    sigma, xi = params
    if sigma <= 0:
        return np.inf

    n = len(data)
    if abs(xi) < 1e-6:
        return n * np.log(sigma) + np.sum(data) / sigma
    else:
        y = 1 + xi * data / sigma
        if np.any(y <= 0):
            return np.inf
        return n * np.log(sigma) + (1 + 1/xi) * np.sum(np.log(y))

# Fit using MLE
excesses = data[data > threshold] - threshold
result = minimize(gpd_nll, x0=[excesses.std(), 0.1], args=(excesses,))
sigma_mle, xi_mle = result.x
```

### Method of Moments
**Advantages:**
- Simple to compute
- Robust to outliers
- Good for initial estimates

### Probability Weighted Moments (PWM)
**Advantages:**
- Often better than MLE for small samples
- Less biased for heavy tails
- Recommended for GEV fitting

### Bayesian Methods
**Advantages:**
- Incorporates prior knowledge
- Full posterior distribution
- Natural uncertainty quantification

**Example (using PyMC3):**
```python
import pymc3 as pm

with pm.Model() as model:
    # Priors
    sigma = pm.HalfNormal('sigma', sigma=excesses.std())
    xi = pm.Normal('xi', mu=0, sigma=0.5)

    # Likelihood
    likelihood = pm.DensityDist('likelihood',
                                lambda value: gpd_loglike(value, sigma, xi),
                                observed=excesses)

    # Sample
    trace = pm.sample(2000, tune=1000)
```

---

## 6. Model Validation

### Diagnostic Plots

#### 1. QQ-Plot
Compare theoretical quantiles vs empirical quantiles
```python
def qq_plot(data, fitted_dist, params):
    """
    Quantile-Quantile plot
    """
    sorted_data = np.sort(data)
    n = len(data)
    theoretical_quantiles = fitted_dist.ppf(np.arange(1, n+1)/(n+1), *params)

    plt.scatter(theoretical_quantiles, sorted_data, alpha=0.6)
    plt.plot([sorted_data.min(), sorted_data.max()],
             [sorted_data.min(), sorted_data.max()], 'r--')
    plt.xlabel('Theoretical Quantiles')
    plt.ylabel('Empirical Quantiles')
    plt.title('QQ-Plot')
```

#### 2. PP-Plot
Compare theoretical probabilities vs empirical probabilities
```python
def pp_plot(data, fitted_dist, params):
    """
    Probability-Probability plot
    """
    sorted_data = np.sort(data)
    n = len(data)
    empirical_prob = np.arange(1, n+1) / (n+1)
    theoretical_prob = fitted_dist.cdf(sorted_data, *params)

    plt.scatter(theoretical_prob, empirical_prob, alpha=0.6)
    plt.plot([0, 1], [0, 1], 'r--')
    plt.xlabel('Theoretical Probabilities')
    plt.ylabel('Empirical Probabilities')
    plt.title('PP-Plot')
```

#### 3. Return Level Plot
```python
def return_level_plot(block_maxima, mu, sigma, xi):
    """
    Plot empirical vs theoretical return levels
    """
    n = len(block_maxima)
    sorted_data = np.sort(block_maxima)

    # Empirical return periods
    empirical_rp = n / (n - np.arange(n))

    # Theoretical return levels
    theoretical_rp = np.logspace(0, 3, 100)  # 1 to 1000 years
    theoretical_rl = [gev_return_level(mu, sigma, xi, rp) for rp in theoretical_rp]

    plt.scatter(empirical_rp, sorted_data, label='Empirical', alpha=0.6)
    plt.plot(theoretical_rp, theoretical_rl, 'r-', label='Fitted GEV')
    plt.xscale('log')
    plt.xlabel('Return Period (years)')
    plt.ylabel('Return Level')
    plt.legend()
    plt.grid(True, alpha=0.3)
```

### Goodness-of-Fit Tests

#### Kolmogorov-Smirnov Test
```python
from scipy.stats import kstest

# For GPD
statistic, pvalue = kstest(excesses, lambda x: genpareto.cdf(x, xi, loc=0, scale=sigma))
print(f"KS statistic: {statistic:.4f}, p-value: {pvalue:.4f}")
```

#### Anderson-Darling Test
More weight on tails (better for EVT)
```python
from scipy.stats import anderson

result = anderson(excesses, dist='gumbel')  # or custom GPD
print(f"AD statistic: {result.statistic:.4f}")
```

#### Likelihood Ratio Test
Compare nested models (e.g., Exponential vs GPD)

### Backtesting

#### Historical Simulation
- Hold out recent data
- Predict extremes using fitted model
- Compare predictions vs actual

```python
def backtest_evt(train_data, test_data, threshold, confidence_level=0.99):
    """
    Backtest EVT model on held-out data
    """
    # Fit on training data
    excesses = train_data[train_data > threshold] - threshold
    xi, _, sigma = genpareto.fit(excesses, floc=0)

    # Predict VaR on test period
    var_predicted, _ = calculate_var_es(train_data, threshold, xi, sigma, confidence_level)

    # Count exceedances in test data
    exceedances = (test_data > var_predicted).sum()
    expected_exceedances = len(test_data) * (1 - confidence_level)

    print(f"Expected exceedances: {expected_exceedances:.1f}")
    print(f"Actual exceedances: {exceedances}")
    print(f"Violation rate: {exceedances/len(test_data):.2%}")

    return exceedances, expected_exceedances
```

---

## 7. Practical Implementation

### Complete EVT Workflow (POT Method)

```python
import pandas as pd
import numpy as np
from scipy.stats import genpareto
import matplotlib.pyplot as plt

class EVTModel:
    """
    Complete EVT model using Peaks Over Threshold approach
    """

    def __init__(self, data, threshold_percentile=0.95):
        self.data = data
        self.threshold_percentile = threshold_percentile
        self.threshold = None
        self.excesses = None
        self.xi = None  # shape
        self.sigma = None  # scale
        self.n_exceedances = None

    def select_threshold(self, method='percentile', custom_threshold=None):
        """Select threshold"""
        if custom_threshold:
            self.threshold = custom_threshold
        else:
            self.threshold = np.percentile(self.data, self.threshold_percentile * 100)

        print(f"Selected threshold: {self.threshold:.4f}")
        return self.threshold

    def extract_exceedances(self, decluster=True, min_separation=5):
        """Extract peaks over threshold"""
        if decluster:
            # Simplified de-clustering
            peaks_idx = (self.data > self.threshold)
            self.excesses = self.data[peaks_idx] - self.threshold
        else:
            self.excesses = self.data[self.data > self.threshold] - self.threshold

        self.n_exceedances = len(self.excesses)
        print(f"Number of exceedances: {self.n_exceedances}")

    def fit(self, method='mle'):
        """Fit GPD to excesses"""
        if method == 'mle':
            self.xi, _, self.sigma = genpareto.fit(self.excesses, floc=0)

        print(f"Fitted parameters:")
        print(f"  Shape (ξ): {self.xi:.4f}")
        print(f"  Scale (σ): {self.sigma:.4f}")

    def calculate_var(self, confidence_level=0.99):
        """Calculate Value at Risk"""
        p = 1 - confidence_level
        zeta_u = self.n_exceedances / len(self.data)

        if abs(self.xi) < 1e-6:
            var = self.threshold + self.sigma * np.log(zeta_u / p)
        else:
            var = self.threshold + (self.sigma / self.xi) * ((zeta_u / p)**(-self.xi) - 1)

        return var

    def calculate_es(self, confidence_level=0.99):
        """Calculate Expected Shortfall"""
        var = self.calculate_var(confidence_level)

        if self.xi < 1:
            es = (var + self.sigma - self.xi * self.threshold) / (1 - self.xi)
        else:
            es = np.inf

        return es

    def plot_diagnostics(self):
        """Generate diagnostic plots"""
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))

        # 1. Threshold exceedances
        axes[0, 0].hist(self.excesses, bins=30, alpha=0.7, edgecolor='black')
        axes[0, 0].set_title('Distribution of Excesses')
        axes[0, 0].set_xlabel('Excess over threshold')

        # 2. QQ-plot
        sorted_excesses = np.sort(self.excesses)
        n = len(sorted_excesses)
        theoretical = genpareto.ppf(np.arange(1, n+1)/(n+1), self.xi, loc=0, scale=self.sigma)
        axes[0, 1].scatter(theoretical, sorted_excesses, alpha=0.6)
        axes[0, 1].plot([sorted_excesses.min(), sorted_excesses.max()],
                        [sorted_excesses.min(), sorted_excesses.max()], 'r--')
        axes[0, 1].set_title('QQ-Plot')
        axes[0, 1].set_xlabel('Theoretical Quantiles')
        axes[0, 1].set_ylabel('Sample Quantiles')

        # 3. Tail behavior
        return_periods = np.logspace(0, 3, 100)
        return_levels = [self.calculate_var(1 - 1/rp) for rp in return_periods]
        axes[1, 0].plot(return_periods, return_levels)
        axes[1, 0].set_xscale('log')
        axes[1, 0].set_title('Return Level Plot')
        axes[1, 0].set_xlabel('Return Period')
        axes[1, 0].set_ylabel('Return Level')
        axes[1, 0].grid(True, alpha=0.3)

        # 4. Probability plot
        empirical_prob = np.arange(1, n+1) / (n+1)
        theoretical_prob = genpareto.cdf(sorted_excesses, self.xi, loc=0, scale=self.sigma)
        axes[1, 1].scatter(theoretical_prob, empirical_prob, alpha=0.6)
        axes[1, 1].plot([0, 1], [0, 1], 'r--')
        axes[1, 1].set_title('PP-Plot')
        axes[1, 1].set_xlabel('Theoretical Probabilities')
        axes[1, 1].set_ylabel('Empirical Probabilities')

        plt.tight_layout()
        return fig

# Example usage
if __name__ == "__main__":
    # Simulate some loss data
    np.random.seed(42)
    losses = np.random.lognormal(0, 1, 1000)

    # Build EVT model
    model = EVTModel(losses, threshold_percentile=0.95)
    model.select_threshold()
    model.extract_exceedances()
    model.fit()

    # Calculate risk metrics
    var_99 = model.calculate_var(0.99)
    es_99 = model.calculate_es(0.99)

    print(f"\n99% VaR: {var_99:.4f}")
    print(f"99% ES: {es_99:.4f}")

    # Diagnostics
    model.plot_diagnostics()
    plt.show()
```

---

## 8. Common Pitfalls

### ❌ Pitfall 1: Insufficient Data
**Problem**: Fitting EVT with <20 exceedances
**Solution**:
- Lower threshold (more data)
- Pool data from similar sources
- Use Bayesian methods with informative priors

### ❌ Pitfall 2: Ignoring Dependence
**Problem**: Using clustered extremes as independent
**Solution**:
- Apply proper de-clustering
- Use extremal index correction
- Consider multivariate EVT for dependencies

### ❌ Pitfall 3: Wrong Threshold
**Problem**: Threshold too low (bias) or too high (variance)
**Solution**:
- Use multiple diagnostic plots
- Test threshold stability
- Sensitivity analysis across thresholds

### ❌ Pitfall 4: Non-stationarity
**Problem**: Structural changes in data over time
**Solution**:
- Test for stationarity
- Use time-varying parameters
- Segment data by regime

### ❌ Pitfall 5: Extrapolating Too Far
**Problem**: Predicting 1000-year events from 10 years of data
**Solution**:
- Stay within reasonable extrapolation range (max 2-3x data period)
- Report confidence intervals
- Use scenario analysis

### ❌ Pitfall 6: Ignoring Model Uncertainty
**Problem**: Presenting point estimates without uncertainty
**Solution**:
- Bootstrap confidence intervals
- Bayesian credible intervals
- Profile likelihood intervals

### ❌ Pitfall 7: Mixing Block Maxima with POT
**Problem**: Using both approaches inconsistently
**Solution**:
- Choose one method and stick with it
- If comparing, understand theoretical relationships

### ❌ Pitfall 8: Not Validating the Model
**Problem**: Fitting without diagnostic checks
**Solution**:
- Always produce QQ-plots, PP-plots
- Perform goodness-of-fit tests
- Backtest on held-out data

---

## Best Practices Summary

### ✅ Do's
1. **Start with exploratory data analysis** - understand your data first
2. **Use multiple threshold selection methods** - confirm stability
3. **De-cluster dependent data** - ensure independence assumption
4. **Validate thoroughly** - use multiple diagnostic plots
5. **Report uncertainty** - provide confidence/credible intervals
6. **Backtest** - validate on out-of-sample data
7. **Sensitivity analysis** - test robustness to parameter choices
8. **Document assumptions** - be transparent about limitations
9. **Compare approaches** - Block Maxima vs POT if feasible
10. **Update regularly** - refit as new data arrives

### ❌ Don'ts
1. **Don't ignore data quality** - garbage in, garbage out
2. **Don't extrapolate excessively** - stay within reasonable bounds
3. **Don't assume stationarity** - test for it
4. **Don't fit without validation** - always check diagnostics
5. **Don't ignore dependence** - cluster your extremes
6. **Don't use arbitrary thresholds** - use data-driven selection
7. **Don't over-interpret** - EVT has uncertainty, communicate it
8. **Don't forget domain knowledge** - statistics alone isn't enough

---

## Resources & References

### Key Papers
- Embrechts, P., Klüppelberg, C., & Mikosch, T. (1997). *Modelling Extremal Events for Insurance and Finance*
- Coles, S. (2001). *An Introduction to Statistical Modeling of Extreme Values*
- McNeil, A. J., & Frey, R. (2000). "Estimation of tail-related risk measures for heteroscedastic financial time series"

### Software Libraries

**Python:**
- `scipy.stats`: genextreme, genpareto
- `extremes`: Dedicated EVT library
- `pyextremes`: Modern EVT toolkit
- `thresholdmodeling`: Threshold selection tools

**R:**
- `evd`: Extreme Value Distributions
- `ismev`: Introduction to Statistical Modeling of Extreme Values
- `POT`: Peaks Over Threshold modeling
- `extRemes`: Extreme Value Analysis

### Online Resources
- NIST Engineering Statistics Handbook - EVT Chapter
- Quantitative Risk Management tutorial (ETH Zurich)
- RiskLab documentation

---

## Conclusion

Building a good EVT model requires:
1. **Solid theoretical understanding** of extreme value distributions
2. **Careful data preparation** including stationarity and independence
3. **Thoughtful threshold selection** balancing bias and variance
4. **Rigorous validation** through multiple diagnostic methods
5. **Clear communication** of uncertainty and limitations

EVT is powerful but not magic - it extrapolates from observed extremes to rarer events. Use it wisely, validate thoroughly, and always combine statistical rigor with domain expertise.
