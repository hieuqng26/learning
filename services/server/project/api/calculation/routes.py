from flask import Blueprint

calculate = Blueprint('calculate', __name__)

# Import route modules to register them with the blueprint
# from project.api.calculation.trade.ir.routes import calculate_ir_callable_ccs, calculate_ir_callable_floating_rate_bond, calculate_ir_fixed_rate_bond  # noqa
# from project.api.calculation.trade.fx.routes import calculate_fx_spot  # noqa
# from project.api.calculation.trade.commodity.routes import *  # noqa
# from project.api.calculation.trade.equity.routes import *  # noqa
# from project.api.calculation.trade.crypto.routes import *  # noqa
# from project.api.calculation.portfolio.routes import *   # noqa

from project.api.calculation.ORETrade.ir.routes import *  # noqa
from project.api.calculation.ORETrade.fx.routes import *  # noqa
from project.api.calculation.ORETrade.portfolio.routes import *  # noqa
