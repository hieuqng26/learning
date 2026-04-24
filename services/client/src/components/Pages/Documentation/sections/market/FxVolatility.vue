<template>
  <div class="doc-section">
    <h1>FX Volatility</h1>

    <div class="doc-intro">
      <p>
        FX volatility surfaces represent the implied volatilities of currency options across different
        strikes and maturities. Understanding volatility surfaces is essential for pricing FX options
        and managing volatility risk.
      </p>
    </div>

    <section class="doc-subsection">
      <h2>Volatility Surface Overview</h2>
      <p>
        An FX volatility surface is a 3-dimensional representation showing how implied volatility varies with:
      </p>
      <ul>
        <li><strong>Maturity (Time to Expiry):</strong> How volatility changes over different time horizons</li>
        <li><strong>Strike/Moneyness:</strong> How volatility varies across different strike prices (the "smile")</li>
      </ul>

      <div class="mt-3">
        <Card>
          <template #title>The Volatility Smile</template>
          <template #content>
            <p>
              In FX markets, implied volatility typically forms a "smile" pattern when plotted against strike prices:
            </p>
            <ul class="mt-2">
              <li><strong>ATM (At-The-Money):</strong> Lowest volatility, at or near the spot/forward rate</li>
              <li><strong>OTM Puts/Calls:</strong> Higher volatility as you move away from ATM in either direction</li>
              <li><strong>Skew:</strong> Asymmetry in the smile (one side higher than the other)</li>
            </ul>
            <p class="text-sm text-color-secondary mt-3">
              The smile reflects market participants' views on the likelihood of large currency moves (fat tails)
              and directional biases.
            </p>
          </template>
        </Card>
      </div>
    </section>

    <section class="doc-subsection">
      <h2>Market Quotation Convention</h2>
      <p>FX volatility is typically quoted using three key parameters for each maturity:</p>

      <DataTable :value="quotingConventions" class="mt-3" :paginator="false">
        <Column field="param" header="Parameter" style="width: 20%">
          <template #body="slotProps">
            <strong>{{ slotProps.data.param }}</strong>
          </template>
        </Column>
        <Column field="abbrev" header="Abbreviation" style="width: 15%">
          <template #body="slotProps">
            <code>{{ slotProps.data.abbrev }}</code>
          </template>
        </Column>
        <Column field="description" header="Description"></Column>
      </DataTable>

      <h3 class="mt-4">Example Market Quote</h3>
      <div class="mt-2 p-3" style="background: var(--surface-ground)">
        <p><strong>EUR/USD 1-Month:</strong></p>
        <ul class="compact-list text-sm mt-2">
          <li>ATM: 7.5%</li>
          <li>25-Delta RR: -0.5% (puts more expensive than calls)</li>
          <li>25-Delta BF: 0.3%</li>
        </ul>
      </div>
    </section>

    <section class="doc-subsection">
      <h2>Surface Construction</h2>
      <p>Building a complete volatility surface from market quotes involves several steps:</p>

      <Panel header="1. Collect Market Quotes" :toggleable="true">
        <p>Gather ATM, RR, and BF quotes for standard maturities:</p>
        <ul class="text-sm mt-2">
          <li>O/N, 1W, 2W, 1M, 2M, 3M, 6M, 9M, 1Y, 18M, 2Y, 3Y, 5Y</li>
          <li>Typically quoted for 10-delta and 25-delta strikes</li>
        </ul>
      </Panel>

      <Panel header="2. Convert to Strike Volatilities" :toggleable="true" class="mt-2">
        <p>Transform ATM/RR/BF quotes into volatilities at specific strikes:</p>
        <div class="mt-2 p-2" style="background: var(--surface-ground)">
          <code class="text-sm">
            Vol(25D Put) = ATM - 0.5 × RR - BF<br>
            Vol(ATM) = ATM<br>
            Vol(25D Call) = ATM + 0.5 × RR - BF
          </code>
        </div>
      </Panel>

      <Panel header="3. Determine Strike Levels" :toggleable="true" class="mt-2">
        <p>
          Calculate actual strike prices corresponding to the delta levels using
          iterative methods (since volatility affects delta, which affects strike).
        </p>
      </Panel>

      <Panel header="4. Interpolate in Strike Direction" :toggleable="true" class="mt-2">
        <p>Interpolation methods for strike dimension:</p>
        <ul class="text-sm mt-2">
          <li><strong>SABR Model:</strong> Stochastic Alpha Beta Rho model (most common in FX)</li>
          <li><strong>Cubic Spline:</strong> On variance or volatility</li>
          <li><strong>SVI (Stochastic Volatility Inspired):</strong> Parametric form</li>
        </ul>
      </Panel>

      <Panel header="5. Interpolate in Time Direction" :toggleable="true" class="mt-2">
        <p>Interpolation between maturities:</p>
        <ul class="text-sm mt-2">
          <li>Linear interpolation on variance (σ² × t)</li>
          <li>Ensures variance increases with time (no calendar arbitrage)</li>
        </ul>
      </Panel>
    </section>

    <section class="doc-subsection">
      <h2>Volatility Surface Uses</h2>

      <div class="grid mt-3">
        <div class="col-12 md:col-6">
          <Card class="h-full">
            <template #title>
              <span class="text-sm">Option Pricing</span>
            </template>
            <template #content">
              <p>For a given option (strike, maturity):</p>
              <ol class="compact-list text-sm mt-2">
                <li>1. Look up implied volatility from surface</li>
                <li>2. Input into pricing model (e.g., Black-Scholes, Garman-Kohlhagen)</li>
                <li>3. Calculate option premium</li>
              </ol>
            </template>
          </Card>
        </div>

        <div class="col-12 md:col-6">
          <Card class="h-full">
            <template #title>
              <span class="text-sm">Risk Management</span>
            </template>
            <template #content>
              <p>Volatility sensitivities:</p>
              <ul class="compact-list text-sm mt-2">
                <li><strong>Vega:</strong> Sensitivity to parallel shift in volatility</li>
                <li><strong>Volga:</strong> Convexity with respect to volatility</li>
                <li><strong>Vanna:</strong> Cross-sensitivity to spot and volatility</li>
              </ul>
            </template>
          </Card>
        </div>

        <div class="col-12 md:col-6">
          <Card class="h-full">
            <template #title>
              <span class="text-sm">Hedging Strategies</span>
            </template>
            <template #content>
              <p>Traders use volatility surfaces to:</p>
              <ul class="compact-list text-sm mt-2">
                <li>Hedge exotic options with vanilla options</li>
                <li>Construct volatility arbitrage strategies</li>
                <li>Manage smile risk and skew risk</li>
              </ul>
            </template>
          </Card>
        </div>

        <div class="col-12 md:col-6">
          <Card class="h-full">
            <template #title>
              <span class="text-sm">Model Calibration</span>
            </template>
            <template #content>
              <p>Calibrate pricing models to market:</p>
              <ul class="compact-list text-sm mt-2">
                <li>Fit model parameters to match market volatilities</li>
                <li>Used for exotic options and path-dependent products</li>
                <li>Examples: Local volatility, stochastic volatility models</li>
              </ul>
            </template>
          </Card>
        </div>
      </div>
    </section>

    <section class="doc-subsection">
      <h2>Key Considerations</h2>

      <Panel header="Arbitrage-Free Conditions" :toggleable="true">
        <p>A valid volatility surface must satisfy no-arbitrage constraints:</p>
        <ul class="text-sm mt-2">
          <li><strong>Calendar arbitrage:</strong> Variance must increase with maturity</li>
          <li><strong>Butterfly arbitrage:</strong> Call spreads must have positive value</li>
          <li><strong>Call spread arbitrage:</strong> Call prices must be decreasing in strike</li>
        </ul>
      </Panel>

      <Panel header="Delta Conventions" :toggleable="true" class="mt-2">
        <p>Different delta conventions affect strike calculations:</p>
        <ul class="text-sm mt-2">
          <li><strong>Premium-included delta:</strong> Accounts for premium payment</li>
          <li><strong>Forward delta:</strong> Based on forward rate, not spot</li>
          <li><strong>Spot delta:</strong> Based on spot rate</li>
        </ul>
        <p class="text-sm text-color-secondary mt-2">
          Standard in FX: Premium-included forward delta
        </p>
      </Panel>

      <Panel header="Smile Dynamics" :toggleable="true" class="mt-2">
        <p>How the smile changes when spot moves:</p>
        <ul class="text-sm mt-2">
          <li><strong>Sticky strike:</strong> Volatility stays with absolute strike levels</li>
          <li><strong>Sticky delta:</strong> Volatility stays with delta levels (more common in FX)</li>
          <li><strong>Sticky moneyness:</strong> Volatility stays with moneyness (K/F)</li>
        </ul>
      </Panel>
    </section>

    <Message severity="info" class="mt-4">
      <strong>Market Practice:</strong> FX volatility surfaces are typically rebuilt multiple times
      per day as market quotes change. Real-time surface updates are crucial for accurate pricing
      and risk management.
    </Message>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Card from 'primevue/card'
