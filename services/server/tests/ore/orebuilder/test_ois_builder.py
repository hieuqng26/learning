"""
Test OvernightIndexSwapBuilder XML generation.
"""

from lxml import etree
from project.orelab.trade_builders.oiswap import OvernightIndexSwapBuilder


def test_ois_builder_basic():
    """Test OvernightIndexSwapBuilder generates correct XML structure."""
    # Data from portfolio.xml - OIS
    trade_data = {
        'TradeId': 'OIS',
        'CounterParty': 'CPTY_A',
        'Currency': 'EUR',
        'Notional': 100000000,
        'Payer': 'false',
        'StartDate': '2023-01-31',
        'EndDate': '2028-02-01',
        'Tenor': '3M',
        'Calendar': 'US',
        'Convention': 'MF',
        'FloatingIndex': 'EUR-EONIA',
        'FloatingSpread': 0.000122,
        'IsInArrears': 'false',
        'FixingDays': 2,
        'DayCounter': 'A360',
        'PaymentConvention': 'MF'
    }

    builder = OvernightIndexSwapBuilder(trade_data)
    trade_xml = builder.build()

    # Verify XML structure
    assert trade_xml.tag == 'Trade'
    assert trade_xml.get('id') == 'OIS'

    # Verify TradeType
    trade_type = trade_xml.find('TradeType')
    assert trade_type is not None
    assert trade_type.text == 'Swap'

    # Verify Envelope
    envelope = trade_xml.find('Envelope')
    assert envelope is not None
    assert envelope.find('CounterParty').text == 'CPTY_A'

    # Verify SwapData exists
    swap_data = trade_xml.find('SwapData')
    assert swap_data is not None

    # Verify single floating leg
    legs = swap_data.findall('LegData')
    assert len(legs) == 1

    leg = legs[0]
    assert leg.find('LegType').text == 'Floating'
    assert leg.find('Payer').text == 'false'
    assert leg.find('Currency').text == 'EUR'
    assert leg.find('DayCounter').text == 'A360'
    assert leg.find('PaymentConvention').text == 'MF'

    # Verify Notional
    notionals = leg.find('Notionals')
    assert notionals is not None
    assert notionals.find('Notional').text == '100000000'

    # Verify FloatingLegData
    floating_data = leg.find('FloatingLegData')
    assert floating_data is not None
    assert floating_data.find('Index').text == 'EUR-EONIA'
    assert floating_data.find('IsInArrears').text == 'false'
    assert floating_data.find('FixingDays').text == '2'

    # Verify Spreads
    spreads = floating_data.find('Spreads')
    assert spreads is not None
    assert spreads.find('Spread').text == '0.000122'

    # Verify ScheduleData
    schedule_data = leg.find('ScheduleData')
    assert schedule_data is not None
    rules = schedule_data.find('Rules')
    assert rules is not None
    # Dates are formatted as YYYYMMDD by format_date_for_ore()
    assert rules.find('StartDate').text == '20230131'
    assert rules.find('EndDate').text == '20280201'
    assert rules.find('Tenor').text == '3M'
    assert rules.find('Calendar').text == 'US'
    assert rules.find('Convention').text == 'MF'


def test_ois_builder_xml_string():
    """Test OvernightIndexSwapBuilder generates valid XML string."""
    trade_data = {
        'TradeId': 'OIS_TEST',
        'CounterParty': 'CPTY_A',
        'Currency': 'EUR',
        'Notional': 100000000,
        'Payer': False,
        'StartDate': '2023-01-31',
        'EndDate': '2028-02-01',
        'Tenor': '3M',
        'FloatingIndex': 'EUR-EONIA',
        'DayCounter': 'A360',
    }

    builder = OvernightIndexSwapBuilder(trade_data)
    xml_string = builder.to_xml_string()

    # Verify we can parse the XML string
    root = etree.fromstring(xml_string.encode('utf-8'))
    assert root.tag == 'Trade'
    assert root.get('id') == 'OIS_TEST'


def test_ois_builder_payer_conversion():
    """Test OvernightIndexSwapBuilder correctly handles payer boolean conversion."""
    # Test with string 'true'
    trade_data = {
        'TradeId': 'OIS_PAYER',
        'CounterParty': 'CPTY_A',
        'Currency': 'EUR',
        'Notional': 100000000,
        'Payer': 'true',  # String
        'StartDate': '2023-01-31',
        'EndDate': '2028-02-01',
        'Tenor': '3M',
        'FloatingIndex': 'EUR-EONIA',
        'DayCounter': 'A360',
    }

    builder = OvernightIndexSwapBuilder(trade_data)
    trade_xml = builder.build()

    leg = trade_xml.find('.//LegData')
    assert leg.find('Payer').text == 'true'

    # Test with boolean True
    trade_data['Payer'] = True
    builder = OvernightIndexSwapBuilder(trade_data)
    trade_xml = builder.build()

    leg = trade_xml.find('.//LegData')
    assert leg.find('Payer').text == 'true'


if __name__ == "__main__":
    test_ois_builder_basic()
    test_ois_builder_xml_string()
    test_ois_builder_payer_conversion()
    print("All OIS builder tests passed!")
