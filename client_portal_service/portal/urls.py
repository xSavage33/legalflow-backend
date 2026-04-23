"""
Modulo de Configuracion de URLs del Portal de Clientes (Client Portal Service)

Este archivo define las rutas URL para la aplicacion 'portal' del servicio
de portal de clientes. Cada URL mapea a una vista especifica que maneja
las peticiones HTTP correspondientes.

El modulo organiza las URLs en tres grupos logicos:
    1. Vistas de datos del cliente (proxy a otros servicios):
       - /my-cases/: Lista de casos del cliente
       - /my-cases/<uuid>/: Detalle de un caso especifico
       - /my-documents/: Documentos de todos los casos
       - /my-invoices/: Facturas del cliente
       - /my-time-entries/: Registros de tiempo

    2. Preferencias del cliente:
       - /preferences/: Ver y actualizar preferencias

    3. Mensajeria:
       - /messages/: Lista y creacion de mensajes
       - /messages/unread/: Mensajes no leidos
       - /messages/<uuid>/: Detalle de un mensaje
       - /messages/<uuid>/read/: Marcar mensaje como leido

Todas las URLs requieren autenticacion JWT valida.

Autor: Equipo LegalFlow
"""

# Importacion de la funcion path de Django para definir patrones de URL
# path() es la forma moderna de definir URLs en Django (desde version 2.0)
# Permite definir rutas con convertidores de tipo como <uuid:id>, <int:pk>, etc.
from django.urls import path

# Importacion del modulo views que contiene todas las clases de vistas
# El punto (.) indica importacion relativa desde el mismo paquete (portal)
from . import views

# Lista de patrones de URL para esta aplicacion
# urlpatterns es una variable especial que Django busca automaticamente
# Cada elemento es un objeto path() que asocia una ruta con una vista
urlpatterns = [
    # ==========================================================================
    # SECCION 1: VISTAS DE DATOS DEL CLIENTE (PROXY A OTROS SERVICIOS)
    # Estas vistas actuan como intermediarios hacia otros microservicios
    # del sistema LegalFlow, agregando filtros de seguridad por cliente.
    # ==========================================================================

    # Ruta para obtener la lista de casos del cliente autenticado
    # URL: /api/portal/my-cases/
    # Metodo: GET
    # Vista: MyCasesView - Proxea al servicio de casos (Matter Service)
    # Nombre: 'my_cases' - Usado para reverse() y en templates
    path('my-cases/', views.MyCasesView.as_view(), name='my_cases'),

    # Ruta para obtener el detalle de un caso especifico del cliente
    # URL: /api/portal/my-cases/<uuid>/
    # Metodo: GET
    # Parametro: case_id - UUID del caso a consultar
    # Vista: MyCaseDetailView - Verifica que el caso pertenezca al cliente
    # Nombre: 'my_case_detail'
    path('my-cases/<uuid:case_id>/', views.MyCaseDetailView.as_view(), name='my_case_detail'),

    # Ruta para obtener todos los documentos de los casos del cliente
    # URL: /api/portal/my-documents/
    # Metodo: GET
    # Vista: MyDocumentsView - Agrega documentos de todos los casos del cliente
    # Nombre: 'my_documents'
    path('my-documents/', views.MyDocumentsView.as_view(), name='my_documents'),

    # Ruta para descargar un documento especifico
    # URL: /api/portal/my-documents/<uuid>/download/
    # Metodo: GET
    # Vista: MyDocumentDownloadView - Verifica permisos y proxea la descarga
    # Nombre: 'my_document_download'
    path('my-documents/<uuid:document_id>/download/', views.MyDocumentDownloadView.as_view(), name='my_document_download'),

    # Ruta para obtener las facturas del cliente
    # URL: /api/portal/my-invoices/
    # Metodo: GET
    # Vista: MyInvoicesView - Proxea al servicio de facturacion (Billing Service)
    # Nombre: 'my_invoices'
    path('my-invoices/', views.MyInvoicesView.as_view(), name='my_invoices'),

    # Ruta para obtener los registros de tiempo de los casos del cliente
    # URL: /api/portal/my-time-entries/
    # Metodo: GET
    # Vista: MyTimeEntriesView - Actualmente retorna lista vacia (info interna)
    # Nombre: 'my_time_entries'
    path('my-time-entries/', views.MyTimeEntriesView.as_view(), name='my_time_entries'),

    # ==========================================================================
    # SECCION 2: PREFERENCIAS DEL CLIENTE
    # Permite al cliente gestionar sus configuraciones personales.
    # ==========================================================================

    # Ruta para ver y actualizar las preferencias del cliente
    # URL: /api/portal/preferences/
    # Metodos: GET (ver), PUT (actualizar todo), PATCH (actualizar parcialmente)
    # Vista: ClientPreferenceView - Usa get_or_create para asegurar que existan
    # Nombre: 'preferences'
    path('preferences/', views.ClientPreferenceView.as_view(), name='preferences'),

    # ==========================================================================
    # SECCION 3: SISTEMA DE MENSAJERIA
    # Permite la comunicacion entre clientes y el equipo legal del bufete.
    # ==========================================================================

    # Ruta para listar y crear mensajes
    # URL: /api/portal/messages/
    # Metodos: GET (listar mensajes), POST (crear nuevo mensaje)
    # Vista: MessageListCreateView - Soporta filtrado y busqueda
    # Parametros de consulta soportados:
    #   - ?case_id=<uuid>: Filtrar por caso
    #   - ?status=<sent|delivered|read>: Filtrar por estado
    #   - ?search=<texto>: Buscar en asunto y contenido
    # Nombre: 'message_list_create'
    path('messages/', views.MessageListCreateView.as_view(), name='message_list_create'),

    # Ruta para obtener mensajes no leidos del cliente
    # URL: /api/portal/messages/unread/
    # Metodo: GET
    # Vista: UnreadMessagesView - Filtra mensajes con estado 'sent' o 'delivered'
    # Nombre: 'unread_messages'
    # NOTA: Esta ruta debe estar ANTES de messages/<uuid:id>/ para evitar conflictos
    path('messages/unread/', views.UnreadMessagesView.as_view(), name='unread_messages'),

    # Ruta para obtener el detalle de un mensaje especifico
    # URL: /api/portal/messages/<uuid>/
    # Metodo: GET
    # Parametro: id - UUID del mensaje a consultar
    # Vista: MessageDetailView - Marca automaticamente como leido si es destinatario
    # Nombre: 'message_detail'
    path('messages/<uuid:id>/', views.MessageDetailView.as_view(), name='message_detail'),

    # Ruta para marcar explicitamente un mensaje como leido
    # URL: /api/portal/messages/<uuid>/read/
    # Metodo: POST
    # Parametro: id - UUID del mensaje a marcar como leido
    # Vista: MarkMessageReadView - Solo el destinatario puede marcar como leido
    # Nombre: 'mark_message_read'
    path('messages/<uuid:id>/read/', views.MarkMessageReadView.as_view(), name='mark_message_read'),

    # ========================================================================
    # ENDPOINT INTERNO: NOTIFICACIONES DEL SISTEMA
    # ========================================================================

    # URL: /api/portal/internal/notification/
    # Metodo: POST
    # Uso: Otros microservicios envian notificaciones a clientes
    # Seguridad: Requiere header X-Service-Token
    # Vista: SystemNotificationView
    # Nombre: 'system_notification'
    path('internal/notification/', views.SystemNotificationView.as_view(), name='system_notification'),
]
