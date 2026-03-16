# OPEX EVT Implementation Guide

## Overview

`opex_evt.py` is a refactored version of `opex.py` that replaces **empirical distribution methods** with **Extreme Value Theory (EVT)** for tail risk estimation. It maintains all data preparation and cleaning logic while providing:

- More robust tail risk estimates
- Comprehensive backtesting framework
- Enhanced performance metrics
- Better handling of sparse extreme events

---

## Key Differences: Empirical vs EVT

| Aspect | Original (opex.py) | EVT Version (opex_evt.py) |
|--------|-------------------|--------------------------|
| **Method** | Empirical percentiles | Generalized Pareto Distribution (GPD) |
| **Tail Estimation** | Sample quantiles | Parametric extrapolation |
| **Data Efficiency** | Uses all data equally | Focuses on tail exceedances |
| **Extreme Events** | May underestimate | Better for rare events |
| **Backtesting** | Basic (2008-2009 comparison) | Comprehensive (coverage, Kupiec test, MAE/RMSE) |
| **Diagnostics** | Limited | QQ-plots, PP-plots, return level plots |

---

## Architecture

### 1. **PanelEVT Class**
Core EVT modeling for panel data with pooled GPD fitting.

```python
class PanelEVT:
    def fit_segment(segment_name, threshold_percentile=0.95)
        → Fits GPD to threshold exceedances

    def calculate_var(segment_name, confidence_level)
        → Calculates Value at Risk using GPD

    def calculate_es(segment_name, confidence_level)
        → Calculates Expected Shortfall (CVaR)

    def calculate_stress_impacts(segment_name, percentiles)
        → Computes stress impacts vs baseline
```

**Key Features:**
- Automatic threshold selection (default: 95th percentile)
- MLE parameter estimation for GPD
- Fallback to empirical if insufficient exceedances
- Shape parameter interpretation (tail behavior)

### 2. **EVTBacktester Class**
Comprehensive backtesting framework.

```python
class EVTBacktester:
    def backtest_crisis(segment_name, crisis_years, target_percentile)
        → Tests model against historical crisis

    def calculate_coverage_by_percentile(segment_name, percentiles)
        → Coverage and exception rates

    def kupiec_test(segment_name, confidence_level)
        → Statistical test for unconditional coverage
```

**Metrics Computed:**
- **MAE** (Mean Absolute Error)
- **RMSE** (Root Mean Squared Error)
- **Coverage**: % of observations below VaR
- **Exception Rate**: % exceeding VaR
- **Kupiec Test**: LR statistic and p-value

---

## Data Processing Pipeline

The script follows a **9-step cleaning pipeline** (identical to original):

```
Step 1: Initial data load
Step 2: Remove Revenue "Not applicable"
Step 3: Remove Revenue "Missing"
Step 4: Remove Revenue = 0
Step 5: Calculate Opex/Revenue, filter > 0
Step 6: Drop NA values
Step 7: Remove quarterly duplicates (annual only)
Step 8: Remove infinity values
Step 9: Final modeling data
```

**Additional EVT-Specific Steps:**
- **Step 10**: Compute year-over-year delta (relative change)
- **Step 11**: Apply dampeners (exclusion list + percentile winsorization)
- **Step 12**: Fit GPD models per segment
- **Step 13**: Calculate EVT-based stress impacts
- **Step 14**: Comprehensive backtesting

---

## EVT Methodology Details

### Threshold Selection

```python
threshold = segment_data.quantile(0.95)  # 95th percentile
exceedances = segment_data[segment_data > threshold] - threshold
```

**Why 95th percentile?**
- Balances bias (lower threshold) vs variance (higher threshold)
- Typically yields 50-100+ exceedances per segment
- Industry standard for financial tail risk

### GPD Fitting

```python
xi, loc, sigma = genpareto.fit(exceedances, floc=0)
```

