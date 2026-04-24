"""
Example script demonstrating sensitivity analysis with ORE trades.

This script shows how to:
1. Create an FX Forward trade
2. Configure sensitivity analysis
3. Run pricing with sensitivity
4. Access sensitivity results
5. (Optional) Keep temporary files for inspection
"""

from project.qld.ORETrade.fx.fxforward import FXForward
from project.qld.ORETrade.ir.cross_currency_swap import CrossCurrencySwap
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))


def example_basic_sensitivity():
    """Example 1: Basic sensitivity analysis."""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Basic FX Forward Sensitivity Analysis")
    print("=" * 70)

    # Create FX Forward trade
    trade = FXForward(
        evaluation_date='2016-02-05',
        value_date='2017-02-05',
        bought_currency='EUR',
        bought_amount=1000000,
        sold_currency='USD',
        sold_amount=1100000
    )

    # Configure sensitivity analysis
    sensitivity_config = {
        'discount_curves': [{
            'ccy': 'EUR',
            'shift_type': 'Absolute',
            'shift_size': 0.0001,
            'shift_scheme': 'Forward',
            'shift_tenors': ['1Y', '5Y']
        }],
        'fx_spots': [{
            'ccypair': 'USDEUR',
            'shift_type': 'Relative',
            'shift_size': 0.01,
            'shift_scheme': 'Central'
        }],
        'credit_curves': [{
            'name': 'CPTY_A',
            'currency': 'USD',
            'shift_type': 'Absolute',
            'shift_size': 0.0001,
            'shift_scheme': 'Forward',
            'shift_tenors': ['1Y', '5Y']
        }],
        'compute_gamma': False,
        'use_spreaded_term_structures': False
    }

    # Price with sensitivity
    print("\nPricing trade with sensitivity analysis...")
    trade.price(sensitivity_config=sensitivity_config)

    # Display results
    print("\n" + "-" * 70)
    print("RESULTS:")
    print("-" * 70)
    print(f"NPV: {trade.result['npv']:,.2f}")
    print(f"CVA: {trade.result['cva']:,.2f}")
    print(f"DVA: {trade.result['dva']:,.2f}")

    print("\nExposure Profile:")
    if trade.result['exposures'] is not None and not trade.result['exposures'].empty:
        print(trade.result['exposures'].head())
    else:
        print("  No exposure data")

    print("\nSensitivity Results:")
    if trade.result['sensitivity'] is not None and not trade.result['sensitivity'].empty:
        print(f"  Rows: {len(trade.result['sensitivity'])}")
        print(f"  Columns: {list(trade.result['sensitivity'].columns)}")
        print("\n  Sample data:")
        print(trade.result['sensitivity'].head())
    else:
        print("  No sensitivity data (check if sensitivity.xml was generated)")


def example_comprehensive_sensitivity():
    """Example 3: Comprehensive sensitivity configuration."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Comprehensive Sensitivity Configuration")
    print("=" * 70)

    # trade = FXForward(
    #     evaluation_date='2016-02-05',
    #     value_date='2017-02-05',
    #     bought_currency='EUR',
    #     bought_amount=10000000,  # 10M EUR
    #     sold_currency='USD',
    #     sold_amount=11000000     # 11M USD
    # )

    trade = CrossCurrencySwap(
        evaluation_date='2016-02-05',
        start_date='2019-09-04',
        end_date='2032-09-03',
        # Leg 1 (EUR)
        currency1='EUR',
        notional1=30000000,
        index1='EUR-EURIBOR-6M',
        spread1=0.0,
        tenor1='6M',
        day_counter1='A360',
        # Leg 2 (USD)
        currency2='USD',
        notional2=33900000,
        index2='USD-LIBOR-3M',
        spread2=0.0,
        tenor2='3M',
        day_counter2='A360',
        # Exchange flags
        initial_exchange=True,
        final_exchange=True,
        # Common
        calendar='TARGET',
        payment_convention='ModifiedFollowing'
    )

    # Comprehensive sensitivity config
    sensitivity_config = {
        'discount_curves': [
            {
                'ccy': 'EUR',
                'shift_type': 'Absolute',
                'shift_size': 0.0001,  # 1bp
                'shift_scheme': 'Forward',
                'shift_tenors': ['3M']  # '6M', '1Y', '2Y', '5Y', '10Y', '20Y'
            },
            {
                'ccy': 'USD',
                'shift_type': 'Absolute',
                'shift_size': 0.0001,  # 1bp
                'shift_scheme': 'Forward',
                'shift_tenors': ['3M']  # '6M', '1Y', '2Y', '5Y', '10Y', '20Y'
            }
        ],
        'fx_spots': [
            {
                'ccypair': 'USDEUR',
                'shift_type': 'Relative',
                'shift_size': 0.01,  # 1%
                'shift_scheme': 'Central'
            }
        ],
        'fx_volatilities': [
            {
                'ccypair': 'USDEUR',
                'shift_type': 'Relative',
                'shift_size': 0.01,  # 1%
                'shift_scheme': 'Forward',
                'shift_expiries': ['1Y'],  # '2Y', '5Y'
                'shift_strikes': [0.0]  # ATM
            }
        ],
        'credit_curves': [{
            'name': 'CPTY_A',
            'currency': 'USD',
            'shift_type': 'Absolute',
            'shift_size': 0.0001,
            'shift_scheme': 'Forward',
            'shift_tenors': ['1Y', '5Y']
        }],
        'compute_gamma': False,  # Set to True for second-order sensitivities
        'use_spreaded_term_structures': False
    }

    print("\nPricing with comprehensive sensitivity configuration...")
    print(f"  Discount curves: EUR (7 tenors), USD (7 tenors)")
    print(f"  FX spots: USDEUR")
    print(f"  FX vols: USDEUR (3 expiries)")

    trade.price(sensitivity_config=sensitivity_config, cleanup=True)

    print("\n" + "-" * 70)
    print("RESULTS:")
    print("-" * 70)
    print(f"Base NPV: {trade.result['npv']:,.2f}")

    if trade.result['sensitivity'] is not None and not trade.result['sensitivity'].empty:
        sensitivity_df = trade.result['sensitivity']
        print(f"\nSensitivity Results: {len(sensitivity_df)} risk factors")

        # Show summary by risk factor type
        if 'Factor_1' in sensitivity_df.columns:
            print("\nRisk Factors:")
            for factor in sensitivity_df['Factor_1'].unique()[:10]:  # Show first 10
                factor_data = sensitivity_df[sensitivity_df['Factor_1'] == factor]
                if 'Delta' in factor_data.columns:
                    delta = factor_data['Delta'].iloc[0]
                    print(f"  {factor}: Delta = {delta:,.2f}")
    else:
        print("\nNo sensitivity results")


if __name__ == "__main__":
    # Run examples
    try:
        # example_basic_sensitivity()
        # print("\n" + "=" * 70)
        # input("\nPress Enter to continue to Example 2...")

        # example_keep_temp_files()
        # print("\n" + "=" * 70)
        # input("\nPress Enter to continue to Example 3...")

        example_comprehensive_sensitivity()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
