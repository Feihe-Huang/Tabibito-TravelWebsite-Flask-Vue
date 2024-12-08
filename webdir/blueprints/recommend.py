import nltk
from flask import Blueprint, jsonify, g
from models import UserBrowse, Product, User
bp = Blueprint("Recommend", __name__, url_prefix="/recommend")

wnl = nltk.WordNetLemmatizer()
stopwords = set(nltk.corpus.stopwords.words('english'))


def clean_string(s):
    s = s.lower()
    tokens = nltk.tokenize.wordpunct_tokenize(s)
    words = [w for w in tokens if w.isalpha() and w not in stopwords]
    words = [wnl.lemmatize(w) for w in words]
    cleaned_string = ' '.join(words)
    return cleaned_string


def get_similarity(str1, str2):
    str1 = clean_string(str1)
    str2 = clean_string(str2)
    distance = nltk.edit_distance(str1, str2)
    similarity = 1 - (distance / max(len(str1), len(str2)))
    return similarity


def set_similar(set1, set2):
    return len(set1.intersection(set2)) / (len(set1) + len(set2)) > 0.3


def find_similar_products(browses, products):
    similar_products = set()
    for browse in browses:
        for product in products:
            if set_similar(set(product.types), set(browse.product.types)) or \
                    product.raw_loc == browse.product.raw_loc or \
                    get_similarity(product.name, browse.product.name) >= 0.8:
                similar_products.add(product)
            # with same tags
            for tag in product.tags:
                for browse_tag in browse.product.tags:
                    if tag.key == browse_tag.key and \
                            get_similarity(tag.value, browse_tag.value) >= 0.8:
                        similar_products.add(product)
                        break
    return similar_products


@bp.route("/products", methods=["POST", "GET"])
def recommend_search():
    browses = User.query.filter_by(user_id=2).first().user_browses
    products = Product.query.all()
    result = list(find_similar_products(browses, products))[:4]

    return jsonify(products=[product.serialize_homepage() for product in result])