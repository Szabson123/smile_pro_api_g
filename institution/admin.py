from django.contrib import admin
from .models import Institution
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

admin.site.register(Institution)

