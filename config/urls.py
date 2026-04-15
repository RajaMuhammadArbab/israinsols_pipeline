"""
Israinsols Pipeline - URL Configuration
"""
from django.contrib import admin
from django.urls import path
from leads.views import freelancer_webhook

urlpatterns = [
    path('admin/', admin.site.urls),
]

urlpatterns = [
    # ... your existing paths ...
    path('api/webhook/freelancer/', freelancer_webhook, name='freelancer_webhook'),
]
