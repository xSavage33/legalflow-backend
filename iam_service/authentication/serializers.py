"""
===========================================================================================
ARCHIVO: serializers.py
MODULO: authentication (Servicio IAM - Identity and Access Management)
===========================================================================================

PROPOSITO:
Este archivo define los serializadores de Django REST Framework para el modulo de
autenticacion del servicio IAM. Los serializadores convierten datos complejos
(como instancias de modelos Django) en tipos de datos nativos de Python que pueden
ser facilmente renderizados en JSON, XML u otros tipos de contenido.

FUNCIONALIDADES PRINCIPALES:
- Serializador para registro de nuevos usuarios (UserRegistrationSerializer)
- Serializador para inicio de sesion (UserLoginSerializer)
- Serializador para visualizacion de datos de usuario (UserSerializer)
- Serializador para actualizacion de perfil de usuario (UserUpdateSerializer)
- Serializador para cambio de contrasena (PasswordChangeSerializer)
- Serializador para listado de usuarios (UserListSerializer)
- Serializador para creacion de usuarios por administradores (UserCreateSerializer)
- Serializador para actualizacion de usuarios por administradores (UserAdminUpdateSerializer)
- Serializador para actividad de usuario (UserActivitySerializer)

AUTOR: Equipo de Desarrollo LegalFlow
===========================================================================================
"""

# Importacion del modulo de serializadores de Django REST Framework
# Este modulo proporciona las clases base para crear serializadores
from rest_framework import serializers

# Importacion de la funcion de validacion de contrasenas de Django
# Esta funcion valida que las contrasenas cumplan con los requisitos de seguridad
# definidos en la configuracion de Django (longitud minima, complejidad, etc.)
from django.contrib.auth.password_validation import validate_password

# Importacion de la funcion de autenticacion de Django
# Esta funcion verifica las credenciales del usuario contra la base de datos
from django.contrib.auth import authenticate

