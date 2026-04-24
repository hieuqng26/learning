from flask import jsonify, make_response, request
from flask_jwt_extended import jwt_required

from project.api.utils import validate_request
from project.api.auditlog.models import log_audit
from project.api.auth.utils import prevent_multiple_logins_per_user
from project.api.calculation.routes import calculate
from project.logger import get_logger

from project.qld.trade.equity.equity_spot import EQSpot
from project.qld.trade.equity.equity_forward import EQForward
from project.qld.trade.equity.equity_vanilla_option import EQVanillaOption


logger = get_logger(__name__)


@calculate.route('/equity/spot', methods=['POST'], endpoint='calculate_equity_spot')
@jwt_required()
@prevent_multiple_logins_per_user()
@validate_request(allowed_keys=['data'])
def calculate_equity_spot():
    try:
        data = request.get_json()
        trade_data = data.get('data', {})
        trade = EQSpot(
            evaluation_date=trade_data.get('evaluation_date'),
            ticker=trade_data.get('ticker'),
            currency=trade_data.get('currency'),
            notional=trade_data.get('notional'),
            calendar=trade_data.get('calendar'),
            settlement_date_or_tenor=trade_data.get('settlement_date_or_tenor'),
            strike=trade_data.get('strike'),
            discounting=trade_data.get('discounting')
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
            description=f'User [$USER] calculated equity_spot',
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
            description=f'User [$USER] failed to calculate equity_spot. Error: {str(e)}',
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
            description=f'User [$USER] failed to calculate equity_spot. Error: {str(e)}',
            error_codes='500',
            database_involved=''
        )
        return make_response(jsonify({'message': str(e)}), 400)


@calculate.route('/equity/forward', methods=['POST'], endpoint='calculate_equity_forward')
@jwt_required()
@prevent_multiple_logins_per_user()
@validate_request(allowed_keys=['data'])
def calculate_equity_forward():
    try:
        data = request.get_json()
        trade_data = data.get('data', {})
        trade = EQForward(
            evaluation_date=trade_data.get('evaluation_date'),
            ticker=trade_data.get('ticker'),
            currency=trade_data.get('currency'),
            notional=trade_data.get('notional'),
            calendar=trade_data.get('calendar'),
            settlement_date_or_tenor=trade_data.get('settlement_date_or_tenor'),
            strike=trade_data.get('strike'),
            discounting=trade_data.get('discounting')
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
            description=f'User [$USER] calculated equity_forward',
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
            description=f'User [$USER] failed to calculate equity_forward. Error: {str(e)}',
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
            description=f'User [$USER] failed to calculate equity_forward. Error: {str(e)}',
            error_codes='500',
            database_involved=''
        )
        return make_response(jsonify({'message': str(e)}), 400)


@calculate.route('/equity/vanilla_option', methods=['POST'], endpoint='calculate_equity_vanilla_option')
@jwt_required()
@prevent_multiple_logins_per_user()
@validate_request(allowed_keys=['data'])
def calculate_equity_vanilla_option():
    try:
        data = request.get_json()
        trade_data = data.get('data', {})
        trade = EQVanillaOption(
            evaluation_date=trade_data.get('evaluation_date'),
            ticker=trade_data.get('ticker'),
            currency=trade_data.get('currency'),
            notional=trade_data.get('notional'),
            expiry_date=trade_data.get('expiry_date'),
            calendar=trade_data.get('calendar'),
            settlement_tenor=trade_data.get('settlement_tenor'),
            option_type=trade_data.get('option_type'),
            strike=trade_data.get('strike'),
            settlement_type=trade_data.get('settlement_type'),
            discounting=trade_data.get('discounting')
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
            description=f'User [$USER] calculated equity_vanilla_option',
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
            description=f'User [$USER] failed to calculate equity_vanilla_option. Error: {str(e)}',
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
            description=f'User [$USER] failed to calculate equity_vanilla_option. Error: {str(e)}',
            error_codes='500',
            database_involved=''
        )
        return make_response(jsonify({'message': str(e)}), 400)
