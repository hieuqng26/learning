export const fxvanillaoptionForm = {
  name: 'FX Vanilla Option',
  category: 'FX',
  api: 'calculateFXVanillaOption',
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
          helpText: 'The date at which the FX vanilla option will be valued'
        },
        {
          key: 'domestic_currency',
          type: 'dropdown',
          label: 'Domestic Currency',
          required: true,
          defaultValue: 'USD',
          options: [
            { label: 'USD - US Dollar', value: 'USD' },
            { label: 'EUR - Euro', value: 'EUR' },
            { label: 'JPY - Japanese Yen', value: 'JPY' }
          ],
          filter: true,
          helpText: 'The domestic currency (base currency for pricing)'
        },
        {
          key: 'foreign_currency',
          type: 'dropdown',
          label: 'Foreign Currency',
          required: true,
          defaultValue: 'EUR',
          options: [
            { label: 'USD - US Dollar', value: 'USD' },
            { label: 'EUR - Euro', value: 'EUR' },
            { label: 'JPY - Japanese Yen', value: 'JPY' }
          ],
          filter: true,
          helpText: 'The foreign currency underlying the option',
          validators: [
            (value, formData) => {
              if (value === formData?.domestic_currency) {
                return 'Foreign currency must be different from domestic currency'
              }
              return true
            }
          ]
        },
        {
          key: 'notional_currency',
          type: 'dropdown',
          label: 'Notional Currency',
          required: true,
          defaultValue: 'USD',
          options: [
            { label: 'USD - US Dollar', value: 'USD' },
            { label: 'EUR - Euro', value: 'EUR' },
            { label: 'JPY - Japanese Yen', value: 'JPY' }
          ],
          filter: true,
          helpText: 'The currency in which the notional amount is denominated'
        },
        {
          key: 'notional',
          type: 'float',
          label: 'Notional Amount',
          required: true,
          defaultValue: 10000000,
          step: 1000,
          minFractionDigits: 2,
          maxFractionDigits: 2,
          helpText: 'The notional amount of the FX vanilla option'
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
          defaultValue: ['US', 'TARGET'],
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
              // Basic validation for tenor format (e.g., 2D, 1M, 3M, 1Y)
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
          label: 'Strike Rate',
          required: true,
          defaultValue: 1.3,
          min: 0,
          step: 0.0001,
          minFractionDigits: 4,
          maxFractionDigits: 6,
          helpText: 'The strike rate for the option',
          validators: [
            (value) => {
              if (value <= 0) {
                return 'Strike rate must be greater than 0'
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
          key: 'domestic_discounting',
          type: 'dropdown',
          label: 'Domestic Discounting Curve',
          required: true,
          defaultValue: 'USD.SOFR.CSA_USD',
          options: [
            { label: 'USD.SOFR.CSA_USD', value: 'USD.SOFR.CSA_USD' },
            { label: 'EUR.ESTR.CSA_USD', value: 'EUR.ESTR.CSA_USD' },
            { label: 'JPY.TONA.CSA_USD', value: 'JPY.TONA.CSA_USD' }
          ],
          filter: true,
          helpText:
            'The yield curve used for discounting domestic currency cash flows'
        },
        {
          key: 'foreign_discounting',
          type: 'dropdown',
          label: 'Foreign Discounting Curve',
          required: true,
          defaultValue: 'EUR.ESTR.CSA_USD',
          options: [
            { label: 'USD.SOFR.CSA_USD', value: 'USD.SOFR.CSA_USD' },
            { label: 'EUR.ESTR.CSA_USD', value: 'EUR.ESTR.CSA_USD' },
            { label: 'JPY.TONA.CSA_USD', value: 'JPY.TONA.CSA_USD' }
          ],
          filter: true,
          helpText:
            'The yield curve used for discounting foreign currency cash flows'
        },
        {
          key: 'fx_vol_surface',
          type: 'dropdown',
          label: 'FX Volatility Surface',
          required: true,
          defaultValue: 'EURUSD.FXVOLSURFACE',
          options: [
            { label: 'EURUSD.FXVOLSURFACE', value: 'EURUSD.FXVOLSURFACE' },
            { label: 'USDJPY.FXVOLSURFACE', value: 'USDJPY.FXVOLSURFACE' }
          ],
          filter: true,
          helpText: 'The FX volatility surface used for option pricing'
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
            { label: 'JPY.TONA.CSA_USD', value: 'JPY.TONA.CSA_USD' }
          ],
          filter: true,
          helpText:
            'Specify which curve to bump for risk analysis. Leave empty to use the domestic discounting curve.'
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
