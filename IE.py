import sys
import warnings

warnings.filterwarnings("ignore")

from log_file import TimestampLog
from IE_config import *

from ie_data_processing import load_and_clean_data
from ie_modelling import run_modelling
from ie_backtesting import run_backtesting
from ie_output import write_outputs

OUT_DIR = r"C:\Users\1643986\repo\50991-risk-portfolio-analytics\output"


# ============================================================================
# MAIN RUNNER
# ============================================================================


def interest_expense_run(sector_name):
    """Run the full interest expense Alpha model for a given sector.

    Orchestrates data loading, modelling, backtesting, and Excel output.
    """
    IE_config = SECTORS[sector_name]
    sector = IE_config.sector
    sector_short = IE_config.sector_short

    consolid_path = windows_long_path(
        f"{OUT_DIR}/{sector}/consolidated_results_{sector_short}.xlsx"
    )

    # --- Data processing ---
    summary_steps, interest_data_df, int_expense_issue, processed_id, processed_agg = (
        load_and_clean_data(IE_config)
    )

    # --- Modelling ---
    modelling_results = run_modelling(processed_id, processed_agg, IE_config)

    # --- Backtesting ---
    backtest_results = run_backtesting(processed_id, processed_agg, modelling_results, IE_config)

    # --- Output ---
    write_outputs(
        consolid_path, modelling_results, backtest_results, interest_data_df, summary_steps, sector, IE_config
    )


if __name__ == "__main__":
    sys.stdout = TimestampLog("IE_master")
    for sector in [
        # "O&G",
        # "Commodity Traders",
        # "Metals & Mining",
        # "Automobiles & Components",
        # "Consumer Durables & Apparel",
        # "Technology Hardware & Equipment",
        # "Building Products, Construction & Engineering",
        # "CRE",
        # "Other Capital Goods",
        # "Transportation and Storage",
        "Global",
    ]:
        interest_expense_run(sector)
