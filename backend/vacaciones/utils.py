from datetime import date, timedelta
from .models import Feriado

def dias_habiles(inicio: date, fin: date) -> int:
    if not inicio or not fin or fin < inicio:
        return 0
    total = 0
    feriados = set(Feriado.objects.filter(fecha__gte=inicio, fecha__lte=fin).values_list("fecha", flat=True))
    d = inicio
    while d <= fin:
        if d.weekday() < 5 and d not in feriados:  # 0-4 = lun-vie
            total += 1
        d += timedelta(days=1)
    return total
