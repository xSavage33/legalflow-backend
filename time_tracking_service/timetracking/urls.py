"""
Modulo de Configuracion de URLs del Servicio de Control de Tiempo (Time Tracking Service)

Este archivo define las rutas URL que mapean a las vistas de la API.
Cada ruta especifica un patron de URL y la vista que debe manejar
las solicitudes a esa URL.

Grupos de URLs:
- Entradas de Tiempo (/time-entries/): CRUD y operaciones especiales
- Temporizadores (/timers/): Control de temporizadores en tiempo real
- Tarifas (/rates/): Configuracion de tarifas por usuario y caso

Convenciones de nomenclatura:
- Las rutas usan guiones (-) para separar palabras
- Los IDs son UUIDs
- Los nombres de las rutas usan guiones bajos (_)

Autor: LegalFlow Team
Fecha: 2024
"""

# Importa la funcion path de Django para definir rutas URL
# path() permite crear patrones de URL simples y legibles
from django.urls import path

# Importa el modulo views que contiene todas las vistas de la API
from . import views

# Lista de patrones de URL para este modulo
# Cada elemento es una ruta que mapea una URL a una vista
# El nombre de la ruta (name) se usa para referenciarla en el codigo
urlpatterns = [

    # ==========================================================================
    # RUTAS DE ENTRADAS DE TIEMPO (Time Entries)
    # ==========================================================================
    # Estas rutas manejan el CRUD de entradas de tiempo y operaciones especiales
    # como aprobacion y obtencion de entradas no facturadas.

    # Ruta: GET/POST /time-entries/
    # GET: Lista todas las entradas de tiempo (con filtros)
    # POST: Crea una nueva entrada de tiempo
    # Vista: TimeEntryListCreateView
    path('time-entries/', views.TimeEntryListCreateView.as_view(), name='time_entry_list_create'),

    # Ruta: GET /time-entries/summary/
    # GET: Obtiene un resumen estadistico de las entradas de tiempo
    # Incluye totales, desglose por actividad y estado
    # Vista: TimeEntrySummaryView
    # IMPORTANTE: Esta ruta debe estar ANTES de /time-entries/<uuid:id>/
    # porque Django evalua las rutas en orden y 'summary' podria ser interpretado como UUID
    path('time-entries/summary/', views.TimeEntrySummaryView.as_view(), name='time_entry_summary'),

    # Ruta: GET /time-entries/unbilled/
    # GET: Lista entradas de tiempo que aun no han sido facturadas
    # Util para preparar facturas con tiempo pendiente
    # Vista: UnbilledTimeEntriesView
    path('time-entries/unbilled/', views.UnbilledTimeEntriesView.as_view(), name='unbilled_time_entries'),

    # Ruta: GET /time-entries/my/
    # GET: Lista las entradas de tiempo del usuario actual
    # Muestra solo las entradas propias del usuario autenticado
    # Vista: MyTimeEntriesView
    path('time-entries/my/', views.MyTimeEntriesView.as_view(), name='my_time_entries'),

    # Ruta: GET/PUT/PATCH/DELETE /time-entries/{id}/
    # GET: Obtiene los detalles de una entrada especifica
    # PUT: Actualiza completamente una entrada
    # PATCH: Actualiza parcialmente una entrada
    # DELETE: Elimina una entrada (si no esta aprobada o facturada)
    # Vista: TimeEntryDetailView
    # <uuid:id>: Captura un UUID y lo pasa como parametro 'id' a la vista
    path('time-entries/<uuid:id>/', views.TimeEntryDetailView.as_view(), name='time_entry_detail'),

    # Ruta: POST /time-entries/{id}/approve/
    # POST: Aprueba o rechaza una entrada de tiempo
    # Requiere un cuerpo JSON con 'action' (approve/reject) y opcionalmente 'rejection_reason'
    # Vista: TimeEntryApprovalView
    path('time-entries/<uuid:id>/approve/', views.TimeEntryApprovalView.as_view(), name='time_entry_approval'),

    # ==========================================================================
    # RUTAS DE TEMPORIZADORES (Timers)
    # ==========================================================================
    # Estas rutas permiten controlar temporizadores en tiempo real para
    # seguimiento de tiempo mientras se trabaja.

    # Ruta: GET /timers/
    # GET: Lista todos los temporizadores del usuario actual
    # Incluye temporizadores activos y pausados
    # Vista: TimerListView
    path('timers/', views.TimerListView.as_view(), name='timer_list'),

    # Ruta: POST /timers/start/
    # POST: Inicia un nuevo temporizador
    # Solo se permite un temporizador activo por usuario
    # Vista: TimerStartView
    path('timers/start/', views.TimerStartView.as_view(), name='timer_start'),

    # Ruta: POST /timers/stop/
    # POST: Detiene el temporizador activo del usuario
    # Opcionalmente crea una entrada de tiempo con el tiempo registrado
    # Vista: TimerStopView
    path('timers/stop/', views.TimerStopView.as_view(), name='timer_stop'),

    # Ruta: GET /timers/current/
    # GET: Obtiene el temporizador activo actual del usuario
    # Retorna 404 si no hay temporizador activo
    # Vista: CurrentTimerView
    path('timers/current/', views.CurrentTimerView.as_view(), name='current_timer'),

    # Ruta: POST /timers/{id}/stop/
    # POST: Detiene un temporizador especifico por su ID
    # Permite detener un temporizador especifico en lugar del activo
    # Vista: TimerStopView (misma vista pero con ID especifico)
    path('timers/<uuid:id>/stop/', views.TimerStopView.as_view(), name='timer_stop_specific'),

    # Ruta: POST /timers/{id}/pause/
    # POST: Pausa un temporizador especifico
    # El tiempo acumulado se guarda para poder reanudar despues
    # Vista: TimerPauseView
    path('timers/<uuid:id>/pause/', views.TimerPauseView.as_view(), name='timer_pause'),

    # Ruta: POST /timers/{id}/resume/
    # POST: Reanuda un temporizador pausado
    # Continua el conteo manteniendo el tiempo acumulado
    # Vista: TimerResumeView
    path('timers/<uuid:id>/resume/', views.TimerResumeView.as_view(), name='timer_resume'),

    # Ruta: DELETE /timers/{id}/
    # DELETE: Elimina un temporizador sin crear entrada de tiempo
    # Util para descartar tiempo sin guardar
    # Vista: TimerDeleteView
    path('timers/<uuid:id>/', views.TimerDeleteView.as_view(), name='timer_delete'),

    # ==========================================================================
    # RUTAS DE TARIFAS (Rates)
    # ==========================================================================
    # Estas rutas permiten configurar tarifas por hora para usuarios
    # y tarifas especiales para casos especificos.

    # Ruta: GET/PUT/PATCH /rates/user/
    # GET: Obtiene la tarifa del usuario actual
    # PUT/PATCH: Actualiza la tarifa del usuario actual
    # Si no existe tarifa, se crea una con valores predeterminados
    # Vista: UserRateView
    path('rates/user/', views.UserRateView.as_view(), name='my_rate'),

    # Ruta: GET/PUT/PATCH /rates/user/{user_id}/
    # GET: Obtiene la tarifa de un usuario especifico
    # PUT/PATCH: Actualiza la tarifa de un usuario especifico
    # Usado por administradores para configurar tarifas de otros usuarios
    # Vista: UserRateView
    path('rates/user/<uuid:user_id>/', views.UserRateView.as_view(), name='user_rate'),

    # Ruta: GET/POST /rates/case/{case_id}/
    # GET: Lista las tarifas especiales de un caso
    # POST: Crea una nueva tarifa especial para el caso
    # Las tarifas de caso tienen prioridad sobre las de usuario
    # Vista: CaseRateListCreateView
    path('rates/case/<uuid:case_id>/', views.CaseRateListCreateView.as_view(), name='case_rates'),
]
