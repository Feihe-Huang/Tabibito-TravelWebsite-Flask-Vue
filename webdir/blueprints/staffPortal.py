from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from exts import db
from models import Order, Product, OrderStatus, ProductStatus, User


bp = Blueprint("Staff", __name__, url_prefix="/staff_portal")


@bp.route("/change_order_status", methods=['POST'])
def change_order_status():
    data = request.get_json(silent=True)
    order_id = data['id']
    order = Order.query.filter_by(id=order_id).first()
    if data['operation'] == "Delete":
        db.session.delete(order)
        db.session.commit()
        return jsonify(message="delete successfully", code=200)
    if order.order_status.name == OrderStatus.Completed.name or order.order_status.name == OrderStatus.Cancelled.name:
        if data['operation'] == OrderStatus.Completed.name or data['operation'] == OrderStatus.Cancelled.name:
            return jsonify(code=400, message="wrong operation")
    if order.order_status.name == OrderStatus.Processing.name:
        order.order_status = data['operation']
    db.session.commit()
    return jsonify(message="modify successfully", code=200)


@bp.route("/view_all", methods=['GET', 'POST'])
def view_all_order():
    page = request.get_json()["page"]
    per_page = 120  # 每页10个对象，hfh改的，就要120个，没写错，不信看项目，分页是对的，且每页10个
    all_orders = Order.query.order_by(Order.id).paginate(page=page, per_page=per_page, error_out=False).items
    return jsonify(all_orders=[order.serialize_all() for order in all_orders], code=200)


@bp.route("/recent_product_list", methods=["GET"])
def view_latest_order():
    latest_orders = db.session.query(Order).order_by("id").limit(10).all()
    return jsonify(code=200, orders=[order.serialize_latest() for order in latest_orders])


@bp.route("/product_number", methods=["GET"])
def product_number():
    number = Product.query.count()
    return jsonify(number=number)


@bp.route("/product_list", methods=['GET', 'POST'])
def product_list():
    data = request.get_json()
    page = data['page']
    per_page = 120  # 每页10个对象，hfh改的，就要120个，没写错，不信看项目，分页是对的，且每页10个
    products = Product.query.order_by(Product.id.desc()).paginate(page=page, per_page=per_page, error_out=False).items
    return jsonify(products=[product.serialize_staff_page() for product in products])


@bp.route("/product_status", methods=['POST'])
def change_product_status():
    data = request.get_json()
    product_id = data['id']
    new_status = data['operation']
    product = Product.query.filter_by(id=product_id).first()
    if product is not None:
        if product.status == ProductStatus(new_status):
            return jsonify(code=400, error="product is already '%s'" % (product.status.name))
        else:
            product.status = ProductStatus(new_status)
            db.session.commit()
        return jsonify(code=200)
    else:
        return jsonify(code=400, error='product not found')


@bp.route("/get_statistic", methods=['GET'])
def statistic():
    last_thirty_days = datetime.now() - timedelta(days=30)
    last_ninty_days = datetime.now() - timedelta(days=90)

    pending_orders_month = Order.query.filter(
        Order.create_time >= last_thirty_days,
        Order.order_status == OrderStatus.Processing
    ).all()

    month_pending = sum(
        order.product.ori_price * order.product.discount * order.product_number for order in pending_orders_month)

    confirm_orders_month = Order.query.filter(
        Order.create_time >= last_thirty_days,
        Order.order_status == OrderStatus.Completed
    ).all()

    month_earning = sum(
        order.product.ori_price * order.product.discount * order.product_number for order in confirm_orders_month)

    pending_orders_quarter = Order.query.filter(
        Order.create_time >= last_ninty_days,
        Order.order_status == OrderStatus.Processing
    ).all()

    quarterly_pending = sum(
        order.product.ori_price * order.product.discount * order.product_number for order in pending_orders_quarter)

    confirm_orders_quarter = Order.query.filter(
        Order.create_time >= last_ninty_days,
        Order.order_status == OrderStatus.Completed
    ).all()

    quarterly_earning = sum(
        order.product.ori_price * order.product.discount * order.product_number for order in confirm_orders_quarter)

    return jsonify(
        month_pending=round(month_pending),
        month_earning=round(month_earning),
        quarterly_pending=round(quarterly_pending),
        quarterly_earning=round(quarterly_earning)
    )

