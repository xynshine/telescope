import json
import locale
from datetime import datetime

import pytz
from django.db.models import Q, QuerySet
from rest_framework import serializers
from telescope.settings import SITE_URL, MEDIA_URL
from tasks.models import Telescope, Satellite, InputData, Point, Task, Frame, TLEData, BalanceRequest, TaskResult
from tasks.helpers import converting_degrees, is_float, is_int


class TelescopeSerializer(serializers.ModelSerializer):
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    balance = serializers.SerializerMethodField()

    def get_latitude(self, obj):
        deg, min, sec = converting_degrees(obj.latitude)
        place = 'N' if obj.latitude > 0 else 'S'
        return f'{deg}°{min}\'{sec}\" {place}'

    def get_longitude(self, obj):
        deg, min, sec = converting_degrees(obj.longitude)
        place = 'E' if obj.longitude > 0 else 'W'
        return f'{deg}°{min}\'{sec}\" {place}'

    def get_status(self, obj):
        return obj.get_status_display()

    def get_balance(self, obj):
        return obj.get_user_balance(self.context['request'].user)

    class Meta:
        model = Telescope
        fields = ('id', 'name', 'avatar', 'status', 'description', 'location', 'latitude', 'longitude', 'altitude', 'fov', 'balance')


class TelescopeBalanceSerializer(serializers.ModelSerializer):
    value = serializers.CharField(source='id')
    label = serializers.CharField(source='name')
    balance = serializers.SerializerMethodField()

    def get_balance(self, obj):
        return obj.get_user_balance(self.context['request'].user)

    class Meta:
        model = Telescope
        fields = ('label', 'value', 'balance')


class SatelliteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Satellite
        fields = ('id', 'number', 'name')


class PointSerializer(serializers.ModelSerializer):

    def validate(self, data):
        errors = {}
        errors.update(Point.validate_point(data, data.get('cs_type', None)))
        errors.update(Point.validate_moment(data, datetime.now(tz=pytz.UTC)))
        errors.update(Point.validate(data))
        if len(errors) > 0:
            raise serializers.ValidationError(errors)
        return data

    class Meta:
        model = Point
        fields = ('id', 'alpha', 'beta', 'cs_type', 'dt', 'task', 'jdn', 'jd')


class FrameSerializer(serializers.ModelSerializer):

    def validate(self, data):
        errors = {}
        errors.update(Frame.validate_frame(data))
        errors.update(Frame.validate_moment(data, datetime.now(tz=pytz.UTC)))
        errors.update(Frame.validate(data))
        if len(errors) > 0:
            raise serializers.ValidationError(errors)
        return data

    class Meta:
        model = Frame
        fields = ('id', 'task', 'mag', 'exposure', 'dt', 'jdn', 'jd')


class InputDataSerializer(serializers.ModelSerializer):

    def save(self):
        data_type = InputData.NONE
        if len(self.validated_data.get('data_tle')) > 0:
            data_type = InputData.TLE
        if self.validated_data.get('data_json') is not None:
            data_type = InputData.JSON
            data_json = self.validated_data.get('data_json')
            if isinstance(data_json, str):
                data_json = json.loads(data_json)
                self.validated_data.update(data_json=data_json)
        data = super().save(data_type=data_type)
        return data

    class Meta:
        model = InputData
        fields = ('id', 'task', 'data_type', 'data_tle', 'data_json')


class TleDataSerializer(serializers.ModelSerializer):

    class Meta:
        model = TLEData
        fields = ('id', 'task', 'satellite_id', 'header', 'line1', 'line2')


class BalanceRequestSerializer(serializers.ModelSerializer):
    telescope = serializers.CharField(source='telescope.name')
    created = serializers.SerializerMethodField()
    approved = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    def get_created(self, obj):
        locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        return obj.created_at.strftime('%d %b %Y, %H:%M')

    def get_approved(self, obj):
        return obj.approved_by.get_full_name() if obj.approved_by else ''

    def get_status(self, obj):
        return obj.get_status_display()

    class Meta:
        model = BalanceRequest
        fields = ('telescope', 'minutes', 'status', 'created', 'approved')


class BalanceRequestCreateSerializer(serializers.ModelSerializer):
    telescope = serializers.CharField(source='telescope.id')
    minutes = serializers.IntegerField()

    class Meta:
        model = BalanceRequest
        fields = ('telescope', 'minutes')

    def create(self, validated_data):
        telescope_id = validated_data.pop('telescope').get('id')
        minutes = validated_data.pop('minutes')
        user = self.context['request'].user
        instance = BalanceRequest.objects.create(user=user, minutes=minutes, telescope_id=telescope_id)
        return instance


class TaskSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    data_tle = serializers.CharField(label='Данные в формате TLE', required=False, allow_blank=True, default='', max_length=165)
    data_json = serializers.JSONField(label='Данные в формате JSON', required=False, allow_null=True, default=None, binary=True)

    def get_url(self, obj):
        if obj.status == Task.READY:
            return f'{obj.id}/results/'

    def validate_enabled(self, enabled):
        if not enabled:
            raise serializers.ValidationError({"telescope": "telescope should be enabled"})

    def validate_ttype(self, ttype):
        if ttype not in {Task.POINTS_MODE, Task.TRACKING_MODE}:
            raise serializers.ValidationError({"task_type": "invalid task type"})

    def validate(self, data):
        self.validate_enabled(data.get('telescope', None).enabled)
        self.validate_ttype(data.get('task_type', None))
        return data

    def create(self, validated_data):
        validated_data.pop('data_tle')
        validated_data.pop('data_json')
        return super().create(validated_data)

    def save(self, user):
        task = super().save(author=user)
        return task

    class Meta:
        model = Task
        fields = ('id', 'status', 'author', 'created_at', 'telescope', "satellite", 'task_type', 'start_dt', 'end_dt', 'jdn', 'start_jd', 'end_jd', 'url', 'data_tle', 'data_json')


class TelescopeTaskSerializer(serializers.Serializer):
    jdn = serializers.IntegerField()
    telescope = serializers.DictField()
    points = serializers.ListField()
    frames = serializers.ListField()

    def update(self, instance, validated_data):
        return instance

    def create(self, validated_data):
        return None

    class Meta:
        fields = ('jdn', 'telescope', 'points', 'frames')


class TaskResultSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    task_type = serializers.SerializerMethodField()
    created = serializers.SerializerMethodField()
    start_dt = serializers.SerializerMethodField()
    end_dt = serializers.SerializerMethodField()
    results = serializers.SerializerMethodField()
    type_code = serializers.SerializerMethodField()
    other_data = serializers.SerializerMethodField()

    def get_name(self, obj):
        return f'Результаты наблюдения №{obj.id}'

    def get_task_type(self, obj):
        return obj.get_task_type_display()

    def get_created(self, obj):
        locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        return obj.created_at.strftime('%d %b %Y, %H:%M')

    def get_start_dt(self, obj):
        return obj.start_dt.strftime('%d %b, %H:%M:%S')

    def get_end_dt(self, obj):
        return obj.end_dt.strftime('%d %b, %H:%M:%S')

    def get_type_code(self, obj):
        if obj.task_type == Task.POINTS_MODE:
            return 'point'
        if obj.task_type == Task.TRACKING_MODE:
            return 'track'
        if obj.task_type == Task.TLE_MODE:
            return 'tle'

    def get_other_data(self, obj):
        if obj.task_type == Task.TRACKING_MODE:
            return {
                'satellite': obj.tracking_data.first().id,
                'mag': obj.tracking_data.first().mag,
            }
        if obj.task_type == Task.TLE_MODE:
            return {
                'satellite': obj.TLE_data.first().id,
                'line1': obj.TLE_data.first().line1,
                'line2': obj.TLE_data.first().line2,
            }

    def get_results(self, obj):
        results = []
        for result in obj.results.all():
            if obj.task_type == Task.POINTS_MODE:
                results.append({
                    'satellite': result.point.satellite_id,
                    'mag': result.point.mag,
                    'dt': result.point.dt.strftime('%d %b %Y, %H:%M:%S'),
                    'alpha': result.point.alpha,
                    'beta': result.point.beta,
                    'exposure': result.point.exposure,
                    'url': f'{SITE_URL}{result.image.url}',
                })
            else:
                results.append({
                    'exposure': result.frame.exposure,
                    'dt': result.frame.dt.strftime('%d %b %Y, %H:%M:%S'),
                    'url': f'{SITE_URL}{result.image.url}',
                })
        return results

    class Meta:
        model = Task
        fields = ('name', 'task_type', 'created', 'start_dt', 'end_dt', 'results', 'type_code', 'other_data')


class TelescopeFilteredPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        request = self.context.get('request', None)
        if request:
            user = request.user
            if user:
                telescope = Telescope.objects.get(user=user)
                if telescope:
                    queryset = super().get_queryset()
                    return queryset.filter(telescope=telescope)
        return QuerySet()


class TaskStatusSerializer(serializers.ModelSerializer):
    id = TelescopeFilteredPrimaryKeyRelatedField(queryset=Task.objects.filter(Q(
        status__in=[Task.CREATED, Task.RECEIVED]
    )))
    status = serializers.ChoiceField(choices=[
        Task.STATUS_CHOICES[Task.RECEIVED],
        Task.STATUS_CHOICES[Task.READY],
        Task.STATUS_CHOICES[Task.FAILED],
    ])

    class Meta:
        model = Task
        fields = ('id', 'status')
