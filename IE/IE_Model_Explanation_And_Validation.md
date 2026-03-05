# Interest Expense Model - Explanation & Validation Strategy

## 1. Current Model Overview

### What the Model Does
The Interest Expense (IE) model predicts how a company's interest rate on debt responds to changes in central bank monetary policy rates. The key output is **Alpha (α)**, a sensitivity parameter that quantifies the relationship between:
- **Input**: Central bank monetary policy rate (4-quarter moving average)
- **Output**: Entity-level interest rate (Interest Expense / Total Debt)

### Model Formula
For each entity (identified by `spread_id` or `LEID`):

```
Alpha (α) = Correlation × Sensitivity
```

Where:
- **Correlation**: Pearson correlation between entity interest rate and central bank rate over time
- **Sensitivity**: `std(entity_interest_rate) / std(central_bank_rate)`
- **Alpha is clipped**: Constrained to range [alpha_min, alpha_max] (e.g., [0, 1])

### How Alpha is Used (Prediction)
```
Expected Interest Rate Change = Alpha × Central Bank Rate Change
```

If Alpha = 0.7 and central bank rate increases by 1%, the entity's interest rate is expected to increase by 0.7%.

---

## 2. Current Model Methodology

### Step-by-Step Process

**A. Data Preparation (Lines 80-304)**
1. Load interest expense and total debt data for entities
2. Calculate interest rate: `interest_rate = InterestExpense / TotalDebt`
3. Filter data:
   - Remove NaN values
   - Keep one data point per entity per year (most recent quarter)
   - Remove zero debt and zero EAD
   - Filter interest rates > 0.5 (data quality issue)
   - Keep only years ≥ 2018
4. Merge with central bank rate data (4QMA)

**B. Main Model - Entity-Level Alpha Calculation (Lines 416-482)**
Function: `get_corr_df()`

For each entity:
1. Calculate standard deviation of entity interest rate over time
2. Calculate standard deviation of central bank rate over time
3. Calculate correlation between the two series
4. Calculate sensitivity: `std(entity_rate) / std(CB_rate)`
5. Calculate alpha: `correlation × sensitivity`
6. Clip alpha to [alpha_min, alpha_max]

**C. Country-Level Aggregation (Lines 615-636)**
- Aggregate entity-level alphas to country level
- Two methods: unweighted mean or EAD-weighted mean
- Calculate both local currency (LCY) and USD-based alphas

**D. Backtesting (Lines 515-601)**
- Rolling 3-year window approach
- For each entity, calculate alpha using historical data
- Compare alpha predictions to actual interest rate changes
- Calculate Rank IC (Spearman correlation) and R²

---

## 3. Current Model Type

**This is a LINEAR SENSITIVITY MODEL**, similar to:
- **Beta in CAPM**: Measures how stock returns move with market returns
- **Duration in fixed income**: Measures bond price sensitivity to interest rate changes
- **Factor models**: Where alpha represents factor loading/exposure

**It is NOT:**
- A classification model (no logistic regression)
- A causal model (assumes correlation = causation)
- A structural model (no economic theory embedded)

---

## 4. PROBLEMS with Current Implementation

### ❌ Critical Issues

1. **Wrong Sensitivity Formula in Backtesting** (Line 487)
   - Uses `mean()` instead of `std()` in denominator
   - Produces incorrect alpha values in backtest

2. **Look-Ahead Bias** (Lines 532-540)
   - Window includes current period, then predicts next period
   - Overstates predictive power

3. **Mislabeled R²** (Lines 565-567)
   - Calculates in-sample R² but labels as "OOS_R2"
   - No true out-of-sample validation

4. **Invalid Validation** (Lines 673-686)
   - Compares interest rate changes to rate × alpha (incompatible units)
   - Metrics are meaningless

---

## 5. RECOMMENDED VALIDATION APPROACHES

### A. Out-of-Sample Backtesting (Time-Series Cross-Validation)

**Expanding Window Approach:**
```
Train Period         | Test Period
---------------------|------------
2018-2020           | 2021
2018-2021           | 2022
2018-2022           | 2023
2018-2023           | 2024
```

