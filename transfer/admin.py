from django.contrib import admin
from .models import EncryptedImage, Profile
# Register your models here.

admin.site.register(EncryptedImage)
admin.site.register(Profile)