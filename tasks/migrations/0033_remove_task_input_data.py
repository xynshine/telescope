# Generated by Django 3.1.2 on 2021-08-25 15:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0032_auto_20210825_1157'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='task',
            name='input_data',
        ),
    ]
