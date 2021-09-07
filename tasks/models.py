from datetime import datetime
from julian import julian

from django.db import models
from django.conf import settings


class Telescope(models.Model):
    ONLINE = 1
    OFFLINE = 0
    STATUS_CHOICES = (
        (ONLINE, 'В сети'),
        (OFFLINE, 'Не в сети'),
    )
    alias = models.TextField('Псевдоним', unique=True)
    name = models.TextField('Название', unique=True)
    code = models.IntegerField('Код', unique=True)
    enabled = models.BooleanField('Доступность', default=True)
    status = models.SmallIntegerField('Статус', choices=STATUS_CHOICES, default=OFFLINE)
    description = models.TextField('Описание', blank=True)
    location = models.TextField('Местоположение', blank=True)
    altitude = models.FloatField('Высота над уровнем моря в м')
    latitude = models.FloatField('Широта в градусах')
    longitude = models.FloatField('Долгота в градусах')
    fov = models.FloatField('Поле зрения в градусах')
    avatar = models.ImageField('Аватар', null=True, blank=True, upload_to='telescopes')

    class Meta:
        verbose_name = 'Телескоп'
        verbose_name_plural = 'Телескопы'

    def __str__(self):
        return f'({self.code}) {self.name}'

    def get_user_balance(self, user):
        balance = self.balances.filter(user=user).first()
        return balance.minutes if balance else 0

    def to_dict(self):
        data = {}
        for f in self._meta.concrete_fields:
            data[f.name] = f.value_from_object(self)
        return data


class Satellite(models.Model):
    number = models.IntegerField('Номер спутника', unique=True)
    name = models.TextField('Название спутника', blank=True)

    class Meta:
        verbose_name = 'Космический объект'
        verbose_name_plural = 'Космические объекты'

    def __str__(self):
        return f'({self.number}) "{self.name}"'


class Task(models.Model):
    DRAFT = 0
    CREATED = 1
    RECEIVED = 2
    READY = 3
    FAILED = 4
    STATUS_CHOICES = (
        (DRAFT, 'Черновик'),
        (CREATED, 'Создано'),
        (RECEIVED, 'Получено телескопом'),
        (READY, 'Выполнено'),
        (FAILED, 'Не удалось выполнить'),
    )
    POINTS_MODE = 1
    TRACKING_MODE = 2
    TYPE_CHOICES = (
        (POINTS_MODE, 'Снимки по точкам'),
        (TRACKING_MODE, 'Трэкинг по точкам'),
    )
    status = models.SmallIntegerField('Статус задания', choices=STATUS_CHOICES, editable=False, default=DRAFT)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Автор задания', related_name='tasks', editable=False, on_delete=models.DO_NOTHING)
    telescope = models.ForeignKey(to=Telescope, verbose_name='Телескоп', related_name='tasks', limit_choices_to={'enabled': True}, on_delete=models.DO_NOTHING)
    satellite = models.ForeignKey(to=Satellite, to_field='number', verbose_name='Спутник', related_name='tasks', null=True, on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True, blank=True)
    task_type = models.SmallIntegerField('Тип задания', choices=TYPE_CHOICES)
    start_dt = models.DateTimeField('Дата и время начала наблюдения', editable=False, null=True, blank=True)
    end_dt = models.DateTimeField('Дата и время конца наблюдения', editable=False, null=True, blank=True)
    jdn = models.IntegerField('Юлианская дата начала наблюдения', editable=False, null=True)
    start_jd = models.FloatField('Юлианское время начала наблюдения', editable=False, null=True)
    end_jd = models.FloatField('Юлианское время конца наблюдения', editable=False, null=True)

    class Meta:
        verbose_name = 'Задание'
        verbose_name_plural = 'Задания'

    def __str__(self):
        return f'({self.id}) за {self.created_at.strftime("%Y-%m-%d %H:%M")} от пользователя {self.author.get_full_name()}: {self.get_task_type_display()} ({self.get_status_display()})'

    def to_dict(self):
        data = {}
        for f in self._meta.concrete_fields:
            data[f.name] = f.value_from_object(self)
        return data


class InputData(models.Model):
    NONE = 0
    TLE = 1
    JSON = 2
    TYPE_CHOICES = (
        (NONE, 'Нет данных'),
        (TLE, 'Элементы орбит в формате TLE'),
        (JSON, 'Массив точек в формате JSON'),
    )
    task = models.OneToOneField(Task, verbose_name='Задание', related_name='tasks_inputdata', on_delete=models.CASCADE)
    data_type = models.SmallIntegerField('Тип данных', choices=TYPE_CHOICES, editable=False)
    data_tle = models.TextField('Данные в формате TLE', blank=True)
    data_json = models.JSONField('Данные в формате JSON', null=True)

    class Meta:
        verbose_name = 'Входные данные'
        verbose_name_plural = 'Входные данные'

    def __str__(self):
        return f'({self.id}) {self.get_data_type_display()} для задания {self.task}'


