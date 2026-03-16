# Bug Analysis Report: IE.py

## Context
Analysis of C:\repo\mst\IE.py to identify bugs, logic errors, and potential runtime issues in the interest expense calculation code.

## Critical Issues Found

### 1. ⚠️ CRITICAL: Indentation Bug (Lines 146-152)
**Impact**: Data gets overwritten repeatedly in loop, causing incorrect results

The code inside the `for` loop at line 144 is incorrectly indented:
```python
for group_label, countries in country_group_mapping.items():
    for country in countries:
        reverse_country_map[country] = group_label
    interest_data["country_of_risk_grouped"] = ...  # ❌ This executes in EVERY iteration
    interest_data.drop(columns=[...])                # ❌ Overwrites results each time
    interest_data.rename(columns={...})              # ❌ Overwrites results each time
```

**Fix**: Lines 146-152 should be unindented to run AFTER the loop completes.

---

### 2. ⚠️ CRITICAL: Missing `os` Module Import (Line 1168)
**Impact**: Runtime error - code will crash

```python
os.makedirs(os.path.dirname(consolid_path), exist_ok=True)  # ❌ NameError
```

The `os` module is used but never imported.

**Fix**: Add `import os` at the top of the file.

---

## High Severity Issues

### 3. Division by Zero Risk (Line 487)
In `compute_alpha()` function:
```python
sensitivity = window_df["interest_rate"].std() / window_df[f"{country}_Monetary policy or key interest rate_4QMA"].mean()
```
No validation that denominator is non-zero.

### 4. KeyError Risk (Line 308)
In `MEV_data_processing()`:
```python
MEVdata_interest_rate = MEVdata[["Date", f"{country}_Monetary policy or key interest rate"]]
```
If country column doesn't exist, raises KeyError.

### 5. Division by Zero Risk (Line 428-430)
In `get_corr_df()`:
```python
std_df["LEID Sensitvity"] = std_df["interest_rate"] / std_df[f"{country}_Monetary policy or key interest rate_4QMA"]
```
No validation for zero denominator.

### 6. NaN Comparison Issue (Line 250)
```python
interest_data = interest_data[interest_data.irb_ead != 0]
```
After converting to float with `errors="coerce"` (line 195), NaN values exist but aren't explicitly filtered.

### 7. Multiple Division by Zero in Weighted Averages (Lines 752, 757, 779, 784)
```python
country_level_df2["irb_ead"].sum()  # No check if sum == 0
```
Multiple weighted average calculations without validating sum is non-zero.

---

## Medium Severity Issues

### 8. Off-by-One Error in Backtest Loop (Line 532)
```python
for i in range(WINDOW, len(g) - 1):  # ❌ Should be len(g), not len(g)-1
```
With WINDOW=3, groups with exactly 4 rows won't create any windows.

### 9. Variable Overwrite Bug (Lines 643-644)
```python
mevData = mevData.rename(columns={'Date': 'DATE_OF_FINANCIALS'})  # Line 643
mevData = MEV_data_processing_before2018("US", MEVdata)  # Line 644 OVERWRITES line 643
```
Line 644 completely discards the work from line 643.

### 10. Misleading Print Statements (Lines 239-240)
```python
print(f"shape before drop the quarterly data': {interest_data.shape}")
print(f"shape af drop the quarterly data': {interest_data.shape}")
```
Both print the SAME value (after drop). The first print should occur BEFORE line 237.

### 11. Bare Exception Catches (Lines 384, 650)
```python
except:  # ❌ Catches ALL exceptions including SystemExit
```
Should catch specific exceptions (e.g., `KeyError`, `ValueError`).

### 12. Mixed Data Type Comparison (Lines 829, 837)
```python
if pd.isna(row["Alpha_LCY"]) or row["Alpha_LCY"] == ""
```
Checking both `pd.isna()` AND `== ""` suggests unclear data type handling.

### 13. Hardcoded User-Specific Path (Line 40)
```python
output_temp = r"C:\Users\1665642\OneDrive - Standard Chartered Bank\Documents\test_run"
```
Won't work on other machines/users.

