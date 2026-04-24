"""
Scenario/Stress Test XML generator.

Generates scenarios.xml for stress testing with actual stressed NPVs.
"""

from lxml import etree
from pathlib import Path
from typing import Dict, List, Optional, Any


class ScenarioGenerator:
    """
    Generate scenarios.xml from scenario configuration.

    Creates stress test scenarios for ORE stress testing analytic.
    Unlike sensitivity analysis (which gives deltas), stress testing
    gives actual stressed NPVs for each scenario.
    """

    def __init__(self):
        """Initialize ScenarioGenerator."""
        pass

    def generate(self, scenario_config: Dict[str, Any]) -> etree.Element:
        """
        Generate stress test XML from configuration dictionary.

        Args:
            scenario_config: Dictionary with scenario/stress test parameters
                - use_spreaded_term_structures: Optional boolean (default: False)
                - scenarios: List of scenario configurations, each containing:
                    - id: Scenario identifier
                    - description: Optional description
                    - discount_curves: List of discount curve shifts (optional)
                      Required format: shifts (array) + shift_tenors (array)
                    - index_curves: List of index curve shifts (optional)
                      Required format: shifts (array) + shift_tenors (array)
                    - fx_spots: List of FX spot shifts (optional)
                      Format: shift_size (single value)
                    - fx_volatilities: List of FX vol shifts (optional)
                      Required format: shifts (array) + shift_expiries (array)
                    - equity_spots: List of equity spot shifts (optional)
                      Format: shift_size (single value)
                    - swaption_volatilities: List of swaption vol shifts (optional)
                      Format: complex shift structure with nested Shift elements

        Returns:
            StressTesting XML element (ORE format)

        Example config:
            {
                'use_spreaded_term_structures': False,
                'scenarios': [
                    {
                        'id': 'EUR_rates_up_100bp',
                        'description': 'EUR rates parallel shift +100bp',
                        'discount_curves': [{
                            'ccy': 'EUR',
                            'shift_type': 'Absolute',
                            'shifts': [0.01, 0.01, 0.01],
                            'shift_tenors': ['1Y', '5Y', '10Y']
                        }]
                    },
                    {
                        'id': 'EURUSD_down_10pct',
                        'description': 'EUR/USD down 10%',
                        'fx_spots': [{
                            'ccypair': 'EURUSD',
                            'shift_type': 'Relative',
                            'shift_size': -0.10
                        }]
                    }
                ]
            }
        """
        # Create root element (changed from StressTestData)
        stress_testing = etree.Element("StressTesting")

        # Add UseSpreadedTermStructures parameter
        use_spreaded = scenario_config.get('use_spreaded_term_structures', False)
        etree.SubElement(stress_testing, "UseSpreadedTermStructures").text = str(use_spreaded).lower()

        # Add scenarios directly to root (no StressTests wrapper)
        scenarios = scenario_config.get('scenarios', [])
        for scenario in scenarios:
            self._add_stress_test(stress_testing, scenario)

        return stress_testing

    def _add_stress_test(self, parent: etree.Element, scenario: Dict[str, Any]) -> None:
        """
        Add a stress test scenario.

        Args:
            parent: StressTesting XML element (root)
            scenario: Scenario configuration dict
        """
        scenario_id = scenario['id']
        stress_test = etree.SubElement(parent, "StressTest", id=scenario_id)

        # Add description if provided
        if 'description' in scenario:
            etree.SubElement(stress_test, "Description").text = scenario['description']

        # Remove Market wrapper - add risk factor groups directly to stress_test
        # All 14 risk factor groups must be present for ORE compatibility

        # 1. DiscountCurves (implemented)
        self._add_discount_curves_group(stress_test, scenario.get('discount_curves', []))

        # 2. IndexCurves (implemented)
        self._add_index_curves_group(stress_test, scenario.get('index_curves', []))

        # 3. YieldCurves (empty placeholder)
        etree.SubElement(stress_test, "YieldCurves")

        # 4. FxSpots (implemented)
        self._add_fx_spots_group(stress_test, scenario.get('fx_spots', []))

        # 5. FxVolatilities (implemented)
        self._add_fx_volatilities_group(stress_test, scenario.get('fx_volatilities', []))

        # 6. SwaptionVolatilities (implemented)
        self._add_swaption_volatilities_group(stress_test, scenario.get('swaption_volatilities', []))

        # 7. CapFloorVolatilities (empty placeholder)
        etree.SubElement(stress_test, "CapFloorVolatilities")

        # 8. EquitySpots (implemented)
        self._add_equity_spots_group(stress_test, scenario.get('equity_spots', []))

        # 9. EquityVolatilities (empty placeholder)
        etree.SubElement(stress_test, "EquityVolatilities")

        # 10. CommodityCurves (empty placeholder)
        etree.SubElement(stress_test, "CommodityCurves")

        # 11. CommodityVolatilities (empty placeholder)
        etree.SubElement(stress_test, "CommodityVolatilities")

        # 12. SecuritySpreads (empty placeholder)
        etree.SubElement(stress_test, "SecuritySpreads")

        # 13. RecoveryRates (empty placeholder)
        etree.SubElement(stress_test, "RecoveryRates")

        # 14. SurvivalProbabilities (empty placeholder)
        etree.SubElement(stress_test, "SurvivalProbabilities")

    def _add_discount_curves_group(self, parent: etree.Element, curves: List[Dict[str, Any]]) -> None:
        """Create DiscountCurves wrapper and add all discount curve shifts."""
        curves_elem = etree.SubElement(parent, "DiscountCurves")
        for curve_config in curves:
            self._add_discount_curve(curves_elem, curve_config)

    def _add_index_curves_group(self, parent: etree.Element, curves: List[Dict[str, Any]]) -> None:
        """Create IndexCurves wrapper and add all index curve shifts."""
        curves_elem = etree.SubElement(parent, "IndexCurves")
        for curve_config in curves:
            self._add_index_curve(curves_elem, curve_config)

    def _add_fx_spots_group(self, parent: etree.Element, spots: List[Dict[str, Any]]) -> None:
        """Create FxSpots wrapper and add all FX spot shifts."""
        spots_elem = etree.SubElement(parent, "FxSpots")
        for spot_config in spots:
            self._add_fx_spot(spots_elem, spot_config)

    def _add_fx_volatilities_group(self, parent: etree.Element, vols: List[Dict[str, Any]]) -> None:
        """Create FxVolatilities wrapper and add all FX volatility shifts."""
        vols_elem = etree.SubElement(parent, "FxVolatilities")
        for vol_config in vols:
            self._add_fx_volatility(vols_elem, vol_config)

    def _add_swaption_volatilities_group(self, parent: etree.Element, vols: List[Dict[str, Any]]) -> None:
        """Create SwaptionVolatilities wrapper and add all swaption volatility shifts."""
        vols_elem = etree.SubElement(parent, "SwaptionVolatilities")
        for vol_config in vols:
            self._add_swaption_volatility(vols_elem, vol_config)

    def _add_equity_spots_group(self, parent: etree.Element, spots: List[Dict[str, Any]]) -> None:
        """Create EquitySpots wrapper and add all equity spot shifts."""
        spots_elem = etree.SubElement(parent, "EquitySpots")
        for spot_config in spots:
            self._add_equity_spot(spots_elem, spot_config)

    def _add_discount_curve(self, parent: etree.Element, config: Dict[str, Any]) -> None:
        """
        Add a discount curve shift.

        Args:
            parent: DiscountCurves XML element
            config: Discount curve shift configuration
                Required: ccy, shifts, shift_tenors
                Optional: shift_type (default: Absolute)
        """
        # Use attribute for currency identifier (not child element)
        curve = etree.SubElement(parent, "DiscountCurve", ccy=config['ccy'])

        etree.SubElement(curve, "ShiftType").text = config.get('shift_type', 'Absolute')

        # Require shifts and shift_tenors arrays (no backward compatibility)
        shifts_str = ','.join([str(s) for s in config['shifts']])
        etree.SubElement(curve, "Shifts").text = shifts_str

        tenors_str = ','.join(config['shift_tenors'])
        etree.SubElement(curve, "ShiftTenors").text = tenors_str

    def _add_index_curve(self, parent: etree.Element, config: Dict[str, Any]) -> None:
        """
        Add an index curve shift.

        Args:
            parent: IndexCurves XML element
            config: Index curve shift configuration
                Required: index, shifts, shift_tenors
                Optional: shift_type (default: Absolute)
        """
        # Use attribute for index identifier (not child element)
        curve = etree.SubElement(parent, "IndexCurve", index=config['index'])

        etree.SubElement(curve, "ShiftType").text = config.get('shift_type', 'Absolute')

        # Require shifts and shift_tenors arrays (no backward compatibility)
        shifts_str = ','.join([str(s) for s in config['shifts']])
        etree.SubElement(curve, "Shifts").text = shifts_str

        tenors_str = ','.join(config['shift_tenors'])
        etree.SubElement(curve, "ShiftTenors").text = tenors_str

    def _add_fx_spot(self, parent: etree.Element, config: Dict[str, Any]) -> None:
        """
        Add an FX spot shift.

        Args:
            parent: FxSpots XML element
            config: FX spot shift configuration
                Required: ccypair, shift_size
                Optional: shift_type (default: Relative)
        """
        # Use attribute for currency pair identifier (not child element)
        spot = etree.SubElement(parent, "FxSpot", ccypair=config['ccypair'])

        etree.SubElement(spot, "ShiftType").text = config.get('shift_type', 'Relative')
        etree.SubElement(spot, "ShiftSize").text = str(config.get('shift_size', 0.01))

    def _add_fx_volatility(self, parent: etree.Element, config: Dict[str, Any]) -> None:
        """
        Add an FX volatility shift.

        Args:
            parent: FxVolatilities XML element
            config: FX volatility shift configuration
                Required: ccypair, shifts, shift_expiries
                Optional: shift_type (default: Absolute)
        """
        # Use attribute for currency pair identifier (not child element)
        vol = etree.SubElement(parent, "FxVolatility", ccypair=config['ccypair'])

        etree.SubElement(vol, "ShiftType").text = config.get('shift_type', 'Absolute')

        # Require shifts and shift_expiries arrays (no backward compatibility)
        shifts_str = ','.join([str(s) for s in config['shifts']])
        etree.SubElement(vol, "Shifts").text = shifts_str

        expiries_str = ','.join(config['shift_expiries'])
        etree.SubElement(vol, "ShiftExpiries").text = expiries_str

    def _add_equity_spot(self, parent: etree.Element, config: Dict[str, Any]) -> None:
        """
        Add an equity spot shift.

        Args:
            parent: EquitySpots XML element
            config: Equity spot shift configuration
                Required: equity, shift_size
                Optional: shift_type (default: Relative)
        """
        # Use attribute for equity identifier (not child element)
        equity = etree.SubElement(parent, "EquitySpot", equity=config['equity'])

        etree.SubElement(equity, "ShiftType").text = config.get('shift_type', 'Relative')
        etree.SubElement(equity, "ShiftSize").text = str(config.get('shift_size', 0.01))

    def _add_swaption_volatility(self, parent: etree.Element, config: Dict[str, Any]) -> None:
        """
        Add a swaption volatility shift.

        SwaptionVolatilities use complex nested shift structure:
        <Shifts>
          <Shift>0.0010</Shift>  <!-- Default shift -->
          <Shift expiry="1Y" term="5Y">0.0010</Shift>  <!-- Point-specific -->
        </Shifts>

        Args:
            parent: SwaptionVolatilities XML element
            config: Swaption volatility shift configuration
                Required: ccy, shifts
                Optional: shift_type (default: Absolute), shift_expiries, shift_terms

                shifts format: List of dicts with 'value' and optional 'expiry'/'term'
                Example: [
                    {'value': 0.001},
                    {'expiry': '1Y', 'term': '5Y', 'value': 0.001}
                ]
        """
        # Use attribute for currency identifier (not child element)
        vol = etree.SubElement(parent, "SwaptionVolatility", ccy=config['ccy'])

        etree.SubElement(vol, "ShiftType").text = config.get('shift_type', 'Absolute')

        # Create Shifts container with nested Shift elements
        shifts_elem = etree.SubElement(vol, "Shifts")

        shifts = config.get('shifts', [])
        if isinstance(shifts, list) and len(shifts) > 0:
            for shift in shifts:
                if isinstance(shift, dict):
                    # Check if this is a point-specific shift with expiry/term
                    if 'expiry' in shift and 'term' in shift:
                        shift_elem = etree.SubElement(
                            shifts_elem, "Shift",
                            expiry=shift['expiry'],
                            term=shift['term']
                        )
                        shift_elem.text = str(shift['value'])
                    else:
                        # Default shift (no attributes)
                        shift_elem = etree.SubElement(shifts_elem, "Shift")
                        shift_elem.text = str(shift.get('value', 0.001))

        # Add ShiftExpiries and ShiftTerms if provided
        if 'shift_expiries' in config:
            expiries_str = ','.join(config['shift_expiries'])
            etree.SubElement(vol, "ShiftExpiries").text = expiries_str

        if 'shift_terms' in config:
            terms_str = ','.join(config['shift_terms'])
            etree.SubElement(vol, "ShiftTerms").text = terms_str

    def save_to_file(self, stress_test_data: etree.Element, output_path: Path) -> None:
        """
        Save stress test XML to file.

        Args:
            stress_test_data: StressTestData XML element
            output_path: Path to output file
        """
        tree = etree.ElementTree(stress_test_data)
        tree.write(
            str(output_path),
            encoding='utf-8',
            xml_declaration=True,
            pretty_print=True
        )
