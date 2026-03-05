# Justification and Critique of IE Model Methodology

## **Executive Summary**
The Interest Expense model uses a **historical calibration approach** where entity-specific sensitivity parameters (Alpha) are derived from past relationships between corporate interest rates and central bank policy rates. This document evaluates the theoretical soundness, practical limitations, and potential improvements.

---

## **1. Core Methodology: Alpha = Correlation × Sensitivity**

### ✅ **Strengths**

#### **Theoretically Grounded**
```
Alpha = Correlation × Sensitivity
      = ρ(r_entity, r_cb) × [σ(r_entity) / σ(r_cb)]
```

This formulation captures two distinct aspects:
- **Correlation (ρ)**: Direction and strength of relationship
- **Sensitivity (σ ratio)**: Magnitude of response

**Why this makes sense:**
- Entities with floating-rate debt should track policy rates (high correlation)
- But the pass-through may vary by credit quality, debt structure, hedging (sensitivity)
- Multiplying these captures the **effective beta** to rate changes

#### **Entity-Specific Parameters**
- Avoids "one-size-fits-all" assumption
- Captures heterogeneity in:
  - Debt structure (floating vs. fixed)
  - Credit quality (spreads over benchmark)
  - Refinancing patterns
  - Hedging strategies

#### **Bounded Estimates**
```python
Alpha = (Correlation × Sensitivity).clip(alpha_min, alpha_max)
```
- Prevents extreme/unstable estimates
- Acknowledges estimation uncertainty
- Practical risk management (avoids tail scenarios)

### ⚠️ **Potential Issues**

#### **1. Stationarity Assumption**
**Problem:** Assumes the historical relationship (Alpha) will persist into the future

**Reality checks:**
- Companies refinance debt → changes debt structure
- Credit quality deteriorates/improves → changes spreads
- Hedging policies change
- Market regimes shift (QE vs. tightening cycles)

**Impact:** Alpha calculated in 2018-2023 may not apply to 2024+

#### **2. Sensitivity Formula Issues**
```python
sensitivity = std(entity_rate) / std(cb_rate)
```

**Concern:** This is NOT a proper regression beta. A true sensitivity would be:
```python
beta = cov(entity_rate, cb_rate) / var(cb_rate)
```

**Current formula issues:**
- `std(entity_rate)` includes idiosyncratic noise (company-specific shocks)
- Dividing by `std(cb_rate)` doesn't properly isolate systematic relationship
- Could inflate sensitivity estimates

**Better approach:**
```python
# This IS what standard beta captures:
beta = correlation × (std_entity / std_market)

# But a regression would be more robust:
from scipy.stats import linregress
slope, intercept, r_value, p_value, std_err = linregress(cb_rate, entity_rate)
alpha = slope  # This is the true sensitivity
```

#### **3. Correlation × Sensitivity Redundancy**

The formula `ρ × (σ_y / σ_x)` is mathematically equivalent to regression beta:
```
β = ρ × (σ_y / σ_x) = cov(x,y) / var(x)
```

**Why not just use regression beta directly?**
- Would be simpler and more standard
- Provides standard errors for confidence intervals
- Regression also gives R² and residual diagnostics

---

## **2. Data Processing Decisions**

### **A. 4-Quarter Moving Average (4QMA) of Central Bank Rates**

#### ✅ **Justified**
- **Smooths noise**: Policy rates can be sticky or have discrete jumps
- **Reflects lagged transmission**: Corporate debt doesn't reprice instantly
  - Fixed-rate bonds: Only reprice at maturity/refinancing
  - Floating-rate: Often quarterly resets (LIBOR/SOFR + spread)
- **Matches financial reporting**: Annual financial statements capture ~year of rates

#### 🤔 **Alternative considerations**
- Why 4 quarters specifically? Could test 2Q, 3Q, 6Q sensitivity
- Simple MA assumes equal weights → exponential MA might be better
- Could use rate at end-of-period instead of average

### **B. Year 2018+ Filter**

