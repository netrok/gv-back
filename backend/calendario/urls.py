from django.urls import path
from .views import CalendarioAusenciasView

urlpatterns = [
    path("ausencias/", CalendarioAusenciasView.as_view(), name="calendario-ausencias"),
]
