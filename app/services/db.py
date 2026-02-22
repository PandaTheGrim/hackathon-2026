from pymongo import MongoClient
from pymongo.collection import Collection
import os

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "checker")

client = MongoClient(MONGO_URL)
db = client[DB_NAME]

results_collection: Collection = db["results"]
tasks_collection: Collection = db["tasks"]
prompts_collection: Collection = db["prompts"]