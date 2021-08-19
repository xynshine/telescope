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


class Satellite(models.Model):

    class Meta:
        verbose_name = 'Спутник'
        verbose_name_plural = 'Спутники'

    def __str__(self):
        return f'Спутник (id={self.id})'


class InputData(models.Model):
    NONE = 0
    TLE = 1
    JSON = 2
    TYPE_CHOICES = (
        (NONE, 'Нет данных'),
        (TLE, 'Элементы орбит в формате TLE'),
        (JSON, 'Массив точек в формате JSON'),
    )
    author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Автор входных данных', related_name='tasks_inputdata', on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    expected_sat = models.ForeignKey(to=Satellite, verbose_name='Ожидаемый спутник', related_name='tasks_inputdata', null=True, on_delete=models.DO_NOTHING)
    data_type = models.SmallIntegerField('Тип данных', choices=TYPE_CHOICES, default=NONE)
    data_tle = models.TextField('Данные в формате TLE', blank=True)
    data_json = models.JSONField('Данные в формате JSON', null=True)

    class Meta:
        verbose_name = 'Входные данные'
        verbose_name_plural = 'Входные данные'

    def __str__(self):
        return f'{self.get_data_type_display()} (id={self.id}) от {self.author.get_full_name()} за {self.get_created_at_display()}'


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
    status = models.SmallIntegerField('Статус задания', choices=STATUS_CHOICES, default=DRAFT)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Автор задания', related_name='tasks', on_delete=models.DO_NOTHING)
    telescope = models.ForeignKey(Telescope, verbose_name='Телескоп', related_name='tasks', on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    input_data = models.ForeignKey(InputData, verbose_name='Входные данные', related_name='tasks', null=True, on_delete=models.DO_NOTHING)
    task_type = models.SmallIntegerField('Тип задания', choices=TYPE_CHOICES)
    start_dt = models.DateTimeField('Дата и время начала наблюдения', null=True, blank=True)
    end_dt = models.DateTimeField('Дата и время конца наблюдения', null=True, blank=True)
    jdn = models.IntegerField('Юлианская дата начала наблюдения', null=True)
    start_jd = models.FloatField('Юлианское время начала наблюдения', null=True)
    end_jd = models.FloatField('Юлианское время конца наблюдения', null=True)

    class Meta:
        verbose_name = 'Задание'
        verbose_name_plural = 'Задания'

    def __str__(self):
        return f'{self.get_task_type_display()} (id={self.id}) от {self.author.get_full_name()} за {self.get_created_at_display()}'


class Frame(models.Model):
    task = models.ForeignKey(to=Task, verbose_name='Задание', related_name='frames', null=True, blank=True, on_delete=models.CASCADE)
    exposure = models.IntegerField('Требуемая выдержка снимка')
    dt = models.DateTimeField('Время снимка')

    class Meta:
        verbose_name = 'Фрейм'
        verbose_name_plural = 'Фреймы (выдержка + время снимка)'


class TrackPoint(models.Model):
    task = models.ForeignKey(to=Task, verbose_name='Задание', related_name='track_points', null=True, blank=True, on_delete=models.CASCADE)
    alpha = models.FloatField('Азимут')
    beta = models.FloatField('Высота')
    dt = models.DateTimeField('Время снимка')

    class Meta:
        verbose_name = 'Точка для трекинга'
        verbose_name_plural = 'Точки для трекинга'


class TrackingData(models.Model):
    task = models.ForeignKey(to=Task, verbose_name='Задание', related_name='tracking_data', null=True, blank=True, on_delete=models.CASCADE)
    satellite_id = models.IntegerField('Номер спутника')
    mag = models.FloatField('Звездная велечина')
    step_sec = models.IntegerField('Временной шаг', default=1)
    count = models.IntegerField('Количество снимков', default=100)

    class Meta:
        verbose_name = 'Данные для трекинга'
        verbose_name_plural = 'Данные для трекинга'


class TLEData(models.Model):
    task = models.ForeignKey(to=Task, verbose_name='Задание', related_name='TLE_data', null=True, blank=True, on_delete=models.CASCADE)
    satellite_id = models.IntegerField('Номер спутника')
    line1 = models.CharField('Первая строка TLE спутника', max_length=255)
    line2 = models.CharField('Вторая строка TLE спутника', max_length=255)

    class Meta:
        verbose_name = 'Данные для TLE'
        verbose_name_plural = 'Данные для TLE'


class Point(models.Model):
    EARTH_SYSTEM = 0
    STARS_SYSTEM = 1
    SYSTEM_CHOICES = (
        (EARTH_SYSTEM, 'Земная система координат'),
        (STARS_SYSTEM, 'Звездная система координат'),
    )
    task = models.ForeignKey(to=Task, verbose_name='Задание', related_name='points', null=True, blank=True, on_delete=models.CASCADE)
    satellite_id = models.IntegerField('Номер спутника')
    mag = models.FloatField('Звездная велечина')
    dt = models.DateTimeField('Время снимка')
    alpha = models.FloatField('Азимут')
    beta = models.FloatField('Высота')
    exposure = models.IntegerField('Требуемая выдержка снимка')
    cs_type = models.SmallIntegerField('Система координат', choices=SYSTEM_CHOICES, default=EARTH_SYSTEM)

    class Meta:
        verbose_name = 'Точка для снимка'
        verbose_name_plural = 'Точки для снимков'


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
    task = models.ForeignKey(to=Task, verbose_name='Задание', related_name='results', null=True, blank=True, on_delete=models.CASCADE)
    image = models.ImageField('Снимок', null=True, blank=True, upload_to='results')
    point = models.ForeignKey(to=Point, verbose_name='Точка', related_name='result', null=True, blank=True, on_delete=models.CASCADE)
    frame = models.ForeignKey(to=Frame, verbose_name='Фрейм', related_name='result', null=True, blank=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Результаты наблюдений'
        verbose_name_plural = 'Результаты наблюдений'

    def __str__(self):
        return f'Снимок {self.id} (задание {self.task.id}, на фрейм/точку{self.point_id or self.frame_id })'
