from django.db import models
from django.conf import settings


class Company(models.Model):
    name = models.CharField('Название', max_length=30, blank=True)

    class Meta:
        verbose_name = 'Место работы'
        verbose_name_plural = 'Места работы'

    def __str__(self):
        return self.name


class Profile(models.Model):
    FEMALE = 0
    MALE = 1
    GENDER_CHOICES = (
        (FEMALE, 'Женский'),
        (MALE, 'Мужской')
    )
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    gender = models.SmallIntegerField('Пол', choices=GENDER_CHOICES, default=1, blank=True, null=True)
    company = models.ForeignKey(verbose_name='Место работы', to=Company, on_delete=models.SET_NULL, blank=True,
                                related_name='workers', null=True)
    position = models.CharField('Должность', max_length=70, blank=True)
    hours = models.IntegerField('Оставшиеся часы', default=0, blank=True, null=True)
    avatar = models.ImageField('Аватар', null=True, blank=True, upload_to='avatars')

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'

    def __str__(self):
        if self.full_name:
            return self.full_name
        return self.user.username

    @property
    def full_name(self):
        if self.user.first_name and self.user.last_name:
            return "%s %s" % (self.user.first_name, self.user.last_name)
        return None


