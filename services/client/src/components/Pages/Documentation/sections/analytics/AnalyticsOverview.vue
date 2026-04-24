<template>
  <div class="doc-section">
    <h1>Analytics</h1>

    <div class="doc-intro">
      <p>
        Analytics tools provide critical insights into the risk profile and capital requirements
        of derivative portfolios. This section covers risk sensitivity measures (Greeks) and
        regulatory capital calculations including SA-CCR methodology.
      </p>
    </div>

    <section class="doc-subsection">
      <h2>Analytics Categories</h2>

      <div class="grid mt-3">
        <div class="col-12 md:col-6">
          <Card class="h-full">
            <template #title>
              <div class="flex align-items-center gap-2">
                <i class="pi pi-chart-bar text-primary"></i>
                <span>Risk Sensitivity</span>
              </div>
            </template>
            <template #content>
              <p>Measure how portfolio value changes with market factor movements:</p>
              <ul class="compact-list mt-2 text-sm">
                <li><strong>Greeks:</strong> Delta, Gamma, Vega, Rho, Theta</li>
                <li><strong>Scenario Analysis:</strong> Stress testing under various scenarios</li>
                <li><strong>VaR:</strong> Value at Risk calculations</li>
                <li><strong>PnL Attribution:</strong> Explain daily profit and loss</li>
              </ul>
            </template>
          </Card>
        </div>

        <div class="col-12 md:col-6">
          <Card class="h-full">
            <template #title>
              <div class="flex align-items-center gap-2">
                <i class="pi pi-shield text-primary"></i>
                <span>Capital & Regulatory</span>
              </div>
            </template>
            <template #content>
              <p>Calculate regulatory capital requirements:</p>
              <ul class="compact-list mt-2 text-sm">
                <li><strong>SA-CCR:</strong> Standardized Approach for Counterparty Credit Risk</li>
                <li><strong>CVA:</strong> Credit Valuation Adjustment</li>
                <li><strong>Initial Margin:</strong> SIMM (Standard Initial Margin Model)</li>
                <li><strong>Exposure:</strong> EE, PFE, EPE calculations</li>
              </ul>
            </template>
          </Card>
        </div>
      </div>
    </section>

    <section class="doc-subsection">
      <h2>Why Analytics Matter</h2>

      <Panel header="Risk Management" :toggleable="true">
        <p>Understanding and quantifying risk exposure is essential for:</p>
        <ul class="text-sm mt-2">
          <li>Portfolio hedging decisions</li>
          <li>Setting risk limits and monitoring compliance</li>
          <li>Identifying concentration risks</li>
          <li>Optimizing risk-return profiles</li>
        </ul>
      </Panel>

      <Panel header="Regulatory Compliance" :toggleable="true" class="mt-2">
        <p>Financial institutions must comply with regulations requiring:</p>
        <ul class="text-sm mt-2">
          <li>Capital adequacy assessments (Basel III/IV)</li>
          <li>Counterparty credit risk calculations (SA-CCR)</li>
          <li>Margin requirements for uncleared derivatives</li>
          <li>Stress testing and scenario analysis</li>
        </ul>
      </Panel>

      <Panel header="Performance Attribution" :toggleable="true" class="mt-2">
        <p>Analytics help explain trading performance:</p>
        <ul class="text-sm mt-2">
          <li>Decompose P&L by risk factor (rates, FX, vol, etc.)</li>
          <li>Identify profitable and loss-making positions</li>
          <li>Validate trading models and assumptions</li>
          <li>Support performance reporting to management</li>
        </ul>
      </Panel>
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

    <section class="doc-subsection">
      <h2>Analytics Workflow</h2>

      <div class="mt-3">
        <Card>
          <template #content>
            <div class="grid">
              <div class="col-12 md:col-3">
                <div class="workflow-step">
                  <div class="workflow-number">1</div>
                  <h4>Data Collection</h4>
                  <p class="text-sm text-color-secondary">
                    Gather portfolio positions, market data, and model parameters
                  </p>
                </div>
              </div>
              <div class="col-12 md:col-3">
                <div class="workflow-step">
                  <div class="workflow-number">2</div>
                  <h4>Valuation</h4>
                  <p class="text-sm text-color-secondary">
                    Price all positions using appropriate models and curves
                  </p>
                </div>
              </div>
              <div class="col-12 md:col-3">
                <div class="workflow-step">
                  <div class="workflow-number">3</div>
                  <h4>Risk Calculation</h4>
                  <p class="text-sm text-color-secondary">
                    Compute sensitivities by shocking market factors and revaluing
                  </p>
                </div>
              </div>
              <div class="col-12 md:col-3">
                <div class="workflow-step">
                  <div class="workflow-number">4</div>
                  <h4>Reporting</h4>
                  <p class="text-sm text-color-secondary">
                    Aggregate, analyze, and report risk metrics to stakeholders
                  </p>
                </div>
              </div>
            </div>
          </template>
        </Card>
      </div>
    </section>

    <section class="doc-subsection">
      <h2>Analytic Types Comparison</h2>

      <DataTable :value="analyticTypes" class="mt-3" :paginator="false">
        <Column field="type" header="Analytic Type" style="width: 20%">
          <template #body="slotProps">
            <strong>{{ slotProps.data.type }}</strong>
          </template>
        </Column>
        <Column field="purpose" header="Primary Purpose" style="width: 30%"></Column>
        <Column field="frequency" header="Calculation Frequency" style="width: 25%"></Column>
        <Column field="users" header="Primary Users" style="width: 25%"></Column>
      </DataTable>
    </section>

    <Message severity="info" class="mt-4">
      <strong>Note:</strong> Select a specific topic from the sidebar to learn more about
      risk sensitivity measures and SA-CCR methodology in detail.
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
    concept: 'Greeks',
    description: 'First and second-order partial derivatives of portfolio value with respect to market risk factors (spot, vol, rates, time).'
  },
  {
    concept: 'Scenario Analysis',
    description: 'Revaluation of portfolio under hypothetical market scenarios (parallel shifts, historical stress events, custom scenarios).'
  },
  {
    concept: 'VaR (Value at Risk)',
    description: 'Maximum expected loss over a given time horizon at a specified confidence level (e.g., 99% VaR).'
  },
  {
    concept: 'CVA (Credit Valuation Adjustment)',
    description: 'Market value of counterparty credit risk. Adjusts derivative value for probability of counterparty default.'
  },
  {
    concept: 'Exposure',
    description: 'Potential future exposure to a counterparty. Key metrics: Expected Exposure (EE), Potential Future Exposure (PFE).'
  },
  {
    concept: 'SA-CCR',
    description: 'Standardized Approach for measuring Counterparty Credit Risk exposure for capital requirements (Basel III framework).'
  }
])

