from django.urls import re_path, include

import tasks.views as views

urlpatterns = [
    re_path(r'^telescopes/$', views.TelescopeView.as_view(), name='telescope_list'),
    re_path(r'^satellites/$', views.SatelliteView.as_view(), name='satellite_list'),
    re_path(r'^satellite_add/$', views.SatelliteCreateView.as_view(), name='satellite_add'),
    re_path(r'^inputdata/$', views.InputDataView.as_view(), name='inputdata_list'),
    re_path(r'^tasks/$', views.UserTasks.as_view(), name='user_tasks'),
    re_path(r'^task_add/$', views.UserTaskCreateView.as_view(), name='task_add'),
    re_path(r'^tasks_get/(?P<jdn>\d+)?/?$', views.get_telescope_tasks, name='tasks_get'),
    re_path(r'^(?P<pk>\d+)/get_result/$', views.TaskResult.as_view(), name='task_result'),
    re_path(r'^requests/$', views.BalanceRequestView.as_view(), name='requests'),
    re_path(r'^save_request/$', views.BalanceRequestCreateView.as_view(), name='save_request'),
    re_path(r'^telescopes_with_balances/$', views.TelescopeChoosingView.as_view(), name='telescope_with_balances'),
    re_path(r'^(?P<telescope_id>\d+)/schedule/$', views.get_telescope_schedule, name='telescope_schedule'),
    re_path(r'^(?P<telescope_id>\d+)/get_plan/(?P<task_id>\d+)/$', views.get_telescope_plan, name='get_telescope_plan'),
]
