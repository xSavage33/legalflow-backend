"""
Configuracion de URLs para la aplicacion Analytics del servicio de analiticas.

Este archivo define los patrones de URL que mapean las rutas HTTP a las vistas
correspondientes del servicio de analiticas. Cada endpoint proporciona acceso
a diferentes tipos de reportes y metricas del despacho juridico.

Endpoints disponibles:
    - /dashboard/: Panel principal con KPIs generales
    - /workload/: Analisis de carga de trabajo
    - /profitability/: Metricas de rentabilidad
    - /billing-status/: Estado de facturacion
    - /deadline-compliance/: Cumplimiento de plazos
    - /case-portfolio/: Analisis del portafolio de casos

Nota:
    Estas URLs se incluyen bajo el prefijo /api/analytics/ definido
    en la configuracion principal de URLs del proyecto.

Autor: LegalFlow Team
"""

# Importacion de la funcion path de Django para definir patrones de URL
# Permite mapear rutas URL a vistas de forma declarativa
from django.urls import path

# Importacion del modulo views que contiene las vistas de analiticas
# El punto indica importacion relativa desde el mismo paquete
from . import views

# Lista de patrones de URL para la aplicacion de analiticas
# Django procesa esta lista en orden para encontrar coincidencias
urlpatterns = [
    # Endpoint del dashboard principal
    # URL: /api/analytics/dashboard/
    # Vista: DashboardView - Proporciona KPIs agregados del despacho
    # Nombre: 'dashboard' - Permite referenciar la URL por nombre en templates/codigo
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),

    # Endpoint de analisis de carga de trabajo
    # URL: /api/analytics/workload/
    # Vista: WorkloadView - Muestra distribucion de trabajo por usuario
    # Nombre: 'workload' - Identificador unico para reverse URL lookup
    path('workload/', views.WorkloadView.as_view(), name='workload'),

    # Endpoint de analisis de rentabilidad
    # URL: /api/analytics/profitability/
    # Vista: ProfitabilityView - Calcula metricas financieras
    # Nombre: 'profitability' - Para generar URLs dinamicamente
    path('profitability/', views.ProfitabilityView.as_view(), name='profitability'),

    # Endpoint de estado de facturacion
    # URL: /api/analytics/billing-status/
    # Vista: BillingStatusView - Desglose de facturas por estado
    # Nombre: 'billing_status' - Usa guion bajo para consistencia con Python
    path('billing-status/', views.BillingStatusView.as_view(), name='billing_status'),

    # Endpoint de cumplimiento de plazos
    # URL: /api/analytics/deadline-compliance/
    # Vista: DeadlineComplianceView - Analisis de vencimientos
    # Nombre: 'deadline_compliance' - Identificador para la URL
    path('deadline-compliance/', views.DeadlineComplianceView.as_view(), name='deadline_compliance'),

    # Endpoint del portafolio de casos
    # URL: /api/analytics/case-portfolio/
    # Vista: CasePortfolioView - Distribucion de casos por tipo/estado
    # Nombre: 'case_portfolio' - Para referencias en codigo
    path('case-portfolio/', views.CasePortfolioView.as_view(), name='case_portfolio'),
]
