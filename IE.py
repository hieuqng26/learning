import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm

plt.rcdefaults()
from datetime import datetime
import warnings
from matplotlib.backends.backend_pdf import PdfPages
import sys
from log_file import TimestampLog
from io import BytesIO
from openpyxl.drawing.image import Image
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

warnings.filterwarnings("ignore")

from IE_config import *


def interest_expense_run(sector_name):

    # --- Configuration ---
    IE_config = SECTORS[sector_name]

    sector = IE_config.sector
    sector_short = IE_config.sector_short
    id_column_name = IE_config.id_column_name
    ISIC_mapping = IE_config.ISIC_mapping
    exclude_IE_Zero = IE_config.exclude_IE_Zero
    globalmodel = IE_config.globalmodel
    groupCountry = IE_config.groupCountry

    # file paths
    interest_file_path = IE_config.interest_file_path
    MEV_file_path = IE_config.MEV_file_path
    isic_file_path = IE_config.isic_file_path

    output_temp = r"C:\Users\1665642\OneDrive - Standard Chartered Bank\Documents\test_run"
    output_path = windows_long_path(
        f"{output_temp}/{sector}/interest_expense_{sector_short}.xlsx"
    )
    pdf_path = windows_long_path(
        f"{output_temp}/{sector}/interest_expense_{sector_short}.pdf"
    )
    sum_path = windows_long_path(
        f"{output_temp}/{sector}/IE_Data_Points_{sector_short}.xlsx"
    )
    consolid_path = windows_long_path(
        f"{output_temp}/{sector}/consolidated_results_{sector_short}.xlsx"
    )

    # output_path = windows_long_path(
    #     f"{OUT_DIR}/{sector}/interest_expense_{sector_short}.xlsx"
    # )
    # pdf_path = windows_long_path(
    #     f"{OUT_DIR}/{sector}/interest_expense_{sector_short}.pdf"
    # )
    # sum_path = windows_long_path(
    #     f"{OUT_DIR}/{sector}/IE_Data_Points_{sector_short}.xlsx"
    # )

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

    # --- Run ---
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
            #  GLOBAL MODEL: Map full RA_Industry and sub_segment
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
                    isic_data_filtered["ISIC Code"].unique()
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
        # Build reverse mapping: each country -> EU
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
        # Build reverse mapping: each country -> group label
        reverse_country_map = {}
        for group_label, countries in country_group_mapping.items():
            for country in countries:
                reverse_country_map[country] = group_label

        # Apply mapping to financials['country_of_risk']
        interest_data["Region_group"] = interest_data["country_of_risk"].apply(
            lambda x: reverse_country_map.get(x, x)
        )

    ############# Define the summarize_step function to output the datapoints summary table######
    def summarize_step(
        df, top_countries_1, c_column_name, step_name, id_column_name="spread_id"
    ):
        financials = df.copy()

        # Step 1: Create a clean grouping column
        region_list = top_countries_1 + ["Others"]
        financials["__region__"] = financials[c_column_name].apply(
            lambda x: x if x in top_countries_1 else "Others"
        )

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

    ######################
    #  convert 'irb_ead' to float with coercion of invalid values
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
    # Print row count before dropping NaNs
    print("Rows before dropping NA:", len(interest_data))
    summary_1 = summarize_step(
        interest_data,
        top_countries_1,
        c_column_name,
        step_name="Step 1: Rows before dropping NA",
    )

    # Drop rows where InterestExpense or TotalDebt is NaN
    interest_data = interest_data.dropna(subset=["InterestExpense", "TotalDebt"])
    # Print row count after dropping NaNs
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

    interest_data = interest_data.sort_values(
        by=[id_column_name, "Year", "Month"], ascending=[True, True, False]
    )
    interest_data = interest_data.drop_duplicates(
        subset=[id_column_name, "Year"], keep="first"
    )
    print(f"shape before drop the quarterly data': {interest_data.shape}")
    print(f"shape af drop the quarterly data': {interest_data.shape}")

    summary_3 = summarize_step(
        interest_data,
        top_countries_1,
        c_column_name,
        step_name="Step 3: Rows after keep one data point for one year",
    )

    ###########################
    interest_data = interest_data[interest_data.irb_ead != 0]
    summary_4 = summarize_step(
        interest_data,
        top_countries_1,
        c_column_name,
        step_name="Step 4: Rows after filter  irb!=0",
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
    # check interest expense too large -----> interest expense/totalDebt > 0.5, data issue, need to be handled separately

    summary_6 = summarize_step(
        interest_data,
        top_countries_1,
        c_column_name,
        step_name="Step 6: Rows after filter ie !=0",
    )
    interest_data["interest_rate"] = (
        interest_data["InterestExpense"] / interest_data["TotalDebt"]
    )

    interest_data_df = interest_data[["spread_id","DATE_OF_FINANCIALS", "InterestExpense","TotalDebt", "interest_rate"]]
    interest_data_df["interest_expense_issue"] = interest_data_df["interest_rate"].apply(lambda x: 'T' if x>0.5 else 'F')

    # filter modelling data that interest_rate <=0.5
    int_expense_issue = interest_data[interest_data["interest_rate"] > 0.5]
    interest_data = interest_data[interest_data["interest_rate"] <= 0.5]

    summary_7 = summarize_step(
        interest_data,
        top_countries_1,
        c_column_name,
        step_name="Step 7: Rows after filter interest_rate<=0.5",
    )

    ## filter for interest rate data after year 2018
    int_before_2018 = interest_data[interest_data["Year"] < 2018]
    interest_data = interest_data[interest_data["Year"] >= 2018]

    summary_8 = summarize_step(
        interest_data,
        top_countries_1,
        c_column_name,
        step_name="Step 8: Rows after filter interest_rate year before 2018",
    )

    # -------------------
    def MEV_data_processing(country, MEVdata):
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
   
    # -------------------
    def MEV_data_processing_before2018(country, MEVdata):
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

    # --------

    def process_data_country_sector(
        interest_data,
        MEVdata,
        country,
        sector,
    ):
        if sector == "Global":
            interest_data = interest_data[((interest_data.country_of_risk == country))]
        else:
            interest_data = interest_data[
                (
                    (interest_data.RA_Industry == sector)
                    & (interest_data.country_of_risk == country)
                )
            ]

        # MEV data select
        MEVdata_groupby_US = MEV_data_processing("US", MEVdata)
        MEVdata_groupby_US = MEVdata_groupby_US.rename(
            columns={
                "US_Monetary policy or key interest rate_4QMA": "Monetary policy or key interest rate_4QMA_US"
            }
        )
        country_data_avaliable_flag = 0
        try:
            MEVdata_groupby = MEV_data_processing(country, MEVdata)

        except:
            # print(f"Central bank data for country {country} is not avaliable!")
            MEVdata_groupby = MEVdata_groupby_US
            country_data_avaliable_flag = 1
        interest_data["DATE_OF_FINANCIALS"] = pd.to_datetime(
            interest_data["DATE_OF_FINANCIALS"], format="%Y-%m-%d"
        )
        final = pd.merge(
            interest_data,
            MEVdata_groupby,
            left_on="DATE_OF_FINANCIALS",
            right_on="Date",
        )
        if country_data_avaliable_flag == 1:
            final[f"{country}_Monetary policy or key interest rate_4QMA"] = np.nan
        else:
            final = pd.merge(
                final,
                MEVdata_groupby_US,
                left_on="DATE_OF_FINANCIALS",
                right_on="Date",
            )

        leid_counts = final.groupby(id_column_name).size()
        leid_wanted = leid_counts[leid_counts > 3].index
        error_df = final[~final[id_column_name].isin(leid_wanted)]
        final = final[final[id_column_name].isin(leid_wanted)]
        error_df = pd.concat([error_df, int_expense_issue], ignore_index=True)
        return final

    # ---------------

    def get_corr_df(data, country):
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
        std_df["LEID Sensitvity"] = (
            std_df["interest_rate"]
            / std_df[f"{country}_Monetary policy or key interest rate_4QMA"]
        )
        std_df["LEID Sensitvity_US"] = (
            std_df["interest_rate"]
            / std_df["Monetary policy or key interest rate_4QMA_US"]
        )
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

        all_df["Alpha"] = (all_df["Correlation"] * all_df["LEID Sensitvity"]).clip(
            lower=alpha_min, upper=alpha_max
        )
        all_df["Alpha_US"] = (
            all_df["Correlation_US"] * all_df["LEID Sensitvity_US"]
        ).clip(lower=alpha_min, upper=alpha_max)
        all_df = all_df.rename(
            columns={
                "country_of_risk": "Country",
                "interest_rate": "LEID Interest Rate Std Dev",
                f"{country}_Monetary policy or key interest rate_4QMA": "Central bank Interest Rate Std Dev",
            }
        )

        return all_df[
            [
                id_column_name,
                "No. of data points",
                "Country",
                "irb_ead",
                "LEID Interest Rate Std Dev",
                "Monetary policy or key interest rate_4QMA_US",
                "LEID Sensitvity_US",
                "Correlation_US",
                "Alpha_US",
                "Central bank Interest Rate Std Dev",
                "LEID Sensitvity",
                "Correlation",
                "Alpha",
            ]
        ]
   
   
    def compute_alpha(window_df, country):
        corr = window_df["interest_rate"].corr(window_df[f"{country}_Monetary policy or key interest rate_4QMA"])
        sensitivity = window_df["interest_rate"].std() / window_df[f"{country}_Monetary policy or key interest rate_4QMA"].mean()
        alpha = corr * sensitivity
        return np.clip(alpha, alpha_min, alpha_max)

    # ----------
    def interest_expense(interest_data, MEVdata, country, sector):
        data = process_data_country_sector(interest_data, MEVdata, country, sector)
        if len(data) == 0:
            final = pd.DataFrame()
        else:
            final = get_corr_df(data, country)
        return final

    # ---------------
    all_country_frame = pd.DataFrame(
        columns=[
            id_column_name,
            "No. of data points",
            "Country",
            "LEID Interest Rate Std Dev",
            "Central bank Interest Rate Std Dev",
            "LEID Sensitvity",
            "Correlation",
            "Alpha",
            "Alpha_US",
        ]
    )

    ## backtesting ------------
    ## Apply rolling window to calculate alpha ----------
    WINDOW = 3
    results = []
    bt_rows = []
    for country in interest_data.country_of_risk.unique():
        data = process_data_country_sector(interest_data, MEVdata, country, sector)
        data = data.sort_values(["spread_id", "DATE_OF_FINANCIALS"])
        data["future_interest_change"] = (
            data
            .groupby("spread_id")["interest_rate"]
            .shift(-1) - data["interest_rate"]
            )
       
        for spread_id, g in data.groupby("spread_id"):
           if len(g) <= WINDOW:
               continue
           for i in range(WINDOW, len(g) -1):
               window = g.iloc[i-WINDOW:i]
               alpha = compute_alpha(window, country)
               bt_rows.append({
                   "Country": country,
                   "spread_id": spread_id,
                   "date":g.iloc[i]["DATE_OF_FINANCIALS"],
                   "Alpha": alpha,
                   "future_interest_change": g.iloc[i]["future_interest_change"]
               })
    alpha_ts_df = pd.DataFrame(bt_rows).dropna()
    rank_ic = alpha_ts_df["Alpha"].corr(alpha_ts_df["future_interest_change"], method = "spearman")
    alpha_ts_df["rank_ic"] = rank_ic

    # alpha_ts_df["alpha_bucket"]=pd.qcut(alpha_ts_df["Alpha"],5,duplicates="drop")
    # bucket_perf = alpha_ts_df.groupby("alpha_bucket")["future_interest_change"].mean()
    # top_minus_bottom = bucket_perf.iloc[-1] - bucket_perf.iloc[0]

    def cal_country_stats_with_r2(x):
        buckets = pd.qcut(x["Alpha"],5,duplicates="drop")
        bucket_perf = x.groupby(buckets)["future_interest_change"].mean()

        if len(bucket_perf) < 2:
            top_minus_bottom = np.nan
        else:
            top_minus_bottom = bucket_perf.iloc[-1] - bucket_perf.iloc[0]

         ## OLS
        X = sm.add_constant(x["Alpha"])
        y = x["future_interest_change"]
        model = sm.OLS(y,X, missing ="drop").fit()
        y_pred = model.predict(X)

        mse_model = np.mean((y - y_pred)**2)
        mse_benchmark = np.mean((y - np.mean(y))**2)
        r2_oos = 1 - mse_model/mse_benchmark

        return pd.Series({
            "rank_ic": x["Alpha"].corr(x["future_interest_change"], method = "spearman"),
            "n_obs": len(x),
            "top_minus_bottom": top_minus_bottom,
            "OOS_R2": r2_oos
        })

    bt_all_country_df = (
        alpha_ts_df
        .groupby("Country")
        .apply(cal_country_stats_with_r2)
        .reset_index()
    )

    bt_final_all_df = (
        alpha_ts_df.groupby(["Country","spread_id"])
        .agg(
            avg_alpha= ("Alpha", "mean"),
            alpha_std = ("Alpha", "std"),
            n_obs =("Alpha", "count")
        )
        .reset_index()
    )

    full_summary = cal_country_stats_with_r2(alpha_ts_df).to_frame().T
    full_summary["key"] =1
    alpha_ts_df["key"] = 1
    full_df = alpha_ts_df.merge(full_summary, on="key", how="left").drop(columns="key")

    print(full_df.head())
    print(bt_all_country_df.head())
    print(bt_final_all_df.head())
    print(rank_ic)


    ##---------------------------------------  

    for country in interest_data.country_of_risk.unique():
        # print("Country to be processed: ", country)
        data = interest_expense(interest_data, MEVdata, country, sector=sector)
        if len(data) > 0:
            all_country_frame = pd.concat(
                [all_country_frame, data], axis=0, ignore_index=True
            )        
   
    # --------
    if not isWeighted:
        # unweighted
        country_level_df = all_country_frame.groupby("Country").agg(
            {
                "Alpha": "mean",
                "Alpha_US": "mean",
            }
        )
    else:
        # weighted
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
######################################################################################################################
    ## validation set using before year 2018
    def validate_before2018(interest, mevData, alpha_df, add_metrics=True):
        interest = interest.sort_values(["spread_id", "DATE_OF_FINANCIALS"])
        interest["actual_interest_change"] = interest.groupby("spread_id")["interest_rate"].diff()
        interest["actual_interest_change"] = interest["actual_interest_change"].fillna(0)
        mevData = mevData.rename(columns={'Date': 'DATE_OF_FINANCIALS'})
        mevData = MEV_data_processing_before2018("US", MEVdata)
        mev_list = []
        for country in int_before_2018.country_of_risk.unique():
            try:
                mev_country = MEV_data_processing_before2018(country, MEVdata)

            except:
                # print(f"Central bank data for country {country} is not avaliable!")
                mev_country = mevData
            mev_country["country_of_risk"] = country
            mev_list.append(mev_country)
        mevData = pd.concat(mev_list, ignore_index=True)
        rate_cols = [c for c in mevData.columns if c.endswith('_Monetary policy or key interest rate_4QMA')]
        mevData = mevData.rename(columns={'Date': 'DATE_OF_FINANCIALS'})

        mev_long = mevData.melt(
            id_vars=['DATE_OF_FINANCIALS','country_of_risk'],
            value_vars = rate_cols,
            var_name='rate_col',
            value_name='monetary_interest'
        )
        mev_long = mev_long.drop(columns=['rate_col'])

        df = interest.merge(
            mev_long,
            on=['country_of_risk','DATE_OF_FINANCIALS'],
            how='left'
        )
        df = df.merge(alpha_df[['spread_id','Alpha']], on='spread_id', how='left')
        df['expected_interest_rate'] = df['monetary_interest'] * df['Alpha']
        df['expected_interest_rate'] = df['expected_interest_rate'].fillna(0)
       
        if add_metrics:
            metrics_list = []
            for i in df['spread_id'].unique():
                temp = df[df['spread_id'] == i]
                y_true = temp['actual_interest_change']
                y_pred = temp['expected_interest_rate']
                metrics_list.append({
                    'spread_id': i,
                    'r2': r2_score(y_true, y_pred),
                    'MSE': mean_squared_error(y_true,y_pred),
                    'MAE': mean_absolute_error(y_true,y_pred)
                })
            metrics_df = pd.DataFrame(metrics_list)
            df = df.merge(metrics_df, on='spread_id', how='left')
            df = df[['Year','DATE_OF_FINANCIALS','spread_id','country_of_risk','interest_rate','actual_interest_change', 'expected_interest_rate', 'Alpha', 'r2','MSE','MAE']]
            df = df.drop_duplicates(subset=['spread_id','DATE_OF_FINANCIALS'], keep='first')
        return df
   
    validate_data = validate_before2018(int_before_2018, MEVdata, all_country_frame)

    ######################################################################################################################

    # ----------
    ead_sum = all_country_frame.groupby("Country").agg({"irb_ead": "sum"})
    country_level_df = country_level_df.merge(ead_sum, how="left", on="Country")
    country_level_df["Country"] = country_level_df.index
    if globalmodel:
        # handle global model
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
        # handle for "Others"
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

    # ----------
    plt.figure(figsize=(8, 6))
    plt.bar(country_level_df.index, 100 * country_level_df.Alpha)
    plt.title(f"Country level Alpha", fontsize=16)
    plt.xlabel("Country", fontsize=14)
    plt.ylabel(f"Alpha (%)", fontsize=14)
    plt.grid(True)
    # plt.show()

    plt.figure(figsize=(8, 6))
    plt.bar(country_level_df.index, 100 * country_level_df.Alpha_US)
    plt.title(f"Country level Alpha with US rate", fontsize=16)
    plt.xlabel("Country", fontsize=14)
    plt.ylabel(f"Alpha (%)", fontsize=14)
    plt.grid(True)
    # plt.show()

    # -----------
    ## Summarize and export to files
    country_level_df.loc["All countries average"] = [
        country_level_df.Alpha.mean(),
        country_level_df.Alpha_US.mean(),
    ]

    current_date = datetime.now().strftime("%Y-%m-%d")

    leid_output = all_country_frame[["Country", id_column_name, "Alpha", "Alpha_US"]]
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
        "LEID",
        "Alpha Base",
        "Alpha",
        "As of Date",
    ]
    leid_output = leid_output[new_order]

    # ---------
    country_output = country_level_df.copy()
    if globalmodel:
        country_output["Country"] = country_output.index

    country_output.reset_index(inplace=True)
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


    # ------------------------------------------------
    # os.makedirs(os.path.dirname(output_path), exist_ok=True)
    # with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
    #     leid_output.to_excel(writer, sheet_name="LEID level output", index=False)
    #     country_output.to_excel(writer, sheet_name="Country level output", index=True)
    # print(f"results excel saved at: {output_path}")

    # ------------------------------------------------
    # Prepare data for bar chart

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

    # Create IE bar chart

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
    plt.xticks(index + 3 * bar_width / 2, country_output_bchart["Country"], fontsize=12)
    plt.xticks(wrap=True)
    plt.legend(loc="upper center", ncol=2)

    # Add labels
    def add_labels_LCY(x, y):
        for i in range(len(x)):
            lable_LCY = ((y[i] * 100).round(0)).astype("int")
            plt.text(
                i + bar_width,
                y[i] + 0.01,
                f"{lable_LCY}" + "%",
                ha="center",
                fontsize=12,
            )  # Aligning text for LCY

    def add_labels_FCY(x, y):
        for i in range(len(x)):
            lable_FCY = ((y[i] * 100).round(0)).astype("int")
            plt.text(
                i + bar_width + 0.4,
                y[i] + 0.01,
                f"{lable_FCY}" + "%",
                ha="center",
                fontsize=12,
            )  # Aligning text for FCY right of LCY

    add_labels_LCY(country_output_bchart["Country"], country_output_bchart["LCY"])
    add_labels_FCY(country_output_bchart["Country"], country_output_bchart["FCY"])

    plt.ylim((0, 1))
    plt.yticks(
        ticks=[0, 0.2, 0.4, 0.6, 0.8, 1],
        labels=["0%", "20%", "40%", "60%", "80%", "100%"],
        fontsize=12,
    )
    plt.tight_layout()
    # plt.savefig(rf"{pdf_path}")
    # plt.show()

    # # Optional: Print confirmation
    # print(f"Bar chart has been saved to {pdf_path}")

    # ------------------------------------------------

    # Display or save
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
    ):
        fig,ax = plt.subplots(figsize=figsize)

        plt.hist(
            data,
            bins=bin_edges,
            alpha = 0.7,
            color="blue",
            edgecolor ="black",
            label = "Histogram (Count)"
        )

        # Calculate percentiles
        percentile_values = [data.quantile(p / 100) for p in percentiles_for_chart]

        for i, (perc, value) in enumerate(
            zip(percentiles_for_chart, percentile_values)
        ):
            color = "green" if i == 0 else "red"
            label_text = f"{perc}th Percentile: {value:.4f}"
            plt.axvline(
                value,
                color = color,
                linestyle="--",
                linewidth = 1.5,
                label = label_text,
            )

        if xrange:
            # Set X-axis range
            ax.set_xlim(xrange[0], xrange[1])

        ax.set_title(chartTitle)
        ax.set_xlabel("Interest Rate")
        ax.set_ylabel("Frequency")
        ax.legend(fontsize=8)
        ax.grid(axis = "y", alpha = 0.75)

        imgdata = BytesIO()
        fig.savefig(imgdata, format = "png", bbox_inches="tight")
        plt.close(fig)
        imgdata.seek(0)

        ws = workbook.create_sheet(sheet_name[:31])
        img = Image(imgdata)
        ws.add_image(img, "B2")

    ## -output final results as chart in excel
    def final_chart(
        data,
        chartTitle,
        workbook,
        sheet_name,
    ):
       
        plt.figure(figsize=(10, 6))

        index = np.arange(len(data["Country"]))
        bar_width = 0.35
        opacity = 0.8

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
        plt.xticks(index + 3 * bar_width / 2, data["Country"], fontsize=12)
        plt.xticks(wrap=True)
        plt.legend(loc="upper center", ncol=2)

        # Add labels
        def add_labels_LCY(x, y):
            for i in range(len(x)):
                lable_LCY = ((y[i] * 100).round(0)).astype("int")
                plt.text(
                    i + bar_width,
                    y[i] + 0.01,
                    f"{lable_LCY}" + "%",
                    ha="center",
                    fontsize=12,
                )  # Aligning text for LCY

        def add_labels_FCY(x, y):
            for i in range(len(x)):
                lable_FCY = ((y[i] * 100).round(0)).astype("int")
                plt.text(
                    i + bar_width + 0.4,
                    y[i] + 0.01,
                    f"{lable_FCY}" + "%",
                    ha="center",
                    fontsize=12,
                )  # Aligning text for FCY right of LCY

        add_labels_LCY(data["Country"], data["LCY"])
        add_labels_FCY(data["Country"], data["FCY"])

        plt.ylim((0, 1))
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



    # summary_df.to_excel("spread_summary_by_region.xlsx", index=False)
    summary_all = pd.concat(
        [summary_1, summary_2, summary_3, summary_4, summary_5, summary_6, summary_7, summary_8],
        ignore_index=True,
    )

    # ---- Step 1: Define preferred region order ----
    preferred_order = top_countries_1

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

    datapoints_wide_renamed = datapoints_wide.add_suffix('-datapoints')
    spread_ids_widee_renamed = spread_ids_wide.add_suffix('-spread_ids')
    concat_df = pd.concat([datapoints_wide_renamed, spread_ids_widee_renamed], axis=1)
    concat_df = concat_df.reset_index()

    # save to Excel
    # with pd.ExcelWriter(sum_path, engine="openpyxl") as writer:
    #     datapoints_wide.to_excel(writer, sheet_name="Sheet1_datapoints")
    #     spread_ids_wide.to_excel(writer, sheet_name="Sheet2_spread_ids")
    # print(f"Excel file saved successfully to {sum_path}")

    # ------------------------------------------------
    ## Consolidated output
    os.makedirs(os.path.dirname(consolid_path), exist_ok=True)
    with pd.ExcelWriter(consolid_path, engine="openpyxl") as writer:
        all_country_frame.to_excel(writer, sheet_name="all country modelling data", index=False)
        interest_data_df.to_excel(writer, sheet_name="interest data", index=False)
        leid_output.to_excel(writer, sheet_name="LEID level output", index=False)
        country_output.to_excel(writer, sheet_name="Country level output", index=True)
        concat_df.to_excel(writer, sheet_name="Data cleaning steps", index=False)
        full_df.to_excel(writer, sheet_name="Backtest full data", index=False)
        bt_all_country_df.to_excel(writer, sheet_name="Backtest_country level", index=False)
        bt_final_all_df.to_excel(writer, sheet_name="Backtest_id level", index=False)
        validate_data.to_excel(writer, sheet_name="Validation before 2018", index=False)
       

    ## add charts in excel --------------------------------------------------------------------------
        wb = writer.book
        outputChart_excel(
            data = interest_data_df["interest_rate"],
            chartTitle = "Interest Rate Distribution (before filtering)",
            workbook = wb,
            sheet_name = "Interest rate charts",
            bin_edges = np.arange(0,1.2,0.02),
            xrange=(0,1)
        )

        filtered_data = interest_data_df.loc[interest_data_df["interest_expense_issue"] == "F", "interest_rate"]
        outputChart_excel(
            data = filtered_data,
            chartTitle = "Interest Rate Distribution (after filtering)",
            workbook = wb,
            sheet_name = "Interest rate charts",
            bin_edges = np.arange(0,0.6,0.02),
            xrange=(0,0.6)
        )

        final_chart(
            data = country_output_bchart,
            chartTitle = f"Alpha Parameter - {sector}",
            workbook = wb,
            sheet_name = "Final model chart"
        )

    print(f"results excel saved at: {consolid_path}")
###---------------------------------------------------------------------------------------------------


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
        # "Global",
    ]:
        interest_expense_run(sector)
        sys.stdout = TimestampLog("IE_master")
