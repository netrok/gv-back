# core/workdays_sources.py
from calendario.models import Feriado

def feriados_en(desde, hasta):
    return list(Feriado.objects.filter(fecha__gte=desde, fecha__lte=hasta).values_list("fecha", flat=True))
