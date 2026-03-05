import pandas as pd
import numpy as np
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
import os, re
from dotenv import load_dotenv

load_dotenv()

windows_long_path = lambda p: f"\\\\?\\{os.path.abspath(p)}"

USER_SPECIFIC_PATH = os.getenv("USER_SPECIFIC_PATH", ".")
PROJECT_DIR = (
    Path(USER_SPECIFIC_PATH) / "04. Deloitte Modelling" / "06. Corporates Gen2"
)
DATA_DIR = (
    Path(USER_SPECIFIC_PATH)
    / "03. SCB Documents & Data"
    / "2. Financials & Non-Financials"
    / "Corporate Gen2"
    / "data"
)
isic_data = pd.read_excel(
    windows_long_path(
        Path(USER_SPECIFIC_PATH)
        / "04. Deloitte Modelling"
        / "06. Corporates Gen2"
        / "1) Input"
        / "ISIC retagging_Risk Industry_Dec 2025.xlsx"
    ),
    sheet_name="ISIC Mapping",
).drop_duplicates(subset=["ISIC Code"], keep="first")
OUTPUT_DIR = PROJECT_DIR / "2) Output" / "1) Financials"
OUTPUT_PATH = windows_long_path(OUTPUT_DIR / "Financials_final_output_gen2.xlsx")
#-OUTPUT_PATH2 = windows_long_path(
#-----PROJECT_DIR
#-----/ "1) Input"
#-----/ "3) MST Model"
#-----/ "1) Financials"
#-----/ "Financials_final_output_gen2.csv"
# )
required_columns_fin = list(
    set(
        [
            "spread_id",
            "FIN_STM_TYPE",  # "fin_stm_type",
            "SCORECARD_ID",  # "scorecard_id",
            "standardized_date_of_financials",  # "date_of_financials",
            "SLS_REVENUES",
            "TOTALCOSTOFSALES",
            "Opex",
            "GrossFixedAssets",
            "InterestExpense",
            "LongTermDebt",
            "ShortTermDebt",
            "TotalDebt",
        ]
    )
)


