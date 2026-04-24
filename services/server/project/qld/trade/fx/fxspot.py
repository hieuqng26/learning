from .fxforward import FXForward


class FXSpot(FXForward):
    __name__ = "FXSpot"

    def __init__(self, evaluation_date, domestic_currency, notional_currency, foreign_currency, notional, calendar,
                 settlement_date_or_tenor, strike, domestic_discounting, foreign_discounting):
        super().__init__(evaluation_date, domestic_currency, notional_currency, foreign_currency, notional, calendar,
                         settlement_date_or_tenor, strike, domestic_discounting, foreign_discounting)
