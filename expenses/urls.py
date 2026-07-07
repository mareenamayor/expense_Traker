from django.urls import path
from . import views

urlpatterns = [
    # Category CRUD Routes
    path('categories/', views.category_list_view, name='category_list'),
    path('categories/create/', views.category_create_view, name='category_create'),
    path('categories/update/<str:category_id>/', views.category_update_view, name='category_update'),
    path('categories/delete/<str:category_id>/', views.category_delete_view, name='category_delete'),
]
