# Bug Report: capex.py

**File**: `C:\repo\mst\capex.py`
**Date**: 2026-03-05
**Status**: Reviewed - Awaiting Fixes

---

## Executive Summary

Comprehensive review of `capex.py` identified **10 issues** including 2 critical bugs that will cause immediate crashes, 3 high-priority issues affecting data quality and maintainability, and 5 medium-to-low priority code quality improvements.

**Immediate Action Required**: Fix critical bugs #1 and #2 before running code.

---

## Critical Bugs (MUST FIX)

### Bug #1: Undefined Variable in outputChart()
**Severity**: 🔴 CRITICAL
**Location**: Line 130
**Type**: NameError

**Current Code**:
```python
def outputChart(..., pdfPagesObject=None, ...):
    # ... code ...
    if pdfPagesObject:
        pdf.savefig()  # ❌ 'pdf' is not defined
```

**Issue**: Variable `pdf` does not exist in function scope. Should be `pdfPagesObject`.

**Impact**: Code crashes with `NameError: name 'pdf' is not defined` whenever `outputChart()` is called with a PDF object.

**Fix**:
```python
if pdfPagesObject:
    pdfPagesObject.savefig()  # ✓ Use parameter name
```

---

### Bug #2: Missing Import Statement
**Severity**: 🔴 CRITICAL
**Location**: Line 547
**Type**: NameError

**Current Code**:
```python
# Imports section (lines 1-12) - missing 'import os'

# ... later in code ...
os.makedirs(os.path.dirname(stress_result_file_path), exist_ok=True)  # ❌
```

**Issue**: Module `os` is never imported but used on line 547.

**Impact**: Code crashes with `NameError: name 'os' is not defined` when creating output directories.

**Fix**: Add to imports section:
```python
import os
```

---

## High Priority Issues

### Issue #3: Incomplete Infinity/NaN Handling
**Severity**: 🟠 HIGH
**Location**: Line 364
**Type**: Data Validation Bug

**Current Code**:
```python
CAPEX_clean = CAPEX_end[~CAPEX_end["CAPEX/Revenue"].isin([float("inf")])]
```

**Issue**: Only filters positive infinity `inf`. Does NOT filter:
- Negative infinity: `-inf` (can occur from negative CAPEX)
- NaN values (`.isin([float("inf")])` does not catch NaN)

**Impact**: Invalid data (NaN, -inf) passes through to analysis, corrupting results.

**Fix** (Option 1 - Recommended):
```python
CAPEX_clean = CAPEX_end[np.isfinite(CAPEX_end["CAPEX/Revenue"])]
```

**Fix** (Option 2 - Explicit):
```python
CAPEX_clean = CAPEX_end[
    ~(CAPEX_end["CAPEX/Revenue"].isin([float("inf"), float("-inf")]) |
      CAPEX_end["CAPEX/Revenue"].isna())
]
```

---

### Issue #4: Duplicated Metrics Calculation Code
**Severity**: 🟠 HIGH
**Location**: Lines 449-475 vs Lines 554-580
**Type**: Code Duplication

**Current Code**: Two nearly identical blocks calculating metrics:

**Block 1 (lines 449-475)**:
```python
result_data_full = []
for top_segment in top_segments:
    subset = CAPEX_clean[CAPEX_clean["TOPS"] == top_segment]
    unique_leids = subset[id_column_name].nunique()
    percentile_values = (
        subset["CAPEX/Revenue"]
        .quantile([p / 100 for p in percentiles_for_file])
        .values
    )
    stresses = np.array(percentile_values[1:]) - percentile_values[0]
    result_data_full.append([
        top_segment, unique_leids,
        *percentile_values, *stresses,
    ])
```

**Block 2 (lines 554-580)**: Nearly identical, only adds `data_points = len(subset)`

**Issue**:
- ~30 lines of duplicated logic
- Changes must be made in two places (maintenance burden)
- Both blocks also duplicate percentile string formatting (lines 479 and 584)

**Impact**: High maintenance cost, increased risk of bugs when updating one block but forgetting the other.

