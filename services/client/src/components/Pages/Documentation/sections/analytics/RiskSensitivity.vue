<template>
  <div class="doc-section">
    <h1>Risk Sensitivity (Greeks)</h1>

    <div class="doc-intro">
      <p>
        Risk sensitivities, commonly known as "Greeks", measure how the value of a derivative or
        portfolio changes in response to changes in underlying market risk factors. Understanding
        and managing these sensitivities is fundamental to effective risk management.
      </p>
    </div>

    <section class="doc-subsection">
      <h2>First-Order Greeks</h2>
      <p>First-order Greeks measure the rate of change in value with respect to a single risk factor:</p>

      <Panel header="Delta (Δ)" :toggleable="true">
        <div class="greek-detail">
          <p><strong>Definition:</strong> Rate of change of value with respect to underlying spot price</p>
          <div class="mt-2 p-2" style="background: var(--surface-ground)">
            <code>Delta = ∂V / ∂S</code>
          </div>

          <div class="grid mt-3">
            <div class="col-12 md:col-6">
              <h4 class="text-sm">Interpretation</h4>
              <ul class="compact-list text-sm">
                <li>Delta = 0.5 means $1 increase in underlying → $0.50 increase in option value</li>
                <li>Call options: Delta between 0 and 1</li>
                <li>Put options: Delta between -1 and 0</li>
                <li>Linear products (forwards, swaps): Delta ≈ ±1</li>
              </ul>
            </div>
            <div class="col-12 md:col-6">
              <h4 class="text-sm">Usage</h4>
              <ul class="compact-list text-sm">
                <li>Delta hedging: Trade underlying to neutralize spot risk</li>
                <li>Portfolio aggregation: Net delta position</li>
                <li>Quick estimate of P&L for small spot moves</li>
              </ul>
            </div>
          </div>
        </div>
      </Panel>

      <Panel header="Vega (ν)" :toggleable="true" class="mt-2">
        <div class="greek-detail">
          <p><strong>Definition:</strong> Rate of change of value with respect to volatility</p>
          <div class="mt-2 p-2" style="background: var(--surface-ground)">
            <code>Vega = ∂V / ∂σ</code>
          </div>

          <div class="grid mt-3">
            <div class="col-12 md:col-6">
              <h4 class="text-sm">Interpretation</h4>
              <ul class="compact-list text-sm">
                <li>Vega = 1000 means 1% increase in vol → $1000 increase in value</li>
                <li>Always positive for long options (calls and puts)</li>
                <li>Always negative for short options</li>
                <li>Largest for ATM options, decreases for ITM/OTM</li>
              </ul>
            </div>
            <div class="col-12 md:col-6">
              <h4 class="text-sm">Usage</h4>
              <ul class="compact-list text-sm">
                <li>Vega hedging: Trade options to neutralize vol risk</li>
                <li>Identify exposure to volatility regime changes</li>
                <li>Essential for options portfolios and vol traders</li>
              </ul>
            </div>
          </div>
        </div>
      </Panel>

      <Panel header="Rho (ρ)" :toggleable="true" class="mt-2">
        <div class="greek-detail">
          <p><strong>Definition:</strong> Rate of change of value with respect to interest rates</p>
          <div class="mt-2 p-2" style="background: var(--surface-ground)">
            <code>Rho = ∂V / ∂r</code>
          </div>

          <div class="grid mt-3">
            <div class="col-12 md:col-6">
              <h4 class="text-sm">Interpretation</h4>
              <ul class="compact-list text-sm">
                <li>Measures exposure to interest rate changes</li>
                <li>Larger for longer-dated instruments</li>
                <li>Can have domestic and foreign rho for FX products</li>
              </ul>
            </div>
            <div class="col-12 md:col-6">
              <h4 class="text-sm">Usage</h4>
              <ul class="compact-list text-sm">
                <li>Interest rate risk management</li>
                <li>Important for long-dated options and swaps</li>
                <li>Cross-currency exposures</li>
              </ul>
            </div>
          </div>
        </div>
      </Panel>

      <Panel header="Theta (Θ)" :toggleable="true" class="mt-2">
        <div class="greek-detail">
          <p><strong>Definition:</strong> Rate of change of value with respect to time (time decay)</p>
          <div class="mt-2 p-2" style="background: var(--surface-ground)">
            <code>Theta = ∂V / ∂t</code>
          </div>

          <div class="grid mt-3">
            <div class="col-12 md:col-6">
              <h4 class="text-sm">Interpretation</h4>
              <ul class="compact-list text-sm">
                <li>Negative for long options (value decays over time)</li>
                <li>Positive for short options (benefit from time decay)</li>
                <li>Accelerates as expiry approaches</li>
                <li>Largest for ATM options near expiry</li>
              </ul>
            </div>
            <div class="col-12 md:col-6">
              <h4 class="text-sm">Usage</h4>
              <ul class="compact-list text-sm">
                <li>Understand P&L erosion over time</li>
                <li>Plan for rolling/extending positions</li>
                <li>Options selling strategies exploit positive theta</li>
              </ul>
            </div>
          </div>
        </div>
      </Panel>
    </section>

    <section class="doc-subsection">
      <h2>Second-Order Greeks</h2>
      <p>Second-order Greeks measure the curvature or rate of change of first-order Greeks:</p>

      <Panel header="Gamma (Γ)" :toggleable="true">
        <div class="greek-detail">
          <p><strong>Definition:</strong> Rate of change of Delta with respect to underlying spot price</p>
          <div class="mt-2 p-2" style="background: var(--surface-ground)">
            <code>Gamma = ∂²V / ∂S² = ∂Δ / ∂S</code>
          </div>

          <div class="grid mt-3">
            <div class="col-12 md:col-6">
              <h4 class="text-sm">Interpretation</h4>
              <ul class="compact-list text-sm">
                <li>Positive for long options, negative for short options</li>
                <li>Largest for ATM options near expiry</li>
                <li>Measures convexity of option payoff</li>
                <li>High gamma → Delta changes rapidly with spot moves</li>
              </ul>
            </div>
            <div class="col-12 md:col-6">
              <h4 class="text-sm">Usage</h4>
              <ul class="compact-list text-sm">
                <li>Rebalancing frequency for delta hedges</li>
                <li>P&L from large spot moves (Delta + 0.5 × Gamma × ΔS²)</li>
                <li>Gamma scalping strategies</li>
              </ul>
            </div>
          </div>
        </div>
      </Panel>

      <Panel header="Vanna" :toggleable="true" class="mt-2">
        <div class="greek-detail">
          <p><strong>Definition:</strong> Rate of change of Delta with respect to volatility (or Vega w.r.t. spot)</p>
          <div class="mt-2 p-2" style="background: var(--surface-ground)">
            <code>Vanna = ∂²V / (∂S ∂σ) = ∂Δ / ∂σ = ∂ν / ∂S</code>
          </div>

          <div class="mt-2">
            <p class="text-sm">
              <strong>Usage:</strong> Measures cross-sensitivity between spot and volatility.
              Important for managing complex option portfolios and understanding how delta hedges
              change with volatility shifts.
            </p>
          </div>
        </div>
      </Panel>

      <Panel header="Volga (Vomma)" :toggleable="true" class="mt-2">
        <div class="greek-detail">
          <p><strong>Definition:</strong> Rate of change of Vega with respect to volatility</p>
          <div class="mt-2 p-2" style="background: var(--surface-ground)">
            <code>Volga = ∂²V / ∂σ² = ∂ν / ∂σ</code>
          </div>

          <div class="mt-2">
            <p class="text-sm">
              <strong>Usage:</strong> Measures convexity of option value with respect to volatility.
              Important for volatility trading and managing risk in changing volatility environments.
            </p>
          </div>
        </div>
      </Panel>
    </section>

    <section class="doc-subsection">
      <h2>Interest Rate Sensitivities</h2>
      <p>For interest rate products, specialized sensitivity measures are used:</p>

      <DataTable :value="irSensitivities" class="mt-3" :paginator="false">
        <Column field="measure" header="Measure" style="width: 25%">
          <template #body="slotProps">
            <strong>{{ slotProps.data.measure }}</strong>
          </template>
        </Column>
        <Column field="definition" header="Definition" style="width: 40%"></Column>
        <Column field="usage" header="Usage" style="width: 35%"></Column>
      </DataTable>
    </section>

    <section class="doc-subsection">
      <h2>Scenario Analysis</h2>
      <p>Beyond individual Greeks, scenario analysis evaluates portfolio value under various market conditions:</p>

      <div class="grid mt-3">
        <div class="col-12 md:col-4">
          <Card class="h-full">
            <template #title>
              <span class="text-sm">Parallel Shifts</span>
            </template>
            <template #content>
              <p class="text-sm">Shift entire curve up or down uniformly</p>
              <ul class="compact-list text-sm mt-2">
                <li>+100bp rate shift</li>
                <li>-50bp rate shift</li>
                <li>+10% vol shift</li>
                <li>+5% spot shift</li>
              </ul>
            </template>
          </Card>
        </div>

        <div class="col-12 md:col-4">
          <Card class="h-full">
            <template #title>
              <span class="text-sm">Non-Parallel Shifts</span>
            </template>
            <template #content>
              <p class="text-sm">Curve shape changes (steepening/flattening)</p>
              <ul class="compact-list text-sm mt-2">
                <li>Steepening: short rates ↓, long rates ↑</li>
                <li>Flattening: short rates ↑, long rates ↓</li>
                <li>Butterfly: ends fixed, middle moves</li>
              </ul>
            </template>
          </Card>
        </div>

        <div class="col-12 md:col-4">
          <Card class="h-full">
            <template #title>
              <span class="text-sm">Historical Scenarios</span>
            </template>
            <template #content>
              <p class="text-sm">Replay historical stress events</p>
              <ul class="compact-list text-sm mt-2">
                <li>2008 Financial Crisis</li>
                <li>COVID-19 March 2020</li>
                <li>Brexit vote 2016</li>
                <li>Custom scenarios</li>
              </ul>
            </template>
          </Card>
        </div>
      </div>
    </section>

    <section class="doc-subsection">
      <h2>Practical Example: FX Option Greeks</h2>

      <div class="mt-3">
        <Card>
          <template #title>EUR/USD Call Option</template>
          <template #content>
            <p class="text-sm"><strong>Position:</strong> Long 1M EUR/USD Call, Strike 1.1000, Notional EUR 10M, Expiry in 3 months</p>

            <DataTable :value="exampleGreeks" class="mt-3" :paginator="false">
              <Column field="greek" header="Greek" style="width: 20%">
                <template #body="slotProps">
                  <strong>{{ slotProps.data.greek }}</strong>
                </template>
              </Column>
              <Column field="value" header="Value" style="width: 20%"></Column>
              <Column field="interpretation" header="Interpretation"></Column>
            </DataTable>

            <p class="text-sm text-color-secondary mt-3">
              <strong>Hedging Strategy:</strong> To delta hedge, sell EUR 5,000,000 spot. This neutralizes immediate spot risk
              but Gamma and Vega exposures remain. Continuous rebalancing needed as Delta changes (captured by Gamma).
            </p>
          </template>
        </Card>
      </div>
    </section>

    <Message severity="warn" class="mt-4">
      <strong>Important:</strong> Greeks are local measures (valid for small changes). For large market moves,
      higher-order Greeks (Gamma, Vanna, Volga) become increasingly important for accurate P&L estimation.
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

