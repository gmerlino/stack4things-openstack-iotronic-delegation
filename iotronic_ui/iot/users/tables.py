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


class CreateUserLink(tables.LinkAction):
    name = "create"
    verbose_name = _("Create User")
    url = "horizon:iot:users:create"
    classes = ("ajax-modal",)
    icon = "plus"
    # policy_rules = (("iot", "iot:create_user"),)


class EditUserLink(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit")
    url = "horizon:iot:users:update"
    classes = ("ajax-modal",)
    icon = "pencil"
    # policy_rules = (("iot", "iot:update_user"),)

    """
    def allowed(self, request, role):
        return api.keystone.keystone_can_edit_role()
    """


class DeleteUsersAction(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete User",
            u"Delete Users",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted User",
            u"Deleted Users",
            count
        )
    # policy_rules = (("iot", "iot:delete_user"),)

    """
    def allowed(self, request, role):
        return api.keystone.keystone_can_edit_role()
    """

    def delete(self, request, user_id):
        api.iotronic.user_delete(request, user_id)


class UserFilterAction(tables.FilterAction):

    # If uncommented it will appear the select menu list of fields
    # and filter button
    """
    filter_type = "server"
    filter_choices = (("uuid", _("User ID ="), True),
                      ("name", _("User Name ="), True),
                      ("base_role", _("Base Role ="), True))
    """

    def filter(self, table, users, filter_string):
        """Naive case-insensitive search."""
        q = filter_string.lower()
        return [user for user in users
                if q in user.name.lower()]


class UsersTable(tables.DataTable):
    uuid = tables.Column('uuid', verbose_name=_('User ID'))
    name = tables.WrappingColumn('name', link="horizon:iot:users:detail",
                                 verbose_name=_('User Name'))
    base_role = tables.Column('base_role', verbose_name=_('Base Role'))

    # Overriding get_object_id method because in IoT service the "id" is
    # identified by the field UUID
    def get_object_id(self, datum):
        return datum.uuid

    class Meta(object):
        name = "users"
        verbose_name = _("users")
        row_actions = (EditUserLink, DeleteUsersAction)
        table_actions = (UserFilterAction, CreateUserLink,
                         DeleteUsersAction)
