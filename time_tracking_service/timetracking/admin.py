from django.contrib import admin
from .models import TimeEntry, Timer, UserRate, CaseRate


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ['user_name', 'date', 'duration_minutes', 'case_number', 'status', 'is_billable', 'amount']
    list_filter = ['status', 'is_billable', 'activity_type', 'date']
    search_fields = ['user_name', 'case_number', 'description']
    readonly_fields = ['id', 'amount', 'created_at', 'updated_at']
    ordering = ['-date', '-created_at']


@admin.register(Timer)
class TimerAdmin(admin.ModelAdmin):
    list_display = ['user_name', 'is_running', 'case_number', 'start_time', 'accumulated_seconds']
    list_filter = ['is_running']
    search_fields = ['user_name', 'case_number']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(UserRate)
class UserRateAdmin(admin.ModelAdmin):
    list_display = ['user_id', 'default_rate', 'currency', 'effective_date']
    search_fields = ['user_id']


@admin.register(CaseRate)
class CaseRateAdmin(admin.ModelAdmin):
    list_display = ['case_id', 'user_id', 'rate', 'currency']
    search_fields = ['case_id']
