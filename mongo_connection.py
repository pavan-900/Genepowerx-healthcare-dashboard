from pymongo import MongoClient
import gridfs

# ✅ MongoDB Atlas Connection
client = MongoClient("mongodb+srv://pavanshankar9000:pavan%409000@project1.gfku5.mongodb.net/?retryWrites=true&w=majority")
db = client["Finish_db"]
fs = gridfs.GridFS(db)
