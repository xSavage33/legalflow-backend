"""
Modulo de Modelos del Portal de Clientes (Client Portal Service)

Este archivo define los modelos de datos para el portal de clientes del sistema LegalFlow.
Contiene dos modelos principales:
    - ClientPreference: Almacena las preferencias de configuracion de cada cliente
    - Message: Gestiona los mensajes entre clientes y el equipo legal

Estos modelos utilizan UUID como identificadores primarios para mayor seguridad
y compatibilidad con arquitecturas de microservicios.

Autor: Equipo LegalFlow
"""

# Importacion del modulo uuid para generar identificadores unicos universales
# UUID proporciona identificadores de 128 bits que son practicamente imposibles de duplicar
import uuid

# Importacion del modulo models de Django para definir los modelos de base de datos
# models.Model es la clase base de la cual heredan todos los modelos de Django
from django.db import models


class ClientPreference(models.Model):
    """
    Modelo de Preferencias del Cliente.

    Este modelo almacena todas las configuraciones y preferencias personalizadas
    de cada cliente del sistema. Incluye configuraciones de notificaciones,
    idioma y zona horaria.

    Atributos:
        id: Identificador unico UUID del registro de preferencias
        user_id: Identificador UUID del usuario asociado (relacion con el servicio de usuarios)
        email_notifications: Indica si el cliente desea recibir notificaciones por correo
        sms_notifications: Indica si el cliente desea recibir notificaciones por SMS
        case_updates: Indica si el cliente desea recibir actualizaciones de sus casos
        billing_updates: Indica si el cliente desea recibir actualizaciones de facturacion
        deadline_reminders: Indica si el cliente desea recibir recordatorios de fechas limite
        language: Codigo del idioma preferido del cliente (por defecto espanol 'es')
        timezone: Zona horaria del cliente (por defecto 'America/Bogota')
        created_at: Fecha y hora de creacion del registro
        updated_at: Fecha y hora de la ultima actualizacion del registro
    """

    # Campo de identificador unico primario usando UUID
    # primary_key=True: Este campo es la clave primaria de la tabla
    # default=uuid.uuid4: Genera automaticamente un UUID version 4 (aleatorio)
    # editable=False: No se puede modificar una vez creado
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Identificador del usuario asociado a estas preferencias
    # unique=True: Solo puede existir un registro de preferencias por usuario
    # db_index=True: Crea un indice en la base de datos para busquedas mas rapidas
    user_id = models.UUIDField(unique=True, db_index=True)

    # Preferencia de notificaciones por correo electronico
    # default=True: Por defecto, las notificaciones por email estan activadas
    email_notifications = models.BooleanField(default=True)

    # Preferencia de notificaciones por SMS (mensaje de texto)
    # default=False: Por defecto, las notificaciones por SMS estan desactivadas
    sms_notifications = models.BooleanField(default=False)

    # Preferencia para recibir actualizaciones sobre el estado de los casos legales
    # default=True: Por defecto, el cliente recibe estas actualizaciones
    case_updates = models.BooleanField(default=True)

    # Preferencia para recibir actualizaciones sobre facturacion y pagos
    # default=True: Por defecto, el cliente recibe estas actualizaciones
    billing_updates = models.BooleanField(default=True)

    # Preferencia para recibir recordatorios de fechas limite importantes
    # default=True: Por defecto, el cliente recibe estos recordatorios
    deadline_reminders = models.BooleanField(default=True)

    # Codigo del idioma preferido del cliente
    # max_length=5: Permite codigos como 'es', 'en', 'es-CO', etc.
    # default='es': El idioma por defecto es espanol
    language = models.CharField(max_length=5, default='es')

    # Zona horaria del cliente para mostrar fechas y horas correctamente
    # max_length=50: Suficiente para nombres de zona horaria como 'America/Bogota'
    # default='America/Bogota': Zona horaria por defecto de Colombia
    timezone = models.CharField(max_length=50, default='America/Bogota')

    # Marca de tiempo de cuando se creo el registro
    # auto_now_add=True: Se establece automaticamente al crear el registro
    created_at = models.DateTimeField(auto_now_add=True)

    # Marca de tiempo de la ultima modificacion del registro
    # auto_now=True: Se actualiza automaticamente cada vez que se guarda el registro
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """
        Clase Meta para configuracion adicional del modelo.

        Define opciones de metadatos como el nombre de la tabla en la base de datos.
        """
        # Nombre personalizado de la tabla en la base de datos
        # En lugar de 'portal_clientpreference', se usara 'client_preferences'
        db_table = 'client_preferences'

    def __str__(self):
        """
        Representacion en cadena de texto del objeto ClientPreference.

        Este metodo es utilizado por Django en el panel de administracion
        y en la depuracion para mostrar una descripcion legible del objeto.

        Returns:
            str: Cadena descriptiva indicando a que usuario pertenecen las preferencias
        """
        # Retorna una cadena formateada con el ID del usuario
        return f"Preferences for user {self.user_id}"


