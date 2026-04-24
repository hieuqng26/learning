export const equityVanillaOptionForm = {
  name: 'Equity Vanilla Option',
  category: 'EQUITY',
  api: 'calculateEquityVanillaOption',
  groups: [
    {
      title: 'Trade Details',
      collapsible: true,
      initiallyCollapsed: false,
      fields: [
        {
          key: 'evaluation_date',
          type: 'date',
          label: 'Evaluation Date',
          required: true,
          defaultValue: new Date('2024-12-31'),
          helpText: 'The date at which the equity vanilla option will be valued'
        },
        {
          key: 'ticker',
          type: 'dropdown',
          label: 'Equity Ticker',
          required: true,
          defaultValue: 'AAPL',
          options: [
            { label: 'AAPL - Apple Inc.', value: 'AAPL' },
            { label: 'SPX - S&P 500', value: 'SPX' }
          ],
          filter: true,
          helpText: 'The equity underlying the option'
        },
        {
          key: 'currency',
          type: 'dropdown',
          label: 'Currency',
          required: true,
          defaultValue: 'USD',
          options: [
            { label: 'USD - US Dollar', value: 'USD' },
            { label: 'EUR - Euro', value: 'EUR' },
            { label: 'JPY - Japanese Yen', value: 'JPY' },
            { label: 'GBP - British Pound', value: 'GBP' }
          ],
          filter: true,
          helpText: 'The currency for pricing and settlement'
        },
        {
          key: 'notional',
          type: 'float',
          label: 'Number of Shares',
          required: true,
          defaultValue: 1000,
          step: 1,
          minFractionDigits: 0,
          maxFractionDigits: 0,
          helpText: 'The number of shares in the option contract'
        },
        {
          key: 'expiry_date',
          type: 'date',
          label: 'Expiry Date',
          required: true,
          defaultValue: new Date('2038-01-03'),
          helpText: 'The expiry date of the option',
          validators: [
            (value, formData) => {
              if (!value || !formData || !formData.evaluation_date) return true
              if (value <= formData.evaluation_date) {
                return 'Expiry date must be after evaluation date'
              }
              return true
            }
          ]
        },
        {
          key: 'calendar',
          type: 'multiselect',
          label: 'Business Day Calendars',
          required: true,
          defaultValue: ['US'],
          options: [
            { label: 'US - United States', value: 'US' },
            { label: 'TARGET - European Central Bank', value: 'TARGET' },
            { label: 'UK - United Kingdom', value: 'UK' },
            { label: 'JP - Japan', value: 'JP' }
          ],
          filter: true,
          maxSelectedLabels: 3,
          selectedItemsLabel: '{0} calendars selected',
          selectionLimit: null,
          helpText: 'The business day calendars used for date adjustments'
        },
        {
          key: 'settlement_tenor',
          type: 'string',
          label: 'Settlement Tenor',
          required: true,
          defaultValue: '2D',
          helpText:
            'The settlement tenor (e.g., 2D for 2 days, 1M for 1 month)',
          validators: [
            (value) => {
              if (!value) return 'Settlement tenor is required'
              const tenorPattern = /^\d+[DWMY]$/i
              if (!tenorPattern.test(value)) {
                return 'Invalid tenor format. Use format like 2D, 1M, 3M, 1Y'
              }
              return true
            }
          ]
        },
        {
          key: 'option_type',
          type: 'dropdown',
          label: 'Option Type',
          required: true,
          defaultValue: 'CALL',
          options: [
            { label: 'Call', value: 'CALL' },
            { label: 'Put', value: 'PUT' }
          ],
          helpText: 'The type of option (Call or Put)'
        },
        {
          key: 'strike',
          type: 'float',
          label: 'Strike Price',
          required: true,
          defaultValue: 160.0,
          min: 0,
          step: 0.01,
          minFractionDigits: 2,
          maxFractionDigits: 4,
          helpText: 'The strike price for the option',
          validators: [
            (value) => {
              if (value <= 0) {
                return 'Strike price must be greater than 0'
              }
              return true
            }
          ]
        },
        {
          key: 'settlement_type',
          type: 'dropdown',
          label: 'Settlement Type',
          required: true,
          defaultValue: 'CashDomestic',
          options: [
            { label: 'Cash Domestic', value: 'CashDomestic' },
            { label: 'Cash Foreign', value: 'CashForeign' },
            { label: 'Physical', value: 'Physical' }
          ],
          helpText: 'The settlement type for the option'
        }
      ]
    },
    {
      title: 'Pricing',
      collapsible: true,
      initiallyCollapsed: false,
      fields: [
        {
          key: 'discounting',
          type: 'dropdown',
          label: 'Discounting Curve',
          required: true,
          defaultValue: 'USD.SOFR.CSA_USD',
          options: [
            { label: 'USD.SOFR.CSA_USD', value: 'USD.SOFR.CSA_USD' },
            { label: 'EUR.ESTR.CSA_USD', value: 'EUR.ESTR.CSA_USD' },
            { label: 'JPY.TONA.CSA_USD', value: 'JPY.TONA.CSA_USD' },
            { label: 'GBP.SONIA.CSA_USD', value: 'GBP.SONIA.CSA_USD' }
          ],
          filter: true,
          helpText: 'The yield curve used for discounting cash flows'
        }
      ]
    },
    {
      title: 'Stress Configuration',
      collapsible: true,
      initiallyCollapsed: true,
      fields: [
        {
          key: 'risk_curve_name',
          type: 'dropdown',
          label: 'Curve to Bump',
          required: false,
          defaultValue: '',
          options: [
            { label: 'None', value: null },
            { label: 'USD.SOFR.CSA_USD', value: 'USD.SOFR.CSA_USD' },
            { label: 'EUR.ESTR.CSA_USD', value: 'EUR.ESTR.CSA_USD' },
            { label: 'JPY.TONA.CSA_USD', value: 'JPY.TONA.CSA_USD' },
            { label: 'GBP.SONIA.CSA_USD', value: 'GBP.SONIA.CSA_USD' }
          ],
          filter: true,
          helpText:
            'Specify which curve to bump for risk analysis. Leave empty to use the discounting curve.'
        },
        {
          key: 'bump_type',
          type: 'dropdown',
          label: 'Bump Type',
          required: false,
          defaultValue: 'Absolute',
          options: [
            { label: 'Absolute', value: 'Absolute' },
            { label: 'Relative', value: 'Relative' }
          ],
          filter: true,
          helpText:
            'How to apply the bump: absolute addition or relative multiplication'
        },
        {
          key: 'bump_points',
          type: 'string',
          label: 'Bump Points (BP)',
          required: false,
          defaultValue: '1,5,10,20,30,50',
          helpText:
            'Comma-separated list of basis points to bump the curve (e.g., 1,5,10,20,30,50)',
          validators: [
            (value) => {
              if (!value) return true
              const points = value.split(',').map((p) => p.trim())
              for (const point of points) {
                if (isNaN(parseFloat(point))) {
                  return 'All bump points must be valid numbers'
                }
                if (parseFloat(point) < 0) {
                  return 'Bump points cannot be negative'
                }
              }
              return true
            }
          ]
        }
      ]
    }
  ]
}
