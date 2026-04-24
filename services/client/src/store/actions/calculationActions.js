import { calculationAPI } from '@/api'

export const calculationActions = {
  calculateIRFixedRateBond(context, payload) {
    return calculationAPI.calculateIRFixedRateBond(
      payload,
      context.state.jwt.accessToken
    )
  },
  calculateIRCallableCCS(context, payload) {
    return calculationAPI.calculateIRCallableCCS(
      payload,
      context.state.jwt.accessToken
    )
  },
  calculateIROISwap(context, payload) {
    return calculationAPI.calculateIROISwap(
      payload,
      context.state.jwt.accessToken
    )
  },
  calculateIRSwap(context, payload) {
    return calculationAPI.calculateIRSwap(
      payload,
      context.state.jwt.accessToken
    )
  },
  calculateIRCallableFloatingRateBond(context, payload) {
    return calculationAPI.calculateIRCallableFloatingRateBond(
      payload,
      context.state.jwt.accessToken
    )
  },
  calculateFXForward(context, payload) {
    return calculationAPI.calculateFXForward(
      payload,
      context.state.jwt.accessToken
    )
  },
  calculateFXSpot(context, payload) {
    return calculationAPI.calculateFXSpot(
      payload,
      context.state.jwt.accessToken
    )
  },
  calculateFXVanillaOption(context, payload) {
    return calculationAPI.calculateFXVanillaOption(
      payload,
      context.state.jwt.accessToken
    )
  },
  calculateFXOption(context, payload) {
    return calculationAPI.calculateFXOption(
      payload,
      context.state.jwt.accessToken
    )
  },
  calculateIRCrossCurrencySwap(context, payload) {
    return calculationAPI.calculateIRCrossCurrencySwap(
      payload,
      context.state.jwt.accessToken
    )
  },
  calculateSwaption(context, payload) {
    return calculationAPI.calculateSwaption(
      payload,
      context.state.jwt.accessToken
    )
  },
  calculatePortfolio(context, payload) {
    return calculationAPI.calculatePortfolio(
      payload,
      context.state.jwt.accessToken
    )
  },
  calculateOREPortfolio(context, payload) {
    return calculationAPI.calculateOREPortfolio(
      payload,
      context.state.jwt.accessToken
    )
  },
  calculateCommoditySpot(context, payload) {
    return calculationAPI.calculateCommoditySpot(
      payload,
      context.state.jwt.accessToken
    )
  },
  calculateCommodityForward(context, payload) {
    return calculationAPI.calculateCommodityForward(
      payload,
      context.state.jwt.accessToken
    )
  },
  calculateCommodityVanillaOption(context, payload) {
    return calculationAPI.calculateCommodityVanillaOption(
      payload,
      context.state.jwt.accessToken
    )
  },
  calculateEquitySpot(context, payload) {
    return calculationAPI.calculateEquitySpot(
      payload,
      context.state.jwt.accessToken
    )
  },
  calculateEquityForward(context, payload) {
    return calculationAPI.calculateEquityForward(
      payload,
      context.state.jwt.accessToken
    )
  },
  calculateEquityVanillaOption(context, payload) {
    return calculationAPI.calculateEquityVanillaOption(
      payload,
      context.state.jwt.accessToken
    )
  },
  calculateCryptoSpot(context, payload) {
    return calculationAPI.calculateCryptoSpot(
      payload,
      context.state.jwt.accessToken
    )
  },
  calculateCryptoForward(context, payload) {
    return calculationAPI.calculateCryptoForward(
      payload,
      context.state.jwt.accessToken
    )
  },
  calculateCryptoVanillaOption(context, payload) {
    return calculationAPI.calculateCryptoVanillaOption(
      payload,
      context.state.jwt.accessToken
    )
  }
}