**Parameters:**
- **ξ (xi)**: Shape parameter (tail heaviness)
  - ξ > 0.5: Very heavy tail (infinite variance)
  - ξ > 0: Heavy tail (Pareto-like)
  - ξ ≈ 0: Exponential tail
  - ξ < 0: Light/bounded tail
- **σ (sigma)**: Scale parameter (spread)
- **u**: Threshold (location fixed at 0 for exceedances)

### VaR Calculation

For confidence level α (e.g., 99%):

```python
p = 1 - α
ζ_u = n_exceedances / n_total

if ξ ≈ 0:  # Exponential case
    VaR = u + σ * log(ζ_u / p)
else:       # General case
    VaR = u + (σ / ξ) * ((ζ_u / p)^(-ξ) - 1)
```

### Expected Shortfall (ES)

```python
if ξ < 1:
    ES = (VaR + σ - ξ * u) / (1 - ξ)
else:
    ES = ∞  # Undefined for very heavy tails
```

---

## Backtesting Framework

### 1. Crisis Period Analysis

Tests model performance against 2008-2009 financial crisis:

```python
crisis_results = backtester.backtest_crisis(
    segment_name='CT_Energy',
    crisis_years=[2008, 2009],
    target_percentile=96  # 1 in 25 event
)
```

**Outputs:**
- Actual avg crisis value vs Predicted VaR
- MAE and RMSE
- Coverage rate (should be ~96% for 96th percentile)
- Exception rate (should be ~4%)
- Empirical percentile rank of crisis value

### 2. Coverage Testing

Validates that VaR at X% percentile is exceeded by (100-X)% of observations:

```python
coverage_results = backtester.calculate_coverage_by_percentile(
    segment_name='CT_Energy',
    percentiles=[50, 60, 67, 75, 90, 97.5]
)
```

**Ideal Results:**
- 90th percentile → 90% coverage, 10% exception rate
- 97.5th percentile → 97.5% coverage, 2.5% exception rate

### 3. Kupiec Test

Statistical test (Christoffersen, 1998) for unconditional coverage:

**Null Hypothesis**: Exception rate = Expected rate
**Test Statistic**: LR ~ χ²(1)

```python
kupiec = backtester.kupiec_test(
    segment_name='CT_Energy',
    confidence_level=0.96
)

if kupiec['p_value'] < 0.05:
    print("REJECT: Model is inadequate")
else:
    print("ACCEPT: Model is adequate")
```

---

## Output Files

All outputs saved to: `{OUT_DIR}/{sector_name}/EVT/`

### 1. **Consolidated Results** (`Opex_{sector}_EVT_Consolidated.xlsx`)

**Sheets:**
- `DataStats_Datapoints`: Datapoint counts per step
- `DataStats_SpreadIDs`: Unique ID counts per step
- `Exclusions`: Dampening summary
- `Outliers_Winsorized`: Winsorization summary
- `EVT_Model_Summary`: GPD parameters per segment
- `Full_Results_EVT`: All percentiles + metrics
- `Stress_Impacts_EVT`: Stress impacts (long format)
- `Backtesting_Results`: MAE, RMSE, coverage, Kupiec test
- `Model_Data`: Raw data used for modeling

### 2. **Diagnostic Plots** (`Opex_{sector}_EVT_Diagnostics.pdf`)

**6 plots per segment:**

1. **Histogram with EVT Quantiles**
   - Distribution with percentile overlays
   - Color-coded: green (median), orange (moderate), red (extreme)

2. **QQ-Plot**
   - Theoretical GPD quantiles vs sample quantiles
   - Perfect fit = 45° line

3. **PP-Plot**
   - Theoretical GPD probabilities vs empirical
   - Tests distribution fit

4. **Return Level Plot**
   - VaR vs Return Period (log scale)
   - Shows 10, 25, 50, 100-year levels

5. **Exceedances Over Time**
   - Threshold exceedances by year
   - Checks for temporal clustering

