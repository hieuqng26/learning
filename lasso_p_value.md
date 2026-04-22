## Why Lasso cannot produce p-values

Classical regression produces p-values through a well-established mechanism: fit the model once, then use the known sampling distribution of each coefficient to ask "how likely is this estimate if the true effect were zero?" This works because OLS coefficients follow a normal distribution with a closed-form variance — the math is exact and the answer is a single number per coefficient.

Lasso breaks this mechanism in three distinct ways.

---

### 1. The shrinkage bias makes the sampling distribution unknown

Lasso deliberately shrinks coefficients toward zero as part of its estimation. This bias is the point — it produces sparse models — but it means the coefficient estimates no longer follow the clean normal distribution that p-values require.

Leeb & Pötscher (2008) showed this formally: after any variable selection procedure, the sampling distribution of the surviving coefficients is not normal, not even approximately, and its shape depends on unknown population parameters in a way that cannot be estimated from the data. You cannot compute a standard error, and without a standard error there is no test statistic and no p-value. The distribution is simply not tractable.

---

### 2. The zero boundary creates a discontinuity

When a coefficient is shrunk exactly to zero, it has crossed a hard boundary. Lasso does not say "this coefficient is small" — it says "this coefficient is exactly zero and this variable is excluded." This discrete on/off behaviour is fundamentally incompatible with the continuous probability statements p-values require.

Knight & Fu (2000) showed that Lasso estimates have a non-standard asymptotic distribution precisely because of this discontinuity at zero. Near the boundary, the coefficient can be zero in one sample and non-zero in the next, with no smooth transition. A p-value assumes you can ask "how far is this estimate from zero on a continuous scale?" — but for Lasso, zero is a pile-up point, not just one value among many.

---

### 3. Selection and inference cannot use the same data

Even if you could somehow compute a p-value after Lasso selection, it would be statistically invalid to use it. Lasso chose which variables to include by looking at the data. If you then test those same variables on that same data, you are asking "are these variables significant?" about variables that were selected precisely because they looked significant. The answer is guaranteed to be yes, and the p-value is guaranteed to be too small.

This is the selective inference problem, formalised by Berk et al. (2013) and Taylor & Tibshirani (2015). They showed that naively applying classical tests after Lasso selection produces p-values that are massively anti-conservative — false positive rates far exceeding the nominal level. In simulations, a nominal 5% test can have an actual false positive rate above 50%.

---

### What researchers have done about it

The problem is well-known and several solutions exist, each with trade-offs.

**Post-selection inference (PoSI)** by Berk et al. (2013) adjusts the critical values to account for the fact that variables were selected from a larger pool. Valid, but conservative — the confidence intervals are wide.

**The selective inference framework** by Lee et al. (2016) conditions on the event that Lasso selected a particular set of variables and derives exact p-values under that conditioning. Theoretically correct, but the conditioning event is complex and the resulting tests have low power.

**Data splitting** uses half the data for Lasso selection and the other half for OLS inference on the selected variables. Simple and valid, but wasteful — you lose half your data for selection, and results vary depending on the random split.

**Stability selection itself** (Meinshausen & Bühlmann, 2010) can be seen as a partial answer to this problem: instead of asking for a p-value, it asks for a reproducibility probability. The false positive bound in Theorem 1 provides a frequentist guarantee without requiring a tractable sampling distribution.

The deeper lesson, articulated by Hastie, Tibshirani & Wainwright (2015), is that Lasso was designed for prediction and variable screening, not for hypothesis testing. Trying to extract p-values from it is asking a tool to do something it was never built for. The right sequence is: use Lasso or stability selection to identify candidate variables, then fit OLS on that confirmed small set and read the p-values from OLS — which is exactly what `SparseModelSelector` does by refitting with `LinearRegression` in Stage 2.

---

### References

- Knight, K. & Fu, W. (2000). Asymptotics for lasso-type estimators. *Annals of Statistics* 28(5), 1356–1378.
- Leeb, H. & Pötscher, B.M. (2008). Sparse estimators and the oracle property, or the return of Hodges' estimator. *Journal of Econometrics* 142(1), 201–211.
- Berk, R. et al. (2013). Valid post-selection inference. *Annals of Statistics* 41(2), 802–837.
- Taylor, J. & Tibshirani, R. (2015). Statistical learning and selective inference. *PNAS* 112(25), 7629–7634.
- Lee, J.D. et al. (2016). Exact post-selection inference, with application to the lasso. *Annals of Statistics* 44(3), 907–927.
- Meinshausen, N. & Bühlmann, P. (2010). Stability selection. *JRSS-B* 72(4), 417–473.
- Hastie, T., Tibshirani, R. & Wainwright, M. (2015). *Statistical Learning with Sparsity*. CRC Press. (freely available at https://hastie.su.domains/StatLearnSparsity/)
