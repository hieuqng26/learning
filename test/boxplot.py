import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# -------------------------------------------------------------------
# Sample data — replace with your actual DataFrame
# -------------------------------------------------------------------
np.random.seed(42)
dates = pd.date_range("2024-01-01", "2024-12-31", freq="D")
df = pd.DataFrame({
    "date":  np.random.choice(dates, size=500),
    "value": np.random.randn(500) * 10 + 50
})

# -------------------------------------------------------------------
# 1. Parse dates and extract year-month period
# -------------------------------------------------------------------
df["date"] = pd.to_datetime(df["date"])
df["month"] = df["date"].dt.to_period("M")          # e.g. 2024-01

# -------------------------------------------------------------------
# 2. Group values by month → list of arrays (one per box)
# -------------------------------------------------------------------
grouped = df.groupby("month")["value"].apply(list)  # Series of lists
labels  = [str(m) for m in grouped.index]           # ["2024-01", ...]
data    = grouped.tolist()                           # [[...], [...], ...]

# -------------------------------------------------------------------
# 3. Plot
# -------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(14, 5))

bp = ax.boxplot(
    data,
    patch_artist=True,       # filled boxes
    notch=False,
    widths=0.6,
    medianprops=dict(color="crimson",  linewidth=2),
    boxprops=dict(facecolor="steelblue", alpha=0.6),
    whiskerprops=dict(linewidth=1.2),
    capprops=dict(linewidth=1.5),
    flierprops=dict(marker="o", markersize=4, alpha=0.4,
                    markerfacecolor="gray", linestyle="none"),
)

# -------------------------------------------------------------------
# 4. Formatting
# -------------------------------------------------------------------
ax.set_xticks(range(1, len(labels) + 1))
ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=9)

ax.set_title("Monthly Distribution of Values", fontsize=14, fontweight="bold", pad=12)
ax.set_xlabel("Month", fontsize=11)
ax.set_ylabel("Value", fontsize=11)
ax.yaxis.grid(True, linestyle="--", alpha=0.7)
ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig("monthly_boxplot.png", dpi=150)
plt.show()
