<template>
  <div class="doc-section">
    <h1>FX Forward</h1>

    <div class="doc-intro">
      <p>
        An FX Forward (Foreign Exchange Forward) is a binding contract to exchange one currency for another
        at a pre-agreed exchange rate (forward rate) on a specified future date (maturity date).
        Unlike options, forwards are obligations that must be settled.
      </p>
    </div>

    <section class="doc-subsection">
      <h2>Product Description</h2>
      <p>FX Forwards are fundamental currency hedging instruments characterized by:</p>
      <ul>
        <li><strong>Obligation:</strong> Both parties are committed to the exchange</li>
        <li><strong>Customization:</strong> Flexible maturity dates and notional amounts</li>
        <li><strong>Zero Initial Cost:</strong> No upfront premium payment required</li>
        <li><strong>Linear Payoff:</strong> Direct 1:1 relationship with FX rate movements</li>
      </ul>

      <h3 class="mt-3">How It Works</h3>
      <p>
        The forward rate is determined by the spot FX rate adjusted for the interest rate differential
        between the two currencies (covered interest rate parity). This ensures no arbitrage opportunities
        exist between spot and forward markets.
      </p>

      <div class="mt-3">
        <Card>
          <template #title>Forward Rate Formula</template>
          <template #content>
            <p class="text-center">
              <code class="text-lg">Forward Rate = Spot Rate × (1 + r_domestic × T) / (1 + r_foreign × T)</code>
            </p>
            <p class="text-sm text-color-secondary mt-2">
              Where r_domestic and r_foreign are the interest rates, and T is the time to maturity in years.
            </p>
          </template>
        </Card>
      </div>
    </section>

    <section class="doc-subsection">
      <h2>Use Cases</h2>

      <Panel header="Import/Export Hedging" :toggleable="true">
        <p>
          <strong>Scenario:</strong> A US company will pay EUR 500,000 to a European supplier in 6 months.
        </p>
        <p class="mt-2">
          <strong>Solution:</strong> Enter a 6-month EUR/USD forward to lock in the exchange rate today,
          eliminating uncertainty about the USD cost of the payment.
        </p>
      </Panel>

      <Panel header="Investment Hedging" :toggleable="true" class="mt-2">
        <p>
          <strong>Scenario:</strong> An investor holds foreign currency bonds and wants to hedge FX risk
          when converting proceeds back to home currency.
        </p>
        <p class="mt-2">
          <strong>Solution:</strong> Use FX forwards with maturities matching the bond coupon dates and maturity.
        </p>
      </Panel>

      <Panel header="Budget Rate Fixing" :toggleable="true" class="mt-2">
        <p>
          <strong>Scenario:</strong> A company with foreign currency revenues/expenses needs certainty
          for budgeting and financial planning.
        </p>
        <p class="mt-2">
          <strong>Solution:</strong> Lock in forward rates for the budget period to fix cash flows in reporting currency.
        </p>
      </Panel>
    </section>

    <section class="doc-subsection">
      <h2>Trade Details & Termsheet</h2>
      <p>Key fields required for an FX Forward trade:</p>

      <DataTable :value="termsheetFields" class="mt-3" :paginator="false">
        <Column field="field" header="Field" style="width: 25%">
          <template #body="slotProps">
            <strong>{{ slotProps.data.field }}</strong>
          </template>
        </Column>
        <Column field="description" header="Description" style="width: 45%"></Column>
        <Column field="example" header="Example" style="width: 30%">
          <template #body="slotProps">
            <code>{{ slotProps.data.example }}</code>
          </template>
        </Column>
      </DataTable>
    </section>

    <section class="doc-subsection">
      <h2>Pricing & Valuation</h2>

      <div class="grid mt-3">
        <div class="col-12 md:col-6">
          <Card class="h-full">
            <template #title>
              <span class="text-sm">At Inception</span>
            </template>
            <template #content>
              <p>The forward rate is set such that the contract has zero value at inception (no upfront payment).</p>
              <ul class="compact-list mt-2">
                <li>Spot FX rate</li>
                <li>Domestic interest rate curve</li>
                <li>Foreign interest rate curve</li>
                <li>Time to maturity</li>
              </ul>
            </template>
          </Card>
        </div>
        <div class="col-12 md:col-6">
          <Card class="h-full">
            <template #title>
              <span class="text-sm">Mark-to-Market (MTM)</span>
            </template>
            <template #content>
              <p>The value changes as market conditions evolve:</p>
              <ul class="compact-list mt-2">
                <li>Current spot rate movements</li>
                <li>Changes in interest rate curves</li>
                <li>Time decay effect</li>
                <li>Calculated by comparing to new forward rate</li>
              </ul>
            </template>
          </Card>
        </div>
      </div>
    </section>

    <section class="doc-subsection">
      <h2>Key Differences vs. FX Option</h2>

      <DataTable :value="comparisonData" class="mt-3" :paginator="false">
        <Column field="aspect" header="Aspect" style="width: 25%">
          <template #body="slotProps">
            <strong>{{ slotProps.data.aspect }}</strong>
          </template>
        </Column>
        <Column field="forward" header="FX Forward" style="width: 37.5%"></Column>
        <Column field="option" header="FX Option" style="width: 37.5%"></Column>
      </DataTable>
    </section>

    <Message severity="info" class="mt-4">
      <strong>Note:</strong> FX forwards are binding obligations. Both parties must settle at maturity,
      regardless of whether the forward rate is favorable or unfavorable compared to the spot rate.
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

const termsheetFields = ref([
  {
    field: 'Trade ID',
    description: 'Unique identifier for the trade',
    example: 'FX_FWD_001'
  },
  {
    field: 'Currency Pair',
    description: 'Base currency / Quote currency',
    example: 'EURUSD'
  },
  {
    field: 'Notional Amount',
    description: 'Amount in base currency to be exchanged',
    example: '1,000,000 EUR'
  },
  {
    field: 'Forward Rate',
    description: 'Agreed exchange rate for future settlement',
    example: '1.1050'
  },
  {
    field: 'Maturity Date',
    description: 'Date when currencies will be exchanged',
    example: '2025-09-15'
  },
  {
    field: 'Settlement',
    description: 'Deliverable (physical exchange) or Non-Deliverable (NDF)',
    example: 'Deliverable'
  },
  {
    field: 'Buy/Sell',
    description: 'Buy base currency (long) or Sell base currency (short)',
    example: 'Buy'
  },
  {
    field: 'Value Date',
    description: 'Settlement date (typically T+2 from trade date)',
    example: '2025-09-17'
  }
])

const comparisonData = ref([
  {
    aspect: 'Obligation',
    forward: 'Must settle (binding contract)',
    option: 'Right but not obligation'
  },
  {
    aspect: 'Upfront Cost',
    forward: 'Zero (no premium)',
    option: 'Premium payment required'
  },
  {
    aspect: 'Payoff Profile',
    forward: 'Linear (symmetric)',
    option: 'Non-linear (asymmetric)'
  },
  {
    aspect: 'Downside Risk',
    forward: 'Unlimited (if rate moves against you)',
    option: 'Limited to premium paid'
  },
  {
    aspect: 'Upside Potential',
    forward: 'Locked at forward rate (no upside)',
    option: 'Unlimited (can benefit from favorable moves)'
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