# Importacion de los modelos User y UserActivity definidos en el modulo de autenticacion
# User: Modelo personalizado de usuario que extiende AbstractUser
# UserActivity: Modelo para registrar la actividad/auditoria de los usuarios
from .models import User, UserActivity


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializador para el registro de nuevos usuarios en el sistema.

    Este serializador maneja la validacion y creacion de nuevas cuentas de usuario.
    Incluye validacion de contrasena y confirmacion de la misma para asegurar
    que el usuario ingrese correctamente su contrasena deseada.

    Campos:
        - email: Correo electronico del usuario (identificador unico)
        - password: Contrasena del usuario (solo escritura, validada)
        - password_confirm: Confirmacion de contrasena (solo escritura)
        - first_name: Nombre del usuario
        - last_name: Apellido del usuario
        - phone: Numero de telefono (opcional)
        - role: Rol del usuario en el sistema (opcional)
    """

    # Campo de contrasena con validacion de seguridad
    # write_only=True: Este campo solo se usa para entrada, nunca se incluye en la salida
    # validators=[validate_password]: Aplica las validaciones de contrasena de Django
    password = serializers.CharField(write_only=True, validators=[validate_password])

    # Campo de confirmacion de contrasena
    # write_only=True: Solo se usa para validacion, no se almacena ni se retorna
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        """
        Clase Meta que define la configuracion del serializador.
        Especifica el modelo asociado y los campos a incluir.
        """
        # Modelo de Django asociado a este serializador
        model = User

        # Lista de campos que seran serializados/deserializados
        fields = ['email', 'password', 'password_confirm', 'first_name', 'last_name', 'phone', 'role']

        # Configuracion adicional para campos especificos
        # El campo 'role' no es requerido durante el registro
        extra_kwargs = {
            'role': {'required': False}
        }

    def validate(self, attrs):
        """
        Metodo de validacion a nivel de objeto.

        Valida que la contrasena y su confirmacion coincidan.
        Este metodo se ejecuta despues de las validaciones individuales de cada campo.

        Args:
            attrs (dict): Diccionario con los datos validados de cada campo

        Returns:
            dict: Diccionario de atributos validados si la validacion es exitosa

        Raises:
            serializers.ValidationError: Si las contrasenas no coinciden
        """
        # Comparar contrasena con su confirmacion
        if attrs['password'] != attrs['password_confirm']:
            # Lanzar error de validacion si no coinciden
            raise serializers.ValidationError({'password_confirm': 'Las contraseñas no coinciden.'})
        # Retornar los atributos validados
        return attrs

    def create(self, validated_data):
        """
        Metodo para crear una nueva instancia de usuario.

        Elimina el campo de confirmacion de contrasena (no se almacena)
        y utiliza el metodo create_user del manager de User para crear
        el usuario con la contrasena correctamente hasheada.

        Args:
            validated_data (dict): Datos validados del formulario de registro

        Returns:
            User: Nueva instancia de usuario creada
        """
        # Eliminar el campo password_confirm ya que no se almacena en la base de datos
        validated_data.pop('password_confirm')

        # Crear el usuario usando el manager personalizado
        # create_user hashea la contrasena automaticamente
        user = User.objects.create_user(**validated_data)

        # Retornar la instancia del usuario creado
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializador para el inicio de sesion de usuarios.

    Este serializador valida las credenciales del usuario (email y contrasena)
    y retorna el objeto usuario si las credenciales son validas.
    No esta basado en un modelo (hereda de Serializer, no ModelSerializer).

    Campos:
        - email: Correo electronico del usuario
        - password: Contrasena del usuario (solo escritura)
    """

    # Campo para el correo electronico con validacion de formato email
    email = serializers.EmailField()

    # Campo para la contrasena
    # write_only=True: La contrasena nunca se incluye en las respuestas
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """
        Metodo de validacion que autentica al usuario.

        Utiliza el sistema de autenticacion de Django para verificar
        las credenciales. Si son validas, adjunta el objeto usuario
        a los datos validados.

        Args:
            attrs (dict): Diccionario con email y password

        Returns:
            dict: Atributos validados con el objeto usuario incluido

        Raises:
            serializers.ValidationError: Si las credenciales son invalidas
                                         o la cuenta esta desactivada
        """
        # Obtener email y password de los atributos
        email = attrs.get('email')
        password = attrs.get('password')

        # Intentar autenticar al usuario usando el email como username
        # Django authenticate busca en el backend de autenticacion configurado
        user = authenticate(username=email, password=password)

        # Verificar si la autenticacion fue exitosa
        if not user:
            # Lanzar error si las credenciales son invalidas
            raise serializers.ValidationError('Credenciales inválidas.')

        # Verificar si la cuenta del usuario esta activa
        if not user.is_active:
            # Lanzar error si la cuenta esta desactivada
            raise serializers.ValidationError('La cuenta está desactivada.')

        # Adjuntar el objeto usuario a los atributos para uso posterior
        attrs['user'] = user

        # Retornar los atributos validados
        return attrs


