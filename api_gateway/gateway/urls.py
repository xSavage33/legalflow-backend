"""
Configuracion de URLs para la aplicacion Gateway del API Gateway.

Este archivo define los patrones de URL que mapean las rutas HTTP a las
vistas proxy correspondientes. El API Gateway actua como punto de entrada
unico, enrutando las peticiones a los microservicios apropiados basandose
en el prefijo de la URL.

Arquitectura de enrutamiento:
    /api/health/      -> HealthCheckView (verificacion de salud)
    /api/auth/*       -> IAM Service (autenticacion)
    /api/iam/*        -> IAM Service (gestion de usuarios)
    /api/cases/*      -> Matter Service (casos)
    /api/tasks/*      -> Matter Service (tareas)
    /api/clients/*    -> Matter Service (clientes)
    /api/documents/*  -> Document Service (documentos)
    /api/folders/*    -> Document Service (carpetas)
    /api/time-entries/* -> Time Tracking Service
    /api/timers/*     -> Time Tracking Service
    /api/rates/*      -> Time Tracking Service
    /api/invoices/*   -> Billing Service
    /api/rate-agreements/* -> Billing Service
    /api/events/*     -> Calendar Service
    /api/deadlines/*  -> Calendar Service
    /api/holidays/*   -> Calendar Service
    /api/portal/*     -> Client Portal Service
    /api/analytics/*  -> Analytics Service

Nota:
    Las URLs usan re_path con expresiones regulares para capturar
    cualquier subruta despues del prefijo, permitiendo que el
    microservicio maneje rutas complejas como /cases/123/documents/

Autor: LegalFlow Team
"""

# Importacion de path para rutas simples y re_path para rutas con expresiones regulares
# path: Para URLs fijas como '/health/'
# re_path: Para URLs con patrones dinamicos usando regex
from django.urls import path, re_path

# Importacion del modulo views que contiene las vistas proxy
# El punto indica importacion relativa desde el mismo paquete
from . import views

