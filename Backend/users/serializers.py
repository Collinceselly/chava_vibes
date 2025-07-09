from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
  password = serializers.CharField(write_only=True)

  class Meta:
    model = User
    fields = '__all__'

  
  def create(self, validate_data):
    user = User.objects.create_user(
      username=validate_data['username'],
      email=validate_data['email'],
      password=validate_data['password'],
      is_staff=validate_data.get('is_staff', False),
      is_superuser=validate_data.get('is_superuser', False),
      phone_number=validate_data.get('phone_number', '')
    )
    return User