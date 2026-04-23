"""
serializers.py - Serializadores para el Servicio de Documentos

Este archivo contiene los serializadores de Django REST Framework que se encargan
de convertir los datos entre formatos Python/Django y JSON para el API REST.

Los serializadores realizan las siguientes funciones:
- Validacion de datos de entrada
- Serializacion de objetos Django a JSON para respuestas
- Deserializacion de JSON a objetos Django para creacion/actualizacion
- Control de campos visibles y de solo lectura

Serializadores incluidos:
- DocumentVersionSerializer: Para versiones de documentos
- DocumentAccessLogSerializer: Para registros de auditoria
- DocumentShareSerializer: Para permisos de comparticion
- DocumentListSerializer: Para listado resumido de documentos
- DocumentDetailSerializer: Para detalle completo de documentos
- DocumentUploadSerializer: Para subida de nuevos documentos
- DocumentUpdateSerializer: Para actualizacion de documentos
- NewVersionSerializer: Para crear nuevas versiones
- FolderSerializer: Para carpetas
- ShareDocumentSerializer: Para compartir documentos

Autor: Equipo de Desarrollo LegalFlow
"""

# Importacion del modulo serializers de Django REST Framework
from rest_framework import serializers

# Importacion de todos los modelos necesarios
from .models import Document, DocumentVersion, DocumentAccessLog, DocumentShare, Folder


class DocumentVersionSerializer(serializers.ModelSerializer):
    """
    Serializador para versiones de documentos.

    Convierte instancias de DocumentVersion a/desde JSON.
    La mayoria de campos son de solo lectura ya que se generan automaticamente.
    """

    class Meta:
        """
        Configuracion del serializador.

        Define el modelo asociado, los campos a incluir,
        y cuales son de solo lectura.
        """
        # Modelo asociado a este serializador
        model = DocumentVersion

        # Lista de campos a incluir en la serializacion
        fields = [
            'id',                   # UUID de la version
            'version_number',       # Numero de version
            'file',                 # Archivo de la version
            'file_size',           # Tamano en bytes
            'checksum',            # Hash SHA-256
            'changes_description', # Descripcion de cambios
            'created_by_id',       # ID del creador
            'created_by_name',     # Nombre del creador
            'created_at'           # Fecha de creacion
        ]

        # Campos que no pueden ser modificados por el cliente
        # Estos se generan automaticamente en el servidor
        read_only_fields = [
            'id',              # Se genera automaticamente con UUID
            'version_number',  # Se calcula secuencialmente
            'file_size',       # Se obtiene del archivo
            'checksum',        # Se calcula con SHA-256
            'created_by_id',   # Se obtiene del usuario autenticado
            'created_by_name', # Se obtiene del usuario autenticado
            'created_at'       # Se establece automaticamente
        ]


class DocumentAccessLogSerializer(serializers.ModelSerializer):
    """
    Serializador para registros de acceso/auditoria.

    Incluye un campo adicional 'action_display' que muestra
    la etiqueta legible de la accion en lugar del codigo interno.
    """

    # Campo calculado que obtiene la etiqueta legible de la accion
    # source='get_action_display' llama al metodo del modelo
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        """
        Configuracion del serializador de registros de acceso.
        """
        # Modelo asociado
        model = DocumentAccessLog

        # Campos incluidos en la serializacion
        fields = [
            'id',              # UUID del registro
            'action',          # Codigo de la accion (view, download, etc.)
            'action_display',  # Etiqueta legible (Visualizado, Descargado, etc.)
            'user_id',         # ID del usuario
            'user_email',      # Email del usuario
            'user_role',       # Rol del usuario
            'ip_address',      # Direccion IP del cliente
            'details',         # Detalles adicionales en JSON
            'timestamp'        # Marca de tiempo de la accion
        ]


