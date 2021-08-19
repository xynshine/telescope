# Generated by Django 3.1.2 on 2021-08-19 12:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0018_auto_20210819_1156'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='tledata',
            options={'verbose_name': 'Данные в формате TLE', 'verbose_name_plural': 'Данные в формате TLE'},
        ),
        migrations.RemoveField(
            model_name='tledata',
            name='satellite_id',
        ),
        migrations.AddField(
            model_name='tledata',
            name='header',
            field=models.CharField(blank=True, max_length=25, null=True, verbose_name='Заголовок'),
        ),
        migrations.AddField(
            model_name='tledata',
            name='satellite',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='TLE_data', to='tasks.satellite', verbose_name='Спутник'),
        ),
        migrations.AlterField(
            model_name='tledata',
            name='line1',
            field=models.CharField(max_length=70, verbose_name='Первая строка TLE спутника'),
        ),
        migrations.AlterField(
            model_name='tledata',
            name='line2',
            field=models.CharField(max_length=70, verbose_name='Вторая строка TLE спутника'),
        ),
        migrations.AlterField(
            model_name='tledata',
            name='task',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.DO_NOTHING, related_name='TLE_data', to='tasks.task', verbose_name='Задание'),
            preserve_default=False,
        ),
    ]