**Implementation:**
```python
def expanding_window_backtest(data, min_train_years=3):
    """
    True out-of-sample backtesting with expanding window
    """
    results = []
    years = sorted(data['Year'].unique())

    for test_year in years[min_train_years:]:
        # Split data
        train_data = data[data['Year'] < test_year]
        test_data = data[data['Year'] == test_year]

        # Calculate alpha on TRAINING data only
        train_alphas = calculate_entity_alphas(train_data)

        # Predict on TEST data
        test_data = test_data.merge(train_alphas[['spread_id', 'Alpha']], on='spread_id')
        test_data['predicted_rate_change'] = (
            test_data['cb_rate_change'] * test_data['Alpha']
        )

        # Calculate metrics
        metrics = evaluate_predictions(
            y_true=test_data['actual_rate_change'],
            y_pred=test_data['predicted_rate_change']
        )
        metrics['test_year'] = test_year
        results.append(metrics)

    return pd.DataFrame(results)
```

---

### B. Performance Metrics for This Model

Since this is a **regression/prediction model** for continuous values (interest rate changes), use:

#### 1. **Mean Absolute Error (MAE)**
```python
MAE = mean(|actual_change - predicted_change|)
```
- **Interpretation**: Average prediction error in percentage points
- **Example**: MAE = 0.02 means predictions are off by ±2% on average
- **Why useful**: Easy to interpret, robust to outliers

#### 2. **Root Mean Squared Error (RMSE)**
```python
RMSE = sqrt(mean((actual_change - predicted_change)²))
```
- **Interpretation**: Penalizes large errors more than MAE
- **Why useful**: Standard metric for regression, comparable across models

#### 3. **Out-of-Sample R² (R²_OOS)**
```python
R²_OOS = 1 - (MSE_model / MSE_naive)

where:
- MSE_model = mean((y_actual - y_predicted)²)
- MSE_naive = mean((y_actual - mean(y_train))²)  # Using TRAIN mean
```
- **Interpretation**: Proportion of variance explained by model vs. naive baseline
- **Range**: Can be negative if model is worse than baseline
- **Why useful**: Measures improvement over simple mean prediction

#### 4. **Rank IC (Information Coefficient)**
```python
Rank_IC = spearman_correlation(predicted_change, actual_change)
```
- **Interpretation**: Monotonic relationship between predictions and actuals
- **Range**: [-1, 1], where 1 = perfect ranking
- **Why useful**: Measures if model correctly ranks entities by interest rate sensitivity

#### 5. **Hit Rate / Direction Accuracy**
```python
Hit_Rate = mean(sign(predicted_change) == sign(actual_change))
```
- **Interpretation**: % of times model correctly predicts direction of change
- **Why useful**: Simple to interpret, relevant for decision-making

#### 6. **Calibration Plot**
```python
# Bucket predictions and compare to actuals
buckets = pd.qcut(predicted_change, q=10)
calibration = df.groupby(buckets).agg({
    'predicted_change': 'mean',
    'actual_change': 'mean'
})
plot(calibration['predicted_change'], calibration['actual_change'])
# Should be close to 45-degree line
```

---

### C. Recommended Validation Framework

```python
def comprehensive_validation(data, alphas):
    """
    Complete validation suite for interest expense model
    """
    # Merge alphas with test data
    df = data.merge(alphas[['spread_id', 'Alpha']], on='spread_id')

    # Calculate predicted change
    df['actual_change'] = df.groupby('spread_id')['interest_rate'].diff()
    df['cb_rate_change'] = df.groupby('spread_id')['cb_rate_4qma'].diff()
    df['predicted_change'] = df['Alpha'] * df['cb_rate_change']

    # Remove first observation per entity (NaN from diff)
    df = df.dropna(subset=['actual_change', 'predicted_change'])

    # Calculate metrics
    metrics = {
        'MAE': mean_absolute_error(df['actual_change'], df['predicted_change']),
        'RMSE': np.sqrt(mean_squared_error(df['actual_change'], df['predicted_change'])),
        'R2_OOS': calculate_r2_oos(df['actual_change'], df['predicted_change']),
        'Rank_IC': df['predicted_change'].corr(df['actual_change'], method='spearman'),
        'Hit_Rate': (np.sign(df['predicted_change']) == np.sign(df['actual_change'])).mean(),
        'N_observations': len(df),
        'N_entities': df['spread_id'].nunique()
    }

    # Country-level metrics
    country_metrics = df.groupby('country_of_risk').apply(
        lambda x: pd.Series({
            'MAE': mean_absolute_error(x['actual_change'], x['predicted_change']),
            'Rank_IC': x['predicted_change'].corr(x['actual_change'], method='spearman'),
            'N_obs': len(x)
        })
    )

    return metrics, country_metrics

def calculate_r2_oos(y_true, y_pred, y_train_mean=None):
    """
    True out-of-sample R²
    If y_train_mean is None, uses mean of y_true (in-sample)
    """
    if y_train_mean is None:
        y_train_mean = y_true.mean()

    mse_model = np.mean((y_true - y_pred)**2)
    mse_baseline = np.mean((y_true - y_train_mean)**2)

    return 1 - (mse_model / mse_baseline)
```

