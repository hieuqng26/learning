from flask import jsonify, make_response, request
from flask_jwt_extended import jwt_required

from project.api.utils import validate_request
from project.api.auditlog.models import log_audit
from project.api.auth.utils import prevent_multiple_logins_per_user
from project.api.calculation.routes import calculate
from project.logger import get_logger

from project.qld.trade.ir.ir_fixed_rate_bond import IRFixedRateBond
from project.qld.trade.ir.callable_ccs import CallableCCS
from project.qld.trade.ir.oiswap import OISwap
from project.qld.trade.ir.irswap import IRSwap
from project.qld.trade.ir.callable_floating_rate_bond import CallableFloatingRateBond


logger = get_logger(__name__)


@calculate.route('/ir/fixed_rate_bond', methods=['POST'], endpoint='calculate_ir_fixed_rate_bond')
@jwt_required()
@prevent_multiple_logins_per_user()
@validate_request(allowed_keys=['data'])
def calculate_ir_fixed_rate_bond():
    try:
        data = request.get_json()
        trade_data = data.get('data', {})
        trade = IRFixedRateBond(
            evaluation_date=trade_data.get('evaluation_date'),
            currency=trade_data.get('currency'),
            notional=trade_data.get('notional'),
            start_date=trade_data.get('start_date'),
            end_date=trade_data.get('end_date'),
            calendar=trade_data.get('calendar'),
            day_count_convention=trade_data.get('day_count_convention'),
            business_day_convention=trade_data.get('business_day_convention'),
            settlement_lag=trade_data.get('settlement_lag'),
            fixed_rate=trade_data.get('fixed_rate'),
            fixed_frequency=trade_data.get('fixed_frequency'),
            discounting_curve=trade_data.get('discounting_curve')
        )
        # trade.price()
        # result = trade.result

        bump_points = trade_data.get('bump_points', None)
        curve_name = trade_data.get('risk_curve_name', None)
        bump_type = trade_data.get('bump_type')
        risk_results = trade.calculate_risk_sensitivity(bump_points=bump_points,
                                                        curve_name=curve_name,
                                                        bump_type=bump_type)
        risk_sensitivity = {
            'BP': [0] + risk_results['bump_points'],
            'NPV': [risk_results['base_npv']] + risk_results['npv_values'],
            'NPV_CHANGES': [0] + risk_results['npv_changes']
        }
        result = {
            'npv': risk_results['base_npv'],
            'cva': risk_results['base_cva'],
            'dva': risk_results['base_dva'],
            'risk_sensitivity': risk_sensitivity
        }

        # audit log
        log_audit(
            action='Compute',
            module='pricing',
            submodule='single_product',
            previous_data='',
            new_data='',
            description=f'User [$USER] calculated ir_fixed_rate_bond',
            error_codes='',
            database_involved=''
        )
        return make_response(jsonify(result), 200)
    except ValueError as e:
        log_audit(
            action='Compute',
            module='pricing',
            submodule='single_product',
            previous_data='',
            new_data='',
            description=f'User [$USER] failed to calculate ir_fixed_rate_bond. Error: {str(e)}',
            error_codes='400',
            database_involved=''
        )
        return make_response(jsonify({'message': str(e)}), 400)
    except Exception as e:
        log_audit(
            action='Compute',
            module='pricing',
            submodule='single_product',
            previous_data='',
            new_data='',
            description=f'User [$USER] failed to calculate ir_fixed_rate_bond. Error: {str(e)}',
            error_codes='500',
            database_involved=''
        )
        return make_response(jsonify({'message': str(e)}), 400)


