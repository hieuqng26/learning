from flask import request
from flask_jwt_extended import jwt_required

from project.api.utils import validate_request
from project.api.auth.utils import prevent_multiple_logins_per_user
from project.api.calculation.routes import calculate
from project.api.calculation.ORETrade.utils import execute_trade_calculation
from project.logger import get_logger

from project.qld.ORETrade.fx.fxforward import FXForward
from project.qld.ORETrade.fx.fxoption import FXOption


logger = get_logger(__name__)


@calculate.route('/fx/fxforward', methods=['POST'], endpoint='calculate_fx_fxforward')
@jwt_required()
@prevent_multiple_logins_per_user()
@validate_request(allowed_keys=['data'])
def calculate_fx_forward():
    trade_data = request.get_json().get('data', {})
    trade = FXForward(
        evaluation_date=trade_data.get('evaluation_date'),
        value_date=trade_data.get('value_date'),
        bought_currency=trade_data.get('bought_currency'),
        bought_amount=trade_data.get('bought_amount'),
        sold_currency=trade_data.get('sold_currency'),
        sold_amount=trade_data.get('sold_amount'),
        settlement=trade_data.get('settlement', 'Physical'),
        settlement_currency=trade_data.get('settlement_currency'),
        fx_index=trade_data.get('fx_index'),
        settlement_date=trade_data.get('settlement_date'),
        payment_lag=trade_data.get('payment_lag'),
        payment_calendar=trade_data.get('payment_calendar'),
        payment_convention=trade_data.get('payment_convention')
    )
    return execute_trade_calculation(trade, trade_data, 'fx_forward')


@calculate.route('/fx/fxoption', methods=['POST'], endpoint='calculate_fx_fxoption')
@jwt_required()
@prevent_multiple_logins_per_user()
@validate_request(allowed_keys=['data'])
def calculate_fx_option():
    trade_data = request.get_json().get('data', {})
    trade = FXOption(
        evaluation_date=trade_data.get('evaluation_date'),
        bought_currency=trade_data.get('bought_currency'),
        bought_amount=trade_data.get('bought_amount'),
        sold_currency=trade_data.get('sold_currency'),
        sold_amount=trade_data.get('sold_amount'),
        long_short=trade_data.get('long_short'),
        option_type=trade_data.get('option_type'),
        style=trade_data.get('style'),
        exercise_date=trade_data.get('exercise_date'),
        settlement=trade_data.get('settlement', 'Cash'),
        payoff_at_expiry=trade_data.get('payoff_at_expiry', False),
        premium_amount=trade_data.get('premium_amount'),
        premium_currency=trade_data.get('premium_currency'),
        premium_pay_date=trade_data.get('premium_pay_date')
    )
    return execute_trade_calculation(trade, trade_data, 'fx_option')
