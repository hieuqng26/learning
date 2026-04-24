from ..fx.fxspot import FXSpot


class COMSpot(FXSpot):
    __name__ = "COMSpot"

    def __init__(self, evaluation_date, ticker, currency, notional, calendar,
                 settlement_date_or_tenor, strike, discounting):
        domestic_currency = currency
        foreign_currency = ticker
        notional_currency = ticker
        domestic_discounting = discounting
        foreign_discounting = f"{ticker}.FUTURE.CSA_{currency}"
        super().__init__(evaluation_date, domestic_currency, notional_currency, foreign_currency, notional, calendar,
                         settlement_date_or_tenor, strike, domestic_discounting, foreign_discounting)
