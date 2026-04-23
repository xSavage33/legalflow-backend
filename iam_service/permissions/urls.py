from django.urls import path
from . import views

urlpatterns = [
    # Role management
    path('roles/', views.RoleListCreateView.as_view(), name='role_list_create'),
    path('roles/<uuid:id>/', views.RoleDetailView.as_view(), name='role_detail'),

    # Permission management
    path('permissions/', views.PermissionListView.as_view(), name='permission_list'),
    path('permissions/create/', views.PermissionCreateView.as_view(), name='permission_create'),

    # Permission checking (for other microservices)
    path('check-permission/', views.CheckPermissionView.as_view(), name='check_permission'),

    # Object-level permissions
    path('grant/', views.GrantObjectPermissionView.as_view(), name='grant_permission'),
    path('revoke/', views.RevokeObjectPermissionView.as_view(), name='revoke_permission'),

    # Permission queries
    path('user/<uuid:user_id>/permissions/', views.UserPermissionsView.as_view(), name='user_permissions'),
    path('object/<str:object_type>/<uuid:object_id>/permissions/', views.ObjectPermissionsView.as_view(), name='object_permissions'),
]
