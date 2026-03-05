# EVT Threshold Selection: Complete Practical Guide

**The Most Important Decision in EVT Modeling**

---

## Table of Contents

1. [The Fundamental Problem](#1-the-fundamental-problem)
2. [Theoretical Guidelines](#2-theoretical-guidelines)
3. [Practical Selection Methods](#3-practical-selection-methods)
4. [Sample Size Requirements](#4-sample-size-requirements)
5. [Diagnostic Tools](#5-diagnostic-tools)
6. [Decision Framework](#6-decision-framework)
7. [Common Pitfalls](#7-common-pitfalls)
8. [Case Study: Your Opex Data](#8-case-study-your-opex-data)

---

## 1. The Fundamental Problem

### 1.1 The Threshold Dilemma

**Central Question:** Where should we set threshold $u$?

**The Trade-off:**

```
LOW THRESHOLD (e.g., 75th percentile)
═══════════════════════════════════════════════════════════
Data below:  ████████████████████████████ (75%)
Data above:  ██████                        (25% = MANY exceedances)
             ↑
         threshold

✅ Advantages:
  • Many exceedances (say, 250 out of 1000)
  • Low variance in parameter estimates
  • Stable estimates

❌ Disadvantages:
  • GPD approximation may not hold yet
  • Bias: Not in true "tail" region
  • Model misspecification

Result: PRECISE but WRONG estimates
        (Low variance, high bias)


HIGH THRESHOLD (e.g., 98th percentile)
═══════════════════════════════════════════════════════════
Data below:  ████████████████████████████████████████ (98%)
Data above:  █                                         (2% = FEW exceedances)
                                                       ↑
                                                   threshold

✅ Advantages:
  • GPD approximation holds well
  • Low bias: In true tail region
  • Correct model

❌ Disadvantages:
  • Few exceedances (say, 20 out of 1000)
  • High variance in estimates
  • Unstable parameters

Result: CORRECT but IMPRECISE estimates
        (High variance, low bias)


OPTIMAL THRESHOLD (e.g., 90th percentile)
═══════════════════════════════════════════════════════════
Data below:  ████████████████████████████████ (90%)
Data above:  ████                              (10% = ADEQUATE exceedances)
                                               ↑
                                           threshold

✅ Sweet spot:
  • GPD approximation starts to hold
  • Enough exceedances for stability
  • Balance bias-variance trade-off

Goal: Find this optimal threshold!
```

### 1.2 Mathematical Framework

**Pickands-Balkema-de Haan Theorem** states:
$$\lim_{u \to \infty} P(X - u \leq y \mid X > u) = H(y; \sigma(u), \xi)$$

**Key insight:** Approximation improves as $u \to \infty$

**But:** As $u$ increases, sample size $N_u$ decreases
$$N_u = \#\{i: X_i > u\}$$

**The Mathematics:**

**Bias:**
$$\text{Bias}(u) \approx A(u) \quad \text{where } A(u) \to 0 \text{ as } u \to \infty$$

**Variance:**
$$\text{Var}(\hat{\xi}, \hat{\sigma} \mid u) \approx \frac{C}{N_u}$$

**Mean Squared Error:**
$$\text{MSE}(u) = \text{Bias}^2(u) + \text{Var}(u) = A^2(u) + \frac{C}{N_u}$$

**Optimal $u$** minimizes MSE:
$$u^* = \arg\min_u \left[A^2(u) + \frac{C}{N_u}\right]$$

---

## 2. Theoretical Guidelines

### 2.1 Academic Rules of Thumb

**From Literature:**

#### Embrechts et al. (1997)
> "Choose threshold such that 5-10% of data are exceedances"

**Translation:**
- 90th-95th percentile
- For n=1000: 50-100 exceedances

#### Coles (2001)
> "Aim for at least 50 exceedances, preferably 100+"

**Translation:**
- If n=500: 90th percentile (50 exc.)
- If n=1000: 90th percentile (100 exc.)
- If n=2000: 95th percentile (100 exc.)

#### Scarrott & MacDonald (2012)
> "No single threshold is optimal. Try multiple and assess stability."

**Translation:** Test thresholds from 85th to 95th percentile

---

### 2.2 Sample Size Requirements

**Minimum Requirements:**

```
╔═══════════════════════════════════════════════════════════╗
║  RULE OF THUMB: Minimum Exceedances                      ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  Absolute Minimum:  30 exceedances                        ║
║  Adequate:          50 exceedances                        ║
║  Good:              100 exceedances                       ║
║  Excellent:         200+ exceedances                      ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
```

**Why These Numbers?**

**Statistical Theory:**
- MLE asymptotic theory requires $N_u \to \infty$
- Rule: $N_u \geq 30$ for asymptotic approximations to hold
- Better: $N_u \geq 50$ for reliable confidence intervals

**Empirical Studies:**
- Simulations show stable estimates with $N_u \geq 50$
- Below 30: Parameter estimates highly variable
- Below 20: Should not use EVT

### 2.3 Percentage Guidelines

**By Total Sample Size:**

| Total Sample $n$ | Min Exceedances | Threshold Percentile | % of Data |
|-----------------|-----------------|---------------------|-----------|
| 100             | 10-20           | 80th-90th           | 10-20%    |
| 200             | 20-40           | 80th-90th           | 10-20%    |
| 500             | 50-75           | 85th-90th           | 10-15%    |
| 1,000           | 50-100          | 90th-95th           | 5-10%     |
| 2,000           | 100-150         | 92.5th-95th         | 5-7.5%    |
| 5,000           | 100-200         | 95th-98th           | 2-5%      |
| 10,000+         | 100-300         | 97th-99th           | 1-3%      |

**General Rule:**
$$\text{Threshold Percentile} \approx 1 - \frac{50 \text{ to } 100}{n}$$

**Examples:**
- $n = 500$: Threshold $\approx 1 - 100/500 = 0.80$ (80th to 90th)
- $n = 1000$: Threshold $\approx 1 - 100/1000 = 0.90$ (90th)
- $n = 2000$: Threshold $\approx 1 - 100/2000 = 0.95$ (95th)

---

## 3. Practical Selection Methods

### 3.1 Method 1: Mean Excess Plot (Primary Method)

**Theory:**
For GPD, mean excess function is linear:
$$e(u) = E[X - u \mid X > u] = \frac{\sigma + \xi u}{1 - \xi}$$

**Procedure:**

```python
import numpy as np
import matplotlib.pyplot as plt

def mean_excess_plot(data, thresholds=None):
    """
    Generate mean excess plot for threshold selection

    Look for: Linear trend above appropriate threshold
    """
    data_clean = data[~np.isnan(data)]

    if thresholds is None:
        # Test thresholds from 50th to 98th percentile
        thresholds = np.percentile(data_clean, np.linspace(50, 98, 50))

    mean_excesses = []
    n_exceedances = []

    for u in thresholds:
        exceedances = data_clean[data_clean > u] - u
        if len(exceedances) > 0:
            mean_excesses.append(exceedances.mean())
            n_exceedances.append(len(exceedances))
        else:
            mean_excesses.append(np.nan)
            n_exceedances.append(0)

    # Plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Mean excess plot
    ax1.plot(thresholds, mean_excesses, 'b-', linewidth=2)
    ax1.scatter(thresholds, mean_excesses, c=n_exceedances,
                cmap='viridis', s=30, alpha=0.6)
    ax1.set_xlabel('Threshold u')
    ax1.set_ylabel('Mean Excess e(u)')
    ax1.set_title('Mean Excess Plot\n(Look for linear region)')
    ax1.grid(True, alpha=0.3)

    # Add reference lines for common percentiles
    for pct in [0.80, 0.85, 0.90, 0.95]:
        thresh = np.percentile(data_clean, pct * 100)
        ax1.axvline(thresh, color='red', linestyle='--',
                   alpha=0.3, label=f'{int(pct*100)}th %ile')

    # Number of exceedances
    ax2.plot(thresholds, n_exceedances, 'r-', linewidth=2)
    ax2.axhline(50, color='green', linestyle='--',
               label='Min recommended (50)')
    ax2.axhline(100, color='blue', linestyle='--',
               label='Good (100)')
    ax2.set_xlabel('Threshold u')
    ax2.set_ylabel('Number of Exceedances')
    ax2.set_title('Sample Size Above Threshold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig
```

**How to Interpret:**

```
GOOD MEAN EXCESS PLOT:
════════════════════════════════════════════════════════════

Mean Excess e(u)
        │
    0.3 │    •
        │      •
    0.2 │        • • ───────────────  ← Linear region
        │          • • • • • • •         (GPD holds!)
    0.1 │        •
        │      •                         Choose threshold
        │    •                           at START of
    0.0 └────────────────────────────    linear region ↓
        0.1   0.15  0.2  0.3  0.4
              ↑ threshold range

Interpretation:
  • Before 0.15: Curved (GPD doesn't hold yet)
  • After 0.15:  Linear (GPD valid)
  • Choose:      u ≈ 0.15 (start of linear trend)


BAD MEAN EXCESS PLOT:
════════════════════════════════════════════════════════════

Mean Excess e(u)
        │
    0.3 │    •
        │      •  •
    0.2 │          •  •
        │              •   •  ← No clear linear region!
    0.1 │                •  •  •
        │                      •
    0.0 └────────────────────────────
        0.1   0.15  0.2  0.3  0.4

Interpretation:
  • Highly variable (too few exceedances at each u)
  • No stable region
  • Need more data OR lower threshold
```

---

### 3.2 Method 2: Parameter Stability Plot

**Theory:**
If threshold is in correct region, GPD parameters should be stable as threshold increases.

**Procedure:**

```python
def parameter_stability_plot(data, thresholds=None):
    """
    Plot GPD parameter estimates across different thresholds

    Look for: Stable (flat) region for ξ and σ
    """
    from evt_model import GPDModel

    data_clean = data[~np.isnan(data)]

    if thresholds is None:
        # Test from 75th to 95th percentile
        percentiles = np.linspace(75, 95, 20)
        thresholds = np.percentile(data_clean, percentiles)

    shape_params = []
    scale_params = []
    n_exceedances = []

    for u in thresholds:
        try:
            model = GPDModel(data_clean, threshold=u)
            model.fit()
            shape_params.append(model.shape)
            scale_params.append(model.scale)
            n_exceedances.append(model.n_exceedances)
        except:
            shape_params.append(np.nan)
            scale_params.append(np.nan)
            n_exceedances.append(0)

    # Plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # Shape parameter
    ax1.plot(thresholds, shape_params, 'bo-', linewidth=2, markersize=6)
    ax1.axhline(np.nanmean(shape_params), color='red',
               linestyle='--', label='Mean ξ')
    ax1.fill_between(thresholds,
                     np.nanmean(shape_params) - 2*np.nanstd(shape_params),
                     np.nanmean(shape_params) + 2*np.nanstd(shape_params),
                     alpha=0.2, color='red', label='±2 SD')
    ax1.set_ylabel('Shape Parameter (ξ)', fontsize=12)
    ax1.set_title('Parameter Stability: Shape ξ\n(Should be relatively flat)',
                 fontsize=14)
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Scale parameter (modified)
    # For better comparison, plot σ̃ = σ + ξ(u - u_min)
    u_min = thresholds[0]
    scale_modified = [s + xi*(u - u_min)
                     for s, xi, u in zip(scale_params, shape_params, thresholds)]

    ax2.plot(thresholds, scale_modified, 'go-', linewidth=2, markersize=6)
    ax2.axhline(np.nanmean(scale_modified), color='red',
               linestyle='--', label='Mean σ̃')
    ax2.fill_between(thresholds,
                     np.nanmean(scale_modified) - 2*np.nanstd(scale_modified),
                     np.nanmean(scale_modified) + 2*np.nanstd(scale_modified),
                     alpha=0.2, color='red', label='±2 SD')
    ax2.set_xlabel('Threshold u', fontsize=12)
    ax2.set_ylabel('Modified Scale (σ̃)', fontsize=12)
    ax2.set_title('Parameter Stability: Modified Scale σ̃\n(Should be relatively flat)',
                 fontsize=14)
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig
```

**How to Interpret:**

```
GOOD STABILITY PLOT:
════════════════════════════════════════════════════════════

Shape ξ
    │
0.3 │ • • • ───────────────────  ← Flat, stable
    │                              Choose any threshold
0.2 │                              in this range
    │
0.1 │
    └─────────────────────────────
     85th  90th      95th
          Percentile

Interpretation:
  • Parameters stable from 90th-95th percentile
  • GPD model is valid in this range
  • Choose 90th (more data) or 95th (better tail fit)
  • Trade-off: 90th safer


BAD STABILITY PLOT:
════════════════════════════════════════════════════════════

Shape ξ
    │
0.5 │                          •
    │                     •        ← Highly variable!
0.3 │         •      •               No stable region
    │    •      •
0.1 │ •
    └─────────────────────────────
     85th  90th      95th

Interpretation:
  • No stable region found
  • High variability (small sample issue)
  • Try: Lower threshold OR need more data
```

---

### 3.3 Method 3: Multiple Threshold Comparison

**Idea:** Fit GPD at several thresholds and compare quantile estimates

**Procedure:**

```python
def threshold_comparison(data, percentiles=[0.80, 0.85, 0.90, 0.95],
                        target_quantile=0.96):
    """
    Compare quantile estimates across different thresholds

    Look for: Stable estimates (agreement across thresholds)
    """
    from evt_model import GPDModel

    data_clean = data[~np.isnan(data)]
    results = []

    for pct in percentiles:
        threshold = np.percentile(data_clean, pct * 100)

        try:
            model = GPDModel(data_clean, threshold=threshold)
            model.fit()

            # Estimate target quantile
            q_est = model.quantile(target_quantile)
            ci_lower, ci_upper = model.confidence_interval(target_quantile)

            results.append({
                'Threshold %ile': f'{int(pct*100)}th',
                'Threshold Value': threshold,
                'N Exceedances': model.n_exceedances,
                'Shape (ξ)': model.shape,
                'Scale (σ)': model.scale,
                f'{int(target_quantile*100)}th %ile': q_est,
                'CI Lower': ci_lower,
                'CI Upper': ci_upper,
                'CI Width': ci_upper - ci_lower
            })
        except Exception as e:
            print(f"Error at {pct}: {e}")

    return pd.DataFrame(results)
```

**Example Output:**

```
Threshold Comparison for 96th Percentile Estimation:
═══════════════════════════════════════════════════════════════════════════

Threshold  Threshold   N Exc.  Shape   Scale   96th %ile   CI Width
  %ile      Value                (ξ)     (σ)    Estimate
─────────────────────────────────────────────────────────────────────────
 80th       0.12       100      0.25    0.045    0.215      0.042
 85th       0.15       75       0.27    0.048    0.221      0.051
 90th       0.18       50       0.28    0.051    0.224      0.068   ← Best
 95th       0.24       25       0.31    0.062    0.238      0.125   ← Too few

Interpretation:
  • 80th-90th: Estimates stable around 0.22
  • 95th: Higher estimate (0.24), wider CI (fewer exceedances)
  • Best choice: 90th percentile
    - Reasonable sample size (50)
    - Stable estimate
    - Moderate CI width
```

---

### 3.4 Method 4: Automated Selection

**Hill Plot Method** (for heavy tails only, ξ > 0):

```python
def hill_plot(data, max_k=None):
    """
    Hill estimator plot for shape parameter

    For heavy-tailed data (ξ > 0)
    Look for: Stable plateau region
    """
    data_sorted = np.sort(data)[::-1]  # Descending order
    n = len(data_sorted)

    if max_k is None:
        max_k = min(n // 2, 500)  # Don't use more than half the data

    k_values = np.arange(10, max_k)
    hill_estimates = []

    for k in k_values:
        # Hill estimator: ξ̂ = (1/k) Σ log(X_i / X_{k+1})
        if data_sorted[k] > 0:
            xi_hat = np.mean(np.log(data_sorted[:k] / data_sorted[k]))
            hill_estimates.append(xi_hat)
        else:
            hill_estimates.append(np.nan)

    # Convert k to threshold percentile
    percentiles = (1 - k_values / n) * 100

    plt.figure(figsize=(12, 6))
    plt.plot(percentiles, hill_estimates, 'b-', linewidth=2)
    plt.xlabel('Threshold Percentile')
    plt.ylabel('Hill Estimator (ξ)')
    plt.title('Hill Plot for Shape Parameter\n(Look for stable plateau)')
    plt.grid(True, alpha=0.3)
    plt.axhline(np.nanmean(hill_estimates), color='red',
               linestyle='--', label='Mean ξ')

    # Mark suggested region (where it stabilizes)
    stable_region = np.where(
        (hill_estimates > np.nanmean(hill_estimates) - np.nanstd(hill_estimates)) &
        (hill_estimates < np.nanmean(hill_estimates) + np.nanstd(hill_estimates))
    )[0]

    if len(stable_region) > 0:
        plt.axvspan(percentiles[stable_region[0]],
                   percentiles[stable_region[-1]],
                   alpha=0.2, color='green', label='Stable region')

    plt.legend()
    plt.show()

    return k_values, hill_estimates
```

---

## 4. Sample Size Requirements

### 4.1 Minimum Sample Sizes by Use Case

```
╔══════════════════════════════════════════════════════════════╗
║  SAMPLE SIZE REQUIREMENTS                                    ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  USE CASE                  MIN TOTAL    MIN EXCEEDANCES     ║
║  ─────────────────────────────────────────────────────────  ║
║  Exploratory analysis          100             10-20        ║
║  Basic risk assessment         200             20-30        ║
║  Operational use               500             50           ║
║  Regulatory reporting        1,000            100           ║
║  High-stakes decisions       2,000            100-200       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

### 4.2 Your Opex Stress Testing Case

**Your Situation:**
- **Purpose:** Regulatory stress testing (96th percentile)
- **Target quantile:** 96th-99th percentile
- **Decision stakes:** High (capital allocation)

**Recommended Sample Sizes:**

| Sub-sector | Min Total Obs | Target Threshold | Min Exceedances |
|------------|--------------|------------------|-----------------|
| Each sub-sector | 300 | 85th-90th | 30-45 |
| Each sub-sector | 500 | 90th | 50 |
| **Each sub-sector** | **800** | **90th-92nd** | **60-80** ✓ Best |
| Each sub-sector | 1,000+ | 90th-95th | 50-100 |

**Current Assessment:**
If you have ~500 observations per sub-sector:
- ✅ **Sufficient** for 90th percentile threshold (50 exceedances)
- ⚠️ **Marginal** for 95th percentile (25 exceedances - too few)
- ❌ **Insufficient** for 97th percentile (15 exceedances - do not use)

---

### 4.3 What If You Don't Have Enough Data?

**Option 1: Lower the Threshold**
```
Instead of 95th → Use 85th or 90th percentile
Trade-off: More bias, less variance
```

**Option 2: Pool Data Across Sub-segments**
```
Combine similar sub-sectors
Trade-off: Lose granularity, gain sample size
```

**Option 3: Bayesian EVT**
```
Use informative priors from literature/other sectors
Reduces data requirements
Trade-off: Requires prior specification
```

**Option 4: Bootstrap Aggregation**
```
Generate bootstrap samples, fit multiple models
Average predictions
Trade-off: Computational cost
```

**Option 5: Use Empirical Percentiles (Honestly)**
```
If < 50 exceedances available:
  → EVT may not be reliable
  → Use empirical with wide confidence intervals
  → Report uncertainty clearly
```

---

## 5. Diagnostic Tools

### 5.1 Comprehensive Diagnostic Checklist

After choosing threshold, verify:

```python
def diagnostic_checklist(data, threshold):
    """
    Run all diagnostic checks for threshold validation
    """
    from evt_model import GPDModel

    model = GPDModel(data, threshold=threshold)
    model.fit()

    print("="*70)
    print("EVT THRESHOLD DIAGNOSTIC CHECKLIST")
    print("="*70)

    # 1. Sample size check
    print(f"\n1. SAMPLE SIZE:")
    print(f"   Total observations:    {len(data)}")
    print(f"   Exceedances (N_u):     {model.n_exceedances}")
    print(f"   Exceedance rate:       {model.n_exceedances/len(data):.1%}")

    status = "✓ PASS" if model.n_exceedances >= 50 else "⚠ WARNING" if model.n_exceedances >= 30 else "❌ FAIL"
    print(f"   Assessment:            {status}")
    if model.n_exceedances < 50:
        print(f"   → Recommendation: Lower threshold to get ≥50 exceedances")

    # 2. Parameter values
    print(f"\n2. PARAMETER ESTIMATES:")
    print(f"   Shape (ξ):             {model.shape:.3f}")
    print(f"   Scale (σ):             {model.scale:.3f}")

    # Check if ξ is reasonable
    if -0.5 < model.shape < 0.5:
        print(f"   Assessment:            ✓ Reasonable range")
    else:
        print(f"   Assessment:            ⚠ Unusual value - check data")

    # 3. QQ plot
    print(f"\n3. GOODNESS OF FIT:")
    print(f"   Generating QQ plot...")
    fig = model.diagnostic_plots()
    plt.savefig('diagnostic_plots.png', dpi=150, bbox_inches='tight')
    print(f"   → Saved to diagnostic_plots.png")
    print(f"   → Check: Points should follow 45° line in QQ plot")

    # 4. Estimate key quantiles
    print(f"\n4. QUANTILE ESTIMATES:")
    for p in [0.90, 0.95, 0.96, 0.99]:
        q = model.quantile(p)
        ci_low, ci_high = model.confidence_interval(p, n_bootstrap=200)
        ci_width = ci_high - ci_low
        rel_width = ci_width / q * 100

        print(f"   {int(p*100)}th %ile: {q:.4f} [{ci_low:.4f}, {ci_high:.4f}]")
        print(f"               CI width: {ci_width:.4f} ({rel_width:.1f}% of estimate)")

        if rel_width > 50:
            print(f"               ⚠ Wide CI - consider lower threshold")

    # 5. Return levels
    print(f"\n5. RETURN LEVELS:")
    for T in [10, 25, 50, 100]:
        rl = model.return_level(T)
        print(f"   1-in-{T:3d} year event: {rl:.4f}")

    print("\n" + "="*70)
    print("RECOMMENDATION:")

    if model.n_exceedances >= 50 and -0.5 < model.shape < 0.5:
        print("✓ Threshold appears appropriate")
        print("  → Proceed with this threshold")
        print("  → Review diagnostic plots to confirm")
    elif model.n_exceedances >= 30:
        print("⚠ Threshold is marginal")
        print("  → Consider lowering threshold slightly")
        print("  → Report wider confidence intervals")
    else:
        print("❌ Threshold too high")
        print("  → Lower threshold to get ≥50 exceedances")
        print("  → Or pool data across segments")

    print("="*70)

    return model
```

---

## 6. Decision Framework

### 6.1 Step-by-Step Selection Process

```
┌─────────────────────────────────────────────────────────────┐
│  THRESHOLD SELECTION WORKFLOW                               │
└─────────────────────────────────────────────────────────────┘

STEP 1: Determine Target Sample Size
───────────────────────────────────────────────────────────────
Question: How many exceedances do I need?

  Minimum:   30  (absolute floor)
  Adequate:  50  (recommended minimum)
  Good:      100 (preferred)

Decision: Target ≥ 50 exceedances
          → For n=500, this means 90th percentile


STEP 2: Generate Mean Excess Plot
───────────────────────────────────────────────────────────────
Code: mean_excess_plot(data)

Look for: Linear region starting around target threshold

Result: Linear region starts at ~85th percentile
        → Candidate range: 85th-95th percentile


STEP 3: Check Parameter Stability
───────────────────────────────────────────────────────────────
Code: parameter_stability_plot(data,
                               thresholds=percentiles(85, 95))

Look for: Flat region for ξ and σ̃

Result: Parameters stable from 88th-93rd percentile
        → Narrow down to: 88th-93rd


STEP 4: Compare Multiple Thresholds
───────────────────────────────────────────────────────────────
Code: threshold_comparison(data,
                          percentiles=[0.88, 0.90, 0.92])

Look for: Similar quantile estimates, reasonable CI widths

Result:
  88th: q₉₆ = 0.218, CI width = 0.055
  90th: q₉₆ = 0.221, CI width = 0.063  ← Most stable
  92nd: q₉₆ = 0.219, CI width = 0.078

Decision: Choose 90th percentile
          → Balance of stability and sample size


STEP 5: Validate with Diagnostics
───────────────────────────────────────────────────────────────
Code: diagnostic_checklist(data, threshold_90th)

Check:
  ✓ N_u = 50 (adequate)
  ✓ ξ = 0.28 (reasonable)
  ✓ QQ plot looks good
  ✓ CI widths acceptable (<30% of estimate)

Final Decision: USE 90TH PERCENTILE ✓


STEP 6: Sensitivity Analysis
───────────────────────────────────────────────────────────────
Test: Run with 85th and 95th percentile

Compare:
  85th: q₉₆ = 0.215 (slightly lower, more bias)
  90th: q₉₆ = 0.221 ← BASELINE
  95th: q₉₆ = 0.235 (higher, wider CI)

Conclusion: Results stable within ±7%
            → Robust to threshold choice
            → Proceed with 90th percentile
```

---

### 6.2 Quick Decision Tree

```
START: Do you have data?
│
├─ Total observations < 100?
│  └─ ❌ DO NOT USE EVT
│     Use empirical percentiles with caution
│
├─ 100 ≤ Total < 500?
│  ├─ Use threshold: 80th-85th percentile
│  └─ Expect: 20-50 exceedances (marginal)
│     Report: Wide confidence intervals
│
├─ 500 ≤ Total < 1,000?
│  ├─ Use threshold: 85th-90th percentile  ← YOUR CASE
│  └─ Expect: 50-75 exceedances (adequate)
│     Report: Moderate CI, validate with diagnostics
│
├─ 1,000 ≤ Total < 5,000?
│  ├─ Use threshold: 90th-95th percentile
│  └─ Expect: 50-150 exceedances (good)
│     Report: Narrow CI, high confidence
│
└─ Total ≥ 5,000?
   ├─ Use threshold: 95th-98th percentile
   └─ Expect: 100-250 exceedances (excellent)
      Report: Very precise estimates
```

---

## 7. Common Pitfalls

### 7.1 Mistakes to Avoid

**❌ MISTAKE #1: Threshold Mining**
```
BAD PRACTICE:
  1. Try threshold at 90th: p₉₆ = 0.22 (doesn't match desired value)
  2. Try threshold at 85th: p₉₆ = 0.18 (closer to what I want!)
  3. Use 85th percentile ← WRONG!

Reason: Cherry-picking threshold to get desired result
Impact: Biased estimates, invalid inference

CORRECT:
  1. Choose threshold using diagnostic plots
  2. Accept whatever estimate results
  3. Report uncertainty with CI
```

**❌ MISTAKE #2: Using Too Few Exceedances**
```
BAD:
  Total data: 200
  Threshold: 98th percentile
  Exceedances: 4  ← Too few!

Result: Highly unstable estimates

CORRECT:
  Total data: 200
  Threshold: 85th percentile
  Exceedances: 30  ← Minimum acceptable
```

**❌ MISTAKE #3: Ignoring Diagnostics**
```
BAD:
  "I'll just use 90th percentile because the textbook says so"
  → Never checks QQ plot, parameter stability, etc.

Result: May be fitting GPD where it doesn't apply

CORRECT:
  1. Try 90th as starting point
  2. Generate all diagnostic plots
  3. Adjust based on diagnostics
  4. Validate final choice
```

**❌ MISTAKE #4: Same Threshold for All Segments**
```
BAD:
  Sector A: n=1000 → Use 90th (100 exc.)
  Sector B: n=200  → Use 90th (20 exc.) ← Too few!

CORRECT:
  Sector A: n=1000 → Use 90th-95th (50-100 exc.)
  Sector B: n=200  → Use 80th-85th (30-40 exc.)

Adapt threshold to sample size!
```

**❌ MISTAKE #5: Forgetting Uncertainty**
```
BAD:
  Report: "96th percentile is 0.22"

CORRECT:
  Report: "96th percentile is 0.22 [95% CI: 0.18-0.28]"

Always quantify uncertainty!
```

---

### 7.2 Red Flags

**🚩 Warning Signs Your Threshold May Be Wrong:**

1. **Very few exceedances (< 30)**
   → Lower threshold or pool data

2. **Parameter estimates jumping around**
   → Unstable estimates, try different threshold

3. **Shape parameter |ξ| > 1**
   → Unusual, check for outliers or data errors

4. **QQ plot shows clear curvature**
   → GPD not fitting well, adjust threshold

5. **Confidence intervals > 50% of estimate**
   → Too much uncertainty, lower threshold

6. **Mean excess plot not linear**
   → Threshold may be too low or data not GPD

7. **Estimates change dramatically with small threshold changes**
   → Not in stable region, collect more data

---

## 8. Case Study: Your Opex Data

### 8.1 Your Specific Situation

**Context:**
- **Data:** Year-over-year change in Opex/Revenue
- **Sample size per sub-sector:** ~500-800 observations
- **Target quantiles:** 96th (1-in-25), 99th (1-in-100)
- **Purpose:** Regulatory stress testing
- **Segments:** Multiple sub-sectors (Chemicals, Energy, Metals, etc.)

### 8.2 Recommended Approach

#### Step 1: Baseline Assessment

```python
# For each sub-sector
for subsector in ['Chemicals', 'Energy', 'Metals', 'Others']:
    data = opex_data[opex_data['TOPS'] == subsector]['delta_opex/rev']

    print(f"\n{subsector}:")
    print(f"  Observations: {len(data)}")
    print(f"  Data range: [{data.min():.3f}, {data.max():.3f}]")

    # Test different thresholds
    for pct in [0.85, 0.90, 0.92]:
        threshold = data.quantile(pct)
        n_exc = (data > threshold).sum()
        print(f"  {int(pct*100)}th %ile (u={threshold:.3f}): {n_exc} exceedances")
```

**Expected Output:**
```
Chemicals:
  Observations: 650
  Data range: [-0.08, 0.42]
  85th %ile (u=0.145): 98 exceedances  ← Good
  90th %ile (u=0.172): 65 exceedances  ← Adequate
  92nd %ile (u=0.195): 52 exceedances  ← Minimum

Energy:
  Observations: 580
  Data range: [-0.12, 0.51]
  85th %ile (u=0.165): 87 exceedances  ← Good
  90th %ile (u=0.198): 58 exceedances  ← Adequate
  92nd %ile (u=0.224): 46 exceedances  ← Marginal
```

#### Step 2: Recommended Thresholds

```
╔══════════════════════════════════════════════════════════════╗
║  RECOMMENDED THRESHOLDS FOR YOUR OPEX MODEL                 ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Sub-sector    Sample Size    Threshold    N Exceedances   ║
║  ────────────────────────────────────────────────────────── ║
║  Chemicals        650          90th           65            ║
║  Energy           580          90th           58            ║
║  Metals           520          88th           62            ║
║  Others           450          85th           68            ║
║                                                              ║
║  GENERAL RULE: Adjust to get 50-70 exceedances             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

**Rationale:**
- Target 50-70 exceedances per sector
- Adjust percentile based on sample size
- Larger sectors → higher percentile
- Smaller sectors → lower percentile (to maintain sample size)

#### Step 3: Implementation Code

```python
def select_threshold_for_sector(data, target_exceedances=60):
    """
    Automatically select threshold to achieve target exceedances

    Parameters:
    -----------
    data : array-like
        The data series
    target_exceedances : int
        Desired number of exceedances (default 60)

    Returns:
    --------
    threshold : float
        Selected threshold
    percentile : float
        Percentile of threshold
    """
    n = len(data)

    # Target percentile
    target_pct = 1 - (target_exceedances / n)

    # Clip to reasonable range (80th-95th)
    target_pct = np.clip(target_pct, 0.80, 0.95)

    threshold = np.percentile(data, target_pct * 100)
    actual_exc = (data > threshold).sum()

    print(f"Data size: {n}")
    print(f"Target exceedances: {target_exceedances}")
    print(f"Selected threshold: {int(target_pct*100)}th percentile = {threshold:.4f}")
    print(f"Actual exceedances: {actual_exc}")

    return threshold, target_pct


# Usage for your Opex model
for subsector in subsectors:
    print(f"\n{'='*60}")
    print(f"Sub-sector: {subsector}")
    print(f"{'='*60}")

    data = opex_data[opex_data['TOPS'] == subsector]['delta_opex/rev'].dropna()

    # Auto-select threshold
    threshold, percentile = select_threshold_for_sector(data, target_exceedances=60)

    # Fit EVT model
    from evt_model import GPDModel
    model = GPDModel(data.values, threshold=threshold)
    model.fit()

    # Generate diagnostics
    fig = model.diagnostic_plots()
    plt.savefig(f'diagnostics_{subsector}.png', dpi=150, bbox_inches='tight')
    plt.close()

    # Report key results
    print(f"\nGPD Parameters:")
    print(f"  Shape (ξ): {model.shape:.3f}")
    print(f"  Scale (σ): {model.scale:.3f}")

    print(f"\nQuantile Estimates:")
    for p in [0.96, 0.99]:
        q = model.quantile(p)
        ci_low, ci_high = model.confidence_interval(p)
        print(f"  {int(p*100)}th %ile: {q:.4f} [{ci_low:.4f}, {ci_high:.4f}]")
```

---

### 8.3 Final Recommendations for Your Project

```
┌─────────────────────────────────────────────────────────────┐
│  YOUR OPEX MODEL: THRESHOLD SELECTION STRATEGY              │
└─────────────────────────────────────────────────────────────┘

PRIMARY RECOMMENDATION: Adaptive Threshold
═══════════════════════════════════════════════════════════════

  For each sub-sector:
    1. Calculate sample size n
    2. Set threshold to achieve 50-70 exceedances
    3. Typically: 88th-92nd percentile for n ≈ 500-800
    4. Validate with diagnostic plots
    5. Report actual threshold percentile used

  Why adaptive?
    ✓ Accounts for varying sample sizes
    ✓ Maintains statistical power
    ✓ Maximizes data use
    ✓ Sector-specific optimization


ALTERNATIVE: Fixed Threshold (Simpler)
═══════════════════════════════════════════════════════════════

  Use 90th percentile for ALL sub-sectors

  Pros:
    ✓ Simple, consistent
    ✓ Easy to explain
    ✓ Comparable across sectors

  Cons:
    ⚠ May have <50 exceedances for smaller sectors
    ⚠ Wastes data for larger sectors

  Acceptable if: All sectors have n > 500


VALIDATION CHECKLIST:
═══════════════════════════════════════════════════════════════

  For EACH sub-sector, verify:
    □ N_exceedances ≥ 50
    □ Shape parameter 0 < ξ < 0.5
    □ QQ plot shows good fit
    □ Parameter stability across similar thresholds
    □ 96th %ile CI width < 30% of estimate
    □ Mean excess plot shows linearity

  If any check fails → Adjust threshold or flag for review


REPORTING TEMPLATE:
═══════════════════════════════════════════════════════════════

  "For the [Sub-sector] segment (n = [N] observations),
   we selected the [X]th percentile as the EVT threshold,
   yielding [Y] exceedances above the threshold value of [U].

   The fitted GPD model has shape parameter ξ = [ξ] and
   scale parameter σ = [σ], indicating [heavy/moderate/light]
   tail behavior.

   Based on this model, the estimated 96th percentile is
   [Q96] with 95% confidence interval [CI_low, CI_high].

   Diagnostic plots (attached) confirm adequate model fit."
```

---

## 9. Summary & Quick Reference

### 9.1 Key Takeaways

```
╔══════════════════════════════════════════════════════════════╗
║  THRESHOLD SELECTION: THE ESSENTIALS                        ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  1. TARGET: 50-100 exceedances                              ║
║     Minimum: 30  |  Adequate: 50  |  Good: 100              ║
║                                                              ║
║  2. TYPICAL RANGE: 85th-95th percentile                     ║
║     Small samples (n<500):  80th-90th                       ║
║     Medium (n=500-1000):    85th-92nd  ← YOUR CASE          ║
║     Large (n>1000):         90th-95th                       ║
║                                                              ║
║  3. USE DIAGNOSTICS:                                        ║
║     • Mean excess plot (linearity)                          ║
║     • Parameter stability (flatness)                        ║
║     • QQ plot (goodness of fit)                            ║
║     • Confidence intervals (width)                          ║
║                                                              ║
║  4. ADAPT TO DATA:                                          ║
║     Different sectors → Different thresholds OK             ║
║     Prioritize: Adequate sample size > Fixed percentile     ║
║                                                              ║
║  5. VALIDATE:                                               ║
║     • Check all diagnostics                                 ║
║     • Test sensitivity to threshold                         ║
║     • Report uncertainty (CI)                               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

### 9.2 Decision Cheat Sheet

```
YOUR SITUATION → RECOMMENDED THRESHOLD
═══════════════════════════════════════════════════════════════

Sample Size     Typical Threshold    Exceedances    Confidence
────────────────────────────────────────────────────────────────
< 100           DON'T USE EVT        -              -
100-200         80th-85th            15-30          Low
200-500         85th-90th            20-50          Medium
500-1,000       88th-92nd ⭐         50-80          Good
1,000-2,000     90th-95th            50-150         Very Good
> 2,000         92nd-97th            60-200         Excellent
```

### 9.3 Final Recommendation for YOU

```
FOR YOUR OPEX STRESS TESTING MODEL:
═══════════════════════════════════════════════════════════════

RECOMMENDED THRESHOLD: 90th percentile (baseline)

RATIONALE:
  • Your sample sizes: ~500-800 per sector
  • This gives: 50-80 exceedances
  • Meets minimum standards (≥50)
  • Provides stable estimates
  • Industry standard for similar applications

ADJUSTMENT RULE:
  IF sub-sector has < 500 obs → Use 85th-88th %ile
  IF sub-sector has > 800 obs → Consider 92nd-95th %ile

VALIDATION:
  Generate diagnostic plots for EACH sector
  Verify:
    ✓ ≥50 exceedances
    ✓ Good QQ plot fit
    ✓ Reasonable ξ (0 < ξ < 0.5)
    ✓ CI width < 30% of estimate

IMPLEMENTATION:
  Use provided code in run_evt_analysis.py
  Reports will automatically adapt threshold if needed
```

---

**Document Complete**

**Version:** 1.0
**Last Updated:** March 2, 2026
**Next Review:** After first implementation run

For questions or issues, refer to:
- `evt_model.py` for implementation
- `EVT_theory_documentation.md` for mathematical details
- `EVT_visual_guide.md` for conceptual overview
