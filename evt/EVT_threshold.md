EVT Threshold Selection Guidelines                                  

  1. Minimum Sample Size Beyond Threshold

  General Rules of Thumb:
  - Minimum exceedances: 30-50 observations above the threshold       
  - Preferred range: 50-100+ exceedances for reliable estimation      
  - Never use: <20 exceedances (estimates become too unstable)        

  Why?
  - Generalized Pareto Distribution (GPD) requires sufficient data for
   MLE estimation
  - Too few exceedances → high variance in parameter estimates        
  - Too many exceedances → bias from including non-extreme values     

  2. Threshold Selection Methods

  Method A: Mean Residual Life (MRL) Plot

  The most common diagnostic tool.

  import numpy as np
  import matplotlib.pyplot as plt

  def mrl_plot(data, thresholds=None):
      """
      Plot Mean Residual Life to identify threshold

      GPD is appropriate when MRL plot is approximately linear above  
  threshold
      """
      if thresholds is None:
          thresholds = np.percentile(data, np.linspace(80, 99, 50))   

      mrl = []
      for u in thresholds:
          exceedances = data[data > u] - u
          mrl.append(np.mean(exceedances) if len(exceedances) > 0 else
   np.nan)

      plt.plot(thresholds, mrl)
      plt.xlabel('Threshold')
      plt.ylabel('Mean Excess')
      plt.title('Mean Residual Life Plot')
      plt.grid(True)

      return thresholds, mrl

  How to use:
  - Look for region where plot becomes roughly linear
  - The threshold should be where linearity begins
  - Trade-off: higher threshold = better GPD fit but fewer
  observations

  Method B: Parameter Stability Plot

  Check if GPD shape parameter (ξ) is stable across thresholds.       

  from scipy import stats

  def parameter_stability_plot(data, thresholds=None):
      """
      Plot GPD shape parameter stability across thresholds

      Good threshold: where ξ becomes relatively constant
      """
      if thresholds is None:
          thresholds = np.percentile(data, np.linspace(85, 99, 30))   

      shapes = []
      scales = []
      n_exceedances = []

      for u in thresholds:
          exceedances = data[data > u] - u
          n_exceedances.append(len(exceedances))

          if len(exceedances) >= 30:  # Minimum for fitting
              shape, loc, scale = stats.genpareto.fit(exceedances,    
  floc=0)
              shapes.append(shape)
              scales.append(scale)
          else:
              shapes.append(np.nan)
              scales.append(np.nan)

      fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

      ax1.plot(thresholds, shapes, 'o-')
      ax1.set_ylabel('Shape Parameter (ξ)')
      ax1.set_title('Parameter Stability')
      ax1.grid(True)

      ax2.plot(thresholds, n_exceedances, 'o-')
      ax2.set_xlabel('Threshold')
      ax2.set_ylabel('Number of Exceedances')
      ax2.grid(True)

      return thresholds, shapes, n_exceedances

  Method C: Quantile-Based Approach

  A practical starting point.

  Common choices:
  - 90th percentile: If you have 1000+ observations (100 exceedances) 
  - 95th percentile: If you have 2000+ observations (100 exceedances) 
   
  - 97th-99th percentile: For very large datasets (10,000+ obs)       

  Formula:
  threshold = np.percentile(data, 90)  # Start here
  n_exceedances = np.sum(data > threshold)

  # Check if you have enough exceedances
  if n_exceedances < 50:
      # Lower the threshold
      threshold = np.percentile(data, 85)

  3. Practical Workflow for Threshold Selection

  def select_evt_threshold(data, min_exceedances=50, max_quantile=99):
      """
      Automated threshold selection with diagnostics
   
      Parameters:
      -----------
      data : array
          Your time series data
      min_exceedances : int
          Minimum required exceedances (default: 50)
      max_quantile : float
          Maximum quantile to consider (default: 99)

      Returns:
      --------
      threshold : float
          Recommended threshold
      diagnostics : dict
          Diagnostic information
      """
      # Step 1: Define candidate thresholds
      quantiles = np.linspace(80, max_quantile, 40)
      thresholds = np.percentile(data, quantiles)

      # Step 2: Calculate stability metrics
      results = []
      for u in thresholds:
          exceedances = data[data > u] - u
          n_exc = len(exceedances)

          if n_exc >= 30:
              # Fit GPD
              shape, _, scale = stats.genpareto.fit(exceedances,      
  floc=0)

              # Calculate mean excess
              mean_excess = np.mean(exceedances)

              results.append({
                  'threshold': u,
                  'n_exceedances': n_exc,
                  'shape': shape,
                  'scale': scale,
                  'mean_excess': mean_excess
              })

      df = pd.DataFrame(results)

      # Step 3: Select threshold based on criteria
      # Filter: Must have minimum exceedances
      candidates = df[df['n_exceedances'] >= min_exceedances]

      if len(candidates) == 0:
          raise ValueError(f"Cannot find threshold with
  {min_exceedances} exceedances")

      # Step 4: Look for stability in shape parameter
      # Choose where shape parameter variance is minimized
      # in a local window
      window = 5
      shape_stability = []
      for i in range(window, len(candidates)):
          window_std = candidates.iloc[i-window:i]['shape'].std()     
          shape_stability.append(window_std)

      if shape_stability:
          # Select threshold with most stable shape parameter
          # that still has enough exceedances
          best_idx = np.argmin(shape_stability) + window
          selected = candidates.iloc[best_idx]
      else:
          # Fallback: use middle of candidate range
          selected = candidates.iloc[len(candidates)//2]

      return selected['threshold'], df

  # Usage example:
  # threshold, diagnostics = select_evt_threshold(your_data,
  min_exceedances=50)

  4. Validation Checks

  After selecting a threshold, validate:

  def validate_threshold(data, threshold):
      """
      Perform diagnostic checks on selected threshold
      """
      exceedances = data[data > threshold] - threshold

      print(f"Threshold: {threshold:.4f}")
      print(f"Number of exceedances: {len(exceedances)}")
      print(f"Percentage above threshold:
  {100*len(exceedances)/len(data):.2f}%")

      # Fit GPD
      shape, _, scale = stats.genpareto.fit(exceedances, floc=0)      
      print(f"Shape parameter (ξ): {shape:.4f}")
      print(f"Scale parameter (σ): {scale:.4f}")

      # GPD validity checks
      if shape < -0.5:
          print("⚠️ WARNING: Shape < -0.5, distribution has finite    
  endpoint")
      elif shape > 0:
          print("✓ Heavy-tailed distribution (shape > 0)")
      else:
          print("✓ Light-tailed distribution (shape ≈ 0)")

      # QQ plot for goodness of fit
      from scipy.stats import genpareto
      fig, ax = plt.subplots(1, 2, figsize=(12, 5))

      # QQ plot
      stats.probplot(exceedances, dist=genpareto,
                     sparams=(shape, 0, scale), plot=ax[0])
      ax[0].set_title('Q-Q Plot')

      # Empirical vs fitted CDF
      sorted_exc = np.sort(exceedances)
      empirical_cdf = np.arange(1, len(sorted_exc)+1) /
  len(sorted_exc)
      fitted_cdf = genpareto.cdf(sorted_exc, shape, 0, scale)

      ax[1].plot(sorted_exc, empirical_cdf, 'o', alpha=0.5,
  label='Empirical')
      ax[1].plot(sorted_exc, fitted_cdf, '-', label='Fitted GPD')     
      ax[1].set_xlabel('Exceedance')
      ax[1].set_ylabel('CDF')
      ax[1].legend()
      ax[1].set_title('CDF Comparison')

      plt.tight_layout()
      return shape, scale

  5. Context-Specific Recommendations

  For Financial Risk (like FRTB market risk):
  - Threshold: 95th-99th percentile (depending on data size)
  - Min exceedances: 50-100
  - Rationale: Balance between capturing true extremes and statistical
   power

  For Physical Climate Risk (floods, cyclones):
  - Threshold: Often based on return period (e.g., 25-year event)     
  - Min exceedances: 30-50 events
  - Rationale: Physical meaning (e.g., design standards)

  For Credit Risk:
  - Threshold: 90th-95th percentile of losses
  - Min exceedances: 50+
  - Rationale: Regulatory requirements and data availability

  6. Sample Size Requirements by Dataset Size
  Total Sample Size: 250-500
  Recommended Percentile: 80th-85th
  Expected Exceedances: 38-100
  ────────────────────────────────────────
  Total Sample Size: 500-1000
  Recommended Percentile: 85th-90th
  Expected Exceedances: 50-150
  ────────────────────────────────────────
  Total Sample Size: 1000-2000
  Recommended Percentile: 90th-95th
  Expected Exceedances: 50-200
  ────────────────────────────────────────
  Total Sample Size: 2000-5000
  Recommended Percentile: 95th-97th
  Expected Exceedances: 100-250
  ────────────────────────────────────────
  Total Sample Size: 5000+
  Recommended Percentile: 97th-99th
  Expected Exceedances: 150-500
  7. Common Pitfalls to Avoid

  ❌ Too low threshold: Non-extreme values violate GPD assumptions    
  ❌ Too high threshold: Too few exceedances, unstable estimates      
  ❌ Ignoring diagnostics: Always check MRL plot and parameter        
  stability
  ❌ Fixed threshold across different datasets: Adapt to your data    
  ❌ Ignoring temporal dependence: Check for clustering of extremes   

  Summary Recommendation

  Start with this approach:
  1. Initial threshold: 90th-95th percentile of your data
  2. Check exceedances: Should have 50-100+ observations
  3. Run diagnostics: MRL plot, parameter stability plot
  4. Iterate: Adjust threshold based on stability
  5. Validate: QQ plot and goodness-of-fit tests