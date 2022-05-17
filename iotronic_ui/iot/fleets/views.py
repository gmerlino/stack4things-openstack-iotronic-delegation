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
# from horizon import messages
from horizon import tables
from horizon import tabs
from horizon.utils import memoized

from openstack_dashboard.api import iotronic
from openstack_dashboard import policy

from iotronic_ui.iot.fleets import forms as project_forms
from iotronic_ui.iot.fleets import tables as project_tables
from iotronic_ui.iot.fleets import tabs as project_tabs


LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = project_tables.FleetsTable
    template_name = 'iot/fleets/index.html'
    page_title = _("Fleets")

    def get_data(self):
        fleets = []

        # Admin
        if policy.check((("iot", "iot:list_all_fleets"),), self.request):
            try:
                fleets = iotronic.fleet_list(self.request, None)

            except Exception:
                exceptions.handle(self.request,
                                  _('Unable to retrieve fleets list.'))

        # Admin_iot_project
        elif policy.check((("iot", "iot:list_project_fleets"),),
                          self.request):
            try:
                fleets = iotronic.fleet_list(self.request, None)

            except Exception:
                exceptions.handle(self.request,
                                  _('Unable to retrieve user fleets list.'))

        # Other users
        else:
            try:
                fleets = iotronic.fleet_list(self.request, None)

            except Exception:
                exceptions.handle(self.request,
                                  _('Unable to retrieve user fleets list.'))
        for fleet in fleets:
            fleet.delegations = 'delegations...'

        return fleets


class CreateView(forms.ModalFormView):
    template_name = 'iot/fleets/create.html'
    modal_header = _("Create Fleet")
    form_id = "create_fleet_form"
    form_class = project_forms.CreateFleetForm
    submit_label = _("Create Fleet")
    submit_url = reverse_lazy("horizon:iot:fleets:create")
    success_url = reverse_lazy('horizon:iot:fleets:index')
    page_title = _("Create Fleet")


