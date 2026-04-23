import pytest
from django.urls import reverse
from permissions.models import Role, Permission, RolePermission


@pytest.mark.django_db
class TestRoles:
    def test_create_role(self, admin_client):
        url = reverse('role_list_create')
        response = admin_client.post(url, {
            'name': 'custom_role',
            'description': 'A custom role'
        }, format='json')

        assert response.status_code == 201
        assert Role.objects.filter(name='custom_role').exists()

    def test_list_roles(self, admin_client):
        Role.objects.create(name='test_role')
        url = reverse('role_list_create')
        response = admin_client.get(url)

        assert response.status_code == 200
        assert len(response.data['results']) >= 1

    def test_delete_system_role_fails(self, admin_client):
        role = Role.objects.create(name='system_role', is_system=True)
        url = reverse('role_detail', kwargs={'id': role.id})
        response = admin_client.delete(url)

        assert response.status_code == 400


@pytest.mark.django_db
class TestPermissions:
    def test_list_permissions(self, admin_client):
        Permission.objects.create(
            codename='test.permission',
            name='Test Permission',
            content_type='case'
        )
        url = reverse('permission_list')
        response = admin_client.get(url)

        assert response.status_code == 200

    def test_filter_permissions_by_content_type(self, admin_client):
        Permission.objects.create(
            codename='case.test',
            name='Case Test',
            content_type='case'
        )
        Permission.objects.create(
            codename='doc.test',
            name='Doc Test',
            content_type='document'
        )

        url = reverse('permission_list')
        response = admin_client.get(url, {'content_type': 'case'})

        assert response.status_code == 200


@pytest.mark.django_db
class TestCheckPermission:
    def test_check_permission_superuser(self, admin_client, admin_user):
        Permission.objects.create(
            codename='test.permission',
            name='Test Permission',
            content_type='case'
        )

        url = reverse('check_permission')
        response = admin_client.post(url, {
            'user_id': str(admin_user.id),
            'permission_codename': 'test.permission'
        }, format='json')

        assert response.status_code == 200
        assert response.data['has_permission'] is True

    def test_check_permission_role_based(self, admin_client, user):
        # Create permission and assign to role
        perm = Permission.objects.create(
            codename='case.view',
            name='View Cases',
            content_type='case'
        )
        role = Role.objects.create(name='associate')
        RolePermission.objects.create(role=role, permission=perm)

        url = reverse('check_permission')
        response = admin_client.post(url, {
            'user_id': str(user.id),
            'permission_codename': 'case.view'
        }, format='json')

        assert response.status_code == 200
        assert response.data['has_permission'] is True

    def test_check_permission_denied(self, admin_client, user):
        url = reverse('check_permission')
        response = admin_client.post(url, {
            'user_id': str(user.id),
            'permission_codename': 'nonexistent.permission'
        }, format='json')

        assert response.status_code == 200
        assert response.data['has_permission'] is False
