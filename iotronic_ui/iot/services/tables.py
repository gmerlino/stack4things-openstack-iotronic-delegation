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

from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables

from openstack_dashboard import api

LOG = logging.getLogger(__name__)


class CreateServiceLink(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Service")
    url = "horizon:iot:services:create"
    classes = ("ajax-modal",)
    icon = "plus"
    # policy_rules = (("iot", "iot:create_service"),)


class EditServiceLink(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit")
    url = "horizon:iot:services:update"
    classes = ("ajax-modal",)
    icon = "pencil"
    # policy_rules = (("iot", "iot:update_service"),)


class ActionServiceLink(tables.LinkAction):
    name = "action"
    verbose_name = _("Service Action")
    url = "horizon:iot:services:action"
    classes = ("ajax-modal",)
    # icon = "plus"
    # policy_rules = (("iot", "iot:service_action"),)


class DeleteServicesAction(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Service",
            u"Delete Services",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Service",
            u"Deleted Services",
            count
        )
    # policy_rules = (("iot", "iot:delete_service"),)

    def delete(self, request, service_id):
        api.iotronic.service_delete(request, service_id)


class ServiceFilterAction(tables.FilterAction):

    def filter(self, table, services, filter_string):
        # Naive case-insensitive search.
        q = filter_string.lower()
        return [service for service in services
                if q in service.name.lower()]


class DelegateLink(tables.LinkAction):
    name = "delegateservice"
    verbose_name = _("Delegate Service")
    url = "horizon:iot:services:delegateservice"
    classes = ("ajax-modal",)
    icon = "plus"


class ServicesTable(tables.DataTable):
    name = tables.WrappingColumn('name', link="horizon:iot:services:detail",
                                 verbose_name=_('Service Name'))
    protocol = tables.Column('protocol', verbose_name=_('Protocol'))
    port = tables.Column('port', verbose_name=_('Port'))
    delegations = tables.WrappingColumn('delegations',
                                        link="horizon:iot:services"
                                        ":delegations",
                                        verbose_name=_(''))

    # Overriding get_object_id method because in IoT service the "id" is
    # identified by the field UUID
    def get_object_id(self, datum):
        return datum.uuid

    class Meta(object):
        name = "services"
        verbose_name = _("services")
        row_actions = (EditServiceLink, DelegateLink, ActionServiceLink,
                       DeleteServicesAction)
        table_actions = (ServiceFilterAction, CreateServiceLink,
                         DeleteServicesAction)

# Delegation


class EditDelegationLink(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit")
    url = "horizon:iot:services:delegationupdate"
    classes = ("ajax-modal",)
    icon = "pencil"


class DeleteDelegationsAction(tables.LinkAction):
    name = "delete"
    verbose_name = _("Delete")
    url = "horizon:iot:services:delegationdelete"
    classes = ("ajax-modal",)
    icon = "trash"
    action_type = "danger"


class DelegationFilterAction(tables.FilterAction):

    # If uncommented it will appear the select menu list of fields
    # and filter button
    """
    filter_type = "server"
    filter_choices = (("uuid", _("UUID ="), True),
                      ("delegated", _("Delegated ="), True),
                      ("delegator", _("Delegator ="), True))
    """

    def filter(self, table, delegations, filter_string):
        """Naive case-insensitive search."""
        q = filter_string.lower()
        return [delegation for delegation in delegations
                if q in delegation.uuid]


class DelegationsTable(tables.DataTable):
    uuid = tables.WrappingColumn('uuid', verbose_name=_('UUID'))
    delegated = tables.Column('delegated', verbose_name=_('Delegated'))
    delegator = tables.Column('delegator', verbose_name=_('Delegator'))
    parent = tables.Column('parent', verbose_name=_('Parent'))
    node = tables.Column('node', verbose_name=_('Service'))
    role = tables.Column('role', verbose_name=_('Role'))
    # Overriding get_object_id method because in IoT service the "id" is
    # identified by the field UUID

    def get_object_id(self, datum):
        return datum.uuid

    class Meta(object):
        name = "delegations"
        verbose_name = _("delegations")
        row_actions = (EditDelegationLink, DeleteDelegationsAction)
        table_actions = (DelegationFilterAction,)  # DeleteDelegationsAction)
