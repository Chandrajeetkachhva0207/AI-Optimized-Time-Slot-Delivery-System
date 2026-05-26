"""Delivery API - ML prediction for time slots"""
from flask import Blueprint, request, jsonify
from utils.helpers import get_day_of_week, get_hour
from utils.maps_api import MapsAPI
from utils.weather_api import WeatherAPI
import os
import datetime

from ml_models.time_slot_classifier import TimeSlotClassifier
from ml_models.delivery_time_regressor import DeliveryTimeRegressor

delivery_bp = Blueprint('delivery', __name__, url_prefix='/api')

# Warehouse origin for deliveries
WAREHOUSE_COORDS = (19.0760, 72.8777)  # Central warehouse coordinates

# ML models - loaded optionally
time_slot_classifier = None
delivery_time_regressor = None


def _normalize_traffic(value):
    v = str(value or '').strip().lower()
    if v in ['low', 'l', 'light']:
        return 'low'
    if v in ['high', 'h', 'heavy']:
        return 'high'
    return 'medium'


def _normalize_weather(value):
    v = str(value or '').strip().lower()
    if v in ['sunny', 'clear', 'bright']:
        return 'sunny'
    if v in ['cloudy', 'overcast']:
        return 'cloudy'
    if v in ['rainy', 'rain', 'wet']:
        return 'rainy'
    if v in ['foggy', 'mist', 'hazy']:
        return 'foggy'
    return 'sunny'


def _shift_label(slot):
    normalized = str(slot or '').lower()
    if 'morning' in normalized:
        return 'Morning Shift (09:00 - 12:00)'
    if 'afternoon' in normalized:
        return 'Afternoon Shift (12:00 - 16:00)'
    if 'evening' in normalized:
        return 'Evening Shift (16:00 - 20:00)'
    if 'night' in normalized:
        return 'Night Shift (20:00 - 23:59)'
    return 'Anytime Delivery (09:00 - 23:59)'


def _delivery_category(minutes):
    now = datetime.datetime.now()
    arrival = now + datetime.timedelta(minutes=minutes)
    end_today = datetime.datetime(now.year, now.month, now.day, 23, 59, 59)
    if arrival <= end_today:
        return 'Today'
    if arrival <= end_today + datetime.timedelta(days=1):
        return 'Tomorrow'
    if arrival <= end_today + datetime.timedelta(days=3):
        return 'Within 3 days'
    return 'Within 5 days'


def _slot_by_arrival(arrival):
    hour = arrival.hour
    if 9 <= hour < 12:
        return 'Morning'
    if 12 <= hour < 16:
        return 'Afternoon'
    if 16 <= hour < 20:
        return 'Evening'
    if 20 <= hour < 24:
        return 'Night'
    return 'Morning'


def _eta_to_slot(minutes):
    if minutes <= 30:
        return 'Morning'
    if minutes <= 50:
        return 'Afternoon'
    if minutes <= 70:
        return 'Evening'
    return 'Night'


def _slot_risk_score(traffic_level, weather_condition, slot):
    traffic_risk = {'low': 1.0, 'medium': 1.2, 'high': 1.5}.get(traffic_level, 1.2)
    weather_risk = {'sunny': 1.0, 'cloudy': 1.1, 'rainy': 1.4, 'foggy': 1.3}.get(weather_condition, 1.1)
    slot_factor = {'Morning': 1.0, 'Afternoon': 1.0, 'Evening': 1.05, 'Night': 0.95}.get(slot, 1.0)
    return round(traffic_risk * weather_risk * slot_factor, 2)


