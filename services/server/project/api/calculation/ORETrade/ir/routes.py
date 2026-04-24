from flask import request
from flask_jwt_extended import jwt_required

from project.api.utils import validate_request
from project.api.auth.utils import prevent_multiple_logins_per_user
from project.api.calculation.routes import calculate
from project.api.calculation.ORETrade.utils import execute_trade_calculation
from project.logger import get_logger

from project.qld.ORETrade.ir.oiswap import OISwap
from project.qld.ORETrade.ir.irswap import IRSwap
from project.qld.ORETrade.ir.cross_currency_swap import CrossCurrencySwap
from project.qld.ORETrade.ir.swaption import Swaption


logger = get_logger(__name__)


@calculate.route('/ir/oiswap', methods=['POST'], endpoint='calculate_ir_oiswap')
@jwt_required()
@prevent_multiple_logins_per_user()
@validate_request(allowed_keys=['data'])
def calculate_ir_oiswap():
    trade_data = request.get_json().get('data', {})
    trade = OISwap(
        evaluation_date=trade_data.get('evaluation_date'),
        currency=trade_data.get('currency'),
        notional=trade_data.get('notional'),
        payer=trade_data.get('payer', False),
        start_date=trade_data.get('start_date'),
        end_date=trade_data.get('end_date'),
        tenor=trade_data.get('tenor'),
        calendar=trade_data.get('calendar'),
        convention=trade_data.get('convention'),
        index=trade_data.get('index'),
        spread=trade_data.get('spread', 0.0),
        is_in_arrears=trade_data.get('is_in_arrears', False),
        fixing_days=trade_data.get('fixing_days', 2),
        day_counter=trade_data.get('day_counter'),
        payment_convention=trade_data.get('payment_convention')
    )
    return execute_trade_calculation(trade, trade_data, 'ir_oiswap')


@calculate.route('/ir/irswap', methods=['POST'], endpoint='calculate_ir_irswap')
@jwt_required()
@prevent_multiple_logins_per_user()
@validate_request(allowed_keys=['data'])
def calculate_ir_irswap():
    trade_data = request.get_json().get('data', {})
    trade = IRSwap(
        evaluation_date=trade_data.get('evaluation_date'),
        currency=trade_data.get('currency'),
        notional=trade_data.get('notional'),
        start_date=trade_data.get('start_date'),
        end_date=trade_data.get('end_date'),
        fixed_payer=trade_data.get('fixed_payer', True),
        fixed_rate=trade_data.get('fixed_rate'),
        fixed_tenor=trade_data.get('fixed_tenor'),
        fixed_day_counter=trade_data.get('fixed_day_counter'),
        floating_payer=trade_data.get('floating_payer', False),
        floating_index=trade_data.get('floating_index'),
        floating_tenor=trade_data.get('floating_tenor'),
        floating_day_counter=trade_data.get('floating_day_counter'),
        floating_spread=trade_data.get('floating_spread', 0.0),
        is_in_arrears=trade_data.get('is_in_arrears', False),
        fixing_days=trade_data.get('fixing_days', 2),
        calendar=trade_data.get('calendar'),
        payment_convention=trade_data.get('payment_convention')
    )
    return execute_trade_calculation(trade, trade_data, 'ir_irswap')


@calculate.route('/ir/crosscurrencyswap', methods=['POST'], endpoint='calculate_ir_crosscurrencyswap')
@jwt_required()
@prevent_multiple_logins_per_user()
@validate_request(allowed_keys=['data'])
def calculate_cross_currency_swap():
    trade_data = request.get_json().get('data', {})
    trade = CrossCurrencySwap(
        evaluation_date=trade_data.get('evaluation_date'),
        start_date=trade_data.get('start_date'),
        end_date=trade_data.get('end_date'),
        currency1=trade_data.get('currency1'),
        notional1=trade_data.get('notional1'),
        index1=trade_data.get('index1'),
        spread1=trade_data.get('spread1'),
        tenor1=trade_data.get('tenor1'),
        day_counter1=trade_data.get('day_counter1'),
        currency2=trade_data.get('currency2'),
        notional2=trade_data.get('notional2'),
        index2=trade_data.get('index2'),
        spread2=trade_data.get('spread2'),
        tenor2=trade_data.get('tenor2'),
        day_counter2=trade_data.get('day_counter2'),
        initial_exchange=trade_data.get('initial_exchange'),
        final_exchange=trade_data.get('final_exchange'),
        calendar=trade_data.get('calendar'),
        payment_convention=trade_data.get('payment_convention'),
        is_in_arrears=trade_data.get('is_in_arrears', False),
        fixing_days=trade_data.get('fixing_days', 2)
    )
    return execute_trade_calculation(trade, trade_data, 'cross_currency_swap')


@calculate.route('/ir/swaption', methods=['POST'], endpoint='calculate_ir_swaption')
@jwt_required()
@prevent_multiple_logins_per_user()
@validate_request(allowed_keys=['data'])
def calculate_swaption():
    """Calculate Swaption pricing and exposures."""
    trade_data = request.get_json().get('data', {})
    trade = Swaption(
        evaluation_date=trade_data.get('evaluation_date'),
        # Option parameters
        exercise_style=trade_data.get('exercise_style'),
        exercise_dates=trade_data.get('exercise_dates'),
        long_short=trade_data.get('long_short'),
        settlement_type=trade_data.get('settlement_type'),
        payer_receiver=trade_data.get('payer_receiver'),
        # Premium parameters (optional)
        premium_amount=trade_data.get('premium_amount'),
        premium_currency=trade_data.get('premium_currency'),
        premium_pay_date=trade_data.get('premium_pay_date'),
        # Underlying swap parameters
        currency=trade_data.get('currency'),
        notional=trade_data.get('notional'),
        start_date=trade_data.get('start_date'),
        end_date=trade_data.get('end_date'),
        # Fixed leg parameters
        fixed_rate=trade_data.get('fixed_rate'),
        fixed_tenor=trade_data.get('fixed_tenor'),
        fixed_day_counter=trade_data.get('fixed_day_counter'),
        # Floating leg parameters
        floating_index=trade_data.get('floating_index'),
        floating_tenor=trade_data.get('floating_tenor'),
        floating_day_counter=trade_data.get('floating_day_counter'),
        floating_spread=trade_data.get('floating_spread', 0.0),
        # Common parameters
        calendar=trade_data.get('calendar', 'TARGET'),
        payment_convention=trade_data.get('payment_convention', 'MF'),
        is_in_arrears=trade_data.get('is_in_arrears', 'false'),
        fixing_days=trade_data.get('fixing_days', 2)
    )
    return execute_trade_calculation(trade, trade_data, 'ir_swaption')
