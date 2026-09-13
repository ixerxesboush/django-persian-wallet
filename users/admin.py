from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, LoginHistory


admin.site.register(CustomUser, UserAdmin)
admin.site.register(LoginHistory)
