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


class CreateRoleLink(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Role")
    url = "horizon:iot:roles:create"
    classes = ("ajax-modal",)
    icon = "plus"
    # policy_rules = (("iot", "iot:create_role"),)


class EditRoleLink(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit")
    url = "horizon:iot:roles:update"
    classes = ("ajax-modal",)
    icon = "pencil"
    # policy_rules = (("iot", "iot:update_role"),)

    """
    def allowed(self, request, role):
        return api.keystone.keystone_can_edit_role()
    """


class DeleteRolesAction(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Role",
            u"Delete Roles",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Role",
            u"Deleted Roles",
            count
        )
    # policy_rules = (("iot", "iot:delete_role"),)

    """
    def allowed(self, request, role):
        return api.keystone.keystone_can_edit_role()
    """

    def delete(self, request, role_id):
        api.iotronic.role_delete(request, role_id)


class RoleFilterAction(tables.FilterAction):

    # If uncommented it will appear the select menu list of fields
    # and filter button
    """
    filter_type = "server"
    filter_choices = (("name", _("Role Name ="), True),
                      ("permissions", _("Role Permissions ="), True)
    """

    def filter(self, table, roles, filter_string):
        """Naive case-insensitive search."""
        q = filter_string.lower()
        return [role for role in roles
                if q in role.name.lower()]


class RolesTable(tables.DataTable):
    name = tables.Column('name', link="horizon:iot:roles:detail",
                         verbose_name=_('Role Name'))
    permissions = tables.WrappingColumn('permissions',
                                        verbose_name=_('Permissions'))
    description = tables.Column('description', verbose_name=_('Description'))

    # Overriding get_object_id method because in IoT service the "id" is
    # identified by the field UUID
    def get_object_id(self, datum):
        return datum.name

    class Meta(object):
        name = "roles"
        verbose_name = _("roles")
        row_actions = (EditRoleLink, DeleteRolesAction)
        table_actions = (RoleFilterAction, CreateRoleLink,
                         DeleteRolesAction)
