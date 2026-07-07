import sys
import pymongo
from django.conf import settings

# Connect to MongoDB using the URI from settings
client = pymongo.MongoClient(settings.MONGO_URI)

# Route to test database during testing
if 'test' in sys.argv:
    db = client['test_expense_tracker_db']
else:
    try:
        # Get the default database specified in the URI path
        db = client.get_default_database()
    except Exception:
        # Fallback if no database name is in the URI
        db = client['expense_tracker_db']
