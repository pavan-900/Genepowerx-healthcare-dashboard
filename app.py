from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from routes.batch_routes import batch_routes
from routes.patient_routes import patient_bp
from routes.json_process_routes import json_process_bp
import pandas as pd
import gridfs
import io
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ✅ Register Blueprints
app.register_blueprint(batch_routes)
app.register_blueprint(patient_bp)
app.register_blueprint(json_process_bp)

# ✅ Connect to MongoDB
client = MongoClient("mongodb+srv://pavanshankar:pavan%4096188@cluster0.mns8h.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["Finish_db"]
fs = gridfs.GridFS(db)
submitted_reports_collection = db["submitted_reports"]
availability_collection = db["availability_status"]  # ✅ New collection for availability statusF
@app.route("/upload-pdf", methods=["POST"])
def upload_pdf():
    """
    Uploads PDF files for a patient inside a batch and stores them in MongoDB GridFS.
    """
    try:
        batch_name = request.args.get("batch_name", "").strip()
        patient_id = request.args.get("patient_id", "").strip()

        if "pdfs" not in request.files:
            return jsonify({"error": "No PDF file uploaded"}), 400

        uploaded_files = request.files.getlist("pdfs")  # Multiple PDFs

        file_ids = []
        for file in uploaded_files:
            file_id = fs.put(file, filename=file.filename, patient_id=patient_id, batch=batch_name)
            file_ids.append(str(file_id))

        return jsonify({"message": "PDFs uploaded successfully", "file_ids": file_ids}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to upload PDFs: {str(e)}"}), 500

@app.route("/excel-download", methods=["POST"])
def generate_excel():
    """
    Stores JSON data in MongoDB as an object but does NOT generate or store an Excel file.
    """
    try:
        json_data = request.get_json()
        selected_patient = json_data.get("selectedPatient", "").strip()
        selected_batch = json_data.get("selectedBatch", "").strip()
        data = json_data.get("data", [])

        if not selected_patient or not data:
            return jsonify({"error": "Invalid data received"}), 400

        # ✅ Store JSON data in MongoDB (as an object)
        report_entry = {
            "batch": selected_batch,
            "patient_id": selected_patient,
            "report_data": data,
            "timestamp": datetime.utcnow()
        }
        inserted_id = submitted_reports_collection.insert_one(report_entry).inserted_id

        return jsonify({
            "message": "Report submitted successfully",
            "document_id": str(inserted_id)
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to submit report: {str(e)}"}), 500


@app.route("/f/<batch_name>/<patient_id>", methods=["GET"])
def download_excel(batch_name, patient_id):
    """
    Fetches the latest Excel file for a patient from MongoDB GridFS.
    """
    try:
        file_doc = db.fs.files.find_one({"patient_id": patient_id, "batch": batch_name}, sort=[("uploadDate", -1)])
        if not file_doc:
            return jsonify({"error": "No Excel file found for this patient"}), 404

        file_id = file_doc["_id"]
        file_data = fs.get(file_id)

        return send_file(
            io.BytesIO(file_data.read()),
            as_attachment=True,
            download_name=file_doc["filename"],
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        return jsonify({"error": f"Error fetching Excel file: {str(e)}"}), 500

@app.route("/update-availability", methods=["POST"])
def update_availability():
    """
    Updates patient availability status (Available = 🟠, Not Available = 🔴).
    """
    try:
        json_data = request.get_json()
        batch_name = json_data.get("batch_name", "").strip()
        patient_id = json_data.get("patient_id", "").strip()
        availability = json_data.get("availability", "").strip()

        if not batch_name or not patient_id or availability not in ["available", "not_available"]:
            return jsonify({"error": "Invalid data received"}), 400

        availability_collection.update_one(
            {"batch": batch_name, "patient_id": patient_id},
            {"$set": {"available": availability == "available"}},
            upsert=True
        )

        return jsonify({"message": "Availability status updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to update availability: {str(e)}"}), 500

@app.route("/get-report-status", methods=["GET"])
def get_report_status():
    """
    Fetches report submission and availability status from MongoDB.
    """
    batch_name = request.args.get("batch_name", "").strip()
    if not batch_name:
        return jsonify({"error": "Batch name is required"}), 400

    patient_reports = {}
    reports = submitted_reports_collection.find({"batch": batch_name})

    for report in reports:
        patient_id = report["patient_id"]
        patient_reports[patient_id] = {"submitted": True}

    availability_data = availability_collection.find({"batch": batch_name})
    for entry in availability_data:
        patient_id = entry["patient_id"]
        patient_reports.setdefault(patient_id, {})["available"] = entry["available"]

    return jsonify(patient_reports), 200



@app.route("/submit-report", methods=["POST"])
def submit_report():
    """
    Saves the submitted report details in MongoDB.
    """
    try:
        json_data = request.get_json()
        selected_patient = json_data.get("selectedPatient", "").strip()
        selected_batch = json_data.get("selectedBatch", "").strip()
        report_data = json_data.get("report_data", [])

        if not selected_patient or not selected_batch or not report_data:
            return jsonify({"error": "Invalid data received"}), 400

        if "submitted_reports" not in db.list_collection_names():
            db.create_collection("submitted_reports")

        report_entry = {
            "batch": selected_batch,
            "patient_id": selected_patient,
            "report_data": report_data,
            "timestamp": datetime.utcnow()
        }
        inserted_id = db.submitted_reports.insert_one(report_entry).inserted_id

        return jsonify({"message": "Report submitted successfully", "report_id": str(inserted_id)}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to submit report: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
