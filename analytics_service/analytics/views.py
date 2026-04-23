"""
Vistas del Servicio de Analytics (Analiticas) para LegalFlow.

Este archivo contiene las vistas basadas en clases (Class-Based Views) que
proporcionan los endpoints de la API REST para el servicio de analiticas.
Las vistas agregan datos de multiples microservicios (casos, facturacion,
tiempo, calendario) para generar reportes y dashboards ejecutivos.

Vistas incluidas:
    - DashboardView: Panel principal con KPIs generales
    - WorkloadView: Analisis de carga de trabajo por usuario
    - ProfitabilityView: Analisis de rentabilidad del despacho
    - BillingStatusView: Estado de facturacion y cobranza
    - DeadlineComplianceView: Cumplimiento de plazos y vencimientos
    - CasePortfolioView: Analisis del portafolio de casos

Seguridad:
    Todas las vistas requieren autenticacion y rol de admin o socio.

Autor: LegalFlow Team
"""

# Importacion de la biblioteca requests para realizar peticiones HTTP sincronas
# Se utiliza para comunicarse con otros microservicios del sistema
import requests

# Importacion de la clase Response de Django REST Framework
# Proporciona una respuesta HTTP con contenido serializado automaticamente
from rest_framework.response import Response

# Importacion de la clase base APIView de Django REST Framework
# Permite crear vistas basadas en clases con manejo automatico de metodos HTTP
from rest_framework.views import APIView

# Importacion del permiso IsAuthenticated de Django REST Framework
# Verifica que el usuario este autenticado antes de procesar la solicitud
from rest_framework.permissions import IsAuthenticated

# Importacion del modulo settings de Django para acceder a la configuracion
# Contiene las URLs de los microservicios y otras configuraciones del proyecto
from django.conf import settings

# Importacion del modulo timezone de Django para manejo de fechas y horas
# Proporciona funciones conscientes de zona horaria (timezone-aware)
from django.utils import timezone

# Importacion de timedelta para calcular diferencias de tiempo
# Se usa para definir periodos de tiempo (dias, horas, etc.)
from datetime import timedelta

# Importacion de la clase Decimal para manejo preciso de numeros decimales
# Evita errores de redondeo en calculos financieros
from decimal import Decimal


def fetch_service_data(url, headers):
    """
    Funcion auxiliar para obtener datos de otro microservicio.

    Realiza una peticion HTTP GET a la URL especificada con los headers
    proporcionados. Incluye manejo de errores para evitar que fallos
    en servicios externos afecten la respuesta.

    Args:
        url (str): URL completa del endpoint del microservicio a consultar
        headers (dict): Diccionario con headers HTTP, incluyendo autorizacion

    Returns:
        dict: Datos JSON de la respuesta si fue exitosa, diccionario vacio si falla

    Ejemplo:
        datos = fetch_service_data(
            'http://matter-service:8000/api/cases/statistics/',
            {'Authorization': 'Bearer token123'}
        )
    """
    try:
        # Agrega el header Host para evitar errores DisallowedHost en Docker
        # Los nombres de servicio de Docker no son hosts validos por defecto
        proxy_headers = {**headers, 'Host': 'localhost'}

        # Realiza la peticion GET con timeout de 10 segundos para evitar bloqueos
        response = requests.get(url, headers=proxy_headers, timeout=10)

        # Verifica si la respuesta fue exitosa (codigo 200)
        if response.status_code == 200:
            # Parsea y retorna los datos JSON de la respuesta
            return response.json()
    except Exception:
        # Captura cualquier excepcion (timeout, conexion, etc.) silenciosamente
        # Esto permite que el dashboard continue funcionando parcialmente
        pass

    # Retorna diccionario vacio si hubo error o respuesta no exitosa
    return {}


