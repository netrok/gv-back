# backend/asistencia/utils.py
from __future__ import annotations

from typing import Optional, Tuple, Union, TYPE_CHECKING
from decimal import Decimal
from math import radians, sin, cos, asin, sqrt

if TYPE_CHECKING:
    # Solo para tipado, evita import real (y ciclos) en tiempo de ejecución
    from organigrama.models import Ubicacion

Number = Union[float, int, Decimal, None]


def _to_float(x: Number) -> Optional[float]:
    """Convierte a float seguro; None o excepción -> None."""
    if x is None:
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def haversine_m(lat1: Number, lon1: Number, lat2: Number, lon2: Number) -> Optional[int]:
    """
    Distancia aproximada en metros entre dos puntos (lat, lon) usando Haversine.
    Devuelve None si algún valor no es convertible a float.
    """
    lat1f, lon1f, lat2f, lon2f = map(_to_float, (lat1, lon1, lat2, lon2))
    if None in (lat1f, lon1f, lat2f, lon2f):
        return None

    R = 6371000.0  # radio terrestre en metros
    dlat = radians(lat2f - lat1f)
    dlon = radians(lon2f - lon1f)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1f)) * cos(radians(lat2f)) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return int(round(R * c))


def evaluar_geocerca(
    lat: Number,
    lon: Number,
    ubicacion: "Ubicacion | None",
) -> Tuple[Optional[int], bool]:
    """
    Calcula (distancia_m, dentro_geocerca).
    - lat/lon: Decimal|float|int|None (coordenadas reportadas).
    - ubicacion: instancia con .lat, .lon, .radio_m; puede ser None.
    Reglas:
      * Si falta ubicacion o coordenadas -> (None, False)
      * radio_m <= 0 se considera 0 (nunca dentro)
    """
    if not ubicacion or lat is None or lon is None:
        return (None, False)

    dist = haversine_m(lat, lon, getattr(ubicacion, "lat", None), getattr(ubicacion, "lon", None))
    if dist is None:
        return (None, False)

    try:
        radio = int(getattr(ubicacion, "radio_m", 0) or 0)
    except (TypeError, ValueError):
        radio = 0

    return (dist, dist <= max(radio, 0))
