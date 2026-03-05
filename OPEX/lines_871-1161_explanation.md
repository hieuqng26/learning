# Explanation: Lines 871-1161 - Results Generation & Formatting

This section is the **core output generation engine** of the OPEX model. It calculates stress scenarios, validates against historical crises, and formats results for Excel export.

---

## High-Level Overview

**Purpose**: Generate two main output files:
1. **Full Results**: Wide format with all metrics per segment
2. **Stress Impacts**: Long/melted format ready for stress testing models

**Process Flow**:
```
Optional Categorization (871-880)
    ↓
Loop: Calculate Metrics per Segment (886-985)
    ↓
Format Results - Full Data (987-1023)
    ↓
Transform to Long Format (1025-1079)
    ↓
Add Metadata & Formatting (1081-1161)
```

---

## Section-by-Section Breakdown

### 1. Additional Categorization Setup (Lines 871-880)

**Purpose**: Optional secondary segmentation (e.g., Oil & Gas: Producer vs. Non-Producer)

```python
def additionalCategorizationFunction(data):
    # Maps ISIC codes 2200, 2203 to "Producer", rest to "Others"
    def mapping(x): return "Producer" if x in {2200, 2203} else "Others"
    return data["isic_code"].map(mapping).fillna("Others")

for outputAddCat in outputAddCats:  # Loop: False (no addCat), then True (with addCat)
    Opex_clean_rel_exclude_add_cat = Opex_clean_rel_exclude.copy()
    if outputAddCat:
        # Add additional category column (e.g., "Producer" vs "Others")
        Opex_clean_rel_exclude_add_cat[additionalCategoryColumnName] = (
            additionalCategorizationFunction(Opex_clean_rel_exclude_add_cat)
        )
```

**Key Points**:
- Runs **twice**: once without additional categorization, once with
- Currently only used for O&G sector to split by Producer/Non-Producer
- Configured via `useAdditionalCategory` flag

---

### 2. Calculate Metrics Per Segment (Lines 882-985)

**Purpose**: Core calculation loop - computes all statistics for each segment

#### 2.1 Loop Setup (Lines 886-896)
```python
result_data_full = []  # Collect results

for top_segment in top_segments:  # e.g., ["Chemicals", "Energy", "Metals", "Others"]
    for addCat in additionalCategories if outputAddCat else [None]:
        # Filter data for this specific segment (and addCat if applicable)
        if addCat:
            mask = (data["TOPS"] == top_segment) & (data[addCatCol] == addCat)
        else:
            mask = (data["TOPS"] == top_segment)
        subset = data[mask]
```

**Example**:
- Without addCat: 4 segments → 4 iterations
- With addCat (2 categories): 4 segments × 2 categories → 8 iterations

#### 2.2 Basic Statistics (Lines 898-911)
```python
# Count unique companies and data points
unique_spread_id = subset[id_column_name].nunique()
data_points = len(subset)

# Calculate percentiles (e.g., 50th, 75th, 90th, 95th, 96th, 97th, 98th, 99th)
percentile_values = subset["delta_opex/rev"].quantile([p/100 for p in percentiles_for_file]).values

# Calculate stress impacts = stress percentile - base percentile
stresses = np.array(percentile_values[1:]) - percentile_values[0]
# Example: 96th percentile - 50th percentile = stress impact for "1 in 25 year" scenario
```

**Output**:
- `unique_spread_id`: Number of unique companies in segment
- `data_points`: Total observations
- `percentile_values`: Array of percentile values [p50, p75, p90, p95, p96, p97, p98, p99]
- `stresses`: Stress impacts [p75-p50, p90-p50, ..., p99-p50]

