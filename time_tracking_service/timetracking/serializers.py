"""
Modulo de Serializadores del Servicio de Control de Tiempo (Time Tracking Service)

Este archivo contiene los serializadores de Django REST Framework que transforman
los modelos de Python a formatos JSON y viceversa. Los serializadores definen
que campos se incluyen en las respuestas de la API y validan los datos de entrada.

Serializadores incluidos:
- TimeEntrySerializer: Serializador completo para lectura de entradas de tiempo
- TimeEntryCreateSerializer: Serializador para crear nuevas entradas
- TimeEntryUpdateSerializer: Serializador para actualizar entradas existentes
- TimeEntryApprovalSerializer: Serializador para acciones de aprobacion/rechazo
- TimerSerializer: Serializador completo para temporizadores
- TimerStartSerializer: Serializador para iniciar temporizadores
- TimerStopSerializer: Serializador para detener temporizadores
- UserRateSerializer: Serializador para tarifas de usuario
- CaseRateSerializer: Serializador para tarifas de caso
- TimeEntrySummarySerializer: Serializador para resumen estadistico

Autor: LegalFlow Team
Fecha: 2024
"""

# Importa el modulo serializers de Django REST Framework
# Proporciona clases base para crear serializadores
from rest_framework import serializers

# Importa timezone para manejar fechas y horas con zona horaria
from django.utils import timezone

# Importa los modelos que seran serializados
from .models import TimeEntry, Timer, UserRate, CaseRate


class TimeEntrySerializer(serializers.ModelSerializer):
    """
    Serializador completo de Entrada de Tiempo para operaciones de lectura

    Incluye todos los campos del modelo TimeEntry mas campos calculados
    adicionales como la duracion en horas y las etiquetas legibles de
    estado y tipo de actividad.

    Campos adicionales:
        - duration_hours: Duracion convertida a horas (propiedad del modelo)
        - status_display: Etiqueta legible del estado (ej: "Aprobado")
        - activity_type_display: Etiqueta legible del tipo de actividad
    """

    # Campo de solo lectura que obtiene la propiedad duration_hours del modelo
    # ReadOnlyField indica que este campo no se puede escribir, solo leer
    duration_hours = serializers.ReadOnlyField()

    # Campo que obtiene la etiqueta legible del estado usando get_status_display()
    # source='get_status_display' indica que el valor viene de ese metodo del modelo
    # read_only=True indica que no se puede escribir
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    # Campo que obtiene la etiqueta legible del tipo de actividad
    # Django crea automaticamente get_FOO_display() para campos con choices
    activity_type_display = serializers.CharField(source='get_activity_type_display', read_only=True)

    class Meta:
        """
        Clase Meta que configura el serializador

        Define el modelo asociado, los campos a incluir y cuales
        son de solo lectura.
        """
        # Modelo que este serializador representa
        model = TimeEntry

        # Lista de todos los campos a incluir en la serializacion
        # Incluye campos del modelo y campos adicionales definidos arriba
        fields = [
            'id',                      # UUID de la entrada
            'user_id',                 # ID del usuario
            'user_name',               # Nombre del usuario
            'case_id',                 # ID del caso
            'case_number',             # Numero de caso legible
            'task_id',                 # ID de tarea asociada
            'date',                    # Fecha del trabajo
            'duration_minutes',        # Duracion en minutos
            'duration_hours',          # Duracion en horas (calculado)
            'description',             # Descripcion del trabajo
            'activity_type',           # Tipo de actividad (valor interno)
            'activity_type_display',   # Tipo de actividad (etiqueta legible)
            'is_billable',             # Si es facturable
            'hourly_rate',             # Tarifa por hora
            'amount',                  # Monto total calculado
            'status',                  # Estado (valor interno)
            'status_display',          # Estado (etiqueta legible)
            'invoice_id',              # ID de factura asociada
            'approved_by_id',          # ID de quien aprobo
            'approved_by_name',        # Nombre de quien aprobo
            'approved_at',             # Fecha de aprobacion
            'rejection_reason',        # Razon de rechazo
            'timer_id',                # ID del temporizador origen
            'notes',                   # Notas adicionales
            'created_at',              # Fecha de creacion
            'updated_at'               # Fecha de actualizacion
        ]

        # Campos que no se pueden modificar (solo lectura)
        # Estos campos son establecidos por el sistema, no por el usuario
        read_only_fields = [
            'id',               # Generado automaticamente
            'user_id',          # Establecido desde el request
            'user_name',        # Establecido desde el request
            'amount',           # Calculado automaticamente
            'invoice_id',       # Establecido por el sistema de facturacion
            'approved_by_id',   # Establecido al aprobar
            'approved_by_name', # Establecido al aprobar
            'approved_at',      # Establecido al aprobar
            'created_at',       # Establecido automaticamente
            'updated_at'        # Actualizado automaticamente
        ]


