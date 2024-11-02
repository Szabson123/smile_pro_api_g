from django.urls import path
from .views import ProfileListView
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from user_profile.views import EmployeeProfileViewSet

router = DefaultRouter()
router.register(r'employees', EmployeeProfileViewSet, basename='employee')

urlpatterns = [
    path('', include(router.urls)),
    path('list-profiles', ProfileListView.as_view(), name='profile_list'),
]