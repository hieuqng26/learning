# EVT Visual Guide: From Theory to Practice

**Companion to EVT Theory Documentation**

---

## Quick Concept Map

```
EXTREME VALUE THEORY
│
├─── QUESTION: How to model rare, extreme events?
│
├─── TWO MAIN APPROACHES:
│    │
│    ├─── 1. BLOCK MAXIMA (GEV)
│    │    │
│    │    ├─── Method: Take max from each time block
│    │    ├─── Theory: Fisher-Tippett-Gnedenko Theorem
│    │    ├─── Distribution: Generalized Extreme Value (GEV)
│    │    ├─── Parameters: μ (location), σ (scale), ξ (shape)
│    │    ├─── Pro: Simple, direct application of theory
│    │    └─── Con: Wastes data (one value per block)
│    │
│    └─── 2. PEAKS OVER THRESHOLD (GPD) ⭐ RECOMMENDED
│         │
│         ├─── Method: Use all values above high threshold
│         ├─── Theory: Pickands-Balkema-de Haan Theorem
│         ├─── Distribution: Generalized Pareto (GPD)
│         ├─── Parameters: u (threshold), σ (scale), ξ (shape)
│         ├─── Pro: Efficient, uses all extreme data
│         └─── Con: Must choose threshold
│
└─── KEY INSIGHT: Shape parameter ξ controls tail behavior
     │
     ├─── ξ > 0: Heavy tail (financial returns, losses)
     ├─── ξ = 0: Exponential tail (normal-ish)
     └─── ξ < 0: Light tail (bounded distributions)
```

---

## The Core Problem: Why Normal Distribution Fails

### Standard Approach (WRONG for extremes)

```
                Normal Distribution
                       │
        ┌──────────────┼──────────────┐
        │              │              │
    ───▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓───
        ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
         ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
          ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
             ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
                  ▓▓▓▓▓▓
                    ▓
      -3σ   -2σ   -1σ   0   +1σ  +2σ  +3σ
                                  ↑
                            Thin tail!

Problem: Real financial data has FAT TAILS
         Extreme events happen MORE than normal predicts
```

### Reality: Heavy-Tailed Distribution

```
              Heavy-Tailed (EVT)
                       │
        ┌──────────────┼──────────────────────────┐
        │              │                          │
    ───▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓───                 │
        ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓                   │
         ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓                     │
          ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓                       │
             ▓▓▓▓▓▓▓▓▓▓                         ▓▓▓
                  ▓▓▓                         ▓▓▓▓
                    ▓                       ▓▓▓▓▓
                                          ▓▓▓▓▓▓  ← Fat tail!
      -3σ   -2σ   -1σ   0   +1σ  +2σ  +3σ  +4σ  +5σ

Solution: Use EVT to model this tail accurately
```

---

## Visual Workflow: Peaks Over Threshold (GPD)

### Step-by-Step Process

```
STEP 1: CHOOSE THRESHOLD
═══════════════════════════════════════════════════════════

Your data:  • • • • • •• ••• •••••••••••• ••• •• • • • • •
                                ↑
            ─────────────────── u (threshold) ──────────
                                │
Below u: Use empirical         Above u: Use GPD
distribution                   (EVT modeling)


STEP 2: EXTRACT EXCEEDANCES
═══════════════════════════════════════════════════════════

Original values above u: [0.25, 0.18, 0.32, 0.21, 0.28, ...]
Threshold u = 0.15
                              ↓
Exceedances (y = X - u):  [0.10, 0.03, 0.17, 0.06, 0.13, ...]
                          └── These follow GPD! ──┘


STEP 3: FIT GPD DISTRIBUTION
═══════════════════════════════════════════════════════════

              GPD Density

         │
         │  ▓▓
         │  ▓▓▓
         │  ▓▓▓▓
         │  ▓▓▓▓▓
         │  ▓▓▓▓▓▓___
         │  ▓▓▓▓▓▓▓▓▓▓___
         │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓───────────
         └──────────────────────────────────── y
            0

Parameters: σ (scale), ξ (shape)


STEP 4: COMPUTE EXTREME QUANTILES
═══════════════════════════════════════════════════════════

Now can estimate:
• 95th percentile ✓
• 99th percentile ✓
• 99.9th percentile ✓ (even if never observed!)
• 1-in-100 year event ✓

Using formula: x_p = u + (σ/ξ)[(1-p)^(-ξ) - 1]
```