#### 2.3 Crisis Data Analysis (Lines 913-932)
```python
# Extract 2008 and 2009 crisis data
crisis_data2008 = subset[subset["Year"].isin([2008])]
crisis_data2009 = subset[subset["Year"].isin([2009])]
x_crisis_08 = crisis_data2008["delta_opex/rev"].mean()
x_crisis_09 = crisis_data2009["delta_opex/rev"].mean()

# Calculate percentile rank (where does crisis value fall in distribution?)
model_data = subset["delta_opex/rev"]
percentile_rank_08 = (model_data <= x_crisis_08).mean()  # % of data <= crisis value
percentile_rank_09 = (model_data <= x_crisis_09).mean()

# Calculate return period (1 in X year event)
tail_prob_08 = 1 - percentile_rank_08  # Probability of exceeding crisis value
return_period_08 = 1/tail_prob_08 if tail_prob_08 > 0 else np.inf
# Example: If percentile_rank = 96%, then tail_prob = 4%, return_period = 1/0.04 = 25 years

# Map crisis value to model percentiles using interpolation
percentile_08 = np.interp(x_crisis_08, percentile_values, percentiles_for_file)
# Example: If crisis value = 0.15, and it falls between p95 and p96, result might be 95.5
```

**Output**:
- `x_crisis_08/09`: Mean delta OPEX/Rev during crisis years
- `percentile_rank_08/09`: Historical percentile rank (0-1)
- `return_period_08/09`: Return period in years
- `percentile_08/09`: Mapped percentile in model distribution

#### 2.4 Model Validation - MAE/MSE (Lines 934-946)
```python
# Compare model's 96th percentile forecast to actual crisis values
target_perc = 96  # 1 in 25 year scenario
target_idx = np.abs(np.array(percentiles_for_file) - target_perc).argmin()
forecasted_stress = percentile_values[target_idx] - percentile_values[0]
# Example: forecasted_stress = p96 - p50 = 0.18 - 0.02 = 0.16 (16% stress)

crisis_data_clean_2008 = crisis_data2008["delta_opex/rev"].dropna()
crisis_data_clean_2009 = crisis_data2009["delta_opex/rev"].dropna()

# Calculate forecast error metrics
mae_2008 = mean_absolute_error(
    crisis_data_clean_2008,
    [forecasted_stress] * len(crisis_data_clean_2008)
)
# Example: If actual 2008 values = [0.14, 0.16, 0.18] and forecast = 0.16
# MAE = mean(|0.14-0.16|, |0.16-0.16|, |0.18-0.16|) = mean(0.02, 0, 0.02) = 0.013

mse_2008 = mean_squared_error(crisis_data_clean_2008, [forecasted_stress]*len(...))
# Same as MAE but squared: MSE = mean((0.02)², 0², (0.02)²) = 0.00027
```

**Output**:
- `mae_2008/09`: Mean Absolute Error (average forecast error)
- `mse_2008/09`: Mean Squared Error (penalizes large errors more)

#### 2.5 Coverage & Exception Rates (Lines 948-959)
```python
actual = subset["delta_opex/rev"]

# Coverage = proportion of actuals at or below each stress threshold
coverage = {
    stress_level: (actual <= stress_level).mean()
    for stress_level in percentile_values[1:]  # For each stress scenario
}
# Example: For p96, coverage might be 0.94 (94% of actuals fall below p96)

# Exception rate = proportion of actuals exceeding each stress threshold
exception_rate = {
    stress_level: (actual > stress_level).mean()
    for stress_level in percentile_values[1:]
}
# Example: For p96, exception_rate = 0.06 (6% of actuals exceed p96)

coverage_list = [coverage[stress_lvl] for stress_lvl in percentile_values[1:]]
exception_list = [exception_rate[stress_lvl] for stress_lvl in percentile_values[1:]]
```

**Output**:
- `coverage_list`: [coverage at p75, p90, p95, p96, p97, p98, p99]
- `exception_list`: [exception at p75, p90, p95, p96, p97, p98, p99]

**Note**: These should sum to 1.0, but won't if there are NaN values (see Bug #14)

