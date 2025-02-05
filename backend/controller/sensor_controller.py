from flask import Blueprint, request, jsonify
from services.sensor_service import process_sensor_data

sensor_bp = Blueprint('sensor', __name__)

@sensor_bp.route('/data', methods=['POST'])
def receive_sensor_data():
    data = request.get_json()
    response, status_code = process_sensor_data(data)
    return jsonify(response), status_code
