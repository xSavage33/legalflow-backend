"""
Modulo de Vistas del Servicio de Control de Tiempo (Time Tracking Service)

Este archivo contiene todas las vistas (endpoints de API) para gestionar
el seguimiento de tiempo en un entorno legal. Proporciona funcionalidad
para crear, leer, actualizar y eliminar entradas de tiempo, gestionar
temporizadores y configurar tarifas.

Vistas incluidas:
- Vistas de Entradas de Tiempo: CRUD completo, aprobacion, resumen
- Vistas de Temporizadores: Iniciar, pausar, reanudar, detener
- Vistas de Tarifas: Configuracion de tarifas por usuario y caso

El modulo utiliza Django REST Framework para construir la API RESTful.

Autor: LegalFlow Team
Fecha: 2024
"""

# ==================== IMPORTACIONES DE DJANGO REST FRAMEWORK ====================

# Importa vistas genericas de DRF para operaciones CRUD estandar
# generics proporciona clases base como ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework import generics, status, filters

# Importa Response para construir respuestas HTTP personalizadas
from rest_framework.response import Response

# Importa APIView como clase base para vistas personalizadas sin comportamiento CRUD predefinido
from rest_framework.views import APIView

# ==================== IMPORTACIONES DE FILTRADO ====================

# Importa DjangoFilterBackend para filtrado avanzado basado en campos del modelo
from django_filters.rest_framework import DjangoFilterBackend

# ==================== IMPORTACIONES DE DJANGO ====================

# Importa funciones de agregacion para calculos en consultas de base de datos
# Sum: Suma de valores, Count: Conteo de registros, Q: Consultas complejas
from django.db.models import Sum, Count, Q

# Importa timezone para manejar fechas y horas con zona horaria
from django.utils import timezone

# Importa date y timedelta para manipulacion de fechas
from datetime import date, timedelta

# ==================== IMPORTACIONES LOCALES ====================

# Importa los modelos definidos en este servicio
from .models import TimeEntry, Timer, UserRate, CaseRate

# Importa todos los serializadores necesarios para transformar datos
from .serializers import (
    TimeEntrySerializer,          # Serializador completo de lectura
    TimeEntryCreateSerializer,    # Serializador para crear entradas
    TimeEntryUpdateSerializer,    # Serializador para actualizar entradas
    TimeEntryApprovalSerializer,  # Serializador para aprobar/rechazar
    TimerSerializer,              # Serializador completo de temporizador
    TimerStartSerializer,         # Serializador para iniciar temporizador
    TimerStopSerializer,          # Serializador para detener temporizador
    UserRateSerializer,           # Serializador de tarifa de usuario
    CaseRateSerializer,           # Serializador de tarifa de caso
    TimeEntrySummarySerializer,   # Serializador para resumen estadistico
)


# ==================== VISTAS DE ENTRADAS DE TIEMPO ====================

