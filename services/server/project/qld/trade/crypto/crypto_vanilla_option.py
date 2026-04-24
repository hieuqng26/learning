from ..fx.fx_vanilla_option import FXVanillaOption


class CRYPTOVanillaOption(FXVanillaOption):
    __name__ = "CRYPTOVanillaOption"

    def __init__(self, evaluation_date, ticker, currency, notional, expiry_date, calendar,
                 settlement_tenor, option_type, strike, settlement_type, discounting):
        domestic_currency = currency
        foreign_currency = ticker
        notional_currency = ticker
        domestic_discounting = discounting
        foreign_discounting = f"{ticker}.FUTURE.CSA_{currency}"
        fx_vol_surface = f"{ticker}{currency}.FXVOLSURFACE"
        super().__init__(evaluation_date, domestic_currency, notional_currency, foreign_currency, notional, expiry_date, calendar,
                         settlement_tenor, option_type, strike, settlement_type, domestic_discounting, foreign_discounting, fx_vol_surface)
