import factory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from empleados.models import Empleado
from organigrama.models import Ubicacion
from asistencia.models import Checada

User = get_user_model()


# =======================
# Users
# =======================
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    is_active = True
    is_staff = False
    is_superuser = False

    # Password hasheado por defecto (para login JWT)
    raw_password = "pass123"

    @factory.post_generation
    def set_password(obj, create, extracted, **kwargs):
        pwd = extracted or getattr(obj, "raw_password", "pass123")
        obj.set_password(pwd)
        if create:
            obj.save(update_fields=["password"])

    # Permite pasar groups=[...] explícitamente
    @factory.post_generation
    def groups(obj, create, extracted, **kwargs):
        if not create or not extracted:
            return
        for g in extracted:
            obj.groups.add(g)

    class Params:
        rrhh = factory.Trait(
            groups=factory.LazyFunction(lambda: [Group.objects.get_or_create(name="RRHH")[0]])
        )
        admin = factory.Trait(
            groups=factory.LazyFunction(lambda: [Group.objects.get_or_create(name="Admin")[0]])
        )
        supervisor = factory.Trait(
            groups=factory.LazyFunction(lambda: [Group.objects.get_or_create(name="Supervisor")[0]])
        )
        gerente = factory.Trait(
            groups=factory.LazyFunction(lambda: [Group.objects.get_or_create(name="Gerente")[0]])
        )
        superadmin = factory.Trait(
            is_superuser=True,
            is_staff=True,
        )


# =======================
# Empleados
# =======================
class EmpleadoFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Empleado

    # Campos OBLIGATORIOS de tu modelo
    numero_empleado = factory.Sequence(lambda n: f"{n:06d}")
    primer_nombre = "Juan"
    segundo_nombre = ""
    apellido_paterno = "Pérez"
    apellido_materno = ""

    # Documentos obligatorios y únicos
    curp = factory.Sequence(lambda n: f"CUPR900101HDFSRN{n%10}")   # 18 chars aprox
    rfc  = factory.Sequence(lambda n: f"XAXX010101{n:03d}")        # 12-13 chars
    nss  = factory.Sequence(lambda n: f"{97000000000 + n:011d}")   # 11 dígitos

    # Estado laboral mínimo
    estatus = "A"  # Activo

    # Opcionales comunes
    email_personal = factory.LazyAttribute(lambda o: f"{o.numero_empleado}@example.com")


# =======================
# Organigrama
# =======================
class UbicacionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Ubicacion

    nombre = factory.Sequence(lambda n: f"Ubicación {n}")
    lat = 20.666000
    lon = -103.350000
    radio_m = 150


# =======================
# Asistencia
# =======================
class ChecadaFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Checada

    empleado = factory.SubFactory(EmpleadoFactory)
    tipo = "IN"          # IN/OUT (core.enums.TipoChecada)
    fuente = "WEB"       # MOBILE/WEB/KIOSK/OTHER
    ubicacion = None

    # Datos opcionales
    nota = factory.Faker("sentence", nb_words=4)
    dentro_geocerca = False
    distancia_m = None
    # lat = 20.666
    # lon = -103.350
