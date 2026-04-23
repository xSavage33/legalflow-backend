"""
serializers.py - Serializadores del servicio de calendario

Este archivo contiene los serializadores (serializers) que convierten
objetos de modelo Django a representaciones JSON y viceversa.

Los serializadores son fundamentales en Django REST Framework para:
    - Validar datos de entrada en las solicitudes POST/PUT
    - Convertir objetos de modelo a JSON para las respuestas
    - Definir que campos se incluyen en la API
    - Aplicar transformaciones a los datos

Serializadores incluidos:
    - EventSerializer: Serializador completo para eventos (lectura)
    - EventCreateSerializer: Serializador para crear eventos
    - DeadlineSerializer: Serializador completo para plazos (lectura)
    - DeadlineCreateSerializer: Serializador para crear plazos
    - HolidayCalendarSerializer: Serializador para dias festivos
    - CalculateDeadlineSerializer: Entrada para calculo de plazos
    - DeadlineCalculationResultSerializer: Resultado del calculo de plazos

Autor: Equipo LegalFlow
Fecha de creacion: 2024
"""

# Importacion del modulo serializers de Django REST Framework
# Proporciona clases base para crear serializadores
from rest_framework import serializers

# Importacion de los modelos que seran serializados
# Event: modelo de eventos del calendario
# Deadline: modelo de plazos legales
# HolidayCalendar: modelo de dias festivos
from .models import Event, Deadline, HolidayCalendar


class EventSerializer(serializers.ModelSerializer):
    """
    Serializador completo para el modelo Event

    Este serializador se utiliza para operaciones de lectura (GET)
    e incluye todos los campos del modelo junto con campos calculados
    que muestran las etiquetas legibles de los choices.

    Campos adicionales:
        - type_display: Muestra la etiqueta del tipo de evento (ej: "Audiencia")
        - status_display: Muestra la etiqueta del estado (ej: "Programado")

    Campos de solo lectura:
        - id: Se genera automaticamente
        - created_by_id: Se asigna automaticamente al crear
        - created_by_name: Se asigna automaticamente al crear
        - created_at: Timestamp automatico
        - updated_at: Timestamp automatico
    """

    # Campo calculado para mostrar la etiqueta del tipo de evento
    # source='get_event_type_display': Llama al metodo de Django que
    # retorna la etiqueta legible del choice (ej: 'hearing' -> 'Audiencia')
    # read_only=True: Este campo solo se incluye en respuestas, no se puede escribir
    type_display = serializers.CharField(source='get_event_type_display', read_only=True)

    # Campo calculado para mostrar la etiqueta del estado
    # Usa el metodo get_status_display() generado automaticamente por Django
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        """
        Clase Meta para configuracion del serializador

        Define el modelo asociado, los campos a incluir y
        cuales campos son de solo lectura.
        """
        # Modelo que este serializador representa
        model = Event

        # Lista de todos los campos a incluir en la serializacion
        # Incluye campos del modelo y campos calculados (type_display, status_display)
        fields = [
            'id',                # Identificador unico UUID
            'title',             # Titulo del evento
            'description',       # Descripcion detallada
            'event_type',        # Tipo de evento (valor almacenado)
            'type_display',      # Tipo de evento (etiqueta legible)
            'status',            # Estado del evento (valor almacenado)
            'status_display',    # Estado del evento (etiqueta legible)
            'case_id',           # ID del caso asociado
            'case_number',       # Numero de radicado del caso
            'start_datetime',    # Fecha y hora de inicio
            'end_datetime',      # Fecha y hora de fin
            'all_day',           # Indica si es evento de todo el dia
            'location',          # Ubicacion del evento
            'attendees',         # Lista de IDs de asistentes
            'reminder_minutes',  # Minutos antes para recordatorios
            'created_by_id',     # ID del usuario creador
            'created_by_name',   # Nombre del usuario creador
            'created_at',        # Fecha de creacion
            'updated_at'         # Fecha de ultima actualizacion
        ]

        # Campos que no pueden ser modificados por el usuario
        # Estos campos se establecen automaticamente por el sistema
        read_only_fields = [
            'id',              # Generado automaticamente (UUID)
            'created_by_id',   # Asignado del usuario autenticado
            'created_by_name', # Asignado del usuario autenticado
            'created_at',      # Timestamp automatico
            'updated_at'       # Timestamp automatico
        ]


