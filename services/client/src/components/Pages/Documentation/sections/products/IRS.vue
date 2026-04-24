<template>
  <div class="doc-section">
    <h1>Interest Rate Swap (IRS)</h1>

    <div class="doc-intro">
      <p>
        An Interest Rate Swap (IRS) is a derivative contract in which two parties agree to exchange
        interest rate cash flows based on a specified notional amount. The most common type involves
        exchanging fixed rate payments for floating rate payments in the same currency.
      </p>
    </div>

    <section class="doc-subsection">
      <h2>Product Description</h2>
      <p>Interest Rate Swaps are among the most liquid and widely traded derivatives:</p>
      <ul>
        <li><strong>Notional Principal:</strong> Reference amount for calculating payments (not exchanged)</li>
        <li><strong>Fixed Leg:</strong> One party pays a fixed interest rate</li>
        <li><strong>Floating Leg:</strong> Other party pays a floating rate (e.g., SOFR, EURIBOR)</li>
        <li><strong>Net Settlement:</strong> Only the difference between payments is exchanged</li>
      </ul>

      <h3 class="mt-3">Standard IRS Structure</h3>
      <div class="grid mt-3">
        <div class="col-12 md:col-6">
          <Card class="h-full">
            <template #title>
              <span class="text-sm">Fixed Rate Payer</span>
            </template>
            <template #content>
              <p><strong>Pays:</strong> Fixed rate (e.g., 3.50% annually)</p>
              <p class="mt-2"><strong>Receives:</strong> Floating rate (e.g., 3-month SOFR)</p>
              <p class="text-sm text-color-secondary mt-2">
                Benefits if floating rates rise above the fixed rate
              </p>
            </template>
          </Card>
        </div>
        <div class="col-12 md:col-6">
          <Card class="h-full">
            <template #title>
              <span class="text-sm">Fixed Rate Receiver</span>
            </template>
            <template #content>
              <p><strong>Pays:</strong> Floating rate (e.g., 3-month SOFR)</p>
              <p class="mt-2"><strong>Receives:</strong> Fixed rate (e.g., 3.50% annually)</p>
              <p class="text-sm text-color-secondary mt-2">
                Benefits if floating rates fall below the fixed rate
              </p>
            </template>
          </Card>
        </div>
      </div>

      <h3 class="mt-3">Common Floating Rate Benchmarks</h3>
      <ul>
        <li><strong>USD:</strong> SOFR (Secured Overnight Financing Rate), previously LIBOR</li>
        <li><strong>EUR:</strong> EURIBOR (Euro Interbank Offered Rate), €STR</li>
        <li><strong>GBP:</strong> SONIA (Sterling Overnight Index Average)</li>
        <li><strong>JPY:</strong> TONA (Tokyo Overnight Average Rate)</li>
      </ul>
    </section>

    <section class="doc-subsection">
      <h2>Use Cases</h2>

      <Panel header="Converting Floating to Fixed Rate Debt" :toggleable="true">
        <p>
          <strong>Scenario:</strong> A company has $50M floating rate debt (SOFR + 1.5%) but wants
          to fix its interest costs for budgeting purposes.
        </p>
        <p class="mt-2">
          <strong>Solution:</strong> Enter an IRS to pay fixed and receive floating (SOFR).
          The received floating cancels out the debt's floating payments, leaving a synthetic fixed rate.
        </p>
        <div class="mt-2 p-2" style="background: var(--surface-ground)">
          <p class="text-sm"><strong>Result:</strong></p>
          <ul class="compact-list text-sm">
            <li>Pay on debt: SOFR + 1.5%</li>
            <li>Receive on swap: SOFR</li>
            <li>Pay on swap: 3.50% (fixed)</li>
            <li><strong>Net cost: 5.00% fixed</strong> (3.50% + 1.5%)</li>
          </ul>
        </div>
      </Panel>

      <Panel header="Converting Fixed to Floating Rate Assets" :toggleable="true" class="mt-2">
        <p>
          <strong>Scenario:</strong> An investor holds fixed rate bonds but wants floating rate exposure
          to benefit from rising rates.
        </p>
        <p class="mt-2">
          <strong>Solution:</strong> Enter an IRS to receive fixed (matching bond coupons) and pay floating,
          creating synthetic floating rate asset.
        </p>
      </Panel>

      <Panel header="Interest Rate View" :toggleable="true" class="mt-2">
        <p>
          <strong>Scenario:</strong> A trader believes interest rates will rise over the next 5 years.
        </p>
        <p class="mt-2">
          <strong>Solution:</strong> Pay fixed and receive floating in an IRS. If rates rise as expected,
          the floating receipts will increase while fixed payments remain constant.
        </p>
      </Panel>

      <Panel header="Duration Management" :toggleable="true" class="mt-2">
        <p>
          <strong>Scenario:</strong> A portfolio manager wants to adjust the interest rate duration
          of a bond portfolio without trading the underlying bonds.
        </p>
        <p class="mt-2">
          <strong>Solution:</strong> Use IRS to overlay duration exposure. Receive fixed to increase duration,
          or pay fixed to decrease duration.
        </p>
      </Panel>
    </section>

    <section class="doc-subsection">
      <h2>Trade Details & Termsheet</h2>
      <p>Key fields required for an Interest Rate Swap trade:</p>

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

      <div class="grid mt-3">
        <div class="col-12 md:col-6">
          <Card class="h-full">
            <template #title>
              <span class="text-sm">At Inception</span>
            </template>
            <template #content>
              <p>The fixed rate is set such that the swap has zero value (par swap).</p>
              <ul class="compact-list mt-2">
                <li><strong>Swap Rate:</strong> Fixed rate that makes PV(fixed leg) = PV(floating leg)</li>
                <li>Derived from the forward curve implied by the yield curve</li>
                <li>No upfront payment required</li>
              </ul>
            </template>
          </Card>
        </div>
        <div class="col-12 md:col-6">
          <Card class="h-full">
            <template #title>
              <span class="text-sm">Mark-to-Market</span>
            </template>
            <template #content>
              <p>Value changes as interest rates move:</p>
              <ul class="compact-list mt-2">
                <li><strong>Fixed Leg:</strong> PV of remaining fixed payments using current discount curve</li>
                <li><strong>Floating Leg:</strong> PV using forward rates from current curve</li>
                <li><strong>MTM:</strong> Difference between the two legs' present values</li>
              </ul>
            </template>
          </Card>
        </div>
      </div>

      <h3 class="mt-3">Required Market Data</h3>
      <ul>
        <li><strong>Discount Curve:</strong> For calculating present values (typically OIS curve)</li>
        <li><strong>Forward Curve:</strong> For projecting future floating rate fixings</li>
        <li><strong>Day Count Conventions:</strong> For accurate interest accrual calculations</li>
        <li><strong>Business Day Calendars:</strong> For determining payment dates</li>
      </ul>
    </section>

    <section class="doc-subsection">
      <h2>Key Risk Measures (Greeks)</h2>

      <DataTable :value="greeksData" class="mt-3" :paginator="false">
        <Column field="greek" header="Risk Measure" style="width: 20%">
          <template #body="slotProps">
            <strong>{{ slotProps.data.greek }}</strong>
          </template>
        </Column>
        <Column field="description" header="Description" style="width: 50%"></Column>
        <Column field="interpretation" header="Interpretation" style="width: 30%"></Column>
      </DataTable>
    </section>

    <Message severity="info" class="mt-4">
      <strong>Market Standard:</strong> IRS are typically traded under ISDA (International Swaps and
      Derivatives Association) documentation, which provides standardized legal terms and conditions.
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
    example: 'IRS_001'
  },
  {
    field: 'Currency',
    description: 'Currency of the swap',
    example: 'USD'
  },
  {
    field: 'Notional Amount',
    description: 'Principal amount for interest calculations',
    example: '50,000,000'
  },
  {
    field: 'Fixed Rate',
    description: 'Fixed interest rate',
    example: '3.50%'
  },
  {
    field: 'Floating Index',
    description: 'Reference rate for floating leg',
    example: '3M SOFR'
  },
  {
    field: 'Floating Spread',
    description: 'Spread added to floating index (if any)',
    example: '+0.25%'
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
    example: '2030-01-15'
  },
  {
    field: 'Fixed Leg Frequency',
    description: 'Payment frequency for fixed leg',
    example: 'Semi-Annual'
  },
  {
    field: 'Floating Leg Frequency',
    description: 'Reset and payment frequency for floating leg',
    example: 'Quarterly'
  },
  {
    field: 'Day Count Convention (Fixed)',
    description: 'Day count for fixed leg',
    example: '30/360'
  },
  {
    field: 'Day Count Convention (Floating)',
    description: 'Day count for floating leg',
    example: 'ACT/360'
  },
  {
    field: 'Business Day Convention',
    description: 'Adjustment for non-business days',
    example: 'Modified Following'
  },
  {
    field: 'Payment Delay',
    description: 'Days between fixing and payment',
    example: '2 business days'
  }
])

const greeksData = ref([
  {
    greek: 'DV01 (Dollar Value of 1bp)',
    description: 'Change in swap value for 1 basis point parallel shift in curve',
    interpretation: 'Measures interest rate sensitivity'
  },
  {
    greek: 'Duration',
    description: 'Weighted average time to cash flows',
    interpretation: 'Higher duration = more rate sensitivity'
  },
  {
    greek: 'Convexity',
    description: 'Rate of change of duration as yields change',
    interpretation: 'Measures non-linear price behavior'
  },
  {
    greek: 'Key Rate Duration',
    description: 'Sensitivity to specific points on the yield curve',
    interpretation: 'Shows exposure to curve shape changes'
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
