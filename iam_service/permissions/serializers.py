"""
===========================================================================================
ARCHIVO: serializers.py
MODULO: permissions (Servicio IAM - Identity and Access Management)
===========================================================================================

PROPOSITO:
Este archivo define los serializadores de Django REST Framework para el modulo de
permisos del servicio IAM. Los serializadores manejan la conversion de datos entre
modelos Django y formatos JSON para las APIs REST.

SERIALIZADORES DEFINIDOS:
- PermissionSerializer: Serializa permisos individuales
- RolePermissionSerializer: Serializa relaciones rol-permiso
- RoleSerializer: Serializa roles con sus permisos (CRUD completo)
- RoleListSerializer: Version optimizada para listados de roles
- ObjectPermissionSerializer: Serializa permisos a nivel de objeto
- CheckPermissionSerializer: Valida peticiones de verificacion de permisos
- GrantPermissionSerializer: Valida peticiones de otorgamiento/revocacion de permisos

AUTOR: Equipo de Desarrollo LegalFlow
===========================================================================================
"""

# Importacion del modulo de serializadores de Django REST Framework
# Proporciona las clases base y campos para crear serializadores
from rest_framework import serializers

# Importacion de los modelos del modulo de permisos
from .models import Role, Permission, RolePermission, ObjectPermission


class PermissionSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Permission.

    Convierte instancias de Permission a/desde formato JSON.
    Se utiliza para operaciones CRUD basicas sobre permisos.

    Campos:
        - id: Identificador unico del permiso (UUID, solo lectura)
        - codename: Codigo unico del permiso (ej: 'case.view')
        - name: Nombre descriptivo del permiso
        - description: Descripcion detallada
        - content_type: Tipo de recurso al que aplica
        - created_at: Fecha de creacion (solo lectura)
    """

    class Meta:
        """
        Configuracion del serializador.
        """
        # Modelo Django asociado a este serializador
        model = Permission

        # Campos a incluir en la serializacion
        fields = ['id', 'codename', 'name', 'description', 'content_type', 'created_at']

        # Campos que solo pueden ser leidos, no escritos
        # id y created_at son generados automaticamente
        read_only_fields = ['id', 'created_at']


class RolePermissionSerializer(serializers.ModelSerializer):
    """
    Serializador para la relacion muchos a muchos entre Role y Permission.

    Permite serializar la informacion completa del permiso junto con
    la relacion, y tambien permite escribir solo el ID del permiso
    para crear nuevas relaciones.

    Campos de lectura:
        - id: ID de la relacion
        - permission: Objeto permiso completo (anidado)
        - created_at: Fecha de creacion de la relacion

    Campos de escritura:
        - permission_id: UUID del permiso a asociar
    """

    # Campo anidado de solo lectura que muestra el permiso completo
    # read_only=True: Solo se incluye en las respuestas, no en las peticiones
    permission = PermissionSerializer(read_only=True)

    # Campo de solo escritura para recibir el ID del permiso
    # write_only=True: Solo se usa en peticiones, no en respuestas
    permission_id = serializers.UUIDField(write_only=True)

    class Meta:
        """
        Configuracion del serializador.
        """
        # Modelo asociado
        model = RolePermission

        # Campos incluidos (tanto lectura como escritura)
        fields = ['id', 'permission', 'permission_id', 'created_at']

        # Campos generados automaticamente
        read_only_fields = ['id', 'created_at']


class RoleSerializer(serializers.ModelSerializer):
    """
    Serializador completo para el modelo Role.

    Incluye la logica para crear y actualizar roles junto con sus
    permisos asociados. Permite asignar permisos mediante una lista
    de IDs de permisos.

    Campos de lectura:
        - id: UUID del rol
        - name: Nombre del rol
        - description: Descripcion del rol
        - is_system: Indica si es un rol del sistema
        - permissions: Lista de permisos asociados (objetos completos)
        - created_at: Fecha de creacion
        - updated_at: Fecha de actualizacion

    Campos de escritura:
        - permission_ids: Lista de UUIDs de permisos a asignar
    """

    # Campo calculado que retorna la lista de permisos del rol
    # SerializerMethodField usa un metodo personalizado (get_permissions)
    permissions = serializers.SerializerMethodField()

    # Campo de solo escritura para recibir lista de IDs de permisos
    # child=serializers.UUIDField(): Cada elemento de la lista debe ser UUID
    # write_only=True: No se incluye en las respuestas
    # required=False: No es obligatorio proporcionar permisos
    permission_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )

    class Meta:
        """
        Configuracion del serializador.
        """
        # Modelo asociado
        model = Role

        # Todos los campos del rol mas los campos calculados/escritura
        fields = ['id', 'name', 'description', 'is_system', 'permissions', 'permission_ids', 'created_at', 'updated_at']

        # Campos que no pueden ser modificados por el usuario
        # is_system se controla internamente para proteger roles criticos
        read_only_fields = ['id', 'is_system', 'created_at', 'updated_at']

    def get_permissions(self, obj):
        """
        Metodo para obtener la lista de permisos asociados al rol.

        Este metodo es llamado por SerializerMethodField para calcular
        el valor del campo 'permissions'.

        Args:
            obj (Role): Instancia del rol siendo serializado

        Returns:
            list: Lista de diccionarios con datos de cada permiso
        """
        # Obtener todas las relaciones RolePermission para este rol
        # select_related('permission') optimiza la consulta haciendo JOIN
        role_permissions = RolePermission.objects.filter(role=obj).select_related('permission')

        # Serializar cada permiso y retornar como lista
        return [PermissionSerializer(rp.permission).data for rp in role_permissions]

    def create(self, validated_data):
        """
        Metodo para crear un nuevo rol con sus permisos.

        Extrae los IDs de permisos, crea el rol, y luego crea
        las relaciones RolePermission para cada permiso.

        Args:
            validated_data (dict): Datos validados del formulario

        Returns:
            Role: Nueva instancia de rol creada
        """
        # Extraer la lista de IDs de permisos (lista vacia si no se proporcionan)
        permission_ids = validated_data.pop('permission_ids', [])

        # Crear el rol con los datos restantes
        role = Role.objects.create(**validated_data)

        # Crear relaciones RolePermission para cada permiso
        for perm_id in permission_ids:
            try:
                # Intentar obtener el permiso por su ID
                permission = Permission.objects.get(id=perm_id)
                # Crear la relacion rol-permiso
                RolePermission.objects.create(role=role, permission=permission)
            except Permission.DoesNotExist:
                # Si el permiso no existe, simplemente ignorarlo
                # Esto evita errores si se proporciona un ID invalido
                pass

        # Retornar el rol creado
        return role

    def update(self, instance, validated_data):
        """
        Metodo para actualizar un rol existente y sus permisos.

        Si se proporcionan permission_ids, elimina todos los permisos
        actuales y crea nuevas relaciones con los permisos especificados.

        Args:
            instance (Role): Instancia del rol a actualizar
            validated_data (dict): Datos validados del formulario

        Returns:
            Role: Instancia del rol actualizada
        """
        # Extraer la lista de IDs de permisos (None si no se proporcionan)
        permission_ids = validated_data.pop('permission_ids', None)

        # Actualizar cada atributo del rol con los nuevos valores
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Guardar los cambios del rol
        instance.save()

        # Solo actualizar permisos si se proporciono la lista
        # (None significa que no se quiere cambiar los permisos)
        if permission_ids is not None:
            # Eliminar todas las relaciones de permisos existentes
            RolePermission.objects.filter(role=instance).delete()

            # Crear nuevas relaciones con los permisos especificados
            for perm_id in permission_ids:
                try:
                    permission = Permission.objects.get(id=perm_id)
                    RolePermission.objects.create(role=instance, permission=permission)
                except Permission.DoesNotExist:
                    # Ignorar IDs de permisos invalidos
                    pass

        # Retornar la instancia actualizada
        return instance


class RoleListSerializer(serializers.ModelSerializer):
    """
    Serializador optimizado para listados de roles.

    Incluye solo la informacion basica necesaria para mostrar en
    listas, con un conteo de permisos en lugar de la lista completa.
    Esto mejora el rendimiento al reducir la cantidad de datos.

    Campos:
        - id: UUID del rol
        - name: Nombre del rol
        - description: Descripcion
        - is_system: Indica si es rol del sistema
        - permission_count: Numero de permisos asignados (calculado)
        - created_at: Fecha de creacion
    """

    # Campo calculado para el conteo de permisos
    permission_count = serializers.SerializerMethodField()

    class Meta:
        """
        Configuracion del serializador.
        """
        # Modelo asociado
        model = Role

        # Campos basicos mas el conteo de permisos
        fields = ['id', 'name', 'description', 'is_system', 'permission_count', 'created_at']

    def get_permission_count(self, obj):
        """
        Metodo para contar los permisos asignados al rol.

        Args:
            obj (Role): Instancia del rol siendo serializado

        Returns:
            int: Numero de permisos asignados al rol
        """
        # Contar las relaciones RolePermission para este rol
        return RolePermission.objects.filter(role=obj).count()


class ObjectPermissionSerializer(serializers.ModelSerializer):
    """
    Serializador para permisos a nivel de objeto.

    Serializa la informacion de ObjectPermission incluyendo el
    codigo del permiso como campo adicional para facilitar su uso.

    Campos:
        - id: UUID del permiso de objeto
        - user_id: UUID del usuario que tiene el permiso
        - permission: UUID del permiso (clave foranea)
        - permission_codename: Codigo del permiso (solo lectura)
        - object_type: Tipo de objeto (ej: 'case', 'document')
        - object_id: UUID del objeto especifico
        - granted_by_id: UUID del usuario que otorgo el permiso
        - created_at: Fecha de creacion
    """

    # Campo de solo lectura que extrae el codename del permiso relacionado
    # source='permission.codename': Indica de donde obtener el valor
    permission_codename = serializers.CharField(source='permission.codename', read_only=True)

    class Meta:
        """
        Configuracion del serializador.
        """
        # Modelo asociado
        model = ObjectPermission

        # Todos los campos del modelo mas el campo calculado
        fields = ['id', 'user_id', 'permission', 'permission_codename', 'object_type', 'object_id', 'granted_by_id', 'created_at']

        # Campos generados automaticamente
        read_only_fields = ['id', 'created_at']


class CheckPermissionSerializer(serializers.Serializer):
    """
    Serializador para validar peticiones de verificacion de permisos.

    Este serializador no esta asociado a ningun modelo Django.
    Se utiliza para validar los datos que envian otros microservicios
    cuando quieren verificar si un usuario tiene un permiso.

    Campos requeridos:
        - user_id: UUID del usuario a verificar
        - permission_codename: Codigo del permiso a verificar

    Campos opcionales:
        - object_type: Tipo de objeto (para permisos a nivel de objeto)
        - object_id: ID del objeto especifico
    """

    # ID del usuario cuyo permiso se quiere verificar
    user_id = serializers.UUIDField()

    # Codigo del permiso a verificar (ej: 'case.view', 'document.edit')
    permission_codename = serializers.CharField()

    # Tipo de objeto para verificacion de permisos a nivel de objeto
    # required=False: No es necesario para permisos basados solo en rol
    # allow_null=True: Permite enviar null explicitamente
    object_type = serializers.CharField(required=False, allow_null=True)

    # ID del objeto especifico para verificacion de permisos a nivel de objeto
    object_id = serializers.UUIDField(required=False, allow_null=True)


class GrantPermissionSerializer(serializers.Serializer):
    """
    Serializador para validar peticiones de otorgamiento o revocacion de permisos.

    Se utiliza tanto para otorgar como para revocar permisos a nivel de objeto.
    Todos los campos son requeridos ya que se necesita identificar exactamente
    que permiso sobre que objeto se quiere otorgar/revocar a que usuario.

    Campos requeridos:
        - user_id: UUID del usuario que recibira/perdera el permiso
        - permission_codename: Codigo del permiso a otorgar/revocar
        - object_type: Tipo de objeto (ej: 'case', 'document')
        - object_id: UUID del objeto especifico
    """

    # ID del usuario al que se otorgara o revocara el permiso
    user_id = serializers.UUIDField()

    # Codigo del permiso a otorgar o revocar
    permission_codename = serializers.CharField()

    # Tipo de objeto sobre el que se otorgara el permiso
    object_type = serializers.CharField()

    # ID del objeto especifico sobre el que se otorgara el permiso
    object_id = serializers.UUIDField()
