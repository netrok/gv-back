# backend/back_gv/settings/base.py
from pathlib import Path
import environ
from datetime import timedelta

# =========================
# Paths & .env
# =========================
# Este archivo está en: backend/back_gv/settings/base.py
# BASE_DIR -> carpeta "backend/"
BASE_DIR = Path(__file__).resolve().parents[2]

# Inicializa django-environ
env = environ.Env(DEBUG=(bool, True))

# Intentar leer .env en dos ubicaciones:
# 1) Un nivel ARRIBA de "backend/" => D:\...\gv-back\.env
# 2) Dentro de "backend/"          => D:\...\gv-back\backend\.env
_env_candidates = [
    BASE_DIR.parent / ".env",
    BASE_DIR / ".env",
]
for _p in _env_candidates:
    if _p.exists():
        environ.Env.read_env(str(_p))
        break
# Si no existe .env en ninguna, los env() usarán defaults
# (también puedes definir vars en el entorno del sistema)

# =========================
# Core
# =========================
SECRET_KEY = env("SECRET_KEY", default="django-insecure-change-me")
DEBUG = env.bool("DEBUG", default=True)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
)
# Nota: la env var se llama CORS_ORIGINS, la setting es CORS_ALLOWED_ORIGINS
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ORIGINS",
    default=["http://localhost:5173", "http://127.0.0.1:5173"],
)
CORS_ALLOW_CREDENTIALS = True

INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # 3rd party
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "drf_spectacular",
    "simple_history",
    "django_filters",  # usado en DEFAULT_FILTER_BACKENDS

    # Apps propias
    "core",
    "cuentas",
    "catalogos",
    "organigrama",
    "empleados",
    "auditoria",
    "reportes",
    "configuracion",
    "notificaciones",
    "asistencia",
    "vacaciones",
    "permisos",
    "calendario",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # Debe ir arriba de CommonMiddleware
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
]

ROOT_URLCONF = "back_gv.urls"
WSGI_APPLICATION = "back_gv.wsgi.application"
ASGI_APPLICATION = "back_gv.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

# =========================
# Base de datos
# =========================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST", default="127.0.0.1"),
        "PORT": env("DB_PORT", default="5432"),
    }
}

# =========================
# Localización
# =========================
LANGUAGE_CODE = "es-mx"
TIME_ZONE = "America/Mexico_City"
USE_I18N = True
USE_TZ = True

# =========================
# Archivos estáticos y media
# =========================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR.parent / "staticfiles"  # útil para collectstatic en despliegues

MEDIA_URL = "/media/"
# MEDIA_ROOT fuera de backend/ para mantener portabilidad
MEDIA_ROOT = (BASE_DIR.parent / env("UPLOADS_DIR", default="media")).resolve()

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =========================
# DRF
# =========================
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PAGINATION_CLASS": "core.pagination.DefaultPageNumberPagination",
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
        "rest_framework.filters.SearchFilter",
    ],
    "PAGE_SIZE": 25,
}

# =========================
# OpenAPI / Swagger (drf-spectacular)
# =========================
SPECTACULAR_SETTINGS = {
    "TITLE": "GV RH API",
    "DESCRIPTION": "API de Recursos Humanos",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,

    # 👇 Orden manual de grupos (tags)
    "TAGS": [
        {"name": "auth",          "description": "Autenticación y perfil (tokens, me, permisos)"},
        {"name": "cuentas",       "description": "Cuentas de usuario y permisos del sistema"},
        {"name": "catalogos",     "description": "Catálogos (bancos, estados, turnos, etc.)"},
        {"name": "organigrama",   "description": "Estructura: unidades, sucursales, áreas, ubicaciones"},
        {"name": "empleados",     "description": "Gestión de empleados"},
        {"name": "asistencia",    "description": "Checadas, justificaciones, resúmenes"},
        {"name": "permisos",      "description": "Permisos con/sin goce, flujos de aprobación"},
        {"name": "vacaciones",    "description": "Políticas, feriados, saldos y solicitudes"},
        {"name": "calendario",    "description": "Calendario de ausencias"},
        {"name": "reportes",      "description": "Reportes y consultas"},
        {"name": "configuracion", "description": "Parámetros y configuración del sistema"},
        {"name": "notificaciones","description": "Notificaciones y avisos"},
        {"name": "auditoria",     "description": "Auditoría y trazabilidad"},
        {"name": "health",        "description": "Healthchecks"},
    ],

    # 👇 UI Swagger
    "SWAGGER_UI_SETTINGS": {
        "filter": True,                 # cuadro de búsqueda por operación
        "docExpansion": "list",         # colapsado por tag
        "defaultModelsExpandDepth": 0,  # oculta modelos por defecto
        "operationsSorter": "alpha",    # orden alfabético de operaciones dentro del tag
        "tagsSorter": "manual",         # respeta el orden definido en TAGS
    },

    # Hooks y enums
    "POSTPROCESSING_HOOKS": [
        "drf_spectacular.hooks.postprocess_schema_enums",
    ],
    "ENUM_NAME_OVERRIDES": {
        "EstadoSolicitudEnum": "core.enums.EstadoSolicitud",
        "TipoChecadaEnum": "core.enums.TipoChecada",
    },
}

# =========================
# JWT
# =========================
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env.int("ACCESS_TOKEN_LIFETIME_MIN", 60)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.int("REFRESH_TOKEN_LIFETIME_DAYS", 7)),
    "AUTH_HEADER_TYPES": ("Bearer",),
}
