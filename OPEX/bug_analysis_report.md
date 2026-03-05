# OPEX.py Bug Analysis Report

**Date**: 2026-02-27
**Script**: opex.py
**Total Bugs Found**: 27
**Severity Breakdown**:
- Critical: 9 bugs
- High: 10 bugs
- Medium: 7 bugs
- Low: 1 bug

---

## Executive Summary

This analysis identifies 27 bugs and issues in the opex.py script, focusing on data processing, model implementation, and backtesting logic. The most critical issues include:

1. **Hardcoded sector-specific logic** that breaks for other sectors
2. **Incorrect revenue adjustment conditional** (inverted logic)
3. **Missing column error handling** causing KeyErrors
4. **Wrong return period calculation** for 2009 crisis
5. **Coverage/exception rate calculations** using NaN-inclusive data

**Recommendation**: Address all Critical and High severity bugs before production use.

---

## 1. Data Processing Bugs

### Bug #1: Inconsistent Missing Value Replacement
**Lines**: 544-565
**Severity**: 🟡 Medium
**Description**: Missing values are replaced with `None` first, then converted to float. Separate handling of `"Missing"` and `"Not applicable"` is inefficient.

**Current Code**:
```python
financials["SLS_REVENUES"] = financials["SLS_REVENUES"].replace("Not applicable", None)
summary_2 = summarize_step(...)
financials["SLS_REVENUES"] = financials["SLS_REVENUES"].replace("Missing", None)
summary_3 = summarize_step(...)
financials["SLS_REVENUES"] = financials["SLS_REVENUES"].astype(float)
```

**Impact**: May cause inconsistent data handling and NaN propagation

**Fix**:
```python
financials["SLS_REVENUES"] = pd.to_numeric(
    financials["SLS_REVENUES"].replace(["Not applicable", "Missing"], np.nan),
    errors='coerce'
)
```

---

### Bug #2: Summary Created Before Filtering
**Lines**: 547-565
**Severity**: 🔴 High
**Description**: Summary steps 2-4 are created BEFORE data is actually filtered. Replacements don't remove rows, making summaries identical to step 1.

**Impact**: Summary statistics are incorrect and misleading

**Fix**:
```python
# Replace values
financials["SLS_REVENUES"] = pd.to_numeric(
    financials["SLS_REVENUES"].replace(["Not applicable", "Missing"], np.nan),
    errors='coerce'
)
# Filter data
financials = financials.dropna(subset=["SLS_REVENUES"])
financials = financials[financials["SLS_REVENUES"] != 0]
# Then create summaries
summary_2 = summarize_step(financials, ...)
```

---

### Bug #3: Duplicate Variable in groupSector
**Lines**: 459-467
**Severity**: 🔴 High
**Description**: `groupSector` block reuses `reverse_country_map` from `groupCountry` block. When both flags are True, country grouping is lost.

**Current Code**:
```python
if groupCountry:
    reverse_country_map = {}
    # ... populate

if groupSector:
    reverse_country_map = {}  # ← Overwrites country mapping!
    for group_label, countries in country_group_mapping.items():
```

**Impact**: When both groupCountry=True and groupSector=True, country grouping is overwritten

**Fix**:
```python
if groupSector:
    reverse_sector_map = {}  # Use different variable name
    for group_label, sectors in sector_group_mapping.items():  # Use correct mapping
        for sector_item in sectors:
            reverse_sector_map[sector_item] = group_label
    financials["sub_segment_group"] = financials["sub_segment"].apply(
        lambda x: reverse_sector_map.get(x, x)
    )
```

---

### Bug #4: Wrong Mapping Dictionary
**Lines**: 461-463
**Severity**: 🔴 Critical
**Description**: `groupSector` uses `country_group_mapping` instead of sector-specific mapping.

**Impact**: Sector grouping will fail or produce incorrect results

**Fix**: Create and use separate `sector_group_mapping` configuration

---

### Bug #5: Missing Column References
**Lines**: 1285-1293
**Severity**: 🔴 Critical
**Description**: Output references columns `Revenue_Change` and `Opex_Change` that are never created.

**Impact**: KeyError at runtime during Excel export

**Fix**:
```python
# Either create the columns:
Opex_clean_rel_exclude_add_cat["Revenue_Change"] = (
    Opex_clean_rel_exclude_add_cat["SLS_REVENUES"].pct_change()
)
Opex_clean_rel_exclude_add_cat["Opex_Change"] = (
    Opex_clean_rel_exclude_add_cat["Opex"].pct_change()
)

# Or remove from output columns list
```

