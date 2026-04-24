<template>
  <div class="doc-section">
    <h1>Financial Products</h1>

    <div class="doc-intro">
      <p>
        This section provides comprehensive documentation for the financial products supported by DeVal2.
        Each product includes detailed descriptions, common use cases, and termsheet specifications.
      </p>
    </div>

    <section class="doc-subsection">
      <h2>Product Categories</h2>
      <p>The system supports various types of financial instruments across different asset classes:</p>

      <div class="grid mt-3">
        <div class="col-12 md:col-6">
          <Card>
            <template #title>
              <div class="flex align-items-center gap-2">
                <i class="pi pi-money-bill text-primary"></i>
                <span>FX Products</span>
              </div>
            </template>
            <template #content>
              <ul>
                <li><strong>FX Options</strong> - Currency options for hedging and speculation</li>
                <li><strong>FX Forwards</strong> - Forward contracts for currency exchange</li>
              </ul>
            </template>
          </Card>
        </div>

        <div class="col-12 md:col-6">
          <Card>
            <template #title>
              <div class="flex align-items-center gap-2">
                <i class="pi pi-chart-line text-primary"></i>
                <span>Interest Rate Products</span>
              </div>
            </template>
            <template #content>
              <ul>
                <li><strong>Interest Rate Swaps (IRS)</strong> - Fixed-floating rate exchanges</li>
                <li><strong>Overnight Index Swaps (OIS)</strong> - Swaps based on overnight rates</li>
                <li><strong>Cross Currency Swaps</strong> - Multi-currency interest rate swaps</li>
              </ul>
            </template>
          </Card>
        </div>
      </div>
    </section>

    <section class="doc-subsection">
      <h2>How to Use This Documentation</h2>
      <p>Each product page includes the following information:</p>

      <div class="mt-3">
        <Panel header="Product Description" :toggleable="true">
          <p>Overview of what the product is, its key characteristics, and how it works.</p>
        </Panel>

        <Panel header="Use Cases" :toggleable="true" class="mt-2">
          <p>Common scenarios where the product is used, including hedging strategies, risk management, and trading applications.</p>
        </Panel>

        <Panel header="Trade Details & Termsheet" :toggleable="true" class="mt-2">
          <p>Detailed specifications of the trade structure, including all required fields, conventions, and examples.</p>
        </Panel>
      </div>
    </section>

    <Message severity="info" class="mt-4">
      <strong>Note:</strong> Select a specific product from the sidebar to view detailed documentation.
    </Message>
  </div>
</template>

<script setup>
import Card from 'primevue/card'
import Panel from 'primevue/panel'
import Message from 'primevue/message'
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
    list-style-type: none;
    padding-left: 0;

    li {
      padding: 0.5rem 0;
      border-bottom: 1px solid var(--surface-border);

      &:last-child {
        border-bottom: none;
      }
    }
  }
}
</style>