def _build_dynamic_slot_options(now, arrival_dt, traffic_level, weather_condition):
    windows = [
        ('Morning', 9, 12),
        ('Afternoon', 12, 16),
        ('Evening', 16, 20),
        ('Night', 20, 24)
    ]

    today_last_slot_end = datetime.datetime.combine(now.date(), datetime.time(23, 59, 59))
    display_date = now.date()
    if arrival_dt > today_last_slot_end or now >= today_last_slot_end:
        display_date = now.date() + datetime.timedelta(days=1)

    day_label = 'Tomorrow' if display_date > now.date() else 'Today'
    slot_list = []
    recommended_found = False

    for slot_name, start_hour, end_hour in windows:
        start_dt = datetime.datetime.combine(display_date, datetime.time(start_hour, 0))
        if end_hour == 24:
            end_dt = datetime.datetime.combine(display_date, datetime.time(23, 59, 59))
        else:
            end_dt = datetime.datetime.combine(display_date, datetime.time(end_hour, 0))
        available = end_dt > now if day_label == 'Today' else True
        contains_arrival = start_dt <= arrival_dt <= end_dt
        risk_score = _slot_risk_score(traffic_level, weather_condition, slot_name)
        window_text = _slot_time_window(slot_name)

        slot_list.append({
            'slot_short': slot_name,
            'window': window_text,
            'day': day_label,
            'available': available,
            'risk_score': risk_score,
            'recommended': False,
            'arrival_estimate': arrival_dt.isoformat()
        })

        if contains_arrival and available:
            slot_list[-1]['recommended'] = True
            recommended_found = True

    if not recommended_found:
        available_slots = [slot for slot in slot_list if slot['available']]
        if available_slots:
            best_slot = min(available_slots, key=lambda s: s['risk_score'])
            best_slot['recommended'] = True
        else:
            slot_list[0]['recommended'] = True

    return slot_list


def _slot_time_window(slot):
    if slot == 'Morning':
        return '09:00 AM - 12:00 PM'
    if slot == 'Afternoon':
        return '12:00 PM - 04:00 PM'
    if slot == 'Evening':
        return '04:00 PM - 08:00 PM'
    if slot == 'Night':
        return '08:00 PM - 11:59 PM'
    return '09:00 AM - 11:59 PM'


def _traffic_factor(level):
    return {
        'low': 0.85,
        'medium': 1.0,
        'high': 1.35
    }.get(level, 1.0)


def _weather_factor(condition):
    return {
        'sunny': 0.9,
        'cloudy': 1.0,
        'rainy': 1.25,
        'foggy': 1.15
    }.get(condition, 1.0)


def _weight_multiplier(weight):
    weight = float(weight or 2.0)
    return 1.0 + min(0.7, max(0.0, (weight - 2.0) * 0.14))


def _slot_time_multiplier(slot):
    return {
        'Morning': 1.05,
        'Afternoon': 1.0,
        'Evening': 1.08,
        'Night': 0.95
    }.get(slot, 1.0)


def _compute_eta(distance, traffic_level, weather_condition, package_weight, slot):
    base = float(distance) * 4.0
    traffic_adj = _traffic_factor(traffic_level)
    weather_adj = _weather_factor(weather_condition)
    weight_adj = _weight_multiplier(package_weight)
    slot_adj = _slot_time_multiplier(slot)
    estimated = base * traffic_adj * weather_adj * weight_adj * slot_adj + 12
    return max(20, int(round(estimated)))


def _compute_risk_score(traffic_level, weather_condition, package_weight, slot):
    traffic_risk = {'low': 0.8, 'medium': 1.0, 'high': 1.25}.get(traffic_level, 1.0)
    weather_risk = {'sunny': 0.8, 'cloudy': 1.0, 'rainy': 1.35, 'foggy': 1.2}.get(weather_condition, 1.0)
    weight_risk = 1.0 + min(0.5, max(0.0, (float(package_weight or 2.0) - 2.0) * 0.12))
    slot_risk = {'Morning': 1.0, 'Afternoon': 1.0, 'Evening': 1.08, 'Night': 0.92}.get(slot, 1.0)
    return traffic_risk * weather_risk * weight_risk * slot_risk


def _compute_confidence_pct(eta, risk_score):
    base = 100 - ((eta - 20) / 40) * 16 - ((risk_score - 1.0) * 18)
    return round(max(55, min(96, base)))


