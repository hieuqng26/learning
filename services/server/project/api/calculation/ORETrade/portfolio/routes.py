from flask import jsonify, make_response, request
from flask_jwt_extended import jwt_required
import pandas as pd

from project.api.utils import validate_request, toJSON, convert_level_to_json
from project.api.auditlog.models import log_audit
from project.api.auth.utils import prevent_multiple_logins_per_user
from project.api.calculation.routes import calculate
from project.api.calculation.ORETrade.utils import validate_scenario_config
from project.logger import get_logger

from project.qld.ORETrade.ore_portfolio import OREPortfolio


logger = get_logger(__name__)


@calculate.route('/ore/portfolio', methods=['POST'], endpoint='calculate_ore_portfolio')
@jwt_required()
@prevent_multiple_logins_per_user()
@validate_request(allowed_keys=['evaluation_date', 'trades', 'netting_sets', 'sensitivity_config', 'scenario_config'])
def calculate_ore_portfolio():
    """
    Calculate ORE portfolio pricing for multiple trade types.

    Expected payload:
    {
        "evaluation_date": "2016-02-05",
        "trades": {
            "InterestRateSwap": [...],  // Array of trade objects
            "FxForward": [...]
        },
        "netting_sets": [...],  // Optional array of netting set objects
        "sensitivity_config": {...},  // Optional
        "scenario_config": {...}  // Optional
    }

    Returns structured results with trade/nettingset/portfolio levels:
    {
        "trade_count": int,
        "successful_trades": int,
        "total_npv": float,
        "total_cva": float,
        "total_dva": float,
        "base": {
            "npv": {
                "trade": [...],  // Trade-level NPV DataFrame
                "nettingset": null,
                "portfolio": float  // Aggregated portfolio NPV
            },
            "cva": {
                "trade": null,
                "nettingset": null,
                "portfolio": float
            },
            "dva": {
                "trade": null,
                "nettingset": null,
                "portfolio": float
            },
            "exposures": {
                "trade": [...],  // Trade-level exposures
                "nettingset": [...],  // Nettingset-level exposures
                "portfolio": [...]  // Portfolio-level aggregated exposures
            }
        },
        "sensitivity": {
            "npv": {"trade": [...], "nettingset": null, "portfolio": null},
            "cva": {"trade": null, "nettingset": null, "portfolio": null},
            "dva": {"trade": null, "nettingset": null, "portfolio": null},
            "exposures": {"trade": [...], "nettingset": [...], "portfolio": [...]}
        },
        "stress": {
            "npv": {"trade": [...], "nettingset": null, "portfolio": null},
            "cva": {"trade": null, "nettingset": null, "portfolio": null},
            "dva": {"trade": null, "nettingset": null, "portfolio": null},
            "exposures": {"trade": [...], "nettingset": [...], "portfolio": [...]}
        }
    }
    """
    try:
        data = request.get_json()
        evaluation_date = data.get('evaluation_date')
        trades_data = data.get('trades', {})
        netting_sets_data = data.get('netting_sets')
        sensitivity_config = data.get('sensitivity_config')
        scenario_config = data.get('scenario_config')

        if not evaluation_date:
            return make_response(jsonify({'message': 'evaluation_date is required'}), 400)

        # Parse and validate scenario config if provided
        parsed_scenario_config = None
        if scenario_config:
            # Already in dict format (from JSON or pre-parsed Excel)
            parsed_scenario_config = scenario_config

            # Validate scenario config structure
            is_valid, errors = validate_scenario_config(parsed_scenario_config)
            if not is_valid:
                return make_response(
                    jsonify({'message': f'Invalid scenario config: {"; ".join(errors)}'}),
                    400
                )

        if not trades_data:
            return make_response(jsonify({'message': 'No trades data provided'}), 400)

        # Convert trades data (list of dicts) to DataFrames grouped by TradeType
        trades_by_type = {}
        total_trade_count = 0

        for sheet_name, sheet_data in trades_data.items():
            if not sheet_data:
                continue

            # Convert to DataFrame
            df = pd.DataFrame(sheet_data)

            if df.empty:
                continue

            # Group by TradeType if present, otherwise use sheet_name as trade type
            if 'TradeType' in df.columns:
                for trade_type in df['TradeType'].unique():
                    type_df = df[df['TradeType'] == trade_type].copy()
                    if trade_type in trades_by_type:
                        # Append to existing DataFrame for this type
                        trades_by_type[trade_type] = pd.concat([trades_by_type[trade_type], type_df], ignore_index=True)
                    else:
                        trades_by_type[trade_type] = type_df
                    total_trade_count += len(type_df)
            else:
                # Use sheet name as trade type indicator
                trades_by_type[sheet_name] = df
                total_trade_count += len(df)

        if not trades_by_type:
            return make_response(jsonify({'message': 'No valid trades found in data'}), 400)

        # Convert netting_sets data to DataFrame if provided
        netting_sets_df = None
        if netting_sets_data:
            try:
                if isinstance(netting_sets_data, list):
                    netting_sets_df = pd.DataFrame(netting_sets_data)
                elif isinstance(netting_sets_data, dict):
                    netting_sets_df = pd.DataFrame([netting_sets_data])

                # Validate required columns
                required_cols = ['NettingSetId', 'CounterParty']
                missing_cols = [col for col in required_cols if col not in netting_sets_df.columns]
                if missing_cols:
                    return make_response(
                        jsonify({'message': f'Netting sets missing required columns: {", ".join(missing_cols)}'}),
                        400
                    )

                logger.info(f"Processing {len(netting_sets_df)} netting set(s)")
            except Exception as e:
                logger.warning(f"Failed to process netting_sets: {str(e)}. Using default netting.")
                netting_sets_df = None

        # Create OREPortfolio instance
        portfolio = OREPortfolio(
            evaluation_date=evaluation_date,
            trades=trades_by_type,
            netting_sets=netting_sets_df
        )

        # Price the portfolio
        portfolio.price(sensitivity_config=sensitivity_config, scenario_config=parsed_scenario_config)

        # Extract structured results from portfolio
        base_results = portfolio.result.get('base', {})
        sensitivity_results = portfolio.result.get('sensitivity', {})
        stress_results = portfolio.result.get('stress', {})

        # Get trade count from base NPV
        npv_trade_df = base_results.get('npv', {}).get('trade')
        successful_trades = len(npv_trade_df) if npv_trade_df is not None and not npv_trade_df.empty else 0

        # Build response with trade/nettingset/portfolio levels
        formatted_results = {
            'trade_count': total_trade_count,
            'successful_trades': successful_trades,
            'base': convert_level_to_json(base_results),
            'sensitivity': convert_level_to_json(sensitivity_results),
            'stress': convert_level_to_json(stress_results),
        }

        # Audit log
        netting_count = len(netting_sets_df) if netting_sets_df is not None else 0
        log_audit(
            action='Compute',
            module='pricing',
            submodule='ore_portfolio',
            previous_data='',
            new_data='',
            description=f'User [$USER] calculated ORE portfolio with {total_trade_count} trades and {netting_count} netting set(s)',
            error_codes='',
            database_involved=''
        )

        return make_response(jsonify(formatted_results), 200)

    except ValueError as e:
        logger.error(f"Validation error in ORE portfolio calculation: {str(e)}")
        log_audit(
            action='Compute',
            module='pricing',
            submodule='ore_portfolio',
            previous_data='',
            new_data='',
            description=f'User [$USER] failed to calculate ORE portfolio. Error: {str(e)}',
            error_codes='400',
            database_involved=''
        )
        return make_response(jsonify({'message': str(e)}), 400)
    except Exception as e:
        logger.error(f"Error in ORE portfolio calculation: {str(e)}")
        log_audit(
            action='Compute',
            module='pricing',
            submodule='ore_portfolio',
            previous_data='',
            new_data='',
            description=f'User [$USER] failed to calculate ORE portfolio. Error: {str(e)}',
            error_codes='500',
            database_involved=''
        )
        return make_response(jsonify({'message': str(e)}), 500)
