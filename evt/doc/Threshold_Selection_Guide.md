# EVT Threshold Selection Guide

## Overview

Threshold selection is the **most critical** step in Extreme Value Theory (EVT) modeling. The threshold determines which observations are considered "extreme" and used to fit the Generalized Pareto Distribution (GPD). A poor threshold choice can lead to biased estimates, poor model fit, or insufficient data.

This guide explains the automated threshold selection tools in `opex_evt.py` and how to interpret them.

---

## Why Threshold Selection Matters

### The Bias-Variance Tradeoff

| Threshold Too Low | Threshold Optimal | Threshold Too High |
|-------------------|-------------------|-------------------|
| ❌ Bias introduced | ✅ Balanced | ❌ High variance |
| Includes non-extreme data | Captures true tail | Too few exceedances |
| GPD assumption violated | GPD fits well | Unreliable estimates |
| Underestimates tail risk | Good extrapolation | Unstable parameters |
| Example: 75th percentile | Example: 95th percentile | Example: 99.5th percentile |

### Impact on Results

```
Example: Delta OPEX/Revenue Data (n=1,000)

Threshold at 80th percentile:
  • Exceedances: 200
  • Shape (ξ): 0.08 (underestimated)
  • 99th %ile VaR: 0.145 ❌ Too conservative

Threshold at 95th percentile:
  • Exceedances: 50
  • Shape (ξ): 0.22
  • 99th %ile VaR: 0.187 ✅ Reasonable

Threshold at 99th percentile:
  • Exceedances: 10
  • Shape (ξ): 0.45 (noisy)
  • 99th %ile VaR: 0.246 ❌ Unreliable
```

---

## Threshold Selection Methods

### 1. Mean Residual Life (MRL) Plot

**Theory**: For GPD data, mean excess over threshold should be approximately linear above optimal threshold.

**Formula**:
```
MRL(u) = E[X - u | X > u]
```

**Interpretation**:
- **Linear trend above threshold** → Good threshold
- **Curved upward** → Threshold too low (capturing non-extreme data)
- **Highly variable** → Threshold too high (insufficient data)

**Example**:
```
MRL Plot Analysis:

Threshold (u)  |  MRL   | Interpretation
─────────────────────────────────────────
0.050         | 0.025  | Curved (too low)
0.100         | 0.035  | Slightly curved
0.150         | 0.048  | Linear! ✓
0.160         | 0.049  | Linear
0.170         | 0.051  | Linear
0.200         | 0.064  | Noisy (too high)
```

**Recommendation**: Choose threshold where MRL becomes approximately linear.

---

### 2. Parameter Stability Plot

**Theory**: Above optimal threshold, shape parameter (ξ) and modified scale should be stable.

**Parameters to Monitor**:
- **Shape (ξ)**: Should be roughly constant above optimal threshold
- **Modified Scale (σ - ξu)**: Should be constant (theoretical property of GPD)

**Interpretation**:
- **Stable ξ above threshold** → Good choice
- **ξ trending upward** → Threshold still too low
- **ξ highly variable** → Threshold too high
- **Confidence intervals narrow** → Good precision

**Example**:
```
Parameter Stability Analysis:

Threshold %ile | Shape ξ  | 95% CI      | Assessment
──────────────────────────────────────────────────
85%           | 0.12     | [0.05,0.19] | Trending up
90%           | 0.18     | [0.12,0.24] | More stable
95%           | 0.22     | [0.16,0.28] | Stable ✓
97%           | 0.21     | [0.14,0.28] | Stable ✓
98%           | 0.25     | [0.11,0.39] | Too noisy
```

**Recommendation**: Choose threshold where ξ stabilizes and CI remains reasonable.

---

### 3. Goodness-of-Fit (GOF) Testing

**Theory**: Statistical tests assess how well GPD fits the exceedances.

**Tests Used**:
- **Kolmogorov-Smirnov (KS) Test**: Tests overall distribution match
- **Anderson-Darling (AD) Test**: Emphasizes tail fit

**Interpretation**:
- **p-value > 0.05** → Good fit, do not reject GPD
- **p-value < 0.05** → Poor fit, consider different threshold
- **Higher p-value** → Better fit (but not always!)

**Example**:
```
Goodness-of-Fit Results:

Threshold %ile | KS Stat | p-value | Fit Quality
──────────────────────────────────────────────
90%           | 0.089   | 0.032   | Poor ❌
92%           | 0.071   | 0.087   | Acceptable ~
95%           | 0.058   | 0.234   | Good ✓
97%           | 0.052   | 0.312   | Good ✓
99%           | 0.041   | 0.523   | Good (but few data)
```

