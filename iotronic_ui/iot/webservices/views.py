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
from horizon.utils import memoized

from openstack_dashboard.api import iotronic
from openstack_dashboard import policy

from iotronic_ui.iot.webservices import forms as project_forms
from iotronic_ui.iot.webservices import tables as project_tables


LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = project_tables.WebservicesTable
    template_name = 'iot/webservices/index.html'
    page_title = _("Web Services")

    def get_data(self):
        webservices = []
        en_webservices = []

        # Admin
        if policy.check((("iot", "iot:list_all_webservices"),), self.request):
            try:
                webservices = iotronic.webservice_list(self.request,
                                                       None)
                en_webservices = iotronic.webservice_enabled_list(self.request)

            except Exception:
                exceptions.handle(self.request,
                                  _('Unable to retrieve webservices list.'))

        # Admin_iot_project
        elif policy.check((("iot", "iot:list_project_webservices"),),
                          self.request):
            try:
                webservices = iotronic.webservice_list(self.request,
                                                       None)
                en_webservices = iotronic.webservice_enabled_list(self.request)

            except Exception:
                exceptions.handle(self.request,
                                  _('Unable to retrieve webservices list.'))

        # Other users
        else:
            try:
                webservices = iotronic.webservice_list(self.request,
                                                       None)
                en_webservices = iotronic.webservice_enabled_list(self.request)

            except Exception:
                exceptions.handle(self.request,
                                  _('Unable to retrieve webservices list.'))

        # Append some information to the webservice
        # LOG.debug('WSS: %s', webservices)
        for ws_en in en_webservices:

            ws_list = []

            for ws in webservices:
                if ws_en.board_uuid == ws.board_uuid:

                    service_url = "https://" + ws.name + "." + ws_en.dns +\
                                  "." + ws_en.zone
                    ws_list.append({"local_port": ws.port,
                                    "service_url": service_url})

                    ws_en.uuid = ws.uuid

            board = iotronic.board_get(self.request, ws_en.board_uuid, None)
            ws_en.name = board.name
            ws_en._info.update(dict(webservices=ws_list))
            ws_en.delegations = 'delegations...'

        return en_webservices