const analyticTypes = ref([
  {
    type: 'Greeks',
    purpose: 'Manage market risk, hedge portfolios',
    frequency: 'Real-time to daily',
    users: 'Traders, Risk Managers'
  },
  {
    type: 'Scenario Analysis',
    purpose: 'Stress testing, what-if analysis',
    frequency: 'Daily to weekly',
    users: 'Risk Managers, Senior Management'
  },
  {
    type: 'VaR',
    purpose: 'Quantify potential losses',
    frequency: 'Daily',
    users: 'Risk Managers, Regulators'
  },
  {
    type: 'SA-CCR',
    purpose: 'Regulatory capital calculation',
    frequency: 'Daily to monthly',
    users: 'Risk, Finance, Regulators'
  },
  {
    type: 'CVA',
    purpose: 'Price counterparty credit risk',
    frequency: 'Daily',
    users: 'CVA Desk, Risk Managers'
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

  .workflow-step {
    text-align: center;
    padding: 1rem;

    .workflow-number {
      width: 3rem;
      height: 3rem;
      background: var(--primary-color);
      color: white;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.5rem;
      font-weight: bold;
      margin: 0 auto 1rem auto;
    }

    h4 {
      margin-bottom: 0.5rem;
      color: var(--text-color);
    }
  }
}
</style>
