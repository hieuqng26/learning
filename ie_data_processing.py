import pandas as pd
import numpy as np


# ============================================================================
# MEV & INTEREST DATA HELPERS
# ============================================================================


def summarize_step(df, top_countries_1, c_column_name, step_name, id_column_name="spread_id"):
    """Summarize entity and data point counts by region for a given filtering step."""
    financials = df.copy()

    region_list = top_countries_1 + ["Others"]
    financials["__region__"] = financials[c_column_name].apply(
        lambda x: x if x in top_countries_1 else "Others"
    )

    summary = []
    for region in region_list:
        df_region = financials[financials["__region__"] == region]
        counts = df_region["Portfolio"].value_counts()
        summary.append(
            {
                "Step": step_name,
                "Region": region,
                "Unique spread IDs": df_region[id_column_name].nunique(),
                "Total datapoints": df_region.shape[0],
                "LC+CC datapoints": counts.get("LC", 0) + counts.get("CC", 0),
                "MC datapoints": counts.get("MC", 0),
            }
        )

    return pd.DataFrame(summary)


def MEV_data_processing(country, MEVdata):
    """Return the 4-quarter moving average of the central bank rate for `country` from 2018 onward."""
    MEVdata_interest_rate = MEVdata[
        ["Date", f"{country}_Monetary policy or key interest rate"]
    ].copy()
    MEVdata_interest_rate = MEVdata_interest_rate[
        MEVdata_interest_rate["Date"] >= "2018-01-01"
    ]
    MEVdata_interest_rate["Date"] = pd.to_datetime(
        MEVdata_interest_rate["Date"], format="%Y-%m-%d"
    )
    MEVdata_interest_rate["Year"] = MEVdata_interest_rate["Date"].apply(
        lambda x: x.year
    )
    MEVdata_interest_rate[
        f"{country}_Monetary policy or key interest rate_4QMA"
    ] = (
        MEVdata_interest_rate[f"{country}_Monetary policy or key interest rate"]
        .rolling(window=4)
        .mean()
        / 100
    )

    return MEVdata_interest_rate


def process_data_country_sector(
    interest_data,
    MEVdata,
    country,
    sector,
    aggregate,
    id_column_name,
    int_expense_issue,
):
    """Merge entity interest data with central bank rate data for a given country and sector.

    Filters to entities with at least 4 observations (when not in aggregate mode).
    Returns a merged DataFrame ready for correlation/sensitivity calculation.
    """
    if sector == "Global":
        interest_data = interest_data[((interest_data.country_of_risk == country))]
    else:
        interest_data = interest_data[
            (
                (interest_data.RA_Industry == sector)
                & (interest_data.country_of_risk == country)
            )
        ]

    # Always fetch US central bank rate as a fallback
    MEVdata_groupby_US = MEV_data_processing("US", MEVdata)
    MEVdata_groupby_US = MEVdata_groupby_US.rename(
        columns={
            "US_Monetary policy or key interest rate_4QMA": "Monetary policy or key interest rate_4QMA_US"
        }
    )

    country_data_available_flag = 0
    try:
        MEVdata_groupby = MEV_data_processing(country, MEVdata)
    except Exception:
        # Central bank data for this country is not available; fall back to US rate
        MEVdata_groupby = MEVdata_groupby_US
        country_data_available_flag = 1

    interest_data["DATE_OF_FINANCIALS"] = pd.to_datetime(
        interest_data["DATE_OF_FINANCIALS"], format="%Y-%m-%d"
    )

    final = pd.merge(
        interest_data,
        MEVdata_groupby,
        left_on="DATE_OF_FINANCIALS",
        right_on="Date",
    )

    if country_data_available_flag == 1:
        final[f"{country}_Monetary policy or key interest rate_4QMA"] = np.nan
    else:
        final = pd.merge(
            final,
            MEVdata_groupby_US,
            left_on="DATE_OF_FINANCIALS",
            right_on="Date",
        )

    if not aggregate:
        # Require at least 4 data points per entity for a stable regression
        leid_counts = final.groupby(id_column_name).size()
        leid_wanted = leid_counts[leid_counts > 3].index
        error_df = final[~final[id_column_name].isin(leid_wanted)]
        final = final[final[id_column_name].isin(leid_wanted)]
        error_df = pd.concat([error_df, int_expense_issue], ignore_index=True)
    return final


# ============================================================================
# MAIN DATA LOADING AND CLEANING PIPELINE
# ============================================================================