**Fix**: Extract into helper function:
```python
def calculate_segment_metrics(data, top_segments, id_column_name,
                              percentiles, include_data_points=False):
    """
    Calculate percentile metrics for each segment.

    Parameters
    ----------
    data : pd.DataFrame
        Cleaned CAPEX data with 'TOPS' column
    top_segments : list
        List of segment names to process
    id_column_name : str
        Column name for unique identifiers (e.g., 'spread_id', 'leid')
    percentiles : list
        List of percentile values (e.g., [50, 60, 75, 90, 97.5])
    include_data_points : bool, optional
        Whether to include total datapoint count (default: False)

    Returns
    -------
    list of list
        Each inner list contains: [segment, unique_ids, (data_points,)
        percentiles..., stresses...]
    """
    result_data = []
    for top_segment in top_segments:
        subset = data[data["TOPS"] == top_segment]
        unique_leids = subset[id_column_name].nunique()

        percentile_values = (
            subset["CAPEX/Revenue"]
            .quantile([p / 100 for p in percentiles])
            .values
        )
        stresses = np.array(percentile_values[1:]) - percentile_values[0]

        row = [top_segment, unique_leids]
        if include_data_points:
            row.append(len(subset))
        row.extend(percentile_values)
        row.extend(stresses)

        result_data.append(row)

    return result_data

# Usage:
result_data_full = calculate_segment_metrics(
    CAPEX_clean, top_segments, id_column_name,
    percentiles_for_file, include_data_points=False
)

result_data_full_summary = calculate_segment_metrics(
    CAPEX_clean, top_segments, id_column_name,
    percentiles_for_file, include_data_points=True
)
```

---

### Issue #5: Hard-Coded Magic Number
**Severity**: 🟠 HIGH
**Location**: Line 414
**Type**: Code Quality / Magic Number

**Current Code**:
```python
CAPEX_clean.loc[
    CAPEX_clean[["DATE_OF_FINANCIALS", id_column_name]]
    .apply(tuple, axis=1)
    .isin(exclude_set),
    "CAPEX/Revenue",
] *= 0.0001  # ❌ Magic number
```

**Issue**: Dampening factor `0.0001` is hard-coded without explanation.

**Reference**: Per `MEMORY.md`, this pattern was fixed in `opex.py`:
> "Constants: All magic numbers extracted to constants section"
> "Format: `DAMPENER_PERCENTILE_OUTLIER = 0.0001`"

**Impact**: Unclear why this specific value is used; hard to change globally if needed.

**Fix**: Add to constants section at top of file:
```python
# --- Constants ---
DAMPENER_PERCENTILE_OUTLIER = 0.0001  # Factor to dampen outlier datapoints
```

Then use:
```python
] *= DAMPENER_PERCENTILE_OUTLIER
```

---

## Medium Priority Issues

### Issue #6: Non-Standard Variable Name "TOPS"
**Severity**: 🟡 MEDIUM
**Location**: Lines 431, 440, 450, 481, 508, 555, 604
**Type**: Naming Convention Violation

**Current Code**:
```python
CAPEX_clean["TOPS"] = np.where(
    CAPEX_clean[sub_segment_column_name].isin(top_segments),
    CAPEX_clean[sub_segment_column_name],
    "Others",
)
```

**Issue**: Column named `"TOPS"` is cryptic and sector-specific.

**Reference**: Per `MEMORY.md` naming conventions:
> "Segments: `segment_group` (not `TOPS`)"

**Impact**: Reduces code readability; inconsistent with project standards.

**Fix**: Rename all occurrences:
```python
CAPEX_clean["segment_group"] = np.where(...)
dampened_segments = CAPEX_clean.loc[dampening_mask, "segment_group"]
subset = CAPEX_clean[CAPEX_clean["segment_group"] == top_segment]
```

**Affected Lines**: 431, 440, 450, 481, 508, 555, 604

---

### Issue #7: Misleading Variable Names in Sector Mapping
**Severity**: 🟡 MEDIUM
**Location**: Lines 208-217
**Type**: Copy-Paste Error / Misleading Names

