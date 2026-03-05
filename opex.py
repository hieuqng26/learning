from log_file import TimestampLog
import sys
from Opex_config import *
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import warnings
from io import BytesIO
from openpyxl import load_workbook
from openpyxl.drawing.image import Image
from sklearn.metrics import mean_absolute_error, mean_squared_error

warnings.filterwarnings("ignore")


# -------------------


def Opex(sector_name):

    # --- Configuration ---

    Opex_config = SECTORS[sector_name]

    sector = Opex_config.sector
    sector_short = Opex_config.sector_short
    segmentByCountry = Opex_config.segmentByCountry
    top_segments = Opex_config.top_segments
    includeOthers = Opex_config.includeOthers
    sub_segment_column_name = Opex_config.sub_segment_column_name
    sub_segment_function = Opex_config.sub_segment_function
    sub_segment_mapping = Opex_config.sub_segment_mapping
    sub_segment_replacement_dict = Opex_config.sub_segment_replacement_dict
    applyingDampener = Opex_config.applyingDampener
    dampenerPercentileBySegment = Opex_config.dampenerPercentileBySegment
    id_column_name = Opex_config.id_column_name
    includeZeroOpex = Opex_config.includeZeroOpex
    useAdditionalCategory = Opex_config.useAdditionalCategory
    additionalCategoryColumnName = Opex_config.additionalCategoryColumnName
    additionalCategoryColumnNameToOutputFile = (
        Opex_config.additionalCategoryColumnNameToOutputFile
    )
    additionalCategories = Opex_config.additionalCategories
    percentiles_for_chart = Opex_config.percentiles_for_chart
    percentiles_for_file = Opex_config.percentiles_for_file
    computeChartAggregatedSegments = Opex_config.computeChartAggregatedSegments
    groupCountry = Opex_config.groupCountry
    groupSector = Opex_config.groupSector
    ISIC_mapping = Opex_config.ISIC_mapping
    country_group_mapping = Opex_config.country_group_mapping
    exclude_sub_na = Opex_config.exclude_sub_na
    dampned_for_revenue_outlier = Opex_config.dampned_for_revenue_outlier
    step_2_quantile = Opex_config.step_2_quantile
    globalmodel = Opex_config.globalmodel
    global_exclude_sectors = Opex_config.global_exclude_sectors
    sub_segment_case = Opex_config.sub_segment_case

    # input paths
    isic_file_path = Opex_config.isic_file_path
    fin_file_path = Opex_config.fin_file_path

    exclusion_file_path = Opex_config.exclusion_file_path
    exclusion_file_path_gen2 = Opex_config.exclusion_file_path_gen2
    # output paths

    output_temp = r"C:\Users\1665642\OneDrive - Standard Chartered Bank\Documents\test_run"
    stress_result_file_path = windows_long_path(
        f"{output_temp}/{sector_name}/Opex_{sector_short} - Stress Impacts.xlsx"
    )
    full_result_file_path = windows_long_path(
        f"{output_temp}/{sector_name}/Opex_{sector_short} - Full Data.xlsx"
    )
    pdf_path = windows_long_path(
        f"{output_temp}/{sector_name}/Opex_{sector_short}.pdf"
    )
    sum_path = windows_long_path(
        f"{output_temp}/{sector_name}/{sector_short}_Opex_Consolidated.xlsx"
    )

    # stress_result_file_path = windows_long_path(
    #     f"{OUT_DIR}/{sector_name}/Opex_{sector_short} - Stress Impacts_gen2.xlsx"
    # )
    # full_result_file_path = windows_long_path(
    #     f"{OUT_DIR}/{sector_name}/Opex_{sector_short} - Full Data_gen2.xlsx"
    # )
    # pdf_path = windows_long_path(
    #     f"{OUT_DIR}/{sector_name}/Opex_{sector_short}_gen2.pdf"
    # )
    # sum_path = windows_long_path(
    #     f"{OUT_DIR}/{sector_name}/{sector_short}_Opex_Combined_gen2.xlsx"
    # )

    # O&G paths only
    full_result_file_additional_category_path = (
        f"{OUT_DIR}/{sector_name}/Opex_country_producer.xlsx"
    )
    pdf_additional_category_path = (
        f"{OUT_DIR}/{sector_name}/opex_country_producer_old.pdf"
    )
    stress_result_file_additional_category_path = (
        f"{OUT_DIR}/{sector_name}/Opex_{sector_short} - Stress Impacts.xlsx"
    )
    os.makedirs(f"{OUT_DIR}/{sector_name}", exist_ok=True)

    # --- Run ---
    def compute_delta(group, change):
        # Ensure data is sorted
        group = group.sort_values(by=["Year", "Month"])

        if change == "abs":
            # Shift values for previous year and month
            group["Opex/Revenue_prev"] = group["Opex/Revenue"].shift(1)
            group["Month_prev"] = group["Month"].shift(1)
            group["Year_prev"] = group["Year"].shift(1)

            # Compute absolute difference only if Month matches and Year difference is 1
            group["delta_opex/rev"] = group["Opex/Revenue"].diff()
            group["delta_opex/rev"] = group.apply(
                lambda row: (
                    row["delta_opex/rev"]
                    if (
                        row["Month"] == row["Month_prev"]
                        and row["Year"] - row["Year_prev"] == 1
                    )
                    else np.nan
                ),
                axis=1,
            )

        elif change == "relative":
            # Shift values for previous year and month
            group["Opex/Revenue_prev"] = group["Opex/Revenue"].shift(1)
            group["Month_prev"] = group["Month"].shift(1)
            group["Year_prev"] = group["Year"].shift(1)

            # Compute relative difference only if Month matches and Year difference is 1
            group["delta_opex/rev"] = np.where(
                (group["Month"] == group["Month_prev"])
                & (group["Year"] - group["Year_prev"] == 1)
                & (group["Opex/Revenue_prev"] != 0),
                (group["Opex/Revenue"] - group["Opex/Revenue_prev"])
                / group["Opex/Revenue_prev"],
                np.nan,
            )

        elif change == "none":
            # Do nothing, just sort by year and return
            pass

        # Clean up helper columns
        group.drop(
            columns=["Opex/Revenue_prev", "Month_prev", "Year_prev"],
            inplace=True,
            errors="ignore",
        )
        return group

    def revenue_adjustment(df, id_column_name="spread_id"):
        if exclusion_file_path_gen2.endswith("xlsx"):
            exclusion = pd.read_excel(
                exclusion_file_path_gen2, sheet_name="Outlier Panel Data"
            )
        elif exclusion_file_path_gen2.endswith("csv"):
            exclusion = pd.read_csv(exclusion_file_path_gen2)
        else:
            raise ValueError("Invalid file type for exclusion data")
        original_fin = df
        original_fin["DATE_OF_FINANCIALS"] = original_fin["DATE_OF_FINANCIALS"].astype(
            "str"
        )
        dates = ["-12-31", "-03-31", "-06-30", "-09-30"]
        for date in dates:
            date_ = date.replace("-", "_")
            globals()[f"final{date_}"] = original_fin[
                original_fin["DATE_OF_FINANCIALS"].str.endswith(date)
            ]
            globals()[f"final{date_}"] = globals()[f"final{date_}"].sort_values(
                [id_column_name, "DATE_OF_FINANCIALS"], ascending=[True, True]
            )
        original_fin = pd.concat(
            [final_12_31, final_03_31, final_06_30, final_09_30],
            axis=0,
            ignore_index=True,
        )
        original_fin["Prev_Rev"] = original_fin["SLS_REVENUES"].shift()
        original_fin["DATE_OF_FINANCIALS"] = pd.to_datetime(
            original_fin["DATE_OF_FINANCIALS"]
        )
        exclusion["Date"] = pd.to_datetime(exclusion["Date"])
        original_fin["Prev_Rev"] = np.where(
            (
                (
                    original_fin["DATE_OF_FINANCIALS"]
                    .diff()
                    .abs()
                    .between(pd.Timedelta(days=365), pd.Timedelta(days=366))
                )
                & (original_fin[id_column_name] == original_fin[id_column_name].shift())
            ),
            original_fin["Prev_Rev"],
            "Not applicable",
        )
        rev_ref = pd.merge(
            exclusion,
            original_fin,
            # [
            #     ["DATE_OF_FINANCIALS", id_column_name, "SLS_REVENUES", "Prev_Rev"]
            # ],
            how="right",
            left_on=["Date", id_column_name],
            right_on=[
                "DATE_OF_FINANCIALS",
                id_column_name,
            ],
        )
        rev_ref["Prev_Rev"] = pd.to_numeric(rev_ref["Prev_Rev"], errors="coerce")
        rev_ref["SLS_REVENUES"] = np.where(
            (rev_ref["outlier_weight"] == 0.00001),
            rev_ref["Prev_Rev"] * (1 + rev_ref["y_winsor"]),
            rev_ref["SLS_REVENUES"],
        )
        return rev_ref

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
            color = "green" if i == 0 else "red"
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
        plt.title(chartTitle)
        plt.xlabel("Delta Opex/Revenue")
        plt.ylabel("Frequency")
        plt.legend()
        plt.grid(axis="y", alpha=0.75)

        # plt.show() # Show the plot
        if pdfPagesObject:
            pdf.savefig()  # Save the current figure
        plt.clf()
        plt.close()

        # - output chart excel------------
    def outputChart_excel(
        data,
        chartTitle,
        workbook,
        sheet_name,
        bin_edges=np.arange(-2, 2.2, 0.05),  # At least 20, but max 100 for granularity
        plotSeaboneHistplot=False,
        pdfPagesObject=None,
        figsize=(10, 6),
        xrange=(-2, 2),
        coverage_values=None,
        historical_value08=None,
        historical_value09=None,
        crisis_percentile08=None,
        crisis_percentile09=None,
        relative_percentile08=None,
        relative_percentile09=None,
    ):
        fig, ax = plt.subplots(figsize=figsize)

        ax.hist(
            data,
            bins=bin_edges,
            range=(0, 1),
            color="blue",
            alpha=0.7,
            edgecolor="black",
        )

        # Calculate percentiles
        percentile_values = [data.quantile(p / 100) for p in percentiles_for_chart]

        for i, (perc, value) in enumerate(
            zip(percentiles_for_chart, percentile_values)
        ):
            color = "green" if i == 0 else "red"
            label_text = f"{perc}th Percentile: {value:.4f}"

            # if coverage_values is not None:
            #     cov = round(coverage_values[i]*100,1)
            #     label_text += f" | Coverage = {cov}%"

            ax.axvline(
                value,
                linestyle="--",
                color=color,
                linewidth=1.5,
                alpha=0.7,
                label=label_text,
            )

        if historical_value08 is not None:
            historical_value08 = historical_value08.mean()
            relative_percentile08 = relative_percentile08.mean()
            label_text = f"2008 delta opex/rev: {historical_value08:.4f}\n"
            if crisis_percentile08 is not None:
                crisis_percentile08 = crisis_percentile08.mean()
                label_text += f"(2008 historical percentile rank {crisis_percentile08: .4f}th perc)"
                label_text += f"(2008 relative percentile {relative_percentile08: .4f}%)"
            ax.axvline(
                historical_value08,
                color="orange",
                linestyle="-",
                linewidth=2,
                label=label_text,
            )
        if historical_value09 is not None:
            historical_value09 = historical_value09.mean()
            relative_percentile09 = relative_percentile09.mean()
            label_text = f"2009 delta opex/rev: {historical_value09:.4f}\n"
            if crisis_percentile09 is not None:
                crisis_percentile09 = crisis_percentile09.mean()
                label_text += f"(2009 historical percentile rank{crisis_percentile09: .4f}th perc)"
                label_text += f"(2009 relative percentile {relative_percentile09: .4f}%)"
            ax.axvline(
                historical_value09,
                color="yellow",
                linestyle="-",
                linewidth=2,
                label=label_text,
            )

        if xrange:
            # Set X-axis range
            ax.set_xlim(xrange[0], xrange[1])

        ax.set_title(chartTitle)
        ax.set_xlabel("Delta Opex/Revenue")
        ax.set_ylabel("Frequency")
        ax.legend(fontsize=8)
        ax.grid(axis="y", alpha=0.75)

        imgdata = BytesIO()
        fig.savefig(imgdata, format="png", bbox_inches="tight")
        plt.close(fig)
        imgdata.seek(0)

        ws = workbook.create_sheet(sheet_name[:31])
        img = Image(imgdata)
        ws.add_image(img, "B2")

    # ----------------
    # Load data
    financials = pd.read_csv(fin_file_path).iloc[:, 1:]
    if not dampned_for_revenue_outlier:
        financials = revenue_adjustment(financials.copy())
    else:
        pass
    isic_data = pd.read_excel(isic_file_path)

    financials["country_of_risk"] = financials["country_of_risk"].str.upper()

    # ISI
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

            #  map sub_segment in non-global case
            financials["sub_segment"] = (
                financials["isic_code"].map(subseg_map).fillna("NA")
            )
            financials = financials[financials["RA_Industry"] == sector]
            if sub_segment_case:
                financials["sub_segment"] = financials["sub_segment"].str.title()
    else:
        financials = financials[financials["RA_Industry"] == sector]

    # Filter: Keep only data from the desired sector

    ##############################################

    if groupCountry:
        reverse_country_map = {}
        for group_label, countries in country_group_mapping.items():
            for country in countries:
                reverse_country_map[country] = group_label
        financials["country_of_risk_grouped"] = financials["country_of_risk"].apply(
            lambda x: reverse_country_map.get(x, x)
        )

    if groupSector:
        reverse_country_map = {}
        for group_label, countries in country_group_mapping.items():
            for country in countries:
                reverse_country_map[country] = group_label

        financials["sub_segment_group"] = financials["sub_segment"].apply(
            lambda x: reverse_country_map.get(x, x)
        )

    ########################################
    # for MM
    if sub_segment_replacement_dict:
        financials.replace(
            {sub_segment_column_name: sub_segment_replacement_dict}, inplace=True
        )
    financials[sub_segment_column_name] = financials[sub_segment_column_name].fillna(
        "Others"
    )

    # Apply the function to create the new column --this is for Commodity Trader Only
    if sub_segment_function:
        financials[sub_segment_column_name] = (
            financials["isic_code"].map(sub_segment_mapping).fillna("Others")
        )

    # filterout the sub_segment ==Not applicable, these setting are for Automobile/Consumer Durable/Tech
    if exclude_sub_na:
        financials = financials[financials["sub_segment"] != "Not applicable"]

    if sector_name == "Consumer Durables & Apparel":
        financials["sub_segment"] = financials["sub_segment"].str.upper()

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

    ##########################################

    financials[id_column_name] = financials[id_column_name].astype(str)

    financials["DATE_OF_FINANCIALS"] = pd.to_datetime(financials["DATE_OF_FINANCIALS"])
    financials["Year"] = financials["DATE_OF_FINANCIALS"].dt.year
    financials["Month"] = financials["DATE_OF_FINANCIALS"].dt.month

    # ----------------
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
    financials["SLS_REVENUES"] = financials["SLS_REVENUES"].astype(
        float
    )  # this is needed due to a row with a string "0.0"
    financials = financials[financials["SLS_REVENUES"] != 0]
    summary_4 = summarize_step(
        financials,
        top_segments,
        sub_segment_column_name,
        includeOthers,
        step_name="Step 4: Data after dropping Revenue 0",
    )

    financials["Opex"] = financials["Opex"].replace("Missing", None)
    financials["Opex"] = financials["Opex"].replace("Not applicable", None)

    financials["Opex"] = financials["Opex"].astype(float)

    # ----------------
    financials["Opex/Revenue"] = (financials["Opex"]) / (financials["SLS_REVENUES"])

    if includeZeroOpex:
        financials = financials[financials["Opex/Revenue"] >= 0]
    else:
        financials = financials[financials["Opex/Revenue"] > 0]

    summary_5 = summarize_step(
        financials,
        top_segments,
        sub_segment_column_name,
        includeOthers,
        step_name="Step 5: Data after keeping only OPEX/REVENUE > 0",
    )

    # ----------------
    # Counting the rows with NA values in column 'Opex/Revenue'
    na_rows = financials["Opex/Revenue"].isna().sum()

    leid_dropped = financials.loc[
        financials["Opex/Revenue"].isna() | financials["SLS_REVENUES"].isna(),
        id_column_name,
    ].nunique()

    Opex = financials.dropna(subset=["Opex/Revenue", "SLS_REVENUES"])

    summary_6 = summarize_step(
        Opex,
        top_segments,
        sub_segment_column_name,
        includeOthers,
        step_name="Step 6: Data after dropping 'Opex/Revenue' or Revenue NA",
    )

    # print(f"Number of rows dropped due to NA: {na_rows}")
    # print(f"Number of unique leid dropped due to NA: {leid_dropped}")
    # print(f"shape before drop NA: {financials.shape}")
    # print(f"shape after drop NA: {Opex.shape}")

    # - remove quarter data points and only leave annual data ------------------- # This is happening in Financials script already
    Opex = Opex.sort_values(
        by=[id_column_name, "Year", "Month"], ascending=[True, True, False]
    )
    Opex_end = Opex.drop_duplicates(subset=[id_column_name, "Year"], keep="first")
    # print(f"shape before drop the quarterly data': {Opex.shape}")
    # print(f"shape af drop the quarterly data': {Opex.shape}")

    summary_7 = summarize_step(
        Opex,
        top_segments,
        sub_segment_column_name,
        includeOthers,
        step_name="Step 7: Data after removing duplicates by spread_id and Date",
    )

    # --------------------
    # Drop rows with inf values in 'Opex/Revenue'
    Opex_clean = Opex_end[~Opex_end["Opex/Revenue"].isin([float("inf")])]

    summary_8 = summarize_step(
        Opex_clean,
        top_segments,
        sub_segment_column_name,
        includeOthers,
        step_name="Step 8: Data after removing inf values in 'Opex/Revenue'",
    )
    summary_9 = summarize_step(
        Opex_clean,
        top_segments,
        sub_segment_column_name,
        includeOthers,
        step_name="Step 9: Final modelling data",
    )

    # Opex_clean.to_excel(fr"{DATA_DIR}/03. Model/{sector_name}/03. Opex\OPEX_{sector_short}_Modelling_data.xlsx")

    # Apply function to each leid with chosen change type ------------------------
    change_type = "relative"  # take the relative change
    Opex_clean_rel = Opex_clean.groupby(id_column_name, group_keys=False).apply(
        lambda x: compute_delta(x, change=change_type)
    )

    # Opex_clean_rel.to_excel(fr"{DATA_DIR}/03. Model/{sector_name}/03. Opex/OPEX_{sector_short}_Modelling_delta_OPEX.xlsx")
    # - Compute chart of aggregated segments after dampening consistent dampened data points ---------------
    if computeChartAggregatedSegments:
        # Drop NaN values from delta_opex/rev before filtering
        filtered_data = Opex_clean_rel["delta_opex/rev"].dropna()

        # Check min/max and unique value count after filtering
        # print(f"Min value after removing NA: {filtered_data.min()}")
        # print(f"Max value after removing NA: {filtered_data.max()}")
        # print(f"Number of unique values: {filtered_data.nunique()}")

        chartTitle = (
            f"Distribution of Relateive Delta Opex/Revenue without Dampner ({sector})"
        )
        outputChart(filtered_data, chartTitle, plotSeaboneHistplot=True)

    Opex_clean_rel_exclude = Opex_clean_rel.copy()

    Opex_clean_rel_exclude["TOPS"] = np.where(
        Opex_clean_rel_exclude[sub_segment_column_name].isin(top_segments),
        Opex_clean_rel_exclude[sub_segment_column_name],
        "Others",
    )

    if includeOthers:
        top_segments += ["Others"]

    # - Apply dampeners ---------------------
    if applyingDampener:
        # Ensure 'Date' and 'DATE_OF_FINANCIALS' are in datetime format (if not already)
        if dampned_for_revenue_outlier:
            if exclusion_file_path.endswith("xlsx"):
                exclude = pd.read_excel(exclusion_file_path)
            elif exclusion_file_path.endswith("csv"):
                exclude = pd.read_csv(exclusion_file_path)
            else:
                raise ValueError("Invalid file type for exclusion data")
            dampner_val = 0.0001
        else:
            if exclusion_file_path_gen2.endswith("xlsx"):
                exclusion = pd.read_excel(
                    exclusion_file_path_gen2, sheet_name="Outlier Panel Data"
                )
            elif exclusion_file_path_gen2.endswith("csv"):
                exclusion = pd.read_csv(exclusion_file_path_gen2)
            else:
                raise ValueError("Invalid file type for exclusion data")
            exclude = exclusion[exclusion["outlier_weight"] == 0.00001]
            dampner_val = 1
        # Ensure 'Date' and 'DATE_OF_FINANCIALS' are in datetime format (if not already)
        exclude["Date"] = pd.to_datetime(exclude["Date"])
        Opex_clean_rel_exclude["DATE_OF_FINANCIALS"] = pd.to_datetime(
            Opex_clean_rel_exclude["DATE_OF_FINANCIALS"]
        )

        exclude[id_column_name] = exclude[id_column_name].astype(str)

        # Create a set of (Date, spread_id) tuples for fast lookup
        exclude_set = set(zip(exclude["Date"], exclude[id_column_name]))

        # Step 1: First dampener - based on exclude set
        # ----------------------------------------------
        # Track how many rows are dampened by first condition
        dampened_first = Opex_clean_rel_exclude.loc[
            Opex_clean_rel_exclude[["DATE_OF_FINANCIALS", id_column_name]]
            .apply(tuple, axis=1)
            .isin(exclude_set)
        ]
        num_dampened_first = len(dampened_first)

        # Create mask where (DATE_OF_FINANCIALS, id_column_name) matches exclude_set
        dampening_mask = (
            Opex_clean_rel_exclude[["DATE_OF_FINANCIALS", id_column_name]]
            .apply(tuple, axis=1)
            .isin(exclude_set)
        )
        dampening_n = dampening_mask.sum()

        dampened_segments = Opex_clean_rel_exclude.loc[dampening_mask, "TOPS"]
        # Count number of dampened rows per unique sub-segment
        dampened_counts = dampened_segments.value_counts()

        #  Apply transformation where both DATE_OF_FINANCIALS and spread_id exist in exclude (multiply by 0.01)
        Opex_clean_rel_exclude.loc[
            Opex_clean_rel_exclude[["DATE_OF_FINANCIALS", id_column_name]]
            .apply(tuple, axis=1)
            .isin(exclude_set),
            "delta_opex/rev",
        ] *= dampner_val

        # Step 2: Prepare for second dampener by segment
        # ----------------------------------------------
        # Calculate {int(100*(step_2_quantile))}th percentile per segment
        def shrink_value(row):
            segment = row["TOPS"]
            # Only shrink if value > percentile, and not already excluded in first dampener
            if (
                row["DATE_OF_FINANCIALS"],
                row[id_column_name],
            ) not in exclude_set and row["delta_opex/rev"] > percentile_dict[segment]:
                counter["total_shrunk"] += 1
                counter[segment] += 1
                return row["delta_opex/rev"] * 0.0001
            return row["delta_opex/rev"]

        percentile_dict = {}
        for segment in Opex_clean_rel_exclude["TOPS"].unique():
            segment_mask = Opex_clean_rel_exclude["TOPS"] == segment
            if dampenerPercentileBySegment:
                percentile_dict[segment] = Opex_clean_rel_exclude.loc[
                    segment_mask, "delta_opex/rev"
                ].quantile(step_2_quantile)
            else:
                percentile_dict[segment] = Opex_clean_rel_exclude[
                    "delta_opex/rev"
                ].quantile(step_2_quantile)

        # Step 3: Second dampener with per-segment stats
        # ----------------------------------------------
        # Counter to store total and per-segment shrunk counts
        counter = {"total_shrunk": 0}
        for c in Opex_clean_rel_exclude["TOPS"].unique():
            counter[c] = 0

        # Apply shrink logic
        if dampned_for_revenue_outlier:
            Opex_clean_rel_exclude["delta_opex/rev"] = Opex_clean_rel_exclude.apply(
                shrink_value, axis=1
            )
        else:
            for subSector in Opex_clean_rel_exclude.TOPS.unique():
                subSector_ = subSector.replace(" ", "_")
                globals()[f"final{subSector_}"] = Opex_clean_rel_exclude[
                    Opex_clean_rel_exclude["TOPS"] == subSector
                ]
                quantile_value = globals()[f"final{subSector_}"][
                    "delta_opex/rev"
                ].quantile(step_2_quantile)
                globals()[f"final{subSector_}"][
                    f"winsorised as top{int(100*(1-step_2_quantile))}"
                ] = (globals()[f"final{subSector_}"]["delta_opex/rev"] > quantile_value)
                globals()[f"final{subSector_}"]["delta_opex/rev"] = globals()[
                    f"final{subSector_}"
                ]["delta_opex/rev"].clip(
                    upper=quantile_value,
                )
                counter[subSector] = globals()[f"final{subSector_}"][
                    f"winsorised as top{int(100*(1-step_2_quantile))}"
                ].sum()
                counter["total_shrunk"] += globals()[f"final{subSector_}"][
                    f"winsorised as top{int(100*(1-step_2_quantile))}"
                ].sum()
            Opex_clean_rel_exclude = pd.concat(
                [finalCT_Chemicals, finalCT_Energy, finalOthers, finalCT_Metal],
                axis=0,
                ignore_index=True,
            )
            Opex_clean_rel_exclude["winsorised from revenue model"] = (
                Opex_clean_rel_exclude["outlier_weight"] == 0.00001
            )
        # Step 4a: Convert shrink counter into DataFrame
        shrink_summary_df = pd.DataFrame(
            [
                {
                    "TOPS": seg,
                    f"Outliers {int(100*(step_2_quantile))}th Percentile": val,
                }
                for seg, val in counter.items()
                if seg != "total_shrunk"
            ]
        )

        # Optionally add total as a row
        shrink_summary_df = pd.concat(
            [
                shrink_summary_df,
                pd.DataFrame(
                    [
                        {
                            "TOPS": "TOTAL",
                            f"Outliers {int(100*(step_2_quantile))}th Percentile": counter[
                                "total_shrunk"
                            ],
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )

        # Step 4b: Print statistics
        # ----------------------------------------------
        # print(
        #     f"\nStep 1: Number of data points dampened by exclude_set: {num_dampened_first}"
        # )
        # print(
        #     f"Step 2: Number of data points dampened by percentile shrink: {counter['total_shrunk']}"
        # )
        # print("\nPer-segment shrink counts:")
        # for c in percentile_dict.keys():
        #     print(f"{c}: {counter[c]}")

    # - consider additional category -----------------
    if useAdditionalCategory:
        outputAddCats = [False, True]
    else:
        outputAddCats = [False]

    # - excel / chart output loop over additional category -----------------
    def additionalCategorizationFunction(data):
        def mapping(x): return "Producer" if x in {2200, 2203} else "Others"
        return data["isic_code"].map(mapping).fillna("Others")

    for outputAddCat in outputAddCats:
        Opex_clean_rel_exclude_add_cat = Opex_clean_rel_exclude.copy()
        if outputAddCat:
            Opex_clean_rel_exclude_add_cat[additionalCategoryColumnName] = (
                additionalCategorizationFunction(Opex_clean_rel_exclude_add_cat)
            )

        # Create an empty list to collect data
        result_data_full = []

        # Calculate metrics for each segment and additional category
        for top_segment in top_segments:
            for addCat in additionalCategories if outputAddCat else [None]:
                # filter opex data per segment and additional category if any
                if addCat:
                    mask = (Opex_clean_rel_exclude_add_cat["TOPS"] == top_segment) & (
                        Opex_clean_rel_exclude_add_cat[additionalCategoryColumnName]
                        == addCat
                    )
                else:
                    mask = Opex_clean_rel_exclude_add_cat["TOPS"] == top_segment
                subset = Opex_clean_rel_exclude_add_cat[mask]

                # Calculate unique ID count
                unique_spread_id = subset[id_column_name].nunique()

                # Calculate percentiles
                percentile_values = (
                    subset["delta_opex/rev"]
                    .quantile([p / 100 for p in percentiles_for_file])
                    .values
                )

                # Calculate stress impacts
                stresses = np.array(percentile_values[1:]) - percentile_values[0]

                data_points = len(subset)

                # Crisis data 2008-2009
                crisis_data2008 = subset[subset["Year"].isin([2008])]
                crisis_data2009 = subset[subset["Year"].isin([2009])]
                x_crisis_08 = crisis_data2008["delta_opex/rev"].mean()
                x_crisis_09 = crisis_data2009["delta_opex/rev"].mean()
                model_data = subset["delta_opex/rev"]

                # the actual percentile rank
                percentile_rank_08 = (model_data <= x_crisis_08).mean()
                percentile_rank_09 = (model_data <= x_crisis_09).mean()
                tail_prob_08 = 1 - percentile_rank_08
                tail_prob_09 = 1 - percentile_rank_09
                return_period_08 = 1/tail_prob_08 if tail_prob_08 > 0 else np.inf
                return_period_09 = 1/tail_prob_09 if tail_prob_08 > 0 else np.inf

                # the percentile in current distribution percentile
                percentile_08 = np.interp(x_crisis_08, percentile_values, percentiles_for_file)
                percentile_08 = np.clip(percentile_08, percentiles_for_file[0], percentiles_for_file[-1])
                percentile_09 = np.interp(x_crisis_09, percentile_values, percentiles_for_file)
                percentile_09 = np.clip(percentile_09, percentiles_for_file[0], percentiles_for_file[-1])

                # MAE MSE global financial crisis
                target_perc = 96  # 1in25 scenario severity
                target_idx = np.abs(np.array(percentiles_for_file) - target_perc).argmin()
                forecasted_stress = percentile_values[target_idx] - percentile_values[0]
                crisis_data_clean_2008 = crisis_data2008["delta_opex/rev"].dropna()
                crisis_data_clean_2009 = crisis_data2009["delta_opex/rev"].dropna()
                if len(model_data) == 0:
                    mae_2008, mse_2008, mae_2009, mse_2009 = None, None
                else:
                    mae_2008 = mean_absolute_error(crisis_data_clean_2008, [forecasted_stress]*len(crisis_data_clean_2008))
                    mse_2008 = mean_squared_error(crisis_data_clean_2008, [forecasted_stress]*len(crisis_data_clean_2008))
                    mae_2009 = mean_absolute_error(crisis_data_clean_2009, [forecasted_stress]*len(crisis_data_clean_2009))
                    mse_2009 = mean_squared_error(crisis_data_clean_2009, [forecasted_stress]*len(crisis_data_clean_2009))

                # Calculate quantile loss
                actual = subset["delta_opex/rev"]
                coverage = {
                    stress_level: (actual <= stress_level).mean()
                    for stress_level in percentile_values[1:]
                }
                exception_rate = {
                    stress_level: (actual > stress_level).mean()
                    for stress_level in percentile_values[1:]
                }
                coverage_list = [coverage[stress_lvl] for stress_lvl in percentile_values[1:]]
                exception_list = [exception_rate[stress_lvl] for stress_lvl in percentile_values[1:]]

                # Append the data to the result list
                result_data_full.append(
                    [top_segment]
                    + (
                        [addCat] if outputAddCat else []
                    )  # output additional category only if outputAddCat is True
                    + [
                        unique_spread_id,
                        data_points,
                        *percentile_values,  # Expand percentile values into individual columns
                        *stresses,
                        *coverage_list,
                        *exception_list,
                        x_crisis_08,
                        x_crisis_09,
                        percentile_rank_08,
                        percentile_rank_09,
                        percentile_08,
                        percentile_09,
                        mae_2008,
                        mse_2008,
                        mae_2009,
                        mse_2009,
                    ]
                )

        # Define column names for the result dataframe
        # convert percentiles to string: 33.333... --> 33.33, 66.6666... --> 66.67, 50.0 --> 50, 97.50 --> 97.5
        percentiles_str = [f"{p:.2f}".rstrip("0").rstrip(".") for p in percentiles_for_file]
        stress_impact_columns = [
            "Stress Impact - " + ps + "th Perc" for ps in percentiles_str[1:]
        ]
        stress_percentiles_str = percentiles_str[1:]
        coverage_columns = [f"Coverage - {ps}th Perc" for ps in stress_percentiles_str]
        exception_columns = [f"Exception - {ps}th Perc" for ps in stress_percentiles_str]
        crisis_columns = ["Historical 2008", "Historical 2009", "Historical Percentile 2008", "Historical Percentile 2009", "Relative Percentile 2008", "Relative Percentile 2009"]
        error_columns = ["MAE - financial crisis08", "MSE - financial crisis08", "MAE - financial crisis09", "MSE - financial crisis09"]

        columns = (
            ["TOPS"]
            + (
                [additionalCategoryColumnName] if outputAddCat else []
            )  # output only if outputAddCat is True
            + [
                f'Unique {"LEID" if id_column_name.upper() == "LEID" else "Spread_ID"}s',
                "Data Points",
                *[ps + "th Perc" for ps in percentiles_str],
                *stress_impact_columns,
                *coverage_columns,
                *exception_columns,
                *crisis_columns,
                *error_columns,
            ]
        )

        # Create a dataframe from the result data
        result_df = pd.DataFrame(result_data_full, columns=columns)
        result_df = result_df.reset_index(drop=True)
        result_df.to_excel(
            full_result_file_additional_category_path
            if outputAddCat
            else full_result_file_path
        )

        # - Stress date ----------------------------------------------
        segmentColumn = "Country" if segmentByCountry else "Sub-sector"
        if outputAddCat:
            result_st_df = pd.melt(
                result_df,
                id_vars=["TOPS", additionalCategoryColumnName],
                value_vars=stress_impact_columns,
            )
        else:
            result_st_df = pd.melt(
                result_df, id_vars=["TOPS"], value_vars=stress_impact_columns
            )

        coverage_df = pd.melt(
            result_df,
            id_vars=["TOPS"] + ([additionalCategoryColumnName] if outputAddCat else []),
            value_vars=coverage_columns,
        )
        exception_df = pd.melt(
            result_df,
            id_vars=["TOPS"] + ([additionalCategoryColumnName] if outputAddCat else []),
            value_vars=exception_columns,
        )

        def normalize_var(x):
            x.split("-")[-1].strip if "-" in x else x.split("-", 1)[-1].strip()
            return str(x)

        def extract_perc_key(col):
            return col.split("-")[-1].strip()

        for df in (result_st_df, coverage_df, exception_df):
            df["variable"] = df["variable"].apply(normalize_var)
            df["perc_key"] = df["variable"].apply(extract_perc_key)

        coverage_df = coverage_df.rename(columns={"value": "coverage"})
        exception_df = exception_df.rename(columns={"value": "exception_rate"})

        id_vars = ["TOPS"] + ([additionalCategoryColumnName] if outputAddCat else [])
        result_st_df = (
            result_st_df
            .merge(coverage_df.drop(columns=["variable"]), on=id_vars + ["perc_key"])
            .merge(exception_df.drop(columns=["variable"]), on=id_vars + ["perc_key"])
        )

        assert result_st_df["perc_key"].notna().all()
        assert (
            result_st_df.groupby(id_vars)["perc_key"].nunique() == len(stress_impact_columns)
        ).all()

        crisis_df = result_df[["TOPS", "Historical 2008", "Historical Percentile 2008", "Historical 2009",
                               "Historical Percentile 2009", "Relative Percentile 2008", "Relative Percentile 2009"]]
        result_st_df = result_st_df.merge(crisis_df, on="TOPS", how="left")
        error_df = result_df[["TOPS", "MAE - financial crisis08", "MSE - financial crisis08", "MAE - financial crisis09", "MSE - financial crisis09"]]
        result_st_df = result_st_df.merge(error_df, on="TOPS", how="left")

        result_st_df = result_st_df.rename(
            columns={
                "TOPS": segmentColumn,
                "variable": "Stress Impact - percentile",
                "value": "Stress Impact",
            }
        )

        # extract percentile from "Stress Impact - percentile" only for sorting
        result_st_df["Percentile"] = result_st_df["Stress Impact - percentile"].apply(
            lambda x: x.split("-")[1].strip().split(" ")[0] if "Stress" in x else "-"
        )
        result_st_df["Percentile"] = result_st_df["Percentile"].str[:-2]
        if outputAddCat:
            result_st_df = result_st_df.sort_values(
                by=[segmentColumn, additionalCategoryColumnName, "Percentile"],
                ascending=[False, True, True],
            )
        else:
            result_st_df = result_st_df.sort_values(
                by=[segmentColumn, "Percentile"], ascending=[False, True]
            )

        lenDF = len(result_st_df)
        pctiles_for_1_in_x = percentiles_for_file[1:]  # need to skip 50%tile
        lenPercTile = len(pctiles_for_1_in_x)
        if lenDF % lenPercTile != 0:
            raise ValueError(
                f"Total number of rows {lenDF} should be a multiple of number of percentiles except base 50%tile {lenPercTile}"
            )
        if not outputAddCat:

            nRepeat_for_subsegment = lenDF // lenPercTile  # integer division
            nRepeat_for_additionalCat = 1
        else:
            nAdditionalCategories = len(additionalCategories)
            nRepeat_for_subsegment = (
                lenDF // lenPercTile // nAdditionalCategories
            )  # integer division
            nRepeat_for_additionalCat = nAdditionalCategories
        severity_1_in_x = [
            round(100.0 / (100.0 - p), 1)
            for _ in range(nRepeat_for_additionalCat)
            for p in pctiles_for_1_in_x
        ] * nRepeat_for_subsegment

        result_st_df["Driver"] = "OPEX"

        result_st_df["Scenario Severity (1 in x)"] = severity_1_in_x
        current_date = datetime.now().strftime("%Y-%m-%d")
        result_st_df["As of Date"] = current_date
        result_st_df["Sector"] = sector
        if segmentByCountry:
            result_st_df["Sub-sector"] = "-"
        else:
            result_st_df["Country"] = "-"
        new_column_order = (
            [
                "Driver",
                "Stress Impact - percentile",
                "Scenario Severity (1 in x)",
                "Sector",
                "Sub-sector",
            ]
            + ([additionalCategoryColumnName] if outputAddCat else [])
            + ["Country", "Stress Impact", "As of Date", "coverage", "exception_rate",
               "Historical 2008", "Historical Percentile 2008", "Historical 2009", "Historical Percentile 2009", "Relative Percentile 2008", "Relative Percentile 2009",
               "MAE - financial crisis08", "MSE - financial crisis08", "MAE - financial crisis09", "MSE - financial crisis09"]
        )
        result_st_df = result_st_df[new_column_order]
        result_st_df = result_st_df.sort_values(
            by=[segmentColumn, "Scenario Severity (1 in x)"], ascending=[False, True]
        )
        result_st_df = result_st_df.reset_index(drop=True)
        # if additionalCategoryColumnNameToOutputFile is not equal to additionalCategoryColumnName, replace
        if outputAddCat:
            if additionalCategoryColumnNameToOutputFile != additionalCategoryColumnName:
                result_st_df[additionalCategoryColumnNameToOutputFile] = result_st_df[
                    additionalCategoryColumnName
                ]
                result_st_df = result_st_df.drop(additionalCategoryColumnName, axis=1)

        # result_st_df.to_excel(
        #     stress_result_file_path
        #     if not outputAddCat
        #     else stress_result_file_additional_category_path
        # )

        # - output chart -----------------------------------------------
        # currently, only for a case without additional category
        # from matplotlib.backends.backend_pdf import PdfPages

        # # Create a PdfPages object to save multiple plots
        # chart_pdf_file_name = (
        #     pdf_path if not outputAddCat else pdf_additional_category_path
        # )
        # with PdfPages(chart_pdf_file_name) as pdf:
        #     for top_segment in top_segments:
        #         for addCat in additionalCategories if outputAddCat else [None]:
        #             # filter opex data per segment and additional category if any
        #             if addCat:
        #                 mask = (
        #                     Opex_clean_rel_exclude_add_cat["TOPS"] == top_segment
        #                 ) & (
        #                     Opex_clean_rel_exclude_add_cat[additionalCategoryColumnName]
        #                     == addCat
        #                 )
        #             else:
        #                 mask = Opex_clean_rel_exclude_add_cat["TOPS"] == top_segment
        #             subset = Opex_clean_rel_exclude_add_cat[mask]
        #             # subset =  Opex_clean_rel_exclude_add_cat[Opex_clean_rel_exclude_add_cat[sub_segment_column_name] == top_segment]
        #             unique_leids = subset[id_column_name].nunique()
        #             segmentNameForChart = (
        #                 "Country" if segmentByCountry else "Sub-sector"
        #             )
        #             if addCat:
        #                 segmentNameForChart += " (" + addCat + ")"
        #             chartTitle = f"Distribution of Delta Opex/Revenue for {segmentNameForChart}: {top_segment}\nNumber of Unique Spread IDs: {unique_leids}"
        #             outputChart(
        #                 subset["delta_opex/rev"],
        #                 chartTitle,
        #                 bin_edges=100,
        #                 pdfPagesObject=pdf,
        #                 figsize=(8, 6),
        #                 xrange=None,
        #             )
        #     # Optional: Print confirmation
        #     print(f"All plots have been saved to {chart_pdf_file_name}")

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

    dampening_summary = pd.DataFrame(dampened_counts).reset_index()
    dampening_summary.columns = ["Sub-Segment", "Exclusions from Revenue Model"]
    total_row = pd.DataFrame(
        [["TOTAL", dampening_n]],
        columns=["Sub-Segment", "Exclusions from Revenue Model"],
    )
    dampening_summary = pd.concat([dampening_summary, total_row], ignore_index=True)

    # Define output path
    datapoints_wide = datapoints_wide.rename(
        columns={col: f"datapoints_{col}" for col in datapoints_wide.columns}
    )
    spread_ids_wide = spread_ids_wide.rename(
        columns={col: f"spreadIDs_{col}" for col in spread_ids_wide.columns}
    )
    DataStats = pd.concat([datapoints_wide, spread_ids_wide], axis=1)
    Opex_clean_rel_exclude_add_cat = Opex_clean_rel_exclude_add_cat.rename(
        columns={
            "y": "Rev_Chg",
            "y_winsor": "Rev_Chg_winzorised",
            "TOPS": "country/subsector",
        }
    )
    Opex_clean_rel_exclude_add_cat["Sector"] = sector
    with pd.ExcelWriter(sum_path, engine="openpyxl") as writer:
        DataStats.to_excel(writer, sheet_name="DataStats")
        dampening_summary.to_excel(
            writer, sheet_name="Exclusions from Revenue Model", index=False
        )
        shrink_summary_df.to_excel(
            writer,
            sheet_name=f"Outliers {int(100*(step_2_quantile))}th Perc",
            index=False,
        )
        Opex_clean_rel_exclude_add_cat[
            [
                "Sector",
                "country/subsector",
                "DATE_OF_FINANCIALS",
                "spread_id",
                "scorecard_type",
                "SLS_REVENUES",
                "Prev_Rev",
                "Revenue_Change",
                "Opex",
                "Opex_Change",
                "Opex/Revenue",
                "delta_opex/rev",
                "Rev_Chg",
                "Rev_Chg_winzorised",
                "winsorised as top1",
                "winsorised from revenue model",
            ]
        ].to_excel(writer, sheet_name="Outlier Panel data", index=False)
        result_df.to_excel(writer, sheet_name="Stress Impacts Full data", index=False)
        result_st_df.to_excel(writer, sheet_name="Stress Impacts", index=False)

        # add charts in excel --------------------------------------------------------------------------
        wb = writer.book
        sub_sectors = result_st_df["Sub-sector"].unique()
        for sub_sec in sub_sectors:
            mask = (
                (Opex_clean_rel_exclude_add_cat["country/subsector"] == sub_sec)
            )
            subset = Opex_clean_rel_exclude_add_cat[mask]

            if subset.empty:
                continue
            unique_ids = subset["spread_id"].nunique()

            chartTitle = (
                f"Distribution for {sub_sec}\n"
                f"Number of spread_ids: {unique_ids}"
            )
            sec_df = result_st_df[result_st_df["Sub-sector"] == sub_sec]

            outputChart_excel(
                data=subset["delta_opex/rev"],
                chartTitle=chartTitle,
                # bin_edges=100,
                workbook=wb,
                sheet_name=f"{sub_sec}_chart",
                # coverage_values = result_st_df["coverage"],
                historical_value08=sec_df["Historical 2008"],
                crisis_percentile08=sec_df["Historical Percentile 2008"],
                relative_percentile08=sec_df["Relative Percentile 2008"],
                historical_value09=sec_df["Historical 2009"],
                crisis_percentile09=sec_df["Historical Percentile 2009"],
                relative_percentile09=sec_df["Relative Percentile 2009"],
                xrange=None,
            )
    print("export to excel completed!!")


# ---------------------------------------------------------------------------------------------------


if __name__ == "__main__":
    for sector in [
        # "O&G",
        "Commodity Traders",
        # "Metals & Mining",
        # "Automobiles & Components",
        # "Consumer Durables & Apparel",
        # "Technology Hardware & Equipment",
        # "Building Products, Construction & Engineering",
        # "CRE",
        # "Other Capital Goods",
        # "Transportation and Storage",
        # "Global",
    ]:
        Opex(sector)
        sys.stdout = TimestampLog("Opex_master")
