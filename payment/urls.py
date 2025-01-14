from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ObligationViewSet, DepositViewSet, UserHistoryApiView

router = DefaultRouter()
router.register(r'(?P<patient_id>\d+)/obligation', ObligationViewSet, basename='obligation')
router.register(r'(?P<patient_id>\d+)/deposit', DepositViewSet, basename='deposit')

urlpatterns = [
    path('', include(router.urls)),
    path('patient_payment_history/<int:patient_id>/', UserHistoryApiView.as_view(), name='user-history-api-view'),
]