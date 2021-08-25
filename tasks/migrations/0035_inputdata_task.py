# Generated by Django 3.1.2 on 2021-08-25 15:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0034_remove_inputdata_author'),
    ]

    operations = [
        migrations.AddField(
            model_name='inputdata',
            name='task',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='tasks_inputdata', to='tasks.task', verbose_name='Задание'),
            preserve_default=False,
        ),
    ]
