from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from routes.batch_routes import batch_routes
from routes.patient_routes import patient_bp
from routes.json_process_routes import json_process_bp
import pandas as pd
import gridfs
import io
from pymongo import MongoClient

app = Flask(__name__)
CORS(app)

# Register Blueprints


 # ✅ Register blueprint after defining `app`

app.register_blueprint(batch_routes)
app.register_blueprint(patient_bp)
app.register_blueprint(json_process_bp)

# Connect to MongoDB
client = MongoClient("mongodb+srv://pavanshankar9000:pavan%409000@project1.gfku5.mongodb.net/?retryWrites=true&w=majority")
db = client["Finish_db"]
fs = gridfs.GridFS(db)# Initialize GridFS for file storage

@app.route("/excel-download", methods=["POST"])
def generate_excel():
    try:
        # Get JSON data from frontend
        json_data = request.get_json()
        headers = json_data.get("headers", [])
        data = json_data.get("data", [])
        selected_patient = json_data.get("selectedPatient", "").strip()
        selected_batch = json_data.get("selectedBatch", "BATCH1").strip()

        if not headers or not data or not selected_patient:
            return jsonify({"error": "Invalid data received"}), 400

        # Convert JSON to DataFrame
        df = pd.DataFrame(data, columns=[
            "condition", "low", "lowToMild", "mild", "mildToModerate", "moderate", "moderateToHigh", "high",
            "concern", "noMutation", "aiScore", "reason"
        ])
        df.columns = headers  # Rename columns based on headers

        # Save DataFrame to a BytesIO stream (in-memory file)
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False)

        # Save file in MongoDB GridFS
        file_name = f"{selected_patient}_Scoring_chart.xlsx"
        file_id = fs.put(excel_buffer.getvalue(), filename=file_name, patient_id=selected_patient, batch=selected_batch)

        return jsonify({"message": "Excel file stored in MongoDB", "file_id": str(file_id)}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to generate Excel: {str(e)}"}), 500


@app.route("/download-excel/<patient_id>", methods=["GET"])
def download_excel(patient_id):
    """
    Fetches the Excel file for a patient from MongoDB GridFS.
    """
    try:
        # Find the latest file for the given patient_id
        file_doc = db.fs.files.find_one({"patient_id": patient_id}, sort=[("uploadDate", -1)])
        if not file_doc:
            return jsonify({"error": "No Excel file found for this patient"}), 404

        # Fetch file from GridFS
        file_id = file_doc["_id"]
        file_data = fs.get(file_id)

        # Read file into memory and send for download
        return send_file(
            io.BytesIO(file_data.read()),
            as_attachment=True,
            download_name=file_doc["filename"],
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        return jsonify({"error": f"Error fetching Excel file: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True)
