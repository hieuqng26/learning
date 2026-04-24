import { sensitivityGroup } from '../shared/sensitivity-fields'

export const fxforwardForm = {
  name: 'FX Forward',
  category: 'FX',
  api: 'calculateFXForward',
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
          helpText: 'The date at which the FX forward will be valued'
        },
        {
          key: 'value_date',
          type: 'date',
          label: 'Value Date',
          required: true,
          defaultValue: new Date('2033-02-20'),
          helpText: 'The settlement/value date of the FX forward',
          validators: [
            (value, formData) => {
              if (!value || !formData || !formData.evaluation_date) return true
              if (value <= formData.evaluation_date) {
                return 'Value date must be after evaluation date'
              }
              return true
            }
          ]
        },
        {
          key: 'bought_currency',
          type: 'dropdown',
          label: 'Bought Currency',
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
          helpText: 'The currency being bought in the forward contract'
        },
        {
          key: 'bought_amount',
          type: 'float',
          label: 'Bought Amount',
          required: true,
          defaultValue: 1000000,
          step: 1000,
          minFractionDigits: 2,
          maxFractionDigits: 2,
          helpText: 'The amount of bought currency',
          validators: [
            (value) => {
              if (value <= 0) {
                return 'Bought amount must be greater than 0'
              }
              return true
            }
          ]
        },
        {
          key: 'sold_currency',
          type: 'dropdown',
          label: 'Sold Currency',
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
          helpText: 'The currency being sold in the forward contract',
          validators: [
            (value, formData) => {
              if (value === formData?.bought_currency) {
                return 'Sold currency must be different from bought currency'
              }
              return true
            }
          ]
        },
        {
          key: 'sold_amount',
          type: 'float',
          label: 'Sold Amount',
          required: true,
          defaultValue: 1100000,
          step: 1000,
          minFractionDigits: 2,
          maxFractionDigits: 2,
          helpText: 'The amount of sold currency',
          validators: [
            (value) => {
              if (value <= 0) {
                return 'Sold amount must be greater than 0'
              }
              return true
            }
          ]
        },
        {
          key: 'settlement',
          type: 'dropdown',
          label: 'Settlement Type',
          required: true,
          defaultValue: 'Cash',
          options: [
            { label: 'Physical - Actual currency exchange', value: 'Physical' },
            { label: 'Cash - Cash settled against FX fixing', value: 'Cash' }
          ],
          filter: true,
          helpText: 'Whether settlement is physical delivery or cash settled'
        }
      ]
    },
    {
      title: 'Cash Settlement Data',
      collapsible: true,
      initiallyCollapsed: false,
      condition: (formData) => formData.settlement === 'Cash',
      fields: [
        {
          key: 'settlement_currency',
          type: 'dropdown',
          label: 'Settlement Currency',
          required: false,
          defaultValue: 'USD',
          options: [
            { label: 'USD - US Dollar', value: 'USD' },
            { label: 'EUR - Euro', value: 'EUR' },
            { label: 'GBP - British Pound', value: 'GBP' },
            { label: 'JPY - Japanese Yen', value: 'JPY' }
          ],
          filter: true,
          helpText: 'Currency for cash settlement (required if settlement is Cash)'
        },
        {
          key: 'fx_index',
          type: 'string',
          label: 'FX Index',
          required: false,
          defaultValue: 'FX-TR20H-EUR-USD',
          helpText: 'FX index for cash settlement fixing (e.g., FX-TR20H-EUR-USD)'
        },
        {
          key: 'settlement_date',
          type: 'date',
          label: 'Settlement Date',
          required: false,
          defaultValue: new Date('2033-02-24'),
          helpText: 'Optional specific settlement date for cash settlement'
        },
        {
          key: 'payment_lag',
          type: 'string',
          label: 'Payment Lag',
          required: false,
          defaultValue: '2D',
          helpText: 'Payment lag (e.g., 2D for 2 business days)'
        },
        {
          key: 'payment_calendar',
          type: 'dropdown',
          label: 'Payment Calendar',
          required: false,
          defaultValue: 'USD',
          options: [
            { label: 'US - United States', value: 'USD' },
            { label: 'TARGET - European Central Bank', value: 'TARGET' },
            { label: 'UK - United Kingdom', value: 'UK' },
            { label: 'JP - Japan', value: 'JP' }
          ],
          filter: true,
          helpText: 'Calendar for payment date adjustments'
        },
        {
          key: 'payment_convention',
          type: 'dropdown',
          label: 'Payment Convention',
          required: false,
          defaultValue: 'Following',
          options: [
            { label: 'Following', value: 'Following' },
            { label: 'Modified Following', value: 'ModifiedFollowing' },
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
