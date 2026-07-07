from django.test import TestCase
from django.contrib.auth.hashers import make_password, check_password
from bson import ObjectId
from config.db_connection import db
from datetime import datetime

class ExpenseTrackerTestCase(TestCase):

    def setUp(self):
        # Clean all test database collections before test runs
        db.users.delete_many({})
        db.categories.delete_many({})
        db.income.delete_many({})
        db.expenses.delete_many({})

    def tearDown(self):
        # Clean all test database collections after test runs
        db.users.delete_many({})
        db.categories.delete_many({})
        db.income.delete_many({})
        db.expenses.delete_many({})

    def test_password_hashing(self):
        # Verify password hashing security works
        raw_password = "mySecretPassword123"
        hashed = make_password(raw_password)
        
        self.assertNotEqual(raw_password, hashed)
        self.assertTrue(check_password(raw_password, hashed))
        self.assertFalse(check_password("wrongPassword", hashed))

    def test_category_creation_and_retrieval(self):
        # Test category document insert and find operations
        user_id = ObjectId()
        category = {
            'user_id': user_id,
            'name': 'Groceries',
            'type': 'expense',
            'color': '#ff0000'
        }
        
        db.categories.insert_one(category)
        
        retrieved = db.categories.find_one({'user_id': user_id})
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved['name'], 'Groceries')
        self.assertEqual(retrieved['type'], 'expense')

    def test_aggregation_calculations(self):
        # Test aggregation pipeline returns expected sums
        user_id = ObjectId()
        
        incomes = [
            {'user_id': user_id, 'amount': 1500.0, 'date': datetime.utcnow()},
            {'user_id': user_id, 'amount': 500.0, 'date': datetime.utcnow()}
        ]
        expenses = [
            {'user_id': user_id, 'amount': 250.0, 'date': datetime.utcnow()},
            {'user_id': user_id, 'amount': 150.0, 'date': datetime.utcnow()}
        ]
        
        db.income.insert_many(incomes)
        db.expenses.insert_many(expenses)
        
        inc_pipeline = [
            {'$match': {'user_id': user_id}},
            {'$group': {'_id': None, 'total': {'$sum': '$amount'}}}
        ]
        income_res = list(db.income.aggregate(inc_pipeline))
        total_income = income_res[0]['total'] if income_res else 0.0
        
        exp_pipeline = [
            {'$match': {'user_id': user_id}},
            {'$group': {'_id': None, 'total': {'$sum': '$amount'}}}
        ]
        expense_res = list(db.expenses.aggregate(exp_pipeline))
        total_expense = expense_res[0]['total'] if expense_res else 0.0
        
        self.assertEqual(total_income, 2000.0)
        self.assertEqual(total_expense, 400.0)
        self.assertEqual(total_income - total_expense, 1600.0)
