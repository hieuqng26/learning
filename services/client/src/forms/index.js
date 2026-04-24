import IR from './ir'
import FX from './fx'
import EQ from './equity'
import COM from './commodity'
import CRYPTO from './crypto'

export const productCategories = [
  { label: 'Interest Rates', value: 'IR' },
  { label: 'Foreign Exchange', value: 'FX' },
  { label: 'Commodities', value: 'COMMODITY' },
  { label: 'Equities', value: 'EQUITY' },
  { label: 'Cryptocurrencies', value: 'CRYPTO' }
]

export const productsByCategory = {
  IR: [
    IR.fixedRateBondForm,
    IR.callableCCSForm,
    IR.oiswapForm,
    IR.irswapForm,
    IR.crosscurrencyswapForm,
    IR.callableFloatingRateBondForm,
    IR.swaptionForm,
    IR.irCapFloorForm
  ],
  FX: [
    FX.fxforwardForm,
    FX.fxspotForm,
    FX.fxoptionForm,
    FX.fxAmericanOptionForm,
    FX.fxBarrierOptionForm,
    FX.fxBarrierTriggerRedemptionNoteForm,
    FX.dualCurrencyDepositForm
  ],
  COMMODITY: [
    COM.commoditySpotForm,
    COM.commodityForwardForm,
    COM.commodityVanillaOptionForm
  ],
  EQUITY: [
    EQ.equitySpotForm,
    EQ.equityForwardForm,
    EQ.equityVanillaOptionForm,
    EQ.eqBarrierLeveragedRangeAccrualForm
  ],
  CRYPTO: [
    CRYPTO.cryptoSpotForm,
    CRYPTO.cryptoForwardForm,
    CRYPTO.cryptoVanillaOptionForm
  ]
}

export const getProductsByCategory = (category) => {
  return productsByCategory[category] || []
}

export const getProductForm = (category, productName) => {
  const products = getProductsByCategory(category)
  return products.find((product) => product.name === productName)
}

export const getAllProducts = () => {
  return Object.values(productsByCategory).flat()
}
