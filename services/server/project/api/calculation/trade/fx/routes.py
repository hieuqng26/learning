from flask import jsonify, make_response, request
from flask_jwt_extended import jwt_required

from project.api.utils import validate_request
from project.api.auditlog.models import log_audit
from project.api.auth.utils import prevent_multiple_logins_per_user
from project.api.calculation.routes import calculate
from project.logger import get_logger

from project.qld.trade.fx.fxforward import FXForward
from project.qld.trade.fx.fxspot import FXSpot
from project.qld.trade.fx.fx_vanilla_option import FXVanillaOption


logger = get_logger(__name__)


# @calculate.route('/fx/fxforward', methods=['POST'], endpoint='calculate_fx_fxforward')
# @jwt_required()
# @prevent_multiple_logins_per_user()
# @validate_request(allowed_keys=['data'])
# def calculate_fx_forward():
#     try:
#         data = request.get_json()
#         trade_data = data.get('data', {})
#         trade = FXForward(
#             evaluation_date=trade_data.get('evaluation_date'),
#             domestic_currency=trade_data.get('domestic_currency'),
#             notional_currency=trade_data.get('notional_currency'),
#             foreign_currency=trade_data.get('foreign_currency'),
#             notional=trade_data.get('notional'),
#             calendar=trade_data.get('calendar'),
#             settlement_date_or_tenor=trade_data.get('settlement_date_or_tenor'),
#             strike=trade_data.get('strike'),
#             domestic_discounting=trade_data.get('domestic_discounting'),
#             foreign_discounting=trade_data.get('foreign_discounting')
#         )

#         bump_points = trade_data.get('bump_points', None)
#         curve_name = trade_data.get('risk_curve_name', None)
#         bump_type = trade_data.get('bump_type')
#         risk_results = trade.calculate_risk_sensitivity(
#             bump_points=bump_points,
#             curve_name=curve_name,
#             bump_type=bump_type
#         )
#         risk_sensitivity = {
#             'BP': [0] + risk_results['bump_points'],
#             'NPV': [risk_results['base_npv']] + risk_results['npv_values'],
#             'NPV_CHANGES': [0] + risk_results['npv_changes']
#         }
#         result = {
#             'npv': risk_results['base_npv'],
#             'cva': risk_results['base_cva'],
#             'dva': risk_results['base_dva'],
#             'risk_sensitivity': risk_sensitivity,
#             'exposures': (
#                 risk_results['exposures'].to_dict(orient='records')
#                 if risk_results['exposures'] is not None
#                 else None
#             )
#         }

#         # audit log
#         log_audit(
#             action='Compute',
#             module='pricing',
#             submodule='single_product',
#             previous_data='',
#             new_data='',
#             description=f'User [$USER] calculated fx_forward',
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
#             description=f'User [$USER] failed to calculate fx_forward. Error: {str(e)}',
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
#             description=f'User [$USER] failed to calculate fx_forward. Error: {str(e)}',
#             error_codes='500',
#             database_involved=''
#         )
#         return make_response(jsonify({'message': str(e)}), 400)


@calculate.route('/fx/fxspot', methods=['POST'], endpoint='calculate_fx_fxspot')
@jwt_required()
@prevent_multiple_logins_per_user()
@validate_request(allowed_keys=['data'])
def calculate_fx_spot():
    try:
        data = request.get_json()
        trade_data = data.get('data', {})
        trade = FXSpot(
            evaluation_date=trade_data.get('evaluation_date'),
            domestic_currency=trade_data.get('domestic_currency'),
            notional_currency=trade_data.get('notional_currency'),
            foreign_currency=trade_data.get('foreign_currency'),
            notional=trade_data.get('notional'),
            calendar=trade_data.get('calendar'),
            settlement_date_or_tenor=trade_data.get('settlement_date_or_tenor'),
            strike=trade_data.get('strike'),
            domestic_discounting=trade_data.get('domestic_discounting'),
            foreign_discounting=trade_data.get('foreign_discounting')
        )

        bump_points = trade_data.get('bump_points', None)
        curve_name = trade_data.get('risk_curve_name', None)
        bump_type = trade_data.get('bump_type')
        risk_results = trade.calculate_risk_sensitivity(
            bump_points=bump_points,
            curve_name=curve_name,
            bump_type=bump_type
        )
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
            description=f'User [$USER] calculated fx_spot',
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
            description=f'User [$USER] failed to calculate fx_spot. Error: {str(e)}',
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
            description=f'User [$USER] failed to calculate fx_spot. Error: {str(e)}',
            error_codes='500',
            database_involved=''
        )
        return make_response(jsonify({'message': str(e)}), 400)


@calculate.route('/fx/fxvanillaoption', methods=['POST'], endpoint='calculate_fx_fxvanillaoption')
@jwt_required()
@prevent_multiple_logins_per_user()
@validate_request(allowed_keys=['data'])
def calculate_fx_vanilla_option():
    try:
        data = request.get_json()
        trade_data = data.get('data', {})
        trade = FXVanillaOption(
            evaluation_date=trade_data.get('evaluation_date'),
            domestic_currency=trade_data.get('domestic_currency'),
            notional_currency=trade_data.get('notional_currency'),
            foreign_currency=trade_data.get('foreign_currency'),
            notional=trade_data.get('notional'),
            expiry_date=trade_data.get('expiry_date'),
            calendar=trade_data.get('calendar'),
            settlement_tenor=trade_data.get('settlement_tenor'),
            option_type=trade_data.get('option_type'),
            strike=trade_data.get('strike'),
            settlement_type=trade_data.get('settlement_type'),
            domestic_discounting=trade_data.get('domestic_discounting'),
            foreign_discounting=trade_data.get('foreign_discounting'),
            fx_vol_surface=trade_data.get('fx_vol_surface')
        )

        bump_points = trade_data.get('bump_points', None)
        curve_name = trade_data.get('risk_curve_name', None)
        bump_type = trade_data.get('bump_type')
        risk_results = trade.calculate_risk_sensitivity(
            bump_points=bump_points,
            curve_name=curve_name,
            bump_type=bump_type
        )
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
            description=f'User [$USER] calculated fx_vanilla_option',
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
            description=f'User [$USER] failed to calculate fx_vanilla_option. Error: {str(e)}',
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
            description=f'User [$USER] failed to calculate fx_vanilla_option. Error: {str(e)}',
            error_codes='500',
            database_involved=''
        )
        return make_response(jsonify({'message': str(e)}), 400)