class TimeEntryListCreateView(generics.ListCreateAPIView):
    """
    Vista para listar y crear entradas de tiempo

    Endpoints:
        GET /time-entries/: Lista todas las entradas de tiempo
        POST /time-entries/: Crea una nueva entrada de tiempo

    Caracteristicas:
        - Filtrado por caso, usuario, estado, tipo de actividad, fecha
        - Busqueda por descripcion y numero de caso
        - Ordenamiento por fecha, duracion, monto
        - Filtrado automatico por rol de usuario
    """

    # QuerySet base que incluye todas las entradas de tiempo
    queryset = TimeEntry.objects.all()

    # Configura los backends de filtrado disponibles
    # DjangoFilterBackend: Filtrado por campos exactos
    # SearchFilter: Busqueda de texto
    # OrderingFilter: Ordenamiento dinamico
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Campos por los cuales se puede filtrar con parametros de consulta exactos
    # Ejemplo: ?case_id=xxx&status=approved
    filterset_fields = ['case_id', 'user_id', 'status', 'is_billable', 'activity_type', 'date']

    # Campos en los que se puede buscar texto
    # Ejemplo: ?search=contrato
    search_fields = ['description', 'case_number']

    # Campos por los cuales se puede ordenar
    # Ejemplo: ?ordering=-amount (descendente por monto)
    ordering_fields = ['date', 'duration_minutes', 'created_at', 'amount']

    # Ordenamiento predeterminado: fecha descendente, luego creacion descendente
    ordering = ['-date', '-created_at']

    def get_serializer_class(self):
        """
        Retorna el serializador apropiado segun el metodo HTTP

        Para POST (crear), usa TimeEntryCreateSerializer que solo incluye
        campos necesarios para creacion. Para GET (listar), usa el
        serializador completo TimeEntrySerializer.

        Retorna:
            class: Clase del serializador a usar
        """
        # Si es una solicitud POST, usa el serializador de creacion
        if self.request.method == 'POST':
            return TimeEntryCreateSerializer
        # Para GET y otros metodos, usa el serializador completo
        return TimeEntrySerializer

    def get_queryset(self):
        """
        Personaliza el queryset segun el usuario y parametros de consulta

        Aplica filtros de seguridad basados en el rol del usuario:
        - Admin y Partner: Ven todas las entradas
        - Otros roles: Solo ven sus propias entradas

        Tambien aplica filtros de rango de fechas si se proporcionan.

        Retorna:
            QuerySet: Entradas de tiempo filtradas
        """
        # Obtiene el queryset base
        queryset = super().get_queryset()
        # Obtiene el usuario autenticado de la solicitud
        user = self.request.user

        # Filtrado basado en rol de usuario
        # Solo admin y partner pueden ver todas las entradas
        if user.role not in ['admin', 'partner']:
            # Filtra para mostrar solo las entradas del usuario actual
            queryset = queryset.filter(user_id=user.id)

        # Filtro de rango de fechas (fecha desde)
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')

        # Aplica filtro de fecha inicial si se proporciona
        if date_from:
            # __gte significa "greater than or equal" (mayor o igual)
            queryset = queryset.filter(date__gte=date_from)

        # Aplica filtro de fecha final si se proporciona
        if date_to:
            # __lte significa "less than or equal" (menor o igual)
            queryset = queryset.filter(date__lte=date_to)

        return queryset


class TimeEntryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Vista para ver, actualizar y eliminar una entrada de tiempo especifica

    Endpoints:
        GET /time-entries/{id}/: Obtiene detalles de una entrada
        PUT /time-entries/{id}/: Actualiza completamente una entrada
        PATCH /time-entries/{id}/: Actualiza parcialmente una entrada
        DELETE /time-entries/{id}/: Elimina una entrada

    Restricciones:
        - No se pueden eliminar entradas facturadas o aprobadas
    """

    # QuerySet que incluye todas las entradas de tiempo
    queryset = TimeEntry.objects.all()

    # Campo usado para buscar la entrada en la URL
    # La URL sera /time-entries/<uuid:id>/
    lookup_field = 'id'

    def get_serializer_class(self):
        """
        Retorna el serializador apropiado segun el metodo HTTP

        Para PUT/PATCH (actualizar), usa TimeEntryUpdateSerializer.
        Para GET, usa el serializador completo.

        Retorna:
            class: Clase del serializador a usar
        """
        # Si es PUT o PATCH, usa el serializador de actualizacion
        if self.request.method in ['PUT', 'PATCH']:
            return TimeEntryUpdateSerializer
        # Para GET, usa el serializador completo de lectura
        return TimeEntrySerializer

    def perform_destroy(self, instance):
        """
        Valida y ejecuta la eliminacion de una entrada de tiempo

        Impide eliminar entradas que ya han sido facturadas o aprobadas
        para mantener la integridad de los registros contables.

        Args:
            instance: Instancia de TimeEntry a eliminar

        Raises:
            ValidationError: Si la entrada esta facturada o aprobada
        """
        # Verifica si la entrada tiene un estado que impide eliminacion
        if instance.status in ['billed', 'approved']:
            # Lanza error si se intenta eliminar una entrada protegida
            raise serializers.ValidationError('No se pueden eliminar entradas facturadas o aprobadas.')
        # Si pasa la validacion, elimina la entrada
        instance.delete()


class TimeEntryApprovalView(APIView):
    """
    Vista para aprobar o rechazar entradas de tiempo

    Endpoint:
        POST /time-entries/{id}/approve/

    Acciones:
        - approve: Marca la entrada como aprobada
        - reject: Marca la entrada como rechazada con razon opcional

    Esta vista es usada por supervisores para validar el tiempo
    registrado por los miembros del equipo.
    """

    def post(self, request, id):
        """
        Procesa la aprobacion o rechazo de una entrada de tiempo

        Args:
            request: Objeto de solicitud HTTP con datos de aprobacion
            id: UUID de la entrada de tiempo

        Retorna:
            Response: Mensaje de exito o error
        """
        # Intenta obtener la entrada de tiempo por su ID
        try:
            entry = TimeEntry.objects.get(id=id)
        except TimeEntry.DoesNotExist:
            # Retorna error 404 si la entrada no existe
            return Response({'error': 'Entrada de tiempo no encontrada'}, status=status.HTTP_404_NOT_FOUND)

        # Valida los datos de la solicitud usando el serializador
        serializer = TimeEntryApprovalSerializer(data=request.data)
        # raise_exception=True hace que lance error automaticamente si es invalido
        serializer.is_valid(raise_exception=True)

        # Obtiene la accion validada (approve o reject)
        action = serializer.validated_data['action']

        # Procesa segun la accion solicitada
        if action == 'approve':
            # Marca la entrada como aprobada
            entry.status = 'approved'
            # Registra quien aprobo (ID del usuario actual)
            entry.approved_by_id = request.user.id
            # Registra el nombre/email de quien aprobo
            entry.approved_by_name = request.user.email
            # Registra la fecha y hora de aprobacion
            entry.approved_at = timezone.now()
            # Guarda los cambios en la base de datos
            entry.save()
            # Retorna mensaje de exito en espanol
            return Response({'message': 'Entrada de tiempo aprobada'})
        else:
            # Marca la entrada como rechazada
            entry.status = 'rejected'
            # Guarda la razon de rechazo (si se proporciono)
            entry.rejection_reason = serializer.validated_data.get('rejection_reason', '')
            # Guarda los cambios en la base de datos
            entry.save()
            # Retorna mensaje de exito en espanol
            return Response({'message': 'Entrada de tiempo rechazada'})


class UnbilledTimeEntriesView(generics.ListAPIView):
    """
    Vista para listar entradas de tiempo no facturadas

    Endpoint:
        GET /time-entries/unbilled/

    Muestra entradas que:
        - Son facturables (is_billable=True)
        - Estan aprobadas o enviadas
        - No tienen factura asociada

    Util para preparar facturas con tiempo pendiente.
    """

    # Serializador para la respuesta
    serializer_class = TimeEntrySerializer

    def get_queryset(self):
        """
        Construye el queryset de entradas no facturadas

        Filtra entradas que son facturables, estan aprobadas o enviadas,
        y no tienen ID de factura asignado.

        Retorna:
            QuerySet: Entradas de tiempo pendientes de facturar
        """
        # Consulta entradas facturables sin factura asociada
        queryset = TimeEntry.objects.filter(
            is_billable=True,                    # Solo entradas facturables
            status__in=['approved', 'submitted'],  # Estados validos para facturar
            invoice_id__isnull=True              # Sin factura asociada
        )

        # Filtro opcional por caso especifico
        case_id = self.request.query_params.get('case_id')
        if case_id:
            # Filtra por el caso especificado
            queryset = queryset.filter(case_id=case_id)

        return queryset


class MyTimeEntriesView(generics.ListAPIView):
    """
    Vista para listar las entradas de tiempo del usuario actual

    Endpoint:
        GET /time-entries/my/

    Muestra solo las entradas de tiempo creadas por el usuario
    autenticado, sin importar su rol.
    """

    # Serializador para la respuesta
    serializer_class = TimeEntrySerializer

    def get_queryset(self):
        """
        Obtiene las entradas de tiempo del usuario actual

        Retorna:
            QuerySet: Entradas de tiempo del usuario autenticado
        """
        # Filtra por el ID del usuario actual obtenido de la solicitud
        return TimeEntry.objects.filter(user_id=self.request.user.id)


class TimeEntrySummaryView(APIView):
    """
    Vista para obtener resumen estadistico de entradas de tiempo

    Endpoint:
        GET /time-entries/summary/

    Proporciona:
        - Total de entradas y minutos
        - Minutos facturables vs no facturables
        - Monto total
        - Desglose por tipo de actividad
        - Desglose por estado
    """

    def get(self, request):
        """
        Calcula y retorna el resumen de entradas de tiempo

        Aplica filtros de seguridad por rol y filtros opcionales
        de rango de fechas y caso.

        Args:
            request: Objeto de solicitud HTTP

        Retorna:
            Response: Datos de resumen serializados
        """
        # Obtiene el usuario autenticado
        user = request.user
        # Inicia con todas las entradas
        queryset = TimeEntry.objects.all()

        # Filtrado por rol: usuarios no admin/partner solo ven sus datos
        if user.role not in ['admin', 'partner']:
            queryset = queryset.filter(user_id=user.id)

        # Obtiene parametros de filtro de la URL
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        # Aplica filtro de fecha inicial
        if date_from:
            queryset = queryset.filter(date__gte=date_from)

        # Aplica filtro de fecha final
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        # Filtro opcional por caso
        case_id = request.query_params.get('case_id')
        if case_id:
            queryset = queryset.filter(case_id=case_id)

        # Calcula totales usando agregacion de Django
        # aggregate() retorna un diccionario con los valores calculados
        totals = queryset.aggregate(
            # Suma total de minutos
            total_minutes=Sum('duration_minutes'),
            # Suma de minutos solo de entradas facturables
            # filter=Q() permite condicionar la suma
            billable_minutes=Sum('duration_minutes', filter=Q(is_billable=True)),
            # Suma de minutos de entradas no facturables
            non_billable_minutes=Sum('duration_minutes', filter=Q(is_billable=False)),
            # Suma total de montos
            total_amount=Sum('amount')
        )

        # Calcula desglose por tipo de actividad
        # values() agrupa por el campo especificado
        # annotate() agrega calculos por grupo
        by_activity = dict(
            queryset.values('activity_type').annotate(
                minutes=Sum('duration_minutes')
            ).values_list('activity_type', 'minutes')  # Convierte a lista de tuplas
        )

        # Calcula desglose por estado
        by_status = dict(
            queryset.values('status').annotate(
                count=Count('id')  # Cuenta entradas por estado
            ).values_list('status', 'count')
        )

        # Construye el diccionario de resumen
        summary = {
            'total_entries': queryset.count(),  # Total de entradas
            'total_minutes': totals['total_minutes'] or 0,  # Minutos totales (0 si None)
            'total_hours': round((totals['total_minutes'] or 0) / 60, 2),  # Horas totales
            'billable_minutes': totals['billable_minutes'] or 0,  # Minutos facturables
            'non_billable_minutes': totals['non_billable_minutes'] or 0,  # Minutos no facturables
            'total_amount': totals['total_amount'] or 0,  # Monto total
            'by_activity_type': by_activity,  # Desglose por actividad
            'by_status': by_status,  # Desglose por estado
        }

        # Serializa y retorna el resumen
        serializer = TimeEntrySummarySerializer(summary)
        return Response(serializer.data)


# ==================== VISTAS DE TEMPORIZADORES ====================

class TimerStartView(APIView):
    """
    Vista para iniciar un nuevo temporizador

    Endpoint:
        POST /timers/start/

    Restricciones:
        - Un usuario solo puede tener un temporizador activo a la vez

    Al crear el temporizador, automaticamente obtiene la tarifa
    por hora del usuario si esta configurada.
    """

    def post(self, request):
        """
        Inicia un nuevo temporizador para el usuario

        Verifica que el usuario no tenga otro temporizador activo,
        obtiene la tarifa del usuario y crea el temporizador.

        Args:
            request: Objeto de solicitud HTTP con datos del temporizador

        Retorna:
            Response: Datos del temporizador creado o error
        """
        # Verifica si el usuario ya tiene un temporizador corriendo
        existing_timer = Timer.objects.filter(
            user_id=request.user.id,  # Del usuario actual
            is_running=True           # Que este activo
        ).first()  # Obtiene el primero (si existe)

        # Si ya existe un temporizador activo, retorna error
        if existing_timer:
            return Response(
                {
                    'error': 'Ya tienes un temporizador activo',
                    'timer': TimerSerializer(existing_timer).data  # Incluye datos del timer existente
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Valida los datos de la solicitud
        serializer = TimerStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Intenta obtener la tarifa por hora del usuario
        hourly_rate = None
        try:
            # Busca la tarifa configurada para el usuario
            user_rate = UserRate.objects.get(user_id=request.user.id)
            hourly_rate = user_rate.default_rate
        except UserRate.DoesNotExist:
            # Si no hay tarifa configurada, continua sin tarifa
            pass

        # Crea el nuevo temporizador con los datos proporcionados
        timer = Timer.objects.create(
            user_id=request.user.id,                                    # ID del usuario
            user_name=request.user.email,                               # Email como nombre
            case_id=serializer.validated_data.get('case_id'),           # Caso asociado (opcional)
            case_number=serializer.validated_data.get('case_number', ''),  # Numero de caso
            task_id=serializer.validated_data.get('task_id'),           # Tarea asociada (opcional)
            description=serializer.validated_data.get('description', ''),  # Descripcion del trabajo
            activity_type=serializer.validated_data.get('activity_type', 'other'),  # Tipo de actividad
            is_billable=serializer.validated_data.get('is_billable', True),  # Si es facturable
            hourly_rate=hourly_rate,                                    # Tarifa obtenida
        )

        # Retorna los datos del temporizador creado con estado 201 Created
        return Response(TimerSerializer(timer).data, status=status.HTTP_201_CREATED)


class TimerStopView(APIView):
    """
    Vista para detener un temporizador y crear entrada de tiempo

    Endpoints:
        POST /timers/stop/: Detiene el temporizador activo del usuario
        POST /timers/{id}/stop/: Detiene un temporizador especifico

    Comportamiento:
        - Detiene el temporizador
        - Opcionalmente crea una entrada de tiempo con el tiempo registrado
        - Elimina el temporizador despues de procesarlo
    """

    def post(self, request, id=None):
        """
        Detiene un temporizador y opcionalmente crea entrada de tiempo

        Args:
            request: Objeto de solicitud HTTP
            id: UUID del temporizador (opcional, si no se proporciona
                usa el temporizador activo del usuario)

        Retorna:
            Response: Datos del temporizador y entrada de tiempo creada
        """
        # Obtiene el temporizador segun si se proporciono ID o no
        if id:
            # Busca el temporizador especifico por ID
            try:
                timer = Timer.objects.get(id=id, user_id=request.user.id)
            except Timer.DoesNotExist:
                return Response({'error': 'Temporizador no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        else:
            # Busca el temporizador activo del usuario
            timer = Timer.objects.filter(user_id=request.user.id, is_running=True).first()
            if not timer:
                return Response({'error': 'No hay temporizador activo'}, status=status.HTTP_404_NOT_FOUND)

        # Valida los datos de la solicitud
        serializer = TimerStopSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Actualiza la descripcion si se proporciono una nueva
        if serializer.validated_data.get('description'):
            timer.description = serializer.validated_data['description']

        # Pausa el temporizador (guarda el tiempo acumulado)
        timer.pause()

        # Prepara el resultado con los datos del temporizador
        result = {'timer': TimerSerializer(timer).data}

        # Crea entrada de tiempo si se solicita (por defecto True)
        if serializer.validated_data.get('create_time_entry', True):
            # Obtiene los minutos transcurridos
            elapsed_minutes = timer.get_elapsed_minutes()

            # Solo crea entrada si hay tiempo registrado
            if elapsed_minutes > 0:
                # Crea la entrada de tiempo con los datos del temporizador
                time_entry = TimeEntry.objects.create(
                    user_id=timer.user_id,              # ID del usuario
                    user_name=timer.user_name,          # Nombre del usuario
                    case_id=timer.case_id,              # Caso asociado
                    case_number=timer.case_number,      # Numero de caso
                    task_id=timer.task_id,              # Tarea asociada
                    date=date.today(),                  # Fecha actual
                    duration_minutes=elapsed_minutes,   # Duracion del temporizador
                    description=timer.description,      # Descripcion del trabajo
                    activity_type=timer.activity_type,  # Tipo de actividad
                    is_billable=timer.is_billable,      # Si es facturable
                    hourly_rate=timer.hourly_rate,      # Tarifa por hora
                    timer_id=timer.id,                  # Referencia al temporizador origen
                )
                # Agrega los datos de la entrada de tiempo al resultado
                result['time_entry'] = TimeEntrySerializer(time_entry).data

        # Elimina el temporizador (ya no se necesita)
        timer.delete()

        # Retorna el resultado con temporizador y entrada de tiempo
        return Response(result)


class TimerPauseView(APIView):
    """
    Vista para pausar un temporizador

    Endpoint:
        POST /timers/{id}/pause/

    Pausa el temporizador especificado sin eliminarlo ni crear
    entrada de tiempo. Permite reanudar posteriormente.
    """

    def post(self, request, id):
        """
        Pausa el temporizador especificado

        Args:
            request: Objeto de solicitud HTTP
            id: UUID del temporizador a pausar

        Retorna:
            Response: Datos del temporizador pausado
        """
        # Busca el temporizador del usuario
        try:
            timer = Timer.objects.get(id=id, user_id=request.user.id)
        except Timer.DoesNotExist:
            return Response({'error': 'Temporizador no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        # Pausa el temporizador (guarda tiempo acumulado)
        timer.pause()

        # Retorna los datos actualizados del temporizador
        return Response(TimerSerializer(timer).data)


class TimerResumeView(APIView):
    """
    Vista para reanudar un temporizador pausado

    Endpoint:
        POST /timers/{id}/resume/

    Reanuda un temporizador que fue pausado previamente,
    manteniendo el tiempo acumulado.
    """

    def post(self, request, id):
        """
        Reanuda el temporizador especificado

        Args:
            request: Objeto de solicitud HTTP
            id: UUID del temporizador a reanudar

        Retorna:
            Response: Datos del temporizador reanudado
        """
        # Busca el temporizador del usuario
        try:
            timer = Timer.objects.get(id=id, user_id=request.user.id)
        except Timer.DoesNotExist:
            return Response({'error': 'Temporizador no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        # Reanuda el temporizador
        timer.resume()

        # Retorna los datos actualizados del temporizador
        return Response(TimerSerializer(timer).data)


class CurrentTimerView(APIView):
    """
    Vista para obtener el temporizador activo actual

    Endpoint:
        GET /timers/current/

    Retorna el temporizador que esta corriendo actualmente
    para el usuario autenticado.
    """

    def get(self, request):
        """
        Obtiene el temporizador activo del usuario

        Args:
            request: Objeto de solicitud HTTP

        Retorna:
            Response: Datos del temporizador activo o mensaje si no hay ninguno
        """
        # Busca temporizador activo del usuario
        timer = Timer.objects.filter(user_id=request.user.id, is_running=True).first()

        # Si existe, retorna sus datos
        if timer:
            return Response(TimerSerializer(timer).data)

        # Si no hay temporizador activo, retorna mensaje informativo
        return Response({'message': 'No hay temporizador activo'}, status=status.HTTP_404_NOT_FOUND)


class TimerListView(generics.ListAPIView):
    """
    Vista para listar todos los temporizadores del usuario

    Endpoint:
        GET /timers/

    Muestra todos los temporizadores (activos y pausados) del usuario.
    """

    # Serializador para la respuesta
    serializer_class = TimerSerializer

    def get_queryset(self):
        """
        Obtiene los temporizadores del usuario actual

        Retorna:
            QuerySet: Temporizadores del usuario autenticado
        """
        # Filtra por el usuario actual
        return Timer.objects.filter(user_id=self.request.user.id)


class TimerDeleteView(generics.DestroyAPIView):
    """
    Vista para eliminar un temporizador sin crear entrada de tiempo

    Endpoint:
        DELETE /timers/{id}/

    Elimina el temporizador especificado descartando el tiempo registrado.
    Util cuando el usuario quiere cancelar sin guardar.
    """

    # Serializador (no se usa en DELETE pero es requerido)
    serializer_class = TimerSerializer

    # Campo para buscar en la URL
    lookup_field = 'id'

    def get_queryset(self):
        """
        Limita la eliminacion a temporizadores del usuario actual

        Retorna:
            QuerySet: Temporizadores del usuario autenticado
        """
        # Solo permite eliminar temporizadores propios
        return Timer.objects.filter(user_id=self.request.user.id)


# ==================== VISTAS DE TARIFAS ====================

class UserRateView(generics.RetrieveUpdateAPIView):
    """
    Vista para ver y actualizar la tarifa de un usuario

    Endpoints:
        GET /rates/user/: Obtiene la tarifa del usuario actual
        GET /rates/user/{user_id}/: Obtiene la tarifa de un usuario especifico
        PUT/PATCH /rates/user/{user_id}/: Actualiza la tarifa de un usuario

    Si no existe tarifa para el usuario, crea una con valores predeterminados.
    """

    # Serializador para la tarifa de usuario
    serializer_class = UserRateSerializer

    # Campo para buscar en la URL
    lookup_field = 'user_id'

    def get_queryset(self):
        """
        Retorna el queryset de tarifas de usuario

        Retorna:
            QuerySet: Todas las tarifas de usuario
        """
        return UserRate.objects.all()

    def get_object(self):
        """
        Obtiene o crea la tarifa para el usuario especificado

        Si se proporciona user_id en la URL, usa ese ID.
        Si no, usa el ID del usuario actual.
        Si no existe tarifa, crea una con valores predeterminados.

        Retorna:
            UserRate: Objeto de tarifa del usuario
        """
        # Obtiene el user_id de la URL o usa el del usuario actual
        user_id = self.kwargs.get('user_id', self.request.user.id)

        # get_or_create retorna una tupla (objeto, created)
        # Si el objeto no existe, lo crea con los defaults
        obj, created = UserRate.objects.get_or_create(
            user_id=user_id,
            defaults={
                'default_rate': 0,           # Tarifa inicial de 0
                'effective_date': date.today()  # Fecha efectiva: hoy
            }
        )
        return obj


class CaseRateListCreateView(generics.ListCreateAPIView):
    """
    Vista para listar y crear tarifas especiales por caso

    Endpoints:
        GET /rates/case/{case_id}/: Lista tarifas de un caso
        POST /rates/case/{case_id}/: Crea tarifa para un caso

    Permite configurar tarifas diferentes para casos especificos,
    que tienen prioridad sobre las tarifas de usuario.
    """

    # Serializador para tarifas de caso
    serializer_class = CaseRateSerializer

    def get_queryset(self):
        """
        Obtiene las tarifas del caso especificado

        Si se proporciona case_id en la URL, filtra por ese caso.
        Si no, retorna todas las tarifas de casos.

        Retorna:
            QuerySet: Tarifas de caso filtradas
        """
        # Obtiene el case_id de los parametros de URL
        case_id = self.kwargs.get('case_id')

        if case_id:
            # Filtra por el caso especificado
            return CaseRate.objects.filter(case_id=case_id)

        # Si no hay case_id, retorna todas
        return CaseRate.objects.all()

    def perform_create(self, serializer):
        """
        Personaliza la creacion de tarifa de caso

        Si se proporciona case_id en la URL, lo usa automaticamente
        al crear la tarifa.

        Args:
            serializer: Serializador con datos validados
        """
        # Obtiene el case_id de los parametros de URL
        case_id = self.kwargs.get('case_id')

        if case_id:
            # Guarda incluyendo el case_id de la URL
            serializer.save(case_id=case_id)
        else:
            # Guarda con los datos proporcionados en el request
            serializer.save()
