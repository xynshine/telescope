# Generated by Django 3.1.2 on 2021-08-18 17:58

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tasks', '0012_auto_20210818_1526'),
    ]

    operations = [
        migrations.CreateModel(
            name='InputData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dt', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('data_type', models.SmallIntegerField(choices=[(0, 'Нет данных'), (1, 'Элементы орбит в формате TLE'), (2, 'Массив точек в формате JSON')], default=0, verbose_name='Тип данных')),
                ('data_tle', models.TextField(blank=True, verbose_name='Данные в формате TLE')),
                ('data_json', models.JSONField(null=True, verbose_name='Данные в формате JSON')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='tasks_inputdata', to=settings.AUTH_USER_MODEL, verbose_name='Автор входных данных')),
            ],
            options={
                'verbose_name': 'Входные данные',
                'verbose_name_plural': 'Входные данные',
            },
        ),
    ]
