<template>
  <div class="doc-section">
    <h1>Yield Curves</h1>

    <div class="doc-intro">
      <p>
        A yield curve represents the relationship between interest rates (or yields) and different
        maturities for debt instruments of similar credit quality. Yield curves are fundamental
        building blocks for pricing and risk management of interest rate derivatives.
      </p>
    </div>

    <section class="doc-subsection">
      <h2>Types of Yield Curves</h2>

      <Panel header="OIS (Overnight Index Swap) Curves" :toggleable="true">
        <p><strong>Purpose:</strong> Discounting curve for collateralized derivatives</p>
        <p class="mt-2"><strong>Construction:</strong> Bootstrapped from OIS swap rates</p>
        <p class="mt-2"><strong>Key Characteristics:</strong></p>
        <ul class="text-sm mt-1">
          <li>Closest proxy to risk-free rates</li>
          <li>Based on overnight rates (SOFR, ESTR, SONIA)</li>
          <li>Used as discount curve in dual-curve framework</li>
          <li>Lower than LIBOR/SOFR term curves (no credit risk premium)</li>
        </ul>
      </Panel>

      <Panel header="IBOR/RFR Curves (SOFR, EURIBOR)" :toggleable="true" class="mt-2">
        <p><strong>Purpose:</strong> Projection curve for floating rate cash flows</p>
        <p class="mt-2"><strong>Construction:</strong> Bootstrapped from deposits, futures, and swaps</p>
        <p class="mt-2"><strong>Key Characteristics:</strong></p>
        <ul class="text-sm mt-1">
          <li>SOFR has replaced USD LIBOR as the benchmark</li>
          <li>EURIBOR still widely used in EUR markets</li>
          <li>Used to project future floating rate fixings</li>
          <li>Includes credit risk and liquidity premiums</li>
        </ul>
      </Panel>

      <Panel header="Government Bond Curves" :toggleable="true" class="mt-2">
        <p><strong>Purpose:</strong> Sovereign risk-free benchmark rates</p>
        <p class="mt-2"><strong>Construction:</strong> Fitted to government bond prices</p>
        <p class="mt-2"><strong>Key Characteristics:</strong></p>
        <ul class="text-sm mt-1">
          <li>US Treasuries, German Bunds, UK Gilts, etc.</li>
          <li>Considered "risk-free" for pricing purposes</li>
          <li>Liquidity and special repo effects can distort rates</li>
          <li>Used for relative value analysis</li>
        </ul>
      </Panel>

      <Panel header="Cross-Currency Basis Curves" :toggleable="true" class="mt-2">
        <p><strong>Purpose:</strong> Adjust foreign currency curves for basis spreads</p>
        <p class="mt-2"><strong>Construction:</strong> Built from FX swaps and cross-currency basis swaps</p>
        <p class="mt-2"><strong>Key Characteristics:</strong></p>
        <ul class="text-sm mt-1">
          <li>Captures supply/demand imbalances in currency swap markets</li>
          <li>Non-zero basis violates covered interest parity</li>
          <li>Essential for pricing cross-currency swaps</li>
          <li>Varies significantly by currency pair and tenor</li>
        </ul>
      </Panel>
    </section>

    <section class="doc-subsection">
      <h2>Curve Construction Methods</h2>

      <h3>Bootstrapping Process</h3>
      <p>Sequential method to extract discount factors from market instruments:</p>

      <div class="mt-3">
        <Card>
          <template #title>Step-by-Step Bootstrapping</template>
          <template #content>
            <ol class="construction-steps">
              <li>
                <strong>Start with shortest maturity:</strong> Use overnight or 1-day deposit rate
                to get first discount factor DF(T1)
              </li>
              <li>
                <strong>Move to next maturity:</strong> Use market quote for instrument maturing
                at T2. Solve for DF(T2) given known DF(T1)
              </li>
              <li>
                <strong>Continue sequentially:</strong> For each subsequent maturity Tn, solve for
                DF(Tn) using all previously determined discount factors
              </li>
              <li>
                <strong>Result:</strong> Complete discount factor curve at all instrument maturity points
              </li>
            </ol>
          </template>
        </Card>
      </div>

      <h3 class="mt-4">Interpolation Methods</h3>
      <p>Techniques to determine rates between observable market points:</p>

      <DataTable :value="interpolationMethods" class="mt-3" :paginator="false">
        <Column field="method" header="Method" style="width: 25%">
          <template #body="slotProps">
            <strong>{{ slotProps.data.method }}</strong>
          </template>
        </Column>
        <Column field="interpolated" header="What's Interpolated" style="width: 30%"></Column>
        <Column field="pros" header="Advantages" style="width: 22.5%"></Column>
        <Column field="cons" header="Disadvantages" style="width: 22.5%"></Column>
      </DataTable>
    </section>

    <section class="doc-subsection">
      <h2>Building Instruments</h2>
      <p>Different instruments are used for different parts of the curve:</p>

      <div class="grid mt-3">
        <div class="col-12 md:col-4">
          <Card class="h-full">
            <template #title>
              <span class="text-sm">Short End (0-1 Year)</span>
            </template>
            <template #content>
              <ul class="compact-list">
                <li><strong>Deposits:</strong> O/N, 1W, 1M, 3M, 6M</li>
                <li><strong>Overnight Rates:</strong> SOFR, ESTR, SONIA</li>
                <li><strong>FRAs:</strong> Forward Rate Agreements</li>
              </ul>
              <p class="text-sm text-color-secondary mt-2">
                Most liquid and reliable quotes
              </p>
            </template>
          </Card>
        </div>

        <div class="col-12 md:col-4">
          <Card class="h-full">
            <template #title>
              <span class="text-sm">Medium Term (1-3 Years)</span>
            </template>
            <template #content>
              <ul class="compact-list">
                <li><strong>Futures:</strong> Eurodollar, SOFR futures</li>
                <li><strong>Short Swaps:</strong> 1Y, 18M, 2Y swaps</li>
              </ul>
              <p class="text-sm text-color-secondary mt-2">
                Futures provide high liquidity but require convexity adjustments
              </p>
            </template>
          </Card>
        </div>

        <div class="col-12 md:col-4">
          <Card class="h-full">
            <template #title>
              <span class="text-sm">Long End (3+ Years)</span>
            </template>
            <template #content>
              <ul class="compact-list">
                <li><strong>IRS:</strong> 3Y, 5Y, 7Y, 10Y, 15Y, 20Y, 30Y, 50Y</li>
                <li><strong>Bonds:</strong> Government bonds for sovereign curves</li>
              </ul>
              <p class="text-sm text-color-secondary mt-2">
                Swaps are most liquid long-dated instruments
              </p>
            </template>
          </Card>
        </div>
      </div>
    </section>

    <section class="doc-subsection">
      <h2>Use in Pricing</h2>

      <h3>Discounting Cash Flows</h3>
      <p>Convert future cash flows to present value:</p>
      <div class="mt-2 p-3" style="background: var(--surface-ground)">
        <code class="text-lg">PV = Σ (Cash Flow_i × DF(t_i))</code>
        <p class="text-sm text-color-secondary mt-2">
          Where DF(t_i) is the discount factor from the appropriate curve at time t_i
        </p>
      </div>

      <h3 class="mt-4">Forward Rate Calculation</h3>
      <p>Derive forward rates for floating leg projections:</p>
      <div class="mt-2 p-3" style="background: var(--surface-ground)">
        <code class="text-lg">Forward Rate(t1, t2) = [DF(t1) / DF(t2) - 1] / (t2 - t1)</code>
        <p class="text-sm text-color-secondary mt-2">
          Forward rate from t1 to t2, annualized based on day count convention
        </p>
      </div>

      <h3 class="mt-4">Dual Curve Framework</h3>
      <p>Modern derivatives pricing uses two curves:</p>
      <div class="grid mt-3">
        <div class="col-12 md:col-6">
          <Card>
            <template #title>Discounting Curve</template>
            <template #content>
              <p><strong>Curve:</strong> OIS (risk-free rate)</p>
              <p class="mt-2"><strong>Purpose:</strong> Calculate present value of all cash flows</p>
              <p class="mt-2"><strong>Reflects:</strong> The cost of funding collateralized positions</p>
            </template>
          </Card>
        </div>
        <div class="col-12 md:col-6">
          <Card>
            <template #title>Projection Curve</template>
            <template #content>
              <p><strong>Curve:</strong> IBOR/RFR (SOFR, EURIBOR)</p>
              <p class="mt-2"><strong>Purpose:</strong> Project future floating rate fixings</p>
              <p class="mt-2"><strong>Reflects:</strong> Expected future interest rate levels</p>
            </template>
          </Card>
        </div>
      </div>
    </section>

    <Message severity="warn" class="mt-4">
      <strong>Important:</strong> Always ensure curve construction is arbitrage-free and that all
      input instruments are priced correctly by the resulting curve. Inconsistent inputs can lead
      to pricing errors and unreliable risk measures.
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

const interpolationMethods = ref([
  {
    method: 'Linear on Zero Rates',
    interpolated: 'Zero rates',
    pros: 'Simple, fast',
    cons: 'Forward rates can be discontinuous'
  },
  {
    method: 'Linear on Log DF',
    interpolated: 'Log of discount factors',
    pros: 'Continuous forward rates',
    cons: 'Can produce negative forwards'
  },
  {
    method: 'Cubic Spline',
    interpolated: 'Zero rates or log DF',
    pros: 'Smooth curves, continuous derivatives',
    cons: 'Can oscillate, computationally intensive'
  },
  {
    method: 'Hermite Spline',
    interpolated: 'Log DF',
    pros: 'No oscillations, monotonic',
    cons: 'More complex to implement'
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

  ol.construction-steps {
    padding-left: 1.5rem;

    li {
      padding: 0.75rem 0;
      line-height: 1.6;
    }
  }

  code {
    background: var(--surface-ground);
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-family: 'Courier New', monospace;
    font-size: 0.9em;

    &.text-lg {
      font-size: 1em;
      padding: 0.5rem 1rem;
      display: inline-block;
    }
  }
}
</style>
