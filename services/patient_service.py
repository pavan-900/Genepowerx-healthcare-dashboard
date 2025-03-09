import pandas as pd
import io
import gridfs
from bson import ObjectId
from mongo_connection import db, fs  # ✅ Import MongoDB connection
import numpy as np

def extract_batch_data(batch_name):
    """
    Fetches batch data from MongoDB and extracts patient Excel data.
    Returns only subcategories (no conditions).
    """
    batch_data = db["batches"].find_one({"batch_name": batch_name}, {"_id": 0, "patients": 1})


    if not batch_data:
        return {"error": f"Batch '{batch_name}' not found in database"}

    processed_data = {}

    for patient in batch_data.get("patients", []):
        if "excel" in patient["files"]:
            file_id = patient["files"]["excel"]
            
            # ✅ Retrieve the filename from GridFS
            file_record = db["fs.files"].find_one({"_id": ObjectId(file_id)})
            if not file_record:
                print(f"❌ No file found in GridFS with _id {file_id}")
                continue  
            
            file_name = file_record["filename"]
            print(f"✅ Fetching file: {file_name} ({file_id})")

            # ✅ Read the Excel file from GridFS
            excel_data = read_excel_from_gridfs(file_id)

            # ✅ Fix: Only return subcategories (exclude conditions)
            processed_data[file_name] = {
                "subcategories": excel_data.get("subcategories", [])
            }

    return {"conditions": processed_data}  # ✅ Matches expected output structure

def extract_batch_data2(batch_name):
    """
    Fetches batch data from MongoDB with only conditions.
    Returns conditions only (no subcategories).
    """
    batch_data = db["batches"].find_one({"batch_name": batch_name}, {"_id": 0, "patients": 1})


    if not batch_data:
        return {"error": f"Batch '{batch_name}' not found in database"}

    processed_data = {}

    for patient in batch_data.get("patients", []):
        if "excel" in patient["files"]:
            file_id = patient["files"]["excel"]
            
            # ✅ Retrieve the filename from GridFS
            file_record = db["fs.files"].find_one({"_id": ObjectId(file_id)})
            if not file_record:
                print(f"❌ No file found in GridFS with _id {file_id}")
                continue  
            
            file_name = file_record["filename"]
            print(f"✅ Fetching file: {file_name} ({file_id})")

            # ✅ Read the Excel file from GridFS
            excel_data = read_excel_from_gridfs(file_id)

            # ✅ Fix: Only store conditions (no subcategories)
            processed_data[file_name] = {
                "conditions": excel_data.get("conditions", [])
            }

    return processed_data  # ✅ Correct syntax and structure

