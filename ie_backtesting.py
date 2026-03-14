import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn.metrics import mean_absolute_error, mean_squared_error

from ie_modelling import compute_alpha


# ============================================================================
# BACKTESTING HELPERS
# ============================================================================


def cal_country_stats_with_r2(data):
    """Compute backtesting statistics: top-minus-bottom bucket spread, R², MSE, and MAE."""
    buckets = pd.qcut(data["pred_change"], 5, duplicates="drop")
    bucket_perf = data.groupby(buckets)["actual_change"].mean()

    if len(bucket_perf) < 2:
        top_minus_bottom = np.nan
    else:
        top_minus_bottom = bucket_perf.iloc[-1] - bucket_perf.iloc[0]

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


# ============================================================================
# MAIN BACKTESTING PIPELINE
# ============================================================================


def run_backtesting(processed_id, processed_agg, modelling_results, IE_config):
    """Run entity- and aggregate-level backtesting with rolling or full-history alpha.

    processed_id: concatenated entity-level DataFrame from load_and_clean_data.
    processed_agg: concatenated aggregate-level DataFrame from load_and_clean_data.
    Returns:
        id_alpha_ts_df: entity-level backtest results with metrics
        agg_alpha_ts_df: aggregate-level backtest results with metrics
        summary_ts_df: summary-level backtest results with metrics
    """
    id_column_name = IE_config.id_column_name
    alpha_min = IE_config.alpha_min
    alpha_max = IE_config.alpha_max
    applyWindow = IE_config.applyWindow
    globalmodel = IE_config.globalmodel
    country_group_mapping = IE_config.country_group_mapping

    summary_testing = modelling_results["summary_testing"]

    WINDOW = 3  # Rolling window of 3 years for backtesting
    id_bt_rows = []
    agg_bt_rows = []
    summary_bt_rows = []

    for country, id_data in processed_id.groupby("country_of_risk"):
        agg_data = processed_agg[processed_agg["country_of_risk"] == country]

        # LEID-level: compute future changes
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

        # Aggregate-level: compute future changes
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
                regional_country_list = []
                for key, values in country_group_mapping.items():
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

    # --- Entity-level backtest metrics ---
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

    # --- Aggregated backtest metrics ---
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

    # --- Summary-level backtest metrics ---
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

    return id_alpha_ts_df, agg_alpha_ts_df, summary_ts_df
