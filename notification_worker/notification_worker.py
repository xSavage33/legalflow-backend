"""
Notification Worker - Servicio de Notificaciones para LegalFlow

Este modulo implementa un worker de Celery que gestiona todas las notificaciones
del sistema LegalFlow, un software de gestion legal. Sus principales funciones son:

1. Envio de correos electronicos mediante SMTP
2. Recordatorios automaticos de plazos legales
3. Notificaciones de facturas (creadas, enviadas, vencidas, pagadas)
4. Actualizaciones de casos para clientes
5. Notificaciones de mensajes y documentos compartidos
6. Recordatorios de eventos del calendario

El worker utiliza Redis como broker de mensajes y backend de resultados,
y se programa mediante Celery Beat para ejecutar tareas periodicas.

Autor: Equipo LegalFlow
Zona horaria: America/Bogota (Colombia)
"""

# ============================================================================
# IMPORTACIONES
# ============================================================================

# Modulo os: permite acceder a variables de entorno del sistema operativo
import os

# Modulo smtplib: proporciona funcionalidad para enviar correos via protocolo SMTP
import smtplib

# MIMEText: clase para crear contenido de texto plano o HTML en correos
from email.mime.text import MIMEText

# MIMEMultipart: clase para crear correos con multiples partes (texto plano y HTML)
from email.mime.multipart import MIMEMultipart

# Celery: framework para procesamiento de tareas asincronas en segundo plano
from celery import Celery

# crontab: permite programar tareas periodicas con sintaxis similar a cron de Linux
from celery.schedules import crontab

# requests: biblioteca para realizar peticiones HTTP a otros servicios
import requests

# load_dotenv: carga variables de entorno desde un archivo .env
from dotenv import load_dotenv

# ============================================================================
# CARGA DE VARIABLES DE ENTORNO
# ============================================================================

# Carga las variables de entorno desde el archivo .env en el directorio actual
# Esto permite configurar el sistema sin modificar el codigo fuente
load_dotenv()

# ============================================================================
# CONFIGURACION DE CELERY
# ============================================================================

# URL del broker de mensajes (Redis) - donde se encolan las tareas
# Por defecto usa Redis en localhost, puerto 6379, base de datos 9
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/9')

# URL del backend de resultados - donde se almacenan los resultados de las tareas
# Utiliza la misma instancia de Redis que el broker
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/9')

# Crea la instancia principal de la aplicacion Celery
# 'notification_worker' es el nombre identificador de esta aplicacion
# broker: URL donde Celery busca tareas pendientes
# backend: URL donde Celery almacena resultados de tareas completadas
app = Celery('notification_worker', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

# Configuracion adicional de la aplicacion Celery
app.conf.update(
    # Formato de serializacion para las tareas: JSON para compatibilidad universal
    task_serializer='json',
    # Tipos de contenido aceptados: solo JSON por seguridad
    accept_content=['json'],
    # Formato de serializacion para los resultados: JSON
    result_serializer='json',
    # Zona horaria para programacion de tareas: Colombia
    timezone='America/Bogota',
    # Habilita UTC internamente para consistencia en calculos de tiempo
    enable_utc=True,
)

# ============================================================================
# CONFIGURACION DE CORREO ELECTRONICO (SMTP)
# ============================================================================

# Servidor SMTP para envio de correos (por defecto Gmail)
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')

# Puerto del servidor SMTP (587 es el puerto estandar para TLS)
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))

# Usuario/cuenta de correo para autenticacion SMTP
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')

# Contrasena o token de aplicacion para autenticacion SMTP
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

# Indica si se debe usar TLS (cifrado) para la conexion SMTP
# Convierte el string a booleano comparando con 'true'
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'

# Direccion de correo que aparecera como remitente por defecto
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@legalflow.com')

# ============================================================================
# URLs DE SERVICIOS INTERNOS (MICROSERVICIOS)
# ============================================================================

# URL del servicio de calendario - gestiona eventos, plazos y audiencias
CALENDAR_SERVICE_URL = os.environ.get('CALENDAR_SERVICE_URL', 'http://localhost:8006')