class Message(models.Model):
    """
    Modelo de Mensajes del Portal de Clientes.

    Este modelo gestiona la comunicacion entre clientes y el equipo legal.
    Permite enviar, recibir y dar seguimiento a mensajes relacionados con casos legales.
    Soporta hilos de conversacion mediante mensajes de respuesta (parent_message_id).

    Atributos:
        id: Identificador unico UUID del mensaje
        sender_id: UUID del usuario que envia el mensaje
        sender_name: Nombre del remitente
        sender_role: Rol del remitente (cliente, abogado, etc.)
        recipient_id: UUID del usuario que recibe el mensaje
        recipient_name: Nombre del destinatario
        case_id: UUID del caso legal asociado (opcional)
        case_number: Numero de referencia del caso (opcional)
        subject: Asunto del mensaje
        content: Contenido/cuerpo del mensaje
        status: Estado actual del mensaje (enviado, entregado, leido)
        read_at: Fecha y hora en que se leyo el mensaje
        parent_message_id: UUID del mensaje padre (para respuestas)
        created_at: Fecha y hora de creacion del mensaje
    """

    # Definicion de las opciones de estado del mensaje como tuplas
    # Cada tupla contiene: (valor_almacenado, etiqueta_legible)
    # Estos estados permiten rastrear el ciclo de vida del mensaje
    STATUS_CHOICES = [
        ('sent', 'Enviado'),      # Estado inicial cuando se envia el mensaje
        ('delivered', 'Entregado'),  # El mensaje fue entregado al destinatario
        ('read', 'Leido'),        # El destinatario ha leido el mensaje
    ]

    # Identificador unico primario del mensaje usando UUID
    # primary_key=True: Este campo es la clave primaria
    # default=uuid.uuid4: Genera automaticamente un UUID aleatorio
    # editable=False: No se puede modificar despues de la creacion
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Identificador del usuario que envia el mensaje
    # db_index=True: Indice para optimizar busquedas por remitente
    sender_id = models.UUIDField(db_index=True)

    # Nombre completo del remitente del mensaje
    # Se almacena para evitar consultas adicionales al servicio de usuarios
    sender_name = models.CharField(max_length=255)

    # Rol del remitente (por ejemplo: 'client', 'lawyer', 'admin')
    # Permite identificar el tipo de usuario que envia el mensaje
    sender_role = models.CharField(max_length=50)

    # Identificador del usuario destinatario del mensaje
    # db_index=True: Indice para optimizar busquedas por destinatario
    recipient_id = models.UUIDField(db_index=True)

    # Nombre completo del destinatario del mensaje
    # Se almacena para evitar consultas adicionales al servicio de usuarios
    recipient_name = models.CharField(max_length=255)

    # Identificador del caso legal asociado al mensaje (opcional)
    # null=True, blank=True: El mensaje puede no estar asociado a un caso especifico
    # db_index=True: Indice para optimizar busquedas por caso
    case_id = models.UUIDField(null=True, blank=True, db_index=True)

    # Numero de referencia del caso legal (opcional)
    # blank=True: Permite que el campo este vacio en formularios
    case_number = models.CharField(max_length=50, blank=True)

    # Asunto o titulo del mensaje
    # max_length=255: Longitud maxima estandar para asuntos
    subject = models.CharField(max_length=255)

    # Contenido completo del mensaje
    # TextField: Permite texto de longitud ilimitada
    content = models.TextField()

    # Estado actual del mensaje
    # choices=STATUS_CHOICES: Limita los valores a las opciones definidas
    # default='sent': Estado inicial es 'enviado'
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')

    # Fecha y hora en que el destinatario leyo el mensaje
    # null=True, blank=True: Sera nulo hasta que se lea el mensaje
    read_at = models.DateTimeField(null=True, blank=True)

    # Identificador del mensaje padre para crear hilos de respuestas
    # null=True, blank=True: Sera nulo si es un mensaje nuevo (no una respuesta)
    # Permite construir conversaciones encadenadas
    parent_message_id = models.UUIDField(null=True, blank=True)  # Para respuestas

    # Marca de tiempo de cuando se creo el mensaje
    # auto_now_add=True: Se establece automaticamente al crear el mensaje
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """
        Clase Meta para configuracion adicional del modelo Message.

        Define el nombre de la tabla, el ordenamiento por defecto y los
        indices compuestos para optimizar las consultas mas frecuentes.
        """
        # Nombre personalizado de la tabla en la base de datos
        db_table = 'messages'

        # Ordenamiento por defecto: mensajes mas recientes primero
        # El signo '-' indica orden descendente (de mayor a menor)
        ordering = ['-created_at']

        # Indices compuestos para optimizar consultas frecuentes
        # Estos indices mejoran el rendimiento al buscar mensajes
        indexes = [
            # Indice compuesto para buscar mensajes de un remitente ordenados por fecha
            models.Index(fields=['sender_id', 'created_at']),
            # Indice compuesto para buscar mensajes de un destinatario ordenados por fecha
            models.Index(fields=['recipient_id', 'created_at']),
            # Indice simple para buscar mensajes por caso
            models.Index(fields=['case_id']),
        ]

    def __str__(self):
        """
        Representacion en cadena de texto del objeto Message.

        Este metodo es utilizado por Django en el panel de administracion
        y en la depuracion para mostrar una descripcion legible del mensaje.

        Returns:
            str: Cadena con el asunto, remitente y destinatario del mensaje
        """
        # Retorna una cadena formateada con informacion clave del mensaje
        return f"{self.subject} - From: {self.sender_name} To: {self.recipient_name}"
