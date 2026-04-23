"""
Modulo de Modelos del Servicio de Control de Tiempo (Time Tracking Service)

Este archivo define los modelos de base de datos para el sistema de seguimiento
de tiempo en un entorno legal. Permite registrar entradas de tiempo, gestionar
temporizadores activos y configurar tarifas por hora para usuarios y casos.

Modelos incluidos:
- TimeEntry: Representa una entrada de tiempo individual para facturacion
- Timer: Temporizador activo para seguimiento en tiempo real
- UserRate: Tarifa por hora predeterminada de un usuario
- CaseRate: Tarifa especial para casos especificos

Autor: LegalFlow Team
Fecha: 2024
"""

# Importacion de la libreria uuid para generar identificadores unicos universales
import uuid

# Importacion del modulo models de Django para definir modelos de base de datos
from django.db import models

# Importacion de timezone para manejar fechas y horas con zona horaria
from django.utils import timezone

# Importacion de Decimal para calculos monetarios precisos (evita errores de punto flotante)
from decimal import Decimal


class TimeEntry(models.Model):
    """
    Modelo de Entrada de Tiempo

    Representa un registro de tiempo trabajado que puede ser facturado al cliente.
    Almacena informacion sobre quien trabajo, en que caso, cuanto tiempo,
    y el estado de aprobacion y facturacion.

    Atributos principales:
        - id: Identificador unico de la entrada
        - user_id: ID del usuario que registro el tiempo
        - case_id: ID del caso legal asociado
        - duration_minutes: Duracion del trabajo en minutos
        - status: Estado actual (borrador, enviado, aprobado, facturado, rechazado)
        - is_billable: Indica si el tiempo es facturable
        - amount: Monto calculado basado en tarifa por hora
    """

    # Opciones de estado para una entrada de tiempo
    # Cada tupla contiene (valor_interno, etiqueta_mostrada)
    STATUS_CHOICES = [
        ('draft', 'Borrador'),           # Estado inicial, puede ser editado
        ('submitted', 'Enviado'),         # Enviado para revision
        ('approved', 'Aprobado'),         # Aprobado por supervisor
        ('billed', 'Facturado'),          # Ya incluido en una factura
        ('rejected', 'Rechazado'),        # Rechazado por supervisor
    ]

    # Opciones de tipo de actividad legal
    # Categoriza el tipo de trabajo realizado
    ACTIVITY_TYPE_CHOICES = [
        ('research', 'Investigacion'),           # Investigacion juridica
        ('drafting', 'Redaccion'),               # Redaccion de documentos
        ('review', 'Revision'),                  # Revision de documentos
        ('meeting', 'Reunion'),                  # Reuniones con clientes o equipo
        ('court', 'Audiencia/Juzgado'),          # Comparecencias en tribunal
        ('call', 'Llamada'),                     # Llamadas telefonicas
        ('email', 'Correo electronico'),         # Correspondencia por email
        ('travel', 'Desplazamiento'),            # Viajes relacionados al caso
        ('administrative', 'Administrativo'),    # Tareas administrativas
        ('other', 'Otro'),                       # Otras actividades no categorizadas
    ]

    # ==================== CAMPOS DE IDENTIFICACION ====================

    # Campo de clave primaria usando UUID en lugar de entero autoincrementable
    # primary_key=True: Este campo es la clave primaria
    # default=uuid.uuid4: Genera un UUID automaticamente al crear
    # editable=False: No se puede modificar despues de crear
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # ID del usuario que registro esta entrada de tiempo
    # db_index=True: Crea un indice en la base de datos para busquedas rapidas
    user_id = models.UUIDField(db_index=True)

    # Nombre del usuario (almacenado para evitar consultas adicionales)
    # max_length=255: Limite maximo de caracteres
    user_name = models.CharField(max_length=255)

    # ==================== ENTIDADES RELACIONADAS ====================

    # ID del caso legal asociado (opcional)
    # null=True: Permite valores NULL en la base de datos
    # blank=True: Permite dejar el campo vacio en formularios
    case_id = models.UUIDField(db_index=True, null=True, blank=True)

    # Numero de caso legible por humanos (ej: "CASO-2024-001")
    case_number = models.CharField(max_length=50, blank=True)

    # ID de la tarea especifica asociada (opcional)
    task_id = models.UUIDField(null=True, blank=True)

    # ==================== DETALLES DEL TIEMPO ====================

    # Fecha en que se realizo el trabajo
    date = models.DateField()

    # Duracion del trabajo en minutos (se usa minutos para mayor precision)
    duration_minutes = models.IntegerField()

    # Descripcion detallada del trabajo realizado
    description = models.TextField()

    # Tipo de actividad realizada (usa las opciones definidas arriba)
    # default='other': Si no se especifica, se usa 'Otro'
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPE_CHOICES, default='other')

    # ==================== FACTURACION ====================

    # Indica si este tiempo es facturable al cliente
    # default=True: Por defecto, todo tiempo es facturable
    is_billable = models.BooleanField(default=True)

    # Tarifa por hora aplicada a esta entrada
    # max_digits=10: Maximo 10 digitos en total
    # decimal_places=2: 2 decimales para centavos
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Monto total calculado (tarifa * horas)
    # Se calcula automaticamente en el metodo save()
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    # ==================== ESTADO ====================

    # Estado actual de la entrada de tiempo
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # ID de la factura asociada (se establece cuando se factura)
    invoice_id = models.UUIDField(null=True, blank=True)

    # ==================== APROBACION ====================

    # ID del usuario que aprobo la entrada
    approved_by_id = models.UUIDField(null=True, blank=True)

    # Nombre del usuario que aprobo
    approved_by_name = models.CharField(max_length=255, blank=True)

    # Fecha y hora de aprobacion
    approved_at = models.DateTimeField(null=True, blank=True)

    # Razon de rechazo (si aplica)
    rejection_reason = models.TextField(blank=True)

    # ==================== REFERENCIA DE TEMPORIZADOR ====================

    # ID del temporizador del cual se creo esta entrada (si aplica)
    timer_id = models.UUIDField(null=True, blank=True)

    # ==================== METADATOS ====================

    # Notas adicionales sobre la entrada
    notes = models.TextField(blank=True)

    # Fecha y hora de creacion (se establece automaticamente)
    # auto_now_add=True: Se establece solo al crear el registro
    created_at = models.DateTimeField(auto_now_add=True)

    # Fecha y hora de ultima actualizacion (se actualiza automaticamente)
    # auto_now=True: Se actualiza cada vez que se guarda el registro
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """
        Clase Meta para configuracion del modelo

        Define opciones de configuracion a nivel de base de datos
        como nombre de tabla, ordenamiento e indices.
        """
        # Nombre de la tabla en la base de datos
        db_table = 'time_entries'

        # Ordenamiento predeterminado: fecha descendente, luego creacion descendente
        # El signo menos (-) indica orden descendente
        ordering = ['-date', '-created_at']

        # Indices compuestos para optimizar consultas frecuentes
        indexes = [
            # Indice para buscar entradas por usuario y fecha
            models.Index(fields=['user_id', 'date']),
            # Indice para buscar entradas por caso y fecha
            models.Index(fields=['case_id', 'date']),
            # Indice para filtrar por estado
            models.Index(fields=['status']),
            # Indice para buscar entradas facturables por estado
            models.Index(fields=['is_billable', 'status']),
        ]

    def __str__(self):
        """
        Representacion en cadena de texto del objeto

        Se usa cuando se imprime el objeto o se muestra en el admin de Django.

        Retorna:
            str: Cadena con formato "nombre_usuario - duracion_minutos min on fecha"
        """
        return f"{self.user_name} - {self.duration_minutes}min on {self.date}"

    def save(self, *args, **kwargs):
        """
        Sobrescribe el metodo save para calcular el monto automaticamente

        Antes de guardar, si la entrada es facturable y tiene tarifa,
        calcula el monto total multiplicando las horas por la tarifa.

        Args:
            *args: Argumentos posicionales pasados al metodo padre
            **kwargs: Argumentos de palabra clave pasados al metodo padre
        """
        # Verifica si la entrada es facturable y tiene tarifa definida
        if self.is_billable and self.hourly_rate:
            # Convierte minutos a horas usando Decimal para precision
            hours = Decimal(self.duration_minutes) / Decimal(60)
            # Calcula el monto: horas * tarifa por hora
            self.amount = hours * self.hourly_rate
        # Llama al metodo save() del padre (Model) para guardar en la base de datos
        super().save(*args, **kwargs)

    @property
    def duration_hours(self):
        """
        Propiedad calculada que retorna la duracion en horas

        Convierte los minutos almacenados a horas con 2 decimales.
        Se usa @property para acceder como atributo: entry.duration_hours

        Retorna:
            float: Duracion en horas redondeada a 2 decimales
        """
        return round(self.duration_minutes / 60, 2)


