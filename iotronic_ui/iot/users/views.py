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

import logging

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs
from horizon.utils import memoized

from openstack_dashboard import api
from openstack_dashboard import policy

from iotronic_ui.iot.users import forms as project_forms
from iotronic_ui.iot.users import tables as project_tables
from iotronic_ui.iot.users import tabs as project_tabs
from openstack_dashboard.utils import identity

LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = project_tables.UsersTable
    template_name = 'iot/users/index.html'
    page_title = _("Users")

    def get_data(self):
        users = []

        # Admin
        if policy.check((("iot", "iot:list_all_users"),), self.request):
            try:
                users = api.iotronic.user_list(self.request)

            except Exception as ex:
                exceptions.handle(self.request,
                                  _('Unable to retrieve users list.\n')
                                  + str(ex))

        # Admin_iot_project
        elif policy.check((("iot", "iot:list_project_users"),), self.request):
            try:
                users = api.iotronic.user_list(self.request)

            except Exception as ex:
                exceptions.handle(self.request,
                                  _('Unable to retrieve users list.\n')
                                  + str(ex))

        # Other users
        else:
            try:
                users = api.iotronic.user_list(self.request)

            except Exception as ex:
                exceptions.handle(self.request,
                                  _('Unable to retrieve users list.\n')
                                  + str(ex))

        return users


class CreateView(forms.ModalFormView):
    template_name = 'iot/users/create.html'
    modal_header = _("Create User")
    form_id = "create_user_form"
    form_class = project_forms.CreateUserForm
    submit_label = _("Create User")
    submit_url = reverse_lazy("horizon:iot:users:create")
    success_url = reverse_lazy('horizon:iot:users:index')
    page_title = _("Create User")

    @memoized.memoized_method
    def get_users(self):
        domain_id = identity.get_domain_id_for_operation(self.request)
        try:
            return api.keystone.user_list(self.request,
                                          domain=domain_id)
        except Exception:
            redirect = reverse("horizon:iot:users:index")
            exceptions.handle(self.request,
                              _('Unable to retrieve user list.'),
                              redirect=redirect)

    def get_roles(self):
        try:
            return api.iotronic.role_list(self.request)
        except Exception as ex:
            redirect = reverse("horizon:iot:users:index")
            exceptions.handle(self.request,
                              _('Unable to get user information.\n') + str(ex),
                              redirect=redirect)

    def get_initial(self):
        roles = self.get_roles()
        users = self.get_users()
        return {"users": users, "roles": roles}


class UpdateView(forms.ModalFormView):
    template_name = 'iot/users/update.html'
    modal_header = _("Update User")
    form_id = "update_user_form"
    form_class = project_forms.UpdateUserForm
    submit_label = _("Update User")
    submit_url = "horizon:iot:users:update"
    success_url = reverse_lazy('horizon:iot:users:index')
    page_title = _("Update User")

    @memoized.memoized_method
    def get_roles(self):
        try:
            return api.iotronic.role_list(self.request)
        except Exception as ex:
            redirect = reverse("horizon:iot:users:index")
            exceptions.handle(self.request,
                              _('Unable to get user information.\n') + str(ex),
                              redirect=redirect)

    def get_object(self):
        try:
            return api.iotronic.user_get(self.request,
                                         self.kwargs['user_id'])
        except Exception as ex:
            redirect = reverse("horizon:iot:users:index")
            exceptions.handle(self.request,
                              _('Unable to get user information.\n') + str(ex),
                              redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        args = (self.get_object().uuid,)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        user = self.get_object()
        roles = self.get_roles()
        return {'uuid': user.uuid,
                'name': user.name,
                'current_role': user.base_role,
                'roles': roles}


class DetailView(tabs.TabView):
    tab_group_class = project_tabs.UserDetailTabs
    template_name = 'horizon/common/_detail.html'
    page_title = "{{ user.name|default:user.uuid }}"

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        user = self.get_data()
        context["user"] = user
        context["url"] = reverse(self.redirect_url)
        context["actions"] = self._get_actions(user)

        return context

    def _get_actions(self, user):
        table = project_tables.UsersTable(self.request)
        return table.render_row_actions(user)

    @memoized.memoized_method
    def get_data(self):
        user = []
        user_id = self.kwargs['user_id']
        try:
            user = api.iotronic.user_get(self.request, user_id)
        except Exception as ex:
            msg = (('Unable to retrieve user %s information\n') %
                   {'name': user.name}) + str(ex)
            exceptions.handle(self.request, msg, ignore=True)
        return user

    def get_tabs(self, request, *args, **kwargs):
        user = self.get_data()
        return self.tab_group_class(request, user=user, **kwargs)


class UserDetailView(DetailView):
    redirect_url = 'horizon:iot:users:index'

    def _get_actions(self, user):
        table = project_tables.UsersTable(self.request)
        return table.render_row_actions(user)