#### ✅ **Justified**
- **Regime shift**: Post-2008 crisis era (near-zero rates) vs. 2018+ normalization
- **Rate volatility**: Need variation in rates to estimate correlations
- **Data quality**: More recent data likely more relevant

#### ⚠️ **Concerns**
- **Small sample**: Only 5-6 years of data (2018-2023)
- **Regime-specific**: Calibrated in rising/high rate environment
- **What about next cycle?**: Will Alpha hold in rate-cutting cycle?

**Evidence from validation:**
- Pre-2018 hold-out test (lines 638-694) should reveal if this is an issue
- If validation R² is low, suggests regime-dependency

### **C. Interest Rate ≤ 0.5 Filter**

#### ✅ **Justified**
```python
interest_data = interest_data[interest_data["interest_rate"] <= 0.5]
```

**Rationale:** Interest rate > 50% likely indicates:
- Data errors (numerator/denominator in wrong units)
- Distressed/restructuring scenarios (not representative)
- Non-operating subsidiaries

#### 🤔 **Lost information**
- Filters out distressed entities
- Alpha may behave differently in stress (non-linear effects)
- Could bias toward "quality" borrowers

### **D. Minimum 4 Observations Requirement**

#### ✅ **Statistically necessary**
```python
leid_wanted = leid_counts[leid_counts > 3].index
```

**Why 4 is minimum:**
- Need degrees of freedom for correlation (n-2 df)
- Need temporal variation to measure sensitivity
- With 3 points, one outlier dominates

#### ⚠️ **Survivorship bias**
- Only includes entities with 4+ years of continuous data
- Excludes:
  - New borrowers (no history)
  - Defaulted/acquired entities (incomplete history)
- May underestimate risk

---

## **3. Backtesting Methodology**

### **A. Rolling 3-Period Window**

```python
WINDOW = 3
for i in range(WINDOW, len(g) - 1):
    window = g.iloc[i-WINDOW:i]
    alpha = compute_alpha(window, country)
    predict_change_at_t = g.iloc[i]["future_interest_change"]
```

#### ✅ **Strengths**
- **True out-of-sample**: Uses only past data to predict future
- **Expanding test set**: Tests across multiple time periods
- **Realistic**: Mimics how model would be used in practice

#### ⚠️ **Concerns**

**1. Short Estimation Window**
- Only 3 observations to calculate correlation
- Correlations highly unstable with small samples
- Standard error on 3-point correlation is huge

**Statistical issue:**
```python
# With n=3, correlation has ~1.4 standard error!
# Meaningless for inference
```

**Better approach:** Use expanding window or longer fixed window (e.g., 5 years)

**2. Overlapping Windows**
- Windows overlap significantly (t-3:t, t-2:t+1, t-1:t+2)
- Creates **serial correlation** in backtest results
- Overstates statistical significance

**3. Look-Ahead Bias Check**
```python
future_interest_change = rate[t+1] - rate[t]
```
✅ **Clean**: Predicting t→t+1 change using t-3:t data. No look-ahead bias.

### **B. Performance Metrics**

#### **1. Rank IC (Spearman Correlation)**
```python
rank_ic = alpha_ts_df["Alpha"].corr(
    alpha_ts_df["future_interest_change"],
    method="spearman"
)
```

#### ✅ **Good choice**
- **Rank-based**: Robust to outliers
- **Non-parametric**: Doesn't assume linear relationship
- **Industry standard**: Used in quantitative finance (factor analysis)

#### 🤔 **Interpretation**
- What's a "good" Rank IC?
  - In equity factor models: IC > 0.05 is decent, IC > 0.10 is excellent
  - For interest rate prediction: Lower bar, but should be positive and significant
- Should report **significance** (t-stat, p-value)

#### **2. Top-Minus-Bottom Quintile**
```python
buckets = pd.qcut(x["Alpha"], 5, duplicates="drop")
top_minus_bottom = bucket_perf.iloc[-1] - bucket_perf.iloc[0]
```

#### ✅ **Practical metric**
- Tests if high-Alpha entities actually have higher rate changes
- Directly interpretable
- Robust to outliers (uses quintiles)

