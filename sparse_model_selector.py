"""
Stability-Guided Sparse Model Selector
=======================================
Combines stability selection (Meinshausen & Bühlmann, 2010) with an
exhaustive cross-validated subset search to find a 3-5 predictor model
that is simultaneously stable and predictively performant.

Pipeline
--------
Stage 1 — Stability selection
    Rank all p predictors by their stability score Π̂.
    Retain the top-K as the candidate shortlist (default K=15).

Stage 2 — Exhaustive subset search
    For every subset of size min_size..max_size drawn from the shortlist,
    refit OLS (LinearRegression) and estimate CV R² with k-fold CV.
    Score each subset on:
        stability_score  = mean Π̂ of its members
        cv_r2            = cross-validated R² (OLS, no shrinkage)
    Identify Pareto-optimal subsets (not dominated on both axes).

Stage 3 — Final model
    User selects from the Pareto frontier. The default recommendation is
    the subset that maximises  alpha * cv_r2 + (1-alpha) * stability_score
    for a user-supplied trade-off weight alpha (default 0.6).

References
----------
Meinshausen, N. & Bühlmann, P. (2010). Stability selection.
    JRSS-B 72(4), 417–473. https://doi.org/10.1111/j.1467-9868.2010.00740.x
"""

from __future__ import annotations

import warnings
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from dataclasses import dataclass
from itertools import combinations
from typing import Optional

from sklearn.linear_model import LinearRegression, Lasso
from sklearn.model_selection import cross_val_score, KFold
from sklearn.preprocessing import StandardScaler
from sklearn.utils import check_random_state

# Re-use StabilitySelector from the companion module
from stability_selection import StabilitySelector


# ---------------------------------------------------------------------------
# Result containers
# ---------------------------------------------------------------------------

@dataclass
class SubsetResult:
    """One evaluated subset."""
    indices: tuple[int, ...]
    feature_names: list[str]
    size: int
    cv_r2: float
    stability_score: float      # mean max-Π̂ of members
    width_score: float          # mean fraction-of-grid-above-thr of members
    is_pareto: bool = False

    def __repr__(self):
        names = ", ".join(self.feature_names)
        return (
            f"SubsetResult([{names}], size={self.size}, "
            f"cv_r2={self.cv_r2:.3f}, stability={self.stability_score:.3f})"
        )


