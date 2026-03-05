# Overview of opex.py

This script implements a **stress testing model for Operating Expenses (OPEX)** across various sectors. It calculates percentile-based stress scenarios for the OPEX/Revenue ratio.

## Purpose
Generates stress impact scenarios for OPEX by analyzing historical financial data, computing year-over-year changes in OPEX/Revenue ratios, and producing percentile-based projections.

---

## Model Methodology

### 1. **Core Metric**
- **OPEX/Revenue ratio**: Primary indicator of operational efficiency
- **Delta OPEX/Rev**: Relative year-over-year change in the ratio
  - `delta_opex/rev = (OPEX/Rev_current - OPEX/Rev_previous) / OPEX/Rev_previous`

### 2. **Data Processing Pipeline**

```
Raw Financials → Data Cleaning → Segmentation → Delta Calculation →
Dampening (Outlier Treatment) → Percentile Calculation → Stress Scenarios
```

**Key Steps:**
1. **Step 1-4**: Filter by sector, remove missing/zero revenues
2. **Step 5**: Keep only OPEX/Revenue > 0 (configurable)
3. **Step 6**: Drop NAs in OPEX/Revenue or revenues
4. **Step 7**: Remove quarterly duplicates, keep annual data only
5. **Step 8-9**: Remove infinite values, create final modeling dataset

### 3. **Segmentation Approaches**
- By **sub-sector** (e.g., Commodity Traders: Chemicals, Energy, Metals)
- By **country** (if `segmentByCountry=True`)
- Optional **additional categories** (e.g., Producer vs Non-Producer)
- ISIC code mapping for sector classification

---

## Key Implementation Details

### **Dampening Methodology** (Outlier Treatment)
Two-step dampening process if `applyingDampener=True`:

**Step 1: Exclusion-based dampening**
- Loads exclusion list from revenue outlier model
- Multiplies flagged data points by dampener (0.0001 or 1)
- Tracks dampened counts by segment

**Step 2: Percentile-based dampening**
```python
# Default: 99th percentile (step_2_quantile = 0.99)
# Values > 99th percentile are either:
#   - Multiplied by 0.0001 (if dampned_for_revenue_outlier=True)
#   - Clipped to 99th percentile (winsorization, if False)
```

### **Revenue Adjustment** (Optional)
- If `dampned_for_revenue_outlier=False`, applies revenue adjustments from outlier model
- Replaces revenues for flagged outliers: `Revenue = Prev_Rev × (1 + y_winsor)`

---

## Stress Scenario Generation

### **Percentile-Based Approach**
For each segment, calculates percentiles from `percentiles_for_file` (e.g., [50, 75, 90, 95, 96, 97, 98, 99]):

- **Base**: 50th percentile (median)
- **Stress Impact**: `Stress_X = Percentile_X - Percentile_50`
- **Scenario Severity**: Expressed as "1 in X year" event
  - Example: 96th percentile = 1 in 25 year event

### **Historical Calibration**
Compares 2008/2009 crisis data against current distribution:
- **Historical percentile rank**: Where crisis values fall in overall distribution
- **Relative percentile**: Where crisis values fall in model percentiles
- **MAE/MSE**: Model accuracy metrics comparing 96th percentile forecast to actual crisis data

---

## Key Outputs

### **Excel Files**
1. **Full Data**: Percentile values, stress impacts, coverage, exception rates, crisis metrics
2. **Stress Impacts**: Melted format ready for stress testing models
3. **Consolidated**: Summary statistics, outlier details, panel data, charts

### **Charts** (embedded in Excel)
- Distribution histograms per sub-sector
- Percentile lines (green: 50th, red: stress percentiles)
- Orange/yellow lines: 2008/2009 historical crisis values

### **Summary Tables**
- Data filtering statistics by step
- Unique spread_ids and datapoints per segment
- Dampening/exclusion counts

---

## Notable Features

- **Flexible configuration**: Sector-specific settings via `Opex_config.py`
- **Global vs sector-specific models**: Can model all sectors together or individually
- **Coverage/exception tracking**: Monitors what % of data falls below/above stress thresholds
- **Crisis benchmarking**: Automatically compares model outputs to 2008-2009 financial crisis
- **Return period calculation**: Estimates rarity of crisis events (1 in X years)

---

## Current Configuration
The script is set to run **"Commodity Traders"** sector (line 1342), with other sectors commented out.
