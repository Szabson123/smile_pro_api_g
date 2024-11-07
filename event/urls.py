from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventViewSet, TimeSlotView

router = DefaultRouter()
router.register(r'events', EventViewSet, basename='events')

urlpatterns = [
    path('', include(router.urls)),
    path('time-slots/', TimeSlotView.as_view(), name='time-slots'),
]