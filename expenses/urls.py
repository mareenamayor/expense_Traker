from django.urls import path
from . import views

urlpatterns = [
    # Category CRUD Routes
    path('categories/', views.category_list_view, name='category_list'),
    path('categories/create/', views.category_create_view, name='category_create'),
    path('categories/update/<str:category_id>/', views.category_update_view, name='category_update'),
    path('categories/delete/<str:category_id>/', views.category_delete_view, name='category_delete'),

    # Income CRUD Routes
    path('income/', views.income_list_view, name='income_list'),
    path('income/add/', views.income_create_view, name='income_create'),
    path('income/edit/<str:income_id>/', views.income_update_view, name='income_update'),
    path('income/delete/<str:income_id>/', views.income_delete_view, name='income_delete'),

    # Expense CRUD Routes
    path('expenses/', views.expense_list_view, name='expense_list'),
    path('expenses/add/', views.expense_create_view, name='expense_create'),
    path('expenses/edit/<str:expense_id>/', views.expense_update_view, name='expense_update'),
    path('expenses/delete/<str:expense_id>/', views.expense_delete_view, name='expense_delete'),
]