class EventCreateSerializer(serializers.ModelSerializer):
    """
    Serializador para crear nuevos eventos

    Este serializador tiene un conjunto reducido de campos que el
    usuario puede proporcionar al crear un evento. Los campos como
    created_by_id y created_by_name se asignan automaticamente
    desde el usuario autenticado.

    Se utiliza solo para operaciones POST en la creacion de eventos.
    """

    class Meta:
        """
        Clase Meta con configuracion del serializador de creacion
        """
        # Modelo asociado
        model = Event

        # Campos que el usuario puede proporcionar al crear un evento
        # No incluye campos automaticos como id, created_by_*, timestamps
        fields = [
            'title',             # Titulo del evento (requerido)
            'description',       # Descripcion (opcional)
            'event_type',        # Tipo de evento (requerido)
            'case_id',           # ID del caso (opcional)
            'case_number',       # Numero de caso (opcional)
            'start_datetime',    # Fecha/hora inicio (requerido)
            'end_datetime',      # Fecha/hora fin (opcional)
            'all_day',           # Es todo el dia (opcional, default False)
            'location',          # Ubicacion (opcional)
            'attendees',         # Lista de asistentes (opcional)
            'reminder_minutes'   # Minutos para recordatorios (opcional)
        ]

    def create(self, validated_data):
        """
        Crea un nuevo evento con datos del usuario autenticado

        Este metodo sobrescribe el metodo create() base para agregar
        automaticamente la informacion del usuario que crea el evento.

        Args:
            validated_data: Diccionario con los datos validados del evento

        Returns:
            Event: Instancia del nuevo evento creado
        """
        # Obtener el objeto request del contexto del serializador
        # El contexto se pasa automaticamente desde la vista
        request = self.context.get('request')

        # Agregar el ID del usuario autenticado como creador
        validated_data['created_by_id'] = request.user.id

        # Agregar el email del usuario como nombre del creador
        # Se usa email porque es un campo unico y siempre disponible
        validated_data['created_by_name'] = request.user.email

        # Llamar al metodo create() de la clase padre para crear el objeto
        return super().create(validated_data)


class DeadlineSerializer(serializers.ModelSerializer):
    """
    Serializador completo para el modelo Deadline

    Utilizado para operaciones de lectura (GET) de plazos.
    Incluye todos los campos del modelo mas campos calculados
    que proporcionan informacion adicional sobre el plazo.

    Campos calculados:
        - priority_display: Etiqueta de la prioridad (ej: "Alta")
        - status_display: Etiqueta del estado (ej: "Pendiente")
        - days_remaining: Dias que faltan para el vencimiento
        - is_overdue: Indica si el plazo ya vencio
    """

    # Campo calculado para la etiqueta de prioridad
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)

    # Campo calculado para la etiqueta de estado
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    # Campo de solo lectura que obtiene el valor de la propiedad days_remaining del modelo
    # ReadOnlyField: Campo que se obtiene directamente del modelo sin transformacion
    days_remaining = serializers.ReadOnlyField()

    # Campo de solo lectura que obtiene el valor de la propiedad is_overdue del modelo
    is_overdue = serializers.ReadOnlyField()

    class Meta:
        """
        Clase Meta con configuracion del serializador
        """
        # Modelo asociado
        model = Deadline

        # Lista completa de campos a incluir
        fields = [
            'id',                  # Identificador unico UUID
            'title',               # Titulo del plazo
            'description',         # Descripcion detallada
            'priority',            # Nivel de prioridad (valor)
            'priority_display',    # Nivel de prioridad (etiqueta)
            'status',              # Estado actual (valor)
            'status_display',      # Estado actual (etiqueta)
            'case_id',             # ID del caso asociado
            'case_number',         # Numero de radicado
            'due_date',            # Fecha de vencimiento actual
            'original_due_date',   # Fecha de vencimiento original
            'business_days_only',  # Solo cuenta dias habiles
            'jurisdiction',        # Jurisdiccion aplicable
            'reminder_dates',      # Fechas de recordatorio
            'assigned_to_id',      # ID del usuario asignado
            'assigned_to_name',    # Nombre del usuario asignado
            'completed_at',        # Fecha de completado
            'days_remaining',      # Dias restantes (calculado)
            'is_overdue',          # Esta vencido (calculado)
            'created_by_id',       # ID del creador
            'created_by_name',     # Nombre del creador
            'created_at',          # Fecha de creacion
            'updated_at'           # Fecha de actualizacion
        ]

        # Campos que no pueden ser modificados por el usuario
        read_only_fields = [
            'id',                  # Generado automaticamente
            'original_due_date',   # Se establece al crear
            'days_remaining',      # Calculado automaticamente
            'is_overdue',          # Calculado automaticamente
            'created_by_id',       # Asignado del usuario autenticado
            'created_by_name',     # Asignado del usuario autenticado
            'created_at',          # Timestamp automatico
            'updated_at'           # Timestamp automatico
        ]


