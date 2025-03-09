from flask import Blueprint, jsonify
from services.file_service import get_batches_with_files

batch_routes = Blueprint('batch_routes', __name__)

@batch_routes.route('/get-batches', methods=['GET'])
def get_batches():
    """
    Fetch batches with patient files.
    """
    try:
        batch_data = get_batches_with_files()
        return jsonify(batch_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