class UserSerializer(serializers.ModelSerializer):
    """
    Serializador principal para visualizacion de datos de usuario.

    Este serializador se utiliza para mostrar informacion completa del usuario,
    incluyendo campos calculados como el nombre completo y la lista de permisos.
    Es el serializador usado para el perfil de usuario y respuestas de API.

    Campos:
        - id: Identificador unico del usuario (UUID)
        - email: Correo electronico
        - first_name: Nombre
        - last_name: Apellido
        - full_name: Nombre completo (campo calculado de solo lectura)
        - role: Rol del usuario
        - phone: Telefono
        - is_active: Estado de activacion de la cuenta
        - created_at: Fecha de creacion
        - updated_at: Fecha de ultima actualizacion
        - last_login: Fecha del ultimo inicio de sesion
        - permissions: Lista de permisos del usuario (campo calculado)
    """

    # Campo de solo lectura para el nombre completo
    # Obtiene su valor del metodo/propiedad full_name del modelo User
    full_name = serializers.ReadOnlyField()

    # Campo calculado para obtener la lista de permisos del usuario
    # SerializerMethodField permite definir un metodo personalizado para obtener el valor
    permissions = serializers.SerializerMethodField()

    class Meta:
        """
        Configuracion del serializador.
        Define el modelo y los campos a serializar.
        """
        # Modelo asociado
        model = User

        # Lista completa de campos a incluir en la serializacion
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'phone', 'is_active', 'created_at', 'updated_at',
            'last_login', 'permissions'
        ]

        # Campos que solo pueden ser leidos, no modificados
        read_only_fields = ['id', 'email', 'created_at', 'updated_at', 'last_login']

    def get_permissions(self, obj):
        """
        Metodo para obtener la lista de permisos del usuario.

        Este metodo es llamado automaticamente por SerializerMethodField
        para calcular el valor del campo 'permissions'.

        Args:
            obj (User): Instancia del usuario siendo serializado

        Returns:
            list: Lista de nombres de permisos del usuario
        """
        # Llamar al metodo del modelo User que retorna la lista de permisos
        return obj.get_permissions_list()


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializador para actualizacion de perfil de usuario por el propio usuario.

    Este serializador permite a los usuarios actualizar su informacion basica
    de perfil. Solo incluye campos que el usuario puede modificar por si mismo
    (no incluye email, rol ni estado de activacion).

    Campos permitidos para actualizacion:
        - first_name: Nombre
        - last_name: Apellido
        - phone: Numero de telefono
    """

    class Meta:
        """
        Configuracion del serializador.
        """
        # Modelo asociado
        model = User

        # Solo estos campos pueden ser actualizados por el usuario
        fields = ['first_name', 'last_name', 'phone']


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializador para el cambio de contrasena.

    Permite a los usuarios cambiar su contrasena actual por una nueva.
    Requiere la contrasena actual para verificacion de identidad.

    Campos:
        - old_password: Contrasena actual (solo escritura)
        - new_password: Nueva contrasena (solo escritura, validada)
        - new_password_confirm: Confirmacion de nueva contrasena (solo escritura)
    """

    # Campo para la contrasena actual
    old_password = serializers.CharField(write_only=True)

    # Campo para la nueva contrasena con validacion de seguridad
    new_password = serializers.CharField(write_only=True, validators=[validate_password])

    # Campo para confirmar la nueva contrasena
    new_password_confirm = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        """
        Metodo de validacion especifico para el campo old_password.

        Verifica que la contrasena actual proporcionada sea correcta
        comparandola con la contrasena almacenada del usuario.

        Args:
            value (str): Contrasena actual proporcionada

        Returns:
            str: La contrasena si es valida

        Raises:
            serializers.ValidationError: Si la contrasena es incorrecta
        """
        # Obtener el usuario desde el contexto del request
        user = self.context['request'].user

        # Verificar si la contrasena proporcionada es correcta
        if not user.check_password(value):
            # Lanzar error si la contrasena no coincide
            raise serializers.ValidationError('Contraseña actual incorrecta.')

        # Retornar el valor si es valido
        return value

    def validate(self, attrs):
        """
        Metodo de validacion a nivel de objeto.

        Verifica que la nueva contrasena y su confirmacion coincidan.

        Args:
            attrs (dict): Diccionario con los campos validados

        Returns:
            dict: Atributos validados

        Raises:
            serializers.ValidationError: Si las contrasenas no coinciden
        """
        # Verificar que las nuevas contrasenas coincidan
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': 'Las nuevas contraseñas no coinciden.'})

        # Retornar los atributos validados
        return attrs


