import pymongo
from django.conf import settings

# Initialize the MongoDB client.
# settings.MONGO_URI is loaded from Django settings, which reads from the .env file.
client = pymongo.MongoClient(settings.MONGO_URI)

try:
    # client.get_default_database() automatically extracts the database name from the MONGO_URI string.
    # E.g., from "mongodb://localhost:27017/expense_tracker_db", it extracts "expense_tracker_db".
    db = client.get_default_database()
except Exception:
    # Fallback if the connection URI doesn't specify a database name path.
    db = client['expense_tracker_db']
