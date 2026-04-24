<template>
  <div class="doc-section">
    <h1>FX Option</h1>

    <div class="doc-intro">
      <p>
        An FX Option (Foreign Exchange Option) is a derivative contract that gives the buyer the right,
        but not the obligation, to exchange money denominated in one currency into another currency
        at a pre-agreed exchange rate (strike) on or before a specified date (expiry).
      </p>
    </div>

    <section class="doc-subsection">
      <h2>Product Description</h2>
      <p>FX Options are widely used financial instruments that provide:</p>
      <ul>
        <li><strong>Flexibility:</strong> Right but not obligation to exercise</li>
        <li><strong>Hedging:</strong> Protection against adverse currency movements</li>
        <li><strong>Leverage:</strong> Exposure to currency movements with limited upfront cost</li>
        <li><strong>Risk Management:</strong> Downside protection while maintaining upside potential</li>
      </ul>

      <h3 class="mt-3">Option Types</h3>
      <div class="grid mt-2">
        <div class="col-12 md:col-6">
          <Card>
            <template #title>Call Option</template>
            <template #content>
              <p>Gives the holder the right to <strong>buy</strong> the base currency at the strike price.</p>
              <p class="text-sm text-color-secondary mt-2">
                Example: EUR/USD Call option allows buying EUR with USD at the strike rate.
              </p>
            </template>
          </Card>
        </div>
        <div class="col-12 md:col-6">
          <Card>
            <template #title>Put Option</template>
            <template #content>
              <p>Gives the holder the right to <strong>sell</strong> the base currency at the strike price.</p>
              <p class="text-sm text-color-secondary mt-2">
                Example: EUR/USD Put option allows selling EUR for USD at the strike rate.
              </p>
            </template>
          </Card>
        </div>
      </div>

      <h3 class="mt-3">Exercise Styles</h3>
      <ul>
        <li><strong>European:</strong> Can only be exercised on the expiry date</li>
        <li><strong>American:</strong> Can be exercised any time up to and including the expiry date</li>
      </ul>
    </section>

    <section class="doc-subsection">
      <h2>Use Cases</h2>

      <Panel header="Corporate Hedging" :toggleable="true">
        <p>
          A company expecting to receive EUR 1,000,000 in 3 months can buy a EUR/USD Put option
          to protect against EUR depreciation. If EUR weakens, the option gains value offsetting the FX loss.
        </p>
      </Panel>

      <Panel header="Speculation" :toggleable="true" class="mt-2">
        <p>
          Traders use FX options to speculate on currency movements with limited downside risk.
          The maximum loss is limited to the premium paid.
        </p>
      </Panel>

      <Panel header="Portfolio Protection" :toggleable="true" class="mt-2">
        <p>
          Investors with foreign currency exposure use options to protect their portfolio against
          adverse FX movements while retaining upside potential if the currency moves favorably.
        </p>
      </Panel>
    </section>

    <section class="doc-subsection">
      <h2>Trade Details & Termsheet</h2>
      <p>Key fields required for an FX Option trade:</p>

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
      <h2>Pricing Considerations</h2>
      <p>FX Option pricing depends on several factors:</p>

      <div class="grid mt-3">
        <div class="col-12 md:col-4">
          <Card class="h-full">
            <template #title>
              <span class="text-sm">Market Inputs</span>
            </template>
            <template #content>
              <ul class="compact-list">
                <li>Spot FX rate</li>
                <li>Strike price</li>
                <li>Time to expiry</li>
                <li>Volatility</li>
              </ul>
            </template>
          </Card>
        </div>
        <div class="col-12 md:col-4">
          <Card class="h-full">
            <template #title>
              <span class="text-sm">Curve Inputs</span>
            </template>
            <template #content>
              <ul class="compact-list">
                <li>Domestic interest rate curve</li>
                <li>Foreign interest rate curve</li>
              </ul>
            </template>
          </Card>
        </div>
        <div class="col-12 md:col-4">
          <Card class="h-full">
            <template #title>
              <span class="text-sm">Pricing Model</span>
            </template>
            <template #content>
              <ul class="compact-list">
                <li>Black-Scholes (European)</li>
                <li>Garman-Kohlhagen (FX specific)</li>
                <li>Binomial/Trinomial (American)</li>
              </ul>
            </template>
          </Card>
        </div>
      </div>
    </section>

    <Message severity="warn" class="mt-4">
      <strong>Market Convention:</strong> FX options are typically quoted in terms of volatility.
      The premium is calculated based on this volatility input and other market parameters.
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
    example: 'FX_OPT_001'
  },
  {
    field: 'Currency Pair',
    description: 'Base currency / Quote currency (e.g., EUR/USD)',
    example: 'EURUSD'
  },
  {
    field: 'Option Type',
    description: 'Call or Put option',
    example: 'Call'
  },
  {
    field: 'Exercise Style',
    description: 'European or American exercise',
    example: 'European'
  },
  {
    field: 'Notional Amount',
    description: 'Nominal amount in base currency',
    example: '1,000,000 EUR'
  },
  {
    field: 'Strike Price',
    description: 'Exchange rate at which option can be exercised',
    example: '1.1000'
  },
  {
    field: 'Expiry Date',
    description: 'Date when the option expires',
    example: '2025-06-15'
  },
  {
    field: 'Premium',
    description: 'Cost of the option (paid upfront)',
    example: '25,000 USD'
  },
  {
    field: 'Premium Currency',
    description: 'Currency in which premium is paid',
    example: 'USD'
  },
  {
    field: 'Settlement',
    description: 'Cash settled or Physical delivery',
    example: 'Cash'
  },
  {
    field: 'Buy/Sell',
    description: 'Long (buy) or Short (sell) position',
    example: 'Buy'
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
  }
}
</style>
