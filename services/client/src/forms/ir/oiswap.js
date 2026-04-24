import { sensitivityGroup } from '../shared/sensitivity-fields'

export const oiswapForm = {
  name: 'Overnight Index Swap',
  category: 'IR',
  api: 'calculateIROISwap',
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
          defaultValue: new Date('2016-02-05'),
          helpText: 'The date at which the swap will be valued'
        },
        {
          key: 'currency',
          type: 'dropdown',
          label: 'Currency',
          required: true,
          defaultValue: 'EUR',
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
          helpText: 'The currency in which the swap is denominated'
        },
        {
          key: 'notional',
          type: 'float',
          label: 'Notional Amount',
          required: true,
          defaultValue: 100000000,
          step: 1000,
          minFractionDigits: 2,
          maxFractionDigits: 2,
          helpText: 'The notional amount of the swap',
          validators: [
            (value) => {
              if (value <= 0) {
                return 'Notional amount must be greater than 0'
              }
              return true
            }
          ]
        },
        {
          key: 'payer',
          type: 'boolean',
          label: 'Payer',
          required: true,
          defaultValue: false,
          helpText: 'True if paying floating rate, false if receiving floating rate'
        },
        {
          key: 'start_date',
          type: 'date',
          label: 'Start Date',
          required: true,
          defaultValue: new Date('2023-01-31'),
          helpText: 'The effective date when the swap begins',
          validators: [
            (value, formData) => {
              if (!value || !formData || !formData.evaluation_date) return true
              if (value < formData.evaluation_date) {
                return 'Start date cannot be before evaluation date'
              }
              return true
            }
          ]
        },
        {
          key: 'end_date',
          type: 'date',
          label: 'Maturity Date',
          required: true,
          defaultValue: new Date('2028-02-01'),
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
          key: 'tenor',
          type: 'dropdown',
          label: 'Payment Frequency',
          required: true,
          defaultValue: '3M',
          options: [
            { label: 'Annual', value: '1Y' },
            { label: 'Semi-Annual', value: '6M' },
            { label: 'Quarterly', value: '3M' },
            { label: 'Monthly', value: '1M' }
          ],
          filter: true,
          helpText: 'How frequently payments are made'
        },
        {
          key: 'calendar',
          type: 'dropdown',
          label: 'Business Day Calendar',
          required: true,
          defaultValue: 'US',
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
          helpText: 'The business day calendar used for date adjustments'
        },
        {
          key: 'convention',
          type: 'dropdown',
          label: 'Business Day Convention',
          required: true,
          defaultValue: 'MF',
          options: [
            { label: 'Following', value: 'Following' },
            { label: 'Modified Following', value: 'MF' },
            { label: 'Preceding', value: 'Preceding' },
            { label: 'Modified Preceding', value: 'ModifiedPreceding' }
          ],
          filter: true,
          helpText: 'The convention used to adjust dates that fall on non-business days'
        }
      ]
    },
    {
      title: 'Floating Leg (Overnight Index)',
      collapsible: true,
      initiallyCollapsed: false,
      fields: [
        {
          key: 'index',
          type: 'dropdown',
          label: 'Overnight Index',
          required: true,
          defaultValue: 'EUR-EONIA',
          options: [
            { label: 'EUR-EONIA - Euro OverNight Index Average', value: 'EUR-EONIA' },
            { label: 'USD-SOFR - Secured Overnight Financing Rate', value: 'USD-SOFR' },
            { label: 'GBP-SONIA - Sterling Overnight Index Average', value: 'GBP-SONIA' },
            { label: 'JPY-TONAR - Tokyo Overnight Average Rate', value: 'JPY-TONAR' },
            { label: 'AUD-AONIA - Australian Overnight Index Average', value: 'AUD-AONIA' },
            { label: 'CAD-CORRA - Canadian Overnight Repo Rate Average', value: 'CAD-CORRA' },
            { label: 'CHF-SARON - Swiss Average Rate Overnight', value: 'CHF-SARON' }
          ],
          filter: true,
          helpText: 'The overnight index used for the floating rate'
        },
        {
          key: 'spread',
          type: 'float',
          label: 'Spread',
          required: true,
          defaultValue: 0.000122,
          step: 0.000001,
          minFractionDigits: 6,
          maxFractionDigits: 8,
          helpText: 'Spread over the overnight index in decimal form (e.g., 0.000122 for 1.22bp)'
        },
        {
          key: 'is_in_arrears',
          type: 'boolean',
          label: 'Is In Arrears',
          required: true,
          defaultValue: false,
          helpText: 'Whether the fixing is in arrears (fixed at end of period)'
        },
        {
          key: 'fixing_days',
          type: 'number',
          label: 'Fixing Days',
          required: true,
          defaultValue: 2,
          min: 0,
          max: 10,
          helpText: 'Number of business days between rate fixing and payment period start',
          validators: [
            (value) => {
              if (value < 0) {
                return 'Fixing days cannot be negative'
              }
              if (value > 10) {
                return 'Fixing days cannot exceed 10'
              }
              return true
            }
          ]
        },
        {
          key: 'day_counter',
          type: 'dropdown',
          label: 'Day Count Convention',
          required: true,
          defaultValue: 'A360',
          options: [
            { label: 'Actual/360', value: 'A360' },
            { label: 'Actual/365', value: 'A365' },
            { label: 'Actual/Actual', value: 'ACT/ACT' },
            { label: '30/360', value: '30/360' }
          ],
          filter: true,
          helpText: 'The convention used to calculate the fraction of a year for payments'
        },
        {
          key: 'payment_convention',
          type: 'dropdown',
          label: 'Payment Convention',
          required: true,
          defaultValue: 'MF',
          options: [
            { label: 'Following', value: 'Following' },
            { label: 'Modified Following', value: 'MF' },
            { label: 'Preceding', value: 'Preceding' },
            { label: 'Modified Preceding', value: 'ModifiedPreceding' }
          ],
          filter: true,
          helpText: 'Business day convention for payment dates'
        }
      ]
    },
    sensitivityGroup
  ]
}