# URL del servicio IAM (Identity Access Management) - gestiona usuarios y autenticacion
IAM_SERVICE_URL = os.environ.get('IAM_SERVICE_URL', 'http://localhost:8001')

# URL del servicio de casos/asuntos legales - gestiona expedientes y casos
MATTER_SERVICE_URL = os.environ.get('MATTER_SERVICE_URL', 'http://localhost:8002')

# URL del servicio de facturacion - gestiona facturas y pagos
BILLING_SERVICE_URL = os.environ.get('BILLING_SERVICE_URL', 'http://localhost:8005')

# URL del servicio del portal de clientes - interfaz para clientes externos
PORTAL_SERVICE_URL = os.environ.get('PORTAL_SERVICE_URL', 'http://localhost:8007')


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def send_email(to_email, subject, body_html, body_text=None):
    """
    Envia un correo electronico utilizando el protocolo SMTP.

    Esta funcion es la base para todas las notificaciones por correo del sistema.
    Soporta envio de correos en formato HTML con version alternativa en texto plano.

    Parametros:
        to_email (str): Direccion de correo del destinatario
        subject (str): Asunto del correo
        body_html (str): Contenido del correo en formato HTML
        body_text (str, opcional): Contenido alternativo en texto plano

    Retorna:
        bool: True si el correo se envio exitosamente, False en caso contrario

    Notas:
        - Si no hay credenciales configuradas, imprime un mensaje de depuracion
        - Utiliza TLS si esta habilitado en la configuracion
        - Captura y registra cualquier excepcion durante el envio
    """
    # Verifica si las credenciales de correo estan configuradas
    if not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
        # Si no hay credenciales, imprime mensaje de depuracion y retorna False
        print(f"Email configuration missing. Would send to {to_email}: {subject}")
        return False

    try:
        # Crea un mensaje multipart que puede contener texto plano y HTML
        # 'alternative' indica que el cliente puede elegir cual version mostrar
        msg = MIMEMultipart('alternative')

        # Establece el asunto del correo
        msg['Subject'] = subject

        # Establece el remitente del correo
        msg['From'] = DEFAULT_FROM_EMAIL

        # Establece el destinatario del correo
        msg['To'] = to_email

        # Si se proporciono texto plano, lo adjunta como primera alternativa
        # Los clientes de correo mostraran HTML si lo soportan, sino texto plano
        if body_text:
            msg.attach(MIMEText(body_text, 'plain'))

        # Adjunta el contenido HTML como segunda alternativa (preferida)
        msg.attach(MIMEText(body_html, 'html'))

        # Establece conexion con el servidor SMTP usando context manager
        # El context manager asegura que la conexion se cierre correctamente
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            # Si TLS esta habilitado, inicia la conexion segura
            if EMAIL_USE_TLS:
                server.starttls()

            # Autentica con el servidor usando las credenciales configuradas
            server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)

            # Envia el mensaje al destinatario
            server.send_message(msg)

        # Retorna True indicando envio exitoso
        return True

    except Exception as e:
        # Captura cualquier error durante el envio y lo registra
        print(f"Error sending email: {str(e)}")
        # Retorna False indicando que el envio fallo
        return False


# ============================================================================
# TAREAS DE CELERY - NOTIFICACIONES DE PLAZOS
# ============================================================================

