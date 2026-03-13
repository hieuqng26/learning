import os

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
from openpyxl.drawing.image import Image


# ============================================================================
# CHART HELPERS
# ============================================================================


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
        )


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
        )


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

        plt.bar(
            index + bar_width,
            data["LCY"],
            bar_width,
            alpha=opacity,
            color="royalblue",
            label="LCY",
        )

        plt.bar(
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

        plt.bar(
            index + bar_width,
            data["LCY"],
            bar_width,
            alpha=opacity,
            color="royalblue",
            label="LCY",
        )

        plt.bar(
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
# MAIN OUTPUT PIPELINE
# ============================================================================


def write_outputs(consolid_path, modelling_results, backtest_results, interest_data_df, summary_steps, sector, IE_config):
    """Write all DataFrames to Excel sheets and embed charts in the workbook."""
    percentiles_for_chart = IE_config.percentiles_for_chart
    globalmodel = IE_config.globalmodel

    if globalmodel:
        top_countries_1 = IE_config.top_countries_1
    else:
        top_countries_1 = IE_config.top_countries

    all_country_frame = modelling_results["all_country_frame"]
    agg_frame = modelling_results["agg_frame"]
    leid_output = modelling_results["leid_output"]
    country_output = modelling_results["country_output"]
    portfolio_output = modelling_results["portfolio_output"]
    LC_CC_split_output = modelling_results["LC_CC_split_output"]
    MC_split_output = modelling_results["MC_split_output"]

    id_alpha_ts_df, agg_alpha_ts_df, summary_ts_df = backtest_results

    # --- Build data cleaning steps summary table ---
    summary_all = pd.concat(summary_steps, ignore_index=True)

    preferred_order = top_countries_1 + ["Others"]

    datapoints_wide = summary_all.pivot(
        index="Step", columns="Region", values="Total datapoints"
    )
    datapoints_wide = datapoints_wide.reindex(columns=preferred_order)
    datapoints_wide = datapoints_wide.fillna(0).astype(int)

    spread_ids_wide = summary_all.pivot(
        index="Step", columns="Region", values="Unique spread IDs"
    )
    spread_ids_wide = spread_ids_wide.reindex(columns=preferred_order)
    spread_ids_wide = spread_ids_wide.fillna(0).astype(int)

    datapoints_wide_renamed = datapoints_wide.add_suffix("-datapoints")
    spread_ids_wide_renamed = spread_ids_wide.add_suffix("-spread_ids")
    concat_df = pd.concat([datapoints_wide_renamed, spread_ids_wide_renamed], axis=1)

    portfolio_table = (
        summary_all.groupby("Step")[["LC+CC datapoints", "MC datapoints"]].sum()
    )

    steps_df = pd.concat([concat_df, portfolio_table], axis=1)
    steps_df = steps_df.reset_index()

    # --- Prepare country bar chart data ---
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

    portfolio_output_bchart = data_for_chart(portfolio_output, "Portfolio")
    LC_CC_output_bchart = data_for_chart(LC_CC_split_output, "Country")
    MC_output_bchart = data_for_chart(MC_split_output, "Country")

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
