from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PatientViewSet, TreatmentList, TreatmentViewSet, TreatmentPlanViewSet, PlanTreatmentCreateView

router = DefaultRouter()
router.register(r'patient', PatientViewSet, basename='patients')
router.register(r'treatment', TreatmentViewSet, basename='treatment')
router.register(r'treatment-plan', TreatmentPlanViewSet, basename='treatment_plan')

urlpatterns = [
    path('', include(router.urls)),
    path('treatment-list/', TreatmentList.as_view(), name='treatment-list'),
    path('treatment-plan-element/<int:plan_id>/', PlanTreatmentCreateView.as_view(), name='treatment-create'),

]