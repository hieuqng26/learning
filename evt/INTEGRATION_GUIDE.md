# Quick Integration Guide: Adding EVT to Your Opex Model

## Files Created

1. **`evt_model.py`** - Core EVT modeling class (GPDModel)
2. **`evt_backtest.py`** - Backtesting functionality
3. **`run_evt_analysis.py`** - Complete analysis script
4. **`evt_implementation_guide.md`** - Detailed documentation

---

## Quick Start (3 Steps)

### Step 1: Add Import to `opex.py`

Add this at the top of your `opex.py` file (around line 15):

```python
# Add EVT analysis
try:
    from run_evt_analysis import run_evt_analysis
    EVT_AVAILABLE = True
except ImportError:
    print("EVT modules not available. Install scipy to enable EVT analysis.")
    EVT_AVAILABLE = False
```

### Step 2: Add EVT Call at End of `Opex()` Function

Add this code at the very end of the `Opex()` function (around line 1333, just before the final `print` statement):

```python
    # ========================================================================
    # EVT ANALYSIS AND BACKTESTING
    # ========================================================================
    if EVT_AVAILABLE:
        try:
            print("\n" + "="*80)
            print("RUNNING EVT ANALYSIS")
            print("="*80)

            evt_results = run_evt_analysis(
                opex_data=Opex_clean_rel_exclude_add_cat,
                sector=sector,
                output_dir=f"{output_temp}/{sector_name}",
                test_crisis_years=[2008, 2009],
                training_years=10
            )

            # Optionally add EVT results to your consolidated Excel
            with pd.ExcelWriter(sum_path, engine='openpyxl', mode='a') as writer:
                evt_results['evt_summary'].to_excel(
                    writer,
                    sheet_name='EVT_Summary',
                    index=False
                )
                if not evt_results['backtest_results'].empty:
                    evt_results['backtest_results'].to_excel(
                        writer,
                        sheet_name='EVT_Backtest',
                        index=False
                    )
                if not evt_results['comparison'].empty:
                    evt_results['comparison'].to_excel(
                        writer,
                        sheet_name='EVT_vs_Empirical',
                        index=False
                    )

        except Exception as e:
            print(f"Warning: EVT analysis failed with error: {e}")
            print("Continuing without EVT analysis...")

    print("export to excel completed!!")
```

### Step 3: Run Your Code

```python
python opex.py
```

That's it! Your existing code will now include EVT analysis.

---

## What You'll Get

### New Excel Sheets in Your Consolidated File

1. **EVT_Summary**: EVT parameters by sub-sector
   - Shape parameter (tail behavior)
   - Scale parameter
   - Percentiles (80th, 90th, 96th, 99th)
   - Return levels (1-in-25yr, 1-in-100yr, etc.)

2. **EVT_Backtest**: Out-of-sample backtest results
   - 2008 and 2009 crisis forecasts vs actuals
   - EVT errors vs Empirical errors
   - 95% confidence intervals
   - Coverage indicators

3. **EVT_vs_Empirical**: Direct comparison
   - Shows which method performed better
   - Errors by percentile level
   - Win rate statistics

### New Output Files

1. **`[Sector]_EVT_Analysis.xlsx`**: Comprehensive EVT results
2. **`evt_diagnostics/`** folder with diagnostic plots:
   - Q-Q plots
   - Probability plots
   - Density plots
   - Return level plots
   - Mean excess plots
3. **`backtest_2008_96th.png`**: Visualization of 2008 backtest
4. **`backtest_2009_96th.png`**: Visualization of 2009 backtest

---

## Stand-Alone Usage (Without Modifying opex.py)

If you prefer NOT to modify `opex.py`, you can run EVT analysis separately:

```python
import pandas as pd
from run_evt_analysis import run_evt_analysis

# Load your processed Opex data
# Option 1: From the "Outlier Panel data" sheet in your consolidated Excel
opex_data = pd.read_excel(
    r"C:\Users\1665642\OneDrive - Standard Chartered Bank\Documents\test_run\Commodity Traders\CT_Opex_Consolidated.xlsx",
    sheet_name="Outlier Panel data"
)

# Option 2: Export from opex.py before final output
# Add this line before the final excel export in opex.py:
# Opex_clean_rel_exclude_add_cat.to_csv('temp_opex_data.csv', index=False)
# Then load here:
# opex_data = pd.read_csv('temp_opex_data.csv')

# Run EVT analysis
results = run_evt_analysis(
    opex_data=opex_data,
    sector='Commodity Traders',
    output_dir=r'C:\Users\1665642\OneDrive - Standard Chartered Bank\Documents\test_run\Commodity Traders',
    test_crisis_years=[2008, 2009],
    training_years=10
)

print("\nEVT analysis complete!")
print(f"Results saved to: {output_dir}")
```

