import pandas as pd
import numpy as np
from datetime import datetime

from ie_data_processing import process_data_country_sector


# ============================================================================
# MODELLING HELPERS
# ============================================================================


def get_corr_df(data, country, aggregate, id_column_name, alpha_min, alpha_max):
    """Compute per-entity (or aggregate) correlation, sensitivity, and Alpha against central bank rate.

    Returns a DataFrame with columns including Sensitivity, Correlation, Alpha, and Alpha_US.
    """
    if not aggregate:
        data["No. of data points"] = data[id_column_name]
        std_df = data.groupby(id_column_name).agg(
            {
                "No. of data points": "count",
                "country_of_risk": "first",
                "interest_rate": "std",
                f"{country}_Monetary policy or key interest rate_4QMA": "std",
                "Monetary policy or key interest rate_4QMA_US": "std",
                "irb_ead": "first",
            }
        )
        std_df["Sensitivity"] = (
            std_df["interest_rate"]
            / std_df[f"{country}_Monetary policy or key interest rate_4QMA"]
        )
        std_df["Sensitivity_US"] = (
            std_df["interest_rate"]
            / std_df["Monetary policy or key interest rate_4QMA_US"]
        )
    else:
        data["No. of data points"] = len(data["DATE_OF_FINANCIALS"])
        std_df = data.agg(
            {
                "No. of data points": "count",
                "country_of_risk": lambda x: x.iloc[0],
                "interest_rate": "std",
                f"{country}_Monetary policy or key interest rate_4QMA": "std",
                "Monetary policy or key interest rate_4QMA_US": "std",
                "irb_ead": lambda x: x.iloc[0],
            }
        )
        std_df["Sensitivity"] = (
            std_df["interest_rate"]
            / std_df[f"{country}_Monetary policy or key interest rate_4QMA"]
        )
        std_df["Sensitivity_US"] = (
            std_df["interest_rate"]
            / std_df["Monetary policy or key interest rate_4QMA_US"]
        )
        std_df = std_df.to_dict()

    if not aggregate:
        correlation_per_id = data.groupby(id_column_name).apply(
            lambda x: x["interest_rate"].corr(
                x[f"{country}_Monetary policy or key interest rate_4QMA"]
            )
        )

        correlation_per_id_US = data.groupby(id_column_name).apply(
            lambda x: x["interest_rate"].corr(
                x[f"Monetary policy or key interest rate_4QMA_US"]
            )
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
        correlation_agg = data["interest_rate"].corr(
            data[f"{country}_Monetary policy or key interest rate_4QMA"]
        )
        correlation_agg_US = data["interest_rate"].corr(
            data[f"Monetary policy or key interest rate_4QMA_US"]
        )

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
            "interest_rate": "Interest Rate Std Dev",
            f"{country}_Monetary policy or key interest rate_4QMA": "Central bank Interest Rate Std Dev",
        }
    )

    return all_df


def compute_alpha(window_df, country, alpha_min, alpha_max):
    """Compute the Alpha parameter for a given data window and country.

    Alpha = Correlation(entity_rate, central_bank_rate) x Sensitivity,
    clipped to [alpha_min, alpha_max].
    """
    corr = window_df["interest_rate"].corr(
        window_df[f"{country}_Monetary policy or key interest rate_4QMA"]
    )
    sensitivity = (
        window_df["interest_rate"].std()
        / window_df[f"{country}_Monetary policy or key interest rate_4QMA"].std()
    )
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

        if not aggregate:
            final = final.merge(
                interest_data[["spread_id", "Portfolio"]],
                on="spread_id",
                how="left",
            )
    return final


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


# ============================================================================
# MAIN MODELLING PIPELINE
# ============================================================================