def _generate_slot_options(model_input, predicted_slot):
    choices = ['Morning', 'Afternoon', 'Evening', 'Night']
    slots = []
    for choice in choices:
        eta_minutes = _compute_eta(
            model_input['distance'],
            model_input['traffic_level'],
            model_input['weather_condition'],
            model_input['package_weight'],
            choice
        )
        risk_score = _compute_risk_score(
            model_input['traffic_level'],
            model_input['weather_condition'],
            model_input['package_weight'],
            choice
        )
        confidence_pct = _compute_confidence_pct(eta_minutes, risk_score)
        score = eta_minutes * risk_score
        slots.append({
            'slot_short': choice,
            'time_window': _slot_time_window(choice),
            'eta_minutes': eta_minutes,
            'eta_readable': f'{eta_minutes} mins',
            'confidence_pct': confidence_pct,
            'risk_score': round(risk_score, 2),
            'score': round(score, 1),
            'recommendation': 'Safe',
            'optimal': False
        })

    fastest = min(slots, key=lambda s: s['eta_minutes'])
    safest = min(slots, key=lambda s: s['risk_score'])
    best = next((s for s in slots if s['slot_short'].lower() == str(predicted_slot or '').lower()), None)
    if not best:
        best = min(slots, key=lambda s: s['score'])

    for slot in slots:
        if slot['slot_short'] == best['slot_short']:
            slot['recommendation'] = 'Best'
            slot['optimal'] = True
        elif slot['slot_short'] == fastest['slot_short']:
            slot['recommendation'] = 'Fast'
        elif slot['slot_short'] == safest['slot_short']:
            slot['recommendation'] = 'Safe'
        else:
            slot['recommendation'] = 'Safe'

    return slots


def init_ml_models(model_path):
    """Load ML models if they exist"""
    global time_slot_classifier, delivery_time_regressor
    loaded = False
    try:
        cls_path = os.path.join(model_path, 'time_slot_classifier.pkl')
        if os.path.exists(cls_path):
            time_slot_classifier = TimeSlotClassifier(model_path=cls_path)
            time_slot_classifier.load_model()
            loaded = True
    except Exception as e:
        print(f"Time slot classifier load skipped: {e}")
        time_slot_classifier = None

    try:
        reg_path = os.path.join(model_path, 'delivery_time_regressor.pkl')
        if os.path.exists(reg_path):
            delivery_time_regressor = DeliveryTimeRegressor(model_path=reg_path)
            delivery_time_regressor.load_model()
            loaded = True
    except Exception as e:
        print(f"Delivery time regressor load skipped: {e}")
        delivery_time_regressor = None

    return loaded


def predict_slot_internal(distance, traffic, weather, order_hour, package_weight=2.0, day_of_week=None, full=False):
    """
    Internal prediction - used by checkout.
    Returns slot string or full prediction details.
    """
    global time_slot_classifier, delivery_time_regressor

    traffic_level = _normalize_traffic(traffic)
    weather_condition = _normalize_weather(weather)
    hour = int(order_hour or get_hour())
    day_of_week = day_of_week if day_of_week is not None else get_day_of_week()

    model_input = {
        'distance': float(distance),
        'traffic_level': traffic_level,
        'weather_condition': weather_condition,
        'temperature': 25.0,
        'package_weight': float(package_weight or 2.0),
        'day_of_week': int(day_of_week),
        'hour': hour
    }

    predicted_slot = None
    confidence = 0.0
    if time_slot_classifier:
        try:
            result = time_slot_classifier.predict(model_input)
            predicted_slot = result.get('predicted_slot', 'Afternoon')
            confidence = float(result.get('confidence', 0.75))
        except Exception as e:
            print(f"ML slot prediction failed: {e}")

    if not predicted_slot:
        if hour < 12:
            predicted_slot = 'Morning'
        elif hour < 16:
            predicted_slot = 'Afternoon'
        else:
            predicted_slot = 'Evening'
        confidence = 0.65

    delivery_minutes = None
    selected_slot = None
    if delivery_time_regressor:
        try:
            delivery = delivery_time_regressor.predict(model_input)
            delivery_minutes = max(10, int(round(delivery.get('estimated_time_minutes', 60))))
            selected_slot = delivery.get('estimated_slot')
            confidence = float(delivery.get('confidence', confidence))
            confidence_pct = int(round(delivery.get('confidence_pct', confidence * 100)))
        except Exception as e:
            print(f"ML delivery time regression failed: {e}")
            delivery_minutes = None
            selected_slot = None

    if delivery_minutes is None:
        delivery_minutes = max(30, int(round(float(distance) * 5 + (traffic_level == 'high') * 15 + float(package_weight or 2.0) * 3)))
        selected_slot = _eta_to_slot(delivery_minutes)
        confidence_pct = int(round(confidence * 100))

    if not selected_slot:
        selected_slot = _eta_to_slot(delivery_minutes)

    now = datetime.datetime.now()
    arrival_time = now + datetime.timedelta(minutes=delivery_minutes)
    if arrival_time.date() > now.date() or arrival_time.hour < 9:
        selected_slot = _slot_by_arrival(arrival_time)

    delivery_category = _delivery_category(delivery_minutes)
    slot_label = _shift_label(selected_slot)
    predicted_label = slot_label
    if delivery_category == 'Tomorrow' or delivery_category.startswith('Within'):
        predicted_label = f"{delivery_category} {slot_label}"

    if full:
        return {
            'predicted_slot': predicted_label,
            'slot_short': selected_slot,
            'estimated_minutes': delivery_minutes,
            'estimated_time_readable': f'{delivery_minutes} mins',
            'delivery_category': delivery_category,
            'confidence': confidence,
            'confidence_pct': confidence_pct,
            'window': slot_label,
            'reason': 'Gradient boosting ETA model converted into delivery slots using distance, traffic, weather, time, and package weight.',
            'eta_slot': selected_slot,
            'arrival_time': arrival_time.isoformat()
        }

    return slot_label


