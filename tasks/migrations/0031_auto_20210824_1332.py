# Generated by Django 3.1.2 on 2021-08-24 13:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0030_auto_20210824_1258'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='telescope',
            field=models.ForeignKey(limit_choices_to={'enabled': True}, on_delete=django.db.models.deletion.DO_NOTHING, related_name='tasks', to='tasks.telescope', verbose_name='Телескоп'),
        ),
    ]
