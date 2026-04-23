from django.contrib import admin
from .models import ClientPreference, Message


@admin.register(ClientPreference)
class ClientPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user_id', 'email_notifications', 'language', 'created_at']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['subject', 'sender_name', 'recipient_name', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['subject', 'sender_name', 'recipient_name']
