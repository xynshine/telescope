# Generated by Django 3.1.2 on 2021-08-30 08:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0037_auto_20210830_0824'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inputdata',
            name='task',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='tasks_inputdata', to='tasks.task', verbose_name='Задание'),
        ),
    ]
