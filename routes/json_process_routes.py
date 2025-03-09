from flask import Blueprint, jsonify
from pymongo import MongoClient
from gridfs import GridFS
import json
from bson import ObjectId

# Connect to MongoDB
MONGO_URI = "mongodb+srv://pavanshankar9000:pavan%409000@project1.gfku5.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client["Finish_db"]
fs = GridFS(db)

json_process_bp = Blueprint('json_process', __name__)

@json_process_bp.route('/json/<batch_id>/<patient_id>/<file_type>', methods=['GET'])
def get_json_data(batch_id, patient_id, file_type):
    try:
        filename = f"{patient_id}_{file_type}.json"

        # 🔹 Fix: Check if filename exists in MongoDB
        file_doc = db["fs.files"].find_one({"filename": filename})
        if not file_doc:
            return jsonify({"error": f"File '{file_type}' not found for patient '{patient_id}'"}), 404

        # 🔹 Fetch file from GridFS
        file_data = fs.get(file_doc["_id"]).read().decode("utf-8")

        # 🔹 Convert JSON string to Python dictionary and return
        return jsonify(json.loads(file_data))

    except Exception as e:
        return jsonify({"error": str(e)}), 500