class data_processing:
    # A class to load and preprocess financial and risk data from CSV files
    def __init__(
        self,
        fin_path,
        risk_path,
    ):
        try:
            self.risk = pd.read_csv(risk_path)
            self.financial = pd.read_csv(fin_path)  # .iloc[:1000, :]
            self.financial.spread_id = self.financial.spread_id.astype("str")

            print("Data loaded!")
        except Exception as e:
            print(f"Data loaded error! {str(e)}")

    # Zhaochen: define a safe sum function for the sum:
    def safe_sum(self, row, cols=[]):
        # Normalize the columns in the row to lower case
        normalized_row = {k.lower(): v for k, v in row.items()}
        # Normalize the cols list to lower case
        normalized_cols = [col.lower() for col in cols]
        if any(
            pd.isna(normalized_row[col]) or normalized_row[col] == ""
            for col in normalized_cols
        ):
            return "Missing"

        try:
            return sum(float(normalized_row[col]) for col in normalized_cols)
        except (ValueError, TypeError):
            return "Missing"

    def summarize_step(
        self,
        df,
        end_data,
        step_name,
        id_column_name="spread_id",
    ):
        financials = df.copy()
        summary = []
        summary.append(
            {
                "Step": step_name,
                "Unique spread IDs": financials[id_column_name].nunique(),
                "Total datapoints": financials.shape[0],
                "end_month": end_data,
            }
        )

        return pd.DataFrame(summary)

    # functions to process financials data based on the portfolio type, date and target
    # target: 'SLS_REVENUES', 'TOTALCOSTOFSALES', 'Opex', 'NetFixedAssets', 'InterestExpense', 'LongTermDebt', 'ShortTermDebt'
    def process_fin(
        self,
        fin_date,
        targets=[
            "SLS_REVENUES",
            "TOTALCOSTOFSALES",
            "Opex",
            "GrossFixedAssets",
            "InterestExpense",
            "LongTermDebt",
            "ShortTermDebt",
            "TotalDebt",
        ],
    ):
        financial = self.financial.copy()
        summary_1 = self.summarize_step(
            financial,
            fin_date,
            step_name="Step 1: Initial financial dataset count",
        )
        print("Financial dataset initial shape:", financial.shape[0])
        # Define a dictionary to group related financial columns and sum them into the relevant target variables.
        grouping_dict = {
            "Opex": [
                i.lower()
                for i in [
                    "SLS_AND_MKTG_EXP",
                    "GENL_AND_AMINISTRATVE_EXP",
                    "WAGES_AND_SALARIES_EXP",
                    "EMP_BNF_EXP",
                    "RESTRUCTURING_EXP",
                    "RESTRUCTURING_EXP_NON_CASH",
                    "OTH_OPRT_EXP",
                    "RET_BNF_PRVSN_EXP",
                    "BAD_DEBT_EXP",
                    "SHR_OPT_COSTS",
                    "OTH_TAX_EXP",
                    "PROVISIONS_EXP",
                    "AMRT_CHRG_ON_CAPITALISED_COST",
                ]
            ],
            "GrossFixedAssets": [i.lower() for i in ["GRS_FX_AST"]],
            "InterestExpense": [i.lower() for i in ["INT_EXP_IS"]],
            "LongTermDebt": [
                i.lower()
                for i in [
                    "NON_CUR_LIABILITIES_BANK_LOA",
                    "NON_CUR_LIABILITIES_BONDS",
                    "NON_CUR_LIABILITIES_CNV_DEBT",
                    "NON_CUR_LIABILITIES_SBORD_DE",
                    "NON_CUR_LIABS_RDMB_PRF_SHR_CP",
                    "NON_CUR_LIABILITIES_FIN_LSE",
                    "NON_CUR_LIABILITIES_BANK_5",
                ]
            ],
            "ShortTermDebt": [
                i.lower()
                for i in [
                    "CUR_PORTN_OF_BANK_LOANS",
                    "CUR_PORTN_OF_BONDS",
                    "CUR_PORTN_OF_CONVERTIBLES",
                    "CUR_PORTN_OF_SBORD_LOANS",
                    "CUR_LIABILITIES_BANK_LOANS_P",
                    "CUR_LIABILITIES_FIN_LSE",
                    "CUR_LIABILITIES_OVERDRAFTS",
                ]
            ],
            "SLS_REVENUES": [i.lower() for i in ["SLS_REVENUES"]],
            "TOTALCOSTOFSALES": [i.lower() for i in ["TOTALCOSTOFSALES"]],
        }
        # Zhaochen: use safe sum function instead of the common sum:
        financial["Opex"] = financial.apply(
            lambda x: self.safe_sum(x, grouping_dict["Opex"]), axis=1
        )
        financial["GrossFixedAssets"] = financial.apply(
            lambda x: self.safe_sum(x, grouping_dict["GrossFixedAssets"]), axis=1
        )
        financial["InterestExpense"] = financial.apply(
            lambda x: self.safe_sum(x, grouping_dict["InterestExpense"]), axis=1
        )
        financial["LongTermDebt"] = financial.apply(
            lambda x: self.safe_sum(x, grouping_dict["LongTermDebt"]), axis=1
        )
        financial["ShortTermDebt"] = financial.apply(
            lambda x: self.safe_sum(x, grouping_dict["ShortTermDebt"]), axis=1
        )
        # Calculate a new column for Total Debt as sum of the Long-Term Debt and the Short-Term Debt
        financial["TotalDebt"] = financial.apply(
            lambda x: self.safe_sum(x, ["LongTermDebt", "ShortTermDebt"]), axis=1
        )
        financial["SLS_REVENUES"] = financial.apply(
            lambda x: self.safe_sum(x, grouping_dict["SLS_REVENUES"]), axis=1
        )
        financial["TOTALCOSTOFSALES"] = financial.apply(
            lambda x: self.safe_sum(x, grouping_dict["TOTALCOSTOFSALES"]), axis=1
        )

        # Keep only the necessary columns needed for analysis in the financial dataset
        financial = financial[required_columns_fin].rename(
            columns={
                "FIN_STM_TYPE": "fin_stm_type",
            }
        )
        # Convert the "DATE_OF_FINANCIALS" column to string format for filtering purposes
        financial.standardized_date_of_financials = pd.to_datetime(
            financial.standardized_date_of_financials
        ).astype("str")
        financial = financial.loc[
            financial.standardized_date_of_financials.str.endswith(fin_date)
        ]
        print(
            "Financial dataset shape after filtering by ending quarter:",
            financial.shape[0],
        )
        summary_2 = self.summarize_step(
            financial,
            fin_date,
            step_name="Step 2: Financial dataset after filtering ending quarter",
        )
        financial.standardized_date_of_financials = pd.to_datetime(
            financial.standardized_date_of_financials
        )

        # financial = financial[financial["fin_stm_type"] != ""]
        # financial = financial[financial["fin_stm_type"] != " "]
        # print(
        #     "Financial dataset after filtering for empty 'fin_stm_type':",
        #     financial.shape[0],
        # )
        financial = financial[financial["fin_stm_type"] == "Annual"]
        print("Financial dataset after 'Annual' filter:", financial.shape[0])
        summary_3 = self.summarize_step(
            financial,
            fin_date,
            step_name="Step 3: Financial dataset after 'Annual' filter",
        )
        # Sort, Identify and remove duplicate rows in the dataset based on the 'spread_id' and 'DATE_OF_FINANCIALS', keeping the fist occurrence only
        financial = financial.sort_values(
            by=["spread_id", "standardized_date_of_financials", "SCORECARD_ID"],
            ascending=[True, True, False],
        ).drop_duplicates(
            subset=["spread_id", "standardized_date_of_financials"], keep="first"
        )

        financial = financial.drop_duplicates(
            subset=["spread_id", "standardized_date_of_financials"], keep="first"
        )
        print("Financial dataset shape after removing duplicates:", financial.shape[0])
        summary_4 = self.summarize_step(
            financial,
            fin_date,
            step_name="Step 4: Financial dataset after removing duplicates based on latest scorecard_ID",
        )
        # Zhaochen: fill invalid entries where the target columns is blank or NA, as "Missing"
        for target in targets:
            financial[target] = np.where(
                (financial[target].isna()) | (financial[target] == ""),
                "Missing",
                financial[target],
            )
        print(
            "Financial dataset shape after removing NAs and empty values:",
            financial.shape[0],
        )
        summary_5 = self.summarize_step(
            financial,
            fin_date,
            step_name="Step 5: Financial dataset after filling 'Missing' for NA/missing values",
        )
        summary_all = pd.concat(
            [
                summary_1,
                summary_2,
                summary_3,
                summary_4,
                summary_5,
            ],
            ignore_index=True,
        )
        return financial, summary_all

    # Process financial data for different portfolio types and return the combined financial data
    def get_fin_by_endMonth(self, date):
        financial = pd.DataFrame(columns=required_columns_fin)
        financial, summary = self.process_fin(date)
        return financial, summary

    # Process the risk csv files, get the necessary columns from risk dataset
    def process_risk(self):
        risk = self.risk.copy()
        risk = risk[
            [
                "Modified_leid",
                "leid",
                "spread_id",
                "ps_parent_leid",
                "ps_parent_company",
                "ps_parent_name",
                "ps_sc_parent_cr_id",
                "cr_cust_id",
                "scorecard_id",
                "scorecard_type",
                "main_profile",
                "country_of_domicile",
                "country_of_risk",
                "sc_financial_currency",
                "isic_code",
                "RA_Industry",
                "sub_segment",
                "irb_ead",
                "exchange_rate",
                "final_approved_grade",
                "ps_parent_final_appr_crg",
                "standalone_pd",
            ]
        ]
        rows_bf_merging = len(risk)
        risk = pd.merge(
            risk,
            isic_data[["ISIC Code", "Sector", "Sub-Sector"]],
            how="left",
            left_on="isic_code",
            right_on="ISIC Code",
        )
        assert rows_bf_merging == len(risk), "Length changed after merging!"
        risk["Sub-Sector"] = risk["Sub-Sector"].apply(lambda x: str(x).upper())
        # Add a 'Portfolio' column to identify the portfolio type for each row
        risk["Portfolio"] = risk["scorecard_type"]
        return risk

    def get_mapping(self, financial, date):
        # Combine risk data for all portfolio types into a single DataFrame
        mapping = pd.concat(
            [self.process_risk()],
            axis=0,
            ignore_index=True,
        )

        # # Making sure that spread_id is string without decimals
        mapping["spread_id"] = mapping["spread_id"].apply(
            lambda x: str(
                int(float(x))
                if pd.notna(x) and str(x).replace(".", "", 1).isdigit()
                else x
            )
        )
        financial["spread_id"] = financial["spread_id"].apply(
            lambda x: str(
                int(float(x))
                if pd.notna(x) and str(x).replace(".", "", 1).isdigit()
                else x
            )
        )
        summary_6 = self.summarize_step(
            mapping,
            date,
            step_name="Step 6: Initial risk dataset count",
        )
        print("Financial dataset shape before merging:", financial.shape[0])
        print("Risk dataset shape before merging:", mapping.shape[0])
        # Merge the financial dataset and risk dataset together, performed on leid
        # rows_bf_merging = len(financial)
        final = pd.merge(financial, mapping, on="spread_id", how="inner")  # financial
        # summary_risk_2 = self.summarize_step(
        #     final,
        #     date,
        #     step_name="Step 2: Risk dataset after merging with financial data",
        # )
        # assert rows_bf_merging == len(final), "Length changed after merging!"
        print("Final dataset shape after merging:", financial.shape[0])
        # Convert the Date column to a date format for consistency
        final.standardized_date_of_financials = pd.to_datetime(
            final.standardized_date_of_financials
        )

        # Sorting is performed by descending the irb_ead
        final = final.sort_values(
            by=[
                "irb_ead",
                "spread_id",
                "standardized_date_of_financials",
                "SCORECARD_ID",
            ],
            ascending=[False, True, True, False],
        )
        return final, summary_6

    # Process the financial dataset to calculate yearly changes, validate entries
    def processing_final(self, final, summary, date):
        final = final.drop_duplicates(
            subset=["spread_id", "standardized_date_of_financials"], keep="first"
        )
        print(
            "Financial dataset shape after removing duplicates in diferent datafiles:",
            final.shape[0],
        )
        # summary_8 = self.summarize_step(
        #     final,
        #     date,
        #     step_name="Step 8: Merged dataset after removing duplicates in different data files",
        # )
        final_merged = pd.DataFrame(
            columns=["spread_id", "standardized_date_of_financials"]
        )
        # Add a 'Year' column derived from date
        final["Year"] = final.standardized_date_of_financials.dt.year
        columns_needed = [
            "Year",
            "fin_stm_type",
            "standardized_date_of_financials",
            "spread_id",
            "ps_parent_leid",
            "ps_parent_company",
            "ps_parent_name",
            "SCORECARD_ID",
            "Modified_leid",
            "ps_sc_parent_cr_id",
            "cr_cust_id",
            "scorecard_id",
            "scorecard_type",
            "main_profile",
            "country_of_domicile",
            "country_of_risk",
            "Portfolio",
            "sc_financial_currency",
            "isic_code",
            "RA_Industry",
            "sub_segment",
            "Sector",
            "Sub-Sector",
            "irb_ead",
            "exchange_rate",
            "final_approved_grade",
            "ps_parent_final_appr_crg",
            "standalone_pd",
        ]
        for target in [
            "SLS_REVENUES",
            "TOTALCOSTOFSALES",
            "Opex",
            "GrossFixedAssets",
            "InterestExpense",
            "LongTermDebt",
            "ShortTermDebt",
            "TotalDebt",
        ]:
            # print("Targeted variable to be processed: ", target)
            # Zhaochen: split missing vs non-missing for the target, and make the missing df the _change terms all "Missing", valid column all False
            rows_bf_concat = len(final)
            globals()[f"final_missing_{target}"] = final[final[target] == "Missing"]
            globals()[f"final_missing_{target}"]["Year_Diff"] = globals()[
                f"final_missing_{target}"
            ]["Year"].diff()
            # globals()[f"final_mising_{target}"]["Valid_{target}"] = False
            globals()[f"final_{target}"] = final[final[target] != "Missing"]
            globals()[f"final_{target}"][target] = pd.to_numeric(
                globals()[f"final_{target}"][target], errors="coerce"
            )
            # Add a Year_Diff column to calculate the gap between consecutive years for each 'spread_id'
            globals()[f"final_{target}"]["Year_Diff"] = globals()[f"final_{target}"][
                "Year"
            ].diff()

            globals()[f"final_{target}"]["Valid"] = (
                globals()[f"final_{target}"]["Year_Diff"] == 1
            ) & (
                globals()[f"final_{target}"]["spread_id"]
                == globals()[f"final_{target}"]["spread_id"].shift()
            )
            if target == "SLS_REVENUES":
                target2 = "Revenue_Change"
                globals()[f"final_missing_{target}"][target2] = "Missing"
                globals()[f"final_{target}"][target2] = globals()[f"final_{target}"][
                    target
                ].diff() / globals()[f"final_{target}"][target].shift().replace(
                    0, np.nan
                )

                globals()[f"final_{target}"].loc[
                    globals()[f"final_{target}"]["Valid"] == False, target2
                ] = "Not applicable"
                globals()[f"final_{target}"] = pd.concat(
                    [
                        globals()[f"final_{target}"],
                        globals()[f"final_missing_{target}"],
                    ],
                    axis=0,
                    ignore_index=True,
                )
            elif target == "TOTALCOSTOFSALES":
                target2 = "COGS_Change"
                globals()[f"final_missing_{target}"][target2] = "Missing"
                globals()[f"final_{target}"][target2] = globals()[f"final_{target}"][
                    target
                ].diff() / globals()[f"final_{target}"][target].shift().replace(
                    0, np.nan
                )

                globals()[f"final_{target}"].loc[
                    globals()[f"final_{target}"]["Valid"] == False, target2
                ] = "Not applicable"
                globals()[f"final_{target}"] = pd.concat(
                    [
                        globals()[f"final_{target}"],
                        globals()[f"final_missing_{target}"],
                    ],
                    axis=0,
                    ignore_index=True,
                )
            elif target == "Opex":
                target2 = "Opex_Change"
                globals()[f"final_missing_{target}"][target2] = "Missing"
                globals()[f"final_{target}"][target2] = globals()[f"final_{target}"][
                    target
                ].diff() / globals()[f"final_{target}"][target].shift().replace(
                    0, np.nan
                )

                globals()[f"final_{target}"].loc[
                    globals()[f"final_{target}"]["Valid"] == False, target2
                ] = "Not applicable"
                globals()[f"final_{target}"] = pd.concat(
                    [
                        globals()[f"final_{target}"],
                        globals()[f"final_missing_{target}"],
                    ],
                    axis=0,
                    ignore_index=True,
                )
            elif target == "GrossFixedAssets":
                target2 = "Capex_Change"
                globals()[f"final_missing_{target}"][target2] = "Missing"
                globals()[f"final_missing_{target}"]["Valid_CAPEX"] = False
                globals()[f"final_{target}"]["CAPEX"] = globals()[f"final_{target}"][
                    target
                ].diff()
                globals()[f"final_{target}"][target2] = globals()[f"final_{target}"][
                    "CAPEX"
                ].diff() / globals()[f"final_{target}"][
                    "CAPEX"
                ].shift().replace(
                    0, np.nan
                )

                globals()[f"final_{target}"]["Valid_capex"] = (
                    (globals()[f"final_{target}"]["Year_Diff"] == 1)
                    & (globals()[f"final_{target}"]["Year_Diff"].shift() == 1)
                    & (
                        globals()[f"final_{target}"]["spread_id"]
                        == globals()[f"final_{target}"]["spread_id"].shift()
                    )
                    & (
                        globals()[f"final_{target}"]["spread_id"]
                        == globals()[f"final_{target}"]["spread_id"].shift(2)
                    )
                )
                # Mark invalid CAPEX changes as not applicable
                globals()[f"final_{target}"].loc[
                    globals()[f"final_{target}"]["Valid_capex"] == False, target2
                ] = "Not applicable"
                # Remove the rows where CAPEX is missing
                # final = final[~((final["CAPEX"].isna()) | (final["CAPEX"] == ""))]
                globals()[f"final_{target}"] = pd.concat(
                    [
                        globals()[f"final_{target}"],
                        globals()[f"final_missing_{target}"],
                    ],
                    axis=0,
                    ignore_index=True,
                )
            elif target == "InterestExpense":
                target2 = "InterestExpense_Change"
                globals()[f"final_missing_{target}"][target2] = "Missing"
                globals()[f"final_{target}"][target2] = globals()[f"final_{target}"][
                    target
                ].diff() / globals()[f"final_{target}"][target].shift().replace(
                    0, np.nan
                )

                globals()[f"final_{target}"].loc[
                    globals()[f"final_{target}"]["Valid"] == False,
                    target2,
                ] = "Not applicable"
                globals()[f"final_{target}"] = pd.concat(
                    [
                        globals()[f"final_{target}"],
                        globals()[f"final_missing_{target}"],
                    ],
                    axis=0,
                    ignore_index=True,
                )
            elif target == "LongTermDebt":
                target2 = "Long_Debt_Change"
                globals()[f"final_missing_{target}"][target2] = "Missing"
                globals()[f"final_{target}"][target2] = globals()[f"final_{target}"][
                    target
                ].diff() / globals()[f"final_{target}"][target].shift().replace(
                    0, np.nan
                )

                globals()[f"final_{target}"].loc[
                    globals()[f"final_{target}"]["Valid"] == False, target2
                ] = "Not applicable"
                globals()[f"final_{target}"] = pd.concat(
                    [
                        globals()[f"final_{target}"],
                        globals()[f"final_missing_{target}"],
                    ],
                    axis=0,
                    ignore_index=True,
                )
            elif target == "ShortTermDebt":
                target2 = "Short_Debt_Change"
                globals()[f"final_missing_{target}"][target2] = "Missing"
                globals()[f"final_{target}"][target2] = globals()[f"final_{target}"][
                    target
                ].diff() / globals()[f"final_{target}"][target].shift().replace(
                    0, np.nan
                )

                globals()[f"final_{target}"].loc[
                    globals()[f"final_{target}"]["Valid"] == False, target2
                ] = "Not applicable"
                globals()[f"final_{target}"] = pd.concat(
                    [
                        globals()[f"final_{target}"],
                        globals()[f"final_missing_{target}"],
                    ],
                    axis=0,
                    ignore_index=True,
                )
            elif target == "TotalDebt":
                target2 = "Total_Debt_Change"
                globals()[f"final_missing_{target}"][target2] = "Missing"
                globals()[f"final_{target}"][target2] = globals()[f"final_{target}"][
                    target
                ].diff() / globals()[f"final_{target}"][target].shift().replace(
                    0, np.nan
                )

                globals()[f"final_{target}"].loc[
                    globals()[f"final_{target}"]["Valid"] == False, target2
                ] = "Not applicable"
                globals()[f"final_{target}"] = pd.concat(
                    [
                        globals()[f"final_{target}"],
                        globals()[f"final_missing_{target}"],
                    ],
                    axis=0,
                    ignore_index=True,
                )
            assert rows_bf_concat == len(
                globals()[f"final_{target}"]
            ), "Length changed after concating!"
            if len(final_merged) == 0:
                final_merged = globals()[f"final_{target}"][
                    columns_needed + [target, target2]
                ]
            else:
                final_merged_processing = final_merged.copy()
                final_merged_processing = final_merged_processing.rename(
                    columns={
                        "spread_id": "spread_id_df1",
                        "standardized_date_of_financials": "standardized_date_of_financials_df1",
                    }
                )
                if target != "GrossFixedAssets":
                    final_columns = list(final_merged.columns) + [target, target2]
                    globals()[f"final_{target}"] = globals()[f"final_{target}"][
                        columns_needed + [target, target2]
                    ]
                else:
                    final_columns = list(final_merged.columns) + [
                        target,
                        "CAPEX",
                        target2,
                    ]
                    globals()[f"final_{target}"] = globals()[f"final_{target}"][
                        columns_needed + [target, "CAPEX", target2]
                    ]
                globals()[f"final_{target}"] = globals()[f"final_{target}"].rename(
                    columns={
                        "spread_id": "spread_id_df2",
                        "standardized_date_of_financials": "standardized_date_of_financials_df2",
                    }
                )
                rows_bf_merging = len(final_merged_processing)
                final_merged_processing = pd.merge(
                    final_merged_processing,
                    globals()[f"final_{target}"],
                    left_on=["spread_id_df1", "standardized_date_of_financials_df1"],
                    right_on=["spread_id_df2", "standardized_date_of_financials_df2"],
                    how="left",
                    suffixes=("_df1", "_df2"),
                )
                assert rows_bf_merging == len(
                    final_merged_processing
                ), "Length changed after merging!"
                for col in columns_needed:
                    final_merged_processing[col] = final_merged_processing[
                        f"{col}_df1"
                    ].fillna(final_merged_processing[f"{col}_df2"])
                # final_merged_processing.columns = {
                #     final_merged_processing.columns.str.replace("_df1S", "", regex=True)
                # }
                final_merged = final_merged_processing[final_columns]

        final_merged.replace([np.inf, -np.inf, np.nan], "Not applicable", inplace=True)
        final_merged = final_merged.sort_values(
            ["spread_id", "standardized_date_of_financials"], ascending=[True, True]
        )
        summary_8 = self.summarize_step(
            final_merged,
            date,
            step_name="Step 8: Dataset after calculating YoY changes",
        )
        summary = pd.concat(
            [
                summary,
                summary_8,
                # summary_9,
            ],
            ignore_index=True,
        )
        return final_merged, summary

    # Set the financial date as quarterly financial report date
    def combine_tgt(self):
        dates = ["-12-31", "-03-31", "-06-30", "-09-30"]
        summary_all = pd.DataFrame(
            columns=["Step", "Unique spread IDs", "Total datapoints", "end_month"]
        )
        for date in dates:
            print("Financial quarter to be processed: ", date)
            financial, summary = self.get_fin_by_endMonth(date)
            financial, summary_6 = self.get_mapping(financial, date)
            summary_7 = self.summarize_step(
                financial,
                date,
                step_name="Step 7: Merged dataset after merging risk with financials based on spread_id",
            )
            summary = pd.concat(
                [
                    summary,
                    summary_6,
                    summary_7,
                ],
                ignore_index=True,
            )
            date_ = date.replace("-", "_")
            globals()[f"final{date_}"], summary = self.processing_final(
                financial, summary, date
            )
            summary_all = pd.DataFrame(
                pd.concat(
                    [
                        summary_all,
                        summary,
                    ],
                    ignore_index=True,
                ),
            )
        return (
            final_12_31,
            final_03_31,
            final_06_30,
            final_09_30,
            summary_all,
        )