@app.task(name='send_deadline_reminder')
def send_deadline_reminder(deadline_id, user_email, deadline_title, due_date, case_number=''):
    """
    Envia un correo recordatorio sobre un plazo legal proximo a vencer.

    Esta tarea se ejecuta de forma asincrona cuando se detecta un plazo
    que requiere atencion del usuario asignado.

    Parametros:
        deadline_id (int): Identificador unico del plazo en la base de datos
        user_email (str): Correo electronico del usuario asignado al plazo
        deadline_title (str): Titulo o descripcion del plazo
        due_date (str): Fecha de vencimiento del plazo
        case_number (str, opcional): Numero de radicado del caso asociado

    Retorna:
        bool: Resultado del envio del correo (True/False)
    """
    # Construye el asunto del correo con prefijo identificador de LegalFlow
    subject = f"[LegalFlow] Recordatorio de Plazo: {deadline_title}"

    # Construye el cuerpo del correo en formato HTML con estilos basicos
    # Incluye informacion del plazo, fecha de vencimiento y caso asociado
    body_html = f"""
    <html>
    <body>
        <h2>Recordatorio de Plazo</h2>
        <p>Este es un recordatorio de que el siguiente plazo esta proximo a vencer:</p>
        <ul>
            <li><strong>Plazo:</strong> {deadline_title}</li>
            <li><strong>Fecha de vencimiento:</strong> {due_date}</li>
            {'<li><strong>Caso:</strong> ' + case_number + '</li>' if case_number else ''}
        </ul>
        <p>Por favor, tome las acciones necesarias.</p>
        <hr>
        <p><small>Este es un mensaje automatico de LegalFlow.</small></p>
    </body>
    </html>
    """

    # Version en texto plano para clientes de correo que no soportan HTML
    body_text = f"""
    Recordatorio de Plazo

    Plazo: {deadline_title}
    Fecha de vencimiento: {due_date}
    {'Caso: ' + case_number if case_number else ''}

    Por favor, tome las acciones necesarias.
    """

    # Invoca la funcion de envio de correo y retorna su resultado
    return send_email(user_email, subject, body_html, body_text)


# ============================================================================
# TAREAS DE CELERY - NOTIFICACIONES DE FACTURACION
# ============================================================================

@app.task(name='send_invoice_notification')
def send_invoice_notification(invoice_number, client_email, client_name, total_amount, due_date, action='created'):
    """
    Envia una notificacion por correo relacionada con una factura.

    Esta tarea maneja diferentes tipos de notificaciones de facturacion
    segun la accion especificada (creacion, envio, vencimiento, pago).

    Parametros:
        invoice_number (str): Numero identificador de la factura
        client_email (str): Correo electronico del cliente
        client_name (str): Nombre del cliente para personalizacion
        total_amount (float): Monto total de la factura
        due_date (str): Fecha de vencimiento de la factura
        action (str): Tipo de accion ('created', 'sent', 'overdue', 'paid')

    Retorna:
        bool: Resultado del envio del correo (True/False)
    """
    # Diccionario que mapea codigos de accion a textos legibles en espanol
    actions = {
        'created': 'Nueva Factura',      # Cuando se crea una nueva factura
        'sent': 'Factura Enviada',        # Cuando se envia la factura al cliente
        'overdue': 'Factura Vencida',     # Cuando la factura supera su fecha de pago
        'paid': 'Pago Recibido',          # Cuando se registra el pago de la factura
    }

    # Obtiene el texto de accion correspondiente, con valor por defecto
    action_text = actions.get(action, 'Notificacion de Factura')

    # Construye el asunto del correo con el tipo de accion y numero de factura
    subject = f"[LegalFlow] {action_text}: {invoice_number}"

    # Construye el cuerpo del correo en HTML con los detalles de la factura
    body_html = f"""
    <html>
    <body>
        <h2>{action_text}</h2>
        <p>Estimado/a {client_name},</p>
        <p>Le informamos sobre su factura:</p>
        <ul>
            <li><strong>Numero de factura:</strong> {invoice_number}</li>
            <li><strong>Monto total:</strong> ${total_amount}</li>
            <li><strong>Fecha de vencimiento:</strong> {due_date}</li>
        </ul>
        <hr>
        <p><small>Este es un mensaje automatico de LegalFlow.</small></p>
    </body>
    </html>
    """

    # Envia el correo (sin version texto plano en este caso)
    return send_email(client_email, subject, body_html)


# ============================================================================
# TAREAS DE CELERY - ACTUALIZACIONES DE CASOS
# ============================================================================

