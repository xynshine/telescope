from datetime import datetime
import locale
import pytz
import julian
from django.db.models import Q

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from rest_framework import generics
from rest_framework.response import Response


from tasks.models import Telescope, Satellite, InputData, Task, BalanceRequest, Balance
from tasks.serializers import (
    TelescopeSerializer, TelescopeBalanceSerializer, PointTaskSerializer,
    SatelliteSerializer, InputDataSerializer,
    TrackingTaskSerializer, TleTaskSerializer, BalanceRequestSerializer,
    BalanceRequestCreateSerializer, TaskSerializer, TaskResultSerializer
)
from tasks.helpers import telescope_collision_task_message, get_points_json, get_track_json, get_frames_json


DT_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


class TelescopeView(generics.ListAPIView):
    queryset = Telescope.objects.filter(enabled=True)
    serializer_class = TelescopeSerializer


class TelescopeChoosingView(generics.ListAPIView):
    queryset = Telescope.objects.filter(enabled=True)
    serializer_class = TelescopeBalanceSerializer


class SatelliteView(generics.ListAPIView):
    queryset = Satellite.objects.all().order_by('number')
    serializer_class = SatelliteSerializer


class SatelliteCreateView(generics.CreateAPIView):
    serializer_class = SatelliteSerializer

    def create(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=self.request.data, context=self.get_serializer_context())
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        satellite = serializer.save()
        return Response(data={
            'msg': f'Спутник №{satellite.id} успешно создан',
            'status': 'ok'
        })


class InputDataView(generics.ListAPIView):
    serializer_class = InputDataSerializer

    def get_queryset(self):
        tasks = Task.objects.filter(author=self.request.user)
        return InputData.objects.filter(task__in=tasks).order_by('-id')


class InputDataCreateView(generics.CreateAPIView):
    serializer_class = InputDataSerializer

    def create(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=self.request.data, context=self.get_serializer_context())
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        inputdata = serializer.save(self.request.user)
        return Response(data={
            'msg': f'Входные данные №{inputdata.id} успешно созданы',
            'status': 'ok'
        })


class PointTaskView(generics.CreateAPIView):
    queryset = Task.objects.filter(task_type=Task.POINTS_MODE)
    serializer_class = PointTaskSerializer

    def create(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=self.request.data, context=self.get_serializer_context())
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        telescope_id = self.request.data.get('telescope')
        start_dt = datetime.strptime(self.request.data.get('min_dt'), DT_FORMAT).replace(tzinfo=pytz.UTC)
        end_dt = datetime.strptime(self.request.data.get('max_dt'), DT_FORMAT).replace(tzinfo=pytz.UTC)
        collisions_message = telescope_collision_task_message(telescope_id, start_dt, end_dt)
        if collisions_message:
            return Response(data={'msg': collisions_message}, status=400)
        point_task = serializer.save()
        duration = int(self.request.data.get('duration'))
        try:
            balance = Balance.objects.get(user=self.request.user, telescope_id=telescope_id)
            balance.minutes = balance.minutes - duration
            balance.save()
            return Response(data={'msg': f'Задание №{point_task.id} успешно создано, на этом телескопе осталось {balance.minutes} минут для наблюдений', 'status': 'ok'})
        except Balance.DoesNotExist:
            return Response(data={'msg': f'Ошибка создания задания, нет доступа к данному телескопу', 'status': 'error'}, status=400)


class TrackingTaskView(generics.CreateAPIView):
    queryset = Task.objects.filter(task_type=Task.TRACKING_MODE)
    serializer_class = TrackingTaskSerializer

    def create(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=self.request.data, context=self.get_serializer_context())
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        tracking_task = serializer.save()
        telescope_id = self.request.data.get('telescope')
        start_dt = datetime.strptime(self.request.data.get('min_dt'), DT_FORMAT).replace(tzinfo=pytz.UTC)
        end_dt = datetime.strptime(self.request.data.get('max_dt'), DT_FORMAT).replace(tzinfo=pytz.UTC)
        collisions_message = telescope_collision_task_message(telescope_id, start_dt, end_dt)
        if collisions_message:
            return Response(data={'msg': collisions_message}, status=400)
        duration = int(self.request.data.get('duration'))
        try:
            balance = Balance.objects.get(user=self.request.user, telescope_id=telescope_id)
            balance.minutes = balance.minutes - duration
            balance.save()
            return Response(data={
                'msg': f'Задание №{tracking_task.id} успешно создано, на этом телескопе осталось {balance.minutes} минут для наблюдений',
                'status': 'ok'})
        except Balance.DoesNotExist:
            return Response(data={'msg': f'Ошибка создания задания, нет доступа к данному телескопу', 'status': 'error'}, status=400)


