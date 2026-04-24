import { httpClient, setAuthHeader } from '@/api/httpClient'

const calculationAPI = {
  calculateIRFixedRateBond: (payload, jwt) =>
    httpClient.post(`/calculate/ir/fixed_rate_bond`, payload, {
      headers: {
        ...setAuthHeader(jwt),
        'Content-Type': 'application/json'
      }
    }),
  calculateIRCallableCCS: (payload, jwt) =>
    httpClient.post(`/calculate/ir/callable_ccs`, payload, {
      headers: {
        ...setAuthHeader(jwt),
        'Content-Type': 'application/json'
      }
    }),
  calculateIROISwap: (payload, jwt) =>
    httpClient.post(`/calculate/ir/oiswap`, payload, {
      headers: {
        ...setAuthHeader(jwt),
        'Content-Type': 'application/json'
      }
    }),
  calculateIRSwap: (payload, jwt) =>
    httpClient.post(`/calculate/ir/irswap`, payload, {
      headers: {
        ...setAuthHeader(jwt),
        'Content-Type': 'application/json'
      }
    }),
  calculateIRCallableFloatingRateBond: (payload, jwt) =>
    httpClient.post(`/calculate/ir/callable_floating_rate_bond`, payload, {
      headers: {
        ...setAuthHeader(jwt),
        'Content-Type': 'application/json'
      }
    }),
  calculateFXForward: (payload, jwt) =>
    httpClient.post(`/calculate/fx/fxforward`, payload, {
      headers: {
        ...setAuthHeader(jwt),
        'Content-Type': 'application/json'
      }
    }),
  calculateFXSpot: (payload, jwt) =>
    httpClient.post(`/calculate/fx/fxspot`, payload, {
      headers: {
        ...setAuthHeader(jwt),
        'Content-Type': 'application/json'
      }
    }),
  calculateFXVanillaOption: (payload, jwt) =>
    httpClient.post(`/calculate/fx/fxvanillaoption`, payload, {
      headers: {
        ...setAuthHeader(jwt),
        'Content-Type': 'application/json'
      }
    }),
  calculateFXOption: (payload, jwt) =>
    httpClient.post(`/calculate/fx/fxoption`, payload, {
      headers: {
        ...setAuthHeader(jwt),
        'Content-Type': 'application/json'
      }
    }),
  calculateIRCrossCurrencySwap: (payload, jwt) =>
    httpClient.post(`/calculate/ir/crosscurrencyswap`, payload, {
      headers: {
        ...setAuthHeader(jwt),
        'Content-Type': 'application/json'
      }
    }),
  calculateSwaption: (payload, jwt) =>
    httpClient.post(`/calculate/ir/swaption`, payload, {
      headers: {
        ...setAuthHeader(jwt),
        'Content-Type': 'application/json'
      }
    }),
  calculatePortfolio: (payload, jwt) =>
    httpClient.post(`/calculate/portfolio`, payload, {
      headers: {
        ...setAuthHeader(jwt),
        'Content-Type': 'application/json'
      }
    }),
  calculateOREPortfolio: (payload, jwt) =>
    httpClient.post(`/calculate/ore/portfolio`, payload, {
      headers: {
        ...setAuthHeader(jwt),
        'Content-Type': 'application/json'
      }
    }),
  calculateCommoditySpot: (payload, jwt) =>
    httpClient.post(`/calculate/commodity/spot`, payload, {
      headers: {
        ...setAuthHeader(jwt),
        'Content-Type': 'application/json'
      }
    }),
  calculateCommodityForward: (payload, jwt) =>
    httpClient.post(`/calculate/commodity/forward`, payload, {
      headers: {
        ...setAuthHeader(jwt),
        'Content-Type': 'application/json'
      }
    }),
  calculateCommodityVanillaOption: (payload, jwt) =>
    httpClient.post(`/calculate/commodity/vanilla_option`, payload, {
      headers: {
        ...setAuthHeader(jwt),
        'Content-Type': 'application/json'
      }
    }),
  calculateEquitySpot: (payload, jwt) =>
    httpClient.post(`/calculate/equity/spot`, payload, {
      headers: {
        ...setAuthHeader(jwt),
        'Content-Type': 'application/json'
      }
    }),
  calculateEquityForward: (payload, jwt) =>
    httpClient.post(`/calculate/equity/forward`, payload, {
      headers: {
        ...setAuthHeader(jwt),
        'Content-Type': 'application/json'
      }
    }),
  calculateEquityVanillaOption: (payload, jwt) =>
    httpClient.post(`/calculate/equity/vanilla_option`, payload, {
      headers: {
        ...setAuthHeader(jwt),
        'Content-Type': 'application/json'
      }
    }),
  calculateCryptoSpot: (payload, jwt) =>
    httpClient.post(`/calculate/crypto/spot`, payload, {
      headers: {
        ...setAuthHeader(jwt),
        'Content-Type': 'application/json'
      }
    }),
  calculateCryptoForward: (payload, jwt) =>
    httpClient.post(`/calculate/crypto/forward`, payload, {
      headers: {
        ...setAuthHeader(jwt),
        'Content-Type': 'application/json'
      }
    }),
  calculateCryptoVanillaOption: (payload, jwt) =>
    httpClient.post(`/calculate/crypto/vanilla_option`, payload, {
      headers: {
        ...setAuthHeader(jwt),
        'Content-Type': 'application/json'
      }
    })
}

export default calculationAPI