class UpdateView(forms.ModalFormView):
    template_name = 'iot/fleets/update.html'
    modal_header = _("Update Fleet")
    form_id = "update_fleet_form"
    form_class = project_forms.UpdateFleetForm
    submit_label = _("Update Fleet")
    submit_url = "horizon:iot:fleets:update"
    success_url = reverse_lazy('horizon:iot:fleets:index')
    page_title = _("Update Fleet")

    @memoized.memoized_method
    def get_object(self):
        try:
            return iotronic.fleet_get(self.request,
                                      self.kwargs['fleet_id'],
                                      None)
        except Exception:
            redirect = reverse("horizon:iot:fleets:index")
            exceptions.handle(self.request,
                              _('Unable to get fleet information.'),
                              redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        args = (self.get_object().uuid,)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        fleet = self.get_object()

        return {'uuid': fleet.uuid,
                'name': fleet.name,
                'description': fleet.description}


class DetailView(tabs.TabView):
    tab_group_class = project_tabs.FleetDetailTabs
    template_name = 'horizon/common/_detail.html'
    page_title = "{{ fleet.name|default:fleet.uuid }}"

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        fleet = self.get_data()
        context["fleet"] = fleet
        context["url"] = reverse(self.redirect_url)
        context["actions"] = self._get_actions(fleet)

        return context

    def _get_actions(self, fleet):
        table = project_tables.FleetsTable(self.request)
        return table.render_row_actions(fleet)

    @memoized.memoized_method
    def get_data(self):
        fleet = []
        fleet_boards = []

        fleet_id = self.kwargs['fleet_id']
        try:
            fleet = iotronic.fleet_get(self.request, fleet_id, None)
            boards = iotronic.fleet_get_boards(self.request, fleet_id)

            # LOG.debug('Boards: %s', boards)

            for board in boards:
                fleet_boards.append(board._info)

            fleet._info.update(dict(boards=fleet_boards))
            # LOG.debug('FLEET COMPLETE: %s', fleet)

        except Exception:
            s = fleet.name
            msg = ('Unable to retrieve fleet %s information') % {'name': s}
            exceptions.handle(self.request, msg, ignore=True)
        return fleet

    def get_tabs(self, request, *args, **kwargs):
        fleet = self.get_data()
        return self.tab_group_class(request, fleet=fleet, **kwargs)


class FleetDetailView(DetailView):
    redirect_url = 'horizon:iot:fleets:index'

    def _get_actions(self, fleet):
        table = project_tables.FleetsTable(self.request)
        return table.render_row_actions(fleet)

# Delegation


class FleetDelegateView(forms.ModalFormView):
    template_name = 'iot/delegatenode.html'
    modal_header = _("Delegate a fleet")
    form_id = "delegate_fleet"
    form_class = project_forms.FleetDelegateForm
    submit_label = _("Delegate")
    submit_url = "horizon:iot:fleets:delegatefleet"
    success_url = reverse_lazy('horizon:iot:fleets:index')
    page_title = _("Delegate fleet {{fleet.name}}")

    @memoized.memoized_method
    def get_object(self):
        try:
            return iotronic.fleet_get(self.request,
                                      self.kwargs['fleet_id'],
                                      None)
        except Exception:
            redirect = reverse("horizon:iot:fleets:index")
            exceptions.handle(self.request,
                              _('Unable to get fleet information.'),
                              redirect=redirect)

    @memoized.memoized_method
    def get_roles(self):
        try:
            return iotronic.role_list(self.request)
        except Exception as ex:
            redirect = reverse("horizon:iot:fleets:index")
            exceptions.handle(self.request,
                              _('Unable to get role information.\n')
                              + str(ex),
                              redirect=redirect)

    @memoized.memoized_method
    def get_users(self):
        try:
            return iotronic.user_list(self.request)
        except Exception as ex:
            redirect = reverse("horizon:iot:fleets:index")
            exceptions.handle(self.request,
                              _('Unable to get users information.\n')
                              + str(ex),
                              redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(FleetDelegateView, self).get_context_data(**kwargs)
        args = (self.get_object().uuid,)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        fleet = self.get_object()
        roles = self.get_roles()
        users = self.get_users()
        return {'fleet_uuid': fleet.uuid,
                'roles': roles,
                'users': users}


class DelegationUpdateView(forms.ModalFormView):
    template_name = 'iot/delegation_update.html'
    modal_header = _("Update Fleet Delegation")
    form_id = "update_fleet_delegation_form"
    form_class = project_forms.UpdateFleetDelegationForm
    submit_label = _("Update Fleet Delegation")
    submit_url = "horizon:iot:fleets:delegationupdate"
    # success_url = reverse_lazy('horizon:iot:fleets:delegations')
    page_title = _("Update Fleet Delegation")
    base_node = None

    def get_success_url(self, **kwargs):
        return reverse('horizon:iot:fleets:delegations',
                       args={self.base_node: 'fleet_id'})

    @memoized.memoized_method
    def get_roles(self):
        try:
            return iotronic.role_list(self.request)
        except Exception as ex:
            exceptions.handle(self.request,
                              _('Unable to get role information.\n') + str(ex))

    @memoized.memoized_method
    def get_delegation(self):
        try:
            dele = self.kwargs['delegation_id']
            return iotronic.node_delegation_get(self.request, dele)
        except Exception as ex:
            exceptions.handle(self.request,
                              _('Unable to get delegation information.\n')
                              + str(ex))

    def get_context_data(self, **kwargs):
        context = super(DelegationUpdateView, self).get_context_data(**kwargs)
        args = (self.kwargs['delegation_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        delegation = self.get_delegation()
        roles = self.get_roles()
        self.base_node = delegation.node
        return {'fleet': delegation.node,
                'delegation': delegation.uuid,
                'delegated': delegation.delegated,
                'delegator': delegation.delegator,
                'roles': roles,
                'current_role': delegation.role, }


class DelegationDeleteView(forms.ModalFormView):
    template_name = 'iot/delegation_delete.html'
    modal_header = _("Delete Fleet Delegation")
    form_id = "delete_fleet_delegation_form"
    form_class = project_forms.DeleteFleetDelegationForm
    submit_label = _("Delete Fleet Delegation")
    submit_url = "horizon:iot:fleets:delegationdelete"
    # success_url = reverse_lazy('horizon:iot:fleets:delegations')
    page_title = _("Delete Fleet Delegation")
    base_node = None

    def get_success_url(self, **kwargs):
        return reverse('horizon:iot:fleets:delegations',
                       args={self.base_node: 'fleet_id'})

    @memoized.memoized_method
    def get_delegation(self):
        try:
            dele = self.kwargs['delegation_id']
            return iotronic.node_delegation_get(self.request, dele)
        except Exception as ex:
            exceptions.handle(self.request,
                              _('Unable to get delegation information.\n')
                              + str(ex))

    def get_context_data(self, **kwargs):
        context = super(DelegationDeleteView, self).get_context_data(**kwargs)
        args = (self.kwargs['delegation_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        delegation = self.get_delegation()
        self.base_node = delegation.node
        return {'fleet': delegation.node,
                'delegation': delegation.uuid, }


class DelegationsView(tables.DataTableView):
    table_class = project_tables.DelegationsTable
    template_name = 'iot/delegations.html'
    page_title = _("Delegations")

    @memoized.memoized_method
    def get_data(self):
        delegation = []
        try:
            delegation = iotronic.node_delegation_list(
                self.request, self.kwargs['fleet_id'], 'fleet')
        except Exception as ex:
            exceptions.handle(self.request,
                              _('Unable to retrieve delegations list.\n')
                              + str(ex))

        return delegation


class FleetDelegationsView(DelegationsView):
    redirect_url = 'horizon:iot:fleets:index'

    def _get_actions(self, delegation):
        table = project_tables.DelegationsTable(self.request)
        return table.render_row_actions(delegation)
