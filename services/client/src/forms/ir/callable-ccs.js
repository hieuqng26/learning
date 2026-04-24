export const callableCCSForm = {
  name: 'Callable Cross Currency Swap',
  category: 'IR',
  api: 'calculateIRCallableCCS',
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
          defaultValue: new Date(), // '2024-12-31'
          helpText: 'The date at which the swap will be valued',
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
          key: 'start_date',
          type: 'date',
          label: 'Start Date',
          required: true,
          defaultValue: (() => {
            const date = new Date()
            date.setDate(date.getDate() + 3)
            return date
          })(), // '2021-06-09'
          helpText: 'The effective date when the swap begins'
        },
        {
          key: 'end_date',
          type: 'date',
          label: 'Maturity Date',
          required: true,
          defaultValue: (() => {
            const startDate = new Date()
            startDate.setDate(startDate.getDate() + 3)
            const endDate = new Date(startDate)
            endDate.setFullYear(endDate.getFullYear() + 45)
            return endDate
          })(), // '2066-06-09'
          helpText: 'The date when the swap matures',
          validators: [
            (value, formData) => {
              if (!value || !formData || !formData.start_date) return true
              if (value <= formData.start_date) {
                return 'Maturity date must be after start date'
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
          defaultValue: ['TARGET', 'US', 'UK'],
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
        },
        {
          key: 'termination_business_day_convention',
          type: 'dropdown',
          label: 'Termination Business Day Convention',
          required: true,
          defaultValue: 'Following',
          options: [
            { label: 'Following', value: 'Following' },
            { label: 'Modified Following', value: 'ModifiedFollowing' },
            { label: 'Preceding', value: 'Preceding' },
            { label: 'Modified Preceding', value: 'ModifiedPreceding' }
          ],
          filter: true,
          helpText: 'The convention for adjusting termination dates'
        },
        {
          key: 'settlement_lag',
          type: 'number',
          label: 'Settlement Lag (Days)',
          required: true,
          defaultValue: 2,
          min: 0,
          helpText:
            'Number of business days between trade date and settlement date'
        }
      ]
    },
    {
      title: 'Domestic Leg (Currency 1)',
      collapsible: true,
      initiallyCollapsed: false,
      fields: [
        {
          key: 'currency1',
          type: 'dropdown',
          label: 'Currency 1',
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
          helpText: 'The first currency of the cross-currency swap'
        },
        {
          key: 'notionals1',
          type: 'array',
          arrayType: 'number',
          label: 'Notionals 1',
          required: true,
          defaultValue: [73440000.0],
          placeholder: 'Enter notional amount',
          helpText:
            'Array of notional amounts for currency 1 (enter single values or comma-separated: 100000,200000,300000)',
          validators: [
            // (value) => {
            //   if (!Array.isArray(value) || value.length === 0) {
            //     return 'Must contain at least one notional amount'
            //   }
            //   if (!value.every((n) => typeof n === 'number' && n > 0)) {
            //     return 'All notionals must be positive numbers'
            //   }
            //   return true
            // }
          ]
        },
        {
          key: 'day_count_convention1',
          type: 'dropdown',
          label: 'Day Count Convention 1',
          required: true,
          defaultValue: 'ACTUAL360',
          options: [
            { label: 'Actual/360', value: 'ACTUAL360' },
            { label: 'Actual/365', value: 'ACTUAL365FIXED' },
            { label: 'Actual/Actual', value: 'ACT/ACT' },
            { label: '30/360', value: '30/360' }
          ],
          filter: true,
          helpText: 'Day count convention for currency 1 leg'
        },
        {
          key: 'frequency1',
          type: 'string',
          label: 'Payment Frequency 1',
          required: true,
          defaultValue: '6M',
          helpText: 'Payment frequency for currency 1 leg',
          placeholder: 'e.g., "6M", "1Y"'
        },
        {
          key: 'spread_or_fixed_rate1',
          type: 'float',
          label: 'Spread or Fixed Rate 1',
          required: true,
          defaultValue: 0.004,
          step: 0.01,
          minFractionDigits: 4,
          maxFractionDigits: 6,
          helpText:
            'Spread (for floating) or fixed rate (for fixed) in decimal form'
        },
        {
          key: 'final_notional1',
          type: 'float',
          label: 'Final Notional 1',
          required: true,
          defaultValue: 134038704.55,
          step: 1000000,
          minFractionDigits: 2,
          maxFractionDigits: 2,
          helpText: 'Final notional amount for currency 1'
        }
      ]
    },
    {
      title: 'Foreign Leg (Currency 2)',
      collapsible: true,
      initiallyCollapsed: false,
      fields: [
        {
          key: 'currency2',
          type: 'dropdown',
          label: 'Currency 2',
          required: true,
          defaultValue: 'EUR',
          options: [
            { label: 'EUR - Euro', value: 'EUR' },
            { label: 'USD - US Dollar', value: 'USD' },
            { label: 'GBP - British Pound', value: 'GBP' },
            { label: 'JPY - Japanese Yen', value: 'JPY' },
            { label: 'AUD - Australian Dollar', value: 'AUD' },
            { label: 'CAD - Canadian Dollar', value: 'CAD' },
            { label: 'CHF - Swiss Franc', value: 'CHF' }
          ],
          filter: true,
          helpText: 'The second currency of the cross-currency swap'
        },
        {
          key: 'notionals2',
          type: 'array',
          arrayType: 'number',
          label: 'Notionals 2',
          required: true,
          defaultValue: [60000000.0],
          placeholder: 'Enter notional amount',
          helpText:
            'Array of notional amounts for currency 2 (enter single values or comma-separated)',
          min: 0,
          validators: [
            // (value) => {
            //   if (!Array.isArray(value) || value.length === 0) {
            //     return 'Must contain at least one notional amount'
            //   }
            //   if (!value.every((n) => typeof n === 'number' && n > 0)) {
            //     return 'All notionals must be positive numbers'
            //   }
            //   return true
            // }
          ]
        },
        {
          key: 'day_count_convention2',
          type: 'dropdown',
          label: 'Day Count Convention 2',
          required: true,
          defaultValue: '30/360',
          options: [
            { label: 'Actual/360', value: 'ACTUAL360' },
            { label: 'Actual/365', value: 'ACTUAL365FIXED' },
            { label: 'Actual/Actual', value: 'ACT/ACT' },
            { label: '30/360', value: '30/360' }
          ],
          filter: true,
          helpText: 'Day count convention for currency 2 leg'
        },
        {
          key: 'frequency2',
          type: 'string',
          label: 'Payment Frequency 2',
          required: true,
          defaultValue: '12M',
          helpText: 'Payment frequency for currency 2 leg',
          placeholder: 'e.g., "6M", "1Y"'
        },
        {
          key: 'spread_or_fixed_rate2',
          type: 'float',
          label: 'Spread or Fixed Rate 2',
          required: true,
          defaultValue: 0,
          minFractionDigits: 4,
          maxFractionDigits: 6,
          helpText:
            'Spread (for floating) or fixed rate (for fixed) in decimal form'
        },
        {
          key: 'final_notional2',
          type: 'float',
          label: 'Final Notional 2',
          required: true,
          defaultValue: 109508745.55,
          minFractionDigits: 2,
          maxFractionDigits: 2,
          helpText: 'Final notional amount for currency 2'
        }
      ]
    },
    {
      title: 'Exchange & Option Terms',
      collapsible: true,
      initiallyCollapsed: true,
      fields: [
        {
          key: 'redemption_notionals1',
          type: 'array',
          arrayType: 'number',
          label: 'Redemption Notionals 1',
          required: false,
          defaultValue: [89749461.78],
          placeholder: 'Enter redemption amount',
          helpText: 'Array of redemption amounts for currency 1',
          min: 0,
          validators: [
            // (value) => {
            //   if (!Array.isArray(value) || value.length === 0) {
            //     return 'Must contain at least one redemption amount'
            //   }
            //   if (!value.every((n) => typeof n === 'number' && n > 0)) {
            //     return 'All redemption amounts must be positive numbers'
            //   }
            //   return true
            // }
          ]
        },
        {
          key: 'redemption_notionals2',
          type: 'array',
          arrayType: 'number',
          label: 'Redemption Notionals 2',
          required: false,
          defaultValue: [73324723.68],
          placeholder: 'Enter redemption amount',
          helpText: 'Array of redemption amounts for currency 2',
          min: 0,
          validators: [
            // (value) => {
            //   if (!Array.isArray(value) || value.length === 0) {
            //     return 'Must contain at least one redemption amount'
            //   }
            //   if (!value.every((n) => typeof n === 'number' && n > 0)) {
            //     return 'All redemption amounts must be positive numbers'
            //   }
            //   return true
            // }
          ]
        },
        {
          key: 'interim_exchange_notionals1',
          type: 'array',
          arrayType: 'number',
          label: 'Interim Exchange Notionals 1',
          required: false,
          defaultValue: [0],
          placeholder: 'Enter interim exchange amount',
          helpText: 'Array of interim exchange amounts for currency 1',
          min: 0,
          validators: [
            // (value) => {
            //   if (!Array.isArray(value) || value.length === 0) {
            //     return 'Must contain at least one interim exchange amount'
            //   }
            //   if (!value.every((n) => typeof n === 'number' && n > 0)) {
            //     return 'All interim exchange amounts must be positive numbers'
            //   }
            //   return true
            // }
          ]
        },
        {
          key: 'interim_exchange_notionals2',
          type: 'array',
          arrayType: 'number',
          label: 'Interim Exchange Notionals 2',
          required: false,
          defaultValue: [0],
          placeholder: 'Enter interim exchange amount',
          helpText: 'Array of interim exchange amounts for currency 2',
          min: 0,
          validators: [
            // (value) => {
            //   if (!Array.isArray(value) || value.length === 0) {
            //     return 'Must contain at least one interim exchange amount'
            //   }
            //   if (!value.every((n) => typeof n === 'number' && n > 0)) {
            //     return 'All interim exchange amounts must be positive numbers'
            //   }
            //   return true
            // }
          ]
        },
        {
          key: 'option_tenors',
          type: 'array',
          arrayType: 'string',
          label: 'Option Tenors',
          required: false,
          defaultValue: ['15Y'],
          placeholder: 'Enter tenor (e.g., 2Y, 3Y)',
          helpText:
            'Array of option exercise tenors (enter single tenors or comma-separated: 2Y,3Y,5Y)',
          validators: [
            // (value) => {
            //   if (!Array.isArray(value) || value.length === 0) {
            //     return 'Must contain at least one option tenor'
            //   }
            //   const tenorPattern = /^\d+[YMWD]$/i
            //   if (!value.every((tenor) => tenorPattern.test(tenor.trim()))) {
            //     return 'All tenors must be in format like "2Y", "6M", "30D"'
            //   }
            //   return true
            // }
          ]
        },
        {
          key: 'exercise_lag',
          type: 'number',
          label: 'Exercise Lag (Days)',
          required: false,
          defaultValue: 20,
          min: 0,
          helpText:
            'Number of days before option exercise date for notification'
        },
        {
          key: 'notional_exchange',
          type: 'boolean',
          label: 'Notional Exchange',
          required: true,
          defaultValue: true,
          helpText: 'Whether to exchange notional amounts'
        },
        {
          key: 'interim_exchange',
          type: 'boolean',
          label: 'Interim Exchange',
          required: true,
          defaultValue: false,
          helpText: 'Whether to exchange interim amounts'
        },
        {
          key: 'notional_reset',
          type: 'boolean',
          label: 'Notional Reset',
          required: true,
          defaultValue: false,
          helpText: 'Whether notional amounts reset'
        }
      ],
      validators: [
        (formData) => {
          if (formData.currency1 === formData.currency2) {
            return 'Currency 1 and Currency 2 must be different'
          }
          return true
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
            { label: 'GBP.CREDIT.FUNDING', value: 'GBP.CREDIT.FUNDING' },
            { label: 'PLN.WIRON.CSA_PLN', value: 'PLN.WIRON.CSA_PLN' },
            { label: 'PLN.CREDIT.FUNDING', value: 'PLN.CREDIT.FUNDING' },
            { label: 'IDR.JIBOR.CSA_USD', value: 'IDR.JIBOR.CSA_USD' },
            { label: 'IDR.CREDIT.USDFUNDING', value: 'IDR.CREDIT.USDFUNDING' }
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
