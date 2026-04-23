from django.contrib import admin
from .models import Document, DocumentVersion, DocumentAccessLog, DocumentShare, Folder


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'status', 'case_id', 'current_version', 'created_by_name', 'created_at']
    list_filter = ['category', 'status', 'is_confidential', 'is_privileged']
    search_fields = ['name', 'description', 'original_filename']
    readonly_fields = ['id', 'file_size', 'checksum', 'current_version', 'created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = ['document', 'version_number', 'file_size', 'created_by_name', 'created_at']
    list_filter = ['created_at']
    search_fields = ['document__name']
    readonly_fields = ['id', 'file_size', 'checksum', 'created_at']


@admin.register(DocumentAccessLog)
class DocumentAccessLogAdmin(admin.ModelAdmin):
    list_display = ['document', 'action', 'user_email', 'ip_address', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['document__name', 'user_email']
    readonly_fields = ['id', 'document', 'action', 'user_id', 'user_email', 'user_role', 'ip_address', 'user_agent', 'details', 'timestamp']
    ordering = ['-timestamp']


@admin.register(DocumentShare)
class DocumentShareAdmin(admin.ModelAdmin):
    list_display = ['document', 'shared_with_email', 'permission', 'shared_by_name', 'created_at']
    list_filter = ['permission', 'created_at']
    search_fields = ['document__name', 'shared_with_email']


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'case_id', 'created_at']
    search_fields = ['name']
    ordering = ['name']
