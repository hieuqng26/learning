export const callableFloatingRateBondForm = {
  name: 'Callable Floating Rate Bond',
  category: 'IR',
  api: 'calculateIRCallableFloatingRateBond',
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
          defaultValue: new Date(),
          helpText: 'The date at which the bond will be valued',
          validators: [
            (value) => {
              if (!value) return true
              const today = new Date()
              if (value > today) {
                return 'Evaluation date cannot be in the future'
              }
              return true
            }
          ]
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
            { label: 'GBP - British Pound', value: 'GBP' },
            { label: 'JPY - Japanese Yen', value: 'JPY' },
            { label: 'AUD - Australian Dollar', value: 'AUD' },
            { label: 'CAD - Canadian Dollar', value: 'CAD' },
            { label: 'CHF - Swiss Franc', value: 'CHF' }
          ],
          filter: true,
          helpText: 'The currency of the bond'
        },
        {
          key: 'notional',
          type: 'float',
          label: 'Notional Amount',
          required: true,
          defaultValue: 100000000,
          step: 1000000,
          minFractionDigits: 2,
          maxFractionDigits: 2,
          helpText: 'The notional amount of the bond'
        },
        {
          key: 'start_date',
          type: 'date',
          label: 'Start Date',
          required: true,
          defaultValue: (() => {
            const date = new Date()
            date.setDate(date.getDate() + 3)
            return date
          })(),
          helpText: 'The effective date when the bond starts'
        },
        {
          key: 'bond_tenor',
          type: 'string',
          label: 'Bond Tenor',
          required: true,
          defaultValue: '5Y',
          helpText: 'The tenor/maturity of the bond (e.g., 10Y, 30Y)',
          placeholder: 'e.g., "10Y", "30Y"'
        }
      ]
    },
    {
      title: 'Calendar & Conventions',
      collapsible: true,
      initiallyCollapsed: false,
      fields: [
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
            { label: 'JP - Japan', value: 'JP' },
            { label: 'AU - Australia', value: 'AU' },
            { label: 'CA - Canada', value: 'CA' },
            { label: 'CH - Switzerland', value: 'CH' }
          ],
          filter: true,
          maxSelectedLabels: 3,
          selectedItemsLabel: '{0} calendars selected',
          helpText: 'The business day calendars used for date adjustments'
        },
        {
          key: 'day_count_convention',
          type: 'dropdown',
          label: 'Day Count Convention',
          required: true,
          defaultValue: '30/360',
          options: [
            { label: 'Actual/360', value: 'ACTUAL360' },
            { label: 'Actual/365', value: 'ACTUAL365FIXED' },
            { label: 'Actual/Actual', value: 'ACT/ACT' },
            { label: '30/360', value: '30/360' }
          ],
          filter: true,
          helpText: 'Day count convention for the floating rate calculations'
        },
        {
          key: 'business_day_convention',
          type: 'dropdown',
          label: 'Business Day Convention',
          required: true,
          defaultValue: 'Following',
          options: [
            { label: 'Following', value: 'Following' },
            { label: 'Modified Following', value: 'ModifiedFollowing' },
            { label: 'Preceding', value: 'Preceding' },
            { label: 'Modified Preceding', value: 'ModifiedPreceding' }
          ],
          filter: true,
          helpText:
            'The convention used to adjust dates that fall on non-business days'
        }
      ]
    },
    {
      title: 'Option Terms',
      collapsible: true,
      initiallyCollapsed: false,
      fields: [
        {
          key: 'option_tenors',
          type: 'array',
          arrayType: 'string',
          label: 'Option Tenors',
          required: true,
          defaultValue: ['2Y', '3Y', '4Y'],
          placeholder: 'Enter tenor (e.g., 5Y, 10Y)',
          helpText:
            'Array of option exercise tenors (enter single tenors or comma-separated: 5Y,10Y,15Y)',
          validators: [
            (value) => {
              if (!Array.isArray(value) || value.length === 0) {
                return 'Must contain at least one option tenor'
              }
              const tenorPattern = /^\d+[YMWD]$/i
              if (!value.every((tenor) => tenorPattern.test(tenor.trim()))) {
                return 'All tenors must be in format like "2Y", "6M", "30D"'
              }
              return true
            }
          ]
        },
        {
          key: 'exercise_lag',
          type: 'number',
          label: 'Exercise Lag (Days)',
          required: true,
          defaultValue: 20,
          min: 0,
          helpText:
            'Number of days before option exercise date for notification'
        }
      ]
    },
    {
      title: 'Market Data & Pricing',
      collapsible: true,
      initiallyCollapsed: false,
      fields: [
        {
          key: 'discount_curve_name',
          type: 'dropdown',
          label: 'Discount Curve',
          required: true,
          defaultValue: 'USD.CREDIT.FUNDING',
          options: [
            { label: 'USD.SOFR.CSA_USD', value: 'USD.SOFR.CSA_USD' },
            { label: 'USD.CREDIT.FUNDING', value: 'USD.CREDIT.FUNDING' },
            { label: 'EUR.ESTR.CSA_EUR', value: 'EUR.ESTR.CSA_EUR' },
            { label: 'EUR.CREDIT.FUNDING', value: 'EUR.CREDIT.FUNDING' },
            { label: 'GBP.SONIA.CSA_GBP', value: 'GBP.SONIA.CSA_GBP' },
            { label: 'GBP.CREDIT.FUNDING', value: 'GBP.CREDIT.FUNDING' }
          ],
          filter: true,
          helpText: 'The yield curve used for discounting cash flows'
        },
        {
          key: 'forecast_curve_name',
          type: 'dropdown',
          label: 'Forecast Curve',
          required: true,
          defaultValue: 'USD.SOFR.CSA_USD',
          options: [
            { label: 'USD.SOFR.CSA_USD', value: 'USD.SOFR.CSA_USD' },
            { label: 'USD.CREDIT.FUNDING', value: 'USD.CREDIT.FUNDING' },
            { label: 'EUR.ESTR.CSA_EUR', value: 'EUR.ESTR.CSA_EUR' },
            { label: 'EUR.CREDIT.FUNDING', value: 'EUR.CREDIT.FUNDING' },
            { label: 'GBP.SONIA.CSA_GBP', value: 'GBP.SONIA.CSA_GBP' },
            { label: 'GBP.CREDIT.FUNDING', value: 'GBP.CREDIT.FUNDING' }
          ],
          filter: true,
          helpText: 'The yield curve used for forecasting floating rates'
        },
        {
          key: 'vol_matrix',
          type: 'dropdown',
          label: 'Volatility Matrix',
          required: true,
          defaultValue: 'USD.SOFR.VOLMATRIX',
          options: [
            { label: 'USD.SOFR.VOLMATRIX', value: 'USD.SOFR.VOLMATRIX' },
            { label: 'EUR.ESTR.VOLMATRIX', value: 'EUR.ESTR.VOLMATRIX' },
            { label: 'GBP.SONIA.VOLMATRIX', value: 'GBP.SONIA.VOLMATRIX' }
          ],
          filter: true,
          helpText: 'The volatility matrix for swaption pricing'
        },
        {
          key: 'spread',
          type: 'float',
          label: 'Spread',
          required: true,
          defaultValue: 0.03,
          step: 1,
          minFractionDigits: 2,
          maxFractionDigits: 4,
          helpText: 'The spread over the reference rate'
        },
        {
          key: 'gearing',
          type: 'float',
          label: 'Gearing',
          required: false,
          defaultValue: 1.0,
          step: 0.1,
          min: 0,
          minFractionDigits: 2,
          maxFractionDigits: 4,
          helpText: 'Gearing factor applied to the floating rate (default: 1.0)'
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
            { label: 'USD.CREDIT.FUNDING', value: 'USD.CREDIT.FUNDING' },
            { label: 'EUR.ESTR.CSA_EUR', value: 'EUR.ESTR.CSA_EUR' },
            { label: 'EUR.CREDIT.FUNDING', value: 'EUR.CREDIT.FUNDING' },
            { label: 'GBP.SONIA.CSA_GBP', value: 'GBP.SONIA.CSA_GBP' },
            { label: 'GBP.CREDIT.FUNDING', value: 'GBP.CREDIT.FUNDING' }
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
