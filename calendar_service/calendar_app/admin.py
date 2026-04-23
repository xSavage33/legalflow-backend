from django.contrib import admin
from .models import Event, Deadline, HolidayCalendar


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'event_type', 'status', 'start_datetime', 'case_number']
    list_filter = ['event_type', 'status']
    search_fields = ['title', 'case_number']


@admin.register(Deadline)
class DeadlineAdmin(admin.ModelAdmin):
    list_display = ['title', 'priority', 'status', 'due_date', 'case_number', 'assigned_to_name']
    list_filter = ['priority', 'status']
    search_fields = ['title', 'case_number']


@admin.register(HolidayCalendar)
class HolidayCalendarAdmin(admin.ModelAdmin):
    list_display = ['name', 'date', 'jurisdiction', 'is_national', 'year']
    list_filter = ['year', 'is_national', 'jurisdiction']
    search_fields = ['name']