@calculate.route('/ir/callable_ccs', methods=['POST'], endpoint='calculate_ir_callable_ccs')
@jwt_required()
@prevent_multiple_logins_per_user()
@validate_request(allowed_keys=['data'])
def calculate_ir_callable_ccs():
    try:
        data = request.get_json()
        trade_data = data.get('data', {})
        trade = CallableCCS(
            evaluation_date=trade_data.get('evaluation_date'),
            start_date=trade_data.get('start_date'),
            end_date=trade_data.get('end_date'),
            cal=trade_data.get('calendar'),
            bdc=trade_data.get('business_day_convention'),
            termination_bdc=trade_data.get('termination_business_day_convention'),
            settlement_lag=trade_data.get('settlement_lag'),
            dc1=trade_data.get('day_count_convention1'),
            dc2=trade_data.get('day_count_convention2'),
            ccy1=trade_data.get('currency1'),
            ccy2=trade_data.get('currency2'),
            notional_exchange=trade_data.get('notional_exchange'),
            interim_exchange=trade_data.get('interim_exchange'),
            notional_reset=trade_data.get('notional_reset'),
            notionals1=trade_data.get('notionals1'),
            redemption_notionals1=trade_data.get('redemption_notionals1'),
            interim_exchange_notionals1=trade_data.get('interim_exchange_notionals1'),
            notionals2=trade_data.get('notionals2'),
            redemption_notionals2=trade_data.get('redemption_notionals2'),
            interim_exchange_notionals2=trade_data.get('interim_exchange_notionals2'),
            option_tenors=trade_data.get('option_tenors'),
            exercise_lag=trade_data.get('exercise_lag'),
            freq1=trade_data.get('frequency1'),
            freq2=trade_data.get('frequency2'),
            spread_or_fixed_rate1=trade_data.get('spread_or_fixed_rate1'),
            spread_or_fixed_rate2=trade_data.get('spread_or_fixed_rate2'),
            final_notional1=trade_data.get('final_notional1'),
            final_notional2=trade_data.get('final_notional2')
        )
        # trade.price()
        # result = trade.result

        bump_points = trade_data.get('bump_points', None)
        curve_name = trade_data.get('risk_curve_name', None)
        bump_type = trade_data.get('bump_type')
        risk_results = trade.calculate_risk_sensitivity(bump_points=bump_points,
                                                        curve_name=curve_name,
                                                        bump_type=bump_type)
        risk_sensitivity = {
            'BP': [0] + risk_results['bump_points'],
            'NPV': [risk_results['base_npv']] + risk_results['npv_values'],
            'NPV_CHANGES': [0] + risk_results['npv_changes']
        }
        result = {
            'npv': risk_results['base_npv'],
            'cva': risk_results['base_cva'],
            'dva': risk_results['base_dva'],
            'risk_sensitivity': risk_sensitivity
        }

        # audit log
        log_audit(
            action='Compute',
            module='pricing',
            submodule='single_product',
            previous_data='',
            new_data='',
            description=f'User [$USER] calculated ir_callable_ccs',
            error_codes='',
            database_involved=''
        )
        return make_response(jsonify(result), 200)
    except ValueError as e:
        log_audit(
            action='Compute',
            module='pricing',
            submodule='single_product',
            previous_data='',
            new_data='',
            description=f'User [$USER] failed to calculate ir_callable_ccs. Error: {str(e)}',
            error_codes='400',
            database_involved=''
        )
        return make_response(jsonify({'message': str(e)}), 400)
    except Exception as e:
        log_audit(
            action='Compute',
            module='pricing',
            submodule='single_product',
            previous_data='',
            new_data='',
            description=f'User [$USER] failed to calculate ir_callable_ccs. Error: {str(e)}',
            error_codes='500',
            database_involved=''
        )
        return make_response(jsonify({'message': str(e)}), 400)


# @calculate.route('/ir/oiswap', methods=['POST'], endpoint='calculate_ir_oiswap')
# @jwt_required()
# @prevent_multiple_logins_per_user()
# @validate_request(allowed_keys=['data'])
# def calculate_ir_oiswap():
#     try:
#         data = request.get_json()
#         trade_data = data.get('data', {})
#         trade = OISwap(
#             evaluation_date=trade_data.get('evaluation_date'),
#             currency=trade_data.get('currency'),
#             notional=trade_data.get('notional'),
#             start_date=trade_data.get('start_date'),
#             end_date=trade_data.get('end_date'),
#             calendar=trade_data.get('calendar'),
#             payment_lag=trade_data.get('payment_lag'),
#             business_day_convention=trade_data.get('business_day_convention'),
#             type=trade_data.get('type'),
#             fixed_rate=trade_data.get('fixed_rate'),
#             fixed_frequency=trade_data.get('fixed_frequency'),
#             fixed_day_count=trade_data.get('fixed_day_count'),
#             overnight_index=trade_data.get('overnight_index'),
#             overnight_spread=trade_data.get('overnight_spread'),
#             overnight_day_count=trade_data.get('overnight_day_count'),
#             discounting_curve=trade_data.get('discounting_curve')
#         )
#         # trade.price()
#         # result = trade.result