---

### D. Cross-Sectional Validation (Buckets/Quantiles)

**Quintile Analysis:**
```python
def quintile_analysis(df):
    """
    Bucket entities by predicted sensitivity (Alpha)
    Compare average actual changes across buckets
    """
    df['alpha_quintile'] = pd.qcut(df['Alpha'], q=5, labels=['Q1', 'Q2', 'Q3', 'Q4', 'Q5'])

    quintile_perf = df.groupby('alpha_quintile').agg({
        'actual_change': 'mean',
        'predicted_change': 'mean',
        'spread_id': 'count'
    })

    # Top-Bottom Spread
    top_minus_bottom = quintile_perf['actual_change'].iloc[-1] - quintile_perf['actual_change'].iloc[0]

    return quintile_perf, top_minus_bottom
```

**Expected Behavior:**
- Q5 (high alpha) should have larger actual changes than Q1 (low alpha)
- Monotonic relationship: Q1 < Q2 < Q3 < Q4 < Q5

---

### E. Rolling Window Validation (Walk-Forward)

**Fixed Window Approach:**
```python
def rolling_window_validation(data, window_size=3, step=1):
    """
    Walk-forward validation with fixed window

    Window 1: [2018, 2019, 2020] → test 2021
    Window 2: [2019, 2020, 2021] → test 2022
    Window 3: [2020, 2021, 2022] → test 2023
    """
    results = []
    years = sorted(data['Year'].unique())

    for i in range(len(years) - window_size):
        train_years = years[i:i+window_size]
        test_year = years[i+window_size]

        train_data = data[data['Year'].isin(train_years)]
        test_data = data[data['Year'] == test_year]

        # Calculate alpha on training window
        train_alphas = calculate_entity_alphas(train_data)

        # Predict on test year
        test_results = predict_and_evaluate(test_data, train_alphas)
        test_results['train_years'] = f"{train_years[0]}-{train_years[-1]}"
        test_results['test_year'] = test_year

        results.append(test_results)

    return pd.DataFrame(results)
```

---

## 6. Additional Validation Checks

### A. Stability Analysis
```python
def alpha_stability_check(data):
    """
    Check if alpha estimates are stable over time
    """
    # Calculate alpha using first half vs second half of data
    mid_year = data['Year'].median()

    alpha_first_half = calculate_entity_alphas(data[data['Year'] <= mid_year])
    alpha_second_half = calculate_entity_alphas(data[data['Year'] > mid_year])

    comparison = alpha_first_half.merge(
        alpha_second_half,
        on='spread_id',
        suffixes=('_first', '_second')
    )

    # Correlation between first and second half alphas
    stability_corr = comparison['Alpha_first'].corr(comparison['Alpha_second'])

    # Average absolute difference
    avg_diff = (comparison['Alpha_first'] - comparison['Alpha_second']).abs().mean()

    return stability_corr, avg_diff, comparison
```

### B. Sensitivity to Window Length
```python
def window_sensitivity_test(data, windows=[2, 3, 4, 5]):
    """
    Test how alpha estimates vary with different window lengths
    """
    results = {}
    for window in windows:
        # Calculate alpha using only last 'window' years
        recent_data = data[data['Year'] >= (data['Year'].max() - window)]
        alphas = calculate_entity_alphas(recent_data)
        results[f'{window}yr'] = alphas

    # Compare correlations between different window lengths
    correlations = pd.DataFrame(index=windows, columns=windows)
    for w1 in windows:
        for w2 in windows:
            merged = results[f'{w1}yr'].merge(
                results[f'{w2}yr'],
                on='spread_id',
                suffixes=(f'_{w1}yr', f'_{w2}yr')
            )
            correlations.loc[w1, w2] = merged[f'Alpha_{w1}yr'].corr(merged[f'Alpha_{w2}yr'])

    return correlations
```

