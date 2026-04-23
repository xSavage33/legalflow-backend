"""
Modulo de Serializadores del Servicio de Casos Legales (Matter Service)

Este archivo contiene todos los serializadores utilizados para convertir
objetos de modelos Django a formato JSON y viceversa. Los serializadores
tambien manejan la validacion de datos de entrada.

Serializadores incluidos:
- CasePartySerializer: Para partes involucradas en un caso
- CaseDateSerializer: Para fechas importantes del caso
- CaseNoteSerializer: Para notas internas del caso
- CaseTaskSerializer: Para tareas asociadas al caso
- CaseListSerializer: Para listado de casos (datos minimos)
- CaseDetailSerializer: Para vista detallada de caso (datos completos)
- CaseCreateSerializer: Para creacion de nuevos casos
- CaseUpdateSerializer: Para actualizacion de casos existentes
- CaseStatisticsSerializer: Para estadisticas agregadas

Los serializadores utilizan Django REST Framework (DRF) que proporciona
una abstraccion poderosa para la serializacion/deserializacion de datos.

Autor: Equipo de Desarrollo LegalFlow
"""

# Importacion del modulo de serializadores de Django REST Framework
# Este modulo proporciona las clases base para crear serializadores
from rest_framework import serializers

# Importacion de todos los modelos de la aplicacion
# Cada serializador esta asociado a uno o mas modelos
from .models import Case, CaseParty, CaseDate, CaseNote, CaseTask


class CasePartySerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo CaseParty (Partes del Caso).

    Este serializador maneja la conversion de objetos CaseParty a JSON
    y viceversa. Se utiliza para listar, crear, actualizar y eliminar
    partes involucradas en un caso.

    Campos incluidos:
    - id: Identificador unico (solo lectura)
    - party_type: Tipo de parte (demandante, demandado, etc.)
    - name: Nombre de la parte
    - identification: Documento de identidad
    - email: Correo electronico
    - phone: Telefono
    - address: Direccion
    - company: Empresa
    - notes: Notas adicionales
    - created_at: Fecha de creacion (solo lectura)
    - updated_at: Fecha de actualizacion (solo lectura)
    """

    class Meta:
        """
        Clase Meta que configura el serializador.

        Atributos:
            model: Modelo Django asociado al serializador
            fields: Lista de campos a incluir en la serializacion
            read_only_fields: Campos que no se pueden modificar via API
        """
        # Modelo asociado a este serializador
        model = CaseParty

        # Lista explicita de campos a incluir en la serializacion
        # Esto es mas seguro que usar '__all__' ya que controla exactamente que se expone
        fields = [
            'id',              # Identificador unico UUID
            'party_type',      # Tipo de parte (plaintiff, defendant, etc.)
            'name',            # Nombre completo
            'identification',  # Numero de documento
            'email',           # Correo electronico
            'phone',           # Telefono de contacto
            'address',         # Direccion fisica
            'company',         # Empresa asociada
            'notes',           # Notas adicionales
            'created_at',      # Fecha de creacion
            'updated_at'       # Fecha de ultima modificacion
        ]

        # Campos de solo lectura - no se pueden establecer via API
        # Estos campos son generados automaticamente por el sistema
        read_only_fields = ['id', 'created_at', 'updated_at']


class CaseDateSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo CaseDate (Fechas del Caso).

    Maneja eventos y fechas importantes como audiencias, plazos,
    juicios, reuniones, etc.

    Campos incluidos:
    - id: Identificador unico (solo lectura)
    - date_type: Tipo de fecha (audiencia, plazo, juicio, etc.)
    - title: Titulo del evento
    - description: Descripcion detallada
    - date: Fecha del evento
    - time: Hora del evento
    - location: Ubicacion
    - is_completed: Estado de completado
    - reminder_sent: Indicador de recordatorio (solo lectura)
    - created_at: Fecha de creacion (solo lectura)
    - updated_at: Fecha de actualizacion (solo lectura)
    """

    class Meta:
        """
        Configuracion del serializador de fechas.
        """
        # Modelo asociado
        model = CaseDate

        # Campos incluidos en la serializacion
        fields = [
            'id',             # Identificador unico
            'date_type',      # Tipo de evento (hearing, deadline, etc.)
            'title',          # Titulo descriptivo
            'description',    # Descripcion detallada
            'date',           # Fecha del evento
            'time',           # Hora del evento (opcional)
            'location',       # Ubicacion del evento
            'is_completed',   # Si el evento ya se completo
            'reminder_sent',  # Si se envio recordatorio
            'created_at',     # Fecha de creacion
            'updated_at'      # Fecha de modificacion
        ]

        # Campos de solo lectura
        # reminder_sent es controlado por el sistema de notificaciones
        read_only_fields = ['id', 'created_at', 'updated_at', 'reminder_sent']


class CaseNoteSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo CaseNote (Notas del Caso).

    Maneja notas internas y comentarios sobre un caso.
    Las notas pueden ser publicas o privadas.

    Campos incluidos:
    - id: Identificador unico (solo lectura)
    - author_id: ID del autor (solo lectura, se asigna automaticamente)
    - author_name: Nombre del autor (solo lectura)
    - content: Contenido de la nota
    - is_private: Si la nota es privada
    - created_at: Fecha de creacion (solo lectura)
    - updated_at: Fecha de actualizacion (solo lectura)
    """

    class Meta:
        """
        Configuracion del serializador de notas.
        """
        # Modelo asociado
        model = CaseNote

        # Campos incluidos en la serializacion
        fields = [
            'id',           # Identificador unico
            'author_id',    # ID del autor (referencia al servicio IAM)
            'author_name',  # Nombre del autor
            'content',      # Contenido de la nota
            'is_private',   # Indicador de privacidad
            'created_at',   # Fecha de creacion
            'updated_at'    # Fecha de modificacion
        ]

        # Campos de solo lectura
        # author_id y author_name se asignan automaticamente en la vista
        read_only_fields = ['id', 'author_id', 'author_name', 'created_at', 'updated_at']


class CaseTaskSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo CaseTask (Tareas del Caso).

    Maneja tareas asociadas a un caso, incluyendo asignacion,
    estado, prioridad y fechas de vencimiento.

    Campos incluidos:
    - id: Identificador unico (solo lectura)
    - title: Titulo de la tarea
    - description: Descripcion detallada
    - status: Estado (pendiente, en progreso, completada, cancelada)
    - priority: Prioridad (baja, media, alta, urgente)
    - assigned_to_id: ID del usuario asignado
    - assigned_to_name: Nombre del usuario asignado
    - due_date: Fecha de vencimiento
    - completed_at: Fecha de completado (solo lectura)
    - created_by_id: ID del creador (solo lectura)
    - created_at: Fecha de creacion (solo lectura)
    - updated_at: Fecha de actualizacion (solo lectura)
    """

    class Meta:
        """
        Configuracion del serializador de tareas.
        """
        # Modelo asociado
        model = CaseTask

        # Campos incluidos en la serializacion
        fields = [
            'id',               # Identificador unico
            'title',            # Titulo de la tarea
            'description',      # Descripcion detallada
            'status',           # Estado de la tarea
            'priority',         # Prioridad de la tarea
            'assigned_to_id',   # ID del usuario asignado
            'assigned_to_name', # Nombre del usuario asignado
            'due_date',         # Fecha de vencimiento
            'completed_at',     # Fecha y hora de completado
            'created_by_id',    # ID del usuario que creo la tarea
            'created_at',       # Fecha de creacion
            'updated_at'        # Fecha de modificacion
        ]

        # Campos de solo lectura
        # completed_at se establece automaticamente cuando el estado cambia a 'completed'
        # created_by_id se asigna automaticamente al crear la tarea
        read_only_fields = ['id', 'created_by_id', 'created_at', 'updated_at', 'completed_at']


class CaseListSerializer(serializers.ModelSerializer):
    """
    Serializador para vista de lista de casos (datos minimos).

    Este serializador se utiliza cuando se listan multiples casos.
    Incluye solo los campos esenciales para mostrar en una tabla
    o lista, mejorando el rendimiento al reducir la cantidad de
    datos transferidos.

    Campos incluidos:
    - Informacion basica del caso
    - Conteos calculados (partes, tareas pendientes)

    Campos calculados:
    - party_count: Numero de partes involucradas
    - task_count: Numero de tareas pendientes/en progreso
    """

    # Campo calculado para contar las partes del caso
    # SerializerMethodField permite definir un metodo personalizado para calcular el valor
    party_count = serializers.SerializerMethodField()

    # Campo calculado para contar las tareas activas del caso
    task_count = serializers.SerializerMethodField()

    class Meta:
        """
        Configuracion del serializador de lista de casos.
        """
        # Modelo asociado
        model = Case

        # Campos incluidos - solo los esenciales para una vista de lista
        fields = [
            'id',               # Identificador unico
            'case_number',      # Numero de caso (ej: LF-2024-00001)
            'title',            # Titulo del caso
            'case_type',        # Tipo de caso (civil, penal, etc.)
            'status',           # Estado del caso
            'priority',         # Prioridad del caso
            'client_name',      # Nombre del cliente
            'lead_attorney_id', # ID del abogado principal
            'opened_date',      # Fecha de apertura
            'party_count',      # Numero de partes (campo calculado)
            'task_count',       # Numero de tareas activas (campo calculado)
            'created_at'        # Fecha de creacion
        ]

    def get_party_count(self, obj):
        """
        Calcula el numero de partes involucradas en el caso.

        Este metodo es llamado automaticamente por el SerializerMethodField
        para cada objeto Case serializado.

        Args:
            obj: Instancia del modelo Case

        Returns:
            int: Numero total de partes en el caso
        """
        # Usar la relacion 'parties' definida en el modelo para contar
        return obj.parties.count()

    def get_task_count(self, obj):
        """
        Calcula el numero de tareas pendientes o en progreso.

        Solo cuenta las tareas que estan activas (pendiente o en progreso),
        excluyendo las completadas y canceladas.

        Args:
            obj: Instancia del modelo Case

        Returns:
            int: Numero de tareas activas en el caso
        """
        # Filtrar tareas por estado y contar
        # status__in permite filtrar por multiples valores
        return obj.tasks.filter(status__in=['pending', 'in_progress']).count()


