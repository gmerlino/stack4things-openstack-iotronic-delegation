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


class User(base.IotronicObject):
    # Version 1.0: Initial version
    VERSION = '1.0'

    dbapi = db_api.get_instance()

    fields = {
        'uuid': obj_utils.str_or_none,
        'name': obj_utils.str_or_none,
        'base_role': obj_utils.str_or_none,
    }

    @staticmethod
    def _from_db_object(user, db_user):
        """Converts a database entity to a formal object."""
        for field in user.fields:
            user[field] = db_user[field]
        user.obj_reset_changes()
        return user

    @base.remotable_classmethod
    def get_by_uuid(cls, context, user_uuid):
        """Find a user based on its integer id and return a User object.

        :param user_uuid: the uuid of a user.
        :returns: a :class:`User` object.
        """
        db_user = cls.dbapi.get_user_by_uuid(user_uuid)
        user = User._from_db_object(cls(context), db_user)
        return user

    @base.remotable_classmethod
    def get_by_name(cls, context, user_name):
        """Find a user based on name and return a User object.

        :param user_name: the name of a user.
        :returns: a :class:`User` object.
        """
        db_user = cls.dbapi.get_user_by_name(user_name)
        user = User._from_db_object(cls(context), db_user)
        return user

    @base.remotable_classmethod
    def list(cls, context, limit=None, sort_key=None, sort_dir=None,
             filters=None):
        """Return a list of User objects.

        :param context: Security context.
        :param limit: maximum number of resources to return in a single result.
        :param filters: Filters to apply.
        :returns: a list of :class:`User` object.

        """
        db_users = cls.dbapi.get_user_list(filters=filters, limit=limit,
                                           sort_key=sort_key,
                                           sort_dir=sort_dir)
        return [User._from_db_object(cls(context), obj) for obj in db_users]

    @base.remotable
    def create(self, context=None):
        """Create a User record in the DB.

        Column-wise updates will be made based on the result of
        self.what_changed(). If target_power_state is provided,
        it will be checked against the in-database copy of the
        user before updates are made.

        :param context: Security context. NOTE: This should only
                        be used internally by the indirection_api.
                        Unfortunately, RPC requires context as the first
                        argument, even though we don't use it.
                        A context should be set when instantiating the
                        object, e.g.: User(context)

        """
        values = self.obj_get_changes()
        db_user = self.dbapi.create_user(values)
        self._from_db_object(self, db_user)

    @base.remotable
    def destroy(self, context=None):
        """Delete the User from the DB.

        :param context: Security context. NOTE: This should only
                        be used internally by the indirection_api.
                        Unfortunately, RPC requires context as the first
                        argument, even though we don't use it.
                        A context should be set when instantiating the
                        object, e.g.: User(context)
        """
        self.dbapi.destroy_user(self.uuid)
        self.obj_reset_changes()

    @base.remotable
    def save(self, context=None):
        """Save updates to this User.

        Column-wise updates will be made based on the result of
        self.what_changed(). If target_power_state is provided,
        it will be checked against the in-database copy of the
        user before updates are made.

        :param context: Security context. NOTE: This should only
                        be used internally by the indirection_api.
                        Unfortunately, RPC requires context as the first
                        argument, even though we don't use it.
                        A context should be set when instantiating the
                        object, e.g.: User(context)
        """
        updates = self.obj_get_changes()
        self.dbapi.update_user(self.uuid, updates)
        self.obj_reset_changes()
