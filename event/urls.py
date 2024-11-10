from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventViewSet, TimeSlotView, AbsenceViewSet, DoctorScheduleViewSet, OfficeViewSet, VisitTypeViewSet, TagsViewSet

router = DefaultRouter()
router.register(r'events', EventViewSet, basename='events')
router.register(r'absence', AbsenceViewSet, basename='absence')
router.register(r'doctor_schedule', DoctorScheduleViewSet, basename='doctor_schedule')
router.register(r'office', OfficeViewSet, basename='office')
router.register(r'tags', TagsViewSet, basename='tags')
router.register(r'viewset', VisitTypeViewSet, basename='visittype')

urlpatterns = [
    path('', include(router.urls)),
    path('time-slots/', TimeSlotView.as_view(), name='time-slots'),
]