from django.urls import path
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return JsonResponse({
        "service": "document_service",
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "database": db_status,
    })

urlpatterns = [
    path('', health_check, name='health_check'),
]
