# backend/core/enums.py
from django.db.models import TextChoices

# Checadas (asistencia)
class TipoChecada(TextChoices):
    IN = "IN", "Entrada"
    OUT = "OUT", "Salida"

# Estados genéricos de solicitudes (vacaciones / permisos / justificaciones)
class EstadoSolicitud(TextChoices):
    PEND = "PEND", "Pendiente"
    APROB = "APROB", "Aprobada"
    RECH = "RECH", "Rechazada"
    CANC = "CANC", "Cancelada"

# Calendario (ausencias combinadas)
class TipoAusencia(TextChoices):
    VAC = "VAC", "Vacaciones"
    PERM = "PERM", "Permiso"

__all__ = ["TipoChecada", "EstadoSolicitud", "TipoAusencia"]
