from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PatientViewSet, TreatmentList, TreatmentViewSet, TreatmentPlanViewSet, TreatmentInPlanCreateView, GeneratePatientsView

router = DefaultRouter()
router.register(r'patient', PatientViewSet, basename='patients')
router.register(r'(?P<patient_id>\d+)/treatment', TreatmentViewSet, basename='treatment')
router.register(r'(?P<patient_id>\d+)/treatment-plan', TreatmentPlanViewSet, basename='treatment_plan')

urlpatterns = [
    path('', include(router.urls)),
    path('/<int:patient_id>/treatment-list/', TreatmentList.as_view(), name='treatment-list'),
    path('treatment-plan-element/<int:plan_id>/', TreatmentInPlanCreateView.as_view(), name='treatment-create'),
    path('generate-patients/', GeneratePatientsView.as_view(), name='generate_patients'),

]