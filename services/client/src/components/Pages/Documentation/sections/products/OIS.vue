<template>
  <div class="doc-section">
    <h1>Overnight Index Swap (OIS)</h1>

    <div class="doc-intro">
      <p>
        An Overnight Index Swap (OIS) is an interest rate swap where one party pays a fixed rate
        and receives a floating rate based on a published overnight index rate (such as SOFR, ESTR, or SONIA).
        OIS rates are key benchmarks for risk-free rates and discounting.
      </p>
    </div>

    <section class="doc-subsection">
      <h2>Product Description</h2>
      <p>OIS contracts have distinctive characteristics that set them apart from traditional interest rate swaps:</p>
      <ul>
        <li><strong>Overnight Rate:</strong> Floating leg based on daily overnight rates compounded over the period</li>
        <li><strong>No Principal Exchange:</strong> Only net interest payments are exchanged</li>
        <li><strong>Risk-Free Rate:</strong> Considered the closest proxy to a risk-free interest rate</li>
        <li><strong>Discounting Standard:</strong> Widely used for discounting collateralized derivatives</li>
      </ul>

      <h3 class="mt-3">Common Overnight Indices</h3>
      <div class="grid mt-3">
        <div class="col-12 md:col-4">
          <Card class="h-full">
            <template #title>
              <span class="text-sm">USD - SOFR</span>
            </template>
            <template #content>
              <p><strong>Secured Overnight Financing Rate</strong></p>
              <p class="text-sm text-color-secondary mt-2">
                Based on US Treasury repo transactions. Replaced USD LIBOR as the benchmark rate.
              </p>
            </template>
          </Card>
        </div>
        <div class="col-12 md:col-4">
          <Card class="h-full">
            <template #title>
              <span class="text-sm">EUR - €STR (ESTR)</span>
            </template>
            <template #content>
              <p><strong>Euro Short-Term Rate</strong></p>
              <p class="text-sm text-color-secondary mt-2">
                Based on wholesale euro unsecured overnight borrowing costs of eurozone banks.
              </p>
            </template>
          </Card>
        </div>
        <div class="col-12 md:col-4">
          <Card class="h-full">
            <template #title>
              <span class="text-sm">GBP - SONIA</span>
            </template>
            <template #content">
              <p><strong>Sterling Overnight Index Average</strong></p>
              <p class="text-sm text-color-secondary mt-2">
                Reflects average interest rate that banks pay to borrow sterling overnight.
              </p>
            </template>
          </Card>
        </div>
      </div>
    </section>

    <section class="doc-subsection">
      <h2>Use Cases</h2>

      <Panel header="Interest Rate View Expression" :toggleable="true">
        <p>
          <strong>Scenario:</strong> A trader believes short-term interest rates will remain low.
        </p>
        <p class="mt-2">
          <strong>Solution:</strong> Receive fixed in an OIS (pay floating). If rates stay low,
          the fixed payments received will exceed the floating payments paid.
        </p>
      </Panel>

      <Panel header="Hedging Floating Rate Exposure" :toggleable="true" class="mt-2">
        <p>
          <strong>Scenario:</strong> A company has floating rate debt linked to overnight rates.
        </p>
        <p class="mt-2">
          <strong>Solution:</strong> Pay fixed in an OIS to convert floating rate exposure to fixed,
          providing certainty on interest costs.
        </p>
      </Panel>

      <Panel header="Discounting Benchmark" :toggleable="true" class="mt-2">
        <p>
          <strong>Scenario:</strong> Financial institutions need to value collateralized derivatives.
        </p>
        <p class="mt-2">
          <strong>Solution:</strong> OIS curves are the market standard for discounting cash flows
          of collateralized trades, as they represent the risk-free rate.
        </p>
      </Panel>

      <Panel header="Basis Trading" :toggleable="true" class="mt-2">
        <p>
          <strong>Scenario:</strong> Traders want to exploit spreads between different rate benchmarks.
        </p>
        <p class="mt-2">
          <strong>Solution:</strong> Trade the basis between OIS rates and other benchmarks
          (e.g., LIBOR-OIS spread, though LIBOR has been discontinued).
        </p>
      </Panel>
    </section>

    <section class="doc-subsection">
      <h2>Trade Details & Termsheet</h2>
      <p>Key fields required for an OIS trade:</p>

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
      <h2>Floating Rate Calculation</h2>
      <p>The floating leg payment is calculated using compounded overnight rates:</p>

      <Card class="mt-3">
        <template #title>Compound Interest Formula</template>
        <template #content>
          <p class="text-center">
            <code class="text-lg">Floating Rate = ∏(1 + r_i × d_i/360) - 1</code>
          </p>
          <p class="text-sm text-color-secondary mt-3">
            Where:
          </p>
          <ul class="compact-list text-sm text-color-secondary">
            <li>r_i = overnight rate on day i</li>
            <li>d_i = number of days the rate r_i applies (typically 1)</li>
            <li>∏ = product over all days in the interest period</li>
          </ul>
          <p class="text-sm mt-3">
            The compounded rate is then annualized and applied to the notional to calculate the payment.
          </p>
        </template>
      </Card>
    </section>

    <section class="doc-subsection">
      <h2>Pricing & Valuation</h2>

      <div class="grid mt-3">
        <div class="col-12 md:col-6">
          <Card class="h-full">
            <template #title>
              <span class="text-sm">Market Inputs</span>
            </template>
            <template #content>
              <ul class="compact-list">
                <li>OIS discount curve (for present value)</li>
                <li>OIS forward curve (for future floating payments)</li>
                <li>Day count conventions</li>
                <li>Compounding method</li>
              </ul>
            </template>
          </Card>
        </div>
        <div class="col-12 md:col-6">
          <Card class="h-full">
            <template #title>
              <span class="text-sm">Valuation Method</span>
            </template>
            <template #content">
              <ul class="compact-list">
                <li>Fixed leg: PV of all fixed payments</li>
                <li>Floating leg: PV of expected compounded overnight rates</li>
                <li>MTM = PV(floating leg) - PV(fixed leg) for fixed payer</li>
                <li>Curves built from liquid OIS quotes</li>
              </ul>
            </template>
          </Card>
        </div>
      </div>
    </section>

    <Message severity="info" class="mt-4">
      <strong>Market Convention:</strong> OIS trades are typically quoted as the fixed rate
      that makes the swap have zero value at inception. This rate is called the "OIS rate" or "swap rate".
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
    example: 'OIS_001'
  },
  {
    field: 'Currency',
    description: 'Currency of the swap',
    example: 'USD'
  },
  {
    field: 'Notional Amount',
    description: 'Principal amount (not exchanged)',
    example: '10,000,000'
  },
  {
    field: 'Fixed Rate',
    description: 'Fixed interest rate paid/received',
    example: '3.25%'
  },
  {
    field: 'Floating Index',
    description: 'Overnight index reference rate',
    example: 'SOFR'
  },
  {
    field: 'Pay/Receive Fixed',
    description: 'Whether party pays or receives fixed rate',
    example: 'Pay Fixed'
  },
  {
    field: 'Effective Date',
    description: 'Start date of the swap',
    example: '2025-01-15'
  },
  {
    field: 'Maturity Date',
    description: 'End date of the swap',
    example: '2027-01-15'
  },
  {
    field: 'Payment Frequency',
    description: 'How often payments are exchanged',
    example: 'Annual'
  },
  {
    field: 'Day Count Convention',
    description: 'Method for calculating accrued interest',
    example: 'ACT/360'
  },
  {
    field: 'Business Day Convention',
    description: 'How to adjust for non-business days',
    example: 'Modified Following'
  },
  {
    field: 'Compounding Method',
    description: 'How overnight rates are compounded',
    example: 'Compounded in arrears'
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
