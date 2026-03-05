# Opex Model and Backtesting Review

## **Model Overview**

This is an **Operating Expense (Opex) stress testing model** that estimates stress impacts on the Opex/Revenue ratio for various financial sectors. The model uses historical panel data to derive percentile-based stress scenarios.

---

## **Model Methodology**

### **1. Core Approach**
- **Metric**: Year-over-year **relative change** in Opex/Revenue ratio
- **Distribution-based**: Uses empirical percentiles (50th, 80th, 90th, 96th, 99th) to define stress scenarios
- **Sector segmentation**: Analyzes by sub-sectors/countries with option to aggregate "Others"

### **2. Data Preparation (Lines 393-653)**
**Strengths:**
- ✅ Robust filtering pipeline with 9 documented steps
- ✅ Removes quarterly duplicates, keeps only annual data
- ✅ Handles missing/zero revenue cases appropriately
- ✅ Tracks data attrition at each step via `summarize_step()`

**Issues:**
- ⚠️ **Line 815**: Hardcoded concatenation of specific sub-sectors (`finalCT_Chemicals, finalCT_Energy, finalOthers, finalCT_Metal`) - this will fail for other sectors
- ⚠️ Revenue adjustment logic (lines 161-225) uses outlier weights but relationship to main model is unclear

### **3. Delta Calculation (Lines 109-159)**
**Strengths:**
- ✅ Proper handling of year-over-year matching (same month, 1-year difference)
- ✅ Avoids division by zero in relative change calculation

**Issues:**
- ⚠️ Only uses **relative change** (line 657) - absolute change option exists but isn't utilized
- ⚠️ No handling of extreme relative changes (e.g., if prior year Opex/Revenue was near zero)

---

## **Outlier Treatment**

### **Two-Step Dampening Process (Lines 689-821)**

**Step 1: Revenue Model Exclusions**
- Applies dampening factor (0.0001 or 1) to flagged outliers from external exclusion file
- Tracks dampened counts by segment

**Step 2: Percentile-based Winsorization**
- Clips values above a specified quantile (default appears to be 99th percentile based on `step_2_quantile`)
- Applied per segment or globally depending on `dampenerPercentileBySegment`

**Critical Issues:**
- 🔴 **Lines 814-818**: **Hardcoded concatenation** will break for non-Commodity Trader sectors
- ⚠️ Dampening factor of 0.0001 effectively removes outliers but retains them in dataset (may skew percentiles)
- ⚠️ The interaction between Step 1 and Step 2 dampening isn't clearly validated

---

## **Backtesting Methodology**

### **Metrics Calculated (Lines 914-946)**

#### **1. Historical Crisis Values**
```python
x_crisis_08 = crisis_data2008["delta_opex/rev"].mean()
x_crisis_09 = crisis_data2009["delta_opex/rev"].mean()
```
- Takes mean of 2008 and 2009 delta Opex/Revenue values

#### **2. Historical Percentile Rank** (Lines 921-926)
```python
percentile_rank_08 = (model_data <= x_crisis_08).mean()
tail_prob_08 = 1 - percentile_rank_08
return_period_08 = 1/tail_prob_08
```
- **What it measures**: Where the 2008/2009 crisis fell in the historical distribution
- **Issue**: ⚠️ Return period calculation on line 926 has typo - uses `tail_prob_08` instead of `tail_prob_09` for 2009

#### **3. Relative Percentile** (Lines 929-932)
```python
percentile_08 = np.interp(x_crisis_08, percentile_values, percentiles_for_file)
```
- **What it measures**: Linear interpolation to find where crisis value sits among model percentiles
- **Issue**: ⚠️ This is clipped to model percentile range - doesn't handle crisis being more severe than 99th percentile

#### **4. Forecast Accuracy (MAE/MSE)** (Lines 935-946)
```python
target_perc = 96  # 1in25 scenario severity
forecasted_stress = percentile_values[target_idx] - percentile_values[0]
mae_2008 = mean_absolute_error(crisis_data_clean_2008, [forecasted_stress]*len(...))
```

**Critical Issues:**
- 🔴 **Conceptual Error**: Compares individual 2008 data points to a **single aggregate forecasted stress** (96th percentile impact)
- 🔴 This is not a proper backtesting approach - should compare:
  - Option A: 2008 forecast (made with pre-2008 data) vs actual 2008 impact
  - Option B: Current model percentiles vs 2008 empirical distribution
- 🔴 Using all historical data including crisis years to build the model, then "backtesting" against the same crisis = **look-ahead bias**

---

## **Key Backtesting Problems**

### **1. No Out-of-Sample Testing**
The model builds its distribution using ALL available data (including 2008-2009), then checks where 2008-2009 fell in that distribution. This is **in-sample validation**, not backtesting.