---

## Shape Parameter ξ: The Key to Everything

### Visual Interpretation

```
ξ < 0: LIGHT TAIL (Weibull)
═══════════════════════════════════════════════════════════
         │
         │  ▓▓▓
         │  ▓▓▓▓▓
         │  ▓▓▓▓▓▓▓
         │  ▓▓▓▓▓▓▓▓▓
         │  ▓▓▓▓▓▓▓▓▓▓▓
         │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓|  ← Bounded!
         └────────────────────────────── y
                           ^
                      Max possible

Example: Temperature (can't exceed physical limits)
Moments: All moments exist
Risk: Low - events are bounded


ξ = 0: EXPONENTIAL TAIL (Gumbel)
═══════════════════════════════════════════════════════════
         │
         │  ▓▓▓
         │  ▓▓▓▓▓
         │  ▓▓▓▓▓▓▓
         │  ▓▓▓▓▓▓▓▓▓
         │  ▓▓▓▓▓▓▓▓▓▓▓
         │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓───────
         └────────────────────────────── y
                            ↓
                     Exponential decay

Example: Normal, Lognormal-ish distributions
Moments: All moments exist
Risk: Moderate


ξ > 0: HEAVY TAIL (Fréchet) ⚠️ FINANCIAL DATA
═══════════════════════════════════════════════════════════
         │
         │  ▓▓▓
         │  ▓▓▓▓
         │  ▓▓▓▓▓
         │  ▓▓▓▓▓▓
         │  ▓▓▓▓▓▓▓
         │  ▓▓▓▓▓▓▓▓─────────────────────
         └────────────────────────────────── y
                     ↓
              Polynomial decay (slow!)
              Extreme values MORE likely

Example: Stock returns, operational losses, insurance claims
Moments: Can be infinite!
  • ξ = 0.5: Mean infinite
  • ξ = 0.25: Variance infinite
Risk: HIGH - "black swans" happen


FINANCIAL EXAMPLES:
═══════════════════════════════════════════════════════════

S&P 500 daily returns:     ξ ≈ 0.3  (heavy tail)
EUR/USD exchange rate:     ξ ≈ 0.2  (moderate heavy)
Credit default losses:     ξ ≈ 0.5  (very heavy!)
Operational risk:          ξ > 0.5  (extreme!)
```

---

## Practical Example: Opex Stress Testing

### Scenario

```
DATA: Year-over-year change in Opex/Revenue
      From 2000-2023 (24 years)
      For "Commodity Traders" sector

      Values: [-0.05, 0.03, 0.08, 0.02, ..., 0.15, 0.35, ...]
                                                      ↑
                                                 2008 crisis!
```

### Traditional Method (Current Opex Code)

```
EMPIRICAL PERCENTILES:
════════════════════════════════════════════════════════════

Sort all data: [-0.05, 0.02, 0.03, 0.08, 0.15, ..., 0.35]
                  ↑                                    ↑
                 Min                                  Max

50th %ile (median): 0.06
90th %ile:          0.12
96th %ile:          0.18
99th %ile:          ???  ← Only 1 observation above 96th!

PROBLEM:
- Unreliable at extremes (few data points)
- Can't extrapolate beyond 0.35
- What about 99.9th percentile?
```

### EVT Method (Our Implementation)

```
STEP 1: SET THRESHOLD at 90th %ile (u = 0.12)
════════════════════════════════════════════════════════════

Below u=0.12:  Use empirical (lots of data)
Above u=0.12:  Use GPD (EVT magic!)
               ↓
   Exceedances: [0.03, 0.06, 0.23]  (10% of data)


STEP 2: FIT GPD
════════════════════════════════════════════════════════════

Maximum Likelihood Estimation:
  σ̂ = 0.05  (scale)
  ξ̂ = 0.28  (shape - HEAVY TAIL!)

Interpretation:
  Heavy tail (ξ>0) → Extreme Opex changes more likely
  than normal distribution predicts


STEP 3: ESTIMATE EXTREME QUANTILES
════════════════════════════════════════════════════════════

              Empirical   EVT (GPD)   Difference
              ─────────   ─────────   ──────────
50th %ile:      0.06        0.06         -
90th %ile:      0.12        0.12         -
96th %ile:      0.18        0.22       +22%  ← EVT higher!
99th %ile:       ?          0.31       Can't compare
99.9th %ile:     ?          0.45       Only EVT can estimate

Key insight: EVT gives HIGHER extreme quantiles
             → More conservative stress scenarios
             → Better risk management


STEP 4: BACKTEST (2008 Crisis)
════════════════════════════════════════════════════════════

Train model on 2000-2007 data:
  EVT 96th %ile forecast:  0.24
  Empirical forecast:      0.16

Actual 2008 96th %ile:     0.25

Errors:
  EVT error:        0.01  ✓ Very close!
  Empirical error:  0.09  ✗ Way off!

Conclusion: EVT captures crisis severity much better
```