---

## 2. Model Implementation Bugs

### Bug #6: Incorrect Delta Calculation Logic
**Lines**: 119-131
**Severity**: 🟡 Medium
**Description**: Uses `.diff()` then checks conditions. Should check conditions first, then compute diff.

**Current Code**:
```python
group["delta_opex/rev"] = group["Opex/Revenue"].diff()
group["delta_opex/rev"] = group.apply(
    lambda row: (
        row["delta_opex/rev"]
        if (row["Month"] == row["Month_prev"] and row["Year"] - row["Year_prev"] == 1)
        else np.nan
    ),
    axis=1,
)
```

**Impact**: May produce incorrect delta values for edge cases

**Fix**:
```python
group["delta_opex/rev"] = group.apply(
    lambda row: (
        row["Opex/Revenue"] - row["Opex/Revenue_prev"]
        if (row["Month"] == row["Month_prev"] and row["Year"] - row["Year_prev"] == 1)
        else np.nan
    ),
    axis=1,
)
```

---

### Bug #7: Division by Zero Not Protected
**Lines**: 144-145
**Severity**: 🟡 Medium
**Description**: Checks `!= 0` but doesn't handle very small denominators that create extreme ratios.

**Impact**: Can produce unrealistic delta values (e.g., 10,000% change)

**Fix**:
```python
group["delta_opex/rev"] = np.where(
    (group["Month"] == group["Month_prev"])
    & (group["Year"] - group["Year_prev"] == 1)
    & (np.abs(group["Opex/Revenue_prev"]) > 1e-10),  # Add threshold
    (group["Opex/Revenue"] - group["Opex/Revenue_prev"]) / group["Opex/Revenue_prev"],
    np.nan,
)
```

---

### Bug #8: Wrong Variable in Return Period Calculation
**Lines**: 925-926
**Severity**: 🔴 High
**Description**: 2009 return period uses `tail_prob_08` instead of `tail_prob_09`.

**Current Code**:
```python
return_period_08 = 1/tail_prob_08 if tail_prob_08 > 0 else np.inf
return_period_09 = 1/tail_prob_09 if tail_prob_08 > 0 else np.inf  # ← Wrong variable!
```

**Impact**: 2009 return period is calculated incorrectly

**Fix**:
```python
return_period_09 = 1/tail_prob_09 if tail_prob_09 > 0 else np.inf
```

---

### Bug #9: Circular Logic in Percentile Rank
**Lines**: 920-926
**Severity**: 🟡 Medium
**Description**: Percentile rank calculation includes the crisis year itself, creating circular logic.

**Current Code**:
```python
model_data = subset["delta_opex/rev"]
percentile_rank_08 = (model_data <= x_crisis_08).mean()  # Includes 2008 data!
```

**Impact**: Percentile ranks are biased upward

**Fix**:
```python
model_data_excl_08 = subset[~subset["Year"].isin([2008])]["delta_opex/rev"]
percentile_rank_08 = (model_data_excl_08 <= x_crisis_08).mean()

model_data_excl_09 = subset[~subset["Year"].isin([2009])]["delta_opex/rev"]
percentile_rank_09 = (model_data_excl_09 <= x_crisis_09).mean()
```

---

### Bug #10: MAE/MSE Calculation Error
**Lines**: 940-946
**Severity**: 🔴 Critical
**Description**: Wrong variable checked for empty condition; tries to assign 2 values to 2 variables in one line.

**Current Code**:
```python
if len(model_data) == 0:  # Wrong variable!
    mae_2008, mse_2008, mae_2009, mse_2009 = None, None  # Wrong count!
else:
    mae_2008 = mean_absolute_error(crisis_data_clean_2008, [forecasted_stress]*len(...))
    # ...
```

**Impact**: ValueError or incorrect None assignments