@app.task(name='send_case_update')
def send_case_update(case_number, client_email, client_name, update_type, update_message):
    """
    Envia una notificacion de actualizacion sobre un caso legal.

    Notifica al cliente cuando hay cambios relevantes en su caso,
    como cambios de estado, nuevos documentos, o actuaciones procesales.

    Parametros:
        case_number (str): Numero de radicado del caso
        client_email (str): Correo electronico del cliente
        client_name (str): Nombre del cliente
        update_type (str): Tipo de actualizacion (ej: 'Estado', 'Documento')
        update_message (str): Descripcion detallada de la actualizacion

    Retorna:
        bool: Resultado del envio del correo (True/False)
    """
    # Construye el asunto del correo con el numero de caso
    subject = f"[LegalFlow] Actualizacion de Caso: {case_number}"

    # Construye el cuerpo del correo con la informacion de la actualizacion
    body_html = f"""
    <html>
    <body>
        <h2>Actualizacion de Caso</h2>
        <p>Estimado/a {client_name},</p>
        <p>Hay una actualizacion en su caso <strong>{case_number}</strong>:</p>
        <p><strong>{update_type}:</strong> {update_message}</p>
        <hr>
        <p><small>Este es un mensaje automatico de LegalFlow.</small></p>
    </body>
    </html>
    """

    # Envia la notificacion al cliente
    return send_email(client_email, subject, body_html)


@app.task(name='process_event_case_closed')
def process_event_case_closed(case_id, case_number, client_email, client_name):
    """
    Procesa el evento de cierre de un caso legal y notifica al cliente.

    Esta tarea se dispara automaticamente cuando un caso cambia su estado
    a 'cerrado' en el sistema, informando al cliente sobre la finalizacion.

    Parametros:
        case_id (int): Identificador unico del caso en la base de datos
        case_number (str): Numero de radicado del caso
        client_email (str): Correo electronico del cliente
        client_name (str): Nombre del cliente

    Retorna:
        bool: Resultado del envio del correo (True/False)
    """
    # Construye el asunto indicando el cierre del caso
    subject = f"[LegalFlow] Caso Cerrado: {case_number}"

    # Construye el cuerpo del correo informando sobre el cierre
    # Incluye invitacion a revisar detalles en el portal de clientes
    body_html = f"""
    <html>
    <body>
        <h2>Caso Cerrado</h2>
        <p>Estimado/a {client_name},</p>
        <p>Le informamos que su caso <strong>{case_number}</strong> ha sido cerrado.</p>
        <p>Puede acceder al portal de clientes para ver los detalles finales del caso.</p>
        <hr>
        <p><small>Este es un mensaje automatico de LegalFlow.</small></p>
    </body>
    </html>
    """

    # Envia la notificacion de cierre al cliente
    return send_email(client_email, subject, body_html)


# ============================================================================
# TAREAS DE CELERY - VERIFICACION PERIODICA DE PLAZOS
# ============================================================================

@app.task(name='check_upcoming_deadlines')
def check_upcoming_deadlines():
    """
    Verifica plazos proximos a vencer y envia recordatorios automaticos.

    Esta tarea periodica consulta el servicio de calendario para obtener
    todos los plazos que vencen en los proximos 3 dias. Para cada plazo
    encontrado, obtiene los datos del usuario asignado y programa el
    envio de un recordatorio.

    Esta tarea se ejecuta diariamente a las 8:00 AM (hora de Colombia)
    segun la configuracion de Celery Beat.

    Retorna:
        None: Esta tarea no retorna valor, pero programa tareas hijas

    Excepciones:
        Captura y registra cualquier error durante la ejecucion
    """
    try:
        # Consulta al servicio de calendario los plazos de los proximos 3 dias
        response = requests.get(f'{CALENDAR_SERVICE_URL}/api/deadlines/upcoming/?days=3')

        # Verifica que la respuesta sea exitosa (codigo 200)
        if response.status_code == 200:
            # Extrae la lista de plazos del JSON de respuesta
            deadlines = response.json().get('results', [])

            # Itera sobre cada plazo encontrado
            for deadline in deadlines:
                # Verifica si el plazo tiene un usuario asignado
                if deadline.get('assigned_to_id'):
                    # Consulta al servicio IAM para obtener datos del usuario
                    user_response = requests.get(
                        f'{IAM_SERVICE_URL}/api/auth/users/{deadline["assigned_to_id"]}/'
                    )

                    # Verifica que se obtuvo el usuario exitosamente
                    if user_response.status_code == 200:
                        # Extrae los datos del usuario del JSON
                        user = user_response.json()

                        # Programa el envio del recordatorio de forma asincrona
                        # .delay() encola la tarea para ejecucion en segundo plano
                        send_deadline_reminder.delay(
                            deadline['id'],              # ID del plazo
                            user.get('email'),           # Correo del usuario
                            deadline['title'],           # Titulo del plazo
                            deadline['due_date'],        # Fecha de vencimiento
                            deadline.get('case_number', '')  # Numero de caso (opcional)
                        )

    except Exception as e:
        # Registra cualquier error que ocurra durante la verificacion
        print(f"Error checking deadlines: {str(e)}")


