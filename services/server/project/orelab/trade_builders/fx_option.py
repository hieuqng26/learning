"""
FX Option trade builder.
"""

from lxml import etree
from .base import BaseTradeBuilder, ValidationResult
from ..utils import format_date_for_ore
from ..config import DEFAULTS


class FxOptionBuilder(BaseTradeBuilder):
    """
    Build FX Option trade XML.
    """

    REQUIRED_COLUMNS = [
        "TradeId", "CounterParty", "ExerciseDate",
        "LongShort", "OptionType", "Style",
        "BoughtCurrency", "BoughtAmount",
        "SoldCurrency", "SoldAmount"
    ]

    def validate(self) -> ValidationResult:
        """Validate FX Option trade data."""
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

        # Validate option parameters
        long_short = str(self.trade_data.get("LongShort", "")).lower()
        if long_short not in ["long", "short"]:
            result.add_error(f"Invalid LongShort: {self.trade_data.get('LongShort')} (expected Long or Short)")

        option_type = str(self.trade_data.get("OptionType", "")).lower()
        if option_type not in ["call", "put"]:
            result.add_error(f"Invalid OptionType: {self.trade_data.get('OptionType')} (expected Call or Put)")

        style = str(self.trade_data.get("Style", "european")).lower()
        if style not in ["european", "american", "bermudan"]:
            result.add_warning(f"Unusual option style: {self.trade_data.get('Style')}")

        # Validate exercise date
        self._validate_date(self.trade_data.get("ExerciseDate"), "ExerciseDate", result)

        return result

    def build(self) -> etree.Element:
        """
        Build FX Option trade XML element.

        Returns:
            XML Element for FX Option trade
        """
        # Create root Trade element
        trade = etree.Element("Trade", id=self._get_required("TradeId"))

        # TradeType
        etree.SubElement(trade, "TradeType").text = "FxOption"

        # Envelope
        self._create_envelope(trade)

        # FxOptionData
        fx_opt_data = etree.SubElement(trade, "FxOptionData")

        # OptionData section
        option_data = etree.SubElement(fx_opt_data, "OptionData")

        # LongShort
        long_short = self._get_required("LongShort")
        etree.SubElement(option_data, "LongShort").text = str(long_short)

        # OptionType
        option_type = self._get_required("OptionType")
        etree.SubElement(option_data, "OptionType").text = str(option_type)

        # Style
        style = self._get_optional("Style", "European")
        etree.SubElement(option_data, "Style").text = str(style)

        # Settlement
        settlement = self._get_optional("Settlement", DEFAULTS["Settlement"])
        etree.SubElement(option_data, "Settlement").text = str(settlement)

        # PayOffAtExpiry
        payoff = self._get_optional("PayOffAtExpiry", DEFAULTS["PayOffAtExpiry"])
        etree.SubElement(option_data, "PayOffAtExpiry").text = str(payoff).lower()

        # ExerciseDates - support both single date and multiple dates
        exercise_dates_elem = etree.SubElement(option_data, "ExerciseDates")
        exercise_date = self._get_required("ExerciseDate")

        # Handle both single date (string) and multiple dates (list)
        if isinstance(exercise_date, list):
            for date in exercise_date:
                date_formatted = format_date_for_ore(date)
                etree.SubElement(exercise_dates_elem, "ExerciseDate").text = date_formatted
        else:
            date_formatted = format_date_for_ore(exercise_date)
            etree.SubElement(exercise_dates_elem, "ExerciseDate").text = date_formatted

        # Premiums (optional) - support multiple premiums
        premium_amount = self._get_optional("PremiumAmount")
        if premium_amount is not None:
            premiums_elem = etree.SubElement(option_data, "Premiums")

            # Handle both single premium and multiple premiums
            premium_currency = self._get_optional("PremiumCurrency")
            premium_pay_date = self._get_optional("PremiumPayDate")

            if isinstance(premium_amount, list):
                # Multiple premiums
                for i, amt in enumerate(premium_amount):
                    premium_elem = etree.SubElement(premiums_elem, "Premium")
                    etree.SubElement(premium_elem, "Amount").text = str(amt)

                    # Get corresponding currency and pay date
                    ccy = premium_currency[i] if isinstance(premium_currency, list) else premium_currency
                    pay_date = premium_pay_date[i] if isinstance(premium_pay_date, list) else premium_pay_date

                    etree.SubElement(premium_elem, "Currency").text = str(ccy)
                    etree.SubElement(premium_elem, "PayDate").text = format_date_for_ore(pay_date)
            else:
                # Single premium
                premium_elem = etree.SubElement(premiums_elem, "Premium")
                etree.SubElement(premium_elem, "Amount").text = str(premium_amount)
                etree.SubElement(premium_elem, "Currency").text = str(premium_currency)
                etree.SubElement(premium_elem, "PayDate").text = format_date_for_ore(premium_pay_date)

        # BoughtCurrency and BoughtAmount
        bought_ccy = self._get_required("BoughtCurrency")
        bought_amt = self._get_required("BoughtAmount")
        etree.SubElement(fx_opt_data, "BoughtCurrency").text = str(bought_ccy)
        etree.SubElement(fx_opt_data, "BoughtAmount").text = str(bought_amt)

        # SoldCurrency and SoldAmount
        sold_ccy = self._get_required("SoldCurrency")
        sold_amt = self._get_required("SoldAmount")
        etree.SubElement(fx_opt_data, "SoldCurrency").text = str(sold_ccy)
        etree.SubElement(fx_opt_data, "SoldAmount").text = str(sold_amt)

        return trade