class TimeEntryCreateSerializer(serializers.ModelSerializer):
    """
    Serializador para crear nuevas entradas de tiempo

    Incluye solo los campos que el usuario debe proporcionar al crear
    una entrada. Los campos como user_id y user_name se obtienen
    automaticamente del usuario autenticado.

    Funcionalidad adicional:
        - Asigna automaticamente user_id y user_name del request
        - Obtiene la tarifa por defecto del usuario si no se proporciona
    """

    class Meta:
        """
        Configuracion del serializador de creacion
        """
        # Modelo asociado
        model = TimeEntry

        # Solo campos necesarios para crear una entrada
        # No incluye user_id, user_name, amount, etc. que son automaticos
        fields = [
            'case_id',           # Caso asociado (opcional)
            'case_number',       # Numero de caso (opcional)
            'task_id',           # Tarea asociada (opcional)
            'date',              # Fecha del trabajo (requerido)
            'duration_minutes',  # Duracion en minutos (requerido)
            'description',       # Descripcion del trabajo (requerido)
            'activity_type',     # Tipo de actividad (opcional, default='other')
            'is_billable',       # Si es facturable (opcional, default=True)
            'hourly_rate',       # Tarifa por hora (opcional)
            'notes'              # Notas adicionales (opcional)
        ]

    def create(self, validated_data):
        """
        Crea una nueva entrada de tiempo con datos adicionales del request

        Este metodo sobrescribe el create() por defecto para:
        1. Agregar user_id y user_name desde el usuario autenticado
        2. Obtener la tarifa por defecto del usuario si no se proporciono

        Args:
            validated_data: Diccionario con los datos ya validados

        Retorna:
            TimeEntry: Nueva instancia de TimeEntry creada
        """
        # Obtiene el objeto request desde el contexto del serializador
        # El contexto se pasa automaticamente por DRF cuando se usa en una vista
        request = self.context.get('request')

        # Agrega el ID del usuario autenticado a los datos
        validated_data['user_id'] = request.user.id

        # Agrega el email del usuario como nombre
        validated_data['user_name'] = request.user.email

        # Si la entrada es facturable pero no tiene tarifa, busca la tarifa del usuario
        if validated_data.get('is_billable') and not validated_data.get('hourly_rate'):
            try:
                # Intenta obtener la tarifa configurada para el usuario
                user_rate = UserRate.objects.get(user_id=request.user.id)
                # Asigna la tarifa por defecto del usuario
                validated_data['hourly_rate'] = user_rate.default_rate
            except UserRate.DoesNotExist:
                # Si no hay tarifa configurada, continua sin ella
                pass

        # Llama al metodo create() del padre para crear el objeto
        return super().create(validated_data)


class TimeEntryUpdateSerializer(serializers.ModelSerializer):
    """
    Serializador para actualizar entradas de tiempo existentes

    Incluye los mismos campos que el serializador de creacion,
    pero no tiene logica personalizada ya que el usuario y otros
    campos automaticos ya estan establecidos.
    """

    class Meta:
        """
        Configuracion del serializador de actualizacion
        """
        # Modelo asociado
        model = TimeEntry

        # Campos que se pueden actualizar
        # Similares a los de creacion
        fields = [
            'case_id',           # Puede cambiar el caso asociado
            'case_number',       # Puede cambiar el numero de caso
            'task_id',           # Puede cambiar la tarea asociada
            'date',              # Puede cambiar la fecha
            'duration_minutes',  # Puede cambiar la duracion
            'description',       # Puede cambiar la descripcion
            'activity_type',     # Puede cambiar el tipo de actividad
            'is_billable',       # Puede cambiar si es facturable
            'hourly_rate',       # Puede cambiar la tarifa
            'notes'              # Puede cambiar las notas
        ]


class TimeEntryApprovalSerializer(serializers.Serializer):
    """
    Serializador para acciones de aprobacion o rechazo de entradas

    Este serializador no esta asociado a un modelo (no usa ModelSerializer)
    porque solo valida datos de una accion, no crea ni actualiza objetos.

    Campos:
        - action: Accion a realizar ('approve' o 'reject')
        - rejection_reason: Razon de rechazo (opcional, solo para 'reject')
    """

    # Campo para la accion, limitado a las opciones validas
    # ChoiceField valida que el valor sea una de las opciones permitidas
    action = serializers.ChoiceField(choices=['approve', 'reject'])

    # Campo para la razon de rechazo
    # required=False: No es obligatorio
    # allow_blank=True: Permite cadena vacia
    rejection_reason = serializers.CharField(required=False, allow_blank=True)


