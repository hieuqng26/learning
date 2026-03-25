import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error

# --- Sample data (replace with your own df) ---
rng = np.random.default_rng(42)
n = 100
x = rng.uniform(0, 10, n)
y = 2.5 * x + rng.normal(0, 3, n)
df = pd.DataFrame({"x": x, "y": y})

# --- 1. Fit linear regression ---
X = df[["x"]]          # shape (n, 1) — 2D required by sklearn
y = df["y"]

model = LinearRegression()
model.fit(X, y)

x_line = np.linspace(df["x"].min(), df["x"].max(), 300).reshape(-1, 1)
y_line = model.predict(x_line)

y_pred = model.predict(X)
r2  = r2_score(y, y_pred)
mse = mean_squared_error(y, y_pred)

# --- 2. Plot ---
fig, ax = plt.subplots(figsize=(8, 5))

# Scatter
ax.scatter(df["x"], df["y"],
           alpha=0.6, edgecolors="white", linewidths=0.5,
           color="steelblue", s=60, label="Observations")

# Regression line
ax.plot(x_line, y_line,
        color="crimson", linewidth=2,
        label=f"Fit: y = {model.coef_[0]:.2f}x + {model.intercept_:.2f}")

# Confidence band (±1 std of residuals)
residual_std = np.std(y - y_pred)
ax.fill_between(x_line.flatten(),
                y_line - residual_std,
                y_line + residual_std,
                color="crimson", alpha=0.12, label="±1 SD band")

# --- 3. Annotations ---
ax.text(0.05, 0.95,
        f"$R^2$ = {r2:.3f}\nRMSE = {np.sqrt(mse):.3f}",
        transform=ax.transAxes,
        fontsize=11, verticalalignment="top",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="gray", alpha=0.8))

# --- 4. Formatting ---
ax.set_xlabel("x (independent variable)", fontsize=12)
ax.set_ylabel("y (dependent variable)", fontsize=12)
ax.set_title("Simple Linear Regression", fontsize=14)
ax.legend(fontsize=10)
ax.yaxis.grid(True, linestyle="--", alpha=0.5)
ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig("regression_scatter.png", dpi=150)
plt.show()
