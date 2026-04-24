<template>
  <div class="doc-section">
    <h1>Pricing Methods</h1>

    <div class="doc-intro">
      <p>
        This section covers the fundamental pricing methodologies used for financial derivatives,
        including discounting approaches, curve selection, and key market conventions that affect
        valuation calculations.
      </p>
    </div>

    <section class="doc-subsection">
      <h2>Fundamental Pricing Principle</h2>
      <p>
        The core principle of derivative pricing is that the present value of a derivative equals
        the expected value of its future cash flows, discounted at appropriate rates:
      </p>

      <div class="mt-3">
        <Card>
          <template #title>Present Value Formula</template>
          <template #content>
            <div class="text-center">
              <code class="text-lg">PV = Σ E[CF_i] × DF(t_i)</code>
            </div>
            <div class="mt-3">
              <p class="text-sm"><strong>Where:</strong></p>
              <ul class="compact-list text-sm text-color-secondary">
                <li>PV = Present Value of the derivative</li>
                <li>E[CF_i] = Expected cash flow at time t_i</li>
                <li>DF(t_i) = Discount factor from time t_i to today</li>
                <li>Σ = Sum over all future cash flow dates</li>
              </ul>
            </div>
          </template>
        </Card>
      </div>
    </section>

    <section class="doc-subsection">
      <h2>Discounting Approaches</h2>

      <Panel header="Single Curve Approach (Pre-2008)" :toggleable="true">
        <p><strong>Historical Method:</strong> Used the same curve for both discounting and projection</p>
        <div class="mt-2 p-2" style="background: var(--surface-ground)">
          <p class="text-sm"><strong>Example:</strong> USD Interest Rate Swap</p>
          <ul class="compact-list text-sm mt-1">
            <li>Discount all cash flows using LIBOR curve</li>
            <li>Project floating LIBOR fixings using same LIBOR curve</li>
          </ul>
        </div>
        <p class="text-sm text-color-secondary mt-2">
          <strong>Note:</strong> This approach is no longer market standard due to basis between funding
          and index rates revealed during the 2008 financial crisis.
        </p>
      </Panel>

      <Panel header="Dual Curve Approach (Post-2008)" :toggleable="true" class="mt-2">
        <p><strong>Modern Standard:</strong> Separate curves for discounting and projection</p>

        <div class="grid mt-3">
          <div class="col-12 md:col-6">
            <Card>
              <template #title>
                <span class="text-sm">Discounting Curve</span>
              </template>
              <template #content>
                <p><strong>Purpose:</strong> Calculate present value of cash flows</p>
                <p class="mt-2"><strong>Typical Choice:</strong></p>
                <ul class="compact-list text-sm mt-1">
                  <li><strong>Collateralized trades:</strong> OIS curve (risk-free rate)</li>
                  <li><strong>Uncollateralized:</strong> Funding curve specific to entity</li>
                </ul>
              </template>
            </Card>
          </div>

          <div class="col-12 md:col-6">
            <Card>
              <template #title>
                <span class="text-sm">Projection Curve</span>
              </template>
              <template #content>
                <p><strong>Purpose:</strong> Project future floating rate fixings</p>
                <p class="mt-2"><strong>Typical Choice:</strong></p>
                <ul class="compact-list text-sm mt-1">
                  <li><strong>USD:</strong> SOFR curve (or legacy LIBOR)</li>
                  <li><strong>EUR:</strong> EURIBOR curve or €STR</li>
                  <li><strong>GBP:</strong> SONIA curve</li>
                </ul>
              </template>
            </Card>
          </div>
        </div>

        <div class="mt-3 p-2" style="background: var(--surface-ground)">
          <p class="text-sm"><strong>Example:</strong> USD Interest Rate Swap (Pay Fixed, Receive 3M SOFR)</p>
          <ul class="compact-list text-sm mt-1">
            <li><strong>Discount:</strong> Both fixed and floating legs using OIS curve</li>
            <li><strong>Project:</strong> Future 3M SOFR fixings using SOFR forward curve</li>
          </ul>
        </div>
      </Panel>
    </section>

    <section class="doc-subsection">
      <h2>Curve Selection by Product</h2>
      <p>Different products require different curve combinations:</p>

      <DataTable :value="curveSelection" class="mt-3" :paginator="false" :scrollable="true" scrollHeight="400px">
        <Column field="product" header="Product" style="width: 25%">
          <template #body="slotProps">
            <strong>{{ slotProps.data.product }}</strong>
          </template>
        </Column>
        <Column field="discount" header="Discount Curve" style="width: 25%"></Column>
        <Column field="projection" header="Projection Curve" style="width: 25%"></Column>
        <Column field="notes" header="Notes" style="width: 25%"></Column>
      </DataTable>
    </section>

    <section class="doc-subsection">
      <h2>Day Count Conventions</h2>
      <p>
        Day count conventions determine how interest accrues between dates.
        Different conventions are used for different currencies and products:
      </p>

      <DataTable :value="dayCountConventions" class="mt-3" :paginator="false">
        <Column field="convention" header="Convention" style="width: 20%">
          <template #body="slotProps">
            <code>{{ slotProps.data.convention }}</code>
          </template>
        </Column>
        <Column field="calculation" header="Calculation Method" style="width: 40%"></Column>
        <Column field="usage" header="Typical Usage" style="width: 40%"></Column>
      </DataTable>
    </section>

    <section class="doc-subsection">
      <h2>Forward Rate Calculation</h2>
      <p>Forward rates are essential for projecting floating rate cash flows:</p>

      <div class="grid mt-3">
        <div class="col-12 md:col-6">
          <Card>
            <template #title>Simple Forward Rate</template>
            <template #content>
              <div class="p-2" style="background: var(--surface-ground)">
                <code>F(t1, t2) = [DF(t1) / DF(t2) - 1] / dcf(t1, t2)</code>
              </div>
              <p class="text-sm text-color-secondary mt-2">
                Where dcf(t1, t2) is the day count fraction between t1 and t2
              </p>
            </template>
          </Card>
        </div>

        <div class="col-12 md:col-6">
          <Card>
            <template #title>Compounded Overnight Rate</template>
            <template #content>
              <div class="p-2" style="background: var(--surface-ground)">
                <code>F_compound = [∏(1 + r_i × d_i) - 1] / dcf</code>
              </div>
              <p class="text-sm text-color-secondary mt-2">
                Used for overnight indices like SOFR, ESTR, SONIA
              </p>
            </template>
          </Card>
        </div>
      </div>
    </section>

    <section class="doc-subsection">
      <h2>Collateral and CSA Impact</h2>
      <p>
        Credit Support Annex (CSA) agreements significantly impact pricing through the choice
        of discount curve:
      </p>

      <Panel header="CSA Discounting" :toggleable="true">
        <p>For trades under CSA with daily collateral posting:</p>
        <ul class="text-sm mt-2">
          <li>Discount using OIS curve (represents overnight collateral rate)</li>
          <li>Nearly risk-free as collateral mitigates counterparty credit risk</li>
          <li>Interest earned/paid on collateral follows overnight index</li>
        </ul>
      </Panel>

      <Panel header="Non-CSA Discounting" :toggleable="true" class="mt-2">
        <p>For uncollateralized trades:</p>
        <ul class="text-sm mt-2">
          <li>Discount using entity's funding curve</li>
          <li>Includes credit risk and funding spread</li>
          <li>Incorporates Credit Valuation Adjustment (CVA)</li>
          <li>Wider spread over OIS curve</li>
        </ul>
      </Panel>
    </section>

    <section class="doc-subsection">
      <h2>Business Day Adjustments</h2>
      <p>Payment dates may fall on weekends or holidays and need to be adjusted:</p>

      <DataTable :value="businessDayConventions" class="mt-3" :paginator="false">
        <Column field="convention" header="Convention" style="width: 30%">
          <template #body="slotProps">
            <strong>{{ slotProps.data.convention }}</strong>
          </template>
        </Column>
        <Column field="description" header="Description"></Column>
      </DataTable>
    </section>

    <section class="doc-subsection">
      <h2>Pricing Workflow Example</h2>
      <p>Step-by-step pricing of a USD Interest Rate Swap (5Y, Pay Fixed 3.5%, Receive 3M SOFR):</p>

      <div class="mt-3">
        <Card>
          <template #content>
            <ol class="pricing-workflow">
              <li>
                <strong>Generate Fixed Leg Cash Flows</strong>
                <p class="text-sm text-color-secondary">
                  Calculate fixed payments: Notional × 3.5% × day count fraction for each period
                </p>
              </li>
              <li>
                <strong>Project Floating Leg Cash Flows</strong>
                <p class="text-sm text-color-secondary">
                  Use SOFR forward curve to project future 3M SOFR fixings for each reset period
                </p>
              </li>
              <li>
                <strong>Discount All Cash Flows</strong>
                <p class="text-sm text-color-secondary">
                  Apply OIS discount factors to both fixed and floating leg cash flows
                </p>
              </li>
              <li>
                <strong>Calculate Net Present Value</strong>
                <p class="text-sm text-color-secondary">
                  NPV = PV(Floating Leg) - PV(Fixed Leg) for fixed payer
                </p>
              </li>
            </ol>
          </template>
        </Card>
      </div>
    </section>

    <Message severity="info" class="mt-4">
      <strong>Best Practice:</strong> Always verify that the curves you're using for pricing
      are appropriate for the product, currency, and collateral arrangement. Incorrect curve
      selection can lead to significant pricing errors.
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

