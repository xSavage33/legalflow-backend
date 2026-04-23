from django.contrib import admin
from .models import Role, Permission, RolePermission, ObjectPermission


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_system', 'created_at']
    list_filter = ['is_system']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['codename', 'name', 'content_type', 'created_at']
    list_filter = ['content_type']
    search_fields = ['codename', 'name']
    readonly_fields = ['created_at']


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ['role', 'permission', 'created_at']
    list_filter = ['role']
    search_fields = ['role__name', 'permission__codename']
    readonly_fields = ['created_at']


@admin.register(ObjectPermission)
class ObjectPermissionAdmin(admin.ModelAdmin):
    list_display = ['user_id', 'permission', 'object_type', 'object_id', 'created_at']
    list_filter = ['object_type', 'permission']
    search_fields = ['user_id', 'object_id']
    readonly_fields = ['created_at']