6. **Model Summary**
   - Parameters, data statistics, tail interpretation

### 3. **Backtesting Plots** (`Opex_{sector}_EVT_Backtesting.pdf`)

**4 plots per segment:**

1. **Actual vs Expected Coverage**
   - Bar chart comparing coverage rates
   - Should align closely

2. **Actual vs Expected Exception Rate**
   - Complement of coverage
   - Tests tail calibration

3. **Crisis Period: Actual vs Predicted**
   - 2008 and 2009 comparison
   - VaR prediction vs actual values

4. **Performance Metrics Summary**
   - Textual summary with assessment
   - MAE, RMSE, coverage accuracy

---

## Usage

### Basic Usage

```python
from opex_evt import Opex_EVT

# Run EVT analysis for a sector
Opex_EVT(
    sector_name="Commodity Traders",
    threshold_percentile=0.95,    # 95th percentile
    min_exceedances=30            # Minimum for GPD fitting
)
```

### Parameter Tuning

```python
# More conservative (higher threshold)
Opex_EVT(
    sector_name="O&G",
    threshold_percentile=0.97,    # 97th percentile
    min_exceedances=25
)

# More data (lower threshold)
Opex_EVT(
    sector_name="Metals & Mining",
    threshold_percentile=0.90,    # 90th percentile
    min_exceedances=50
)
```

### Batch Processing

```python
sectors = [
    "Commodity Traders",
    "O&G",
    "Metals & Mining",
    "Automobiles & Components"
]

for sector in sectors:
    try:
        Opex_EVT(sector, threshold_percentile=0.95, min_exceedances=30)
    except Exception as e:
        print(f"Error in {sector}: {e}")
        continue
```

---

## Interpretation Guide

### EVT Model Summary

```
Method: GPD
Shape (ξ): 0.23
Scale (σ): 0.045
Tail Interpretation: → Heavy tail
```

**What this means:**
- ξ = 0.23 indicates moderately heavy tail (Pareto-like)
- Extreme losses decay slowly (power law)
- Traditional percentiles may underestimate tail risk
- EVT provides more reliable extreme quantiles

### Backtesting Results

```
2008 Crisis:
  Actual avg value: 0.287
  Predicted VaR (96th): 0.255
  Coverage: 92%
  MAE: 0.035
```

**Interpretation:**
- Model slightly underestimated 2008 crisis (actual > predicted)
- Coverage at 92% vs target 96% → reasonable
- MAE of 0.035 indicates good accuracy
- Model captures crisis magnitude well

### Coverage Analysis

```
90th percentile:
  Actual coverage: 88.5%
  Expected coverage: 90.0%
  Exception rate: 11.5%
```

**Assessment:**
- Slight underestimation (88.5% < 90%)
- Model is conservative (good for risk management)
- Exception rate slightly high but acceptable

---

## When to Use EVT vs Empirical

### Use EVT When:
✅ Modeling tail risk (>90th percentile)
✅ Limited extreme observations
✅ Need to extrapolate beyond observed data
✅ Regulatory capital requirements (Basel III)
✅ Heavy-tailed distributions
✅ Statistical rigor required

### Use Empirical When:
✅ Modeling central tendency (<75th percentile)
✅ Abundant data across all ranges
✅ No extrapolation needed
✅ Quick exploratory analysis
✅ Light-tailed distributions
✅ Simple communication to stakeholders

---

## Troubleshooting

### Issue: "Only X exceedances (< 30)"

**Problem**: Insufficient data for reliable GPD fitting

**Solutions:**
1. Lower threshold: `threshold_percentile=0.90`
2. Pool similar segments
3. Use longer time horizon
4. Accept empirical fallback (automatic)

### Issue: "Shape parameter ξ > 1"

**Problem**: Infinite mean and variance (very extreme tail)