#         bump_points = trade_data.get('bump_points', None)
#         curve_name = trade_data.get('risk_curve_name', None)
#         bump_type = trade_data.get('bump_type')
#         risk_results = trade.calculate_risk_sensitivity(bump_points=bump_points,
#                                                         curve_name=curve_name,
#                                                         bump_type=bump_type)
#         risk_sensitivity = {
#             'BP': [0] + risk_results['bump_points'],
#             'NPV': [risk_results['base_npv']] + risk_results['npv_values'],
#             'NPV_CHANGES': [0] + risk_results['npv_changes']
#         }
#         result = {
#             'npv': risk_results['base_npv'],
#             'cva': risk_results['base_cva'],
#             'dva': risk_results['base_dva'],
#             'risk_sensitivity': risk_sensitivity
#         }

#         # audit log
#         log_audit(
#             action='Compute',
#             module='pricing',
#             submodule='single_product',
#             previous_data='',
#             new_data='',
#             description=f'User [$USER] calculated ir_oiswap',
#             error_codes='',
#             database_involved=''
#         )
#         return make_response(jsonify(result), 200)
#     except ValueError as e:
#         log_audit(
#             action='Compute',
#             module='pricing',
#             submodule='single_product',
#             previous_data='',
#             new_data='',
#             description=f'User [$USER] failed to calculate ir_oiswap. Error: {str(e)}',
#             error_codes='400',
#             database_involved=''
#         )
#         return make_response(jsonify({'message': str(e)}), 400)
#     except Exception as e:
#         log_audit(
#             action='Compute',
#             module='pricing',
#             submodule='single_product',
#             previous_data='',
#             new_data='',
#             description=f'User [$USER] failed to calculate ir_oiswap. Error: {str(e)}',
#             error_codes='500',
#             database_involved=''
#         )
#         return make_response(jsonify({'message': str(e)}), 400)


# @calculate.route('/ir/irswap', methods=['POST'], endpoint='calculate_ir_irswap')
# @jwt_required()
# @prevent_multiple_logins_per_user()
# @validate_request(allowed_keys=['data'])
# def calculate_ir_irswap():
#     try:
#         data = request.get_json()
#         trade_data = data.get('data', {})
#         trade = IRSwap(
#             evaluation_date=trade_data.get('evaluation_date'),
#             currency=trade_data.get('currency'),
#             notional=trade_data.get('notional'),
#             start_date=trade_data.get('start_date'),
#             end_date=trade_data.get('end_date'),
#             calendar=trade_data.get('calendar'),
#             fixing_lag=trade_data.get('fixing_lag'),
#             business_day_convention=trade_data.get('business_day_convention'),
#             type=trade_data.get('type'),
#             fixed_rate=trade_data.get('fixed_rate'),
#             fixed_frequency=trade_data.get('fixed_frequency'),
#             fixed_day_count=trade_data.get('fixed_day_count'),
#             float_index=trade_data.get('float_index'),
#             float_spread=trade_data.get('float_spread'),
#             float_frequency=trade_data.get('float_frequency'),
#             float_day_count=trade_data.get('float_day_count'),
#             discounting_curve=trade_data.get('discounting_curve')
#         )
#         # trade.price()
#         # result = trade.result

#         bump_points = trade_data.get('bump_points', None)
#         curve_name = trade_data.get('risk_curve_name', None)
#         bump_type = trade_data.get('bump_type')
#         risk_results = trade.calculate_risk_sensitivity(bump_points=bump_points,
#                                                         curve_name=curve_name,
#                                                         bump_type=bump_type)
#         risk_sensitivity = {
#             'BP': [0] + risk_results['bump_points'],
#             'NPV': [risk_results['base_npv']] + risk_results['npv_values'],
#             'NPV_CHANGES': [0] + risk_results['npv_changes']
#         }
#         result = {
#             'npv': risk_results['base_npv'],
#             'cva': risk_results['base_cva'],
#             'dva': risk_results['base_dva'],
#             'risk_sensitivity': risk_sensitivity
#         }

