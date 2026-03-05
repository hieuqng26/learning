# Bug #9: Circular Logic in Percentile Rank - Deep Dive

## The Problem in Simple Terms

**Current code** (lines 920-926):
```python
# Get ALL historical data including 2008
model_data = subset["delta_opex/rev"]  # Includes years 2000-2023 (including 2008!)

# Calculate 2008 crisis mean
crisis_data2008 = subset[subset["Year"].isin([2008])]
x_crisis_08 = crisis_data2008["delta_opex/rev"].mean()  # e.g., 0.25

# Calculate where 2008 falls in the FULL distribution
percentile_rank_08 = (model_data <= x_crisis_08).mean()
# ↑ This INCLUDES 2008 data points in the comparison!
```

**This is circular logic** - you're asking: "Where does 2008 crisis rank in a distribution that includes 2008 crisis data?"

---

## Why This Is Wrong (The "Exam Analogy")

### Analogy: Exam Score Ranking

Imagine you want to know how hard an exam was by seeing where the top student scored relative to historical performance.

**❌ Circular (Current Code):**
```
Question: "Where does Student A's 2008 score (95%) rank historically?"
Method: Look at all scores from 2000-2023 INCLUDING 2008
Result: "95% is at the 88th percentile"
```

**Problem:** You're including Student A's 2008 score in the historical data you're comparing against! This artificially inflates the percentile.

**✅ Correct (Fixed Code):**
```
Question: "Where does Student A's 2008 score (95%) rank historically?"
Method: Look at scores from 2000-2007 ONLY (before 2008)
Result: "95% is at the 94th percentile"
```

This tells you: "Based on pre-2008 history, a 95% score was a very rare event (94th percentile)."

---

## Why This Matters for Stress Testing

### Scenario: 2008 Financial Crisis

**Goal:** Determine how severe the 2008 crisis was relative to historical norms.

**Method 1 (Current - WRONG):**
```python
all_data = data_2000_to_2023  # Includes 2008
x_crisis_08 = 0.25  # Mean delta in 2008
percentile_rank = (all_data <= 0.25).mean()  # = 0.92 (92nd percentile)
```

**Interpretation:** "2008 crisis was at the 92nd percentile of historical experience"

**Method 2 (Correct - FIXED):**
```python
pre_crisis_data = data_2000_to_2007  # EXCLUDES 2008
x_crisis_08 = 0.25  # Mean delta in 2008
percentile_rank = (pre_crisis_data <= 0.25).mean()  # = 0.98 (98th percentile)
```

**Interpretation:** "2008 crisis was at the 98th percentile - a 1-in-50 year event based on pre-crisis data"

**Difference:** 92nd vs 98th percentile! This dramatically changes your risk assessment.

---

## Concrete Example with Real Numbers

### Sample Dataset

| Year | Company | delta_opex/rev |
|------|---------|----------------|
| 2006 | A       | 0.05           |
| 2006 | B       | 0.08           |
| 2006 | C       | 0.03           |
| 2007 | A       | 0.06           |
| 2007 | B       | 0.04           |
| 2007 | C       | 0.07           |
| **2008** | **A** | **0.35** ← Crisis! |
| **2008** | **B** | **0.42** ← Crisis! |
| **2008** | **C** | **0.28** ← Crisis! |
| 2009 | A       | 0.15           |
| 2009 | B       | 0.12           |

### Calculate 2008 Crisis Mean

```python
x_crisis_08 = mean([0.35, 0.42, 0.28]) = 0.35
```

### Method 1: Current (Circular) Logic

```python
all_data = [0.05, 0.08, 0.03, 0.06, 0.04, 0.07, 0.35, 0.42, 0.28, 0.15, 0.12]
#                                              ↑  Including 2008 crisis data!

# Count how many values ≤ 0.35
values_below = [0.05, 0.08, 0.03, 0.06, 0.04, 0.07, 0.35, 0.28, 0.15, 0.12]
# 10 out of 11 values are ≤ 0.35

percentile_rank_08 = 10 / 11 = 0.909 (90.9th percentile)
```