# initialize
model = data_processing(
    windows_long_path(
        DATA_DIR / "corp_data_only_annual_statement_updated_sls_revenues.csv"
    ),
    windows_long_path(DATA_DIR / "corp_risk_data_LC_MC_CC_20250930_processed.csv"),
)

# Concat all dataframes with different end dates
# Process data for each quarterly data and combine it
final_12_31, final_03_31, final_06_30, final_09_30, summary = model.combine_tgt()
final = pd.concat(
    [final_12_31, final_03_31, final_06_30, final_09_30], axis=0, ignore_index=True
)


def Month_rename(date):
    if date == "-03-31":
        return "Mar-31"
    elif date == "-06-30":
        return "Jun-30"
    elif date == "-09-30":
        return "Sep-30"
    elif date == "-12-31":
        return "Dec-31"


summary["end_month"] = summary["end_month"].apply(lambda x: Month_rename(x))
datapoint_smry = summary.pivot(
    index="Step", columns="end_month", values="Total datapoints"
)
id_smry = summary.pivot(index="Step", columns="end_month", values="Unique spread IDs")
datapoint_smry["Total"] = datapoint_smry.sum(axis=1)
datapoint_smry.loc["Step 1: Initial financial dataset count", "Total"] = (
    datapoint_smry.loc["Step 1: Initial financial dataset count", "Dec-31"]
)
datapoint_smry.loc["Step 6: Initial risk dataset count", "Total"] = datapoint_smry.loc[
    "Step 6: Initial risk dataset count", "Dec-31"
]
id_smry["Total"] = id_smry.sum(axis=1)
id_smry.loc["Step 1: Initial financial dataset count", "Total"] = id_smry.loc[
    "Step 1: Initial financial dataset count", "Dec-31"
]
id_smry.loc["Step 6: Initial risk dataset count", "Total"] = id_smry.loc[
    "Step 6: Initial risk dataset count", "Dec-31"
]
id_smry.loc["Additional Step: Unique IDs across the full dataset", "Total"] = (
    id_smry.loc["Step 1: Initial financial dataset count", "Total"]
)
for i in ["Mar-31", "Jun-30", "Sep-30", "Dec-31"]:
    for j in [
        "Step 6: Initial risk dataset count",
        "Step 1: Initial financial dataset count",
        "Additional Step: Unique IDs across the full dataset",
    ]:
        if j != "Additional Step: Unique IDs across the full dataset":
            datapoint_smry.loc[j, i] = "/"
        id_smry.loc[j, i] = "/"

