import jwt
from django.conf import settings


def decode_jwt(token):
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=['HS256']
        )
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, 'Token has expired'
    except jwt.InvalidTokenError as e:
        return None, f'Invalid token: {str(e)}'


def get_user_from_token(request):
    """Extract user info from the Authorization header."""
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')

    if not auth_header.startswith('Bearer '):
        return None, 'No bearer token provided'

    token = auth_header.split(' ')[1]
    payload, error = decode_jwt(token)

    if error:
        return None, error

    return payload, None
