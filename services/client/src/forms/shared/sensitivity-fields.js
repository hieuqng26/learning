/**
 * Shared sensitivity analysis fields for all ORE trade forms.
 * Import and add to form groups to enable sensitivity analysis.
 */

export const sensitivityGroup = {
  title: 'Stress Configuration',
  collapsible: true,
  initiallyCollapsed: false,
  fields: [
    {
      key: 'sensitivity_entries',
      type: 'sensitivity',
      label: 'Sensitivity Configuration',
      required: false,
      defaultValue: [],
      helpText: 'Configure risk factors for sensitivity analysis'
    }
  ]
}

/**
 * Validate if a sensitivity entry is complete and valid.
 */
function isValidEntry(entry) {
  if (!entry.type) return false

  if (entry.type === 'discount_curve') {
    return (
      entry.currency &&
      entry.shift_type &&
      entry.shift_size != null &&
      entry.shift_size > 0 &&
      entry.shift_tenors &&
      entry.shift_tenors.trim().length > 0
    )
  }

  if (entry.type === 'index_curve') {
    return (
      entry.index &&
      entry.shift_type &&
      entry.shift_size != null &&
      entry.shift_size > 0 &&
      entry.shift_tenors &&
      entry.shift_tenors.trim().length > 0
    )
  }

  if (entry.type === 'fx_spot') {
    return (
      entry.pair &&
      entry.shift_type &&
      entry.shift_size != null &&
      entry.shift_size > 0
    )
  }

  if (entry.type === 'fx_volatility') {
    return (
      entry.pair &&
      entry.shift_type &&
      entry.shift_size != null &&
      entry.shift_size > 0 &&
      entry.shift_expiries &&
      Array.isArray(entry.shift_expiries) &&
      entry.shift_expiries.length > 0
      // shift_strikes can be empty (means ATM)
    )
  }

  if (entry.type === 'swaption_volatility') {
    return (
      entry.currency &&
      entry.shift_type &&
      entry.shift_size != null &&
      entry.shift_size > 0 &&
      entry.shift_expiries &&
      Array.isArray(entry.shift_expiries) &&
      entry.shift_expiries.length > 0 &&
      entry.shift_terms &&
      Array.isArray(entry.shift_terms) &&
      entry.shift_terms.length > 0
      // shift_strikes can be empty (means ATM only)
    )
  }

  return false
}

/**
 * Helper to transform form sensitivity data to API format.
 * Call this in SingleProduct.vue before sending to API.
 */
export function transformSensitivityData(formData) {
  const entries = formData?.sensitivity_entries
  if (!entries || !Array.isArray(entries) || entries.length === 0) {
    return null
  }

  // Filter to only valid entries
  const validEntries = entries.filter(isValidEntry)
  if (validEntries.length === 0) {
    return null
  }

  const result = {
    enabled: true,
    discount_curves: [],
    index_curves: [],
    fx_spots: [],
    fx_volatilities: [],
    swaption_volatilities: []
  }

  // Transform each valid entry
  validEntries.forEach((entry) => {
    if (entry.type === 'discount_curve') {
      result.discount_curves.push({
        ccy: entry.currency,
        shift_type: entry.shift_type,
        shift_size: entry.shift_size,
        shift_scheme: entry.shift_scheme || 'Forward',
        shift_tenors: entry.shift_tenors
          .split(',')
          .map((t) => t.trim())
          .filter((t) => t)
      })
    } else if (entry.type === 'index_curve') {
      result.index_curves.push({
        index: entry.index,
        shift_type: entry.shift_type,
        shift_size: entry.shift_size,
        shift_scheme: entry.shift_scheme || 'Forward',
        shift_tenors: entry.shift_tenors
          .split(',')
          .map((t) => t.trim())
          .filter((t) => t)
      })
    } else if (entry.type === 'fx_spot') {
      result.fx_spots.push({
        ccypair: entry.pair,
        shift_type: entry.shift_type,
        shift_size: entry.shift_size,
        shift_scheme: entry.shift_scheme || 'Forward'
      })
    } else if (entry.type === 'fx_volatility') {
      result.fx_volatilities.push({
        ccypair: entry.pair,
        shift_type: entry.shift_type,
        shift_size: entry.shift_size,
        shift_scheme: entry.shift_scheme || 'Forward',
        shift_expiries: entry.shift_expiries,
        shift_strikes:
          entry.shift_strikes && entry.shift_strikes.length > 0
            ? entry.shift_strikes.map((s) => parseFloat(s))
            : [] // Empty means ATM
      })
    } else if (entry.type === 'swaption_volatility') {
      result.swaption_volatilities.push({
        ccy: entry.currency,
        shift_type: entry.shift_type,
        shift_size: entry.shift_size,
        shift_scheme: entry.shift_scheme || 'Forward',
        shift_expiries: entry.shift_expiries,
        shift_terms: entry.shift_terms,
        shift_strikes:
          entry.shift_strikes && entry.shift_strikes.length > 0
            ? entry.shift_strikes.map((s) => parseFloat(s))
            : [0.0] // Default to ATM (0.0) if empty
      })
    }
  })

  // Return null if no actual configurations
  if (
    result.discount_curves.length === 0 &&
    result.index_curves.length === 0 &&
    result.fx_spots.length === 0 &&
    result.fx_volatilities.length === 0 &&
    result.swaption_volatilities.length === 0
  ) {
    return null
  }

  return result
}

