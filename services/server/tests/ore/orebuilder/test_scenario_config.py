"""
Tests for ScenarioGenerator XML structure validation.

Verifies that the generated XML matches the ORE stress testing format.
"""
from project.orelab.xml_generators import ScenarioGenerator
from lxml import etree


def test_scenario_xml_structure():
    """Verify scenario XML matches ORE stress testing format."""
    scenario_config = {
        'use_spreaded_term_structures': False,
        'scenarios': [
            {
                'id': 'test_scenario',
                'description': 'Test scenario',
                'discount_curves': [{
                    'ccy': 'EUR',
                    'shift_type': 'Absolute',
                    'shifts': [0.01, 0.01, 0.01],
                    'shift_tenors': ['1Y', '5Y', '10Y']
                }],
                'index_curves': [{
                    'index': 'EUR-EURIBOR-6M',
                    'shift_type': 'Absolute',
                    'shifts': [0.01, 0.01],
                    'shift_tenors': ['1Y', '5Y']
                }],
                'fx_spots': [{
                    'ccypair': 'USDEUR',
                    'shift_type': 'Relative',
                    'shift_size': 0.01
                }],
                'fx_volatilities': [{
                    'ccypair': 'USDEUR',
                    'shift_type': 'Absolute',
                    'shifts': [0.1, 0.1, 0.1],
                    'shift_expiries': ['1Y', '2Y', '3Y']
                }],
                'equity_spots': [{
                    'equity': 'SP5',
                    'shift_type': 'Relative',
                    'shift_size': 0.05
                }],
                'swaption_volatilities': [{
                    'ccy': 'EUR',
                    'shift_type': 'Absolute',
                    'shifts': [
                        {'value': 0.001},
                        {'expiry': '1Y', 'term': '5Y', 'value': 0.001}
                    ],
                    'shift_expiries': ['1Y', '5Y'],
                    'shift_terms': ['5Y']
                }]
            }
        ]
    }

    generator = ScenarioGenerator()
    xml_elem = generator.generate(scenario_config)

    # Verify root element
    assert xml_elem.tag == "StressTesting", "Root should be StressTesting"

    # Verify UseSpreadedTermStructures
    use_spreaded = xml_elem.find("UseSpreadedTermStructures")
    assert use_spreaded is not None, "UseSpreadedTermStructures should exist"
    assert use_spreaded.text == "true", "UseSpreadedTermStructures should be 'true'"

    # Verify no StressTests wrapper
    assert xml_elem.find("StressTests") is None, "Should not have StressTests wrapper"

    # Get first stress test
    stress_test = xml_elem.find("StressTest")
    assert stress_test is not None, "StressTest should exist"
    assert stress_test.get('id') == 'test_scenario', "StressTest should have id attribute"

    # Verify all 14 risk factor groups present
    required_groups = [
        'DiscountCurves', 'IndexCurves', 'YieldCurves',
        'FxSpots', 'FxVolatilities', 'SwaptionVolatilities',
        'CapFloorVolatilities', 'EquitySpots', 'EquityVolatilities',
        'CommodityCurves', 'CommodityVolatilities',
        'SecuritySpreads', 'RecoveryRates', 'SurvivalProbabilities'
    ]
    for group in required_groups:
        assert stress_test.find(group) is not None, f"Missing {group}"

    # Verify DiscountCurve uses attribute and arrays
    discount_curves = stress_test.find("DiscountCurves")
    discount_curve = discount_curves.find("DiscountCurve")
    assert discount_curve.get('ccy') == 'EUR', "DiscountCurve should use ccy attribute"
    shifts = discount_curve.find("Shifts")
    assert shifts is not None, "Shifts should exist"
    assert shifts.text == '0.01,0.01,0.01', "Shifts should be comma-separated"
    shift_tenors = discount_curve.find("ShiftTenors")
    assert shift_tenors is not None, "ShiftTenors should exist"
    assert shift_tenors.text == '1Y,5Y,10Y', "ShiftTenors should be comma-separated"

    # Verify IndexCurve uses attribute
    index_curves = stress_test.find("IndexCurves")
    index_curve = index_curves.find("IndexCurve")
    assert index_curve.get('index') == 'EUR-EURIBOR-6M', "IndexCurve should use index attribute"

    # Verify FxSpot uses attribute and ShiftSize
    fx_spots = stress_test.find("FxSpots")
    fx_spot = fx_spots.find("FxSpot")
    assert fx_spot.get('ccypair') == 'USDEUR', "FxSpot should use ccypair attribute"
    assert fx_spot.find("ShiftSize") is not None, "FxSpot should have ShiftSize"

    # Verify FxVolatility uses arrays
    fx_vols = stress_test.find("FxVolatilities")
    fx_vol = fx_vols.find("FxVolatility")
    assert fx_vol.get('ccypair') == 'USDEUR', "FxVolatility should use ccypair attribute"
    fx_vol_shifts = fx_vol.find("Shifts")
    assert fx_vol_shifts is not None, "FxVolatility should have Shifts"
    assert fx_vol_shifts.text == '0.1,0.1,0.1', "FxVolatility Shifts should be comma-separated"

    # Verify SwaptionVolatility has nested Shift elements
    swaption_vols = stress_test.find("SwaptionVolatilities")
    swaption_vol = swaption_vols.find("SwaptionVolatility")
    assert swaption_vol.get('ccy') == 'EUR', "SwaptionVolatility should use ccy attribute"
    swaption_shifts = swaption_vol.find("Shifts")
    assert swaption_shifts is not None, "SwaptionVolatility should have Shifts container"
    shift_elems = swaption_shifts.findall("Shift")
    assert len(shift_elems) == 2, "Should have 2 Shift elements"
    # Check first shift has no attributes (default)
    assert not shift_elems[0].attrib, "First Shift should have no attributes"
    # Check second shift has expiry and term attributes
    assert shift_elems[1].get('expiry') == '1Y', "Second Shift should have expiry"
    assert shift_elems[1].get('term') == '5Y', "Second Shift should have term"

    # Verify empty placeholders
    assert len(stress_test.find("YieldCurves")) == 0, "YieldCurves should be empty"
    assert len(stress_test.find("CapFloorVolatilities")) == 0, "CapFloorVolatilities should be empty"
    assert len(stress_test.find("SecuritySpreads")) == 0, "SecuritySpreads should be empty"

    print("✓ All XML structure validations passed")


if __name__ == "__main__":
    test_scenario_xml_structure()
    print("All tests passed!")
