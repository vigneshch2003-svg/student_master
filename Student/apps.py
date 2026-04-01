from django.apps import AppConfig


class StudentConfig(AppConfig):
    name = 'Student'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        from django.db.models.signals import post_migrate
        post_migrate.connect(create_groups, sender=self)


def create_groups(sender, **kwargs):
    from django.contrib.auth.models import Group
    for name in ['Admin', 'Staff', 'Student']:
        Group.objects.get_or_create(name=name)
