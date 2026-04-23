import django_filters
from .models import Case


class CaseFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Case.STATUS_CHOICES)
    case_type = django_filters.ChoiceFilter(choices=Case.CASE_TYPE_CHOICES)
    priority = django_filters.ChoiceFilter(choices=Case.PRIORITY_CHOICES)
    client_id = django_filters.UUIDFilter()
    lead_attorney_id = django_filters.UUIDFilter()
    opened_after = django_filters.DateFilter(field_name='opened_date', lookup_expr='gte')
    opened_before = django_filters.DateFilter(field_name='opened_date', lookup_expr='lte')
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = Case
        fields = [
            'status', 'case_type', 'priority', 'client_id',
            'lead_attorney_id', 'jurisdiction', 'billing_type'
        ]
