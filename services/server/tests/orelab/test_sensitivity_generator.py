"""
Unit tests for SensitivityGenerator ParConversion functionality.

Tests ensure that ParConversion sections are properly generated for
discount curves and index curves, including fallback mechanisms.
"""

import pytest
from lxml import etree
from project.orelab.xml_generators.sensitivity import SensitivityGenerator


class TestSensitivityGeneratorParConversion:
    """Test ParConversion generation in sensitivity configurations."""

    def test_index_curve_with_default_parconversion(self):
        """Test that index curves get ParConversion from defaults."""
        generator = SensitivityGenerator()

        config = {
            'index_curves': [{
                'index': 'EUR-EURIBOR-3M',
                'shift_type': 'Absolute',
                'shift_size': 0.0001,
                'shift_scheme': 'Forward',
                'shift_tenors': ['6M', '1Y', '2Y', '5Y', '10Y']
            }]
        }

        sensitivity_xml = generator.generate(config)
        xml_string = etree.tostring(sensitivity_xml, pretty_print=True).decode('utf-8')

        # Verify structure exists
        assert '<IndexCurves>' in xml_string
        assert '<IndexCurve index="EUR-EURIBOR-3M">' in xml_string

        # Verify ParConversion exists
        assert '<ParConversion>' in xml_string
        assert '<Instruments>' in xml_string
        assert '<SingleCurve>' in xml_string
        assert '<Conventions>' in xml_string

        # Verify correct number of instruments (should match tenors)
        instruments_elem = sensitivity_xml.find('.//IndexCurves/IndexCurve/ParConversion/Instruments')
        assert instruments_elem is not None
        instruments = [i.strip() for i in instruments_elem.text.split(',')]
        assert len(instruments) == 5, f"Expected 5 instruments for 5 tenors, got {len(instruments)}"

        # Verify conventions are present
        conventions = sensitivity_xml.findall('.//IndexCurves/IndexCurve/ParConversion/Conventions/Convention')
        assert len(conventions) > 0, "No conventions found in ParConversion"

        print(f"[OK] EUR-EURIBOR-3M ParConversion generated with {len(instruments)} instruments")

    def test_index_curve_fallback_parconversion(self):
        """Test fallback ParConversion for unknown indices."""
        generator = SensitivityGenerator()

        config = {
            'index_curves': [{
                'index': 'CHF-LIBOR-3M',  # Not in defaults
                'shift_type': 'Absolute',
                'shift_size': 0.0001,
                'shift_scheme': 'Forward',
                'shift_tenors': ['6M', '1Y', '2Y', '5Y']
            }]
        }

        sensitivity_xml = generator.generate(config)
        xml_string = etree.tostring(sensitivity_xml, pretty_print=True).decode('utf-8')

        # Verify fallback ParConversion was added
        assert '<ParConversion>' in xml_string
        assert '<Instruments>' in xml_string

        # Verify correct number of instruments
        instruments_elem = sensitivity_xml.find('.//IndexCurves/IndexCurve/ParConversion/Instruments')
        assert instruments_elem is not None
        instruments = [i.strip() for i in instruments_elem.text.split(',')]
        assert len(instruments) == 4, f"Expected 4 instruments for 4 tenors, got {len(instruments)}"

        # Verify fallback conventions
        conventions = sensitivity_xml.findall('.//IndexCurves/IndexCurve/ParConversion/Conventions/Convention')
        assert len(conventions) > 0, "No fallback conventions found"

        print(f"[OK] CHF-LIBOR-3M fallback ParConversion generated with {len(instruments)} instruments")

    def test_discount_curve_parconversion(self):
        """Test ParConversion for discount curves."""
        generator = SensitivityGenerator()

        config = {
            'discount_curves': [{
                'ccy': 'EUR',
                'shift_type': 'Absolute',
                'shift_size': 0.0001,
                'shift_scheme': 'Forward',
                'shift_tenors': ['6M', '1Y', '2Y', '5Y', '10Y']
            }]
        }

        sensitivity_xml = generator.generate(config)
        xml_string = etree.tostring(sensitivity_xml, pretty_print=True).decode('utf-8')

        # Verify ParConversion exists
        assert '<DiscountCurves>' in xml_string
        assert '<ParConversion>' in xml_string

        # Verify instruments count matches tenors
        instruments_elem = sensitivity_xml.find('.//DiscountCurves/DiscountCurve/ParConversion/Instruments')
        assert instruments_elem is not None
        instruments = [i.strip() for i in instruments_elem.text.split(',')]
        assert len(instruments) == 5

        print(f"[OK] EUR discount curve ParConversion generated with {len(instruments)} instruments")

    def test_multiple_indices_parconversion(self):
        """Test multiple index curves with ParConversion."""
        generator = SensitivityGenerator()

        config = {
            'index_curves': [
                {
                    'index': 'EUR-EURIBOR-3M',
                    'shift_type': 'Absolute',
                    'shift_size': 0.0001,
                    'shift_scheme': 'Forward',
                    'shift_tenors': ['1Y', '5Y']
                },
                {
                    'index': 'USD-LIBOR-3M',
                    'shift_type': 'Absolute',
                    'shift_size': 0.0001,
                    'shift_scheme': 'Forward',
                    'shift_tenors': ['1Y', '5Y', '10Y']
                }
            ]
        }

        sensitivity_xml = generator.generate(config)

        # Find all index curves
        index_curves = sensitivity_xml.findall('.//IndexCurves/IndexCurve')
        assert len(index_curves) == 2

        # Verify each has ParConversion
        for curve in index_curves:
            par_conversion = curve.find('ParConversion')
            assert par_conversion is not None

            instruments_elem = par_conversion.find('Instruments')
            assert instruments_elem is not None

            tenors_elem = curve.find('ShiftTenors')
            tenor_count = len([t.strip() for t in tenors_elem.text.split(',')])
            instrument_count = len([i.strip() for i in instruments_elem.text.split(',')])

            assert tenor_count == instrument_count, \
                f"Tenor count ({tenor_count}) != Instrument count ({instrument_count})"

        print("[OK] Multiple index curves with ParConversion validated")

    def test_swaption_volatility_without_parconversion(self):
        """Test that swaption volatilities don't get ParConversion."""
        generator = SensitivityGenerator()

        config = {
            'swaption_volatilities': [{
                'ccy': 'EUR',
                'shift_type': 'Relative',
                'shift_size': 0.01,
                'shift_scheme': 'Forward',
                'shift_expiries': ['2Y'],
                'shift_terms': ['10Y'],
                'shift_strikes': [0.0]
            }]
        }

        sensitivity_xml = generator.generate(config)
        xml_string = etree.tostring(sensitivity_xml, pretty_print=True).decode('utf-8')

        # Verify swaption vol exists
        assert '<SwaptionVolatilities>' in xml_string

        # Verify NO ParConversion for swaption vols (they don't need it)
        swaption_vol = sensitivity_xml.find('.//SwaptionVolatilities/SwaptionVolatility')
        assert swaption_vol is not None
        par_conversion = swaption_vol.find('ParConversion')
        assert par_conversion is None, "SwaptionVolatility should not have ParConversion"

        print("[OK] SwaptionVolatility correctly has no ParConversion")

    def test_instruments_for_various_tenors(self):
        """Test instrument selection for different tenor patterns."""
        generator = SensitivityGenerator()

        # Test short tenors (should use DEP)
        short_instruments = generator._get_fallback_instruments_for_tenors(
            ['1M', '3M', '6M'], 'TEST-INDEX'
        )
        assert all(i == 'DEP' for i in short_instruments), \
            f"Short tenors should use DEP, got {short_instruments}"

        # Test long tenors (should use IRS)
        long_instruments = generator._get_fallback_instruments_for_tenors(
            ['2Y', '5Y', '10Y'], 'TEST-INDEX'
        )
        assert all(i == 'IRS' for i in long_instruments), \
            f"Long tenors should use IRS, got {long_instruments}"

        # Test mixed tenors
        mixed_instruments = generator._get_fallback_instruments_for_tenors(
            ['6M', '1Y', '2Y', '5Y'], 'TEST-INDEX'
        )
        assert mixed_instruments[0] == 'DEP', "6M should be DEP"
        assert mixed_instruments[1] == 'DEP', "1Y should be DEP"
        assert mixed_instruments[2] == 'IRS', "2Y should be IRS"
        assert mixed_instruments[3] == 'IRS', "5Y should be IRS"

        print(f"[OK] Instrument selection works correctly for various tenor patterns")


if __name__ == '__main__':
    # Run tests with verbose output
    pytest.main([__file__, '-v', '-s'])
