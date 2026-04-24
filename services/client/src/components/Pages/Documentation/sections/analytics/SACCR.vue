<template>
  <div class="doc-section">
    <h1>SA-CCR (Standardized Approach for Counterparty Credit Risk)</h1>

    <div class="doc-intro">
      <p>
        The Standardized Approach for measuring Counterparty Credit Risk (SA-CCR) is a Basel III
        framework methodology for calculating exposure at default (EAD) for derivative transactions.
        It replaced earlier methods (CEM, SM-CCR) to provide a more risk-sensitive approach to
        measuring counterparty credit risk for regulatory capital purposes.
      </p>
    </div>

    <section class="doc-subsection">
      <h2>Overview</h2>

      <div class="grid mt-3">
        <div class="col-12 md:col-6">
          <Card class="h-full">
            <template #title>
              <span class="text-sm">Purpose</span>
            </template>
            <template #content>
              <ul class="compact-list text-sm">
                <li>Calculate Exposure at Default (EAD) for derivatives</li>
                <li>Determine regulatory capital requirements</li>
                <li>Replace Current Exposure Method (CEM)</li>
                <li>More risk-sensitive than previous approaches</li>
              </ul>
            </template>
          </Card>
        </div>

        <div class="col-12 md:col-6">
          <Card class="h-full">
            <template #title>
              <span class="text-sm">Key Features</span>
            </template>
            <template #content>
              <ul class="compact-list text-sm">
                <li>Recognizes netting benefits within netting sets</li>
                <li>Accounts for collateral posted/received</li>
                <li>Hedging recognition across asset classes</li>
                <li>Maturity factor adjustments</li>
              </ul>
            </template>
          </Card>
        </div>
      </div>
    </section>

    <section class="doc-subsection">
      <h2>SA-CCR Formula</h2>

      <div class="mt-3">
        <Card>
          <template #title>Exposure at Default (EAD) Calculation</template>
          <template #content>
            <div class="text-center p-2" style="background: var(--surface-ground)">
              <code class="text-lg">EAD = α × (RC + PFE)</code>
            </div>

            <div class="grid mt-3">
              <div class="col-12 md:col-4">
                <div class="formula-component">
                  <h4 class="text-sm">α (Alpha Factor)</h4>
                  <p class="text-sm text-color-secondary">
                    Regulatory multiplier = 1.4<br>
                    Applied to final exposure amount
                  </p>
                </div>
              </div>

              <div class="col-12 md:col-4">
                <div class="formula-component">
                  <h4 class="text-sm">RC (Replacement Cost)</h4>
                  <p class="text-sm text-color-secondary">
                    Current exposure<br>
                    RC = max(V - C, 0)
                  </p>
                </div>
              </div>

              <div class="col-12 md:col-4">
                <div class="formula-component">
                  <h4 class="text-sm">PFE (Potential Future Exposure)</h4>
                  <p class="text-sm text-color-secondary">
                    Potential future exposure<br>
                    Based on asset class add-ons
                  </p>
                </div>
              </div>
            </div>
          </template>
        </Card>
      </div>
    </section>

    <section class="doc-subsection">
      <h2>Replacement Cost (RC)</h2>

      <Panel header="RC Calculation" :toggleable="true">
        <div class="p-2" style="background: var(--surface-ground)">
          <code>RC = max(V - C, TH + MTA - NICA, 0)</code>
        </div>

        <div class="mt-3">
          <p class="text-sm"><strong>Where:</strong></p>
          <ul class="compact-list text-sm">
            <li><strong>V:</strong> Current market value of the derivative transactions (mark-to-market)</li>
            <li><strong>C:</strong> Net collateral held (haircut-adjusted)</li>
            <li><strong>TH:</strong> Threshold amount before collateral is required</li>
            <li><strong>MTA:</strong> Minimum Transfer Amount</li>
            <li><strong>NICA:</strong> Net Independent Collateral Amount</li>
          </ul>
        </div>

        <div class="mt-3">
          <p class="text-sm text-color-secondary">
            <strong>Interpretation:</strong> RC represents the cost to replace the derivative portfolio
            if the counterparty defaults today, accounting for netting and collateral.
          </p>
        </div>
      </Panel>
    </section>

    <section class="doc-subsection">
      <h2>Potential Future Exposure (PFE)</h2>

      <Panel header="PFE Calculation Steps" :toggleable="true">
        <ol class="calculation-steps">
          <li>
            <strong>Step 1: Calculate Add-Ons by Asset Class</strong>
            <p class="text-sm text-color-secondary">
              For each asset class (IR, FX, Credit, Equity, Commodity), calculate effective notional
              and apply supervisory factors.
            </p>
          </li>
          <li>
            <strong>Step 2: Apply Hedging Recognition</strong>
            <p class="text-sm text-color-secondary">
              Within each asset class, offset positions with opposite signs to recognize hedging.
            </p>
          </li>
          <li>
            <strong>Step 3: Aggregate Across Asset Classes</strong>
            <p class="text-sm text-color-secondary">
              Combine add-ons from different asset classes with correlation factors.
            </p>
          </li>
          <li>
            <strong>Step 4: Apply Multiplier</strong>
            <p class="text-sm text-color-secondary">
              Apply a multiplier that reduces PFE based on overcollateralization.
            </p>
          </li>
        </ol>
      </Panel>

      <Panel header="Multiplier Formula" :toggleable="true" class="mt-2">
        <div class="p-2" style="background: var(--surface-ground)">
          <code>Multiplier = min(1, Floor + (1 - Floor) × exp(V - C) / (2 × (1 - Floor) × AddOn))</code>
        </div>
        <p class="text-sm text-color-secondary mt-2">
          Where Floor = 0.05 (5%). Multiplier reduces PFE when the netting set has a negative
          replacement cost and significant overcollateralization.
        </p>
      </Panel>
    </section>

    <section class="doc-subsection">
      <h2>Asset Class Add-Ons</h2>
      <p>Each asset class has specific supervisory factors and calculation methods:</p>

      <DataTable :value="assetClassAddOns" class="mt-3" :paginator="false" :scrollable="true" scrollHeight="350px">
        <Column field="assetClass" header="Asset Class" style="width: 20%">
          <template #body="slotProps">
            <strong>{{ slotProps.data.assetClass }}</strong>
          </template>
        </Column>
        <Column field="hedgingSets" header="Hedging Sets" style="width: 25%"></Column>
        <Column field="supervisoryFactor" header="Supervisory Factor Range" style="width: 20%"></Column>
        <Column field="maturityBuckets" header="Maturity Buckets" style="width: 35%"></Column>
      </DataTable>
    </section>

    <section class="doc-subsection">
      <h2>Calculation Example</h2>

      <div class="mt-3">
        <Card>
          <template #title>Simple Interest Rate Swap Example</template>
          <template #content>
            <p class="text-sm">
              <strong>Position:</strong> Single 5Y USD interest rate swap, pay fixed 3.0%, receive floating SOFR<br>
              <strong>Notional:</strong> USD 10,000,000<br>
              <strong>Current MTM:</strong> +$50,000 (positive for bank)<br>
              <strong>Collateral:</strong> $30,000 posted by counterparty<br>
              <strong>Maturity:</strong> 5 years
            </p>

            <Divider />

            <p class="text-sm"><strong>Step 1: Calculate Replacement Cost (RC)</strong></p>
            <div class="p-2 mt-1" style="background: var(--surface-ground)">
              <code class="text-sm">
                RC = max(V - C, 0) = max(50,000 - 30,000, 0) = 20,000
              </code>
            </div>

            <p class="text-sm mt-3"><strong>Step 2: Calculate PFE Add-On</strong></p>
            <div class="p-2 mt-1" style="background: var(--surface-ground)">
              <code class="text-sm">
                Effective Notional = Adjusted Notional × Maturity Factor × Supervisory Delta<br>
                Adjusted Notional = 10,000,000 × 1.0 (no trades offset) = 10,000,000<br>
                Supervisory Delta = 1 (linear IR derivative)<br>
                Supervisory Factor (SF) = 0.5% (5-year bucket)<br>
                Add-On = 10,000,000 × 0.005 × 1.0 = 50,000
              </code>
            </div>

            <p class="text-sm mt-3"><strong>Step 3: Calculate PFE with Multiplier</strong></p>
            <div class="p-2 mt-1" style="background: var(--surface-ground)">
              <code class="text-sm">
                Multiplier ≈ 0.95 (simplified, actual calculation more complex)<br>
                PFE = Multiplier × Add-On = 0.95 × 50,000 = 47,500
              </code>
            </div>

            <p class="text-sm mt-3"><strong>Step 4: Calculate EAD</strong></p>
            <div class="p-2 mt-1" style="background: var(--surface-ground)">
              <code class="text-sm">
                EAD = α × (RC + PFE) = 1.4 × (20,000 + 47,500) = 94,500
              </code>
            </div>

            <p class="text-sm text-color-secondary mt-3">
              <strong>Result:</strong> The regulatory exposure for this swap is $94,500, which would be used to
              calculate risk-weighted assets (RWA) and capital requirements.
            </p>
          </template>
        </Card>
      </div>
    </section>

    <section class="doc-subsection">
      <h2>Key Considerations</h2>

      <Panel header="Netting Sets" :toggleable="true">
        <p class="text-sm">
          Trades eligible for netting under a qualifying master agreement (e.g., ISDA) are grouped
          into a netting set. SA-CCR calculations are performed at the netting set level, with
          substantial reduction in exposure through netting benefits.
        </p>
      </Panel>

      <Panel header="Margined vs. Unmargined" :toggleable="true" class="mt-2">
        <ul class="text-sm">
          <li><strong>Margined netting sets:</strong> Significant reduction in RC due to collateral.
            Multiplier can further reduce PFE if overcollateralized.</li>
          <li><strong>Unmargined netting sets:</strong> Higher RC (no collateral offset).
            Multiplier typically = 1 (no reduction).</li>
        </ul>
      </Panel>

      <Panel header="Hedging Recognition" :toggleable="true" class="mt-2">
        <p class="text-sm">
          SA-CCR recognizes hedging within the same hedging set of an asset class. For example,
          offsetting interest rate swaps in the same currency and maturity bucket receive netting
          benefits, reducing the overall add-on.
        </p>
      </Panel>

      <Panel header="Regulatory Reporting" :toggleable="true" class="mt-2">
        <p class="text-sm">
          Banks must calculate and report SA-CCR EAD for all derivative exposures. This feeds into:
        </p>
        <ul class="text-sm mt-2">
          <li>Risk-Weighted Assets (RWA) calculation</li>
          <li>Capital adequacy ratios (CET1, Tier 1, Total Capital)</li>
          <li>Leverage ratio exposure measure</li>
          <li>Large exposure limits</li>
        </ul>
      </Panel>
    </section>

    <Message severity="info" class="mt-4">
      <strong>Regulatory Context:</strong> SA-CCR became effective in January 2017 under Basel III
      and has been adopted by major jurisdictions including the EU (CRR II), US (final rule 2020),
      and many others. It provides a more risk-sensitive and transparent approach to measuring
      counterparty credit risk compared to legacy methods.
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
import Divider from 'primevue/divider'

