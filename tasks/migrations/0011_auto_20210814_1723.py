# Generated by Django 3.1.2 on 2021-08-14 17:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0010_taskresult'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='status',
            field=models.SmallIntegerField(choices=[(1, 'Создано'), (2, 'Получено телескопом'), (3, 'Выполнено'), (4, 'Не удалось выполнить')], default=1, verbose_name='Статус'),
        ),
    ]
