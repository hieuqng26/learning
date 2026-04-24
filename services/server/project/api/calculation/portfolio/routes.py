from flask import jsonify, make_response, request
from flask_jwt_extended import jwt_required
import pandas as pd

from project.api.utils import validate_request, toJSON
from project.api.auditlog.models import log_audit
from project.api.auth.utils import prevent_multiple_logins_per_user
from project.api.calculation.routes import calculate
from project.logger import get_logger

from project.qld.trade.portfolio import Portfolio


logger = get_logger(__name__)


@calculate.route('/portfolio', methods=['POST'], endpoint='calculate_portfolio')
@jwt_required()
@prevent_multiple_logins_per_user()
@validate_request(allowed_keys=['portfolio_data'])
def calculate_portfolio():
    try:
        data = request.get_json()
        portfolio_data = data.get('portfolio_data', [])

        if not portfolio_data:
            return make_response(jsonify({'message': 'No portfolio data provided'}), 400)

        # Convert portfolio data to DataFrame
        df = pd.DataFrame(portfolio_data)
        trade_type = df['trade_type'].values[0]  # assume unique
        evaluation_date = df['evaluation_date'].values[0]  # assume unique
        df = df.set_index('trade_id').drop(columns=['trade_type', 'evaluation_date'])

        if df.empty:
            return make_response(jsonify({'message': 'Portfolio data is empty'}), 400)

        # Create Portfolio instance
        portfolio = Portfolio(trade_type=trade_type, evaluation_date=evaluation_date)

        # Load trades from DataFrame
        portfolio.load_trades_from_dataframe(df, validate=True)

        # Price the portfolio
        results = portfolio.price(max_workers=4)

        # Format the results for frontend consumption
        formatted_results = {
            'trade_type': results['trade_type'],
            'evaluation_date': results['evaluation_date'],
            'trade_count': results['trade_count'],
            'successful_trades': results['successful_trades'],
            'failed_trades': results['failed_trades'],
            'portfolio_npv': results['portfolio_npv'],
            'trade_results': toJSON(results['trade_results'])
        }

        # audit log
        log_audit(
            action='Compute',
            module='pricing',
            submodule='portfolio',
            previous_data='',
            new_data='',
            description=f'User [$USER] calculated portfolio {trade_type} with {len(portfolio_data)} trades',
            error_codes='',
            database_involved=''
        )

        return make_response(jsonify(formatted_results), 200)

    except ValueError as e:
        log_audit(
            action='Compute',
            module='pricing',
            submodule='portfolio',
            previous_data='',
            new_data='',
            description=f'User [$USER] failed to calculate portfolio. Error: {str(e)}',
            error_codes='400',
            database_involved=''
        )
        return make_response(jsonify({'message': str(e)}), 400)
    except Exception as e:
        log_audit(
            action='Compute',
            module='pricing',
            submodule='portfolio',
            previous_data='',
            new_data='',
            description=f'User [$USER] failed to calculate portfolio. Error: {str(e)}',
            error_codes='500',
            database_involved=''
        )
        return make_response(jsonify({'message': str(e)}), 500)