**Recommendation**: Choose threshold with p-value > 0.05, but balance with other criteria.

---

## Automated Threshold Selection Algorithm

### Composite Scoring Approach

The automated algorithm combines multiple criteria with configurable weights:

```python
Composite Score =
    stability_weight × Stability Score +
    gof_weight × GOF Score +
    exceedance_weight × Exceedance Score
```

**Default weights**:
- Stability: 40%
- Goodness-of-Fit: 30%
- Exceedance Balance: 30%

### Component Scores

#### 1. Stability Score
- Measures rolling standard deviation of ξ
- Lower variance → higher score
- Penalizes thresholds with unstable parameters

#### 2. GOF Score
- Based on KS test p-value
- Higher p-value → higher score
- Rewards good statistical fit

#### 3. Exceedance Score
- Targets 50-100 exceedances (optimal range)
- Penalizes extremes (too few or too many)
- Balances bias-variance tradeoff

### Selection Process

```
Step 1: Generate candidate thresholds (75th - 99th percentiles)
Step 2: Fit GPD for each candidate
Step 3: Calculate all three component scores
Step 4: Compute composite score
Step 5: Select threshold with highest composite score
Step 6: Validate selection with diagnostics
```

---

## Using Threshold Selection Tools

### Option 1: Generate Diagnostics Only (Recommended First Run)

```python
from opex_evt import Opex_EVT

Opex_EVT(
    sector_name="Commodity Traders",
    threshold_percentile=0.95,
    min_exceedances=30,
    run_threshold_diagnostics=True,   # Generate diagnostic plots
    use_auto_threshold=False           # Use fixed threshold for now
)
```

**Output**: `Opex_CT_EVT_Threshold_Selection.pdf` with 4 diagnostic plots per segment

**Workflow**:
1. Run analysis with fixed threshold
2. Review threshold selection PDF
3. Identify if fixed threshold is appropriate
4. Decide whether to use auto-selection

---

### Option 2: Use Automated Selection

```python
Opex_EVT(
    sector_name="Commodity Traders",
    threshold_percentile=0.95,  # Ignored (auto-selected)
    min_exceedances=30,
    run_threshold_diagnostics=True,   # Still generate plots
    use_auto_threshold=True            # Use optimal threshold per segment
)
```

**Behavior**:
- Each segment gets optimal threshold
- Thresholds can differ by segment
- Recommendations saved to Excel

---

### Option 3: Interactive Selection (Advanced)

```python
from opex_evt import select_threshold_interactive
import pandas as pd

# Load and prepare data
data = pd.read_csv("your_data.csv")
segment_data = data[data['segment'] == 'CT_Energy']

# Run interactive selection
result = select_threshold_interactive(
    data=segment_data,
    segment_name="CT_Energy",
    value_col='delta_opex/rev'
)

print(f"Recommended threshold: {result['optimal_threshold']}")
print(f"Alternative thresholds: {result['all_candidates']}")
```

---

## Interpreting Diagnostic Plots

### Plot 1: Mean Residual Life

```
 MRL
  │         ╱────────  ← Linear (good!)
  │       ╱
  │    ╱──
  │  ╱
  │╱
  └──────────────────> Threshold

✓ GOOD: Linear above optimal threshold
❌ BAD: Curved upward (threshold too low)
❌ BAD: Erratic (threshold too high)
```

**Action**:
- If linear → Threshold is appropriate
- If curved → Increase threshold
- If noisy → Decrease threshold or check data

---

### Plot 2: Shape Parameter Stability

```
  ξ
  │
  │  •──•──•──•──•  ← Stable (good!)
  │           •
  │     •───•
  │ •──•
  └──────────────────> Threshold

✓ GOOD: Flat line with narrow CI
❌ BAD: Trending upward (threshold too low)
❌ BAD: Wide CI (threshold too high)
```

**Action**:
- If stable → Threshold is good
- If trending → Adjust threshold up
- If noisy → Need more data or lower threshold

---

### Plot 3: Modified Scale

```
 σ-ξu
  │
  │  •──•──•──•  ← Constant (good!)
  │
  │     •──•───•
  │  •──
  └──────────────────> Threshold

✓ GOOD: Approximately constant
❌ BAD: Trending (GPD not appropriate)
```

**Action**:
- If constant → GPD is valid
- If trending → Consider alternative threshold or model

---

### Plot 4: Goodness-of-Fit

```
p-value
  │         •  •  •  •  ← Above 0.05 (good!)
  │     •  •
0.05├─ • •  ─ ─ ─ ─ ─ ─  ← Critical value
  │ •  •
  │•
  └──────────────────────> Threshold

✓ GOOD: p-value > 0.05
❌ BAD: p-value < 0.05 (poor fit)
```

