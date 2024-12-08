import datetime
from flask import Blueprint, jsonify, request
from flask_login import current_user, AnonymousUserMixin
import os
from exts import db
from config import Config
from werkzeug.utils import secure_filename
from models import Product, ProductPicture, Tag, Trip, FeeDes, ProductType, Comment, PictureType, UserBrowse, NoticeType, UserNotice

bp = Blueprint("Product", __name__, url_prefix="/product")


@bp.route("/add", methods=["POST", "GET"])
def add_product():
    data = request.get_json()
    if 'name' in data and 'description' in data and 'group_number' in data:
        name = data['name']
        description = data['description']
        group_number = data['group_number']
        if name and description and group_number:
            if "product_id" in data:
                product = Product.query.filter_by(id=data['product_id']).first()
                product.name = name
                product.description =description
                product.group_number = group_number
            else:
                product = Product(name=name, description=description, group_number=group_number)
            location = data['location']
            if location:
                product.raw_loc = location['raw_loc']
                product.map_latitude = location['map_latitude']
                product.map_longitude = location['map_longitude']
                product.map_zoom = location['map_zoom']
            discount = data['discount']
            if discount:
                product.discount = discount
            total_day_number = data['total_day_number']
            if total_day_number:
                product.total_day_number = total_day_number
            ori_price = data['ori_price']
            if ori_price:
                product.ori_price = ori_price
            currency = data['currency']
            if currency:
                product.currency = currency
            start_time = data['start_time']
            if start_time:
                product.start_time = datetime.datetime.fromtimestamp(int(start_time) / 1000)
            end_time = data['end_time']
            if end_time:
                product.end_time = datetime.datetime.fromtimestamp(int(end_time) / 1000)
            app_ddl = data['app_ddl']
            if app_ddl:
                product.app_ddl = datetime.datetime.fromtimestamp(int(app_ddl) / 1000)
            flight_numbers = data['flight_numbers']
            if flight_numbers and len(flight_numbers) > 0:
                flight_numbers = " ".join([str(n).strip() for n in data['flight_numbers']])
                product.flight = flight_numbers
            video_url = data["video_link"]
            if video_url:
                product.video_url = video_url
            if "product_id" not in data:
                db.session.add(product)
            db.session.commit()

            types = data['types']
            if types:
                product.types = []
                for i in types:
                    t = ProductType.query.filter(ProductType.type == i).first()
                    product.types.append(t)

            cover_image = data['cover_image']
            if cover_image:
                if "product_id" in data:
                    for i in product.pictures:
                        db.session.delete(i)
                p = ProductPicture(product_id=product.id, address=cover_image, type=PictureType.Cover)
                db.session.add(p)
            banner_image = data['banner_image']
            if banner_image:
                for p in banner_image:
                    p = ProductPicture(product_id=product.id, address=p, type=PictureType.Banner)
                    db.session.add(p)
            gallery = data['gallery']
            if gallery:
                for picture in gallery:
                    p = ProductPicture(product_id=product.id, address=picture, type=PictureType.Gallery)
                    db.session.add(p)

            tags = data['tags']
            if tags:
                if "product_id" in data:
                    for i in product.tags:
                        db.session.delete(i)
                for tag in tags:
                    if tag['key']:
                        t = Tag(key=tag["key"], value=tag['value'], product_id=product.id)
                        db.session.add(t)
            trips = data['trips']
            if trips:
                if "product_id" in data:
                    for i in product.trips:
                        db.session.delete(i)
                for trip in trips:
                    t = Trip(
                        product_id=product.id,
                        time=datetime.datetime.fromtimestamp(int(trip['time']) / 1000),
                        activity=trip['activity'],
                        picture=trip['picture'],
                        day=trip['day'],
                        time_of_day=trip['time_of_day']
                    )
                    t.exact = trip['location']['exact']
                    t.map_latitude = trip['location']['map_latitude']
                    t.map_longitude = trip['location']['map_longitude']
                    t.map_zoom = trip['location']['map_zoom']
                    db.session.add(t)
            fee_des = data['fee_des']
            if fee_des:
                if "product_id" in data:
                    for i in product.fee_des:
                        db.session.delete(i)
                for f in fee_des:
                    fee = FeeDes(product_id=product.id, name=f['name'], description=f['description'])
                    db.session.add(fee)

            db.session.commit()
            return jsonify(code=200)
        else:
            return jsonify(code=400, error="name or description or group_number null")
    else:
        return jsonify(code=400, error="name or description or group_number missing")


@bp.route("/detail", methods=['POST', 'GET'])
def product_detail():
    product_id = request.json.get('product_id')
    product = Product.query.filter(Product.id == product_id).first()
    if current_user.is_authenticated:
        user_browse = UserBrowse(product_id=product_id, user_id=current_user.user_id, duration=3)
        product.user_browses.append(user_browse)
        db.session.commit()
    return jsonify(product=product.serialize_detail())


