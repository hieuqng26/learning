"""
Stability Selection for Lasso Regression
=========================================
Implementation based on:
    Meinshausen, N. & Bühlmann, P. (2010).
    "Stability selection." Journal of the Royal Statistical Society:
    Series B (Statistical Methodology), 72(4), 417–473.
    https://doi.org/10.1111/j.1467-9868.2010.00740.x

Key guarantee (Theorem 1 of the paper):
    E[V] <= q^2 / ((2 * pi_thr - 1) * p)
    where:
        V        = number of falsely selected variables
        q        = avg number of selected variables per subsample (across lambda)
        pi_thr   = selection probability threshold
        p        = total number of features
"""

from __future__ import annotations

import warnings
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from dataclasses import dataclass, field
from typing import Optional

from sklearn.base import BaseEstimator, clone
from sklearn.linear_model import LassoCV, Lasso
from sklearn.preprocessing import StandardScaler
from sklearn.utils import check_random_state
from sklearn.utils.validation import check_is_fitted


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class StabilitySelectionResult:
    """
    Attributes
    ----------
    selection_probabilities : ndarray of shape (p, n_lambdas)
        Pi_hat[j, k] = fraction of bootstrap runs in which feature j was
        selected at regularisation strength lambda_grid[k].
    stable_mask : ndarray of shape (p,)
        Boolean mask — True for features whose max selection probability
        across the lambda grid reaches pi_thr.
    stable_indices : ndarray of int
        Column indices of stable features.
    feature_names : list of str or None
        Names used in plots and summaries.
    lambda_grid : ndarray of shape (n_lambdas,)
        The regularisation grid used (sorted ascending).
    pi_thr : float
        The selection probability threshold applied.
    n_bootstraps : int
        Number of bootstrap subsamples used.
    max_sel_probs : ndarray of shape (p,)
        max_k Pi_hat[j, k] — the headline stability score per feature.
    upper_bound_fpr : float
        Theoretical upper bound on E[V] from Theorem 1, given the
        average number of selected variables q̄ observed in the run.
    """
    selection_probabilities: np.ndarray
    stable_mask: np.ndarray
    stable_indices: np.ndarray
    feature_names: list[str] | None
    lambda_grid: np.ndarray
    pi_thr: float
    n_bootstraps: int
    max_sel_probs: np.ndarray
    upper_bound_fpr: float

    # Set after construction
    _n_features: int = field(init=False, repr=False)

    def __post_init__(self):
        self._n_features = len(self.stable_mask)

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    def summary(self) -> str:
        lines = [
            "=" * 60,
            "Stability Selection Summary",
            "=" * 60,
            f"  Features total    : {self._n_features}",
            f"  Bootstrap runs    : {self.n_bootstraps}",
            f"  Lambda grid size  : {len(self.lambda_grid)}",
            f"  Threshold (π_thr) : {self.pi_thr:.2f}",
            f"  Stable features   : {self.stable_mask.sum()}",
            f"  E[V] upper bound  : {self.upper_bound_fpr:.4f}",
            "-" * 60,
            "  Stable feature scores (max Π̂ across λ grid):",
        ]
        for idx in self.stable_indices:
            name = (self.feature_names[idx]
                    if self.feature_names is not None else f"x{idx}")
            lines.append(f"    [{idx:>4d}]  {name:<30s}  Π̂ = {self.max_sel_probs[idx]:.3f}")
        if not self.stable_indices.size:
            lines.append("    (none — consider lowering pi_thr or n_bootstraps)")
        lines.append("=" * 60)
        return "\n".join(lines)

    def __repr__(self):
        return (
            f"StabilitySelectionResult("
            f"stable={self.stable_mask.sum()}/{self._n_features}, "
            f"pi_thr={self.pi_thr}, "
            f"E[V]<={self.upper_bound_fpr:.4f})"
        )


# ---------------------------------------------------------------------------
# Core estimator
# ---------------------------------------------------------------------------

