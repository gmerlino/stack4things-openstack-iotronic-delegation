# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.conf.urls import url

from iotronic_ui.iot.plugins import views


urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^create/$', views.CreateView.as_view(), name='create'),
    url(r'^(?P<plugin_id>[^/]+)/update/$', views.UpdateView.as_view(),
        name='update'),
    url(r'^(?P<plugin_id>[^/]+)/inject/$', views.InjectView.as_view(),
        name='inject'),
    url(r'^(?P<plugin_id>[^/]+)/start/$', views.StartView.as_view(),
        name='start'),
    url(r'^(?P<plugin_id>[^/]+)/stop/$', views.StopView.as_view(),
        name='stop'),
    url(r'^(?P<plugin_id>[^/]+)/call/$', views.CallView.as_view(),
        name='call'),
    url(r'^(?P<plugin_id>[^/]+)/remove/$', views.RemoveView.as_view(),
        name='remove'),
    url(r'^(?P<plugin_id>[^/]+)/detail/$', views.PluginDetailView.as_view(),
        name='detail'),
    url(r'^(?P<plugin_id>[^/]+)/delegate/$',
        views.PluginDelegateView.as_view(),
        name='delegateplugin'),
    url(r'^(?P<plugin_id>[^/]+)/delegations/$',
        views.PluginDelegationsView.as_view(),
        name='delegations'),
    url(r'^plugins/delegations/(?P<delegation_id>[^/]+)/update/$',
        views.DelegationUpdateView.as_view(),
        name='delegationupdate'),
    url(r'^plugins/delegations/(?P<delegation_id>[^/]+)/delete/$',
        views.DelegationDeleteView.as_view(),
        name='delegationdelete'),
]
