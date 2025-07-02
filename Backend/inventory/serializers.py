from rest_framework import serializers
from .models import Product
from django.urls import reverse


class ProductSerializer(serializers.ModelSerializer):
  image_url = serializers.SerializerMethodField()
  
  class Meta:
    model = Product
    fields = "__all__"
    read_only_fields = ['id','image_url']

  def get_image_url(self, obj):
    if obj.image and hasattr(obj.image, 'url'):
      request = self.context.get('request')
      return request.build_absolute_uri(obj.image.url) if request else obj.image.url
    return None
  
  def update(self, instance, validated_data):
    # Handle image update optionally

    image = validated_data.pop('image', None)
    if image is not None:
      instance.image = image
    instance.name = validated_data.get('name', instance.name)
    instance.price = validated_data.get('price', instance.price)
    instance.description = validated_data.get('description', instance.description)
    instance.category_id = validated_data.get('category', instance.category_id)
    instance.quantity = validated_data.get('quantity', instance.quantity)
    instance.save()
    return instance