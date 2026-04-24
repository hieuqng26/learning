"""
Example usage of ORELab Excel-to-ORE converter.

This script demonstrates how to:
1. Convert Excel trade data to ORE XML format
2. Run ORE analytics on the generated portfolio
3. Read and display results
"""

import pandas as pd
from project.orelab import ORERunner
from ORE import *


def test_ore_runner():
    """
    Complete workflow using ORERunner.

    ORERunner handles:
    - Excel to XML conversion
    - ORE execution
    - Result parsing and storage
    - Automatic cleanup
    """
    print("\n" + "=" * 70)
    print("Test: Complete Workflow with ORERunner")
    print("=" * 70)

    excel_file = "project/data/ORE/templates/sample_trades.xlsx"

    inputs = {'trades': {}, 'netting_sets': None}
    all_sheets = pd.read_excel(excel_file, sheet_name=None)
    for sheet_name, df in all_sheets.items():
        if 'TradeType' in df.columns:
            inputs['trades'][df['TradeType'].iloc[0]] = df
        elif sheet_name == 'NettingSets':
            inputs['netting_sets'] = df

    try:
        # ORERunner handles the complete workflow
        with ORERunner(inputs, asof_date='2016-02-05', cleanup=True) as runner:
            # Execute: Convert → Run ORE → Parse results
            runner.run()

            # Access NPV results
            print("\n" + "=" * 70)
            print("NPV Results")
            print("=" * 70)
            npv_df = runner.get_npv()
            print(npv_df)

            # Access XVA results
            try:
                print("\n" + "=" * 70)
                print("XVA Results")
                print("=" * 70)
                xva_df = runner.get_xva()
                print(xva_df)
            except FileNotFoundError:
                print("\nXVA results not available (requires XVA analytics enabled)")

            # Access exposure profiles
            try:
                print("\n" + "=" * 70)
                print("Exposure Profiles")
                print("=" * 70)
                exposure_df = runner.get_exposures(exposure_type='trade')
                print(exposure_df)
            except FileNotFoundError:
                print("\nExposure data not available (requires simulation)")

        # Temp folders cleaned up automatically after exiting context
        print("\n✓ Temporary folders cleaned up automatically")

    except ImportError:
        print("\nX  ORE Python module not available.")
        print("Install ORE Python bindings to run this example.")
    except FileNotFoundError as e:
        print(f"\nX  File not found: {e}")


def test_ore_basic():
    import os

    os.chdir('project/data/ORE')

    params_xva = Parameters()
    params_xva.fromFile("Input/ore.xml")
    ore_xva = OREApp(params_xva, True)
    ore_xva.run()


def test_ore_plot():
    import os
    import sys
    sys.path.append('../')
    from ore_examples_helper import OreExample

    oreex = OreExample(sys.argv[1] if len(sys.argv) > 1 else False)
    os.chdir('project/data/ORE')

    # npv = open("npv.csv")
    # call = []
    # put = []
    # for line in npv.readlines():
    #     line_list = line.split(',')
    #     call = ([[0.0, float(line_list[6])], [float(line_list[3]), float(line_list[6])]])

    oreex.setup_plot("exposure_fxoption")
    oreex.plot("temp_20251121_184008/exposure_trade_dummy.csv", 2, 3, 'b', "EPE")
    oreex.plot("temp_20251121_184008/exposure_trade_dummy.csv", 2, 3, 'r', "ENE")
    # oreex.plot_line([0, call[1][0]], [call[0][1], call[1][1]], color='g', label="Call Price")
    # oreex.plot_line([0, put[1][0]], [put[0][1], put[1][1]], color='m', label="Put Price")
    oreex.decorate_plot(title="FX Option")
    oreex.save_plot_to_file()


if __name__ == "__main__":
    # test_ore_basic()
    test_ore_plot()
    # test_ore_runner()