class ExposeView(forms.ModalFormView):
    template_name = 'iot/webservices/expose.html'
    modal_header = _("Expose Web Service")
    form_id = "expose_webservice_form"
    form_class = project_forms.ExposeWebserviceForm
    submit_label = _("Expose")
    submit_url = "horizon:iot:webservices:expose"
    success_url = reverse_lazy('horizon:iot:webservices:index')
    page_title = _("Expose Web Service")

    @memoized.memoized_method
    def get_object(self):
        try:
            return iotronic.board_get(self.request,
                                      self.kwargs['board_id'],
                                      None)
        except Exception:
            redirect = reverse("horizon:iot:webservices:index")
            exceptions.handle(self.request,
                              _('Unable to get webservice information.'),
                              redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(ExposeView, self).get_context_data(**kwargs)
        args = (self.get_object().uuid,)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        board = self.get_object()
        board_exp_info = iotronic.webservice_get_enabled_info(self.request,
                                                              board.uuid)
        zone = board_exp_info.dns + "." + board_exp_info.zone

        return {'uuid': board.uuid, 'name': board.name, 'zone': zone}


class UnexposeView(forms.ModalFormView):
    template_name = 'iot/webservices/unexpose.html'
    modal_header = _("Unexpose Web Service")
    form_id = "unexpose_webservice_form"
    form_class = project_forms.UnexposeWebserviceForm
    submit_label = _("Unexpose")
    submit_url = "horizon:iot:webservices:unexpose"
    success_url = reverse_lazy('horizon:iot:webservices:index')
    page_title = _("Unexpose Web Service")

    @memoized.memoized_method
    def get_object(self):
        try:
            return iotronic.board_get(self.request,
                                      self.kwargs['board_id'],
                                      None)
        except Exception:
            redirect = reverse("horizon:iot:webservices:index")
            exceptions.handle(self.request,
                              _('Unable to get webservice information.'),
                              redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(UnexposeView, self).get_context_data(**kwargs)
        args = (self.get_object().uuid,)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        board = self.get_object()

        # Populate web services on board
        ws_onboard = iotronic.webservices_on_board(self.request, board.uuid)
        ws_onboard.sort(key=lambda b: b["name"])

        ws_onboard_list = []
        for ws in ws_onboard:
            ws_onboard_list.append((ws["uuid"], _(ws["name"])))

        return {'uuid': board.uuid,
                'name': board.name,
                'ws_onboard': ws_onboard_list}


"""
class DetailView(tabs.TabView):
    tab_group_class = project_tabs.WebserviceDetailTabs
    template_name = 'horizon/common/_detail.html'
    page_title = "{{ webservice.name|default:webservice.uuid }}"

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        webservice = self.get_data()
        context["webservice"] = webservice
        context["url"] = reverse(self.redirect_url)
        context["actions"] = self._get_actions(webservice)

        return context

    def _get_actions(self, webservice):
        table = project_tables.WebservicesTable(self.request)
        return table.render_row_actions(webservice)

    @memoized.memoized_method
    def get_data(self):
        webservice = []

        webservice_id = self.kwargs['webservice_id']
        try:
            webservice = iotronic.webservice_get(self.request,
                                                 webservice_id,
                                                 None)
            board = iotronic.board_get(self.request,
                                       webservice.board_uuid,
                                       None)

            webservice._info.update({u'board_name': board.name})
            webservice.board_name = board.name
            # LOG.debug('WS: %s', webservice)

        except Exception:
            s = webservice.name
            m = ('Unable to retrieve webservice %s information') % {'name': s}
            exceptions.handle(self.request, m, ignore=True)

        return webservice

    def get_tabs(self, request, *args, **kwargs):
        webservice = self.get_data()
        return self.tab_group_class(request, webservice=webservice, **kwargs)


class WebserviceDetailView(DetailView):
    redirect_url = 'horizon:iot:webservices:index'

    def _get_actions(self, webservice):
        table = project_tables.WebservicesTable(self.request)
        return table.render_row_actions(webservice)
"""

# Delegation


class WebserviceDelegateView(forms.ModalFormView):
    template_name = 'iot/delegatenode.html'
    modal_header = _("Delegate a webservice")
    form_id = "delegate_webservice"
    form_class = project_forms.WebserviceDelegateForm
    submit_label = _("Delegate")
    submit_url = "horizon:iot:webservices:delegatewebservice"
    success_url = reverse_lazy('horizon:iot:webservices:index')
    page_title = _("Delegate webservice {{webservice.name}}")

    @memoized.memoized_method
    def get_object(self):
        try:
            return iotronic.webservice_get(self.request,
                                           self.kwargs['webservice_id'],
                                           None)
        except Exception:
            redirect = reverse("horizon:iot:webservices:index")
            exceptions.handle(self.request,
                              _('Unable to get webservice information.'),
                              redirect=redirect)

    @memoized.memoized_method
    def get_roles(self):
        try:
            return iotronic.role_list(self.request)
        except Exception as ex:
            redirect = reverse("horizon:iot:webservices:index")
            exceptions.handle(self.request,
                              _('Unable to get role information.\n')
                              + str(ex),
                              redirect=redirect)

    @memoized.memoized_method
    def get_users(self):
        try:
            return iotronic.user_list(self.request)
        except Exception as ex:
            redirect = reverse("horizon:iot:webservices:index")
            exceptions.handle(self.request,
                              _('Unable to get users information.\n')
                              + str(ex),
                              redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(WebserviceDelegateView,
                        self).get_context_data(**kwargs)
        args = (self.get_object().uuid,)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        webservice = self.get_object()
        roles = self.get_roles()
        users = self.get_users()
        return {'webservice_uuid': webservice.uuid,
                'roles': roles,
                'users': users}


class DelegationUpdateView(forms.ModalFormView):
    template_name = 'iot/delegation_update.html'
    modal_header = _("Update Webservice Delegation")
    form_id = "update_webservice_delegation_form"
    form_class = project_forms.UpdateWebserviceDelegationForm
    submit_label = _("Update Webservice Delegation")
    submit_url = "horizon:iot:webservices:delegationupdate"
    # success_url = reverse_lazy('horizon:iot:boards:delegations')
    page_title = _("Update Webservice Delegation")
    base_node = None

    def get_success_url(self, **kwargs):
        return reverse('horizon:iot:webservices:delegations',
                       args={self.base_node: 'webservice_id'})

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
        return {'webservice': delegation.node,
                'delegation': delegation.uuid,
                'delegated': delegation.delegated,
                'delegator': delegation.delegator,
                'roles': roles,
                'current_role': delegation.role, }


class DelegationDeleteView(forms.ModalFormView):
    template_name = 'iot/delegation_delete.html'
    modal_header = _("Delete Webservice Delegation")
    form_id = "delete_webservice_delegation_form"
    form_class = project_forms.DeleteWebserviceDelegationForm
    submit_label = _("Delete Webservice Delegation")
    submit_url = "horizon:iot:webservices:delegationdelete"
    # success_url = reverse_lazy('horizon:iot:webservices:delegations')
    page_title = _("Delete Webservice Delegation")
    base_node = None

    def get_success_url(self, **kwargs):
        return reverse('horizon:iot:webservices:delegations',
                       args={self.base_node: 'webservice_id'})

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
        return {'webservice': delegation.node,
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
                self.request, self.kwargs['webservice_id'], 'webservice')
        except Exception as ex:
            exceptions.handle(self.request,
                              _('Unable to retrieve delegations list.\n')
                              + str(ex))

        return delegation


class WebserviceDelegationsView(DelegationsView):
    redirect_url = 'horizon:iot:webservices:index'

    def _get_actions(self, delegation):
        table = project_tables.DelegationsTable(self.request)
        return table.render_row_actions(delegation)
