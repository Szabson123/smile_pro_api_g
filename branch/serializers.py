from restframework import serializer
from .models import Branch, BranchInfo
from user_profile.models import ProfileCentralUser
from django.forms.models import model_to_dict


class BranchInfoSerializer(serializer.ModelSerializer):
    class Meta:
        model = BranchInfo
        fields = ['bdo_number', 'regon', 'nip', 'v_register_code', 'town', 'address', 'post_code', 'bank', 'bank_acc']


class BranchSerializer(serializer.ModelSerializer):
    branch_info = BranchInfoSerializer()
    class Meta:
        fields = ['owner', 'name', 'branch_info']
        read_only_fields = ['owner']
        
    def create(self, validated_data):
        branch_info_data = validated_data.pop('branch_info')
        branch = Branch.objects.create(**validated_data)
        
        BranchInfo.objects.create(branch=branch, **branch_info_data)
        
        branch_uuid = self.context.get('view').kwargs.get('branch_uuid')
        
        request = self.context.get('request')
        user = request.user
                
        existing_profile = ProfileCentralUser.objects.get(user=user, branch__identyficator=branch_uuid)
        
        profile_data = model_to_dict(existing_profile)

        profile_data.pop('id', None)
        profile_data.pop('branch', None)
        
        profile_data['branch'] = branch
        profile_data['user'] = user
        ProfileCentralUser.objects.create(**profile_data)
        
        return branch
        

