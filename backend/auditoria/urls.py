# backend/auditoria/urls.py
from django.urls import path
from .views import HealthView, PingView

urlpatterns = [
    path("health/", HealthView.as_view(), name="auditoria-health"),
    path("ping/",   PingView.as_view(),   name="auditoria-ping"),
]
