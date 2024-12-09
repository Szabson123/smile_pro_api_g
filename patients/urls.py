from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PatientViewSet, TreatmentList, TreatmentViewSet

router = DefaultRouter()
router.register(r'patient', PatientViewSet, basename='events')
router.register(r'treatment', TreatmentViewSet, basename='treatment')

urlpatterns = [
    path('', include(router.urls)),
    path('treatment-list/', TreatmentList.as_view(), name='treatment-list'),
]