**Fix**:
```python
if len(crisis_data_clean_2008) == 0:
    mae_2008, mse_2008 = None, None
else:
    mae_2008 = mean_absolute_error(
        crisis_data_clean_2008,
        [forecasted_stress] * len(crisis_data_clean_2008)
    )
    mse_2008 = mean_squared_error(
        crisis_data_clean_2008,
        [forecasted_stress] * len(crisis_data_clean_2008)
    )

if len(crisis_data_clean_2009) == 0:
    mae_2009, mse_2009 = None, None
else:
    mae_2009 = mean_absolute_error(
        crisis_data_clean_2009,
        [forecasted_stress] * len(crisis_data_clean_2009)
    )
    mse_2009 = mean_squared_error(
        crisis_data_clean_2009,
        [forecasted_stress] * len(crisis_data_clean_2009)
    )
```

---

### Bug #11: Hardcoded Sub-segment Names
**Lines**: 814-818
**Severity**: 🔴 Critical
**Description**: Hardcoded Commodity Trader sub-segments. Will crash for all other sectors.

**Current Code**:
```python
Opex_clean_rel_exclude = pd.concat(
    [finalCT_Chemicals, finalCT_Energy, finalOthers, finalCT_Metal],  # ← Hardcoded!
    axis=0,
    ignore_index=True,
)
```

**Impact**: Code crashes for all sectors except Commodity Traders

**Fix**:
```python
# Collect all dynamically created sub-segment dataframes
subsector_dfs = [
    globals()[f"final{subSector.replace(' ', '_')}"]
    for subSector in Opex_clean_rel_exclude.TOPS.unique()
]
Opex_clean_rel_exclude = pd.concat(subsector_dfs, axis=0, ignore_index=True)
```

---

### Bug #12: Incorrect Percentile Interpolation
**Lines**: 929-932
**Severity**: 🟡 Medium
**Description**: `np.interp` requires x-values to be sorted. Unsorted `percentile_values` will produce wrong results.

**Current Code**:
```python
percentile_08 = np.interp(x_crisis_08, percentile_values, percentiles_for_file)
percentile_08 = np.clip(percentile_08, percentiles_for_file[0], percentiles_for_file[-1])
```

**Impact**: Incorrect percentile mapping for crisis data

**Fix**:
```python
# Sort before interpolation
sorted_indices = np.argsort(percentile_values)
sorted_values = percentile_values[sorted_indices]
sorted_percentiles = np.array(percentiles_for_file)[sorted_indices]

percentile_08 = np.interp(x_crisis_08, sorted_values, sorted_percentiles)
percentile_09 = np.interp(x_crisis_09, sorted_values, sorted_percentiles)
```

---

## 3. Backtesting/Validation Bugs

### Bug #13: Crisis Data Uses Mean Only
**Lines**: 916-917
**Severity**: 🟡 Medium
**Description**: Takes mean of crisis year, losing information about within-year variance.

**Current Code**:
```python
x_crisis_08 = crisis_data2008["delta_opex/rev"].mean()
x_crisis_09 = crisis_data2009["delta_opex/rev"].mean()
```

**Impact**: Reduces accuracy of historical calibration

**Fix**: Use median or report both:
```python
x_crisis_08_mean = crisis_data2008["delta_opex/rev"].mean()
x_crisis_08_median = crisis_data2008["delta_opex/rev"].median()
# Use median for more robust comparison
x_crisis_08 = x_crisis_08_median
```

---

### Bug #14: Coverage Calculation Uses Wrong Values
**Lines**: 950-953
**Severity**: 🔴 High
**Description**: Coverage uses `percentile_values[1:]` (absolute values) instead of stress impacts. Also includes NaN values.

**Current Code**:
```python
actual = subset["delta_opex/rev"]  # Includes NaN!
coverage = {
    stress_level: (actual <= stress_level).mean()  # Wrong comparison
    for stress_level in percentile_values[1:]
}
```

**Impact**: Coverage metrics are meaningless; NaN values cause coverage + exception ≠ 1

**Fix**:
```python
actual = subset["delta_opex/rev"].dropna()  # Remove NaN first!
base = percentile_values[0]
coverage = {
    stress_level: (actual <= stress_level).mean()  # Now comparing to actual threshold
    for stress_level in percentile_values[1:]
}
```

---

### Bug #15: Exception Rate Redundant Calculation
**Lines**: 954-957
**Severity**: 🟡 Low
**Description**: Exception rate is simply `1 - coverage`, making it redundant. Also has same NaN issue.

**Impact**: Redundant storage, NaN handling issue

**Fix**:
```python
# Either remove exception_rate entirely, or calculate from coverage:
exception_list = [1 - cov for cov in coverage_list]
```

---

## 4. Other Critical Issues

