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
        if self.name:
            return self.name
        return f'Телескоп {self.id}'

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
        verbose_name = 'Спутник'
        verbose_name_plural = 'Спутники'

    def __str__(self):
        return f'{self.number} "{self.name}"'


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
    telescope = models.ForeignKey(Telescope, verbose_name='Телескоп', related_name='tasks', limit_choices_to={'enabled': True}, on_delete=models.DO_NOTHING)
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
        return f'{self.created_at.strftime("%Y-%m-%d %H:%M")} от {self.author.get_full_name()}: {self.get_task_type_display()} ({self.get_status_display()})'

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
    expected_sat = models.ForeignKey(to=Satellite, to_field='number', verbose_name='Ожидаемый спутник', related_name='tasks_inputdata', null=True, on_delete=models.DO_NOTHING)
    data_type = models.SmallIntegerField('Тип данных', choices=TYPE_CHOICES, editable=False)
    data_tle = models.TextField('Данные в формате TLE', blank=True)
    data_json = models.JSONField('Данные в формате JSON', null=True)

    class Meta:
        verbose_name = 'Входные данные'
        verbose_name_plural = 'Входные данные'

    def __str__(self):
        return f'{self.get_data_type_display()} по {self.expected_sat} для {self.task}'


class Frame(models.Model):
    task = models.ForeignKey(to=Task, verbose_name='Задание', related_name='frames', on_delete=models.DO_NOTHING)
    exposure = models.FloatField('Требуемая выдержка снимка')
    dt = models.DateTimeField('Дата и время снимка')
    jdn = models.IntegerField('Юлианская дата снимка')
    jd = models.FloatField('Юлианское время снимка')

    class Meta:
        verbose_name = 'Фрейм'
        verbose_name_plural = 'Фреймы (выдержка + время снимка)'

    def __str__(self):
        return f'{self.exposure} с; {self.get_dt_display()}'


class TrackPoint(models.Model):
    task = models.ForeignKey(to=Task, verbose_name='Задание', related_name='track_points', on_delete=models.DO_NOTHING)
    alpha = models.FloatField('Азимут')
    beta = models.FloatField('Угол места')
    dt = models.DateTimeField('Дата и время снимка')
    jdn = models.IntegerField('Юлианская дата снимка')
    jd = models.FloatField('Юлианское время снимка')

    class Meta:
        verbose_name = 'Точка для трекинга'
        verbose_name_plural = 'Точки для трекинга'

    def __str__(self):
        return f'{self.alpha}°; {self.beta}°; {self.get_dt_display()}'


class TrackingData(models.Model):
    task = models.ForeignKey(to=Task, verbose_name='Задание', related_name='tracking_data', on_delete=models.DO_NOTHING)
    satellite = models.ForeignKey(to=Satellite, to_field='number', verbose_name='Спутник', related_name='tracking_data', null=True, on_delete=models.DO_NOTHING)
    mag = models.FloatField('Звездная велечина')
    step_sec = models.FloatField('Шаг по времени', default=1)
    count = models.IntegerField('Количество снимков', default=20)

    class Meta:
        verbose_name = 'Данные для трекинга'
        verbose_name_plural = 'Данные для трекинга'

    def __str__(self):
        if self.satellite:
            return f'{self.satellite}; {self.count} × {self.step_sec} с'


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


class Point(models.Model):
    EARTH_SYSTEM = 0
    STARS_SYSTEM = 1
    SYSTEM_CHOICES = (
        (EARTH_SYSTEM, 'Земная система координат'),
        (STARS_SYSTEM, 'Звездная система координат'),
    )
    task = models.ForeignKey(to=Task, verbose_name='Задание', related_name='points', on_delete=models.DO_NOTHING)
    satellite = models.ForeignKey(to=Satellite, to_field='number', verbose_name='Спутник', related_name='points', null=True, on_delete=models.DO_NOTHING)
    mag = models.FloatField('Звездная велечина')
    dt = models.DateTimeField('Дата и время снимка')
    jdn = models.IntegerField('Юлианская дата снимка')
    jd = models.FloatField('Юлианское время снимка')
    alpha = models.FloatField('Азимут')
    beta = models.FloatField('Угол места')
    exposure = models.FloatField('Требуемая выдержка снимка')
    cs_type = models.SmallIntegerField('Система координат', choices=SYSTEM_CHOICES, default=EARTH_SYSTEM)

    class Meta:
        verbose_name = 'Точка для снимка'
        verbose_name_plural = 'Точки для снимков'

    def __str__(self):
        return f'{self.satellite}; {self.alpha}°; {self.beta}°; {self.exposure} с; {self.get_dt_display()}'


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
    task = models.ForeignKey(to=Task, verbose_name='Задание', related_name='results', on_delete=models.DO_NOTHING)
    image = models.ImageField('Снимок', null=True, blank=True, upload_to='results')
    point = models.ForeignKey(to=Point, verbose_name='Точка', related_name='result', null=True, on_delete=models.DO_NOTHING)
    frame = models.ForeignKey(to=Frame, verbose_name='Фрейм', related_name='result', null=True, on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name = 'Результаты наблюдений'
        verbose_name_plural = 'Результаты наблюдений'

    def __str__(self):
        return f'Снимок {self.id} (задание {self.task.id}, на фрейм/точку{self.point_id or self.frame_id })'