id_smry = id_smry.iloc[1:, :]
id_smry = pd.concat(
    [id_smry.iloc[:4], id_smry.iloc[-1:], id_smry.iloc[4:-1]]
).reset_index()


def decre_integer(text):
    if pd.isna(text):
        return text

    def replace(match):
        num = int(match.group())
        return str(num - 1)

    pattern = r"-?\d+"
    return re.sub(pattern, replace, str(text))


id_smry["Step"] = id_smry["Step"].apply(decre_integer)
print("Final Combined Datapoints:", final.shape[0])
final.isic_code = final.isic_code.apply(lambda x: str(x).replace(".0", ""))
final["isic_code"] = pd.to_numeric(final["isic_code"], errors="coerce").astype("Int64")
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
# os.makedirs(os.path.dirname(OUTPUT_PATH2), exist_ok=True)
# final.reset_index(drop=True).to_csv(OUTPUT_PATH)
with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
    datapoint_smry.to_excel(writer, sheet_name="Summary_DataPoints")
    id_smry.to_excel(writer, sheet_name="Summary_IDs", index=False)
    final.to_excel(writer, sheet_name="processed_findata", index=False)
# final.reset_index(drop=True).to_csv(OUTPUT_PATH2)
print("Done!")
# print("Financials saved at: ", f"{DATA_DIR}\data\Financials_final_output.csv")


