# Generated by Django 3.1.2 on 2021-09-02 14:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0042_auto_20210831_0926'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='satellite',
            options={'verbose_name': 'Космический объект', 'verbose_name_plural': 'Космические объекты'},
        ),
    ]
