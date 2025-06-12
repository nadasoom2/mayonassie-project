from flask import Blueprint, request, jsonify
import uuid

payment_bp = Blueprint('payment', __name__)

@payment_bp.route('/create-payment', methods=['POST'])
def create_payment():
    data = request.get_json()
    amount = data.get('amount')

    if not amount or not isinstance(amount, int):
        return jsonify({'code': 'FAIL', 'message': 'Invalid amount'}), 400

    # 고유 주문번호 생성 (UUID 사용)
    order_id = str(uuid.uuid4())

    # 실제 결제 생성 로직이 여기 들어가야 하나, 토스 테스트 환경에선 클라이언트 결제창 호출만 하면 됨

    return jsonify({'code': 'SUCCESS', 'orderId': order_id})


@payment_bp.route('/payment-success')
def payment_success():
    return "결제 성공 페이지 (여기에 UI 또는 리다이렉션 처리)"

@payment_bp.route('/payment-fail')
def payment_fail():
    return "결제 실패 페이지 (여기에 UI 또는 리다이렉션 처리)"