from flask import jsonify, make_response, request
from flask_jwt_extended import jwt_required

from project.api.utils import validate_request
from project.api.auditlog.models import log_audit
from project.api.auth.utils import prevent_multiple_logins_per_user
from project.api.calculation.routes import calculate
from project.logger import get_logger

from project.qld.trade.commodity.commodity_spot import COMSpot
from project.qld.trade.commodity.commodity_forward import COMForward
from project.qld.trade.commodity.commodity_vanilla_option import COMVanillaOption


logger = get_logger(__name__)


@calculate.route('/commodity/spot', methods=['POST'], endpoint='calculate_commodity_spot')
@jwt_required()
@prevent_multiple_logins_per_user()
@validate_request(allowed_keys=['data'])
def calculate_commodity_spot():
    try:
        data = request.get_json()
        trade_data = data.get('data', {})
        trade = COMSpot(
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
            description=f'User [$USER] calculated commodity_spot',
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
            description=f'User [$USER] failed to calculate commodity_spot. Error: {str(e)}',
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
            description=f'User [$USER] failed to calculate commodity_spot. Error: {str(e)}',
            error_codes='500',
            database_involved=''
        )
        return make_response(jsonify({'message': str(e)}), 400)


@calculate.route('/commodity/forward', methods=['POST'], endpoint='calculate_commodity_forward')
@jwt_required()
@prevent_multiple_logins_per_user()
@validate_request(allowed_keys=['data'])
def calculate_commodity_forward():
    try:
        data = request.get_json()
        trade_data = data.get('data', {})
        trade = COMForward(
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
            description=f'User [$USER] calculated commodity_forward',
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
            description=f'User [$USER] failed to calculate commodity_forward. Error: {str(e)}',
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
            description=f'User [$USER] failed to calculate commodity_forward. Error: {str(e)}',
            error_codes='500',
            database_involved=''
        )
        return make_response(jsonify({'message': str(e)}), 400)


@calculate.route('/commodity/vanilla_option', methods=['POST'], endpoint='calculate_commodity_vanilla_option')
@jwt_required()
@prevent_multiple_logins_per_user()
@validate_request(allowed_keys=['data'])
def calculate_commodity_vanilla_option():
    try:
        data = request.get_json()
        trade_data = data.get('data', {})
        trade = COMVanillaOption(
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
            description=f'User [$USER] calculated commodity_vanilla_option',
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
            description=f'User [$USER] failed to calculate commodity_vanilla_option. Error: {str(e)}',
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
            description=f'User [$USER] failed to calculate commodity_vanilla_option. Error: {str(e)}',
            error_codes='500',
            database_involved=''
        )
        return make_response(jsonify({'message': str(e)}), 400)
