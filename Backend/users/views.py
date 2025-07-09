from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from .serializers import UserSerializer
from rest_framework.permissions import IsAuthenticated

User = get_user_model()

class UserCreateView(APIView):
  def post(self, request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
      user = serializer.save()
      return Response({"message": "User created successfully", "id": user.id}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
  

class UserProfileView(APIView):
  permission_classes = [IsAuthenticated]

  def get(self, request):
    user = request.user
    role = user.get_role()
    profile_data = {
      'username':user.username,
      'email':user.email,
      'role':role,
      'phone_number': user.phone_number or '',
    }
    return Response(profile_data)
