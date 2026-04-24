"""
Test FxForwardBuilder XML generation with settlement data.
"""

from lxml import etree
from project.orelab.trade_builders.fx_forward import FxForwardBuilder


def test_fxforward_builder_cash_settlement():
    """Test FxForwardBuilder generates correct XML for cash settlement."""
    # Data from portfolio.xml - FXFWD_EURUSD_10Y (cash settlement)
    trade_data = {
        'TradeId': 'FXFWD_EURUSD_10Y',
        'CounterParty': 'CPTY_A',
        'ValueDate': '2033-02-20',
        'BoughtCurrency': 'EUR',
        'BoughtAmount': 1000000,
        'SoldCurrency': 'USD',
        'SoldAmount': 1100000,
        'Settlement': 'Cash',
        'SettlementCurrency': 'USD',
        'FXIndex': 'FX-TR20H-EUR-USD',
        'SettlementDate': '2033-02-24',
        'PaymentLag': '2D',
        'PaymentCalendar': 'USD',
        'PaymentConvention': 'Following'
    }

    builder = FxForwardBuilder(trade_data)
    trade_xml = builder.build()

    # Verify XML structure
    assert trade_xml.tag == 'Trade'
    assert trade_xml.get('id') == 'FXFWD_EURUSD_10Y'

    # Verify TradeType
    trade_type = trade_xml.find('TradeType')
    assert trade_type is not None
    assert trade_type.text == 'FxForward'

    # Verify FxForwardData
    fx_data = trade_xml.find('FxForwardData')
    assert fx_data is not None
    assert fx_data.find('ValueDate').text == '20330220'
    assert fx_data.find('BoughtCurrency').text == 'EUR'
    assert fx_data.find('BoughtAmount').text == '1000000'
    assert fx_data.find('SoldCurrency').text == 'USD'
    assert fx_data.find('SoldAmount').text == '1100000'
    assert fx_data.find('Settlement').text == 'Cash'

    # Verify SettlementData
    settlement_data = fx_data.find('SettlementData')
    assert settlement_data is not None
    assert settlement_data.find('Currency').text == 'USD'
    assert settlement_data.find('FXIndex').text == 'FX-TR20H-EUR-USD'
    assert settlement_data.find('Date').text == '20330224'

    # Verify Rules
    rules = settlement_data.find('Rules')
    assert rules is not None
    assert rules.find('PaymentLag').text == '2D'
    assert rules.find('PaymentCalendar').text == 'USD'
    assert rules.find('PaymentConvention').text == 'Following'


def test_fxforward_builder_physical_settlement():
    """Test FxForwardBuilder generates correct XML for physical settlement."""
    trade_data = {
        'TradeId': 'FXFWD_PHYSICAL',
        'CounterParty': 'CPTY_A',
        'ValueDate': '2033-02-20',
        'BoughtCurrency': 'EUR',
        'BoughtAmount': 1000000,
        'SoldCurrency': 'USD',
        'SoldAmount': 1100000,
        'Settlement': 'Physical'
    }

    builder = FxForwardBuilder(trade_data)
    trade_xml = builder.build()

    # Verify XML structure
    assert trade_xml.tag == 'Trade'
    assert trade_xml.get('id') == 'FXFWD_PHYSICAL'

    # Verify FxForwardData
    fx_data = trade_xml.find('FxForwardData')
    assert fx_data is not None
    assert fx_data.find('Settlement').text == 'Physical'

    # Verify NO SettlementData for physical settlement
    settlement_data = fx_data.find('SettlementData')
    assert settlement_data is None


def test_fxforward_builder_default_settlement():
    """Test FxForwardBuilder uses Physical as default settlement."""
    trade_data = {
        'TradeId': 'FXFWD_DEFAULT',
        'CounterParty': 'CPTY_A',
        'ValueDate': '2033-02-20',
        'BoughtCurrency': 'EUR',
        'BoughtAmount': 1000000,
        'SoldCurrency': 'USD',
        'SoldAmount': 1100000,
        # No Settlement specified
    }

    builder = FxForwardBuilder(trade_data)
    trade_xml = builder.build()

    # Verify default settlement is Physical
    fx_data = trade_xml.find('FxForwardData')
    assert fx_data is not None
    assert fx_data.find('Settlement').text == 'Physical'


if __name__ == "__main__":
    test_fxforward_builder_cash_settlement()
    test_fxforward_builder_physical_settlement()
    test_fxforward_builder_default_settlement()
    print("All FX Forward builder tests passed!")