class AbstractSpherePoint(models.Model):
    EARTH_SYSTEM = 0
    STARS_SYSTEM = 1
    SYSTEM_CHOICES = (
        (EARTH_SYSTEM, 'Земная система координат'),
        (STARS_SYSTEM, 'Звездная система координат'),
    )
    alpha = models.FloatField('Азимут в градусах')
    beta = models.FloatField('Угол места в градусах')

    class Meta:
        abstract = True
        verbose_name = 'Точка'
        verbose_name_plural = 'Точки'

    def __str__(self):
        return f'{self.alpha}°; {self.beta}°'

    @staticmethod
    def validate_point(point, cs_type: SYSTEM_CHOICES):
        errors = {}
        if point is None:
            errors['point'] = 'point is None'
            return errors
        alpha = point.get('alpha', None)
        if alpha is None:
            errors['alpha'] = 'alpha is None'
            return errors
        beta = point.get('beta', None)
        if beta is None:
            errors['beta'] = 'beta is None'
            return errors
        try:
            float(alpha)
        except ValueError:
            errors['alpha'] = 'alpha is not float'
            return errors
        try:
            float(beta)
        except ValueError:
            errors['beta'] = 'beta is not float'
            return errors
        if alpha < 0.0 or not alpha < 360.0:
            errors['alpha'] = 'alpha is not in [0..360)'
            return errors
        if cs_type == AbstractSpherePoint.EARTH_SYSTEM:
            if beta < 0.0 or beta > 90.0:
                errors['beta'] = 'beta is not in [0..90]'
                return errors
        elif cs_type == AbstractSpherePoint.STARS_SYSTEM:
            if beta < 0.0 or beta > 180.0:
                errors['beta'] = 'beta is not in [0..180]'
                return errors
        else:
            errors['cs_type'] = 'cs_type is not in [EARTH_SYSTEM, STARS_SYSTEM]'
            return errors
        return errors


class AbstractTimeMoment(models.Model):
    dt = models.DateTimeField('Дата и время')
    jdn = models.IntegerField('Юлианская дата')
    jd = models.FloatField('Юлианское время')

    class Meta:
        abstract = True
        verbose_name = 'Момент времени'
        verbose_name_plural = 'Моменты времени'

    def __str__(self):
        return f'{self.dt.strftime("%Y-%m-%d %H:%M:%S")}'

    @staticmethod
    def validate_moment(moment, now: datetime):
        errors = {}
        if moment is None:
            errors['moment'] = 'moment is None'
            return errors
        dt = moment.get('dt', None)
        if dt is None:
            errors['dt'] = 'dt is None'
            return errors
        jdn = moment.get('jdn', None)
        if jdn is None:
            errors['jdn'] = 'jdn is None'
            return errors
        jd = moment.get('jd', None)
        if jd is None:
            errors['jd'] = 'jd is None'
            return errors
        if not isinstance(dt, datetime):
            errors['dt'] = 'dt is not datetime'
            return errors
        try:
            int(jdn)
        except ValueError:
            errors['jdn'] = 'jdn is not int'
            return errors
        try:
            float(jd)
        except ValueError:
            errors['jd'] = 'jd is not float'
            return errors
        if not dt > now:
            errors['dt'] = 'dt is not in the future'
            return errors
        if jd < 0.0 or not jd < 1.0:
            errors['jd'] = 'jd is not in [0..1)'
            return errors
        return errors

    @staticmethod
    def dt_to_jdn_jdf(dt: datetime):
        jdn = int(julian.to_jd(dt))
        jdf = (dt.hour - 12) / 24 + dt.minute / 1440 + dt.second / 86400 + dt.microsecond / 86400000000
        return jdn, jdf


class AbstractImageFrame(models.Model):
    mag = models.FloatField('Звездная велечина')
    exposure = models.FloatField('Выдержка снимка в мс')

    class Meta:
        abstract = True
        verbose_name = 'Кадр'
        verbose_name_plural = 'Кадры'

    def __str__(self):
        return f'{self.exposure} мс'

    @staticmethod
    def validate_frame(frame):
        errors = {}
        if frame is None:
            errors['frame'] = 'frame is None'
            return errors
        mag = frame.get('mag', None)
        if mag is None:
            errors['mag'] = 'mag is None'
            return errors
        exposure = frame.get('exposure', None)
        if exposure is None:
            errors['exposure'] = 'exposure is None'
            return errors
        try:
            float(mag)
        except ValueError:
            errors['mag'] = 'mag is not float'
            return errors
        try:
            float(exposure)
        except ValueError:
            errors['exposure'] = 'exposure is not float'
            return errors
        if not exposure > 0.0:
            errors['exposure'] = 'exposure is not positive'
            return errors
        return errors


