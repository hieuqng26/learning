<template>
  <div class="doc-section">
    <h1>Cross Currency Swap</h1>

    <div class="doc-intro">
      <p>
        A Cross Currency Swap (CCS) is an agreement between two parties to exchange interest payments
        and principal amounts denominated in different currencies. It combines the features of an
        interest rate swap with foreign exchange elements.
      </p>
    </div>

    <section class="doc-subsection">
      <h2>Product Description</h2>
      <p>Cross Currency Swaps are complex instruments with the following characteristics:</p>
      <ul>
        <li><strong>Dual Currency:</strong> Involves two different currencies throughout the life of the swap</li>
        <li><strong>Principal Exchange:</strong> Notional amounts are exchanged at inception and maturity</li>
        <li><strong>Interest Payments:</strong> Periodic interest payments in both currencies</li>
        <li><strong>Long Tenor:</strong> Typically medium to long-term (1-30 years)</li>
      </ul>

      <h3 class="mt-3">Cash Flow Structure</h3>
      <div class="grid mt-3">
        <div class="col-12 md:col-4">
          <Card class="h-full">
            <template #title>
              <span class="text-sm">1. Inception</span>
            </template>
            <template #content>
              <p>Exchange of principal amounts at the spot FX rate</p>
              <p class="text-sm text-color-secondary mt-2">
                Party A pays Currency 1<br>
                Party B pays Currency 2
              </p>
            </template>
          </Card>
        </div>
        <div class="col-12 md:col-4">
          <Card class="h-full">
            <template #title>
              <span class="text-sm">2. During Life</span>
            </template>
            <template #content>
              <p>Periodic interest payments in both currencies</p>
              <p class="text-sm text-color-secondary mt-2">
                Party A pays interest in Currency 2<br>
                Party B pays interest in Currency 1
              </p>
            </template>
          </Card>
        </div>
        <div class="col-12 md:col-4">
          <Card class="h-full">
            <template #title>
              <span class="text-sm">3. Maturity</span>
            </template>
            <template #content>
              <p>Re-exchange of principal at the original FX rate</p>
              <p class="text-sm text-color-secondary mt-2">
                Reverse the initial exchange<br>
                Plus final interest payments
              </p>
            </template>
          </Card>
        </div>
      </div>

      <h3 class="mt-3">Common Structures</h3>
      <ul>
        <li><strong>Fixed-Fixed CCS:</strong> Fixed rates in both currencies</li>
        <li><strong>Fixed-Floating CCS:</strong> Fixed rate in one currency, floating in the other</li>
        <li><strong>Floating-Floating CCS:</strong> Floating rates in both currencies (basis swap)</li>
      </ul>
    </section>

    <section class="doc-subsection">
      <h2>Use Cases</h2>

      <Panel header="Funding Arbitrage" :toggleable="true">
        <p>
          <strong>Scenario:</strong> A European company can borrow cheaply in EUR but needs USD financing.
        </p>
        <p class="mt-2">
          <strong>Solution:</strong> Issue EUR bonds and enter a CCS to swap EUR cash flows for USD,
          achieving USD funding at an attractive all-in rate.
        </p>
      </Panel>

      <Panel header="Asset-Liability Management" :toggleable="true" class="mt-2">
        <p>
          <strong>Scenario:</strong> A company has USD revenues but EUR expenses, creating a currency mismatch.
        </p>
        <p class="mt-2">
          <strong>Solution:</strong> Use CCS to convert USD cash flows to EUR, matching asset and liability currencies.
        </p>
      </Panel>

      <Panel header="Foreign Investment Hedging" :toggleable="true" class="mt-2">
        <p>
          <strong>Scenario:</strong> An investor holds foreign currency bonds and wants to eliminate FX risk.
        </p>
        <p class="mt-2">
          <strong>Solution:</strong> Enter a CCS to swap all foreign currency cash flows (coupons and principal)
          back to home currency.
        </p>
      </Panel>
    </section>

    <section class="doc-subsection">
      <h2>Trade Details & Termsheet</h2>
      <p>Key fields required for a Cross Currency Swap trade:</p>

      <DataTable :value="termsheetFields" class="mt-3" :paginator="false" :scrollable="true" scrollHeight="400px">
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
      <p>CCS valuation requires multiple market curves:</p>

      <div class="grid mt-3">
        <div class="col-12 md:col-6">
          <Card class="h-full">
            <template #title>
              <span class="text-sm">Market Inputs</span>
            </template>
            <template #content>
              <ul class="compact-list">
                <li>Spot FX rate</li>
                <li>Domestic currency yield curve</li>
                <li>Foreign currency yield curve</li>
                <li>Cross currency basis spread</li>
                <li>Discount curves for both currencies</li>
              </ul>
            </template>
          </Card>
        </div>
        <div class="col-12 md:col-6">
          <Card class="h-full">
            <template #title>
              <span class="text-sm">Valuation Approach</span>
            </template>
            <template #content>
              <ul class="compact-list">
                <li>Value each leg separately in its own currency</li>
                <li>Convert one leg to the other currency using spot FX</li>
                <li>Calculate the difference (MTM)</li>
                <li>Include basis spread adjustments</li>
              </ul>
            </template>
          </Card>
        </div>
      </div>
    </section>

    <Message severity="warn" class="mt-4">
      <strong>Important:</strong> Cross currency swaps involve both interest rate and FX risk.
      The principal exchange at maturity creates significant FX exposure that must be carefully managed.
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
    example: 'CCS_001'
  },
  {
    field: 'Currency Pair',
    description: 'Two currencies involved in the swap',
    example: 'EUR / USD'
  },
  {
    field: 'Notional (Currency 1)',
    description: 'Principal amount in first currency',
    example: '10,000,000 EUR'
  },
  {
    field: 'Notional (Currency 2)',
    description: 'Principal amount in second currency',
    example: '11,000,000 USD'
  },
  {
    field: 'Initial FX Rate',
    description: 'Exchange rate used for initial principal exchange',
    example: '1.1000'
  },
  {
    field: 'Leg 1 Type',
    description: 'Fixed or Floating interest rate for currency 1',
    example: 'Fixed'
  },
  {
    field: 'Leg 1 Rate/Spread',
    description: 'Fixed rate or floating spread for currency 1',
    example: '2.50%'
  },
  {
    field: 'Leg 2 Type',
    description: 'Fixed or Floating interest rate for currency 2',
    example: 'Floating'
  },
  {
    field: 'Leg 2 Rate/Spread',
    description: 'Fixed rate or floating spread for currency 2',
    example: 'SOFR + 0.50%'
  },
  {
    field: 'Effective Date',
    description: 'Start date of the swap (principal exchange)',
    example: '2025-01-15'
  },
  {
    field: 'Maturity Date',
    description: 'End date of the swap (principal re-exchange)',
    example: '2030-01-15'
  },
  {
    field: 'Payment Frequency (Leg 1)',
    description: 'How often interest is paid on leg 1',
    example: 'Annual'
  },
  {
    field: 'Payment Frequency (Leg 2)',
    description: 'How often interest is paid on leg 2',
    example: 'Quarterly'
  },
  {
    field: 'Day Count Convention',
    description: 'Method for calculating accrued interest',
    example: '30/360, Act/360'
  },
  {
    field: 'Business Day Convention',
    description: 'How to handle payment dates falling on non-business days',
    example: 'Modified Following'
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
