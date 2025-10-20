# backend/calendario/models.py
from django.db import models
from vacaciones.models import Feriado as VacacionesFeriado

class Feriado(VacacionesFeriado):
    """
    Proxy del feriado definido en vacaciones.models.Feriado.
    Permite exponerlo/administrarlo desde la app 'calendario' sin duplicar tablas.
    """
    class Meta:
        proxy = True
        ordering = ["fecha"]
        verbose_name = "Feriado"
        verbose_name_plural = "Feriados"

    def __str__(self):
        return f"{self.fecha} - {self.nombre}"
