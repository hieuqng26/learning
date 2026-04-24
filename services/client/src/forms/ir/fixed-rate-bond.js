export const fixedRateBondForm = {
  name: 'Fixed Rate Bond',
  category: 'IR',
  api: 'calculateIRFixedRateBond',
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
          defaultValue: 'PLN',
          options: [
            { label: 'USD - US Dollar', value: 'USD' },
            { label: 'EUR - Euro', value: 'EUR' },
            { label: 'GBP - British Pound', value: 'GBP' },
            { label: 'JPY - Japanese Yen', value: 'JPY' },
            { label: 'AUD - Australian Dollar', value: 'AUD' },
            { label: 'CAD - Canadian Dollar', value: 'CAD' },
            { label: 'CHF - Swiss Franc', value: 'CHF' },
            { label: 'PLN - Polish Zloty', value: 'PLN' },
            { label: 'IDR - Indonesian Rupiah', value: 'IDR' }
          ],
          filter: true,
          helpText: 'The currency in which the bond is denominated'
        },
        {
          key: 'notional',
          type: 'float',
          label: 'Notional Amount',
          required: true,
          defaultValue: 750000000,
          step: 1000,
          minFractionDigits: 2,
          maxFractionDigits: 2,
          helpText: 'The face value or principal amount of the bond',
          validators: []
        },
        {
          key: 'start_date',
          type: 'date',
          label: 'Start Date',
          required: true,
          defaultValue: new Date('2024-02-03'),
          helpText: 'The effective date when the bond starts accruing interest'
        },
        {
          key: 'end_date',
          type: 'date',
          label: 'Maturity Date',
          required: true,
          defaultValue: new Date('2026-02-03'),
          helpText: 'The date when the bond matures and principal is repaid',
          validators: [
            (value, formData) => {
              if (!value || !formData || !formData.start_date) return true
              if (value <= formData.start_date) {
                return 'Maturity date must be after start date'
              }
              return true
            }
          ]
        }
      ]
    },
    {
      title: 'Bond Terms',
      collapsible: true,
      initiallyCollapsed: false,
      fields: [
        {
          key: 'calendar',
          type: 'multiselect',
          label: 'Business Day Calendars',
          required: true,
          defaultValue: ['US', 'UK', 'TARGET'],
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
          selectionLimit: null,
          helpText: 'The business day calendars used for date adjustments'
        },
        {
          key: 'day_count_convention',
          type: 'dropdown',
          label: 'Day Count Convention',
          required: true,
          defaultValue: 'ACT/ACT',
          options: [
            { label: 'Actual/360', value: 'ACTUAL360' },
            { label: 'Actual/365', value: 'ACTUAL365FIXED' },
            { label: 'Actual/Actual', value: 'ACT/ACT' },
            { label: '30/360', value: '30/360' },
            { label: '30/365', value: '30/365' }
          ],
          filter: true,
          helpText:
            'The convention used to calculate the fraction of a year between two dates'
        },
        {
          key: 'business_day_convention',
          type: 'dropdown',
          label: 'Business Day Convention',
          required: true,
          defaultValue: 'ModifiedFollowing',
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
          key: 'settlement_lag',
          type: 'number',
          label: 'Settlement Lag (Days)',
          required: true,
          defaultValue: 2,
          min: 0,
          helpText:
            'Number of business days between trade date and settlement date',
          validators: [
            (value) => {
              if (value < 0) {
                return 'Settlement lag cannot be negative'
              }
              return true
            }
          ]
        },
        {
          key: 'fixed_rate',
          type: 'float',
          label: 'Fixed Rate',
          required: true,
          defaultValue: 0.055,
          min: 0,
          max: 1,
          step: 0.0001,
          minFractionDigits: 4,
          maxFractionDigits: 6,
          helpText:
            'The annual coupon rate in decimal form (e.g., 0.0525 for 5.25%)',
          validators: [
            (value) => {
              if (value < 0) {
                return 'Fixed rate cannot be negative'
              }
              if (value > 1) {
                return 'Fixed rate cannot exceed 1.0 (100%)'
              }
              return true
            }
          ]
        },
        {
          key: 'fixed_frequency',
          type: 'string',
          label: 'Payment Frequency',
          required: true,
          defaultValue: '1Y',
          helpText: 'How frequently coupon payments are made'
        }
      ]
    },
    {
      title: 'Pricing',
      collapsible: true,
      initiallyCollapsed: false,
      fields: [
        {
          key: 'discounting_curve',
          type: 'dropdown',
          label: 'Discounting Curve',
          required: true,
          defaultValue: 'PLN.WIRON.CSA_PLN',
          options: [
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
