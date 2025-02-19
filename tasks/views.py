from datetime import datetime
import locale
import pytz
import julian
from django.db.models import Q

from django.shortcuts import get_object_or_404
from django.http import QueryDict
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.utils import json


from tasks.models import Telescope, Satellite, InputData, Task, BalanceRequest, AbstractTimeMoment, Point, Frame
from tasks.serializers import (
    TelescopeSerializer, TelescopeBalanceSerializer, SatelliteSerializer,
    InputDataSerializer, PointSerializer, BalanceRequestSerializer, TaskStatusSerializer,
    BalanceRequestCreateSerializer, TaskSerializer, TaskResultSerializer, FrameSerializer, TelescopeTaskSerializer,
    ResultSerializer
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


class UserTaskCreateView(generics.CreateAPIView):
    serializer_class = TaskSerializer

    def create(self, request, *args, **kwargs):
        data = request.data
        if isinstance(data, QueryDict):
            data._mutable = True
        task_serializer_class = self.get_serializer_class()
        task_serializer = task_serializer_class(data=data, context=self.get_serializer_context())
        if not task_serializer.is_valid():
            return Response(task_serializer.errors, status=400)
        inputtask = task_serializer.save(request.user)
        data.update(task=inputtask.id)
        data_serializer = InputDataSerializer(data=data, context=self.get_serializer_context())
        if not data_serializer.is_valid():
            return Response(data_serializer.errors, status=400)
        inputdata = data_serializer.save()
        if inputdata.data_type == InputData.JSON:
            min_dt = datetime.max.replace(tzinfo=pytz.UTC)
            max_dt = datetime.min.replace(tzinfo=pytz.UTC)
            if inputtask.task_type in [Task.POINTS_MODE, Task.TRACKING_MODE]:
                plan = inputdata.data_json
                points = plan.get('points', None)
                if points is None:
                    return Response({"points": "points is None"}, status=400)
                if not len(points) > 0:
                    return Response({"points": "points is Empty"}, status=400)
                for point in points:
                    dt = datetime.strptime(point['dt'], DT_FORMAT).replace(tzinfo=pytz.UTC)
                    if min_dt > dt:
                        min_dt = dt
                    if max_dt < dt:
                        max_dt = dt
                    jdn, jdf = AbstractTimeMoment.dt_to_jdn_jdf(dt)
                    point['jdn'] = jdn
                    point['jd'] = jdf
                    point['task'] = inputtask.id
                point_serializer = PointSerializer(data=points, many=True)
                if not point_serializer.is_valid():
                    errors = {}
                    for error in point_serializer.errors:
                        errors.update(error)
                    return Response(errors, status=400)
                point_serializer.save()
                frames = plan.get('frames', None)
                if frames is None:
                    return Response({"frames": "frames is None"}, status=400)
                if not len(frames) > 0:
                    return Response({"frames": "frames is Empty"}, status=400)
                for frame in frames:
                    dt = datetime.strptime(frame['dt'], DT_FORMAT).replace(tzinfo=pytz.UTC)
                    if min_dt > dt:
                        min_dt = dt
                    if max_dt < dt:
                        max_dt = dt
                    jdn, jdf = AbstractTimeMoment.dt_to_jdn_jdf(dt)
                    frame['jdn'] = jdn
                    frame['jd'] = jdf
                    frame['task'] = inputtask.id
                frames_serializer = FrameSerializer(data=frames, many=True)
                if not frames_serializer.is_valid():
                    errors = {}
                    for error in frames_serializer.errors:
                        errors.update(error)
                    return Response(errors, status=400)
                frames_serializer.save()
            else:
                return Response(data_serializer.errors, status=400)
            jdn1, jdf1 = AbstractTimeMoment.dt_to_jdn_jdf(min_dt)
            inputtask.start_dt = min_dt
            inputtask.start_jd = jdf1 + jdn1
            inputtask.jdn = jdn1
            jdn2, jdf2 = AbstractTimeMoment.dt_to_jdn_jdf(max_dt)
            inputtask.end_dt = max_dt
            inputtask.end_jd = jdf2 + jdn2
        elif inputdata.data_type == InputData.TLE:
            return Response(data_serializer.errors, status=501)
        else:
            return Response(data_serializer.errors, status=400)
        inputtask.status = Task.CREATED
        inputtask.save()
        return Response(data={
            'msg': f'Задание №{inputtask.id} успешно создано',
            'status': 'ok'
        })


class PointTaskCreateView(UserTaskCreateView):

    def create(self, request, *args, **kwargs):
        data = request.data
        if isinstance(data, QueryDict):
            data._mutable = True
        telescope = data.get('telescope', None)
        task_type = Task.POINTS_MODE
        data_json = data.get('points', None)
        points = []
        frames = []
        satellites = set()
        for data_point in data_json:
            point = {'dt': data_point['dt'], 'alpha': data_point['alpha'], 'beta': data_point['beta'], 'cs_type': data_point['cs_type']}
            frame = {'dt': data_point['dt'], 'mag': data_point['mag'], 'exposure': data_point['exposure']}
            satellite = data_point['satellite_id']
            points.append(point)
            frames.append(frame)
            satellites.add(satellite)
        satellite = None
        if len(satellites) == 1:
            satellite = next(iter(satellites))
        data.clear()
        data.update(telescope=telescope)
        if satellite:
            data.update(satellite=satellite)
        data.update(task_type=task_type)
        data.update(data_tle='')
        data.update(data_json=json.dumps({'points': points, 'frames': frames}))
        return super().create(request, *args, **kwargs)


class TrackingTaskCreateView(UserTaskCreateView):

    def create(self, request, *args, **kwargs):
        data = request.data
        if isinstance(data, QueryDict):
            data._mutable = True
        telescope = data.get('telescope', None)
        task_type = Task.TRACKING_MODE
        tracking_data = data.get('tracking_data', None)
        satellite = tracking_data.get('satellite_id', None)
        mag = tracking_data.get('mag', None)
        cs_type = Point.EARTH_SYSTEM
        track_points = data.get('track_points', None)
        points = []
        for p in track_points:
            point = {'dt': p['dt'], 'alpha': p['alpha'], 'beta': p['beta'], 'cs_type': cs_type}
            points.append(point)
        frames = data.get('frames', None)
        for frame in frames:
            frame.update(mag=mag)
        data.clear()
        data.update(telescope=telescope)
        data.update(satellite=satellite)
        data.update(task_type=task_type)
        data.update(data_tle='')
        data.update(data_json=json.dumps({'points': points, 'frames': frames}))
        return super().create(request, *args, **kwargs)


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


class UserTasks(generics.ListAPIView):
    serializer_class = TaskSerializer

    def get_queryset(self):
        return Task.objects.filter(author=self.request.user).order_by('-id')


class TaskResultView(generics.RetrieveAPIView):
    serializer_class = TaskResultSerializer
    queryset = Task.objects.all()


class TelescopeTasks(generics.ListAPIView):
    serializer_class = TelescopeTaskSerializer

    def get_queryset(self):
        plan = {}
        telescope = get_object_or_404(Telescope, user=self.request.user)
        telescope_id = telescope.id
        plan['telescope'] = telescope.to_dict()
        plan['telescope']['avatar'] = None
        jdn = int(julian.to_jd(datetime.now()))
        plan['jdn'] = jdn
        tasks = Task.objects.filter(Q(
            status=Task.CREATED,
            telescope_id=telescope_id,
            jdn=jdn
        )).order_by('start_dt')
        plan['points'] = []
        plan['frames'] = []
        for task in tasks:
            points = Point.objects.filter(task=task).order_by('dt')
            for point in points:
                p = point.to_dict()
                p['task_type'] = task.task_type
                if task.satellite is not None:
                    p['satellite'] = task.satellite.number
                plan['points'].append(p)
            frames = Frame.objects.filter(task=task).order_by('dt')
            for frame in frames:
                f = frame.to_dict()
                f['task_type'] = task.task_type
                if task.satellite is not None:
                    f['satellite'] = task.satellite.number
                plan['frames'].append(f)
        return [plan]


class TaskStatusView(generics.CreateAPIView):
    serializer_class = TaskStatusSerializer

    def create(self, request, *args, **kwargs):
        task_serializer_class = self.get_serializer_class()
        task_serializer = task_serializer_class(data=request.data, context=self.get_serializer_context())
        if not task_serializer.is_valid():
            return Response(task_serializer.errors, status=400)
        task = task_serializer.save(user=request.user)
        return Response(data={
            'msg': f'Задание №{task.id} успешно обновлено',
            'status': 'ok'
        })


class ResultCreateView(generics.CreateAPIView):
    serializer_class = ResultSerializer

    def create(self, request, *args, **kwargs):
        result_serializer_class = self.get_serializer_class()
        result_serializer = result_serializer_class(data=request.data, context=self.get_serializer_context())
        if not result_serializer.is_valid():
            return Response(result_serializer.errors, status=400)
        result = result_serializer.save(user=request.user, task_id=int(kwargs.pop('task_id', None)))
        return Response(data={
            'msg': f'Результат №{result.id} успешно обновлен',
            'status': 'ok'
        })
