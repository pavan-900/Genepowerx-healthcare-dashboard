from flask import Blueprint, request, jsonify, send_file
import gridfs
import io
from mongo_connection import db, fs  # ✅ Import MongoDB connection
from services.patient_service import extract_batch_data, extract_batch_data2

patient_bp = Blueprint("patient_routes", __name__)

@patient_bp.route("/get-batch-data", methods=["GET"])
def get_batch_data():
    """
    Fetch all patient data from a batch stored in MongoDB.
    """
    batch_name = request.args.get("batch_name", "") # Convert to uppercase
    if not batch_name:
        return jsonify({"error": "Missing batch_name"}), 400

    batch_data = extract_batch_data(batch_name)
    return jsonify(batch_data)

@patient_bp.route("/get-batch-data2", methods=["GET"])  # ✅ Added this route
def get_batch_data2():
    """
    Fetch alternative patient data format from MongoDB.
    """
    batch_name = request.args.get("batch_name", "")# Convert to uppercase
    if not batch_name:
        return jsonify({"error": "Missing batch_name"}), 400

    batch_data = extract_batch_data2(batch_name)  # ✅ Calls extract_batch_data2
    return jsonify(batch_data), 200  # ✅ Ensure HTTP 200 OK response
@patient_bp.route("/patient_files/<batch_name>/<patient_id>/<file_type>", methods=["GET"])
def serve_patient_file(batch_name, patient_id, file_type):
    """
    Serve patient-specific PDF files based on batch, patient ID, and file type.
    The PDF will be displayed in the browser instead of downloading.
    """

    # Retrieve file from GridFS
    file_map = {
        "pdf": f"{patient_id}.pdf",
        "consent": f"{patient_id}_Consent.pdf",
        "blood_reports": f"{patient_id}_Blood_work.pdf"
    }

    # Ensure valid file type
    if file_type not in file_map:
        return jsonify({"error": "Invalid file type"}), 400

    filename = file_map[file_type]

    try:
        # Find the file in MongoDB GridFS
        file_record = db["fs.files"].find_one({"filename": filename})
        if not file_record:
            return jsonify({"error": "File not found"}), 404

        file_id = file_record["_id"]
        file_obj = fs.get(file_id)

        # ✅ Display PDF in the browser instead of forcing download
        return send_file(io.BytesIO(file_obj.read()), mimetype="application/pdf")

    except Exception as e:
        return jsonify({"error": str(e)}), 500
