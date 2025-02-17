from restframework import serializer
from .models import Branch


class BranchSerializer(serializer.ModelSerializer):
    class Meta:
        fields = ['owner', 'name']

