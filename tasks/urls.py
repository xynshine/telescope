from django.urls import re_path

import tasks.views as views

urlpatterns = [
    re_path(r'^telescopes/$', views.TelescopeView.as_view(), name='telescope_list'),
    re_path(r'^satellites/$', views.SatelliteView.as_view(), name='satellite_list'),
    re_path(r'^satellite_add/$', views.SatelliteCreateView.as_view(), name='satellite_add'),
    re_path(r'^inputdata/$', views.InputDataView.as_view(), name='inputdata_list'),
    re_path(r'^get_tasks/$', views.UserTasks.as_view(), name='user_tasks'),
    re_path(r'^task_add/$', views.UserTaskCreateView.as_view(), name='task_add'),
    re_path(r'^point_task/$', views.PointTaskCreateView.as_view(), name='point_task_add'),
    re_path(r'^tracking_task/$', views.TrackingTaskCreateView.as_view(), name='tracking_task_add'),
    re_path(r'^tasks_get/$', views.TelescopeTasks.as_view(), name='telescope_tasks'),
    re_path(r'^task_stat/$', views.TaskStatusView.as_view(), name='task_status'),
    # re_path(r'^(?P<pk>\d+)/get_result/$', views.TaskResult.as_view(), name='task_result'),
    re_path(r'^requests/$', views.BalanceRequestView.as_view(), name='requests'),
    re_path(r'^save_request/$', views.BalanceRequestCreateView.as_view(), name='save_request'),
    re_path(r'^telescopes_with_balances/$', views.TelescopeChoosingView.as_view(), name='telescope_with_balances'),
]