class Timer(models.Model):
    """
    Modelo de Temporizador

    Representa un temporizador activo para seguimiento de tiempo en tiempo real.
    Permite a los usuarios iniciar, pausar, reanudar y detener el cronometro
    mientras trabajan, y luego convertirlo en una entrada de tiempo.

    Atributos principales:
        - id: Identificador unico del temporizador
        - user_id: ID del usuario propietario
        - is_running: Indica si el temporizador esta activo
        - start_time: Hora de inicio del periodo actual
        - accumulated_seconds: Tiempo acumulado de periodos anteriores
    """

    # ==================== CAMPOS DE IDENTIFICACION ====================

    # Clave primaria UUID generada automaticamente
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # ID del usuario propietario del temporizador
    user_id = models.UUIDField(db_index=True)

    # Nombre del usuario
    user_name = models.CharField(max_length=255)

    # ==================== ENTIDADES RELACIONADAS ====================

    # ID del caso asociado (opcional)
    case_id = models.UUIDField(null=True, blank=True)

    # Numero de caso legible
    case_number = models.CharField(max_length=50, blank=True)

    # ID de tarea asociada (opcional)
    task_id = models.UUIDField(null=True, blank=True)

    # ==================== ESTADO DEL TEMPORIZADOR ====================

    # Descripcion del trabajo siendo realizado
    description = models.TextField(blank=True)

    # Tipo de actividad (reutiliza las opciones de TimeEntry)
    activity_type = models.CharField(max_length=20, choices=TimeEntry.ACTIVITY_TYPE_CHOICES, default='other')

    # Indica si el temporizador esta corriendo actualmente
    # default=True: Al crear, el temporizador inicia automaticamente
    is_running = models.BooleanField(default=True)

    # Hora de inicio del periodo actual de conteo
    # default=timezone.now: Se establece a la hora actual al crear
    start_time = models.DateTimeField(default=timezone.now)

    # Hora en que se detuvo el temporizador (si esta pausado)
    stop_time = models.DateTimeField(null=True, blank=True)

    # ==================== TIEMPO ACUMULADO ====================

    # Segundos acumulados de periodos anteriores (para pausar/reanudar)
    # Cuando se pausa, el tiempo actual se suma aqui
    accumulated_seconds = models.IntegerField(default=0)

    # ==================== FACTURACION ====================

    # Indica si el tiempo sera facturable
    is_billable = models.BooleanField(default=True)

    # Tarifa por hora a aplicar cuando se convierta en entrada de tiempo
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # ==================== METADATOS ====================

    # Fecha y hora de creacion del temporizador
    created_at = models.DateTimeField(auto_now_add=True)

    # Fecha y hora de ultima actualizacion
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """
        Configuracion del modelo Timer
        """
        # Nombre de la tabla en la base de datos
        db_table = 'timers'

        # Ordenamiento: mas recientes primero
        ordering = ['-created_at']

    def __str__(self):
        """
        Representacion en cadena de texto del temporizador

        Muestra el usuario, estado (Running/Stopped) y tiempo transcurrido.

        Retorna:
            str: Cadena descriptiva del temporizador
        """
        # Determina el texto de estado basado en is_running
        status = "Running" if self.is_running else "Stopped"
        return f"{self.user_name} - {status} ({self.get_elapsed_time()}s)"

    def get_elapsed_time(self):
        """
        Calcula el tiempo total transcurrido en segundos

        Si el temporizador esta corriendo, suma el tiempo de la sesion actual
        al tiempo acumulado. Si esta pausado, retorna solo el acumulado.

        Retorna:
            int: Tiempo total en segundos
        """
        if self.is_running:
            # Calcula los segundos de la sesion actual
            current_session = (timezone.now() - self.start_time).total_seconds()
            # Retorna el total: acumulado + sesion actual
            return int(self.accumulated_seconds + current_session)
        # Si esta pausado, retorna solo el tiempo acumulado
        return self.accumulated_seconds

    def get_elapsed_minutes(self):
        """
        Calcula el tiempo total transcurrido en minutos

        Convierte el tiempo en segundos a minutos redondeados.

        Retorna:
            int: Tiempo total en minutos (redondeado)
        """
        return round(self.get_elapsed_time() / 60)

    def pause(self):
        """
        Pausa el temporizador

        Guarda el tiempo transcurrido en accumulated_seconds,
        registra la hora de parada y marca el temporizador como detenido.
        Solo actua si el temporizador esta corriendo.
        """
        if self.is_running:
            # Guarda el tiempo total transcurrido hasta ahora
            self.accumulated_seconds = self.get_elapsed_time()
            # Registra la hora de parada
            self.stop_time = timezone.now()
            # Marca como no corriendo
            self.is_running = False
            # Guarda los cambios en la base de datos
            self.save()

    def resume(self):
        """
        Reanuda el temporizador

        Reinicia el conteo desde la hora actual, manteniendo
        el tiempo acumulado de periodos anteriores.
        Solo actua si el temporizador esta pausado.
        """
        if not self.is_running:
            # Establece nueva hora de inicio
            self.start_time = timezone.now()
            # Limpia la hora de parada
            self.stop_time = None
            # Marca como corriendo
            self.is_running = True
            # Guarda los cambios en la base de datos
            self.save()