const irSensitivities = ref([
  {
    measure: 'DV01 (Dollar Value of 1bp)',
    definition: 'Change in portfolio value for 1bp parallel shift in yield curve',
    usage: 'Primary interest rate risk measure for IR swaps, bonds'
  },
  {
    measure: 'Duration',
    definition: 'Weighted average time to cash flows; measures price sensitivity to yield changes',
    usage: 'Bond portfolio risk, Macaulay and Modified Duration'
  },
  {
    measure: 'Convexity',
    definition: 'Second derivative of price with respect to yield (curvature)',
    usage: 'Measures how duration changes with yield; important for large rate moves'
  },
  {
    measure: 'Key Rate Duration (KRD)',
    definition: 'Sensitivity to specific points on the curve (e.g., 2Y, 5Y, 10Y)',
    usage: 'Curve risk decomposition, hedging specific tenors'
  },
  {
    measure: 'Basis Point Value (BPV)',
    definition: 'P&L impact of 1bp move in a specific curve or spread',
    usage: 'Spread risk (e.g., LIBOR-OIS spread), credit spreads'
  }
])

const exampleGreeks = ref([
  {
    greek: 'Delta',
    value: '+0.50',
    interpretation: 'If EUR/USD rises by 0.0100 (100 pips), option value increases by ~$50,000'
  },
  {
    greek: 'Gamma',
    value: '+0.015',
    interpretation: 'Delta increases by 0.015 for every 0.0100 move in spot'
  },
  {
    greek: 'Vega',
    value: '+8,500',
    interpretation: '1% increase in implied vol increases option value by $8,500'
  },
  {
    greek: 'Theta',
    value: '-1,200',
    interpretation: 'Option loses $1,200 per day from time decay (all else equal)'
  },
  {
    greek: 'Rho (Domestic)',
    value: '+2,500',
    interpretation: '1% increase in USD rates increases option value by $2,500'
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

  h4 {
    margin-bottom: 0.5rem;
    color: var(--text-color);
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

  .greek-detail {
    p {
      line-height: 1.6;
    }
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

  code {
    background: var(--surface-ground);
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-family: 'Courier New', monospace;
    font-size: 0.9em;
  }
}
</style>