def load_and_clean_data(IE_config):
    """Load raw data, apply ISIC mapping, and run the 8-step cleaning pipeline.

    Returns:
        interest_data: fully filtered entity-level DataFrame (year >= 2018, rate <= 0.5)
        agg_interest_data: quarterly aggregated DataFrame
        summary_steps: list of 8 summary DataFrames (one per cleaning step)
        MEVdata: raw MEV DataFrame
        interest_data_df: interest data with interest_expense_issue flag column
        int_expense_issue: rows excluded because interest_rate > 0.5
    """
    sector = IE_config.sector
    id_column_name = IE_config.id_column_name
    ISIC_mapping = IE_config.ISIC_mapping
    exclude_IE_Zero = IE_config.exclude_IE_Zero
    globalmodel = IE_config.globalmodel
    groupCountry = IE_config.groupCountry
    country_group_mapping = IE_config.country_group_mapping
    sub_segment_filter_out = IE_config.sub_segment_filter_out
    global_exclude_sectors = IE_config.global_exclude_sectors
    c_column_name = IE_config.c_column_name
    top_countries = IE_config.top_countries

    interest_file_path = IE_config.interest_file_path
    MEV_file_path = IE_config.MEV_file_path
    isic_file_path = IE_config.isic_file_path

    if globalmodel:
        top_countries_1 = IE_config.top_countries_1
    else:
        top_countries_1 = top_countries

    # --- Load data ---
    interest_data = pd.read_csv(interest_file_path).iloc[:, 1:]
    MEVdata = pd.read_csv(MEV_file_path)
    isic_data = pd.read_excel(isic_file_path)

    # --- ISIC Code Mapping ---
    if ISIC_mapping:
        interest_data.rename(columns={"RA_Industry": "RA_Industry_Old"}, inplace=True)

        isic_map = isic_data.set_index("ISIC Code")[
            "Risk Industry_April 2025"
        ].to_dict()
        subseg_map = isic_data.set_index("ISIC Code")["Biz L1_Apr 2025.1"].to_dict()

        if globalmodel:
            interest_data["RA_Industry"] = (
                interest_data["isic_code"].map(isic_map).fillna("NA")
            )
            interest_data["sub_segment"] = (
                interest_data["isic_code"].map(subseg_map).fillna("NA")
            )
            interest_data = interest_data[
                ~interest_data["RA_Industry"].isin(global_exclude_sectors)
            ]
            interest_data = interest_data[interest_data["RA_Industry"] != "NA"]

        else:
            isic_data_filtered = isic_data[
                isic_data["Risk Industry_April 2025"] == sector
            ]
            interest_data["RA_Industry"] = np.where(
                interest_data["isic_code"].isin(
                    isic_data_filtered["ISIC Code"]
                ),
                sector,
                "Not Applicable",
            )
            interest_data["sub_segment"] = (
                interest_data["isic_code"].map(subseg_map).fillna("NA")
            )
            interest_data = interest_data[interest_data["RA_Industry"] == sector]

        interest_data = interest_data.drop(columns=["RA_Industry_Old"])

    else:
        interest_data = interest_data[interest_data["RA_Industry"] == sector]

    if sub_segment_filter_out:
        interest_data = interest_data[interest_data["sub_segment"] != "Not applicable"]

    if groupCountry:
        reverse_country_map = {}
        for group_label, countries in country_group_mapping.items():
            for country in countries:
                reverse_country_map[country] = group_label
            interest_data["country_of_risk_grouped"] = interest_data[
                "country_of_risk"
            ].apply(lambda x: reverse_country_map.get(x, x))
            interest_data.drop(columns=["country_of_risk"], inplace=True)
            interest_data.rename(
                columns={"country_of_risk_grouped": "country_of_risk"}, inplace=True
            )

    if globalmodel:
        reverse_country_map = {}
        for group_label, countries in country_group_mapping.items():
            for country in countries:
                reverse_country_map[country] = group_label
        interest_data["Region_group"] = interest_data["country_of_risk"].apply(
            lambda x: reverse_country_map.get(x, x)
        )

    # --- Clean and filter data ---
    interest_data["irb_ead"] = pd.to_numeric(interest_data["irb_ead"], errors="coerce")
    interest_data["InterestExpense"] = pd.to_numeric(
        interest_data["InterestExpense"].replace(["Missing", "Not applicable"], np.nan),
        errors="coerce",
    )
    interest_data["TotalDebt"] = pd.to_numeric(
        interest_data["TotalDebt"].replace(["Missing", "Not applicable"], np.nan),
        errors="coerce",
    )

    print("Rows before dropping NA:", len(interest_data))
    summary_1 = summarize_step(
        interest_data,
        top_countries_1,
        c_column_name,
        step_name="Step 1: Rows before dropping NA",
        id_column_name=id_column_name,
    )

    interest_data = interest_data.dropna(subset=["InterestExpense", "TotalDebt"])
    print("Rows after dropping NA:", len(interest_data))
    summary_2 = summarize_step(
        interest_data,
        top_countries_1,
        c_column_name,
        step_name="Step 2: Rows after dropping NA in InterestExpense and TotalDebt",
        id_column_name=id_column_name,
    )

    interest_data["DATE_OF_FINANCIALS"] = pd.to_datetime(
        interest_data["DATE_OF_FINANCIALS"]
    )
    interest_data["Year"] = interest_data["DATE_OF_FINANCIALS"].dt.year
    interest_data["Month"] = interest_data["DATE_OF_FINANCIALS"].dt.month

    interest_data = interest_data.sort_values(
        by=[id_column_name, "Year", "Month"], ascending=[True, True, False]
    )
    print(f"shape before dropping duplicate yearly data: {interest_data.shape}")
    interest_data = interest_data.drop_duplicates(
        subset=[id_column_name, "Year"], keep="first"
    )
    print(f"shape after dropping duplicate yearly data: {interest_data.shape}")

    summary_3 = summarize_step(
        interest_data,
        top_countries_1,
        c_column_name,
        step_name="Step 3: Rows after keep one data point for one year",
        id_column_name=id_column_name,
    )

    interest_data = interest_data[interest_data.irb_ead != 0]
    summary_4 = summarize_step(
        interest_data,
        top_countries_1,
        c_column_name,
        step_name="Step 4: Rows after filter irb!=0",
        id_column_name=id_column_name,
    )

    interest_data = interest_data[interest_data["TotalDebt"] != 0]
    summary_5 = summarize_step(
        interest_data,
        top_countries_1,
        c_column_name,
        step_name="Step 5: Rows after filter totaldebt!=0",
        id_column_name=id_column_name,
    )

    if exclude_IE_Zero:
        interest_data = interest_data[interest_data["InterestExpense"] != 0]

    summary_6 = summarize_step(
        interest_data,
        top_countries_1,
        c_column_name,
        step_name="Step 6: Rows after filter ie !=0",
        id_column_name=id_column_name,
    )

    interest_data["interest_rate"] = (
        interest_data["InterestExpense"] / interest_data["TotalDebt"]
    )

    interest_data_df = interest_data[
        ["spread_id", "DATE_OF_FINANCIALS", "InterestExpense", "TotalDebt", "interest_rate"]
    ]
    interest_data_df = interest_data_df.copy()
    interest_data_df["interest_expense_issue"] = interest_data_df["interest_rate"].apply(
        lambda x: "T" if x > 0.5 else "F"
    )

    int_expense_issue = interest_data[interest_data["interest_rate"] > 0.5]
    interest_data = interest_data[interest_data["interest_rate"] <= 0.5]

    summary_7 = summarize_step(
        interest_data,
        top_countries_1,
        c_column_name,
        step_name="Step 7: Rows after filter interest_rate<=0.5",
        id_column_name=id_column_name,
    )

    int_before_2018 = interest_data[interest_data["Year"] < 2018]  # noqa: F841
    interest_data = interest_data[interest_data["Year"] >= 2018]

    summary_8 = summarize_step(
        interest_data,
        top_countries_1,
        c_column_name,
        step_name="Step 8: Rows after filter interest_rate year before 2018",
        id_column_name=id_column_name,
    )

    # --- Aggregate to one data point per country per quarter ---
    agg_interest_data = (
        interest_data.groupby(
            ["country_of_risk", pd.Grouper(key="DATE_OF_FINANCIALS", freq="Q")]
        )
        .agg(
            {
                "InterestExpense": "mean",
                "TotalDebt": "mean",
                "interest_rate": "mean",
                "RA_Industry": "first",
                "sub_segment": "first",
                "irb_ead": "mean",
            }
        )
        .reset_index()
    )
    agg_interest_data.dropna()

    summary_steps = [
        summary_1,
        summary_2,
        summary_3,
        summary_4,
        summary_5,
        summary_6,
        summary_7,
        summary_8,
    ]

    # --- Pre-process per-country data for modelling and backtesting ---
    id_frames = []
    agg_frames = []
    for country in interest_data.country_of_risk.unique():
        id_frame = process_data_country_sector(
            interest_data, MEVdata, country, sector, aggregate=False,
            id_column_name=id_column_name, int_expense_issue=int_expense_issue,
        )
        agg_frame = process_data_country_sector(
            agg_interest_data, MEVdata, country, sector, aggregate=True,
            id_column_name=id_column_name, int_expense_issue=int_expense_issue,
        )
        if len(id_frame) > 0:
            id_frames.append(id_frame)
        if len(agg_frame) > 0:
            agg_frames.append(agg_frame)

    processed_id = pd.concat(id_frames, ignore_index=True) if id_frames else pd.DataFrame()
    processed_agg = pd.concat(agg_frames, ignore_index=True) if agg_frames else pd.DataFrame()

    return interest_data, agg_interest_data, summary_steps, MEVdata, interest_data_df, int_expense_issue, processed_id, processed_agg