class UserRate(models.Model):
    """
    Modelo de Tarifa de Usuario

    Almacena la tarifa por hora predeterminada para cada usuario.
    Esta tarifa se aplica automaticamente cuando se crean entradas de tiempo.

    Atributos principales:
        - user_id: ID del usuario (unico)
        - default_rate: Tarifa por hora predeterminada
        - currency: Moneda de la tarifa (COP por defecto)
        - effective_date: Fecha desde la cual aplica esta tarifa
    """

    # Clave primaria UUID
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # ID del usuario (unico - un usuario solo puede tener una tarifa)
    # unique=True: Garantiza que no haya duplicados
    user_id = models.UUIDField(db_index=True, unique=True)

    # Tarifa por hora predeterminada del usuario
    default_rate = models.DecimalField(max_digits=10, decimal_places=2)

    # Moneda de la tarifa (codigo ISO de 3 letras)
    # default='COP': Pesos colombianos por defecto
    currency = models.CharField(max_length=3, default='COP')

    # Fecha desde la cual esta tarifa es efectiva
    effective_date = models.DateField()

    # Fecha de creacion del registro
    created_at = models.DateTimeField(auto_now_add=True)

    # Fecha de ultima actualizacion
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """
        Configuracion del modelo UserRate
        """
        # Nombre de la tabla en la base de datos
        db_table = 'user_rates'

    def __str__(self):
        """
        Representacion en cadena de texto de la tarifa de usuario

        Retorna:
            str: Cadena con formato "User UUID: tarifa moneda/hr"
        """
        return f"User {self.user_id}: {self.default_rate} {self.currency}/hr"


