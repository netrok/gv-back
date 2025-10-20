from datetime import date, datetime
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.timezone import make_aware

from empleados.models import Empleado
from vacaciones.models import PoliticaVacaciones, BalanceVacaciones, SolicitudVacaciones


def _antiguedad_anios(empleado: Empleado, anio: int) -> int:
    """
    Antigüedad en años al 1 de enero del año 'anio'.
    Usamos fecha_antiguedad si existe; si no, fecha_alta.
    """
    base = empleado.fecha_antiguedad or empleado.fecha_alta
    if not base:
        return 0
    corte = date(anio, 1, 1)
    if base > corte:
        return 0
    return corte.year - base.year - ((corte.month, corte.day) < (base.month, base.day))


def _politica_para_anios(anios: int) -> PoliticaVacaciones | None:
    return (
        PoliticaVacaciones.objects
        .filter(activo=True, anios_desde__lte=anios, anios_hasta__gte=anios)
        .order_by("anios_desde")
        .first()
    )


def _dias_tomados_en_anio(empleado_id: int, anio: int) -> Decimal:
    """
    Suma los días aprobados dentro del año calendario.
    Considera solicitudes con estado APROB cuyo rango se traslape con el año.
    """
    desde = date(anio, 1, 1)
    hasta = date(anio, 12, 31)
    qs = SolicitudVacaciones.objects.filter(
        empleado_id=empleado_id,
        estado="APROB",
        fecha_inicio__lte=hasta,
        fecha_fin__gte=desde,
    )
    total = Decimal("0.00")
    for s in qs:
        total += Decimal(s.dias or 0)
    return total


class Command(BaseCommand):
    help = "Recalcula BalanceVacaciones para el año indicado (por defecto, el año actual)."

    def add_arguments(self, parser):
        parser.add_argument("--year", type=int, help="Año a recalcular (ej. 2025). Por defecto: año actual.")
        parser.add_argument("--empleado", type=int, help="ID de empleado a recalcular (opcional).")
        parser.add_argument("--solo-activos", action="store_true", help="Solo empleados estatus=A (activo).")
        parser.add_argument("--dry-run", action="store_true", help="Muestra resultados sin guardar cambios.")

    @transaction.atomic
    def handle(self, *args, **opts):
        anio = opts.get("year") or date.today().year
        empleado_id = opts.get("empleado")
        solo_activos = bool(opts.get("solo_activos"))
        dry = bool(opts.get("dry_run"))

        self.stdout.write(self.style.NOTICE(f"Recalculando balances de vacaciones para {anio}"))
        empleados = Empleado.objects.all()
        if solo_activos:
            empleados = empleados.filter(estatus="A")
        if empleado_id:
            empleados = empleados.filter(id=empleado_id)

        total = empleados.count()
        if total == 0:
            self.stdout.write(self.style.WARNING("No hay empleados que coincidan con el criterio."))
            return

        actualizados = 0
        for emp in empleados.iterator():
            anios = _antiguedad_anios(emp, anio)
            pol = _politica_para_anios(anios)
            dias_asignados = Decimal(pol.dias if pol else 0)

            # Arrastre desde el año anterior
            arrastre = Decimal("0.00")
            if pol:
                prev = BalanceVacaciones.objects.filter(empleado=emp, anio=anio - 1).first()
                if prev:
                    arrastre = min(Decimal(pol.arrastre_maximo), max(Decimal("0.00"), prev.dias_disponibles))

            dias_tomados = _dias_tomados_en_anio(emp.id, anio)
            dias_disponibles = dias_asignados + arrastre - dias_tomados
            if dias_disponibles < 0:
                dias_disponibles = Decimal("0.00")

            # Caducidad: por simplicidad, el 31/dic del año
            caduca_el = date(anio, 12, 31)

            if dry:
                self.stdout.write(
                    f"- {emp.id} {emp.numero_empleado} {emp.nombre_completo} | antig {anios}a | "
                    f"asign:{dias_asignados} arr:{arrastre} tom:{dias_tomados} disp:{dias_disponibles}"
                )
                continue

            bal, _ = BalanceVacaciones.objects.get_or_create(empleado=emp, anio=anio)
            bal.dias_asignados = dias_asignados
            bal.dias_arrastrados = arrastre
            bal.dias_tomados = dias_tomados
            bal.dias_disponibles = dias_disponibles
            bal.caduca_el = caduca_el
            bal.save()
            actualizados += 1

        if dry:
            self.stdout.write(self.style.SUCCESS("Dry-run completado. No se guardaron cambios."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Balances actualizados: {actualizados}/{total}"))
