from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventViewSet, TimeSlotView, AbsenceViewSet, DoctorScheduleViewSet, OfficeViewSet, VisitTypeViewSet, TagsViewSet, AvailableAssistantsView, CheckRepetitionEvents, EventCalendarViewSet, EventListView

router = DefaultRouter()
router.register(r'events', EventViewSet, basename='events')
router.register(r'absence', AbsenceViewSet, basename='absence')
router.register(r'doctor_schedule', DoctorScheduleViewSet, basename='doctor_schedule')
router.register(r'office', OfficeViewSet, basename='office')
router.register(r'tags', TagsViewSet, basename='tags')
router.register(r'visittype', VisitTypeViewSet, basename='visittype')
router.register(r'events-calendar', EventCalendarViewSet, basename='event-calendar')

urlpatterns = [
    path('', include(router.urls)),
    path('time-slots/', TimeSlotView.as_view(), name='time-slots'),
    path('available-assistants/', AvailableAssistantsView.as_view(), name='available-assistants'),
    path('check-repetition-events/', CheckRepetitionEvents.as_view(), name='check-repetition-events'),
    path('get_event_list/', EventListView.as_view(), name='get_event_list')
]