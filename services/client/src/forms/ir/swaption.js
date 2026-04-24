import { sensitivityGroup } from '../shared/sensitivity-fields'

export const swaptionForm = {
  name: 'Swaption',
  category: 'IR',
  api: 'calculateSwaption',
  groups: [
    {
      title: 'Option Details',
      collapsible: true,
      initiallyCollapsed: false,
      fields: [
        {
          key: 'evaluation_date',
          type: 'date',
          label: 'Evaluation Date',
          required: true,
          defaultValue: new Date('2016-02-05'),
          helpText: 'The date at which the swaption will be valued'
        },
        {
          key: 'exercise_style',
          type: 'dropdown',
          label: 'Exercise Style',
          required: true,
          defaultValue: 'European',
          options: [
            { label: 'European', value: 'European' },
            { label: 'Bermudan', value: 'Bermudan' },
            { label: 'American', value: 'American' }
          ],
          helpText:
            'European: single exercise date; Bermudan: multiple discrete dates; American: any date in a period'
        },
        {
          key: 'exercise_dates',
          type: 'string',
          label: 'Exercise Date(s)',
          required: true,
          defaultValue: '2036-02-20',
          helpText:
            'Single date for European (YYYY-MM-DD), multiple comma-separated dates for Bermudan/American (e.g., 2033-02-20,2034-02-20)'
        },
        {
          key: 'long_short',
          type: 'dropdown',
          label: 'Position',
          required: true,
          defaultValue: 'Long',
          options: [
            { label: 'Long (Buyer)', value: 'Long' },
            { label: 'Short (Seller)', value: 'Short' }
          ],
          helpText:
            'Long: buy the swaption (right to enter swap); Short: sell the swaption (obligation to enter swap)'
        },
        {
          key: 'settlement_type',
          type: 'dropdown',
          label: 'Settlement',
          required: true,
          defaultValue: 'Cash',
          options: [
            { label: 'Cash', value: 'Cash' },
            { label: 'Physical', value: 'Physical' }
          ],
          helpText:
            'Cash: cash-settled based on swap value; Physical: actual delivery of underlying swap'
        },
        {
          key: 'payer_receiver',
          type: 'dropdown',
          label: 'Swaption Type',
          required: true,
          defaultValue: 'Payer',
          options: [
            { label: 'Payer (Pay Fixed)', value: 'Payer' },
            { label: 'Receiver (Receive Fixed)', value: 'Receiver' }
          ],
          helpText:
            'Payer: option to pay fixed and receive floating; Receiver: option to receive fixed and pay floating'
        }
      ]
    },
    {
      title: 'Premium (Optional)',
      collapsible: true,
      initiallyCollapsed: true,
      fields: [
        {
          key: 'premium_amount',
          type: 'float',
          label: 'Premium Amount',
          required: false,
          step: 1000,
          minFractionDigits: 2,
          maxFractionDigits: 2,
          helpText: 'The upfront premium paid for the swaption (optional)',
          validators: [
            (value) => {
              if (value !== null && value !== undefined && value < 0) {
                return 'Premium amount cannot be negative'
              }
              return true
            }
          ]
        },
        {
          key: 'premium_currency',
          type: 'dropdown',
          label: 'Premium Currency',
          required: false,
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
            'Currency of the premium (required if premium amount is specified)'
        },
        {
          key: 'premium_pay_date',
          type: 'date',
          label: 'Premium Pay Date',
          required: false,
          helpText:
            'Date when the premium is paid (required if premium amount is specified)'
        }
      ]
    },
    {
      title: 'Underlying Swap - General',
      collapsible: true,
      initiallyCollapsed: false,
      fields: [
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
          helpText: 'The currency in which the underlying swap is denominated'
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
          helpText: 'The notional amount of the underlying swap',
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
          key: 'start_date',
          type: 'date',
          label: 'Swap Start Date',
          required: true,
          defaultValue: new Date('2033-02-20'),
          helpText:
            'The effective date when the underlying swap begins (must be after exercise date for European)',
          validators: [
            (value, formData) => {
              if (!value || !formData || !formData.evaluation_date) return true
              if (value < formData.evaluation_date) {
                return 'Swap start date cannot be before evaluation date'
              }
              return true
            }
          ]
        },
        {
          key: 'end_date',
          type: 'date',
          label: 'Swap Maturity Date',
          required: true,
          defaultValue: new Date('2043-02-21'),
          helpText: 'The date when the underlying swap matures',
          validators: [
            (value, formData) => {
              if (!value || !formData || !formData.start_date) return true
              if (value <= formData.start_date) {
                return 'Swap maturity date must be after swap start date'
              }
              return true
            }
          ]
        },
        {
          key: 'calendar',
          type: 'dropdown',
          label: 'Business Day Calendar',
          required: true,
          defaultValue: 'TARGET',
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
    {
      title: 'Underlying Swap - Fixed Leg',
      collapsible: true,
      initiallyCollapsed: false,
      fields: [
        {
          key: 'fixed_rate',
          type: 'float',
          label: 'Fixed Rate',
          required: true,
          defaultValue: 0.02,
          min: 0,
          max: 1,
          step: 0.0001,
          minFractionDigits: 4,
          maxFractionDigits: 6,
          helpText: 'The fixed rate in decimal form (e.g., 0.02 for 2%)',
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
          key: 'fixed_tenor',
          type: 'dropdown',
          label: 'Fixed Leg Payment Frequency',
          required: true,
          defaultValue: '1Y',
          options: [
            { label: 'Annual', value: '1Y' },
            { label: 'Semi-Annual', value: '6M' },
            { label: 'Quarterly', value: '3M' },
            { label: 'Monthly', value: '1M' }
          ],
          filter: true,
          helpText: 'How frequently fixed rate payments are made'
        },
        {
          key: 'fixed_day_counter',
          type: 'dropdown',
          label: 'Fixed Leg Day Count Convention',
          required: true,
          defaultValue: 'ACT/ACT',
          options: [
            { label: 'Actual/360', value: 'A360' },
            { label: 'Actual/365', value: 'A365' },
            { label: 'Actual/Actual', value: 'ACT/ACT' },
            { label: '30/360', value: '30/360' }
          ],
          filter: true,
          helpText:
            'The convention used to calculate the fraction of a year for fixed leg payments'
        }
      ]
    },
    {
      title: 'Underlying Swap - Floating Leg',
      collapsible: true,
      initiallyCollapsed: false,
      fields: [
        {
          key: 'floating_index',
          type: 'dropdown',
          label: 'Floating Rate Index',
          required: true,
          defaultValue: 'EUR-EURIBOR-3M',
          options: [
            { label: 'USD-LIBOR-3M', value: 'USD-LIBOR-3M' },
            { label: 'USD-LIBOR-6M', value: 'USD-LIBOR-6M' },
            { label: 'USD-SOFR', value: 'USD-SOFR' },
            { label: 'EUR-EURIBOR-3M', value: 'EUR-EURIBOR-3M' },
            { label: 'EUR-EURIBOR-6M', value: 'EUR-EURIBOR-6M' },
            { label: 'EUR-ESTR', value: 'EUR-ESTR' },
            { label: 'GBP-LIBOR-3M', value: 'GBP-LIBOR-3M' },
            { label: 'GBP-LIBOR-6M', value: 'GBP-LIBOR-6M' },
            { label: 'GBP-SONIA', value: 'GBP-SONIA' },
            { label: 'JPY-LIBOR-3M', value: 'JPY-LIBOR-3M' },
            { label: 'JPY-LIBOR-6M', value: 'JPY-LIBOR-6M' },
            { label: 'JPY-TONAR', value: 'JPY-TONAR' },
            { label: 'AUD-BBSW-3M', value: 'AUD-BBSW-3M' },
            { label: 'AUD-BBSW-6M', value: 'AUD-BBSW-6M' },
            { label: 'CAD-CDOR-3M', value: 'CAD-CDOR-3M' },
            { label: 'CHF-LIBOR-3M', value: 'CHF-LIBOR-3M' },
            { label: 'CHF-LIBOR-6M', value: 'CHF-LIBOR-6M' }
          ],
          filter: true,
          helpText: 'The floating rate index used for the floating leg'
        },
        {
          key: 'floating_tenor',
          type: 'dropdown',
          label: 'Floating Leg Payment Frequency',
          required: true,
          defaultValue: '3M',
          options: [
            { label: 'Annual', value: '1Y' },
            { label: 'Semi-Annual', value: '6M' },
            { label: 'Quarterly', value: '3M' },
            { label: 'Monthly', value: '1M' }
          ],
          filter: true,
          helpText: 'How frequently floating rate payments are made'
        },
        {
          key: 'floating_day_counter',
          type: 'dropdown',
          label: 'Floating Leg Day Count Convention',
          required: true,
          defaultValue: 'A360',
          options: [
            { label: 'Actual/360', value: 'A360' },
            { label: 'Actual/365', value: 'A365' },
            { label: 'Actual/Actual', value: 'ACT/ACT' },
            { label: '30/360', value: '30/360' }
          ],
          filter: true,
          helpText:
            'The convention used to calculate the fraction of a year for floating leg payments'
        },
        {
          key: 'floating_spread',
          type: 'float',
          label: 'Floating Spread',
          required: true,
          defaultValue: 0.0,
          step: 0.0001,
          minFractionDigits: 4,
          maxFractionDigits: 6,
          helpText:
            'Spread over the floating index in decimal form (e.g., 0.001 for 10bp)'
        },
        {
          key: 'is_in_arrears',
          type: 'boolean',
          label: 'Is In Arrears',
          required: false,
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
          helpText:
            'Number of business days between rate fixing and payment period start',
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
        }
      ]
    },
    sensitivityGroup
  ]
}
