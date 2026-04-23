from django.contrib import admin
from .models import Case, CaseParty, CaseDate, CaseNote, CaseTask


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ['case_number', 'title', 'case_type', 'status', 'client_name', 'opened_date']
    list_filter = ['status', 'case_type', 'priority', 'billing_type']
    search_fields = ['case_number', 'title', 'client_name']
    readonly_fields = ['case_number', 'created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(CaseParty)
class CasePartyAdmin(admin.ModelAdmin):
    list_display = ['name', 'party_type', 'case', 'email']
    list_filter = ['party_type']
    search_fields = ['name', 'email', 'case__case_number']


@admin.register(CaseDate)
class CaseDateAdmin(admin.ModelAdmin):
    list_display = ['title', 'date_type', 'case', 'date', 'is_completed']
    list_filter = ['date_type', 'is_completed']
    search_fields = ['title', 'case__case_number']


@admin.register(CaseNote)
class CaseNoteAdmin(admin.ModelAdmin):
    list_display = ['case', 'author_name', 'is_private', 'created_at']
    list_filter = ['is_private', 'created_at']
    search_fields = ['case__case_number', 'content']


@admin.register(CaseTask)
class CaseTaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'case', 'status', 'priority', 'due_date', 'assigned_to_name']
    list_filter = ['status', 'priority']
    search_fields = ['title', 'case__case_number']