**Solutions:**
1. Check for data errors/outliers
2. Apply dampening more aggressively
3. Consider alternative distributions (e.g., Burr)
4. Use Expected Shortfall with caution (may be infinite)

### Issue: "QQ-Plot shows poor fit"

**Problem**: GPD not appropriate for this data

**Solutions:**
1. Try different threshold (90th or 97th percentile)
2. Check for non-stationarity (trends over time)
3. Consider Block Maxima (GEV) instead
4. Inspect histogram for multi-modality

### Issue: "Kupiec test p-value < 0.05"

**Problem**: Model fails coverage test

**Solutions:**
1. Adjust threshold selection
2. Check for temporal dependence (cluster extremes)
3. Re-examine dampening strategy
4. Validate crisis period data quality

---

## Best Practices

### 1. Threshold Selection
- Start with 95th percentile
- Use diagnostic plots to validate
- Ensure 30-50+ exceedances per segment
- Check threshold stability across values

### 2. Model Validation
- Always generate diagnostic plots
- Review QQ-plot and PP-plot carefully
- Run full backtesting suite
- Compare to empirical for sanity check

### 3. Crisis Testing
- Use multiple crisis periods (not just 2008-2009)
- Test at multiple percentiles (90th, 95th, 97.5th)
- Report both MAE and RMSE
- Consider relative errors, not just absolute

### 4. Reporting
- Include shape parameter interpretation
- Report confidence intervals (bootstrap if needed)
- Show both EVT and empirical for comparison
- Highlight model limitations clearly

---

## References

### Academic Papers
1. McNeil, A. J., & Frey, R. (2000). "Estimation of tail-related risk measures for heteroscedastic financial time series: an extreme value approach." *Journal of Empirical Finance*, 7(3-4), 271-300.

2. Embrechts, P., Klüppelberg, C., & Mikosch, T. (1997). *Modelling Extremal Events for Insurance and Finance*. Springer.

3. Coles, S. (2001). *An Introduction to Statistical Modeling of Extreme Values*. Springer.

4. Kupiec, P. H. (1995). "Techniques for verifying the accuracy of risk measurement models." *The Journal of Derivatives*, 3(2), 73-84.

### Software Documentation
- `scipy.stats.genpareto`: [SciPy Documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.genpareto.html)
- Panel EVT methods: McNeil & Frey (2000)

---

## Comparison: Sample Output

### Empirical Method (opex.py)
```
Sub-sector: CT_Energy
50th Percentile: 0.025
75th Percentile: 0.085
90th Percentile: 0.145
97.5th Percentile: 0.235

Stress Impact (97.5th): 0.210
```

### EVT Method (opex_evt.py)
```
Sub-sector: CT_Energy
Method: GPD (ξ=0.18, σ=0.052)

50th Percentile: 0.025  (empirical baseline)
75th Percentile: 0.088  (EVT)
90th Percentile: 0.158  (EVT, +9% vs empirical)
97.5th Percentile: 0.268 (EVT, +14% vs empirical)

Stress Impact (97.5th): 0.243

Backtesting (2008-2009):
  MAE: 0.028
  Coverage: 94.5%
  Kupiec test: p=0.32 (PASS)
```

**Key Differences:**
- EVT gives higher tail estimates (more conservative)
- EVT provides statistical justification via backtesting
- EVT quantifies model uncertainty

---

## Conclusion

`opex_evt.py` provides a **statistically rigorous** approach to OPEX tail risk estimation by:

1. **Leveraging EVT**: Better extrapolation to rare events
2. **Maintaining consistency**: Same data cleaning as original
3. **Enhanced validation**: Comprehensive backtesting framework
4. **Transparency**: Diagnostic plots and model summaries
5. **Flexibility**: Automatic fallback to empirical when needed

For **regulatory reporting** and **tail risk management**, EVT is the preferred approach. For **exploratory analysis** and **central tendency**, empirical methods remain valid.

Use both methods in parallel for robust risk assessment! 🎯