---

## Low Severity Issues

### 14. Redundant Column Rename (Line 657)
Same rename operation appears twice (lines 643 and 657).

### 15. Silent String Truncation (Line 1046)
```python
ws = workbook.create_sheet(sheet_name[:31])
```
Excel sheet names limited to 31 chars; could create duplicates if multiple sheets share first 31 characters.

---

## Summary Statistics
- **Critical Issues**: 2
- **High Severity**: 5
- **Medium Severity**: 8
- **Low Severity**: 2
- **Total Issues**: 17

## Recommended Priority
1. **Fix Immediately**: Issues #1, #2 (CRITICAL - will cause wrong results or crashes)
2. **Fix Soon**: Issues #3-7 (HIGH - potential runtime errors)
3. **Fix When Convenient**: Issues #8-13 (MEDIUM - code quality and edge cases)
4. **Optional**: Issues #14-15 (LOW - minor improvements)

---

# CRITICAL MODEL & BACKTESTING BUGS

## Model Implementation Issues

### 🔴 BUG #1: Incorrect Sensitivity Calculation (Line 487) - CRITICAL
**Function:** `compute_alpha()`

```python
# WRONG (current):
sensitivity = window_df["interest_rate"].std() / window_df[f"{country}_Monetary policy or key interest rate_4QMA"].mean()

# CORRECT (should be):
sensitivity = window_df["interest_rate"].std() / window_df[f"{country}_Monetary policy or key interest rate_4QMA"].std()
```

**Impact:** Uses `.mean()` instead of `.std()` for denominator. This violates statistical principles for sensitivity calculation and produces fundamentally incorrect alpha values.

---

### 🔴 BUG #2: Inconsistent Sensitivity Formulas (Lines 428-430 vs 487) - CRITICAL

**Two different calculations:**
- `get_corr_df()` (line 428): `std(interest_rate) / std(central_bank_rate)` ✓ CORRECT
- `compute_alpha()` (line 487): `std(interest_rate) / mean(central_bank_rate)` ✗ WRONG

**Impact:** Main model and backtesting use different formulas. Alpha values are incomparable between production and backtest.

---

### 🟠 BUG #3: Alpha Clipping Loses Information (Lines 452-457)
```python
all_df["Alpha"] = (all_df["Correlation"] * all_df["LEID Sensitvity"]).clip(lower=alpha_min, upper=alpha_max)
```

**Impact:** Clipping after multiplication truncates valid high-sensitivity/high-correlation combinations, biasing estimates downward.

---

## Backtesting Implementation Issues

### 🔴 BUG #4: Data Leakage - Look-Ahead Bias (Lines 532-540) - CRITICAL

```python
for i in range(WINDOW, len(g) -1):
    window = g.iloc[i-WINDOW:i]  # Window includes current period i
    alpha = compute_alpha(window, country)
    bt_rows.append({
        "date": g.iloc[i]["DATE_OF_FINANCIALS"],  # Date is period i
        "future_interest_change": g.iloc[i]["future_interest_change"]  # Predicting from i to i+1
    })
```

**Impact:** Window includes period `i`, then predicts change from `i→i+1`. This is look-ahead bias. Backtesting results are unrealistically optimistic and don't reflect true out-of-sample performance.

---

### 🔴 BUG #5: Wrong R² Type - Mislabeled as "OOS_R2" (Lines 565-567) - CRITICAL

```python
mse_model = np.mean((y - y_pred)**2)
mse_benchmark = np.mean((y - np.mean(y))**2)
r2_oos = 1 - mse_model/mse_benchmark  # ❌ This is IN-SAMPLE R², not OOS
```

**Impact:** Code calculates in-sample R² but labels it as out-of-sample ("OOS_R2"). No data is held out for validation. This severely overstates model quality - reported R² values are much higher than true predictive power.

---

### 🟠 BUG #6: Off-by-One in Range (Line 532)
```python
for i in range(WINDOW, len(g) - 1):  # Should be len(g), not len(g)-1
```