class AdminOnlyMixin:
    """
    Mixin para restringir acceso solo a administradores y socios.

    Este mixin se utiliza en conjunto con las vistas de analiticas para
    asegurar que solo usuarios con roles privilegiados puedan acceder
    a los reportes ejecutivos y datos sensibles del despacho.

    El mixin sobrescribe check_permissions() para agregar validacion
    adicional despues de la verificacion estandar de permisos.

    Roles permitidos:
        - admin: Administrador del sistema
        - partner: Socio del despacho

    Raises:
        PermissionDenied: Si el usuario no tiene rol de admin o partner
    """

    def check_permissions(self, request):
        """
        Verifica que el usuario tenga rol de administrador o socio.

        Primero ejecuta la verificacion de permisos de la clase padre,
        luego valida que el rol del usuario sea admin o partner.

        Args:
            request: Objeto de solicitud HTTP con informacion del usuario

        Raises:
            PermissionDenied: Si el usuario no tiene rol autorizado
        """
        # Ejecuta la verificacion de permisos de la clase padre (APIView)
        # Esto verifica autenticacion y otros permisos configurados
        super().check_permissions(request)

        # Verifica si el rol del usuario esta en la lista de roles permitidos
        if request.user.role not in ['admin', 'partner']:
            # Importa la excepcion PermissionDenied de DRF
            from rest_framework.exceptions import PermissionDenied

            # Lanza excepcion con mensaje en espanol
            raise PermissionDenied('Solo administradores y socios pueden acceder a analytics.')


class DashboardView(AdminOnlyMixin, APIView):
    """
    Vista del dashboard principal con KPIs del despacho.

    Esta vista agrega datos de multiples microservicios para proporcionar
    una vision ejecutiva del estado del despacho juridico. Incluye metricas
    de casos, facturacion, tiempo y vencimientos proximos.

    Endpoints:
        GET /api/analytics/dashboard/

    Respuesta:
        - cases: Estadisticas de casos (total, activos, pendientes, cerrados)
        - billing: Resumen de facturacion (facturado, pagado, pendiente, vencido)
        - time_tracking: Horas trabajadas y facturables
        - deadlines: Conteo de vencimientos proximos
        - generated_at: Marca de tiempo de generacion

    Seguridad:
        Requiere autenticacion y rol admin o partner.
    """

    def get(self, request):
        """
        Maneja peticiones GET para obtener el dashboard.

        Recopila datos de los servicios de casos, facturacion, tiempo
        y calendario para construir un resumen ejecutivo completo.

        Args:
            request: Objeto de solicitud HTTP con headers de autorizacion

        Returns:
            Response: Objeto Response con los datos del dashboard en JSON
        """
        # Extrae el header de autorizacion para pasarlo a los microservicios
        # Esto permite que los servicios validen el token del usuario
        headers = {'Authorization': request.META.get('HTTP_AUTHORIZATION', '')}

        # Obtiene estadisticas de casos del servicio de Matter (Gestion de Casos)
        # Incluye totales por estado y tipo de caso
        cases_data = fetch_service_data(f"{settings.MATTER_SERVICE_URL}/api/cases/statistics/", headers)

        # Obtiene resumen de facturacion del servicio de Billing
        # Incluye totales facturados, pagados, pendientes y vencidos
        billing_data = fetch_service_data(f"{settings.BILLING_SERVICE_URL}/api/invoices/summary/", headers)

        # Obtiene resumen de entradas de tiempo del servicio de Time Tracking
        # Incluye horas totales trabajadas y montos facturables
        time_data = fetch_service_data(f"{settings.TIME_SERVICE_URL}/api/time-entries/summary/", headers)

        # Obtiene vencimientos proximos (7 dias) del servicio de Calendar
        # Permite alertar sobre plazos que requieren atencion
        deadlines_data = fetch_service_data(f"{settings.CALENDAR_SERVICE_URL}/api/deadlines/upcoming/?days=7", headers)

        # Construye el diccionario de respuesta del dashboard
        dashboard = {
            # Seccion de estadisticas de casos
            'cases': {
                'total': cases_data.get('total_cases', 0),     # Total de casos en el sistema
                'active': cases_data.get('active_cases', 0),   # Casos actualmente activos
                'pending': cases_data.get('pending_cases', 0),  # Casos pendientes de accion
                'closed': cases_data.get('closed_cases', 0),   # Casos cerrados/finalizados
                'by_type': cases_data.get('by_type', {}),      # Distribucion por tipo de caso
            },
            # Seccion de estadisticas de facturacion
            'billing': {
                'total_invoiced': billing_data.get('total_invoiced', 0),    # Total facturado
                'total_paid': billing_data.get('total_paid', 0),            # Total cobrado
                'outstanding': billing_data.get('total_outstanding', 0),    # Saldo pendiente
                'overdue': billing_data.get('overdue_amount', 0),           # Monto vencido
            },
            # Seccion de estadisticas de tiempo
            'time_tracking': {
                'total_hours': time_data.get('total_hours', 0),  # Horas totales trabajadas
                # Convierte minutos facturables a horas con 2 decimales
                # Se usa el operador 'or 0' para manejar valores None
                'billable_hours': round((time_data.get('billable_minutes', 0) or 0) / 60, 2),
                'total_amount': time_data.get('total_amount', 0),  # Monto total facturable
            },
            # Seccion de vencimientos proximos
            'deadlines': {
                # Cuenta el numero de vencimientos en los resultados
                'upcoming_count': len(deadlines_data.get('results', [])),
            },
            # Marca de tiempo de cuando se genero el dashboard
            # Formato ISO 8601 para compatibilidad con JavaScript
            'generated_at': timezone.now().isoformat(),
        }

        # Retorna la respuesta con los datos del dashboard
        return Response(dashboard)