#### 2.6 Append Results (Lines 961-985)
```python
# Compile all metrics into one row
result_data_full.append(
    [top_segment]
    + ([addCat] if outputAddCat else [])  # Optional additional category
    + [
        unique_spread_id,
        data_points,
        *percentile_values,      # 8 values: p50, p75, p90, p95, p96, p97, p98, p99
        *stresses,               # 7 values: stress impacts
        *coverage_list,          # 7 values: coverage rates
        *exception_list,         # 7 values: exception rates
        x_crisis_08,             # 2008 crisis mean
        x_crisis_09,             # 2009 crisis mean
        percentile_rank_08,      # Historical percentile rank 2008
        percentile_rank_09,      # Historical percentile rank 2009
        percentile_08,           # Relative percentile 2008
        percentile_09,           # Relative percentile 2009
        mae_2008,                # Forecast error 2008
        mse_2008,                # Forecast error 2008
        mae_2009,                # Forecast error 2009
        mse_2009,                # Forecast error 2009
    ]
)
```

**Result**: List of lists, each row containing ~40 values

---

### 3. Format Full Results DataFrame (Lines 987-1023)

**Purpose**: Convert collected data into a structured DataFrame and export

#### 3.1 Create Column Names (Lines 987-997)
```python
# Clean percentile strings: 50.00 → "50", 96.00 → "96", 97.50 → "97.5"
percentiles_str = [f"{p:.2f}".rstrip("0").rstrip(".") for p in percentiles_for_file]
# Result: ["50", "75", "90", "95", "96", "97", "98", "99"]

stress_impact_columns = ["Stress Impact - " + ps + "th Perc" for ps in percentiles_str[1:]]
# Result: ["Stress Impact - 75th Perc", "Stress Impact - 90th Perc", ...]

coverage_columns = [f"Coverage - {ps}th Perc" for ps in stress_percentiles_str]
exception_columns = [f"Exception - {ps}th Perc" for ps in stress_percentiles_str]

crisis_columns = [
    "Historical 2008", "Historical 2009",
    "Historical Percentile 2008", "Historical Percentile 2009",
    "Relative Percentile 2008", "Relative Percentile 2009"
]

error_columns = [
    "MAE - financial crisis08", "MSE - financial crisis08",
    "MAE - financial crisis09", "MSE - financial crisis09"
]
```

#### 3.2 Create Full Results DataFrame (Lines 999-1023)
```python
columns = (
    ["TOPS"]
    + ([additionalCategoryColumnName] if outputAddCat else [])
    + [
        'Unique Spread_IDs',
        "Data Points",
        *["50th Perc", "75th Perc", "90th Perc", ...],  # Percentile values
        *stress_impact_columns,                          # Stress impacts
        *coverage_columns,                               # Coverage rates
        *exception_columns,                              # Exception rates
        *crisis_columns,                                 # Crisis validation
        *error_columns,                                  # Forecast errors
    ]
)

# Create DataFrame
result_df = pd.DataFrame(result_data_full, columns=columns)

# Export to Excel
result_df.to_excel(
    full_result_file_additional_category_path if outputAddCat
    else full_result_file_path
)
```

**Output**: Excel file with wide format
```
| TOPS      | Unique IDs | Data Points | 50th Perc | 96th Perc | Stress Impact - 96th | Coverage - 96th | ... |
|-----------|------------|-------------|-----------|-----------|---------------------|-----------------|-----|
| Chemicals | 150        | 1200        | 0.02      | 0.18      | 0.16                | 0.94            | ... |
| Energy    | 95         | 800         | 0.03      | 0.22      | 0.19                | 0.95            | ... |
```

---

### 4. Transform to Long Format (Lines 1025-1079)

**Purpose**: Reshape data from wide to long format for stress testing models

#### 4.1 Initial Melting (Lines 1025-1047)
```python
segmentColumn = "Country" if segmentByCountry else "Sub-sector"

# Melt stress impacts
result_st_df = pd.melt(
    result_df,
    id_vars=["TOPS"] + ([additionalCategoryColumnName] if outputAddCat else []),
    value_vars=stress_impact_columns  # ["Stress Impact - 75th Perc", ...]
)

# Melt coverage rates
coverage_df = pd.melt(
    result_df,
    id_vars=["TOPS"] + ([additionalCategoryColumnName] if outputAddCat else []),
    value_vars=coverage_columns
)

# Melt exception rates
exception_df = pd.melt(
    result_df,
    id_vars=["TOPS"] + ([additionalCategoryColumnName] if outputAddCat else []),
    value_vars=exception_columns
)
```