def column_summary(df, columns, categories):
    results = []
    for col in columns:
        col_data = df[col]
        row = {"Column": col}
        total_sum = 0
        for cat_name, condition in categories.items():
            if callable(condition):
                count = sum(condition(col_data))
            else:
                count = (col_data == condition).sum()
            row[cat_name] = count
            row[f"{cat_name}_%"] = round(count / len(col_data) * 100, 2)
            total_sum += count
        row["Sum_of_Categories"] = total_sum
        row["Sum_of_Categories_%"] = round(total_sum / len(col_data) * 100, 2)
        row["Total_Rows"] = len(col_data)
        results.append(row)
    df_result = pd.DataFrame(results)
    cat_columns = []
    for cat in categories.keys():
        cat_columns.extend([cat, f"{cat}_%"])
    col_order = (
        ["Column"]
        + cat_columns
        + ["Sum_of_Categories", "Sum_of_Categories_%", "Total_Rows"]
    )
    return df_result[col_order]


categories1 = {
    "Missing": "Missing",
    "Not applicable": "Not applicable",
    "NAs": pd.isna,
    "Blanks": lambda x: x == "",
    "Zero": lambda x: pd.to_numeric(x, errors="coerce") == 0,
}
key_columns = [
    "standardized_date_of_financials",
    "spread_id",
    "ps_parent_leid",
    "SCORECARD_ID",
    "scorecard_type",
    "country_of_risk",
    "isic_code",
    "Sector",
    "Sub-Sector",
]  # ZC 2026FEB27 use "ps_parent_leid" as no other parent ID column found so far, can replace in the future
smry1 = column_summary(final.copy(), key_columns, categories1)
categories2 = {
    "Missing": "Missing",
    "Not applicable": "Not applicable",
    "NAs": pd.isna,
    "Blanks": lambda x: x == "",
    "Zero": lambda x: pd.to_numeric(x, errors="coerce") == 0,
    "Positive": lambda x: pd.to_numeric(x, errors="coerce") > 0,
    "Negative": lambda x: pd.to_numeric(x, errors="coerce") < 0,
}
key_columns = [
    "irb_ead",
    "SLS_REVENUES",
    "Revenue_Change",
    "TOTALCOSTOFSALES",
    "COGS_Change",
    "Opex",
    "Opex_Change",
    "GrossFixedAssets",
    "CAPEX",
    "Capex_Change",
    "InterestExpense",
    "InterestExpense_Change",
    "LongTermDebt",
    "Long_Debt_Change",
    "ShortTermDebt",
    "Short_Debt_Change",
    "TotalDebt",
    "Total_Debt_Change",
]  # ZC 2026FEB27 use "ps_parent_leid" as no other parent ID column found so far, can replace in the future
smry2 = column_summary(final.copy(), key_columns, categories2)


