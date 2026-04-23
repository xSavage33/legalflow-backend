"""
Modulo de Configuracion de URLs del Servicio de Casos Legales (Matter Service)

Este archivo define todas las rutas URL para la API REST del servicio de casos.
Cada URL esta mapeada a una vista especifica que maneja las solicitudes HTTP.

Estructura de URLs:
- /cases/                          - Listar y crear casos
- /cases/statistics/               - Obtener estadisticas de casos
- /cases/<uuid:id>/                - Detalle, actualizar y eliminar caso por UUID
- /cases/by-number/<case_number>/  - Buscar caso por numero de expediente
- /cases/<uuid:case_id>/parties/   - Gestionar partes del caso
- /cases/<uuid:case_id>/dates/     - Gestionar fechas del caso
- /cases/<uuid:case_id>/notes/     - Gestionar notas del caso
- /cases/<uuid:case_id>/tasks/     - Gestionar tareas del caso
- /tasks/                          - Listar tareas del usuario actual
- /clients/<uuid:client_id>/cases/ - Listar casos de un cliente especifico

Todas las URLs utilizan UUID como identificadores para mayor seguridad
y compatibilidad con arquitecturas distribuidas.

Autor: Equipo de Desarrollo LegalFlow
"""

# Importacion de la funcion path de Django para definir rutas URL
# path() es la forma recomendada de definir URLs en Django 2.0+
from django.urls import path

# Importacion del modulo views que contiene todas las vistas de la API
# Se importa el modulo completo para acceder a las vistas como views.NombreVista
from . import views