class Frame(AbstractTimeMoment, AbstractImageFrame):
    id = models.BigAutoField(primary_key=True)
    task = models.ForeignKey(to=Task, verbose_name='Задание', related_name='frames', on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name = 'Фрейм'
        verbose_name_plural = 'Фреймы (выдержка + время снимка)'

    def __str__(self):
        return f'{self.exposure} мс; {self.dt.strftime("%Y-%m-%d %H:%M:%S")}'

    @staticmethod
    def validate(frame):
        errors = {}
        if frame is None:
            errors['frame'] = 'frame is None'
            return errors
        return errors


class TLEData(models.Model):
    task = models.ForeignKey(to=Task, verbose_name='Задание', related_name='TLE_data', on_delete=models.DO_NOTHING)
    satellite = models.ForeignKey(to=Satellite, to_field='number', verbose_name='Спутник', related_name='TLE_data', null=True, on_delete=models.DO_NOTHING)
    header = models.CharField('Заголовок', max_length=25, null=True, blank=True)
    line1 = models.CharField('Первая строка TLE спутника', max_length=70)
    line2 = models.CharField('Вторая строка TLE спутника', max_length=70)

    class Meta:
        verbose_name = 'Данные в формате TLE'
        verbose_name_plural = 'Данные в формате TLE'

    def __str__(self):
        if self.header:
            return self.header
        return 'Без заголовка'


class Point(AbstractSpherePoint, AbstractTimeMoment):
    id = models.BigAutoField(primary_key=True)
    task = models.ForeignKey(to=Task, verbose_name='Задание', related_name='points', on_delete=models.DO_NOTHING)
    cs_type = models.SmallIntegerField('Система координат', choices=AbstractSpherePoint.SYSTEM_CHOICES, default=AbstractSpherePoint.EARTH_SYSTEM)

    class Meta:
        verbose_name = 'Точка для снимка'
        verbose_name_plural = 'Точки для снимков'

    def __str__(self):
        return f'{self.alpha}°; {self.beta}°; {self.dt.strftime("%Y-%m-%d %H:%M:%S")}'

    @staticmethod
    def validate(point):
        errors = {}
        if point is None:
            errors['point'] = 'point is None'
            return errors
        cs_type = point.get('cs_type', None)
        if cs_type is None:
            errors['cs_type'] = 'cs_type is None'
            return errors
        if cs_type not in [AbstractSpherePoint.EARTH_SYSTEM, AbstractSpherePoint.STARS_SYSTEM]:
            errors['cs_type'] = 'cs_type is not in [EARTH_SYSTEM, STARS_SYSTEM]'
            return errors
        return errors


class Balance(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Пользователь', related_name='balances',
                             on_delete=models.CASCADE)
    telescope = models.ForeignKey(to=Telescope, verbose_name='Телескоп', related_name='balances',
                                  on_delete=models.CASCADE)
    minutes = models.IntegerField('Наблюдательное время', default=0)

    class Meta:
        verbose_name = 'Баланс наблюдательного времени'
        verbose_name_plural = 'Балансы наблюдательного времени'

    def __str__(self):
        return f'{self.user} ({self.telescope})'


class BalanceRequest(models.Model):
    CREATED = 1
    APPROVED = 2
    REJECTED = 3
    STATUS_CHOICES = (
        (CREATED, 'Создана'),
        (APPROVED, 'Одобрена'),
        (REJECTED, 'Отклонена'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Пользователь', related_name='requests',
                             on_delete=models.CASCADE)
    telescope = models.ForeignKey(to=Telescope, verbose_name='Телескоп', related_name='balances_requests',
                                  on_delete=models.CASCADE)
    minutes = models.IntegerField('Требуемое время в минутах')
    status = models.SmallIntegerField('Статус', choices=STATUS_CHOICES, default=CREATED)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True, blank=True, null=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Администратор', blank=True, null=True,
                                    related_name='approved_requests', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Заявка на получение наблюдательного времени'
        verbose_name_plural = 'Заявки на получение наблюдательного времени'

    def __str__(self):
        return f'Заявка {self.id} (от {self.user}, на {self.telescope})'


class TaskResult(models.Model):
    id = models.BigAutoField(primary_key=True)
    task = models.ForeignKey(to=Task, verbose_name='Задание', related_name='results', on_delete=models.DO_NOTHING)
    image = models.ImageField('Снимок', null=True, blank=True, upload_to='results')
    point = models.OneToOneField(to=Point, verbose_name='Точка', related_name='result', null=True, on_delete=models.DO_NOTHING)
    frame = models.OneToOneField(to=Frame, verbose_name='Фрейм', related_name='result', null=True, on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name = 'Результат наблюдений'
        verbose_name_plural = 'Результаты наблюдений'

    def __str__(self):
        return f'Снимок {self.id} (задание {self.task.id}, на фрейм/точку{self.point_id or self.frame_id })'