class WorkloadView(AdminOnlyMixin, APIView):
    """
    Vista de analisis de carga de trabajo por usuario.

    Proporciona informacion sobre la distribucion de trabajo entre
    los miembros del equipo, permitiendo identificar sobrecarga
    o subutilizacion de recursos.

    Endpoints:
        GET /api/analytics/workload/

    Respuesta:
        - total_hours: Total de horas trabajadas
        - by_activity_type: Distribucion por tipo de actividad
        - generated_at: Marca de tiempo de generacion

    Seguridad:
        Requiere autenticacion y rol admin o partner.
    """

    def get(self, request):
        """
        Maneja peticiones GET para obtener analisis de carga de trabajo.

        Obtiene datos de entradas de tiempo y los agrega para mostrar
        la distribucion de trabajo en el despacho.

        Args:
            request: Objeto de solicitud HTTP con headers de autorizacion

        Returns:
            Response: Objeto Response con los datos de carga de trabajo en JSON
        """
        # Extrae el header de autorizacion para autenticar con el microservicio
        headers = {'Authorization': request.META.get('HTTP_AUTHORIZATION', '')}

        # Obtiene resumen de tiempo del servicio de Time Tracking
        # Nota: En una implementacion real se necesitaria agregacion por usuario
        time_data = fetch_service_data(f"{settings.TIME_SERVICE_URL}/api/time-entries/summary/", headers)

        # Construye el diccionario de respuesta de carga de trabajo
        workload = {
            'total_hours': time_data.get('total_hours', 0),          # Horas totales trabajadas
            'by_activity_type': time_data.get('by_activity_type', {}),  # Distribucion por actividad
            'generated_at': timezone.now().isoformat(),                # Marca de tiempo
        }

        # Retorna la respuesta con los datos de carga de trabajo
        return Response(workload)


