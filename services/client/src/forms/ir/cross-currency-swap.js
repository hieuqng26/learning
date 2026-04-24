import { sensitivityGroup } from '../shared/sensitivity-fields'

export const crosscurrencyswapForm = {
  name: 'Cross Currency Swap',
  category: 'IR',
  api: 'calculateIRCrossCurrencySwap',
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
          key: 'start_date',
          type: 'date',
          label: 'Start Date',
          required: true,
          defaultValue: new Date('2019-09-04'),
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
          defaultValue: new Date('2032-09-03'),
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
          defaultValue: 'ModifiedFollowing',
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
    {
      title: 'Leg 1 (Domestic/Receive)',
      collapsible: true,
      initiallyCollapsed: false,
      fields: [
        {
          key: 'currency1',
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
          helpText: 'Currency for the first leg'
        },
        {
          key: 'notional1',
          type: 'float',
          label: 'Notional Amount',
          required: true,
          defaultValue: 30000000,
          step: 1000,
          minFractionDigits: 2,
          maxFractionDigits: 2,
          helpText: 'The notional amount for leg 1',
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
          key: 'index1',
          type: 'dropdown',
          label: 'Floating Rate Index',
          required: true,
          defaultValue: 'EUR-EURIBOR-6M',
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
          helpText: 'The floating rate index for leg 1'
        },
        {
          key: 'spread1',
          type: 'float',
          label: 'Spread',
          required: true,
          defaultValue: 0.0,
          step: 0.0001,
          minFractionDigits: 4,
          maxFractionDigits: 6,
          helpText: 'Spread over the index in decimal form (e.g., 0.001 for 10bp)'
        },
        {
          key: 'tenor1',
          type: 'dropdown',
          label: 'Payment Frequency',
          required: true,
          defaultValue: '6M',
          options: [
            { label: 'Annual', value: '1Y' },
            { label: 'Semi-Annual', value: '6M' },
            { label: 'Quarterly', value: '3M' },
            { label: 'Monthly', value: '1M' }
          ],
          filter: true,
          helpText: 'How frequently payments are made for leg 1'
        },
        {
          key: 'day_counter1',
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
          helpText: 'The convention used to calculate the fraction of a year for leg 1'
        }
      ]
    },
    {
      title: 'Leg 2 (Foreign/Pay)',
      collapsible: true,
      initiallyCollapsed: false,
      fields: [
        {
          key: 'currency2',
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
          helpText: 'Currency for the second leg',
          validators: [
            (value, formData) => {
              if (value === formData?.currency1) {
                return 'Leg 2 currency must be different from Leg 1 currency'
              }
              return true
            }
          ]
        },
        {
          key: 'notional2',
          type: 'float',
          label: 'Notional Amount',
          required: true,
          defaultValue: 33900000,
          step: 1000,
          minFractionDigits: 2,
          maxFractionDigits: 2,
          helpText: 'The notional amount for leg 2',
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
          key: 'index2',
          type: 'dropdown',
          label: 'Floating Rate Index',
          required: true,
          defaultValue: 'USD-LIBOR-3M',
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
          helpText: 'The floating rate index for leg 2'
        },
        {
          key: 'spread2',
          type: 'float',
          label: 'Spread',
          required: true,
          defaultValue: 0.0,
          step: 0.0001,
          minFractionDigits: 4,
          maxFractionDigits: 6,
          helpText: 'Spread over the index in decimal form (e.g., 0.001 for 10bp)'
        },
        {
          key: 'tenor2',
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
          helpText: 'How frequently payments are made for leg 2'
        },
        {
          key: 'day_counter2',
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
          helpText: 'The convention used to calculate the fraction of a year for leg 2'
        }
      ]
    },
    {
      title: 'Exchange & Fixing Options',
      collapsible: true,
      initiallyCollapsed: false,
      fields: [
        {
          key: 'initial_exchange',
          type: 'boolean',
          label: 'Initial Notional Exchange',
          required: true,
          defaultValue: true,
          helpText: 'Whether to exchange notional amounts at the start of the swap'
        },
        {
          key: 'final_exchange',
          type: 'boolean',
          label: 'Final Notional Exchange',
          required: true,
          defaultValue: true,
          helpText: 'Whether to exchange notional amounts at maturity of the swap'
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
        }
      ]
    },
    sensitivityGroup
  ]
}
