# Generated by Django 3.1.2 on 2021-08-25 15:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0035_inputdata_task'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='inputdata',
            name='created_at',
        ),
    ]