class ProfitabilityView(AdminOnlyMixin, APIView):
    """
    Vista de analisis de rentabilidad del despacho.

    Calcula metricas financieras clave como tasa de cobranza,
    tarifa horaria efectiva y comparacion de ingresos facturados
    vs cobrados para evaluar la salud financiera del despacho.

    Endpoints:
        GET /api/analytics/profitability/

    Respuesta:
        - total_revenue: Ingresos totales facturados
        - collected_revenue: Ingresos cobrados
        - collection_rate: Porcentaje de cobranza
        - total_hours_worked: Horas totales trabajadas
        - effective_hourly_rate: Tarifa horaria efectiva
        - generated_at: Marca de tiempo de generacion

    Seguridad:
        Requiere autenticacion y rol admin o partner.
    """

    def get(self, request):
        """
        Maneja peticiones GET para obtener analisis de rentabilidad.

        Combina datos de facturacion y tiempo para calcular metricas
        de rentabilidad del despacho.

        Args:
            request: Objeto de solicitud HTTP con headers de autorizacion

        Returns:
            Response: Objeto Response con los datos de rentabilidad en JSON
        """
        # Extrae el header de autorizacion para autenticar con microservicios
        headers = {'Authorization': request.META.get('HTTP_AUTHORIZATION', '')}

        # Obtiene datos de facturacion del servicio de Billing
        billing_data = fetch_service_data(f"{settings.BILLING_SERVICE_URL}/api/invoices/summary/", headers)

        # Obtiene datos de tiempo del servicio de Time Tracking
        time_data = fetch_service_data(f"{settings.TIME_SERVICE_URL}/api/time-entries/summary/", headers)

        # Convierte valores a Decimal para calculos financieros precisos
        # El operador 'or 0' maneja valores None retornados por los servicios
        total_invoiced = Decimal(str(billing_data.get('total_invoiced', 0) or 0))
        total_paid = Decimal(str(billing_data.get('total_paid', 0) or 0))
        total_hours = Decimal(str(time_data.get('total_hours', 0) or 0))

        # Construye el diccionario de respuesta de rentabilidad
        profitability = {
            # Total de ingresos facturados (convertido a float para JSON)
            'total_revenue': float(total_invoiced),

            # Total de ingresos efectivamente cobrados
            'collected_revenue': float(total_paid),

            # Tasa de cobranza: porcentaje de lo facturado que se ha cobrado
            # Se verifica que total_invoiced > 0 para evitar division por cero
            'collection_rate': float(total_paid / total_invoiced * 100) if total_invoiced > 0 else 0,

            # Total de horas trabajadas por el equipo
            'total_hours_worked': float(total_hours),

            # Tarifa horaria efectiva: ingresos cobrados dividido por horas trabajadas
            # Indica cuanto se gana realmente por hora de trabajo
            'effective_hourly_rate': float(total_paid / total_hours) if total_hours > 0 else 0,

            # Marca de tiempo de generacion del reporte
            'generated_at': timezone.now().isoformat(),
        }

        # Retorna la respuesta con los datos de rentabilidad
        return Response(profitability)


class BillingStatusView(AdminOnlyMixin, APIView):
    """
    Vista de estado de facturacion y cobranza.

    Proporciona un desglose detallado del estado de las facturas
    del despacho, incluyendo montos por estado y alertas de
    facturas vencidas.

    Endpoints:
        GET /api/analytics/billing-status/

    Respuesta:
        - total_invoiced: Total facturado
        - total_paid: Total cobrado
        - outstanding: Saldo pendiente de cobro
        - overdue: Monto de facturas vencidas
        - by_status: Distribucion por estado de factura
        - generated_at: Marca de tiempo de generacion

    Seguridad:
        Requiere autenticacion y rol admin o partner.
    """

    def get(self, request):
        """
        Maneja peticiones GET para obtener estado de facturacion.

        Obtiene el resumen de facturas del servicio de Billing y
        lo formatea para presentacion en el dashboard.

        Args:
            request: Objeto de solicitud HTTP con headers de autorizacion

        Returns:
            Response: Objeto Response con el estado de facturacion en JSON
        """
        # Extrae el header de autorizacion para autenticar con el microservicio
        headers = {'Authorization': request.META.get('HTTP_AUTHORIZATION', '')}

        # Obtiene resumen de facturacion del servicio de Billing
        billing_data = fetch_service_data(f"{settings.BILLING_SERVICE_URL}/api/invoices/summary/", headers)

        # Construye el diccionario de respuesta de estado de facturacion
        billing_status = {
            'total_invoiced': billing_data.get('total_invoiced', 0),    # Total facturado
            'total_paid': billing_data.get('total_paid', 0),            # Total pagado
            'outstanding': billing_data.get('total_outstanding', 0),    # Pendiente de cobro
            'overdue': billing_data.get('overdue_amount', 0),           # Facturas vencidas
            'by_status': billing_data.get('by_status', {}),             # Desglose por estado
            'generated_at': timezone.now().isoformat(),                 # Marca de tiempo
        }

        # Retorna la respuesta con el estado de facturacion
        return Response(billing_status)