**Current Code**:
```python
if groupSector:
    # Build reverse mapping: each country -> group label  ❌ Wrong comment
    reverse_country_map = {}  # ❌ Maps sectors, not countries
    for group_label, countries in country_group_mapping.items():
        for country in countries:  # ❌ Should be 'sector' not 'country'
            reverse_country_map[country] = group_label

    # Apply mapping to financials['country_of_risk']  ❌ Wrong comment
    financials["sub_segment_group"] = financials["sub_segment"].apply(
        lambda x: reverse_country_map.get(x, x)
    )
```

**Issue**:
- Variable `reverse_country_map` maps sectors, not countries
- Comments refer to "country" when code operates on "sub_segment"
- Clear copy-paste from `groupCountry` block above (lines 195-205)

**Impact**: Confusing for maintainers; misleading variable/comment naming.

**Fix**:
```python
if groupSector:
    # Build reverse mapping: each sector -> group label
    reverse_sector_map = {}
    for group_label, sectors in country_group_mapping.items():
        for sector in sectors:
            reverse_sector_map[sector] = group_label

    # Apply mapping to financials['sub_segment']
    financials["sub_segment_group"] = financials["sub_segment"].apply(
        lambda x: reverse_sector_map.get(x, x)
    )
```

---

### Issue #8: Type Conversion Lacks Error Handling
**Severity**: 🟡 MEDIUM
**Location**: Lines 311-314
**Type**: Data Validation

**Current Code**:
```python
financials["SLS_REVENUES"] = financials["SLS_REVENUES"].astype(float)
# this is needed due to a row with a string "0.0"  ❌ Known data quality issue
financials["CAPEX"] = financials["CAPEX"].astype(float)
```

**Issue**:
- Comment acknowledges data quality problems (string `"0.0"`)
- No validation that conversion succeeded
- No logging of failed conversions
- `.astype(float)` will raise error or produce NaN for invalid strings

**Impact**: Silent data corruption if conversion fails; no visibility into data quality issues.

**Fix**:
```python
# Convert with error handling
num_revenue_na_before = financials["SLS_REVENUES"].isna().sum()
financials["SLS_REVENUES"] = pd.to_numeric(
    financials["SLS_REVENUES"], errors='coerce'
)
num_revenue_na_after = financials["SLS_REVENUES"].isna().sum()

if num_revenue_na_after > num_revenue_na_before:
    num_failed = num_revenue_na_after - num_revenue_na_before
    print(f"Warning: {num_failed} SLS_REVENUES values could not be converted to float")

# Same for CAPEX
num_capex_na_before = financials["CAPEX"].isna().sum()
financials["CAPEX"] = pd.to_numeric(financials["CAPEX"], errors='coerce')
num_capex_na_after = financials["CAPEX"].isna().sum()

if num_capex_na_after > num_capex_na_before:
    num_failed = num_capex_na_after - num_capex_na_before
    print(f"Warning: {num_failed} CAPEX values could not be converted to float")
```

---

## Low Priority Issues (Code Quality)

### Issue #9: Missing Function Docstring
**Severity**: 🟢 LOW
**Location**: Lines 68-132
**Type**: Documentation

**Current Code**:
```python
def outputChart(
    data,
    chartTitle,
    bin_edges=np.arange(-2, 2.2, 0.05),
    plotSeaboneHistplot=False,
    pdfPagesObject=None,
    figsize=(10, 6),
    xrange=(-2, 2),
):
    # No docstring ❌
    plt.figure(figsize=figsize)
    # ...
```

**Issue**: Function lacks docstring explaining parameters, purpose, and behavior.

**Reference**: Per `MEMORY.md`:
> "Helper Functions: Include NumPy-style docstrings with Parameters, Returns, Examples"

**Impact**: Reduces code maintainability and understandability.

