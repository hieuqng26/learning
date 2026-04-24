"""
Configuration constants for ORELab Excel-to-ORE converter.
"""

from pathlib import Path

# Base paths
ORELAB_ROOT = Path(__file__).parent.parent / "data" / "ORE"
INPUT_PATH = ORELAB_ROOT / "Input"
STATIC_PATH = INPUT_PATH / "Static"
OUTPUT_PATH = ORELAB_ROOT / "Output"

# Default values
DEFAULTS = {
    "PaymentConvention": "MF",  # Modified Following
    "Calendar": "TARGET",
    "Convention": "MF",
    "TermConvention": "MF",
    "Rule": "Forward",
    "FixingDays": 2,
    "IsInArrears": False,
    "Settlement": "Cash",
    "PayOffAtExpiry": False,
    # Netting defaults
    "CSAThreshold": 0.0,
    "CSAMta": 0.0,
    "CollateralCurrency": "EUR",
    "MarginCallFrequency": "1D",
    "MarginPostFrequency": "1D"
}

# Date format
DATE_FORMAT = "%Y%m%d"
DATE_FORMAT_DISPLAY = "%Y-%m-%d"

# Temp folder prefix
TEMP_FOLDER_PREFIX = "temp_"

# Validation settings
VALIDATION_SETTINGS = {
    "skip_invalid_trades": True,
    "warn_on_skip": True,
    "strict_mode": False  # If True, raise exception on invalid trade
}