/**
 * Validate sensitivity configuration before submission.
 * Returns { valid: boolean, errors: string[] }
 */
export function validateSensitivityConfig(formData) {
  const entries = formData?.sensitivity_entries
  const errors = []

  if (!entries || !Array.isArray(entries) || entries.length === 0) {
    return { valid: true, errors: [] } // No sensitivity configured is valid
  }

  entries.forEach((entry, index) => {
    const num = index + 1

    if (!entry.type) {
      errors.push(`Risk Factor ${num}: Please select a risk factor type`)
      return
    }

    if (entry.type === 'discount_curve') {
      if (!entry.currency) {
        errors.push(`Risk Factor ${num}: Currency is required`)
      }
      if (!entry.shift_type) {
        errors.push(`Risk Factor ${num}: Shift type is required`)
      }
      if (entry.shift_size == null || entry.shift_size <= 0) {
        errors.push(`Risk Factor ${num}: Shift size must be greater than 0`)
      }
      if (!entry.shift_tenors || entry.shift_tenors.trim().length === 0) {
        errors.push(`Risk Factor ${num}: Shift tenors are required`)
      }
    } else if (entry.type === 'index_curve') {
      if (!entry.index) {
        errors.push(`Risk Factor ${num}: Index is required`)
      }
      if (!entry.shift_type) {
        errors.push(`Risk Factor ${num}: Shift type is required`)
      }
      if (entry.shift_size == null || entry.shift_size <= 0) {
        errors.push(`Risk Factor ${num}: Shift size must be greater than 0`)
      }
      if (!entry.shift_tenors || entry.shift_tenors.trim().length === 0) {
        errors.push(`Risk Factor ${num}: Shift tenors are required`)
      }
    } else if (entry.type === 'fx_spot') {
      if (!entry.pair) {
        errors.push(`Risk Factor ${num}: Currency pair is required`)
      }
      if (!entry.shift_type) {
        errors.push(`Risk Factor ${num}: Shift type is required`)
      }
      if (entry.shift_size == null || entry.shift_size <= 0) {
        errors.push(`Risk Factor ${num}: Shift size must be greater than 0`)
      }
    } else if (entry.type === 'fx_volatility') {
      if (!entry.pair) {
        errors.push(`Risk Factor ${num}: Currency pair is required`)
      }
      if (!entry.shift_type) {
        errors.push(`Risk Factor ${num}: Shift type is required`)
      }
      if (entry.shift_size == null || entry.shift_size <= 0) {
        errors.push(`Risk Factor ${num}: Shift size must be greater than 0`)
      }
      if (
        !entry.shift_expiries ||
        !Array.isArray(entry.shift_expiries) ||
        entry.shift_expiries.length === 0
      ) {
        errors.push(`Risk Factor ${num}: At least one expiry must be selected`)
      }
      // shift_strikes is optional - empty means ATM
    } else if (entry.type === 'swaption_volatility') {
      if (!entry.currency) {
        errors.push(`Risk Factor ${num}: Currency is required`)
      }
      if (!entry.shift_type) {
        errors.push(`Risk Factor ${num}: Shift type is required`)
      }
      if (entry.shift_size == null || entry.shift_size <= 0) {
        errors.push(`Risk Factor ${num}: Shift size must be greater than 0`)
      }
      if (
        !entry.shift_expiries ||
        !Array.isArray(entry.shift_expiries) ||
        entry.shift_expiries.length === 0
      ) {
        errors.push(`Risk Factor ${num}: At least one expiry must be selected`)
      }
      if (
        !entry.shift_terms ||
        !Array.isArray(entry.shift_terms) ||
        entry.shift_terms.length === 0
      ) {
        errors.push(`Risk Factor ${num}: At least one term must be selected`)
      }
      // shift_strikes is optional - empty means ATM only
    }
  })

  return {
    valid: errors.length === 0,
    errors
  }
}