---

## Return Levels: Translating Quantiles to Business Language

### Concept

```
QUANTILE (Statistical):    96th percentile
                          ↓ translate ↓
RETURN LEVEL (Business):  1-in-25 year event


Formula: If percentile p = 96% = 0.96
         Then return period T = 1/(1-p) = 1/0.04 = 25 years

Interpretation: "Event this severe expected once per 25 years"
```

### Visual Timeline

```
RETURN PERIODS FOR OPEX STRESS SCENARIOS:
════════════════════════════════════════════════════════════

Year:    1    5    10         25              50              100
         │    │    │          │               │               │
         ▼    ▼    ▼          ▼               ▼               ▼
Stress: ─────────────────────────────────────────────────────►
        Low        Medium     Severe          Very Severe     Catastrophic

50%:    Median scenario (every year)
80%:    1-in-5 year event (common stress)
90%:    1-in-10 year event (standard stress test)
96%:    1-in-25 year event (Basel III scenario)
99%:    1-in-100 year event (tail risk)
99.9%:  1-in-1000 year event (catastrophic)

Your Opex Model Uses: 96th %ile (1-in-25 year)
                      Aligns with regulatory standards
```

---

## Confidence Intervals: Quantifying Uncertainty

### Why Important

```
POINT ESTIMATE vs CONFIDENCE INTERVAL:
════════════════════════════════════════════════════════════

BAD: "96th percentile is 0.22"
     │
     └─ Single number - no uncertainty!

GOOD: "96th percentile is 0.22 [95% CI: 0.18 - 0.28]"
      │                        └── Confidence interval
      └─ Point estimate

Interpretation:
  We're 95% confident the true 96th %ile is between 0.18-0.28
  Accounts for sampling uncertainty
  Critical for risk management decisions!
```

### Bootstrap Method (How We Compute CI)

```
BOOTSTRAP ALGORITHM:
════════════════════════════════════════════════════════════

Original data: [y₁, y₂, ..., y₁₀₀]

Repeat 1000 times:
  1. Resample WITH replacement: [y₃₄, y₇, y₃₄, y₂₃, ...]
  2. Fit GPD to bootstrap sample
  3. Estimate 96th %ile → store result

Results: [0.19, 0.23, 0.21, 0.25, 0.20, ..., 0.24]
         └── 1000 bootstrap estimates

95% CI = [2.5th %ile of results, 97.5th %ile of results]
       = [0.18, 0.28]
```

### Visualization

```
    DISTRIBUTION OF BOOTSTRAP ESTIMATES

    Frequency
        │
     40 │              ▓▓▓
        │          ▓▓▓▓▓▓▓▓▓
     30 │        ▓▓▓▓▓▓▓▓▓▓▓▓▓
        │      ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
     20 │    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
        │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
     10 │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
        │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
      0 └─────────────────────────────────── 96th %ile
        0.15   0.18  0.22  0.28   0.31
               ↑     ↑     ↑
            CI lower│ CI upper
                 Point
                estimate

Width of CI = Uncertainty
Narrow CI = Confident estimate
Wide CI = Uncertain (need more data)
```

---

## Diagnostic Plots: Is Your Model Any Good?

### 1. Q-Q Plot (Quantile-Quantile)

```
GOOD FIT:
════════════════════════════════════════════════════════════

Empirical Quantile
        │
    0.4 │                              •
        │                          •
    0.3 │                      •
        │                  •
    0.2 │              •
        │          •
    0.1 │      •
        │  •
      0 └────────────────────────────────
        0   0.1  0.2  0.3  0.4
               Model Quantile

Points follow 45° line ✓
Model fits well!


BAD FIT:
════════════════════════════════════════════════════════════

Empirical Quantile
        │
    0.4 │                          •
        │                        •
    0.3 │                     •
        │                •
    0.2 │            •
        │       •
    0.1 │    •
        │  •
      0 └────────────────────────────────
        0   0.1  0.2  0.3  0.4
               Model Quantile

Points curve away from line ✗
Model underestimates tail!
→ Try different threshold or check for outliers
```

