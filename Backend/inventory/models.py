from django.db import models

class Category(models.Model):
  name = models.CharField(max_length=100, unique=True)
  def __str__(self): return self.name

class Product(models.Model):
  name = models.CharField(max_length=200)
  price = models.DecimalField(max_digits=6, decimal_places=2)
  description = models.TextField()
  category = models.ForeignKey(Category, on_delete=models.CASCADE)
  quantity = models.IntegerField(default=0)
  image = models.ImageField(upload_to='products/')
  def __str__(self): return self.name