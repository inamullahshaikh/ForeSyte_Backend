from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DB_URL")
DB_NAME = os.getenv("DB_NAME")

client = MongoClient(DB_URL)
db = client[DB_NAME]

users_collection = db["users"]
admins_collection = db["admins"]