'''
class TleTaskView(generics.CreateAPIView):
    queryset = Task.objects.filter(task_type=Task.TLE_MODE)
    serializer_class = TleTaskSerializer

    def create(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=self.request.data, context=self.get_serializer_context())
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        tle_task = serializer.save()
        telescope_id = self.request.data.get('telescope')
        start_dt = datetime.strptime(self.request.data.get('min_dt'), DT_FORMAT).replace(tzinfo=pytz.UTC)
        end_dt = datetime.strptime(self.request.data.get('max_dt'), DT_FORMAT).replace(tzinfo=pytz.UTC)
        collisions_message = telescope_collision_task_message(telescope_id, start_dt, end_dt)
        if collisions_message:
            return Response(data={'msg': collisions_message}, status=400)
        duration = int(self.request.data.get('duration'))
        try:
            balance = Balance.objects.get(user=self.request.user, telescope_id=telescope_id)
            balance.minutes = balance.minutes - duration
            balance.save()
            return Response(data={
                'msg': f'Задание №{tle_task.id} успешно создано, на этом телескопе осталось {balance.minutes} минут для наблюдений',
                'status': 'ok'})
        except Balance.DoesNotExist:
            return Response(
                data={'msg': f'Ошибка создания задания, нет доступа к данному телескопу', 'status': 'error'},
                status=400)
'''


class BalanceRequestView(generics.ListAPIView):
    serializer_class = BalanceRequestSerializer

    def get_queryset(self):
        return BalanceRequest.objects.filter(user=self.request.user)


class BalanceRequestCreateView(generics.CreateAPIView):
    serializer_class = BalanceRequestCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=self.request.data, context=self.get_serializer_context())
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        request = serializer.save()
        return Response(data=f'Заявка №{request.id} успешна создана')


def get_telescope_schedule(request, telescope_id):
    locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
    actual_tasks = Task.objects.filter(status__in=[Task.CREATED, Task.RECEIVED], telescope_id=telescope_id)
    slots = []
    for task in actual_tasks:
        slot = f'{task.start_dt.strftime("%d %b %Y, %H:%M:%S")} - {task.end_dt.strftime("%d %b %Y, %H:%M:%S")}'
        slots.append(slot)
    return JsonResponse({'schedule': slots})


class UserTasks(generics.ListAPIView):
    serializer_class = TaskSerializer

    def get_queryset(self):
        return Task.objects.filter(author=self.request.user).order_by('-id')


class UserTaskCreateView(generics.CreateAPIView):
    serializer_class = TaskSerializer

    def create(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=self.request.data, context=self.get_serializer_context())
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        inputtask = serializer.save(self.request.user)
        return Response(data={
            'msg': f'Задание №{inputtask.id} успешно создано',
            'status': 'ok'
        })


def get_task_confirm(request, task_id):
    task = get_object_or_404(Task, Q(id=task_id, author=request.user, status=Task.DRAFT))
    task.status = Task.CREATED
    task.save()
    return JsonResponse(data={
            'msg': f'Задание №{task.id} успешно обновлено',
            'status': 'ok'
        })


class TaskResult(generics.RetrieveAPIView):
    serializer_class = TaskResultSerializer
    queryset = Task.objects.all()


def get_telescope_plan(request, telescope_id, task_id):
    telescope = get_object_or_404(Telescope, id=telescope_id)
    task = get_object_or_404(Task, id=task_id)
    telescope_data = {
        'id': telescope_id,
        'name': telescope.name,
        'site_lon': telescope.longitude,
        'site_lat': telescope.latitude,
        'site_height': telescope.altitude,
        'FOV': telescope.fov,
    }
    data = {
        'user': task.author.get_full_name(),
        'key': task.author_id,
        'jd_start': julian.to_jd(task.start_dt, fmt='jd'),
        'jd_end': julian.to_jd(task.end_dt, fmt='jd'),
        'telescope': telescope_data,
    }
    if task.task_type == Task.POINTS_MODE:
        data['points'] = get_points_json(task.points.all())
    if task.task_type == Task.TRACKING_MODE:
        tracking_data = {
            'id': task.tracking_data.first().satellite_id,
            'mag': task.tracking_data.first().mag,
            'step_sec': task.tracking_data.first().step_sec,
            'count': task.tracking_data.first().count,
            'track': get_track_json(task.track_points.all()),
            'frames': get_frames_json(task.frames.all()),
        }
        data['tracking'] = tracking_data
    if task.task_type == Task.TLE_MODE:
        tle_data = {
            'id': task.TLE_data.first().satellite_id,
            'line1': task.TLE_data.first().line1,
            'line2': task.TLE_data.first().line2,
            'frames': get_frames_json(task.frames.all()),
        }
        data['TLE'] = tle_data
    return JsonResponse({'plan': data})


def get_telescope_tasks(request, telescope_id, jdn=None):
    plan = {}
    telescope = get_object_or_404(Telescope, id=telescope_id)
    plan['telescope'] = telescope.to_dict()
    plan['telescope']['avatar'] = None
    tasks = Task.objects.filter(Q(
        status=Task.CREATED,
        telescope_id=telescope_id,
        jdn=jdn
    ))
    plan['tasks'] = []
    for task in tasks:
        t = task.to_dict()
        t_type = ''
        if task.task_type == Task.POINTS_MODE:
            t_type = 'points'
        elif task.task_type == Task.TRACKING_MODE:
            t_type = 'tracking'
        t[t_type] = []
        t['tle'] = []
        input_jsons = InputData.objects.filter(task=task)
        for input_json in input_jsons:
            if input_json.data_type == InputData.JSON:
                t[t_type].append(input_json.data_json)
            if len(input_json.data_tle) > 0:
                t['tle'].append(input_json.data_tle)
        plan['tasks'].append(t)
    return JsonResponse({"plan": plan})

