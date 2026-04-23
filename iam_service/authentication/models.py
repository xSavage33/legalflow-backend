"""
Modelos de autenticacion del servicio IAM.
Define el modelo de Usuario personalizado y el registro de actividades.
"""

# Importacion de UUID para generar identificadores unicos
import uuid

# Importacion de clases base de Django para modelos de usuario personalizados
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

# Importacion del modulo de modelos de Django
from django.db import models


class UserManager(BaseUserManager):
    """
    Gestor personalizado para el modelo de Usuario.
    Proporciona metodos para crear usuarios normales y superusuarios.
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        Crea y guarda un usuario normal con el email y contrasena proporcionados.

        Parametros:
            email (str): Direccion de correo electronico del usuario (requerido)
            password (str): Contrasena del usuario (opcional)
            **extra_fields: Campos adicionales como first_name, last_name, etc.

        Retorna:
            User: Instancia del usuario creado

        Lanza:
            ValueError: Si no se proporciona un email
        """
        # Validacion de que el email sea proporcionado
        if not email:
            raise ValueError('El email es requerido')

        # Normaliza el email (convierte el dominio a minusculas)
        email = self.normalize_email(email)

        # Crea la instancia del usuario con los campos proporcionados
        user = self.model(email=email, **extra_fields)

        # Establece la contrasena de forma segura (genera hash)
        user.set_password(password)

        # Guarda el usuario en la base de datos
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Crea y guarda un superusuario con privilegios de administrador.

        Parametros:
            email (str): Direccion de correo electronico del superusuario
            password (str): Contrasena del superusuario
            **extra_fields: Campos adicionales

        Retorna:
            User: Instancia del superusuario creado

        Lanza:
            ValueError: Si is_staff o is_superuser no son True
        """
        # Establece valores por defecto para superusuario
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin')

        # Validaciones de seguridad para superusuarios
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser debe tener is_superuser=True.')

        # Delega la creacion al metodo create_user
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Modelo de Usuario personalizado para el sistema LegalFlow.
    Utiliza email como identificador unico en lugar de username.
    Implementa control de acceso basado en roles (RBAC).
    """

    # Definicion de los roles disponibles en el sistema
    ROLE_CHOICES = [
        ('admin', 'Administrador'),      # Acceso total al sistema
        ('partner', 'Socio'),            # Socio del bufete, acceso amplio
        ('associate', 'Asociado'),       # Abogado asociado, acceso limitado
        ('paralegal', 'Paralegal'),      # Asistente legal, acceso restringido
        ('client', 'Cliente'),           # Cliente del bufete, solo portal de cliente
    ]

    # Identificador unico universal (UUID) como clave primaria
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Email como campo de identificacion unico
    email = models.EmailField(unique=True)

    # Nombre del usuario
    first_name = models.CharField(max_length=100)

    # Apellido del usuario
    last_name = models.CharField(max_length=100)

    # Rol del usuario que determina sus permisos
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='associate'
    )

    # Telefono de contacto (opcional)
    phone = models.CharField(max_length=20, blank=True)

    # Indica si el usuario puede iniciar sesion
    is_active = models.BooleanField(default=True)

    # Indica si el usuario puede acceder al panel de administracion de Django
    is_staff = models.BooleanField(default=False)

    # Marca de tiempo de creacion del usuario
    created_at = models.DateTimeField(auto_now_add=True)

    # Marca de tiempo de ultima actualizacion
    updated_at = models.DateTimeField(auto_now=True)

    # Fecha y hora del ultimo inicio de sesion
    last_login = models.DateTimeField(null=True, blank=True)

    # Asigna el gestor personalizado
    objects = UserManager()

    # Define el campo que se usara como nombre de usuario
    USERNAME_FIELD = 'email'

    # Campos requeridos adicionales al crear usuario por linea de comandos
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        """Metadatos del modelo User."""
        # Nombre de la tabla en la base de datos
        db_table = 'users'
        # Ordenamiento por defecto (mas recientes primero)
        ordering = ['-created_at']

    def __str__(self):
        """
        Representacion en cadena del usuario.
        Retorna el email y el rol del usuario.
        """
        return f"{self.email} ({self.get_role_display()})"

    @property
    def full_name(self):
        """
        Propiedad que retorna el nombre completo del usuario.
        Combina nombre y apellido.
        """
        return f"{self.first_name} {self.last_name}"

    def get_permissions_list(self):
        """
        Obtiene la lista de permisos del usuario basados en su rol.
        Incluye permisos a nivel de objeto si django-guardian esta configurado.

        Retorna:
            list: Lista de codigos de permisos asignados al usuario
        """
        # Importacion de RolePermission para obtener permisos basados en rol
        from permissions.models import RolePermission

        # Obtiene los permisos asociados al rol del usuario
        role_perms = RolePermission.objects.filter(
            role__name=self.role
        ).values_list('permission__codename', flat=True)

        # Retorna lista unica de permisos (sin duplicados)
        return list(set(role_perms))


class UserActivity(models.Model):
    """
    Modelo para registrar la actividad de los usuarios.
    Utilizado para auditoria y seguimiento de seguridad.
    Registra inicios de sesion, cierres de sesion, cambios de contrasena, etc.
    """

    # Tipos de acciones que se pueden registrar
    ACTION_CHOICES = [
        ('login', 'Inicio de sesion'),
        ('logout', 'Cierre de sesion'),
        ('login_failed', 'Intento de inicio de sesion fallido'),
        ('password_change', 'Cambio de contrasena'),
        ('profile_update', 'Actualizacion de perfil'),
    ]

    # Identificador unico del registro de actividad
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Usuario que realizo la accion
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activities'
    )

    # Tipo de accion realizada
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)

    # Direccion IP desde donde se realizo la accion
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    # Informacion del navegador/cliente del usuario
    user_agent = models.TextField(blank=True)

    # Momento en que se registro la actividad
    timestamp = models.DateTimeField(auto_now_add=True)

    # Detalles adicionales de la actividad en formato JSON
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        """Metadatos del modelo UserActivity."""
        # Nombre de la tabla en la base de datos
        db_table = 'user_activities'
        # Ordenamiento por defecto (mas recientes primero)
        ordering = ['-timestamp']
        # Nombre plural para el panel de administracion
        verbose_name_plural = 'User activities'

    def __str__(self):
        """
        Representacion en cadena del registro de actividad.
        Muestra el email del usuario, la accion y la fecha.
        """
        return f"{self.user.email} - {self.action} at {self.timestamp}"
