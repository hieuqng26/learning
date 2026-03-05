# Overview of IE.py - Interest Expense Model

## **Purpose**
This script models the relationship between corporate interest expenses and central bank monetary policy rates, calculating entity-specific "Alpha" parameters that capture how sensitive each borrower's interest costs are to rate changes.

---

## **Model Methodology**

### 1. **Core Concept**
- **Alpha Parameter**: Measures how an entity's interest rate responds to changes in central bank policy rates
- **Formula**: `Alpha = Correlation × Sensitivity`
  - **Correlation**: Between entity's interest rate and central bank rate (4QMA)
  - **Sensitivity**: `std(entity_interest_rate) / std(central_bank_rate)`
- Alpha is clipped to `[alpha_min, alpha_max]` range (configured per sector)

### 2. **Data Processing Pipeline** (Lines 195-303)
```
Step 1: Load raw data
Step 2: Drop NaN in InterestExpense/TotalDebt
Step 3: Keep one datapoint per entity per year (latest quarter)
Step 4: Filter irb_ead != 0
Step 5: Filter TotalDebt != 0
Step 6: Filter InterestExpense != 0 (if configured)
Step 7: Filter interest_rate <= 0.5 (data quality)
Step 8: Filter years >= 2018 (modeling period)
```

### 3. **Interest Rate Calculation**
- `interest_rate = InterestExpense / TotalDebt`
- Merges with 4-quarter moving average of central bank rates
- Uses both local currency (LCY) and US dollar (FCY) rates

### 4. **Entity-Level Alpha** (Lines 416-482)
For each entity (spread_id):
- Requires **minimum 4 data points**
- Calculates standard deviations and correlations
- Produces both Alpha (local rate) and Alpha_US (US rate fallback)

### 5. **Aggregation** (Lines 615-636)
- **Weighted**: By `irb_ead` (IRB Exposure at Default)
- **Unweighted**: Simple average
- Aggregates to country level with "Others" bucket

---

## **Backtesting Methodology** (Lines 515-601)

### **Rolling Window Out-of-Sample Test**

```python
WINDOW = 3  # Use 3 periods to calculate alpha
```

**Process:**
1. For each entity with >3 observations:
   - At each time point `t` (starting at t=4):
     - Use periods `[t-3, t-2, t-1]` to calculate alpha
     - Predict interest change from `t` to `t+1`
     - Record: `future_interest_change = rate[t+1] - rate[t]`

2. Build dataset of (Alpha, future_interest_change) pairs

### **Performance Metrics:**

#### **1. Rank IC (Information Coefficient)** - Line 543
```python
rank_ic = alpha_ts_df["Alpha"].corr(
    alpha_ts_df["future_interest_change"],
    method="spearman"
)
```
- Spearman correlation between predicted alpha and actual future changes
- Measures rank-order predictive power

#### **2. Top-Minus-Bottom** - Lines 551-557
```python
buckets = pd.qcut(x["Alpha"], 5, duplicates="drop")
bucket_perf = x.groupby(buckets)["future_interest_change"].mean()
top_minus_bottom = bucket_perf.iloc[-1] - bucket_perf.iloc[0]
```
- Sorts alphas into 5 quintiles
- Compares average future interest change in highest vs lowest bucket
- Measures discriminatory power

#### **3. Out-of-Sample R²** - Lines 559-567
```python
X = sm.add_constant(x["Alpha"])
y = x["future_interest_change"]
model = sm.OLS(y, X, missing="drop").fit()

r2_oos = 1 - mse_model / mse_benchmark
```
- OLS regression: `future_change ~ Alpha`
- R² relative to naive mean forecast
- Measures explained variance

### **Output Tables:**
- `full_df`: Overall backtest metrics
- `bt_all_country_df`: Country-level rank_ic, n_obs, top_minus_bottom, OOS_R²
- `bt_final_all_df`: Entity-level average alpha, std, observation count

---

## **Validation Set** (Lines 638-694)

### **Pre-2018 Hold-Out Validation**

**Setup:**
- Training: Data from 2018 onwards → calculate alphas
- Validation: Data before 2018 → test alpha performance

**Process:**
1. Apply learned alphas to pre-2018 entities
2. Calculate expected interest rate: `monetary_rate × Alpha`
3. Compare to actual interest rate changes

**Metrics (per entity):**
```python
'r2': r2_score(y_true, y_pred)
'MSE': mean_squared_error(y_true, y_pred)
'MAE': mean_absolute_error(y_true, y_pred)
```

---

## **Key Model Features**

✅ **Strengths:**
- Entity-specific sensitivities (not one-size-fits-all)
- Robust backtesting with rolling windows
- Multiple validation approaches (OOS + hold-out)
- Handles missing local rates with US fallback
- Comprehensive data quality filtering

⚠️ **Requirements:**
- Minimum 4 observations per entity
- Data quality filters (e.g., interest_rate ≤ 0.5)
- Sufficient central bank rate volatility for meaningful correlation

📊 **Output:**
- LEID-level alphas with LCY/FCY designation
- Country-level aggregated alphas
- Backtesting performance metrics
- Validation metrics on historical data
- Distribution charts and summary tables

---

## **Summary**

The model essentially learns how individual borrowers' interest costs historically responded to rate changes, then tests whether those learned relationships can predict future rate changes out-of-sample.