class CaseDetailSerializer(serializers.ModelSerializer):
    """
    Serializador para vista detallada de caso (datos completos).

    Este serializador se utiliza cuando se consulta un caso individual.
    Incluye toda la informacion del caso mas los objetos relacionados
    (partes, fechas, notas y tareas) anidados.

    Relaciones anidadas:
    - parties: Lista de partes involucradas
    - dates: Lista de fechas importantes
    - case_notes: Lista de notas del caso
    - tasks: Lista de tareas del caso
    """

    # Serializador anidado para las partes del caso
    # many=True indica que es una relacion uno-a-muchos
    # read_only=True indica que estos datos son solo de lectura
    parties = CasePartySerializer(many=True, read_only=True)

    # Serializador anidado para las fechas del caso
    dates = CaseDateSerializer(many=True, read_only=True)

    # Serializador anidado para las notas del caso
    case_notes = CaseNoteSerializer(many=True, read_only=True)

    # Serializador anidado para las tareas del caso
    tasks = CaseTaskSerializer(many=True, read_only=True)

    class Meta:
        """
        Configuracion del serializador de detalle de caso.
        """
        # Modelo asociado
        model = Case

        # Lista completa de campos incluyendo relaciones anidadas
        fields = [
            # Identificacion del caso
            'id',                     # UUID del caso
            'case_number',            # Numero de caso
            'title',                  # Titulo
            'description',            # Descripcion detallada

            # Clasificacion
            'case_type',              # Tipo de caso
            'status',                 # Estado actual
            'priority',               # Prioridad

            # Informacion del cliente
            'client_id',              # ID del cliente
            'client_name',            # Nombre del cliente
            'client_email',           # Email del cliente
            'client_phone',           # Telefono del cliente

            # Informacion del tribunal
            'jurisdiction',           # Jurisdiccion
            'court',                  # Tribunal
            'judge',                  # Juez asignado
            'court_case_number',      # Numero de expediente judicial

            # Abogados
            'lead_attorney_id',       # Abogado principal
            'assigned_attorneys',     # Lista de abogados asignados

            # Informacion financiera
            'billing_type',           # Tipo de facturacion
            'estimated_value',        # Valor estimado
            'retainer_amount',        # Monto de anticipo

            # Fechas importantes
            'opened_date',            # Fecha de apertura
            'closed_date',            # Fecha de cierre
            'statute_of_limitations', # Fecha de prescripcion

            # Metadatos
            'tags',                   # Etiquetas
            'notes',                  # Notas generales
            'created_by_id',          # ID del creador
            'created_at',             # Fecha de creacion
            'updated_at',             # Fecha de actualizacion

            # Relaciones anidadas
            'parties',                # Partes involucradas
            'dates',                  # Fechas del caso
            'case_notes',             # Notas del caso
            'tasks'                   # Tareas del caso
        ]

        # Campos de solo lectura - generados automaticamente
        read_only_fields = ['id', 'case_number', 'created_by_id', 'created_at', 'updated_at']


