# Generated by Django 3.1.2 on 2021-09-07 12:36

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tasks', '0048_remove_inputdata_expected_sat'),
    ]

    operations = [
        migrations.AddField(
            model_name='telescope',
            name='user',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='telescopes', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь телескопа'),
        ),
    ]
