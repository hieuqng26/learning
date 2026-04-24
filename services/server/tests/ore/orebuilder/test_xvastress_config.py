"""
Tests for xvaStress analytic configuration.

Verifies that the xvaStress analytic is properly configured in ore.xml.
"""
from project.orelab.xml_generators.ore_config import OREConfigGenerator
from lxml import etree
from pathlib import Path


def test_xvastress_analytic_exists_in_template():
    """Verify xvaStress analytic exists in template ore.xml."""
    template_path = Path(__file__).parent.parent.parent.parent / "project" / "data" / "ORE" / "Input" / "ore.xml"

    # Parse template
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(str(template_path), parser)
    root = tree.getroot()

    # Find xvaStress analytic
    analytics = root.find("Analytics")
    assert analytics is not None, "Analytics section should exist"

    xvastress_analytic = None
    for analytic in analytics.findall("Analytic"):
        if analytic.get("type") == "xvaStress":
            xvastress_analytic = analytic
            break

    assert xvastress_analytic is not None, "xvaStress analytic should exist in template"

    # Verify required parameters
    assert xvastress_analytic.find("Parameter[@name='active']") is not None, "active parameter should exist"
    assert xvastress_analytic.find("Parameter[@name='marketConfigFile']") is not None, "marketConfigFile parameter should exist"
    assert xvastress_analytic.find("Parameter[@name='stressConfigFile']") is not None, "stressConfigFile parameter should exist"
    assert xvastress_analytic.find("Parameter[@name='writeCubes']") is not None, "writeCubes parameter should exist"
    assert xvastress_analytic.find("Parameter[@name='baseCurrency']") is not None, "baseCurrency parameter should exist"

    print("✓ xvaStress analytic exists in template with all required parameters")


def test_xvastress_config_enabled_with_scenario():
    """Verify xvaStress analytic is enabled when scenario_file and xvasensimarket_file are provided."""
    template_path = Path(__file__).parent.parent.parent.parent / "project" / "data" / "ORE" / "Input" / "ore.xml"

    # Create generator with template
    generator = OREConfigGenerator(template_path)
    generator.load_template()

    # Update paths with scenario and xvasensimarket files
    generator.update_paths(
        input_path="Input",
        output_path="Output",
        scenario_file="scenarios.xml",
        xvasensimarket_file="xvasensimarket.xml"
    )

    # Verify xvaStress analytic is enabled
    root = generator._config_tree.getroot()
    analytics = root.find("Analytics")

    xvastress_analytic = None
    for analytic in analytics.findall("Analytic"):
        if analytic.get("type") == "xvaStress":
            xvastress_analytic = analytic
            break

    assert xvastress_analytic is not None, "xvaStress analytic should exist"

    # Check active status
    active_param = xvastress_analytic.find("Parameter[@name='active']")
    assert active_param is not None, "active parameter should exist"
    assert active_param.text == "Y", "xvaStress should be enabled when scenario_file and xvasensimarket_file provided"

    # Check config files
    market_config_param = xvastress_analytic.find("Parameter[@name='marketConfigFile']")
    assert market_config_param is not None, "marketConfigFile parameter should exist"
    assert market_config_param.text == "xvasensimarket.xml", "marketConfigFile should be set correctly"

    stress_config_param = xvastress_analytic.find("Parameter[@name='stressConfigFile']")
    assert stress_config_param is not None, "stressConfigFile parameter should exist"
    assert stress_config_param.text == "scenarios.xml", "stressConfigFile should be set correctly"

    print("✓ xvaStress analytic is properly enabled with scenario configuration")


def test_xvastress_config_disabled_without_scenario():
    """Verify xvaStress analytic is disabled when no scenario_file is provided."""
    template_path = Path(__file__).parent.parent.parent.parent / "project" / "data" / "ORE" / "Input" / "ore.xml"

    # Create generator with template
    generator = OREConfigGenerator(template_path)
    generator.load_template()

    # Update paths without scenario file
    generator.update_paths(
        input_path="Input",
        output_path="Output"
    )

    # Verify xvaStress analytic is disabled
    root = generator._config_tree.getroot()
    analytics = root.find("Analytics")

    xvastress_analytic = None
    for analytic in analytics.findall("Analytic"):
        if analytic.get("type") == "xvaStress":
            xvastress_analytic = analytic
            break

    assert xvastress_analytic is not None, "xvaStress analytic should exist"

    # Check active status
    active_param = xvastress_analytic.find("Parameter[@name='active']")
    assert active_param is not None, "active parameter should exist"
    assert active_param.text == "N", "xvaStress should be disabled when scenario_file not provided"

    print("✓ xvaStress analytic is properly disabled without scenario configuration")


def test_xvastress_base_currency_update():
    """Verify xvaStress base currency is updated by set_base_currency method."""
    template_path = Path(__file__).parent.parent.parent.parent / "project" / "data" / "ORE" / "Input" / "ore.xml"

    # Create generator with template
    generator = OREConfigGenerator(template_path)
    generator.load_template()

    # Set base currency
    generator.set_base_currency("USD")

    # Verify xvaStress base currency is updated
    root = generator._config_tree.getroot()
    analytics = root.find("Analytics")

    xvastress_analytic = None
    for analytic in analytics.findall("Analytic"):
        if analytic.get("type") == "xvaStress":
            xvastress_analytic = analytic
            break

    assert xvastress_analytic is not None, "xvaStress analytic should exist"

    # Check base currency
    base_currency_param = xvastress_analytic.find("Parameter[@name='baseCurrency']")
    assert base_currency_param is not None, "baseCurrency parameter should exist"
    assert base_currency_param.text == "USD", "xvaStress baseCurrency should be updated to USD"

    print("✓ xvaStress base currency is properly updated")


if __name__ == "__main__":
    test_xvastress_analytic_exists_in_template()
    test_xvastress_config_enabled_with_scenario()
    test_xvastress_config_disabled_without_scenario()
    test_xvastress_base_currency_update()
    print("\nAll xvaStress configuration tests passed!")