### Bug #16: Dangerous globals() Usage
**Lines**: 177-187, 794-818
**Severity**: 🔴 High
**Description**: Uses `globals()` to dynamically create variables, causing namespace pollution and hard-to-debug errors.

**Current Code**:
```python
for date in dates:
    date_ = date.replace("-", "_")
    globals()[f"final{date_}"] = original_fin[...]  # Dangerous!
```

**Impact**: Variable overwrites, namespace pollution, debugging nightmares

**Fix**:
```python
# Use dictionaries instead
dataframes_by_date = {}
for date in dates:
    date_key = date.replace("-", "_")
    dataframes_by_date[date_key] = original_fin[
        original_fin["DATE_OF_FINANCIALS"].str.endswith(date)
    ]
    dataframes_by_date[date_key] = dataframes_by_date[date_key].sort_values(...)

# Access via dictionary
original_fin = pd.concat(dataframes_by_date.values(), axis=0, ignore_index=True)
```

---

### Bug #17: Hardcoded User-Specific Path
**Lines**: 69
**Severity**: 🔴 Critical
**Description**: Hardcoded OneDrive path specific to one user.

**Current Code**:
```python
output_temp = r"C:\Users\1665642\OneDrive - Standard Chartered Bank\Documents\test_run"
```

**Impact**: Code won't run on other systems

**Fix**:
```python
# Use configuration or environment variable
import os
output_temp = os.getenv('OPEX_OUTPUT_DIR', OUT_DIR)
```

---

### Bug #18: In-Place List Modification
**Lines**: 686-687
**Severity**: 🟡 Medium
**Description**: Modifies `top_segments` list in-place, affecting original configuration.

**Current Code**:
```python
if includeOthers:
    top_segments += ["Others"]  # Modifies original list!
```

**Impact**: Multiple runs cause list to grow: ['A', 'B', 'Others', 'Others', ...]

**Fix**:
```python
if includeOthers:
    segments_to_process = top_segments + ["Others"]  # Create new list
else:
    segments_to_process = top_segments
```

---

### Bug #19: Dead Code in normalize_var
**Lines**: 1049-1051
**Severity**: 🟡 Low
**Description**: Function defines operation but doesn't execute it.

**Current Code**:
```python
def normalize_var(x):
    x.split("-")[-1].strip if "-" in x else x.split("-", 1)[-1].strip()  # Not executed!
    return str(x)
```

**Fix**:
```python
def normalize_var(x):
    return x.split("-")[-1].strip() if "-" in x else x.strip()
```

---

### Bug #20: Year Difference Calculation Issues
**Lines**: 193-205
**Severity**: 🟡 Medium
**Description**: Uses 365-366 day range, missing leap years and valid gaps.

**Current Code**:
```python
.diff().abs().between(pd.Timedelta(days=365), pd.Timedelta(days=366))
```

**Impact**: Some valid year-over-year pairs are missed

**Fix**:
```python
date_diff = original_fin["DATE_OF_FINANCIALS"].diff()
is_annual_gap = date_diff.dt.days.between(360, 370)  # More flexible range
```

---

### Bug #21: No Empty Subset Check
**Lines**: 886-896
**Severity**: 🔴 High
**Description**: No validation if subset is empty before calculating statistics.

**Impact**: Quantile calculations crash on empty data

**Fix**:
```python
subset = Opex_clean_rel_exclude_add_cat[mask]
if subset.empty:
    print(f"Warning: No data for {top_segment}")
    continue
```

---

### Bug #22: Undefined Variable Reference
**Lines**: 285
**Severity**: 🔴 Critical
**Description**: References `pdf` but parameter is `pdfPagesObject`.

**Current Code**:
```python
if pdfPagesObject:
    pdf.savefig()  # ← pdf not defined!
```

**Impact**: NameError

**Fix**:
```python
if pdfPagesObject:
    pdfPagesObject.savefig()
```

---

### Bug #23: Column Rename Without Existence Check
**Lines**: 1258-1263
**Severity**: 🔴 High
**Description**: Renames columns that may not exist depending on configuration.

**Impact**: KeyError if columns don't exist