class DocumentShareSerializer(serializers.ModelSerializer):
    """
    Serializador para permisos de comparticion de documentos.

    Maneja la serializacion de los permisos otorgados a otros usuarios
    para acceder a documentos compartidos.
    """

    class Meta:
        """
        Configuracion del serializador de comparticiones.
        """
        # Modelo asociado
        model = DocumentShare

        # Campos incluidos en la serializacion
        fields = [
            'id',                   # UUID del permiso
            'shared_with_user_id',  # ID del usuario con acceso
            'shared_with_email',    # Email del usuario con acceso
            'permission',           # Nivel de permiso (view, download, edit)
            'shared_by_id',         # ID del usuario que compartio
            'shared_by_name',       # Nombre del usuario que compartio
            'expires_at',           # Fecha de expiracion (opcional)
            'created_at'            # Fecha de creacion del permiso
        ]

        # Campos de solo lectura que se generan en el servidor
        read_only_fields = [
            'id',              # Se genera automaticamente
            'shared_by_id',    # Se obtiene del usuario autenticado
            'shared_by_name',  # Se obtiene del usuario autenticado
            'created_at'       # Se establece automaticamente
        ]


class DocumentListSerializer(serializers.ModelSerializer):
    """
    Serializador para la vista de lista de documentos.

    Proporciona una version resumida de los datos del documento
    optimizada para mostrar en listados y tablas.
    Incluye campos adicionales con etiquetas legibles para categoria y estado.
    """

    # Campo calculado que obtiene la etiqueta legible de la categoria
    # Ejemplo: 'contract' -> 'Contrato'
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    # Campo calculado que obtiene la etiqueta legible del estado
    # Ejemplo: 'draft' -> 'Borrador'
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        """
        Configuracion del serializador de lista de documentos.
        """
        # Modelo asociado
        model = Document

        # Campos incluidos - version resumida para listados
        fields = [
            'id',                # UUID del documento
            'name',              # Nombre del documento
            'category',          # Codigo de categoria
            'category_display',  # Etiqueta legible de categoria
            'status',            # Codigo de estado
            'status_display',    # Etiqueta legible de estado
            'original_filename', # Nombre original del archivo
            'file_size',         # Tamano en bytes
            'mime_type',         # Tipo MIME
            'current_version',   # Numero de version actual
            'case_id',           # ID del caso asociado
            'is_confidential',   # Si es confidencial
            'is_privileged',     # Si tiene privilegio abogado-cliente
            'tags',              # Etiquetas para clasificacion
            'created_by_name',   # Nombre del creador
            'created_at',        # Fecha de creacion
            'updated_at'         # Fecha de ultima actualizacion
        ]


class DocumentDetailSerializer(serializers.ModelSerializer):
    """
    Serializador para la vista de detalle de documentos.

    Proporciona todos los campos del documento incluyendo:
    - Historial de versiones
    - Permisos de comparticion
    - Etiquetas legibles para categoria y estado
    """

    # Serializador anidado para incluir todas las versiones del documento
    # many=True indica que es una relacion uno-a-muchos
    versions = DocumentVersionSerializer(many=True, read_only=True)

    # Serializador anidado para incluir todos los permisos de comparticion
    shares = DocumentShareSerializer(many=True, read_only=True)

    # Campo calculado para etiqueta legible de categoria
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    # Campo calculado para etiqueta legible de estado
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        """
        Configuracion del serializador de detalle de documentos.
        """
        # Modelo asociado
        model = Document

        # Todos los campos relevantes para vista de detalle
        fields = [
            'id',                     # UUID del documento
            'name',                   # Nombre del documento
            'description',            # Descripcion detallada
            'category',               # Codigo de categoria
            'category_display',       # Etiqueta legible de categoria
            'status',                 # Codigo de estado
            'status_display',         # Etiqueta legible de estado
            'file',                   # URL del archivo
            'original_filename',      # Nombre original del archivo
            'file_size',              # Tamano en bytes
            'mime_type',              # Tipo MIME del archivo
            'checksum',               # Hash SHA-256
            'current_version',        # Numero de version actual
            'case_id',                # ID del caso asociado
            'parent_document_id',     # ID del documento padre
            'is_confidential',        # Si es confidencial
            'is_privileged',          # Si tiene privilegio abogado-cliente
            'encryption_status',      # Estado de cifrado
            'tags',                   # Etiquetas
            'metadata',               # Metadatos personalizados
            'created_by_id',          # ID del creador
            'created_by_name',        # Nombre del creador
            'last_modified_by_id',    # ID del ultimo modificador
            'last_modified_by_name',  # Nombre del ultimo modificador
            'created_at',             # Fecha de creacion
            'updated_at',             # Fecha de actualizacion
            'versions',               # Lista de versiones (anidado)
            'shares'                  # Lista de comparticiones (anidado)
        ]

        # Campos que no pueden ser modificados
        read_only_fields = [
            'id',               # Se genera automaticamente
            'file_size',        # Se calcula del archivo
            'checksum',         # Se calcula con SHA-256
            'current_version',  # Se incrementa automaticamente
            'created_by_id',    # Se obtiene del usuario autenticado
            'created_by_name',  # Se obtiene del usuario autenticado
            'created_at',       # Se establece automaticamente
            'updated_at'        # Se actualiza automaticamente
        ]


