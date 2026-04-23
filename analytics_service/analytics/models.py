"""
Modelos de datos para el Servicio de Analytics (Analiticas).

Este archivo define los modelos de base de datos que almacenan metricas diarias
y reportes en cache para el sistema de analiticas de LegalFlow. Los modelos
permiten rastrear KPIs del despacho juridico como casos abiertos/cerrados,
horas facturadas, ingresos, y generar reportes pre-calculados para mejorar
el rendimiento del dashboard.

Modelos incluidos:
    - DailyMetrics: Almacena metricas diarias agregadas por tipo
    - CachedReport: Almacena reportes pre-generados con tiempo de expiracion

Autor: LegalFlow Team
"""

# Importacion del modulo uuid para generar identificadores unicos universales
# Se usa como clave primaria en lugar de enteros auto-incrementales
import uuid

# Importacion del modulo models de Django ORM para definir modelos de base de datos
# Proporciona clases base y tipos de campos para mapear objetos Python a tablas SQL
from django.db import models


class DailyMetrics(models.Model):
    """
    Modelo para almacenar metricas diarias del despacho juridico.

    Este modelo captura diferentes tipos de metricas agregadas por dia,
    permitiendo analisis historico y visualizacion de tendencias en el dashboard.
    Cada registro representa un valor de metrica especifico para una fecha dada.

    Atributos:
        id (UUID): Identificador unico del registro, generado automaticamente
        date (Date): Fecha a la que corresponde la metrica
        metric_type (str): Tipo de metrica (casos abiertos, ingresos, etc.)
        value (Decimal): Valor numerico de la metrica
        dimensions (JSON): Filtros adicionales (por usuario, tipo de caso, etc.)
        created_at (DateTime): Fecha y hora de creacion del registro

    Ejemplo de uso:
        DailyMetrics.objects.create(
            date='2024-01-15',
            metric_type='cases_opened',
            value=5,
            dimensions={'case_type': 'civil'}
        )
    """

    # Lista de opciones para el tipo de metrica
    # Cada tupla contiene (valor_almacenado, etiqueta_legible)
    METRIC_TYPE_CHOICES = [
        ('cases_opened', 'Casos Abiertos'),      # Cantidad de casos nuevos abiertos
        ('cases_closed', 'Casos Cerrados'),       # Cantidad de casos finalizados
        ('hours_billed', 'Horas Facturadas'),     # Total de horas facturadas a clientes
        ('revenue', 'Ingresos'),                   # Ingresos totales generados
        ('invoices_sent', 'Facturas Enviadas'),   # Numero de facturas emitidas
        ('payments_received', 'Pagos Recibidos'), # Numero de pagos recibidos
    ]

    # Campo UUID como clave primaria para identificacion unica global
    # primary_key=True: Indica que es la clave primaria de la tabla
    # default=uuid.uuid4: Genera automaticamente un UUID version 4
    # editable=False: No permite edicion manual del campo
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Campo de fecha para identificar el dia de la metrica
    # db_index=True: Crea un indice en la base de datos para busquedas rapidas por fecha
    date = models.DateField(db_index=True)

    # Campo de texto para el tipo de metrica con opciones predefinidas
    # max_length=50: Longitud maxima de 50 caracteres
    # choices=METRIC_TYPE_CHOICES: Restringe los valores a las opciones definidas
    metric_type = models.CharField(max_length=50, choices=METRIC_TYPE_CHOICES)

    # Campo decimal para almacenar el valor numerico de la metrica
    # max_digits=15: Maximo 15 digitos en total
    # decimal_places=2: 2 digitos decimales para precision monetaria
    value = models.DecimalField(max_digits=15, decimal_places=2)

    # Campo JSON para almacenar dimensiones adicionales de filtrado
    # Permite segmentar metricas por usuario, tipo de caso, cliente, etc.
    # default=dict: Valor por defecto es un diccionario vacio
    # blank=True: Permite dejar el campo vacio en formularios
    dimensions = models.JSONField(default=dict, blank=True)

    # Campo de fecha y hora de creacion del registro
    # auto_now_add=True: Se establece automaticamente al crear el registro
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """
        Clase Meta para configuracion del modelo DailyMetrics.

        Define el nombre de la tabla, restricciones de unicidad y ordenamiento
        por defecto de los registros.
        """
        # Nombre personalizado de la tabla en la base de datos
        db_table = 'daily_metrics'

        # Restriccion de unicidad compuesta: no puede haber dos registros
        # con la misma combinacion de fecha, tipo de metrica y dimensiones
        unique_together = ['date', 'metric_type', 'dimensions']

        # Ordenamiento por defecto: fecha descendente (mas reciente primero)
        ordering = ['-date']

    def __str__(self):
        """
        Representacion en cadena del objeto DailyMetrics.

        Retorna una cadena legible que muestra el tipo de metrica,
        la fecha y el valor para facilitar la identificacion en el admin.

        Returns:
            str: Representacion formateada del registro de metrica
        """
        return f"{self.metric_type} on {self.date}: {self.value}"