class DeadlineComplianceView(AdminOnlyMixin, APIView):
    """
    Vista de analisis de cumplimiento de plazos.

    Evalua el desempeno del despacho en el cumplimiento de
    vencimientos y plazos legales, identificando riesgos
    de incumplimiento.

    Endpoints:
        GET /api/analytics/deadline-compliance/

    Respuesta:
        - upcoming_deadlines: Numero de vencimientos proximos (30 dias)
        - overdue_deadlines: Numero de vencimientos ya pasados
        - compliance_rate: Porcentaje de cumplimiento
        - generated_at: Marca de tiempo de generacion

    Seguridad:
        Requiere autenticacion y rol admin o partner.
    """

    def get(self, request):
        """
        Maneja peticiones GET para obtener analisis de cumplimiento.

        Obtiene datos de vencimientos proximos y vencidos del servicio
        de Calendar para calcular la tasa de cumplimiento.

        Args:
            request: Objeto de solicitud HTTP con headers de autorizacion

        Returns:
            Response: Objeto Response con datos de cumplimiento en JSON
        """
        # Extrae el header de autorizacion para autenticar con el microservicio
        headers = {'Authorization': request.META.get('HTTP_AUTHORIZATION', '')}

        # Obtiene vencimientos proximos (30 dias) del servicio de Calendar
        upcoming = fetch_service_data(f"{settings.CALENDAR_SERVICE_URL}/api/deadlines/upcoming/?days=30", headers)

        # Obtiene vencimientos ya pasados (vencidos) del servicio de Calendar
        overdue = fetch_service_data(f"{settings.CALENDAR_SERVICE_URL}/api/deadlines/overdue/", headers)

        # Cuenta el numero de vencimientos en cada categoria
        upcoming_count = len(upcoming.get('results', []))  # Vencimientos proximos
        overdue_count = len(overdue.get('results', []))    # Vencimientos pasados

        # Construye el diccionario de respuesta de cumplimiento
        compliance = {
            'upcoming_deadlines': upcoming_count,  # Vencimientos por venir
            'overdue_deadlines': overdue_count,    # Vencimientos incumplidos

            # Tasa de cumplimiento: porcentaje de vencimientos cumplidos
            # Formula: proximos / (proximos + vencidos) * 100
            # Si no hay vencimientos, la tasa es 100% (no hay incumplimientos)
            'compliance_rate': round(upcoming_count / (upcoming_count + overdue_count) * 100, 2) if (upcoming_count + overdue_count) > 0 else 100,

            'generated_at': timezone.now().isoformat(),  # Marca de tiempo
        }

        # Retorna la respuesta con los datos de cumplimiento
        return Response(compliance)


class CasePortfolioView(AdminOnlyMixin, APIView):
    """
    Vista de analisis del portafolio de casos.

    Proporciona una vision completa de la composicion del portafolio
    de casos del despacho, incluyendo distribucion por estado,
    tipo y prioridad.

    Endpoints:
        GET /api/analytics/case-portfolio/

    Respuesta:
        - total_cases: Numero total de casos
        - by_status: Distribucion por estado (activo, pendiente, cerrado)
        - by_type: Distribucion por tipo de caso
        - by_priority: Distribucion por prioridad
        - generated_at: Marca de tiempo de generacion

    Seguridad:
        Requiere autenticacion y rol admin o partner.
    """

    def get(self, request):
        """
        Maneja peticiones GET para obtener analisis del portafolio.

        Obtiene estadisticas de casos del servicio de Matter y las
        organiza para mostrar la composicion del portafolio.

        Args:
            request: Objeto de solicitud HTTP con headers de autorizacion

        Returns:
            Response: Objeto Response con datos del portafolio en JSON
        """
        # Extrae el header de autorizacion para autenticar con el microservicio
        headers = {'Authorization': request.META.get('HTTP_AUTHORIZATION', '')}

        # Obtiene estadisticas de casos del servicio de Matter
        cases_data = fetch_service_data(f"{settings.MATTER_SERVICE_URL}/api/cases/statistics/", headers)

        # Construye el diccionario de respuesta del portafolio
        portfolio = {
            'total_cases': cases_data.get('total_cases', 0),  # Total de casos

            # Distribucion de casos por estado
            'by_status': {
                'active': cases_data.get('active_cases', 0),    # Casos activos
                'pending': cases_data.get('pending_cases', 0),  # Casos pendientes
                'closed': cases_data.get('closed_cases', 0),    # Casos cerrados
            },

            'by_type': cases_data.get('by_type', {}),           # Por tipo de caso
            'by_priority': cases_data.get('by_priority', {}),   # Por prioridad
            'generated_at': timezone.now().isoformat(),         # Marca de tiempo
        }

        # Retorna la respuesta con los datos del portafolio
        return Response(portfolio)
