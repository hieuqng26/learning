"""
Sensitivity XML generator.
"""

from lxml import etree
from pathlib import Path
from typing import Dict, List, Optional, Any


class SensitivityGenerator:
    """
    Generate sensitivity.xml from sensitivity configuration.

    Creates sensitivity analysis configuration for risk factor bumps
    (discount curves, index curves, FX spots, FX volatilities).
    """

    def __init__(self):
        """Initialize SensitivityGenerator."""
        self._has_credit_curves = False

    # Default ParConversion configurations for common currencies
    DEFAULT_PAR_CONVERSIONS = {
        'EUR': {
            'discount': {
                'instruments': ['OIS'],
                'single_curve': True,
                'conventions': {
                    'DEP': 'EUR-EONIA-CONVENTIONS',
                    'OIS': 'EUR-OIS-CONVENTIONS'
                }
            },
            'index': {
                'EUR-EURIBOR-3M': {
                    'instruments': ['DEP', 'IRS'],
                    'single_curve': False,
                    'discount_curve': 'EUR-EONIA',
                    'conventions': {
                        'DEP': 'EUR-EURIBOR-CONVENTIONS',
                        'IRS': 'EUR-3M-SWAP-CONVENTIONS',
                        'OIS': 'EUR-OIS-CONVENTIONS'
                    }
                },
                'EUR-EURIBOR-6M': {
                    'instruments': ['DEP', 'IRS'],
                    'single_curve': False,
                    'discount_curve': 'EUR-EONIA',
                    'conventions': {
                        'DEP': 'EUR-EURIBOR-CONVENTIONS',
                        'IRS': 'EUR-6M-SWAP-CONVENTIONS',
                        'OIS': 'EUR-OIS-CONVENTIONS'
                    }
                },
                'EUR-EURIBOR-1M': {
                    'instruments': ['DEP', 'IRS'],
                    'single_curve': False,
                    'discount_curve': 'EUR-EONIA',
                    'conventions': {
                        'DEP': 'EUR-EURIBOR-CONVENTIONS',
                        'IRS': 'EUR-1M-SWAP-CONVENTIONS',
                        'OIS': 'EUR-OIS-CONVENTIONS'
                    }
                },
                'EUR-EONIA': {
                    'instruments': ['OIS'],
                    'single_curve': False,
                    'conventions': {
                        'OIS': 'EUR-OIS-CONVENTIONS'
                    }
                }
            }
        },
        'USD': {
            'discount': {
                'instruments': ['FXF', 'XBS'],
                'single_curve': True,
                'conventions': {
                    'XBS': 'EUR-USD-XCCY-BASIS-CONVENTIONS',
                    'FXF': 'EUR-USD-FX-CONVENTIONS'
                }
            },
            'index': {
                'USD-LIBOR-3M': {
                    'instruments': ['DEP', 'IRS'],
                    'single_curve': False,
                    'discount_curve': 'USD-FedFunds',
                    'conventions': {
                        'DEP': 'USD-LIBOR-CONVENTIONS',
                        'IRS': 'USD-3M-SWAP-CONVENTIONS'
                    }
                },
                'USD-LIBOR-6M': {
                    'instruments': ['DEP', 'IRS'],
                    'single_curve': False,
                    'discount_curve': 'USD-FedFunds',
                    'conventions': {
                        'DEP': 'USD-LIBOR-CONVENTIONS',
                        'IRS': 'USD-6M-SWAP-CONVENTIONS'
                    }
                },
                'USD-FedFunds': {
                    'instruments': ['DEP', 'OIS'],
                    'single_curve': False,
                    'conventions': {
                        'DEP': 'USD-LIBOR-CONVENTIONS',
                        'IRS': 'USD-3M-SWAP-CONVENTIONS',
                        'OIS': 'USD-OIS-CONVENTIONS'
                    }
                }
            }
        },
        'GBP': {
            'discount': {
                'instruments': ['DEP', 'IRS'],
                'single_curve': True,
                'conventions': {
                    'DEP': 'GBP-DEPOSIT',
                    'IRS': 'GBP-6M-SWAP-CONVENTIONS',
                    'OIS': 'GBP-OIS-CONVENTIONS'
                }
            },
            'index': {
                'GBP-LIBOR-3M': {
                    'instruments': ['DEP', 'IRS'],
                    'single_curve': False,
                    'conventions': {
                        'DEP': 'GBP-DEPOSIT',
                        'IRS': 'GBP-3M-SWAP-CONVENTIONS'
                    }
                },
                'GBP-LIBOR-6M': {
                    'instruments': ['DEP', 'IRS'],
                    'single_curve': False,
                    'conventions': {
                        'DEP': 'GBP-DEPOSIT',
                        'IRS': 'GBP-6M-SWAP-CONVENTIONS'
                    }
                },
                'GBP-SONIA': {
                    'instruments': ['DEP', 'IRS'],
                    'single_curve': False,
                    'conventions': {
                        'DEP': 'GBP-DEPOSIT',
                        'IRS': 'GBP-3M-SWAP-CONVENTIONS',
                        'OIS': 'GBP-OIS-CONVENTIONS'
                    }
                }
            }
        },
        'JPY': {
            'discount': {
                'instruments': ['DEP', 'IRS'],
                'single_curve': True,
                'conventions': {
                    'DEP': 'JPY-DEPOSIT',
                    'IRS': 'JPY-6M-SWAP-CONVENTIONS'
                }
            },
            'index': {
                'JPY-LIBOR-3M': {
                    'instruments': ['DEP', 'IRS'],
                    'single_curve': False,
                    'conventions': {
                        'DEP': 'JPY-DEPOSIT',
                        'IRS': 'JPY-3M-SWAP-CONVENTIONS'
                    }
                },
                'JPY-LIBOR-6M': {
                    'instruments': ['DEP', 'IRS'],
                    'single_curve': False,
                    'conventions': {
                        'DEP': 'JPY-DEPOSIT',
                        'IRS': 'JPY-6M-SWAP-CONVENTIONS'
                    }
                }
            }
        }
    }

    def generate(self, sensitivity_config: Dict[str, Any]) -> etree.Element:
        """
        Generate sensitivity XML from configuration dictionary.

        Args:
            sensitivity_config: Dictionary with sensitivity parameters
                - discount_curves: List of discount curve configs
                - index_curves: List of index curve configs
                - fx_spots: List of FX spot configs
                - fx_volatilities: List of FX vol configs
                - swaption_volatilities: List of swaption vol configs (optional)
                - credit_curves: List of credit curve configs (optional)
                - compute_gamma: Boolean (default False)
                - use_spreaded_term_structures: Boolean (default False)

        Returns:
            SensitivityAnalysis XML element

        Example config:
            {
                'discount_curves': [{
                    'ccy': 'EUR',
                    'shift_type': 'Absolute',
                    'shift_size': 0.0001,
                    'shift_scheme': 'Forward',
                    'shift_tenors': ['1Y', '5Y', '10Y']
                }],
                'index_curves': [{
                    'index': 'EUR-EURIBOR-6M',
                    'shift_type': 'Absolute',
                    'shift_size': 0.0001,
                    'shift_scheme': 'Forward',
                    'shift_tenors': ['1Y', '5Y']
                }],
                'fx_spots': [{
                    'ccypair': 'EURUSD',
                    'shift_type': 'Relative',
                    'shift_size': 0.01,
                    'shift_scheme': 'Central'
                }],
                'fx_volatilities': [{
                    'ccypair': 'EURUSD',
                    'shift_type': 'Relative',
                    'shift_size': 0.01,
                    'shift_scheme': 'Forward',
                    'shift_expiries': ['5Y'],
                    'shift_strikes': []  # Empty means ATM
                }],
                'compute_gamma': False,
                'use_spreaded_term_structures': False
            }
        """
        # Create root element
        sensitivity = etree.Element("SensitivityAnalysis")

        # Add discount curves
        if 'discount_curves' in sensitivity_config:
            discount_curves_elem = etree.SubElement(sensitivity, "DiscountCurves")
            for curve_config in sensitivity_config['discount_curves']:
                self._add_discount_curve(discount_curves_elem, curve_config)

        # Add yield curves (typically empty, but keep structure)
        etree.SubElement(sensitivity, "YieldCurves")

        # Add index curves
        if 'index_curves' in sensitivity_config:
            index_curves_elem = etree.SubElement(sensitivity, "IndexCurves")
            for curve_config in sensitivity_config['index_curves']:
                self._add_index_curve(index_curves_elem, curve_config)

        # Add FX spots
        if 'fx_spots' in sensitivity_config:
            fx_spots_elem = etree.SubElement(sensitivity, "FxSpots")
            for spot_config in sensitivity_config['fx_spots']:
                self._add_fx_spot(fx_spots_elem, spot_config)

        # Add credit curves (optional)
        if 'credit_curves' in sensitivity_config and len(sensitivity_config['credit_curves']) > 0:
            credit_curves_elem = etree.SubElement(sensitivity, "CreditCurves")
            for curve_config in sensitivity_config['credit_curves']:
                self._add_credit_curve(credit_curves_elem, curve_config)
            self._has_credit_curves = True

        # Add swaption volatilities (optional)
        if 'swaption_volatilities' in sensitivity_config:
            swaption_vols_elem = etree.SubElement(sensitivity, "SwaptionVolatilities")
            for vol_config in sensitivity_config['swaption_volatilities']:
                self._add_swaption_volatility(swaption_vols_elem, vol_config)

        # Add FX volatilities
        if 'fx_volatilities' in sensitivity_config:
            fx_vols_elem = etree.SubElement(sensitivity, "FxVolatilities")
            for vol_config in sensitivity_config['fx_volatilities']:
                self._add_fx_volatility(fx_vols_elem, vol_config)

        # Add cap/floor volatilities (typically empty)
        etree.SubElement(sensitivity, "CapFloorVolatilities")

        # Add ComputeGamma
        compute_gamma = sensitivity_config.get('compute_gamma', False)
        etree.SubElement(sensitivity, "ComputeGamma").text = str(compute_gamma).lower()

        # Add UseSpreadedTermStructures
        use_spreaded = sensitivity_config.get('use_spreaded_term_structures', False)
        etree.SubElement(sensitivity, "UseSpreadedTermStructures").text = str(use_spreaded).lower()

        return sensitivity

    def _add_discount_curve(self, parent: etree.Element, config: Dict[str, Any]) -> None:
        """
        Add a discount curve sensitivity configuration.

        Args:
            parent: DiscountCurves XML element
            config: Discount curve configuration dict
        """
        ccy = config['ccy']
        curve = etree.SubElement(parent, "DiscountCurve", ccy=ccy)

        etree.SubElement(curve, "ShiftType").text = config.get('shift_type', 'Absolute')
        etree.SubElement(curve, "ShiftSize").text = str(config.get('shift_size', 0.0001))
        etree.SubElement(curve, "ShiftScheme").text = config.get('shift_scheme', 'Forward')

        # ShiftTenors: convert list to comma-separated string
        tenors = config.get('shift_tenors', ['1Y', '5Y'])
        etree.SubElement(curve, "ShiftTenors").text = ', '.join(tenors)

        # Add ParConversion - use provided config or defaults
        if 'par_conversion' in config:
            self._add_par_conversion(curve, config['par_conversion'])
        elif ccy in self.DEFAULT_PAR_CONVERSIONS:
            # Use default ParConversion for this currency
            default_config = self.DEFAULT_PAR_CONVERSIONS[ccy]['discount']
            # Create instruments list matching number of tenors
            instruments = self._get_instruments_for_tenors(
                tenors, default_config['instruments']
            )

            par_config = {
                'instruments': instruments,
                'single_curve': default_config['single_curve'],
                'conventions': default_config['conventions']
            }
            self._add_par_conversion(curve, par_config)
        else:
            # Fallback for unknown currencies - use OIS by default
            instruments = ['OIS'] * len(tenors)
            par_config = {
                'instruments': instruments,
                'single_curve': True,
                'conventions': {
                    'OIS': f'{ccy}-OIS-CONVENTIONS'
                }
            }
            self._add_par_conversion(curve, par_config)

    def _add_index_curve(self, parent: etree.Element, config: Dict[str, Any]) -> None:
        """
        Add an index curve sensitivity configuration.

        Args:
            parent: IndexCurves XML element
            config: Index curve configuration dict
        """
        index = config['index']
        curve = etree.SubElement(parent, "IndexCurve", index=index)

        etree.SubElement(curve, "ShiftType").text = config.get('shift_type', 'Absolute')
        etree.SubElement(curve, "ShiftSize").text = str(config.get('shift_size', 0.0001))
        etree.SubElement(curve, "ShiftScheme").text = config.get('shift_scheme', 'Forward')

        # ShiftTenors
        tenors = config.get('shift_tenors', ['1Y', '5Y'])
        etree.SubElement(curve, "ShiftTenors").text = ', '.join(tenors)

        # Add ParConversion - use provided config or defaults
        if 'par_conversion' in config:
            self._add_par_conversion(curve, config['par_conversion'])
        else:
            # Try to find default for this index
            found = False
            for ccy, ccy_config in self.DEFAULT_PAR_CONVERSIONS.items():
                if 'index' in ccy_config and index in ccy_config['index']:
                    default_config = ccy_config['index'][index]
                    # Create instruments list matching number of tenors
                    instruments = self._get_instruments_for_tenors(
                        tenors, default_config['instruments']
                    )

                    par_config = {
                        'instruments': instruments,
                        'single_curve': default_config['single_curve'],
                        'discount_curve': default_config.get('discount_curve'),
                        'conventions': default_config['conventions']
                    }
                    self._add_par_conversion(curve, par_config)
                    found = True
                    break

            # Fallback: if no default found, create a generic ParConversion
            if not found:
                instruments = self._get_fallback_instruments_for_tenors(tenors, index)
                conventions = self._get_fallback_conventions_for_index(index)

                par_config = {
                    'instruments': instruments,
                    'single_curve': False,
                    'conventions': conventions
                }
                self._add_par_conversion(curve, par_config)

    def _add_fx_spot(self, parent: etree.Element, config: Dict[str, Any]) -> None:
        """
        Add an FX spot sensitivity configuration.

        Args:
            parent: FxSpots XML element
            config: FX spot configuration dict
        """
        spot = etree.SubElement(parent, "FxSpot", ccypair=config['ccypair'])

        etree.SubElement(spot, "ShiftType").text = config.get('shift_type', 'Relative')
        etree.SubElement(spot, "ShiftSize").text = str(config.get('shift_size', 0.01))
        etree.SubElement(spot, "ShiftScheme").text = config.get('shift_scheme', 'Central')

    def _add_fx_volatility(self, parent: etree.Element, config: Dict[str, Any]) -> None:
        """
        Add an FX volatility sensitivity configuration.

        Args:
            parent: FxVolatilities XML element
            config: FX volatility configuration dict
        """
        vol = etree.SubElement(parent, "FxVolatility", ccypair=config['ccypair'])

        etree.SubElement(vol, "ShiftType").text = config.get('shift_type', 'Relative')
        etree.SubElement(vol, "ShiftSize").text = str(config.get('shift_size', 0.01))
        etree.SubElement(vol, "ShiftScheme").text = config.get('shift_scheme', 'Forward')

        # ShiftExpiries
        expiries = config.get('shift_expiries', ['5Y'])
        etree.SubElement(vol, "ShiftExpiries").text = ', '.join(expiries)

        # ShiftStrikes - empty means ATM (At-The-Money)
        strikes = config.get('shift_strikes', [])
        if strikes and len(strikes) > 0:
            strikes_str = ', '.join([self._format_strike(s) for s in strikes])
            etree.SubElement(vol, "ShiftStrikes").text = strikes_str
        else:
            # Empty ShiftStrikes means ATM
            etree.SubElement(vol, "ShiftStrikes")

    def _add_swaption_volatility(self, parent: etree.Element, config: Dict[str, Any]) -> None:
        """
        Add a swaption volatility sensitivity configuration.

        Args:
            parent: SwaptionVolatilities XML element
            config: Swaption volatility configuration dict
        """
        vol = etree.SubElement(parent, "SwaptionVolatility", ccy=config['ccy'])

        etree.SubElement(vol, "ShiftType").text = config.get('shift_type', 'Relative')
        etree.SubElement(vol, "ShiftSize").text = str(config.get('shift_size', 0.01))
        etree.SubElement(vol, "ShiftScheme").text = config.get('shift_scheme', 'Forward')

        # ShiftExpiries
        expiries = config.get('shift_expiries', ['5Y'])
        etree.SubElement(vol, "ShiftExpiries").text = ', '.join(expiries)

        # ShiftTerms (must come before ShiftStrikes per ORE specification)
        terms = config.get('shift_terms', ['5Y'])
        etree.SubElement(vol, "ShiftTerms").text = ', '.join(terms)

        # ShiftStrikes
        strikes = config.get('shift_strikes', [0.0])
        strikes_str = ', '.join([self._format_strike(s) for s in strikes])
        etree.SubElement(vol, "ShiftStrikes").text = strikes_str

    def _add_credit_curve(self, parent: etree.Element, config: Dict[str, Any]) -> None:
        """
        Add a credit curve sensitivity configuration.

        Args:
            parent: CreditCurves XML element
            config: Credit curve configuration dict
        """
        curve = etree.SubElement(parent, "CreditCurve", name=config['name'])

        etree.SubElement(curve, "Currency").text = config.get('currency', 'USD')
        etree.SubElement(curve, "ShiftType").text = config.get('shift_type', 'Absolute')
        etree.SubElement(curve, "ShiftSize").text = str(config.get('shift_size', 0.0001))
        etree.SubElement(curve, "ShiftScheme").text = config.get('shift_scheme', 'Forward')

        # ShiftTenors
        tenors = config.get('shift_tenors', ['1Y', '5Y'])
        etree.SubElement(curve, "ShiftTenors").text = ', '.join(tenors)

        # Add ParConversion - use provided config or default CDS convention
        if 'par_conversion' in config:
            self._add_par_conversion(curve, config['par_conversion'])
        else:
            # Default ParConversion for credit curves using CDS
            instruments = ['CDS'] * len(tenors)
            par_config = {
                'instruments': instruments,
                'single_curve': False,
                'conventions': {
                    'CDS': 'CDS-STANDARD-CONVENTIONS'
                }
            }
            self._add_par_conversion(curve, par_config)

    def _get_instruments_for_tenors(
        self, tenors: List[str], default_instruments: List[str]
    ) -> List[str]:
        """
        Generate instrument list matching tenor count.

        Uses the default pattern and extends/cycles to match tenor count.

        Args:
            tenors: List of tenor strings
            default_instruments: Default instrument pattern

        Returns:
            List of instruments matching tenor count
        """
        if len(default_instruments) >= len(tenors):
            return default_instruments[:len(tenors)]

        # Repeat pattern to fill
        instruments = []
        for i, tenor in enumerate(tenors):
            instruments.append(default_instruments[i % len(default_instruments)])

        return instruments

    def _get_fallback_instruments_for_tenors(
        self, tenors: List[str], index: str
    ) -> List[str]:
        """
        Generate fallback instrument list for tenors when no default exists.

        Uses common pattern: DEP for short tenors, IRS for longer ones.

        Args:
            tenors: List of tenor strings
            index: Index name

        Returns:
            List of instruments
        """
        instruments = []
        for tenor in tenors:
            # Parse tenor to determine if short or long
            # Short tenors (<=1Y) use DEP, longer use IRS
            tenor_upper = tenor.upper().strip()
            if any(tenor_upper.endswith(unit) for unit in ['D', 'W', 'M']):
                # Days, weeks, months - use DEP
                instruments.append('DEP')
            elif tenor_upper.endswith('Y'):
                # Years - check if <= 1Y
                try:
                    years = int(tenor_upper[:-1])
                    if years <= 1:
                        instruments.append('DEP')
                    else:
                        instruments.append('IRS')
                except ValueError:
                    instruments.append('IRS')
            else:
                # Default to IRS
                instruments.append('IRS')

        return instruments

    def _get_fallback_conventions_for_index(self, index: str) -> Dict[str, str]:
        """
        Generate fallback conventions based on index name.

        Args:
            index: Index name (e.g., 'EUR-EURIBOR-3M')

        Returns:
            Dictionary of convention mappings
        """
        # Extract currency from index name
        parts = index.split('-')
        if len(parts) >= 1:
            ccy = parts[0].upper()
        else:
            ccy = 'EUR'

        # Extract index type and tenor
        if 'EURIBOR' in index:
            index_type = 'EURIBOR'
            if '3M' in index:
                tenor = '3M'
            elif '6M' in index:
                tenor = '6M'
            elif '1M' in index:
                tenor = '1M'
            else:
                tenor = '6M'
        elif 'LIBOR' in index:
            index_type = 'LIBOR'
            if '3M' in index:
                tenor = '3M'
            elif '6M' in index:
                tenor = '6M'
            else:
                tenor = '3M'
        elif 'EONIA' in index:
            return {
                'OIS': f'{ccy}-OIS-CONVENTIONS'
            }
        elif 'SONIA' in index or 'FedFunds' in index:
            return {
                'DEP': f'{ccy}-DEPOSIT',
                'OIS': f'{ccy}-OIS-CONVENTIONS'
            }
        else:
            # Generic fallback
            return {
                'DEP': f'{ccy}-DEPOSIT',
                'IRS': f'{ccy}-SWAP-CONVENTIONS'
            }

        # EURIBOR or LIBOR conventions
        if index_type == 'EURIBOR':
            return {
                'DEP': f'{ccy}-EURIBOR-CONVENTIONS',
                'IRS': f'{ccy}-{tenor}-SWAP-CONVENTIONS',
                'OIS': f'{ccy}-OIS-CONVENTIONS'
            }
        else:  # LIBOR
            return {
                'DEP': f'{ccy}-LIBOR-CONVENTIONS',
                'IRS': f'{ccy}-{tenor}-SWAP-CONVENTIONS'
            }

    def _add_par_conversion(self, parent: etree.Element, par_config: Dict[str, Any]) -> None:
        """
        Add ParConversion section to a curve.

        Args:
            parent: Curve XML element (DiscountCurve, IndexCurve, etc.)
            par_config: ParConversion configuration dict
        """
        par_conv = etree.SubElement(parent, "ParConversion")

        # Instruments
        instruments = par_config.get('instruments', [])
        etree.SubElement(par_conv, "Instruments").text = ', '.join(instruments)

        # SingleCurve
        single_curve = par_config.get('single_curve', True)
        etree.SubElement(par_conv, "SingleCurve").text = str(single_curve).lower()

        # DiscountCurve (for index curves with multi-curve setup)
        if 'discount_curve' in par_config:
            etree.SubElement(par_conv, "DiscountCurve").text = par_config['discount_curve']

        # Conventions
        if 'conventions' in par_config:
            conventions_elem = etree.SubElement(par_conv, "Conventions")
            for conv_id, conv_name in par_config['conventions'].items():
                etree.SubElement(conventions_elem, "Convention", id=conv_id).text = conv_name

    def _format_strike(self, strike: float) -> str:
        """
        Format strike value with consistent precision.

        Args:
            strike: Strike value

        Returns:
            Formatted strike string
        """
        # Format with 16 decimal places to match template
        return f"{strike:.16f}"

    def save_to_file(self, sensitivity: etree.Element, output_path: Path) -> None:
        """
        Save sensitivity XML to file.

        Args:
            sensitivity: SensitivityAnalysis XML element
            output_path: Path to output file
        """
        tree = etree.ElementTree(sensitivity)
        tree.write(
            str(output_path),
            encoding='utf-8',
            xml_declaration=True,
            pretty_print=True
        )

    def has_credit_curves(self) -> bool:
        """
        Check if credit curves were included in the generated sensitivity config.

        Returns:
            True if credit curves are present, False otherwise
        """
        return self._has_credit_curves