**Fix**: Add NumPy-style docstring:
```python
def outputChart(
    data,
    chartTitle,
    bin_edges=np.arange(-2, 2.2, 0.05),
    plotSeaboneHistplot=False,
    pdfPagesObject=None,
    figsize=(10, 6),
    xrange=(-2, 2),
):
    """
    Generate histogram chart of CAPEX/Revenue distribution with percentile markers.

    Parameters
    ----------
    data : pd.Series
        Data values to plot (CAPEX/Revenue ratios)
    chartTitle : str
        Title for the chart
    bin_edges : array-like, optional
        Histogram bin edges (default: np.arange(-2, 2.2, 0.05))
    plotSeaboneHistplot : bool, optional
        Whether to overlay seaborn histogram (default: False)
    pdfPagesObject : PdfPages, optional
        PDF object to save figure to. If None, figure is not saved (default: None)
    figsize : tuple, optional
        Figure size (width, height) in inches (default: (10, 6))
    xrange : tuple or None, optional
        X-axis range limits (min, max). If None, auto-scale (default: (-2, 2))

    Returns
    -------
    None
        Saves figure to pdfPagesObject if provided, then closes the figure

    Examples
    --------
    >>> with PdfPages('output.pdf') as pdf:
    ...     outputChart(data['CAPEX/Revenue'], 'Distribution', pdfPagesObject=pdf)
    """
```

---

### Issue #10: Commented-Out Debug Code
**Severity**: 🟢 LOW
**Location**: Lines 191, 272, 373, 626
**Type**: Code Clutter

**Current Code**:
```python
Line 191: # financials.to_excel(fr'{DATA_DIR}/03. Model/{sector_name}/04. Capex/{sector_short}_financials.xlsx')
Line 272: # financials.to_excel(fr'{DATA_DIR}/03. Model/{sector_name}/04. Capex/Capex_{sector_short}_Financials.xlsx')
Line 373: # CAPEX_clean.to_excel(fr"{DATA_DIR}/03. Model/{sector_name}/04. Capex/CAPEX_{sector_short}_Modelling_data.xlsx")
Line 626: # summary_df.to_excel("spread_summary_by_region.xlsx", index=False)
```

**Issue**: Old debugging/output statements left commented out.

**Reference**: Per `MEMORY.md`:
> "File Organization: Remove commented code (keep history in git)"

**Impact**: Code clutter; adds noise without value.

**Fix**: Delete these lines. Use version control (git) for history if needed.

---

## Summary Statistics

| Severity | Count | Issues |
|----------|-------|--------|
| 🔴 Critical | 2 | #1 (undefined variable), #2 (missing import) |
| 🟠 High | 3 | #3 (inf/NaN handling), #4 (code duplication), #5 (magic number) |
| 🟡 Medium | 3 | #6 (naming: TOPS), #7 (misleading names), #8 (type conversion) |
| 🟢 Low | 2 | #9 (missing docstring), #10 (commented code) |
| **Total** | **10** | |

---

## Comparison to opex.py

**Better than opex.py**:
- ✅ No `globals()` abuse
- ✅ No hardcoded sector names in data structures
- ✅ No variable typo bugs like `tail_prob_08` vs `tail_prob_09`

**Needs improvement (matching opex.py standards)**:
- ❌ Missing import statement (critical)
- ❌ Undefined variables (critical)
- ❌ Magic numbers not extracted to constants
- ❌ Significant code duplication (30+ lines)
- ❌ Non-standard naming conventions (`TOPS` vs `segment_group`)
- ❌ Incomplete documentation

---

## Recommended Fix Priority

1. **Immediate** (before next run):
   - Fix Bug #1: Change `pdf.savefig()` to `pdfPagesObject.savefig()`
   - Fix Bug #2: Add `import os` to imports

2. **Next Sprint**:
   - Issue #3: Fix inf/NaN handling with `np.isfinite()`
   - Issue #4: Extract duplicated code into helper function
   - Issue #5: Extract magic number to constant

3. **Technical Debt**:
   - Issues #6-10: Naming conventions, documentation, cleanup

---

## Testing Recommendations

After fixes, test with all sectors (per `MEMORY.md` testing requirements):
- O&G
- Commodity Traders
- Metals & Mining
- Automobiles & Components
- Consumer Durables & Apparel
- Technology Hardware & Equipment
- Building Products, Construction & Engineering
- CRE
- Other Capital Goods
- Transportation and Storage
- Global

Compare outputs before/after to ensure no regression.
