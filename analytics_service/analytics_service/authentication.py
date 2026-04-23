import jwt
from django.conf import settings
from rest_framework import authentication, exceptions

class JWTUser:
    def __init__(self, payload):
        self.id = payload.get('user_id')
        self.email = payload.get('email', '')
        self.role = payload.get('role', 'associate')
        self.is_authenticated = True
        self.is_active = True

    @property
    def is_staff(self):
        return self.role in ['admin', 'partner']

class JWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return None
        token = auth_header.split(' ')[1]
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed('Invalid token')
        return (JWTUser(payload), token)
