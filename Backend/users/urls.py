from django.urls import path
from .views import UserCreateView, UserProfileView


urlpatterns = [
  path('create/', UserCreateView.as_view()),
  path('profile/', UserProfileView.as_view()),
]