class TimerSerializer(serializers.ModelSerializer):
    """
    Serializador completo de Temporizador para operaciones de lectura

    Incluye todos los campos del modelo Timer mas campos calculados
    adicionales para mostrar el tiempo transcurrido.

    Campos adicionales:
        - elapsed_seconds: Tiempo transcurrido en segundos (calculado en tiempo real)
        - elapsed_minutes: Tiempo transcurrido en minutos (calculado en tiempo real)
    """

    # Campo calculado usando un metodo del serializador
    # SerializerMethodField llama a get_elapsed_seconds() para obtener el valor
    elapsed_seconds = serializers.SerializerMethodField()

    # Campo calculado para tiempo en minutos
    elapsed_minutes = serializers.SerializerMethodField()

    class Meta:
        """
        Configuracion del serializador de temporizador
        """
        # Modelo asociado
        model = Timer

        # Lista de todos los campos a incluir
        fields = [
            'id',                  # UUID del temporizador
            'user_id',             # ID del usuario propietario
            'user_name',           # Nombre del usuario
            'case_id',             # ID del caso asociado
            'case_number',         # Numero de caso legible
            'task_id',             # ID de tarea asociada
            'description',         # Descripcion del trabajo
            'activity_type',       # Tipo de actividad
            'is_running',          # Si el temporizador esta activo
            'start_time',          # Hora de inicio del periodo actual
            'stop_time',           # Hora de parada (si pausado)
            'accumulated_seconds', # Segundos acumulados de periodos anteriores
            'elapsed_seconds',     # Tiempo total transcurrido en segundos
            'elapsed_minutes',     # Tiempo total transcurrido en minutos
            'is_billable',         # Si el tiempo sera facturable
            'hourly_rate',         # Tarifa por hora
            'created_at',          # Fecha de creacion
            'updated_at'           # Fecha de actualizacion
        ]

        # Campos que no se pueden modificar
        read_only_fields = [
            'id',                  # Generado automaticamente
            'user_id',             # Establecido al crear
            'user_name',           # Establecido al crear
            'start_time',          # Gestionado por el modelo
            'stop_time',           # Gestionado por el modelo
            'accumulated_seconds', # Calculado por el modelo
            'created_at',          # Establecido automaticamente
            'updated_at'           # Actualizado automaticamente
        ]

    def get_elapsed_seconds(self, obj):
        """
        Calcula el tiempo transcurrido en segundos

        Este metodo es llamado automaticamente por SerializerMethodField
        para obtener el valor del campo elapsed_seconds.

        Args:
            obj: Instancia de Timer que se esta serializando

        Retorna:
            int: Tiempo transcurrido en segundos
        """
        # Llama al metodo del modelo que calcula el tiempo
        return obj.get_elapsed_time()

    def get_elapsed_minutes(self, obj):
        """
        Calcula el tiempo transcurrido en minutos

        Args:
            obj: Instancia de Timer que se esta serializando

        Retorna:
            int: Tiempo transcurrido en minutos (redondeado)
        """
        # Llama al metodo del modelo que calcula los minutos
        return obj.get_elapsed_minutes()


class TimerStartSerializer(serializers.Serializer):
    """
    Serializador para iniciar un nuevo temporizador

    Define los campos opcionales que se pueden proporcionar al
    iniciar un temporizador. Todos los campos son opcionales
    porque se pueden agregar o modificar mas tarde.
    """

    # ID del caso asociado (opcional)
    # UUIDField valida que sea un UUID valido
    # allow_null=True: Permite valor null
    case_id = serializers.UUIDField(required=False, allow_null=True)

    # Numero de caso legible (opcional)
    # allow_blank=True: Permite cadena vacia
    case_number = serializers.CharField(required=False, allow_blank=True)

    # ID de la tarea asociada (opcional)
    task_id = serializers.UUIDField(required=False, allow_null=True)

    # Descripcion del trabajo a realizar (opcional)
    description = serializers.CharField(required=False, allow_blank=True)

    # Tipo de actividad (opcional con valor por defecto)
    # ChoiceField valida que sea una opcion valida de ACTIVITY_TYPE_CHOICES
    activity_type = serializers.ChoiceField(
        choices=TimeEntry.ACTIVITY_TYPE_CHOICES,  # Opciones del modelo
        required=False,                           # No es obligatorio
        default='other'                           # Valor por defecto
    )

    # Si el tiempo sera facturable (opcional con valor por defecto)
    is_billable = serializers.BooleanField(required=False, default=True)