#### ⚠️ **Missing information**
- Should also show **monotonicity**: Do quintiles increase smoothly?
- Need statistical test: Is difference significant?

#### **3. Out-of-Sample R²**
```python
X = sm.add_constant(x["Alpha"])
y = x["future_interest_change"]
model = sm.OLS(y, X, missing="drop").fit()

r2_oos = 1 - mse_model / mse_benchmark
```

#### ⚠️ **Misleading terminology**
- This is NOT truly "out-of-sample R²"
- It's **in-sample R²** on the backtest dataset
- True OOS R² would use holdout set not used in alpha calculation

**The validation set (pre-2018) is closer to true OOS**

#### **Missing: Economic Significance**
- R² tells us variance explained, but what about **magnitude**?
- Example: If Alpha = 0.5, and CB rate rises 1%, does entity rate rise 0.5%?
- Should report:
  - Mean predicted vs. actual changes
  - Mean absolute error in percentage points
  - RMSE in business terms

---

## **4. Validation Set (Pre-2018)**

### ✅ **Excellent practice**
```python
validate_data = validate_before2018(int_before_2018, MEVdata, all_country_frame)
```

**Why this is strong:**
- **True holdout**: Data not used in alpha estimation
- **Different regime**: Tests regime-robustness
- **Entity-level metrics**: R², MSE, MAE per borrower

### ⚠️ **Critical questions not answered in code:**

1. **What are the actual validation results?**
   - Is R² positive?
   - How does it compare to backtest R²?
   - If much worse → model is overfit or regime-specific

2. **Sample overlap issue:**
```python
df = df.merge(alpha_df[['spread_id','Alpha']], on='spread_id', how='left')
```
- Applies alpha to **same entities** in earlier period
- Better test: Apply **country-level** alpha to new entities
- Current approach tests "parameter stability" not "generalization"

---

## **5. Statistical and Methodological Concerns**

### **A. Multiple Testing Problem**

The model runs separately for each country:
```python
for country in interest_data.country_of_risk.unique():
    data = interest_expense(interest_data, MEVdata, country, sector)
```

**Issue:**
- Testing ~20-50 countries
- Some will show good IC by chance
- No multiple testing correction (Bonferroni, FDR)

**Should:**
- Report distribution of ICs across countries
- Test overall significance
- Flag low-sample countries

### **B. Aggregation to Country Level**

```python
if isWeighted:
    country_level_df = all_country_frame.groupby("Country").agg({
        "Alpha": lambda x: (
            (x * all_country_frame.loc[x.index, "irb_ead"]).sum()
            / all_country_frame.loc[x.index, "irb_ead"].sum()
        )
    })
```

#### ✅ **Weighting by exposure makes sense**
- Prioritizes large exposures
- Matches risk management objective

#### ⚠️ **Loss of information**
- Entity-level alpha distribution is lost
- What's the dispersion within country?
- Should report: mean, median, std, 10th/90th percentiles

### **C. Missing: Model Specification Tests**

**Should include:**

1. **Residual diagnostics**
   - Are errors normally distributed?
   - Heteroskedasticity test
   - Serial correlation (Durbin-Watson)

2. **Stability tests**
   - Are alphas stable over time?
   - Chow test for structural breaks
   - Rolling window alpha evolution

3. **Comparison to naive baselines**
   - Does entity-specific alpha beat country average?
   - Does it beat simple industry benchmarks?
   - Incremental R² from granularity?

---

## **6. Alternative Approaches to Consider**

### **A. Panel Regression**
Instead of entity-by-entity estimation:
```python
# Fixed effects panel regression
import statsmodels.formula.api as smf

model = smf.ols(
    'interest_rate ~ C(spread_id) * cb_rate_4qma',
    data=panel_data
).fit()
```

**Advantages:**
- Pools information across entities
- Standard errors and significance tests
- Can add controls (leverage, rating, sector)

