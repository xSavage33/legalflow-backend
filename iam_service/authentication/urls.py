from django.urls import path
from . import views

urlpatterns = [
    # Public endpoints
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', views.TokenRefreshCustomView.as_view(), name='token_refresh'),

    # Protected endpoints
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('password/change/', views.PasswordChangeView.as_view(), name='password_change'),
    path('activities/', views.UserActivityListView.as_view(), name='user_activities'),

    # Admin endpoints
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/<uuid:id>/', views.UserDetailView.as_view(), name='user_detail'),

    # Service-to-service endpoint
    path('validate/', views.ValidateTokenView.as_view(), name='validate_token'),
]
