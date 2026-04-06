"""
Random Forest Regressor — Interpretation & Visualisation
=========================================================
Covers:
  0. Data & Model (RandomForestRegressor, California Housing)
  1. MDI Feature Importance (Mean Decrease in Impurity)
  2. Permutation Importance (MDA)
  3. OOB R² Curve vs. number of trees
  4. Partial Dependence Plots (PDP) + ICE
  5. SHAP Values (TreeSHAP) — fixed for regressor
  6. Tree Split Visualisation (single tree + decision path)
  7. Proximity Matrix + MDS Projection

References:
  - Breiman (2001). Random Forests. Machine Learning, 45, 5-32.
    https://doi.org/10.1023/A:1010933404324
  - Strobl et al. (2007). Bias in RF variable importance. BMC Bioinformatics.
    https://doi.org/10.1186/1471-2105-8-25
  - Lundberg & Lee (2017). SHAP. NeurIPS. https://arxiv.org/abs/1705.07874
  - Lundberg et al. (2020). TreeSHAP. Nature Machine Intelligence.
    https://doi.org/10.1038/s42256-019-0138-9
  - Friedman (2001). PDP. Annals of Statistics.
    https://doi.org/10.1214/aos/1013203451

Install:
  pip install scikit-learn shap matplotlib seaborn numpy pandas
"""

import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import shap

from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance, PartialDependenceDisplay
from sklearn.manifold import MDS
from sklearn.model_selection import train_test_split
from sklearn.tree import plot_tree

warnings.filterwarnings("ignore")

# ── Global style ──────────────────────────────────────────────────────────────
BG       = "#F7F9FC"   # near-white page background
PANEL_BG = "#FFFFFF"   # pure white plot area
BORDER   = "#D0D7E3"   # soft grey border
FG       = "#1E2A3A"   # near-black for titles & labels
MUTED    = "#6B7A99"   # mid-grey for tick labels & annotations

BLUE     = "#2563EB"   # primary accent
TEAL     = "#0D9488"   # secondary accent
CORAL    = "#E05252"   # warning / highlight
GOLD     = "#D97706"   # tertiary accent
PURPLE   = "#7C3AED"   # quaternary accent

plt.rcParams.update({
    # Canvas
    "figure.facecolor"  : BG,
    "figure.dpi"        : 120,
    "savefig.facecolor" : BG,
    # Axes
    "axes.facecolor"    : PANEL_BG,
    "axes.edgecolor"    : BORDER,
    "axes.linewidth"    : 0.9,
    "axes.labelcolor"   : FG,
    "axes.titlecolor"   : FG,
    "axes.titlesize"    : 13,
    "axes.titleweight"  : "bold",
    "axes.labelsize"    : 10,
    "axes.spines.top"   : False,
    "axes.spines.right" : False,
    # Grid
    "axes.grid"         : True,
    "grid.color"        : "#E4E9F2",
    "grid.linewidth"    : 0.7,
    "grid.linestyle"    : "-",
    "grid.alpha"        : 1.0,
    # Ticks
    "xtick.color"       : MUTED,
    "ytick.color"       : MUTED,
    "xtick.labelsize"   : 9,
    "ytick.labelsize"   : 9,
    "xtick.direction"   : "out",
    "ytick.direction"   : "out",
    "xtick.major.size"  : 4,
    "ytick.major.size"  : 4,
    # Text
    "text.color"        : FG,
    "font.family"       : "DejaVu Sans",
    "font.size"         : 10,
    # Legend
    "legend.facecolor"  : PANEL_BG,
    "legend.edgecolor"  : BORDER,
    "legend.fontsize"   : 9,
    "legend.framealpha" : 1.0,
    # Lines
    "lines.linewidth"   : 1.8,
})


# ═══════════════════════════════════════════════════════════════════════════════
# 0.  DATA & MODEL
# ═══════════════════════════════════════════════════════════════════════════════

def generate_synthetic_data(n_samples=2000, n_features=10, random_state=42):
    """
    Synthetic regression dataset with controlled, interpretable structure.

    Target is a non-linear combination of features plus noise:

        y = 3·x0² + 2·x1·x2 − 1.5·x3 + sin(π·x4)
            + 0.5·x5 − x6³ + exp(0.3·x7)
            + 0·x8 + 0·x9          ← x8, x9 are pure noise features
            + ε,   ε ~ N(0, 0.5²)

    This construction guarantees:
      • Non-linear main effects  (x0², sin, exp)
      • Interaction term         (x1·x2)
      • Linear effect            (x3, x5)
      • Irrelevant features      (x8, x9) — useful to verify importances are ~0
    """
    rng = np.random.RandomState(random_state)
    X   = rng.randn(n_samples, n_features)

    y = (
          3.0  * X[:, 0] ** 2
        + 2.0  * X[:, 1] * X[:, 2]
        - 1.5  * X[:, 3]
        + np.sin(np.pi * X[:, 4])
        + 0.5  * X[:, 5]
        - 1.0  * X[:, 6] ** 3
        + np.exp(0.3 * X[:, 7])
        # x8, x9 → pure noise (true importance = 0)
        + rng.randn(n_samples) * 0.5   # ε
    )

    feature_names = [f"x{i}" for i in range(n_features)]
    X_df = pd.DataFrame(X, columns=feature_names)

    print(f"  Synthetic data: {n_samples} samples × {n_features} features")
    print(f"  y ∈ [{y.min():.2f}, {y.max():.2f}],  "
          f"mean={y.mean():.2f},  std={y.std():.2f}")

    return X_df, y, feature_names


