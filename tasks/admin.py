from django.contrib import admin
from .models import Telescope, Task, TrackingData, TLEData, Point, Frame, TrackPoint, Balance, BalanceRequest, \
    TaskResult, Satellite, InputData

admin.site.register(Telescope)
admin.site.register(Satellite)
admin.site.register(Task)
admin.site.register(InputData)
admin.site.register(TrackingData)
admin.site.register(TLEData)
admin.site.register(Point)
admin.site.register(Frame)
admin.site.register(TrackPoint)
admin.site.register(Balance)
admin.site.register(TaskResult)
admin.site.register(BalanceRequest)