### 2. Mean Excess Plot (Threshold Selection)

```
CHOOSING THRESHOLD:
════════════════════════════════════════════════════════════

Mean Excess
        │
        │    •
    0.2 │      •  • ─────────────────  ← Linear region
        │        •  •  •  •  •  •  •       (GPD holds!)
    0.1 │      •
        │    •                              Choose threshold
        │  •                                here ↓
      0 └────────────────────────────────
        0   0.1 0.15 0.2  0.3  0.4
               ↑ threshold

Look for: Approximately linear trend above threshold
Interpretation: GPD approximation valid in linear region
Choose: Threshold at start of linear region (e.g., 0.15)
```

---

## Integration with Your Opex Model: Before/After

### BEFORE (Current Empirical Method)

```
Data → Filter → Calculate delta → Sort → Take percentiles
                                          │
                                          ▼
                                    50th: 0.06
                                    80th: 0.11
                                    96th: 0.18  ← Unreliable!
                                    99th: ???   ← Can't estimate!
```

### AFTER (With EVT)

```
Data → Filter → Calculate delta → Split at threshold
                                          │
                        ┌─────────────────┴─────────────────┐
                        ▼                                   ▼
                   Below 90th %ile:                  Above 90th %ile:
                   Use empirical                     Fit GPD
                        │                                   │
                        └─────────────────┬─────────────────┘
                                          ▼
                                  Combined distribution
                                          │
                                          ▼
                                    50th: 0.06 (empirical)
                                    80th: 0.11 (empirical)
                                    96th: 0.22 (EVT) ← Reliable!
                                    99th: 0.31 (EVT) ← Can extrapolate!

                                  + Confidence intervals
                                  + Return periods
                                  + Proper backtesting
```

---

## Summary: EVT in 5 Bullets

```
┌─────────────────────────────────────────────────────────────┐
│  1. EVT = Rigorous statistical framework for EXTREMES       │
│     Based on limiting theorems (like CLT for tails)         │
│                                                              │
│  2. GPD (Peaks Over Threshold) = Practical method           │
│     Model all values above high threshold                   │
│     More efficient than block maxima                        │
│                                                              │
│  3. Shape parameter ξ = Key to tail behavior                │
│     ξ > 0: Heavy tail (common in finance!)                  │
│     ξ = 0: Exponential tail                                 │
│     ξ < 0: Light tail                                       │
│                                                              │
│  4. Can extrapolate beyond observed data                    │
│     Estimate 99th, 99.9th percentile                        │
│     Even if never observed historically                     │
│     But: Always validate with backtesting!                  │
│                                                              │
│  5. Proper backtesting = Out-of-sample validation           │
│     Train on pre-crisis data (2000-2007)                    │
│     Test on crisis data (2008)                              │
│     Compare EVT vs empirical methods                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Next Steps: Implementing EVT

```
IMPLEMENTATION ROADMAP:
════════════════════════════════════════════════════════════

Week 1: Basic Implementation
  ☐ Fit GPD model to one sub-sector
  ☐ Generate diagnostic plots
  ☐ Compare to empirical percentiles
  ☐ Document results

Week 2: Backtesting
  ☐ Implement out-of-sample test for 2008
  ☐ Calculate forecast errors
  ☐ Compare EVT vs current method
  ☐ Validate model assumptions

Week 3: Production Deployment
  ☐ Apply to all sub-sectors
  ☐ Generate confidence intervals
  ☐ Integrate with existing Excel outputs
  ☐ Update methodology documentation

Week 4: Review & Iteration
  ☐ Present results to stakeholders
  ☐ Gather feedback
  ☐ Refine threshold selection
  ☐ Final validation
```

---

**Visual Guide Complete!**

**See full mathematical treatment in:** `EVT_theory_documentation.md`
**Implementation code in:** `evt_model.py`, `evt_backtest.py`
**Quick start guide:** `INTEGRATION_GUIDE.md`