# Lista de patrones de URL para la aplicacion de casos
# Cada entrada define una ruta y la vista que la maneja
urlpatterns = [

    # ==========================================================================
    # ENDPOINTS PRINCIPALES DE CASOS
    # ==========================================================================

    # Endpoint para listar todos los casos y crear nuevos casos
    # GET: Lista casos con filtros, busqueda y ordenamiento
    # POST: Crea un nuevo caso
    # URL: /api/v1/cases/
    path(
        'cases/',                              # Ruta URL
        views.CaseListCreateView.as_view(),    # Vista asociada (convertida a funcion con as_view())
        name='case_list_create'                # Nombre para referencia inversa (reverse())
    ),

    # Endpoint para obtener estadisticas de casos
    # GET: Retorna metricas agregadas (totales, por tipo, por prioridad)
    # URL: /api/v1/cases/statistics/
    # Nota: Esta ruta debe ir ANTES de /cases/<uuid:id>/ para evitar conflictos
    path(
        'cases/statistics/',                   # Ruta URL
        views.CaseStatisticsView.as_view(),    # Vista asociada
        name='case_statistics'                 # Nombre para referencia inversa
    ),

    # Endpoint para ver, actualizar y eliminar un caso especifico por UUID
    # GET: Obtiene detalles completos del caso
    # PUT/PATCH: Actualiza el caso
    # DELETE: Archiva el caso (soft delete)
    # URL: /api/v1/cases/{uuid}/
    # El parametro <uuid:id> captura un UUID valido y lo pasa como 'id' a la vista
    path(
        'cases/<uuid:id>/',                    # Ruta URL con parametro UUID
        views.CaseDetailView.as_view(),        # Vista asociada
        name='case_detail'                     # Nombre para referencia inversa
    ),

    # Endpoint para buscar un caso por su numero de expediente
    # GET: Obtiene el caso usando el numero de caso (ej: LF-2024-00001)
    # URL: /api/v1/cases/by-number/{case_number}/
    # El parametro <str:case_number> captura cualquier cadena de texto
    path(
        'cases/by-number/<str:case_number>/',  # Ruta URL con parametro string
        views.CaseByNumberView.as_view(),      # Vista asociada
        name='case_by_number'                  # Nombre para referencia inversa
    ),

    # ==========================================================================
    # ENDPOINTS DE PARTES DEL CASO (CaseParty)
    # ==========================================================================

    # Endpoint para listar y crear partes de un caso especifico
    # GET: Lista todas las partes del caso
    # POST: Crea una nueva parte (demandante, demandado, testigo, etc.)
    # URL: /api/v1/cases/{case_uuid}/parties/
    path(
        'cases/<uuid:case_id>/parties/',       # Ruta URL con case_id como parametro
        views.CasePartyListCreateView.as_view(), # Vista asociada
        name='case_party_list_create'          # Nombre para referencia inversa
    ),

    # Endpoint para ver, actualizar y eliminar una parte especifica
    # GET: Obtiene detalles de la parte
    # PUT/PATCH: Actualiza la parte
    # DELETE: Elimina la parte
    # URL: /api/v1/cases/{case_uuid}/parties/{party_uuid}/
    path(
        'cases/<uuid:case_id>/parties/<uuid:id>/',  # Ruta con dos parametros UUID
        views.CasePartyDetailView.as_view(),        # Vista asociada
        name='case_party_detail'                    # Nombre para referencia inversa
    ),

    # ==========================================================================
    # ENDPOINTS DE FECHAS DEL CASO (CaseDate)
    # ==========================================================================

    # Endpoint para listar y crear fechas/eventos de un caso
    # GET: Lista todas las fechas del caso (audiencias, plazos, etc.)
    # POST: Crea una nueva fecha/evento
    # URL: /api/v1/cases/{case_uuid}/dates/
    path(
        'cases/<uuid:case_id>/dates/',         # Ruta URL con case_id
        views.CaseDateListCreateView.as_view(), # Vista asociada
        name='case_date_list_create'           # Nombre para referencia inversa
    ),

    # Endpoint para ver, actualizar y eliminar una fecha especifica
    # GET: Obtiene detalles de la fecha/evento
    # PUT/PATCH: Actualiza la fecha/evento
    # DELETE: Elimina la fecha/evento
    # URL: /api/v1/cases/{case_uuid}/dates/{date_uuid}/
    path(
        'cases/<uuid:case_id>/dates/<uuid:id>/',  # Ruta con dos parametros UUID
        views.CaseDateDetailView.as_view(),       # Vista asociada
        name='case_date_detail'                   # Nombre para referencia inversa
    ),

    # ==========================================================================
    # ENDPOINTS DE NOTAS DEL CASO (CaseNote)
    # ==========================================================================

    # Endpoint para listar y crear notas de un caso
    # GET: Lista notas (respeta privacidad - solo muestra propias notas privadas)
    # POST: Crea una nueva nota
    # URL: /api/v1/cases/{case_uuid}/notes/
    path(
        'cases/<uuid:case_id>/notes/',         # Ruta URL con case_id
        views.CaseNoteListCreateView.as_view(), # Vista asociada
        name='case_note_list_create'           # Nombre para referencia inversa
    ),

    # Endpoint para ver, actualizar y eliminar una nota especifica
    # GET: Obtiene detalles de la nota
    # PUT/PATCH: Actualiza la nota
    # DELETE: Elimina la nota
    # URL: /api/v1/cases/{case_uuid}/notes/{note_uuid}/
    path(
        'cases/<uuid:case_id>/notes/<uuid:id>/',  # Ruta con dos parametros UUID
        views.CaseNoteDetailView.as_view(),       # Vista asociada
        name='case_note_detail'                   # Nombre para referencia inversa
    ),

    # ==========================================================================
    # ENDPOINTS DE TAREAS DEL CASO (CaseTask)
    # ==========================================================================

    # Endpoint para listar y crear tareas de un caso
    # GET: Lista tareas con filtros por estado, prioridad y asignado
    # POST: Crea una nueva tarea
    # URL: /api/v1/cases/{case_uuid}/tasks/
    path(
        'cases/<uuid:case_id>/tasks/',         # Ruta URL con case_id
        views.CaseTaskListCreateView.as_view(), # Vista asociada
        name='case_task_list_create'           # Nombre para referencia inversa
    ),

    # Endpoint para ver, actualizar y eliminar una tarea especifica
    # GET: Obtiene detalles de la tarea
    # PUT/PATCH: Actualiza la tarea (establece completed_at si status='completed')
    # DELETE: Elimina la tarea
    # URL: /api/v1/cases/{case_uuid}/tasks/{task_uuid}/
    path(
        'cases/<uuid:case_id>/tasks/<uuid:id>/',  # Ruta con dos parametros UUID
        views.CaseTaskDetailView.as_view(),       # Vista asociada
        name='case_task_detail'                   # Nombre para referencia inversa
    ),

    # ==========================================================================
    # ENDPOINTS ADICIONALES
    # ==========================================================================

    # Endpoint para listar todas las tareas asignadas al usuario actual
    # GET: Lista tareas del usuario a traves de todos los casos
    # Util para ver la carga de trabajo completa del usuario
    # URL: /api/v1/tasks/
    path(
        'tasks/',                              # Ruta URL simple
        views.TaskListView.as_view(),          # Vista asociada
        name='task_list'                       # Nombre para referencia inversa
    ),

    # Endpoint para listar todos los casos de un cliente especifico
    # GET: Lista casos donde client_id coincide con el parametro
    # URL: /api/v1/clients/{client_uuid}/cases/
    path(
        'clients/<uuid:client_id>/cases/',     # Ruta URL con client_id
        views.ClientCasesView.as_view(),       # Vista asociada
        name='client_cases'                    # Nombre para referencia inversa
    ),
]
