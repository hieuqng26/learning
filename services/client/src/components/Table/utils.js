export const isPositiveInteger = (val) => {
  let str = String(val)

  str = str.trim()

  if (!str) {
    return false
  }

  str = str.replace(/^0+/, '') || '0'
  var n = Math.floor(Number(str))

  return n !== Infinity && String(n) === str && n >= 0
}
export const formatCurrency = (value) => {
  if (value === null || value === undefined) return 'N/A'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value)
}

export const formatPercentage = (value, maxDigits) => {
  return new Intl.NumberFormat('en-US', {
    style: 'percent',
    minimumFractionDigits: maxDigits
  }).format(value)
}

export const formatNumber = (value, digits) => {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits
  }).format(value)
}

export const formatLargeNumber = (value, digits) => {
  if (Math.abs(value) >= 1e20) {
    const exponent = Math.floor(Math.log10(Math.abs(value)))
    const base = value / Math.pow(10, exponent)
    return `${formatNumber(base, digits)} x 10^${exponent}`
  } else if (value >= 1000000000 || value <= -1000000000) {
    return formatNumber(value / 1e9, digits) + ' .bil'
  } else if (value >= 1000000 || value <= -1000000) {
    return formatNumber(value / 1e6, digits) + ' .mil'
  }
  // else if (value >= 1000 || value <= -1000) {
  //   return formatNumber(value / 1e3, digits) + ' K'
  // }
  return formatNumber(value, digits)
}