@bp.route("/type_products", methods=["POST", "GET"])
def get_type_products():
    product_type = request.json.get('type')
    products = Product.query.join(Product.types).filter(ProductType.type == product_type).all()
    return jsonify(products=[product.serialize() for product in products])


@bp.route("/get_product_grade", methods=["POST", "GET"])
def get_product_grade():
    product_id = request.get_json(silent=True)["product_id"]
    product = Product.query.filter_by(id=product_id).first()
    if len(product.comments) != 0:
        marks = product.get_each_part_mark()
        return jsonify(code=200,
                       exceptional=marks["exceptional"], location=marks["location"], staff=marks["staff"],
                       cleanliness=marks["cleanliness"], value_for_money=marks["value_for_money"],
                       comfort=marks["comfort"], facilities=marks["facilities"],
                       free_wifi=marks["free_wifi"])
    else:
        return jsonify(code=201, message="No comments for the project")


@bp.route("/get_reviews", methods=["POST", "GET"])
def get_reviews_number():
    product_id = request.get_json(silent=True)["product_id"]
    product = Product.query.filter_by(id=product_id).first()
    return jsonify(code=200, reviews_num=len(product.comments))


@bp.route("/get_comment", methods=["POST"])
def get_comments():
    data = request.get_json(silent=True)
    product_id = data["product_id"]
    page = data["page"]
    page_size = 10
    comments = Comment.query.filter_by(product_id=product_id).order_by(Comment.datetime.desc()) \
        .offset((page - 1) * page_size).limit(page_size).all()
    return jsonify(code=200, comments=[comment.serialize_product_page_simple() for comment in comments])


@bp.route("/uploadpicture", methods=["POST", "GET"])
def upload_picture():
    files = request.files.values()
    file_paths = []
    filename = ""
    for file in files:
        filename = secure_filename(file.filename)
        file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(file_path)
        file_paths.append(file_path)
    return os.path.join(Config.BASE_URL, Config.UPLOAD_URL, filename)


@bp.route("/deletepicture", methods=["POST", "GET"])
def delete_picture():
    url = request.json.get("url")
    file_name = os.path.join(Config.UPLOAD_FOLDER, os.path.split(url)[-1])
    if os.path.isfile(file_name):
        picture = ProductPicture.query.filter_by(address=url).first()
        if picture:
            db.session.delete(picture)
            db.session.commit()
        os.remove(file_name)
        return {}, 204
    else:
        return {}, 404


@bp.route("/charge_detail", methods=["POST", "GET"])
def charge_detail():
    data = request.get_json(silent=True)
    product_id = data['product_id']
    fee_des = FeeDes.query.filter(FeeDes.product_id == product_id).all()
    if len(fee_des) == 0:
        return jsonify(code="product not found")
    else:
        return jsonify(charges=[fee.serialize() for fee in fee_des])


@bp.route("/trips", methods=["POST", "GET"])
def get_trips():
    data = request.get_json(silent=True)
    product_id = data['product_id']
    product = Product.query.filter(Product.id == product_id).first()
    trips = product.trips
    if len(trips) == 0:
        return jsonify(code="product not found")
    else:
        return jsonify(location=product.location(), trips=[trip.serialize() for trip in trips])


@bp.route("/video", methods=["POST", "GET"])
def get_video():
    data = request.get_json(silent=True)
    product_id = data['product_id']
    product = Product.query.filter(Product.id == product_id).first()
    video = product.video_url
    if video:
        return jsonify(video_link=video), 200
    else:
        return {}, 404


@bp.route("/add_notice_tag", methods=["POST", "GET"])
def add_notice_tag():
    data = request.get_json(silent=True)
    tag = data['new_tag']
    tag = NoticeType.query.filter_by(type=tag).first()
    if tag:
        return {}, 304
    else:
        tag = NoticeType(type=tag)
        db.session.add(tag)
        db.session.commit()
        return {}, 204


@bp.route("/get_edit_info", methods=["POST", "GET"])
def get_edit_info():
    product_id = request.json.get("product_id")
    product = Product.query.filter_by(id=product_id).first()
    if product:
        result = product.serialize_edit_info()
        types = NoticeType.query.all()
        result['notice_tags'] = [type.type for type in types]
        return result, 200
    else:
        return {}, 404


@bp.route("/send_notice", methods=["POST", "GET"])
def send_notice():
    product_id = request.json.get("product_id")
    product = Product.query.filter_by(id=product_id).first()
    if product:
        notice_type = request.json.get("tag")
        title = request.json.get("title")
        content = request.json.get("content")

        for order in product.orders:
            customer = order.user
            notice = UserNotice(type=notice_type, title=title, content=content)
            notice.user = customer
            db.session.add(notice)
        db.session.commit()
        return {}, 200
    else:
        return {}, 404
