import datetime

from flask import Blueprint, jsonify, request
from sqlalchemy import or_, text, func

from exts import db
from models import Product, Trip, Tag, ProductType, Comment, UserBrowse
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.stem import WordNetLemmatizer

bp = Blueprint('Search', __name__, url_prefix='/search')


def clean_text(text):
    # 将文本转换为小写
    text = text.lower()
    # 分词
    tokens = nltk.word_tokenize(text)
    # 去除标点符号和停用词
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if word.isalnum() and word not in stop_words]
    # 词干提取
    stemmer = PorterStemmer()
    tokens = [stemmer.stem(word) for word in tokens]
    # 词形还原
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(word) for word in tokens]
    # 返回清洗后的文本
    return ' '.join(tokens)


@bp.route('/product', methods=['POST'])
def search():
    """
    Searches for products based on user input keywords
    """
    data = request.get_json()
    keywords = data.get('keywords', '')
    page = data.get('page', 1)
    per_page = data.get('per_page', 10)

    keywords_cleaned = clean_text(keywords)

    # Search for products that match the keywords in name, description, tag, or trip location detail
    products = Product.query.filter(
        or_(Product.name.ilike(f'%{keywords_cleaned}%'),
            Product.description.ilike(f'%{keywords_cleaned}%'),
            Product.tags.any(Tag.key.ilike(f'%{keywords_cleaned}%')),
            Product.trips.any(Trip.exact.ilike(f'%{keywords_cleaned}%')))
    ).paginate(page=page, per_page=per_page)

    # Serialize the products to JSON
    result = {
        'total': products.total,
        'page': products.page,
        'per_page': products.per_page,
        'items': [product.serialize() for product in products.items]
    }
    return jsonify(result)


@bp.route('/product_number', methods=["POST"])
def get_product_number():
    data = request.get_json(silent=True)
    products = db.session.query(Product).all()
    # 构造筛选条件
    filters = []
    if 'startTime' in data and data['startTime'] is not None:
        filters.append({'field': 'startTime', 'operator': '>=', 'value': data['startTime']})
    if 'endTime' in data and data['endTime'] is not None:
        filters.append({'field': 'endTime', 'operator': '<=', 'value': data['endTime']})
    if 'currentLocation' in data and data['currentLocation'] is not None:
        filters.append({'field': 'currentLocation', 'operator': '==', 'value': data['currentLocation']})
    if 'tourType' in data and data['tourType'] is not None:
        filters.append({'field': 'tourType', 'operator': '==', 'value': data['tourType']})
    if 'price' in data and data['price'] is not None:
        if data['price'] == '-500':
            high_price = 500
            filters.append({'field': 'high_price', 'operator': '<=', 'value': high_price})
        elif data['price'] == '500-1000':
            low_price = 500
            high_price = 1000
            filters.append({'field': 'low_price', 'operator': '>=', 'value': low_price})
            filters.append({'field': 'high_price', 'operator': '<=', 'value': high_price})
        elif data['price'] == '1000-2000':
            low_price = 1000
            high_price = 2000
            filters.append({'field': 'low_price', 'operator': '>=', 'value': low_price})
            filters.append({'field': 'high_price', 'operator': '<=', 'value': high_price})
        elif data['price'] == '2000+':
            low_price = 2000
            filters.append({'field': 'low_price', 'operator': '>=', 'value': low_price})
    if 'duration' in data and data['duration'] is not None:
        filters.append({'field': 'duration', 'operator': '==', 'value': data['duration']})
    if filters:
        # 使用筛选条件查询产品数据
        results = []
        for product in products:
            match = True
            for f in filters:
                if f['operator'] == '==':
                    if f['field'] == 'currentLocation' and f['value'] not in product.raw_loc:
                        match = False
                        break
                    elif f['field'] == 'tourType' and not f['value'] in product.get_types_list():
                        match = False
                        break
                    elif f['field'] == 'duration' and product.duration_time() != f['value']:
                        match = False
                        break
                elif f['operator'] == '>=':
                    if f['field'] == 'startTime' and product.start_time.timestamp() < f['value']:
                        match = False
                        break
                    elif f['field'] == 'low_price' and product.ori_price < f['value']:
                        match = False
                        break
                elif f['operator'] == '<=':
                    if f['field'] == 'endTime' and product.start_time.timestamp() < f['value']:
                        match = False
                        break
                    elif f['field'] == 'high_price' and product.ori_price > f['value']:
                        match = False
                        break
            if match:
                results.append(product)
        print(results)
        return jsonify(code=200, number=len(results))
    else:
        return jsonify(code=201, message='Wrong range', number=len(products)), 201


