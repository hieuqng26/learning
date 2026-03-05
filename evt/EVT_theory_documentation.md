# Extreme Value Theory: Mathematical Foundations and Theory

**Author**: Claude
**Date**: March 2, 2026
**Purpose**: Theoretical reference for EVT applications in financial risk modeling

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Mathematical Foundations](#2-mathematical-foundations)
3. [Block Maxima Approach (GEV)](#3-block-maxima-approach-gev)
4. [Peaks Over Threshold Approach (GPD)](#4-peaks-over-threshold-approach-gpd)
5. [Parameter Estimation](#5-parameter-estimation)
6. [Statistical Properties](#6-statistical-properties)
7. [Applications in Finance](#7-applications-in-finance)
8. [Model Validation](#8-model-validation)
9. [Limitations and Assumptions](#9-limitations-and-assumptions)
10. [References](#10-references)

---

## 1. Introduction

### 1.1 What is Extreme Value Theory?

**Extreme Value Theory (EVT)** is a branch of statistics that deals with the extreme deviations from the median of probability distributions. It provides a rigorous statistical framework for modeling rare events in the tail of distributions.

**Key Questions EVT Answers:**
- What is the maximum/minimum value we can expect in the next N observations?
- How often will we see values exceeding a high threshold?
- What is the probability of an event more extreme than anything we've observed?

### 1.2 Why EVT for Financial Risk?

Traditional statistics focuses on central tendency (mean, median). But in finance, we care about **tails**:
- What happens in a crisis? (99th percentile)
- What's the worst-case scenario? (Value at Risk)
- How often do "black swan" events occur?

**Problems with Classical Methods:**
- Normal distribution underestimates tail risk
- Empirical percentiles unreliable for extremes (few observations)
- Cannot extrapolate beyond observed data

**EVT Advantages:**
- Mathematically rigorous tail modeling
- Based on limiting theorems (like CLT for extremes)
- Can extrapolate to unobserved quantiles
- Provides uncertainty estimates (confidence intervals)

### 1.3 Historical Development

| Year | Development | Contributors |
|------|-------------|--------------|
| 1928 | Fisher-Tippett theorem | R.A. Fisher, L.H.C. Tippett |
| 1943 | Three-type theorem | B. Gnedenko |
| 1975 | Pickands-Balkema-de Haan theorem | J. Pickands, A. Balkema, L. de Haan |
| 1990s | Financial applications | P. Embrechts, C. Klüppelberg |
| 2000s | Regulatory adoption (Basel II) | BCBS |

---

## 2. Mathematical Foundations

### 2.1 Order Statistics

Let $X_1, X_2, \ldots, X_n$ be independent, identically distributed (i.i.d.) random variables with distribution function $F$.

**Order statistics** are the sample values arranged in ascending order:
$$X_{(1)} \leq X_{(2)} \leq \cdots \leq X_{(n)}$$

where:
- $X_{(1)} = \min(X_1, \ldots, X_n)$ (minimum)
- $X_{(n)} = \max(X_1, \ldots, X_n)$ (maximum)

**Distribution of Maximum:**
$$P(X_{(n)} \leq x) = P(X_1 \leq x, X_2 \leq x, \ldots, X_n \leq x) = [F(x)]^n$$

### 2.2 The Fundamental Question

What is the limiting distribution of the maximum as $n \to \infty$?

**Problem:** As $n \to \infty$, $[F(x)]^n \to 0$ or $1$ (degenerate distribution)

**Solution:** Apply **normalization** (like standardizing):
$$P\left(\frac{X_{(n)} - b_n}{a_n} \leq x\right) \to G(x)$$

for suitable constants $a_n > 0$ and $b_n \in \mathbb{R}$.

**Question:** What are the possible limiting distributions $G(x)$?

---

## 3. Block Maxima Approach (GEV)

### 3.1 Fisher-Tippett-Gnedenko Theorem

**Theorem (1928, 1943):**
If there exist sequences $\{a_n > 0\}$ and $\{b_n\}$ such that
$$P\left(\frac{X_{(n)} - b_n}{a_n} \leq x\right) \to G(x)$$
as $n \to \infty$, where $G$ is a non-degenerate distribution, then $G$ belongs to one of three types:

#### Type I: Gumbel (Light Tail)
$$G(x) = \exp\left(-e^{-x}\right), \quad x \in \mathbb{R}$$

**Domain of Attraction:**
- Distributions with exponential-like tails
- Examples: Normal, Exponential, Gamma, Lognormal

**Interpretation:** Extremes are bounded by exponential growth

#### Type II: Fréchet (Heavy Tail)
$$G(x) = \begin{cases}
0 & x \leq 0 \\
\exp\left(-x^{-\alpha}\right) & x > 0
\end{cases}$$
where $\alpha > 0$ is the **tail index**.

**Domain of Attraction:**
- Distributions with polynomial tails: $P(X > x) \sim x^{-\alpha}$
- Examples: Pareto, Cauchy, Student-t, Log-gamma

**Interpretation:** Heavy tails, extreme values can be arbitrarily large

#### Type III: Weibull (Short Tail)
$$G(x) = \begin{cases}
\exp\left(-(-x)^{\alpha}\right) & x < 0 \\
1 & x \geq 0
\end{cases}$$
where $\alpha > 0$.

**Domain of Attraction:**
- Distributions with finite upper endpoint
- Examples: Uniform, Beta

**Interpretation:** Maximum is bounded from above

### 3.2 Generalized Extreme Value (GEV) Distribution

The three types can be unified into a single family:

**GEV Distribution Function:**
$$G(x; \mu, \sigma, \xi) = \exp\left\{-\left[1 + \xi\left(\frac{x - \mu}{\sigma}\right)\right]_+^{-1/\xi}\right\}$$

where:
- $\mu \in \mathbb{R}$: **location parameter** (mode/center)
- $\sigma > 0$: **scale parameter** (spread)
- $\xi \in \mathbb{R}$: **shape parameter** (tail behavior)
- $[z]_+ = \max(z, 0)$
- Support: $1 + \xi(x - \mu)/\sigma > 0$

**Special Cases:**
- $\xi = 0$ (limit as $\xi \to 0$): Gumbel
  $$G(x) = \exp\left\{-\exp\left(-\frac{x - \mu}{\sigma}\right)\right\}$$

- $\xi > 0$: Fréchet (heavy tail)
  $$G(x) = \exp\left\{-\left[1 + \xi\left(\frac{x - \mu}{\sigma}\right)\right]^{-1/\xi}\right\}, \quad x > \mu - \sigma/\xi$$

- $\xi < 0$: Weibull (bounded tail)
  $$G(x) = \exp\left\{-\left[1 + \xi\left(\frac{x - \mu}{\sigma}\right)\right]^{-1/\xi}\right\}, \quad x < \mu - \sigma/\xi$$

### 3.3 GEV Properties

**Probability Density Function:**
$$g(x; \mu, \sigma, \xi) = \frac{1}{\sigma}\left[1 + \xi\left(\frac{x - \mu}{\sigma}\right)\right]_+^{-1/\xi - 1} \exp\left\{-\left[1 + \xi\left(\frac{x - \mu}{\sigma}\right)\right]_+^{-1/\xi}\right\}$$

**Quantile Function (Inverse CDF):**
$$x_p = \begin{cases}
\mu - \frac{\sigma}{\xi}\left[1 - (-\log p)^{-\xi}\right] & \xi \neq 0 \\
\mu - \sigma \log(-\log p) & \xi = 0
\end{cases}$$

where $p = G(x_p)$ is the probability level.

**Return Level:**
The level $x_m$ expected to be exceeded on average once every $m$ blocks is:
$$x_m = \begin{cases}
\mu - \frac{\sigma}{\xi}\left[1 - m^{\xi}\right] & \xi \neq 0 \\
\mu - \sigma \log(m) & \xi = 0
\end{cases}$$

**Moments:**
- **Mean** (if $\xi < 1$):
  $$E[X] = \mu + \frac{\sigma}{\xi}\left[\Gamma(1 - \xi) - 1\right]$$

- **Variance** (if $\xi < 1/2$):
  $$\text{Var}(X) = \frac{\sigma^2}{\xi^2}\left[\Gamma(1 - 2\xi) - \Gamma^2(1 - \xi)\right]$$

where $\Gamma(\cdot)$ is the gamma function.

### 3.4 Block Maxima Method

**Procedure:**
1. Divide data into $k$ non-overlapping blocks of size $n$
2. Extract maximum from each block: $M_1, M_2, \ldots, M_k$
3. Fit GEV distribution to block maxima
4. Use fitted distribution to estimate extreme quantiles

**Advantages:**
- Direct application of Fisher-Tippett-Gnedenko theorem
- Simple and intuitive

**Disadvantages:**
- Wastes data (only uses one value per block)
- Choice of block size $n$ is arbitrary
- Requires long time series

---

## 4. Peaks Over Threshold Approach (GPD)

### 4.1 Pickands-Balkema-de Haan Theorem

**Motivation:** Block maxima approach is inefficient. Can we use **all** extreme values?

**Theorem (1975):**
For a large class of underlying distributions $F$, the conditional distribution of exceedances over a high threshold $u$ converges to a **Generalized Pareto Distribution (GPD)**.

Mathematically, for $u$ large enough:
$$P(X - u \leq y \mid X > u) \approx H(y; \sigma, \xi)$$

where $H$ is the GPD distribution function.

### 4.2 Generalized Pareto Distribution (GPD)

**Distribution Function:**
$$H(y; \sigma, \xi) = \begin{cases}
1 - \left(1 + \xi \frac{y}{\sigma}\right)_+^{-1/\xi} & \xi \neq 0 \\
1 - \exp\left(-\frac{y}{\sigma}\right) & \xi = 0
\end{cases}$$

where:
- $y \geq 0$: exceedance (amount above threshold)
- $\sigma > 0$: **scale parameter**
- $\xi \in \mathbb{R}$: **shape parameter** (same interpretation as GEV)
- Support: $y \geq 0$ if $\xi \geq 0$; $0 \leq y \leq -\sigma/\xi$ if $\xi < 0$

**Special Cases:**
- $\xi = 0$: **Exponential distribution**
  $$H(y) = 1 - \exp(-y/\sigma)$$

- $\xi > 0$: **Pareto distribution** (heavy tail)
  $$H(y) = 1 - \left(1 + \xi y/\sigma\right)^{-1/\xi}$$

- $\xi < 0$: **Beta distribution** (bounded)
  $$H(y) = 1 - \left(1 + \xi y/\sigma\right)^{-1/\xi}, \quad 0 \leq y \leq -\sigma/\xi$$

### 4.3 GPD Properties

**Probability Density Function:**
$$h(y; \sigma, \xi) = \frac{1}{\sigma}\left(1 + \xi \frac{y}{\sigma}\right)_+^{-1/\xi - 1}$$

**Quantile Function:**
$$y_p = \begin{cases}
\frac{\sigma}{\xi}\left[(1-p)^{-\xi} - 1\right] & \xi \neq 0 \\
-\sigma \log(1-p) & \xi = 0
\end{cases}$$

**Mean** (if $\xi < 1$):
$$E[Y] = \frac{\sigma}{1 - \xi}$$

**Variance** (if $\xi < 1/2$):
$$\text{Var}(Y) = \frac{\sigma^2}{(1 - \xi)^2(1 - 2\xi)}$$

**Tail Behavior:**
$$1 - H(y) = \left(1 + \xi \frac{y}{\sigma}\right)^{-1/\xi}$$

For large $y$:
- $\xi > 0$: Polynomial decay $\sim y^{-1/\xi}$ (heavy tail)
- $\xi = 0$: Exponential decay $\sim e^{-y/\sigma}$ (medium tail)
- $\xi < 0$: Bounded at $y = -\sigma/\xi$ (short tail)

### 4.4 Connection to Original Distribution

**Full Distribution Reconstruction:**
Let $F_u(y) = P(X \leq y \mid X > u)$ be the conditional distribution of exceedances.

For $x > u$:
$$F(x) = P(X \leq x) = P(X \leq u) + P(u < X \leq x)$$
$$= F(u) + P(X > u) \cdot P(X \leq x \mid X > u)$$
$$= F(u) + [1 - F(u)] \cdot F_u(x - u)$$

**Estimating Full Distribution:**
1. Estimate $P(X > u) = N_u / n$ where $N_u$ = number of exceedances
2. For $x > u$:
   $$\hat{F}(x) = 1 - \frac{N_u}{n}\left(1 + \xi \frac{x - u}{\sigma}\right)^{-1/\xi}$$

**High Quantile Estimation:**
The $p$-quantile $x_p$ where $F(x_p) = p$ can be estimated as:
$$\hat{x}_p = u + \frac{\sigma}{\xi}\left[\left(\frac{n}{N_u}(1-p)\right)^{-\xi} - 1\right]$$

This allows extrapolation beyond observed data!

### 4.5 Threshold Selection

**The Trade-off:**
- **Low threshold**: More data, but bias (GPD approximation poor)
- **High threshold**: Better GPD fit, but high variance (fewer observations)

**Methods:**

#### a) Mean Excess Plot
Plot mean exceedance vs threshold:
$$e(u) = E[X - u \mid X > u]$$

**For GPD:**
$$e(u) = \frac{\sigma + \xi u}{1 - \xi}$$

**Interpretation:**
- Should be approximately linear for $u$ above appropriate threshold
- Slope = $\xi / (1 - \xi)$

#### b) Parameter Stability Plot
- Fit GPD for range of thresholds
- Plot estimated $\hat{\xi}$ and $\hat{\sigma}$ vs threshold
- Choose threshold where parameters stabilize

#### c) Goodness-of-Fit Tests
- QQ plot
- Probability plot
- Anderson-Darling, Kolmogorov-Smirnov tests

**Rule of Thumb:**
- Choose $u$ such that $N_u \geq 50$ (at least 50 exceedances)
- Threshold should capture top 5-10% of data
- Typically 90th-95th percentile

---

## 5. Parameter Estimation

### 5.1 Maximum Likelihood Estimation (MLE)

**For GPD:**

Given exceedances $y_1, \ldots, y_k$ above threshold $u$, the likelihood is:
$$L(\sigma, \xi) = \prod_{i=1}^k h(y_i; \sigma, \xi) = \prod_{i=1}^k \frac{1}{\sigma}\left(1 + \xi \frac{y_i}{\sigma}\right)^{-1/\xi - 1}$$

**Log-likelihood:**
$$\ell(\sigma, \xi) = -k \log \sigma - \left(1 + \frac{1}{\xi}\right) \sum_{i=1}^k \log\left(1 + \xi \frac{y_i}{\sigma}\right)$$

subject to $1 + \xi y_i / \sigma > 0$ for all $i$.

**Special case** ($\xi = 0$, exponential):
$$\ell(\sigma) = -k \log \sigma - \frac{1}{\sigma}\sum_{i=1}^k y_i$$

**MLE Solution:** Numerical optimization (e.g., Newton-Raphson, BFGS)

**Asymptotic Properties:**
Under regularity conditions, MLEs are:
- **Consistent**: $\hat{\theta}_n \to \theta$ as $n \to \infty$
- **Asymptotically normal**:
  $$\sqrt{n}(\hat{\theta}_n - \theta) \xrightarrow{d} N(0, I^{-1}(\theta))$$
  where $I(\theta)$ is the Fisher information matrix
- **Asymptotically efficient**: Lowest variance among consistent estimators

**Standard Errors:**
$$\text{Var}(\hat{\theta}) \approx I^{-1}(\hat{\theta})/n$$

Can be used to construct confidence intervals.

### 5.2 Probability-Weighted Moments (PWM)

**Alternative to MLE**, especially when $\xi < -0.5$ (MLE can be unstable).

**Method:**
Based on matching theoretical and empirical probability-weighted moments:
$$M_{s,r} = E[X^s F^r(X)]$$

**For GPD**, PWM estimators are:
$$\hat{\xi} = \frac{M_{1,0} - 2M_{1,1}}{M_{1,1} - M_{1,0}} - 2$$
$$\hat{\sigma} = \frac{2M_{1,0}M_{1,1}}{M_{1,1} - M_{1,0}}$$

**Advantages:**
- Explicit formula (no optimization needed)
- More robust for $\xi < -0.5$

**Disadvantages:**
- Less efficient than MLE for $\xi > -0.5$
- No automatic standard errors

### 5.3 Bayesian Estimation

**Prior distributions** on $(\sigma, \xi)$:
- Flat prior, Gamma prior on $\sigma$
- Uniform or Gaussian prior on $\xi$

**Posterior:**
$$p(\sigma, \xi \mid \mathbf{y}) \propto L(\sigma, \xi \mid \mathbf{y}) \cdot p(\sigma, \xi)$$

**Inference:**
- MCMC (Metropolis-Hastings, Gibbs sampling)
- Full posterior distribution for parameters
- Posterior predictive distribution for quantiles

**Advantages:**
- Natural uncertainty quantification
- Can incorporate expert judgment via priors
- Handles small samples better

---

## 6. Statistical Properties

### 6.1 Tail Index and Heavy Tails

**Tail Index** $\alpha$: Controls decay rate of tail probabilities.

For $\xi > 0$:
$$P(X > x) \sim x^{-\alpha}, \quad \alpha = 1/\xi$$

**Interpretation:**
- $\alpha = 2$ ($\xi = 0.5$): Variance infinite (e.g., Cauchy)
- $\alpha = 3$ ($\xi = 0.33$): Mean exists, variance infinite
- $\alpha > 4$ ($\xi < 0.25$): Both mean and variance finite

**Financial Implications:**
- Stock returns: $\xi \approx 0.2$ to $0.4$ (heavy tails)
- Exchange rates: $\xi \approx 0.1$ to $0.3$
- Credit losses: $\xi$ can exceed 0.5 (very heavy)

### 6.2 Return Levels and Return Periods

**Return Period** $T$: Expected waiting time until event occurs.

**Return Level** $x_T$: Level exceeded on average once per $T$ periods.

**For GPD:**
If exceedance probability is $\zeta_u = P(X > u) = N_u / n$, then:
$$x_T = u + \frac{\sigma}{\xi}\left[(T \zeta_u)^{\xi} - 1\right]$$

**Example:**
- Annual data, $T = 100$ years
- $u = 0.15$ (90th percentile), $\zeta_u = 0.10$
- $\sigma = 0.05$, $\xi = 0.3$
- $x_{100} = 0.15 + \frac{0.05}{0.3}\left[(100 \times 0.10)^{0.3} - 1\right] = 0.25$

**Interpretation:** 1-in-100 year event has value 0.25

### 6.3 Conditional Tail Expectation (CTE)

**Definition:** Expected value given exceedance of quantile $x_p$:
$$\text{CTE}_p = E[X \mid X > x_p]$$

**For GPD** (if $\xi < 1$):
$$\text{CTE}_p = x_p + \frac{\sigma + \xi x_p}{1 - \xi}$$

**Relation to VaR:**
- VaR (Value at Risk) = quantile $x_p$
- CTE = expected loss beyond VaR
- CTE always greater than VaR
- CTE is a **coherent risk measure** (VaR is not)

---

## 7. Applications in Finance

### 7.1 Value at Risk (VaR)

**Definition:** $\text{VaR}_\alpha$ is the quantile such that losses exceed VaR with probability $\alpha$.

**EVT Approach:**
1. Model loss distribution tail with GPD
2. Estimate high quantile (e.g., 99%, 99.9%)
3. VaR = threshold + GPD quantile

**Advantages over parametric VaR:**
- Does not assume normality
- Captures heavy tails accurately
- Extrapolates beyond observed data

### 7.2 Expected Shortfall (ES)

**Definition:** Expected loss given VaR is exceeded:
$$\text{ES}_\alpha = E[X \mid X > \text{VaR}_\alpha]$$

**EVT Estimation:**
$$\text{ES}_\alpha = \text{VaR}_\alpha + \frac{\sigma + \xi(\text{VaR}_\alpha - u)}{1 - \xi}$$

**Why ES > VaR:**
- ES captures severity of tail events
- ES is coherent (sub-additive)
- Required under Basel III (replaced VaR)

### 7.3 Stress Testing

**Scenario Analysis:**
- Use EVT to estimate extreme quantiles (99.9%, 99.99%)
- Corresponds to 1-in-1000, 1-in-10000 year events
- Even if never observed historically

**Example: Opex Stress Testing**
1. Model delta Opex/Revenue using GPD
2. Estimate 96th, 99th percentile stress impacts
3. Apply to portfolio for capital planning
4. Validate against historical crises (2008, 2009)

### 7.4 Insurance and Reinsurance

**Loss Modeling:**
- Claim severity distributions
- Reinsurance pricing (excess-of-loss)
- Catastrophe modeling (earthquakes, hurricanes)

**Example:**
- Threshold = $10M (retention)
- GPD models losses > $10M
- Price reinsurance layer $10M - $100M

---

## 8. Model Validation

### 8.1 Diagnostic Plots

#### a) Probability Plot (PP Plot)
Plot empirical vs theoretical probabilities:
$$(H(y_{(i)}), i/(n+1))$$

Should follow 45° line if model fits well.

#### b) Quantile-Quantile Plot (QQ Plot)
Plot empirical vs theoretical quantiles:
$$(H^{-1}(i/(n+1)), y_{(i)})$$

Should follow 45° line if model fits well.

#### c) Density Plot
Overlay fitted GPD density on histogram of exceedances.

#### d) Return Level Plot
Plot return levels vs return periods on log scale.

### 8.2 Goodness-of-Fit Tests

#### a) Anderson-Darling Test
Measures distance between empirical and theoretical CDFs:
$$A^2 = n \int_{-\infty}^{\infty} \frac{[F_n(x) - F(x)]^2}{F(x)[1 - F(x)]} dF(x)$$

Weighted to emphasize tails.

#### b) Kolmogorov-Smirnov Test
$$D = \sup_x |F_n(x) - F(x)|$$

Less sensitive to tails than Anderson-Darling.

#### c) Cramér-von Mises Test
$$W^2 = n \int_{-\infty}^{\infty} [F_n(x) - F(x)]^2 dF(x)$$

### 8.3 Backtesting

**Out-of-Sample Validation:**
1. Split data: training (e.g., 2000-2007) and test (e.g., 2008)
2. Fit EVT model on training data
3. Predict extreme quantiles
4. Compare to actual test data outcomes

**Metrics:**
- **Forecast Accuracy:** MAE, MSE of quantile estimates
- **Coverage:** % of observations within confidence intervals
- **Exceedance Rate:** Compare predicted vs actual exceedance frequency

**Example:**
- Forecast 96th percentile using 2000-2007 data
- Compare to actual 2008 crisis 96th percentile
- Good model: Low error, 95% CI covers actual

---

## 9. Limitations and Assumptions

### 9.1 Core Assumptions

1. **Independence**: Observations are i.i.d.
   - **Violation:** Financial returns are serially correlated (volatility clustering)
   - **Solution:** Pre-filter with GARCH, use declustering

2. **Stationarity**: Distribution doesn't change over time
   - **Violation:** Regime changes, structural breaks
   - **Solution:** Use rolling windows, regime-switching models

3. **Threshold Stability**: GPD approximation holds above threshold
   - **Violation:** Threshold too low or too high
   - **Solution:** Diagnostic plots, parameter stability checks

### 9.2 Practical Limitations

#### a) Data Requirements
- Need sufficient extremes (≥50-100 exceedances)
- Long time series for reliable estimation
- Short series → high uncertainty

#### b) Threshold Selection
- No universal rule for optimal threshold
- Bias-variance trade-off
- Different thresholds → different estimates

#### c) Extrapolation Risk
- EVT allows extrapolation beyond data
- But uncertainty increases with extrapolation
- 99.9th percentile less reliable than 99th

#### d) Tail Dependence
- Standard EVT assumes univariate distributions
- Multivariate extremes more complex
- Copula-based EVT for dependencies

### 9.3 Common Pitfalls

1. **Over-extrapolation**: Estimating 99.99th percentile with 100 observations
2. **Ignoring uncertainty**: Reporting point estimates without confidence intervals
3. **Wrong direction**: Using GPD for minima instead of maxima (or vice versa)
4. **Threshold mining**: Choosing threshold to get "desired" result
5. **Assuming stationarity**: Applying to non-stationary data

### 9.4 When NOT to Use EVT

- **Small samples** (< 50 observations): Use empirical percentiles or Bayesian methods
- **Light-tailed distributions**: Normal approximation may suffice
- **Multimodal distributions**: EVT assumes unimodal tail behavior
- **Discrete data**: EVT designed for continuous distributions
- **Highly non-stationary data**: Regime switching models more appropriate

---

## 10. References

### 10.1 Foundational Papers

1. **Fisher, R.A. and Tippett, L.H.C. (1928).**
   "Limiting forms of the frequency distribution of the largest or smallest member of a sample."
   *Proceedings of the Cambridge Philosophical Society*, 24, 180-190.

2. **Gnedenko, B. (1943).**
   "Sur la distribution limite du terme maximum d'une série aléatoire."
   *Annals of Mathematics*, 44, 423-453.

3. **Pickands, J. (1975).**
   "Statistical inference using extreme order statistics."
   *Annals of Statistics*, 3, 119-131.

4. **Balkema, A.A. and de Haan, L. (1974).**
   "Residual life time at great age."
   *Annals of Probability*, 2, 792-804.

### 10.2 Textbooks

1. **Embrechts, P., Klüppelberg, C., and Mikosch, T. (1997).**
   *Modelling Extremal Events for Insurance and Finance.*
   Springer. (The definitive reference)

2. **Coles, S. (2001).**
   *An Introduction to Statistical Modeling of Extreme Values.*
   Springer. (Accessible introduction)

3. **de Haan, L. and Ferreira, A. (2006).**
   *Extreme Value Theory: An Introduction.*
   Springer. (Mathematical treatment)

4. **McNeil, A.J., Frey, R., and Embrechts, P. (2015).**
   *Quantitative Risk Management: Concepts, Techniques and Tools.*
   Princeton University Press. (Financial applications)

### 10.3 Software and Packages

**R:**
- `evd`: Functions for extreme value distributions
- `extRemes`: Tools for modeling extremes
- `ismev`: Introduction to statistical modeling of extreme values
- `POT`: Peaks over threshold modeling

**Python:**
- `scipy.stats`: Contains `genpareto` and `genextreme`
- `pyextremes`: Comprehensive EVT library
- Your implementation: `evt_model.py`, `evt_backtest.py`

**MATLAB:**
- Statistics and Machine Learning Toolbox: `gevfit`, `gpfit`

### 10.4 Regulatory and Industry Standards

1. **Basel Committee on Banking Supervision (2019).**
   *Minimum capital requirements for market risk.*
   (Uses EVT for tail risk estimation)

2. **Solvency II Directive (EU).**
   Insurance capital requirements using 99.5th percentile VaR

3. **International Actuarial Association (2004).**
   *A Global Framework for Insurer Solvency Assessment.*

---

## Appendix A: Mathematical Notation

| Symbol | Meaning |
|--------|---------|
| $X$ | Random variable |
| $F(x)$ | Cumulative distribution function |
| $f(x)$ | Probability density function |
| $X_{(n)}$ | Maximum of $n$ observations |
| $\mu$ | Location parameter |
| $\sigma$ | Scale parameter |
| $\xi$ | Shape parameter (tail index) |
| $u$ | Threshold |
| $y$ | Exceedance $(X - u)$ |
| $N_u$ | Number of exceedances above $u$ |
| $\zeta_u$ | Exceedance probability |
| $x_p$ | $p$-quantile |
| $T$ | Return period |
| $\alpha$ | Tail index ($1/\xi$) |

---

## Appendix B: Quick Reference Formulas

### GPD Distribution

**PDF:**
$$h(y; \sigma, \xi) = \frac{1}{\sigma}\left(1 + \xi \frac{y}{\sigma}\right)^{-1/\xi - 1}$$

**CDF:**
$$H(y; \sigma, \xi) = 1 - \left(1 + \xi \frac{y}{\sigma}\right)^{-1/\xi}$$

**Quantile:**
$$y_p = \frac{\sigma}{\xi}\left[(1-p)^{-\xi} - 1\right]$$

**Return Level:**
$$x_T = u + \frac{\sigma}{\xi}\left[(T \zeta_u)^{\xi} - 1\right]$$

**Mean:**
$$E[Y] = \frac{\sigma}{1 - \xi}, \quad \xi < 1$$

**Variance:**
$$\text{Var}(Y) = \frac{\sigma^2}{(1-\xi)^2(1-2\xi)}, \quad \xi < 1/2$$

### GEV Distribution

**CDF:**
$$G(x; \mu, \sigma, \xi) = \exp\left\{-\left[1 + \xi\left(\frac{x - \mu}{\sigma}\right)\right]^{-1/\xi}\right\}$$

**Return Level:**
$$x_m = \mu - \frac{\sigma}{\xi}\left[1 - m^{\xi}\right]$$

---

## Appendix C: Shape Parameter Interpretation Guide

| $\xi$ Range | Tail Type | Examples | Moments | Risk Implication |
|-------------|-----------|----------|---------|------------------|
| $\xi < -0.5$ | Very light | Uniform | All exist | Low tail risk |
| $-0.5 < \xi < 0$ | Light | Beta | All exist | Moderate risk, bounded |
| $\xi \approx 0$ | Exponential | Normal, Exponential | All exist | Standard risk |
| $0 < \xi < 0.25$ | Moderate heavy | Lognormal | Mean, Var exist | Above-average risk |
| $0.25 < \xi < 0.5$ | Heavy | Student-t (df>4) | Mean exists, Var infinite | High risk |
| $\xi > 0.5$ | Very heavy | Cauchy, Pareto | Mean infinite | Extreme risk |
| $\xi > 1$ | Extremely heavy | - | All moments infinite | Catastrophic risk |

**Financial Assets:**
- Equity returns: $\xi \approx 0.2$ to $0.4$
- FX rates: $\xi \approx 0.1$ to $0.3$
- Credit spreads: $\xi \approx 0.3$ to $0.6$
- Operational risk: $\xi$ can exceed 0.5

---

## Conclusion

Extreme Value Theory provides a **rigorous mathematical framework** for modeling tail events. The key insights:

1. **Fisher-Tippett-Gnedenko Theorem**: Limiting distributions of extremes belong to GEV family
2. **Pickands-Balkema-de Haan Theorem**: Exceedances above high thresholds follow GPD
3. **Shape parameter** $\xi$ controls tail behavior (heavy vs light)
4. **Extrapolation**: Can estimate quantiles beyond observed data
5. **Applications**: VaR, ES, stress testing, insurance, reinsurance

**Best Practices:**
- Use GPD (POT) for efficiency (more data than block maxima)
- Validate threshold choice with diagnostic plots
- Always report confidence intervals
- Backtest out-of-sample
- Be cautious with extreme extrapolation

EVT is not a panacea, but when applied correctly, it is the **gold standard** for tail risk modeling in finance and insurance.

---

**Document Version:** 1.0
**Last Updated:** March 2, 2026
**Maintained by:** Your Risk Team