# Lista de patrones de URL para el API Gateway
# Django procesa esta lista en orden, la primera coincidencia gana
urlpatterns = [
    # ==========================================================================
    # ENDPOINT DE SALUD
    # ==========================================================================

    # Endpoint de health check para monitoreo y balanceadores de carga
    # URL: /api/health/
    # Vista: HealthCheckView - Verifica estado del gateway y microservicios
    # No requiere autenticacion
    path('health/', views.HealthCheckView.as_view(), name='health'),

    # ==========================================================================
    # RUTAS DEL SERVICIO IAM (Identity and Access Management)
    # ==========================================================================

    # Rutas de autenticacion (login, logout, refresh token)
    # URL: /api/auth/* (captura cualquier subruta)
    # Patron regex: ^auth/(?P<path>.*)$ - Captura todo despues de 'auth/'
    # Vista: IAMProxyView - Proxy especial con manejo de rutas publicas
    # Ejemplos: /api/auth/login/, /api/auth/token/refresh/
    re_path(r'^auth/(?P<path>.*)$', views.IAMProxyView.as_view(), name='iam_auth_proxy'),

    # Rutas de gestion de usuarios, roles y permisos
    # URL: /api/iam/* (captura cualquier subruta)
    # Patron regex: ^iam/(?P<path>.*)$ - Captura todo despues de 'iam/'
    # Vista: IAMProxyView - Proxy al servicio IAM
    # Ejemplos: /api/iam/users/, /api/iam/roles/, /api/iam/permissions/
    re_path(r'^iam/(?P<path>.*)$', views.IAMProxyView.as_view(), name='iam_proxy'),

    # ==========================================================================
    # RUTAS DEL SERVICIO MATTER (Gestion de Casos)
    # ==========================================================================

    # Rutas de gestion de casos legales
    # URL: /api/cases/* (captura cualquier subruta)
    # Patron regex: ^cases/(?P<path>.*)$ - Captura rutas de casos
    # Vista: MatterProxyView - Proxy al servicio de casos
    # Ejemplos: /api/cases/, /api/cases/123/, /api/cases/123/documents/
    re_path(r'^cases/(?P<path>.*)$', views.MatterProxyView.as_view(), name='matter_cases_proxy'),

    # Rutas de gestion de tareas
    # URL: /api/tasks/* (captura cualquier subruta)
    # Vista: MatterProxyView - Las tareas pertenecen al servicio Matter
    # Ejemplos: /api/tasks/, /api/tasks/456/, /api/tasks/456/comments/
    re_path(r'^tasks/(?P<path>.*)$', views.MatterProxyView.as_view(), name='matter_tasks_proxy'),

    # Rutas de gestion de clientes
    # URL: /api/clients/* (captura cualquier subruta)
    # Vista: MatterProxyView - Los clientes pertenecen al servicio Matter
    # Ejemplos: /api/clients/, /api/clients/789/, /api/clients/789/cases/
    re_path(r'^clients/(?P<path>.*)$', views.MatterProxyView.as_view(), name='matter_clients_proxy'),

    # ==========================================================================
    # RUTAS DEL SERVICIO DOCUMENT (Gestion de Documentos)
    # ==========================================================================

    # Rutas de gestion de documentos
    # URL: /api/documents/* (captura cualquier subruta)
    # Vista: DocumentProxyView - Proxy al servicio de documentos
    # Ejemplos: /api/documents/, /api/documents/abc123/, /api/documents/abc123/download/
    re_path(r'^documents/(?P<path>.*)$', views.DocumentProxyView.as_view(), name='document_proxy'),

    # Rutas de gestion de carpetas
    # URL: /api/folders/* (captura cualquier subruta)
    # Vista: DocumentProxyView - Las carpetas pertenecen al servicio Document
    # Ejemplos: /api/folders/, /api/folders/def456/, /api/folders/def456/documents/
    re_path(r'^folders/(?P<path>.*)$', views.DocumentProxyView.as_view(), name='folders_proxy'),

    # ==========================================================================
    # RUTAS DEL SERVICIO TIME TRACKING (Control de Tiempo)
    # ==========================================================================

    # Rutas de entradas de tiempo (registro de horas trabajadas)
    # URL: /api/time-entries/* (captura cualquier subruta)
    # Vista: TimeTrackingProxyView - Proxy al servicio de tiempo
    # Ejemplos: /api/time-entries/, /api/time-entries/summary/, /api/time-entries/by-case/123/
    re_path(r'^time-entries/(?P<path>.*)$', views.TimeTrackingProxyView.as_view(), name='time_entries_proxy'),

    # Rutas de cronometros activos
    # URL: /api/timers/* (captura cualquier subruta)
    # Vista: TimeTrackingProxyView - Los timers pertenecen al servicio Time
    # Ejemplos: /api/timers/, /api/timers/start/, /api/timers/stop/
    re_path(r'^timers/(?P<path>.*)$', views.TimeTrackingProxyView.as_view(), name='timers_proxy'),

    # Rutas de tarifas por hora
    # URL: /api/rates/* (captura cualquier subruta)
    # Vista: TimeTrackingProxyView - Las tarifas pertenecen al servicio Time
    # Ejemplos: /api/rates/, /api/rates/by-user/, /api/rates/by-case-type/
    re_path(r'^rates/(?P<path>.*)$', views.TimeTrackingProxyView.as_view(), name='rates_proxy'),

    # ==========================================================================
    # RUTAS DEL SERVICIO BILLING (Facturacion)
    # ==========================================================================

    # Rutas de gestion de facturas
    # URL: /api/invoices/* (captura cualquier subruta)
    # Vista: BillingProxyView - Proxy al servicio de facturacion
    # Ejemplos: /api/invoices/, /api/invoices/123/, /api/invoices/123/pdf/, /api/invoices/summary/
    re_path(r'^invoices/(?P<path>.*)$', views.BillingProxyView.as_view(), name='invoices_proxy'),

    # Rutas de acuerdos de tarifas con clientes
    # URL: /api/rate-agreements/* (captura cualquier subruta)
    # Vista: BillingProxyView - Los acuerdos pertenecen al servicio Billing
    # Ejemplos: /api/rate-agreements/, /api/rate-agreements/by-client/456/
    re_path(r'^rate-agreements/(?P<path>.*)$', views.BillingProxyView.as_view(), name='rate_agreements_proxy'),

    # ==========================================================================
    # RUTAS DEL SERVICIO CALENDAR (Calendario)
    # ==========================================================================

    # Rutas de eventos del calendario
    # URL: /api/events/* (captura cualquier subruta)
    # Vista: CalendarProxyView - Proxy al servicio de calendario
    # Ejemplos: /api/events/, /api/events/123/, /api/events/by-date/2024-01-15/
    re_path(r'^events/(?P<path>.*)$', views.CalendarProxyView.as_view(), name='events_proxy'),

    # Rutas de vencimientos y plazos legales
    # URL: /api/deadlines/* (captura cualquier subruta)
    # Vista: CalendarProxyView - Los deadlines pertenecen al servicio Calendar
    # Ejemplos: /api/deadlines/, /api/deadlines/upcoming/, /api/deadlines/overdue/
    re_path(r'^deadlines/(?P<path>.*)$', views.CalendarProxyView.as_view(), name='deadlines_proxy'),

    # Rutas de dias festivos y no laborables
    # URL: /api/holidays/* (captura cualquier subruta)
    # Vista: CalendarProxyView - Los holidays pertenecen al servicio Calendar
    # Ejemplos: /api/holidays/, /api/holidays/2024/, /api/holidays/by-country/MX/
    re_path(r'^holidays/(?P<path>.*)$', views.CalendarProxyView.as_view(), name='holidays_proxy'),

    # ==========================================================================
    # RUTAS DEL SERVICIO PORTAL (Portal de Clientes)
    # ==========================================================================

    # Rutas del portal de clientes
    # URL: /api/portal/* (captura cualquier subruta)
    # Vista: PortalProxyView - Proxy al servicio del portal
    # Ejemplos: /api/portal/my-cases/, /api/portal/my-documents/, /api/portal/my-invoices/
    re_path(r'^portal/(?P<path>.*)$', views.PortalProxyView.as_view(), name='portal_proxy'),

    # ==========================================================================
    # RUTAS DEL SERVICIO ANALYTICS (Analiticas)
    # ==========================================================================

    # Rutas de reportes y analiticas
    # URL: /api/analytics/* (captura cualquier subruta)
    # Vista: AnalyticsProxyView - Proxy al servicio de analiticas
    # Ejemplos: /api/analytics/dashboard/, /api/analytics/profitability/, /api/analytics/workload/
    re_path(r'^analytics/(?P<path>.*)$', views.AnalyticsProxyView.as_view(), name='analytics_proxy'),
]