class TimerStopSerializer(serializers.Serializer):
    """
    Serializador para detener un temporizador

    Define los campos opcionales que se pueden proporcionar al
    detener un temporizador, como actualizar la descripcion o
    elegir si crear una entrada de tiempo.
    """

    # Descripcion actualizada (opcional)
    # Permite proporcionar o actualizar la descripcion al detener
    description = serializers.CharField(required=False, allow_blank=True)

    # Si se debe crear una entrada de tiempo con el tiempo registrado
    # default=True: Por defecto, siempre crea entrada de tiempo
    create_time_entry = serializers.BooleanField(default=True)


class UserRateSerializer(serializers.ModelSerializer):
    """
    Serializador para tarifas de usuario

    Permite ver y actualizar la tarifa por hora predeterminada
    de un usuario.
    """

    class Meta:
        """
        Configuracion del serializador de tarifa de usuario
        """
        # Modelo asociado
        model = UserRate

        # Campos incluidos en la serializacion
        fields = [
            'id',              # UUID de la tarifa
            'user_id',         # ID del usuario
            'default_rate',    # Tarifa por hora predeterminada
            'currency',        # Moneda (COP por defecto)
            'effective_date',  # Fecha desde la cual aplica
            'created_at',      # Fecha de creacion
            'updated_at'       # Fecha de actualizacion
        ]

        # Campos de solo lectura
        read_only_fields = [
            'id',          # Generado automaticamente
            'created_at',  # Establecido automaticamente
            'updated_at'   # Actualizado automaticamente
        ]


class CaseRateSerializer(serializers.ModelSerializer):
    """
    Serializador para tarifas especiales por caso

    Permite ver y gestionar tarifas especiales que aplican
    a casos especificos, con prioridad sobre tarifas de usuario.
    """

    class Meta:
        """
        Configuracion del serializador de tarifa de caso
        """
        # Modelo asociado
        model = CaseRate

        # Campos incluidos en la serializacion
        fields = [
            'id',          # UUID de la tarifa
            'case_id',     # ID del caso
            'user_id',     # ID del usuario (opcional, None aplica a todos)
            'rate',        # Tarifa por hora especial
            'currency',    # Moneda
            'notes',       # Notas explicativas
            'created_at',  # Fecha de creacion
            'updated_at'   # Fecha de actualizacion
        ]

        # Campos de solo lectura
        read_only_fields = [
            'id',          # Generado automaticamente
            'created_at',  # Establecido automaticamente
            'updated_at'   # Actualizado automaticamente
        ]


class TimeEntrySummarySerializer(serializers.Serializer):
    """
    Serializador para resumen estadistico de entradas de tiempo

    Este serializador no esta asociado a un modelo porque representa
    datos agregados y calculados, no un objeto de base de datos.

    Campos:
        - total_entries: Numero total de entradas
        - total_minutes: Suma de minutos de todas las entradas
        - total_hours: Total convertido a horas
        - billable_minutes: Minutos de entradas facturables
        - non_billable_minutes: Minutos de entradas no facturables
        - total_amount: Suma de todos los montos
        - by_activity_type: Diccionario con minutos por tipo de actividad
        - by_status: Diccionario con conteo por estado
    """

    # Numero total de entradas de tiempo
    total_entries = serializers.IntegerField()

    # Total de minutos sumados de todas las entradas
    total_minutes = serializers.IntegerField()

    # Total de horas (minutos / 60)
    # FloatField permite decimales
    total_hours = serializers.FloatField()

    # Minutos de entradas marcadas como facturables
    billable_minutes = serializers.IntegerField()

    # Minutos de entradas marcadas como no facturables
    non_billable_minutes = serializers.IntegerField()

    # Suma total de montos facturables
    # DecimalField para precision monetaria
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)

    # Diccionario con desglose de minutos por tipo de actividad
    # DictField permite cualquier estructura de diccionario
    # Ejemplo: {'research': 120, 'meeting': 60}
    by_activity_type = serializers.DictField()

    # Diccionario con conteo de entradas por estado
    # Ejemplo: {'draft': 5, 'approved': 10, 'billed': 3}
    by_status = serializers.DictField()