### C. Minimum Data Requirements
```python
def min_data_point_analysis(data, min_points_range=[3, 4, 5, 6]):
    """
    Test model performance vs. minimum data points required per entity
    """
    results = []
    for min_points in min_points_range:
        # Filter entities with enough data points
        entity_counts = data.groupby('spread_id').size()
        valid_entities = entity_counts[entity_counts >= min_points].index

        filtered_data = data[data['spread_id'].isin(valid_entities)]

        # Calculate performance
        metrics = calculate_validation_metrics(filtered_data)
        metrics['min_points'] = min_points
        metrics['n_entities'] = len(valid_entities)

        results.append(metrics)

    return pd.DataFrame(results)
```

---

## 7. Benchmark Models

Compare against these baselines:

### A. Naive Models
1. **Mean Persistence**: Predict next period = current period
2. **Zero Change**: Predict change = 0
3. **Historical Mean**: Predict change = entity's historical average change

### B. Alternative Specifications
1. **Linear Regression**: `interest_rate_change ~ cb_rate_change` (pooled)
2. **Fixed Effects**: `interest_rate_change ~ cb_rate_change + entity_FE`
3. **Random Coefficient**: Allow alpha to vary by entity (already done) + industry/country effects

---

## 8. Recommended Metrics Summary Table

| Metric | Type | Interpretation | Good Performance | Use Case |
|--------|------|----------------|------------------|----------|
| **MAE** | Error | Avg absolute error | < 1% | Easy interpretation |
| **RMSE** | Error | Penalizes large errors | < 1.5% | Standard regression metric |
| **R²_OOS** | Fit | Variance explained | > 0.10 | Compare to baseline |
| **Rank IC** | Ranking | Spearman correlation | > 0.3 | Cross-sectional ranking |
| **Hit Rate** | Direction | % correct direction | > 60% | Practical decisions |
| **Top-Bottom** | Strategy | High-Low performance gap | Significant & positive | Cross-sectional validation |

---

## 9. Implementation Priority

### Phase 1: Fix Current Bugs (CRITICAL)
1. Fix sensitivity calculation in `compute_alpha()` (line 487)
2. Remove look-ahead bias from backtesting (lines 532-540)
3. Fix validation variable mismatch (lines 673, 680-686)

### Phase 2: Implement Proper OOS Validation
1. Implement expanding window backtest
2. Calculate true R²_OOS using train set mean as baseline
3. Add MAE, RMSE, Rank IC, Hit Rate

### Phase 3: Robustness Checks
1. Alpha stability over time
2. Sensitivity to window length
3. Minimum data point requirements
4. Country-level performance breakdown

### Phase 4: Model Enhancements (If Needed)
1. Consider regime-dependent alphas (low rate vs high rate environments)
2. Add industry/sector fixed effects
3. Explore non-linear relationships
4. Add macroeconomic controls (GDP growth, inflation, credit spreads)

---

## 10. Expected Performance Benchmarks

For this type of sensitivity model in corporate finance:

| Metric | Weak | Acceptable | Good | Excellent |
|--------|------|------------|------|-----------|
| R²_OOS | < 0 | 0.05 - 0.10 | 0.10 - 0.20 | > 0.20 |
| Rank IC | < 0.1 | 0.1 - 0.2 | 0.2 - 0.3 | > 0.3 |
| MAE (% pts) | > 2% | 1-2% | 0.5-1% | < 0.5% |
| Hit Rate | < 55% | 55-60% | 60-65% | > 65% |

**Note:** Interest rate sensitivity is inherently noisy due to:
- Contractual terms (fixed vs floating rate debt)
- Refinancing decisions
- Credit quality changes
- Company-specific factors

Expectations should be calibrated accordingly. Even modest R²_OOS (5-10%) can be economically meaningful.
