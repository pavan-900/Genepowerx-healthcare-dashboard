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
availability_collection = db["availability_status"]

@app.route("/excel-download", methods=["POST"])
def generate_excel():
    """
    Generates an Excel file from received data and directly uploads it to MongoDB GridFS.
    """
    try:
        json_data = request.get_json()
        headers = json_data.get("headers", [])
        data = json_data.get("data", [])
        selected_patient = json_data.get("selectedPatient", "").strip()
        selected_batch = json_data.get("selectedBatch", "").strip()

        if not headers or not data or not selected_patient:
            return jsonify({"error": "Invalid data received"}), 400

        # ✅ Create DataFrame
        df = pd.DataFrame(data, columns=headers)

        # ✅ Save to in-memory buffer (instead of a file)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False)
        output.seek(0)  # Move cursor to the start of the buffer

        # ✅ Upload to MongoDB GridFS (No Local File Storage)
        file_id = fs.put(output, filename=f"{selected_patient}_Scoring_chart.xlsx", patient_id=selected_patient, batch=selected_batch)

        # ✅ Save report metadata in MongoDB
        report_entry = {
            "batch": selected_batch,
            "patient_id": selected_patient,
            "report_data": data,
            "timestamp": datetime.utcnow()
        }
        submitted_reports_collection.insert_one(report_entry)

        return jsonify({
            "message": "Excel file stored successfully in GridFS & Report submitted",
            "file_id": str(file_id)
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to generate Excel: {str(e)}"}), 500

@app.route("/download-excel/<batch_name>/<patient_id>", methods=["GET"])
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
