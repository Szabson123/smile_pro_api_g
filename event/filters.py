from django_filters import rest_framework as filters
from .models import Event

class EventFilter(filters.FilterSet):
    date_start = filters.DateFilter(field_name="date", lookup_expr="gte")
    date_end = filters.DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = Event
        fields = ['doctor', 'office', 'patient', 'date']