def quarter_summary(df, date_col, val_cols):
    df[date_col] = pd.to_datetime(df[date_col])
    # df["q"] = df[date_col].dt.to_period("Q")

    def num_count(x):
        return pd.to_numeric(x, errors="coerce").notna().sum()

    result = pd.DataFrame(index=df[date_col].unique())
    for col in val_cols:
        result[f"{col}"] = df.groupby(date_col)[col].apply(num_count)
    result.loc["TOTAL"] = result.sum()
    result = result.fillna(0).astype(int)
    indices = [idx for idx in result.index if idx != "TOTAL"]
    sorted_indices = sorted(indices) + ["TOTAL"]
    result = result.loc[sorted_indices]
    return result


key_columns = [
    "Revenue_Change",
    "COGS_Change",
    "Opex_Change",
    "CAPEX",
    "Capex_Change",
    "InterestExpense_Change",
    "Long_Debt_Change",
    "Short_Debt_Change",
    "Total_Debt_Change",
]
smry3 = quarter_summary(final.copy(), "standardized_date_of_financials", key_columns)

# conduct the data count analysis
DataStats = pd.DataFrame()
SpreadIdStats = pd.DataFrame()
countrylevel = pd.DataFrame()
target = "spread_id"
final = final[(final[target] != "Missing") & (final[target] != "Not applicable")]
print(f"No. of samples with valid {target}:", len(final))
for s in final["Sector"].unique():
    final_by_sector = final[final.Sector == s]
    Sector_total = (
        final_by_sector.groupby("Sector")["spread_id"]
        .count()
        .reset_index(name="Sector_total")
    )

    DataStats = pd.concat(
        [
            DataStats,
            final_by_sector.groupby(["Sector", "Sub-Sector"])
            .agg({"spread_id": "count"})
            .reset_index()[["Sector", "Sub-Sector", "spread_id"]]
            .merge(Sector_total, on="Sector", how="left"),
        ],
        axis=0,
        ignore_index=True,
    )
    SpreadIdStats = pd.concat(
        [
            SpreadIdStats,
            final_by_sector.groupby(["Sector", "Sub-Sector"])
            .agg({"spread_id": "nunique"})
            .reset_index()[["Sector", "Sub-Sector", "spread_id"]]
            .sort_values(by=["spread_id"], ascending=[False]),
        ],
        axis=0,
        ignore_index=True,
    )

