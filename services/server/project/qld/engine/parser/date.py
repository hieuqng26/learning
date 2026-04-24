import QuantLib as ql
import datetime as dt
import pandas as pd
import numpy as np
from dateutil import parser


def parse_date(date):
    """
    Parse date from various formats and return QuantLib Date.

    Args:
        date: Can be string, datetime.datetime, or pandas timestamp

    Returns:
        ql.Date: QuantLib Date object

    Raises:
        ValueError: If date cannot be parsed
    """
    if isinstance(date, str):
        try:
            # Use dateutil parser for robust string parsing
            parsed_datetime = parser.parse(date)
            return ql.Date(parsed_datetime.day, parsed_datetime.month, parsed_datetime.year)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Cannot parse date string '{date}': {e}")

    elif isinstance(date, dt.datetime):
        return ql.Date(date.day, date.month, date.year)

    elif isinstance(date, dt.date):
        return ql.Date(date.day, date.month, date.year)

    elif isinstance(date, pd.Timestamp):
        return ql.Date(date.day, date.month, date.year)

    elif hasattr(date, 'to_pydatetime'):  # pandas datetime-like objects
        py_date = date.to_pydatetime()
        return ql.Date(py_date.day, py_date.month, py_date.year)

    elif isinstance(date, ql.Date):
        # Already a QuantLib Date
        return date

    else:
        raise ValueError(f"Unsupported date type: {type(date)}. Expected string, datetime, or pandas timestamp.")


def ql2pydate(ql_date):
    """
    Convert QuantLib Date to Python datetime.date.

    Args:
        ql_date (ql.Date): QuantLib Date object

    Returns:
        datetime.date: Corresponding Python date object
    """
    if not isinstance(ql_date, ql.Date):
        raise ValueError(f"Input must be a QuantLib Date, got {type(ql_date)}")

    return dt.date(ql_date.year(), ql_date.month(), ql_date.dayOfMonth())


def ql2npdate(ql_date):
    """
    Convert QuantLib Date to numpy datetime64.

    Args:
        ql_date (ql.Date): QuantLib Date object

    Returns:
        numpy.datetime64: Corresponding numpy datetime64 object
    """
    py_date = ql2pydate(ql_date)
    return np.datetime64(py_date)
