from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InstitutionViewSet

router = DefaultRouter()
router.register('institution', InstitutionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]