import Panel from 'primevue/panel'
import Message from 'primevue/message'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'

const quotingConventions = ref([
  {
    param: 'At-The-Money',
    abbrev: 'ATM',
    description: 'Volatility at the forward strike (50-delta straddle). Represents the baseline volatility level.'
  },
  {
    param: 'Risk Reversal',
    abbrev: 'RR',
    description: '25-Delta Call volatility minus 25-Delta Put volatility. Measures the skew (directional bias).'
  },
  {
    param: 'Butterfly',
    abbrev: 'BF',
    description: 'Average of 25-Delta Call and Put volatilities minus ATM volatility. Measures the smile convexity.'
  }
])
</script>

<style lang="scss" scoped>
.doc-section {
  h1 {
    color: var(--primary-color);
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid var(--surface-border);
  }

  h2 {
    color: var(--text-color);
    margin-top: 2rem;
    margin-bottom: 1rem;
  }

  h3 {
    color: var(--text-color);
    margin-top: 1.5rem;
    margin-bottom: 0.75rem;
    font-size: 1.1rem;
  }

  .doc-intro {
    background: var(--surface-ground);
    padding: 1rem;
    border-left: 4px solid var(--primary-color);
    margin-bottom: 2rem;
  }

  .doc-subsection {
    margin-bottom: 2rem;
  }

  ul {
    list-style-type: disc;
    padding-left: 1.5rem;

    li {
      padding: 0.25rem 0;
    }

    &.compact-list {
      list-style-type: none;
      padding-left: 0;

      li {
        padding: 0.25rem 0;
      }
    }
  }

  ol.compact-list {
    list-style-type: none;
    padding-left: 0;

    li {
      padding: 0.25rem 0;
    }
  }

  code {
    background: var(--surface-ground);
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-family: 'Courier New', monospace;
    font-size: 0.9em;
  }
}
</style>
