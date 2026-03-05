"""
Run EVT Analysis on Opex Data

This script demonstrates how to integrate EVT modeling and backtesting
into your existing Opex stress testing workflow.

Usage:
------
1. Run your opex.py script to generate the processed data
2. Run this script to perform EVT analysis and backtesting
3. Review the generated Excel files and charts

Or integrate directly into opex.py by calling run_evt_analysis()
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from evt_model import GPDModel, mean_excess_plot
from evt_backtest import EVTBacktester, print_backtest_summary
import os


def run_evt_analysis(
    opex_data: pd.DataFrame,
    sector: str,
    output_dir: str,
    test_crisis_years: list = [2008, 2009],
    training_years: int = 10
):
    """
    Run complete EVT analysis on Opex data

    Parameters:
    -----------
    opex_data : pd.DataFrame
        Processed Opex data with columns:
        - 'TOPS' or 'country/subsector': Sub-sector grouping
        - 'delta_opex/rev': Year-over-year relative change
        - 'Year' or 'DATE_OF_FINANCIALS': Date
        - 'spread_id': Company identifier
    sector : str
        Sector name (for labeling outputs)
    output_dir : str
        Directory to save results
    test_crisis_years : list
        Years to use for backtesting (default [2008, 2009])
    training_years : int
        Years of training data before each crisis year

    Returns:
    --------
    results : dict
        Dictionary containing:
        - 'evt_summary': EVT model parameters by sub-sector
        - 'backtest_results': Backtesting performance
        - 'comparison': EVT vs Empirical method comparison
    """

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Standardize column names
    if 'TOPS' in opex_data.columns:
        group_col = 'TOPS'
    elif 'country/subsector' in opex_data.columns:
        group_col = 'country/subsector'
    else:
        raise ValueError("Cannot find grouping column (TOPS or country/subsector)")

    if 'DATE_OF_FINANCIALS' in opex_data.columns:
        date_col = 'DATE_OF_FINANCIALS'
    elif 'Year' in opex_data.columns:
        date_col = 'Year'
    else:
        raise ValueError("Cannot find date column")

    value_col = 'delta_opex/rev'

    # Filter clean data
    data = opex_data.dropna(subset=[value_col])

    print("\n" + "="*80)
    print(f"EVT ANALYSIS FOR {sector}")
    print("="*80)
    print(f"\nData summary:")
    print(f"  Total observations: {len(data):,}")
    print(f"  Unique companies: {data['spread_id'].nunique():,}")
    print(f"  Sub-sectors: {data[group_col].nunique()}")
    print(f"  Year range: {data['Year'].min()} - {data['Year'].max()}")

    # =========================================================================
    # PART 1: FIT EVT MODELS BY SUB-SECTOR
    # =========================================================================

    print("\n" + "="*80)
    print("PART 1: FITTING EVT MODELS BY SUB-SECTOR")
    print("="*80)

    evt_models = {}
    evt_results = []

    for subsector in sorted(data[group_col].unique()):
        subset = data[data[group_col] == subsector][value_col].values

        if len(subset) < 50:
            print(f"\n⚠️  {subsector}: Insufficient data ({len(subset)} points) - SKIPPED")
            continue

        print(f"\n{subsector}:")
        print(f"  Observations: {len(subset):,}")

        # Fit EVT model
        try:
            evt = GPDModel(subset, threshold_quantile=0.90)
            evt.fit()

            summary = evt.summary()
            summary['Subsector'] = subsector
            evt_results.append(summary)
            evt_models[subsector] = evt

            # Print key results
            print(f"  Shape (ξ): {summary['shape_parameter']:.4f} ({summary['tail_type']})")
            print(f"  Scale (σ): {summary['scale_parameter']:.4f}")
            print(f"  Threshold: {summary['threshold']:.4f}")
            print(f"\n  Percentiles:")
            print(f"    80th: {summary['80th_percentile']:.4f}")
            print(f"    90th: {summary['90th_percentile']:.4f}")
            print(f"    96th: {summary['96th_percentile']:.4f}")
            print(f"    99th: {summary['99th_percentile']:.4f}")
            print(f"\n  Return Levels:")
            print(f"    1-in-10yr:  {summary['1_in_10_year']:.4f}")
            print(f"    1-in-25yr:  {summary['1_in_25_year']:.4f}")
            print(f"    1-in-50yr:  {summary['1_in_50_year']:.4f}")
            print(f"    1-in-100yr: {summary['1_in_100_year']:.4f}")

        except Exception as e:
            print(f"  ❌ Error fitting model: {e}")
            continue

    evt_summary_df = pd.DataFrame(evt_results)

    # =========================================================================
    # PART 2: GENERATE DIAGNOSTIC PLOTS
    # =========================================================================

    print("\n" + "="*80)
    print("PART 2: GENERATING DIAGNOSTIC PLOTS")
    print("="*80)

    plots_dir = os.path.join(output_dir, 'evt_diagnostics')
    os.makedirs(plots_dir, exist_ok=True)

    for subsector, model in evt_models.items():
        try:
            # Diagnostic plots
            fig = model.diagnostic_plots(figsize=(15, 10))
            fig.suptitle(f'{sector} - {subsector}\nEVT Diagnostic Plots',
                        fontsize=14, y=1.00)
            plt.savefig(
                os.path.join(plots_dir, f'{subsector}_diagnostics.png'),
                dpi=150, bbox_inches='tight'
            )
            plt.close()

            # Mean excess plot
            subset = data[data[group_col] == subsector][value_col].values
            fig = mean_excess_plot(subset)
            fig.suptitle(f'{sector} - {subsector}\nMean Excess Plot',
                        fontsize=14)
            plt.savefig(
                os.path.join(plots_dir, f'{subsector}_mean_excess.png'),
                dpi=150, bbox_inches='tight'
            )
            plt.close()

            print(f"  ✓ Generated plots for {subsector}")

        except Exception as e:
            print(f"  ❌ Error generating plots for {subsector}: {e}")

    # =========================================================================
    # PART 3: BACKTEST CRISIS YEARS
    # =========================================================================

    print("\n" + "="*80)
    print("PART 3: BACKTESTING CRISIS YEARS")
    print("="*80)

    backtester = EVTBacktester(
        data=data,
        date_col=date_col,
        value_col=value_col,
        group_col=group_col
    )

    all_backtest_results = []

    for crisis_year in test_crisis_years:
        print(f"\n{'─'*80}")
        print(f"Backtesting {crisis_year} Financial Crisis")
        print(f"{'─'*80}")

        try:
            backtest_results = backtester.backtest_crisis_year(
                crisis_year=crisis_year,
                training_years=training_years,
                test_percentiles=[0.80, 0.90, 0.96, 0.99],
                compute_ci=True
            )

            all_backtest_results.append(backtest_results)

            # Print summary
            print_backtest_summary(backtest_results, percentile='96th')

            # Generate plots
            fig = backtester.plot_backtest_results(
                backtest_results,
                percentile='96th',
                figsize=(14, 8)
            )
            fig.suptitle(
                f'{sector} - {crisis_year} Crisis Backtest\n96th Percentile',
                fontsize=14, y=1.00
            )
            plt.savefig(
                os.path.join(output_dir, f'backtest_{crisis_year}_96th.png'),
                dpi=150, bbox_inches='tight'
            )
            plt.close()

        except Exception as e:
            print(f"  ❌ Error backtesting {crisis_year}: {e}")

    # Combine all backtest results
    if all_backtest_results:
        combined_backtest = pd.concat(all_backtest_results, ignore_index=True)
    else:
        combined_backtest = pd.DataFrame()

    # =========================================================================
    # PART 4: COMPARE EVT VS EMPIRICAL METHOD
    # =========================================================================

    print("\n" + "="*80)
    print("PART 4: METHOD COMPARISON - EVT vs EMPIRICAL PERCENTILES")
    print("="*80)

    comparison_results = []

    for crisis_year in test_crisis_years:
        print(f"\n{'─'*80}")
        print(f"Comparing methods for {crisis_year}")
        print(f"{'─'*80}")

        try:
            comparison = backtester.compare_methods(
                crisis_year=crisis_year,
                training_years=training_years
            )
            comparison_results.append(comparison)

            # Summary statistics
            print(f"\n{crisis_year} Results:")
            print(f"  EVT Mean Absolute Error:       {comparison['EVT_AbsError'].mean():.4f}")
            print(f"  Empirical Mean Absolute Error: {comparison['Empirical_AbsError'].mean():.4f}")
            print(f"  EVT Wins: {comparison['EVT_Better'].sum()} / {len(comparison)} cases")
            print(f"  EVT Win Rate: {comparison['EVT_Better'].mean():.1%}")

        except Exception as e:
            print(f"  ❌ Error comparing methods for {crisis_year}: {e}")

    # Combine comparison results
    if comparison_results:
        combined_comparison = pd.concat(comparison_results, ignore_index=True)
    else:
        combined_comparison = pd.DataFrame()

    # =========================================================================
    # PART 5: SAVE RESULTS TO EXCEL
    # =========================================================================

    print("\n" + "="*80)
    print("PART 5: SAVING RESULTS")
    print("="*80)

    output_file = os.path.join(output_dir, f'{sector}_EVT_Analysis.xlsx')

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Sheet 1: EVT Summary by sub-sector
        evt_summary_df.to_excel(writer, sheet_name='EVT_Summary', index=False)

        # Sheet 2: Backtesting results
        if not combined_backtest.empty:
            combined_backtest.to_excel(writer, sheet_name='Backtest_Results', index=False)

        # Sheet 3: Method comparison
        if not combined_comparison.empty:
            combined_comparison.to_excel(writer, sheet_name='Method_Comparison', index=False)

        # Sheet 4: Summary statistics
        summary_stats = []
        for year in test_crisis_years:
            if not combined_comparison.empty:
                year_data = combined_comparison[combined_comparison['Crisis_Year'] == year]
                if not year_data.empty:
                    summary_stats.append({
                        'Crisis_Year': year,
                        'EVT_MAE_80th': year_data[year_data['Percentile']=='80th']['EVT_AbsError'].mean(),
                        'EVT_MAE_90th': year_data[year_data['Percentile']=='90th']['EVT_AbsError'].mean(),
                        'EVT_MAE_96th': year_data[year_data['Percentile']=='96th']['EVT_AbsError'].mean(),
                        'EVT_MAE_99th': year_data[year_data['Percentile']=='99th']['EVT_AbsError'].mean(),
                        'Empirical_MAE_80th': year_data[year_data['Percentile']=='80th']['Empirical_AbsError'].mean(),
                        'Empirical_MAE_90th': year_data[year_data['Percentile']=='90th']['Empirical_AbsError'].mean(),
                        'Empirical_MAE_96th': year_data[year_data['Percentile']=='96th']['Empirical_AbsError'].mean(),
                        'Empirical_MAE_99th': year_data[year_data['Percentile']=='99th']['Empirical_AbsError'].mean(),
                        'EVT_Win_Rate': year_data['EVT_Better'].mean(),
                    })

        if summary_stats:
            pd.DataFrame(summary_stats).to_excel(writer, sheet_name='Summary_Stats', index=False)

    print(f"\n✓ Results saved to: {output_file}")
    print(f"✓ Diagnostic plots saved to: {plots_dir}")

    print("\n" + "="*80)
    print("EVT ANALYSIS COMPLETE")
    print("="*80)

    return {
        'evt_summary': evt_summary_df,
        'backtest_results': combined_backtest,
        'comparison': combined_comparison,
        'evt_models': evt_models
    }


if __name__ == "__main__":
    """
    Example usage:

    This assumes you've already run opex.py and have the processed data.
    Adjust the file path to match your actual data location.
    """

    # Example: Load processed Opex data
    # This should be the Opex_clean_rel_exclude_add_cat dataframe from opex.py

    print("EVT Analysis Script")
    print("="*80)
    print("\nTo use this script:")
    print("1. Run your opex.py to generate processed data")
    print("2. Load the processed data (Opex_clean_rel_exclude_add_cat)")
    print("3. Call run_evt_analysis() with your data")
    print("\nExample:")
    print("""
    # Load your processed data
    opex_data = pd.read_excel('path/to/your/processed_opex_data.xlsx')

    # Or if integrating directly into opex.py:
    # Use the Opex_clean_rel_exclude_add_cat dataframe

    # Run EVT analysis
    results = run_evt_analysis(
        opex_data=Opex_clean_rel_exclude_add_cat,
        sector='Commodity Traders',
        output_dir=r'C:\\Users\\1665642\\OneDrive - Standard Chartered Bank\\Documents\\test_run\\Commodity Traders',
        test_crisis_years=[2008, 2009],
        training_years=10
    )
    """)
    print("\n" + "="*80)
