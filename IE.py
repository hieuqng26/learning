import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm

plt.rcdefaults()
from datetime import datetime
import warnings
import sys
from log_file import TimestampLog
from io import BytesIO
from openpyxl.drawing.image import Image
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

warnings.filterwarnings("ignore")

from IE_config import *

OUT_DIR = r"C:\Users\1643986\repo\50991-risk-portfolio-analytics\output"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def summarize_step(df, top_countries_1, c_column_name, step_name, id_column_name="spread_id"):
    """Summarize entity and data point counts by region for a given filtering step."""
    financials = df.copy()

    # Create a clean grouping column
    region_list = top_countries_1 + ["Others"]
    financials["__region__"] = financials[c_column_name].apply(
        lambda x: x if x in top_countries_1 else "Others"
    )

    # Generate summary across all regions
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


def MEV_data_processing_before2018(country, MEVdata):
    """Return the 4-quarter moving average of the central bank rate for `country` before 2018."""
    MEVdata_interest_rate = MEVdata[
        ["Date", f"{country}_Monetary policy or key interest rate"]
    ].copy()
    MEVdata_interest_rate = MEVdata_interest_rate[
        MEVdata_interest_rate["Date"] < "2018-01-01"
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


def get_corr_df(data, country, aggregate, id_column_name, alpha_min, alpha_max):
    """Compute per-entity (or aggregate) correlation, sensitivity, and Alpha against central bank rate.

    Sensitivity and Correlation are computed on period-over-period changes in interest rates
    rather than levels.

    Returns a DataFrame with columns including Sensitivity, Correlation, Alpha, and Alpha_US.
    """
    cb_col = f"{country}_Monetary policy or key interest rate_4QMA"
    cb_change_col = f"{country}_rate_change"

    if not aggregate:
        # Compute period-over-period changes within each entity
        data = data.sort_values([id_column_name, "DATE_OF_FINANCIALS"])
        data["interest_rate_change"] = data.groupby(id_column_name)["interest_rate"].diff()
        data[cb_change_col] = data.groupby(id_column_name)[cb_col].diff()
        data["US_rate_change"] = data.groupby(id_column_name)["Monetary policy or key interest rate_4QMA_US"].diff()
        data = data.dropna(subset=["interest_rate_change", cb_change_col, "US_rate_change"])

        data["No. of data points"] = data[id_column_name]
        std_df = data.groupby(id_column_name).agg(
            {
                "No. of data points": "count",
                "country_of_risk": "first",
                "interest_rate_change": "std",
                cb_change_col: "std",
                "US_rate_change": "std",
                "irb_ead": "first",  # irb_ead: Internal Ratings-Based Exposure at Default
            }
        )
        std_df["Sensitivity"] = (
            std_df["interest_rate_change"]
            / std_df[cb_change_col]
        )
        std_df["Sensitivity_US"] = (
            std_df["interest_rate_change"]
            / std_df["US_rate_change"]
        )
    else:
        # Compute period-over-period changes for aggregate data
        data = data.sort_values("DATE_OF_FINANCIALS")
        data["interest_rate_change"] = data["interest_rate"].diff()
        data[cb_change_col] = data[cb_col].diff()
        data["US_rate_change"] = data["Monetary policy or key interest rate_4QMA_US"].diff()
        data = data.dropna(subset=["interest_rate_change", cb_change_col, "US_rate_change"])

        data["No. of data points"] = len(data["DATE_OF_FINANCIALS"])
        std_df = data.agg(
            {
                "No. of data points": "count",
                "country_of_risk": lambda x: x.iloc[0],
                "interest_rate_change": "std",
                cb_change_col: "std",
                "US_rate_change": "std",
                "irb_ead": lambda x: x.iloc[0],
            }
        )
        std_df["Sensitivity"] = (
            std_df["interest_rate_change"]
            / std_df[cb_change_col]
        )
        std_df["Sensitivity_US"] = (
            std_df["interest_rate_change"]
            / std_df["US_rate_change"]
        )
        std_df = std_df.to_dict()

    if not aggregate:
        correlation_per_id = data.groupby(id_column_name).apply(
            lambda x: x["interest_rate_change"].corr(x[cb_change_col])
        )

        correlation_per_id_US = data.groupby(id_column_name).apply(
            lambda x: x["interest_rate_change"].corr(x["US_rate_change"])
        )

        correlation_df = correlation_per_id.rename("Correlation").reset_index()
        correlation_df_US = correlation_per_id_US.rename("Correlation_US").reset_index()
        all_df = pd.merge(std_df, correlation_df, on=id_column_name)
        all_df = pd.merge(all_df, correlation_df_US, on=id_column_name)
        all_df["Alpha"] = (all_df["Correlation"] * all_df["Sensitivity"]).clip(
            lower=alpha_min, upper=alpha_max
        )
        all_df["Alpha_US"] = (
            all_df["Correlation_US"] * all_df["Sensitivity_US"]
        ).clip(lower=alpha_min, upper=alpha_max)
    else:
        correlation_agg = data["interest_rate_change"].corr(data[cb_change_col])
        correlation_agg_US = data["interest_rate_change"].corr(data["US_rate_change"])

        std_df["Correlation"] = correlation_agg
        std_df["Correlation_US"] = correlation_agg_US

        all_df = pd.DataFrame([std_df])
        all_df["Alpha"] = (all_df["Correlation"] * all_df["Sensitivity"]).clip(
            lower=alpha_min, upper=alpha_max
        )
        all_df["Alpha_US"] = (
            all_df["Correlation_US"] * all_df["Sensitivity_US"]
        ).clip(lower=alpha_min, upper=alpha_max)

    all_df = all_df.rename(
        columns={
            "country_of_risk": "Country",
            "interest_rate_change": "Interest Rate Std Dev",
            cb_change_col: "Central bank Interest Rate Std Dev",
        }
    )

    return all_df


def compute_alpha(window_df, country, alpha_min, alpha_max):
    """Compute the Alpha parameter for a given data window and country.

    Alpha = Correlation(entity_rate_change, central_bank_rate_change) x Sensitivity,
    clipped to [alpha_min, alpha_max]. Sensitivity and Correlation are computed on
    period-over-period changes in interest rates rather than levels.
    """
    cb_col = f"{country}_Monetary policy or key interest rate_4QMA"
    window_df = window_df.sort_values("DATE_OF_FINANCIALS")
    ir_change = window_df["interest_rate"].diff().dropna()
    cb_change = window_df[cb_col].diff().dropna()
    corr = ir_change.corr(cb_change)
    sensitivity = ir_change.std() / cb_change.std()
    alpha = corr * sensitivity
    return np.clip(alpha, alpha_min, alpha_max)


def interest_expense(
    interest_data,
    MEVdata,
    country,
    sector,
    aggregate,
    id_column_name,
    alpha_min,
    alpha_max,
    int_expense_issue,
):
    """Run the interest expense model for a single country.

    Processes data, computes correlation/sensitivity/Alpha, and attaches portfolio labels.
    Returns an empty DataFrame if no data is available for the country.
    """
    data = process_data_country_sector(
        interest_data, MEVdata, country, sector, aggregate, id_column_name, int_expense_issue
    )
    if len(data) == 0:
        final = pd.DataFrame()
    else:
        final = get_corr_df(data, country, aggregate, id_column_name, alpha_min, alpha_max)

        # Attach portfolio labels (LC / CC / MC) to entity-level results
        if not aggregate:
            final = final.merge(
                interest_data[["spread_id", "Portfolio"]],
                on="spread_id",
                how="left",
            )
    return final


def cal_country_stats_with_r2(data):
    """Compute backtesting statistics: top-minus-bottom bucket spread, R², MSE, and MAE."""
    buckets = pd.qcut(data["pred_change"], 5, duplicates="drop")
    bucket_perf = data.groupby(buckets)["actual_change"].mean()

    if len(bucket_perf) < 2:
        top_minus_bottom = np.nan
    else:
        top_minus_bottom = bucket_perf.iloc[-1] - bucket_perf.iloc[0]

        # OLS regression of actual change on predicted change
        X = sm.add_constant(data["pred_change"])
        y = data["actual_change"]
        model = sm.OLS(y, X, missing="drop").fit()
        y_pred = model.predict(X)

        mse_model = np.mean((y - y_pred) ** 2)
        mse_benchmark = np.mean((y - np.mean(y)) ** 2)
        r2_oos = 1 - mse_model / mse_benchmark

    return pd.Series(
        {
            "n_obs": len(data),
            "top_minus_bottom": top_minus_bottom,
            "Alpha": data["Alpha"],
            "R2": r2_oos,
            "mse": mean_squared_error(data["actual_change"], data["pred_change"]),
            "mae": mean_absolute_error(data["actual_change"], data["pred_change"]),
        }
    )


def agg_results(input_data, top_countries):
    """Aggregate entity-level Alpha results to country level, grouping non-top countries into 'Others'."""
    data = input_data.copy()
    data = data.dropna()
    df1 = data.loc[data["Country"].isin(top_countries)]
    df2 = data.loc[~data["Country"].isin(top_countries)]
    df2["Alpha"] = np.where(
        df2["Alpha"] == 0.0,
        df2["Alpha_US"],
        df2["Alpha"],
    )

    other_alpha = sum(
        df2["Alpha"]
        * df2["irb_ead"]
        / df2["irb_ead"].sum()
    )

    other_alpha_us = sum(
        df2["Alpha_US"]
        * df2["irb_ead"]
        / df2["irb_ead"].sum()
    )

    other_ead = df2["irb_ead"].sum()
    other_df = pd.DataFrame(
        [{
            "Country": "Others",
            "Alpha": other_alpha,
            "Alpha_US": other_alpha_us,
            "irb_ead": other_ead,
        }]
    )
    df1 = pd.concat([df1, other_df], ignore_index=True)
    output = df1[["Country", "Alpha", "Alpha_US"]]

    all_ave_alpha = output.Alpha.mean()
    all_ave_alpha_us = output.Alpha_US.mean()
    all_ave_df = pd.DataFrame(
        [{
            "Country": "All countries average",
            "Alpha": all_ave_alpha,
            "Alpha_US": all_ave_alpha_us,
        }]
    )
    output = pd.concat([output, all_ave_df], ignore_index=True)
    return output


def split_portfolio(data, portfolio, both_level_df, top_countries):
    """Split portfolio results by currency type (LC_CC or MC) and group non-top countries into 'Others'."""
    output = both_level_df[both_level_df["Portfolio"] == portfolio]
    df1 = output.loc[data["Country"].isin(top_countries)]
    df2 = output.loc[~data["Country"].isin(top_countries)]
    df2["Alpha"] = np.where(
        df2["Alpha"] == 0.0,
        df2["Alpha_US"],
        df2["Alpha"],
    )

    other_alpha = sum(
        df2["Alpha"]
        * df2["irb_ead"]
        / df2["irb_ead"].sum()
    )

    other_alpha_us = sum(
        df2["Alpha_US"]
        * df2["irb_ead"]
        / df2["irb_ead"].sum()
    )

    other_ead = df2["irb_ead"].sum()
    other_df = pd.DataFrame(
        [{
            "Portfolio": portfolio,
            "Country": "Others",
            "Alpha": other_alpha,
            "Alpha_US": other_alpha_us,
            "irb_ead": other_ead,
        }]
    )
    df1 = pd.concat([df1, other_df], ignore_index=True)
    output = df1[["Portfolio", "Country", "Alpha", "Alpha_US"]]

    all_ave_alpha = output.Alpha.mean()
    all_ave_alpha_us = output.Alpha_US.mean()
    all_ave_df = pd.DataFrame(
        [{
            "Portfolio": portfolio,
            "Country": "All countries average",
            "Alpha": all_ave_alpha,
            "Alpha_US": all_ave_alpha_us,
        }]
    )
    output = pd.concat([output, all_ave_df], ignore_index=True)
    return output


def add_labels_LCY(x, y, bar_width=0.35):
    """Add percentage labels above each LCY bar in the active matplotlib figure."""
    for i in range(len(x)):
        lable_LCY = ((y[i] * 100).round(0)).astype("int")
        plt.text(
            i + bar_width,
            y[i] + 0.01,
            f"{lable_LCY}" + "%",
            ha="center",
            fontsize=12,
        )  # Aligning text for LCY


def add_labels_FCY(x, y, bar_width=0.35):
    """Add percentage labels above each FCY bar in the active matplotlib figure."""
    for i in range(len(x)):
        lable_FCY = ((y[i] * 100).round(0)).astype("int")
        plt.text(
            i + bar_width + 0.4,
            y[i] + 0.01,
            f"{lable_FCY}" + "%",
            ha="center",
            fontsize=12,
        )  # Aligning text for FCY right of LCY


def data_for_chart(data, split):
    """Reshape output data into LCY/FCY columns for bar chart rendering."""
    output_LCY = data[data["Alpha Base"] == "LCY"]
    output_LCY = output_LCY.rename(columns={"Alpha": "LCY"})
    output_LCY = output_LCY.drop(
        ["Alpha Base", "Driver", "Sector", "Sub-sector", "As of Date"], axis=1
    )

    output_FCY = data[data["Alpha Base"] == "FCY (USD)"]
    output_FCY = output_FCY.rename(columns={"Alpha": "FCY"})
    output_FCY = output_FCY.drop(
        ["Alpha Base", "Driver", "Sector", "Sub-sector", "As of Date"], axis=1
    )

    if split == "Portfolio":
        output_bchart = pd.merge(output_LCY, output_FCY, on="Portfolio")
        add_labels_LCY(output_bchart["Portfolio"], output_bchart["LCY"])
        add_labels_FCY(output_bchart["Portfolio"], output_bchart["FCY"])
    else:
        output_bchart = pd.merge(output_LCY, output_FCY, on="Country")
        add_labels_LCY(output_bchart["Country"], output_bchart["LCY"])
        add_labels_FCY(output_bchart["Country"], output_bchart["FCY"])

    return output_bchart


def outputChart_excel(
    data,
    chartTitle,
    workbook,
    sheet_name,
    bin_edges=np.arange(-2, 2.2, 0.05),
    percentiles_for_chart=None,
    plotSeaboneHistplot=False,
    pdfPagesObject=None,
    figsize=(10, 6),
    xrange=(-2, 2),
):
    """Render a histogram with percentile lines and embed it as a chart in an Excel workbook."""
    if percentiles_for_chart is None:
        percentiles_for_chart = []

    fig, ax = plt.subplots(figsize=figsize)

    plt.hist(
        data,
        bins=bin_edges,
        alpha=0.7,
        color="blue",
        edgecolor="black",
        label="Histogram (Count)",
    )

    # Calculate and draw percentile lines
    percentile_values = [data.quantile(p / 100) for p in percentiles_for_chart]

    for i, (perc, value) in enumerate(
        zip(percentiles_for_chart, percentile_values)
    ):
        color = "green" if i == 0 else "red"
        label_text = f"{perc}th Percentile: {value:.4f}"
        plt.axvline(
            value,
            color=color,
            linestyle="-",
            linewidth=1.5,
            label=label_text,
        )

    if xrange:
        # Set X-axis range
        ax.set_xlim(xrange[0], xrange[1])

    ax.set_title(chartTitle)
    ax.set_xlabel("Interest Rate")
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


def final_chart(
    data,
    split_type,
    chartTitle,
    workbook,
    sheet_name,
):
    """Render a grouped bar chart of LCY and FCY Alpha parameters and embed it in an Excel workbook."""
    plt.figure(figsize=(10, 6))

    bar_width = 0.35
    opacity = 0.8

    if split_type == "Country":
        index = np.arange(len(data["Country"]))

        rects1 = plt.bar(
            index + bar_width,
            data["LCY"],
            bar_width,
            alpha=opacity,
            color="royalblue",
            label="LCY",
        )

        rects2 = plt.bar(
            index + 2 * bar_width + 0.05,
            data["FCY"],
            bar_width,
            alpha=opacity,
            color="darkorange",
            label="FCY",
        )

        plt.title(chartTitle, fontsize=16)
        plt.xticks(
            index + 3 * bar_width / 2, data["Country"], fontsize=12
        )
        plt.xticks(wrap=True)
        plt.legend(loc="upper center", ncol=2)

        add_labels_LCY(data["Country"], data["LCY"], bar_width)
        add_labels_FCY(data["Country"], data["FCY"], bar_width)

    else:
        index = np.arange(len(data["Portfolio"]))

        rects1 = plt.bar(
            index + bar_width,
            data["LCY"],
            bar_width,
            alpha=opacity,
            color="royalblue",
            label="LCY",
        )

        rects2 = plt.bar(
            index + 2 * bar_width + 0.05,
            data["FCY"],
            bar_width,
            alpha=opacity,
            color="darkorange",
            label="FCY",
        )

        plt.title(chartTitle, fontsize=16)
        plt.xticks(
            index + 3 * bar_width / 2, data["Portfolio"], fontsize=12
        )
        plt.xticks(wrap=True)
        plt.legend(loc="upper center", ncol=2)

        add_labels_LCY(data["Portfolio"], data["LCY"], bar_width)
        add_labels_FCY(data["Portfolio"], data["FCY"], bar_width)

    plt.ylim(0, 1)
    plt.yticks(
        ticks=[0, 0.2, 0.4, 0.6, 0.8, 1],
        labels=["0%", "20%", "40%", "60%", "80%", "100%"],
        fontsize=12,
    )
    plt.tight_layout()

    imgdata = BytesIO()
    plt.savefig(imgdata, format="png", dpi=130)
    plt.close()
    imgdata.seek(0)

    ws = workbook.create_sheet(sheet_name[:31])
    img = Image(imgdata)
    ws.add_image(img, "B2")


# ============================================================================
# MAIN RUNNER
# ============================================================================


def interest_expense_run(sector_name):
    """Run the full interest expense Alpha model for a given sector.

    Loads data, cleans it, computes entity-level Alpha parameters,
    aggregates results, runs backtesting, and writes all outputs to Excel.
    """
    # --- Configuration ---
    IE_config = SECTORS[sector_name]

    sector = IE_config.sector
    sector_short = IE_config.sector_short
    id_column_name = IE_config.id_column_name
    ISIC_mapping = IE_config.ISIC_mapping
    exclude_IE_Zero = IE_config.exclude_IE_Zero
    globalmodel = IE_config.globalmodel
    groupCountry = IE_config.groupCountry
    applyWindow = IE_config.applyWindow

    # File paths
    interest_file_path = IE_config.interest_file_path
    MEV_file_path = IE_config.MEV_file_path
    isic_file_path = IE_config.isic_file_path

    consolid_path = windows_long_path(
        f"{OUT_DIR}/{sector}/consolidated_results_{sector_short}.xlsx"
    )

    alpha_max = IE_config.alpha_max
    alpha_min = IE_config.alpha_min
    isWeighted = IE_config.isWeighted
    top_countries = IE_config.top_countries
    country_group_mapping = IE_config.country_group_mapping
    sub_segment_filter_out = IE_config.sub_segment_filter_out

    global_exclude_sectors = IE_config.global_exclude_sectors
    c_column_name = IE_config.c_column_name
    percentiles_for_chart = IE_config.percentiles_for_chart

    if globalmodel:
        top_countries_1 = IE_config.top_countries_1
    else:
        top_countries_1 = top_countries

    # --- Load data ---
    interest_data = pd.read_csv(interest_file_path).iloc[:, 1:]
    MEVdata = pd.read_csv(MEV_file_path)

    # ISIC Code Mapping
    isic_data = pd.read_excel(isic_file_path)

    if ISIC_mapping:
        # Backup old RA_Industry
        interest_data.rename(columns={"RA_Industry": "RA_Industry_Old"}, inplace=True)

        # Prepare mapping dictionaries (used in both models)
        isic_map = isic_data.set_index("ISIC Code")[
            "Risk Industry_April 2025"
        ].to_dict()
        subseg_map = isic_data.set_index("ISIC Code")["Biz L1_Apr 2025.1"].to_dict()

        if globalmodel:
            # GLOBAL MODEL: Map full RA_Industry and sub_segment
            interest_data["RA_Industry"] = (
                interest_data["isic_code"].map(isic_map).fillna("NA")
            )
            interest_data["sub_segment"] = (
                interest_data["isic_code"].map(subseg_map).fillna("NA")
            )

            # Filter out excluded global sectors
            interest_data = interest_data[
                ~interest_data["RA_Industry"].isin(global_exclude_sectors)
            ]
            interest_data = interest_data[interest_data["RA_Industry"] != "NA"]

        else:
            # NON-GLOBAL MODEL: Only tag if belongs to target sector
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

            # Still map sub_segment in non-global case
            interest_data["sub_segment"] = (
                interest_data["isic_code"].map(subseg_map).fillna("NA")
            )

            # Filter: Keep only data from the desired sector
            interest_data = interest_data[interest_data["RA_Industry"] == sector]

        # Clean up
        interest_data = interest_data.drop(columns=["RA_Industry_Old"])

    else:
        interest_data = interest_data[interest_data["RA_Industry"] == sector]

    if sub_segment_filter_out:
        interest_data = interest_data[interest_data["sub_segment"] != "Not applicable"]

    if groupCountry:  # only used for EU grouping
        # Build reverse mapping: each country -> EU group label
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
        # Build reverse mapping: each country -> region group label
        reverse_country_map = {}
        for group_label, countries in country_group_mapping.items():
            for country in countries:
                reverse_country_map[country] = group_label

        # Apply mapping to financials['country_of_risk']
        interest_data["Region_group"] = interest_data["country_of_risk"].apply(
            lambda x: reverse_country_map.get(x, x)
        )

    # --- Clean and filter data ---
    # irb_ead: Internal Ratings-Based Exposure at Default
    interest_data["irb_ead"] = pd.to_numeric(interest_data["irb_ead"], errors="coerce")

    # Replace "Missing" and "Not applicable" with NaN
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
    )

    # Drop rows where InterestExpense or TotalDebt is NaN
    interest_data = interest_data.dropna(subset=["InterestExpense", "TotalDebt"])
    print("Rows after dropping NA:", len(interest_data))
    summary_2 = summarize_step(
        interest_data,
        top_countries_1,
        c_column_name,
        step_name="Step 2: Rows after dropping NA in InterestExpense and TotalDebt",
    )

    interest_data["DATE_OF_FINANCIALS"] = pd.to_datetime(
        interest_data["DATE_OF_FINANCIALS"]
    )
    interest_data["Year"] = interest_data["DATE_OF_FINANCIALS"].dt.year
    interest_data["Month"] = interest_data["DATE_OF_FINANCIALS"].dt.month

    # Sort so the latest month comes first within each (entity, year), then keep one row per year
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
    )

    interest_data = interest_data[interest_data.irb_ead != 0]
    summary_4 = summarize_step(
        interest_data,
        top_countries_1,
        c_column_name,
        step_name="Step 4: Rows after filter irb!=0",
    )

    interest_data = interest_data[
        interest_data["TotalDebt"] != 0
    ]  # remove the rows where total debt is 0
    summary_5 = summarize_step(
        interest_data,
        top_countries_1,
        c_column_name,
        step_name="Step 5: Rows after filter totaldebt!=0",
    )

    if exclude_IE_Zero:  # define this in config
        interest_data = interest_data[interest_data["InterestExpense"] != 0]

    summary_6 = summarize_step(
        interest_data,
        top_countries_1,
        c_column_name,
        step_name="Step 6: Rows after filter ie !=0",
    )

    interest_data["interest_rate"] = (
        interest_data["InterestExpense"] / interest_data["TotalDebt"]
    )

    interest_data_df = interest_data[["spread_id", "DATE_OF_FINANCIALS", "InterestExpense", "TotalDebt", "interest_rate"]]
    interest_data_df["interest_expense_issue"] = interest_data_df["interest_rate"].apply(lambda x: 'T' if x > 0.5 else 'F')

    # filter modelling data that interest_rate <=0.5
    int_expense_issue = interest_data[interest_data["interest_rate"] > 0.5]
    interest_data = interest_data[interest_data["interest_rate"] <= 0.5]

    summary_7 = summarize_step(
        interest_data,
        top_countries_1,
        c_column_name,
        step_name="Step 7: Rows after filter interest_rate<=0.5",
    )

    # Filter for interest rate data from 2018 onward
    int_before_2018 = interest_data[interest_data["Year"] < 2018]
    interest_data = interest_data[interest_data["Year"] >= 2018]

    summary_8 = summarize_step(
        interest_data,
        top_countries_1,
        c_column_name,
        step_name="Step 8: Rows after filter interest_rate year before 2018",
    )

    # Aggregate to one data point per country per quarter
    agg_interest_data = (
        interest_data.groupby(["country_of_risk", pd.Grouper(key="DATE_OF_FINANCIALS", freq="Q")])
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

    # --- Model: compute Alpha per entity and country ---
    all_country_frame = pd.DataFrame(
        columns=[
            id_column_name,
            "No. of data points",
            "Country",
            "Interest Rate Std Dev",
            "Central bank Interest Rate Std Dev",
            "Sensitivity",
            "Correlation",
            "Alpha",
            "Alpha_US",
        ]
    )

    agg_frame = pd.DataFrame(
        columns=[
            "No. of data points",
            "Country",
            "Interest Rate Std Dev",
            "Central bank Interest Rate Std Dev",
            "Sensitivity",
            "Correlation",
            "Alpha",
            "Alpha_US",
        ]
    )

    for country in interest_data.country_of_risk.unique():
        id_data = interest_expense(
            interest_data, MEVdata, country, sector=sector, aggregate=False,
            id_column_name=id_column_name, alpha_min=alpha_min, alpha_max=alpha_max,
            int_expense_issue=int_expense_issue,
        )
        agg_data = interest_expense(
            agg_interest_data, MEVdata, country, sector=sector, aggregate=True,
            id_column_name=id_column_name, alpha_min=alpha_min, alpha_max=alpha_max,
            int_expense_issue=int_expense_issue,
        )
        if len(id_data) > 0:
            all_country_frame = pd.concat(
                [all_country_frame, id_data], axis=0, ignore_index=True
            )
        if len(agg_data) > 0:
            agg_frame = pd.concat(
                [agg_frame, agg_data], axis=0, ignore_index=True
            )

    all_portfolio_frame = all_country_frame.copy()
    all_portfolio_frame["Portfolio"] = all_portfolio_frame["Portfolio"].replace(
        {
            "LC": "LC_CC",
            "CC": "LC_CC",
        }
    )

    if not isWeighted:
        # Unweighted average across entities
        country_level_df = all_country_frame.groupby("Country").agg(
            {
                "Alpha": "mean",
                "Alpha_US": "mean",
            }
        )

        portfolio_level_df = all_portfolio_frame.groupby("Portfolio").agg(
            {
                "Alpha": "mean",
                "Alpha_US": "mean",
            }
        )

        both_level_df = all_portfolio_frame.groupby(["Portfolio", "Country"]).agg(
            {
                "Alpha": "mean",
                "Alpha_US": "mean",
            }
        )

    else:
        # Weighted average by irb_ead (Internal Ratings-Based Exposure at Default)
        country_level_df = all_country_frame.groupby("Country").agg(
            {
                "Alpha": lambda x: (
                    (x * all_country_frame.loc[x.index, "irb_ead"]).sum()
                    / all_country_frame.loc[x.index, "irb_ead"].sum()
                ),
                "Alpha_US": lambda x: (
                    (x * all_country_frame.loc[x.index, "irb_ead"]).sum()
                    / all_country_frame.loc[x.index, "irb_ead"].sum()
                ),
            }
        )

        portfolio_level_df = all_portfolio_frame.groupby("Portfolio").agg(
            {
                "Alpha": lambda x: (
                    (x * all_portfolio_frame.loc[x.index, "irb_ead"]).sum()
                    / all_portfolio_frame.loc[x.index, "irb_ead"].sum()
                ),
                "Alpha_US": lambda x: (
                    (x * all_portfolio_frame.loc[x.index, "irb_ead"]).sum()
                    / all_portfolio_frame.loc[x.index, "irb_ead"].sum()
                ),
            }
        )

        both_level_df = all_portfolio_frame.groupby(["Portfolio", "Country"]).agg(
            {
                "Alpha": lambda x: (
                    (x * all_portfolio_frame.loc[x.index, "irb_ead"]).sum()
                    / all_portfolio_frame.loc[x.index, "irb_ead"].sum()
                ),
                "Alpha_US": lambda x: (
                    (x * all_portfolio_frame.loc[x.index, "irb_ead"]).sum()
                    / all_portfolio_frame.loc[x.index, "irb_ead"].sum()
                ),
            }
        )

    ead_sum = all_country_frame.groupby("Country").agg({"irb_ead": "sum"})
    country_level_df = country_level_df.merge(ead_sum, how="left", on="Country")
    country_level_df["Country"] = country_level_df.index

    portfolio_ead_sum = all_portfolio_frame.groupby("Portfolio").agg({"irb_ead": "sum"})
    portfolio_level_df = portfolio_level_df.merge(portfolio_ead_sum, how="left", on="Portfolio")
    portfolio_level_df["Portfolio"] = portfolio_level_df.index

    all_ead_sum = all_portfolio_frame.groupby(["Portfolio", "Country"]).agg({"irb_ead": "sum"})
    both_level_df = both_level_df.merge(all_ead_sum, how="left", on=["Portfolio", "Country"])
    both_level_df = both_level_df.reset_index()

    # --- Global model override ---
    if globalmodel:
        # Aggregate countries into regional groups defined in country_group_mapping
        regional_country_list = []
        global_final = pd.DataFrame(columns=country_level_df.columns)
        for (
            key,
            values,
        ) in (
            country_group_mapping.items()
        ):  # key refers to region, values refers to countries
            regional_country_list = list(set(regional_country_list + values))
            country_level_df2 = country_level_df.loc[
                country_level_df.index.isin(values)
            ]

            country_level_df2["Alpha"] = np.where(
                country_level_df2["Alpha"] == 0.0,
                country_level_df2["Alpha_US"],
                country_level_df2["Alpha"],
            )

            globals()[f"{key}_dict"] = {}
            globals()[f"{key}_dict"]["Alpha"] = sum(
                country_level_df2["Alpha"]
                * country_level_df2["irb_ead"]
                / country_level_df2["irb_ead"].sum()
            )

            globals()[f"{key}_dict"]["Alpha_US"] = sum(
                country_level_df2["Alpha_US"]
                * country_level_df2["irb_ead"]
                / country_level_df2["irb_ead"].sum()
            )

            globals()[f"{key}_dict"]["irb_ead"] = country_level_df2["irb_ead"].sum()
            global_final.loc[key] = globals()[f"{key}_dict"]

        country_list_global = country_level_df.Country.unique()
        others_list_global = [
            i for i in country_list_global if i not in regional_country_list
        ]

        country_level_df2 = country_level_df.loc[
            country_level_df.index.isin(others_list_global)
        ]

        country_level_df2["Alpha"] = np.where(
            country_level_df2["Alpha"] == 0.0,
            country_level_df2["Alpha_US"],
            country_level_df2["Alpha"],
        )

        other_dict = {}
        other_dict["Alpha"] = sum(
            country_level_df2["Alpha"]
            * country_level_df2["irb_ead"]
            / country_level_df2["irb_ead"].sum()
        )

        other_dict["Alpha_US"] = sum(
            country_level_df2["Alpha_US"]
            * country_level_df2["irb_ead"]
            / country_level_df2["irb_ead"].sum()
        )

        other_dict["irb_ead"] = country_level_df2["irb_ead"].sum()
        country_level_df = global_final[["Alpha", "Alpha_US"]]

    else:
        # Non-global model: group non-top countries into "Others"
        country_level_df1 = country_level_df.loc[
            country_level_df.index.isin(top_countries)
        ]

        country_level_df2 = country_level_df.loc[
            ~country_level_df.index.isin(top_countries)
        ]

        country_level_df2["Alpha"] = np.where(
            country_level_df2["Alpha"] == 0.0,
            country_level_df2["Alpha_US"],
            country_level_df2["Alpha"],
        )

        other_dict = {}
        other_dict["Alpha"] = sum(
            country_level_df2["Alpha"]
            * country_level_df2["irb_ead"]
            / country_level_df2["irb_ead"].sum()
        )

        other_dict["Alpha_US"] = sum(
            country_level_df2["Alpha_US"]
            * country_level_df2["irb_ead"]
            / country_level_df2["irb_ead"].sum()
        )

        other_dict["irb_ead"] = country_level_df2["irb_ead"].sum()
        country_level_df1.loc["Others"] = other_dict
        country_level_df = country_level_df1[["Alpha", "Alpha_US"]]

    plt.figure(figsize=(8, 6))
    plt.bar(country_level_df.index, 100 * country_level_df.Alpha)
    plt.title(f"Country level Alpha", fontsize=16)
    plt.xlabel("Country", fontsize=14)
    plt.ylabel(f"Alpha (%)", fontsize=14)
    plt.grid(True)

    plt.figure(figsize=(8, 6))
    plt.bar(country_level_df.index, 100 * country_level_df.Alpha_US)
    plt.title(f"Country level Alpha with US rate", fontsize=16)
    plt.xlabel("Country", fontsize=14)
    plt.ylabel(f"Alpha (%)", fontsize=14)
    plt.grid(True)

    # --- Generate outputs ---
    country_level_df.loc["All countries average"] = [
        country_level_df.Alpha.mean(),
        country_level_df.Alpha_US.mean(),
    ]

    current_date = datetime.now().strftime("%Y-%m-%d")

    leid_output = all_country_frame[["Country", "Portfolio", id_column_name, "Alpha", "Alpha_US"]]
    leid_output["Driver"] = "Interest Expense Driver"
    leid_output["Sector"] = sector
    leid_output["Sub-sector"] = "All"
    leid_output["As of Date"] = current_date

    leid_output = leid_output.rename(
        columns={id_column_name: "LEID", "Alpha": "Alpha_LCY"}
    )

    leid_output["Alpha"] = leid_output.apply(
        lambda row: (
            row["Alpha_US"]
            if pd.isna(row["Alpha_LCY"]) or row["Alpha_LCY"] == ""
            else row["Alpha_LCY"]
        ),
        axis=1,
    )

    leid_output["Alpha Base"] = leid_output.apply(
        lambda row: (
            "FCY (USD)"
            if pd.isna(row["Alpha_LCY"]) or row["Alpha_LCY"] == ""
            else "LCY"
        ),
        axis=1,
    )

    leid_output = leid_output.drop(columns=["Alpha_LCY", "Alpha_US"])

    new_order = [
        "Driver",
        "Sector",
        "Sub-sector",
        "Country",
        "Portfolio",
        "LEID",
        "Alpha Base",
        "Alpha",
        "As of Date",
    ]
    leid_output = leid_output[new_order]

    country_output = country_level_df.copy()
    if globalmodel:
        country_output["Country"] = country_output.index

    country_output.reset_index(inplace=True)
    summary_testing = country_output.copy()

    country_output = pd.melt(
        country_output,
        id_vars=["Country"],
        value_vars=["Alpha", "Alpha_US"],
        var_name="Type",
        value_name="Value",
    )

    country_output["Alpha Base"] = country_output.apply(
        lambda row: "FCY (USD)" if row["Type"] == "Alpha_US" else "LCY", axis=1
    )
    country_output["Driver"] = "Interest Expense Driver"
    country_output["Sector"] = sector
    country_output["Sub-sector"] = "All"

    country_output["As of Date"] = current_date

    country_output = country_output.rename(columns={"Value": "Alpha"})

    new_order = [
        "Driver",
        "Sector",
        "Sub-sector",
        "Country",
        "Alpha Base",
        "Alpha",
        "As of Date",
    ]

    country_output = country_output[new_order]

    portfolio_output = portfolio_level_df.copy()
    portfolio_output = pd.melt(
        portfolio_output,
        id_vars=["Portfolio"],
        value_vars=["Alpha", "Alpha_US"],
        var_name="Type",
        value_name="Value",
    )
    portfolio_output["Alpha Base"] = portfolio_output.apply(
        lambda row: "FCY (USD)" if row["Type"] == "Alpha_US" else "LCY", axis=1
    )

    portfolio_output["Driver"] = "Interest Expense Driver"
    portfolio_output["Sector"] = sector
    portfolio_output["Sub-sector"] = "All"

    portfolio_output["As of Date"] = current_date

    portfolio_output = portfolio_output.rename(columns={"Value": "Alpha"})

    new_order = [
        "Driver",
        "Sector",
        "Sub-sector",
        "Portfolio",
        "Alpha Base",
        "Alpha",
        "As of Date",
    ]

    portfolio_output = portfolio_output[new_order]

    agg_output = agg_results(agg_frame, top_countries)
    LC_CC_split_output = split_portfolio(both_level_df, "LC_CC", both_level_df, top_countries)
    MC_split_output = split_portfolio(both_level_df, "MC", both_level_df, top_countries)

    agg_output = pd.melt(
        agg_output,
        id_vars=["Country"],
        value_vars=["Alpha", "Alpha_US"],
        var_name="Type",
        value_name="Value",
    )

    agg_output["Alpha Base"] = agg_output.apply(
        lambda row: "FCY (USD)" if row["Type"] == "Alpha_US" else "LCY", axis=1
    )

    agg_output["Driver"] = "Interest Expense Driver"
    agg_output["Sector"] = sector
    agg_output["Sub-sector"] = "All"
    agg_output["As of Date"] = current_date
    agg_output = agg_output.rename(columns={"Value": "Alpha"})

    LC_CC_split_output = pd.melt(
        LC_CC_split_output,
        id_vars=["Country"],
        value_vars=["Alpha", "Alpha_US"],
        var_name="Type",
        value_name="Value",
    )

    MC_split_output = pd.melt(
        MC_split_output,
        id_vars=["Country"],
        value_vars=["Alpha", "Alpha_US"],
        var_name="Type",
        value_name="Value",
    )

    LC_CC_split_output["Alpha Base"] = LC_CC_split_output.apply(
        lambda row: "FCY (USD)" if row["Type"] == "Alpha_US" else "LCY", axis=1
    )

    MC_split_output["Alpha Base"] = MC_split_output.apply(
        lambda row: "FCY (USD)" if row["Type"] == "Alpha_US" else "LCY", axis=1
    )

    LC_CC_split_output["Driver"] = "Interest Expense Driver"
    LC_CC_split_output["Sector"] = sector
    LC_CC_split_output["Sub-sector"] = "All"
    LC_CC_split_output["As of Date"] = current_date
    LC_CC_split_output = LC_CC_split_output.rename(columns={"Value": "Alpha"})

    MC_split_output["Driver"] = "Interest Expense Driver"
    MC_split_output["Sector"] = sector
    MC_split_output["Sub-sector"] = "All"
    MC_split_output["As of Date"] = current_date
    MC_split_output = MC_split_output.rename(columns={"Value": "Alpha"})

    new_order = [
        "Driver",
        "Sector",
        "Sub-sector",
        "Country",
        "Alpha Base",
        "Alpha",
        "As of Date",
    ]
    agg_output = agg_output[new_order]
    LC_CC_split_output = LC_CC_split_output[new_order]
    MC_split_output = MC_split_output[new_order]

    # --- Backtesting ---
    WINDOW = 3  # Rolling window of 3 years for backtesting
    results = []
    id_bt_rows = []
    agg_bt_rows = []
    summary_bt_rows = []
    for country in interest_data.country_of_risk.unique():
        agg_data = process_data_country_sector(
            agg_interest_data, MEVdata, country, sector, aggregate=True,
            id_column_name=id_column_name, int_expense_issue=int_expense_issue,
        )
        id_data = process_data_country_sector(
            interest_data, MEVdata, country, sector, aggregate=False,
            id_column_name=id_column_name, int_expense_issue=int_expense_issue,
        )

        # LEID-level backtesting
        id_data = id_data.sort_values(["spread_id", "DATE_OF_FINANCIALS"])
        id_data["future_interest_change"] = (
            id_data.groupby("spread_id")["interest_rate"].shift(-1)
            - id_data["interest_rate"]
        )
        id_data["MEV_diff"] = (
            id_data.groupby("spread_id")[
                f"{country}_Monetary policy or key interest rate_4QMA"
            ].shift(-1)
            - id_data[f"{country}_Monetary policy or key interest rate_4QMA"]
        )

        # Aggregated-level backtesting
        agg_data = agg_data.sort_values(["DATE_OF_FINANCIALS"])
        agg_data["future_interest_change"] = (
            agg_data["interest_rate"].shift(-1) - agg_data["interest_rate"]
        )
        agg_data["MEV_diff"] = (
            agg_data[f"{country}_Monetary policy or key interest rate_4QMA"].shift(-1)
            - agg_data[f"{country}_Monetary policy or key interest rate_4QMA"]
        )

        if not applyWindow:
            for spread_id, g in id_data.groupby("spread_id"):
                window = g
                alpha = compute_alpha(window, country, alpha_min, alpha_max)
                for i in range(len(g)):
                    actual_mev_diff = g.iloc[i]["MEV_diff"]
                    pred_interest_change = alpha * actual_mev_diff
                    id_bt_rows.append(
                        {
                            "Country": country,
                            "spread_id": spread_id,
                            "date": g.iloc[i]["DATE_OF_FINANCIALS"],
                            "Alpha": alpha,
                            "pred_change": pred_interest_change,
                            "actual_change": g.iloc[i]["future_interest_change"],
                        }
                    )

            for i in range(len(agg_data)):
                window = agg_data
                alpha = compute_alpha(window, country, alpha_min, alpha_max)
                actual_mev_diff = agg_data.iloc[i]["MEV_diff"]
                pred_interest_change = alpha * actual_mev_diff
                agg_bt_rows.append(
                    {
                        "Country": country,
                        "date": agg_data.iloc[i]["DATE_OF_FINANCIALS"],
                        "Alpha": alpha,
                        "pred_change": pred_interest_change,
                        "actual_change": agg_data.iloc[i]["future_interest_change"],
                    }
                )

            if globalmodel:
                # Handle global model: look up alpha from the regional summary
                regional_country_list = []
                for (
                    key,
                    values,
                ) in (
                    country_group_mapping.items()
                ):  # key refers to region, values refers to countries
                    regional_country_list = list(set(regional_country_list + values))
                    if country in regional_country_list:
                        for key, values in country_group_mapping.items():
                            if country in values:
                                summary_alpha = summary_testing[
                                    summary_testing["Country"] == key
                                ]["Alpha"].values[0]
                    else:
                        summary_alpha = summary_testing[
                            summary_testing["Country"] == "All countries average"
                        ]["Alpha"].values[0]
            else:
                if country in summary_testing["Country"].values:
                    summary_alpha = summary_testing[
                        summary_testing["Country"] == country
                    ]["Alpha"].values[0]
                else:
                    summary_alpha = summary_testing[
                        summary_testing["Country"] == "Others"
                    ]["Alpha"].values[0]

            for i in range(len(agg_data)):
                window = agg_data
                alpha = compute_alpha(window, country, alpha_min, alpha_max)
                actual_mev_diff = agg_data.iloc[i]["MEV_diff"]
                pred_interest_change = alpha * actual_mev_diff
                summary_bt_rows.append(
                    {
                        "Country": country,
                        "date": agg_data.iloc[i]["DATE_OF_FINANCIALS"],
                        "Alpha": summary_alpha,
                        "pred_change": pred_interest_change,
                        "actual_change": agg_data.iloc[i]["future_interest_change"],
                    }
                )

        else:
            # Rolling-window backtesting: use WINDOW most recent years to compute alpha
            for spread_id, g in id_data.groupby("spread_id"):
                if len(g) < WINDOW:
                    continue
                for i in range(WINDOW, len(g)):
                    window = g.iloc[i - WINDOW : i]
                    alpha = compute_alpha(window, country, alpha_min, alpha_max)
                    actual_mev_diff = g.iloc[i]["MEV_diff"]
                    pred_interest_change = alpha * actual_mev_diff
                    id_bt_rows.append(
                        {
                            "Country": country,
                            "spread_id": spread_id,
                            "date": g.iloc[i]["DATE_OF_FINANCIALS"],
                            "Alpha": alpha,
                            "pred_change": pred_interest_change,
                            "actual_change": g.iloc[i]["future_interest_change"],
                        }
                    )

            for i in range(WINDOW, len(agg_data)):
                window = agg_data.iloc[i - WINDOW : i]
                alpha = compute_alpha(window, country, alpha_min, alpha_max)
                actual_mev_diff = agg_data.iloc[i]["MEV_diff"]
                pred_interest_change = alpha * actual_mev_diff
                agg_bt_rows.append(
                    {
                        "Country": country,
                        "date": agg_data.iloc[i]["DATE_OF_FINANCIALS"],
                        "Alpha": alpha,
                        "pred_change": pred_interest_change,
                        "actual_change": agg_data.iloc[i]["future_interest_change"],
                    }
                )

            if country in summary_testing["Country"].values:
                summary_alpha = summary_testing[
                    summary_testing["Country"] == country
                ]["Alpha"].values[0]
            else:
                summary_alpha = summary_testing[
                    summary_testing["Country"] == "Others"
                ]["Alpha"].values[0]

            for i in range(len(agg_data)):
                window = agg_data
                actual_mev_diff = agg_data.iloc[i]["MEV_diff"]
                pred_interest_change = summary_alpha * actual_mev_diff
                summary_bt_rows.append(
                    {
                        "Country": country,
                        "date": agg_data.iloc[i]["DATE_OF_FINANCIALS"],
                        "Alpha": summary_alpha,
                        "pred_change": pred_interest_change,
                        "actual_change": agg_data.iloc[i]["future_interest_change"],
                    }
                )

    id_alpha_ts_df = pd.DataFrame(id_bt_rows).dropna()
    agg_alpha_ts_df = pd.DataFrame(agg_bt_rows).dropna()
    summary_ts_df = pd.DataFrame(summary_bt_rows).dropna()

    # Entity-level backtest metrics
    id_rank_ic = id_alpha_ts_df["pred_change"].corr(
        id_alpha_ts_df["actual_change"], method="spearman"
    )
    id_alpha_ts_df["rank_ic"] = id_rank_ic
    id_alpha_ts_df["MSE"] = (
        id_alpha_ts_df["pred_change"] - id_alpha_ts_df["actual_change"]
    ) ** 2
    id_alpha_ts_df["MAE"] = (
        id_alpha_ts_df["pred_change"] - id_alpha_ts_df["actual_change"]
    ).abs()
    rss_id = (
        (id_alpha_ts_df["actual_change"] - id_alpha_ts_df["pred_change"]) ** 2
    ).sum()
    tss_id = (
        (id_alpha_ts_df["actual_change"] - id_alpha_ts_df["actual_change"].mean()) ** 2
    ).sum()
    id_alpha_ts_df["R2"] = 1 - rss_id / tss_id

    # Aggregated backtest metrics
    agg_rank_ic = agg_alpha_ts_df["pred_change"].corr(
        agg_alpha_ts_df["actual_change"], method="spearman"
    )
    agg_alpha_ts_df["rank_ic"] = agg_rank_ic
    agg_alpha_ts_df["MSE"] = (
        agg_alpha_ts_df["pred_change"] - agg_alpha_ts_df["actual_change"]
    ) ** 2
    agg_alpha_ts_df["MAE"] = (
        agg_alpha_ts_df["pred_change"] - agg_alpha_ts_df["actual_change"]
    ).abs()
    rss_agg = (
        (agg_alpha_ts_df["actual_change"] - agg_alpha_ts_df["pred_change"]) ** 2
    ).sum()
    tss_agg = (
        (agg_alpha_ts_df["actual_change"] - agg_alpha_ts_df["actual_change"].mean()) ** 2
    ).sum()
    agg_alpha_ts_df["R2"] = 1 - rss_agg / tss_agg

    # Summary-level backtest metrics
    rank_ic = summary_ts_df["pred_change"].corr(
        summary_ts_df["actual_change"], method="spearman"
    )
    summary_ts_df["rank_ic"] = rank_ic
    summary_ts_df["MSE"] = (
        summary_ts_df["pred_change"] - summary_ts_df["actual_change"]
    ) ** 2
    summary_ts_df["MAE"] = (
        summary_ts_df["pred_change"] - summary_ts_df["actual_change"]
    ).abs()
    rss = (
        (summary_ts_df["actual_change"] - summary_ts_df["pred_change"]) ** 2
    ).sum()
    tss = (
        (summary_ts_df["actual_change"] - summary_ts_df["actual_change"].mean()) ** 2
    ).sum()
    summary_ts_df["R2"] = 1 - rss / tss

    # --- Generate charts ---
    # Prepare data for country-level bar chart
    country_output_LCY = country_output[country_output["Alpha Base"] == "LCY"]
    country_output_LCY = country_output_LCY.rename(columns={"Alpha": "LCY"})
    country_output_LCY = country_output_LCY.drop(
        ["Alpha Base", "Driver", "Sector", "Sub-sector", "As of Date"], axis=1
    )

    country_output_FCY = country_output[country_output["Alpha Base"] == "FCY (USD)"]
    country_output_FCY = country_output_FCY.rename(columns={"Alpha": "FCY"})
    country_output_FCY = country_output_FCY.drop(
        ["Alpha Base", "Driver", "Sector", "Sub-sector", "As of Date"], axis=1
    )

    country_output_bchart = pd.merge(
        country_output_LCY, country_output_FCY, on="Country"
    )

    # Create country-level IE bar chart
    plt.figure(figsize=(16, 10))

    index = np.arange(len(country_output_bchart["Country"]))
    bar_width = 0.35
    opacity = 0.8

    rects1 = plt.bar(
        index + bar_width,
        country_output_bchart["LCY"],
        bar_width,
        alpha=opacity,
        color="royalblue",
        label="LCY",
    )

    rects2 = plt.bar(
        index + 2 * bar_width + 0.05,
        country_output_bchart["FCY"],
        bar_width,
        alpha=opacity,
        color="darkorange",
        label="FCY",
    )

    plt.title(f"Alpha Parameter - {sector}", fontsize=16)
    plt.xticks(
        index + 3 * bar_width / 2,
        country_output_bchart["Country"],
        fontsize=12,
    )
    plt.xticks(wrap=True)
    plt.legend(loc="upper center", ncol=2)

    add_labels_LCY(country_output_bchart["Country"], country_output_bchart["LCY"], bar_width)
    add_labels_FCY(country_output_bchart["Country"], country_output_bchart["FCY"], bar_width)

    portfolio_output_bchart = data_for_chart(portfolio_output, "Portfolio")
    LC_CC_output_bchart = data_for_chart(LC_CC_split_output, "Country")
    MC_output_bchart = data_for_chart(MC_split_output, "Country")

    summary_all = pd.concat(
        [summary_1, summary_2, summary_3, summary_4, summary_5, summary_6, summary_7, summary_8],
        ignore_index=True,
    )

    # ---- Step 1: Define preferred region order ----
    preferred_order = top_countries_1 + ["Others"]

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

    datapoints_wide_renamed = datapoints_wide.add_suffix("-datapoints")
    spread_ids_wide_renamed = spread_ids_wide.add_suffix("-spread_ids")
    concat_df = pd.concat([datapoints_wide_renamed, spread_ids_wide_renamed], axis=1)

    # ---- Step 4: Create wide table for MC, LC, CC ----
    portfolio_table = (
        summary_all.groupby("Step")[["LC+CC datapoints", "MC datapoints"]].sum()
    )

    steps_df = pd.concat([concat_df, portfolio_table], axis=1)
    steps_df = steps_df.reset_index()

    # --- Write all outputs to Excel ---
    os.makedirs(os.path.dirname(consolid_path), exist_ok=True)
    with pd.ExcelWriter(consolid_path, engine="openpyxl") as writer:
        all_country_frame.to_excel(writer, sheet_name="all country modelling data", index=False)
        agg_frame.to_excel(writer, sheet_name="aggregate modelling data", index=False)
        interest_data_df.to_excel(writer, sheet_name="interest data", index=False)
        leid_output.to_excel(writer, sheet_name="LEID level output", index=False)
        country_output.to_excel(writer, sheet_name="Country level output", index=True)
        portfolio_output.to_excel(writer, sheet_name="Portfolio level output", index=True)
        steps_df.to_excel(writer, sheet_name="Data cleaning steps", index=False)
        summary_ts_df.to_excel(writer, sheet_name="Backtest full data", index=False)
        agg_alpha_ts_df.to_excel(writer, sheet_name="Backtest aggregated data", index=False)
        id_alpha_ts_df.to_excel(writer, sheet_name="Backtest ID level", index=False)

        wb = writer.book
        outputChart_excel(
            data=interest_data_df["interest_rate"],
            chartTitle="Interest Rate Distribution full data(before filtering >0.5)",
            workbook=wb,
            sheet_name="Interest rate charts full",
            bin_edges=np.arange(0, 1.2, 0.02),
            percentiles_for_chart=percentiles_for_chart,
            xrange=(0, 1),
        )

        filtered_data = interest_data_df.loc[
            interest_data_df["interest_expense_issue"] == "F", "interest_rate"
        ]
        outputChart_excel(
            data=filtered_data,
            chartTitle="Interest Rate Distribution full data(after filtering >0.5)",
            workbook=wb,
            sheet_name="Interest rate charts filtered",
            bin_edges=np.arange(0, 0.6, 0.02),
            percentiles_for_chart=percentiles_for_chart,
            xrange=(0, 0.6),
        )

        final_chart(
            data=country_output_bchart,
            split_type="Country",
            chartTitle=f"Alpha Parameter - {sector}",
            workbook=wb,
            sheet_name="Final model chart (Country Split)",
        )

        final_chart(
            data=portfolio_output_bchart,
            split_type="Portfolio",
            chartTitle=f"Alpha Parameter - {sector}",
            workbook=wb,
            sheet_name="Final model chart (Portfolio Split)",
        )

        final_chart(
            data=LC_CC_output_bchart,
            split_type="Country",
            chartTitle=f"Alpha Parameter - {sector}",
            workbook=wb,
            sheet_name="Final model chart (LC_CC)",
        )

        final_chart(
            data=MC_output_bchart,
            split_type="Country",
            chartTitle=f"Alpha Parameter - {sector}",
            workbook=wb,
            sheet_name="Final model chart (MC)",
        )

    print(f"results excel saved at: {consolid_path}")
    # ===================================================================

if __name__ == "__main__":
    for sector in [
        "O&G",
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
    sys.stdout = TimestampLog("IE_master")
