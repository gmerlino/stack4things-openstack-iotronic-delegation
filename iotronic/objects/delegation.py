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

from oslo_utils import strutils
from oslo_utils import uuidutils

from iotronic.common import exception
from iotronic.db import api as db_api
from iotronic.objects import base
from iotronic.objects import utils as obj_utils
from oslo_log import log as logging

LOG = logging.getLogger(__name__)


class Delegation(base.IotronicObject):
    # Version 1.0: Initial version
    VERSION = '1.0'

    dbapi = db_api.get_instance()

    fields = {
        'id': int,
        'uuid': obj_utils.str_or_none,
        'delegated': obj_utils.str_or_none,
        'delegator': obj_utils.str_or_none,
        'parent': obj_utils.str_or_none,
        'role': obj_utils.str_or_none,
        'node': obj_utils.str_or_none,
        'type': obj_utils.str_or_none,
    }

    @staticmethod
    def _from_db_object(delegation, db_delegation):
        """Converts a database entity to a formal object."""
        for field in delegation.fields:
            delegation[field] = db_delegation[field]
        delegation.obj_reset_changes()
        return delegation

    @base.remotable_classmethod
    def get(cls, context, delegation_id):
        """Find a delegation based on its id or uuid and return a Delegation object.

        :param delegation_id: the id *or* uuid of a delegation.
        :returns: a :class:`Delegation` object.
        """
        if strutils.is_int_like(delegation_id):
            return cls.get_by_id(context, delegation_id)
        elif uuidutils.is_uuid_like(delegation_id):
            return cls.get_by_uuid(context, delegation_id)
        else:
            raise exception.InvalidIdentity(identity=delegation_id)

    @base.remotable_classmethod
    def get_by_id(cls, context, delegation_id):
        """Find a delegation based on its integer id and return a Delegation object.

        :param delegation_id: the id of a delegation.
        :returns: a :class:`delegation` object.
        """
        db_delegation = cls.dbapi.get_delegation_by_id(delegation_id)
        delegation = Delegation._from_db_object(cls(context), db_delegation)
        return delegation

    @base.remotable_classmethod
    def get_by_uuid(cls, context, uuid):
        """Find a delegation based on uuid and return a Delegation object.

        :param uuid: the uuid of a delegation.
        :returns: a :class:`Delegation` object.
        """
        db_delegation = cls.dbapi.get_delegation_by_uuid(uuid)
        delegation = Delegation._from_db_object(cls(context), db_delegation)
        return delegation

    @base.remotable_classmethod
    def get_by_user_node(cls, context, user_uuid, node_ident):
        """Find a delegation based on user and node uuid and return a
           Delegation object.

        :param uuid: the uuid of a delegation.
        :returns: a :class:`Delegation` object.
        """
        db_delegation = cls.dbapi.get_delegation_by_user_node(
            user_uuid, node_ident)
        delegation = Delegation._from_db_object(cls(context), db_delegation)
        return delegation

    @base.remotable_classmethod
    def list(cls, context, node_uuid, limit=None, marker=None,
             sort_key=None, sort_dir=None, filters=None):
        # def list(cls, context, authorized_delegations):
        """Return a list of Delegation objects.

        :param context: Security context.
        :param limit: maximum number of resources to return in
                      a single result.
        :param marker: pagination marker for large data sets.
        :param sort_key: column to sort results by.
        :param sort_dir: direction to sort. "asc" or "desc".
        :param filters: Filters to apply.
        :returns: a list of :class:`Delegation` object.

        """
        db_delegations = cls.dbapi.get_delegation_list(node_uuid,
                                                       filters=filters,
                                                       limit=limit,
                                                       marker=marker,
                                                       sort_key=sort_key,
                                                       sort_dir=sort_dir)
        return [Delegation._from_db_object(cls(context),
                                           obj) for obj in db_delegations]

    @base.remotable
    def create(self, context=None):
        """Create a Delegation record in the DB.

        Column-wise updates will be made based on the result of
        self.what_changed(). If target_power_state is provided,
        it will be checked against the in-database copy of the
        delegation before updates are made.

        :param context: Security context. NOTE: This should only
                        be used internally by the indirection_api.
                        Unfortunately, RPC requires context as the first
                        argument, even though we don't use it.
                        A context should be set when instantiating the
                        object, e.g.: Delegation(context)

        """
        values = self.obj_get_changes()
        db_delegation = self.dbapi.create_delegation(values)
        self._from_db_object(self, db_delegation)

    @base.remotable
    def destroy(self, context=None):
        """Delete the Delegation from the DB.

        :param context: Security context. NOTE: This should only
                        be used internally by the indirection_api.
                        Unfortunately, RPC requires context as the first
                        argument, even though we don't use it.
                        A context should be set when instantiating the
                        object, e.g.: Delegation(context)
        """
        self.dbapi.destroy_delegation(self.uuid, self.type)
        self.obj_reset_changes()

    @base.remotable_classmethod
    def destroy_by_node_uuid(cls, context, node_uuid, type):
        """Delete the Delegation from the DB."""
        cls.dbapi.destroy_delegation_by_node(node_uuid, type=type)

    @base.remotable_classmethod
    def destroy_by_uuid(cls, context, delegation_uuid, type):
        """Delete the Delegation from the DB."""
        cls.dbapi.destroy_delegation(delegation_uuid, type=type)

    @base.remotable_classmethod
    def check_role_assignment(cls, context, delegator_role,
                              delegated_role, type):
        """Ceck delegation role assignment."""
        if delegator_role == 'owner':
            return
        if delegated_role == 'owner':
            raise exception.DelegationEscalationRoleConflict()
        delegator_perms = cls.dbapi.get_role_permissions(
            delegator_role).permissions
        delegated_perms = cls.dbapi.get_role_permissions(
            delegated_role).permissions
        for perm_ed in delegated_perms:
            tp, delegated_op = perm_ed.split(':')
            if tp != type and tp != 'all':
                continue
            delegator_ops = []
            for perm_or in delegator_perms:
                tp, op = perm_or.split(':')
                if tp != type and tp != 'all':
                    continue
                if op == 'all':
                    return
                delegator_ops.append(op)
            if delegated_op not in delegator_ops:
                raise exception.DelegationEscalationRoleConflict()

    @base.remotable
    def save(self, context=None):
        """Save updates to this Delegation.

        Column-wise updates will be made based on the result of
        self.what_changed(). If target_power_state is provided,
        it will be checked against the in-database copy of the
        delegation before updates are made.

        :param context: Security context. NOTE: This should only
                        be used internally by the indirection_api.
                        Unfortunately, RPC requires context as the first
                        argument, even though we don't use it.
                        A context should be set when instantiating the
                        object, e.g.: Delegation(context)
        """
        updates = self.obj_get_changes()
        self.dbapi.update_delegation(self.uuid, updates)
        self.obj_reset_changes()

    @base.remotable
    def refresh(self, context=None):
        """Refresh the object by re-fetching from the DB.

        :param context: Security context. NOTE: This should only
                        be used internally by the indirection_api.
                        Unfortunately, RPC requires context as the first
                        argument, even though we don't use it.
                        A context should be set when instantiating the
                        object, e.g.: Delegation(context)
        """
        current = self.__class__.get_by_uuid(self._context, self.uuid)
        for field in self.fields:
            if (hasattr(
                    self, base.get_attrname(field))
                    and self[field] != current[field]):
                self[field] = current[field]
