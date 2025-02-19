# Generated by Django 3.1.2 on 2021-08-19 12:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0019_auto_20210819_1217'),
    ]

    operations = [
        migrations.AddField(
            model_name='trackpoint',
            name='jd',
            field=models.FloatField(default=0, verbose_name='Юлианское время снимка'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='trackpoint',
            name='jdn',
            field=models.IntegerField(default=0, verbose_name='Юлианская дата снимка'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='trackpoint',
            name='beta',
            field=models.FloatField(verbose_name='Угол места'),
        ),
        migrations.AlterField(
            model_name='trackpoint',
            name='dt',
            field=models.DateTimeField(verbose_name='Дата и время снимка'),
        ),
        migrations.AlterField(
            model_name='trackpoint',
            name='task',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.DO_NOTHING, related_name='track_points', to='tasks.task', verbose_name='Задание'),
            preserve_default=False,
        ),
    ]
