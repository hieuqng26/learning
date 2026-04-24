"""
Trade builders for generating ORE XML from trade data.
"""

from .base import BaseTradeBuilder, ValidationResult
from .fx_forward import FxForwardBuilder
from .fx_option import FxOptionBuilder
from .irswap import InterestRateSwapBuilder
from .cross_currency_swap import CrossCurrencySwapBuilder
from .oiswap import OvernightIndexSwapBuilder
from .swaption import SwaptionBuilder

__all__ = [
    "BaseTradeBuilder",
    "ValidationResult",
    "FxForwardBuilder",
    "FxOptionBuilder",
    "InterestRateSwapBuilder",
    "CrossCurrencySwapBuilder",
    "OvernightIndexSwapBuilder",
    "SwaptionBuilder",
]

TradeBuilders = {
    "FxForward": FxForwardBuilder,
    "FxOption": FxOptionBuilder,
    "CrossCurrencySwap": CrossCurrencySwapBuilder,
    "InterestRateSwap": InterestRateSwapBuilder,
    "OvernightIndexSwap": OvernightIndexSwapBuilder,
    "Swaption": SwaptionBuilder,
}