class DocumentUploadSerializer(serializers.ModelSerializer):
    """
    Serializador para la subida de nuevos documentos.

    Maneja la validacion y creacion de documentos nuevos,
    incluyendo validacion del tamano maximo de archivo.
    """

    class Meta:
        """
        Configuracion del serializador de subida.
        """
        # Modelo asociado
        model = Document

        # Campos permitidos al crear un documento
        fields = [
            'name',               # Nombre del documento (requerido)
            'description',        # Descripcion (opcional)
            'category',           # Categoria (requerido)
            'file',               # Archivo a subir (requerido)
            'case_id',            # ID del caso (opcional)
            'parent_document_id', # ID del documento padre (opcional)
            'is_confidential',    # Marcar como confidencial
            'is_privileged',      # Marcar como privilegiado
            'tags',               # Etiquetas
            'metadata'            # Metadatos personalizados
        ]

    def validate_file(self, value):
        """
        Valida el archivo subido.

        Verifica que el tamano del archivo no exceda el limite configurado
        en settings.MAX_UPLOAD_SIZE.

        Args:
            value: Objeto de archivo subido

        Returns:
            value: El archivo validado

        Raises:
            ValidationError: Si el archivo excede el tamano maximo
        """
        # Importar settings para obtener el tamano maximo permitido
        from django.conf import settings

        # Verificar si el archivo excede el tamano maximo
        if value.size > settings.MAX_UPLOAD_SIZE:
            # Calcular el tamano maximo en megabytes para el mensaje
            max_mb = settings.MAX_UPLOAD_SIZE / (1024 * 1024)

            # Lanzar error de validacion con mensaje descriptivo
            raise serializers.ValidationError(
                f'El archivo excede el tamano maximo de {max_mb}MB.'
            )

        # Retornar el archivo si paso la validacion
        return value

    def create(self, validated_data):
        """
        Crea un nuevo documento con los datos validados.

        Agrega automaticamente la informacion del usuario creador,
        el nombre original del archivo y el tipo MIME.

        Args:
            validated_data: Diccionario con datos validados

        Returns:
            Document: Instancia del documento creado
        """
        import mimetypes

        # Obtener el objeto request del contexto del serializador
        request = self.context.get('request')

        # Agregar el ID del usuario creador
        validated_data['created_by_id'] = request.user.id

        # Agregar el nombre/email del usuario creador
        validated_data['created_by_name'] = request.user.email

        # Guardar el nombre original del archivo antes de procesarlo
        original_filename = validated_data['file'].name
        validated_data['original_filename'] = original_filename

        # Detectar y establecer el tipo MIME basado en la extension
        mime_type, _ = mimetypes.guess_type(original_filename)
        validated_data['mime_type'] = mime_type or 'application/octet-stream'

        # Llamar al metodo create() de la clase padre para crear el documento
        return super().create(validated_data)


class DocumentUpdateSerializer(serializers.ModelSerializer):
    """
    Serializador para actualizar documentos existentes.

    Solo permite modificar campos especificos del documento,
    excluyendo el archivo (para cambiar el archivo se debe crear una nueva version).
    """

    class Meta:
        """
        Configuracion del serializador de actualizacion.
        """
        # Modelo asociado
        model = Document

        # Campos que se pueden actualizar
        # Nota: 'file' no esta incluido - se actualiza via versiones
        fields = [
            'name',            # Nombre del documento
            'description',     # Descripcion
            'category',        # Categoria
            'status',          # Estado del documento
            'is_confidential', # Marcar como confidencial
            'is_privileged',   # Marcar como privilegiado
            'tags',            # Etiquetas
            'metadata'         # Metadatos personalizados
        ]

    def update(self, instance, validated_data):
        """
        Actualiza un documento existente.

        Registra automaticamente quien realizo la ultima modificacion.

        Args:
            instance: Instancia del documento a actualizar
            validated_data: Diccionario con datos validados

        Returns:
            Document: Instancia del documento actualizado
        """
        # Obtener el objeto request del contexto
        request = self.context.get('request')

        # Registrar el ID del usuario que realiza la modificacion
        validated_data['last_modified_by_id'] = request.user.id

        # Registrar el nombre del usuario que realiza la modificacion
        validated_data['last_modified_by_name'] = request.user.email

        # Llamar al metodo update() de la clase padre para actualizar
        return super().update(instance, validated_data)


