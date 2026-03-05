# CAPEX Analysis Script Overview

## Purpose
The `capex.py` script performs comprehensive Capital Expenditure (CAPEX) analysis for financial risk modeling across multiple industry sectors. It calculates CAPEX-to-Revenue ratios and generates stress impact metrics based on percentile distributions.

## Main Workflow

### 1. Configuration & Data Loading
- Loads sector-specific configurations from `Capex_config.py`
- Reads financial data (CSV) and ISIC classification data (Excel)
- Configures sector-specific parameters including:
  - Top segments to analyze
  - Percentiles for stress testing
  - Country/sector grouping rules
  - Sub-segment mappings

### 2. ISIC Code Mapping
Two modes are supported:
- **Global Model**: Maps all ISIC codes to Risk Industries, excludes specified sectors
- **Non-Global Model**: Only tags data belonging to the target sector

### 3. Data Cleaning Pipeline
The script applies a systematic 9-step cleaning process:

| Step | Action | Purpose |
|------|--------|---------|
| 1 | Initial data load | Baseline count |
| 2 | Drop Revenue "Not applicable" | Remove invalid revenue entries |
| 3 | Drop Revenue "Missing" | Remove missing revenue data |
| 4 | Drop Revenue = 0 | Prevent division by zero |
| 5 | Calculate CAPEX/Revenue ratio | Core metric computation (floored at 0) |
| 6 | Drop NA values | Remove incomplete records |
| 7 | Remove duplicates | Keep only one record per ID/Year |
| 8 | Remove infinity values | Clean invalid calculations |
| 9 | Final modelling data | Ready for analysis |

At each step, the script generates a summary showing:
- Number of unique spread IDs per segment
- Total datapoints per segment

### 4. Data Dampening
- Reads exclusion/dampening file (Excel or CSV)
- Identifies matching (Date, ID) pairs
- Multiplies CAPEX/Revenue by 0.0001 for dampened points
- Tracks dampened datapoints by segment

### 5. Percentile Calculation
For each segment (country or sub-sector):
- Calculates configured percentiles (e.g., 50th, 60th, 67th, 75th, 90th, 97.5th)
- Computes stress impacts as: `percentile_value - baseline_value`
- Converts percentiles to "1 in x" scenario severity

### 6. Outputs Generated

#### A. Stress Impact File
**File**: `Capex_{sector}_Stress_Impacts.xlsx`

Contains:
- Driver: CAPEX
- Stress impact percentile
- Scenario Severity (1 in x)
- Sector name
- Sub-sector or Country
- Stress Impact value
- As of Date

#### B. Full Results File
**File**: `Capex_{sector} - Full Data.xlsx`

Contains summary table with:
- Sub-segment/Country
- Unique Spread IDs
- Data Points
- All percentile values
- Stress impacts for each percentile

#### C. PDF Charts
**File**: `Capex_{sector}.pdf`

Multi-page PDF with:
- Distribution histogram for each segment
- Percentile markers (green for median, red for others)
- Number of unique LEIDs/Spread IDs
- Optional aggregated segment chart

#### D. Datapoint Summary
**File**: `{sector}_Capex_Datapoints.xlsx`

Three sheets:
1. **Datapoints**: Total datapoints by step and segment
2. **UniqueSpreadIDs**: Unique ID counts by step and segment
3. **Dampened Datapoints**: Breakdown of dampened records

## Key Features

### Country/Sector Grouping
- Optional country grouping: Maps countries to regional groups
- Optional sector grouping: Maps sub-segments to larger groups

### Flexible Segmentation
- Can segment by country (`segmentByCountry=True`)
- Can segment by sub-sector/industry
- Supports "Others" category for non-top segments

### Chart Generation
- Uses matplotlib and seaborn for visualization
- Configurable bin edges and x-axis ranges
- Automatic percentile line overlays
- Exports to multi-page PDF

### Data Quality Controls
- Clips CAPEX/Revenue at 0 (no negative values)
- Removes infinity values
- Handles "Not applicable" and "Missing" data
- Deduplicates by ID and Year (keeps most recent month)

## Supported Sectors
The script processes the following sectors:
- O&G (Oil & Gas)
- Commodity Traders
- Metals & Mining
- Automobiles & Components
- Consumer Durables & Apparel
- Technology Hardware & Equipment
- Building Products, Construction & Engineering
- CRE (Commercial Real Estate)
- Other Capital Goods
- Transportation and Storage
- Global (cross-sector analysis)

## Technical Details

### Dependencies
```python
pandas          # Data manipulation
numpy           # Numerical operations
matplotlib      # Plotting
seaborn         # Statistical visualizations
datetime        # Date handling
warnings        # Warning suppression
```

### ID Column Flexibility
- Supports different ID columns (e.g., `spread_id`, `leid`)
- Configured per sector in `Capex_config.py`

### Date Handling
- Converts DATE_OF_FINANCIALS to datetime
- Extracts Year and Month
- Sorts by Year/Month to keep latest data per year

### Memory Efficiency
- Drops duplicates to reduce dataset size
- Uses `.dropna()` selectively
- Converts to appropriate data types (str, float)

## Usage

### Command Line
```python
python capex.py
```

### Programmatic
```python
from capex import Capex

# Run for specific sector
Capex("O&G")
Capex("Commodity Traders")
```

## Output Interpretation

### Stress Impact
Represents the **incremental change** in CAPEX/Revenue at various stress levels:
- Baseline: Median (50th percentile)
- Stress scenarios: Higher percentiles (60th, 67th, 75th, etc.)
- Formula: `Stress Impact = Pth percentile - 50th percentile`

### Scenario Severity (1 in x)
Converts percentile to probability:
- 90th percentile = 1 in 10 event
- 97.5th percentile = 1 in 40 event
- Formula: `1 in x = 100 / percentile`

## Best Practices

1. **Data Quality**: Ensure financial data has minimal "Missing" or "Not applicable" values
2. **ISIC Mapping**: Keep ISIC reference file up-to-date
3. **Exclusion File**: Maintain dampening file with anomalous datapoints
4. **Segment Selection**: Choose top segments based on data availability (aim for 30+ datapoints)
5. **Percentile Selection**: Use percentiles appropriate for risk appetite (higher = more conservative)

## Troubleshooting

### Low Datapoint Count
- Check if sector filter is too restrictive
- Review exclusion file (may be dampening too many points)
- Verify ISIC mapping includes relevant codes

### Extreme Values
- Review dampening effectiveness
- Check for data entry errors in source files
- Consider capping CAPEX/Revenue at reasonable threshold

### Missing Segments
- Verify segment names match configuration
- Check if data exists for that segment after filters
- Review sub_segment_mapping completeness