# ============================================================================
# TAREAS DE CELERY - VERIFICACION PERIODICA DE FACTURAS VENCIDAS
# ============================================================================

@app.task(name='check_overdue_invoices')
def check_overdue_invoices():
    """
    Verifica facturas vencidas y envia recordatorios de pago.

    Esta tarea periodica consulta el servicio de facturacion para obtener
    todas las facturas con estado 'vencido'. Para cada factura encontrada,
    envia un recordatorio al cliente correspondiente.

    Esta tarea se ejecuta diariamente a las 9:00 AM (hora de Colombia)
    segun la configuracion de Celery Beat.

    Retorna:
        None: Esta tarea no retorna valor, pero programa tareas hijas

    Excepciones:
        Captura y registra cualquier error durante la ejecucion
    """
    try:
        # Consulta al servicio de facturacion las facturas vencidas
        response = requests.get(f'{BILLING_SERVICE_URL}/api/invoices/?status=overdue')

        # Verifica que la respuesta sea exitosa
        if response.status_code == 200:
            # Extrae la lista de facturas del JSON de respuesta
            invoices = response.json().get('results', [])

            # Itera sobre cada factura vencida
            for invoice in invoices:
                # Verifica si la factura tiene correo de cliente asociado
                if invoice.get('client_email'):
                    # Programa el envio de notificacion de factura vencida
                    # .delay() encola la tarea para ejecucion asincrona
                    send_invoice_notification.delay(
                        invoice['invoice_number'],            # Numero de factura
                        invoice['client_email'],              # Correo del cliente
                        invoice.get('client_name', 'Cliente'), # Nombre (con default)
                        invoice['total_amount'],              # Monto total
                        invoice['due_date'],                  # Fecha de vencimiento
                        'overdue'                             # Tipo: vencida
                    )

    except Exception as e:
        # Registra cualquier error durante la verificacion
        print(f"Error checking overdue invoices: {str(e)}")


# ============================================================================
# TAREAS DE CELERY - NOTIFICACIONES DE MENSAJES
# ============================================================================

@app.task(name='send_message_notification')
def send_message_notification(recipient_email, recipient_name, sender_name, subject, case_number=''):
    """
    Envia una notificacion cuando se recibe un nuevo mensaje en el sistema.

    Notifica al usuario destinatario sobre mensajes nuevos en su bandeja
    de entrada de LegalFlow, incluyendo informacion del remitente y asunto.

    Parametros:
        recipient_email (str): Correo del destinatario del mensaje
        recipient_name (str): Nombre del destinatario
        sender_name (str): Nombre de quien envia el mensaje
        subject (str): Asunto del mensaje recibido
        case_number (str, opcional): Numero de caso relacionado

    Retorna:
        bool: Resultado del envio del correo (True/False)
    """
    # Construye el asunto del correo de notificacion
    email_subject = f"[LegalFlow] Nuevo mensaje de {sender_name}"

    # Construye el cuerpo del correo en HTML
    body_html = f"""
    <html>
    <body>
        <h2>Nuevo Mensaje</h2>
        <p>Estimado/a {recipient_name},</p>
        <p>Ha recibido un nuevo mensaje en LegalFlow:</p>
        <ul>
            <li><strong>De:</strong> {sender_name}</li>
            <li><strong>Asunto:</strong> {subject}</li>
            {'<li><strong>Caso:</strong> ' + case_number + '</li>' if case_number else ''}
        </ul>
        <p>Ingrese a LegalFlow para ver el mensaje completo.</p>
        <hr>
        <p><small>Este es un mensaje automatico de LegalFlow.</small></p>
    </body>
    </html>
    """

    # Version en texto plano del correo
    body_text = f"""
    Nuevo Mensaje

    Ha recibido un nuevo mensaje en LegalFlow:
    De: {sender_name}
    Asunto: {subject}
    {'Caso: ' + case_number if case_number else ''}

    Ingrese a LegalFlow para ver el mensaje completo.
    """

    # Envia la notificacion con ambas versiones (HTML y texto)
    return send_email(recipient_email, email_subject, body_html, body_text)


