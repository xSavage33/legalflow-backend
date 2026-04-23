import pytest
from django.urls import reverse
from authentication.models import User


@pytest.mark.django_db
class TestUserRegistration:
    def test_register_user_success(self, api_client, user_data):
        url = reverse('register')
        response = api_client.post(url, user_data, format='json')

        assert response.status_code == 201
        assert 'tokens' in response.data
        assert 'user' in response.data
        assert User.objects.filter(email=user_data['email']).exists()

    def test_register_user_password_mismatch(self, api_client, user_data):
        user_data['password_confirm'] = 'DifferentPass123!'
        url = reverse('register')
        response = api_client.post(url, user_data, format='json')

        assert response.status_code == 400

    def test_register_user_duplicate_email(self, api_client, user_data, user):
        user_data['email'] = user.email
        url = reverse('register')
        response = api_client.post(url, user_data, format='json')

        assert response.status_code == 400


@pytest.mark.django_db
class TestUserLogin:
    def test_login_success(self, api_client, user):
        url = reverse('login')
        response = api_client.post(url, {
            'email': 'testuser@example.com',
            'password': 'TestPass123!'
        }, format='json')

        assert response.status_code == 200
        assert 'tokens' in response.data
        assert 'user' in response.data

    def test_login_invalid_credentials(self, api_client, user):
        url = reverse('login')
        response = api_client.post(url, {
            'email': 'testuser@example.com',
            'password': 'WrongPassword!'
        }, format='json')

        assert response.status_code == 401

    def test_login_inactive_user(self, api_client, user):
        user.is_active = False
        user.save()

        url = reverse('login')
        response = api_client.post(url, {
            'email': 'testuser@example.com',
            'password': 'TestPass123!'
        }, format='json')

        assert response.status_code == 401


@pytest.mark.django_db
class TestUserProfile:
    def test_get_profile(self, authenticated_client, user):
        url = reverse('profile')
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert response.data['email'] == user.email

    def test_update_profile(self, authenticated_client, user):
        url = reverse('profile')
        response = authenticated_client.patch(url, {
            'first_name': 'Updated'
        }, format='json')

        assert response.status_code == 200
        user.refresh_from_db()
        assert user.first_name == 'Updated'

    def test_get_profile_unauthenticated(self, api_client):
        url = reverse('profile')
        response = api_client.get(url)

        assert response.status_code == 401


@pytest.mark.django_db
class TestPasswordChange:
    def test_change_password_success(self, authenticated_client, user):
        url = reverse('password_change')
        response = authenticated_client.post(url, {
            'old_password': 'TestPass123!',
            'new_password': 'NewPass456!',
            'new_password_confirm': 'NewPass456!'
        }, format='json')

        assert response.status_code == 200
        user.refresh_from_db()
        assert user.check_password('NewPass456!')

    def test_change_password_wrong_old(self, authenticated_client):
        url = reverse('password_change')
        response = authenticated_client.post(url, {
            'old_password': 'WrongOldPass!',
            'new_password': 'NewPass456!',
            'new_password_confirm': 'NewPass456!'
        }, format='json')

        assert response.status_code == 400


@pytest.mark.django_db
class TestUserList:
    def test_list_users(self, admin_client):
        url = reverse('user_list')
        response = admin_client.get(url)

        assert response.status_code == 200
        assert 'results' in response.data

    def test_filter_users_by_role(self, admin_client, user):
        url = reverse('user_list')
        response = admin_client.get(url, {'role': 'associate'})

        assert response.status_code == 200
