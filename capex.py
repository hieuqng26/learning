from log_file import TimestampLog
import sys
from Capex_config import *
import seaborn as sns
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import warnings

warnings.filterwarnings("ignore")


# -------------------


def Capex(sector_name):

    # --- Configuration ---

    Capex_config = SECTORS[sector_name]

    sector = Capex_config.sector
    sector_short = Capex_config.sector_short
    segmentByCountry = Capex_config.segmentByCountry
    top_segments = Capex_config.top_segments
    includeOthers = Capex_config.includeOthers
    sub_segment_column_name = Capex_config.sub_segment_column_name
    sub_segment_function = Capex_config.sub_segment_function
    sub_segment_mapping = Capex_config.sub_segment_mapping
    sub_segment_replacement_dict = Capex_config.sub_segment_replacement_dict
    exclude_sub_na = Capex_config.exclude_sub_na

    id_column_name = Capex_config.id_column_name
    percentiles_for_chart = Capex_config.percentiles_for_chart
    percentiles_for_file = Capex_config.percentiles_for_file
    computeChartAggregatedSegments = Capex_config.computeChartAggregatedSegments
    groupCountry = Capex_config.groupCountry
    groupSector = Capex_config.groupSector
    ISIC_mapping = Capex_config.ISIC_mapping
    country_group_mapping = Capex_config.country_group_mapping

    globalmodel = Capex_config.globalmodel
    global_exclude_sectors = Capex_config.global_exclude_sectors

    # input paths
    isic_file_path = Capex_config.isic_file_path
    fin_file_path = Capex_config.fin_file_path

    exclusion_file_path = Capex_config.exclusion_file_path
    sub_segment_case = Capex_config.sub_segment_case

    # output paths

    stress_result_file_path = windows_long_path(
        f"{OUT_DIR}/{sector_name}/Capex_{sector_short}_Stress_Impacts.xlsx"
    )
    full_result_file_path = windows_long_path(
        f"{OUT_DIR}/{sector_name}/Capex_{sector_short} - Full Data.xlsx"
    )
    pdf_path = windows_long_path(f"{OUT_DIR}/{sector_name}/Capex_{sector_short}.pdf")
    sum_path = windows_long_path(
        f"{OUT_DIR}/{sector_name}/{sector_short}_Capex_Datapoints.xlsx"
    )

    # - output chart ------------
    def outputChart(
        data,
        chartTitle,
        bin_edges=np.arange(-2, 2.2, 0.05),  # At least 20, but max 100 for granularity
        plotSeaboneHistplot=False,
        pdfPagesObject=None,
        figsize=(10, 6),
        xrange=(-2, 2),
    ):

        # Create the histogram (without KDE)
        plt.figure(figsize=figsize)
        if plotSeaboneHistplot:
            sns.histplot(
                data,
                bins=bin_edges,
                stat="count",
                color="blue",
                alpha=0.6,
                label="Histogram (Count)",
            )

        # Calculate percentiles
        percentile_values = [data.quantile(p / 100) for p in percentiles_for_chart]

        plt.hist(
            data,
            bins=bin_edges,
            range=(0, 1),
            alpha=0.7,
            color="blue",
            edgecolor="black",
        )
        for i, (perc, value) in enumerate(
            zip(percentiles_for_chart, percentile_values)
        ):
            color = "green" if i == 4 else "red"
            plt.axvline(
                value,
                color=color,
                linestyle="--",
                label=f"{perc}th Percentile: {value:.4f}",
            )

        if xrange:
            # Set X-axis range
            plt.xlim(xrange[0], xrange[1])

        # Add labels, title, and legend
        # plt.title(chartTitle)
        # plt.xlabel("Delta Opex/Revenue")
        # plt.ylabel("Frequency")
        # plt.legend()
        # plt.grid(axis="y", alpha=0.75)
        plt.title(chartTitle)
        plt.xlabel("CAPEX/Revenue")
        plt.ylabel("Frequency")
        plt.legend()
        plt.grid(axis="y", alpha=0.75)

        # plt.show() # Show the plot
        if pdfPagesObject:
            pdf.savefig()  # Save the current figure
        plt.clf()
        plt.close()

    # ------------------------------------------------
    # Load data
    financials = pd.read_csv(fin_file_path).iloc[:, 1:]
    isic_data = pd.read_excel(
        isic_file_path
    )  # Will need to be included in all config files.

    financials["country_of_risk"] = financials["country_of_risk"].str.upper()

    # Updating ISIC Codes
    ###################################
    if ISIC_mapping:
        # Backup old RA_Industry
        financials.rename(columns={"RA_Industry": "RA_Industry_Old"}, inplace=True)

        # Prepare mapping dictionaries (used in both models)
        isic_map = isic_data.set_index("ISIC Code")[
            "Risk Industry_April 2025"
        ].to_dict()
        subseg_map = isic_data.set_index("ISIC Code")["Biz L1_Apr 2025.1"].to_dict()

        if globalmodel:
            #  GLOBAL MODEL: Map full RA_Industry and sub_segment
            financials["RA_Industry"] = (
                financials["isic_code"].map(isic_map).fillna("NA")
            )

            # Filter out excluded global sectors
            financials = financials[
                ~financials["RA_Industry"].isin(global_exclude_sectors)
            ]
            financials = financials[financials["RA_Industry"] != "NA"]

        else:
            # NON-GLOBAL MODEL: Only tag if belongs to target sector
            isic_data_filtered = isic_data[
                isic_data["Risk Industry_April 2025"] == sector
            ]
            financials["RA_Industry"] = np.where(
                financials["isic_code"].isin(isic_data_filtered["ISIC Code"].unique()),
                sector,
                "Not Applicable",
            )

            #  Still map sub_segment in non-global case
            financials["sub_segment"] = (
                financials["isic_code"].map(subseg_map).fillna("NA")
            )
            if sub_segment_case:
                financials["sub_segment"] = financials["sub_segment"].str.title()
            financials = financials[financials["RA_Industry"] == sector]

            # Filter: Keep only data from the desired sector
    else:
        financials = financials[financials["RA_Industry"] == sector]

    # Clean up
    # financials.to_excel(fr'{DATA_DIR}/03. Model/{sector_name}/04. Capex/{sector_short}_financials.xlsx')

    ##############################################

    if groupCountry:
        # Build reverse mapping: each country -> group label
        reverse_country_map = {}
        for group_label, countries in country_group_mapping.items():
            for country in countries:
                reverse_country_map[country] = group_label

        # Apply mapping to financials['country_of_risk']
        financials["country_of_risk_grouped"] = financials["country_of_risk"].apply(
            lambda x: reverse_country_map.get(x, x)
        )

    if groupSector:
        # Build reverse mapping: each country -> group label
        reverse_country_map = {}
        for group_label, countries in country_group_mapping.items():
            for country in countries:
                reverse_country_map[country] = group_label

        # Apply mapping to financials['country_of_risk']
        financials["sub_segment_group"] = financials["sub_segment"].apply(
            lambda x: reverse_country_map.get(x, x)
        )

    ########################################
    # - By segments -----------------------------------------------this mapping is for CT
    if sub_segment_function:
        financials[sub_segment_column_name] = (
            financials["isic_code"].map(sub_segment_mapping).fillna("Others")
        )

    if exclude_sub_na:
        financials = financials[financials["sub_segment"] != "Not applicable"]

    # Summary table function as per GMV requirements
    def summarize_step(
        df,
        top_segments,
        sub_segment_column_name,
        includeOthers,
        step_name,
        id_column_name="spread_id",
    ):
        financials = df.copy()

        # Step 1: Create a clean grouping column
        if includeOthers:
            region_list = top_segments + ["Others"]
            financials["__region__"] = financials[sub_segment_column_name].apply(
                lambda x: x if x in top_segments else "Others"
            )
        else:
            region_list = top_segments
            financials["__region__"] = financials[sub_segment_column_name]

        # Step 2: Generate summary
        summary = []
        for region in region_list:
            df_region = financials[financials["__region__"] == region]
            summary.append(
                {
                    "Step": step_name,
                    "Region": region,
                    "Unique spread IDs": df_region[id_column_name].nunique(),
                    "Total datapoints": df_region.shape[0],
                }
            )

        return pd.DataFrame(summary)

    summary_1 = summarize_step(
        financials,
        top_segments,
        sub_segment_column_name,
        includeOthers,
        step_name="Step 1: Initial data",
    )
    # financials.to_excel(fr'{DATA_DIR}/03. Model/{sector_name}/04. Capex/Capex_{sector_short}_Financials.xlsx')

    if sub_segment_replacement_dict:
        financials.replace(
            {sub_segment_column_name: sub_segment_replacement_dict}, inplace=True
        )
    financials[sub_segment_column_name] = financials[sub_segment_column_name].fillna(
        "Others"
    )

    financials[id_column_name] = financials[id_column_name].astype(str)

    financials["DATE_OF_FINANCIALS"] = pd.to_datetime(financials["DATE_OF_FINANCIALS"])
    financials["Year"] = financials["DATE_OF_FINANCIALS"].dt.year
    financials["Month"] = financials["DATE_OF_FINANCIALS"].dt.month

    # ------------------------------------------------
    financials["SLS_REVENUES"] = financials["SLS_REVENUES"].replace(
        "Not applicable", None
    )
    summary_2 = summarize_step(
        financials,
        top_segments,
        sub_segment_column_name,
        includeOthers,
        step_name="Step 2: Data after dropping Revenue 'Not applicable'",
    )
    financials["SLS_REVENUES"] = financials["SLS_REVENUES"].replace("Missing", None)
    summary_3 = summarize_step(
        financials,
        top_segments,
        sub_segment_column_name,
        includeOthers,
        step_name="Step 3: Data after dropping Revenue 'Missing'",
    )

    financials["CAPEX"] = financials["CAPEX"].replace("Not applicable", None)
    financials["CAPEX"] = financials["CAPEX"].replace("Missing", None)

    financials["SLS_REVENUES"] = financials["SLS_REVENUES"].astype(
        float
    )  # this is needed due to a row with a string "0.0"
    financials["CAPEX"] = financials["CAPEX"].astype(float)
    financials = financials[financials["SLS_REVENUES"] != 0]
    summary_4 = summarize_step(
        financials,
        top_segments,
        sub_segment_column_name,
        includeOthers,
        step_name="Step 4: Data after dropping Revenue 0",
    )

    # ------------------------------------------------
    financials["CAPEX/Revenue"] = (financials["CAPEX"]) / (financials["SLS_REVENUES"])
    financials["CAPEX/Revenue"] = financials["CAPEX/Revenue"].clip(
        lower=0
    )  # floored the ratio at 0
    summary_5 = summarize_step(
        financials,
        top_segments,
        sub_segment_column_name,
        includeOthers,
        step_name="Step 5: Data after keeping only 'CAPEX/Revenue' > 0",
    )

    # ------------------------------------------------
    # Counting the rows with NA values in column 'CAPEX/Revenue'
    CAPEX = financials.dropna(subset=["CAPEX/Revenue", "SLS_REVENUES"])
    summary_6 = summarize_step(
        CAPEX,
        top_segments,
        sub_segment_column_name,
        includeOthers,
        step_name="Step 6: Data after dropping 'CAPEX/Revenue' or Revenue NA",
    )

    # - remove quarter data points and only leave annual data ------------------- # This is happening in Financials script already
    CAPEX = CAPEX.sort_values(
        by=[id_column_name, "Year", "Month"], ascending=[True, True, False]
    )
    CAPEX_end = CAPEX.drop_duplicates(subset=[id_column_name, "Year"], keep="first")
    summary_7 = summarize_step(
        CAPEX_end,
        top_segments,
        sub_segment_column_name,
        includeOthers,
        step_name="Step 7: Data after removing duplicates by spread_id and Date",
    )

    # ------------------------------------------------

    # Drop rows with inf values in 'CAPEX/Revenue'
    CAPEX_clean = CAPEX_end[~CAPEX_end["CAPEX/Revenue"].isin([float("inf")])]
    summary_8 = summarize_step(
        CAPEX_clean,
        top_segments,
        sub_segment_column_name,
        includeOthers,
        step_name="Step 8: Data after removing inf values in 'CAPEX/Revenue'",
    )

    # CAPEX_clean.to_excel(fr"{DATA_DIR}/03. Model/{sector_name}/04. Capex/CAPEX_{sector_short}_Modelling_data.xlsx")
    summary_9 = summarize_step(
        CAPEX_clean,
        top_segments,
        sub_segment_column_name,
        includeOthers,
        step_name="Step 9: Final modelling data",
    )

    # - Data dampening considering exclusion/dampened points of revenue -------------------
    if exclusion_file_path.endswith("xlsx"):
        exclude = pd.read_excel(exclusion_file_path)
    elif exclusion_file_path.endswith("csv"):
        exclude = pd.read_csv(exclusion_file_path)
    else:
        raise ValueError("Invalid file type for exclusion data")
    # Ensure 'Date' and 'DATE_OF_FINANCIALS' are in datetime format (if not already)
    exclude["Date"] = pd.to_datetime(exclude["Date"])
    CAPEX_clean["DATE_OF_FINANCIALS"] = pd.to_datetime(
        CAPEX_clean["DATE_OF_FINANCIALS"]
    )
    exclude[id_column_name] = exclude[id_column_name].astype(str)

    # Create a set of (Date, leid) tuples for fast lookup
    exclude_set = set(zip(exclude["Date"], exclude[id_column_name]))

    # Create mask where (DATE_OF_FINANCIALS, id_column_name) matches exclude_set
    dampening_mask = (
        CAPEX_clean[["DATE_OF_FINANCIALS", id_column_name]]
        .apply(tuple, axis=1)
        .isin(exclude_set)
    )

    dampening_n = dampening_mask.sum()

    # Apply transformation where both DATE_OF_FINANCIALS and leid exist in exclude
    CAPEX_clean.loc[
        CAPEX_clean[["DATE_OF_FINANCIALS", id_column_name]]
        .apply(tuple, axis=1)
        .isin(exclude_set),
        "CAPEX/Revenue",
    ] *= 0.0001

    # - Compute chart of aggregated segments after dampening consistent dampened data points ---------------
    if computeChartAggregatedSegments:
        # Drop NaN values from Opex/Revenue before filtering
        filtered_data = CAPEX_clean["CAPEX/Revenue"].dropna()

        # Check min/max and unique value count after filtering
        # print(f"Min value after removing NA: {filtered_data.min()}")
        # print(f"Max value after removing NA: {filtered_data.max()}")
        # print(f"Number of unique values: {filtered_data.nunique()}")
        outputChart(
            filtered_data,
            f"Distribution of CAPEX/Revenue with Dampner - {sector}",
            plotSeaboneHistplot=True,
        )

    CAPEX_clean["TOPS"] = np.where(
        CAPEX_clean[sub_segment_column_name].isin(top_segments),
        CAPEX_clean[sub_segment_column_name],
        "Others",
    )
    if includeOthers:
        top_segments += ["Others"]

        # Combine dampening mask with sub_segment_column_name
    dampened_segments = CAPEX_clean.loc[dampening_mask, "TOPS"]

    # Count number of dampened rows per unique sub-segment
    dampened_counts = dampened_segments.value_counts()

    # Create an empty list to collect data
    result_data_full = []

    # Calculate metrics for each portfolio
    for top_segment in top_segments:
        subset = CAPEX_clean[CAPEX_clean["TOPS"] == top_segment]

        # Calculate unique LEIDs count
        unique_leids = subset[id_column_name].nunique()
        # data_points = len(subset)

        # Calculate percentiles
        percentile_values = (
            subset["CAPEX/Revenue"]
            .quantile([p / 100 for p in percentiles_for_file])
            .values
        )

        # Calculate stress impacts
        stresses = np.array(percentile_values[1:]) - percentile_values[0]

        # Append the data to the result list
        result_data_full.append(
            [
                top_segment,
                unique_leids,
                # data_points,
                *percentile_values,  # Expand percentile values into individual columns
                *stresses,
            ]
        )

    # Define column names for the result dataframe
    # convert percentiles to string: 33.333... --> 33.33, 66.6666... --> 66.67, 50.0 --> 50, 97.50 --> 97.5
    percentiles_str = [f"{p:.2f}".rstrip("0").rstrip(".") for p in percentiles_for_file]
    columns = [
        "TOPS",
        "Unique Spread_IDs",
        *[ps + "th Perc" for ps in percentiles_str],
        *["Stress Impact - " + ps + "th Perc" for ps in percentiles_str[1:]],
    ]

    # Create a dataframe from the result data
    result_df_exclude = pd.DataFrame(result_data_full, columns=columns)
    result_df_exclude = result_df_exclude.reset_index(drop=True)

    # ------------------------------------------------
    result_df_exclude = result_df_exclude.T.reset_index()
    result_df_exclude.columns = result_df_exclude.iloc[0]
    result_df_exclude = result_df_exclude[1:]
    result_df_exclude = result_df_exclude.reset_index(drop=True)

    # ------------------------------------------------
    # compuate "Scenario Severity (1 in x)" from percentile
    pctiles_for_1_in_x = (
        percentiles_for_file  # for quantile output for 50, 40, 33.33...
        + percentiles_for_file[1:]
    )  # for quantile impact for 40, 33.33...
    result_df_exclude["Scenario Severity (1 in x)"] = ["-"] + [
        round(100.0 / p, 1) for p in pctiles_for_1_in_x
    ]

    result_df_exclude = result_df_exclude.rename(
        columns={"TOPS": "Stress impact - percentile"}
    )
    new_order = [
        "Stress impact - percentile",
        "Scenario Severity (1 in x)",
        *top_segments,
    ]
    result_df_exclude = result_df_exclude[new_order]

    # ------------------------------------------------
    # row offset to skip
    # - skip a row of # of unique spread ID
    # - skip percentile values (we only need percentile IMPACT following percentile VALUES)
    row_offset = 1 + len(percentile_values)
    result_df_exclude = result_df_exclude.iloc[row_offset:].reset_index(drop=True)

    result_data_final = []
    current_date = datetime.now().strftime("%Y-%m-%d")

    for _, row in result_df_exclude.iterrows():
        for top_segment in top_segments:
            result_data_final.append(
                {
                    "Driver": "CAPEX",
                    "Stress impact - percentile": row["Stress impact - percentile"],
                    "Scenario Severity (1 in x)": row["Scenario Severity (1 in x)"],
                    "Sector": sector,
                    "Sub-sector": top_segment if not segmentByCountry else "-",
                    "Country": top_segment if segmentByCountry else "-",
                    "Stress Impact": row[top_segment],
                    "As of Date": current_date,
                }
            )

    result_df_final = pd.DataFrame(result_data_final)
    segmentColumn = "Country" if segmentByCountry else "Sub-sector"
    result_df_final = result_df_final.sort_values(
        by=[segmentColumn, "Scenario Severity (1 in x)"], ascending=[False, True]
    )
    os.makedirs(os.path.dirname(stress_result_file_path), exist_ok=True)
    result_df_final.to_excel(stress_result_file_path)

    # Create an empty list to collect data
    result_data_full_summary = []

    # Calculate metrics for each portfolio
    for top_segment in top_segments:
        subset = CAPEX_clean[CAPEX_clean["TOPS"] == top_segment]

        # Calculate unique LEIDs count
        unique_leids = subset[id_column_name].nunique()
        data_points = len(subset)

        # Calculate percentiles
        percentile_values = (
            subset["CAPEX/Revenue"]
            .quantile([p / 100 for p in percentiles_for_file])
            .values
        )

        # Calculate stress impacts
        stresses = np.array(percentile_values[1:]) - percentile_values[0]

        # Append the data to the result list
        result_data_full_summary.append(
            [
                top_segment,
                unique_leids,
                data_points,
                *percentile_values,  # Expand percentile values into individual columns
                *stresses,
            ]
        )

    # Define column names for the result dataframe
    # convert percentiles to string: 33.333... --> 33.33, 66.6666... --> 66.67, 50.0 --> 50, 97.50 --> 97.5
    percentiles_str = [f"{p:.2f}".rstrip("0").rstrip(".") for p in percentiles_for_file]
    columns = [
        "Sub_Segment/Country",
        "Unique Spread_IDs",
        "Data Points",
        *[ps + "th Perc" for ps in percentiles_str],
        *["Stress Impact - " + ps + "th Perc" for ps in percentiles_str[1:]],
    ]

    result_df_summary = pd.DataFrame(result_data_full_summary, columns=columns)
    result_df_summary = result_df_summary.reset_index(drop=True)
    result_df_summary.to_excel(full_result_file_path)

    # ------------------------------------------------
    from matplotlib.backends.backend_pdf import PdfPages

    # Create a PdfPages object to save multiple plots
    with PdfPages(pdf_path) as pdf:
        for top_segment in top_segments:
            # Filter data and calculate percentiles (replace with your logic)
            subset = CAPEX_clean[CAPEX_clean["TOPS"] == top_segment]
            unique_leids = subset[id_column_name].nunique()

            segmentNameForChart = "Country" if segmentByCountry else "Sector"
            idsNameForChart = (
                "LEIDs" if id_column_name.upper() == "LEID" else "Spread ids"
            )
            chartTitle = f"Distribution of CAPEX/Revenue for Each {segmentNameForChart}: {top_segment}\nNumber of Unique {idsNameForChart}: {unique_leids}"
            outputChart(
                subset["CAPEX/Revenue"],
                chartTitle,
                bin_edges=100,
                pdfPagesObject=pdf,
                figsize=(8, 6),
                xrange=None,
            )

    # Optional: Print confirmation
    print(f"All plots have been saved to {pdf_path}")

    # Display or save

    # summary_df.to_excel("spread_summary_by_region.xlsx", index=False)
    summary_all = pd.concat(
        [
            summary_1,
            summary_2,
            summary_3,
            summary_4,
            summary_5,
            summary_6,
            summary_7,
            summary_8,
            summary_9,
        ],
        ignore_index=True,
    )

    # ---- Step 1: Define preferred region order ----
    preferred_order = top_segments

    # ---- Step 2: Create wide table for Total datapoints ----
    datapoints_wide = summary_all.pivot(
        index="Step", columns="Region", values="Total datapoints"
    )
    datapoints_wide = datapoints_wide.reindex(columns=preferred_order)
    datapoints_wide = datapoints_wide.fillna(0).astype(int)

    # ---- Step 3: Create wide table for Unique spread IDs ----
    spread_ids_wide = summary_all.pivot(
        index="Step", columns="Region", values="Unique spread IDs"
    )
    spread_ids_wide = spread_ids_wide.reindex(columns=preferred_order)
    spread_ids_wide = spread_ids_wide.fillna(0).astype(int)

    # Combine total with sub-segment breakdown
    dampening_summary = pd.DataFrame(dampened_counts).reset_index()
    dampening_summary.columns = ["Sub-Segment", "Dampened Datapoints"]

    # Append total as a new row
    total_row = pd.DataFrame(
        [["TOTAL", dampening_n]], columns=["Sub-Segment", "Dampened Datapoints"]
    )
    dampening_summary = pd.concat([dampening_summary, total_row], ignore_index=True)

    # save to Excel
    with pd.ExcelWriter(sum_path, engine="openpyxl") as writer:
        datapoints_wide.to_excel(writer, sheet_name="Datapoints")
        spread_ids_wide.to_excel(writer, sheet_name="UniqueSpreadIDs")
        dampening_summary.to_excel(
            writer, sheet_name="Dampened Datapoints", index=False
        )


if __name__ == "__main__":
    for sector in [
        "O&G",
        "Commodity Traders",
        "Metals & Mining",
        "Automobiles & Components",
        "Consumer Durables & Apparel",
        "Technology Hardware & Equipment",
        "Building Products, Construction & Engineering",
        "CRE",
        "Other Capital Goods",
        "Transportation and Storage",
        "Global",
    ]:
        Capex(sector)
        sys.stdout = TimestampLog("Capex_master")