const assetClassAddOns = ref([
  {
    assetClass: 'Interest Rate (IR)',
    hedgingSets: 'By currency',
    supervisoryFactor: '0.5% - 1.5%',
    maturityBuckets: '< 1Y, 1-5Y, > 5Y'
  },
  {
    assetClass: 'Foreign Exchange (FX)',
    hedgingSets: 'By currency pair',
    supervisoryFactor: '4.0%',
    maturityBuckets: 'Single bucket (all maturities)'
  },
  {
    assetClass: 'Credit (single name)',
    hedgingSets: 'By reference entity & seniority',
    supervisoryFactor: '0.38% - 10.0%',
    maturityBuckets: '< 1Y, 1-5Y, > 5Y (investment grade vs. speculative)'
  },
  {
    assetClass: 'Credit (index)',
    hedgingSets: 'By index',
    supervisoryFactor: '0.38% - 6.0%',
    maturityBuckets: '< 1Y, 1-5Y, > 5Y (investment grade vs. speculative)'
  },
  {
    assetClass: 'Equity (single name)',
    hedgingSets: 'By reference entity',
    supervisoryFactor: '32.0%',
    maturityBuckets: 'Single bucket'
  },
  {
    assetClass: 'Equity (index)',
    hedgingSets: 'By index',
    supervisoryFactor: '20.0%',
    maturityBuckets: 'Single bucket'
  },
  {
    assetClass: 'Commodity',
    hedgingSets: 'By commodity type (4 categories)',
    supervisoryFactor: '18.0% - 40.0%',
    maturityBuckets: '< 1Y, 1-5Y, > 5Y'
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

  .formula-component {
    background: var(--surface-ground);
    padding: 1rem;
    border-radius: 4px;
    height: 100%;
  }

  .calculation-steps {
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
      display: block;
    }
  }
}
</style>