**Transformation Example**:
```
BEFORE (Wide):
| TOPS      | Stress Impact - 96th | Stress Impact - 99th | Coverage - 96th | Coverage - 99th |
|-----------|---------------------|---------------------|-----------------|-----------------|
| Chemicals | 0.16                | 0.25                | 0.94            | 0.98            |

AFTER (Long):
| TOPS      | variable                | value |
|-----------|------------------------|-------|
| Chemicals | Stress Impact - 96th   | 0.16  |
| Chemicals | Stress Impact - 99th   | 0.25  |
```

#### 4.2 Extract Percentile Keys (Lines 1049-1058)
```python
def extract_perc_key(col):
    return col.split("-")[-1].strip()
    # "Stress Impact - 96th Perc" → "96th Perc"

for df in (result_st_df, coverage_df, exception_df):
    df["variable"] = df["variable"].apply(normalize_var)
    df["perc_key"] = df["variable"].apply(extract_perc_key)
```

**Purpose**: Create a common key for merging the three melted dataframes

#### 4.3 Merge All Metrics (Lines 1060-1068)
```python
coverage_df = coverage_df.rename(columns={"value": "coverage"})
exception_df = exception_df.rename(columns={"value": "exception_rate"})

result_st_df = (
    result_st_df
    .merge(coverage_df.drop(columns=["variable"]), on=id_vars + ["perc_key"])
    .merge(exception_df.drop(columns=["variable"]), on=id_vars + ["perc_key"])
)
```

**Result**:
```
| TOPS      | variable              | value | perc_key  | coverage | exception_rate |
|-----------|-----------------------|-------|-----------|----------|----------------|
| Chemicals | Stress Impact - 96th  | 0.16  | 96th Perc | 0.94     | 0.06           |
| Chemicals | Stress Impact - 99th  | 0.25  | 99th Perc | 0.98     | 0.02           |
```

#### 4.4 Validation Checks (Lines 1070-1073)
```python
# Assert: All perc_keys exist (no missing values)
assert result_st_df["perc_key"].notna().all()

# Assert: Each segment has all expected percentiles
assert (
    result_st_df.groupby(id_vars)["perc_key"].nunique() == len(stress_impact_columns)
).all()
```

#### 4.5 Add Crisis & Error Metrics (Lines 1075-1079)
```python
# Add crisis data
crisis_df = result_df[[
    "TOPS", "Historical 2008", "Historical Percentile 2008",
    "Historical 2009", "Historical Percentile 2009",
    "Relative Percentile 2008", "Relative Percentile 2009"
]]
result_st_df = result_st_df.merge(crisis_df, on="TOPS", how="left")

# Add error metrics
error_df = result_df[[
    "TOPS", "MAE - financial crisis08", "MSE - financial crisis08",
    "MAE - financial crisis09", "MSE - financial crisis09"
]]
result_st_df = result_st_df.merge(error_df, on="TOPS", how="left")
```

---

### 5. Final Formatting & Metadata (Lines 1081-1161)

#### 5.1 Rename Columns (Lines 1081-1087)
```python
result_st_df = result_st_df.rename(
    columns={
        "TOPS": segmentColumn,  # "TOPS" → "Sub-sector" or "Country"
        "variable": "Stress Impact - percentile",
        "value": "Stress Impact",
    }
)
```