class CaseRate(models.Model):
    """
    Modelo de Tarifa por Caso

    Define tarifas especiales para casos especificos. Puede aplicar
    a todos los usuarios en un caso, o a un usuario especifico.
    Tiene prioridad sobre la tarifa de usuario.

    Atributos principales:
        - case_id: ID del caso
        - user_id: ID del usuario (opcional - None aplica a todos)
        - rate: Tarifa por hora especial
        - currency: Moneda de la tarifa
    """

    # Clave primaria UUID
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # ID del caso al que aplica esta tarifa especial
    case_id = models.UUIDField(db_index=True)

    # ID del usuario (opcional)
    # Si es None, la tarifa aplica a todos los usuarios en este caso
    user_id = models.UUIDField(db_index=True, null=True, blank=True)

    # Tarifa por hora especial para este caso
    rate = models.DecimalField(max_digits=10, decimal_places=2)

    # Moneda de la tarifa
    currency = models.CharField(max_length=3, default='COP')

    # Notas sobre la razon de la tarifa especial
    notes = models.TextField(blank=True)

    # Fecha de creacion del registro
    created_at = models.DateTimeField(auto_now_add=True)

    # Fecha de ultima actualizacion
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """
        Configuracion del modelo CaseRate
        """
        # Nombre de la tabla en la base de datos
        db_table = 'case_rates'

        # Restriccion de unicidad compuesta
        # Solo puede existir una tarifa por combinacion de caso y usuario
        unique_together = ['case_id', 'user_id']

    def __str__(self):
        """
        Representacion en cadena de texto de la tarifa de caso

        Retorna:
            str: Cadena con formato "Case UUID: tarifa moneda/hr"
        """
        return f"Case {self.case_id}: {self.rate} {self.currency}/hr"
