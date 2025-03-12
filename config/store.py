import os
import pandas as pd
import gridfs
from bson import ObjectId
from mongoo_connection import db, fs  # ✅ Import MongoDB connection

# Path to the new batch folder
BASE_DIR = r"C:\Users\pavan\OneDrive\Desktop\complete -project22\frontend-project\GenePowerX-website\Batch4_Jan_2025"

def store_new_batch():
    """
    Reads a single batch folder and adds it to MongoDB without overwriting existing batches.
    """
    batch_collection = db["batches"]
    batch_name = os.path.basename(BASE_DIR)  # ✅ Get batch name dynamically

    existing_batch = batch_collection.find_one({"batch_name": batch_name})

    batch_data = {"batch_name": batch_name, "patients": []}

    for patient_id in os.listdir(BASE_DIR):  # ✅ Iterate through patient folders
        patient_path = os.path.join(BASE_DIR, patient_id)

        if os.path.isdir(patient_path):  # Ensure it's a folder
            patient_info = {"patient_id": patient_id, "files": {}}

            for file in os.listdir(patient_path):  # ✅ Iterate through files
                file_path = os.path.join(patient_path, file)

                # ✅ Store Excel in GridFS
                if file.endswith(".xlsx") or file.endswith(".xls"):
                    file_id = store_file_in_gridfs(file_path, file, "excel")
                    patient_info["files"]["excel"] = str(file_id)

                # ✅ Store JSON in GridFS
                elif file.endswith(".json"):
                    file_id = store_file_in_gridfs(file_path, file, "json")
                    patient_info["files"]["json"] = str(file_id)

                # ✅ Store PDF in GridFS
                elif file.endswith(".pdf"):
                    file_id = store_file_in_gridfs(file_path, file, "pdf")
                    patient_info["files"]["pdf"] = str(file_id)

            batch_data["patients"].append(patient_info)

    if existing_batch:
        # ✅ If batch exists, append new patients to the existing batch
        batch_collection.update_one(
            {"batch_name": batch_name},
            {"$push": {"patients": {"$each": batch_data["patients"]}}}
        )
    else:
        # ✅ If batch does not exist, insert new batch
        batch_collection.insert_one(batch_data)

    return {"message": f"Stored batch: {batch_name}"}

def store_file_in_gridfs(file_path, file_name, file_type):
    """
    Stores a file (Excel, JSON, PDF) in GridFS and returns the file ID.
    """
    with open(file_path, "rb") as f:
        file_id = fs.put(f, filename=file_name, file_type=file_type)
    return file_id

if __name__ == "__main__":
    result = store_new_batch()
    print(result)