def load_data_and_train():
    """Generate synthetic data and train a RandomForestRegressor."""
    X, y, feature_names = generate_synthetic_data(
        n_samples=2000, n_features=10, random_state=42
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    rf = RandomForestRegressor(
        n_estimators    = 200,
        max_depth       = None,
        min_samples_leaf= 2,
        oob_score       = True,   # free R² on OOB samples
        n_jobs          = -1,
        random_state    = 42,
    )
    rf.fit(X_train, y_train)

    print(f"  Test R²  : {rf.score(X_test, y_test):.4f}")
    print(f"  OOB  R²  : {rf.oob_score_:.4f}\n")

    return rf, X_train, X_test, y_train, y_test, X, y, feature_names


# ═══════════════════════════════════════════════════════════════════════════════
# 1.  MDI — Mean Decrease in Impurity
# ═══════════════════════════════════════════════════════════════════════════════

def plot_mdi_importance(rf, feature_names, top_n=15):
    """
    MDI (variance-reduction importance) — Breiman (2001):

        MDI(Xj) = (1/T) Σ_t  Σ_{v ∈ V_t(Xj)}  p(v) · Δi(v)

    For regression trees: impurity = MSE, so Δi(v) = MSE_parent − MSE_children.

    ⚠ Biased toward high-cardinality features (Strobl et al. 2007).
    """
    imp = pd.Series(rf.feature_importances_, index=feature_names)
    imp = imp.nlargest(top_n).sort_values()

    fig, ax = plt.subplots(figsize=(9, 5))
    colors  = plt.cm.Blues(np.linspace(0.35, 0.85, len(imp)))
    bars    = ax.barh(imp.index, imp.values, color=colors, height=0.65)

    for bar, val in zip(bars, imp.values):
        ax.text(val + imp.max() * 0.01, bar.get_y() + bar.get_height() / 2,
                f"{val:.4f}", va="center", fontsize=8, color=FG)

    ax.set_xlabel("Mean Decrease in Impurity (MDI)")
    ax.set_title("Feature Importance — MDI", fontsize=13, color=BLUE, pad=10)
    ax.set_xlim(0, imp.max() * 1.18)
    ax.grid(axis="x")
    fig.tight_layout()
    fig.savefig("plot_1_mdi_importance.png", dpi=150, bbox_inches="tight",
                facecolor=BG)
    plt.show()
    print("✔  plot_1_mdi_importance.png\n")


# ═══════════════════════════════════════════════════════════════════════════════
# 2.  MDA — Permutation Importance
# ═══════════════════════════════════════════════════════════════════════════════

def plot_permutation_importance(rf, X_test, y_test, feature_names,
                                top_n=15, n_repeats=30):
    """
    Permutation importance for regressors (Breiman 2001):

        MDA(Xj) = (1/T) Σ_t [ R²_t^OOB  −  R²_t^OOB(π_j) ]

    Shuffles feature Xj on held-out data; measures R² drop.
    n_repeats=30 provides stable estimates of mean ± SD.
    """
    res = permutation_importance(
        rf, X_test, y_test,
        n_repeats   = n_repeats,
        scoring     = "r2",
        n_jobs      = -1,
        random_state= 42,
    )
    df = pd.DataFrame({
        "feature": feature_names,
        "mean":    res.importances_mean,
        "std":     res.importances_std,
    }).nlargest(top_n, "mean").sort_values("mean")

    fig, ax = plt.subplots(figsize=(9, 5))
    ypos = np.arange(len(df))
    ax.barh(ypos, df["mean"], xerr=df["std"], color=TEAL, alpha=0.85, height=0.6,
            error_kw=dict(ecolor="#AABBCC", capsize=3))
    ax.set_yticks(ypos)
    ax.set_yticklabels(df["feature"], fontsize=8)
    ax.set_xlabel(f"Mean R² Decrease ± SD  (n_repeats={n_repeats})")
    ax.set_title("Permutation Importance (MDA)", fontsize=13, color=TEAL, pad=10)
    ax.grid(axis="x")
    fig.tight_layout()
    fig.savefig("plot_2_permutation_importance.png", dpi=150, bbox_inches="tight",
                facecolor=BG)
    plt.show()
    print("✔  plot_2_permutation_importance.png\n")


# ═══════════════════════════════════════════════════════════════════════════════
# 3.  OOB R² Curve
# ═══════════════════════════════════════════════════════════════════════════════

def plot_oob_curve(X_train, y_train, max_trees=300, step=10):
    """
    OOB R² vs. number of trees for RandomForestRegressor.

    Each bootstrap sample covers ~63.2% of training data; the remaining
    ~36.8% are OOB and serve as a free validation set (Breiman 1996).
    warm_start=True avoids re-fitting previously trained trees.
    """
    n_range = range(step, max_trees + 1, step)
    oob_r2s = []

    rf_oob = RandomForestRegressor(
        warm_start=True, oob_score=True, n_jobs=-1,
        min_samples_leaf=2, random_state=42
    )
    for n in n_range:
        rf_oob.set_params(n_estimators=n)
        rf_oob.fit(X_train, y_train)
        oob_r2s.append(rf_oob.oob_score_)

    best_n  = list(n_range)[np.argmax(oob_r2s)]
    best_r2 = max(oob_r2s)

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(list(n_range), oob_r2s, color=CORAL, lw=2.5)
    ax.fill_between(list(n_range), oob_r2s, alpha=0.18, color=CORAL)
    ax.axvline(best_n, color="#AABBCC", linestyle="--", lw=1.2)
    ax.annotate(f"max OOB R² = {best_r2:.4f}\n@ {best_n} trees",
                xy=(best_n, best_r2),
                xytext=(best_n + 20, best_r2 - 0.012),
                color=FG, fontsize=9,
                arrowprops=dict(arrowstyle="->", color=MUTED))
    ax.set_xlabel("Number of Trees")
    ax.set_ylabel("OOB R²")
    ax.set_title("OOB R² vs. Number of Trees", fontsize=13, color=CORAL, pad=10)
    ax.grid()
    fig.tight_layout()
    fig.savefig("plot_3_oob_curve.png", dpi=150, bbox_inches="tight",
                facecolor=BG)
    plt.show()
    print(f"✔  plot_3_oob_curve.png  (best={best_n} trees, OOB R²={best_r2:.4f})\n")


# ═══════════════════════════════════════════════════════════════════════════════
# 4.  PDP + ICE
# ═══════════════════════════════════════════════════════════════════════════════

def plot_pdp_ice(rf, X_train, feature_names):
    """
    PDP (Friedman 2001) — marginal expected prediction:

        f_S(x_S) = E_{X_C}[f(x_S, X_C)]  ≈  (1/n) Σ_i f(x_S, x_C^(i))

    ICE plots (Goldstein et al. 2015) show individual curves, exposing
    heterogeneous effects that PDP averaging can mask.

    ⚠ Both assume feature independence. With correlated features consider
      ALE plots (Apley & Zhu 2020) as a more robust alternative.

    ── Threading note ──────────────────────────────────────────────────────────
    Error: "main thread is not in main loop"

    Root cause: PartialDependenceDisplay uses joblib (n_jobs > 1) to compute
    PDP/ICE curves in parallel background threads. Those threads occasionally
    call back into matplotlib, which tries to update its GUI event loop (Tkinter
    by default). Tkinter's event loop is not thread-safe and raises this error
    when accessed from any thread other than the main one.

    Fix: temporarily switch to the 'Agg' backend (non-interactive, no event
    loop) before computing PDPs, then restore the original backend afterwards.
    Agg renders to an in-memory buffer with no GUI involvement, so background
    threads can safely call into it.

    Alternatively, setting n_jobs=1 avoids the issue by removing threading
    entirely, at the cost of slower computation on large datasets.
    ────────────────────────────────────────────────────────────────────────────
    """
    import matplotlib
    _orig_backend = matplotlib.get_backend()
    matplotlib.use("Agg")           # no GUI event loop → thread-safe

    imp  = pd.Series(rf.feature_importances_, index=feature_names)
    top4 = imp.nlargest(4).index.tolist()

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for ax, feat in zip(axes.flatten(), top4):
        idx = list(feature_names).index(feat)
        PartialDependenceDisplay.from_estimator(
            rf, X_train, features=[idx],
            kind        = "both",
            subsample   = 200,
            n_jobs      = -1,       # parallel — safe now that backend is Agg
            random_state= 42,
            ax          = ax,
            ice_lines_kw= {"color": BLUE, "alpha": 0.08, "lw": 0.6},
            pd_line_kw  = {"color": TEAL, "lw": 2.5},
        )
        ax.set_title(feat, fontsize=9, color=FG)
        ax.set_facecolor(PANEL_BG)
        ax.tick_params(labelsize=7)
        ax.set_ylabel("Predicted value", fontsize=7)
        ax.grid(alpha=0.3)

    fig.suptitle(
        "Partial Dependence (teal) + ICE (blue) — Top 4 Features",
        fontsize=11, color=TEAL, y=1.01
    )
    fig.tight_layout()
    fig.savefig("plot_4_pdp_ice.png", dpi=150, bbox_inches="tight",
                facecolor=BG)
    plt.close(fig)                  # must close before switching backend back

    matplotlib.use(_orig_backend)   # restore original backend for other plots
    print("✔  plot_4_pdp_ice.png\n")


# ═══════════════════════════════════════════════════════════════════════════════
# 5.  SHAP — TreeSHAP (Regressor)
# ═══════════════════════════════════════════════════════════════════════════════

def plot_shap(rf, X_train, X_test, feature_names):
    """
    TreeSHAP for RandomForestRegressor (Lundberg et al. 2020).

    Prediction decomposition:
        f(x) = phi_0 + Σ_{j=1}^{p} phi_j

    Shapley value:
        phi_j = Σ_{S ⊆ F\\{j}}  |S|!(|F|-|S|-1)!/|F|!  · [f(S∪{j}) − f(S)]

    ── ROOT CAUSE OF THE ORIGINAL ERROR ───────────────────────────────────────
    "only integer scalar arrays can be converted to a scalar index"

    This error appears when code does `shap_values[1]` treating the output as
    a list (classifier pattern). For a RandomForestRegressor, shap_values is a
    plain 2-D ndarray of shape (n_samples, n_features) — indexing it with [1]
    selects the second ROW, returning a 1-D array. Downstream code then tries
    to use that 1-D array where a 2-D array is expected, causing the error.

    Fix: never index shap_values for a regressor. Use it directly.
    Similarly, expected_value is a plain scalar float, not a list — no [1].
    ───────────────────────────────────────────────────────────────────────────
    """
    # Use a background sample for speed (100 rows is sufficient for TreeSHAP)
    background   = shap.sample(X_train, 100, random_state=42)
    explainer    = shap.TreeExplainer(rf, data=background)

    # For RFRegressor: always a 2-D ndarray (n_samples, n_features)
    sv           = explainer.shap_values(X_test)          # shape: (n, p)
    base_val     = float(explainer.expected_value)         # scalar float

    assert sv.ndim == 2, f"Expected 2-D shap_values, got shape {sv.shape}"
    print(f"  shap_values shape : {sv.shape}")
    print(f"  expected_value    : {base_val:.4f}")

    feature_list = list(feature_names)

    # ── 5a. Beeswarm summary ─────────────────────────────────────────────────
    shap.summary_plot(sv, X_test, feature_names=feature_list,
                      show=False, plot_size=(10, 6))
    plt.gca().set_title("SHAP Summary — Beeswarm",
                         fontsize=12, color=PURPLE, pad=10)
    plt.tight_layout()
    plt.savefig("plot_5a_shap_beeswarm.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("✔  plot_5a_shap_beeswarm.png")

    # ── 5b. Bar plot (mean |phi_j|) ──────────────────────────────────────────
    shap.summary_plot(sv, X_test, feature_names=feature_list,
                      plot_type="bar", show=False, plot_size=(9, 5), color=TEAL)
    plt.gca().set_title("SHAP Global Importance — Mean |phi_j|",
                         fontsize=12, color=TEAL, pad=10)
    plt.tight_layout()
    plt.savefig("plot_5b_shap_bar.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("✔  plot_5b_shap_bar.png")

    # ── 5c. Waterfall (single sample) ────────────────────────────────────────
    sample_idx = 0
    exp = shap.Explanation(
        values        = sv[sample_idx],          # 1-D array shape (p,)
        base_values   = base_val,                # scalar — NOT base_val[1]
        data          = X_test.iloc[sample_idx].values,
        feature_names = feature_list,
    )
    shap.waterfall_plot(exp, max_display=15, show=False)
    plt.gca().set_title(f"SHAP Waterfall — Sample #{sample_idx}",
                         fontsize=12, color=CORAL, pad=10)
    plt.tight_layout()
    plt.savefig("plot_5c_shap_waterfall.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("✔  plot_5c_shap_waterfall.png")

    # ── 5d. Dependence plot (most important feature) ──────────────────────────
    top_feat = feature_list[int(np.argmax(np.abs(sv).mean(axis=0)))]
    shap.dependence_plot(top_feat, sv, X_test, feature_names=feature_list,
                         show=False, dot_size=20, alpha=0.5)
    plt.gca().set_title(f"SHAP Dependence — {top_feat}",
                         fontsize=12, color=GOLD, pad=10)
    plt.tight_layout()
    plt.savefig("plot_5d_shap_dependence.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("✔  plot_5d_shap_dependence.png\n")

    return sv


# ═══════════════════════════════════════════════════════════════════════════════
# 6.  TREE SPLIT VISUALISATION
# ═══════════════════════════════════════════════════════════════════════════════

def plot_single_tree(rf, feature_names, tree_index=0, max_depth=3):
    """
    Render one estimator from the forest with sklearn.tree.plot_tree.

    Capped at max_depth=3 for readability. Each node shows:
      • Split condition  (feature <= threshold)
      • MSE             (node impurity for regression)
      • samples         (number of training samples at node)
      • value           (mean target in node = local prediction)

    Colour intensity maps to predicted value (lighter = lower, darker = higher).
    """
    tree = rf.estimators_[tree_index]
    fig, ax = plt.subplots(figsize=(22, 8), facecolor=BG)
    ax.set_facecolor(BG)

    plot_tree(
        tree,
        max_depth    = max_depth,
        feature_names= list(feature_names),
        filled       = True,
        impurity     = True,
        rounded      = True,
        fontsize     = 8,
        ax           = ax,
        precision    = 3,
    )
    ax.set_title(
        f"Tree #{tree_index} from forest  (showing max_depth={max_depth})\n"
        f"Full tree depth = {tree.get_depth()}  |  Leaves = {tree.get_n_leaves()}",
        fontsize=12, color=PURPLE, pad=12
    )
    fig.tight_layout()
    fig.savefig("plot_6a_single_tree.png", dpi=150, bbox_inches="tight",
                facecolor=BG)
    plt.show()
    print("✔  plot_6a_single_tree.png")


def plot_decision_path(rf, X_test, feature_names, tree_index=0, sample_idx=0):
    """
    Trace the exact path a single sample takes through one tree.

    sklearn's decision_path() returns a sparse boolean matrix of shape
    (n_samples, n_nodes). The non-zero column indices for a given row
    are the node IDs visited during inference.

    At each internal node we record:
      • which feature was tested
      • the threshold value
      • the sample's actual feature value
      • which branch was taken (left = True if value <= threshold)
    At the leaf we record the final prediction (mean target value).
    """
    tree     = rf.estimators_[tree_index]
    t        = tree.tree_
    sample   = X_test.iloc[[sample_idx]]
    path_mat = tree.decision_path(sample)
    node_ids = path_mat.indices                    # nodes visited

    records = []
    for node_id in node_ids:
        if t.children_left[node_id] == -1:         # leaf node
            records.append({
                "type":  "LEAF",
                "label": f"LEAF  →  Predict: {t.value[node_id][0][0]:.4f}",
            })
        else:
            feat_idx = t.feature[node_id]
            feat     = feature_names[feat_idx]
            thresh   = t.threshold[node_id]
            val      = float(sample.iloc[0, feat_idx])
            branch   = "≤  LEFT ↙" if val <= thresh else ">  RIGHT ↘"
            records.append({
                "type":  "SPLIT",
                "label": (f"Node {node_id}: {feat} ≤ {thresh:.3f}\n"
                          f"  sample = {val:.3f}   →  {branch}"),
                "left":  val <= thresh,
            })

    n = len(records)
    fig, ax = plt.subplots(figsize=(10, max(6, n * 1.35)))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, n + 1)
    ax.axis("off")

    for i, rec in enumerate(records):
        y       = n - i
        is_leaf = rec["type"] == "LEAF"
        border  = TEAL if is_leaf else BLUE
        ax.text(5, y, rec["label"],
                ha="center", va="center", fontsize=9, color=FG,
                fontfamily="monospace",
                bbox=dict(boxstyle="round,pad=0.5",
                          facecolor="#F0F4FF", edgecolor=border, lw=1.8))
        if i < n - 1:
            went_left  = records[i].get("left", True)
            arr_color  = TEAL if went_left else CORAL
            ax.annotate("", xy=(5, y - 0.55), xytext=(5, y - 0.12),
                        arrowprops=dict(arrowstyle="-|>", color=arr_color, lw=1.5))

    ax.set_title(
        f"Decision Path — Sample #{sample_idx}  |  Tree #{tree_index}\n"
        f"Path length: {n} nodes  (depth = {n - 1})",
        fontsize=11, color=GOLD, pad=10
    )
    fig.tight_layout()
    fig.savefig("plot_6b_decision_path.png", dpi=150, bbox_inches="tight",
                facecolor=BG)
    plt.show()
    print("✔  plot_6b_decision_path.png")


def plot_split_frequency(rf, feature_names, top_n=8):
    """
    Count how many times each feature is chosen as a split, weighted by
    the fraction of training samples that flow through each split node.

    For tree t and node v:
        weight(v) = n_node_samples[v] / n_node_samples[root]

    Aggregated over all T trees and normalised:
        SplitFreq(Xj) = (1/T) Σ_t Σ_{v ∈ V_t(Xj)}  weight(v)

    Complements MDI: shows structural usage of features, not just
    impurity reduction.
    """
    counts = np.zeros(len(feature_names))
    for tree in rf.estimators_:
        t = tree.tree_
        n_root = t.n_node_samples[0]
        for v in range(t.node_count):
            if t.children_left[v] != -1:              # internal node
                counts[t.feature[v]] += t.n_node_samples[v] / n_root
    counts /= rf.n_estimators

    df = pd.DataFrame({"feature": feature_names, "weighted_splits": counts})
    df = df.nlargest(top_n, "weighted_splits").sort_values("weighted_splits")

    fig, ax = plt.subplots(figsize=(9, 5))
    colors  = plt.cm.YlOrBr(np.linspace(0.25, 0.85, len(df)))
    bars    = ax.barh(df["feature"], df["weighted_splits"], color=colors, height=0.6)

    for bar, val in zip(bars, df["weighted_splits"]):
        ax.text(val + df["weighted_splits"].max() * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"{val:.2f}", va="center", fontsize=8, color=FG)

    ax.set_xlabel("Avg. weighted split frequency per tree")
    ax.set_title("Feature Split Frequency (sample-weighted)",
                 fontsize=12, color=GOLD, pad=10)
    ax.grid(axis="x")
    fig.tight_layout()
    fig.savefig("plot_6c_split_frequency.png", dpi=150, bbox_inches="tight",
                facecolor=BG)
    plt.show()
    print("✔  plot_6c_split_frequency.png\n")


# ═══════════════════════════════════════════════════════════════════════════════
# 7.  PROXIMITY MATRIX + MDS
# ═══════════════════════════════════════════════════════════════════════════════

def compute_proximity_matrix(rf, X, n_samples=150):
    """
    Proximity matrix (Breiman 2001):
        P_ij = #{trees where x_i and x_j land in same leaf} / T

    P_ij ∈ [0, 1].  High proximity → structurally similar observations.
    Vectorised outer equality avoids Python-level loops over samples.
    Complexity: O(T · n²).
    """
    X_sub  = X.iloc[:n_samples] if hasattr(X, "iloc") else X[:n_samples]
    leaves = rf.apply(X_sub)                           # (n, T)
    T      = rf.n_estimators
    prox   = np.zeros((n_samples, n_samples))

    for t in range(T):
        leaf_t = leaves[:, t]
        prox  += (leaf_t[:, None] == leaf_t[None, :]).astype(float)

    prox /= T
    np.fill_diagonal(prox, 1.0)
    return prox


def plot_proximity_and_mds(rf, X, y, n_samples=150):
    prox  = compute_proximity_matrix(rf, X, n_samples)
    y_sub = y[:n_samples]

    # ── 7a. Heatmap ───────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(prox, cmap="YlGnBu", aspect="auto", vmin=0, vmax=1)
    plt.colorbar(im, ax=ax, label="Proximity P_ij")
    ax.set_title(f"Proximity Matrix  (n={n_samples})",
                 fontsize=12, color=BLUE, pad=10)
    ax.set_xlabel("Sample index")
    ax.set_ylabel("Sample index")
    fig.tight_layout()
    fig.savefig("plot_7a_proximity_matrix.png", dpi=150, bbox_inches="tight",
                facecolor=BG)
    plt.show()
    print("✔  plot_7a_proximity_matrix.png")

    # ── 7b. MDS projection ────────────────────────────────────────────────────
    mds    = MDS(n_components=2, dissimilarity="precomputed",
                 random_state=42, normalized_stress="auto")
    coords = mds.fit_transform(1 - prox)

    fig, ax = plt.subplots(figsize=(8, 6))
    sc = ax.scatter(coords[:, 0], coords[:, 1], c=y_sub,
                    cmap="RdYlBu_r", s=55, alpha=0.8, edgecolors="#CCCCCC", linewidths=0.4)
    plt.colorbar(sc, ax=ax, label="Target value (y)")
    ax.set_title("MDS Projection of Proximity Matrix",
                 fontsize=12, color=BLUE, pad=10)
    ax.set_xlabel("MDS Dimension 1")
    ax.set_ylabel("MDS Dimension 2")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig("plot_7b_proximity_mds.png", dpi=150, bbox_inches="tight",
                facecolor=BG)
    plt.show()
    print("✔  plot_7b_proximity_mds.png\n")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 62)
    print("  Random Forest Regressor — Interpretation Pipeline")
    print("=" * 62, "\n")

    rf, X_train, X_test, y_train, y_test, X, y, feature_names = \
        load_data_and_train()

    print("── 1. MDI Feature Importance ──────────────────────────────────")
    plot_mdi_importance(rf, feature_names)

    print("── 2. Permutation Importance (MDA) ────────────────────────────")
    plot_permutation_importance(rf, X_test, y_test, feature_names)

    print("── 3. OOB R² Curve ─────────────────────────────────────────────")
    plot_oob_curve(X_train, y_train)

    print("── 4. PDP + ICE ────────────────────────────────────────────────")
    plot_pdp_ice(rf, X_train, feature_names)

    print("── 5. SHAP (TreeSHAP) ──────────────────────────────────────────")
    sv = plot_shap(rf, X_train, X_test, feature_names)

    print("── 6. Tree Split Visualisation ─────────────────────────────────")
    plot_single_tree(rf, feature_names, tree_index=0, max_depth=3)
    plot_decision_path(rf, X_test, feature_names, tree_index=0, sample_idx=0)
    plot_split_frequency(rf, feature_names)

    print("── 7. Proximity Matrix & MDS ───────────────────────────────────")
    plot_proximity_and_mds(rf, X, y, n_samples=150)

    print("── 8. Logical Split Explanations ───────────────────────────────")
    direction_df = plot_feature_directions(
        sv, X_test, feature_names, target_name="y", predictor_label="feature"
    )
    rules = extract_all_rules(rf, feature_names, max_depth=3, max_trees=20)
    plot_rule_table(rules, feature_names, direction_df, target_name="y", top_n=8)
    slope_df, pdp_curves = plot_pdp_slopes(rf, X_train, feature_names, target_name="y")
    plot_pdp_annotated(pdp_curves, slope_df, feature_names, target_name="y")
    print_narrative_summary(direction_df, slope_df, feature_names, target_name="y")

    print("=" * 62)
    print("  Done. All plots saved to current directory.")
    print("=" * 62)


if __name__ == "__main__":
    main()

# ═══════════════════════════════════════════════════════════════════════════════
# 8.  LOGICAL SPLIT EXPLANATIONS
#     — "If real GDP rises, the model predicts interest rates rise"
# ═══════════════════════════════════════════════════════════════════════════════

# ── 8a. Feature Direction Analysis ──────────────────────────────────────────

def compute_feature_directions(sv, X_test, feature_names):
    """
    Determine the causal direction of each feature on the prediction
    using Spearman rank correlation between feature values and SHAP values.

    Rationale (Lundberg et al. 2020):
      φ_j(x) is the marginal contribution of feature j to prediction f(x).
      If ρ_S(x_j, φ_j) > 0  →  higher x_j pushes the prediction UP.
      If ρ_S(x_j, φ_j) < 0  →  higher x_j pushes the prediction DOWN.
      If ρ_S(x_j, φ_j) ≈ 0  →  non-monotonic or negligible effect.

    Spearman (not Pearson) is used because tree-based SHAP effects are
    often non-linear — rank correlation captures monotonic relationships
    without assuming linearity.

    Returns a DataFrame sorted by absolute effect strength.
    """
    from scipy.stats import spearmanr

    rows = []
    for i, feat in enumerate(feature_names):
        rho, pval = spearmanr(X_test.iloc[:, i].values, sv[:, i])
        rows.append({
            "feature"    : feat,
            "rho"        : rho,          # Spearman ρ ∈ [−1, +1]
            "pval"       : pval,
            "direction"  : "positive" if rho > 0 else "negative",
            "significant": pval < 0.05,
        })

    return pd.DataFrame(rows).sort_values("rho")


def plot_feature_directions(sv, X_test, feature_names,
                            target_name="y", predictor_label="feature"):
    """
    Diverging bar chart of Spearman ρ between each feature and its SHAP value.

    Positive bar  →  feature ↑  causes prediction ↑
    Negative bar  →  feature ↑  causes prediction ↓
    Hatched bar   →  not statistically significant (p ≥ 0.05)

    The magnitude of ρ reflects how consistently monotonic the relationship is,
    not the size of the effect (use SHAP mean |φ_j| for that).
    """
    df = compute_feature_directions(sv, X_test, feature_names)

    colors = [BLUE if r > 0 else CORAL for r in df["rho"]]
    hatches = ["" if sig else "///" for sig in df["significant"]]

    fig, ax = plt.subplots(figsize=(10, 6))
    ypos  = np.arange(len(df))
    bars  = ax.barh(ypos, df["rho"], color=colors, height=0.6,
                    edgecolor=BORDER, linewidth=0.8)
    for bar, hatch in zip(bars, hatches):
        bar.set_hatch(hatch)

    ax.set_yticks(ypos)
    ax.set_yticklabels(df["feature"], fontsize=10)
    ax.axvline(0, color=FG, linewidth=1.1, linestyle="-")
    ax.set_xlabel("Spearman ρ  (feature value vs. SHAP value)", fontsize=10)
    ax.set_title(
        f"Feature Direction Analysis\n"
        f"Blue = {predictor_label} ↑ → {target_name} ↑     "
        f"Red = {predictor_label} ↑ → {target_name} ↓     "
        f"/// = not significant (p ≥ 0.05)",
        fontsize=11, color=FG, pad=12
    )
    ax.set_xlim(-1.15, 1.15)

    # Annotate ρ values
    for i, (rho, sig) in enumerate(zip(df["rho"], df["significant"])):
        sign = "★" if sig else ""
        ax.text(rho + (0.03 if rho >= 0 else -0.03), i,
                f"{rho:+.2f}{sign}", va="center",
                ha="left" if rho >= 0 else "right",
                fontsize=8, color=FG)

    ax.grid(axis="x")
    fig.tight_layout()
    fig.savefig("plot_8a_feature_directions.png", dpi=150, bbox_inches="tight",
                facecolor=BG)
    plt.show()
    print("✔  plot_8a_feature_directions.png")

    return df


# ── 8b. Rule Extraction ───────────────────────────────────────────────────────

def extract_all_rules(rf, feature_names, max_depth=3, max_trees=10):
    """
    Extract every root-to-leaf path from the first max_trees trees as
    a list of dicts:
        { conditions: [...], prediction: float, n_samples: int, tree: int }

    Each condition is a dict:
        { feature, threshold, direction, split_str }
    where direction is "low" (≤ threshold) or "high" (> threshold).

    Limited to max_depth levels for readability.
    """
    all_rules = []

    for tree_idx, estimator in enumerate(rf.estimators_[:max_trees]):
        t = estimator.tree_

        def recurse(node, conditions, depth):
            if depth > max_depth or t.children_left[node] == -1:
                all_rules.append({
                    "tree"        : tree_idx,
                    "conditions"  : list(conditions),
                    "prediction"  : float(t.value[node][0][0]),
                    "n_samples"   : int(t.n_node_samples[node]),
                    "mse"         : float(t.impurity[node]),
                })
                return
            feat   = feature_names[t.feature[node]]
            thresh = t.threshold[node]
            recurse(t.children_left[node],
                    conditions + [{"feature": feat, "threshold": thresh,
                                   "direction": "low",
                                   "split_str": f"{feat} ≤ {thresh:.3f}"}],
                    depth + 1)
            recurse(t.children_right[node],
                    conditions + [{"feature": feat, "threshold": thresh,
                                   "direction": "high",
                                   "split_str": f"{feat} > {thresh:.3f}"}],
                    depth + 1)

        recurse(0, [], 0)

    return all_rules


def rules_to_narrative(rules, feature_names, direction_df,
                        target_name="y", top_n=10):
    """
    Convert extracted decision rules into plain-English narratives.

    Each condition in a rule is enriched with economic/domain direction:
      "x0 > 1.2"  →  "x0 is HIGH (above 1.200)"
    Then combined with the SHAP direction label to produce:
      "When x0 is HIGH → model predicts y INCREASES"

    Rules are ranked by |prediction − global_mean| so the most
    extreme (most interesting) rules surface first.

    Returns a list of narrative strings.
    """
    global_mean = np.mean([r["prediction"] for r in rules])

    dir_map = dict(zip(direction_df["feature"], direction_df["direction"]))

    def condition_to_text(cond):
        feat      = cond["feature"]
        direction = cond["direction"]        # "low" or "high"
        thresh    = cond["threshold"]
        level     = "HIGH" if direction == "high" else "LOW"
        return f"{feat} is {level} (threshold {thresh:.3f})"

    narratives = []
    for rule in sorted(rules,
                       key=lambda r: abs(r["prediction"] - global_mean),
                       reverse=True)[:top_n]:
        cond_texts = [condition_to_text(c) for c in rule["conditions"]]
        pred       = rule["prediction"]
        pred_dir   = "↑ ABOVE" if pred > global_mean else "↓ BELOW"
        narrative  = (
            "IF   " + "\n AND ".join(cond_texts) + "\n"
            f"THEN {target_name} is predicted {pred_dir} average "
            f"(predicted = {pred:.3f},  global mean = {global_mean:.3f})\n"
            f"     [covers {rule['n_samples']} samples in tree #{rule['tree']}]"
        )
        narratives.append(narrative)

    return narratives


def plot_rule_table(rules, feature_names, direction_df,
                    target_name="y", top_n=8):
    """
    Visualise the top decision rules as a colour-coded table.

    Each row = one rule. Columns = split conditions + predicted value.
    Cell colour:
      Blue  = condition where feature is HIGH
      Red   = condition where feature is LOW
      Green = prediction above global mean
      Pink  = prediction below global mean
    """
    global_mean = np.mean([r["prediction"] for r in rules])
    top_rules   = sorted(rules,
                         key=lambda r: abs(r["prediction"] - global_mean),
                         reverse=True)[:top_n]

    max_conds = max(len(r["conditions"]) for r in top_rules)
    col_labels = [f"Condition {i+1}" for i in range(max_conds)] + ["Prediction"]

    cell_text   = []
    cell_colors = []

    for rule in top_rules:
        row_text   = []
        row_colors = []
        for i in range(max_conds):
            if i < len(rule["conditions"]):
                c     = rule["conditions"][i]
                label = f"{c['feature']} {'>' if c['direction']=='high' else '≤'} {c['threshold']:.3f}"
                color = "#DBEAFE" if c["direction"] == "high" else "#FEE2E2"
            else:
                label = "—"
                color = "#F9FAFB"
            row_text.append(label)
            row_colors.append(color)

        pred_val   = rule["prediction"]
        pred_label = f"{pred_val:.3f}"
        pred_color = "#D1FAE5" if pred_val > global_mean else "#FCE7F3"
        row_text.append(pred_label)
        row_colors.append(pred_color)

        cell_text.append(row_text)
        cell_colors.append(row_colors)

    fig_h = max(4, top_n * 0.55 + 1.5)
    fig, ax = plt.subplots(figsize=(max(12, max_conds * 3.5), fig_h))
    ax.axis("off")

    tbl = ax.table(
        cellText    = cell_text,
        cellColours = cell_colors,
        colLabels   = col_labels,
        loc         = "center",
        cellLoc     = "center",
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    tbl.scale(1, 1.6)

    # Style header row
    for j in range(len(col_labels)):
        tbl[0, j].set_facecolor("#1E3A5F")
        tbl[0, j].set_text_props(color="white", fontweight="bold")

    ax.set_title(
        f"Top {top_n} Decision Rules by Deviation from Mean\n"
        f"Blue cells = feature HIGH   |   Red cells = feature LOW   |   "
        f"Green prediction = above mean ({global_mean:.3f})   |   Pink = below",
        fontsize=10, color=FG, pad=14, loc="left"
    )
    fig.tight_layout()
    fig.savefig("plot_8b_rule_table.png", dpi=150, bbox_inches="tight",
                facecolor=BG)
    plt.show()
    print("✔  plot_8b_rule_table.png")


# ── 8c. PDP Slope Chart ───────────────────────────────────────────────────────

def plot_pdp_slopes(rf, X_train, feature_names,
                   target_name="y", n_points=60):
    """
    Quantify and visualise the direction and shape of each feature's
    marginal effect by computing PDP slopes.

    For feature j with grid points [x_min, ..., x_max]:
        slope_j = (PDP(x_max) − PDP(x_min)) / (x_max − x_min)

    A positive slope → feature ↑ causes prediction ↑  (on average).
    A negative slope → feature ↑ causes prediction ↓.

    Non-linearity index:
        NL_j = std(Δ PDP) / |mean(Δ PDP)|
    High NL → the effect reverses or accelerates across the feature range.

    This directly answers "if real GDP rises, does interest rate rise?"
    using the model's learned marginal response.
    """
    from sklearn.inspection import partial_dependence

    slopes      = []
    nl_indices  = []
    pdp_curves  = {}

    for feat in feature_names:
        idx    = list(feature_names).index(feat)
        result = partial_dependence(rf, X_train, features=[idx],
                                    grid_resolution=n_points, kind="average")
        grid   = result["grid_values"][0]
        avg    = result["average"][0]

        delta     = np.diff(avg)
        slope     = (avg[-1] - avg[0]) / (grid[-1] - grid[0])
        nl        = (np.std(delta) / (abs(np.mean(delta)) + 1e-9))
        slopes.append(slope)
        nl_indices.append(nl)
        pdp_curves[feat] = (grid, avg)

    df = pd.DataFrame({
        "feature"       : list(feature_names),
        "slope"         : slopes,
        "nonlinearity"  : nl_indices,
    }).sort_values("slope")

    # ── Plot 1: slope bar chart ───────────────────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(14, 6),
                             gridspec_kw={"width_ratios": [1.4, 1]})

    ax = axes[0]
    colors  = [BLUE if s > 0 else CORAL for s in df["slope"]]
    ypos    = np.arange(len(df))
    ax.barh(ypos, df["slope"], color=colors, height=0.6,
            edgecolor=BORDER, linewidth=0.7)
    ax.set_yticks(ypos)
    ax.set_yticklabels(df["feature"], fontsize=10)
    ax.axvline(0, color=FG, lw=1.0)
    ax.set_xlabel(f"PDP slope  (Δ {target_name} / Δ feature)")
    ax.set_title(f"Marginal Effect Direction\n"
                 f"Blue = {target_name} rises with feature  |  "
                 f"Red = {target_name} falls",
                 fontsize=11, color=FG)

    for i, (s, feat) in enumerate(zip(df["slope"], df["feature"])):
        ax.text(s + (abs(df["slope"].max()) * 0.02 if s >= 0
                     else -abs(df["slope"].max()) * 0.02),
                i, f"{s:+.4f}", va="center",
                ha="left" if s >= 0 else "right",
                fontsize=8, color=FG)

    # ── Plot 2: non-linearity scatter ─────────────────────────────────────────
    ax2 = axes[1]
    x2  = df["slope"].values
    y2  = df["nonlinearity"].values
    sc  = ax2.scatter(x2, y2, c=[BLUE if s > 0 else CORAL for s in x2],
                      s=90, edgecolors=BORDER, linewidths=0.8, zorder=3)
    for _, row in df.iterrows():
        ax2.annotate(row["feature"],
                     xy=(row["slope"], row["nonlinearity"]),
                     xytext=(5, 3), textcoords="offset points",
                     fontsize=8, color=MUTED)
    ax2.axvline(0, color=FG, lw=0.8, linestyle="--")
    ax2.set_xlabel(f"PDP slope")
    ax2.set_ylabel("Non-linearity index  (high = effect changes direction)")
    ax2.set_title("Effect Shape\nLinear vs. Non-linear", fontsize=11, color=FG)
    ax2.grid(True, alpha=0.5)

    fig.suptitle(
        f"How does each feature affect {target_name}? — PDP Slope Analysis",
        fontsize=13, color=FG, y=1.01, fontweight="bold"
    )
    fig.tight_layout()
    fig.savefig("plot_8c_pdp_slopes.png", dpi=150, bbox_inches="tight",
                facecolor=BG)
    plt.show()
    print("✔  plot_8c_pdp_slopes.png")

    return df, pdp_curves


def plot_pdp_annotated(pdp_curves, slope_df, feature_names,
                       target_name="y", cols=3):
    """
    Plot each feature's PDP curve annotated with:
      • A directional arrow showing overall slope
      • Shading where the curve is rising vs. falling
      • The slope value in the subtitle

    This makes each plot self-contained and readable in isolation,
    e.g. for inclusion in reports or slides.
    """
    n    = len(feature_names)
    rows = int(np.ceil(n / cols))
    fig, axes = plt.subplots(rows, cols,
                             figsize=(cols * 4.5, rows * 3.5))
    axes = axes.flatten()

    slope_map = dict(zip(slope_df["feature"], slope_df["slope"]))
    nl_map    = dict(zip(slope_df["feature"], slope_df["nonlinearity"]))

    for ax, feat in zip(axes, feature_names):
        grid, avg = pdp_curves[feat]
        slope     = slope_map[feat]
        nl        = nl_map[feat]
        color     = BLUE if slope > 0 else CORAL
        arrow     = "↑" if slope > 0 else "↓"

        ax.plot(grid, avg, color=color, lw=2.2, zorder=3)

        # Shade rising vs. falling segments
        for i in range(len(avg) - 1):
            seg_color = BLUE if avg[i+1] >= avg[i] else CORAL
            ax.fill_between(grid[i:i+2], avg[i:i+2],
                            alpha=0.12, color=seg_color)

        # Reference mean line
        ax.axhline(np.mean(avg), color=MUTED, lw=0.9,
                   linestyle="--", label=f"mean={np.mean(avg):.3f}")

        ax.set_title(
            f"{feat}  {arrow}  (slope={slope:+.3f}, NL={nl:.2f})",
            fontsize=9, color=color
        )
        ax.set_xlabel(feat, fontsize=8)
        ax.set_ylabel(target_name, fontsize=8)
        ax.tick_params(labelsize=7)
        ax.grid(True, alpha=0.4)

    # Hide empty subplots
    for ax in axes[n:]:
        ax.set_visible(False)

    fig.suptitle(
        f"PDP Curves — How each feature shifts the predicted {target_name}\n"
        f"Blue = rising effect  |  Red = falling effect  |  NL = non-linearity index",
        fontsize=11, color=FG, y=1.01
    )
    fig.tight_layout()
    fig.savefig("plot_8d_pdp_annotated.png", dpi=150, bbox_inches="tight",
                facecolor=BG)
    plt.show()
    print("✔  plot_8d_pdp_annotated.png\n")


# ── 8e. Narrative summary ─────────────────────────────────────────────────────

def print_narrative_summary(direction_df, slope_df, feature_names,
                             target_name="y", predictor_label="feature"):
    """
    Print a plain-English summary table of every feature's effect,
    combining:
      • SHAP-based direction (sign of Spearman ρ between x and φ)
      • PDP-based direction  (sign of overall PDP slope)
      • Agreement flag       (both methods agree?)
      • Non-linearity index  (is the effect consistent or shape-shifting?)
    """
    shap_dir  = dict(zip(direction_df["feature"], direction_df["direction"]))
    shap_rho  = dict(zip(direction_df["feature"], direction_df["rho"]))
    shap_sig  = dict(zip(direction_df["feature"], direction_df["significant"]))
    pdp_slope = dict(zip(slope_df["feature"],     slope_df["slope"]))
    pdp_nl    = dict(zip(slope_df["feature"],     slope_df["nonlinearity"]))

    header = (f"\n{'─'*74}\n"
              f"  LOGICAL EFFECT SUMMARY  →  how each feature affects '{target_name}'\n"
              f"{'─'*74}")
    print(header)
    print(f"  {'Feature':<12} {'SHAP dir':>10} {'PDP slope':>10} "
          f"{'Agree':>6} {'Significant':>12} {'Non-linear':>11}")
    print(f"  {'─'*12} {'─'*10} {'─'*10} {'─'*6} {'─'*12} {'─'*11}")

    for feat in sorted(feature_names,
                       key=lambda f: abs(shap_rho[f]), reverse=True):
        s_dir  = "↑ rises"  if shap_dir[feat] == "positive" else "↓ falls"
        p_dir  = "↑ rises"  if pdp_slope[feat] > 0           else "↓ falls"
        agree  = "✔" if shap_dir[feat] == ("positive" if pdp_slope[feat] > 0
                                            else "negative") else "✘"
        sig    = "★ yes"    if shap_sig[feat]                else "  no"
        nl_lvl = ("high" if pdp_nl[feat] > 2.0 else
                  "medium" if pdp_nl[feat] > 0.5 else "low")
        print(f"  {feat:<12} {s_dir:>10} {p_dir:>10} "
              f"{agree:>6} {sig:>12} {nl_lvl:>11}")

    print(f"{'─'*74}")
    print("  ★ = significant at p < 0.05  |  NL high = non-monotonic effect\n")

if __name__ == "__main__":
    main()
