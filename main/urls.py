from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('user_dashboard/', views.user_dashboard, name='user_dashboard'),
    path('create_request/', views.create_request, name='create_request'),
    path('delete_request/<int:request_id>/', views.delete_request, name='delete_request'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('change_status/<int:request_id>/', views.change_status, name='change_status'),
    path('manage_categories/', views.manage_categories, name='manage_categories'),
]