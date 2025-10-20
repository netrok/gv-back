from django.http import JsonResponse
from django.conf import settings

def version(request):
    return JsonResponse({
        "version": getattr(settings, "GIT_SHA", "dev"),
        "debug": settings.DEBUG,
    })
