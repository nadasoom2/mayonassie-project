from flask import Blueprint, render_template

buy_bp = Blueprint('buy', __name__, url_prefix='/buy-coins')

@buy_bp.route('/')
def buy_coins():
    coin_rate = {
        "coin_per_unit": 10,
        "price_per_unit": 1000
    }
    return render_template('buy_coins.html', **coin_rate)