#### 5.2 Sort Data (Lines 1089-1102)
```python
# Extract numeric percentile for sorting
result_st_df["Percentile"] = result_st_df["Stress Impact - percentile"].apply(
    lambda x: x.split("-")[1].strip().split(" ")[0] if "Stress" in x else "-"
)
result_st_df["Percentile"] = result_st_df["Percentile"].str[:-2]
# "Stress Impact - 96th Perc" → "96"

# Sort by segment and percentile
if outputAddCat:
    result_st_df = result_st_df.sort_values(
        by=[segmentColumn, additionalCategoryColumnName, "Percentile"],
        ascending=[False, True, True]
    )
else:
    result_st_df = result_st_df.sort_values(
        by=[segmentColumn, "Percentile"],
        ascending=[False, True]
    )
```

#### 5.3 Calculate Scenario Severity (Lines 1104-1125)
```python
lenDF = len(result_st_df)
pctiles_for_1_in_x = percentiles_for_file[1:]  # [75, 90, 95, 96, 97, 98, 99]
lenPercTile = len(pctiles_for_1_in_x)  # 7

# Calculate how many times to repeat severity values
if not outputAddCat:
    nRepeat_for_subsegment = lenDF // lenPercTile  # e.g., 28 rows / 7 = 4 segments
    nRepeat_for_additionalCat = 1
else:
    nAdditionalCategories = len(additionalCategories)  # e.g., 2 (Producer, Others)
    nRepeat_for_subsegment = lenDF // lenPercTile // nAdditionalCategories
    nRepeat_for_additionalCat = nAdditionalCategories

# Convert percentile to "1 in X year" severity
severity_1_in_x = [
    round(100.0 / (100.0 - p), 1)  # 96% → 1/(1-0.96) = 1/0.04 = 25
    for _ in range(nRepeat_for_additionalCat)
    for p in pctiles_for_1_in_x
] * nRepeat_for_subsegment

# Examples:
# 75th percentile → 1/(1-0.75) = 4.0 → "1 in 4 year event"
# 90th percentile → 1/(1-0.90) = 10.0 → "1 in 10 year event"
# 96th percentile → 1/(1-0.96) = 25.0 → "1 in 25 year event"
# 99th percentile → 1/(1-0.99) = 100.0 → "1 in 100 year event"
```

#### 5.4 Add Standard Columns (Lines 1127-1136)
```python
result_st_df["Driver"] = "OPEX"
result_st_df["Scenario Severity (1 in x)"] = severity_1_in_x
result_st_df["As of Date"] = datetime.now().strftime("%Y-%m-%d")
result_st_df["Sector"] = sector

# Add placeholder columns
if segmentByCountry:
    result_st_df["Sub-sector"] = "-"
else:
    result_st_df["Country"] = "-"
```

#### 5.5 Reorder Columns (Lines 1137-1150)
```python
new_column_order = (
    [
        "Driver",                          # "OPEX"
        "Stress Impact - percentile",      # "Stress Impact - 96th Perc"
        "Scenario Severity (1 in x)",      # 25.0
        "Sector",                           # "Commodity Traders"
        "Sub-sector",                       # "Chemicals" or "-"
    ]
    + ([additionalCategoryColumnName] if outputAddCat else [])
    + [
        "Country",                          # "-" or country name
        "Stress Impact",                    # 0.16
        "As of Date",                       # "2026-02-27"
        "coverage",                         # 0.94
        "exception_rate",                   # 0.06
        "Historical 2008",                  # 0.15
        "Historical Percentile 2008",       # 0.96
        "Historical 2009",                  # 0.17
        "Historical Percentile 2009",       # 0.97
        "Relative Percentile 2008",         # 96.2
        "Relative Percentile 2009",         # 97.1
        "MAE - financial crisis08",         # 0.02
        "MSE - financial crisis08",         # 0.0005
        "MAE - financial crisis09",         # 0.01
        "MSE - financial crisis09",         # 0.0002
    ]
)

result_st_df = result_st_df[new_column_order]
```

