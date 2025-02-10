from flask import Blueprint, request, jsonify
from services.sensor_service import process_flower_data

flower_bp = Blueprint('flower', __name__)

@flower_bp.route('/data', methods=['POST'])
def receive_flower_data():
    data = request.get_json()
    response, status_code = process_flower_data(data)
    return jsonify(response), status_code