def get_hot_product():
    hot_product = db.session.query(Product, func.count(Comment.id).label('comment_count')) \
        .outerjoin(Comment, Product.id == Comment.product_id) \
        .group_by(Product.id) \
        .order_by(func.count(Comment.id).desc()) \
        .limit(5).all()
    return jsonify(code=200, products=[product[0].serialize_product_list() for product in hot_product])


def get_popular_product():
    popular_product = db.session.query(
        Product,
        func.count(UserBrowse.id).label("browse_count")
    ).join(Product.user_browses).group_by(Product.id).order_by(func.count(UserBrowse.id).desc()).limit(5).all()

    return jsonify(code=200, products=[product[0].serialize_product_list() for product in popular_product])


def get_type_product(tour_type):
    products = db.session.query(Product).all()
    result_product = []
    for product in products:
        if tour_type in product.get_types_list():
            result_product.append(product)
    return jsonify(code=200, products=[product.serialize_product_list() for product in result_product])


@bp.route('/product_list', methods=["POST"])
def get_product_list():
    data = request.get_json(silent=True)
    products = db.session.query(Product).all()
    # if "state" in data:
    #     if data["state"] == "hot":
    #         get_hot_product()
    #     if data["state"] == "popular":
    #         get_popular_product()
    #     if data["state"] == "type":
    #         get_type_product(data["tourType"])

    # 构造筛选条件
    filters = []
    if 'startTime' in data and data['startTime'] is not None:
        filters.append({'field': 'startTime', 'operator': '>=', 'value': data['startTime']})
    if 'endTime' in data and data['endTime'] is not None:
        filters.append({'field': 'endTime', 'operator': '<=', 'value': data['endTime']})
    if 'currentLocation' in data and data['currentLocation'] is not None:
        filters.append({'field': 'currentLocation', 'operator': '==', 'value': data['currentLocation']})
    if 'tourType' in data and data['tourType'] is not None:
        filters.append({'field': 'tourType', 'operator': '==', 'value': data['tourType']})
    if 'price' in data and data['price'] is not None:
        if data['price'] == '-500':
            high_price = 500
            filters.append({'field': 'high_price', 'operator': '<=', 'value': high_price})
        elif data['price'] == '500-1000':
            low_price = 500
            high_price = 1000
            filters.append({'field': 'low_price', 'operator': '>=', 'value': low_price})
            filters.append({'field': 'high_price', 'operator': '<=', 'value': high_price})
        elif data['price'] == '1000-2000':
            low_price = 1000
            high_price = 2000
            filters.append({'field': 'low_price', 'operator': '>=', 'value': low_price})
            filters.append({'field': 'high_price', 'operator': '<=', 'value': high_price})
        elif data['price'] == '2000+':
            low_price = 2000
            filters.append({'field': 'low_price', 'operator': '>=', 'value': low_price})
    if 'duration' in data and data['duration'] is not None:
        filters.append({'field': 'duration', 'operator': '==', 'value': data['duration']})
    # 使用筛选条件查询产品数据
    results = []
    for product in products:
        match = True
        for f in filters:
            if f['operator'] == '==':
                if f['field'] == 'currentLocation' and f['value'] not in product.raw_loc:
                    match = False
                    break
                elif f['field'] == 'tourType' and not f['value'] in product.get_types_list():
                    match = False
                    break
                elif f['field'] == 'duration' and product.duration_time() != f['value']:
                    match = False
                    break
            elif f['operator'] == '>=':
                if f['field'] == 'startTime' and product.start_time.timestamp() < f['value']:
                    match = False
                    break
                elif f['field'] == 'low_price' and product.ori_price < f['value']:
                    match = False
                    break
            elif f['operator'] == '<=':
                if f['field'] == 'endTime' and product.start_time.timestamp() < f['value']:
                    match = False
                    break
                elif f['field'] == 'high_price' and product.ori_price > f['value']:
                    match = False
                    break
        if match:
            results.append(product)
    page_number = data["page"]
    select_product = results[page_number * 3 - 3: page_number * 3]
    if len(results) == 0:
        return jsonify(code=201, products=[product.serialize_product_list() for product in select_product])
    else:
        return jsonify(code=200, products=[product.serialize_product_list() for product in select_product])