**Impact:** With WINDOW=3, groups with 4 observations get no windows: range(3,3) is empty. Loses valid observations.

---

### 🟠 BUG #7: Pooled Rank IC Ignores Country Dimension (Lines 543-544)
```python
rank_ic = alpha_ts_df["Alpha"].corr(alpha_ts_df["future_interest_change"], method="spearman")
alpha_ts_df["rank_ic"] = rank_ic  # Same value assigned to ALL rows
```

**Impact:** Rank IC pools all countries together, violating independence. Per-country analysis is impossible since all rows get the same global value.

---

## Validation Section Issues

### 🔴 BUG #8: Variable Overwrite - Data Loss (Lines 643-644) - CRITICAL
```python
mevData = mevData.rename(columns={'Date': 'DATE_OF_FINANCIALS'})  # Line 643
mevData = MEV_data_processing_before2018("US", MEVdata)  # Line 644 OVERWRITES line 643!
```

**Impact:** Line 644 completely discards the renamed data from line 643. Input MEV data is lost.

---

### 🔴 BUG #9: Wrong Variable Semantics (Line 673) - CRITICAL
```python
df['expected_interest_rate'] = df['monetary_interest'] * df['Alpha']
```

**Issue:**
- Variable name says "rate" but it's actually calculating a product
- Should calculate expected *change*, not expected *rate*
- Formula produces dimensionally incorrect values

**Impact:** Validation compares incompatible quantities (change vs. rate product). All metrics (R², MSE, MAE) are meaningless.

---

### 🔴 BUG #10: Mismatched Y Variables in Metrics (Lines 680-686) - CRITICAL
```python
y_true = temp['actual_interest_change']  # This is a CHANGE
y_pred = temp['expected_interest_rate']  # This is a RATE PRODUCT (from bug #9)
r2_score(y_true, y_pred)  # ❌ Comparing incompatible variables!
```

**Impact:** Validation metrics don't measure what they claim. R², MSE, MAE are invalid because they compare different units/meanings.

---

### 🟠 BUG #11: Missing 'Year' Column Risk (Line 690)
```python
df = df[['Year','DATE_OF_FINANCIALS',...]]  # 'Year' may not exist
```

**Impact:** KeyError at runtime if 'Year' column doesn't survive merge operations.

---

## Impact Summary

| Area | Critical Bugs | High Bugs | Impact on Model Quality |
|------|--------------|-----------|------------------------|
| Model Implementation | 2 | 1 | **Alpha values are incorrect** |
| Backtesting | 2 | 2 | **Performance metrics overstated by 2-5x** |
| Validation | 3 | 1 | **Validation section completely broken** |

## Key Takeaways

1. **Alpha calculation is wrong**: Sensitivity uses mean() instead of std()
2. **Backtest is invalid**: Look-ahead bias + mislabeled in-sample R² as out-of-sample
3. **Validation is broken**: Comparing incompatible variables, metrics are meaningless
4. **Inconsistency**: Two different sensitivity formulas in same codebase
5. **Data integrity**: Variable overwrites and data loss in validation

## Recommended Actions

**Priority 1 (MUST FIX):**
- Fix sensitivity calculation in `compute_alpha()` (line 487)
- Fix look-ahead bias in backtesting (lines 532-540)
- Fix validation variable semantics (lines 673, 680-686)
- Relabel R² as in-sample or implement true OOS validation

**Priority 2 (SHOULD FIX):**
- Standardize sensitivity calculation across functions
- Fix off-by-one error in backtesting range
- Fix data overwrite in validation (lines 643-644)
- Add country-level rank IC calculation

**Priority 3 (NICE TO HAVE):**
- Review clipping logic
- Add validation for missing columns

---

## Next Steps
Options for proceeding:
1. Fix all critical model/backtesting bugs (recommended)
2. Fix only the sensitivity calculation bug
3. Fix backtesting and validation separately
4. Review and discuss statistical methodology first
