from django.contrib import admin
from .models import DailyMetrics, CachedReport


@admin.register(DailyMetrics)
class DailyMetricsAdmin(admin.ModelAdmin):
    list_display = ['date', 'metric_type', 'value', 'created_at']
    list_filter = ['metric_type', 'date']


@admin.register(CachedReport)
class CachedReportAdmin(admin.ModelAdmin):
    list_display = ['report_type', 'generated_at', 'expires_at']
    list_filter = ['report_type']
