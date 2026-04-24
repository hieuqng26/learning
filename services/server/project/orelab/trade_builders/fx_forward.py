"""
FX Forward trade builder.
"""

from lxml import etree
from .base import BaseTradeBuilder, ValidationResult
from ..utils import format_date_for_ore


class FxForwardBuilder(BaseTradeBuilder):
    """
    Build FX Forward trade XML.

    Optional fields:
    - Settlement (default: Physical)

    Cash settlement fields (only if Settlement='Cash'):
    - SettlementCurrency
    - FXIndex
    - SettlementDate (optional)
    - PaymentLag (optional)
    - PaymentCalendar (optional)
    - PaymentConvention (optional)
    """

    REQUIRED_COLUMNS = [
        "TradeId", "CounterParty", "ValueDate",
        "BoughtCurrency", "BoughtAmount",
        "SoldCurrency", "SoldAmount"
    ]

    def validate(self) -> ValidationResult:
        """Validate FX Forward trade data."""
        result = ValidationResult()

        # Check required fields first
        self._validate_required_fields(result)
        if not result.is_valid:
            return result

        # Validate currencies
        bought_ccy = self.trade_data.get("BoughtCurrency", "")
        sold_ccy = self.trade_data.get("SoldCurrency", "")

        self._validate_currency(bought_ccy, "BoughtCurrency", result)
        self._validate_currency(sold_ccy, "SoldCurrency", result)

        if bought_ccy == sold_ccy:
            result.add_error("Bought and sold currencies must be different")

        # Validate amounts
        self._validate_numeric(self.trade_data.get("BoughtAmount", 0), "BoughtAmount", result)
        self._validate_numeric(self.trade_data.get("SoldAmount", 0), "SoldAmount", result)

        # Validate date
        self._validate_date(self.trade_data.get("ValueDate"), "ValueDate", result)

        return result

    def build(self) -> etree.Element:
        """
        Build FX Forward trade XML element.

        Returns:
            XML Element for FX Forward trade
        """
        # Create root Trade element
        trade = etree.Element("Trade", id=self._get_required("TradeId"))

        # TradeType
        etree.SubElement(trade, "TradeType").text = "FxForward"

        # Envelope
        self._create_envelope(trade)

        # FxForwardData
        fx_data = etree.SubElement(trade, "FxForwardData")

        # ValueDate
        value_date = self._get_required("ValueDate")
        value_date_formatted = format_date_for_ore(value_date)
        etree.SubElement(fx_data, "ValueDate").text = value_date_formatted

        # BoughtCurrency and BoughtAmount
        bought_ccy = self._get_required("BoughtCurrency")
        bought_amt = self._get_required("BoughtAmount")
        etree.SubElement(fx_data, "BoughtCurrency").text = str(bought_ccy)
        etree.SubElement(fx_data, "BoughtAmount").text = str(bought_amt)

        # SoldCurrency and SoldAmount
        sold_ccy = self._get_required("SoldCurrency")
        sold_amt = self._get_required("SoldAmount")
        etree.SubElement(fx_data, "SoldCurrency").text = str(sold_ccy)
        etree.SubElement(fx_data, "SoldAmount").text = str(sold_amt)

        # Settlement
        settlement = self._get_optional("Settlement", "Physical")
        etree.SubElement(fx_data, "Settlement").text = str(settlement)

        # SettlementData (only for cash settlement)
        if settlement == 'Cash':
            self._create_settlement_data(fx_data)

        return trade

    def _create_settlement_data(self, fx_data: etree.Element) -> None:
        """Create settlement data for cash-settled FX forward."""
        settlement_data = etree.SubElement(fx_data, "SettlementData")

        # Currency
        settlement_ccy = self._get_required("SettlementCurrency", "Settlement currency")
        etree.SubElement(settlement_data, "Currency").text = str(settlement_ccy)

        # FXIndex
        fx_index = self._get_required("FXIndex", "FX index")
        etree.SubElement(settlement_data, "FXIndex").text = str(fx_index)

        # Date (optional)
        settlement_date = self._get_optional("SettlementDate")
        if settlement_date:
            date_formatted = format_date_for_ore(settlement_date)
            etree.SubElement(settlement_data, "Date").text = date_formatted

        # Rules (optional)
        payment_lag = self._get_optional("PaymentLag")
        payment_calendar = self._get_optional("PaymentCalendar")
        payment_convention = self._get_optional("PaymentConvention")

        if payment_lag or payment_calendar or payment_convention:
            rules = etree.SubElement(settlement_data, "Rules")

            if payment_lag:
                etree.SubElement(rules, "PaymentLag").text = str(payment_lag)

            if payment_calendar:
                etree.SubElement(rules, "PaymentCalendar").text = str(payment_calendar)

            if payment_convention:
                etree.SubElement(rules, "PaymentConvention").text = str(payment_convention)