**Fix**:
```python
rename_dict = {}
if "y" in Opex_clean_rel_exclude_add_cat.columns:
    rename_dict["y"] = "Rev_Chg"
if "y_winsor" in Opex_clean_rel_exclude_add_cat.columns:
    rename_dict["y_winsor"] = "Rev_Chg_winzorised"
if "TOPS" in Opex_clean_rel_exclude_add_cat.columns:
    rename_dict["TOPS"] = "country/subsector"

if rename_dict:
    Opex_clean_rel_exclude_add_cat = Opex_clean_rel_exclude_add_cat.rename(
        columns=rename_dict
    )
```

---

### Bug #24: Inverted Conditional Logic
**Lines**: 394-397
**Severity**: 🔴 Critical
**Description**: Conditional is backwards - applies revenue adjustment when flag is False.

**Current Code**:
```python
if not dampned_for_revenue_outlier:  # This seems inverted!
    financials = revenue_adjustment(financials.copy())
```

**Impact**: Revenue adjustment applied at wrong time

**Fix**: Verify intended logic and correct:
```python
if dampned_for_revenue_outlier:
    financials = revenue_adjustment(financials.copy())
```

---

### Bug #25: Hardcoded Column Name
**Lines**: 1292-1293
**Severity**: 🔴 High
**Description**: Hardcoded `"winsorised as top1"` only exists if `step_2_quantile=0.99`.

**Current Code**:
```python
"winsorised as top1",  # Only exists for 99th percentile!
```

**Impact**: KeyError for other quantile settings

**Fix**:
```python
quantile_col = f"winsorised as top{int(100*(1-step_2_quantile))}"
if quantile_col in Opex_clean_rel_exclude_add_cat.columns:
    output_cols.append(quantile_col)
```

---

## 5. Additional Edge Cases

### Issue #26: No Empty DataFrame Validation
**Multiple Locations**
**Severity**: 🔴 High
**Description**: No checks for empty dataframes after major filtering steps.

**Fix**: Add validation:
```python
if financials.empty:
    raise ValueError(f"No data remaining for sector {sector_name} after filtering")
```

---

### Issue #27: All-NaN Column Handling
**Lines**: 666, 904
**Severity**: 🟡 Medium
**Description**: No check if all delta values are NaN before quantile calculation.

**Fix**:
```python
filtered_data = Opex_clean_rel["delta_opex/rev"].dropna()
if filtered_data.empty:
    print(f"Warning: No valid delta values for {segment}")
    continue
```

---

## Priority Fix Recommendations

### Immediate (Critical - Breaks Code)
1. ✅ Bug #4: Wrong mapping dictionary (line 461)
2. ✅ Bug #5: Missing columns in output (lines 1285-1293)
3. ✅ Bug #10: MAE/MSE calculation error (lines 940-946)
4. ✅ Bug #11: Hardcoded sub-segments (lines 814-818)
5. ✅ Bug #17: Hardcoded user path (line 69)
6. ✅ Bug #22: Undefined pdf variable (line 285)
7. ✅ Bug #24: Inverted conditional (lines 394-397)

### High Priority (Incorrect Results)
1. ✅ Bug #2: Summary before filtering (lines 547-565)
2. ✅ Bug #3: Variable overwrite (lines 459-467)
3. ✅ Bug #8: Wrong return period variable (line 926)
4. ✅ Bug #14: Coverage calculation (lines 950-953)
5. ✅ Bug #16: globals() usage (lines 177-187, 794-818)
6. ✅ Bug #21: Empty subset check (lines 886-896)

### Medium Priority (Accuracy Issues)
1. ✅ Bug #1: Missing value handling (lines 544-565)
2. ✅ Bug #9: Circular percentile logic (lines 920-926)
3. ✅ Bug #12: Interpolation sorting (lines 929-932)
4. ✅ Bug #18: In-place modification (lines 686-687)

---

## Testing Recommendations

After fixes, test with:

1. **Multiple sectors** (not just Commodity Traders)
2. **Empty data scenarios** for specific segments
3. **Different quantile settings** (not just 99th)
4. **Both groupCountry and groupSector enabled**
5. **Data with high NaN ratios** in delta calculations
6. **Historical crisis years (2008, 2009)** validation

---

## Conclusion

The OPEX model has significant bugs that will cause failures in production. The most severe issues are:
- Sector-specific hardcoding preventing general use
- Incorrect statistical calculations for backtesting
- Poor error handling for missing data/columns
- Dangerous use of dynamic variable creation

**Estimated Fix Time**: 2-3 days for all critical + high priority bugs

**Risk Level Without Fixes**: 🔴 HIGH - Model will crash or produce incorrect results
