# coding=utf-8
#
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from iotronic.db import api as db_api
from iotronic.objects import base
from iotronic.objects import utils as obj_utils


class Role(base.IotronicObject):
    # Version 1.0: Initial version
    VERSION = '1.0'

    dbapi = db_api.get_instance()

    fields = {
        'name': obj_utils.str_or_none,
        'permissions': obj_utils.list_or_none,
        'description': obj_utils.str_or_none
    }

    @staticmethod
    def _from_db_object(role, db_role):
        """Converts a database entity to a formal object."""
        for field in role.fields:
            role[field] = db_role[field]
        role.obj_reset_changes()
        return role

    @base.remotable_classmethod
    def get_by_name(cls, context, role_name):
        """Find a role based on name and return a Role object.

        :param role_name: the name of a role.
        :returns: a :class:`Role` object.
        """
        db_role = cls.dbapi.get_role_by_name(role_name)
        role = Role._from_db_object(cls(context), db_role)
        return role

    @base.remotable_classmethod
    def list(cls, context, limit=None, sort_key=None, sort_dir=None,
             filters=None):
        """Return a list of Role objects.

        :param context: Security context.
        :param limit: maximum number of resources to return in a single result.
        :param filters: Filters to apply.
        :returns: a list of :class:`Role` object.

        """
        db_roles = cls.dbapi.get_role_list(filters=filters, limit=limit,
                                           sort_key=sort_key,
                                           sort_dir=sort_dir)
        return [Role._from_db_object(cls(context), obj) for obj in db_roles]

    @base.remotable
    def create(self, context=None):
        """Create a Role record in the DB.

        Column-wise updates will be made based on the result of
        self.what_changed(). If target_power_state is provided,
        it will be checked against the in-database copy of the
        role before updates are made.

        :param context: Security context. NOTE: This should only
                        be used internally by the indirection_api.
                        Unfortunately, RPC requires context as the first
                        argument, even though we don't use it.
                        A context should be set when instantiating the
                        object, e.g.: Role(context)

        """
        values = self.obj_get_changes()
        db_role = self.dbapi.create_role(values)
        self._from_db_object(self, db_role)

    @base.remotable
    def destroy(self, context=None):
        """Delete the Role from the DB.

        :param context: Security context. NOTE: This should only
                        be used internally by the indirection_api.
                        Unfortunately, RPC requires context as the first
                        argument, even though we don't use it.
                        A context should be set when instantiating the
                        object, e.g.: Role(context)
        """
        self.dbapi.destroy_role(self.name)
        self.obj_reset_changes()

    @base.remotable
    def save(self, context=None):
        """Save updates to this Role.

        Column-wise updates will be made based on the result of
        self.what_changed(). If target_power_state is provided,
        it will be checked against the in-database copy of the
        role before updates are made.

        :param context: Security context. NOTE: This should only
                        be used internally by the indirection_api.
                        Unfortunately, RPC requires context as the first
                        argument, even though we don't use it.
                        A context should be set when instantiating the
                        object, e.g.: Role(context)
        """
        updates = self.obj_get_changes()
        self.dbapi.update_role(self.name, updates)
        self.obj_reset_changes()