**Action**:
- If above 0.05 → Good fit
- If below 0.05 → Try different threshold
- Multiple good thresholds → Use other criteria

---

## Recommended Threshold Summary

The 5th panel shows automated recommendation:

```
╔═══════════════════════════════════════════╗
║   RECOMMENDED THRESHOLD                   ║
╚═══════════════════════════════════════════╝

Optimal Threshold: 0.1458
Percentile: 94.8%
Number of Exceedances: 67

GPD Parameters (at optimal threshold):
  • Shape (ξ): 0.2134
  • Scale (σ): 0.0487

Selection Scores:
  • Stability: 0.856
  • Goodness-of-Fit: 0.712
  • Exceedance Balance: 0.902
  • Composite: 0.824

Method: automated_composite

Alternative Thresholds to Consider:
  • 96.2% (score: 0.809)
  • 93.5% (score: 0.791)
  • 97.1% (score: 0.768)
```

**Interpretation**:
- **Optimal threshold**: Primary recommendation
- **Composite score**: Closer to 1 is better
- **Alternatives**: Nearby options if you want to adjust
- **Scores**: Which criteria drive the selection

---

## Decision Framework

### When to Accept Automated Selection

✅ Accept if ALL these conditions met:
1. Stability score > 0.7
2. GOF score > 0.5 (p-value > 0.05)
3. Exceedance balance > 0.6 (30-150 exceedances)
4. Composite score > 0.7
5. MRL plot shows linearity
6. Shape parameter stable

### When to Manually Adjust

⚠️ Consider manual adjustment if:
- Automated threshold gives < 20 exceedances
- Automated threshold gives > 200 exceedances
- MRL plot not linear at recommended threshold
- Shape parameter unstable
- Domain knowledge suggests different threshold

### Manual Adjustment Guidelines

```
If automated suggests:   Consider:
─────────────────────────────────────────
< 90th percentile     → Too low, increase to 92-95%
90-95th percentile    → Usually good, use as-is
95-97th percentile    → Optimal range for financial data
97-99th percentile    → Good if enough data (>50 exceedances)
> 99th percentile     → Too high, decrease to 97-98%
```

---

## Common Scenarios & Solutions

### Scenario 1: Insufficient Data

**Problem**:
```
Segment: CT_Metals
Data points: 127
Automated threshold: 98.2% (only 12 exceedances)
```

**Solution**:
1. Lower threshold to 90-93rd percentile
2. Pool similar segments
3. Use longer time horizon
4. Accept higher bias (fewer exceedances = higher variance)

---

### Scenario 2: Heavy-Tailed Data

**Problem**:
```
Shape parameter: ξ = 0.67 (very heavy tail)
Modified scale: trending upward
GOF p-value: 0.02 (poor fit)
```

**Solution**:
1. Increase threshold (move further into tail)
2. Check for outliers/data errors
3. Consider alternative distributions (e.g., Burr)
4. Apply more aggressive dampening

---

### Scenario 3: Multiple Modes

**Problem**:
```
MRL plot: Two distinct linear regions
Parameter stability: Stable at two different levels
```

**Solution**:
1. Segment data by regime (e.g., crisis vs normal)
2. Use mixture models
3. Choose higher threshold to focus on extreme regime
4. Model separately by time period

---

### Scenario 4: Contradicting Diagnostics

**Problem**:
```
MRL: Linear at 93rd percentile
Parameter stability: Stable at 96th percentile
GOF: Best fit at 95th percentile
```

**Solution**:
1. Use automated composite score (balances all)
2. Prioritize parameter stability (most important)
3. Test sensitivity: run models with all three thresholds
4. Choose threshold with best backtesting performance

---

## Best Practices

### 1. Always Generate Diagnostics First
```python
# First run: Generate diagnostics
Opex_EVT(sector, run_threshold_diagnostics=True, use_auto_threshold=False)

# Review plots, then decide:
Opex_EVT(sector, run_threshold_diagnostics=True, use_auto_threshold=True)
```

### 2. Compare Multiple Thresholds
```python
# Test sensitivity
for pct in [0.90, 0.92, 0.95, 0.97]:
    Opex_EVT(sector, threshold_percentile=pct, use_auto_threshold=False)
    # Compare results
```

### 3. Validate with Backtesting
- Check coverage accuracy
- Run Kupiec test
- Compare 2008-2009 performance
- Best threshold = best backtesting, not best diagnostics

