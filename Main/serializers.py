from dataclasses import field
import imp
from rest_framework.serializers import ModelSerializer
from .models import Profile

class ProfileSerializer(ModelSerializer):
    class Meta:
        model = Profile
        fields = ['title']