# ============================================================================
# TAREAS DE CELERY - NOTIFICACIONES DE DOCUMENTOS COMPARTIDOS
# ============================================================================

@app.task(name='send_document_shared_notification')
def send_document_shared_notification(recipient_email, recipient_name, document_name, shared_by, case_number=''):
    """
    Envia una notificacion cuando un documento es compartido con un usuario.

    Notifica al destinatario que tiene acceso a un nuevo documento
    compartido en el sistema, incluyendo informacion del documento
    y quien lo compartio.

    Parametros:
        recipient_email (str): Correo del destinatario
        recipient_name (str): Nombre del destinatario
        document_name (str): Nombre del documento compartido
        shared_by (str): Nombre de quien compartio el documento
        case_number (str, opcional): Numero de caso relacionado

    Retorna:
        bool: Resultado del envio del correo (True/False)
    """
    # Construye el asunto del correo con el nombre del documento
    subject = f"[LegalFlow] Documento compartido: {document_name}"

    # Construye el cuerpo del correo con los detalles del documento
    body_html = f"""
    <html>
    <body>
        <h2>Documento Compartido</h2>
        <p>Estimado/a {recipient_name},</p>
        <p>{shared_by} ha compartido un documento con usted:</p>
        <ul>
            <li><strong>Documento:</strong> {document_name}</li>
            {'<li><strong>Caso:</strong> ' + case_number + '</li>' if case_number else ''}
        </ul>
        <p>Ingrese a LegalFlow para acceder al documento.</p>
        <hr>
        <p><small>Este es un mensaje automatico de LegalFlow.</small></p>
    </body>
    </html>
    """

    # Envia la notificacion al destinatario
    return send_email(recipient_email, subject, body_html)


# ============================================================================
# TAREAS DE CELERY - RECORDATORIOS DE EVENTOS
# ============================================================================

@app.task(name='send_event_reminder')
def send_event_reminder(event_id, user_email, event_title, event_datetime, location='', case_number=''):
    """
    Envia un correo recordatorio sobre un evento proximo.

    Notifica al usuario sobre eventos del calendario como audiencias,
    reuniones, citas o cualquier otro compromiso programado.

    Parametros:
        event_id (int): Identificador unico del evento
        user_email (str): Correo del usuario asignado al evento
        event_title (str): Titulo o descripcion del evento
        event_datetime (str): Fecha y hora del evento
        location (str, opcional): Ubicacion donde se realizara el evento
        case_number (str, opcional): Numero de caso relacionado

    Retorna:
        bool: Resultado del envio del correo (True/False)
    """
    # Construye el asunto del correo con el titulo del evento
    subject = f"[LegalFlow] Recordatorio de Evento: {event_title}"

    # Construye el cuerpo del correo en HTML con los detalles del evento
    # Incluye ubicacion y caso solo si estan disponibles
    body_html = f"""
    <html>
    <body>
        <h2>Recordatorio de Evento</h2>
        <p>Este es un recordatorio del siguiente evento:</p>
        <ul>
            <li><strong>Evento:</strong> {event_title}</li>
            <li><strong>Fecha y hora:</strong> {event_datetime}</li>
            {'<li><strong>Ubicacion:</strong> ' + location + '</li>' if location else ''}
            {'<li><strong>Caso:</strong> ' + case_number + '</li>' if case_number else ''}
        </ul>
        <hr>
        <p><small>Este es un mensaje automatico de LegalFlow.</small></p>
    </body>
    </html>
    """

    # Version en texto plano del recordatorio
    body_text = f"""
    Recordatorio de Evento

    Evento: {event_title}
    Fecha y hora: {event_datetime}
    {'Ubicacion: ' + location if location else ''}
    {'Caso: ' + case_number if case_number else ''}
    """

    # Envia el recordatorio con ambas versiones del contenido
    return send_email(user_email, subject, body_html, body_text)