const curveSelection = ref([
  {
    product: 'Interest Rate Swap (IRS)',
    discount: 'OIS (if CSA)',
    projection: 'SOFR / EURIBOR',
    notes: 'Dual curve standard'
  },
  {
    product: 'Overnight Index Swap (OIS)',
    discount: 'OIS',
    projection: 'OIS (same curve)',
    notes: 'Single curve acceptable'
  },
  {
    product: 'Cross Currency Swap',
    discount: 'OIS in each currency',
    projection: 'IBOR/RFR in each currency',
    notes: 'Plus FX forward curve'
  },
  {
    product: 'FX Forward',
    discount: 'OIS in both currencies',
    projection: 'N/A (deterministic)',
    notes: 'Uses FX spot and interest rate differential'
  },
  {
    product: 'FX Option',
    discount: 'OIS in base currency',
    projection: 'OIS in both currencies (for forward)',
    notes: 'Plus FX volatility surface'
  },
  {
    product: 'Swaption',
    discount: 'OIS',
    projection: 'SOFR / EURIBOR',
    notes: 'Plus swaption volatility cube'
  }
])

const dayCountConventions = ref([
  {
    convention: 'ACT/360',
    calculation: 'Actual days / 360',
    usage: 'EUR, JPY money markets; USD floating legs'
  },
  {
    convention: 'ACT/365',
    calculation: 'Actual days / 365',
    usage: 'GBP money markets; some bond markets'
  },
  {
    convention: '30/360',
    calculation: '30 days per month / 360',
    usage: 'USD fixed legs; corporate bonds'
  },
  {
    convention: 'ACT/ACT',
    calculation: 'Actual days / Actual days in year',
    usage: 'Government bonds; some swap fixed legs'
  },
  {
    convention: '30E/360',
    calculation: '30 days per month (European) / 360',
    usage: 'EUR bond market'
  }
])

const businessDayConventions = ref([
  {
    convention: 'Following',
    description: 'If holiday, move to next business day'
  },
  {
    convention: 'Modified Following',
    description: 'Following, unless it crosses month-end, then go to previous business day'
  },
  {
    convention: 'Preceding',
    description: 'If holiday, move to previous business day'
  },
  {
    convention: 'Modified Preceding',
    description: 'Preceding, unless it crosses month-start, then go to next business day'
  },
  {
    convention: 'Unadjusted',
    description: 'No adjustment; payment on the specified date even if holiday'
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

  ol.pricing-workflow {
    list-style-type: none;
    counter-reset: step-counter;
    padding-left: 0;

    li {
      counter-increment: step-counter;
      padding: 1rem;
      margin-bottom: 0.5rem;
      background: var(--surface-ground);
      border-radius: 4px;
      position: relative;
      padding-left: 3rem;

      &::before {
        content: counter(step-counter);
        position: absolute;
        left: 1rem;
        top: 1rem;
        background: var(--primary-color);
        color: white;
        width: 1.5rem;
        height: 1.5rem;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 0.9rem;
      }

      strong {
        display: block;
        margin-bottom: 0.25rem;
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
      display: block;
    }
  }
}
</style>
