"""
Random Forest Model Interpretation
====================================
Covers:
  1. MDI (Gini) Feature Importance
  2. Permutation Importance (MDA)
  3. Out-of-Bag (OOB) Error
  4. Partial Dependence Plots (PDP) + ICE
  5. SHAP Values (TreeSHAP)
  6. Proximity Matrix

References:
  - Breiman (2001). Random Forests. Machine Learning, 45, 5-32.
  - Strobl et al. (2007). Bias in RF variable importance. BMC Bioinformatics.
  - Lundberg & Lee (2017). SHAP. NeurIPS.
  - Friedman (2001). Greedy function approximation. Annals of Statistics.

Install dependencies:
  pip install scikit-learn shap matplotlib seaborn numpy pandas
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
import warnings

from sklearn.datasets import load_breast_cancer
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance, PartialDependenceDisplay
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

import shap

warnings.filterwarnings("ignore")

# ── Plotting style ────────────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.facecolor": "#0f1117",
    "axes.facecolor":   "#1a1d27",
    "axes.edgecolor":   "#3a3d4d",
    "axes.labelcolor":  "#e0e0e0",
    "xtick.color":      "#a0a0b0",
    "ytick.color":      "#a0a0b0",
    "text.color":       "#e0e0e0",
    "grid.color":       "#2a2d3d",
    "grid.linestyle":   "--",
    "grid.alpha":       0.5,
    "font.family":      "monospace",
})

ACCENT   = "#7c6aff"   # purple
ACCENT2  = "#00d4aa"   # teal
ACCENT3  = "#ff6b6b"   # coral
PALETTE  = [ACCENT, ACCENT2, ACCENT3, "#ffd166", "#06aed5"]


# ═══════════════════════════════════════════════════════════════════════════════
# 0. DATA & MODEL
# ═══════════════════════════════════════════════════════════════════════════════

def load_data_and_train():
    """Load Breast Cancer dataset and train a Random Forest."""
    data   = load_breast_cancer()
    X      = pd.DataFrame(data.data, columns=data.feature_names)
    y      = data.target                              # 0 = malignant, 1 = benign
    labels = data.target_names

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        min_samples_leaf=1,
        oob_score=True,        # enables OOB error estimate
        n_jobs=-1,
        random_state=42,
    )
    rf.fit(X_train, y_train)

    print(f"Test Accuracy : {rf.score(X_test, y_test):.4f}")
    print(f"OOB Accuracy  : {rf.oob_score_:.4f}")
    print(f"OOB Error     : {1 - rf.oob_score_:.4f}\n")

    return rf, X_train, X_test, y_train, y_test, X, y, labels, data.feature_names


# ═══════════════════════════════════════════════════════════════════════════════
# 1. MDI — Mean Decrease in Impurity
# ═══════════════════════════════════════════════════════════════════════════════

def plot_mdi_importance(rf, feature_names, top_n=15):
    """
    Mean Decrease in Impurity (Gini importance).
    Computed internally by sklearn during training.

    Formula (per Breiman 2001):
        MDI(Xj) = (1/T) * Σ_t Σ_{v ∈ V_t(Xj)} p(v) * Δi(v)
    where p(v) = n_v / n and Δi(v) is the impurity decrease at node v.

    ⚠ Known to favour high-cardinality features (Strobl et al., 2007).
    """
    importances = pd.Series(rf.feature_importances_, index=feature_names)
    importances = importances.nlargest(top_n).sort_values()

    fig, ax = plt.subplots(figsize=(9, 6))
    colors = plt.cm.plasma(np.linspace(0.3, 0.9, top_n))
    bars = ax.barh(importances.index, importances.values, color=colors, height=0.7)

    # value labels
    for bar, val in zip(bars, importances.values):
        ax.text(val + 0.001, bar.get_y() + bar.get_height() / 2,
                f"{val:.4f}", va="center", fontsize=8, color="#cccccc")

    ax.set_xlabel("Mean Decrease in Impurity (MDI)")
    ax.set_title("Feature Importance — MDI (Gini)", fontsize=13, fontweight="bold",
                 color=ACCENT, pad=12)
    ax.set_xlim(0, importances.max() * 1.15)
    ax.grid(axis="x")
    fig.tight_layout()
    fig.savefig("plot_1_mdi_importance.png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.show()
    print("✔  Saved: plot_1_mdi_importance.png\n")


# ═══════════════════════════════════════════════════════════════════════════════
# 2. MDA — Mean Decrease in Accuracy (Permutation Importance)
# ═══════════════════════════════════════════════════════════════════════════════

def plot_permutation_importance(rf, X_test, y_test, feature_names, top_n=15, n_repeats=30):
    """
    Permutation importance (Breiman 2001).
    Shuffles each feature on OOB / held-out data and measures accuracy drop.

    MDA(Xj) = (1/T) * Σ_t [ Acc_t^OOB − Acc_t^OOB(π_j) ]

    Unbiased w.r.t. feature cardinality unlike MDI.
    Uses n_repeats=30 for stable estimates (see sklearn docs).
    """
    result = permutation_importance(
        rf, X_test, y_test,
        n_repeats=n_repeats,
        random_state=42,
        n_jobs=-1,
        scoring="accuracy",
    )

    perm_df = pd.DataFrame({
        "feature":   feature_names,
        "mean":      result.importances_mean,
        "std":       result.importances_std,
    }).nlargest(top_n, "mean").sort_values("mean")

    fig, ax = plt.subplots(figsize=(9, 6))
    y_pos = np.arange(len(perm_df))
    ax.barh(y_pos, perm_df["mean"], xerr=perm_df["std"],
            color=ACCENT2, alpha=0.85, height=0.65,
            error_kw=dict(ecolor="#ffffff55", capsize=3))
    ax.set_yticks(y_pos)
    ax.set_yticklabels(perm_df["feature"], fontsize=8)
    ax.set_xlabel(f"Mean Accuracy Decrease ± SD  (n_repeats={n_repeats})")
    ax.set_title("Permutation Importance (MDA)", fontsize=13, fontweight="bold",
                 color=ACCENT2, pad=12)
    ax.grid(axis="x")
    fig.tight_layout()
    fig.savefig("plot_2_permutation_importance.png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.show()
    print("✔  Saved: plot_2_permutation_importance.png\n")


# ═══════════════════════════════════════════════════════════════════════════════
# 3. OOB Error Curve
# ═══════════════════════════════════════════════════════════════════════════════

def plot_oob_error_curve(X_train, y_train, max_trees=300, step=10):
    """
    OOB Error vs. number of trees.

    OOB Error = (1/n) * Σ_i 1[ŷ_i^OOB ≠ y_i]

    Each bootstrap sample uses ~63.2% of training data; remaining
    ~36.8% are OOB samples — a free internal validation set (Breiman 1996).
    Uses warm_start=True for incremental fitting efficiency.
    """
    n_trees_range = range(step, max_trees + 1, step)
    oob_errors    = []

    rf_oob = RandomForestClassifier(
        warm_start=True, oob_score=True, n_jobs=-1, random_state=42
    )

    for n in n_trees_range:
        rf_oob.set_params(n_estimators=n)
        rf_oob.fit(X_train, y_train)
        oob_errors.append(1 - rf_oob.oob_score_)

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(list(n_trees_range), oob_errors, color=ACCENT3, lw=2.5)
    ax.fill_between(list(n_trees_range), oob_errors, alpha=0.15, color=ACCENT3)
    best_n   = list(n_trees_range)[np.argmin(oob_errors)]
    best_err = min(oob_errors)
    ax.axvline(best_n, color="#ffffff55", linestyle="--", lw=1.2)
    ax.annotate(f"min OOB = {best_err:.4f}\n@ {best_n} trees",
                xy=(best_n, best_err),
                xytext=(best_n + 15, best_err + 0.005),
                color="#ffffff", fontsize=9,
                arrowprops=dict(arrowstyle="->", color="#ffffff88"))
    ax.set_xlabel("Number of Trees")
    ax.set_ylabel("OOB Error")
    ax.set_title("OOB Error vs. Number of Trees", fontsize=13, fontweight="bold",
                 color=ACCENT3, pad=12)
    ax.grid()
    fig.tight_layout()
    fig.savefig("plot_3_oob_error_curve.png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.show()
    print(f"✔  Saved: plot_3_oob_error_curve.png  (best={best_n} trees, OOB={best_err:.4f})\n")


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Partial Dependence Plots (PDP) + Individual Conditional Expectation (ICE)
# ═══════════════════════════════════════════════════════════════════════════════

def plot_pdp_ice(rf, X_train, feature_names, top_features=None):
    """
    PDP (Friedman 2001):
        f̂_S(x_S) = E_{X_C}[f̂(x_S, X_C)] ≈ (1/n) Σ_i f̂(x_S, x_C^(i))

    ICE plots (Goldstein et al. 2015) show per-instance curves, revealing
    heterogeneous effects hidden by PDP averaging.

    ⚠ PDPs assume feature independence. ICE plots are more robust for
    detecting interaction effects.
    """
    if top_features is None:
        importances  = pd.Series(rf.feature_importances_, index=feature_names)
        top_features = importances.nlargest(4).index.tolist()

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    axes = axes.flatten()

    for ax, feat in zip(axes, top_features):
        feat_idx = list(feature_names).index(feat)
        display  = PartialDependenceDisplay.from_estimator(
            rf, X_train,
            features=[feat_idx],
            kind="both",         # PDP + ICE
            subsample=150,
            n_jobs=-1,
            random_state=42,
            ax=ax,
            ice_lines_kw={"color": ACCENT, "alpha": 0.07, "lw": 0.8},
            pd_line_kw={"color": ACCENT2, "lw": 2.5, "label": "PDP"},
        )
        ax.set_title(feat, fontsize=9, color="#e0e0e0")
        ax.set_facecolor("#1a1d27")
        ax.tick_params(colors="#a0a0b0", labelsize=7)
        ax.set_xlabel(feat, fontsize=8)
        ax.set_ylabel("Partial Dependence", fontsize=8)
        ax.grid(True, alpha=0.3)

    fig.suptitle("Partial Dependence (PDP) + ICE Plots\n"
                 "Purple lines = individual instances  |  Teal line = average (PDP)",
                 fontsize=11, fontweight="bold", color=ACCENT2, y=1.01)
    fig.tight_layout()
    fig.savefig("plot_4_pdp_ice.png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.show()
    print("✔  Saved: plot_4_pdp_ice.png\n")


# ═══════════════════════════════════════════════════════════════════════════════
# 5. SHAP — SHapley Additive exPlanations (TreeSHAP)
# ═══════════════════════════════════════════════════════════════════════════════

def plot_shap(rf, X_train, X_test, feature_names):
    """
    TreeSHAP (Lundberg et al. 2020) — exact Shapley values for tree ensembles.

    Prediction decomposition:
        f̂(x) = φ_0 + Σ_{j=1}^{p} φ_j

    Shapley value formula:
        φ_j = Σ_{S ⊆ F\\{j}} [ |S|!(|F|-|S|-1)! / |F|! ] * [f̂(S∪{j}) - f̂(S)]

    TreeSHAP complexity: O(T * L * D²) — tractable for large forests.
    Satisfies: Efficiency, Symmetry, Dummy, Additivity axioms.
    """
    explainer   = shap.TreeExplainer(rf)
    shap_values = explainer.shap_values(X_test)

    # For binary classification sklearn returns list [class0, class1]
    if isinstance(shap_values, list):
        sv = shap_values[1]   # class=1 (benign)
    else:
        sv = shap_values

    # ── 5a. Summary (beeswarm) plot ───────────────────────────────────────────
    fig1, ax1 = plt.subplots(figsize=(10, 7))
    shap.summary_plot(
        sv, X_test,
        feature_names=list(feature_names),
        show=False,
        plot_size=None,
        color_bar=True,
    )
    ax1 = plt.gca()
    ax1.set_title("SHAP Summary Plot (Beeswarm) — Class: Benign",
                  fontsize=12, fontweight="bold", color=ACCENT, pad=10)
    fig1.tight_layout()
    fig1.savefig("plot_5a_shap_summary.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("✔  Saved: plot_5a_shap_summary.png")

    # ── 5b. Bar plot (mean |SHAP|) ────────────────────────────────────────────
    fig2, ax2 = plt.subplots(figsize=(9, 6))
    shap.summary_plot(
        sv, X_test,
        feature_names=list(feature_names),
        plot_type="bar",
        show=False,
        plot_size=None,
        color=ACCENT2,
    )
    ax2 = plt.gca()
    ax2.set_title("SHAP Global Importance — Mean |φ_j|",
                  fontsize=12, fontweight="bold", color=ACCENT2, pad=10)
    fig2.tight_layout()
    fig2.savefig("plot_5b_shap_bar.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("✔  Saved: plot_5b_shap_bar.png")

    # ── 5c. Waterfall plot for a single prediction ────────────────────────────
    sample_idx = 0
    exp = shap.Explanation(
        values          = sv[sample_idx],
        base_values     = explainer.expected_value[1] if isinstance(
                            explainer.expected_value, (list, np.ndarray))
                          else explainer.expected_value,
        data            = X_test.iloc[sample_idx].values,
        feature_names   = list(feature_names),
    )
    fig3, ax3 = plt.subplots(figsize=(9, 6))
    shap.waterfall_plot(exp, show=False, max_display=15)
    ax3 = plt.gca()
    ax3.set_title(f"SHAP Waterfall — Sample #{sample_idx}",
                  fontsize=12, fontweight="bold", color=ACCENT3, pad=10)
    fig3.tight_layout()
    fig3.savefig("plot_5c_shap_waterfall.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("✔  Saved: plot_5c_shap_waterfall.png\n")

    return sv


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Proximity Matrix
# ═══════════════════════════════════════════════════════════════════════════════

def compute_proximity_matrix(rf, X, n_samples=100):
    """
    Proximity matrix (Breiman 2001):
        P_ij = (# trees where x_i and x_j land in same leaf) / T

    P_ij ∈ [0, 1].  High proximity ⟹ structurally similar instances.
    Useful for: outlier detection, MDS visualisation, imputation.

    Complexity: O(n² * T) — subset of n_samples used for tractability.
    """
    X_sub = X.iloc[:n_samples] if hasattr(X, "iloc") else X[:n_samples]
    # leaf indices: shape (n_samples, n_trees)
    leaves = rf.apply(X_sub)
    n      = len(X_sub)
    T      = rf.n_estimators
    prox   = np.zeros((n, n))

    for t in range(T):
        leaf_ids = leaves[:, t]
        for i in range(n):
            # vectorised: compare row i against all rows
            prox[i] += (leaf_ids == leaf_ids[i])

    prox /= T                 # normalise to [0, 1]
    np.fill_diagonal(prox, 1.0)
    return prox


def plot_proximity_matrix(rf, X, y, n_samples=100):
    prox = compute_proximity_matrix(rf, X, n_samples)

    fig, ax = plt.subplots(figsize=(8, 7))
    im = ax.imshow(prox, cmap="plasma", aspect="auto", vmin=0, vmax=1)
    plt.colorbar(im, ax=ax, label="Proximity P_ij")
    ax.set_title(f"Proximity Matrix  (n={n_samples} samples)",
                 fontsize=12, fontweight="bold", color=ACCENT, pad=10)
    ax.set_xlabel("Sample index")
    ax.set_ylabel("Sample index")
    fig.tight_layout()
    fig.savefig("plot_6_proximity_matrix.png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.show()
    print("✔  Saved: plot_6_proximity_matrix.png\n")
    return prox


def plot_proximity_mds(prox, y_sub):
    """
    Multi-Dimensional Scaling (MDS) on the proximity matrix for 2-D visualisation.
    Converts dissimilarity (1 - P) into a 2-D embedding.
    """
    from sklearn.manifold import MDS
    dissim = 1 - prox
    mds    = MDS(n_components=2, dissimilarity="precomputed",
                 random_state=42, normalized_stress="auto")
    coords = mds.fit_transform(dissim)

    fig, ax = plt.subplots(figsize=(8, 6))
    for label, color, name in [(0, ACCENT3, "Malignant"), (1, ACCENT2, "Benign")]:
        mask = y_sub == label
        ax.scatter(coords[mask, 0], coords[mask, 1],
                   c=color, label=name, alpha=0.75, s=55, edgecolors="#ffffff22")
    ax.set_title("MDS Projection of Proximity Matrix",
                 fontsize=12, fontweight="bold", color=ACCENT, pad=10)
    ax.set_xlabel("MDS Dimension 1")
    ax.set_ylabel("MDS Dimension 2")
    ax.legend(framealpha=0.2, edgecolor="#444")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig("plot_7_proximity_mds.png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.show()
    print("✔  Saved: plot_7_proximity_mds.png\n")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("  Random Forest Interpretation — Full Pipeline")
    print("=" * 60, "\n")

    # 0. Train
    rf, X_train, X_test, y_train, y_test, X, y, labels, feature_names = \
        load_data_and_train()

    # 1. MDI importance
    print("── 1. MDI Feature Importance ──────────────────────────────")
    plot_mdi_importance(rf, feature_names)

    # 2. Permutation importance
    print("── 2. Permutation Importance (MDA) ────────────────────────")
    plot_permutation_importance(rf, X_test, y_test, feature_names)

    # 3. OOB error curve
    print("── 3. OOB Error vs. n_trees ────────────────────────────────")
    plot_oob_error_curve(X_train, y_train)

    # 4. PDP + ICE
    print("── 4. Partial Dependence + ICE ─────────────────────────────")
    plot_pdp_ice(rf, X_train, feature_names)

    # 5. SHAP
    print("── 5. SHAP (TreeSHAP) ──────────────────────────────────────")
    plot_shap(rf, X_train, X_test, feature_names)

    # 6. Proximity matrix + MDS
    print("── 6. Proximity Matrix & MDS ───────────────────────────────")
    n_prox = 150
    X_sub  = X.iloc[:n_prox]
    y_sub  = y[:n_prox]
    prox   = plot_proximity_matrix(rf, X_sub, y_sub, n_samples=n_prox)
    plot_proximity_mds(prox, y_sub)

    print("=" * 60)
    print("  All plots saved. Interpretation complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