#         # audit log
#         log_audit(
#             action='Compute',
#             module='pricing',
#             submodule='single_product',
#             previous_data='',
#             new_data='',
#             description=f'User [$USER] calculated ir_irswap',
#             error_codes='',
#             database_involved=''
#         )
#         return make_response(jsonify(result), 200)
#     except ValueError as e:
#         log_audit(
#             action='Compute',
#             module='pricing',
#             submodule='single_product',
#             previous_data='',
#             new_data='',
#             description=f'User [$USER] failed to calculate ir_irswap. Error: {str(e)}',
#             error_codes='400',
#             database_involved=''
#         )
#         return make_response(jsonify({'message': str(e)}), 400)
#     except Exception as e:
#         log_audit(
#             action='Compute',
#             module='pricing',
#             submodule='single_product',
#             previous_data='',
#             new_data='',
#             description=f'User [$USER] failed to calculate ir_irswap. Error: {str(e)}',
#             error_codes='500',
#             database_involved=''
#         )
#         return make_response(jsonify({'message': str(e)}), 400)


@calculate.route('/ir/callable_floating_rate_bond', methods=['POST'], endpoint='calculate_ir_callable_floating_rate_bond')
@jwt_required()
@prevent_multiple_logins_per_user()
@validate_request(allowed_keys=['data'])
def calculate_ir_callable_floating_rate_bond():
    try:
        data = request.get_json()
        trade_data = data.get('data', {})
        trade = CallableFloatingRateBond(
            evaluation_date=trade_data.get('evaluation_date'),
            currency=trade_data.get('currency'),
            notional=trade_data.get('notional'),
            start_date=trade_data.get('start_date'),
            bond_tenor=trade_data.get('bond_tenor'),
            calendar=trade_data.get('calendar'),
            day_count_convention=trade_data.get('day_count_convention'),
            business_day_convention=trade_data.get('business_day_convention'),
            option_tenors=trade_data.get('option_tenors'),
            exercise_lag=trade_data.get('exercise_lag'),
            discount_curve_name=trade_data.get('discount_curve_name'),
            forecast_curve_name=trade_data.get('forecast_curve_name'),
            vol_matrix=trade_data.get('vol_matrix'),
            spread=trade_data.get('spread'),
            gearing=trade_data.get('gearing', 1.0)
        )

        bump_points = trade_data.get('bump_points', None)
        curve_name = trade_data.get('risk_curve_name', None)
        bump_type = trade_data.get('bump_type')
        risk_results = trade.calculate_risk_sensitivity(bump_points=bump_points,
                                                        curve_name=curve_name,
                                                        bump_type=bump_type)
        risk_sensitivity = {
            'BP': [0] + risk_results['bump_points'],
            'NPV': [risk_results['base_npv']] + risk_results['npv_values'],
            'NPV_CHANGES': [0] + risk_results['npv_changes']
        }
        result = {
            'npv': risk_results['base_npv'],
            'cva': risk_results['base_cva'],
            'dva': risk_results['base_dva'],
            'risk_sensitivity': risk_sensitivity
        }

        # audit log
        log_audit(
            action='Compute',
            module='pricing',
            submodule='single_product',
            previous_data='',
            new_data='',
            description=f'User [$USER] calculated ir_callable_floating_rate_bond',
            error_codes='',
            database_involved=''
        )
        return make_response(jsonify(result), 200)
    except ValueError as e:
        log_audit(
            action='Compute',
            module='pricing',
            submodule='single_product',
            previous_data='',
            new_data='',
            description=f'User [$USER] failed to calculate ir_callable_floating_rate_bond. Error: {str(e)}',
            error_codes='400',
            database_involved=''
        )
        return make_response(jsonify({'message': str(e)}), 400)
    except Exception as e:
        log_audit(
            action='Compute',
            module='pricing',
            submodule='single_product',
            previous_data='',
            new_data='',
            description=f'User [$USER] failed to calculate ir_callable_floating_rate_bond. Error: {str(e)}',
            error_codes='500',
            database_involved=''
        )
        return make_response(jsonify({'message': str(e)}), 400)