class NewVersionSerializer(serializers.Serializer):
    """
    Serializador para crear una nueva version de un documento.

    Este es un Serializer simple (no ModelSerializer) ya que solo
    valida los datos de entrada para crear la version.
    """

    # Campo para el archivo de la nueva version (requerido)
    file = serializers.FileField()

    # Campo para describir los cambios realizados (opcional)
    changes_description = serializers.CharField(required=False, allow_blank=True)


class FolderSerializer(serializers.ModelSerializer):
    """
    Serializador para carpetas de organizacion de documentos.

    Incluye campos calculados para mostrar carpetas hijas
    y el conteo de documentos contenidos.
    """

    # Campo calculado para obtener las carpetas hijas recursivamente
    children = serializers.SerializerMethodField()

    # Campo calculado para obtener el numero de documentos en la carpeta
    document_count = serializers.SerializerMethodField()

    class Meta:
        """
        Configuracion del serializador de carpetas.
        """
        # Modelo asociado
        model = Folder

        # Campos incluidos en la serializacion
        fields = [
            'id',              # UUID de la carpeta
            'name',            # Nombre de la carpeta
            'description',     # Descripcion
            'parent',          # ID de la carpeta padre
            'case_id',         # ID del caso asociado
            'color',           # Color en formato hexadecimal
            'path',            # Ruta completa (propiedad calculada)
            'created_by_id',   # ID del creador
            'created_at',      # Fecha de creacion
            'updated_at',      # Fecha de actualizacion
            'children',        # Carpetas hijas (calculado)
            'document_count'   # Numero de documentos (calculado)
        ]

        # Campos de solo lectura
        read_only_fields = [
            'id',              # Se genera automaticamente
            'path',            # Se calcula del arbol de carpetas
            'created_by_id',   # Se obtiene del usuario autenticado
            'created_at',      # Se establece automaticamente
            'updated_at'       # Se actualiza automaticamente
        ]

    def get_children(self, obj):
        """
        Obtiene las carpetas hijas de forma recursiva.

        Este metodo serializa todas las carpetas hijas usando
        el mismo serializador, creando una estructura de arbol.

        Args:
            obj: Instancia de la carpeta actual

        Returns:
            list: Lista de carpetas hijas serializadas
        """
        # Obtener todas las carpetas que tienen esta carpeta como padre
        children = obj.children.all()

        # Serializar las carpetas hijas recursivamente
        # many=True porque puede haber multiples hijos
        return FolderSerializer(children, many=True).data

    def get_document_count(self, obj):
        """
        Obtiene el numero de documentos en la carpeta.

        Actualmente retorna 0 porque el modelo Document no tiene
        campo folder_id. Se debe implementar cuando se agregue
        la relacion documento-carpeta.

        Args:
            obj: Instancia de la carpeta

        Returns:
            int: Numero de documentos en la carpeta
        """
        # TODO: Implementar cuando se agregue folder_id al modelo Document
        # Ejemplo: return Document.objects.filter(folder_id=obj.id).count()
        return 0


class ShareDocumentSerializer(serializers.Serializer):
    """
    Serializador para la accion de compartir un documento.

    Este es un Serializer simple que valida los datos necesarios
    para crear o actualizar un permiso de comparticion.
    """

    # ID del usuario con quien se comparte (requerido)
    shared_with_user_id = serializers.UUIDField()

    # Email del usuario con quien se comparte (requerido)
    shared_with_email = serializers.EmailField()

    # Nivel de permiso a otorgar (requerido)
    # Opciones: 'view' (ver), 'download' (descargar), 'edit' (editar)
    permission = serializers.ChoiceField(choices=['view', 'download', 'edit'])

    # Fecha de expiracion del permiso (opcional)
    # Si no se especifica, el permiso no expira
    expires_at = serializers.DateTimeField(required=False, allow_null=True)
