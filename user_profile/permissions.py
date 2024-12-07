from rest_framework import permissions
from user_profile.models import ProfileCentralUser
from branch.models import Branch

class HasProfilePermission(permissions.BasePermission):
    message = "User doesn't have a profile in this Branch."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        branch_uuid = view.kwargs.get('branch_uuid')
        if not branch_uuid:
            return False

        return ProfileCentralUser.objects.filter(user=request.user, branch__identyficator=branch_uuid).exists()
    

class IsOwnerOfInstitution(permissions.BasePermission):
    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated:
            return False

        branch_uuid = view.kwargs.get('branch_uuid')
        if not branch_uuid:
            return False

        try:
            profile = ProfileCentralUser.objects.get(user=user)

            branch = Branch.objects.get(identyficator=branch_uuid)

            if branch.owner == profile:
                return True

            return False

        except (ProfileCentralUser.DoesNotExist, Branch.DoesNotExist):
            return False
        
    
        
        