class StabilitySelector(BaseEstimator):
    """
    Stability Selection wrapper for any sklearn Lasso-compatible estimator.

    The algorithm (Algorithm 1, Meinshausen & Bühlmann 2010):
        For b = 1 ... B:
            1. Draw I^b — a random subsample of size floor(n/2), without
               replacement (subsampling, not bootstrap-with-replacement,
               is what the paper proves guarantees for).
            2. Fit the estimator on X[I^b] for every λ in the grid.
            3. Record which features have a non-zero coefficient.
        Estimate Π̂_j = (1/B) Σ_b 1[β̂_j^(b)(λ) ≠ 0]  for each λ.
        Stable set = { j : max_λ Π̂_j >= pi_thr }.

    Parameters
    ----------
    estimator : sklearn estimator, optional
        Must expose `.coef_` after fitting.  Two modes are supported:

        Path estimators (Lasso, ElasticNet — default: Lasso(max_iter=10_000)):
            Must accept an `alpha` parameter.  The estimator is re-fit at
            every point on the lambda grid for each subsample, producing a
            full stability path curve per feature.

        Auto-CV estimators (LassoCV, ElasticNetCV):
            The estimator selects its own alpha via internal CV on each
            subsample.  It is fit once per subsample (not once per lambda).
            The stability paths plot will show flat lines — that is expected.
            max_sel_probs still gives the fraction of subsamples in which
            each feature was selected by the CV-chosen lambda.
    n_bootstraps : int, default=100
        Number of subsample runs B. The paper suggests B ≥ 50; 100 is safer.
    n_lambdas : int, default=50
        Number of points in the regularisation grid.
    lambda_min_ratio : float, default=1e-3
        Ratio lambda_min / lambda_max for the grid (log-spaced).
        Mirrors the convention used by glmnet / LassoCV.
    pi_thr : float, default=0.8
        Selection probability threshold (π_thr in the paper).
        Must be in (0.5, 1.0] — values ≤ 0.5 give a vacuous bound.
    random_state : int or RandomState, optional
        Controls subsampling reproducibility.
    verbose : bool, default=False

    Attributes (set after fit)
    --------------------------
    result_ : StabilitySelectionResult
    """

    def __init__(
        self,
        estimator=None,
        n_bootstraps: int = 100,
        n_lambdas: int = 50,
        lambda_min_ratio: float = 1e-3,
        pi_thr: float = 0.8,
        random_state=None,
        verbose: bool = False,
    ):
        if not (0.5 < pi_thr <= 1.0):
            raise ValueError(f"pi_thr must be in (0.5, 1.0]; got {pi_thr}.")
        self.estimator = estimator
        self.n_bootstraps = n_bootstraps
        self.n_lambdas = n_lambdas
        self.lambda_min_ratio = lambda_min_ratio
        self.pi_thr = pi_thr
        self.random_state = random_state
        self.verbose = verbose

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_lambda_grid(self, X: np.ndarray, y: np.ndarray) -> np.ndarray:
        """
        Derive the lambda grid from the data.

        Lambda_max is the smallest regularisation value that makes every
        coefficient exactly zero, given by:
            lambda_max = max_j |<X_j, y>| / n
        (standard result; see Hastie et al. 2015, §2.2).
        """
        n = X.shape[0]
        lambda_max = np.abs(X.T @ y).max() / n
        lambda_min = lambda_max * self.lambda_min_ratio
        return np.geomspace(lambda_max, lambda_min, num=self.n_lambdas)

    @staticmethod
    def _is_path_estimator(estimator) -> bool:
        """
        Return True if the estimator accepts a manual `alpha` parameter
        (e.g. Lasso, ElasticNet).  Return False for auto-selecting CV
        variants (e.g. LassoCV, ElasticNetCV) that pick alpha internally.
        """
        return "alpha" in estimator.get_params()

    @staticmethod
    def _fit_single(
        estimator,
        X_sub: np.ndarray,
        y_sub: np.ndarray,
        lambda_grid: np.ndarray,
        is_path_estimator: bool = True,
    ) -> np.ndarray:
        """
        Fit the estimator for one subsample.

        Two modes controlled by `is_path_estimator`:

        Path mode (Lasso, ElasticNet):
            Iterate over lambda_grid, set alpha=lam each time, record the
            binary selection mask at every grid point.
            Returns ndarray of shape (p, n_lambdas).

        Auto-CV mode (LassoCV, ElasticNetCV):
            Fit once — the estimator selects its own alpha via internal CV
            on the subsample itself.  The single selection mask is broadcast
            across all n_lambdas columns so the result shape is still
            (p, n_lambdas) and the rest of the pipeline is unchanged.
            The stability paths plot will show flat horizontal lines (all
            columns identical per feature) — that is expected behaviour.
            max_sel_probs is still meaningful: it equals the fraction of
            subsamples in which that feature was selected by the CV-chosen λ.

        Returns
        -------
        selected : ndarray of shape (p, n_lambdas), dtype bool
        """
        p = X_sub.shape[1]
        selected = np.zeros((p, len(lambda_grid)), dtype=bool)
        est = clone(estimator)

        if is_path_estimator:
            for k, lam in enumerate(lambda_grid):
                est.set_params(alpha=lam)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    est.fit(X_sub, y_sub)
                selected[:, k] = np.abs(est.coef_) > 0
        else:
            # Auto-CV: fit once, broadcast the single mask to all λ columns
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                est.fit(X_sub, y_sub)
            mask = np.abs(est.coef_) > 0
            selected[:, :] = mask[:, np.newaxis]

        return selected

    # ------------------------------------------------------------------
    # Sklearn API
    # ------------------------------------------------------------------

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: Optional[list[str]] = None,
    ) -> "StabilitySelector":
        """
        Run stability selection.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Predictors — should already be standardised.
        y : array-like of shape (n_samples,)
        feature_names : list of str, optional
            Used only for display / plots.

        Returns
        -------
        self
        """
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)
        n, p = X.shape
        rng = check_random_state(self.random_state)

        estimator = self.estimator or Lasso(max_iter=10_000)
        is_path = self._is_path_estimator(estimator)
        lambda_grid = self._build_lambda_grid(X, y)

        if not is_path and self.verbose:
            print(
                f"  Auto-CV estimator detected ({type(estimator).__name__}). "
                "Fitting once per subsample; lambda grid is used only for "
                "result shape compatibility."
            )

        # Accumulate selection indicators: shape (p, n_lambdas)
        sel_counts = np.zeros((p, self.n_lambdas), dtype=float)
        subsample_size = n // 2

        for b in range(self.n_bootstraps):
            if self.verbose and (b + 1) % 10 == 0:
                print(f"  Bootstrap {b + 1}/{self.n_bootstraps}")
            idx = rng.choice(n, size=subsample_size, replace=False)
            sel_counts += self._fit_single(
                estimator, X[idx], y[idx], lambda_grid,
                is_path_estimator=is_path,
            )

        # Selection probabilities Π̂_j(λ)
        sel_probs = sel_counts / self.n_bootstraps          # (p, n_lambdas)
        max_sel_probs = sel_probs.max(axis=1)               # (p,)
        stable_mask = max_sel_probs >= self.pi_thr
        stable_indices = np.where(stable_mask)[0]

        # Upper bound on E[V] — Theorem 1 of the paper:
        #   E[V] <= q^2 / ((2 * pi_thr - 1) * p)
        # where q = average number of selected features per subsample run,
        # averaged over all bootstrap runs and all lambda values.
        # We estimate q as the mean number of non-zero coefs per (b, lambda).
        avg_q = sel_counts.sum(axis=0).mean() / self.n_bootstraps
        denom = (2 * self.pi_thr - 1) * p
        upper_bound_fpr = (avg_q ** 2) / denom if denom > 0 else np.inf

        self.result_ = StabilitySelectionResult(
            selection_probabilities=sel_probs,
            stable_mask=stable_mask,
            stable_indices=stable_indices,
            feature_names=list(feature_names) if feature_names is not None else None,
            lambda_grid=lambda_grid,
            pi_thr=self.pi_thr,
            n_bootstraps=self.n_bootstraps,
            max_sel_probs=max_sel_probs,
            upper_bound_fpr=upper_bound_fpr,
        )
        self.is_fitted_ = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Return only the stable columns of X."""
        check_is_fitted(self, "result_")
        X = np.asarray(X, dtype=float)
        return X[:, self.result_.stable_indices]

    def fit_transform(self, X, y, feature_names=None):
        return self.fit(X, y, feature_names).transform(X)

    # ------------------------------------------------------------------
    # Plotting
    # ------------------------------------------------------------------

    def plot_stability_paths(
        self,
        top_n: int = 20,
        figsize: tuple = (10, 5),
        title: str = "Stability paths",
    ) -> plt.Figure:
        """
        Plot selection probability Π̂_j vs log(λ) for the top_n features.

        Stable features (Π̂ >= pi_thr) are drawn in colour; the rest in gray.
        A dashed horizontal line marks pi_thr.
        """
        check_is_fitted(self, "result_")
        res = self.result_

        # Rank features by max selection probability, keep top_n
        order = np.argsort(res.max_sel_probs)[::-1][:top_n]
        log_lam = np.log10(res.lambda_grid)

        fig, ax = plt.subplots(figsize=figsize)
        cmap = plt.cm.tab10
        color_idx = 0

        for rank, j in enumerate(order):
            is_stable = res.stable_mask[j]
            name = (res.feature_names[j]
                    if res.feature_names is not None else f"x{j}")
            if is_stable:
                ax.plot(
                    log_lam, res.selection_probabilities[j],
                    color=cmap(color_idx % 10), lw=1.8,
                    label=f"{name}  (Π̂={res.max_sel_probs[j]:.2f})",
                    zorder=3,
                )
                color_idx += 1
            else:
                ax.plot(
                    log_lam, res.selection_probabilities[j],
                    color="gray", lw=0.7, alpha=0.4, zorder=1,
                )

        # Threshold line
        ax.axhline(res.pi_thr, color="crimson", lw=1.2, ls="--",
                   label=f"π_thr = {res.pi_thr}", zorder=4)

        ax.set_xlabel("log₁₀(λ)", fontsize=11)
        ax.set_ylabel("Selection probability  Π̂", fontsize=11)
        ax.set_title(title, fontsize=12)
        ax.set_ylim(-0.02, 1.05)
        ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
        if color_idx > 0:
            ax.legend(fontsize=9, loc="upper left", framealpha=0.85,
                      title="Stable features")
        fig.tight_layout()
        return fig

    def plot_selection_probabilities(
        self,
        figsize: tuple = (9, 4),
        title: str = "Max selection probability per feature",
    ) -> plt.Figure:
        """
        Horizontal bar chart of max Π̂_j for every feature,
        sorted descending. Bars crossing pi_thr are highlighted.
        """
        check_is_fitted(self, "result_")
        res = self.result_
        p = len(res.max_sel_probs)
        order = np.argsort(res.max_sel_probs)
        probs = res.max_sel_probs[order]

        names = (
            [res.feature_names[i] for i in order]
            if res.feature_names is not None
            else [f"x{i}" for i in order]
        )
        colors = [
            "#2563EB" if v >= res.pi_thr else "#CBD5E1"
            for v in probs
        ]

        fig, ax = plt.subplots(figsize=figsize)
        ax.barh(range(p), probs, color=colors, height=0.7)
        ax.axvline(res.pi_thr, color="crimson", lw=1.2, ls="--",
                   label=f"π_thr = {res.pi_thr}")
        ax.set_yticks(range(p))
        ax.set_yticklabels(names, fontsize=8)
        ax.set_xlabel("Max selection probability  Π̂", fontsize=10)
        ax.set_xlim(0, 1.05)
        ax.xaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
        ax.set_title(title, fontsize=11)
        ax.legend(fontsize=9)
        fig.tight_layout()
        return fig


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------

def stability_selection(
    X,
    y,
    feature_names=None,
    n_bootstraps: int = 100,
    n_lambdas: int = 50,
    pi_thr: float = 0.8,
    lambda_min_ratio: float = 1e-3,
    estimator=None,
    random_state=None,
    verbose: bool = False,
) -> StabilitySelectionResult:
    """
    Functional entry-point. Standardises X internally, then runs
    StabilitySelector.fit().

    Parameters
    ----------
    X : array-like of shape (n, p)
    y : array-like of shape (n,)
    feature_names : list of str, optional
    n_bootstraps : int, default=100
    n_lambdas : int, default=50
    pi_thr : float, default=0.8
    lambda_min_ratio : float, default=1e-3
    estimator : sklearn estimator, optional
        Defaults to Lasso(max_iter=10_000).
    random_state : int or RandomState, optional
    verbose : bool, default=False

    Returns
    -------
    StabilitySelectionResult
    """
    X = np.asarray(X, dtype=float)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    selector = StabilitySelector(
        estimator=estimator,
        n_bootstraps=n_bootstraps,
        n_lambdas=n_lambdas,
        lambda_min_ratio=lambda_min_ratio,
        pi_thr=pi_thr,
        random_state=random_state,
        verbose=verbose,
    )
    selector.fit(X_scaled, y, feature_names=feature_names)
    return selector.result_


# ---------------------------------------------------------------------------
# Demo / smoke test
# ---------------------------------------------------------------------------

def _demo():
    """
    Synthetic example: 200 samples, 50 features, 8 truly non-zero.

    Design choices following the simulation setup in Meinshausen & Bühlmann (2010):
      - Moderate SNR: true coefficients in [0.5, 1.0], noise std = 1.0
      - lambda_min_ratio = 0.05 keeps us away from the fully-dense regime
        where null features also get selected consistently
    """
    rng = np.random.RandomState(42)
    n, p, n_true = 200, 50, 8

    X = rng.randn(n, p)
    true_coef = np.zeros(p)
    true_idx = rng.choice(p, size=n_true, replace=False)
    true_coef[true_idx] = rng.uniform(0.5, 1.0, size=n_true) * rng.choice([-1, 1], size=n_true)
    y = X @ true_coef + rng.randn(n) * 1.0

    feature_names = [f"X{i:02d}" for i in range(p)]

    selector = StabilitySelector(
        n_bootstraps=100, n_lambdas=50, pi_thr=0.8,
        lambda_min_ratio=0.05,          # avoids the fully-dense overfitted regime
        random_state=0, verbose=True
    )
    scaler = StandardScaler()
    X_s = scaler.fit_transform(X)
    selector.fit(X_s, y, feature_names=feature_names)

    res = selector.result_
    print(res.summary())

    true_set = set(true_idx)
    found_set = set(res.stable_indices)
    tp = len(true_set & found_set)
    fp = len(found_set - true_set)
    fn = len(true_set - found_set)
    print(f"True positives  : {tp}/{n_true}")
    print(f"False positives : {fp}")
    print(f"False negatives : {fn}")
    print(f"True feature indices    : {sorted(true_idx)}")
    print(f"Selected feature indices: {sorted(res.stable_indices)}")

    fig1 = selector.plot_stability_paths(top_n=15)
    fig1.savefig("/mnt/user-data/outputs/stability_paths.png", dpi=150, bbox_inches="tight")

    fig2 = selector.plot_selection_probabilities()
    fig2.savefig("/mnt/user-data/outputs/selection_probabilities.png", dpi=150, bbox_inches="tight")

    plt.close("all")
    print("\nPlots saved.")


    print("\n--- LassoCV estimator (auto-CV mode) ---")
    from sklearn.linear_model import LassoCV as _LassoCV
    selector_cv = StabilitySelector(
        estimator=_LassoCV(cv=5, max_iter=10_000),
        n_bootstraps=100, n_lambdas=50, pi_thr=0.8,
        lambda_min_ratio=0.05, random_state=0, verbose=True,
    )
    selector_cv.fit(X_s, y, feature_names=feature_names)
    res_cv = selector_cv.result_
    print(res_cv.summary())
    found_cv = set(res_cv.stable_indices)
    print(f"True positives  : {len(true_set & found_cv)}/{n_true}")
    print(f"False positives : {len(found_cv - true_set)}")


if __name__ == "__main__":
    _demo()
