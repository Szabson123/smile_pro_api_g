from rest_framework import permissions
from user_profile.models import ProfileCentralUser


class HasProfilePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        
        if not user.is_authenticated:
            return False
        
        profile_exists = ProfileCentralUser.objects.filter(user=user).exists()
        return profile_exists
    

class IsOwnerOfInstitution(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        
        if not user.is_authenticated:
            return False
        try:
            profile = ProfileCentralUser.objects.get(user=user)
            if profile and profile.owner:
                return True
            else:
                return False
            
        except ProfileCentralUser.DoesNotExist:
            return False
        
        
        