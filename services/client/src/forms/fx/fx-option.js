import { sensitivityGroup } from '../shared/sensitivity-fields'

export const fxoptionForm = {
  name: 'FX Option',
  category: 'FX',
  api: 'calculateFXOption',
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
          helpText: 'The date at which the option will be valued'
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
          helpText: 'The currency being bought in the option contract'
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
          helpText: 'The amount of bought currency (notional)',
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
          helpText: 'The currency being sold in the option contract',
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
          label: 'Sold Amount (Strike)',
          required: true,
          defaultValue: 1100000,
          step: 1000,
          minFractionDigits: 2,
          maxFractionDigits: 2,
          helpText:
            'The amount of sold currency (strike price in foreign currency units)',
          validators: [
            (value) => {
              if (value <= 0) {
                return 'Sold amount must be greater than 0'
              }
              return true
            }
          ]
        }
      ]
    },
    {
      title: 'Option Details',
      collapsible: true,
      initiallyCollapsed: false,
      fields: [
        {
          key: 'long_short',
          type: 'dropdown',
          label: 'Position',
          required: true,
          defaultValue: 'Long',
          options: [
            { label: 'Long - Buying the option', value: 'Long' },
            { label: 'Short - Selling the option', value: 'Short' }
          ],
          filter: true,
          helpText:
            'Whether you are buying (long) or selling (short) the option'
        },
        {
          key: 'option_type',
          type: 'dropdown',
          label: 'Option Type',
          required: true,
          defaultValue: 'Call',
          options: [
            { label: 'Call - Right to buy', value: 'Call' },
            { label: 'Put - Right to sell', value: 'Put' }
          ],
          filter: true,
          helpText: 'Call option (right to buy) or Put option (right to sell)'
        },
        {
          key: 'style',
          type: 'dropdown',
          label: 'Exercise Style',
          required: true,
          defaultValue: 'European',
          options: [
            {
              label: 'European - Exercise only at maturity',
              value: 'European'
            },
            {
              label: 'American - Exercise anytime before maturity',
              value: 'American'
            }
          ],
          filter: true,
          helpText:
            'European (exercise only at expiry) or American (exercise anytime)'
        },
        {
          key: 'exercise_date',
          type: 'date',
          label: 'Exercise Date',
          required: true,
          defaultValue: new Date('2026-03-01'),
          helpText: 'The date when the option can be exercised (expiry date)',
          validators: [
            (value, formData) => {
              if (!value || !formData || !formData.evaluation_date) return true
              if (value <= formData.evaluation_date) {
                return 'Exercise date must be after evaluation date'
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
            { label: 'Cash - Cash settled', value: 'Cash' }
          ],
          filter: true,
          helpText: 'Whether settlement is physical delivery or cash settled'
        },
        {
          key: 'payoff_at_expiry',
          type: 'boolean',
          label: 'Payoff At Expiry',
          required: true,
          defaultValue: false,
          helpText: 'Whether the payoff occurs at the expiry date'
        }
      ]
    },
    {
      title: 'Premium Data',
      collapsible: true,
      initiallyCollapsed: false,
      fields: [
        {
          key: 'premium_amount',
          type: 'float',
          label: 'Premium Amount',
          required: false,
          defaultValue: null,
          step: 100,
          minFractionDigits: 2,
          maxFractionDigits: 2,
          helpText: 'The premium paid for the option (optional)'
        },
        {
          key: 'premium_currency',
          type: 'dropdown',
          label: 'Premium Currency',
          required: false,
          defaultValue: null,
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
          helpText:
            'Currency of the premium payment (required if premium_amount is provided)'
        },
        {
          key: 'premium_pay_date',
          type: 'date',
          label: 'Premium Payment Date',
          required: false,
          defaultValue: null,
          helpText:
            'Date when the premium is paid (required if premium_amount is provided)'
        }
      ]
    },
    sensitivityGroup
  ]
}
