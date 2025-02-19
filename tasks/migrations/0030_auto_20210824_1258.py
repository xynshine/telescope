# Generated by Django 3.1.2 on 2021-08-24 12:58

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tasks', '0029_auto_20210824_1132'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='author',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='tasks', to=settings.AUTH_USER_MODEL, verbose_name='Автор задания'),
        ),
        migrations.AlterField(
            model_name='task',
            name='end_dt',
            field=models.DateTimeField(blank=True, editable=False, null=True, verbose_name='Дата и время конца наблюдения'),
        ),
        migrations.AlterField(
            model_name='task',
            name='end_jd',
            field=models.FloatField(editable=False, null=True, verbose_name='Юлианское время конца наблюдения'),
        ),
        migrations.AlterField(
            model_name='task',
            name='jdn',
            field=models.IntegerField(editable=False, null=True, verbose_name='Юлианская дата начала наблюдения'),
        ),
        migrations.AlterField(
            model_name='task',
            name='start_dt',
            field=models.DateTimeField(blank=True, editable=False, null=True, verbose_name='Дата и время начала наблюдения'),
        ),
        migrations.AlterField(
            model_name='task',
            name='start_jd',
            field=models.FloatField(editable=False, null=True, verbose_name='Юлианское время начала наблюдения'),
        ),
        migrations.AlterField(
            model_name='task',
            name='status',
            field=models.SmallIntegerField(choices=[(0, 'Черновик'), (1, 'Создано'), (2, 'Получено телескопом'), (3, 'Выполнено'), (4, 'Не удалось выполнить')], default=0, editable=False, verbose_name='Статус задания'),
        ),
    ]