class UserListSerializer(serializers.ModelSerializer):
    """
    Serializador optimizado para listados de usuarios.

    Este serializador incluye solo los campos necesarios para mostrar
    usuarios en una lista, reduciendo la cantidad de datos transferidos
    y mejorando el rendimiento.

    Campos:
        - id: Identificador unico
        - email: Correo electronico
        - first_name: Nombre
        - last_name: Apellido
        - full_name: Nombre completo (calculado)
        - role: Rol del usuario
        - phone: Telefono
        - is_active: Estado de activacion
        - created_at: Fecha de creacion
    """

    # Campo de solo lectura para el nombre completo
    full_name = serializers.ReadOnlyField()

    class Meta:
        """
        Configuracion del serializador para listados.
        """
        # Modelo asociado
        model = User

        # Campos incluidos en el listado
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'role', 'phone', 'is_active', 'created_at']


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializador para la creacion de usuarios por administradores.

    Este serializador permite a los administradores crear nuevas cuentas
    de usuario, incluyendo la capacidad de establecer el rol y el estado
    de activacion desde el momento de la creacion.

    A diferencia de UserRegistrationSerializer, este serializador:
    - No requiere confirmacion de contrasena
    - Permite establecer el rol directamente
    - Permite crear usuarios inactivos

    Campos:
        - email: Correo electronico (requerido)
        - password: Contrasena (solo escritura, validada)
        - first_name: Nombre
        - last_name: Apellido
        - phone: Telefono
        - role: Rol del usuario
        - is_active: Estado de activacion
    """

    # Campo de contrasena con validacion de seguridad de Django
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        """
        Configuracion del serializador.
        """
        # Modelo asociado
        model = User

        # Campos disponibles para la creacion de usuarios
        fields = ['email', 'password', 'first_name', 'last_name', 'phone', 'role', 'is_active']

    def create(self, validated_data):
        """
        Metodo para crear un nuevo usuario.

        Extrae la contrasena de los datos validados, crea el usuario
        y luego establece la contrasena de forma segura (hasheada).

        Args:
            validated_data (dict): Datos validados del formulario

        Returns:
            User: Nueva instancia de usuario creada
        """
        # Extraer la contrasena de los datos validados
        password = validated_data.pop('password')

        # Crear instancia de usuario sin guardar en la base de datos aun
        user = User(**validated_data)

        # Establecer la contrasena de forma segura (hashea la contrasena)
        user.set_password(password)

        # Guardar el usuario en la base de datos
        user.save()

        # Retornar el usuario creado
        return user


class UserAdminUpdateSerializer(serializers.ModelSerializer):
    """
    Serializador para la actualizacion de usuarios por administradores.

    Este serializador permite a los administradores actualizar todos los
    campos de un usuario, incluyendo la capacidad de cambiar el rol,
    desactivar cuentas y restablecer contrasenas.

    Campos:
        - first_name: Nombre
        - last_name: Apellido
        - phone: Telefono
        - role: Rol del usuario
        - is_active: Estado de activacion
        - password: Nueva contrasena (opcional, solo escritura)
    """

    # Campo de contrasena opcional para reseteo
    # required=False: No es necesario proporcionar contrasena para actualizar otros campos
    password = serializers.CharField(write_only=True, required=False, validators=[validate_password])

    class Meta:
        """
        Configuracion del serializador.
        """
        # Modelo asociado
        model = User

        # Campos disponibles para actualizacion por administradores
        fields = ['first_name', 'last_name', 'phone', 'role', 'is_active', 'password']

    def update(self, instance, validated_data):
        """
        Metodo para actualizar un usuario existente.

        Actualiza los campos proporcionados y, si se incluye una nueva
        contrasena, la establece de forma segura.

        Args:
            instance (User): Instancia del usuario a actualizar
            validated_data (dict): Datos validados del formulario

        Returns:
            User: Instancia del usuario actualizada
        """
        # Extraer la contrasena si fue proporcionada (None si no)
        password = validated_data.pop('password', None)

        # Actualizar cada atributo del usuario con los nuevos valores
        for attr, value in validated_data.items():
            # setattr establece el valor de un atributo en un objeto
            setattr(instance, attr, value)

        # Si se proporciono una nueva contrasena, establecerla de forma segura
        if password:
            instance.set_password(password)

        # Guardar los cambios en la base de datos
        instance.save()

        # Retornar la instancia actualizada
        return instance


class UserActivitySerializer(serializers.ModelSerializer):
    """
    Serializador para el registro de actividad de usuarios.

    Este serializador se utiliza para mostrar el historial de actividades
    y acciones realizadas por los usuarios en el sistema (auditoria).

    Campos:
        - id: Identificador unico del registro de actividad
        - action: Tipo de accion realizada (login, logout, etc.)
        - ip_address: Direccion IP desde donde se realizo la accion
        - timestamp: Fecha y hora de la accion
        - details: Detalles adicionales de la accion (JSON)
    """

    class Meta:
        """
        Configuracion del serializador.
        """
        # Modelo asociado para el registro de actividad
        model = UserActivity

        # Campos incluidos en la serializacion de actividad
        fields = ['id', 'action', 'ip_address', 'timestamp', 'details']
