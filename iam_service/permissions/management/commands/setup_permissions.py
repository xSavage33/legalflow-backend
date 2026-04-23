from django.core.management.base import BaseCommand
from permissions.models import Role, Permission, RolePermission


class Command(BaseCommand):
    help = 'Setup initial roles and permissions'

    def handle(self, *args, **options):
        self.stdout.write('Setting up permissions...')

        # Create permissions
        permissions_data = [
            # Case permissions
            ('case.view', 'Ver casos', 'case'),
            ('case.create', 'Crear casos', 'case'),
            ('case.edit', 'Editar casos', 'case'),
            ('case.delete', 'Eliminar casos', 'case'),
            ('case.assign', 'Asignar casos', 'case'),

            # Document permissions
            ('document.view', 'Ver documentos', 'document'),
            ('document.create', 'Crear documentos', 'document'),
            ('document.edit', 'Editar documentos', 'document'),
            ('document.delete', 'Eliminar documentos', 'document'),
            ('document.download', 'Descargar documentos', 'document'),

            # Invoice permissions
            ('invoice.view', 'Ver facturas', 'invoice'),
            ('invoice.create', 'Crear facturas', 'invoice'),
            ('invoice.edit', 'Editar facturas', 'invoice'),
            ('invoice.delete', 'Eliminar facturas', 'invoice'),
            ('invoice.approve', 'Aprobar facturas', 'invoice'),

            # Time entry permissions
            ('time_entry.view', 'Ver entradas de tiempo', 'time_entry'),
            ('time_entry.create', 'Crear entradas de tiempo', 'time_entry'),
            ('time_entry.edit', 'Editar entradas de tiempo', 'time_entry'),
            ('time_entry.delete', 'Eliminar entradas de tiempo', 'time_entry'),
            ('time_entry.approve', 'Aprobar entradas de tiempo', 'time_entry'),

            # Event permissions
            ('event.view', 'Ver eventos', 'event'),
            ('event.create', 'Crear eventos', 'event'),
            ('event.edit', 'Editar eventos', 'event'),
            ('event.delete', 'Eliminar eventos', 'event'),

            # Deadline permissions
            ('deadline.view', 'Ver plazos', 'deadline'),
            ('deadline.create', 'Crear plazos', 'deadline'),
            ('deadline.edit', 'Editar plazos', 'deadline'),
            ('deadline.delete', 'Eliminar plazos', 'deadline'),

            # User permissions
            ('user.view', 'Ver usuarios', 'user'),
            ('user.create', 'Crear usuarios', 'user'),
            ('user.edit', 'Editar usuarios', 'user'),
            ('user.delete', 'Eliminar usuarios', 'user'),

            # Report permissions
            ('report.view', 'Ver reportes', 'report'),
            ('report.export', 'Exportar reportes', 'report'),

            # Client permissions
            ('client.view', 'Ver clientes', 'client'),
            ('client.create', 'Crear clientes', 'client'),
            ('client.edit', 'Editar clientes', 'client'),
            ('client.delete', 'Eliminar clientes', 'client'),

            # Message permissions
            ('message.view', 'Ver mensajes', 'message'),
            ('message.send', 'Enviar mensajes', 'message'),
        ]

        permissions = {}
        for codename, name, content_type in permissions_data:
            perm, created = Permission.objects.get_or_create(
                codename=codename,
                defaults={'name': name, 'content_type': content_type}
            )
            permissions[codename] = perm
            status = 'created' if created else 'exists'
            self.stdout.write(f'  Permission {codename}: {status}')

        # Create roles
        roles_data = [
            ('admin', 'Administrador del sistema', True),
            ('partner', 'Socio del bufete', True),
            ('associate', 'Abogado asociado', True),
            ('paralegal', 'Paralegal', True),
            ('client', 'Cliente', True),
        ]

        roles = {}
        for name, description, is_system in roles_data:
            role, created = Role.objects.get_or_create(
                name=name,
                defaults={'description': description, 'is_system': is_system}
            )
            roles[name] = role
            status = 'created' if created else 'exists'
            self.stdout.write(f'  Role {name}: {status}')

        # Assign permissions to roles
        role_permissions = {
            'admin': list(permissions.keys()),  # Admin has all permissions
            'partner': [
                'case.view', 'case.create', 'case.edit', 'case.delete', 'case.assign',
                'document.view', 'document.create', 'document.edit', 'document.delete', 'document.download',
                'invoice.view', 'invoice.create', 'invoice.edit', 'invoice.delete', 'invoice.approve',
                'time_entry.view', 'time_entry.create', 'time_entry.edit', 'time_entry.delete', 'time_entry.approve',
                'event.view', 'event.create', 'event.edit', 'event.delete',
                'deadline.view', 'deadline.create', 'deadline.edit', 'deadline.delete',
                'user.view',
                'report.view', 'report.export',
                'client.view', 'client.create', 'client.edit',
                'message.view', 'message.send',
            ],
            'associate': [
                'case.view', 'case.create', 'case.edit',
                'document.view', 'document.create', 'document.edit', 'document.download',
                'invoice.view', 'invoice.create',
                'time_entry.view', 'time_entry.create', 'time_entry.edit',
                'event.view', 'event.create', 'event.edit',
                'deadline.view', 'deadline.create', 'deadline.edit',
                'client.view',
                'report.view',
                'message.view', 'message.send',
            ],
            'paralegal': [
                'case.view',
                'document.view', 'document.create', 'document.download',
                'time_entry.view', 'time_entry.create',
                'event.view', 'event.create',
                'deadline.view',
                'client.view',
                'message.view', 'message.send',
            ],
            'client': [
                'case.view',
                'document.view', 'document.download',
                'invoice.view',
                'time_entry.view',
                'event.view',
                'deadline.view',
                'message.view', 'message.send',
            ],
        }

        for role_name, perm_codenames in role_permissions.items():
            role = roles[role_name]
            for codename in perm_codenames:
                perm = permissions.get(codename)
                if perm:
                    RolePermission.objects.get_or_create(
                        role=role,
                        permission=perm
                    )

        self.stdout.write(self.style.SUCCESS('Permissions setup completed!'))
