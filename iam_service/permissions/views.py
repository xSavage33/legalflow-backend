"""
===========================================================================================
ARCHIVO: views.py
MODULO: permissions (Servicio IAM - Identity and Access Management)
===========================================================================================

PROPOSITO:
Este archivo define las vistas (endpoints de API) para el sistema de permisos.
Proporciona endpoints para:
- Gestion de roles (CRUD)
- Listado y creacion de permisos
- Verificacion de permisos (servicio central de autorizacion)
- Otorgamiento y revocacion de permisos a nivel de objeto
- Consulta de permisos de usuarios y objetos

ENDPOINTS PRINCIPALES:
- RoleListCreateView: GET/POST /roles/
- RoleDetailView: GET/PUT/DELETE /roles/{id}/
- PermissionListView: GET /permissions/
- PermissionCreateView: POST /permissions/
- CheckPermissionView: POST /check-permission/
- GrantObjectPermissionView: POST /grant-permission/
- RevokeObjectPermissionView: POST /revoke-permission/
- UserPermissionsView: GET /users/{user_id}/permissions/
- ObjectPermissionsView: GET /objects/{object_type}/{object_id}/permissions/

AUTOR: Equipo de Desarrollo LegalFlow
===========================================================================================
"""

# Importacion de clases genericas de Django REST Framework
# generics proporciona vistas basadas en clases para operaciones CRUD comunes
# status contiene los codigos de estado HTTP como constantes
from rest_framework import generics, status

# Importacion de la clase Response para construir respuestas HTTP
from rest_framework.response import Response

# Importacion de APIView, la clase base para vistas personalizadas
from rest_framework.views import APIView

# Importacion de get_object_or_404 de Django
# Esta funcion obtiene un objeto o lanza un error 404 si no existe
from django.shortcuts import get_object_or_404

# Importacion del modelo User del modulo de autenticacion
from authentication.models import User

# Importacion de los modelos del modulo de permisos
from .models import Role, Permission, RolePermission, ObjectPermission

# Importacion de los serializadores para convertir datos
from .serializers import (
    RoleSerializer,              # Serializador completo para roles
    RoleListSerializer,          # Serializador optimizado para listados de roles
    PermissionSerializer,        # Serializador para permisos
    ObjectPermissionSerializer,  # Serializador para permisos a nivel de objeto
    CheckPermissionSerializer,   # Serializador para peticiones de verificacion
    GrantPermissionSerializer,   # Serializador para otorgar/revocar permisos
)


class RoleListCreateView(generics.ListCreateAPIView):
    """
    Vista para listar y crear roles.

    Endpoints:
        GET /roles/ - Lista todos los roles del sistema
        POST /roles/ - Crea un nuevo rol

    La vista utiliza diferentes serializadores segun el metodo HTTP:
    - GET: RoleListSerializer (optimizado, solo informacion basica)
    - POST: RoleSerializer (completo, permite asignar permisos)

    Atributos:
        queryset: Conjunto de datos base (todos los roles)
    """

    # QuerySet base que retorna todos los roles
    queryset = Role.objects.all()

    def get_serializer_class(self):
        """
        Retorna la clase de serializador apropiada segun el metodo HTTP.

        Este metodo permite usar diferentes serializadores para diferentes
        operaciones en la misma vista.

        Returns:
            class: Clase del serializador a utilizar
        """
        # Para solicitudes GET (listado), usar serializador optimizado
        if self.request.method == 'GET':
            return RoleListSerializer
        # Para POST (creacion), usar serializador completo
        return RoleSerializer


class RoleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Vista para obtener, actualizar o eliminar un rol especifico.

    Endpoints:
        GET /roles/{id}/ - Obtiene un rol por su ID
        PUT /roles/{id}/ - Actualiza un rol existente
        PATCH /roles/{id}/ - Actualiza parcialmente un rol
        DELETE /roles/{id}/ - Elimina un rol (si no es del sistema)

    Atributos:
        queryset: Conjunto de datos base
        serializer_class: Serializador a utilizar
        lookup_field: Campo usado para buscar el objeto (por defecto 'pk')
    """

    # QuerySet base
    queryset = Role.objects.all()

    # Serializador para operaciones de detalle
    serializer_class = RoleSerializer

    # Campo usado para buscar el rol en la URL (ej: /roles/{id}/)
    lookup_field = 'id'

    def destroy(self, request, *args, **kwargs):
        """
        Sobreescribe el metodo destroy para prevenir eliminacion de roles del sistema.

        Los roles marcados como is_system=True son criticos para el funcionamiento
        del sistema y no pueden ser eliminados.

        Args:
            request: Objeto Request de Django REST Framework
            *args: Argumentos posicionales adicionales
            **kwargs: Argumentos de palabra clave adicionales

        Returns:
            Response: Respuesta HTTP con resultado de la operacion
        """
        # Obtener el objeto rol a eliminar
        role = self.get_object()

        # Verificar si es un rol del sistema
        if role.is_system:
            # Retornar error 400 si se intenta eliminar un rol del sistema
            return Response(
                {'error': 'No se puede eliminar un rol del sistema.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Si no es rol del sistema, proceder con la eliminacion normal
        return super().destroy(request, *args, **kwargs)


class PermissionListView(generics.ListAPIView):
    """
    Vista para listar permisos del sistema.

    Endpoint:
        GET /permissions/ - Lista todos los permisos
        GET /permissions/?content_type=case - Filtra por tipo de contenido

    Soporta filtrado por tipo de contenido mediante query parameter.

    Atributos:
        queryset: Conjunto de datos base (todos los permisos)
        serializer_class: Serializador para permisos
    """

    # QuerySet base
    queryset = Permission.objects.all()

    # Serializador para permisos
    serializer_class = PermissionSerializer

    def get_queryset(self):
        """
        Sobreescribe get_queryset para permitir filtrado por tipo de contenido.

        Si se proporciona el parametro 'content_type' en la URL,
        filtra los permisos por ese tipo.

        Returns:
            QuerySet: Permisos filtrados o todos los permisos
        """
        # Obtener el queryset base
        queryset = super().get_queryset()

        # Obtener el parametro content_type de los query params
        content_type = self.request.query_params.get('content_type')

        # Si se especifico un tipo de contenido, filtrar
        if content_type:
            queryset = queryset.filter(content_type=content_type)

        # Retornar el queryset (filtrado o completo)
        return queryset


class PermissionCreateView(generics.CreateAPIView):
    """
    Vista para crear nuevos permisos.

    Endpoint:
        POST /permissions/create/ - Crea un nuevo permiso

    Esta vista esta separada de PermissionListView para permitir
    diferentes niveles de permisos de acceso si es necesario.

    Atributos:
        queryset: Conjunto de datos base
        serializer_class: Serializador para crear permisos
    """

    # QuerySet base
    queryset = Permission.objects.all()

    # Serializador para creacion de permisos
    serializer_class = PermissionSerializer


class CheckPermissionView(APIView):
    """
    Vista central de verificacion de permisos para microservicios.

    Este es el endpoint principal que otros microservicios utilizan para
    verificar si un usuario tiene un permiso especifico. Actua como el
    servicio central de autorizacion del sistema.

    Endpoint:
        POST /check-permission/

    Flujo de verificacion:
    1. Verificar que el usuario existe y esta activo
    2. Si es superusuario, tiene todos los permisos
    3. Verificar permisos basados en rol
    4. Si se especifica un objeto, verificar permisos a nivel de objeto

    Request Body:
        {
            "user_id": "uuid",
            "permission_codename": "string",
            "object_type": "string" (opcional),
            "object_id": "uuid" (opcional)
        }

    Response:
        {
            "has_permission": boolean,
            "reason": "string"
        }
    """

    def post(self, request):
        """
        Maneja las solicitudes POST para verificar permisos.

        Args:
            request: Objeto Request con los datos de verificacion

        Returns:
            Response: Resultado de la verificacion de permisos
        """
        # Validar los datos de entrada usando el serializador
        serializer = CheckPermissionSerializer(data=request.data)
        # raise_exception=True lanza automaticamente errores 400 si la validacion falla
        serializer.is_valid(raise_exception=True)

        # Extraer los datos validados del serializador
        user_id = serializer.validated_data['user_id']
        permission_codename = serializer.validated_data['permission_codename']
        # .get() retorna None si la clave no existe
        object_type = serializer.validated_data.get('object_type')
        object_id = serializer.validated_data.get('object_id')

        # PASO 1: Obtener el usuario
        try:
            # Intentar obtener el usuario por su ID
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            # Si el usuario no existe, denegar el permiso
            return Response({
                'has_permission': False,
                'reason': 'User not found'
            })

        # PASO 2: Verificar que el usuario este activo
        if not user.is_active:
            # Usuarios inactivos no tienen ningun permiso
            return Response({
                'has_permission': False,
                'reason': 'User is inactive'
            })

        # PASO 3: Verificar si es superusuario
        # Los superusuarios tienen todos los permisos automaticamente
        if user.is_superuser:
            return Response({
                'has_permission': True,
                'reason': 'Superuser'
            })

        # PASO 4: Verificar permisos basados en rol
        # Busca si existe una relacion RolePermission que conecte
        # el rol del usuario con el permiso solicitado
        has_role_permission = RolePermission.objects.filter(
            role__name=user.role,                    # Filtrar por nombre del rol del usuario
            permission__codename=permission_codename  # Filtrar por codigo del permiso
        ).exists()

        if has_role_permission:
            # Si no se especifica objeto, el permiso de rol es suficiente
            if not object_type or not object_id:
                return Response({
                    'has_permission': True,
                    'reason': 'Role permission'
                })

            # PASO 5: Si se especifica objeto, verificar permiso a nivel de objeto
            has_object_permission = ObjectPermission.objects.filter(
                user_id=user_id,
                permission__codename=permission_codename,
                object_type=object_type,
                object_id=object_id
            ).exists()

            if has_object_permission:
                return Response({
                    'has_permission': True,
                    'reason': 'Object permission'
                })

        # PASO 6: Verificar permiso de objeto incluso sin permiso de rol
        # Esto permite otorgar acceso a objetos especificos sin dar acceso general
        if object_type and object_id:
            has_object_permission = ObjectPermission.objects.filter(
                user_id=user_id,
                permission__codename=permission_codename,
                object_type=object_type,
                object_id=object_id
            ).exists()

            if has_object_permission:
                return Response({
                    'has_permission': True,
                    'reason': 'Object permission'
                })

        # Si ninguna verificacion fue exitosa, denegar el permiso
        return Response({
            'has_permission': False,
            'reason': 'No matching permission found'
        })


class GrantObjectPermissionView(APIView):
    """
    Vista para otorgar permisos a nivel de objeto a usuarios.

    Permite dar a un usuario acceso a un recurso especifico del sistema,
    como un caso particular o un documento especifico.

    Endpoint:
        POST /grant-permission/

    Request Body:
        {
            "user_id": "uuid",
            "permission_codename": "string",
            "object_type": "string",
            "object_id": "uuid"
        }

    Response:
        {
            "granted": true,
            "created": boolean,
            "permission": {...}
        }
    """

    def post(self, request):
        """
        Maneja las solicitudes POST para otorgar permisos.

        Args:
            request: Objeto Request con los datos del permiso

        Returns:
            Response: Resultado de la operacion con el permiso creado
        """
        # Validar los datos de entrada
        serializer = GrantPermissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Obtener el objeto Permission por su codigo
        # get_object_or_404 lanza 404 si el permiso no existe
        permission = get_object_or_404(
            Permission,
            codename=serializer.validated_data['permission_codename']
        )

        # Crear o obtener el permiso de objeto
        # get_or_create retorna una tupla (objeto, fue_creado)
        # Si ya existe, simplemente lo retorna; si no, lo crea
        obj_perm, created = ObjectPermission.objects.get_or_create(
            user_id=serializer.validated_data['user_id'],
            permission=permission,
            object_type=serializer.validated_data['object_type'],
            object_id=serializer.validated_data['object_id'],
            # defaults: valores usados solo si se crea un nuevo registro
            defaults={'granted_by_id': request.user.id}
        )

        # Retornar respuesta con el resultado
        # 201 CREATED si se creo nuevo, 200 OK si ya existia
        return Response({
            'granted': True,
            'created': created,
            'permission': ObjectPermissionSerializer(obj_perm).data
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class RevokeObjectPermissionView(APIView):
    """
    Vista para revocar permisos a nivel de objeto de usuarios.

    Elimina el acceso de un usuario a un recurso especifico.

    Endpoint:
        POST /revoke-permission/

    Request Body:
        {
            "user_id": "uuid",
            "permission_codename": "string",
            "object_type": "string",
            "object_id": "uuid"
        }

    Response:
        {
            "revoked": boolean,
            "deleted_count": number
        }
    """

    def post(self, request):
        """
        Maneja las solicitudes POST para revocar permisos.

        Args:
            request: Objeto Request con los datos del permiso a revocar

        Returns:
            Response: Resultado de la operacion
        """
        # Validar los datos de entrada
        serializer = GrantPermissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Eliminar el permiso de objeto si existe
        # delete() retorna una tupla (numero_eliminados, diccionario_detalles)
        deleted, _ = ObjectPermission.objects.filter(
            user_id=serializer.validated_data['user_id'],
            permission__codename=serializer.validated_data['permission_codename'],
            object_type=serializer.validated_data['object_type'],
            object_id=serializer.validated_data['object_id']
        ).delete()

        # Retornar resultado de la operacion
        # revoked es True si se elimino al menos un registro
        return Response({
            'revoked': deleted > 0,
            'deleted_count': deleted
        })


class UserPermissionsView(APIView):
    """
    Vista para obtener todos los permisos de un usuario especifico.

    Retorna tanto los permisos basados en rol como los permisos
    a nivel de objeto del usuario.

    Endpoint:
        GET /users/{user_id}/permissions/

    Response:
        {
            "user_id": "uuid",
            "role": "string",
            "is_superuser": boolean,
            "role_permissions": [...],
            "object_permissions": [...]
        }
    """

    def get(self, request, user_id):
        """
        Maneja las solicitudes GET para obtener permisos de usuario.

        Args:
            request: Objeto Request
            user_id: UUID del usuario a consultar

        Returns:
            Response: Permisos del usuario o error 404
        """
        # Intentar obtener el usuario
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            # Retornar 404 si el usuario no existe
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Obtener permisos basados en rol
        # Filtra permisos que estan asignados a roles con el nombre del rol del usuario
        # distinct() elimina duplicados
        role_permissions = Permission.objects.filter(
            permission_roles__role__name=user.role
        ).distinct()

        # Obtener permisos a nivel de objeto
        # select_related('permission') optimiza la consulta haciendo JOIN
        # en lugar de consultas separadas
        object_permissions = ObjectPermission.objects.filter(
            user_id=user_id
        ).select_related('permission')

        # Retornar toda la informacion de permisos del usuario
        return Response({
            'user_id': str(user.id),
            'role': user.role,
            'is_superuser': user.is_superuser,
            'role_permissions': PermissionSerializer(role_permissions, many=True).data,
            'object_permissions': ObjectPermissionSerializer(object_permissions, many=True).data
        })


class ObjectPermissionsView(APIView):
    """
    Vista para obtener todos los usuarios que tienen permisos sobre un objeto.

    Util para ver quien tiene acceso a un recurso especifico del sistema.

    Endpoint:
        GET /objects/{object_type}/{object_id}/permissions/

    Response:
        {
            "object_type": "string",
            "object_id": "uuid",
            "permissions": [...]
        }
    """

    def get(self, request, object_type, object_id):
        """
        Maneja las solicitudes GET para obtener permisos de un objeto.

        Args:
            request: Objeto Request
            object_type: Tipo del objeto (ej: 'case', 'document')
            object_id: UUID del objeto

        Returns:
            Response: Lista de permisos asignados sobre el objeto
        """
        # Obtener todos los permisos de objeto para el objeto especificado
        # select_related optimiza las consultas relacionadas
        object_permissions = ObjectPermission.objects.filter(
            object_type=object_type,
            object_id=object_id
        ).select_related('permission')

        # Retornar la informacion del objeto y sus permisos
        return Response({
            'object_type': object_type,
            'object_id': str(object_id),
            'permissions': ObjectPermissionSerializer(object_permissions, many=True).data
        })