### **B. Hierarchical/Bayesian Approach**
```python
# Partial pooling of estimates
import pymc3 as pm

with pm.Model() as hierarchical_model:
    # Country-level hyperpriors
    mu_alpha = pm.Normal('mu_alpha', mu=0.5, sd=0.2)
    sigma_alpha = pm.HalfNormal('sigma_alpha', sd=0.1)

    # Entity-level alphas (partially pooled)
    alpha = pm.Normal('alpha', mu=mu_alpha, sd=sigma_alpha, shape=n_entities)
```

**Advantages:**
- Shrinks unstable estimates toward group mean
- Quantifies uncertainty
- Better for small-sample entities

### **C. Time-Varying Alpha**
```python
# Allow alpha to evolve
from statsmodels.tsa.statespace.sarimax import SARIMAX

# State-space model where alpha_t follows random walk
```

**Rationale:**
- Capital structure changes over time
- Hedging policies adjust
- More realistic than assuming constant alpha

---

## **7. Overall Assessment**

### **Strengths** 🟢
1. ✅ **Proper out-of-sample testing** (rolling window)
2. ✅ **Multiple validation approaches** (backtest + holdout)
3. ✅ **Entity-specific heterogeneity** captured
4. ✅ **Practical constraints** (bounded alphas, minimum observations)
5. ✅ **Comprehensive data cleaning** with documented steps
6. ✅ **Industry-standard metrics** (Rank IC)

### **Methodological Concerns** 🟡
1. ⚠️ **Small estimation windows** (3 observations for correlation)
2. ⚠️ **Stationarity assumption** (past relationships persist)
3. ⚠️ **Regime-dependency** (calibrated in 2018-2023 environment)
4. ⚠️ **Survivorship bias** (requires 4+ years of data)
5. ⚠️ **No uncertainty quantification** (confidence intervals on alphas)
6. ⚠️ **Multiple testing** (many countries, no correction)

### **Critical Gaps** 🔴
1. ❌ **No significance testing** on alphas or ICs
2. ❌ **No comparison to benchmarks** (naive models)
3. ❌ **No stability analysis** (are alphas changing over time?)
4. ❌ **No economic magnitude interpretation** (just R², not actual error sizes)
5. ❌ **Validation results not displayed** in code (computed but not evaluated)

---

## **8. Recommendations**

### **Immediate Improvements:**

1. **Lengthen estimation window**
   ```python
   WINDOW = 5  # Or use expanding window
   ```

2. **Add statistical tests**
   ```python
   from scipy.stats import spearmanr
   rank_ic, p_value = spearmanr(alpha, future_change)
   ```

3. **Report validation performance**
   ```python
   print(f"Validation R²: {validate_data['r2'].mean():.3f}")
   print(f"Validation RMSE: {np.sqrt(validate_data['MSE'].mean()):.4f}")
   ```

4. **Benchmark comparison**
   ```python
   # Compare to country average
   naive_alpha = country_level_df.loc[entity_country, 'Alpha']
   improvement = r2_entity_specific - r2_naive
   ```

5. **Confidence intervals**
   ```python
   from scipy import stats
   ci = stats.bootstrap(
       (entity_rates, cb_rates),
       compute_alpha,
       n_resamples=1000
   )
   ```

### **Longer-term Enhancements:**

1. Consider **panel regression** for more robust estimates
2. Implement **regime-switching model** for QE vs. tightening cycles
3. Add **covariates** (leverage, rating, debt maturity)
4. Test **non-linear** relationships (alpha might vary with rate level)
5. Incorporate **forward guidance** (market expectations, not just realized rates)

---

## **Conclusion**

The model represents a **reasonable first approach** with sound intuition and proper backtesting structure. However, it suffers from **small sample limitations** and lacks **statistical rigor** in assessing significance and uncertainty.

**For production use**, the following are essential:
- Validation results must show positive out-of-sample R²
- Alphas should be stable across subperiods
- Entity-specific alphas should outperform country averages
- Confidence intervals should be reported for risk management

**Without seeing the actual validation performance metrics, we cannot definitively conclude the model is reliable for forward-looking stress testing.**
