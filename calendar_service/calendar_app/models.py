"""
models.py - Modelos de datos del servicio de calendario

Este archivo define los modelos de base de datos para el servicio de calendario
de LegalFlow. Incluye tres modelos principales:

1. Event (Evento): Representa eventos del calendario como audiencias, reuniones,
   plazos y recordatorios relacionados con casos legales.

2. Deadline (Plazo): Representa plazos legales con fechas de vencimiento,
   prioridades y estados de seguimiento.

3. HolidayCalendar (Calendario de Festivos): Almacena dias festivos por
   jurisdiccion para calcular dias habiles correctamente.

Autor: Equipo LegalFlow
Fecha de creacion: 2024
"""

# Importacion de uuid para generar identificadores unicos universales
# Se utiliza para crear IDs de registro que son unicos globalmente
import uuid

# Importacion del modulo models de Django para definir modelos de base de datos
# Proporciona clases base y tipos de campos para el ORM de Django
from django.db import models

# Importacion de date y timedelta del modulo datetime
# date: para trabajar con fechas sin hora
# timedelta: para realizar calculos de diferencia entre fechas
from datetime import date, timedelta


class Event(models.Model):
    """
    Modelo Event (Evento)

    Representa un evento en el calendario del sistema legal.
    Los eventos pueden ser audiencias, reuniones, plazos, recordatorios,
    fechas judiciales, radicaciones u otros tipos de eventos.

    Atributos principales:
        - id: Identificador unico UUID del evento
        - title: Titulo descriptivo del evento
        - event_type: Tipo de evento (audiencia, reunion, etc.)
        - status: Estado actual del evento (programado, confirmado, etc.)
        - case_id: Referencia al caso legal asociado
        - start_datetime: Fecha y hora de inicio del evento
        - attendees: Lista de IDs de usuarios asistentes
        - reminder_minutes: Lista de minutos antes para enviar recordatorios
    """

    # Definicion de opciones para el tipo de evento
    # Cada tupla contiene (valor_almacenado, etiqueta_legible)
    TYPE_CHOICES = [
        ('hearing', 'Audiencia'),       # Audiencia judicial
        ('meeting', 'Reunion'),          # Reunion general
        ('deadline', 'Plazo'),           # Fecha limite
        ('reminder', 'Recordatorio'),    # Recordatorio simple
        ('court_date', 'Fecha Judicial'), # Fecha de comparecencia en corte
        ('filing', 'Radicacion'),        # Presentacion de documentos
        ('other', 'Otro'),               # Otros tipos de eventos
    ]

    # Definicion de opciones para el estado del evento
    # Permite rastrear el ciclo de vida del evento
    STATUS_CHOICES = [
        ('scheduled', 'Programado'),     # Evento programado inicialmente
        ('confirmed', 'Confirmado'),     # Evento confirmado por las partes
        ('completed', 'Completado'),     # Evento ya realizado
        ('cancelled', 'Cancelado'),      # Evento cancelado
        ('rescheduled', 'Reprogramado'), # Evento reprogramado para otra fecha
    ]

    # Campo ID: Clave primaria usando UUID version 4
    # primary_key=True: Este campo es la clave primaria de la tabla
    # default=uuid.uuid4: Genera automaticamente un UUID al crear el registro
    # editable=False: No se puede modificar despues de la creacion
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Campo titulo: Nombre descriptivo del evento
    # max_length=255: Longitud maxima de 255 caracteres
    title = models.CharField(max_length=255)

    # Campo descripcion: Descripcion detallada del evento
    # blank=True: Permite valores vacios en formularios
    description = models.TextField(blank=True)

    # Campo tipo de evento: Clasificacion del evento
    # choices=TYPE_CHOICES: Solo permite valores definidos en TYPE_CHOICES
    event_type = models.CharField(max_length=20, choices=TYPE_CHOICES)

    # Campo estado: Estado actual del evento
    # default='scheduled': Por defecto, los eventos nuevos estan programados
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')

    # Campo ID del caso: Referencia al caso legal asociado
    # db_index=True: Crea un indice para busquedas mas rapidas
    # null=True, blank=True: El evento puede no estar asociado a un caso
    case_id = models.UUIDField(db_index=True, null=True, blank=True)

    # Campo numero de caso: Numero de radicado del caso para referencia rapida
    case_number = models.CharField(max_length=50, blank=True)

    # Campo fecha y hora de inicio: Cuando comienza el evento
    # Campo obligatorio - todo evento debe tener hora de inicio
    start_datetime = models.DateTimeField()

    # Campo fecha y hora de fin: Cuando termina el evento
    # null=True: Permite valores nulos en la base de datos
    end_datetime = models.DateTimeField(null=True, blank=True)

    # Campo evento de todo el dia: Indica si el evento dura todo el dia
    # default=False: Por defecto, los eventos tienen hora especifica
    all_day = models.BooleanField(default=False)

    # Campo ubicacion: Lugar donde se realiza el evento
    location = models.CharField(max_length=255, blank=True)

    # Campo asistentes: Lista de IDs de usuarios que asistiran
    # JSONField: Almacena una lista JSON de UUIDs
    # default=list: Por defecto es una lista vacia
    attendees = models.JSONField(default=list, blank=True)  # Lista de IDs de usuarios

    # Campo minutos de recordatorio: Lista de minutos antes del evento para notificar
    # Ejemplo: [30, 60, 1440] significa recordatorios a 30 min, 1 hora y 1 dia antes
    reminder_minutes = models.JSONField(default=list, blank=True)

    # Campo ID del creador: UUID del usuario que creo el evento
    created_by_id = models.UUIDField()

    # Campo nombre del creador: Nombre del usuario que creo el evento
    # Se almacena para evitar consultas adicionales al servicio de usuarios
    created_by_name = models.CharField(max_length=255)

    # Campo fecha de creacion: Se establece automaticamente al crear el registro
    # auto_now_add=True: Django establece este valor al momento de crear
    created_at = models.DateTimeField(auto_now_add=True)

    # Campo fecha de actualizacion: Se actualiza automaticamente en cada guardado
    # auto_now=True: Django actualiza este valor en cada save()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """
        Clase Meta para configuracion del modelo Event

        Define opciones de configuracion a nivel de modelo como
        el nombre de la tabla, ordenamiento predeterminado e indices.
        """
        # Nombre de la tabla en la base de datos
        db_table = 'events'

        # Ordenamiento predeterminado: por fecha de inicio ascendente
        ordering = ['start_datetime']

        # Indices de base de datos para optimizar consultas frecuentes
        indexes = [
            models.Index(fields=['case_id']),        # Indice para buscar eventos por caso
            models.Index(fields=['start_datetime']), # Indice para buscar eventos por fecha
            models.Index(fields=['status']),         # Indice para filtrar por estado
        ]

    def __str__(self):
        """
        Representacion en cadena del evento

        Retorna el titulo del evento junto con su fecha y hora de inicio
        formateados para facil lectura.

        Returns:
            str: Titulo y fecha del evento en formato "Titulo - YYYY-MM-DD HH:MM"
        """
        return f"{self.title} - {self.start_datetime.strftime('%Y-%m-%d %H:%M')}"


class Deadline(models.Model):
    """
    Modelo Deadline (Plazo)

    Representa un plazo legal con fecha de vencimiento. Los plazos son
    criticos en el ambito legal y este modelo permite rastrear fechas
    limite, asignaciones, prioridades y estados de cumplimiento.

    Caracteristicas principales:
        - Soporte para dias habiles (excluye fines de semana y festivos)
        - Prioridades desde baja hasta critica
        - Estados de seguimiento (pendiente, completado, vencido, extendido)
        - Recordatorios configurables
        - Calculo automatico de dias restantes
    """

    # Definicion de opciones para la prioridad del plazo
    # Permite clasificar la urgencia de cada plazo
    PRIORITY_CHOICES = [
        ('low', 'Baja'),          # Prioridad baja - puede esperar
        ('medium', 'Media'),      # Prioridad media - atencion normal
        ('high', 'Alta'),         # Prioridad alta - requiere atencion pronta
        ('critical', 'Critica'),  # Prioridad critica - atencion inmediata
    ]

    # Definicion de opciones para el estado del plazo
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),    # Plazo aun no cumplido
        ('completed', 'Completado'), # Plazo cumplido exitosamente
        ('missed', 'Vencido'),       # Plazo no cumplido a tiempo
        ('extended', 'Extendido'),   # Plazo con extension de fecha
    ]

    # Campo ID: Clave primaria usando UUID version 4
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Campo titulo: Descripcion breve del plazo
    title = models.CharField(max_length=255)

    # Campo descripcion: Detalles adicionales sobre el plazo
    description = models.TextField(blank=True)

    # Campo prioridad: Nivel de urgencia del plazo
    # default='medium': Por defecto, prioridad media
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')

    # Campo estado: Estado actual del plazo
    # default='pending': Los plazos nuevos comienzan como pendientes
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Campo ID del caso: Referencia al caso legal asociado
    case_id = models.UUIDField(db_index=True, null=True, blank=True)

    # Campo numero de caso: Numero de radicado para referencia rapida
    case_number = models.CharField(max_length=50, blank=True)

    # Campo fecha de vencimiento: Fecha limite actual del plazo
    # Puede cambiar si se extiende el plazo
    due_date = models.DateField()

    # Campo fecha de vencimiento original: Fecha limite inicial
    # Se mantiene para historico aunque se extienda el plazo
    original_due_date = models.DateField()

    # Campo solo dias habiles: Indica si el calculo considera solo dias laborables
    # default=True: Por defecto, solo cuenta dias habiles (lunes a viernes)
    business_days_only = models.BooleanField(default=True)

    # Campo jurisdiccion: Jurisdiccion legal aplicable
    # Importante para determinar festivos locales
    jurisdiction = models.CharField(max_length=100, blank=True)

    # Campo fechas de recordatorio: Lista de fechas para enviar notificaciones
    # JSONField almacena una lista de fechas en formato JSON
    reminder_dates = models.JSONField(default=list, blank=True)

    # Campo ultimo recordatorio enviado: Fecha del ultimo recordatorio
    # Evita enviar recordatorios duplicados
    last_reminder_sent = models.DateField(null=True, blank=True)

    # Campo ID del asignado: UUID del usuario responsable del plazo
    assigned_to_id = models.UUIDField(null=True, blank=True)

    # Campo nombre del asignado: Nombre del responsable para referencia rapida
    assigned_to_name = models.CharField(max_length=255, blank=True)

    # Campo fecha de completado: Cuando se marco como completado
    completed_at = models.DateTimeField(null=True, blank=True)

    # Campo ID de quien completo: Usuario que marco el plazo como completado
    completed_by_id = models.UUIDField(null=True, blank=True)

    # Campo ID del creador: UUID del usuario que creo el plazo
    created_by_id = models.UUIDField()

    # Campo nombre del creador: Nombre del usuario creador
    created_by_name = models.CharField(max_length=255)

    # Campo fecha de creacion: Timestamp automatico al crear
    created_at = models.DateTimeField(auto_now_add=True)

    # Campo fecha de actualizacion: Timestamp automatico al actualizar
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """
        Clase Meta para configuracion del modelo Deadline

        Define la tabla de base de datos, ordenamiento predeterminado
        e indices para optimizar consultas.
        """
        # Nombre de la tabla en la base de datos
        db_table = 'deadlines'

        # Ordenamiento: primero por fecha de vencimiento, luego por prioridad descendente
        # Esto muestra primero los plazos mas proximos y de mayor prioridad
        ordering = ['due_date', '-priority']

        # Indices para consultas frecuentes
        indexes = [
            models.Index(fields=['case_id']),       # Busqueda por caso
            models.Index(fields=['due_date']),      # Busqueda por fecha de vencimiento
            models.Index(fields=['status']),        # Filtrado por estado
            models.Index(fields=['assigned_to_id']), # Busqueda por usuario asignado
        ]

    def __str__(self):
        """
        Representacion en cadena del plazo

        Returns:
            str: Titulo y fecha de vencimiento del plazo
        """
        return f"{self.title} - {self.due_date}"

    @property
    def days_remaining(self):
        """
        Propiedad calculada: Dias restantes hasta el vencimiento

        Calcula la diferencia en dias entre la fecha actual y la fecha
        de vencimiento del plazo. Si el plazo ya esta completado,
        retorna None.

        Returns:
            int o None: Numero de dias restantes (negativo si vencido),
                       o None si el plazo ya esta completado
        """
        # Si el plazo ya esta completado, no tiene sentido calcular dias restantes
        if self.status == 'completed':
            return None
        # Calcular diferencia entre fecha de vencimiento y fecha actual
        delta = self.due_date - date.today()
        # Retornar numero de dias (puede ser negativo si ya vencio)
        return delta.days

    @property
    def is_overdue(self):
        """
        Propiedad calculada: Indica si el plazo esta vencido

        Un plazo se considera vencido si esta en estado pendiente
        y su fecha de vencimiento ya paso.

        Returns:
            bool: True si el plazo esta vencido, False en caso contrario
        """
        # Esta vencido si esta pendiente Y la fecha de vencimiento ya paso
        return self.status == 'pending' and self.due_date < date.today()


class HolidayCalendar(models.Model):
    """
    Modelo HolidayCalendar (Calendario de Festivos)

    Almacena los dias festivos para diferentes jurisdicciones.
    Se utiliza para calcular correctamente los dias habiles,
    excluyendo fines de semana y dias festivos oficiales.

    Cada registro representa un dia festivo con su jurisdiccion
    aplicable y si es de caracter nacional o local.
    """

    # Campo ID: Clave primaria usando UUID
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Campo nombre: Nombre del dia festivo (ej: "Dia de la Independencia")
    name = models.CharField(max_length=255)

    # Campo fecha: Fecha del dia festivo
    date = models.DateField()

    # Campo jurisdiccion: Jurisdiccion donde aplica el festivo
    # Puede ser vacio para festivos nacionales
    jurisdiction = models.CharField(max_length=100, blank=True)

    # Campo es nacional: Indica si el festivo aplica a todo el pais
    # default=True: Por defecto, los festivos son nacionales
    is_national = models.BooleanField(default=True)

    # Campo anio: Anio del festivo para facilitar consultas por anio
    year = models.IntegerField()

    # Campo fecha de creacion: Timestamp automatico
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """
        Clase Meta para configuracion del modelo HolidayCalendar
        """
        # Nombre de la tabla en la base de datos
        db_table = 'holiday_calendar'

        # Ordenamiento por fecha
        ordering = ['date']

        # Restriccion de unicidad: no puede haber dos festivos
        # en la misma fecha para la misma jurisdiccion
        unique_together = ['date', 'jurisdiction']

    def __str__(self):
        """
        Representacion en cadena del festivo

        Returns:
            str: Nombre y fecha del festivo
        """
        return f"{self.name} - {self.date}"

    @classmethod
    def is_holiday(cls, check_date, jurisdiction=''):
        """
        Metodo de clase: Verifica si una fecha es dia festivo

        Comprueba si la fecha dada es un dia festivo en la jurisdiccion
        especificada o si es un festivo nacional.

        Args:
            check_date (date): Fecha a verificar
            jurisdiction (str): Jurisdiccion a considerar (opcional)

        Returns:
            bool: True si es festivo, False en caso contrario
        """
        # Buscar festivos que coincidan con la fecha
        # y que sean de la jurisdiccion especificada O sean nacionales
        return cls.objects.filter(
            date=check_date
        ).filter(
            # Usa Q objects para crear OR logico en la consulta
            models.Q(jurisdiction=jurisdiction) | models.Q(is_national=True)
        ).exists()  # exists() es mas eficiente que count() > 0

    @classmethod
    def is_business_day(cls, check_date, jurisdiction=''):
        """
        Metodo de clase: Verifica si una fecha es dia habil

        Un dia habil es aquel que no es fin de semana ni festivo.

        Args:
            check_date (date): Fecha a verificar
            jurisdiction (str): Jurisdiccion a considerar (opcional)

        Returns:
            bool: True si es dia habil, False en caso contrario
        """
        # Verificacion de fin de semana
        # weekday() retorna 0-4 para lunes-viernes, 5-6 para sabado-domingo
        if check_date.weekday() >= 5:
            return False  # Es sabado o domingo

        # Verificacion de dia festivo
        if cls.is_holiday(check_date, jurisdiction):
            return False  # Es un dia festivo

        # Si no es fin de semana ni festivo, es dia habil
        return True

    @classmethod
    def add_business_days(cls, start_date, days, jurisdiction=''):
        """
        Metodo de clase: Agrega dias habiles a una fecha

        Calcula una fecha futura agregando un numero especifico de
        dias habiles, saltando fines de semana y dias festivos.

        Args:
            start_date (date): Fecha de inicio
            days (int): Numero de dias habiles a agregar
            jurisdiction (str): Jurisdiccion para considerar festivos (opcional)

        Returns:
            date: Fecha resultante despues de agregar los dias habiles

        Ejemplo:
            Si start_date es viernes y days es 2, el resultado sera
            el martes siguiente (saltando sabado y domingo).
        """
        # Inicializar con la fecha de inicio
        current_date = start_date
        # Contador de dias habiles agregados
        days_added = 0

        # Iterar hasta agregar el numero requerido de dias habiles
        while days_added < days:
            # Avanzar un dia calendario
            current_date += timedelta(days=1)
            # Si el dia es habil, incrementar el contador
            if cls.is_business_day(current_date, jurisdiction):
                days_added += 1

        # Retornar la fecha final
        return current_date