#### 5.6 Final Sort and Column Rename (Lines 1151-1161)
```python
# Final sort by segment and severity
result_st_df = result_st_df.sort_values(
    by=[segmentColumn, "Scenario Severity (1 in x)"],
    ascending=[False, True]
)
result_st_df = result_st_df.reset_index(drop=True)

# Handle column rename if needed
if outputAddCat:
    if additionalCategoryColumnNameToOutputFile != additionalCategoryColumnName:
        result_st_df[additionalCategoryColumnNameToOutputFile] = result_st_df[
            additionalCategoryColumnName
        ]
        result_st_df = result_st_df.drop(additionalCategoryColumnName, axis=1)
```

---

## Final Output Format

### result_df (Full Results - Wide Format)
```
| TOPS      | Unique IDs | 50th Perc | 96th Perc | Stress Impact - 96th | Coverage - 96th | Historical 2008 | MAE - 08 |
|-----------|------------|-----------|-----------|---------------------|-----------------|-----------------|----------|
| Chemicals | 150        | 0.02      | 0.18      | 0.16                | 0.94            | 0.15            | 0.02     |
| Energy    | 95         | 0.03      | 0.22      | 0.19                | 0.95            | 0.18            | 0.03     |
```

### result_st_df (Stress Impacts - Long Format)
```
| Driver | Sector    | Sub-sector | Scenario Severity | Stress Impact | Coverage | Historical 2008 |
|--------|-----------|------------|-------------------|---------------|----------|-----------------|
| OPEX   | Comm Trd  | Chemicals  | 25.0              | 0.16          | 0.94     | 0.15            |
| OPEX   | Comm Trd  | Chemicals  | 100.0             | 0.25          | 0.98     | 0.15            |
| OPEX   | Comm Trd  | Energy     | 25.0              | 0.19          | 0.95     | 0.18            |
| OPEX   | Comm Trd  | Energy     | 100.0             | 0.30          | 0.98     | 0.18            |
```

---

## Key Metrics Calculated

### Per Segment Statistics
- **Sample size**: Unique spread_ids and total data points
- **Percentiles**: 50th (base), 75th, 90th, 95th, 96th, 97th, 98th, 99th
- **Stress impacts**: Difference from base (e.g., 96th - 50th)

### Historical Validation
- **Crisis values**: Mean delta OPEX/Rev for 2008 and 2009
- **Historical percentile rank**: Where crisis falls in full distribution
- **Relative percentile**: Crisis value mapped to model percentiles
- **Return period**: "1 in X year" event estimation

### Forecast Validation
- **MAE/MSE**: Forecast error for 2008 and 2009 vs. 96th percentile
- **Coverage**: % of actuals below each stress threshold
- **Exception rate**: % of actuals exceeding each stress threshold

### Output Metadata
- **Driver**: "OPEX" (vs. other drivers like Revenue, CAPEX)
- **Scenario Severity**: "1 in X year" interpretation
- **As of Date**: Model run date
- **Sector/Sub-sector/Country**: Hierarchical segmentation

---

## Use Cases

1. **Stress Testing**: Feed result_st_df into bank-wide stress testing models
2. **Model Validation**: Review crisis metrics (MAE, percentile ranks)
3. **Risk Management**: Understand "1 in 25 year" OPEX shock scenarios
4. **Segment Analysis**: Compare stress impacts across sub-sectors
5. **Regulatory Reporting**: Document model performance and coverage

---

## Critical Dependencies

This section requires:
- `Opex_clean_rel_exclude`: Cleaned, dampened data with delta calculations
- `top_segments`: List of segments to analyze
- `percentiles_for_file`: List of percentiles to calculate (e.g., [50, 75, 90, 95, 96, 97, 98, 99])
- Configuration flags: `outputAddCat`, `segmentByCountry`, etc.

---

## Known Issues (from Bug Report)

1. **Bug #9**: Crisis percentile rank includes crisis year (circular logic)
2. **Bug #10**: MAE/MSE calculation has wrong variable check
3. **Bug #14**: Coverage calculation includes NaN values
4. **Bug #19**: normalize_var function doesn't execute its logic
5. **Bug #21**: No empty subset validation before quantile calculations

See `bug_analysis_report.md` for full details and fixes.
