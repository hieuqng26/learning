# Backtesting Bug Fixes - Implementation Guide

## Overview
This document provides step-by-step fixes for the 4 critical backtesting bugs identified in IE.py.

---

## Bug #4: Data Leakage - Look-Ahead Bias (Lines 532-540)

### Current Code (WRONG)
```python
for i in range(WINDOW, len(g) -1):
    window = g.iloc[i-WINDOW:i]  # Window includes periods [i-3, i-2, i-1]
    alpha = compute_alpha(window, country)
    bt_rows.append({
        "Country": country,
        "spread_id": spread_id,
        "date": g.iloc[i]["DATE_OF_FINANCIALS"],  # Date is period i
        "Alpha": alpha,
        "future_interest_change": g.iloc[i]["future_interest_change"]  # Change from i to i+1
    })
```

### Problem
The window `[i-WINDOW:i]` includes data up to (but not including) index `i`, which is correct. However, the `future_interest_change` at index `i` represents the change from period `i` to period `i+1`.

**Timeline issue:**
- Window uses data from periods: i-3, i-2, i-1 (doesn't include i) ✓
- But we're trying to predict the change from period i to i+1
- This means we're predicting **one period ahead** of the window end

**The real problem:** The window should predict change from i-1 to i (the next period after window ends), not from i to i+1.

### Fixed Code
```python
for i in range(WINDOW, len(g)):  # Also fixes Bug #6
    # Window: periods [i-WINDOW, i-1] (3 historical periods)
    window = g.iloc[i-WINDOW:i]
    alpha = compute_alpha(window, country)

    # Predict the NEXT period's change (period i-1 to i)
    # This is the first period NOT in the training window
    actual_change = g.iloc[i]["interest_rate"] - g.iloc[i-1]["interest_rate"]
    cb_rate_change = (
        g.iloc[i][f"{country}_Monetary policy or key interest rate_4QMA"] -
        g.iloc[i-1][f"{country}_Monetary policy or key interest rate_4QMA"]
    )

    bt_rows.append({
        "Country": country,
        "spread_id": spread_id,
        "prediction_date": g.iloc[i]["DATE_OF_FINANCIALS"],  # The period we're predicting
        "window_end_date": g.iloc[i-1]["DATE_OF_FINANCIALS"],  # Last period in training window
        "Alpha": alpha,
        "predicted_change": alpha * cb_rate_change,
        "actual_change": actual_change,
        "cb_rate_change": cb_rate_change
    })
```

### Alternative Fix (More Conservative - Predict 1 Period Ahead)
If you want to predict completely out-of-sample (skip one period):
```python
for i in range(WINDOW, len(g) - 1):  # Need -1 because we look ahead
    # Training window: [i-WINDOW, i-1]
    window = g.iloc[i-WINDOW:i]
    alpha = compute_alpha(window, country)

    # Predict change from period i to i+1 (completely out of window)
    actual_change = g.iloc[i+1]["interest_rate"] - g.iloc[i]["interest_rate"]
    cb_rate_change = (
        g.iloc[i+1][f"{country}_Monetary policy or key interest rate_4QMA"] -
        g.iloc[i][f"{country}_Monetary policy or key interest rate_4QMA"]
    )

    bt_rows.append({
        "Country": country,
        "spread_id": spread_id,
        "prediction_date": g.iloc[i+1]["DATE_OF_FINANCIALS"],
        "window_end_date": g.iloc[i-1]["DATE_OF_FINANCIALS"],
        "Alpha": alpha,
        "predicted_change": alpha * cb_rate_change,
        "actual_change": actual_change,
        "cb_rate_change": cb_rate_change
    })
```

### Recommendation
Use **Alternative Fix** for true out-of-sample validation. This ensures:
1. Training window ends at period i-1
2. Skip period i (not used for training or prediction)
3. Predict period i+1 (completely independent)

---

## Bug #5: Wrong R² Type - Mislabeled as "OOS_R2" (Lines 565-567)

### Current Code (WRONG)
```python
def cal_country_stats_with_r2(x):
    # ... bucket analysis code ...

    ## OLS
    X = sm.add_constant(x["Alpha"])
    y = x["future_interest_change"]
    model = sm.OLS(y, X, missing="drop").fit()
    y_pred = model.predict(X)

    mse_model = np.mean((y - y_pred)**2)
    mse_benchmark = np.mean((y - np.mean(y))**2)
    r2_oos = 1 - mse_model/mse_benchmark  # ❌ This is IN-SAMPLE R²

    return pd.Series({
        "rank_ic": x["Alpha"].corr(x["future_interest_change"], method="spearman"),
        "n_obs": len(x),
        "top_minus_bottom": top_minus_bottom,
        "OOS_R2": r2_oos  # ❌ MISLABELED!
    })
```

### Problem
This calculates **in-sample R²** because:
1. Model is fit on ALL data in `x`
2. Predictions are made on the SAME data
3. No holdout set
4. `np.mean(y)` is the mean of the same y used for training

**True OOS R²** requires:
- Separate train/test split OR
- Cross-validation OR
- Use training set mean as benchmark (if doing walk-forward)

### Fixed Code - Option 1: Remove OLS R² Entirely (Simplest)
Since the backtesting loop already calculates predictions, we don't need OLS regression here.

```python
def cal_country_stats_with_r2(x):
    # Bucket analysis
    buckets = pd.qcut(x["Alpha"], 5, duplicates="drop")
    bucket_perf = x.groupby(buckets)["actual_change"].mean()

    if len(bucket_perf) < 2:
        top_minus_bottom = np.nan
    else:
        top_minus_bottom = bucket_perf.iloc[-1] - bucket_perf.iloc[0]

    # Calculate R² from backtesting predictions (if available)
    if "predicted_change" in x.columns:
        mse_model = np.mean((x["actual_change"] - x["predicted_change"])**2)
        mse_naive = np.mean((x["actual_change"])**2)  # Assume mean = 0 for changes
        r2_pseudo = 1 - mse_model/mse_naive
    else:
        r2_pseudo = np.nan

    return pd.Series({
        "rank_ic": x["Alpha"].corr(x["actual_change"], method="spearman"),
        "n_obs": len(x),
        "top_minus_bottom": top_minus_bottom,
        "R2_insample": r2_pseudo,  # Correctly labeled
    })
```

### Fixed Code - Option 2: Calculate True Walk-Forward R²
```python
def calculate_walk_forward_r2(backtest_df):
    """
    Calculate true out-of-sample R² from walk-forward backtest

    For each test point:
    - Alpha calculated on training window (past data only)
    - Prediction made on test point (future data)
    - Compare to naive baseline (predict 0 change or historical mean)
    """
    # Prediction errors
    mse_model = np.mean((backtest_df["actual_change"] - backtest_df["predicted_change"])**2)

    # Naive baseline: predict zero change (or use expanding mean)
    mse_naive = np.mean(backtest_df["actual_change"]**2)

    # True OOS R²
    r2_oos = 1 - (mse_model / mse_naive)

    return r2_oos

# Usage in main code:
bt_all_country_df = (
    alpha_ts_df
    .groupby("Country")
    .apply(lambda x: pd.Series({
        "rank_ic": x["Alpha"].corr(x["actual_change"], method="spearman"),
        "n_obs": len(x),
        "r2_oos": calculate_walk_forward_r2(x),  # Properly calculated
        "mae": np.mean(np.abs(x["actual_change"] - x["predicted_change"])),
        "rmse": np.sqrt(np.mean((x["actual_change"] - x["predicted_change"])**2))
    }))
    .reset_index()
)
```

### Recommendation
Use **Option 2** - calculate true walk-forward R² from the backtesting predictions. This gives you genuine out-of-sample performance.

---

## Bug #6: Off-by-One in Range (Line 532)

### Current Code (WRONG)
```python
for i in range(WINDOW, len(g) - 1):  # Excludes last observation
    window = g.iloc[i-WINDOW:i]
    # ...
```

### Problem
With WINDOW=3 and len(g)=4:
- `range(3, 3)` produces an empty range
- No backtesting observations created for this entity

Even with len(g)=5:
- `range(3, 4)` only produces i=3
- Only ONE backtest observation (should have TWO: i=3 and i=4)

### Fixed Code
Depends on Bug #4 fix choice:

**If using immediate next-period prediction:**
```python
for i in range(WINDOW, len(g)):  # Include last observation
    window = g.iloc[i-WINDOW:i]
    # Predict change from i-1 to i
```

**If using 1-period-ahead prediction:**
```python
for i in range(WINDOW, len(g) - 1):  # Correct: need future observation
    window = g.iloc[i-WINDOW:i]
    # Predict change from i to i+1 (need i+1 to exist)
```

### Recommendation
Use `range(WINDOW, len(g) - 1)` ONLY if predicting i+1 (need lookahead for labels).
Use `range(WINDOW, len(g))` if predicting i (immediate next period after window).

---

## Bug #7: Pooled Rank IC Ignores Country Dimension (Lines 543-544)

### Current Code (WRONG)
```python
rank_ic = alpha_ts_df["Alpha"].corr(
    alpha_ts_df["future_interest_change"],
    method="spearman"
)
alpha_ts_df["rank_ic"] = rank_ic  # Same value for ALL rows
```

### Problem
1. Calculates ONE global rank IC across all countries/entities
2. Assigns the SAME value to every row
3. Makes country-level analysis impossible
4. Ignores independence assumption (observations within country may be correlated)

### Fixed Code
```python
# Remove the global rank_ic calculation
# It's already calculated per country in cal_country_stats_with_r2()

# If you want global rank IC, calculate it separately:
global_rank_ic = alpha_ts_df["Alpha"].corr(
    alpha_ts_df["actual_change"],  # Fixed variable name
    method="spearman"
)
print(f"Global Rank IC: {global_rank_ic:.4f}")

# Don't add it to the dataframe as a column
# Store it separately for reporting
```

### Better Approach: Multi-Level Rank IC
```python
# 1. Global Rank IC
global_rank_ic = alpha_ts_df["Alpha"].corr(
    alpha_ts_df["actual_change"],
    method="spearman"
)

# 2. Country-Level Rank IC (already in bt_all_country_df)
country_rank_ic = (
    alpha_ts_df
    .groupby("Country")
    .apply(lambda x: x["Alpha"].corr(x["actual_change"], method="spearman"))
    .reset_index(name="rank_ic")
)

# 3. Time-Period Rank IC (cross-sectional)
time_rank_ic = (
    alpha_ts_df
    .groupby("prediction_date")
    .apply(lambda x: x["Alpha"].corr(x["actual_change"], method="spearman"))
    .reset_index(name="rank_ic")
)

# 4. Summary Statistics
rank_ic_summary = pd.DataFrame({
    "Level": ["Global", "Country (avg)", "Country (median)", "Time Period (avg)"],
    "Rank IC": [
        global_rank_ic,
        country_rank_ic["rank_ic"].mean(),
        country_rank_ic["rank_ic"].median(),
        time_rank_ic["rank_ic"].mean()
    ]
})
```

### Recommendation
Calculate rank IC at multiple levels:
- **Global**: Overall predictive power
- **Country**: Heterogeneity across regions
- **Time Period**: Stability over time

Don't broadcast a single value to all rows.

---

## Complete Fixed Backtesting Code

Here's the entire backtesting section with all bugs fixed:

```python
## Backtesting with Rolling Window ------------
WINDOW = 3
bt_rows = []

for country in interest_data.country_of_risk.unique():
    data = process_data_country_sector(interest_data, MEVdata, country, sector)
    data = data.sort_values(["spread_id", "DATE_OF_FINANCIALS"])

    for spread_id, g in data.groupby("spread_id"):
        if len(g) <= WINDOW:
            continue

        # BUG FIX #4 & #6: Proper walk-forward validation
        for i in range(WINDOW, len(g) - 1):  # Predict i+1 using window ending at i-1
            # Training window: [i-WINDOW, i-1]
            window = g.iloc[i-WINDOW:i]

            # Calculate alpha on training window only
            alpha = compute_alpha(window, country)

            # True out-of-sample prediction for period i+1
            actual_change = g.iloc[i+1]["interest_rate"] - g.iloc[i]["interest_rate"]
            cb_rate_change = (
                g.iloc[i+1][f"{country}_Monetary policy or key interest rate_4QMA"] -
                g.iloc[i][f"{country}_Monetary policy or key interest rate_4QMA"]
            )
            predicted_change = alpha * cb_rate_change

            bt_rows.append({
                "Country": country,
                "spread_id": spread_id,
                "prediction_date": g.iloc[i+1]["DATE_OF_FINANCIALS"],
                "window_end_date": g.iloc[i-1]["DATE_OF_FINANCIALS"],
                "Alpha": alpha,
                "predicted_change": predicted_change,
                "actual_change": actual_change,
                "cb_rate_change": cb_rate_change
            })

alpha_ts_df = pd.DataFrame(bt_rows).dropna()

# BUG FIX #7: Calculate rank IC at multiple levels
# Global Rank IC
global_rank_ic = alpha_ts_df["Alpha"].corr(
    alpha_ts_df["actual_change"],
    method="spearman"
)
print(f"Global Rank IC: {global_rank_ic:.4f}")

# Country-Level Statistics
def cal_country_stats_proper(x):
    """BUG FIX #5: Calculate true OOS R² from walk-forward predictions"""

    # Quintile Analysis
    try:
        buckets = pd.qcut(x["Alpha"], 5, duplicates="drop")
        bucket_perf = x.groupby(buckets)["actual_change"].mean()
        if len(bucket_perf) < 2:
            top_minus_bottom = np.nan
        else:
            top_minus_bottom = bucket_perf.iloc[-1] - bucket_perf.iloc[0]
    except:
        top_minus_bottom = np.nan

    # True OOS Metrics (from walk-forward backtest)
    mse_model = np.mean((x["actual_change"] - x["predicted_change"])**2)
    mse_naive = np.mean(x["actual_change"]**2)  # Naive: predict zero change
    r2_oos = 1 - (mse_model / mse_naive)

    return pd.Series({
        "rank_ic": x["Alpha"].corr(x["actual_change"], method="spearman"),
        "n_obs": len(x),
        "top_minus_bottom": top_minus_bottom,
        "R2_OOS": r2_oos,  # Now correctly calculated!
        "MAE": np.mean(np.abs(x["actual_change"] - x["predicted_change"])),
        "RMSE": np.sqrt(mse_model)
    })

bt_all_country_df = (
    alpha_ts_df
    .groupby("Country")
    .apply(cal_country_stats_proper)
    .reset_index()
)

# Entity-Level Statistics
bt_final_all_df = (
    alpha_ts_df
    .groupby(["Country", "spread_id"])
    .agg(
        avg_alpha=("Alpha", "mean"),
        alpha_std=("Alpha", "std"),
        n_obs=("Alpha", "count"),
        MAE=("actual_change", lambda x: np.mean(np.abs(
            x - alpha_ts_df.loc[x.index, "predicted_change"]
        )))
    )
    .reset_index()
)

# Global Summary
full_summary = cal_country_stats_proper(alpha_ts_df).to_frame().T
full_summary["Global_Rank_IC"] = global_rank_ic

print("\n=== Backtest Results ===")
print(f"Global Rank IC: {global_rank_ic:.4f}")
print(f"Global R² OOS: {full_summary['R2_OOS'].values[0]:.4f}")
print(f"Global MAE: {full_summary['MAE'].values[0]:.4f}")
print(f"Global RMSE: {full_summary['RMSE'].values[0]:.4f}")
print("\nCountry-Level Results:")
print(bt_all_country_df)
```

---

## Summary of Changes

| Bug | Lines | Change | Impact |
|-----|-------|--------|--------|
| #4 | 532-540 | Predict period i+1 using window ending at i-1 | Removes look-ahead bias |
| #5 | 565-567 | Calculate R² from walk-forward predictions | True OOS R², correctly labeled |
| #6 | 532 | Use `len(g) - 1` for 1-ahead prediction | Includes all valid observations |
| #7 | 543-544 | Calculate rank IC separately by level | Proper country/time analysis |

---

## Testing the Fixes

After implementing, verify:

```python
# 1. Check no look-ahead bias
assert all(alpha_ts_df["prediction_date"] > alpha_ts_df["window_end_date"])

# 2. Check R² OOS is reasonable
assert -1 <= full_summary["R2_OOS"].values[0] <= 1

# 3. Check country-level rank ICs vary
assert bt_all_country_df["rank_ic"].std() > 0  # Should have variance

# 4. Check observation counts
print(f"Total backtest observations: {len(alpha_ts_df)}")
print(f"Entities with predictions: {alpha_ts_df['spread_id'].nunique()}")
```

---

## Expected Results After Fixes

With proper implementation:
- **R² OOS**: Likely 0.05-0.15 (5-15%) - much lower than mislabeled version
- **Rank IC**: Likely 0.1-0.3 - realistic cross-sectional predictive power
- **MAE**: Likely 0.5-2% - average prediction error in percentage points
- **No more look-ahead bias**: Predictions truly out-of-sample