**Problem:** Three 2008 crisis data points (0.35, 0.42, 0.28) are in the denominator AND being compared to themselves!

### Method 2: Correct (Exclude 2008)

```python
pre_crisis_data = [0.05, 0.08, 0.03, 0.06, 0.04, 0.07, 0.15, 0.12]
#                  ↑  Only 2006-2007 + 2009 data (NO 2008!)

# Count how many values ≤ 0.35
values_below = [0.05, 0.08, 0.03, 0.06, 0.04, 0.07, 0.15, 0.12]
# All 8 values are ≤ 0.35

percentile_rank_08 = 8 / 8 = 1.00 (100th percentile)
```

**Interpretation:** 0.35 is worse than EVERY pre-2008 observation → True extreme event!

**Difference:**
- Circular method: 90.9th percentile (seems moderately severe)
- Correct method: 100th percentile (truly unprecedented)

---

## Impact on Your Stress Testing Model

### Current Methodology (Opex Model)

Your code calculates:

1. **Historical Percentile Rank** (Bug #9):
   ```python
   percentile_rank_08 = (model_data <= x_crisis_08).mean()
   ```
   - Used to assess: "How rare was the 2008 crisis?"

2. **Return Period**:
   ```python
   tail_prob_08 = 1 - percentile_rank_08
   return_period_08 = 1 / tail_prob_08
   ```
   - If percentile_rank = 0.90 → return_period = 10 years
   - If percentile_rank = 0.98 → return_period = 50 years

### Impact of Circular Logic

| Scenario | Circular Logic | Correct Logic | Impact |
|----------|----------------|---------------|--------|
| Percentile Rank | 92nd percentile | 98th percentile | **6% difference** |
| Return Period | 1-in-13 years | 1-in-50 years | **4x difference!** |
| Severity Assessment | "Moderately severe" | "Extreme rare event" | Completely changes conclusion |

**Result:** Your model **underestimates** crisis severity because it dilutes extreme events by including them in their own baseline.

---

## The Fix: Proper Implementation

### Option 1: Simple Exclusion (Bug Report Suggestion)

```python
# Calculate 2008 crisis value
crisis_data2008 = subset[subset["Year"].isin([2008])]
x_crisis_08 = crisis_data2008["delta_opex/rev"].mean()

# Calculate 2009 crisis value
crisis_data2009 = subset[subset["Year"].isin([2009])]
x_crisis_09 = crisis_data2009["delta_opex/rev"].mean()

# ✅ FIX: Exclude crisis year from baseline
model_data_excl_08 = subset[~subset["Year"].isin([2008])]["delta_opex/rev"]
percentile_rank_08 = (model_data_excl_08 <= x_crisis_08).mean()

model_data_excl_09 = subset[~subset["Year"].isin([2009])]["delta_opex/rev"]
percentile_rank_09 = (model_data_excl_09 <= x_crisis_09).mean()

# Calculate return periods
tail_prob_08 = 1 - percentile_rank_08
tail_prob_09 = 1 - percentile_rank_09
return_period_08 = 1 / tail_prob_08 if tail_prob_08 > 0 else np.inf
return_period_09 = 1 / tail_prob_09 if tail_prob_09 > 0 else np.inf
```

**Why exclude each year separately?**
- When evaluating 2008, exclude 2008 but keep 2009
- When evaluating 2009, exclude 2009 but keep 2008
- Each crisis year is evaluated against "everything else"

---

### Option 2: Proper Out-of-Sample Backtesting (Recommended)

**Even better:** Use only PRE-CRISIS data (true forecasting scenario)

```python
def backtest_crisis_percentile(data, crisis_year, lookback_years=10):
    """
    Calculate where crisis year ranks using ONLY pre-crisis data

    This simulates: "If we built the model in late 2007,
    how extreme would 2008 crisis appear?"
    """
    # Training data: Only years BEFORE crisis
    train_start = crisis_year - lookback_years
    train_data = data[
        (data["Year"] >= train_start) &
        (data["Year"] < crisis_year)  # ← Strict inequality
    ]["delta_opex/rev"].dropna()

    # Test data: The crisis year
    crisis_data = data[data["Year"] == crisis_year]["delta_opex/rev"].dropna()
    x_crisis = crisis_data.mean()

    # Calculate percentile rank using ONLY training data
    percentile_rank = (train_data <= x_crisis).mean()

    # Calculate return period
    tail_prob = 1 - percentile_rank
    return_period = 1 / tail_prob if tail_prob > 0 else np.inf

    return {
        'crisis_value': x_crisis,
        'percentile_rank': percentile_rank,
        'tail_probability': tail_prob,
        'return_period': return_period,
        'train_n': len(train_data),
        'crisis_n': len(crisis_data)
    }

# Usage
result_2008 = backtest_crisis_percentile(subset, crisis_year=2008, lookback_years=10)
result_2009 = backtest_crisis_percentile(subset, crisis_year=2009, lookback_years=10)

print(f"2008 Crisis Analysis:")
print(f"  Crisis value: {result_2008['crisis_value']:.4f}")
print(f"  Historical percentile: {result_2008['percentile_rank']:.2%}")
print(f"  Return period: {result_2008['return_period']:.1f} years")
```

**Why this is better:**
1. ✅ True out-of-sample test (no look-ahead bias)
2. ✅ Simulates real forecasting scenario
3. ✅ Can be used for walk-forward validation
4. ✅ More conservative/accurate risk assessment

---

## Complete Fixed Code for Your Opex Model

Replace lines 914-926 with:

```python
# Crisis data for 2008 and 2009
crisis_data2008 = subset[subset["Year"].isin([2008])]
crisis_data2009 = subset[subset["Year"].isin([2009])]
x_crisis_08 = crisis_data2008["delta_opex/rev"].mean()
x_crisis_09 = crisis_data2009["delta_opex/rev"].mean()

# ─────────────────────────────────────────────────────────────────
# OPTION 1: EXCLUDE-SELF METHOD (Simpler Fix)
# ─────────────────────────────────────────────────────────────────

# Exclude crisis year from its own baseline
model_data_excl_08 = subset[~subset["Year"].isin([2008])]["delta_opex/rev"].dropna()
model_data_excl_09 = subset[~subset["Year"].isin([2009])]["delta_opex/rev"].dropna()

# Calculate percentile ranks
percentile_rank_08 = (model_data_excl_08 <= x_crisis_08).mean()
percentile_rank_09 = (model_data_excl_09 <= x_crisis_09).mean()

# Calculate tail probabilities and return periods
tail_prob_08 = 1 - percentile_rank_08
tail_prob_09 = 1 - percentile_rank_09
return_period_08 = 1 / tail_prob_08 if tail_prob_08 > 0 else np.inf
return_period_09 = 1 / tail_prob_09 if tail_prob_09 > 0 else np.inf  # ← Fixed Bug #8 too!

# ─────────────────────────────────────────────────────────────────
# OPTION 2: TRUE OUT-OF-SAMPLE METHOD (Better Practice)
# ─────────────────────────────────────────────────────────────────

# Use only pre-2008 data to evaluate 2008
pre_2008_data = subset[subset["Year"] < 2008]["delta_opex/rev"].dropna()
percentile_rank_08_oos = (pre_2008_data <= x_crisis_08).mean()
tail_prob_08_oos = 1 - percentile_rank_08_oos
return_period_08_oos = 1 / tail_prob_08_oos if tail_prob_08_oos > 0 else np.inf

# Use only pre-2009 data to evaluate 2009
pre_2009_data = subset[subset["Year"] < 2009]["delta_opex/rev"].dropna()
percentile_rank_09_oos = (pre_2009_data <= x_crisis_09).mean()
tail_prob_09_oos = 1 - percentile_rank_09_oos
return_period_09_oos = 1 / tail_prob_09_oos if tail_prob_09_oos > 0 else np.inf

# ─────────────────────────────────────────────────────────────────
# OPTION 3: ROLLING WINDOW (Most Realistic)
# ─────────────────────────────────────────────────────────────────

# Use 10 years BEFORE crisis (1998-2007 for 2008 crisis)
lookback_years = 10

window_2008_data = subset[
    (subset["Year"] >= 2008 - lookback_years) &
    (subset["Year"] < 2008)
]["delta_opex/rev"].dropna()

percentile_rank_08_window = (window_2008_data <= x_crisis_08).mean()
tail_prob_08_window = 1 - percentile_rank_08_window
return_period_08_window = 1 / tail_prob_08_window if tail_prob_08_window > 0 else np.inf

window_2009_data = subset[
    (subset["Year"] >= 2009 - lookback_years) &
    (subset["Year"] < 2009)
]["delta_opex/rev"].dropna()

percentile_rank_09_window = (window_2009_data <= x_crisis_09).mean()
tail_prob_09_window = 1 - percentile_rank_09_window
return_period_09_window = 1 / tail_prob_09_window if tail_prob_09_window > 0 else np.inf

# ─────────────────────────────────────────────────────────────────
# Choose which method to use in your output
# ─────────────────────────────────────────────────────────────────

# I recommend Option 2 (True Out-of-Sample) for most accurate risk assessment
# Use these values in your result dictionary:
# percentile_rank_08 = percentile_rank_08_oos
# percentile_rank_09 = percentile_rank_09_oos
# etc.
```

---

## Which Method Should You Use?

| Method | Pros | Cons | Recommended For |
|--------|------|------|-----------------|
| **Option 1: Exclude-Self** | Simple, uses most data | Still has some look-ahead bias (uses post-crisis data) | Quick fix, minimal code change |
| **Option 2: Pre-Crisis Only** | True out-of-sample, realistic | Uses less data | **Best for backtesting, most accurate** |
| **Option 3: Rolling Window** | Realistic, consistent window | May miss early data, more complex | Production stress testing |

**My recommendation:** Use **Option 2 (Pre-Crisis Only)** for your backtesting.

---

## Verification: How to Check If Your Fix Works

```python
# After implementing the fix, verify:

print(f"2008 Crisis Analysis:")
print(f"  Crisis mean value: {x_crisis_08:.4f}")
print(f"  Training data range: {pre_2008_data.min():.4f} to {pre_2008_data.max():.4f}")
print(f"  Percentile rank: {percentile_rank_08_oos:.2%}")
print(f"  Return period: {return_period_08_oos:.1f} years")

# Sanity checks:
assert x_crisis_08 not in pre_2008_data.values, "Crisis data leaked into training!"
assert pre_2008_data.max() < x_crisis_08, "Crisis should be more extreme than training data max"
assert percentile_rank_08_oos > 0.90, "2008 crisis should be at least 90th percentile"
```

---

## Summary

### Why Exclude Crisis Year Data?

1. **Circular Logic**: Can't use test data in the model evaluating that test data
2. **Inflated Percentiles**: Including crisis data makes the crisis appear less severe
3. **Wrong Return Periods**: Drastically underestimates true rarity (1-in-13 vs 1-in-50 years)
4. **Invalid Backtesting**: Not a true out-of-sample test

### How to Fix It Properly

**Minimum Fix:**
```python
model_data_excl_08 = subset[~subset["Year"].isin([2008])]["delta_opex/rev"].dropna()
percentile_rank_08 = (model_data_excl_08 <= x_crisis_08).mean()
```

**Recommended Fix:**
```python
pre_2008_data = subset[subset["Year"] < 2008]["delta_opex/rev"].dropna()
percentile_rank_08 = (pre_2008_data <= x_crisis_08).mean()
```

This ensures your stress testing model provides **accurate, conservative risk estimates** rather than artificially downplaying crisis severity.
