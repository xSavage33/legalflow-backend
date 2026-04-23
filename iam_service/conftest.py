import pytest
from rest_framework.test import APIClient
from authentication.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_data():
    return {
        'email': 'test@example.com',
        'password': 'TestPass123!',
        'password_confirm': 'TestPass123!',
        'first_name': 'Test',
        'last_name': 'User',
    }


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email='testuser@example.com',
        password='TestPass123!',
        first_name='Test',
        last_name='User',
        role='associate'
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        email='admin@example.com',
        password='AdminPass123!',
        first_name='Admin',
        last_name='User'
    )


@pytest.fixture
def authenticated_client(api_client, user):
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client
