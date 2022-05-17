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

from iotronic_ui.iot.roles import forms as project_forms
from iotronic_ui.iot.roles import tables as project_tables
from iotronic_ui.iot.roles import tabs as project_tabs

LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = project_tables.RolesTable
    template_name = 'iot/roles/index.html'
    page_title = _("Roles")

    def get_data(self):
        roles = []

        # Admin
        if policy.check((("iot", "iot:list_all_roles"),), self.request):
            try:
                roles = api.iotronic.role_list(self.request)

            except Exception as ex:
                exceptions.handle(self.request,
                                  _('Unable to retrieve roles list.\n')
                                  + str(ex))

        # Admin_iot_project
        elif policy.check((("iot", "iot:list_project_roles"),), self.request):
            try:
                roles = api.iotronic.role_list(self.request)

            except Exception as ex:
                exceptions.handle(self.request,
                                  _('Unable to retrieve user roles list.\n')
                                  + str(ex))

        # Other users
        else:
            try:
                roles = api.iotronic.role_list(self.request)

            except Exception as ex:
                exceptions.handle(self.request,
                                  _('Unable to retrieve user roles list.\n')
                                  + str(ex))
        for role in roles:
            role.permissions = [str(i) for i in role.permissions]
        return roles


class CreateView(forms.ModalFormView):
    template_name = 'iot/roles/create.html'
    modal_header = _("Create Role")
    form_id = "create_role_form"
    form_class = project_forms.CreateRoleForm
    submit_label = _("Create Role")
    submit_url = reverse_lazy("horizon:iot:roles:create")
    success_url = reverse_lazy('horizon:iot:roles:index')
    page_title = _("Create Role")

    @memoized.memoized_method
    def get_object(self):
        try:
            return api.iotronic.role_get_operations(self.request)

        except Exception as ex:
            redirect = reverse("horizon:iot:roles:index")
            exceptions.handle(self.request,
                              _('Unable to get operations information.\n')
                              + str(ex),
                              redirect=redirect)

    def get_initial(self):
        ops = self.get_object()
        return {'opers': [str(i) for i in ops]}


class UpdateView(forms.ModalFormView):
    template_name = 'iot/roles/update.html'
    modal_header = _("Update Role")
    form_id = "update_role_form"
    form_class = project_forms.UpdateRoleForm
    submit_label = _("Update Role")
    submit_url = "horizon:iot:roles:update"
    success_url = reverse_lazy('horizon:iot:roles:index')
    page_title = _("Update Role")

    @memoized.memoized_method
    def get_object(self):
        try:
            return api.iotronic.role_get(self.request,
                                         self.kwargs['role_id'])
        except Exception as ex:
            redirect = reverse("horizon:iot:roles:index")
            exceptions.handle(self.request,
                              _('Unable to get role information.\n')
                              + str(ex),
                              redirect=redirect)

    @memoized.memoized_method
    def get_ops(self):
        try:
            return api.iotronic.role_get_operations(self.request)

        except Exception as ex:
            redirect = reverse("horizon:iot:roles:index")
            exceptions.handle(self.request,
                              _('Unable to get operations information.\n')
                              + str(ex),
                              redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        args = (self.get_object().name,)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        role = self.get_object()
        ops = self.get_ops()
        return {'name': role.name,
                'opers': [str(i) for i in ops],
                'curr_perms': [str(i) for i in role.permissions],
                'description': role.description}


class DetailView(tabs.TabView):
    tab_group_class = project_tabs.RoleDetailTabs
    template_name = 'horizon/common/_detail.html'
    page_title = "{{role.name}}"

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        role = self.get_data()
        role.permissions = [str(i) for i in role.permissions]
        context["role"] = role
        context["url"] = reverse(self.redirect_url)
        context["actions"] = self._get_actions(role)

        return context

    def _get_actions(self, role):
        table = project_tables.RolesTable(self.request)
        return table.render_row_actions(role)

    @memoized.memoized_method
    def get_data(self):
        role = []
        role_id = self.kwargs['role_id']
        try:
            role = api.iotronic.role_get(self.request, role_id)
        except Exception as ex:
            msg = (('Unable to retrieve role %s information\n') %
                   {'name': role.name}) + str(ex)
            exceptions.handle(self.request, msg, ignore=True)
        return role

    def get_tabs(self, request, *args, **kwargs):
        role = self.get_data()
        return self.tab_group_class(request, role=role, **kwargs)


class RoleDetailView(DetailView):
    redirect_url = 'horizon:iot:roles:index'

    def _get_actions(self, role):
        table = project_tables.RolesTable(self.request)
        return table.render_row_actions(role)