**Proper approach:**
```python
# Build model with data up to 2007
pre_crisis_data = Opex_clean_rel[Opex_clean_rel["Year"] < 2008]
# Generate percentiles from pre-crisis data
# Compare these to actual 2008-2009 outcomes
```

### **2. MAE/MSE Calculation Is Flawed**
Current approach compares:
- **Predicted**: Single value (96th percentile stress impact)
- **Actual**: All 2008 company-level delta values

This mixes:
- Aggregate stress scenario (model output)
- Individual company outcomes (observed data)

**Better approach:**
```python
# Option 1: Portfolio-level backtest
actual_portfolio_impact_2008 = crisis_data2008["delta_opex/rev"].quantile(0.96)
forecasted_impact = pre_crisis_percentiles[0.96]
error = actual_portfolio_impact_2008 - forecasted_impact

# Option 2: Company-level backtest
# Build company-specific models, forecast each, compare to actual
```

### **3. Coverage/Exception Rate** (Lines 950-959)
```python
coverage = {stress_level: (actual <= stress_level).mean() for stress_level in percentile_values[1:]}
```
- This calculates what % of data falls below each percentile threshold
- **Issue**: Using the same data that generated the percentiles - should be 80%, 90%, 96%, 99% by construction
- **Purpose unclear**: May be intended for out-of-sample validation but isn't used that way

---

## **Recommendations**

### **High Priority Fixes**

1. **Remove Hardcoded Concatenation** (Line 815)
   ```python
   # Current: Hardcoded for Commodity Traders
   Opex_clean_rel_exclude = pd.concat([finalCT_Chemicals, finalCT_Energy, ...])

   # Fix: Use dictionary comprehension
   sector_dfs = {}
   for subSector in Opex_clean_rel_exclude.TOPS.unique():
       # ... processing ...
       sector_dfs[subSector] = globals()[f"final{subSector_}"]
   Opex_clean_rel_exclude = pd.concat(sector_dfs.values(), ignore_index=True)
   ```

2. **Implement True Backtesting**
   ```python
   def backtest_crisis(data, crisis_year, lookback_years=10):
       # Use only data before crisis
       train_data = data[data["Year"].between(crisis_year - lookback_years, crisis_year - 1)]
       test_data = data[data["Year"] == crisis_year]

       # Build percentiles from training data
       train_percentiles = train_data.groupby("TOPS")["delta_opex/rev"].quantile([0.5, 0.8, 0.9, 0.96, 0.99])

       # Compare to actual crisis impact
       actual_crisis = test_data.groupby("TOPS")["delta_opex/rev"].quantile(0.96)

       return train_percentiles, actual_crisis
   ```

3. **Fix Return Period Calculation** (Line 926)
   ```python
   return_period_09 = 1/tail_prob_09 if tail_prob_09 > 0 else np.inf
   # Currently uses tail_prob_08 instead of 09
   ```

### **Medium Priority Enhancements**

4. **Add Walk-Forward Validation**
   - Test model stability across different time periods
   - Use expanding or rolling windows

5. **Implement Proper Forecast Accuracy Metrics**
   ```python
   # Compare segment-level forecasts to segment-level actuals
   for segment in segments:
       forecasted_96th = pre_crisis_model[segment].quantile(0.96)
       actual_96th = crisis_data[segment].quantile(0.96)
       error = actual_96th - forecasted_96th
   ```

6. **Document Dampening Strategy**
   - Clarify when to use revenue-based vs percentile-based dampening
   - Validate that dampened outliers don't distort percentile calculations

### **Low Priority Improvements**

7. **Add Model Diagnostics**
   - Q-Q plots comparing model distribution to normal/t-distribution
   - Temporal stability of percentiles
   - Segment sample size adequacy checks

8. **Consider Alternative Approaches**
   - Extreme Value Theory (EVT) for tail modeling
   - Conditional quantile regression to account for macroeconomic factors
   - Bootstrap confidence intervals around percentiles

---

## **Summary Assessment**

| Aspect | Rating | Comment |
|--------|--------|---------|
| **Data Preparation** | ⭐⭐⭐⭐ | Robust, well-documented pipeline |
| **Outlier Treatment** | ⭐⭐⭐ | Reasonable but has hardcoded bugs |
| **Model Logic** | ⭐⭐⭐⭐ | Sound percentile-based approach |
| **Backtesting** | ⭐⭐ | **In-sample validation, not true backtesting** |
| **Code Quality** | ⭐⭐⭐ | Good structure but sector-specific hardcoding |

**Overall**: The model's core methodology is sound, but the backtesting needs fundamental rework to provide genuine out-of-sample validation. The current approach suffers from look-ahead bias and doesn't truly test predictive accuracy.
