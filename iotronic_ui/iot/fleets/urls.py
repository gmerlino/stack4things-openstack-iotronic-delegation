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

from iotronic_ui.iot.fleets import views


urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^create/$', views.CreateView.as_view(), name='create'),
    url(r'^(?P<fleet_id>[^/]+)/update/$', views.UpdateView.as_view(),
        name='update'),
    url(r'^(?P<fleet_id>[^/]+)/detail/$', views.FleetDetailView.as_view(),
        name='detail'),
    url(r'^(?P<fleet_id>[^/]+)/delegate/$', views.FleetDelegateView.as_view(),
        name='delegatefleet'),
    url(r'^(?P<fleet_id>[^/]+)/delegations/$',
        views.FleetDelegationsView.as_view(),
        name='delegations'),
    url(r'^fleets/delegations/(?P<delegation_id>[^/]+)/update/$',
        views.DelegationUpdateView.as_view(),
        name='delegationupdate'),
    url(r'^fleets/delegations/(?P<delegation_id>[^/]+)/delete/$',
        views.DelegationDeleteView.as_view(),
        name='delegationdelete'),
]
