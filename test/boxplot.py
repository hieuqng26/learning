import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# --- Sample data (replace with your own df) ---
rng = np.random.default_rng(42)
dates = pd.date_range("2022-01-01", "2024-12-31", freq="D")
df = pd.DataFrame({
    "date": np.random.choice(dates, size=1000),
    "value": rng.normal(loc=50, scale=10, size=1000)
})

# --- 1. Parse dates and extract quarter label ---
df["date"] = pd.to_datetime(df["date"])
df["quarter"] = df["date"].dt.to_period("Q")  # e.g. 2022Q1, 2022Q2, ...

# --- 2. Group by quarter ---
quarters = sorted(df["quarter"].unique())
grouped_data = [df.loc[df["quarter"] == q, "value"].values for q in quarters]
labels = [str(q) for q in quarters]  # e.g. ["2022Q1", "2022Q2", ...]

# --- 3. Plot ---
fig, ax = plt.subplots(figsize=(14, 5))

bp = ax.boxplot(
    grouped_data,
    tick_labels=labels,
    patch_artist=True,          # filled boxes
    medianprops=dict(color="crimson", linewidth=2),
    boxprops=dict(facecolor="steelblue", alpha=0.6),
    flierprops=dict(marker="o", markersize=3, alpha=0.4, markerfacecolor="gray"),
    whiskerprops=dict(linestyle="--", linewidth=1.2),
)

# --- 4. Formatting ---
ax.set_xlabel("Quarter", fontsize=12)
ax.set_ylabel("Value", fontsize=12)
ax.set_title("Distribution of Values by Quarter", fontsize=14)
ax.tick_params(axis="x", rotation=45)
ax.yaxis.grid(True, linestyle="--", alpha=0.7)
ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig("quarterly_boxplot.png", dpi=150)
plt.show()
