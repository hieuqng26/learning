Lasso instability is a well-documented phenomenon — it stems from the L1 penalty's non-differentiability at zero and its behavior under correlated predictors. Here's a structured breakdown of the causes and the evidence-backed remedies.

---

## Why Lasso is unstable

The Lasso objective (Tibshirani, 1996) is:

$$\hat{\beta} = \arg\min_{\beta} \left\{ \frac{1}{2n} \|y - X\beta\|_2^2 + \lambda \|\beta\|_1 \right\}$$

Three structural properties cause instability:

**1. The L1 penalty is non-smooth at zero.** Small perturbations in data can push a coefficient across the zero boundary, causing variables to suddenly appear or disappear. This is theoretically shown in Knight & Fu (2000) — the Lasso estimator has discontinuous derivatives near zero.

**2. Correlated predictors are arbitrarily selected.** When two predictors are highly correlated, Lasso arbitrarily zeros one out (Zou & Hastie, 2005). Which one it zeros depends on tiny data fluctuations — exactly the instability you're seeing.

**3. λ is data-dependent.** If your new data shifts the optimal λ even slightly, the sparsity pattern can change drastically.Now let me walk through each remedy with the mathematical detail, using properly rendered formulas:---

## Diagnosing which issue you have

Before applying remedies, identify the root cause:

**Coefficients flipping to zero on new data** → most likely a correlated-predictor problem. Check pairwise correlations and VIF scores. Elastic Net is your first fix.

**Overall performance degrading** → likely a distribution shift or overfitted λ. Check whether your new data has the same feature distributions (use KS tests or population stability index). Then apply the 1-SE rule and nested CV.

**Both** → apply the full pipeline: VIF screening → StandardScaler → ElasticNetCV inside a nested CV loop → post-hoc stability selection to audit which features are truly reliable.

---

## Recommended reading

- Tibshirani, R. (1996). *Regression shrinkage and selection via the lasso*. JRSS-B 58(1), 267–288.
- Zou, H. & Hastie, T. (2005). *Regularization and variable selection via the elastic net*. JRSS-B 67(2), 301–320.
- Zou, H. (2006). *The adaptive lasso and its oracle properties*. JASA 101(476), 1418–1429.
- Meinshausen, N. & Bühlmann, P. (2010). *Stability selection*. JRSS-B 72(4), 417–473.
- Hastie, T., Tibshirani, R. & Friedman, J. (2009). *The Elements of Statistical Learning*, 2nd ed., Ch. 3 & 7. (freely available at [https://hastie.su.domains/ElemStatLearn/](https://hastie.su.domains/ElemStatLearn/))