@dataclass
class SparseModelResult:
    """Full output of SparseModelSelector.fit()."""
    all_subsets: list[SubsetResult]
    pareto_subsets: list[SubsetResult]
    recommended: SubsetResult
    shortlist_indices: np.ndarray       # top-K stable feature indices
    shortlist_names: list[str]
    max_sel_probs: np.ndarray           # Π̂ for every feature in shortlist
    width_scores: np.ndarray            # fraction-of-grid scores for shortlist
    alpha: float                        # trade-off weight used
    feature_names_all: list[str] | None

    def summary(self) -> str:
        lines = [
            "=" * 62,
            "Sparse Model Selector — Summary",
            "=" * 62,
            f"  Shortlist size      : {len(self.shortlist_indices)}",
            f"  Subsets evaluated   : {len(self.all_subsets)}",
            f"  Pareto-optimal      : {len(self.pareto_subsets)}",
            f"  Trade-off α         : {self.alpha:.2f}  "
            f"(α×R² + (1-α)×stability)",
            "",
            "  Recommended model:",
            f"    Features   : {', '.join(self.recommended.feature_names)}",
            f"    Size       : {self.recommended.size}",
            f"    CV R²      : {self.recommended.cv_r2:.4f}",
            f"    Stability  : {self.recommended.stability_score:.4f}",
            f"    Width      : {self.recommended.width_score:.4f}",
            "",
            "  Full Pareto frontier (sorted by CV R²):",
            f"    {'Features':<40} {'Size':>4} {'CV R²':>7} {'Stab':>6} {'Width':>6}",
            "    " + "-" * 66,
        ]
        for s in sorted(self.pareto_subsets, key=lambda x: x.cv_r2, reverse=True):
            marker = " <-- recommended" if s is self.recommended else ""
            names = ", ".join(s.feature_names)
            lines.append(
                f"    {names:<40} {s.size:>4} "
                f"{s.cv_r2:>7.4f} {s.stability_score:>6.3f} "
                f"{s.width_score:>6.3f}{marker}"
            )
        lines.append("=" * 62)
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class SparseModelSelector:
    """
    Two-stage pipeline: stability selection → exhaustive subset search.

    Parameters
    ----------
    min_size, max_size : int
        Target model size range (inclusive). Default 3–5.
    shortlist_k : int, default=15
        Number of top-stable features to carry into the subset search.
        Must be >= max_size. Larger values find better subsets but increase
        search time as C(k, max_size).
    alpha : float in [0, 1], default=0.6
        Trade-off weight for the composite score:
            score = alpha * cv_r2 + (1-alpha) * stability_score
        0 = stability only, 1 = performance only.
    cv_folds : int, default=10
        K-fold CV folds used to estimate R² for each subset.
    stability_kwargs : dict, optional
        Extra keyword arguments forwarded to StabilitySelector
        (n_bootstraps, pi_thr, lambda_min_ratio, etc.).
    random_state : int or RandomState, optional
    verbose : bool, default=False
    """

    def __init__(
        self,
        min_size: int = 3,
        max_size: int = 5,
        shortlist_k: int = 15,
        alpha: float = 0.6,
        cv_folds: int = 10,
        stability_kwargs: dict | None = None,
        random_state=None,
        verbose: bool = False,
    ):
        if not (0.0 <= alpha <= 1.0):
            raise ValueError(f"alpha must be in [0, 1]; got {alpha}.")
        if shortlist_k < max_size:
            raise ValueError(
                f"shortlist_k ({shortlist_k}) must be >= max_size ({max_size})."
            )
        self.min_size = min_size
        self.max_size = max_size
        self.shortlist_k = shortlist_k
        self.alpha = alpha
        self.cv_folds = cv_folds
        self.stability_kwargs = stability_kwargs or {}
        self.random_state = random_state
        self.verbose = verbose

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_width_scores(
        sel_probs: np.ndarray, pi_thr: float
    ) -> np.ndarray:
        """Fraction of λ grid for which Π̂_j >= pi_thr."""
        return (sel_probs >= pi_thr).mean(axis=1)

    @staticmethod
    def _pareto_filter(subsets: list[SubsetResult]) -> list[SubsetResult]:
        """
        Identify Pareto-optimal subsets on (cv_r2, stability_score).
        A subset is dominated if another subset is strictly better on
        both axes simultaneously.
        """
        pareto = []
        for candidate in subsets:
            dominated = any(
                (other.cv_r2 >= candidate.cv_r2 and
                 other.stability_score >= candidate.stability_score and
                 (other.cv_r2 > candidate.cv_r2 or
                  other.stability_score > candidate.stability_score))
                for other in subsets
                if other is not candidate
            )
            if not dominated:
                pareto.append(candidate)
        return pareto

    def _cv_r2(
        self,
        X: np.ndarray,
        y: np.ndarray,
        indices: tuple[int, ...],
        rng,
    ) -> float:
        """Cross-validated R² for OLS on the given feature subset."""
        X_sub = X[:, indices]
        cv = KFold(n_splits=self.cv_folds, shuffle=True,
                   random_state=rng.randint(0, 2**31))
        scores = cross_val_score(
            LinearRegression(), X_sub, y, cv=cv, scoring="r2"
        )
        # Clip at 0 to avoid confusing negative R² from tiny subsets
        return float(np.clip(scores.mean(), 0, 1))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: list[str] | None = None,
    ) -> "SparseModelSelector":
        """
        Run the two-stage pipeline.

        Parameters
        ----------
        X : array-like of shape (n, p). Will be standardised internally.
        y : array-like of shape (n,)
        feature_names : list of str, optional

        Returns
        -------
        self  (access results via self.result_)
        """
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)
        rng = check_random_state(self.random_state)
        n, p = X.shape

        # --- Standardise ---
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        feature_names = (
            list(feature_names) if feature_names is not None
            else [f"X{i:02d}" for i in range(p)]
        )

        # ------------------------------------------------------------------
        # Stage 1: Stability selection
        # ------------------------------------------------------------------
        if self.verbose:
            print("Stage 1: running stability selection ...")

        ss_defaults = dict(
            n_bootstraps=100,
            n_lambdas=50,
            pi_thr=0.6,
            lambda_min_ratio=0.05,
            random_state=rng.randint(0, 2**31),
            verbose=self.verbose,
        )
        ss_defaults.update(self.stability_kwargs)
        selector = StabilitySelector(**ss_defaults)
        selector.fit(X_scaled, y, feature_names=feature_names)
        ss_result = selector.result_

        # Rank by max selection probability, take top-K
        order = np.argsort(ss_result.max_sel_probs)[::-1]
        shortlist_idx = order[:self.shortlist_k]
        shortlist_names = [feature_names[i] for i in shortlist_idx]
        shortlist_probs = ss_result.max_sel_probs[shortlist_idx]
        width_scores_all = self._compute_width_scores(
            ss_result.selection_probabilities, ss_result.pi_thr
        )
        shortlist_widths = width_scores_all[shortlist_idx]

        if self.verbose:
            print(f"  Shortlist ({self.shortlist_k} features): "
                  f"{', '.join(shortlist_names)}")

        # ------------------------------------------------------------------
        # Stage 2: Exhaustive subset search
        # ------------------------------------------------------------------
        n_combos = sum(
            len(list(combinations(range(self.shortlist_k), k)))
            for k in range(self.min_size, self.max_size + 1)
        )
        if self.verbose:
            print(f"Stage 2: evaluating {n_combos} subsets "
                  f"(size {self.min_size}–{self.max_size}) ...")

        all_subsets: list[SubsetResult] = []

        for size in range(self.min_size, self.max_size + 1):
            for combo in combinations(range(self.shortlist_k), size):
                # combo = positions within the shortlist
                global_idx = tuple(int(shortlist_idx[i]) for i in combo)
                names = [shortlist_names[i] for i in combo]
                stab = float(np.mean([shortlist_probs[i] for i in combo]))
                width = float(np.mean([shortlist_widths[i] for i in combo]))
                r2 = self._cv_r2(X_scaled, y, global_idx, rng)

                all_subsets.append(SubsetResult(
                    indices=global_idx,
                    feature_names=names,
                    size=size,
                    cv_r2=r2,
                    stability_score=stab,
                    width_score=width,
                ))

        # ------------------------------------------------------------------
        # Pareto filter and recommendation
        # ------------------------------------------------------------------
        pareto = self._pareto_filter(all_subsets)
        for s in all_subsets:
            s.is_pareto = s in pareto

        def composite(s: SubsetResult) -> float:
            return self.alpha * s.cv_r2 + (1 - self.alpha) * s.stability_score

        recommended = max(pareto, key=composite)

        self.result_ = SparseModelResult(
            all_subsets=all_subsets,
            pareto_subsets=pareto,
            recommended=recommended,
            shortlist_indices=shortlist_idx,
            shortlist_names=shortlist_names,
            max_sel_probs=shortlist_probs,
            width_scores=shortlist_widths,
            alpha=self.alpha,
            feature_names_all=feature_names,
        )
        self.scaler_ = scaler
        self.selector_ = selector
        return self

    # ------------------------------------------------------------------
    # Plotting
    # ------------------------------------------------------------------

    def plot_pareto(self, figsize=(8, 5)) -> plt.Figure:
        """
        Scatter plot of all evaluated subsets on (stability, CV R²).
        Pareto-optimal subsets are highlighted; the recommended one is starred.
        Points are coloured by model size.
        """
        res = self.result_
        fig, ax = plt.subplots(figsize=figsize)

        colors = {3: "#2563EB", 4: "#16A34A", 5: "#D97706",
                  6: "#9333EA", 7: "#DC2626"}

        # All non-pareto subsets (background)
        for s in res.all_subsets:
            if not s.is_pareto:
                ax.scatter(
                    s.stability_score, s.cv_r2,
                    color=colors.get(s.size, "#9CA3AF"),
                    alpha=0.25, s=18, zorder=2,
                )

        # Pareto subsets
        for s in res.pareto_subsets:
            ax.scatter(
                s.stability_score, s.cv_r2,
                color=colors.get(s.size, "#9CA3AF"),
                s=60, zorder=4, edgecolors="white", linewidths=0.8,
            )

        # Recommended
        ax.scatter(
            res.recommended.stability_score,
            res.recommended.cv_r2,
            marker="*", s=280, color="#DC2626", zorder=5,
            label=f"Recommended: [{', '.join(res.recommended.feature_names)}]",
        )

        # Pareto frontier line (sorted by stability)
        pf = sorted(res.pareto_subsets, key=lambda s: s.stability_score)
        ax.plot(
            [s.stability_score for s in pf],
            [s.cv_r2 for s in pf],
            color="#6B7280", lw=0.8, ls="--", zorder=3,
        )

        # Size legend
        for size, color in sorted(colors.items()):
            if any(s.size == size for s in res.all_subsets):
                ax.scatter([], [], color=color, s=40,
                           label=f"Size {size}")

        ax.set_xlabel("Stability score  (mean max Π̂)", fontsize=11)
        ax.set_ylabel("Cross-validated R²", fontsize=11)
        ax.set_title("Stability vs performance — all evaluated subsets", fontsize=11)
        ax.legend(fontsize=9, loc="lower right")
        fig.tight_layout()
        return fig

    def plot_shortlist(self, figsize=(8, 4)) -> plt.Figure:
        """
        Horizontal bar chart of the shortlist features, sorted by
        stability score. Width-score shown as a second bar for comparison.
        """
        res = self.result_
        k = len(res.shortlist_indices)
        order = np.argsort(res.max_sel_probs)
        names = [res.shortlist_names[i] for i in order]
        probs = res.max_sel_probs[order]
        widths = res.width_scores[order]

        fig, ax = plt.subplots(figsize=figsize)
        y = np.arange(k)
        ax.barh(y - 0.18, probs,  height=0.35, color="#2563EB",
                label="Max Π̂ (peak stability)", alpha=0.85)
        ax.barh(y + 0.18, widths, height=0.35, color="#93C5FD",
                label="Width score (breadth above π_thr)", alpha=0.85)

        # Highlight recommended features
        rec_names = set(res.recommended.feature_names)
        for i, name in enumerate(names):
            if name in rec_names:
                ax.axhspan(i - 0.45, i + 0.45,
                           color="#FEF9C3", alpha=0.5, zorder=0)

        ax.set_yticks(y)
        ax.set_yticklabels(names, fontsize=9)
        ax.set_xlabel("Score", fontsize=10)
        ax.set_xlim(0, 1.05)
        ax.set_title("Shortlist feature scores  (yellow = in recommended model)",
                     fontsize=10)
        ax.legend(fontsize=9)
        fig.tight_layout()
        return fig


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def _demo():
    rng = np.random.RandomState(42)
    n, p, n_true = 200, 100, 5

    X = rng.randn(n, p)

    # 5 true predictors with moderate signal; mild collinearity on 2 of them
    true_idx = [4, 17, 23, 55, 81]
    true_coef = np.zeros(p)
    true_coef[true_idx] = [0.8, -0.9, 0.7, 1.1, -0.6]

    # Add collinearity: X[:,90] is a noisy copy of X[:,23]
    X[:, 90] = X[:, 23] + rng.randn(n) * 0.3

    y = X @ true_coef + rng.randn(n) * 1.0

    feature_names = [f"X{i:03d}" for i in range(p)]

    print("Running SparseModelSelector (alpha=0.6, target size 3-5) ...")
    selector = SparseModelSelector(
        min_size=3,
        max_size=5,
        shortlist_k=15,
        alpha=0.6,
        cv_folds=10,
        stability_kwargs=dict(n_bootstraps=100, lambda_min_ratio=0.05),
        random_state=0,
        verbose=True,
    )
    selector.fit(X, y, feature_names=feature_names)
    res = selector.result_

    print(res.summary())
    print(f"\nTrue feature indices: {true_idx}")
    print(f"Recommended indices : {sorted(res.recommended.indices)}")

    fig1 = selector.plot_pareto()
    fig1.savefig("/mnt/user-data/outputs/pareto_frontier.png",
                 dpi=150, bbox_inches="tight")

    fig2 = selector.plot_shortlist()
    fig2.savefig("/mnt/user-data/outputs/shortlist_scores.png",
                 dpi=150, bbox_inches="tight")

    plt.close("all")
    print("\nPlots saved.")


if __name__ == "__main__":
    _demo()