# ============================================================================
# TAREAS DE CELERY - VERIFICACION PERIODICA DE EVENTOS
# ============================================================================

@app.task(name='check_upcoming_events')
def check_upcoming_events():
    """
    Verifica eventos del dia y envia recordatorios automaticos.

    Esta tarea periodica consulta el servicio de calendario para obtener
    todos los eventos programados para el dia actual. Para cada evento
    encontrado con usuario asignado, programa el envio de un recordatorio.

    Esta tarea se ejecuta diariamente a las 7:30 AM (hora de Colombia)
    segun la configuracion de Celery Beat, permitiendo a los usuarios
    prepararse para sus compromisos del dia.

    Retorna:
        None: Esta tarea no retorna valor, pero programa tareas hijas

    Excepciones:
        Captura y registra cualquier error durante la ejecucion
    """
    try:
        # Consulta al servicio de calendario los eventos del dia actual
        response = requests.get(f'{CALENDAR_SERVICE_URL}/api/events/today/')

        # Verifica que la respuesta sea exitosa
        if response.status_code == 200:
            # Extrae la lista de eventos del JSON de respuesta
            events = response.json().get('results', [])

            # Itera sobre cada evento del dia
            for event in events:
                # Verifica si el evento tiene un usuario asignado
                if event.get('assigned_to_id'):
                    # Consulta al servicio IAM para obtener datos del usuario
                    user_response = requests.get(
                        f'{IAM_SERVICE_URL}/api/auth/users/{event["assigned_to_id"]}/'
                    )

                    # Verifica que se obtuvo el usuario exitosamente
                    if user_response.status_code == 200:
                        # Extrae los datos del usuario del JSON
                        user = user_response.json()

                        # Programa el envio del recordatorio de forma asincrona
                        send_event_reminder.delay(
                            event['id'],                    # ID del evento
                            user.get('email'),              # Correo del usuario
                            event['title'],                 # Titulo del evento
                            event['start_datetime'],        # Fecha y hora de inicio
                            event.get('location', ''),      # Ubicacion (opcional)
                            event.get('case_number', '')    # Numero de caso (opcional)
                        )

    except Exception as e:
        # Registra cualquier error durante la verificacion de eventos
        print(f"Error checking upcoming events: {str(e)}")


# ============================================================================
# CONFIGURACION DE CELERY BEAT - TAREAS PROGRAMADAS
# ============================================================================

# Configuracion del programador de tareas periodicas de Celery Beat
# Define las tareas que se ejecutan automaticamente segun un horario
app.conf.beat_schedule = {

    # Tarea: Verificacion diaria de plazos proximos a vencer
    # Se ejecuta todos los dias a las 8:00 AM hora de Colombia
    # Busca plazos que vencen en los proximos 3 dias y envia recordatorios
    'check-upcoming-deadlines-daily': {
        'task': 'check_upcoming_deadlines',          # Nombre de la tarea a ejecutar
        'schedule': crontab(hour=8, minute=0),       # Programacion: 8:00 AM diario
    },

    # Tarea: Verificacion diaria de facturas vencidas
    # Se ejecuta todos los dias a las 9:00 AM hora de Colombia
    # Busca facturas con estado 'overdue' y envia recordatorios de pago
    'check-overdue-invoices-daily': {
        'task': 'check_overdue_invoices',            # Nombre de la tarea a ejecutar
        'schedule': crontab(hour=9, minute=0),       # Programacion: 9:00 AM diario
    },

    # Tarea: Verificacion matutina de eventos del dia
    # Se ejecuta todos los dias a las 7:30 AM hora de Colombia
    # Envia recordatorios de todos los eventos programados para el dia actual
    'check-upcoming-events-morning': {
        'task': 'check_upcoming_events',             # Nombre de la tarea a ejecutar
        'schedule': crontab(hour=7, minute=30),      # Programacion: 7:30 AM diario
    },
}
