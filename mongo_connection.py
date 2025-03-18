from pymongo import MongoClient
import gridfs

# ✅ MongoDB Atlas Connection
client = MongoClient("mongodb+srv://pavanshankar:pavan%4096188@cluster0.mns8h.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["Finish_db"]
fs = gridfs.GridFS(db)
