# core/workdays.py
from datetime import date, timedelta
from typing import Iterable

def _dow_bit_index(d: date) -> int:
    # domingo=0 … sábado=6
    return (d.weekday() + 1) % 7

def fechas_en_rango(desde: date, hasta: date):
    cur = desde
    while cur <= hasta:
        yield cur
        cur = cur + timedelta(days=1)

def dias_habiles_empleado(empleado, desde: date, hasta: date, feriados: Iterable[date] = ()):
    """
    Cuenta días hábiles en [desde, hasta] según el horario del empleado y excluye feriados.
    """
    mask = getattr(getattr(empleado, "horario", None), "dias_laborables_mask", 0b0111110)
    feriados_set = set(feriados)
    total = 0
    for f in fechas_en_rango(desde, hasta):
        if f in feriados_set:
            continue
        dow = _dow_bit_index(f)
        if mask & (1 << dow):
            total += 1
    return total
