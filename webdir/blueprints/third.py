from flask import Blueprint, request, render_template, jsonify, g, session, current_app
from datetime import datetime

from flask_login import current_user

import util
from models import Order, OrderStatus

bp = Blueprint("Third", __name__, url_prefix="/third")


@bp.route("/weather", methods=['GET', 'POST'])
def weather():
    location = request.json.get("location")
    weather_data = util.get_weather_data(location)
    if weather_data is not None:
        return jsonify(city=weather_data['location']['name'], temp=int(weather_data['current']['temp_c']),
                       img_url="http:" + weather_data['current']['condition']['icon'],
                       max_temp=int(weather_data['forecast']['forecastday'][0]['day']['maxtemp_c']),
                       avg_temp=int(weather_data['forecast']['forecastday'][0]['day']['avgtemp_c']),
                       min_temp=int(weather_data['forecast']['forecastday'][0]['day']['mintemp_c'])), 200
    else:
        return jsonify(error="No weather Data"), 304


@bp.route("/weather_forecast", methods=['GET', 'POST'])
def weather_forecast():
    location = request.json.get("location")
    weather_data = util.get_weather_forcast(location)
    if weather_data is not None:
        return jsonify(
            weather=[
                {"city": weather_data['location']['name'],
                 "img_url": "http:" + weather_data['forecast']['forecastday'][0]["day"]['condition']['icon'],
                 "max_temp": int(weather_data['forecast']['forecastday'][0]['day']['maxtemp_c']),
                 "avg_temp": int(weather_data['forecast']['forecastday'][0]['day']['avgtemp_c']),
                 "min_temp": int(weather_data['forecast']['forecastday'][0]['day']['mintemp_c']),
                 "date": weather_data['forecast']['forecastday'][0]['date']},
                {"city": weather_data['location']['name'],
                 "img_url": "http:" + weather_data['forecast']['forecastday'][1]["day"]['condition']['icon'],
                 "max_temp": int(weather_data['forecast']['forecastday'][1]['day']['maxtemp_c']),
                 "avg_temp": int(weather_data['forecast']['forecastday'][1]['day']['avgtemp_c']),
                 "min_temp": int(weather_data['forecast']['forecastday'][1]['day']['mintemp_c']),
                 "date": weather_data['forecast']['forecastday'][1]['date']},
                {"city": weather_data['location']['name'],
                 "img_url": "http:" + weather_data['forecast']['forecastday'][2]["day"]['condition']['icon'],
                 "max_temp": int(weather_data['forecast']['forecastday'][2]['day']['maxtemp_c']),
                 "avg_temp": int(weather_data['forecast']['forecastday'][2]['day']['avgtemp_c']),
                 "min_temp": int(weather_data['forecast']['forecastday'][2]['day']['mintemp_c']),
                 "date": weather_data['forecast']['forecastday'][2]['date']},
            ]
        ), 200
    else:
        return jsonify(error="No weather Data"), 304


@bp.route("/flight", methods=['GET', 'POST'])
def flight():
    flight_number = request.json.get("flight_numbers")[0]
    flight_data = util.get_flight_data(flight_number)
    if flight_data is not None:
        departure = {
            "airport_no": flight_data["origin"]["code"],
            "airport_loc": flight_data["origin"]["city"],
            "airport_name": flight_data["origin"]["name"],
            "date": str(datetime.fromisoformat(flight_data["scheduled_off"][:-1]).date()),
            "time": str(datetime.fromisoformat(flight_data["scheduled_off"][:-1]).time())
        }
        arrival = {
            "airport_no": flight_data["destination"]["code"],
            "airport_loc": flight_data["destination"]["city"],
            "airport_name": flight_data["destination"]["name"],
            "date": str(datetime.fromisoformat(flight_data["scheduled_in"][:-1]).date()),
            "time": str(datetime.fromisoformat(flight_data["scheduled_in"][:-1]).time())
        }
        return jsonify(departure=departure, arrival=arrival, status=flight_data["status"]), 200
    else:
        return jsonify(error="No flight Data"), 404


@bp.route("/getfootprint", methods=['POST', 'GET'])
def get_foot_print():
    user_id = current_user.user_id
    orders = Order.query.filter_by(user_id=user_id, order_status=OrderStatus.Completed).all()
    result = []
    for order in orders:
        result.append(order.product.raw_loc)
    print(result)
    return jsonify(locations=result), 200