### 4. Document Rationale
Record in your analysis:
- Which threshold was selected
- Why (automated vs manual)
- What diagnostics supported the choice
- Any adjustments made and why

### 5. Segment-Specific Thresholds
Different segments may need different thresholds:
```
CT_Energy: 95.2% (heavy-tailed, many observations)
CT_Metals: 92.8% (fewer observations)
CT_Agriculture: 96.5% (very heavy tail)
```

Use `use_auto_threshold=True` to allow this flexibility.

---

## Troubleshooting

### Issue: "Automated selection returns 99th percentile"

**Diagnosis**: Not enough data for lower thresholds
**Solutions**:
1. Lower minimum exceedances: `min_exceedances=20`
2. Pool segments
3. Use empirical fallback (automatic)

---

### Issue: "Shape parameter unstable across all thresholds"

**Diagnosis**: Data may not follow GPD
**Solutions**:
1. Check for outliers
2. Apply dampening
3. Consider Block Maxima (GEV) instead
4. Segment by time period

---

### Issue: "GOF test fails for all thresholds"

**Diagnosis**: GPD not appropriate
**Solutions**:
1. Try higher thresholds (deeper in tail)
2. Check data for errors
3. Consider alternative distributions
4. Validate model with backtesting (GOF not always decisive)

---

### Issue: "Different segments suggest wildly different thresholds"

**Diagnosis**: Heterogeneity in tail behavior
**Solutions**:
1. This is expected and good!
2. Use `use_auto_threshold=True` for segment-specific thresholds
3. Document differences in report
4. Validate each segment separately

---

## Excel Output Reference

### Threshold_Selection Sheet

| Column | Description |
|--------|-------------|
| Segment | Segment name |
| Recommended_Threshold | Optimal threshold value |
| Recommended_Percentile | Percentile of threshold |
| N_Exceedances | Number of exceedances at threshold |
| Selection_Method | How threshold was selected |
| Used | Whether recommendation was applied |

### EVT_Model_Summary Sheet

Includes threshold selection info if available:
- **Threshold**: Actual threshold used
- **Threshold_Percentile**: Percentile used
- **Recommended_Threshold**: Automated recommendation
- **Recommended_Percentile**: Recommended percentile

---

## Further Reading

### Academic References

1. **Scarrott, C., & MacDonald, A.** (2012). "A review of extreme value threshold estimation and uncertainty quantification." *REVSTAT Statistical Journal*, 10(1), 33-60.

2. **Dupuis, D. J.** (1999). "Exceedances over high thresholds: A guide to threshold selection." *Extremes*, 1(3), 251-261.

3. **Guillou, A., & Hall, P.** (2001). "A diagnostic for selecting the threshold in extreme value analysis." *Journal of the Royal Statistical Society: Series B*, 63(2), 293-305.

### Practical Guides

- Coles, S. (2001). *An Introduction to Statistical Modeling of Extreme Values*. Springer. (Chapter 4: Threshold Models)

- McNeil, A. J., Frey, R., & Embrechts, P. (2015). *Quantitative Risk Management*. Princeton University Press. (Chapter 7)

---

## Summary Checklist

Before finalizing threshold selection:

- [ ] Generated threshold diagnostic plots
- [ ] Reviewed MRL plot for linearity
- [ ] Checked parameter stability plots
- [ ] Verified GOF test results
- [ ] Examined recommended threshold summary
- [ ] Considered alternative thresholds
- [ ] Validated with backtesting
- [ ] Documented rationale
- [ ] Checked segment-specific needs
- [ ] Compared to empirical distribution

**Remember**: There is no single "correct" threshold - it's a balance of statistical rigor, data availability, and practical considerations. When in doubt, test multiple thresholds and choose based on backtesting performance!

---

## Quick Reference: Threshold Selection Commands

```python
# 1. Generate diagnostics only (recommended first)
Opex_EVT(
    sector_name="Commodity Traders",
    threshold_percentile=0.95,
    run_threshold_diagnostics=True,
    use_auto_threshold=False
)

# 2. Use automated selection
Opex_EVT(
    sector_name="Commodity Traders",
    threshold_percentile=0.95,  # Ignored
    run_threshold_diagnostics=True,
    use_auto_threshold=True  # Uses optimal threshold per segment
)

# 3. Test specific threshold
Opex_EVT(
    sector_name="Commodity Traders",
    threshold_percentile=0.93,  # Test 93rd percentile
    run_threshold_diagnostics=False,
    use_auto_threshold=False
)

# 4. Interactive selection (advanced)
from opex_evt import select_threshold_interactive
result = select_threshold_interactive(data, segment_name="CT_Energy")
```

---

**Happy threshold selecting!** 📊🎯