def run_modelling(interest_data, agg_interest_data, MEVdata, int_expense_issue, IE_config):
    """Run entity-level Alpha computation, country/portfolio aggregation, and output formatting.

    Returns a dict with all modelling outputs needed by downstream steps.
    """
    sector = IE_config.sector
    id_column_name = IE_config.id_column_name
    alpha_min = IE_config.alpha_min
    alpha_max = IE_config.alpha_max
    isWeighted = IE_config.isWeighted
    top_countries = IE_config.top_countries
    country_group_mapping = IE_config.country_group_mapping
    globalmodel = IE_config.globalmodel

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
        regional_country_list = []
        global_final = pd.DataFrame(columns=country_level_df.columns)
        for key, values in country_group_mapping.items():
            regional_country_list = list(set(regional_country_list + values))
            country_level_df2 = country_level_df.loc[
                country_level_df.index.isin(values)
            ]

            country_level_df2["Alpha"] = np.where(
                country_level_df2["Alpha"] == 0.0,
                country_level_df2["Alpha_US"],
                country_level_df2["Alpha"],
            )

            region_dict = {
                "Alpha": sum(
                    country_level_df2["Alpha"]
                    * country_level_df2["irb_ead"]
                    / country_level_df2["irb_ead"].sum()
                ),
                "Alpha_US": sum(
                    country_level_df2["Alpha_US"]
                    * country_level_df2["irb_ead"]
                    / country_level_df2["irb_ead"].sum()
                ),
                "irb_ead": country_level_df2["irb_ead"].sum(),
            }
            global_final.loc[key] = region_dict

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

        other_dict = {
            "Alpha": sum(
                country_level_df2["Alpha"]
                * country_level_df2["irb_ead"]
                / country_level_df2["irb_ead"].sum()
            ),
            "Alpha_US": sum(
                country_level_df2["Alpha_US"]
                * country_level_df2["irb_ead"]
                / country_level_df2["irb_ead"].sum()
            ),
            "irb_ead": country_level_df2["irb_ead"].sum(),
        }  # noqa: F841

        country_level_df = global_final[["Alpha", "Alpha_US"]]

    else:
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

        other_dict = {
            "Alpha": sum(
                country_level_df2["Alpha"]
                * country_level_df2["irb_ead"]
                / country_level_df2["irb_ead"].sum()
            ),
            "Alpha_US": sum(
                country_level_df2["Alpha_US"]
                * country_level_df2["irb_ead"]
                / country_level_df2["irb_ead"].sum()
            ),
            "irb_ead": country_level_df2["irb_ead"].sum(),
        }
        country_level_df1.loc["Others"] = other_dict
        country_level_df = country_level_df1[["Alpha", "Alpha_US"]]

    # --- Compute all-country average and format outputs ---
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

    country_output = country_output[[
        "Driver", "Sector", "Sub-sector", "Country", "Alpha Base", "Alpha", "As of Date",
    ]]

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

    portfolio_output = portfolio_output[[
        "Driver", "Sector", "Sub-sector", "Portfolio", "Alpha Base", "Alpha", "As of Date",
    ]]

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

    for df, name in [(LC_CC_split_output, "LC_CC"), (MC_split_output, "MC")]:
        df["Driver"] = "Interest Expense Driver"
        df["Sector"] = sector
        df["Sub-sector"] = "All"
        df["As of Date"] = current_date
        df.rename(columns={"Value": "Alpha"}, inplace=True)

    new_order = [
        "Driver", "Sector", "Sub-sector", "Country", "Alpha Base", "Alpha", "As of Date",
    ]
    agg_output = agg_output[new_order]
    LC_CC_split_output = LC_CC_split_output[new_order]
    MC_split_output = MC_split_output[new_order]

    return {
        "all_country_frame": all_country_frame,
        "agg_frame": agg_frame,
        "country_level_df": country_level_df,
        "portfolio_level_df": portfolio_level_df,
        "both_level_df": both_level_df,
        "leid_output": leid_output,
        "country_output": country_output,
        "portfolio_output": portfolio_output,
        "agg_output": agg_output,
        "LC_CC_split_output": LC_CC_split_output,
        "MC_split_output": MC_split_output,
        "summary_testing": summary_testing,
        "current_date": current_date,
    }