---

## Customization Options

### Change Threshold

Default is 90th percentile. To use 85th:

```python
# In evt_model.py or when calling GPDModel:
evt = GPDModel(data, threshold_quantile=0.85)
```

### Add More Crisis Years

Test 2020 COVID crisis:

```python
results = run_evt_analysis(
    opex_data=opex_data,
    sector='Commodity Traders',
    output_dir='...',
    test_crisis_years=[2008, 2009, 2020],  # Added 2020
    training_years=10
)
```

### Change Percentiles to Test

Edit in `evt_backtest.py`, line ~50:

```python
test_percentiles = [0.75, 0.80, 0.90, 0.95, 0.96, 0.99, 0.995]
```

### Disable Confidence Intervals (Faster)

```python
backtest_results = backtester.backtest_crisis_year(
    crisis_year=2008,
    training_years=10,
    compute_ci=False  # Skip bootstrap CI calculation
)
```

---

## Interpreting Results

### Shape Parameter (ξ)

- **ξ > 0.1**: Heavy tail → Extreme events more likely than normal distribution
  - Use EVT! Your tail is fat.
  - Example: ξ = 0.3 means very heavy tail

- **-0.1 < ξ < 0.1**: Exponential tail → Moderate extremes
  - EVT still useful but less critical

- **ξ < -0.1**: Light tail → Bounded distribution
  - EVT may not be necessary
  - Empirical percentiles might be sufficient

### Backtest Errors

- **EVT_Error < Empirical_Error**: EVT performed better ✓
- Look at **Coverage**: Did actual fall within 95% CI?
  - Good coverage ≈ 95% of cases should be covered
  - Under-coverage: Model underestimates risk
  - Over-coverage: Model is too conservative

### When to Use EVT vs Empirical

Use **EVT** when:
- ✓ Shape parameter > 0.1 (heavy tail)
- ✓ You need 96th+ percentiles
- ✓ Sample size > 100
- ✓ Backtests show EVT outperforms

Use **Empirical** when:
- ✓ Small sample (< 50 obs)
- ✓ Only need up to 90th percentile
- ✓ Shape parameter ≈ 0 (exponential tail)

**Best Practice**: Hybrid approach
- Use empirical for 50th-90th percentiles
- Use EVT for 96th+ percentiles
- Report both with confidence intervals

---

## Troubleshooting

### "Model must be fitted first"
**Solution**: Call `model.fit()` before using `quantile()` or `summary()`

### "Very few exceedances" warning
**Solution**:
- Lower threshold (try 0.85 instead of 0.90)
- Or use empirical percentiles for this sub-sector

### "Error fitting model: Invalid value encountered"
**Cause**: Extreme outliers or insufficient data
**Solution**:
- Check your dampening logic
- Ensure at least 50+ observations per sub-sector
- Verify no NaN or inf values in data

### EVT gives worse errors than empirical
**Possible reasons**:
1. Sample size too small (< 100)
2. Threshold too high/low
3. Data has structural breaks
4. Not truly a heavy-tailed distribution

**Solution**: Check diagnostic plots, try different thresholds, or stick with empirical method

---

## Next Steps

1. **Run on one sector first** (e.g., Commodity Traders)
2. **Check diagnostic plots** - do they look reasonable?
3. **Review backtest results** - does EVT outperform?
4. **Compare to current model outputs** in your Excel
5. **If successful**, roll out to all sectors
6. **Document findings** in methodology

---

## Questions?

- Check `evt_implementation_guide.md` for detailed theory
- Review diagnostic plots for model quality
- Compare EVT vs Empirical errors in backtest results
- Look at shape parameters to understand tail behavior

**Key principle**: EVT is most valuable for modeling rare events (96th+ percentiles) when you have heavy-tailed distributions. Always validate with backtesting!