def read_excel_from_gridfs(file_id):
    """
    Reads an Excel file from MongoDB GridFS and extracts patient data.
    """
    try:
        if not ObjectId.is_valid(file_id):
            return {"error": f"Invalid file_id: {file_id}"}

        file_obj = fs.get(ObjectId(file_id))  
        if not file_obj:
            return {"error": f"No file found in GridFS with _id {file_id}"}

        excel_data = pd.ExcelFile(io.BytesIO(file_obj.read()))
        patient_data = {"subcategories": [], "conditions": []}

        for sheet_name in excel_data.sheet_names:
            df = excel_data.parse(sheet_name)

            if df.empty:
                continue  

            # ✅ Extract "subcategories" (for extract_batch_data)
            category_icon_mapping = {
                "Pathogenic Variants": "Icons/PathogenicVariantsIcon.png",
                "Conflicting Variants": "Icons/ConflictingVariantsIcon.png",
                "Diabetes": "Icons/DiabetesIcon.png",
                "High Blood Pressure": "Icons/High_Blood_PressureIcon.png",
                "Cardiac Health": "Icons/Cardiac_HealthIcon.png",
                "Cholesterol Disorders": "Icons/Cholesterol_DisordersIcon.png",
                "Thyroid Disorders": "Icons/Thyroid_DisordersIcon.png",
                "Parkinsons": "Icons/ParkinsonsIcon.png",
                "Dementia": "Icons/DementiaIcon.png",
                "Headaches": "Icons/HeadachesIcon.png",
                "Allergies": "Icons/AllergiesIcon.png",
                "Anemia": "Icons/AnemiaIcon.png",
                "Fatty Liver": "Icons/Fatty_LiverIcon.png",
                "Gall stones": "Icons/Gall_stonesIcon.png",
                "Pancreatic Disorders": "Icons/Pancreatic_DisordersIcon.png",
                "Gut Health": "Icons/Gut_HealthIcon.png",
                "Gastritis": "Icons/GastritisIcon.png",
                "Glomerular Diseases": "Icons/Glomerular_DiseasesIcon.png",
                "Interstitial Nephritis": "Icons/Interstitial_NephritisIcon.png",
                "Renal stones": "Icons/Renal_stonesIcon.png",
                "Skin Health": "Icons/Skin_HealthIcon.png",
                "Arthritis Degenerative Joint": "Icons/Arthritis_Degenerative_JointIcon.png",
                "Mood Disorders": "Icons/Mood_DisordersIcon.png",
                "Obesity": "Icons/ObesityIcon.png",
                "Bone Joint health": "Icons/Bone_Joint_healthIcon.png",
                "Muscular health": "Icons/Muscular_healthIcon.png"
            }

            icon_path = category_icon_mapping.get(sheet_name, "Icons/DefaultIcon.png")

            # ✅ Fix: Special handling for Pathogenic Variants and Conflicting Variants
            if sheet_name.lower() in ["pathogenic variants", "conflicting variants"]:
                patient_data["subcategories"].append({
                    "icon": icon_path,
                    "name": sheet_name,
                    "subcategories": [{"name": sheet_name, "subtype": [{"name": sheet_name}]}]
                })
            else:
                if 'Headings' in df.columns and 'Condition' in df.columns:
                    subcategory_obj = {
                        "icon": icon_path,
                        "name": sheet_name,
                        "subcategories": [
                            {
                                "name": heading,
                                "subtype": [{"name": cond} for cond in group['Condition'].dropna().unique()]
                            }
                            for heading, group in df.groupby('Headings')
                        ]
                    }
                    patient_data["subcategories"].append(subcategory_obj)

            # ✅ Extract "conditions" (for extract_batch_data2)
            df.columns = [' '.join(col.split('_')) for col in df.columns]
            for _, row in df.iterrows():
                json_object = {
                    "Condition": sheet_name if sheet_name in ["Pathogenic Variants", "Conflicting Variants"] else row.get("Condition", None),
                    "Headings": sheet_name if sheet_name in ["Pathogenic Variants", "Conflicting Variants"] else row.get("Headings", None),
                    "subtype_cond": sheet_name,
                    "Gene Name": row.get("Gene", None),
                    "Gene Score": row.get("Gene Score", None),
                    "rsID": row.get("rsID", None),
                    "Lit": row.get("Literature", None),
                    "ref": row.get("REF", None),
                    "alt": row.get("ALT", None),
                    "CH": row.get("CHROM", None),
                    "POS": row.get("POS", None),
                    "Zygosity": row.get("Zygosity", None),
                    "Consequence": row.get("Consequence", None),
                    "Conseq score": row.get("Consequence score", None),
                    "IMPACT": row.get("IMPACT", None),
                    "IMPACT score": row.get("IMPACT score", None),
                    "ClinVar CLNDN": row.get("ClinVar CLNDN", None),
                    "Clinical consequence": row.get("Clinical consequence", None),
                    "clin sig": row.get("ClinVar CLNSIG", None),
                    "Variant type": row.get("Variant type", None)
                }

                json_object = {key: (None if pd.isna(value) or value == np.nan else value) for key, value in json_object.items()}
                patient_data["conditions"].append(json_object)

        return patient_data

    except Exception as e:
        return {"error": str(e)}
