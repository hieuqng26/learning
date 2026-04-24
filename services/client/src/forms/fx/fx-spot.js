export const fxspotForm = {
  name: 'FX Spot',
  category: 'FX',
  api: 'calculateFXSpot',
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
          helpText: 'The date at which the FX spot will be valued'
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
            // { label: 'GBP - British Pound', value: 'GBP' },
            { label: 'JPY - Japanese Yen', value: 'JPY' },
            { label: 'IDR - Indonesian Rupiah', value: 'IDR' }
            // { label: 'AUD - Australian Dollar', value: 'AUD' },
            // { label: 'CAD - Canadian Dollar', value: 'CAD' },
            // { label: 'CHF - Swiss Franc', value: 'CHF' },
            // { label: 'NOK - Norwegian Krone', value: 'NOK' },
            // { label: 'SEK - Swedish Krona', value: 'SEK' },
            // { label: 'DKK - Danish Krone', value: 'DKK' }
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
            // { label: 'GBP - British Pound', value: 'GBP' },
            { label: 'JPY - Japanese Yen', value: 'JPY' },
            { label: 'IDR - Indonesian Rupiah', value: 'IDR' }
            // { label: 'AUD - Australian Dollar', value: 'AUD' },
            // { label: 'CAD - Canadian Dollar', value: 'CAD' },
            // { label: 'CHF - Swiss Franc', value: 'CHF' },
            // { label: 'NOK - Norwegian Krone', value: 'NOK' },
            // { label: 'SEK - Swedish Krona', value: 'SEK' },
            // { label: 'DKK - Danish Krone', value: 'DKK' }
          ],
          filter: true,
          helpText: 'The foreign currency to be exchanged',
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
            // { label: 'GBP - British Pound', value: 'GBP' },
            { label: 'JPY - Japanese Yen', value: 'JPY' },
            { label: 'IDR - Indonesian Rupiah', value: 'IDR' }
            // { label: 'AUD - Australian Dollar', value: 'AUD' },
            // { label: 'CAD - Canadian Dollar', value: 'CAD' },
            // { label: 'CHF - Swiss Franc', value: 'CHF' },
            // { label: 'NOK - Norwegian Krone', value: 'NOK' },
            // { label: 'SEK - Swedish Krona', value: 'SEK' },
            // { label: 'DKK - Danish Krone', value: 'DKK' }
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
          helpText: 'The notional amount of the FX spot transaction'
        },
        {
          key: 'settlement_date_or_tenor',
          type: 'date',
          label: 'Settlement Date',
          required: true,
          defaultValue: new Date('2025-01-03'),
          helpText: 'The settlement date of the FX spot (typically T+2)',
          validators: [
            (value, formData) => {
              if (!value || !formData || !formData.evaluation_date) return true
              const evalDate = new Date(formData.evaluation_date)
              const minSettlement = new Date(evalDate)
              minSettlement.setDate(evalDate.getDate() + 1)
              if (value < minSettlement) {
                return 'Settlement date should be after evaluation date (typically T+2 for spot)'
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
            { label: 'JP - Japan', value: 'JP' },
            { label: 'AU - Australia', value: 'AU' },
            { label: 'CA - Canada', value: 'CA' },
            { label: 'CH - Switzerland', value: 'CH' },
            { label: 'NO - Norway', value: 'NO' },
            { label: 'SE - Sweden', value: 'SE' },
            { label: 'DK - Denmark', value: 'DK' }
          ],
          filter: true,
          maxSelectedLabels: 3,
          selectedItemsLabel: '{0} calendars selected',
          selectionLimit: null,
          helpText: 'The business day calendars used for date adjustments'
        },
        {
          key: 'strike',
          type: 'float',
          label: 'Spot Rate',
          required: true,
          defaultValue: 1.1,
          min: 0,
          step: 0.0001,
          minFractionDigits: 4,
          maxFractionDigits: 6,
          helpText: 'The current spot exchange rate',
          validators: [
            (value) => {
              if (value <= 0) {
                return 'Spot rate must be greater than 0'
              }
              return true
            }
          ]
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
            { label: 'JPY.TONA.CSA_USD', value: 'JPY.TONA.CSA_USD' },
            { label: 'IDR.JIBOR.CSA_USD', value: 'IDR.JIBOR.CSA_USD' }
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
            { label: 'JPY.TONA.CSA_USD', value: 'JPY.TONA.CSA_USD' },
            { label: 'IDR.JIBOR.CSA_USD', value: 'IDR.JIBOR.CSA_USD' }
          ],
          filter: true,
          helpText:
            'The yield curve used for discounting foreign currency cash flows'
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
            { label: 'IDR.JIBOR.CSA_USD', value: 'IDR.JIBOR.CSA_USD' }
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
