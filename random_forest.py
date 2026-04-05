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
DARK_BG  = "#0d0f18"
PANEL_BG = "#161925"
BORDER   = "#2e3248"
FG       = "#dde1f0"
MUTED    = "#8890aa"

PURPLE   = "#7c6aff"
TEAL     = "#00d4aa"
CORAL    = "#ff6b6b"
GOLD     = "#ffd166"

plt.rcParams.update({
    "figure.facecolor": DARK_BG,
    "axes.facecolor":   PANEL_BG,
    "axes.edgecolor":   BORDER,
    "axes.labelcolor":  FG,
    "axes.titlecolor":  FG,
    "xtick.color":      MUTED,
    "ytick.color":      MUTED,
    "text.color":       FG,
    "grid.color":       BORDER,
    "grid.linestyle":   "--",
    "grid.alpha":       0.5,
    "font.family":      "monospace",
    "legend.facecolor": PANEL_BG,
    "legend.edgecolor": BORDER,
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
    colors  = plt.cm.plasma(np.linspace(0.25, 0.92, len(imp)))
    bars    = ax.barh(imp.index, imp.values, color=colors, height=0.65)

    for bar, val in zip(bars, imp.values):
        ax.text(val + imp.max() * 0.01, bar.get_y() + bar.get_height() / 2,
                f"{val:.4f}", va="center", fontsize=8, color=MUTED)

    ax.set_xlabel("Mean Decrease in Impurity (MDI)")
    ax.set_title("Feature Importance — MDI", fontsize=13, color=PURPLE, pad=10)
    ax.set_xlim(0, imp.max() * 1.18)
    ax.grid(axis="x")
    fig.tight_layout()
    fig.savefig("plot_1_mdi_importance.png", dpi=150, bbox_inches="tight",
                facecolor=DARK_BG)
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
            error_kw=dict(ecolor="#ffffff44", capsize=3))
    ax.set_yticks(ypos)
    ax.set_yticklabels(df["feature"], fontsize=8)
    ax.set_xlabel(f"Mean R² Decrease ± SD  (n_repeats={n_repeats})")
    ax.set_title("Permutation Importance (MDA)", fontsize=13, color=TEAL, pad=10)
    ax.grid(axis="x")
    fig.tight_layout()
    fig.savefig("plot_2_permutation_importance.png", dpi=150, bbox_inches="tight",
                facecolor=DARK_BG)
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
    ax.fill_between(list(n_range), oob_r2s, alpha=0.12, color=CORAL)
    ax.axvline(best_n, color="#ffffff44", linestyle="--", lw=1.2)
    ax.annotate(f"max OOB R² = {best_r2:.4f}\n@ {best_n} trees",
                xy=(best_n, best_r2),
                xytext=(best_n + 20, best_r2 - 0.012),
                color=FG, fontsize=9,
                arrowprops=dict(arrowstyle="->", color="#ffffff66"))
    ax.set_xlabel("Number of Trees")
    ax.set_ylabel("OOB R²")
    ax.set_title("OOB R² vs. Number of Trees", fontsize=13, color=CORAL, pad=10)
    ax.grid()
    fig.tight_layout()
    fig.savefig("plot_3_oob_curve.png", dpi=150, bbox_inches="tight",
                facecolor=DARK_BG)
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
    """
    imp  = pd.Series(rf.feature_importances_, index=feature_names)
    top4 = imp.nlargest(4).index.tolist()

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for ax, feat in zip(axes.flatten(), top4):
        idx = list(feature_names).index(feat)
        PartialDependenceDisplay.from_estimator(
            rf, X_train, features=[idx],
            kind        = "both",
            subsample   = 200,
            n_jobs      = -1,
            random_state= 42,
            ax          = ax,
            ice_lines_kw= {"color": PURPLE, "alpha": 0.06, "lw": 0.7},
            pd_line_kw  = {"color": TEAL,   "lw": 2.5},
        )
        ax.set_title(feat, fontsize=9, color=FG)
        ax.set_facecolor(PANEL_BG)
        ax.tick_params(colors=MUTED, labelsize=7)
        ax.set_ylabel("Predicted value", fontsize=7)
        ax.grid(alpha=0.3)

    fig.suptitle(
        "Partial Dependence (teal) + ICE (purple) — Top 4 Features",
        fontsize=11, color=TEAL, y=1.01
    )
    fig.tight_layout()
    fig.savefig("plot_4_pdp_ice.png", dpi=150, bbox_inches="tight",
                facecolor=DARK_BG)
    plt.show()
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
    fig, ax = plt.subplots(figsize=(22, 8), facecolor=DARK_BG)
    ax.set_facecolor(DARK_BG)

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
                facecolor=DARK_BG)
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
        border  = TEAL if is_leaf else PURPLE
        ax.text(5, y, rec["label"],
                ha="center", va="center", fontsize=9, color=FG,
                fontfamily="monospace",
                bbox=dict(boxstyle="round,pad=0.5",
                          facecolor=PANEL_BG, edgecolor=border, lw=1.8))
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
                facecolor=DARK_BG)
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
    colors  = plt.cm.viridis(np.linspace(0.3, 0.9, len(df)))
    bars    = ax.barh(df["feature"], df["weighted_splits"], color=colors, height=0.6)

    for bar, val in zip(bars, df["weighted_splits"]):
        ax.text(val + df["weighted_splits"].max() * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"{val:.2f}", va="center", fontsize=8, color=MUTED)

    ax.set_xlabel("Avg. weighted split frequency per tree")
    ax.set_title("Feature Split Frequency (sample-weighted)",
                 fontsize=12, color=GOLD, pad=10)
    ax.grid(axis="x")
    fig.tight_layout()
    fig.savefig("plot_6c_split_frequency.png", dpi=150, bbox_inches="tight",
                facecolor=DARK_BG)
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
    im = ax.imshow(prox, cmap="plasma", aspect="auto", vmin=0, vmax=1)
    plt.colorbar(im, ax=ax, label="Proximity P_ij")
    ax.set_title(f"Proximity Matrix  (n={n_samples})",
                 fontsize=12, color=PURPLE, pad=10)
    ax.set_xlabel("Sample index")
    ax.set_ylabel("Sample index")
    fig.tight_layout()
    fig.savefig("plot_7a_proximity_matrix.png", dpi=150, bbox_inches="tight",
                facecolor=DARK_BG)
    plt.show()
    print("✔  plot_7a_proximity_matrix.png")

    # ── 7b. MDS projection ────────────────────────────────────────────────────
    mds    = MDS(n_components=2, dissimilarity="precomputed",
                 random_state=42, normalized_stress="auto")
    coords = mds.fit_transform(1 - prox)

    fig, ax = plt.subplots(figsize=(8, 6))
    sc = ax.scatter(coords[:, 0], coords[:, 1], c=y_sub,
                    cmap="plasma", s=55, alpha=0.8, edgecolors="#00000033")
    plt.colorbar(sc, ax=ax, label="Target value (y)")
    ax.set_title("MDS Projection of Proximity Matrix",
                 fontsize=12, color=PURPLE, pad=10)
    ax.set_xlabel("MDS Dimension 1")
    ax.set_ylabel("MDS Dimension 2")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig("plot_7b_proximity_mds.png", dpi=150, bbox_inches="tight",
                facecolor=DARK_BG)
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
    plot_shap(rf, X_train, X_test, feature_names)

    print("── 6. Tree Split Visualisation ─────────────────────────────────")
    plot_single_tree(rf, feature_names, tree_index=0, max_depth=3)
    plot_decision_path(rf, X_test, feature_names, tree_index=0, sample_idx=0)
    plot_split_frequency(rf, feature_names)

    print("── 7. Proximity Matrix & MDS ───────────────────────────────────")
    plot_proximity_and_mds(rf, X, y, n_samples=150)

    print("=" * 62)
    print("  Done. All 10 plots saved to current directory.")
    print("=" * 62)


if __name__ == "__main__":
    main()
