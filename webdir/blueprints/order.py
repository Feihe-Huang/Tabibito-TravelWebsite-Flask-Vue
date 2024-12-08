from flask import Blueprint, request, jsonify

from exts import db
from models import Order

bp = Blueprint("Order", __name__, url_prefix="/order")


@bp.route("/get_order_detail", methods=['POST'])
def get_order_detail():
    data = request.get_json(silent=True)
    order_id = data["order_id"]
    order = Order.query.filter_by(id=order_id).first()
    if order is not None:
        # 当后台看时
        if 'user_id' not in data:
            return jsonify(code=200, product_id=order.product_id, create_time=order.create_time,
                           order_status=order.order_status.name, group_number=order.product_number,
                           total=order.total())
        # 当用户看时
        else:
            user_id = data["user_id"]
            order = Order.query.filter_by(id=order_id, user_id=user_id).first()
            if order is not None:
                return jsonify(code=200, product_id=order.product_id, create_time=order.create_time,
                               order_status=order.order_status.name, group_number=order.product_number,
                               total=order.total())
            else:
                return jsonify(code=201, message="Order not found")
    else:
        return jsonify(code=201, message="Order not found")


@bp.route("/create_order", methods=['POST'])
def add_order():
    data = request.get_json(silent=True)
    user_id = data["user_id"]
    product_id = data["product_id"]
    group_number = data["groupNum"]
    old_order = Order.query.filter_by(user_id=user_id, product_id=product_id).first()
    if old_order:
        return jsonify(code=400, message="cannotCreateOrder")
    order = Order(user_id=user_id, product_id=product_id, product_number=group_number)
    db.session.add(order)
    db.session.commit()
    return jsonify(code=200, message="createOrderSuccess"), 200