@delivery_bp.route('/predict_slot', methods=['POST', 'GET'])
def predict_slot():
    """Predict optimal delivery time slot - POST with JSON or GET with query params"""
    try:
        if request.method == 'POST':
            data = request.get_json() or {}
        else:
            data = request.args

        # Build destination address from checkout input when provided
        raw_address = data.get('address') or data.get('destination') or ''
        if not raw_address:
            raw_address = ' '.join(filter(None, [data.get('street_address'), data.get('city'), data.get('state'), data.get('pincode')]))

        order_hour = int(data.get('order_hour', get_hour()))
        package_weight = float(data.get('package_weight', 2.0))
        day_of_week = int(data.get('day_of_week', get_day_of_week()))

        distance = float(data.get('distance', 0) or 0)
        traffic = data.get('traffic')
        weather = data.get('weather')
        temperature = float(data.get('temperature', 0) or 0)
        location_name = None
        demo_mode = False
        fallback_messages = []

        if raw_address:
            maps_api = MapsAPI(api_key=os.environ.get('GOOGLE_MAPS_API_KEY', ''))
            weather_api = WeatherAPI(api_key=os.environ.get('OPENWEATHER_API_KEY', ''))
            geocode = maps_api.geocode_address(raw_address)
            latitude = geocode.get('latitude')
            longitude = geocode.get('longitude')
            location_name = geocode.get('formatted_address') or raw_address

            if latitude is not None and longitude is not None:
                distance_data = maps_api.get_distance_and_traffic(WAREHOUSE_COORDS, (latitude, longitude))
                distance = float(distance_data.get('distance_km', distance or 10))
                traffic = traffic or distance_data.get('traffic_level', 'medium')

                weather_info = weather_api.get_weather(latitude, longitude)
                weather = weather or weather_info.get('condition', 'sunny')
                temperature = temperature or float(weather_info.get('temperature', 25.0))

                if not os.environ.get('GOOGLE_MAPS_API_KEY') or not os.environ.get('OPENWEATHER_API_KEY'):
                    demo_mode = True
                    fallback_messages.append('Demo mode: live geocode or weather API key missing.')
            else:
                demo_mode = True
                fallback_messages.append('Address geocoding unavailable; using fallback prediction.')

        if not traffic:
            traffic = 'medium'
        if not weather:
            weather = 'sunny'
        if not distance or distance <= 0:
            distance = 10.0
        if not temperature:
            temperature = 25.0

        prediction = predict_slot_internal(
            distance=distance,
            traffic=traffic,
            weather=weather,
            order_hour=order_hour,
            package_weight=package_weight,
            day_of_week=day_of_week,
            full=True
        )

        arrival_dt = datetime.datetime.fromisoformat(prediction['arrival_time'])
        dynamic_slots = _build_dynamic_slot_options(
            datetime.datetime.now(), arrival_dt, traffic, weather
        )

        return jsonify({
            'success': True,
            'distance_km': distance,
            'traffic_level': traffic,
            'weather_condition': weather,
            'temperature': temperature,
            'location': location_name,
            'demo_mode': demo_mode,
            'fallback_messages': fallback_messages,
            'dynamic_slots': dynamic_slots,
            **prediction
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