class CaseCreateSerializer(serializers.ModelSerializer):
    """
    Serializador para crear nuevos casos.

    Este serializador define los campos que se pueden establecer
    al crear un nuevo caso. Excluye campos automaticos como
    case_number (generado automaticamente) y created_by_id
    (establecido desde el usuario autenticado).

    El metodo create() personalizado asigna automaticamente
    el ID del usuario que crea el caso.
    """

    class Meta:
        """
        Configuracion del serializador de creacion de casos.
        """
        # Modelo asociado
        model = Case

        # Campos que se pueden establecer al crear un caso
        # Nota: case_number y created_by_id no estan incluidos
        # porque se generan automaticamente
        fields = [
            # Informacion basica
            'title',                  # Titulo del caso (requerido)
            'description',            # Descripcion (opcional)
            'case_type',              # Tipo de caso (requerido)
            'status',                 # Estado inicial
            'priority',               # Prioridad inicial

            # Informacion del cliente
            'client_id',              # ID del cliente (requerido)
            'client_name',            # Nombre del cliente (requerido)
            'client_email',           # Email del cliente
            'client_phone',           # Telefono del cliente

            # Informacion del tribunal
            'jurisdiction',           # Jurisdiccion
            'court',                  # Tribunal
            'judge',                  # Juez
            'court_case_number',      # Numero de expediente

            # Abogados
            'lead_attorney_id',       # Abogado principal
            'assigned_attorneys',     # Lista de abogados

            # Informacion financiera
            'billing_type',           # Tipo de facturacion
            'estimated_value',        # Valor estimado
            'retainer_amount',        # Monto de anticipo

            # Fechas
            'opened_date',            # Fecha de apertura (requerido)
            'closed_date',            # Fecha de cierre
            'statute_of_limitations', # Fecha de prescripcion

            # Metadatos
            'tags',                   # Etiquetas
            'notes'                   # Notas generales
        ]

    def create(self, validated_data):
        """
        Crea un nuevo caso asignando automaticamente el creador.

        Este metodo sobrescribe el metodo create() por defecto para
        agregar el ID del usuario autenticado como creador del caso.

        Args:
            validated_data: Diccionario con los datos validados del caso

        Returns:
            Case: Nueva instancia del caso creado
        """
        # Obtener el objeto request del contexto del serializador
        # El contexto es pasado automaticamente por la vista
        request = self.context.get('request')

        # Agregar el ID del usuario autenticado como creador
        validated_data['created_by_id'] = request.user.id

        # Llamar al metodo create() de la clase padre para crear el objeto
        # Esto tambien activara el metodo save() del modelo que genera el case_number
        return super().create(validated_data)


class CaseUpdateSerializer(serializers.ModelSerializer):
    """
    Serializador para actualizar casos existentes.

    Este serializador define los campos que se pueden modificar
    en un caso existente. Excluye campos inmutables como
    case_number, client_id (el cliente no deberia cambiar),
    opened_date y created_by_id.
    """

    class Meta:
        """
        Configuracion del serializador de actualizacion de casos.
        """
        # Modelo asociado
        model = Case

        # Campos que se pueden actualizar
        # Nota: client_id y opened_date no se pueden cambiar
        # despues de crear el caso
        fields = [
            # Informacion basica
            'title',                  # Titulo del caso
            'description',            # Descripcion
            'case_type',              # Tipo de caso
            'status',                 # Estado actual
            'priority',               # Prioridad

            # Informacion del cliente (solo datos de contacto)
            'client_name',            # Nombre del cliente
            'client_email',           # Email del cliente
            'client_phone',           # Telefono del cliente

            # Informacion del tribunal
            'jurisdiction',           # Jurisdiccion
            'court',                  # Tribunal
            'judge',                  # Juez
            'court_case_number',      # Numero de expediente

            # Abogados
            'lead_attorney_id',       # Abogado principal
            'assigned_attorneys',     # Lista de abogados

            # Informacion financiera
            'billing_type',           # Tipo de facturacion
            'estimated_value',        # Valor estimado
            'retainer_amount',        # Monto de anticipo

            # Fechas (solo cerrado y prescripcion)
            'closed_date',            # Fecha de cierre
            'statute_of_limitations', # Fecha de prescripcion

            # Metadatos
            'tags',                   # Etiquetas
            'notes'                   # Notas generales
        ]


class CaseStatisticsSerializer(serializers.Serializer):
    """
    Serializador para estadisticas de casos.

    Este serializador no esta asociado a un modelo especifico
    (no es ModelSerializer). Se utiliza para validar y serializar
    datos de estadisticas calculados dinamicamente.

    Campos incluidos:
    - total_cases: Total de casos
    - active_cases: Casos activos
    - pending_cases: Casos pendientes
    - closed_cases: Casos cerrados
    - by_type: Distribucion por tipo de caso
    - by_priority: Distribucion por prioridad
    """

    # Campo para el total de casos - numero entero
    total_cases = serializers.IntegerField()

    # Campo para casos activos - numero entero
    active_cases = serializers.IntegerField()

    # Campo para casos pendientes - numero entero
    pending_cases = serializers.IntegerField()

    # Campo para casos cerrados - numero entero
    closed_cases = serializers.IntegerField()

    # Campo para distribucion por tipo de caso
    # DictField acepta un diccionario con claves y valores arbitrarios
    # Ejemplo: {'civil': 10, 'criminal': 5, 'labor': 3}
    by_type = serializers.DictField()

    # Campo para distribucion por prioridad
    # Ejemplo: {'low': 5, 'medium': 8, 'high': 3, 'urgent': 2}
    by_priority = serializers.DictField()
