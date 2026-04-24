<template>
  <div class="doc-section">
    <h1>Market Data</h1>

    <div class="doc-intro">
      <p>
        Market data is essential for pricing and risk management of financial derivatives.
        This section covers the different types of market curves, how they are constructed,
        and how they are used in pricing calculations.
      </p>
    </div>

    <section class="doc-subsection">
      <h2>Overview of Market Curves</h2>
      <p>Market curves represent the term structure of prices, rates, or volatilities across different maturities:</p>

      <div class="grid mt-3">
        <div class="col-12 md:col-4">
          <Card class="h-full">
            <template #title>
              <div class="flex align-items-center gap-2">
                <i class="pi pi-chart-line text-primary"></i>
                <span>Yield Curves</span>
              </div>
            </template>
            <template #content>
              <p>Represent interest rates across different maturities for a given currency and credit quality.</p>
              <ul class="compact-list mt-2 text-sm">
                <li>OIS Curves</li>
                <li>Government Bond Curves</li>
                <li>LIBOR/SOFR Curves</li>
                <li>Credit Spread Curves</li>
              </ul>
            </template>
          </Card>
        </div>

        <div class="col-12 md:col-4">
          <Card class="h-full">
            <template #title>
              <div class="flex align-items-center gap-2">
                <i class="pi pi-globe text-primary"></i>
                <span>FX Volatility</span>
              </div>
            </template>
            <template #content>
              <p>Represent implied volatilities for currency options across strikes and maturities.</p>
              <ul class="compact-list mt-2 text-sm">
                <li>Volatility Surfaces</li>
                <li>ATM, Risk Reversal, Butterfly</li>
                <li>Smile and Skew</li>
                <li>Term Structure</li>
              </ul>
            </template>
          </Card>
        </div>

        <div class="col-12 md:col-4">
          <Card class="h-full">
            <template #title>
              <div class="flex align-items-center gap-2">
                <i class="pi pi-percentage text-primary"></i>
                <span>Other Curves</span>
              </div>
            </template>
            <template #content>
              <p>Additional market data used for specific products and risk factors.</p>
              <ul class="compact-list mt-2 text-sm">
                <li>Swaption Volatility</li>
                <li>Cap/Floor Volatility</li>
                <li>Inflation Curves</li>
                <li>Commodity Curves</li>
              </ul>
            </template>
          </Card>
        </div>
      </div>
    </section>

    <section class="doc-subsection">
      <h2>Curve Construction Process</h2>
      <p>Building market curves involves several key steps:</p>

      <Panel header="1. Market Data Collection" :toggleable="true">
        <p>Gather observable market quotes for liquid instruments:</p>
        <ul class="text-sm mt-2">
          <li>Deposit rates for short tenors</li>
          <li>Futures prices for medium tenors</li>
          <li>Swap rates for long tenors</li>
          <li>Bond prices (for government curves)</li>
        </ul>
      </Panel>

      <Panel header="2. Instrument Selection" :toggleable="true" class="mt-2">
        <p>Choose appropriate instruments for each part of the curve:</p>
        <ul class="text-sm mt-2">
          <li><strong>Short end:</strong> Overnight rates, deposits (1D-1M)</li>
          <li><strong>Medium term:</strong> Futures, FRAs (3M-2Y)</li>
          <li><strong>Long end:</strong> Swaps (2Y-50Y)</li>
        </ul>
      </Panel>

      <Panel header="3. Bootstrapping" :toggleable="true" class="mt-2">
        <p>
          Sequential process to solve for discount factors or zero rates at each maturity point,
          ensuring all instruments are priced correctly by the curve.
        </p>
      </Panel>

      <Panel header="4. Interpolation" :toggleable="true" class="mt-2">
        <p>Define methods for calculating rates between observable points:</p>
        <ul class="text-sm mt-2">
          <li>Linear interpolation on rates or discount factors</li>
          <li>Log-linear interpolation on discount factors</li>
          <li>Cubic spline interpolation for smoothness</li>
        </ul>
      </Panel>
    </section>

    <section class="doc-subsection">
      <h2>Use in Pricing</h2>
      <p>Market curves serve multiple purposes in derivative valuation:</p>

      <div class="grid mt-3">
        <div class="col-12 md:col-6">
          <Card class="h-full">
            <template #title>
              <span class="text-sm">Discounting</span>
            </template>
            <template #content>
              <p>Convert future cash flows to present value using discount factors from the appropriate curve.</p>
              <div class="mt-2 p-2" style="background: var(--surface-ground)">
                <code class="text-sm">PV = Cash Flow × Discount Factor(t)</code>
              </div>
            </template>
          </Card>
        </div>

        <div class="col-12 md:col-6">
          <Card class="h-full">
            <template #title>
              <span class="text-sm">Forward Rate Projection</span>
            </template>
            <template #content>
              <p>Calculate expected future interest rates for floating leg cash flows.</p>
              <div class="mt-2 p-2" style="background: var(--surface-ground)">
                <code class="text-sm">Forward Rate = f(DF(t1), DF(t2))</code>
              </div>
            </template>
          </Card>
        </div>

        <div class="col-12 md:col-6">
          <Card class="h-full">
            <template #title>
              <span class="text-sm">Option Pricing</span>
            </template>
            <template #content>
              <p>Use volatility surfaces to price options using models like Black-Scholes.</p>
            </template>
          </Card>
        </div>

        <div class="col-12 md:col-6">
          <Card class="h-full">
            <template #title>
              <span class="text-sm">Risk Calculation</span>
            </template>
            <template #content">
              <p>Compute sensitivities (Greeks) by shocking curve points and revaluing.</p>
            </template>
          </Card>
        </div>
      </div>
    </section>

    <section class="doc-subsection">
      <h2>Key Concepts</h2>

      <DataTable :value="conceptsData" class="mt-3" :paginator="false">
        <Column field="concept" header="Concept" style="width: 25%">
          <template #body="slotProps">
            <strong>{{ slotProps.data.concept }}</strong>
          </template>
        </Column>
        <Column field="description" header="Description"></Column>
      </DataTable>
    </section>

    <Message severity="info" class="mt-4">
      <strong>Note:</strong> Select a specific topic from the sidebar to learn more about yield curves,
      FX volatility surfaces, and pricing methods in detail.
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

const conceptsData = ref([
  {
    concept: 'Discount Factor',
    description: 'Present value of $1 received at time t. DF(t) = 1 / (1 + r(t))^t for zero rates.'
  },
  {
    concept: 'Zero Rate',
    description: 'Interest rate for a zero-coupon bond maturing at time t. Continuously compounded or discrete.'
  },
  {
    concept: 'Forward Rate',
    description: 'Implied future interest rate between two future dates, derived from the yield curve.'
  },
  {
    concept: 'Par Rate',
    description: 'Coupon rate that makes a bond trade at par (price = 100). Used in swap curve construction.'
  },
  {
    concept: 'Dual Curve Framework',
    description: 'Using separate curves for discounting (OIS) and projection (LIBOR/SOFR) post-2008 financial crisis.'
  },
  {
    concept: 'Collateral Curve',
    description: 'Discount curve reflecting the collateral arrangement (OIS for CSA trades, funding curve for uncollateralized).'
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

  code {
    background: var(--surface-ground);
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-family: 'Courier New', monospace;
    font-size: 0.9em;
  }
}
</style>