class DeadlineCreateSerializer(serializers.ModelSerializer):
    """
    Serializador para crear nuevos plazos

    Contiene el subconjunto de campos que el usuario puede
    proporcionar al crear un plazo. Los campos automaticos
    como created_by_* y original_due_date se establecen
    automaticamente.
    """

    class Meta:
        """
        Clase Meta con configuracion del serializador
        """
        # Modelo asociado
        model = Deadline

        # Campos que el usuario puede proporcionar
        fields = [
            'title',               # Titulo del plazo (requerido)
            'description',         # Descripcion (opcional)
            'priority',            # Prioridad (opcional, default 'medium')
            'case_id',             # ID del caso (opcional)
            'case_number',         # Numero de caso (opcional)
            'due_date',            # Fecha de vencimiento (requerido)
            'business_days_only',  # Solo dias habiles (opcional, default True)
            'jurisdiction',        # Jurisdiccion (opcional)
            'reminder_dates',      # Fechas de recordatorio (opcional)
            'assigned_to_id',      # ID del asignado (opcional)
            'assigned_to_name'     # Nombre del asignado (opcional)
        ]

    def create(self, validated_data):
        """
        Crea un nuevo plazo con datos del usuario y fecha original

        Ademas de agregar la informacion del usuario creador,
        este metodo tambien guarda la fecha de vencimiento original
        para mantener un historico en caso de extensiones.

        Args:
            validated_data: Diccionario con los datos validados

        Returns:
            Deadline: Instancia del nuevo plazo creado
        """
        # Obtener el request del contexto
        request = self.context.get('request')

        # Agregar informacion del usuario creador
        validated_data['created_by_id'] = request.user.id
        validated_data['created_by_name'] = request.user.email

        # Guardar la fecha de vencimiento original
        # Esto permite rastrear si el plazo fue extendido posteriormente
        validated_data['original_due_date'] = validated_data['due_date']

        # Crear y retornar el plazo usando el metodo padre
        return super().create(validated_data)


class HolidayCalendarSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo HolidayCalendar

    Maneja la serializacion de dias festivos para operaciones
    de lectura (GET) y escritura (POST/PUT).

    Se utiliza tanto para listar festivos como para crearlos
    y actualizarlos.
    """

    class Meta:
        """
        Clase Meta con configuracion del serializador
        """
        # Modelo asociado
        model = HolidayCalendar

        # Campos a incluir en la serializacion
        fields = [
            'id',           # Identificador unico UUID
            'name',         # Nombre del festivo
            'date',         # Fecha del festivo
            'jurisdiction', # Jurisdiccion donde aplica
            'is_national',  # Es festivo nacional
            'year',         # Anio del festivo
            'created_at'    # Fecha de creacion del registro
        ]

        # Campos de solo lectura
        read_only_fields = [
            'id',          # Generado automaticamente
            'created_at'   # Timestamp automatico
        ]


class CalculateDeadlineSerializer(serializers.Serializer):
    """
    Serializador para entrada de calculo de plazos

    Este es un serializador NO vinculado a un modelo (Serializer en lugar
    de ModelSerializer). Se utiliza para validar los datos de entrada
    cuando se calcula una fecha de vencimiento basada en dias habiles.

    No crea ni actualiza objetos en la base de datos, solo valida
    los datos de entrada.

    Campos:
        - start_date: Fecha desde la cual comenzar a contar
        - business_days: Numero de dias habiles a agregar
        - jurisdiction: Jurisdiccion para considerar festivos locales
    """

    # Campo fecha de inicio (obligatorio)
    # DateField: Valida que el valor sea una fecha valida
    start_date = serializers.DateField()

    # Campo dias habiles (obligatorio)
    # IntegerField: Valida que sea un entero
    # min_value=1: Debe ser al menos 1 dia
    business_days = serializers.IntegerField(min_value=1)

    # Campo jurisdiccion (opcional)
    # required=False: No es obligatorio proporcionarlo
    # allow_blank=True: Permite cadenas vacias
    jurisdiction = serializers.CharField(required=False, allow_blank=True)


class DeadlineCalculationResultSerializer(serializers.Serializer):
    """
    Serializador para el resultado del calculo de plazos

    Este serializador formatea la respuesta del calculo de
    fecha de vencimiento. No esta vinculado a un modelo,
    solo estructura los datos de salida.

    Campos de salida:
        - start_date: Fecha de inicio proporcionada
        - business_days: Numero de dias habiles solicitados
        - due_date: Fecha de vencimiento calculada
        - jurisdiction: Jurisdiccion utilizada en el calculo
    """

    # Campo fecha de inicio (refleja el valor de entrada)
    start_date = serializers.DateField()

    # Campo dias habiles (refleja el valor de entrada)
    business_days = serializers.IntegerField()

    # Campo fecha de vencimiento (resultado del calculo)
    due_date = serializers.DateField()

    # Campo jurisdiccion (refleja el valor de entrada o default)
    jurisdiction = serializers.CharField()
