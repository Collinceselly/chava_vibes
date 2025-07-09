from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
  phone_number = models.CharField(max_length=15, blank=True, null=True)

  def get_role(self):
    if self.is_superuser:
      return 'admin'
    elif self.is_staff:
      return 'staff'
    return 'guest'
  