class CachedReport(models.Model):
    """
    Modelo para almacenar reportes pre-generados en cache.

    Este modelo permite almacenar reportes complejos que han sido calculados
    previamente, evitando recalcularlos en cada solicitud. Cada reporte tiene
    un tiempo de expiracion para garantizar que los datos se actualicen
    periodicamente.

    Atributos:
        id (UUID): Identificador unico del reporte
        report_type (str): Tipo de reporte (dashboard, rentabilidad, etc.)
        parameters (JSON): Parametros de filtrado usados para generar el reporte
        data (JSON): Datos del reporte pre-calculados
        generated_at (DateTime): Fecha y hora de generacion del reporte
        expires_at (DateTime): Fecha y hora de expiracion del cache

    Propiedades:
        is_expired: Indica si el reporte ha expirado y necesita regenerarse

    Ejemplo de uso:
        reporte = CachedReport.objects.create(
            report_type='dashboard',
            parameters={'user_id': '123'},
            data={'total_cases': 50, 'revenue': 10000},
            expires_at=timezone.now() + timedelta(hours=1)
        )
    """

    # Lista de opciones para el tipo de reporte
    # Cada tupla contiene (valor_almacenado, etiqueta_legible)
    REPORT_TYPE_CHOICES = [
        ('dashboard', 'Dashboard'),                       # Panel principal de KPIs
        ('workload', 'Carga de Trabajo'),                 # Analisis de carga por abogado
        ('profitability', 'Rentabilidad'),                # Analisis de rentabilidad
        ('billing_status', 'Estado de Facturacion'),      # Estado de facturas y pagos
        ('deadline_compliance', 'Cumplimiento de Plazos'), # Analisis de vencimientos
        ('case_portfolio', 'Portafolio de Casos'),        # Distribucion de casos
    ]

    # Campo UUID como clave primaria para identificacion unica global
    # Permite referenciar reportes de forma segura entre servicios
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Campo de texto para el tipo de reporte con opciones predefinidas
    # Determina la estructura y contenido de los datos almacenados
    report_type = models.CharField(max_length=50, choices=REPORT_TYPE_CHOICES)

    # Campo JSON para almacenar los parametros de filtrado del reporte
    # Permite identificar reportes especificos por sus criterios de generacion
    parameters = models.JSONField(default=dict, blank=True)

    # Campo JSON para almacenar los datos pre-calculados del reporte
    # Contiene toda la informacion necesaria para renderizar el reporte
    data = models.JSONField(default=dict)

    # Campo de fecha y hora de generacion del reporte
    # auto_now=True: Se actualiza automaticamente cada vez que se guarda
    generated_at = models.DateTimeField(auto_now=True)

    # Campo de fecha y hora de expiracion del cache
    # Despues de esta fecha, el reporte debe regenerarse
    expires_at = models.DateTimeField()

    class Meta:
        """
        Clase Meta para configuracion del modelo CachedReport.

        Define el nombre de la tabla e indices para optimizar consultas
        de reportes por tipo y fecha de expiracion.
        """
        # Nombre personalizado de la tabla en la base de datos
        db_table = 'cached_reports'

        # Indices compuestos para optimizar busquedas frecuentes
        # El indice por tipo y expiracion acelera la limpieza de cache
        indexes = [
            models.Index(fields=['report_type', 'expires_at']),
        ]

    def __str__(self):
        """
        Representacion en cadena del objeto CachedReport.

        Retorna una cadena legible que muestra el tipo de reporte
        y la fecha de generacion para facilitar la identificacion.

        Returns:
            str: Representacion formateada del reporte cacheado
        """
        return f"{self.report_type} - Generated: {self.generated_at}"

    @property
    def is_expired(self):
        """
        Propiedad que indica si el reporte ha expirado.

        Compara la fecha de expiracion con la fecha y hora actual
        para determinar si el cache es valido o necesita regenerarse.

        Returns:
            bool: True si el reporte ha expirado, False si aun es valido
        """
        # Importacion del modulo timezone de Django para obtener la hora actual
        # Se importa dentro del metodo para evitar importaciones circulares
        from django.utils import timezone

        # Compara la fecha de expiracion con la hora actual del servidor
        # Retorna True si expires_at es anterior a la hora actual
        return self.expires_at < timezone.now()
