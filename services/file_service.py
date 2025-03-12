import os
# from config.sys_paths import BASE_DIR

from mongo_connection import db  # ✅ Import MongoDB connection

def get_batches_with_files():
    """
    Fetches batch data from MongoDB instead of local file system.
    """
    batch_collection = db["batches"]
    batches = {}

    # ✅ Fetch all batch documents from MongoDB
    for batch in batch_collection.find({}, {"_id": 0, "batch_name": 1, "patients.patient_id": 1}):
        batch_name = batch["batch_name"] # Normalize batch name
        patient_ids = [p["patient_id"] for p in batch.get("patients", [])]  # Extract patient IDs
        batches[batch_name] = patient_ids  # Store batch data

    return batches

