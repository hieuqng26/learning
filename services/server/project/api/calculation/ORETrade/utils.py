from flask import jsonify, make_response

from project.api.utils import toJSON
from project.api.auditlog.models import log_audit

from project.qld.ORETrade.ore_base_trade import OREBaseTrade


def execute_trade_calculation(trade, trade_data, trade_name):
    """Execute trade calculation with standard error handling and audit logging."""
    try:
        # Build sensitivity config from request
        sensitivity_config = OREBaseTrade.build_sensitivity_config(trade_data.get('sensitivity'))
        scenario_config = trade_data.get('scenario', None)

        # Price the trade using ORE
        trade.price(sensitivity_config=sensitivity_config, scenario_config=scenario_config)

        # Format results
        result = format_trade_result(trade)

        # audit log
        log_audit(
            action='Compute',
            module='pricing',
            submodule='single_product',
            previous_data='',
            new_data='',
            description=f'User [$USER] calculated {trade_name}',
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
            description=f'User [$USER] failed to calculate {trade_name}. Error: {str(e)}',
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
            description=f'User [$USER] failed to calculate {trade_name}. Error: {str(e)}',
            error_codes='500',
            database_involved=''
        )
        return make_response(jsonify({'message': str(e)}), 500)


def validate_scenario_config(scenario_config: dict) -> tuple:
    """
    Validate scenario configuration structure.

    Args:
        scenario_config: Dictionary containing scenario configuration

    Returns:
        tuple: (is_valid, list_of_errors)
    """
    errors = []

    if not isinstance(scenario_config, dict):
        return False, ['Scenario config must be a dictionary']

    if 'scenarios' not in scenario_config:
        errors.append('Missing "scenarios" key')
        return False, errors

    scenarios = scenario_config['scenarios']
    if not isinstance(scenarios, list):
        errors.append('"scenarios" must be an array')
        return False, errors

    if len(scenarios) == 0:
        errors.append('At least one scenario is required')
        return False, errors

    for i, scenario in enumerate(scenarios):
        if 'id' not in scenario:
            errors.append(f'Scenario {i+1} missing "id" field')

        # Validate shift configurations
        for curve in scenario.get('discount_curves', []):
            if 'ccy' not in curve:
                errors.append(f'Scenario "{scenario.get("id", i+1)}": discount curve missing "ccy"')
            if 'shifts' in curve and 'shift_tenors' in curve:
                if len(curve['shifts']) != len(curve['shift_tenors']):
                    errors.append(f'Scenario "{scenario.get("id", i+1)}": shifts and shift_tenors length mismatch')

        for fx in scenario.get('fx_spots', []):
            if 'ccypair' not in fx:
                errors.append(f'Scenario "{scenario.get("id", i+1)}": FX spot missing "ccypair"')
            if 'shift_size' not in fx:
                errors.append(f'Scenario "{scenario.get("id", i+1)}": FX spot missing "shift_size"')

    return len(errors) == 0, errors


def format_trade_result(trade):
    """Format standard trade pricing result."""
    exposures = trade.result.get('exposures', {'trade': None, 'nettingset': None})
    exposures_sensitivity = trade.result.get('exposures_sensitivity', {'trade': None, 'nettingset': None})
    exposures_stress = trade.result.get('exposures_stress', {'trade': None, 'nettingset': None})

    return {
        'base': {
            'npv': trade.result.get('npv', None),
            'exposures': {
                'trade': toJSON(exposures['trade']),
                'nettingset': toJSON(exposures['nettingset'])
            },
            'cva': trade.result.get('cva', None),
            'dva': trade.result.get('dva', None),
        },
        'sensitivity': {
            'npv': toJSON(trade.result.get('npv_sensitivity')),
            'exposures': {
                'trade': toJSON(exposures_sensitivity['trade']),
                'nettingset': toJSON(exposures_sensitivity['nettingset'])
            }
        },
        'stress': {
            'npv': toJSON(trade.result.get('npv_stress')),
            'exposures': {
                'trade': toJSON(exposures_stress['trade']),
                'nettingset': toJSON(exposures_stress['nettingset'])
            }
        }
    }