for c in final["country_of_risk"].unique():
    final_by_country = final[final.country_of_risk == c]
    countrylevel = pd.concat(
        [
            countrylevel,
            final_by_country.groupby(["country_of_risk"])
            .agg({"spread_id": "count"})
            .reset_index()[["country_of_risk", "spread_id"]]
            .sort_values(by=["spread_id"], ascending=[False]),
        ],
        axis=0,
        ignore_index=True,
    )

with pd.ExcelWriter(OUTPUT_PATH, mode="a", engine="openpyxl") as writer:
    DataStats.sort_values(
        by=["Sector_total", "Sector", "spread_id"],
        ascending=[False, True, False],
    ).rename(
        columns={"spread_id": "DataPoints count (based on spread_id column)"}
    ).to_excel(
        writer, sheet_name="DataPointStats"
    )
    countrylevel.sort_values(by=["spread_id"], ascending=[False]).rename(
        columns={"spread_id": "DataPoints count (based on spread_id column)"}
    ).to_excel(writer, sheet_name="CountryStats")
    smry1.to_excel(writer, sheet_name="DQcheck1")
    smry2.to_excel(writer, sheet_name="DQcheck2")
    smry3.to_excel(writer, sheet_name="Quarter_Summary")
    # SpreadIdStats.to_excel(writer, sheet_name="UniqueSpreadIdStats", index=False)
